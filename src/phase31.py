"""Phase 3.1 pipeline - Malaysian-informed public AC (destination) charging profile as a SENSITIVITY.

Called from run_all.py after Phase 3 (phase3.run fills phase3.LAST_CTX). Phase 3 outputs are not written or
changed here; every Phase 3.1 output has a new file name. Residential, workplace and public DC series are
produced by the unchanged Phase 3 code (hourly.build_profiles); only the public AC series is replaced.
"""
import json

import numpy as np
import pandas as pd

import config as C
import destination as D
import hourly as H

SCENS = ["20pct_xev", "30pct_xev", "historical_trend"]
MILEAGES = list(C.HOURLY_MILEAGE_CASES)
REF, IND = "evipro_reference", "industry_informed"


def variant_name(config=C.INDUSTRY_DEFAULT_CONFIG, width=C.INDUSTRY_DEFAULT_WIDTH, m=1.0):
    parts = [IND]
    if config != C.INDUSTRY_DEFAULT_CONFIG:
        parts.append(config)
    if width != C.INDUSTRY_DEFAULT_WIDTH:
        parts.append(f"width_{width}")
    if m != 1.0:
        parts.append(f"weekend_x{m:.2f}")
    return "__".join(parts)


def three_peaks(config, width) -> bool:
    regs = D.peak_regions(D.industry_shape24("weekday", config, width))
    want = list(C.INDUSTRY_WEEKDAY_PEAK_HOURS.values())
    return len(regs) == 3 and all(any(h in w for h in r["hours"]) for r, w in zip(regs, want))


def _calx(cal):
    base_cols = ["timestamp_local", "month", "day_of_week", "hour", "is_weekend", "is_public_holiday_dated", "behaviour_day_type", "tnb_tou_period"]
    x = cal[base_cols].copy()
    x["timestamp_local"] = cal["timestamp_local"].dt.strftime("%Y-%m-%dT%H:%M:%S%z").str.replace(r"(\+\d\d)(\d\d)$", r"\1:\2", regex=True)
    x.insert(1, "hour_of_year", np.arange(1, len(cal) + 1))
    return x


def run(ctx3) -> int:
    print("[14] Phase 3.1: Industry-informed public AC destination profile (sensitivity) ...")
    cal, targets, shapes3, activity, prof3 = ctx3["cal"], ctx3["targets"], ctx3["shapes"], ctx3["activity"], ctx3["profiles"]
    tg = targets.set_index(["adoption_scenario", "mileage_case"])
    base_mix = C.LOCATION_MIX["base"]

    ac_shapes = {REF: D.reference_shapes48(), IND: D.industry_shapes48()}
    for cf in C.INDUSTRY_PEAK_CONFIGS:
        for w in C.INDUSTRY_PEAK_WIDTHS:
            ac_shapes.setdefault(variant_name(cf, w), D.industry_shapes48(cf, w))

    # ---- physical-plausibility session library and fits ------------------------------------------
    lib, lib_stats = D.destination_session_library()
    fits = {(dt, basis): D.fit_sessions(H.fold24(ac_shapes[IND][dt]), lib, basis)
            for dt in ("weekday", "weekend_holiday") for basis in ("energy", "connected")}
    fits_ref = {(dt, "energy"): D.fit_sessions(H.fold24(ac_shapes[REF][dt]), lib, "energy") for dt in ("weekday", "weekend_holiday")}
    # occupancy interpretation: public AC POWER of the session mixture whose CONNECTED-vehicle profile matches the reported timing
    OCC = f"{IND}__occupancy_basis"
    ac_shapes[OCC] = {dt: D.shape48_from24(fits[(dt, "connected")]["energy_shape"]) for dt in ("weekday", "weekend_holiday")}

    def build(t, p, strat, variant, m=1.0, mix=None, act=None):
        return D.build(t.annual_mwh, act if act is not None else activity[t.name[0]], mix or base_mix, shapes3, p, strat,
                       None if variant == REF else ac_shapes[variant], m)

    def row(locs, **lab):
        mt = D.metrics31(locs, cal)
        mt.update(lab)
        return mt

    # ---- 1. principal comparison: reference vs Industry-informed (+ weekend multipliers) -------------
    main_variants = [(REF, 1.0), (IND, 1.0)] + [(IND, m) for m in C.INDUSTRY_WEEKEND_MULTIPLIERS if m != 1.0]
    comp, keep = [], {}
    for s in SCENS:
        for mc in MILEAGES:
            t = tg.loc[(s, mc)]
            t.name = (s, mc)
            for name, p, strat in C.P31_CHARGING_CASES:
                for v, m in main_variants:
                    locs = build(t, p, strat, v, m)
                    vn = v if v == REF else variant_name(m=m)
                    keep[(s, mc, name, vn)] = locs
                    comp.append(row(locs, adoption_scenario=s, mileage_case=mc, charging_scenario=name, participation_rate=p,
                                    public_ac_profile=vn, weekday_peak_config="-" if v == REF else C.INDUSTRY_DEFAULT_CONFIG,
                                    peak_width_sigma_h=np.nan if v == REF else C.INDUSTRY_PEAK_WIDTHS[C.INDUSTRY_DEFAULT_WIDTH],
                                    weekend_energy_multiplier=m, public_ac_share=base_mix["public_ac"], location_mix="base"))
    comp = pd.DataFrame(comp)
    ref_idx = comp[comp.public_ac_profile == REF].set_index(["adoption_scenario", "mileage_case", "charging_scenario"])
    for c in ("max_load_mw", "max_load_weekday_mw", "max_load_weekend_holiday_mw", "energy_tnb_peak_gwh", "max_ramp_up_mw_per_h",
              "public_ac_max_mw", "public_ac_tnb_peak_gwh"):
        comp[f"delta_{c}_vs_reference"] = [r[c] - ref_idx.loc[(r.adoption_scenario, r.mileage_case, r.charging_scenario), c] for _, r in comp.iterrows()]
    comp["max_timestamp_changed_vs_reference"] = [r.max_load_timestamp != ref_idx.loc[(r.adoption_scenario, r.mileage_case, r.charging_scenario), "max_load_timestamp"]
                                                  for _, r in comp.iterrows()]
    unm = comp[comp.charging_scenario == "unmanaged"].set_index(["adoption_scenario", "mileage_case", "public_ac_profile"])
    comp["weekday_max_reduction_vs_unmanaged_mw"] = [unm.loc[(r.adoption_scenario, r.mileage_case, r.public_ac_profile), "max_load_weekday_mw"] - r.max_load_weekday_mw for _, r in comp.iterrows()]
    comp["energy_shifted_out_of_tnb_peak_gwh"] = [unm.loc[(r.adoption_scenario, r.mileage_case, r.public_ac_profile), "energy_tnb_peak_gwh"] - r.energy_tnb_peak_gwh for _, r in comp.iterrows()]
    lead = ["adoption_scenario", "mileage_case", "charging_scenario", "participation_rate", "public_ac_profile", "weekday_peak_config",
            "peak_width_sigma_h", "weekend_energy_multiplier", "location_mix", "public_ac_share", "annual_gwh"]
    comp = comp[lead + [c for c in comp.columns if c not in lead]]
    comp.round(6).to_csv(C.TABLES / "public_ac_profile_comparison.csv", index=False)

    # ---- 2. sensitivities (20% xEV, base mileage) -----------------------------------------------------
    t20 = tg.loc[("20pct_xev", "base_17969km")]
    t20.name = ("20pct_xev", "base_17969km")
    sens = []

    def srow(dim, locs, v, name, p, **kw):
        lab = dict(sensitivity_dimension=dim, public_ac_profile=v, charging_scenario=name, participation_rate=p,
                   weekday_peak_config=kw.get("config", "-" if v == REF else C.INDUSTRY_DEFAULT_CONFIG),
                   peak_width=kw.get("width", "-" if v == REF else C.INDUSTRY_DEFAULT_WIDTH),
                   weekend_energy_multiplier=kw.get("m", 1.0), public_ac_share=kw.get("share", base_mix["public_ac"]),
                   location_mix=kw.get("mix_name", "base"),
                   three_weekday_peaks_retained=kw.get("three", None))
        sens.append(row(locs, **lab))

    # 2a magnitudes x widths x weekend multipliers (full factorial)
    for cf in C.INDUSTRY_PEAK_CONFIGS:
        for w in C.INDUSTRY_PEAK_WIDTHS:
            for m in C.INDUSTRY_WEEKEND_MULTIPLIERS:
                for name, p, strat in C.P31_CHARGING_CASES:
                    srow("peak_magnitude_x_width_x_weekend_multiplier", build(t20, p, strat, variant_name(cf, w), m),
                         variant_name(cf, w, m), name, p, config=cf, width=w, m=m, three=three_peaks(cf, w))
    for name, p, strat in C.P31_CHARGING_CASES:
        srow("peak_magnitude_x_width_x_weekend_multiplier", build(t20, p, strat, REF), REF, name, p)
        srow("activity_interpretation_occupancy_basis", build(t20, p, strat, OCC), OCC, name, p, config="session-derived", width="-")
    # 2b public AC energy share (others pro rata)
    for sh in C.PUBLIC_AC_SHARE_SENSITIVITY:
        mix = D.mix_with_public_ac_share(sh)
        for v in (REF, IND):
            for name, p, strat in C.P31_CHARGING_CASES:
                srow("public_ac_share", build(t20, p, strat, v, mix=mix), v, name, p, share=sh, mix_name=f"public_ac_{int(sh * 100)}pct_pro_rata")
    # 2c existing alternative location mixes
    for mx in ("home_low", "home_high", "work_high"):
        for v in (REF, IND):
            for name, p, strat in C.P31_CHARGING_CASES:
                srow("location_mix", build(t20, p, strat, v, mix=C.LOCATION_MIX[mx]), v, name, p, share=C.LOCATION_MIX[mx]["public_ac"], mix_name=mx)
    # 2d interaction with residential ToU participation
    for v in (REF, IND):
        for p in C.PARTICIPATION_LEVELS:
            name = "unmanaged" if p == 0 else f"managed_staggered_p{int(p * 100)}"
            srow("residential_tou_participation", build(t20, p, "staggered" if p else "unmanaged", v), v, name, p)
    sens = pd.DataFrame(sens)
    key_cols = ["sensitivity_dimension", "public_ac_share", "location_mix", "charging_scenario", "participation_rate"]
    refs = sens[sens.public_ac_profile == REF].drop_duplicates(key_cols).set_index(key_cols)
    for c in ("max_load_mw", "max_load_weekday_mw", "max_load_weekend_holiday_mw", "energy_tnb_peak_gwh"):
        sens[f"delta_{c}_vs_reference"] = [r[c] - refs.loc[tuple(r[k] for k in key_cols), c]
                                          if tuple(r[k] for k in key_cols) in refs.index else
                                          r[c] - refs.loc[("peak_magnitude_x_width_x_weekend_multiplier", r.public_ac_share, "base", r.charging_scenario, r.participation_rate), c]
                                          for _, r in sens.iterrows()]
    p0 = sens[sens.sensitivity_dimension == "residential_tou_participation"]
    p0u = p0[p0.participation_rate == 0].set_index("public_ac_profile")
    sens["weekday_max_reduction_vs_p0_mw"] = np.nan
    sens["energy_shifted_out_of_tnb_peak_gwh"] = np.nan
    msk = sens.sensitivity_dimension == "residential_tou_participation"
    sens.loc[msk, "weekday_max_reduction_vs_p0_mw"] = [p0u.loc[r.public_ac_profile, "max_load_weekday_mw"] - r.max_load_weekday_mw for _, r in sens[msk].iterrows()]
    sens.loc[msk, "energy_shifted_out_of_tnb_peak_gwh"] = [p0u.loc[r.public_ac_profile, "energy_tnb_peak_gwh"] - r.energy_tnb_peak_gwh for _, r in sens[msk].iterrows()]
    sens.insert(1, "adoption_scenario", "20pct_xev")
    sens.insert(2, "mileage_case", "base_17969km")
    sens.round(6).to_csv(C.TABLES / "phase_3_1_peak_sensitivity.csv", index=False)

    # ---- 3. hourly public AC series --------------------------------------------------------------------
    calx = _calx(cal)
    hourly_variants = {("20pct_xev", "base_17969km"): [(REF, 1.0), (IND, 1.0)] + [(variant_name(cf), 1.0) for cf in C.INDUSTRY_PEAK_CONFIGS if cf != C.INDUSTRY_DEFAULT_CONFIG]
                       + [(variant_name(width=w), 1.0) for w in C.INDUSTRY_PEAK_WIDTHS if w != C.INDUSTRY_DEFAULT_WIDTH]
                       + [(IND, m) for m in C.INDUSTRY_WEEKEND_MULTIPLIERS if m != 1.0] + [(OCC, 1.0)]}
    for s in SCENS:
        for mc in MILEAGES:
            hourly_variants.setdefault((s, mc), [(REF, 1.0), (IND, 1.0)] + [(IND, m) for m in C.INDUSTRY_WEEKEND_MULTIPLIERS if m != 1.0])
    hrows, ac_series = [], {}
    for (s, mc), vs in hourly_variants.items():
        t = tg.loc[(s, mc)]
        days = H.daily_frame()
        for v, m in vs:
            de = D.public_ac_daily_energy(t.annual_mwh, base_mix["public_ac"], days, activity[s], m)
            ser = H.assemble(de, days, ac_shapes[v])
            vn = v if v in (REF, OCC) else (variant_name(m=m) if v == IND else v)
            ac_series[(s, mc, vn)] = ser
            a = calx.copy()
            a["adoption_scenario"], a["mileage_case"], a["public_ac_profile"] = s, mc, vn
            a["weekend_energy_multiplier"] = m
            a["public_ac_share_of_total_bev_energy"] = base_mix["public_ac"]
            a["public_ac_load_mw"] = ser
            a["normalized_hourly_weight"] = ser / ser.sum()
            hrows.append(a)
    hdf = pd.concat(hrows, ignore_index=True)
    hdf["public_ac_load_mw"] = hdf["public_ac_load_mw"].round(6)
    hdf["normalized_hourly_weight"] = hdf["normalized_hourly_weight"].round(12)
    hdf.to_csv(C.TABLES / "public_ac_industry_informed_hourly.csv", index=False)

    # ---- 4. LEAP sensitivity file (wide by location) ----------------------------------------------------
    lrows = []
    leap_keys = [(s, mc, name, IND) for s in SCENS for mc in MILEAGES for name, _, _ in C.P31_CHARGING_CASES] + \
                [("20pct_xev", "base_17969km", name, variant_name(m=m)) for m in C.INDUSTRY_WEEKEND_MULTIPLIERS if m != 1.0
                 for name in ("unmanaged", "managed_staggered_p50")]
    pr = {n: p for n, p, _ in C.P31_CHARGING_CASES}
    for (s, mc, name, vn) in leap_keys:
        locs = keep[(s, mc, name, vn)]
        tot = sum(locs.values())
        a = calx.copy()
        a["adoption_scenario"], a["mileage_case"], a["charging_scenario"], a["participation_rate"] = s, mc, name, pr[name]
        a["public_ac_profile"] = vn
        a["weekend_energy_multiplier"] = 1.0 if vn == IND else float(vn.split("_x")[-1])
        for loc in C.LOCATIONS:
            a[f"{loc}_mw"] = locs[loc]
        a["total_mw"] = tot
        a["normalized_hourly_weight"] = tot / tot.sum()
        lrows.append(a)
    ldf = pd.concat(lrows, ignore_index=True)
    for c in [f"{l}_mw" for l in C.LOCATIONS] + ["total_mw"]:
        ldf[c] = ldf[c].round(6)
    ldf["normalized_hourly_weight"] = ldf["normalized_hourly_weight"].round(12)
    ldf.to_csv(C.TABLES / "leap_bev_hourly_load_2030_industry_sensitivity.csv", index=False)

    # ---- 5. physical plausibility table -------------------------------------------------------------------
    pl = []
    for (s, mc, name, vn), locs in keep.items():
        if name != "unmanaged" or vn not in (REF, IND):
            continue
        ac = locs["public_ac"]
        days = H.daily_frame()
        wk = (cal["behaviour_day_type"] == "weekday").values
        daily = ac.reshape(-1, 24).sum(1)
        for dt, dmask in (("weekday", (days.day_type == "weekday").values), ("weekend_holiday", (days.day_type != "weekday").values)):
            f = fits[(dt, "energy")] if vn == IND else fits_ref[(dt, "energy")]
            hm = wk if dt == "weekday" else ~wk
            imax = int(np.flatnonzero(hm)[np.argmax(ac[hm])])
            dmax = daily[imax // 24]
            pl.append(dict(adoption_scenario=s, mileage_case=mc, public_ac_profile=vn, day_type=dt,
                           max_public_ac_mw=ac[hm].max(), timestamp_of_max=str(cal["timestamp_local"].iloc[imax]),
                           daily_public_ac_mwh_on_that_day=dmax, max_hourly_share_of_daily_energy=ac[imax] / dmax,
                           implied_vehicles_charging_at_max_at_mean_power=ac[hm].max() * 1000 / sum(k * v for k, v in C.DEST_POWER_MIX.items()),
                           implied_sessions_that_day_session_library=f["sessions_per_mwh"] * dmax,
                           mevnet_2026_national_non_dc_public_chargers_context=C.MEVNET_PUBLIC_CHARGERS_2026["total"] - C.MEVNET_PUBLIC_CHARGERS_2026["dc"],
                           session_fit_r=f["r"], session_fit_max_abs_err_pp=f["max_abs_err_pp"],
                           mean_ac_power_kw_assumed=sum(k * v for k, v in C.DEST_POWER_MIX.items()),
                           status="implied by researcher-defined session library; NOT observed station counts or utilisation"))
    pl = pd.DataFrame(pl)
    pl.round(4).to_csv(C.TABLES / "public_ac_plausibility_check.csv", index=False)
    libdf = pd.DataFrame([dict(visit_type=k, arrival_mean_h=v[0], arrival_sd_h=v[1], dwell_median_h=v[2], dwell_lognormal_sigma=v[3],
                               **{kk: round(vv, 4) for kk, vv in lib_stats[k].items()},
                               **{f"fit_sessions_per_mwh__{dt}__{b}": round(fits[(dt, b)]["counts_per_kwh"][k] * 1000, 4)
                                  for dt in ("weekday", "weekend_holiday") for b in ("energy", "connected")})
                          for k, v in C.DEST_VISIT_TYPES.items()])
    libdf.to_csv(C.TABLES / "public_ac_session_library_fit.csv", index=False)

    # ---- 6. normalized 24-h shapes (for reports/figures) ---------------------------------------------------
    shp_rows = []
    for v, sh in ac_shapes.items():
        for dt in ("weekday", "weekend_holiday"):
            vv = H.fold24(sh[dt])
            for hr in range(24):
                shp_rows.append(dict(public_ac_profile=v, day_type=dt, hour=hr, share_of_daily_public_ac_energy=vv[hr]))
    shp = pd.DataFrame(shp_rows)

    ctx = dict(cal=cal, targets=targets, prof3=prof3, keep=keep, comp=comp, sens=sens, hdf=hdf, ldf=ldf, ac_series=ac_series,
               ac_shapes=ac_shapes, shp=shp, fits=fits, fits_ref=fits_ref, lib=lib, lib_stats=lib_stats, pl=pl, activity=activity,
               shapes3=shapes3, three_peaks=three_peaks, OCC=OCC)
    import figures_destination as FD
    import validation_destination as VD
    print("      figures ...")
    FD.make_all(ctx)
    print("      validation ...")
    val = VD.run_checks(ctx)
    val.to_csv(C.TABLES / "phase_3_1_validation_results.csv", index=False)
    VD.write_report(val, C.REPORTS / "phase_3_1_validation.md")
    n_fail = int((val.result == "FAIL").sum())
    print(val[["requirement", "result", "check"]].to_string(index=False))

    key = comp.set_index(["adoption_scenario", "mileage_case", "charging_scenario", "public_ac_profile"])[
        ["max_load_mw", "max_load_timestamp", "max_load_weekday_mw", "max_load_weekend_holiday_mw", "max_load_weekend_holiday_timestamp",
         "public_ac_max_mw", "public_ac_max_timestamp", "share_tnb_peak", "public_ac_share_in_tnb_peak", "max_ramp_up_mw_per_h"]].round(4)
    (C.TABLES / "phase3_1_key_results.json").write_text(json.dumps(
        {"|".join(k): v for k, v in key.to_dict(orient="index").items()} | {"validation_checks": len(val), "validation_failures": n_fail},
        indent=1), encoding="utf-8")
    return n_fail

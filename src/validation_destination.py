"""Phase 3.1 automated validation - the 15 requirements of the brief (section 9) plus a partial physical-plausibility check."""
import hashlib

import numpy as np
import pandas as pd

import config as C
import destination as D
import hourly as H

REF, IND = "evipro_reference", "industry_informed"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_checks(ctx) -> pd.DataFrame:
    res = []

    def add(req, name, ok, detail=""):
        res.append(dict(requirement=req, check=name, result="PASS" if bool(ok) else "FAIL", detail=str(detail)))

    cal, keep, hdf, ldf, prof3, tg = ctx["cal"], ctx["keep"], ctx["hdf"], ctx["ldf"], ctx["prof3"], ctx["targets"]
    sens, comp, shp = ctx["sens"], ctx["comp"], ctx["ac_shapes"]
    tgi = tg.set_index(["adoption_scenario", "mileage_case"])
    totals = {k: sum(v.values()) for k, v in keep.items()}

    # 1 record counts
    nh = hdf.groupby(["adoption_scenario", "mileage_case", "public_ac_profile"]).size()
    nl = ldf.groupby(["adoption_scenario", "mileage_case", "charging_scenario", "public_ac_profile"]).size()
    nk = {len(a) for v in keep.values() for a in v.values()}
    add(1, "Exactly 8,760 hourly values per public AC series, per LEAP sensitivity profile and per in-memory location profile",
        (nh == 8760).all() and (nl == 8760).all() and nk == {8760},
        f"{len(nh)} public AC series, {len(nl)} LEAP profiles, {len(keep)} comparison profile sets")

    # 2 timestamps
    ts = cal["timestamp_local"]
    off = ts.map(lambda t: t.utcoffset().total_seconds() / 3600).unique()
    ok_str = all(df.groupby(g)["timestamp_local"].apply(lambda s: s.is_unique and s.str.endswith("+08:00").all() and
                                                         s.iloc[0] == "2030-01-01T00:00:00+08:00" and s.iloc[-1] == "2030-12-31T23:00:00+08:00").all()
                 for df, g in ((hdf, ["adoption_scenario", "mileage_case", "public_ac_profile"]),
                               (ldf, ["adoption_scenario", "mileage_case", "charging_scenario", "public_ac_profile"])))
    add(2, "Timestamps 2030-01-01T00:00+08:00 to 2030-12-31T23:00+08:00, hourly, unique, Asia/Kuala_Lumpur (UTC+08:00, no DST)",
        list(off) == [8.0] and (ts.diff().dropna() == pd.Timedelta(hours=1)).all() and ok_str, f"offsets {list(off)}")

    # 3 annual energy conserved
    errs = [abs(totals[k].sum() / tgi.loc[(k[0], k[1]), "annual_mwh"] - 1) for k in totals]
    lsum = ldf.groupby(["adoption_scenario", "mileage_case", "charging_scenario", "public_ac_profile"])["total_mw"].sum()
    lerr = max(abs(v / tgi.loc[(k[0], k[1]), "annual_mwh"] - 1) for k, v in lsum.items())
    serr = (sens.annual_gwh / tgi.loc[("20pct_xev", "base_17969km"), "annual_grid_energy_gwh"] - 1).abs().max()
    add(3, "Annual BEV energy of every profile (reference, industry-informed, multipliers, all sensitivities) = Phase 3 / Phase 2 annual target",
        max(errs) < 1e-9 and lerr < 1e-8 and serr < 1e-9,
        f"max rel. error: in-memory {max(errs):.1e}, LEAP file (6-dp) {lerr:.1e}, sensitivities {serr:.1e}; 20% xEV {tgi.loc[('20pct_xev', 'base_17969km'), 'annual_grid_energy_gwh']:.3f} GWh")

    # 4 public AC share
    sh_err = max(abs(v["public_ac"].sum() / totals[k].sum() - C.LOCATION_MIX["base"]["public_ac"]) for k, v in keep.items())
    ac_gwh = keep[("20pct_xev", "base_17969km", "unmanaged", IND)]["public_ac"].sum() / 1000
    s_err = (sens.public_ac_share_of_total - sens.public_ac_share).abs().max()
    mix_ok = all(abs(sum(D.mix_with_public_ac_share(s).values()) - 1) < 1e-12 for s in C.PUBLIC_AC_SHARE_SENSITIVITY)
    add(4, "Public AC = 15% of total BEV energy in every principal profile; share-sensitivity runs hit their assigned share; pro-rata mixes sum to 100%",
        sh_err < 1e-12 and s_err < 1e-9 and mix_ok,
        f"20% xEV public AC {ac_gwh:.3f} GWh (= 15% x 1,284.977); max share error {max(sh_err, s_err):.1e}")

    # 5 other locations unchanged
    bad = [k for k, v in keep.items() for loc in ("residential", "workplace", "public_dc")
           if not np.array_equal(v[loc], prof3[(k[0], k[1], k[2])][1][loc])]
    ref_same = all(np.array_equal(v["public_ac"], prof3[(k[0], k[1], k[2])][1]["public_ac"]) for k, v in keep.items() if k[3] == REF)
    add(5, "Residential, workplace and public DC hourly series identical (bit-for-bit) to Phase 3 in every principal profile; reference public AC identical to Phase 3",
        not bad and ref_same, f"{len(keep)} profile sets compared; mismatches {bad[:3] or 'none'}")

    # 6 nonnegative
    mins = [min(a.min() for a in v.values()) for v in keep.values()] + [hdf.public_ac_load_mw.min(), ldf.total_mw.min()] + \
           [min(s.min() for s in v.values()) for v in shp.values()]
    add(6, "All hourly power values and shapes >= 0", min(mins) >= 0, f"min {min(mins):.3g}")

    # 7 weekday three peaks
    want = list(C.INDUSTRY_WEEKDAY_PEAK_HOURS.values())
    det, merged = {}, []
    for cf in C.INDUSTRY_PEAK_CONFIGS:
        for w in C.INDUSTRY_PEAK_WIDTHS:
            ok = ctx["three_peaks"](cf, w)
            det[f"{cf}/{w}"] = ok
            if not ok:
                merged.append(f"{cf}/{w}")
    claimed = [k for k in det if not k.endswith("/wide") or k.startswith("equal")]
    add(7, "Weekday industry-informed shape has three distinct peak regions (prominence >= 10%) in 12-14, 17-18 and 20-22 h - default and all magnitude configurations at narrow/default width, and equal magnitudes at every width",
        all(det[k] for k in claimed), f"default regions: {[r['hours'] for r in D.peak_regions(D.industry_shape24('weekday'))]}; "
                                       f"peaks merge (flagged, reported in sensitivity table, not claimed as three-peak): {merged or 'none'}")
    spikes = []
    for v, sh in shp.items():
        if v == REF:
            continue
        for dt in ("weekday", "weekend_holiday"):
            s = H.fold24(sh[dt])
            nb = (np.roll(s, 1) + np.roll(s, -1)) / 2
            if (s > 2.0 * nb + 1e-12).any() and v != ctx["OCC"]:
                spikes.append(f"{v}/{dt}")
    add(7, "No isolated single-hour spikes in the aggregate industry-informed shapes (each hour <= 2 x mean of its neighbours)", not spikes,
        f"violations: {spikes or 'none'} (session-derived occupancy-basis variant excluded: it is built from simulated sessions)")

    # 8 weekend plateau
    rows = []
    for w in C.INDUSTRY_PEAK_WIDTHS:
        s = D.industry_shape24("weekend_holiday", width=w)
        regs = D.peak_regions(s)
        rows.append(dict(width=w, argmax=int(np.argmax(s)), plateau=bool((s[12:16] >= 0.80 * s.max()).all()), n_regions=len(regs),
                         share_12_16=float(s[12:16].sum()), max_share=float(s.max()),
                         wk_max_share=float(D.industry_shape24("weekday", width=w).max())))
    ok = all(12 <= r["argmax"] <= 15 and r["plateau"] and r["n_regions"] == 1 and r["share_12_16"] >= 0.45 for r in rows)
    add(8, "Weekend/holiday shape is unimodal with a broad 12:00-16:00 plateau (max in 12-15 h, every hour 12-15 >= 80% of max, >= 45% of daily energy in 12-16 h)",
        ok, "; ".join(f"{r['width']}: max h{r['argmax']}, 12-16 share {r['share_12_16']:.1%}" for r in rows))
    add(8, "Interpretation 1: with equal daily energy the weekend hourly maximum share exceeds the weekday maximum share (higher instantaneous activity)",
        all(r["max_share"] > r["wk_max_share"] for r in rows), "; ".join(f"{r['width']}: weekend {r['max_share']:.1%} vs weekday {r['wk_max_share']:.1%}" for r in rows))

    # 9 weekend multipliers
    act = ctx["activity"]
    oks, det9 = [], []
    days = H.daily_frame()
    wkd = (days.day_type == "weekday").values
    for (s, mc, name, vn), v in keep.items():
        if name != "unmanaged" or not vn.startswith(IND):
            continue
        m = float(vn.split("_x")[-1]) if "_x" in vn else 1.0
        de = D.public_ac_daily_energy(tgi.loc[(s, mc), "annual_mwh"], C.LOCATION_MIX["base"]["public_ac"], days, act[s], m)
        a = act[s].reindex(days.date).values
        ratio = (de[~wkd] / a[~wkd]).mean() / (de[wkd] / a[wkd]).mean()
        oks.append(np.isclose(v["public_ac"].sum(), keep[(s, mc, name, IND)]["public_ac"].sum(), rtol=1e-12) and np.isclose(ratio, m, rtol=1e-12))
        if s == "20pct_xev" and mc == "base_17969km":
            det9.append(f"m={m}: weekday {de[wkd].mean():.1f} / weekend {de[~wkd].mean():.1f} MWh/day")
    add(9, "Weekend multipliers 1.0/1.25/1.5: annual public AC energy unchanged after joint normalization; weekend:weekday energy per vehicle-day = m",
        all(oks) and len(oks) == 18, "; ".join(det9))

    # 10 managed = unmanaged
    ok = all(np.isclose(totals[k].sum(), totals[(k[0], k[1], "unmanaged", k[3])].sum(), rtol=1e-12) for k in totals)
    add(10, "Managed (staggered/synchronized, p50/p100) and unmanaged profiles have identical annual energy for every public AC variant", ok, f"{len(totals)} profiles")

    # 11 ToU
    dow = ts.dt.dayofweek
    exp_peak = (dow < 5) & ~cal["is_public_holiday_dated"] & cal["hour"].between(14, 21)
    h20 = hdf[(hdf.adoption_scenario == "20pct_xev") & (hdf.mileage_case == "base_17969km") & (hdf.public_ac_profile == IND)]
    add(11, "TNB ToU: peak = Mon-Fri 14:00-22:00 except dated holidays (2,056 h); exported period labels match the calendar",
        ((cal["tnb_tou_period"] == "peak") == exp_peak).all() and int(exp_peak.sum()) == 2056 and
        (h20.tnb_tou_period.values == cal["tnb_tou_period"].values).all(), f"{int(exp_peak.sum())} peak hours")

    # 12 Phase 3 reproducible
    diffs = []
    for line in (C.RUN4_ARCHIVE / "SHA256SUMS.txt").read_text().splitlines():
        h, rel = line.split(maxsplit=1)
        cur = (C.TABLES / rel.split("/", 1)[1]) if rel.startswith("tables/") else (C.REPORTS / rel.split("/", 1)[1])
        if not cur.exists() or _sha(cur) != h:
            diffs.append(rel)
    n = len((C.RUN4_ARCHIVE / "SHA256SUMS.txt").read_text().splitlines())
    add(12, "Phase 3 (Run 4) outputs regenerated byte-identical to the frozen archive (all tables incl. both hourly LEAP files, generated validation reports)",
        not diffs, f"{n} files checked; differing: {diffs or 'none'}")
    add(12, "Phase 3.1 writes no file that Phase 3 writes (new file names only)",
        not ({"public_ac_industry_informed_hourly.csv", "public_ac_profile_comparison.csv", "phase_3_1_peak_sensitivity.csv",
              "leap_bev_hourly_load_2030_industry_sensitivity.csv"} & {l.split("/")[-1] for l in (C.RUN4_ARCHIVE / "SHA256SUMS.txt").read_text().split()}), "")

    # 13 adoption and mileage scaling
    ratio = C.HOURLY_MILEAGE_CASES["giz_15000km"] / C.HOURLY_MILEAGE_CASES["base_17969km"]
    ok, det13 = True, []
    for s in ("20pct_xev", "30pct_xev", "historical_trend"):
        for name, _, _ in C.P31_CHARGING_CASES:
            b, g = totals[(s, "base_17969km", name, IND)], totals[(s, "giz_15000km", name, IND)]
            ok &= np.isclose(g.sum() / b.sum(), ratio, rtol=1e-12) and np.allclose(g / g.sum(), b / b.sum(), atol=1e-15)
        ac = keep[(s, "base_17969km", "unmanaged", IND)]["public_ac"].sum()
        ok &= np.isclose(ac, 0.15 * tgi.loc[(s, "base_17969km"), "phase2_annual_grid_energy_gwh"] * 1000, rtol=1e-12)
        det13.append(f"{s}: public AC {ac / 1000:.3f} GWh")
    add(13, "15,000 km profiles = base x 15,000/17,969.23 with identical hourly weights; public AC = 15% of each adoption scenario's Phase 2 total",
        ok, f"ratio {ratio:.6f}; " + "; ".join(det13))

    # 14 losses
    r2 = pd.read_csv(C.TABLES / "bev_annual_energy_2025_2030_detail.csv")
    r2 = r2[(r2.year == C.HOURLY_YEAR) & (r2.case == "base") & (r2.geography == "peninsular") & (r2.scenario == "20pct_xev")].iloc[0]
    batt = r2.vehicle_years * r2.annual_km * r2.kwh_per_100km / 100 / 1e3     # MWh at the battery
    t = totals[("20pct_xev", "base_17969km", "unmanaged", IND)].sum()
    add(14, "Charging losses applied once: industry-informed total = battery energy / 0.90; public AC = 15% of that; no efficiency factor in Phase 3.1",
        np.isclose(t, batt / r2.charging_efficiency, rtol=1e-6), f"grid/battery = {t / batt:.4f} (1/0.90 = 1.1111)")

    # 15 no system peak / reserve margin
    import json
    cols = set(hdf.columns) | set(ldf.columns) | set(comp.columns) | set(sens.columns) | set(ctx["pl"].columns)
    keys = json.dumps(list(comp.columns))
    bad = [c for c in cols if any(w in c.lower() for w in ("system", "reserve", "margin", "gso", "net_load", "residual"))]
    add(15, "No system-wide peak, net/residual load or reserve-margin quantity is computed or exported (no GSO baseline integrated)",
        not bad and "reserve" not in keys, f"offending columns: {bad or 'none'}")

    # 16 partial physical plausibility (session library)
    fits = ctx["fits"]
    add(16, "A non-negative mix of researcher-defined destination sessions (7.4/11 kW AC, 1-9 h dwell, energy <= power x dwell) reproduces the industry-informed shapes (r >= 0.90)",
        all(fits[(dt, "energy")]["r"] >= 0.90 for dt in ("weekday", "weekend_holiday")),
        "; ".join(f"{dt}: r={fits[(dt, 'energy')]['r']:.3f}, max error {fits[(dt, 'energy')]['max_abs_err_pp']:.1f} pp" for dt in ("weekday", "weekend_holiday"))
        + " - consistency check only; station counts, installed capacity and utilisation are NOT validated")
    return pd.DataFrame(res)


NAMES = {1: "8,760 hourly observations per profile", 2: "Malaysian timestamps (UTC+08:00)", 3: "Annual energy conserved",
         4: "Public AC keeps its assigned annual share", 5: "Other charging locations unchanged", 6: "Nonnegative hourly power",
         7: "Weekday shape has three peak regions", 8: "Weekend shape has a broad 12:00-16:00 peak",
         9: "Weekend multipliers preserve annual energy", 10: "Managed = unmanaged annual energy", 11: "TNB ToU classification",
         12: "Phase 3 outputs reproducible", 13: "Adoption and mileage sensitivities scale consistently",
         14: "No double-counted charging losses", 15: "No system-wide peak or reserve margin without the grid baseline",
         16: "Physical plausibility (partial, session-library consistency)"}


def write_report(val: pd.DataFrame, path):
    n_fail = int((val.result == "FAIL").sum())
    lines = ["# Phase 3.1 - destination (public AC) charging profile validation", "",
             "*Generated by `src/run_all.py` (`validation_destination.py`). Do not edit by hand.*", "",
             f"**{len(val)} checks, {len(val) - n_fail} PASS, {n_fail} FAIL.**", "",
             "Requirements 1-15 follow the Phase 3.1 brief (section 9). Requirement 16 is a partial physical-plausibility check.",
             "", "**What these tests cannot establish** (see `public_ac_profile_methodology.md` section 6):",
             "- whether the qualitative 'active usage' peaks describe charging power, connected vehicles or session counts;",
             "- the true relative magnitudes of the three weekday peaks and the true weekend:weekday energy ratio;",
             "- whether 2030 Peninsular AC destination charger capacity can deliver the implied simultaneous charging (no installed-capacity or utilisation data);",
             "- representativeness of the observed sites (coverage, sample size and period unconfirmed).", ""]
    for req, g in val.groupby("requirement"):
        lines += [f"## {req}. {NAMES[req]}", "", "| Check | Result | Detail |", "|---|---|---|"]
        for _, r in g.iterrows():
            lines.append(f"| {r['check']} | **{r['result']}** | {str(r['detail']).replace('|', '/')} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

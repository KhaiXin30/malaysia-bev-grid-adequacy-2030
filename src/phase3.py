"""Phase 3 (Run 4) pipeline - hourly BEV charging profiles 2030 (Peninsular Malaysia), unmanaged vs
TNB-ToU managed. Called from run_all.py after Phase 2; reuses Phase 1.5 daily fleet exposure and the
Phase 2 annual energy (bev_annual_energy_2025_2030_detail.csv).
"""
import json

import numpy as np
import pandas as pd

import config as C
import energy as EN
import exposure as EX
import hourly as H

SCENS = ["20pct_xev", "30pct_xev", "historical_trend"]
LAST_CTX = {}     # filled by run(); consumed by Phase 3.1 (phase31.py) - does not affect Phase 3 outputs
SCEN_IN = {v: k for k, v in EX.SCEN_OUT.items()}
CHARGING_CASES = [("unmanaged", 0.0, "unmanaged")] + \
    [(f"managed_staggered_p{int(p * 100)}", p, "staggered") for p in C.PARTICIPATION_LEVELS if p > 0] + \
    [(f"managed_synchronized_p{int(p * 100)}", p, "synchronized") for p in (0.5, 1.0)]
DETAIL_CASES = ["unmanaged", f"managed_staggered_p{int(C.PROVISIONAL_PARTICIPATION * 100)}", "managed_staggered_p100"]


def annual_energy_targets() -> pd.DataFrame:
    """Phase 2 2030 Peninsular base-case grid energy (MWh) and the 15,000 km sensitivity (fleet,
    consumption and charging efficiency held at base)."""
    d = pd.read_csv(C.TABLES / "bev_annual_energy_2025_2030_detail.csv")
    d = d[(d.year == C.HOURLY_YEAR) & (d.case == "base") & (d.geography == "peninsular")].set_index("scenario")
    rows = []
    for s in SCENS:
        r = d.loc[s]
        for mc, km in C.HOURLY_MILEAGE_CASES.items():
            # exact Phase 2 total for the working base; the mileage sensitivity scales it in proportion to km
            # (identical to recomputing E = VY x km x c / 100 / eta / 1e6 with base fleet, c and eta)
            gwh = float(r.annual_grid_energy_gwh) * km / r.annual_km
            rows.append(dict(adoption_scenario=s, mileage_case=mc, vehicle_years=r.vehicle_years, annual_km=km,
                             kwh_per_100km=r.kwh_per_100km, charging_efficiency=r.charging_efficiency,
                             annual_grid_energy_gwh=gwh, phase2_annual_grid_energy_gwh=r.annual_grid_energy_gwh,
                             annual_mwh=gwh * 1000))
    return pd.DataFrame(rows)


def build_shapes(**kw):
    res, chk = H.session_shapes("residential", **kw)
    wp, chk_wp = H.session_shapes("workplace")
    shapes = {"residential": res, "workplace": wp}
    for loc in ("public_ac", "public_dc"):
        shapes[loc] = {(dt, "unmanaged"): H.public_shape48(loc, dt) for dt in ("weekday", "weekend_holiday")}
    return shapes, {"residential": chk, "workplace": chk_wp}


def run(m, paths, weights) -> int:
    print("[13] Phase 3: hourly charging profiles 2030 ...")
    cal = H.calendar()
    targets = annual_energy_targets()
    targets.to_csv(C.TABLES / "hourly_annual_energy_targets_2030.csv", index=False)
    shapes, sess_checks = build_shapes()
    activity = {}
    for s in SCENS:
        _, traj = EX.run(paths[(SCEN_IN[s], "base")], m, "base", weights["base"], return_traj=True)
        activity[s] = H.daily_activity(traj)

    # ---- main profile set -------------------------------------------------------------------
    profiles = {}
    for _, t in targets.iterrows():
        for name, p, strat in CHARGING_CASES:
            profiles[(t.adoption_scenario, t.mileage_case, name)] = (
                p, H.build_profiles(t.annual_mwh, activity[t.adoption_scenario], C.LOCATION_MIX["base"], shapes, p, strat))

    base_cols = ["timestamp_local", "year", "month", "day_of_week", "hour", "is_weekend", "is_public_holiday_dated", "tnb_tou_period"]
    calx = cal[base_cols].copy()
    calx["timestamp_local"] = cal["timestamp_local"].dt.strftime("%Y-%m-%dT%H:%M:%S%z").str.replace(r"(\+\d\d)(\d\d)$", r"\1:\2", regex=True)

    agg_rows, det_rows, metr = [], [], []
    for (s, mc, name), (p, locs) in profiles.items():
        tot = sum(locs.values())
        a = calx.copy()
        a["adoption_scenario"], a["mileage_case"], a["charging_scenario"], a["participation_rate"] = s, mc, name, p
        a["charging_location"] = "all"
        a["hourly_energy_mwh"] = tot
        a["hourly_load_mw"] = tot
        a["normalized_hourly_weight"] = tot / tot.sum()
        agg_rows.append(a)
        if name in DETAIL_CASES:
            for loc, v in locs.items():
                b = calx.copy()
                b["adoption_scenario"], b["mileage_case"], b["charging_scenario"], b["participation_rate"] = s, mc, name, p
                b["charging_location"] = loc
                b["hourly_energy_mwh"] = v
                b["hourly_load_mw"] = v
                b["normalized_hourly_weight"] = v / tot.sum()
                det_rows.append(b)
        mt = H.metrics(tot, cal)
        mt.update(adoption_scenario=s, mileage_case=mc, charging_scenario=name, participation_rate=p, location_mix="base",
                  sensitivity="main")
        for loc, v in locs.items():
            mt[f"share_{loc}"] = v.sum() / tot.sum()
        metr.append(mt)
    agg = pd.concat(agg_rows, ignore_index=True)
    det = pd.concat(det_rows, ignore_index=True)
    for df in (agg, det):
        for c in ("hourly_energy_mwh", "hourly_load_mw"):
            df[c] = df[c].round(6)
        df["normalized_hourly_weight"] = df["normalized_hourly_weight"].round(12)
    agg.to_csv(C.TABLES / "leap_bev_hourly_load_2030_aggregated.csv", index=False)
    det.to_csv(C.TABLES / "leap_bev_hourly_load_2030.csv", index=False)

    # ---- sensitivities (20% xEV, base mileage) --------------------------------------------------
    t20 = targets[(targets.adoption_scenario == "20pct_xev") & (targets.mileage_case == "base_17969km")].iloc[0]
    sens_cases = []
    for mix in ("home_low", "home_high", "work_high"):
        sens_cases.append((f"location_mix_{mix}", dict(mix=C.LOCATION_MIX[mix])))
    sens_cases.append(("no_fleet_growth_flat_daily_activity", dict(activity=pd.Series(1.0, index=activity["20pct_xev"].index))))
    alt_shapes = {"home_arrival_plus_1h": build_shapes(arrival_shift_h=1)[0],
                  "home_session_20kwh": build_shapes(home_kwh_mean=20.0)[0]}
    for k in alt_shapes:
        sens_cases.append((k, dict(shapes=alt_shapes[k])))
    for label, kw in sens_cases:
        for name, p, strat in [("unmanaged", 0.0, "unmanaged"), ("managed_staggered_p50", 0.5, "staggered"),
                               ("managed_staggered_p100", 1.0, "staggered"), ("managed_synchronized_p100", 1.0, "synchronized")]:
            locs = H.build_profiles(t20.annual_mwh, kw.get("activity", activity["20pct_xev"]), kw.get("mix", C.LOCATION_MIX["base"]),
                                    kw.get("shapes", shapes), p, strat)
            tot = sum(locs.values())
            mt = H.metrics(tot, cal)
            mt.update(adoption_scenario="20pct_xev", mileage_case="base_17969km", charging_scenario=name, participation_rate=p,
                      location_mix=label.replace("location_mix_", "") if label.startswith("location_mix") else "base", sensitivity=label)
            for loc, v in locs.items():
                mt[f"share_{loc}"] = v.sum() / tot.sum()
            metr.append(mt)
    met = pd.DataFrame(metr)
    unm = met[(met.charging_scenario == "unmanaged")].set_index(["adoption_scenario", "mileage_case", "sensitivity"])
    met["energy_shifted_out_of_peak_gwh"] = [unm.loc[(r.adoption_scenario, r.mileage_case, r.sensitivity), "energy_tnb_peak_gwh"] - r.energy_tnb_peak_gwh
                                             for r in met.itertuples()]
    met["peak_change_vs_unmanaged_mw"] = [r.max_load_mw - unm.loc[(r.adoption_scenario, r.mileage_case, r.sensitivity), "max_load_mw"]
                                          for r in met.itertuples()]
    res_share = C.LOCATION_MIX["base"]["residential"]
    met["share_of_drivers_participating"] = met["participation_rate"]
    met["share_of_total_energy_under_management"] = met["participation_rate"] * met.get("share_residential", res_share)
    cols = ["sensitivity", "adoption_scenario", "mileage_case", "location_mix", "charging_scenario", "participation_rate",
            "share_of_drivers_participating", "share_of_total_energy_under_management", "annual_gwh", "max_load_mw",
            "max_load_timestamp", "max_load_weekday_mw", "max_load_weekend_holiday_mw", "max_load_weekday_tnb_peak_hours_mw", "avg_load_mw", "peak_to_average", "share_tnb_peak", "share_tnb_offpeak", "energy_tnb_peak_gwh",
            "energy_shifted_out_of_peak_gwh", "peak_change_vs_unmanaged_mw", "avg_daily_mwh_weekday", "avg_daily_mwh_weekend_holiday",
            "max_ramp_up_mw_per_h", "hour_of_max_ramp_up", "max_ramp_down_mw_per_h"] + [f"share_{l}" for l in C.LOCATIONS]
    met = met[cols]
    met.round(6).to_csv(C.TABLES / "charging_management_sensitivity_2030.csv", index=False)

    # ---- normalized 24-h profiles + source references -------------------------------------------
    rows = []
    basis = {"residential": "session simulation: Liu et al. 2024 plug-in/unplug timing (approx.), Malaysian charger-power and session-energy assumptions",
             "workplace": "session simulation: NREL workplace arrival/park/energy distributions (approx.), Malaysian 7.4/11 kW AC",
             "public_ac": "EVI-Pro Lite (US simulation, 30 C) public L2 shape, averaged over HA50/HA75/HA100 runs",
             "public_dc": f"EVI-Pro Lite (US simulation, 30 C) public DC shape, averaged, {C.DC_SMOOTH_HOURS}-h circular smoothing"}
    for loc, sh in shapes.items():
        for (dt, strat), v in sh.items():
            vv = H.fold24(v) if strat != "connected_share" else H.fold24(v)
            for hr in range(24):
                rows.append(dict(profile_type="model_input_shape", charging_location=loc, day_type=dt, strategy=strat,
                                 hour=hr, value=vv[hr], unit="share of daily location energy (24-h folded)" if strat != "connected_share"
                                 else "average share of the day's sessions connected", basis=basis[loc], measured_or_modelled="modelled"))
    ref = {
        ("Liu et al. 2024 Fig.10 plug-start (simulation)", "residential"): np.array(C.LIU2024_PLUG_START) / np.sum(C.LIU2024_PLUG_START),
        ("NREL workplace Fig.15 pre-COVID power (observed, approx. reading)", "workplace"): np.array(C.NREL_WP_FIG15_KW) / np.sum(C.NREL_WP_FIG15_KW),
    }
    for loc in C.LOCATIONS:
        ref[(f"EVI-Pro Lite weekday {loc} (simulation)", loc)] = H.evipro_profiles()[(loc, "weekday")]
    nrel_val, _ = H.session_shapes("workplace", power_mix=C.NREL_WP_POWER_MIX)
    ref[("Session model with NREL 3.3/6.6 kW mix (validation run)", "workplace")] = H.fold24(nrel_val[("weekday", "unmanaged")])
    for (name, loc), v in ref.items():
        for hr in range(24):
            rows.append(dict(profile_type="source_reference", charging_location=loc, day_type="weekday" if "weekday" in name or "Fig" in name or "validation" in name else "all",
                             strategy=name, hour=hr, value=v[hr], unit="share of daily energy / sessions",
                             basis=name, measured_or_modelled="observed (approx. digitised)" if "observed" in name else "modelled"))
    prof = pd.DataFrame(rows)
    prof.round(6).to_csv(C.TABLES / "normalized_charging_profiles.csv", index=False)

    # ---- location mix and sources -----------------------------------------------------------
    lm = []
    for k, v in C.LOCATION_MIX.items():
        for loc, s in v.items():
            lm.append(dict(mix_case=k, charging_location=loc, share_of_annual_charging_energy=s, total=sum(v.values()),
                           weekend_holiday_energy_factor=C.WEEKEND_ENERGY_FACTOR[loc],
                           tou_managed=loc in C.MANAGED_LOCATIONS,
                           status="scenario assumption (no Malaysian measured energy shares found)"))
    pd.DataFrame(lm).to_csv(C.TABLES / "charging_location_mix_assumptions.csv", index=False)
    pd.DataFrame(SOURCES).to_csv(C.TABLES / "charging_profile_sources.csv", index=False)

    # ---- LEAP import helpers ----------------------------------------------------------------
    keyp = {f"{s}__{name}": (sum(profiles[(s, 'base_17969km', name)][1].values())) for s in SCENS
            for name in ("unmanaged", "managed_staggered_p50", "managed_staggered_p100")}
    imp = calx[["timestamp_local", "month", "day_of_week", "hour", "tnb_tou_period"]].copy()
    imp.insert(0, "hour_of_year", np.arange(1, 8761))
    for k, v in keyp.items():
        imp[f"{k}__pct_of_annual_energy"] = (v / v.sum() * 100).round(9)
    imp.to_csv(C.TABLES / "leap_bev_hourly_shapes_2030.csv", index=False)
    ts = cal[["month", "hour", "behaviour_day_type"]].copy()
    tsl = []
    for k, v in keyp.items():
        g = ts.assign(mwh=v).groupby(["month", "behaviour_day_type", "hour"])["mwh"]
        d = pd.DataFrame({"hours_in_slice": g.size(), "energy_mwh": g.sum(), "avg_mw": g.mean(), "max_hourly_mw": g.max()}).reset_index()
        d["pct_of_annual_energy"] = d.energy_mwh / d.energy_mwh.sum() * 100
        d.insert(0, "profile", k)
        tsl.append(d)
    tsdf = pd.concat(tsl, ignore_index=True)
    tsdf.round(6).to_csv(C.TABLES / "leap_bev_timeslice_576_2030.csv", index=False)

    ctx = dict(cal=cal, targets=targets, profiles=profiles, agg=agg, det=det, met=met, shapes=shapes, sess_checks=sess_checks,
               activity=activity, imp=imp, tsdf=tsdf, prof=prof)
    import figures_hourly as FH
    import validation_hourly as VH
    print("      figures ...")
    FH.make_all(ctx)
    print("      validation ...")
    val = VH.run_checks(ctx)
    val.to_csv(C.TABLES / "phase3_validation_results.csv", index=False)
    VH.write_report(val, C.REPORTS / "phase_3_validation.md")
    n_fail = int((val.result == "FAIL").sum())
    print(val[["requirement", "result", "check"]].to_string(index=False))
    key = met[met.sensitivity == "main"].set_index(["adoption_scenario", "mileage_case", "charging_scenario"])[
        ["annual_gwh", "max_load_mw", "max_load_timestamp", "share_tnb_peak", "energy_shifted_out_of_peak_gwh"]].round(4)
    (C.TABLES / "phase3_key_results.json").write_text(json.dumps(
        {"|".join(k): v for k, v in key.to_dict(orient="index").items()} | {"validation_checks": len(val), "validation_failures": n_fail},
        indent=1), encoding="utf-8")
    LAST_CTX.update(ctx)
    return n_fail


SOURCES = [
    dict(id="H01", reference="NREL/NLR Workplace Charging Data (dataSet_Oct2021.csv)", country_period="USA (Golden, CO), Nov 2016-Jul 2021",
         setting="workplace", observed_or_modelled="observed sessions", bev_only="no: mixed BEV/PHEV (Leaf 41.9%, Volt 30.6% ...)",
         resolution="session level, timestamps MST", downloadable="NOT accessible on 2026-11-23: data.nlr.gov 'Temporarily Offline' (HTTP 503); S3 object AccessDenied; Wayback has redirects only",
         findings="(via companion report) arrivals peak 07:30-08:30; bimodal park duration ~3.5 h and ~8.5 h; mean 11.1 kWh, median 9.5 kWh delivered; >95% one plug-in per day; aggregate power peak 09:00",
         decision="adapt (distributions via companion report)", url="https://data.nlr.gov/submissions/182 ; https://data.openei.org/submissions/8237"),
    dict(id="H02", reference="Neuman, Meintz & Jun (2021) Workplace Charging Data Collection and Behavior, NREL/TP-5400-77515",
         country_period="USA, 56 months to 2021", setting="workplace", observed_or_modelled="observed (summary statistics and figures)",
         bev_only="no", resolution="figures: 30-min arrival bins; hourly average power", downloadable="PDF yes (OSTI); numbers only as figures",
         findings="Free (to May 2019) vs paid: paid sessions deliver more energy per session; COVID-19 sharply reduced users; distributions read approximately from Figs 7, 9, 15",
         decision="adapt workplace session model; validate (r=0.96 vs Fig 15 with NREL charger mix)", url="https://www.osti.gov/biblio/1832434/"),
    dict(id="H03", reference="Liu, Alexeenko, Bruchon, Zhang & Kisacikoglu (2024) Analyzing Residential Charging Demand for Light-Duty EVs in Colorado, IEEE ITEC (NREL/CP-5400-89286)",
         country_period="USA (Boulder, Aurora CO), 2030 projection; NHTS 2017 itineraries", setting="residential",
         observed_or_modelled="modelled (EVI-Pro uncontrolled) + two real-world CONTROLLED datasets for plug-time comparison",
         bev_only="no: light-duty EVs (BEV and PHEV via TEMPO)", resolution="one-week profiles; hourly plug-start/unplug histograms",
         downloadable="no numerical time series published; figures only", findings="plug-in peak 17:00-18:00 (simulation), controlled real-world 20:00-22:00; unplug peak 07:00; winter ambient penalty 1.602 (Jan) vs 1.059 (Jul); feeder peaks <1 to >4 MW in winter",
         decision="adapt (plug-in/unplug timing, approx. digitised); reject winter heating/seasonal scaling", url="https://docs.nlr.gov/docs/fy24osti/89286.pdf ; https://doi.org/10.1109/ITEC60657.2024.10598922"),
    dict(id="H04", reference="NREL EVI-Pro Lite daily load profile API (developer.nlr.gov), retrieved 2026-11-23",
         country_period="USA travel data; settings 30 C, 35 mi/day, BEV, 10,000 vehicles", setting="home, workplace, public L2, DC",
         observed_or_modelled="modelled", bev_only="yes (pev_type=BEV)", resolution="15-min, weekday and weekend",
         downloadable="yes (JSON saved in data/raw/literature/evipro_lite/)", findings="home peak 18:00-19:00; workplace 08:00-09:00; public L2 broad 09:00-19:00; DC midday; energy shares by home access: home 37-73%",
         decision="use for public AC/DC shapes (adapted); validate home/work", url="https://developer.nlr.gov/api/evi-pro-lite/v1/daily-load-profile"),
    dict(id="H05", reference="Smart & Salisbury (2015) Plugged In: How Americans Charge Their EVs, INL/EXT-15-35584",
         country_period="USA EV Project 2012-2013", setting="home and away", observed_or_modelled="observed", bev_only="no (Leaf, Volt)",
         resolution="aggregate statistics", downloadable="PDF yes", findings="84% (Leaf) / 87% (Volt) of charging events at home; all participants had home L2; Leaf 1.1 charges per driving day",
         decision="validate (location shares - events, not energy)", url="https://inldigitallibrary.inl.gov/sites/sti/sti/7323604.pdf"),
    dict(id="H06", reference="TNB - Time-of-Use: Giving Customers More Choice (ESG story) and myTNB tariff/ToU pages",
         country_period="Malaysia, from 1 Jul 2025", setting="tariff", observed_or_modelled="official policy", bev_only="n/a",
         resolution="hour-of-day", downloadable="web pages", findings="Peak 2 PM-10 PM Mon-Fri; off-peak otherwise; weekends and 15 named public holidays off-peak; opt-in via myTNB; ~217,000 customers switched Jul 2025-Jul 2026; domestic 28.52 vs 24.43 sen/kWh (<=1,500 kWh)",
         decision="use directly (ToU calendar); participation remains an assumption",
         url="https://www.tnb.com.my/sustainability/esg-stories-time-of-use-smart-energy-management ; https://www.mytnb.com.my/tariff"),
    dict(id="H07", reference="Umair et al. (2024) A Review of Malaysia's Current State and Future in EVs, JSDEWES 12(4) 1120522",
         country_period="Malaysia, to Dec 2023", setting="all", observed_or_modelled="secondary review (preference survey cited)", bev_only="n/a",
         resolution="-", downloadable="web", findings="60% of users prefer home charging, 29% public (attributed to Deloitte 2023; read from page summary, not verbatim); 1,500 charging stations end-2023; >70% under 29 kW",
         decision="validate direction of home share (preference, not energy)", url="https://www.sdewes.org/jsdewes/pid12.0522"),
    dict(id="H08", reference="Malaysian charge-point operators (DC Handal, Gentari, JomCharge, ChargeSini) and MEVnet",
         country_period="Malaysia 2025-2026", setting="public", observed_or_modelled="-", bev_only="-", resolution="-",
         downloadable="no public session/utilisation data found", findings="DC Handal: deployment/pricing news only; MEVnet: 5,839 public chargers incl. 1,971 DC (31 Mar 2026, secondary)",
         decision="reject for profiles (no data); request from operators", url="https://www.dchandal.com/"),
    dict(id="H09", reference="Baharin, Sulaima, Dahlan & Mokhlis (2024) Evaluation of the time-of-use tariff responsiveness for plug-in electric vehicle home charging in Malaysia, IJAAS 13(4):773-780, doi:10.11591/ijaas.v13.i4.pp773-780",
         country_period="Malaysia; household load data Sep-Oct 2021 (provided by TNB)", setting="residential (landed houses only)",
         observed_or_modelled="modelled: measured household base loads + ASSUMED EV charging (one Nissan Leaf 40 kWh, 6.6 kW, 20->100% SoC, ~7 h)",
         bev_only="yes (single BEV model)", resolution="hourly (24-h profiles, one month)",
         downloadable="PDF supplied by project owner 2026-11-23 (CC BY-SA); no EV time series - charging times are assumptions",
         findings="start times ASSUMED from 'Malaysian driving styles': 18:00 (arrive home after work), 22:00 (sleep time), 09:00 (stay home); daily / 2-day / 3-day / random charging; apartments and condominiums excluded (parking-lot chargers billed per service); hypothetical ToU structures S1-S4 (pre-July-2025 tariff), cheapest bills for 22:00 and 09:00 starts",
         decision="validate (Malaysian researcher assumptions support 18:00 arrival peak, ~7 kW home charging, 22:00 as the ToU-salient start time and condo access limits); not a measured charging profile",
         url="https://doi.org/10.11591/ijaas.v13.i4.pp773-780"),
    dict(id="H10", reference="NREL TEMPO / dsgrid light-duty charging profiles", country_period="USA county-level, 2020-2050",
         setting="household charging", observed_or_modelled="modelled", bev_only="no", resolution="hourly",
         downloadable="yes (OEDI, parquet; large)", findings="not downloaded - US county shapes add little beyond EVI-Pro Lite for Malaysia",
         decision="not used (documented alternative)", url="https://www.nrel.gov/analysis/dsgrid"),
]

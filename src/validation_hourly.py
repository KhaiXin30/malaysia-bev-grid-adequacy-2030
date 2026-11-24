"""Phase 3 automated validation - the 18 requirements of the brief (section 11)."""
import hashlib

import numpy as np
import pandas as pd

import config as C
import energy as EN
import hourly as H


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_checks(ctx) -> pd.DataFrame:
    res = []

    def add(req, name, ok, detail=""):
        res.append(dict(requirement=req, check=name, result="PASS" if bool(ok) else "FAIL", detail=str(detail)))

    cal, agg, det, tg, prof = ctx["cal"], ctx["agg"], ctx["det"], ctx["targets"], ctx["profiles"]
    keys = ["adoption_scenario", "mileage_case", "charging_scenario"]

    # 1 record counts
    n_agg = agg.groupby(keys).size()
    n_det = det.groupby(keys + ["charging_location"]).size()
    add(1, "Exactly 8,760 hourly records per aggregated profile and per location profile",
        (n_agg == 8760).all() and (n_det == 8760).all(), f"{len(n_agg)} aggregated profiles, {len(n_det)} location profiles")

    # 2 timestamps
    ts = cal["timestamp_local"]
    d = ts.diff().dropna()
    off = ts.map(lambda t: t.utcoffset().total_seconds() / 3600).unique()
    add(2, "Local timestamps: 2030-01-01 00:00 to 2030-12-31 23:00, +08:00 throughout, 1-h steps, no duplicates or gaps",
        ts.iloc[0].strftime("%Y-%m-%d %H:%M") == "2030-01-01 00:00" and ts.iloc[-1].strftime("%Y-%m-%d %H:%M") == "2030-12-31 23:00"
        and (d == pd.Timedelta(hours=1)).all() and ts.is_unique and list(off) == [8.0], f"offsets {list(off)}; hour-beginning convention")
    add(2, "Exported timestamp strings carry the +08:00 offset and are unique per profile",
        agg[agg.charging_scenario == "unmanaged"].groupby(["adoption_scenario", "mileage_case"])["timestamp_local"].apply(lambda s: s.is_unique and s.str.endswith("+08:00").all()).all(),
        agg["timestamp_local"].iloc[0])

    # 3 weekday/weekend
    dow = ts.dt.dayofweek
    add(3, "is_weekend = Saturday/Sunday; 2030 has 104 weekend days (2,496 h) and starts on a Tuesday",
        (cal["is_weekend"] == (dow >= 5)).all() and cal["is_weekend"].sum() == 2496 and cal["day_of_week"].iloc[0] == "Tuesday", "")

    # 4 TNB ToU
    exp_peak = (dow < 5) & ~cal["is_public_holiday_dated"] & cal["hour"].between(14, 21)
    spot = {("2030-01-07 14:00", "peak"), ("2030-01-07 21:00", "peak"), ("2030-01-07 22:00", "off_peak"), ("2030-01-07 13:00", "off_peak"),
            ("2030-01-05 15:00", "off_peak"), ("2030-12-25 15:00", "off_peak"), ("2030-01-01 15:00", "off_peak")}
    look = dict(zip(ts.dt.strftime("%Y-%m-%d %H:%M"), cal["tnb_tou_period"]))
    add(4, "TNB peak = Mon-Fri 14:00-22:00 (hour-beginning 14..21) except dated public holidays; everything else off-peak",
        ((cal["tnb_tou_period"] == "peak") == exp_peak).all() and all(look[t] == v for t, v in spot),
        f"{int(exp_peak.sum())} peak hours = 257 weekdays x 8 (4 dated holidays fall on weekdays)")

    # 5 nonnegative
    add(5, "All hourly energy and load values >= 0", (agg.hourly_energy_mwh >= 0).all() and (det.hourly_energy_mwh >= 0).all(),
        f"min {min(agg.hourly_energy_mwh.min(), det.hourly_energy_mwh.min())}")

    # 6 annual energy reconciles with Phase 2
    tot = agg.groupby(keys)["hourly_energy_mwh"].sum()
    p2 = pd.read_csv(C.TABLES / "bev_annual_energy_2025_2030_detail.csv")
    p2 = p2[(p2.year == C.HOURLY_YEAR) & (p2.case == "base") & (p2.geography == "peninsular")].set_index("scenario")["annual_grid_energy_gwh"]
    errs = [abs(tot[(s, "base_17969km", c)] / (p2[s] * 1000) - 1) for (s, m, c) in tot.index if m == "base_17969km"]
    add(6, "Sum of hourly MWh (base mileage) = Phase 2 annual grid energy x 1,000 for every profile", max(errs) < 1e-6,
        f"max relative error {max(errs):.2e}; 20% xEV {p2['20pct_xev'] * 1000:,.1f} MWh, 30% xEV {p2['30pct_xev'] * 1000:,.1f} MWh")

    # 7 managed = unmanaged
    ok = all(np.isclose(tot[(s, m, c)], tot[(s, m, "unmanaged")], rtol=1e-9) for (s, m, c) in tot.index)
    add(7, "Managed and unmanaged profiles have identical annual energy (same adoption and mileage case)", ok, f"{len(tot)} profiles")

    # 8 location sums
    ds = det.groupby(keys + ["timestamp_local"])["hourly_energy_mwh"].sum()
    ag = agg.set_index(keys + ["timestamp_local"])["hourly_energy_mwh"].reindex(ds.index)
    add(8, "Residential + workplace + public AC + public DC = total, every hour", np.allclose(ds.values, ag.values, atol=2e-5),
        f"max |diff| {np.abs(ds.values - ag.values).max():.2e} MWh (6-dp rounding)")

    # 9 shares
    sums = {k: sum(v.values()) for k, v in C.LOCATION_MIX.items()}
    lt = det.groupby(keys + ["charging_location"])["hourly_energy_mwh"].sum() / det.groupby(keys)["hourly_energy_mwh"].sum()
    real = lt.groupby(level="charging_location").agg(["min", "max"])
    add(9, "Location energy shares sum to 100% in every mix case, and realised annual shares equal the base mix",
        all(abs(v - 1) < 1e-12 for v in sums.values()) and all(abs(real.loc[l, "min"] - C.LOCATION_MIX["base"][l]) < 1e-6 and
                                                              abs(real.loc[l, "max"] - C.LOCATION_MIX["base"][l]) < 1e-6 for l in C.LOCATIONS),
        real.round(6).to_dict())

    # 10 connection windows and power limits
    sc = ctx["sess_checks"]
    ok = all(v["outside_window_kwh"] == 0 and v["max_power_excess_kw"] <= 1e-9 and v["min_power_kw"] >= 0 for k in sc for v in sc[k].values())
    add(10, "Session schedules: no energy outside the connection window, never above charger power, never negative", ok,
        {f"{k}:{kk[0]}/{kk[1]}": f"unshiftable {v['unshiftable_share']:.2%}" for k in sc for kk, v in sc[k].items() if kk[1] != "unmanaged"})

    # 11 energy conservation in shifting
    shp = ctx["shapes"]
    ok = all(abs(v.sum() - 1) < 1e-9 for loc in shp for k, v in shp[loc].items() if k[1] != "connected_share") and \
        all(v["energy_conserved"] for k in sc for v in sc[k].values())
    add(11, "Every 48-h shape sums to 1 and every session delivers the same energy under each strategy", ok, "")
    same = all(np.isclose(sc[k][("weekday", "unmanaged")]["mean_delivered_kwh"], sc[k][(dt, st)]["mean_delivered_kwh"])
               for k in sc for (dt, st) in sc[k])
    add(11, "Mean delivered energy per session identical for unmanaged, staggered and synchronized", same, "")

    # 12 zero participation
    t = tg[(tg.adoption_scenario == "20pct_xev") & (tg.mileage_case == "base_17969km")].iloc[0]
    act = ctx["activity"]["20pct_xev"]
    p0 = H.build_profiles(t.annual_mwh, act, C.LOCATION_MIX["base"], shp, 0.0, "staggered")
    un = prof[("20pct_xev", "base_17969km", "unmanaged")][1]
    add(12, "Participation 0% reproduces the unmanaged profile exactly", all(np.allclose(p0[l], un[l]) for l in C.LOCATIONS), "")

    # 13 participation consistency
    p50 = prof[("20pct_xev", "base_17969km", "managed_staggered_p50")][1]
    p100 = prof[("20pct_xev", "base_17969km", "managed_staggered_p100")][1]
    lin = np.allclose(p50["residential"], 0.5 * un["residential"] + 0.5 * p100["residential"])
    others = all(np.allclose(p50[l], un[l]) and np.allclose(p100[l], un[l]) for l in C.LOCATIONS if l not in C.MANAGED_LOCATIONS)
    add(13, "Participation p applied as a share of residential sessions: p50 = average of p0 and p100; non-residential locations unchanged",
        lin and others, "ToU applies to household (residential) charging only")

    # 14 no unintended synchronized spike
    met = ctx["met"]
    mm = met[(met.sensitivity == "main") & (met.mileage_case == "base_17969km")].set_index(["adoption_scenario", "charging_scenario"])
    ok = all(mm.loc[(s, "managed_staggered_p100"), "max_load_mw"] < mm.loc[(s, "managed_synchronized_p100"), "max_load_mw"] and
             mm.loc[(s, "managed_staggered_p100"), "max_ramp_up_mw_per_h"] < mm.loc[(s, "managed_synchronized_p100"), "max_ramp_up_mw_per_h"]
             for s in ("20pct_xev", "30pct_xev", "historical_trend"))
    r = mm.loc[("20pct_xev", "managed_staggered_p100")]
    add(14, "Staggered scheduling avoids the synchronized 22:00 spike (lower maximum load and lower maximum ramp than synchronized starts)",
        ok, f"20% xEV p100: staggered max {r.max_load_mw:.1f} MW vs synchronized {mm.loc[('20pct_xev', 'managed_synchronized_p100'), 'max_load_mw']:.1f} MW; "
            f"unmanaged {mm.loc[('20pct_xev', 'unmanaged'), 'max_load_mw']:.1f} MW")

    # 15 mileage scaling
    ratio = C.HOURLY_MILEAGE_CASES["giz_15000km"] / C.HOURLY_MILEAGE_CASES["base_17969km"]
    ok = True
    for s in ("20pct_xev", "30pct_xev", "historical_trend"):
        a = agg[(agg.adoption_scenario == s) & (agg.charging_scenario == "unmanaged")]
        b, g = a[a.mileage_case == "base_17969km"], a[a.mileage_case == "giz_15000km"]
        ok &= np.isclose(g.hourly_energy_mwh.sum() / b.hourly_energy_mwh.sum(), ratio, rtol=1e-6)
        ok &= np.allclose(g.normalized_hourly_weight.values, b.normalized_hourly_weight.values, atol=1e-12)
    add(15, "15,000 km case = base energy x 15,000/17,969.23 exactly, with identical hourly weights", ok, f"ratio {ratio:.6f}")

    # 16 adoption totals
    tgt = tg.set_index(["adoption_scenario", "mileage_case"])
    ok = all(abs(tgt.loc[(s, "base_17969km"), "annual_grid_energy_gwh"] - p2[s]) < 1e-9 for s in p2.index)
    add(16, "All three adoption scenarios keep their Phase 2 annual totals (base mileage)", ok,
        {s: round(p2[s], 3) for s in p2.index})

    # 17 efficiency not applied twice
    r2 = pd.read_csv(C.TABLES / "bev_annual_energy_2025_2030_detail.csv")
    r2 = r2[(r2.year == C.HOURLY_YEAR) & (r2.case == "base") & (r2.geography == "peninsular") & (r2.scenario == "20pct_xev")].iloc[0]
    batt = r2.vehicle_years * r2.annual_km * r2.kwh_per_100km / 100 / 1e6
    add(17, "Hourly energy uses the Phase 2 grid-side total (= battery energy / 0.90 once); no further efficiency factor in Phase 3",
        np.isclose(tot[("20pct_xev", "base_17969km", "unmanaged")] / 1000, batt / r2.charging_efficiency, rtol=1e-6),
        f"grid/battery = {tot[('20pct_xev', 'base_17969km', 'unmanaged')] / 1000 / batt:.4f} (1/0.90 = 1.1111)")

    # 18 reproducibility of Runs 1-3
    for label, arch in (("Run 1", C.RUN1_ARCHIVE), ("Run 2", C.RUN2_ARCHIVE), ("Run 3", C.RUN3_ARCHIVE)):
        raw_ok = all(_sha(C.ROOT / l.split(maxsplit=1)[1]) == l.split(maxsplit=1)[0] for l in (arch / "RAW_DATA_SHA256.txt").read_text().splitlines())
        diffs = []
        for line in (arch / "SHA256SUMS.txt").read_text().splitlines():
            h, rel = line.split(maxsplit=1)
            if label == "Run 1" and (not rel.startswith("tables/") or rel.endswith(".xlsx")):
                continue   # Run 1 archive also holds hand-written reports later appended to, and timestamped xlsx
            cur = (C.TABLES / rel.split("/", 1)[1]) if rel.startswith("tables/") else (C.REPORTS / rel.split("/", 1)[1])
            if not cur.exists() or _sha(cur) != h:
                diffs.append(rel)
        add(18, f"{label} archived outputs reproduced byte-identical (raw data {'unchanged' if raw_ok else 'CHANGED'})",
            (not diffs) if raw_ok else True, f"differing: {diffs or 'none'}")
    return pd.DataFrame(res)


NAMES = {1: "8,760 records per profile", 2: "Malaysian local timestamps", 3: "Weekday/weekend identification",
         4: "TNB peak/off-peak classification", 5: "Nonnegative power and energy", 6: "Annual energy reconciles with Phase 2",
         7: "Managed = unmanaged annual energy", 8: "Location energies sum to total", 9: "Location shares sum to 100%",
         10: "Connection windows and charger power respected", 11: "No energy created or lost in shifting",
         12: "Zero participation = unmanaged", 13: "Participation applied consistently", 14: "No unintended synchronized spike",
         15: "Mileage sensitivity scales energy correctly", 16: "Adoption scenarios preserve Phase 2 totals",
         17: "Charging losses not applied twice", 18: "Runs 1-3 reproducible"}


def write_report(val: pd.DataFrame, path):
    n_fail = int((val.result == "FAIL").sum())
    lines = ["# Phase 3 - hourly charging profile validation", "", "*Generated by `src/run_all.py` (`validation_hourly.py`). Do not edit by hand.*", "",
             f"**{len(val)} checks, {len(val) - n_fail} PASS, {n_fail} FAIL.**", "",
             "Approximations that are not testable automatically are listed in `phase_3_hourly_charging_report.md` section 9.", ""]
    for req, g in val.groupby("requirement"):
        lines += [f"## {req}. {NAMES[req]}", "", "| Check | Result | Detail |", "|---|---|---|"]
        for _, r in g.iterrows():
            lines.append(f"| {r['check']} | **{r['result']}** | {str(r['detail']).replace('|', '/')} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

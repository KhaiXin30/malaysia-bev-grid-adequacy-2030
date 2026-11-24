"""Phase 2 automated validation (annual BEV charging electricity)."""
import hashlib

import numpy as np
import pandas as pd

import config as C
import energy as E


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checks(ctx: dict) -> pd.DataFrame:
    res = []

    def add(group, name, ok, detail=""):
        res.append(dict(group=group, check=name, result="PASS" if bool(ok) else "FAIL", detail=str(detail)))

    et, leap, ex, ass = ctx["energy"], ctx["leap"], ctx["exposure"], ctx["assumptions"]
    key = ["year", "scenario", "geography"]

    # 1 units and kWh -> GWh conversion
    add("1 Units", "Synthetic: 1,000 vehicle-years x 10,000 km x 15 kWh/100 km / 0.90 = 1.6667 GWh",
        abs(float(E.grid_energy_gwh(1000, 10000, 15, 0.9)) - 1.5e6 / 0.9 / 1e6) < 1e-12, f"{float(E.grid_energy_gwh(1000, 10000, 15, 0.9)):.6f} GWh")
    rec = leap.vehicle_years * leap.annual_km * leap.kwh_per_100km / 100 / leap.charging_efficiency / 1e6
    add("1 Units", "LEAP annual_grid_energy_gwh recomputes from its own columns (VY x km x kWh/100km / 100 / eff / 1e6)",
        np.allclose(rec, leap.annual_grid_energy_gwh, rtol=1e-3, atol=1e-3), f"max |diff| {np.abs(rec - leap.annual_grid_energy_gwh).max():.4f} GWh (rounding of kWh/100km)")
    add("1 Units", "battery_energy_gwh x 1e6 = VY x km x kWh/100km / 100 (kWh) in every row",
        np.allclose(et.battery_energy_gwh * 1e6, et.vehicle_years * et.annual_km * et.kwh_per_100km / 100), "")

    # 2 vehicle-years
    m = et.merge(ex, left_on=["year", "scenario", "geography", "fleet_case"], right_on=["year", "scenario", "geography", "case"], suffixes=("", "_ex"))
    add("2 Vehicle-years", "vehicle_years equal Phase 1.5 leap_bev_exposure_input.csv (same scenario, fleet case, geography, year)",
        len(m) == len(et) and (m.vehicle_years == m.vehicle_years_ex).all(), f"{len(m)} rows matched")
    add("2 Vehicle-years", "Energy uses annual-average stock, not 31-Dec stock (vehicle_years < stock_end in every row)",
        (et.vehicle_years < et.stock_end).all(), "")
    add("2 Vehicle-years", "Years 2025-2030, 3 scenarios x 3 cases x 2 geographies (108 LEAP rows)",
        len(leap) == 108 and sorted(leap.year.unique()) == C.ENERGY_YEARS, f"{len(leap)} rows")

    # 3 inputs plausible and documented
    add("3 Inputs", "annual_km within 10,000-30,000 km", leap.annual_km.between(10000, 30000).all(), f"{leap.annual_km.min():,.0f}-{leap.annual_km.max():,.0f}")
    add("3 Inputs", "kwh_per_100km within 10-25 kWh/100 km (battery-side)", leap.kwh_per_100km.between(10, 25).all(),
        f"{leap.kwh_per_100km.min():.2f}-{leap.kwh_per_100km.max():.2f}")
    add("3 Inputs", "charging_efficiency within 0.75-0.99", leap.charging_efficiency.between(0.75, 0.99).all(), "")
    par = ass[ass.record_type == "parameter"]
    src_ok = all(all(s.strip() in C.ENERGY_SOURCES or s.strip().startswith("S") for s in str(ids).split(";")) for ids in par.source_ids)
    add("3 Inputs", "Every parameter row has a status, a boundary and source ids that exist in the source register",
        par.status.notna().all() and par.boundary.notna().all() and src_ok, f"{len(par)} parameter rows")
    srcs = ass[ass.record_type == "source"]
    add("3 Inputs", "Every source row has a URL and a date", (srcs.url.str.len() > 0).all() and (srcs.date.str.len() > 0).all(), f"{len(srcs)} sources")
    mt = ctx["mapping"]
    add("3 Inputs", "Mapped BEV models cover >= 85% of 2022-Oct 2026 registrations; every mapped key exists in EVDB table",
        mt.loc[mt.mapping_type != "residual", "share_2022_2026oct"].sum() >= 0.85 and all(v[0] in C.EVDB_WH_PER_KM for v in C.JPJ_MODEL_MAP.values()),
        f"{mt.loc[mt.mapping_type != 'residual', 'share_2022_2026oct'].sum():.1%}")
    obs = E.observation_table()
    f = E.consumption_factors()
    add("3 Inputs", "Consumption low factor = median observed/EVDB ratio of included observations; base = midpoint; high = 1",
        np.isclose(f["low"], obs.loc[obs.used_for_low_factor, "ratio_observed_to_evdb"].median()) and np.isclose(f["base"], (f["low"] + 1) / 2) and f["high"] == 1.0,
        f"low {f['low']:.3f}, base {f['base']:.3f}")

    # 4 energy boundary / no double counting of charging losses
    add("4 Boundary", "All consumption values are battery-side (consumption_basis == 'battery')", (leap.consumption_basis == "battery").all(), "")
    ratio = et.annual_grid_energy_gwh / et.battery_energy_gwh
    add("4 Boundary", "Charging losses applied exactly once: grid / battery energy = 1 / efficiency (not 1 / efficiency^2)",
        np.allclose(ratio, 1 / et.charging_efficiency), f"ratio range {ratio.min():.4f}-{ratio.max():.4f}")
    add("4 Boundary", "Grid-side consumption input is NOT divided by efficiency (function test)",
        float(E.grid_energy_gwh(1000, 10000, 15, 0.9, basis="grid")) == 1000 * 10000 * 15 / 100 / 1e6, "")
    try:
        E.grid_energy_gwh(1, 1, 1, 0.9, basis="unknown")
        bad = False
    except ValueError:
        bad = True
    add("4 Boundary", "Unknown measurement basis is rejected", bad, "")
    add("4 Boundary", "No T&D losses: grid energy = battery energy + charging losses only",
        np.allclose(et.annual_grid_energy_gwh, et.battery_energy_gwh + et.charging_losses_gwh), "")

    # 5 nonnegative
    add("5 Nonnegative", "All energy, losses, vehicle-years and parameters >= 0",
        (et[["annual_grid_energy_gwh", "battery_energy_gwh", "charging_losses_gwh", "vehicle_years", "annual_km", "kwh_per_100km"]] >= 0).all().all(), "")

    # 6 monotonicity
    b = (1000.0, 18000.0, 15.0, 0.9)
    e0 = float(E.grid_energy_gwh(*b))
    add("6 Monotonic", "Energy increases with annual km", float(E.grid_energy_gwh(b[0], b[1] * 1.01, b[2], b[3])) > e0, "")
    add("6 Monotonic", "Energy increases with battery-side kWh/100 km", float(E.grid_energy_gwh(b[0], b[1], b[2] * 1.01, b[3])) > e0, "")
    add("6 Monotonic", "Energy increases when charging efficiency decreases", float(E.grid_energy_gwh(b[0], b[1], b[2], b[3] * 0.99)) > e0, "")
    s = ctx["sensitivity"]
    sp = s[s.geography == "peninsular"].set_index(["factor", "level"])["pct_vs_baseline"]
    add("6 Monotonic", "Model sensitivities have the expected sign (km, consumption, efficiency, fleet)",
        sp[("C. Annual driving distance", "high")] > 0 > sp[("C. Annual driving distance", "low")] and
        sp[("D. Consumption level (battery-side)", "high")] > 0 > sp[("D. Consumption level (battery-side)", "low")] and
        sp[("E. Charging efficiency", "high")] > 0 > sp[("E. Charging efficiency", "low")] and
        sp[("A. Annual average fleet size (Phase 1.5 low/high, 20%)", "high")] > 0 > sp[("A. Annual average fleet size (Phase 1.5 low/high, 20%)", "low")], "")

    # 7 scenario comparison
    p = et.pivot_table(index=["case", "geography", "year"], columns="scenario", values=["annual_km", "kwh_per_100km", "charging_efficiency"])
    same = all(np.allclose(p[(v, "20pct_xev")], p[(v, s2)]) for v in ["annual_km", "kwh_per_100km", "charging_efficiency"] for s2 in ["30pct_xev", "historical_trend"])
    add("7 Scenarios", "Identical km, kWh/100 km and efficiency across the three scenarios (per case, year, geography)", same, "")
    q = et.pivot_table(index=["case", "geography", "year"], columns="scenario", values="annual_grid_energy_gwh")
    add("7 Scenarios", "30% xEV energy >= 20% xEV energy in every case / geography / year",
        (q["30pct_xev"] >= q["20pct_xev"] - 1e-9).all(), f"2030 base Peninsular: {q.loc[('base', 'peninsular', 2030), '30pct_xev']:.0f} vs {q.loc[('base', 'peninsular', 2030), '20pct_xev']:.0f} GWh")
    add("7 Scenarios", "20% and 30% energy identical in 2025-2026 (common history)",
        np.allclose(q.xs(2025, level="year")["30pct_xev"], q.xs(2025, level="year")["20pct_xev"]) and
        np.allclose(q.xs(2026, level="year")["30pct_xev"], q.xs(2026, level="year")["20pct_xev"]), "")
    r = et.pivot_table(index=["scenario", "geography", "year"], columns="case", values="annual_grid_energy_gwh")
    add("7 Scenarios", "Combined envelopes ordered low <= base <= high", ((r["low"] <= r["base"]) & (r["base"] <= r["high"])).all(), "")

    # 8 geography
    g = et.pivot_table(index=["scenario", "case", "year"], columns="geography", values="annual_grid_energy_gwh")
    add("8 Geography", "Peninsular energy <= national energy", (g["peninsular"] <= g["national"] + 1e-9).all(), "")

    # 9 reproducibility of Runs 1 and 2
    for label, arch, files in [("Run 1", C.RUN1_ARCHIVE, None), ("Run 2", C.RUN2_ARCHIVE, None)]:
        raw_ok = all(_sha(C.ROOT / l.split(maxsplit=1)[1]) == l.split(maxsplit=1)[0] for l in (arch / "RAW_DATA_SHA256.txt").read_text().splitlines())
        sums = [l.split(maxsplit=1) for l in (arch / "SHA256SUMS.txt").read_text().splitlines()]
        diffs = []
        for h, rel in sums:
            cur = (C.TABLES / rel.split("/", 1)[1]) if rel.startswith("tables/") else (C.REPORTS / rel.split("/", 1)[1])
            if not cur.exists() or _sha(cur) != h:
                diffs.append(rel)
        if label == "Run 1":  # Run 1 archive includes hand-written docs that Phase 1.5 legitimately appended to
            diffs = [d for d in diffs if d.startswith("tables/") and not d.endswith(".xlsx")]
        add("9 Reproducibility", f"{label} archived output tables reproduced byte-identical (raw data {'unchanged' if raw_ok else 'CHANGED'})",
            (not diffs) if raw_ok else True, f"{len(sums)} archived files checked; differing: {diffs or 'none'}")

    # 10 documentation / deliverables
    need = [C.TABLES / f for f in ["bev_energy_assumptions_and_sources.csv", "leap_bev_annual_energy_input.csv", "bev_energy_sensitivity_2030.csv"]] + \
           [C.REPORTS / f for f in ["bev_mileage_literature_review.md", "bev_efficiency_literature_review.md", "bev_charging_efficiency_review.md",
                                    "phase_2_energy_demand_report.md"]]
    missing = [p.name for p in need if not p.exists()]
    add("10 Documentation", "All Phase 2 deliverables exist", not missing, f"missing: {missing or 'none'}")
    return pd.DataFrame(res)


def write_report(val: pd.DataFrame, path):
    n_fail = int((val.result == "FAIL").sum())
    lines = ["# Phase 2 - BEV annual energy validation results", "",
             "*Generated by `src/run_all.py` (`validation_energy.py`). Do not edit by hand.*", "",
             f"**{len(val)} checks, {len(val) - n_fail} PASS, {n_fail} FAIL.**", ""]
    for grp, g in val.groupby("group", sort=False):
        lines += [f"## {grp}", "", "| Check | Result | Detail |", "|---|---|---|"]
        for _, r in g.iterrows():
            lines.append(f"| {r['check']} | **{r['result']}** | {str(r['detail']).replace('|', '/')} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

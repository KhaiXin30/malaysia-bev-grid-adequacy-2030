"""Phase 1.5 (Run 2) pipeline - called from run_all.py after the Run 1 steps, which it reuses unchanged.

Writes (outputs/tables): annual_bev_fleet_exposure_2025_2030.csv, leap_bev_exposure_input.csv,
leap_bev_exposure_data_dictionary.csv, fleet_exposure_sensitivity_2030.csv, exposure_vs_run1_reconciliation.csv,
exposure_timing_profile.csv, policy_path_review_2026_2030.csv, policy_path_review_summary.csv,
run2_change_log.csv, fleet_exposure_assumptions.csv, fleet_exposure_validation_results.csv,
phase15_key_results.json, BEV_fleet_exposure_summary.xlsx;  figures fig09-fig12;
reports/fleet_exposure_validation.md.
"""
import json

import pandas as pd

import config as C
import exposure as E
import figures_exposure as FX
import reporting as R
import validation_exposure as VX

STATUS = {2025: "observed registrations", 2026: "Jan-Oct observed + Nov-Dec estimated"}


def _change_log(comp: pd.DataFrame, sens: pd.DataFrame) -> pd.DataFrame:
    cl = pd.DataFrame(C.RUN2_CHANGES)
    base = comp[comp.timing == C.TIMING_BASE]
    q = {}
    b = base[(base.scenario == "policy_20pct") & (base.case == "base") & (base.year == C.FORECAST_END)].set_index("geography")
    q["C01"] = (f"2030 20% base: Peninsular average {b.loc['peninsular', 'stock_annual_average']:,.0f} vs 31-Dec "
                f"{b.loc['peninsular', 'stock_end']:,.0f}; national average {b.loc['national', 'stock_annual_average']:,.0f} vs 31-Dec "
                f"{b.loc['national', 'stock_end']:,.0f}")
    worst = base.loc[base["stock_end_pct_diff_vs_run1"].abs().idxmax()]
    q["C02"] = (f"31-Dec stock vs Run 1: 2030 20% base national {b.loc['national', 'stock_end']:,.0f} vs "
                f"{b.loc['national', 'run1_stock_end']:,.0f} ({b.loc['national', 'stock_end_pct_diff_vs_run1']:+.3%}); "
                f"largest difference anywhere {worst['stock_end_pct_diff_vs_run1']:+.3%} "
                f"({worst['scenario']}/{worst['case']}/{worst['geography']}/{int(worst['year'])})")
    s = sens[(sens.baseline_scenario == "20pct_xev") & (sens.geography == "peninsular") & (sens.factor != "baseline")]
    top = s.loc[s["delta_avg_vs_baseline"].abs().idxmax()]
    q["C03"] = f"Largest single effect on 2030 Peninsular average: {top['factor']} ({top['setting']}): {top['pct_avg_vs_baseline']:+.1%}"
    f = s[s.factor == "F. Policy denominator"].iloc[0]
    q["C04"] = f"MAA-TIV basis path changes 2030 Peninsular average stock by {f['pct_avg_vs_baseline']:+.1%} (2030 registrations +16.5%)"
    cl["quantified_impact_run2"] = cl["id"].map(q)
    return cl


def _assumptions_run2() -> pd.DataFrame:
    cols = ["id", "category", "item", "value", "unit", "status", "source_ids", "note"]
    reused = [a for a in C.ASSUMPTIONS if a[0] in ("A08", "A09", "A10", "A11", "A12", "A13", "A14")]
    df = pd.DataFrame(reused + C.ASSUMPTIONS_RUN2, columns=cols)
    df["run"] = ["Run 1 (reused unchanged)"] * len(reused) + ["Run 2 (new)"] * len(C.ASSUMPTIONS_RUN2)
    return df


def run(m, af, tc, pc, grid, fc, st, pen, paths, weights) -> int:
    print("[11] Phase 1.5: fleet exposure ...")
    expo = E.exposure_table(paths, weights, m)
    comp = E.method_comparison(paths, weights, m, st, pen)
    comp_out = comp[["timing", "scenario", "case", "geography", "year", "new_registrations", "stock_beginning", "stock_end",
                     "run1_stock_end", "stock_end_minus_run1", "stock_end_pct_diff_vs_run1", "stock_annual_average",
                     "avg_approx_mean_of_endpoints", "avg_approx_minus_cohort_integral"]].copy()
    comp_out["scenario"] = comp_out["scenario"].map(E.SCEN_OUT)
    comp_out.round(4).to_csv(C.TABLES / "exposure_vs_run1_reconciliation.csv", index=False)

    detail = expo.merge(comp[comp.timing == C.TIMING_BASE][["scenario", "case", "geography", "year", "run1_stock_end",
                                                            "stock_end_pct_diff_vs_run1"]], on=["scenario", "case", "geography", "year"])
    detail["scenario"] = detail["scenario"].map(E.SCEN_OUT)
    detail["registration_status"] = detail["year"].map(STATUS).fillna("projected")
    detail["geography_basis"] = detail["geography"].map({"national": "Malaysia, JPJ national registrations",
                                                         "peninsular": "ESTIMATE: national cohorts x Peninsular share (state-of-registration proxy)"})
    detail["peninsular_share_of_new_cohort"] = [weights[c].get(y, 1.0) if g == "peninsular" else 1.0
                                                for c, g, y in zip(detail["case"], detail["geography"], detail["year"])]
    cols = ["scenario", "case", "geography", "year", "registration_status", "new_registrations", "stock_beginning", "stock_end",
            "stock_annual_average", "vehicle_years", "vehicle_days", "days_in_year", "retirements", "avg_approx_mean_of_endpoints",
            "run1_stock_end", "stock_end_pct_diff_vs_run1", "survival_case", "peninsular_share_of_new_cohort", "timing", "geography_basis"]
    detail = detail[cols]
    detail.round(4).to_csv(C.TABLES / "annual_bev_fleet_exposure_2025_2030.csv", index=False)

    leap = E.leap_exposure(expo)
    leap.to_csv(C.TABLES / "leap_bev_exposure_input.csv", index=False)
    dd = E.data_dictionary()
    dd.to_csv(C.TABLES / "leap_bev_exposure_data_dictionary.csv", index=False)

    prof = E.seasonal_profile(m)
    pd.DataFrame({"month": prof.index, "seasonal_share_base": prof.values, "uniform_share": 1 / 12}).round(5).to_csv(
        C.TABLES / "exposure_timing_profile.csv", index=False)

    print("      sensitivity runs ...")
    sens = E.sensitivity_2030(af, grid, m, weights, paths)
    env = E.envelope_rows(expo)
    sens_out = pd.concat([sens, env], ignore_index=True)
    sens_out.round(4).to_csv(C.TABLES / "fleet_exposure_sensitivity_2030.csv", index=False)

    review = E.path_review(af, grid, tc, pc)
    review.round(6).to_csv(C.TABLES / "policy_path_review_2026_2030.csv", index=False)
    rsum = E.path_review_summary(review, af)
    rsum.round(6).to_csv(C.TABLES / "policy_path_review_summary.csv", index=False)

    cl = _change_log(comp, sens)
    cl.to_csv(C.TABLES / "run2_change_log.csv", index=False)
    ass = _assumptions_run2()
    ass.to_csv(C.TABLES / "fleet_exposure_assumptions.csv", index=False)

    print("      validation ...")
    ctx = dict(monthly=m, annual_full=af, paths=paths, weights=weights, expo=expo, comparison=comp, stock=st,
               pen_stock=pen, policy_grid=grid, leap=leap, forecast=fc, change_log=cl)
    val = VX.run_checks(ctx)
    val.to_csv(C.TABLES / "fleet_exposure_validation_results.csv", index=False)
    VX.write_report(val, C.REPORTS / "fleet_exposure_validation.md")
    n_fail = int((val.result == "FAIL").sum())
    print(val[["requirement", "result", "check"]].to_string(index=False))

    print("      figures ...")
    trajs = {}
    for scen in FX.ORDER:
        _, traj = E.run(paths[(scen, "base")], m, "base", weights["base"], return_traj=True)
        trajs[scen] = traj
    FX.fig_new_registrations(expo)
    FX.fig_eoy_vs_average(trajs, expo)
    FX.fig_scenario_comparison(expo)
    FX.fig_tornado(sens, env)

    readme = [
        "Phase 1.5 (Run 2) - passenger BEV fleet exposure, Malaysia and Peninsular Malaysia, 2025-2030.",
        "stock_annual_average = time-average active BEVs in the calendar year (use for annual energy); stock_end = 31 Dec.",
        "vehicle_years = integral of active stock over the year (1 vehicle-year = 1 vehicle active for a full calendar year).",
        "Scenarios: 20pct_xev (PRIMARY), 30pct_xev (SENSITIVITY), historical_trend (COMPARISON). Cases low/base/high are envelopes, NOT confidence intervals.",
        "Peninsular values are ESTIMATES (JPJ state-of-registration proxy), not an observed operating fleet.",
        "Run 1 outputs (BEV_forecast_summary.xlsx etc.) are unchanged; see Run2_Change_Log and Reconciliation_vs_Run1.",
    ]
    sheets = {"LEAP_Exposure_Input": leap, "Data_Dictionary": dd, "Exposure_Detail": detail.round(4),
              "Sensitivity_2030": sens_out.round(4), "Reconciliation_vs_Run1": comp_out.round(4),
              "Policy_Path_Review": review.round(6), "Path_Review_Summary": rsum.round(6), "Timing_Profile":
              pd.read_csv(C.TABLES / "exposure_timing_profile.csv"), "Assumptions_Run2": ass, "Run2_Change_Log": cl,
              "Validation": val}
    R.write_excel(C.TABLES / "BEV_fleet_exposure_summary.xlsx", sheets, readme)

    def pick(df, scen, case, geo, col, y=C.FORECAST_END):
        return int(round(df[(df.scenario == scen) & (df.case == case) & (df.geography == geo) & (df.year == y)][col].iloc[0]))

    key = {"stock_2030": {E.SCEN_OUT[s]: {geo: {c: {"end": pick(expo, s, c, geo, "stock_end"),
                                                     "average": pick(expo, s, c, geo, "stock_annual_average"),
                                                     "run1_end": pick(comp[comp.timing == C.TIMING_BASE], s, c, geo, "run1_stock_end")}
                                                 for c in ("low", "base", "high")} for geo in ("national", "peninsular")}
                          for s in E.SCEN_OUT},
           "validation_checks": len(val), "validation_failures": n_fail}
    (C.TABLES / "phase15_key_results.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key["stock_2030"]["20pct_xev"]["peninsular"], indent=1))
    return n_fail

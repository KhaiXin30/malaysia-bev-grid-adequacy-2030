"""Run the complete workflow:  python src/run_all.py

Steps: audit -> history -> market -> trend models -> policy scenarios -> stock -> Peninsular
       -> validation -> CSV / Excel / figures / summary   (Run 1, unchanged)
       -> Phase 1.5 fleet exposure: average stock, vehicle-years, sensitivity, validation  (Run 2, phase15.py)
       -> Phase 2 annual BEV charging electricity (GWh), sensitivity, validation           (Run 3, phase2.py)
       -> Phase 3 hourly 2030 charging profiles, unmanaged vs TNB-ToU managed              (Run 4, phase3.py)
       -> Phase 3.1 Industry-informed public AC destination profile (sensitivity)             (phase31.py)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import audit
import config as C
import figures
import geography
import history
import market
import phase15
import phase2
import phase3
import phase31
import policy
import reporting as R
import stock
import trend_models as T
import validation


def main():
    for d in (C.PROCESSED, C.TABLES, C.FIGURES, C.REPORTS):
        d.mkdir(parents=True, exist_ok=True)

    # ---- Step 1: audit ---------------------------------------------------------------
    print("[1] Auditing data ...")
    agg_audit = audit.audit_aggregate()
    tx_audit = audit.audit_transactions()
    phev = audit.phev_evidence()
    audit.write_audit_report(agg_audit, tx_audit, phev)
    agg_audit["series_continuity"].to_csv(C.TABLES / "data_audit_series_continuity.csv", index=False)
    tx_audit["reconciliation"].to_csv(C.TABLES / "data_audit_aggregate_vs_transactions.csv", index=False)
    phev.to_csv(C.TABLES / "phev_evidence_emas7_by_fuel_code.csv", index=False)
    audit.hybrid_top_models(2026).to_csv(C.TABLES / "hybrid_top_models_2026.csv", index=False)

    # ---- Step 2a: history -------------------------------------------------------------
    print("[2] Historical tables ...")
    m = history.monthly_table()
    af, rep, pinfo = history.annual_tables(m)
    m.reset_index().to_csv(C.PROCESSED / "car_registrations_monthly.csv", index=False)
    af.reset_index().rename(columns={"index": "year"}).to_csv(C.PROCESSED / "car_registrations_annual_2009_2026E.csv", index=False)
    rep_out = rep.copy()
    for c in ["total_cars", "bev", "hybrid", "xev_proxy"]:
        rep_out[c] = rep_out[c].round().astype(int)
    rep_out["geography"] = "Malaysia (national)"
    rep_out["measure"] = "JPJ new registrations (not sales), type 'car'"
    rep_out.round(6).to_csv(C.TABLES / "annual_registration_history.csv", index=False)
    seas = history.seasonality(m)
    seas.round(4).to_csv(C.TABLES / "seasonality_index_total_cars.csv", index=False)
    outl = history.monthly_outliers(m)
    outl.to_csv(C.TABLES / "monthly_bev_outliers.csv", index=False)

    # ---- Step 3: market ----------------------------------------------------------------
    print("[3] Market projection ...")
    mk = market.market_forecast(af)
    mk.to_csv(C.TABLES / "total_car_market_forecast.csv", index=False)
    jm = market.jpj_vs_maa(af)
    jm.round(4).to_csv(C.TABLES / "jpj_registrations_vs_maa_tiv.csv", index=False)

    # ---- Step 2b: trend models ---------------------------------------------------------
    print("[4] Trend models ...")
    tf = T.trend_forecasts(af, mk)
    tf.round(6).to_csv(C.TABLES / "trend_model_forecasts_all.csv", index=False)
    bt = T.backtests(af)
    bt.round(4).to_csv(C.TABLES / "trend_backtests.csv", index=False)
    bts = T.backtest_summary(bt)
    bts.round(4).to_csv(C.TABLES / "trend_backtest_summary.csv", index=False)
    sys_ = T.start_year_sensitivity(tf)
    sys_.to_csv(C.TABLES / "trend_start_year_sensitivity_2030.csv", index=False)
    tc = T.trend_case_table(tf, af)

    # ---- Step 4: policy ----------------------------------------------------------------
    print("[5] Policy scenarios ...")
    grid = policy.policy_grid(af, mk)
    grid.round(6).to_csv(C.TABLES / "policy_scenario_grid_full.csv", index=False)
    pc = policy.policy_case_table(grid)
    maa_x = policy.maa_basis_crosscheck(af)
    maa_x.to_csv(C.TABLES / "denominator_basis_crosscheck_2030.csv", index=False)
    fc = R.forecast_table(af, pc, tc)
    fc.to_csv(C.TABLES / "bev_forecast_2025_2030.csv", index=False)

    # ---- Step 5: stock -----------------------------------------------------------------
    print("[6] Cohort stock model ...")
    paths = stock.registration_paths(af, tc, pc)
    st = stock.stock_table(paths)
    st_out = R.stock_output(st)
    st_out.to_csv(C.TABLES / "bev_stock_2025_2030.csv", index=False)
    sens = stock.one_at_a_time_sensitivity(af, grid, mk)
    sens.round(0).to_csv(C.TABLES / "stock_sensitivity_2030.csv", index=False)
    surv_chk = stock.survival_plausibility_check(m)
    surv_chk.round(4).to_csv(C.TABLES / "survival_plausibility_check.csv", index=False)

    # ---- Step 6: Peninsular ------------------------------------------------------------
    print("[7] Peninsular Malaysia share ...")
    bd = geography.state_breakdown(C.FUEL_BEV, "bev")
    bd_all = geography.state_breakdown(None, "all_cars")
    pd.concat([bd, bd_all]).round(4).to_csv(C.TABLES / "peninsular_share_evidence_by_year.csv", index=False)
    w = geography.cohort_weights(bd)
    pd.DataFrame({k: v for k, v in w.items()}).rename_axis("cohort_year").round(4).reset_index().to_csv(
        C.TABLES / "peninsular_share_by_cohort.csv", index=False)
    pen = stock.stock_table(paths, weights_by_case=w)
    pen_out = R.peninsular_output(st, pen, bd, m)
    pen_out.to_csv(C.TABLES / "peninsular_bev_stock_2025_2030.csv", index=False)

    # ---- LEAP -------------------------------------------------------------------------
    leap, unc = R.leap_tables(st, pen)
    leap.to_csv(C.TABLES / "leap_bev_stock_input.csv", index=False)
    unc.to_csv(C.TABLES / "leap_bev_stock_uncertainty.csv", index=False)
    (C.TABLES / "leap_input_notes.md").write_text(R.LEAP_NOTE.format(
        g=C.MARKET_GROWTH["base"], bev_in_xev=af.loc[C.PARTIAL_YEAR, "bev_share_of_xev"],
        median=C.SURVIVAL["base"]["median_life"], pen=C.PEN_SHARE_FORECAST["base"],
        xev26=af.loc[C.PARTIAL_YEAR, "xev_share_of_cars"]), encoding="utf-8")

    # ---- Sources / cross-checks ---------------------------------------------------------
    ass = R.assumptions_table()
    ass.to_csv(C.TABLES / "assumptions_and_sources.csv", index=False)
    xc = R.crosscheck_table(m, af)
    xc.to_csv(C.TABLES / "crosscheck_2025_and_published_figures.csv", index=False)

    # ---- Step 7: validation -------------------------------------------------------------
    print("[8] Validation ...")
    ctx = dict(monthly=m, annual_full=af, annual_report=rep, partial_info=pinfo, audit=agg_audit, tx_audit=tx_audit,
               policy_grid=grid, trend_forecasts=tf, stock=st, pen_stock=pen, assumptions_table=ass)
    val = validation.run_checks(ctx)
    val.to_csv(C.TABLES / "validation_results.csv", index=False)
    n_fail = int((val["result"] == "FAIL").sum())
    print(val.to_string(index=False))

    # ---- Figures -------------------------------------------------------------------------
    print("[9] Figures ...")
    figures.fig_monthly(m)
    figures.fig_annual(af, rep)
    figures.fig_shares(af)
    figures.fig_models(af, tf)
    figures.fig_forecasts(af, fc)
    figures.fig_share_paths(af, grid, tc)
    figures.fig_stock(st, pen)
    figures.fig_peninsular_share(bd, bd_all)

    # ---- Excel ---------------------------------------------------------------------------
    print("[10] Excel workbook ...")
    readme = [
        "Passenger BEV Charging and Grid Adequacy in Peninsular Malaysia (2030) - BEV registration & stock forecast.",
        f"Data: JPJ registrations via data.gov.my, data to {pinfo['last_month']} (retrieved {C.RETRIEVAL_DATE}).",
        "Measures: JPJ NEW REGISTRATIONS (flow) of type 'car'; NOT MAA sales. Stock = active vehicles at 31 Dec (cohort x survival).",
        "2026 = Jan-Oct observed + Nov-Dec estimated ('partial_estimated'). 2027-2030 projected.",
        "Scenarios: policy_20pct (PRIMARY; NETR 20% xEV of new car sales by 2030), policy_30pct (SENSITIVITY; MITI 4 Feb 2026 statement), "
        "historical_trend (independent).",
        "xEV proxy = BEV + JPJ 'hybrid' (includes PHEV; HEV/PHEV not separable). BEV share of xEV is NOT the policy target.",
        "Peninsular values are ESTIMATES from the JPJ state-of-registration field (proxy; not operating location).",
        "Cases: low/base/high envelopes; see Assumptions sheet. All counts are vehicles.",
        "Sheets: Historical_Annual, Historical_Monthly, Market, Trend_Models, Trend_Backtests, Trend_StartYear, Forecast_BEV_Registrations, "
        "Policy_Grid, Stock_National, Stock_Peninsular, Peninsular_Evidence, LEAP_Input, LEAP_Uncertainty, Sensitivity_2030, "
        "Crosschecks, JPJ_vs_MAA, Survival_Check, Assumptions, Sources, Validation.",
    ]
    hist_m = m.loc["2015-01-01":].reset_index()
    hist_m["date"] = hist_m["date"].dt.strftime("%Y-%m")
    sheets = {
        "Historical_Annual": rep_out.round(6), "Historical_Monthly": hist_m.round(6), "Market": mk,
        "Trend_Models": tf[tf["fit_start"] == C.TREND_FIT_START].round(6), "Trend_Backtests": bt.round(4),
        "Trend_StartYear": sys_, "Forecast_BEV_Registrations": fc, "Policy_Grid": grid.round(6),
        "Stock_National": st_out, "Stock_Peninsular": pen_out, "Peninsular_Evidence": pd.concat([bd, bd_all]).round(4),
        "LEAP_Input": leap, "LEAP_Uncertainty": unc, "Sensitivity_2030": sens.round(0), "Crosschecks": xc,
        "JPJ_vs_MAA": jm.round(4), "Survival_Check": surv_chk.round(4), "Assumptions": ass[ass["record_type"] != "source"],
        "Sources": R.sources_table(), "Validation": val,
    }
    R.write_excel(C.TABLES / "BEV_forecast_summary.xlsx", sheets, readme)

    # ---- Key-results JSON (used by the report) -------------------------------------------
    def stock_at(df, scen, case, y=2030):
        return int(round(df[(df.scenario == scen) & (df.case == case) & (df.year == y)]["active_stock"].iloc[0]))

    def regs_at(scen, case, y=2030):
        return int(fc[(fc.scenario == scen) & (fc.case == case) & (fc.year == y)]["bev_registrations"].iloc[0])

    key = {
        "data_last_month": pinfo["last_month"],
        "bev_2025": int(af.loc[2025, "bev"]), "hybrid_2025": int(af.loc[2025, "hybrid"]),
        "cars_2025": int(af.loc[2025, "total_cars"]),
        "bev_2026_ytd": int(pinfo["ytd"]["bev"]), "hybrid_2026_ytd": int(pinfo["ytd"]["hybrid"]),
        "cars_2026_ytd": int(pinfo["ytd"]["total_cars"]), "bev_2026_est": int(af.loc[2026, "bev"]),
        "cars_2026_est": int(af.loc[2026, "total_cars"]),
        "bev_ytd_growth_vs_2025_same_months": float(pinfo["ytd"]["bev"] / pinfo["ytd_prev_year_same_months"]["bev"] - 1),
        "xev_share_2026_ytd": float(af.loc[2026, "xev_share_of_cars"]), "bev_share_2026_ytd": float(af.loc[2026, "bev_share_of_cars"]),
        "regs_2030": {s: {c: regs_at(s, c) for c in ["low", "base", "high"]} for s in ["historical_trend", "policy_20pct", "policy_30pct"]},
        "stock_2030_national": {s: {c: stock_at(st, s, c) for c in ["low", "base", "high"]} for s in ["historical_trend", "policy_20pct", "policy_30pct"]},
        "stock_2030_peninsular": {s: {c: stock_at(pen, s, c) for c in ["low", "base", "high"]} for s in ["historical_trend", "policy_20pct", "policy_30pct"]},
        "stock_2025_national_base": stock_at(st, "policy_20pct", "base", 2025),
        "validation_failures": n_fail,
    }
    (C.TABLES / "key_results.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key, indent=2))

    # ---- Phase 1.5 (Run 2): fleet exposure ----------------------------------------------------
    n_fail2 = phase15.run(m, af, tc, pc, grid, fc, st, pen, paths, w)

    # ---- Phase 2 (Run 3): annual charging electricity -----------------------------------------
    n_fail3 = phase2.run(af)

    # ---- Phase 3 (Run 4): hourly charging profiles ------------------------------------------------
    n_fail4 = phase3.run(m, paths, w)

    # ---- Phase 3.1: Industry-informed public AC destination profile (sensitivity; Phase 3 outputs untouched) ----
    n_fail5 = phase31.run(phase3.LAST_CTX)
    if n_fail or n_fail2 or n_fail3 or n_fail4 or n_fail5:
        print(f"WARNING: {n_fail} Run 1, {n_fail2} Phase 1.5, {n_fail3} Phase 2, {n_fail4} Phase 3 and {n_fail5} Phase 3.1 "
              "validation checks FAILED")
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()

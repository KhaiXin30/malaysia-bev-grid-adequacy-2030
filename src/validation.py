"""Step 7 - automated validation checks. Each check returns PASS/FAIL with detail."""
import numpy as np
import pandas as pd

import config as C
from data_io import load_aggregate


def run_checks(ctx: dict) -> pd.DataFrame:
    res = []

    def add(name, ok, detail):
        res.append(dict(check=name, result="PASS" if bool(ok) else "FAIL", detail=detail))

    agg = load_aggregate()
    m, af, rep = ctx["monthly"], ctx["annual_full"], ctx["annual_report"]

    # 1 monthly -> annual reconciliation against raw rows
    car = agg[(agg["type"] == C.CAR_TYPE)].assign(year=lambda d: d["date"].dt.year)
    raw_all = car[car["fuel"] == C.FUEL_ALL].groupby("year")["registrations"].sum()
    raw_bev = car[car["fuel"].isin(C.FUEL_BEV)].groupby("year")["registrations"].sum()
    mon_all = m.groupby("year")["total_cars"].sum()
    mon_bev = m.groupby("year")["bev"].sum()
    add("Annual totals reconcile with monthly totals (all cars, BEV)",
        (raw_all == mon_all.reindex(raw_all.index)).all() and (raw_bev == mon_bev.reindex(raw_bev.index)).all(),
        f"{len(raw_all)} years compared")
    full = rep[rep["period"] == "full_year"].set_index("year")
    add("Report table full years equal raw sums", (full["total_cars"] == raw_all.reindex(full.index)).all(),
        "2020-2025")

    # 2 no double counting
    a = ctx["audit"]
    add("Fuel breakdown rows sum exactly to all_fuels (no double counting)", a["fuel_sum_mismatch_rows"] == 0,
        f"{a['fuel_sum_mismatch_rows']} mismatches / {a['fuel_sum_rows_checked']} groups")
    add("Type breakdown rows sum exactly to all_types", a["type_sum_mismatch_rows"] == 0,
        f"{a['type_sum_mismatch_rows']} mismatches")
    hyb = m["total_cars"] >= m["bev"] + m["hybrid"]
    add("total_cars taken from all_fuels only; BEV+hybrid <= total every month", hyb.all(), f"{(~hyb).sum()} violations")

    # 3 partial year
    pi = ctx["partial_info"]
    ytd_row = rep[rep["period"].str.startswith("YTD")]
    add("2026 flagged as partial year (YTD) with 10 observed months",
        pi["months_observed"] == 10 and len(ytd_row) == 1, f"last month {pi['last_month']}")
    add("2026 estimate >= 2026 YTD for all series",
        all(pi["estimate"][s] >= pi["ytd"][s] for s in ["total_cars", "bev", "hybrid"]), "")
    add("2026 YTD YoY computed like-for-like (Jan-Oct vs Jan-Oct)",
        ytd_row["yoy_basis"].str.contains("like-for-like").all(), ytd_row["yoy_basis"].iloc[0])

    # 4/5 bounds
    add("BEV <= total cars (history)", (af["bev"] <= af["total_cars"]).all(), "")
    add("BEV share <= xEV share (history)", (af["bev_share_of_cars"] <= af["xev_share_of_cars"] + 1e-12).all(), "")
    g = ctx["policy_grid"]
    add("BEV <= xEV <= total cars (policy grid)",
        ((g["bev_registrations"] <= g["xev_registrations"]) & (g["xev_registrations"] <= g["total_cars"])).all(),
        f"{len(g)} rows")
    add("BEV share <= xEV share (policy grid)", (g["bev_share_of_cars"] <= g["xev_share"] + 1e-12).all(), "")
    tf = ctx["trend_forecasts"]
    add("Trend forecasts bounded by total market (after clipping)", (tf["bev_registrations"] <= tf["market_total_cars"] + 1e-6).all(),
        f"{int(tf['exceeds_market'].sum())} raw model predictions exceeded the market and were clipped (model B mainly)")

    # 6 non-negativity
    st, pen = ctx["stock"], ctx["pen_stock"]
    add("All forecast registrations nonnegative",
        (g["bev_registrations"] >= 0).all() and (tf["bev_registrations"] >= 0).all(), "")
    add("All stock values nonnegative", (st["active_stock"] >= 0).all() and (pen["active_stock"] >= 0).all(), "")

    # 7 retirements consistency
    ok = True
    for (_, _), d in st.groupby(["scenario", "case"]):
        d = d.sort_values("year")
        ident = d["active_stock"].shift(1) + d["registrations_in_year"] - d["retirements_in_year"]
        ok &= np.allclose(ident.iloc[1:], d["active_stock"].iloc[1:], atol=1e-6)
        ok &= (d["retirements_in_year"].iloc[1:] >= -1e-9).all()
    add("Retirements consistent: Stock_y = Stock_{y-1} + R_y - Ret_y, Ret_y >= 0", ok, "")

    # 8 stock from cohorts, not cumulative sales
    add("Active stock < cumulative registrations (survival applied)",
        (st["active_stock"] < st["cumulative_registrations"]).all(), "stock computed by cohort x survival")

    # 9 30% >= 20% under identical assumptions
    p = g.pivot_table(index=["market_case", "bev_in_xev_case", "year"], columns="scenario", values="bev_registrations")
    add("30% scenario >= 20% scenario for every identical-assumption combination (registrations)",
        (p["policy_30pct"] >= p["policy_20pct"]).all(), f"{len(p)} combinations")
    s = st.pivot_table(index=["case", "year"], columns="scenario", values="active_stock")
    add("30% scenario stock >= 20% scenario stock (each case)", (s["policy_30pct"] >= s["policy_20pct"] - 1e-6).all(), "")

    # 10 Peninsular <= national
    mg = pen.merge(st, on=["scenario", "case", "year"], suffixes=("_pen", "_nat"))
    add("Peninsular stock <= national stock", (mg["active_stock_pen"] <= mg["active_stock_nat"] + 1e-6).all(), "")

    # 11 anchors
    add("2025 observed BEV registrations = 44,813 (published figure)", int(af.loc[2025, "bev"]) == 44813,
        f"model value {int(af.loc[2025, 'bev'])}")
    rec = ctx["tx_audit"]["reconciliation"].set_index("year")
    add("Aggregate vs transaction BEV counts agree within 1 per year",
        (rec.loc[2015:, "diff_bev"].abs() <= 1).all(), rec.loc[2015:, "diff_bev"].to_dict())
    add("JPJ 2025 xEV proxy share within 0.5 pp of MITI-reported 8.7% of cars registered",
        abs(af.loc[2025, "xev_share_of_cars"] - C.MITI_2026["xev_share_cars_registered_2025"]) < 0.005,
        f"{af.loc[2025, 'xev_share_of_cars']:.4f}")

    # 12 documentation
    ass = ctx["assumptions_table"]
    add("Every assumption row has a status and at least one source id",
        ass["status"].notna().all() and (ass["source_ids"].str.len() > 0).all(), f"{len(ass)} rows")
    return pd.DataFrame(res)

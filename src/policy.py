"""Step 4 - policy-based forecasts.

New BEVs_y = Total new cars_y (JPJ registration basis, national)
             x xEV share_y (linear path from 2026 observed-estimate to 2030 target)
             x BEV share within xEV_y (low / base / high)
"""
import numpy as np
import pandas as pd

import config as C

CASE_COMBOS = {  # envelope definition used for stock outputs
    "low": {"market_case": "low", "bev_in_xev_case": "low"},
    "base": {"market_case": "base", "bev_in_xev_case": "base"},
    "high": {"market_case": "high", "bev_in_xev_case": "high"},
}


def _linear_path(v0: float, v1: float, y0: int, y1: int, years):
    return {y: v0 + (v1 - v0) * (y - y0) / (y1 - y0) for y in years}


def policy_grid(annual_full: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    """Full grid: scenario x market case x BEV-in-xEV case, years 2026-2030."""
    y0, y1 = C.PARTIAL_YEAR, C.FORECAST_END
    years = list(range(y0, y1 + 1))
    xev0 = annual_full.loc[y0, "xev_share_of_cars"]
    b0 = annual_full.loc[y0, "bev_share_of_xev"]
    rows = []
    for scen, target in C.POLICY_TARGETS.items():
        xev_path = _linear_path(xev0, target, y0, y1, years)
        for bcase, b_end in C.BEV_IN_XEV_2030.items():
            b_path = _linear_path(b0, b0 if b_end is None else b_end, y0, y1, years)
            for mcase in C.MARKET_GROWTH:
                mk = market[market["market_case"] == mcase].set_index("year")["total_cars"]
                for y in years:
                    total = mk.loc[y]
                    if y == y0:   # 2026: observed Jan-Oct + estimated Nov-Dec, common to all scenarios
                        xev_n, bev_n = annual_full.loc[y0, "xev_proxy"], annual_full.loc[y0, "bev"]
                        xs, bs = xev0, b0
                    else:
                        xs, bs = xev_path[y], b_path[y]
                        xev_n = total * xs
                        bev_n = xev_n * bs
                    rows.append(dict(scenario=scen, xev_target_2030=target, market_case=mcase,
                                     bev_in_xev_case=bcase, year=y, total_cars=round(total),
                                     xev_share=xs, xev_registrations=round(xev_n), bev_share_of_xev=bs,
                                     bev_registrations=round(bev_n), hybrid_registrations=round(xev_n - bev_n),
                                     bev_share_of_cars=bev_n / total,
                                     status="partial_estimated" if y == y0 else "projected"))
    return pd.DataFrame(rows)


def policy_case_table(grid: pd.DataFrame) -> pd.DataFrame:
    """Low/base/high envelope per scenario (see CASE_COMBOS)."""
    frames = []
    for case, combo in CASE_COMBOS.items():
        sel = grid[(grid["market_case"] == combo["market_case"]) & (grid["bev_in_xev_case"] == combo["bev_in_xev_case"])]
        frames.append(sel.assign(case=case))
    return pd.concat(frames, ignore_index=True)


def maa_basis_crosscheck(annual_full: pd.DataFrame) -> pd.DataFrame:
    """Sensitivity on the denominator basis: apply the targets to MAA TIV (sales) with the MAA
    BEV:xEV split, then show the JPJ/MAA BEV ratio needed to translate to registrations.
    MAA TIV 2026 = revised MAA forecast (800,000); 2027-2030 grow at base market growth."""
    g = C.MARKET_GROWTH["base"]
    tiv = {2026: C.MAA["tiv_2026_forecast_jul"]}
    for y in range(2027, C.FORECAST_END + 1):
        tiv[y] = tiv[y - 1] * (1 + g)
    maa_bev_share_xev_2025 = C.MAA["bev_2025"] / C.MAA["xev_2025"]
    jpj_over_maa_bev_2025 = annual_full.loc[2025, "bev"] / C.MAA["bev_2025"]
    rows = []
    for scen, target in C.POLICY_TARGETS.items():
        tiv30 = tiv[C.FORECAST_END]
        maa_bev = tiv30 * target * 0.5   # MAA's revised 2026 forecast splits xEV ~50:50 BEV:HEV
        rows.append(dict(scenario=scen, basis="MAA TIV (sales, PV+CV)", year=C.FORECAST_END, total_market=round(tiv30),
                         xev_share=target, bev_share_of_xev=0.5, bev_2030=round(maa_bev),
                         note=f"MAA 2025 BEV/xEV = {maa_bev_share_xev_2025:.3f}; MAA Jul-2026 forecast ~0.50"))
        rows.append(dict(scenario=scen, basis="MAA TIV basis x JPJ/MAA 2025 BEV ratio", year=C.FORECAST_END,
                         total_market=round(tiv30), xev_share=target, bev_share_of_xev=0.5,
                         bev_2030=round(maa_bev * jpj_over_maa_bev_2025),
                         note=f"JPJ/MAA BEV ratio 2025 = {jpj_over_maa_bev_2025:.3f} (non-MAA brands, timing, imports)"))
    return pd.DataFrame(rows)

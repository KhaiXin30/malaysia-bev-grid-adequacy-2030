"""Step 5 - cohort/survival conversion of annual registrations into end-of-year active stock.

Stock_y = sum_{c <= y} R_c * w_c * S(y - c + 0.5)
  R_c : registrations of cohort c (registered on average mid-year -> age y-c+0.5 at 31 Dec y)
  w_c : geographic weight (1 for national; Peninsular share for Peninsular stock)
  S   : Weibull survival  S(a) = exp(-(a/lambda)^k),  lambda = median / ln(2)^(1/k)
Retirements_y = Stock_{y-1} + R_y*w_y - Stock_y   (accounting identity, checked in validation)
"""
import numpy as np
import pandas as pd

import config as C


def survival(age, median_life: float, shape: float):
    lam = median_life / np.log(2) ** (1.0 / shape)
    age = np.maximum(np.asarray(age, dtype=float), 0.0)
    return np.exp(-(age / lam) ** shape)


def cohort_stock(regs: pd.Series, years, surv_case: str, weights: pd.Series = None) -> pd.DataFrame:
    p = C.SURVIVAL[surv_case]
    regs = regs.sort_index().astype(float)
    w = pd.Series(1.0, index=regs.index) if weights is None else weights.reindex(regs.index).astype(float)
    eff = regs * w
    rows = []
    prev = None
    for y in years:
        cohorts = eff[eff.index <= y]
        ages = y - cohorts.index.values + 0.5
        stock = float((cohorts.values * survival(ages, p["median_life"], p["shape"])).sum())
        cum = float(cohorts.sum())
        new = float(eff.get(y, 0.0))
        retire = (prev + new - stock) if prev is not None else np.nan
        rows.append(dict(year=y, registrations_in_year=new, cumulative_registrations=cum,
                         active_stock=stock, retirements_in_year=retire))
        prev = stock
    return pd.DataFrame(rows)


def registration_paths(annual_full: pd.DataFrame, trend_cases: pd.DataFrame, policy_cases: pd.DataFrame) -> dict:
    """{(scenario, case): pd.Series of BEV registrations by cohort year 2009..2030}."""
    hist = annual_full["bev"].loc[:C.PARTIAL_YEAR]          # 2009..2025 observed, 2026 estimated
    paths = {}
    for case in ["low", "base", "high"]:
        t = trend_cases[trend_cases["case"] == case].set_index("year")["bev_registrations"]
        paths[("historical_trend", case)] = pd.concat([hist, t.loc[C.PARTIAL_YEAR + 1:]])
        for scen in C.POLICY_TARGETS:
            pc = policy_cases[(policy_cases["scenario"] == scen) & (policy_cases["case"] == case)]
            s = pc.set_index("year")["bev_registrations"]
            paths[(scen, case)] = pd.concat([hist, s.loc[C.PARTIAL_YEAR + 1:]])
    return paths


def stock_table(paths: dict, weights_by_case: dict = None, years=None) -> pd.DataFrame:
    """Survival case follows the scenario case (low->low survival, etc.)."""
    years = years or list(range(2020, C.FORECAST_END + 1))
    frames = []
    for (scen, case), regs in paths.items():
        w = None if weights_by_case is None else weights_by_case[case]
        st = cohort_stock(regs, years, case, w)
        st.insert(0, "case", case)
        st.insert(0, "scenario", scen)
        st["survival_case"] = case
        frames.append(st)
    return pd.concat(frames, ignore_index=True)


def one_at_a_time_sensitivity(annual_full, grid, market) -> pd.DataFrame:
    """2030 national stock, policy_20pct: vary one assumption at a time from base."""
    hist = annual_full["bev"].loc[:C.PARTIAL_YEAR]
    rows = []

    def stock2030(scen, mcase, bcase, scase):
        s = grid[(grid["scenario"] == scen) & (grid["market_case"] == mcase) & (grid["bev_in_xev_case"] == bcase)]
        regs = pd.concat([hist, s.set_index("year")["bev_registrations"].loc[C.PARTIAL_YEAR + 1:]])
        return cohort_stock(regs, [C.FORECAST_END], scase)["active_stock"].iloc[0]

    for scen in C.POLICY_TARGETS:
        base = stock2030(scen, "base", "base", "base")
        rows.append(dict(scenario=scen, varied="none (base)", setting="base", stock_2030=base, delta_vs_base=0.0))
        for c in ["low", "high"]:
            for name, args in {"market growth": (c, "base", "base"),
                               "BEV share within xEV": ("base", c, "base"),
                               "survival": ("base", "base", c)}.items():
                v = stock2030(scen, *args)
                rows.append(dict(scenario=scen, varied=name, setting=c, stock_2030=v, delta_vs_base=v - base))
    return pd.DataFrame(rows)


def survival_plausibility_check(monthly: pd.DataFrame) -> pd.DataFrame:
    """Apply each survival curve to ALL car registrations Jan-2000..Sep-2026 and compare with the
    Ministry of Transport figure of ~16 million 'active' cars at 30 Sep 2026 (S12). Pre-2000
    cohorts are not in the data, so the modelled figure is a lower bound for the same curve.
    'Active' is undefined in the source -> weak plausibility check only, not a calibration."""
    ref = pd.Timestamp(C.MOT_ACTIVE_2026["reference_date"])
    m = monthly.loc[:"2026-09-01", "total_cars"]
    age = ((ref - (m.index + pd.Timedelta(days=15))).days / 365.25).values
    rows = []
    for case, p in C.SURVIVAL.items():
        st = float((m.values * survival(age, p["median_life"], p["shape"])).sum())
        rows.append(dict(survival_case=case, median_life=p["median_life"], shape=p["shape"],
                         modelled_active_cars_2000_2026_cohorts=round(st),
                         cumulative_car_registrations_2000_sep2026=int(m.sum()),
                         mot_reported_active_cars_approx=int(C.MOT_ACTIVE_2026["active_cars_approx"]),
                         ratio_model_to_reported=st / C.MOT_ACTIVE_2026["active_cars_approx"]))
    return pd.DataFrame(rows)

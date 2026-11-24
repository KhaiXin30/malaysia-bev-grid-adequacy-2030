"""Step 2 (part 2) - independent historical-trend forecasts of annual BEV registrations.

Models (fitted to annual data; 2026 = Jan-Oct observed + Nov-Dec estimated):
  A_linear_counts      : OLS of BEV registrations on year.
  B_exponential_counts : OLS of log(BEV registrations) on year (constant CAGR).
  C_logistic_share_K*  : logit(s/K) linear in year, s = BEV share of car registrations, K assumed.
  D_linear_share       : OLS of BEV share on year.
Share models are converted to counts with the total-market forecast.
"""
import numpy as np
import pandas as pd

import config as C

MODELS = ["A_linear_counts", "B_exponential_counts", "D_linear_share"] + \
         [f"C_logistic_share_{k}" for k in C.LOGISTIC_K]


def _ols(x, y):
    X = np.column_stack([np.ones_like(x, dtype=float), x.astype(float)])
    beta, *_ = np.linalg.lstsq(X, y.astype(float), rcond=None)
    return beta  # intercept, slope


def fit_predict(hist: pd.DataFrame, start: int, end: int, years, market: pd.Series) -> pd.DataFrame:
    """hist: annual table with total_cars, bev (index=year). market: total cars for `years`.
    Returns long table of predictions for `years` for all models."""
    h = hist.loc[start:end]
    x = h.index.values.astype(float)
    bev = h["bev"].values.astype(float)
    share = (h["bev"] / h["total_cars"]).values.astype(float)
    yrs = np.array(list(years), dtype=float)
    mk = market.reindex(list(years)).values.astype(float)
    out = []

    b = _ols(x, bev)
    out.append(("A_linear_counts", b[0] + b[1] * yrs, dict(slope_per_year=b[1])))

    b = _ols(x, np.log(bev))
    out.append(("B_exponential_counts", np.exp(b[0] + b[1] * yrs), dict(implied_cagr=np.exp(b[1]) - 1)))

    b = _ols(x, share)
    out.append(("D_linear_share", (b[0] + b[1] * yrs) * mk, dict(share_slope_pp_per_year=100 * b[1])))

    for name, K in C.LOGISTIC_K.items():
        z = np.log((share / K) / (1 - share / K))
        b = _ols(x, z)
        s_hat = K / (1 + np.exp(-(b[0] + b[1] * yrs)))
        out.append((f"C_logistic_share_{name}", s_hat * mk, dict(K=K, logistic_rate=b[1],
                                                                   midpoint_year=-b[0] / b[1])))
    rows = []
    for model, pred, params in out:
        for yr, p, m in zip(yrs.astype(int), pred, mk):
            raw = float(p)
            bounded = float(np.clip(raw, 0, m))
            rows.append(dict(model=model, fit_start=start, fit_end=end, year=yr, bev_raw=raw,
                             bev_registrations=bounded, market_total_cars=m, bev_share=bounded / m,
                             exceeds_market=raw > m, params=str({k: round(float(v), 4) for k, v in params.items()})))
    return pd.DataFrame(rows)


def trend_forecasts(annual_full: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    """Forecasts 2027-2030 for all models, all start years, all market cases."""
    frames = []
    years = range(C.PARTIAL_YEAR + 1, C.FORECAST_END + 1)
    for case in C.MARKET_GROWTH:
        mk = market[market["market_case"] == case].set_index("year")["total_cars"]
        for start in C.TREND_START_YEAR_SENS:
            f = fit_predict(annual_full, start, C.TREND_FIT_END, years, mk)
            f["market_case"] = case
            frames.append(f)
    return pd.concat(frames, ignore_index=True)


def backtests(annual_full: pd.DataFrame) -> pd.DataFrame:
    """Rolling-origin holdout tests. Share models use the ACTUAL market of the holdout year
    (isolates share-model error). Very small samples - illustrative only."""
    rows = []
    actual = annual_full["bev"]
    mk = annual_full["total_cars"]
    for start in C.TREND_START_YEAR_SENS:
        for origin in (2024, 2025):
            if origin - start + 1 < 3:
                continue
            hold = [y for y in range(origin + 1, C.PARTIAL_YEAR + 1)]
            f = fit_predict(annual_full, start, origin, hold, mk)
            for _, r in f.iterrows():
                a = actual.loc[r["year"]]
                rows.append(dict(model=r["model"], fit_start=start, fit_end=origin, n_fit_points=origin - start + 1,
                                 holdout_year=int(r["year"]), actual=a, predicted=r["bev_registrations"],
                                 pct_error=(r["bev_registrations"] - a) / a,
                                 holdout_note="2026 actual = Jan-Oct observed + Nov-Dec estimated" if r["year"] == 2026 else "observed"))
    return pd.DataFrame(rows)


def backtest_summary(bt: pd.DataFrame) -> pd.DataFrame:
    s = bt.assign(ape=bt["pct_error"].abs()).groupby(["model", "fit_start"]).agg(
        n_holdout_points=("ape", "size"), mape=("ape", "mean"), mean_pct_error=("pct_error", "mean")).reset_index()
    return s.sort_values(["fit_start", "mape"])


def start_year_sensitivity(tf: pd.DataFrame) -> pd.DataFrame:
    s = tf[(tf["year"] == C.FORECAST_END) & (tf["market_case"] == "base")]
    return s.pivot_table(index="model", columns="fit_start", values="bev_registrations").round(0).reset_index()


def trend_case_table(tf: pd.DataFrame, annual_full: pd.DataFrame) -> pd.DataFrame:
    """Low/base/high historical-trend case (TREND_CASE_MODELS, base fit window).
    All on the base market; cases differ by model structure (see config.TREND_CASE_MODELS)."""
    rows = []
    market_for = {"low": "base", "base": "base", "high": "base"}
    for case, model in C.TREND_CASE_MODELS.items():
        sel = tf[(tf["model"] == model) & (tf["fit_start"] == C.TREND_FIT_START) &
                 (tf["market_case"] == market_for[case])]
        for _, r in sel.iterrows():
            rows.append(dict(scenario="historical_trend", case=case, year=int(r["year"]), model=model,
                             market_case=market_for[case], total_cars=r["market_total_cars"],
                             bev_registrations=round(r["bev_registrations"]), bev_share_of_cars=r["bev_share"]))
    return pd.DataFrame(rows)

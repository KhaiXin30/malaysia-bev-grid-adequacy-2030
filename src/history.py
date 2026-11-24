"""Step 2 (part 1) - historical annual/monthly tables, partial-year handling, seasonality, outliers."""
import numpy as np
import pandas as pd

import config as C
from data_io import car_monthly_wide

SERIES = ["total_cars", "bev", "hybrid", "xev_proxy"]


def add_shares(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["bev_share_of_cars"] = df["bev"] / df["total_cars"]
    df["hybrid_share_of_cars"] = df["hybrid"] / df["total_cars"]
    df["xev_share_of_cars"] = df["xev_proxy"] / df["total_cars"]
    df["bev_share_of_xev"] = np.where(df["xev_proxy"] > 0, df["bev"] / df["xev_proxy"].replace(0, np.nan), np.nan)
    return df


def monthly_table() -> pd.DataFrame:
    m = car_monthly_wide()
    m = add_shares(m)
    m["year"] = m.index.year
    m["month"] = m.index.month
    return m


def novdec_ratio(m: pd.DataFrame) -> pd.Series:
    """(Nov+Dec)/(Jan..Oct) of total car registrations per complete year."""
    out = {}
    for y in C.NOVDEC_RATIO_YEARS:
        s = m[m["year"] == y]
        out[y] = s.loc[s["month"] >= 11, "total_cars"].sum() / s.loc[s["month"] <= 10, "total_cars"].sum()
    return pd.Series(out, name="novdec_over_janoct")


def annual_tables(m: pd.DataFrame):
    """Return (annual_full, annual_report, partial_info).

    annual_full   : index year (2009..2026); 2026 = Jan-Oct observed + Nov-Dec estimated.
    annual_report : rows 2020..2025 full years, 2026 YTD (Jan-Oct) and 2026 estimated, with YoY.
    """
    last = m.index.max()
    months_obs = int(last.month)
    annual = m.groupby("year")[SERIES].sum()
    n_months = m.groupby("year").size()
    py = C.PARTIAL_YEAR
    assert int(last.year) == py and months_obs < 12, "Partial-year logic assumes data end before December 2026"

    ytd = annual.loc[py].copy()
    ratios = novdec_ratio(m)
    r = ratios.mean()
    est_total_nd = ytd["total_cars"] * r
    bev_sh, hyb_sh = ytd["bev"] / ytd["total_cars"], ytd["hybrid"] / ytd["total_cars"]
    est = pd.Series({"total_cars": ytd["total_cars"] + est_total_nd,
                     "bev": ytd["bev"] + est_total_nd * bev_sh,
                     "hybrid": ytd["hybrid"] + est_total_nd * hyb_sh})
    est["xev_proxy"] = est["bev"] + est["hybrid"]
    est = est.round()

    annual_full = annual.astype(float).copy()
    annual_full.loc[py] = est
    annual_full = add_shares(annual_full)
    annual_full["status"] = np.where(annual_full.index == py, "partial_estimated", "observed_full_year")
    annual_full = annual_full.loc[2009:]

    # Report table
    rep = annual.loc[C.HIST_START:C.BASE_YEAR].astype(float).copy()
    rep["period"] = "full_year"
    rep["months_observed"] = n_months.loc[C.HIST_START:C.BASE_YEAR]
    y_row = ytd.to_frame().T.astype(float)
    y_row.index = [py]
    y_row["period"] = f"YTD_Jan-{last.strftime('%b')}"
    y_row["months_observed"] = months_obs
    e_row = est.to_frame().T
    e_row.index = [py]
    e_row["period"] = f"estimated_full_year (Jan-{last.strftime('%b')} observed + Nov-Dec estimated)"
    e_row["months_observed"] = months_obs
    rep = pd.concat([rep, y_row, e_row])
    rep = add_shares(rep)
    rep.index.name = "year"
    rep = rep.reset_index()

    # YoY: full years vs previous full year; YTD vs same months of previous year; estimate vs 2025.
    prev_ytd = m[(m["year"] == py - 1) & (m["month"] <= months_obs)][SERIES].sum()
    for s in ["total_cars", "bev", "hybrid", "xev_proxy"]:
        yoy = []
        basis = []
        for _, row in rep.iterrows():
            y = row["year"]
            if row["period"] == "full_year":
                pv = annual.loc[y - 1, s] if (y - 1) in annual.index else np.nan
                yoy.append(row[s] / pv - 1 if pv else np.nan)
                basis.append(f"vs full-year {y-1}")
            elif row["period"].startswith("YTD"):
                yoy.append(row[s] / prev_ytd[s] - 1 if prev_ytd[s] else np.nan)
                basis.append(f"vs Jan-{last.strftime('%b')} {py-1} (like-for-like)")
            else:
                pv = annual.loc[py - 1, s]
                yoy.append(row[s] / pv - 1)
                basis.append(f"estimate vs full-year {py-1}")
        rep[f"yoy_{s}"] = yoy
    rep["yoy_basis"] = basis
    partial_info = {"months_observed": months_obs, "last_month": last.strftime("%Y-%m"),
                    "novdec_ratios": ratios, "novdec_ratio_mean": r,
                    "ytd": ytd, "ytd_prev_year_same_months": prev_ytd, "estimate": est}
    return annual_full, rep, partial_info


def seasonality(m: pd.DataFrame) -> pd.DataFrame:
    """Monthly seasonal index of total car registrations (month mean / annual monthly mean)."""
    rows = []
    for label, years in {"2010-2019": range(2010, 2020), "2022-2025": range(2022, 2026)}.items():
        s = m[m["year"].isin(list(years))]
        idx = s.groupby(["year", "month"])["total_cars"].sum().unstack()
        idx = idx.div(idx.mean(axis=1), axis=0).mean()
        rows.append(idx.rename(label))
    return pd.concat(rows, axis=1).rename_axis("month").reset_index()


def monthly_outliers(m: pd.DataFrame, start="2022-01-01", threshold=0.35) -> pd.DataFrame:
    """Flag months whose BEV registrations deviate > threshold (log-ratio) from a centred
    5-month rolling median - a simple robust outlier screen."""
    s = m.loc[start:, "bev"].astype(float)
    med = s.rolling(5, center=True, min_periods=3).median()
    lr = np.log(s / med)
    out = pd.DataFrame({"bev": s, "rolling_median_5m": med.round(0), "log_ratio": lr.round(3)})
    out["flag"] = np.where(lr > threshold, "high", np.where(lr < -threshold, "low", ""))
    out = out[out["flag"] != ""]
    out.index = out.index.strftime("%Y-%m")
    return out.rename_axis("month").reset_index()

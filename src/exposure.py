"""Phase 1.5 (Run 2) - BEV fleet exposure: beginning-, end- and annual-average active stock,
vehicle-years and retirements, 2025-2030, national and Peninsular Malaysia.

Model (continuous time, daily resolution)
-----------------------------------------
Registrations are held as DAILY cohorts r_d (vehicles registered on day d). A vehicle enters the
fleet at the midpoint of its registration day and then survives with the Run 1 Weibull curve
S(a), a = age in years of 365.25 days. With w_c the Peninsular share of cohort year c (1 nationally):

    N(t)          = sum_{d : e_d <= t} r_d * w_{year(d)} * S(t - e_d)        active vehicles at time t
    stock_end_y   = N(24:00 on 31 Dec y);   stock_begin_y = stock_end_{y-1}
    VY_y          = integral over calendar year y of N(t) dt                  [vehicle-years]
    avg_y         = VY_y / T_y,  T_y = 1 calendar year (365 or 366 days)     [vehicles]
    retirements_y = stock_begin_y + new_y - stock_end_y                       [vehicles]

The integral is evaluated day by day. A vehicle contributes 0.5 day on its registration day (it
enters at midday) and S(k / 365.25) days on the k-th day after it; it contributes nothing before
registration. Both N at day ends and the vehicle-days are discrete convolutions of the daily
registration series with survival kernels.

Annual registration totals are exactly those of Run 1 (registration_paths); only their timing within
each year is refined (see config.TIMING_VARIANTS). 'annual_midyear' reproduces the Run 1 convention.
"""
from functools import lru_cache

import numpy as np
import pandas as pd

import config as C
from data_io import load_transactions
from stock import survival

DPY = C.DAYS_PER_YEAR
DAYS = pd.date_range(f"{C.EXPOSURE_START}-01-01", f"{C.FORECAST_END}-12-31", freq="D")
DAY_YEAR = DAYS.year.values
MONTHS = pd.date_range(DAYS[0], DAYS[-1], freq="MS")
TIMING_SHORT = {"seasonal": "seasonal forecast months (base)", "uniform_forecast": "uniform monthly forecast registrations",
                "history_uniform_within_month": "observed months uniform within month (ignore daily dates)",
                "annual_midyear": "Run 1 annual mid-year cohorts"}
G_FACTOR = {"uniform_forecast": "G1. Timing: uniform forecast months",
            "annual_midyear": "G2. Timing: Run 1 annual mid-year cohorts",
            "history_uniform_within_month": "G3. Timing: observed months uniform within month"}
SCEN_OUT = {"policy_20pct": "20pct_xev", "policy_30pct": "30pct_xev", "historical_trend": "historical_trend"}


# --------------------------------------------------------------------------------------
# Registration timing
# --------------------------------------------------------------------------------------
def seasonal_profile(monthly: pd.DataFrame) -> pd.Series:
    """Mean share of annual total car registrations falling in each calendar month (sums to 1)."""
    d = monthly[monthly["year"].isin(C.SEASONAL_PROFILE_YEARS)]
    share = d["total_cars"] / d.groupby("year")["total_cars"].transform("sum")
    prof = share.groupby(d["month"]).mean()
    return prof / prof.sum()


@lru_cache(maxsize=1)
def observed_daily_bev() -> pd.Series:
    """BEV registrations per calendar day from the transaction files (timing pattern only)."""
    tx = load_transactions()
    b = tx[tx["fuel"].isin(C.FUEL_BEV)]
    return b.groupby(b["date_reg"].dt.normalize()).size().astype(float)


def monthly_registrations(annual: pd.Series, monthly: pd.DataFrame, timing: str, prof: pd.Series) -> pd.Series:
    """Monthly BEV registrations (MS index) whose calendar-year sums equal `annual` exactly.
    Observed months use JPJ aggregate counts; the remainder of each year is spread by `timing`."""
    out = pd.Series(0.0, index=MONTHS)
    obs = monthly.loc[MONTHS[0]:, "bev"].astype(float)
    out.loc[obs.index] = obs.values
    last_obs = obs.index.max()
    for y in range(C.EXPOSURE_START, C.FORECAST_END + 1):
        months = pd.date_range(f"{y}-01-01", f"{y}-12-01", freq="MS")
        rem = [mm for mm in months if mm > last_obs]
        target = float(annual.get(y, 0.0))
        done = float(out.loc[[mm for mm in months if mm <= last_obs]].sum())
        if not rem:
            if abs(done - target) > 1e-6:
                raise ValueError(f"{y}: observed monthly sum {done} != annual {target}")
            continue
        remaining = target - done
        if remaining < -1e-6:
            raise ValueError(f"{y}: annual total {target} below observed months {done}")
        p = pd.Series(1.0, index=[mm.month for mm in rem]) if timing == "uniform_forecast" \
            else prof.loc[[mm.month for mm in rem]]
        out.loc[rem] = remaining * (p / p.sum()).values
    return out


def daily_registrations(monthly_regs: pd.Series, history_daily: bool = True) -> pd.Series:
    """Spread monthly counts over days: observed months by actual transaction dates (if
    history_daily), all other months uniformly over their days."""
    obs_daily = observed_daily_bev()
    last_obs = obs_daily.index.max().to_period("M").to_timestamp()
    out = pd.Series(0.0, index=DAYS)
    for ms, val in monthly_regs.items():
        if val == 0:
            continue
        days = pd.date_range(ms, ms + pd.offsets.MonthEnd(0), freq="D")
        if history_daily and ms <= last_obs:
            pat = obs_daily.reindex(days, fill_value=0.0)
            if pat.sum() > 0:
                out.loc[days] = val * (pat / pat.sum()).values
                continue
        out.loc[days] = val / len(days)
    return out


def midyear_registrations(annual: pd.Series) -> pd.Series:
    """Run 1 convention: the whole annual cohort is registered on the day containing mid-year."""
    out = pd.Series(0.0, index=DAYS)
    for y in range(C.EXPOSURE_START, C.FORECAST_END + 1):
        n = 366 if pd.Timestamp(f"{y}-12-31").dayofyear == 366 else 365
        out.loc[pd.Timestamp(f"{y}-01-01") + pd.Timedelta(days=n // 2)] = float(annual.get(y, 0.0))
    return out


def daily_path(annual: pd.Series, monthly: pd.DataFrame, timing: str = C.TIMING_BASE) -> pd.Series:
    if timing == "annual_midyear":
        return midyear_registrations(annual)
    prof = seasonal_profile(monthly)
    mreg = monthly_registrations(annual, monthly, "uniform_forecast" if timing == "uniform_forecast" else "seasonal", prof)
    return daily_registrations(mreg, history_daily=(timing != "history_uniform_within_month"))


# --------------------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------------------
def kernels(surv_case: str):
    p = C.SURVIVAL[surv_case]
    k = np.arange(len(DAYS), dtype=float)
    occ = survival(k / DPY, p["median_life"], p["shape"])        # vehicle-days on k-th day after registration
    occ[0] = 0.5 * survival(0.25 / DPY, p["median_life"], p["shape"])   # half a day on the registration day
    end = survival((k + 0.5) / DPY, p["median_life"], p["shape"])       # alive at end of k-th day
    return occ, end


def weight_vector(weights: pd.Series = None) -> np.ndarray:
    if weights is None:
        return np.ones(len(DAYS))
    return weights.reindex(DAY_YEAR).astype(float).values


def simulate(daily: pd.Series, surv_case: str, weights: pd.Series = None) -> pd.DataFrame:
    """Daily trajectory: registrations r, vehicle-days v, end-of-day stock n_end."""
    r = daily.reindex(DAYS).fillna(0.0).values * weight_vector(weights)
    occ, end = kernels(surv_case)
    n = len(r)
    v = np.convolve(r, occ)[:n]
    n_end = np.convolve(r, end)[:n]
    return pd.DataFrame({"date": DAYS, "year": DAY_YEAR, "registrations": r, "vehicle_days": v, "stock_end_of_day": n_end})


def annualise(traj: pd.DataFrame) -> pd.DataFrame:
    g = traj.groupby("year")
    a = pd.DataFrame({
        "new_registrations": g["registrations"].sum(),
        "stock_end": g["stock_end_of_day"].last(),
        "vehicle_days": g["vehicle_days"].sum(),
        "days_in_year": g.size().astype(int),
        "trajectory_min": g["stock_end_of_day"].min(),
        "trajectory_max": g["stock_end_of_day"].max(),
    })
    a["stock_beginning"] = a["stock_end"].shift(1).fillna(0.0)
    a["trajectory_min"] = np.minimum(a["trajectory_min"], a["stock_beginning"])
    a["trajectory_max"] = np.maximum(a["trajectory_max"], a["stock_beginning"])
    a["stock_annual_average"] = a["vehicle_days"] / a["days_in_year"]
    a["vehicle_years"] = a["stock_annual_average"] * 1.0           # T_y = 1 calendar year (A19)
    a["retirements"] = a["stock_beginning"] + a["new_registrations"] - a["stock_end"]
    a["avg_approx_mean_of_endpoints"] = (a["stock_beginning"] + a["stock_end"]) / 2
    a.index.name = "year"
    return a.reset_index()


def run(annual: pd.Series, monthly: pd.DataFrame, surv_case: str, weights: pd.Series = None,
        timing: str = C.TIMING_BASE, return_traj: bool = False):
    traj = simulate(daily_path(annual, monthly, timing), surv_case, weights)
    a = annualise(traj)
    return (a, traj) if return_traj else a


# --------------------------------------------------------------------------------------
# Scenario tables
# --------------------------------------------------------------------------------------
def exposure_table(paths: dict, weights_by_case: dict, monthly: pd.DataFrame, timing: str = C.TIMING_BASE,
                   years=None) -> pd.DataFrame:
    """All scenario x case x geography runs (survival and Peninsular share follow the case, as Run 1)."""
    years = years or C.EXPOSURE_YEARS
    frames = []
    for (scen, case), regs in paths.items():
        for geo, w in (("national", None), ("peninsular", weights_by_case[case])):
            a = run(regs, monthly, case, w, timing)
            a = a[a["year"].isin(years)].copy()
            a.insert(0, "geography", geo)
            a.insert(0, "case", case)
            a.insert(0, "scenario", scen)
            a["timing"] = timing
            a["survival_case"] = case
            frames.append(a)
    return pd.concat(frames, ignore_index=True)


def method_comparison(paths, weights_by_case, monthly, run1_nat: pd.DataFrame, run1_pen: pd.DataFrame) -> pd.DataFrame:
    """2025-2030 end-of-year and average stock under every timing variant + endpoint approximation,
    with the Run 1 end-of-year stock alongside."""
    frames = []
    for timing in C.TIMING_VARIANTS:
        t = exposure_table(paths, weights_by_case, monthly, timing)
        frames.append(t)
    allt = pd.concat(frames, ignore_index=True)
    r1 = pd.concat([run1_nat.assign(geography="national"), run1_pen.assign(geography="peninsular")])
    r1 = r1.rename(columns={"active_stock": "run1_stock_end"})[["scenario", "case", "geography", "year", "run1_stock_end"]]
    out = allt.merge(r1, on=["scenario", "case", "geography", "year"], how="left")
    out["stock_end_minus_run1"] = out["stock_end"] - out["run1_stock_end"]
    out["stock_end_pct_diff_vs_run1"] = out["stock_end_minus_run1"] / out["run1_stock_end"]
    out["avg_approx_minus_cohort_integral"] = out["avg_approx_mean_of_endpoints"] - out["stock_annual_average"]
    return out


# --------------------------------------------------------------------------------------
# Sensitivity (one at a time) around a policy baseline
# --------------------------------------------------------------------------------------
def maa_denominator_path(annual_full: pd.DataFrame, target: float) -> pd.Series:
    """JPJ-equivalent BEV registrations 2027-2030 if the target applies to MAA TIV (A17)."""
    g = C.MARKET_GROWTH["base"]
    y0 = C.PARTIAL_YEAR
    tiv0 = C.MAA["tiv_2026_forecast_jul"]
    xev0 = C.MAA["xev_2026_forecast_jul"] / tiv0
    ratio = annual_full.loc[C.BASE_YEAR, "bev"] / C.MAA["bev_2025"]
    out = {}
    for y in range(y0 + 1, C.FORECAST_END + 1):
        tiv = tiv0 * (1 + g) ** (y - y0)
        xs = xev0 + (target - xev0) * (y - y0) / (C.FORECAST_END - y0)
        out[y] = round(tiv * xs * C.MAA_BASIS_BEV_IN_XEV * ratio)
    return pd.Series(out, dtype=float)


def _policy_path(annual_full, grid, scen, mcase="base", bcase="base") -> pd.Series:
    hist = annual_full["bev"].loc[:C.PARTIAL_YEAR]
    s = grid[(grid["scenario"] == scen) & (grid["market_case"] == mcase) & (grid["bev_in_xev_case"] == bcase)]
    return pd.concat([hist, s.set_index("year")["bev_registrations"].loc[C.PARTIAL_YEAR + 1:]]).astype(float)


def pen_weights_variant(weights_by_case: dict, level: str, variant: str) -> pd.Series:
    if variant == "all_cohorts":
        return weights_by_case[level]
    w = weights_by_case["base"].copy()
    w.loc[w.index > C.PARTIAL_YEAR] = C.PEN_SHARE_FORECAST[level]
    return w


def sensitivity_2030(annual_full, grid, monthly, weights_by_case, paths, year=C.FORECAST_END) -> pd.DataFrame:
    rows = []

    def metrics(annual, surv="base", w_pen=None, timing=C.TIMING_BASE):
        out = {}
        for geo, w in (("national", None), ("peninsular", w_pen if w_pen is not None else weights_by_case["base"])):
            a = run(annual, monthly, surv, w, timing).set_index("year").loc[year]
            out[geo] = (a["stock_annual_average"], a["stock_end"], a["vehicle_years"])
        return out

    for base_scen in C.POLICY_TARGETS:
        other = [s for s in C.POLICY_TARGETS if s != base_scen][0]
        base_path = _policy_path(annual_full, grid, base_scen)
        variants = [("baseline", "-", "base", dict(annual=base_path))]
        variants.append(("A. xEV policy target", f"{int(C.POLICY_TARGETS[other]*100)}% target",
                         "high" if C.POLICY_TARGETS[other] > C.POLICY_TARGETS[base_scen] else "low",
                         dict(annual=_policy_path(annual_full, grid, other))))
        for lvl in ("low", "high"):
            b_end = C.BEV_IN_XEV_2030[lvl]
            variants.append(("B. BEV share within xEV", f"{lvl}: {b_end:.0%} in 2030", lvl,
                             dict(annual=_policy_path(annual_full, grid, base_scen, bcase=lvl))))
            variants.append(("C. Total market growth", f"{lvl}: {C.MARKET_GROWTH[lvl]:+.1%}/yr", lvl,
                             dict(annual=_policy_path(annual_full, grid, base_scen, mcase=lvl))))
            p = C.SURVIVAL[lvl]
            variants.append(("D. Vehicle survival", f"{lvl}: median {p['median_life']:.0f} y, k={p['shape']}", lvl,
                             dict(annual=base_path, surv=lvl)))
            for var in C.PEN_SENS_VARIANTS:
                lab = "E1. Peninsular share (all cohorts)" if var == "all_cohorts" else "E2. Peninsular share (2027-2030 cohorts only)"
                variants.append((lab, f"{lvl}: {C.PEN_SHARE_FORECAST[lvl]:.0%}", lvl,
                                 dict(annual=base_path, w_pen=pen_weights_variant(weights_by_case, lvl, var))))
        maa = pd.concat([base_path.loc[:C.PARTIAL_YEAR], maa_denominator_path(annual_full, C.POLICY_TARGETS[base_scen])])
        variants.append(("F. Policy denominator", "MAA TIV (sales) basis x JPJ/MAA BEV ratio", "alt", dict(annual=maa)))
        for timing in ("uniform_forecast", "annual_midyear", "history_uniform_within_month"):
            variants.append((G_FACTOR[timing], TIMING_SHORT[timing], timing, dict(annual=base_path, timing=timing)))
        base_m = None
        for factor, setting, level, kw in variants:
            mt = metrics(**kw)
            if factor == "baseline":
                base_m = mt
            for geo in ("national", "peninsular"):
                avg, eoy, vy = mt[geo]
                rows.append(dict(baseline_scenario=SCEN_OUT[base_scen], geography=geo, factor=factor, setting=setting,
                                 level=level, regs_2030=float(kw["annual"].loc[year]) * (1 if geo == "national" else np.nan),
                                 stock_annual_average_2030=avg, stock_end_2030=eoy, vehicle_years_2030=vy,
                                 delta_avg_vs_baseline=avg - base_m[geo][0],
                                 pct_avg_vs_baseline=(avg - base_m[geo][0]) / base_m[geo][0]))
    out = pd.DataFrame(rows)
    out.loc[(out["geography"] == "national") & out["factor"].str.startswith("E"), "note"] = "Peninsular share does not affect national values"
    return out


def envelope_rows(expo: pd.DataFrame, year=C.FORECAST_END) -> pd.DataFrame:
    """Combined low/base/high scenario envelopes (all-low / all-high combinations; not CIs)."""
    d = expo[expo["year"] == year]
    rows = []
    for (scen, geo), g in d.groupby(["scenario", "geography"]):
        g = g.set_index("case")
        rows.append(dict(baseline_scenario=SCEN_OUT[scen], geography=geo, factor="Combined envelope (not a CI)",
                         setting="low / base / high combinations", level="envelope",
                         stock_annual_average_2030=g.loc["base", "stock_annual_average"],
                         envelope_low=g.loc["low", "stock_annual_average"], envelope_high=g.loc["high", "stock_annual_average"],
                         stock_end_2030=g.loc["base", "stock_end"]))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Policy-path review (Task 5)
# --------------------------------------------------------------------------------------
def path_review(annual_full, grid, trend_cases, policy_cases) -> pd.DataFrame:
    rows = []
    hist = annual_full.loc[2022:C.PARTIAL_YEAR]
    for y, r in hist.iterrows():
        rows.append(dict(scenario="observed" if y <= C.BASE_YEAR else "observed+estimated", case="-", year=y,
                         total_cars=r["total_cars"], xev_share=r["xev_share_of_cars"], bev_share_of_xev=r["bev_share_of_xev"],
                         bev_share_of_cars=r["bev_share_of_cars"], bev_registrations=r["bev"], hybrid_registrations=r["hybrid"]))
    for _, r in policy_cases.iterrows():
        if r["year"] <= C.PARTIAL_YEAR:
            continue
        rows.append(dict(scenario=r["scenario"], case=r["case"], year=r["year"], total_cars=r["total_cars"],
                         xev_share=r["xev_share"], bev_share_of_xev=r["bev_share_of_xev"], bev_share_of_cars=r["bev_share_of_cars"],
                         bev_registrations=r["bev_registrations"], hybrid_registrations=r["hybrid_registrations"]))
    for _, r in trend_cases.iterrows():
        if r["year"] <= C.PARTIAL_YEAR:
            continue
        rows.append(dict(scenario="historical_trend", case=r["case"], year=r["year"], total_cars=r["total_cars"],
                         bev_share_of_cars=r["bev_registrations"] / r["total_cars"], bev_registrations=r["bev_registrations"]))
    df = pd.DataFrame(rows).sort_values(["scenario", "case", "year"]).reset_index(drop=True)
    b26 = annual_full.loc[C.PARTIAL_YEAR, "bev"]
    h26 = annual_full.loc[C.PARTIAL_YEAR, "hybrid"]
    df["bev_yoy"] = np.nan
    df["hybrid_yoy"] = np.nan
    for key, g in df.groupby(["scenario", "case"]):
        prev_b = g["bev_registrations"].shift(1)
        prev_h = g["hybrid_registrations"].shift(1)
        if key[0] not in ("observed", "observed+estimated"):
            prev_b.iloc[0], prev_h.iloc[0] = b26, h26
        df.loc[g.index, "bev_yoy"] = g["bev_registrations"] / prev_b - 1
        df.loc[g.index, "hybrid_yoy"] = g["hybrid_registrations"] / prev_h - 1
    # implied xEV share for the trend case if hybrids keep their 2026 share of cars
    hyb_share26 = annual_full.loc[C.PARTIAL_YEAR, "hybrid_share_of_cars"]
    tr = df["scenario"] == "historical_trend"
    df.loc[tr, "xev_share_if_hybrid_share_held_at_2026"] = df.loc[tr, "bev_share_of_cars"] + hyb_share26
    df.loc[tr, "note"] = "trend model projects BEVs only; xEV share shown assumes hybrid share of cars held at 2026 level"
    return df


def path_review_summary(review: pd.DataFrame, annual_full: pd.DataFrame) -> pd.DataFrame:
    b26 = annual_full.loc[C.PARTIAL_YEAR, "bev"]
    b22 = annual_full.loc[2022, "bev"]
    rows = [dict(scenario="observed", case="-", period="2022-2026E", bev_cagr=(b26 / b22) ** (1 / 4) - 1,
                 bev_2030=np.nan, bev_share_of_cars_2030=np.nan, xev_share_2030=np.nan)]
    for (s, c), g in review[review["year"] == C.FORECAST_END].groupby(["scenario", "case"]):
        if s.startswith("observed"):
            continue
        r = g.iloc[0]
        rows.append(dict(scenario=s, case=c, period="2026E-2030", bev_cagr=(r["bev_registrations"] / b26) ** (1 / 4) - 1,
                         bev_2030=r["bev_registrations"], bev_share_of_cars_2030=r["bev_share_of_cars"],
                         xev_share_2030=r["xev_share"] if pd.notna(r["xev_share"]) else r.get("xev_share_if_hybrid_share_held_at_2026")))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# LEAP export
# --------------------------------------------------------------------------------------
LEAP_COLS = ["year", "scenario", "case", "geography", "new_registrations", "stock_beginning", "stock_end",
             "stock_annual_average", "vehicle_years", "retirements"]


def leap_exposure(expo: pd.DataFrame) -> pd.DataFrame:
    d = expo.copy()
    d["scenario"] = d["scenario"].map(SCEN_OUT)
    d = d[LEAP_COLS].copy()
    for c in LEAP_COLS[4:]:
        d[c] = d[c].round(0).astype(int)
    order = {"20pct_xev": 0, "30pct_xev": 1, "historical_trend": 2}
    d = d.sort_values(["scenario", "case", "geography", "year"], key=lambda s: s.map(order) if s.name == "scenario"
                      else (s.map({"low": 0, "base": 1, "high": 2}) if s.name == "case" else s)).reset_index(drop=True)
    return d


DATA_DICTIONARY = [
    ("year", "integer", "calendar year", "Calendar year 2025-2030 (2025 observed registrations; 2026 = Jan-Oct observed + Nov-Dec estimated; 2027-2030 projected)."),
    ("scenario", "text", "-", "20pct_xev = NETR 20% xEV target (PRIMARY); 30pct_xev = 30% xEV (SENSITIVITY, MITI 4 Feb 2026 statement); historical_trend = independent trend (COMPARISON)."),
    ("case", "text", "-", "low / base / high combined assumption envelope (market growth, BEV share within xEV, survival, Peninsular share move together). Not a statistical confidence interval."),
    ("geography", "text", "-", "national = Malaysia; peninsular = Peninsular Malaysia ESTIMATE (JPJ state-of-registration proxy x cohort share; not an observed operating fleet)."),
    ("new_registrations", "number", "vehicles per year", "New passenger BEV registrations (JPJ basis) in the calendar year. National: observed (2025), observed+estimated (2026), projected (2027+). Peninsular: ESTIMATED = national registrations x Peninsular share of that cohort year."),
    ("stock_beginning", "number", "vehicles", "Active BEVs at 00:00 on 1 January (= stock_end of the previous year)."),
    ("stock_end", "number", "vehicles", "Active BEVs at 24:00 on 31 December (daily cohort x Weibull survival). Differs slightly from the Run 1 31-Dec stock because registration timing is monthly/daily rather than mid-year; see exposure_vs_run1_reconciliation.csv."),
    ("stock_annual_average", "number", "vehicles", "Time-average number of active BEVs over the calendar year = (1/T_y) x integral of N(t) dt. USE THIS (not stock_end) for annual energy demand."),
    ("vehicle_years", "number", "vehicle-years", "Integral of N(t) over the calendar year; 1 vehicle-year = one vehicle active for a full calendar year, so numerically equal to stock_annual_average."),
    ("retirements", "number", "vehicles per year", "Vehicles leaving the active fleet during the year (scrappage/deregistration/export), from survival; = stock_beginning + new_registrations - stock_end. In the LEAP file each column is rounded to whole vehicles independently, so this identity can differ by +/-1 there (exact in annual_bev_fleet_exposure_2025_2030.csv)."),
]


def data_dictionary() -> pd.DataFrame:
    return pd.DataFrame(DATA_DICTIONARY, columns=["column", "type", "unit", "definition"])

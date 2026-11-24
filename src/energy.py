"""Phase 2 (Run 3) - annual electricity drawn from the grid for passenger BEV charging, 2025-2030.

    E_grid,y [GWh] = VY_y x km x c_y / 100 / eta / 1e6          (c_y battery-side kWh/100 km)
    E_grid,y [GWh] = VY_y x km x c_y / 100 / 1e6                (if c_y were already grid-side)

VY_y  : vehicle-years (= annual-average active BEVs) from Phase 1.5 (leap_bev_exposure_input.csv)
km    : annual km per active vehicle (config.ANNUAL_KM)
c_y   : fleet-average battery-side consumption in year y = case factor x fleet-weighted EV Database
        'Vehicle' consumption of the BEV models in the active fleet (JPJ model mix by cohort x survival)
eta   : grid-to-battery charging efficiency (config.CHARGING_EFFICIENCY); excludes T&D losses
"""
from functools import lru_cache

import numpy as np
import pandas as pd

import config as C
from data_io import load_transactions
from stock import survival

SCEN_ORDER = {"20pct_xev": 0, "30pct_xev": 1, "historical_trend": 2}
CASE_ORDER = {"low": 0, "base": 1, "high": 2}


# --------------------------------------------------------------------------------------
# Core formula
# --------------------------------------------------------------------------------------
def grid_energy_gwh(vehicle_years, annual_km, kwh_per_100km, charging_efficiency, basis=C.ENERGY_BASIS):
    """Grid-side annual energy in GWh. Charging efficiency is applied only to battery-side consumption."""
    kwh = np.asarray(vehicle_years, float) * np.asarray(annual_km, float) * np.asarray(kwh_per_100km, float) / 100.0
    if basis == "battery":
        kwh = kwh / np.asarray(charging_efficiency, float)
    elif basis != "grid":
        raise ValueError(f"unknown consumption basis {basis!r}")
    return kwh / 1e6


# --------------------------------------------------------------------------------------
# Model mix and fleet-weighted consumption
# --------------------------------------------------------------------------------------
def evdb_kwh_per_100km() -> pd.Series:
    return pd.Series({k: float(np.mean(v)) / 10.0 for k, v in C.EVDB_WH_PER_KM.items()})


@lru_cache(maxsize=1)
def bev_model_counts() -> pd.DataFrame:
    tx = load_transactions()
    b = tx[tx["fuel"].isin(C.FUEL_BEV)]
    return b.groupby(["year", "maker", "model"]).size().rename("n").reset_index()


def model_mapping_table() -> pd.DataFrame:
    cnt = bev_model_counts()
    ev = evdb_kwh_per_100km()
    t = cnt[cnt.year >= 2022].groupby(["maker", "model"])["n"].sum().rename("registrations_2022_2026oct").reset_index()
    t["registrations_2025_2026oct"] = t.apply(lambda r: int(cnt[(cnt.year >= 2025) & (cnt.maker == r.maker) & (cnt.model == r.model)]["n"].sum()), axis=1)
    keys = [C.JPJ_MODEL_MAP.get((a, b)) for a, b in zip(t.maker, t.model)]
    t["evdb_reference"] = [k[0] if k else "residual (fleet-weighted mean of mapped models)" for k in keys]
    t["mapping_type"] = [k[1] if k else "residual" for k in keys]
    t["evdb_kwh_per_100km_battery"] = [ev[k[0]] if k else np.nan for k in keys]
    mapped = t["evdb_kwh_per_100km_battery"].notna()
    resid = np.average(t.loc[mapped, "evdb_kwh_per_100km_battery"], weights=t.loc[mapped, "registrations_2022_2026oct"])
    t.loc[~mapped, "evdb_kwh_per_100km_battery"] = resid
    t = t.sort_values("registrations_2022_2026oct", ascending=False).reset_index(drop=True)
    t["share_2022_2026oct"] = t["registrations_2022_2026oct"] / t["registrations_2022_2026oct"].sum()
    return t


def _value_lookup():
    mt = model_mapping_table()
    return {(a, b): v for a, b, v in zip(mt.maker, mt.model, mt.evdb_kwh_per_100km_battery)}, \
        float(mt.loc[mt.mapping_type == "residual", "evdb_kwh_per_100km_battery"].iloc[0]) if (mt.mapping_type == "residual").any() else np.nan


def mix_consumption(y0: int, y1: int) -> float:
    """Registration-weighted EVDB consumption (kWh/100 km, battery) of BEVs registered y0..y1."""
    cnt = bev_model_counts()
    look, resid = _value_lookup()
    d = cnt[(cnt.year >= y0) & (cnt.year <= y1)]
    v = np.array([look.get((a, b), resid) for a, b in zip(d.maker, d.model)])
    return float(np.average(v, weights=d.n))


def cohort_consumption(mix: str) -> pd.Series:
    """EVDB-basis consumption by cohort year: observed mix for cohorts with transaction data (to 2026),
    the chosen MIX_WINDOWS mix for 2027-2030 cohorts."""
    cnt = bev_model_counts()
    look, resid = _value_lookup()
    out = {}
    for y, d in cnt.groupby("year"):
        if y > C.PARTIAL_YEAR:
            continue
        v = np.array([look.get((a, b), resid) for a, b in zip(d.maker, d.model)])
        out[int(y)] = float(np.average(v, weights=d.n))
    fut = mix_consumption(*C.MIX_WINDOWS[mix])
    for y in range(C.PARTIAL_YEAR + 1, C.FORECAST_END + 1):
        out[y] = fut
    return pd.Series(out).sort_index()


def fleet_consumption(annual_full: pd.DataFrame, exposure: pd.DataFrame, fleet_case: str, mix: str,
                      scenario: str = "20pct_xev") -> pd.Series:
    """Fleet-average EVDB-basis consumption by year, weighting each cohort by its active vehicles
    (annual cohorts, mid-year registration, Weibull survival of the fleet case). Weights only."""
    regs = annual_full["bev"].loc[:C.BASE_YEAR - 1].astype(float).copy()
    nat = exposure[(exposure.scenario == scenario) & (exposure.case == fleet_case) & (exposure.geography == "national")]
    regs = pd.concat([regs, nat.set_index("year")["new_registrations"].astype(float)])
    cc = cohort_consumption(mix)
    p = C.SURVIVAL[fleet_case]
    out = {}
    for y in C.ENERGY_YEARS:
        c = regs.loc[:y]
        age = (y - c.index.values).astype(float)
        w = c.values * np.where(age > 0, survival(age, p["median_life"], p["shape"]), 0.5)
        v = cc.reindex(c.index).values
        ok = w > 0
        if np.isnan(v[ok]).any():
            raise ValueError(f"cohorts with vehicles but no model data: {c.index[ok & np.isnan(v)].tolist()}")
        out[y] = float(np.average(v[ok], weights=w[ok]))
    return pd.Series(out)


# --------------------------------------------------------------------------------------
# Consumption case factors from Malaysian / tropical observations
# --------------------------------------------------------------------------------------
def observation_table() -> pd.DataFrame:
    ev = evdb_kwh_per_100km()
    rows = []
    for oid, model, val, basis, cond, src, key, inc in C.CONSUMPTION_OBSERVATIONS:
        rows.append(dict(id=oid, model=model, observed_kwh_per_100km=val, measurement_basis=basis, conditions=cond,
                         source_id=src, evdb_reference=key, evdb_kwh_per_100km_battery=ev[key],
                         ratio_observed_to_evdb=val / ev[key], used_for_low_factor=inc))
    return pd.DataFrame(rows)


def consumption_factors() -> dict:
    obs = observation_table()
    low = float(obs.loc[obs.used_for_low_factor, "ratio_observed_to_evdb"].median())
    return {"low": low, "base": (low + 1.0) / 2.0, "high": 1.0}


# --------------------------------------------------------------------------------------
# Energy tables
# --------------------------------------------------------------------------------------
def load_exposure() -> pd.DataFrame:
    return pd.read_csv(C.TABLES / "leap_bev_exposure_input.csv")


def parameters(annual_full, exposure, km="base", consumption="base", efficiency="base", mix="base", fleet_case="base"):
    """Year-indexed parameter frame. Consumption is computed from the PRIMARY (20%) fleet composition of
    the fleet case and applied to every scenario, so scenario differences isolate fleet size."""
    fac = consumption_factors()[consumption]
    c = fleet_consumption(annual_full, exposure, fleet_case, mix)
    km_value = C.ANNUAL_KM[km] if isinstance(km, str) else float(km)
    return pd.DataFrame({"year": c.index, "annual_km": km_value, "kwh_per_100km": fac * c.values,
                         "evdb_fleet_kwh_per_100km": c.values, "consumption_factor": fac,
                         "charging_efficiency": C.CHARGING_EFFICIENCY[efficiency]})


def energy_table(annual_full, exposure) -> pd.DataFrame:
    frames = []
    for case, spec in C.ENERGY_CASES.items():
        par = parameters(annual_full, exposure, spec["km"], spec["consumption"], spec["efficiency"], spec["mix"], spec["fleet"])
        e = exposure[exposure["case"] == spec["fleet"]][["year", "scenario", "geography", "vehicle_years", "stock_end"]].copy()
        e["case"] = case
        e = e.merge(par, on="year")
        e["consumption_basis"] = C.ENERGY_BASIS
        e["battery_energy_gwh"] = e.vehicle_years * e.annual_km * e.kwh_per_100km / 100 / 1e6
        e["annual_grid_energy_gwh"] = grid_energy_gwh(e.vehicle_years, e.annual_km, e.kwh_per_100km, e.charging_efficiency)
        e["charging_losses_gwh"] = e["annual_grid_energy_gwh"] - e["battery_energy_gwh"]
        e["grid_kwh_per_vehicle_year"] = e["annual_grid_energy_gwh"] * 1e6 / e["vehicle_years"]
        e["fleet_case"], e["km_case"], e["consumption_case"], e["efficiency_case"], e["mix_case"] = (
            spec["fleet"], spec["km"], spec["consumption"], spec["efficiency"], spec["mix"])
        frames.append(e)
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["scenario", "case", "geography", "year"], key=lambda s: s.map(SCEN_ORDER) if s.name == "scenario"
                           else (s.map(CASE_ORDER) if s.name == "case" else s)).reset_index(drop=True)


LEAP_COLS = ["year", "scenario", "case", "geography", "vehicle_years", "annual_km", "kwh_per_100km",
             "consumption_basis", "charging_efficiency", "annual_grid_energy_gwh"]


def leap_energy(et: pd.DataFrame) -> pd.DataFrame:
    d = et[LEAP_COLS].copy()
    d["vehicle_years"] = d["vehicle_years"].astype(int)
    d["annual_km"] = d["annual_km"].round(2)
    d["kwh_per_100km"] = d["kwh_per_100km"].round(3)
    d["annual_grid_energy_gwh"] = d["annual_grid_energy_gwh"].round(3)
    return d


# --------------------------------------------------------------------------------------
# Sensitivity (one at a time) around the 20% base, 2030
# --------------------------------------------------------------------------------------
def sensitivity_2030(annual_full, exposure, year=C.FORECAST_END) -> pd.DataFrame:
    rows = []

    def calc(scen="20pct_xev", fleet="base", geo="peninsular", **kw):
        par = parameters(annual_full, exposure, fleet_case=fleet, **kw).set_index("year").loc[year]
        vy = exposure[(exposure.scenario == scen) & (exposure.case == fleet) & (exposure.geography == geo) & (exposure.year == year)]["vehicle_years"].iloc[0]
        e = float(grid_energy_gwh(vy, par.annual_km, par.kwh_per_100km, par.charging_efficiency))
        return e, vy, par

    fac = consumption_factors()
    for geo in ("peninsular", "national"):
        base, vy0, p0 = calc(geo=geo)
        variants = [("baseline (20% xEV, all base)", "-", "base", {})]
        variants += [("A. Annual average fleet size (Phase 1.5 low/high, 20%)", f"{c} fleet", c, dict(fleet=c)) for c in ("low", "high")]
        variants += [("B1. Adoption scenario: 30% xEV", "30% xEV", "high", dict(scen="30pct_xev")),
                     ("B2. Adoption scenario: historical trend", "historical trend", "high", dict(scen="historical_trend"))]
        variants += [("C. Annual driving distance", f"{C.ANNUAL_KM[c]:,.0f} km", c, dict(km=c)) for c in ("low", "high")]
        variants += [("C2. BEV mileage = US all-BEV/CV ratio (Zhao 2023)", f"{C.ANNUAL_KM_BASE * C.BEV_CV_RATIO_ALL_BEV:,.0f} km (x{C.BEV_CV_RATIO_ALL_BEV:.3f})",
                      "low", dict(km=C.ANNUAL_KM_BASE * C.BEV_CV_RATIO_ALL_BEV)),
                     ("C3. Malaysian fleet-typical mileage (GIZ 2016)", "15,000 km", "low", dict(km=15000.0))]
        variants += [("D. Consumption level (battery-side)", f"x{fac[c]:.3f} of EVDB fleet value", c, dict(consumption=c)) for c in ("low", "high")]
        variants += [("E. Charging efficiency", f"{C.CHARGING_EFFICIENCY[k]:.0%}", c, dict(efficiency=k)) for c, k in (("low", "high"), ("high", "low"))]
        variants += [("F. Vehicle mix of 2027-2030 cohorts", f"{m} mix ({C.MIX_WINDOWS[m][0]}-{C.MIX_WINDOWS[m][1]} registrations)", c, dict(mix=m))
                     for c, m in (("low", "small"), ("high", "large"))]
        for factor, setting, level, kw in variants:
            e, vy, p = calc(geo=geo, **kw)
            rows.append(dict(geography=geo, factor=factor, setting=setting, level=level, vehicle_years_2030=vy,
                             annual_km=p.annual_km, kwh_per_100km=p.kwh_per_100km, charging_efficiency=p.charging_efficiency,
                             grid_energy_gwh_2030=e, delta_gwh=e - base, pct_vs_baseline=(e - base) / base))
    return pd.DataFrame(rows)


def envelope_rows(et: pd.DataFrame, year=C.FORECAST_END) -> pd.DataFrame:
    d = et[et.year == year].pivot_table(index=["scenario", "geography"], columns="case", values="annual_grid_energy_gwh").reset_index()
    d["factor"] = "Combined envelope (all-low / all-high; not a CI)"
    return d.rename(columns={"low": "envelope_low_gwh", "base": "base_gwh", "high": "envelope_high_gwh"})


def scenario_specific_mix_check(annual_full, exposure) -> pd.DataFrame:
    """Diagnostic: 2030 fleet consumption if each scenario's own cohort weights were used."""
    rows = []
    for scen in SCEN_ORDER:
        c = fleet_consumption(annual_full, exposure, "base", "base", scenario=scen).loc[C.FORECAST_END]
        rows.append(dict(scenario=scen, evdb_fleet_kwh_per_100km_2030=c))
    df = pd.DataFrame(rows)
    df["diff_vs_20pct"] = df["evdb_fleet_kwh_per_100km_2030"] / df.loc[0, "evdb_fleet_kwh_per_100km_2030"] - 1
    return df

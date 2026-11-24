"""Phase 3 (Run 4) - hourly BEV charging profiles for 2030 (Malaysian Standard Time, UTC+08:00).

Energy-conserving construction (per adoption scenario x mileage case x charging strategy):

    E_{L,d}  = E_annual x s_L x A_d g_L(dt_d) / sum_d' A_d' g_L(dt_d')       daily energy of location L
    load_h   = sum_L sum_d E_{L,d} x shape48_{L,dt_d}(h - 24 d)              hourly MWh (= MW for 1-h steps)

  E_annual : Phase 2 annual grid energy (charger input, incl. charging losses, excl. T&D)
  s_L      : charging-location energy share (config.LOCATION_MIX)
  A_d      : daily active-BEV vehicle-days in 2030 (Phase 1.5 daily cohort model) -> fleet growth
  g_L      : weekday / weekend-holiday energy factor of location L
  shape48  : normalized 48-hour charging-energy shape of sessions ARRIVING on a day of type dt
             (residential & workplace: session simulation with connection windows and charger power;
              public AC / DC: EVI-Pro Lite simulated shapes, adapted). Energy past midnight falls on the
              next day; energy past 31 Dec wraps to 1 Jan (stands in for the 31 Dec 2029 carry-in).
Managed (ToU) charging changes shape48 only for residential sessions; annual energy is identical.
"""
import json
from functools import lru_cache

import numpy as np
import pandas as pd

import config as C

STEPS_PER_H = 60 // C.STEP_MIN
DT_H = C.STEP_MIN / 60.0
NSTEP = 48 * STEPS_PER_H


# --------------------------------------------------------------------------------------
# Calendar and TNB ToU
# --------------------------------------------------------------------------------------
def calendar(year: int = C.HOURLY_YEAR) -> pd.DataFrame:
    ts = pd.date_range(f"{year}-01-01 00:00", f"{year}-12-31 23:00", freq="h", tz=C.LOCAL_TZ)
    cal = pd.DataFrame({"timestamp_local": ts})
    cal["date"] = ts.tz_localize(None).normalize()
    cal["year"], cal["month"], cal["day_of_year"] = ts.year, ts.month, ts.dayofyear
    cal["day_of_week"] = ts.day_name()
    cal["hour"] = ts.hour
    hol = pd.to_datetime(list(C.TOU_FIXED_DATE_HOLIDAYS_2030))
    cal["is_public_holiday_dated"] = cal["date"].isin(hol)
    cal["is_weekend"] = ts.dayofweek >= 5
    offday = cal["is_weekend"] | cal["is_public_holiday_dated"]
    cal["tnb_tou_period"] = np.where((~offday) & cal["hour"].isin(C.TOU_PEAK_HOURS_WEEKDAY), "peak", "off_peak")
    cal["behaviour_day_type"] = np.where(offday, "weekend_holiday", "weekday")
    return cal


def daily_frame(year: int = C.HOURLY_YEAR) -> pd.DataFrame:
    cal = calendar(year)
    return cal.groupby("date").agg(day_type=("behaviour_day_type", "first"), day_of_week=("day_of_week", "first")).reset_index()


def tou_mask48(day_type: str) -> np.ndarray:
    """Peak flag for the 48 h following 00:00 of the arrival day, 15-min steps. Day 1 is assumed to be a
    weekday after a weekday arrival (conservative; Friday->Saturday is actually off-peak) and an
    off-peak day after a weekend/holiday arrival only for the arrival day itself."""
    peak = np.zeros(NSTEP, bool)
    hours = np.arange(NSTEP) // STEPS_PER_H
    in_peak = np.isin(hours % 24, C.TOU_PEAK_HOURS_WEEKDAY)
    if day_type == "weekday":
        peak |= in_peak
    else:
        peak |= in_peak & (hours >= 24)          # next day treated as a weekday (conservative)
    return peak


# --------------------------------------------------------------------------------------
# Session simulation (residential, workplace)
# --------------------------------------------------------------------------------------
def _sample_discrete(rng, values, probs, n):
    p = np.asarray(probs, float)
    return rng.choice(np.asarray(values, float), size=n, p=p / p.sum())


def _lognormal(rng, median, mean, n, lo, hi):
    sigma = np.sqrt(2 * np.log(mean / median))
    return np.clip(rng.lognormal(np.log(median), sigma, n), lo, hi)


def sample_sessions(kind: str, n: int = C.N_SESSIONS, seed: int = C.SESSION_SEED, power_mix=None,
                    arrival_shift_h: int = 0, home_kwh_mean: float = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed + (0 if kind == "residential" else 1))
    if kind == "residential":
        arr_h = _sample_discrete(rng, range(24), np.roll(C.LIU2024_PLUG_START, arrival_shift_h), n) \
            + rng.integers(0, STEPS_PER_H, n) / STEPS_PER_H
        dep_h = 24 + _sample_discrete(rng, list(C.LIU2024_UNPLUG_MORNING), list(C.LIU2024_UNPLUG_MORNING.values()), n) \
            + rng.integers(0, STEPS_PER_H, n) / STEPS_PER_H
        m, cv = (home_kwh_mean or C.HOME_SESSION_KWH["mean"]), C.HOME_SESSION_KWH["cv"]
        k = 1 / cv ** 2
        energy = np.clip(rng.gamma(k, m / k, n), C.HOME_SESSION_KWH["min"], C.HOME_SESSION_KWH["max"])
        pm = power_mix or C.HOME_POWER_MIX
    elif kind == "workplace":
        arr_h = _sample_discrete(rng, list(C.NREL_WP_ARRIVAL_30MIN), list(C.NREL_WP_ARRIVAL_30MIN.values()), n) \
            + rng.integers(0, 2, n) * 0.25
        park = _sample_discrete(rng, list(C.NREL_WP_PARK_HOURS_30MIN), list(C.NREL_WP_PARK_HOURS_30MIN.values()), n) \
            + rng.integers(0, 2, n) * 0.25 + 0.25
        dep_h = np.minimum(arr_h + park, 47.75)
        energy = _lognormal(rng, C.NREL_WP_ENERGY["median"], C.NREL_WP_ENERGY["mean"], n, 0.5, C.NREL_WP_ENERGY["max"])
        pm = power_mix or C.WORKPLACE_POWER_MIX_MY
    else:
        raise ValueError(kind)
    power = _sample_discrete(rng, list(pm), list(pm.values()), n)
    a = np.round(arr_h * STEPS_PER_H).astype(int)
    d = np.maximum(np.round(dep_h * STEPS_PER_H).astype(int), a + 1)
    return pd.DataFrame({"arr_step": a, "dep_step": np.minimum(d, NSTEP), "energy_req_kwh": energy, "power_kw": power})


def schedule(sess: pd.DataFrame, strategy: str, day_type: str, rng_seed: int = 7):
    """Return (P matrix [n x NSTEP] kW, diagnostics). strategy: unmanaged | staggered | synchronized.
    Energy delivered per session = min(requested, power x connection time) - identical for all strategies."""
    n = len(sess)
    a, d = sess.arr_step.values[:, None], sess.dep_step.values[:, None]
    steps = np.arange(NSTEP)[None, :]
    window = (steps >= a) & (steps < d)
    P = sess.power_kw.values[:, None]
    cap_step = P[:, 0] * DT_H
    delivered = np.minimum(sess.energy_req_kwh.values, window.sum(1) * cap_step)
    n_full = np.floor(delivered / cap_step + 1e-9).astype(int)
    rem = delivered - n_full * cap_step

    def fill(allowed, offset, idx=slice(None)):
        rank = np.cumsum(allowed, axis=1)             # 1-based rank among allowed steps
        lo = offset[:, None]
        nf = n_full[idx][:, None]
        full = allowed & (rank > lo) & (rank <= lo + nf)
        part = allowed & (rank == lo + nf + 1)
        return full * P[idx] + part * (rem[idx] / DT_H)[:, None]

    if strategy == "unmanaged" or day_type != "weekday":
        out = fill(window, np.zeros(n, int))
        unshift = np.zeros(n)
    else:
        peak = tou_mask48(day_type)[None, :]
        allowed = window & ~peak
        n_allowed = allowed.sum(1)
        need = n_full + (rem > 1e-9)
        ok = n_allowed >= need
        rng = np.random.default_rng(rng_seed)
        slack = np.maximum(n_allowed - need, 0)
        offset = np.where(strategy == "staggered", (rng.random(n) * (slack + 1)).astype(int), 0)
        out = np.zeros((n, NSTEP))
        # sessions that fit entirely in off-peak windows
        out[ok] = fill(allowed[ok], offset[ok], ok)
        # sessions that do not fit: use all off-peak steps, remainder as early as possible in peak steps
        bad = ~ok
        unshift = np.zeros(n)
        if bad.any():
            off_e = n_allowed[bad] * cap_step[bad]
            out_b = allowed[bad] * P[bad]
            rest = delivered[bad] - off_e
            unshift[bad] = rest
            pk = window[bad] & peak[0][None, :]
            nf = np.floor(rest / cap_step[bad] + 1e-9).astype(int)
            rr = rest - nf * cap_step[bad]
            rank = np.cumsum(pk, axis=1)
            out_b = out_b + (pk & (rank <= nf[:, None])) * P[bad] + (pk & (rank == nf[:, None] + 1)) * (rr / DT_H)[:, None]
            out[bad] = out_b
    diag = dict(delivered_kwh=delivered, requested_kwh=sess.energy_req_kwh.values, window=window, power=P[:, 0],
                unshiftable_kwh=unshift)
    return out, diag


def session_shapes(kind: str, power_mix=None, arrival_shift_h: int = 0, home_kwh_mean: float = None):
    """Normalized 48-h hourly energy shapes per day type and strategy + connected-vehicle profiles."""
    sess = sample_sessions(kind, power_mix=power_mix, arrival_shift_h=arrival_shift_h, home_kwh_mean=home_kwh_mean)
    res, checks = {}, {}
    for dt in ("weekday", "weekend_holiday"):
        for strat in (("unmanaged", "staggered", "synchronized") if kind in C.MANAGED_LOCATIONS else ("unmanaged",)):
            P, dg = schedule(sess, strat, dt)
            e_step = P * DT_H
            hourly = e_step.reshape(len(sess), 48, STEPS_PER_H).sum(axis=2).sum(axis=0)
            tot = dg["delivered_kwh"].sum()
            res[(dt, strat)] = hourly / tot
            checks[(dt, strat)] = dict(
                energy_conserved=bool(np.allclose(e_step.sum(1), dg["delivered_kwh"], atol=1e-6)),
                outside_window_kwh=float((e_step * ~dg["window"]).sum()),
                max_power_excess_kw=float((P - dg["power"][:, None]).max()),
                min_power_kw=float(P.min()),
                unshiftable_share=float(dg["unshiftable_kwh"].sum() / tot),
                truncated_share=float(1 - tot / dg["requested_kwh"].sum()),
                mean_delivered_kwh=float(dg["delivered_kwh"].mean()))
        conn = dg["window"].reshape(len(sess), 48, STEPS_PER_H).mean(axis=2).sum(axis=0) / len(sess)
        res[(dt, "connected_share")] = conn
    return res, checks


# --------------------------------------------------------------------------------------
# Shape-based public profiles (EVI-Pro Lite) and source reference profiles
# --------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def evipro_profiles() -> dict:
    out = {}
    files = sorted(C.EVIPRO_DIR.glob("evipro_lite_HA*_min.json"))
    for f in files:
        r = json.loads(f.read_text())["results"]
        for dt, key in (("weekday", "weekday_load_profile"), ("weekend_holiday", "weekend_load_profile")):
            p = r[key]
            for loc, cols in {"residential": ["home_l1", "home_l2"], "workplace": ["work_l1", "work_l2"],
                              "public_ac": ["public_l2"], "public_dc": ["public_l3"]}.items():
                v = np.sum([np.array(p[c]) for c in cols], axis=0).reshape(24, 4).mean(1)
                out.setdefault((loc, dt), []).append(v / v.sum())
    return {k: np.mean(v, axis=0) for k, v in out.items()}


def public_shape48(loc: str, dt: str) -> np.ndarray:
    s = evipro_profiles()[(loc, dt)].copy()
    if loc == "public_dc" and C.DC_SMOOTH_HOURS > 1:
        k = C.DC_SMOOTH_HOURS
        s = np.mean([np.roll(s, i - k // 2) for i in range(k)], axis=0)
    s = s / s.sum()
    return np.concatenate([s, np.zeros(24)])


def fold24(shape48: np.ndarray) -> np.ndarray:
    return shape48[:24] + shape48[24:]


# --------------------------------------------------------------------------------------
# Annual assembly
# --------------------------------------------------------------------------------------
def daily_activity(traj: pd.DataFrame, year: int = C.HOURLY_YEAR) -> pd.Series:
    t = traj[traj["year"] == year]
    return pd.Series(t["vehicle_days"].values, index=pd.to_datetime(t["date"].values))


def location_daily_energy(e_total_mwh: float, share: float, loc: str, days: pd.DataFrame, activity: pd.Series) -> np.ndarray:
    g = np.where(days["day_type"] == "weekday", 1.0, C.WEEKEND_ENERGY_FACTOR[loc])
    w = activity.reindex(days["date"]).values * g
    return e_total_mwh * share * w / w.sum()


def assemble(daily_e: np.ndarray, days: pd.DataFrame, shapes: dict) -> np.ndarray:
    """8,760-h series (MWh) from daily energies and 48-h shapes keyed by day type (circular year)."""
    nh = 24 * len(days)
    out = np.zeros(nh + 24)
    for i, (e, dt) in enumerate(zip(daily_e, days["day_type"])):
        out[24 * i: 24 * i + 48] += e * shapes[dt]
    out[:24] += out[nh:]                           # wrap 31 Dec overflow to 1 Jan (carry-in proxy)
    return out[:nh]


def build_profiles(e_total_mwh: float, activity: pd.Series, mix: dict, shapes_by_loc: dict, participation: float,
                   managed_strategy: str = "staggered") -> dict:
    """Return {location: hourly MWh array}. shapes_by_loc[loc][(dt, strategy)] -> 48-h normalized shape."""
    days = daily_frame()
    out = {}
    for loc in C.LOCATIONS:
        de = location_daily_energy(e_total_mwh, mix[loc], loc, days, activity)
        sh = shapes_by_loc[loc]
        if loc in C.MANAGED_LOCATIONS and participation > 0:
            comb = {dt: (1 - participation) * sh[(dt, "unmanaged")] + participation * sh[(dt, managed_strategy)]
                    for dt in ("weekday", "weekend_holiday")}
        else:
            comb = {dt: sh[(dt, "unmanaged")] for dt in ("weekday", "weekend_holiday")}
        out[loc] = assemble(de, days, comb)
    return out


# --------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------
def metrics(total_mwh: np.ndarray, cal: pd.DataFrame) -> dict:
    s = pd.Series(total_mwh, index=cal["timestamp_local"])
    imax = int(np.argmax(total_mwh))
    peak = cal["tnb_tou_period"].values == "peak"
    wk = cal["behaviour_day_type"].values == "weekday"
    ramp = np.diff(total_mwh)
    return dict(annual_gwh=total_mwh.sum() / 1000, max_load_mw=total_mwh.max(),
                max_load_weekday_mw=total_mwh[wk].max(), max_load_weekend_holiday_mw=total_mwh[~wk].max(),
                max_load_weekday_tnb_peak_hours_mw=total_mwh[wk & peak].max(),
                max_load_timestamp=str(cal["timestamp_local"].iloc[imax]), avg_load_mw=total_mwh.mean(),
                peak_to_average=total_mwh.max() / total_mwh.mean(),
                share_tnb_peak=total_mwh[peak].sum() / total_mwh.sum(), share_tnb_offpeak=total_mwh[~peak].sum() / total_mwh.sum(),
                energy_tnb_peak_gwh=total_mwh[peak].sum() / 1000,
                avg_daily_mwh_weekday=total_mwh[wk].sum() / (wk.sum() / 24),
                avg_daily_mwh_weekend_holiday=total_mwh[~wk].sum() / ((~wk).sum() / 24),
                max_ramp_up_mw_per_h=ramp.max(), max_ramp_down_mw_per_h=-ramp.min(),
                hour_of_max_ramp_up=int(cal["hour"].iloc[int(np.argmax(ramp)) + 1]))

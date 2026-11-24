"""Phase 3.1 - Malaysian-informed public AC (destination) charging shapes and annual assembly.

Construction of the 'public_ac_industry_informed' 24-h shape for a day type (continuous time t in hours, MYT):

    density(t) = floor + (background - floor) x SBOX(t; open hours, sigma_b) + sum_k a_k x SBOX(t; window_k, sigma)
    shape_h    = mean of density over hour h (1-min grid), normalized so that the 24 hourly values sum to 1

  SBOX(t; [L, R], s) = Phi((t - L)/s) - Phi((t - R)/s)   (boxcar with Gaussian edges, circular over midnight)

Weekday windows: lunch 12-14, after work 17-18, dinner 20-22 (reported timing). Weekend/holiday: one 12-16 plateau.
Amplitudes a_k are solved so that the hourly maxima inside each window equal the requested RELATIVE magnitudes
(researcher-defined configurations; observed magnitudes are unknown). Each day type sums to 1, i.e. the shape
carries no information about daily energy; weekend/weekday daily energy is set separately (multiplier m).

Annual public AC energy (unchanged from Phase 3):
    E_d = E_annual x s_AC x A_d g_d / sum_d' A_d' g_d',   g_d = 1 (weekday) or m (weekend / dated holiday)
"""
import numpy as np
import pandas as pd
from scipy.optimize import nnls
from scipy.stats import norm

import config as C
import hourly as H

_T = (np.arange(24 * 60) + 0.5) / 60.0


def _sbox(lo, hi, s):
    return sum(norm.cdf((_T + 24 * k - lo) / s) - norm.cdf((_T + 24 * k - hi) / s) for k in (-1, 0, 1))


def _hourly(d):
    return d.reshape(24, 60).mean(axis=1)


def industry_components(day_type: str, config: str = C.INDUSTRY_DEFAULT_CONFIG, width: str = C.INDUSTRY_DEFAULT_WIDTH) -> dict:
    """Unnormalized hourly components {background, <peak names>} for one day type (relative to peak height 1)."""
    s = C.INDUSTRY_PEAK_WIDTHS[width]
    lo, hi = C.INDUSTRY_BACKGROUND_HOURS[day_type]
    bg = C.INDUSTRY_FLOOR_LEVEL + (C.INDUSTRY_BACKGROUND_LEVEL - C.INDUSTRY_FLOOR_LEVEL) * _hourly(_sbox(lo, hi, C.INDUSTRY_BACKGROUND_SMOOTH_H))
    if day_type == "weekday":
        names = list(C.INDUSTRY_WEEKDAY_WINDOWS)
        comps = [_hourly(_sbox(*C.INDUSTRY_WEEKDAY_WINDOWS[n], s)) for n in names]
        hrs = [C.INDUSTRY_WEEKDAY_PEAK_HOURS[n] for n in names]
        tgt = np.array(C.INDUSTRY_PEAK_CONFIGS[config], float) / max(C.INDUSTRY_PEAK_CONFIGS[config])
    else:
        names = ["weekend_plateau"]
        comps = [_hourly(_sbox(*C.INDUSTRY_WEEKEND_WINDOW, s))]
        hrs = [list(range(int(C.INDUSTRY_WEEKEND_WINDOW[0]), int(C.INDUSTRY_WEEKEND_WINDOW[1])))]
        tgt = np.array([1.0])
    a = tgt.copy()
    for _ in range(500):                       # fixed-point: hourly window maxima -> target magnitudes
        tot = bg + sum(ai * c for ai, c in zip(a, comps))
        obs = np.array([tot[h].max() for h in hrs])
        if np.allclose(obs, tgt, rtol=1e-12, atol=0):
            break
        a = a * tgt / obs
    out = {"background": bg}
    out.update({n: ai * c for n, ai, c in zip(names, a, comps)})
    return out


def industry_shape24(day_type: str, config: str = C.INDUSTRY_DEFAULT_CONFIG, width: str = C.INDUSTRY_DEFAULT_WIDTH) -> np.ndarray:
    v = sum(industry_components(day_type, config, width).values())
    return v / v.sum()


def shape48_from24(s24: np.ndarray) -> np.ndarray:
    s24 = np.asarray(s24, float)
    return np.concatenate([s24 / s24.sum(), np.zeros(24)])


def industry_shapes48(config=C.INDUSTRY_DEFAULT_CONFIG, width=C.INDUSTRY_DEFAULT_WIDTH) -> dict:
    return {dt: shape48_from24(industry_shape24(dt, config, width)) for dt in ("weekday", "weekend_holiday")}


def reference_shapes48() -> dict:
    return {dt: H.public_shape48("public_ac", dt) for dt in ("weekday", "weekend_holiday")}


# --------------------------------------------------------------------------------------
# Peak-region diagnostics (used by validation and reports)
# --------------------------------------------------------------------------------------
def peak_regions(v: np.ndarray, min_prominence: float = 0.10) -> list:
    """Hours of local maxima (plateau-aware, circular) whose prominence - drop to the higher of the two flanking
    minima before a higher peak - is >= min_prominence x the region maximum."""
    v = np.asarray(v, float)
    n = len(v)
    peaks, h = [], 0
    while h < n:
        j = h
        while j + 1 < n and np.isclose(v[j + 1], v[h], rtol=1e-9, atol=1e-15):
            j += 1
        left, right = v[(h - 1) % n], v[(j + 1) % n]
        if v[h] > left and v[h] > right:
            peaks.append((h, j))
        h = j + 1
    out = []
    for (a, b) in peaks:
        top = v[a]
        mins = []
        for step in (-1, 1):                              # walk until a higher value; record the minimum
            k, m = (a if step < 0 else b), top
            for _ in range(n):
                k = (k + step) % n
                m = min(m, v[k])
                if v[k] > top:
                    break
            mins.append(m)
        prom = top - max(mins)
        if prom >= min_prominence * top:
            out.append(dict(hours=list(range(a, b + 1)), max=top, prominence=prom))
    return out


# --------------------------------------------------------------------------------------
# Annual assembly
# --------------------------------------------------------------------------------------
def public_ac_daily_energy(e_total_mwh: float, share: float, days: pd.DataFrame, activity: pd.Series, m: float = 1.0) -> np.ndarray:
    g = np.where(days["day_type"] == "weekday", 1.0, m * C.WEEKEND_ENERGY_FACTOR["public_ac"])
    w = activity.reindex(days["date"]).values * g
    return e_total_mwh * share * w / w.sum()


def build(e_total_mwh, activity, mix, shapes3, participation, strategy, ac_shapes48=None, m=1.0) -> dict:
    """Phase 3 location profiles (H.build_profiles, unchanged) with the public AC series replaced by the given
    shapes / weekend multiplier. ac_shapes48=None and m=1 returns the Phase 3 profile set exactly."""
    locs = H.build_profiles(e_total_mwh, activity, mix, shapes3, participation, strategy)
    if ac_shapes48 is not None or m != 1.0:
        days = H.daily_frame()
        de = public_ac_daily_energy(e_total_mwh, mix["public_ac"], days, activity, m)
        locs["public_ac"] = H.assemble(de, days, ac_shapes48 or reference_shapes48())
    return locs


def mix_with_public_ac_share(share: float, base: dict = None) -> dict:
    base = base or C.LOCATION_MIX["base"]
    rest = 1 - base["public_ac"]
    out = {l: (share if l == "public_ac" else base[l] * (1 - share) / rest) for l in C.LOCATIONS}
    return out


def metrics31(locs: dict, cal: pd.DataFrame) -> dict:
    tot = sum(locs.values())
    mt = H.metrics(tot, cal)
    ac, res = locs["public_ac"], locs["residential"]
    wk = (cal["behaviour_day_type"] == "weekday").values
    pk = (cal["tnb_tou_period"] == "peak").values
    hr = cal["hour"].values
    i_ac, i_tot = int(np.argmax(ac)), int(np.argmax(tot))
    i_wk = int(np.flatnonzero(wk)[np.argmax(tot[wk])])
    i_we = int(np.flatnonzero(~wk)[np.argmax(tot[~wk])])
    i_res = int(np.argmax(res))
    din = wk & np.isin(hr, [20, 21])
    mid = (~wk) & np.isin(hr, [12, 13, 14, 15])
    mt.update(
        public_ac_annual_gwh=ac.sum() / 1000, public_ac_share_of_total=ac.sum() / tot.sum(),
        public_ac_max_mw=ac.max(), public_ac_max_timestamp=str(cal["timestamp_local"].iloc[i_ac]),
        public_ac_weekday_gwh=ac[wk].sum() / 1000, public_ac_weekend_holiday_gwh=ac[~wk].sum() / 1000,
        public_ac_avg_daily_mwh_weekday=ac[wk].sum() / (wk.sum() / 24), public_ac_avg_daily_mwh_weekend_holiday=ac[~wk].sum() / ((~wk).sum() / 24),
        public_ac_max_weekday_mw=ac[wk].max(), public_ac_max_weekend_holiday_mw=ac[~wk].max(),
        public_ac_tnb_peak_gwh=ac[pk].sum() / 1000, public_ac_share_in_tnb_peak=ac[pk].sum() / ac.sum(),
        public_ac_max_in_tnb_peak_mw=ac[pk].max(),
        max_load_weekday_timestamp=str(cal["timestamp_local"].iloc[i_wk]),
        max_load_weekend_holiday_timestamp=str(cal["timestamp_local"].iloc[i_we]),
        hour_of_max_load=int(hr[i_tot]), hour_of_max_weekend_holiday_load=int(hr[i_we]),
        public_ac_at_max_load_mw=ac[i_tot], residential_at_max_load_mw=res[i_tot],
        public_ac_at_residential_max_mw=ac[i_res],
        corr_public_ac_residential_weekday=float(np.corrcoef(ac[wk], res[wk])[0, 1]),
        weekday_2000_2200_avg_public_ac_mw=ac[din].mean(), weekday_2000_2200_avg_residential_mw=res[din].mean(),
        weekend_1200_1600_avg_public_ac_mw=ac[mid].mean(), weekend_1200_1600_avg_total_mw=tot[mid].mean(),
        weekend_max_in_1200_1600=bool(hr[i_we] in (12, 13, 14, 15)))
    return mt


# --------------------------------------------------------------------------------------
# Physical-plausibility check: can plausible destination sessions reproduce the aggregate shape?
# --------------------------------------------------------------------------------------
def destination_session_library(seed: int = C.DEST_SEED):
    """Per visit type: average hourly charging energy per session (kWh) and average connected vehicles per session,
    over 48 h from 00:00 of the arrival day, folded to 24 h. Uses hourly.schedule (unmanaged)."""
    rng = np.random.default_rng(seed)
    n = C.DEST_N_PER_TYPE
    lib, stats = {}, {}
    sig_e = np.sqrt(2 * np.log(C.DEST_SESSION_KWH["mean"] / C.DEST_SESSION_KWH["median"]))
    for name, (mu, sd, dmed, dsig) in C.DEST_VISIT_TYPES.items():
        arr = np.clip(rng.normal(mu, sd, n), 0, 23.75)
        dwell = np.clip(rng.lognormal(np.log(dmed), dsig, n), 0.25, 14.0)
        e = np.clip(rng.lognormal(np.log(C.DEST_SESSION_KWH["median"]), sig_e, n), 1.0, C.DEST_SESSION_KWH["max"])
        pw = rng.choice(list(C.DEST_POWER_MIX), size=n, p=np.array(list(C.DEST_POWER_MIX.values())) / sum(C.DEST_POWER_MIX.values()))
        a = np.round(arr * H.STEPS_PER_H).astype(int)
        d = np.minimum(np.maximum(np.round((arr + dwell) * H.STEPS_PER_H).astype(int), a + 1), H.NSTEP)
        sess = pd.DataFrame({"arr_step": a, "dep_step": d, "energy_req_kwh": e, "power_kw": pw})
        P, dg = H.schedule(sess, "unmanaged", "weekday")
        e_h = (P * H.DT_H).reshape(n, 48, H.STEPS_PER_H).sum(axis=2).sum(axis=0) / n
        c_h = dg["window"].reshape(n, 48, H.STEPS_PER_H).mean(axis=2).sum(axis=0) / n
        ch_h = (P > 0).reshape(n, 48, H.STEPS_PER_H).mean(axis=2).sum(axis=0) / n
        lib[name] = dict(energy=H.fold24(e_h), connected=H.fold24(c_h), charging=H.fold24(ch_h))
        stats[name] = dict(mean_delivered_kwh=float(dg["delivered_kwh"].mean()), mean_dwell_h=float(dwell.mean()),
                           share_dwell_limited=float((dg["delivered_kwh"] < e - 1e-9).mean()),
                           mean_power_kw=float(pw.mean()))
    return lib, stats


def fit_sessions(target24: np.ndarray, lib: dict, basis: str = "energy"):
    """Non-negative session counts per visit type so that the mixture's hourly 'basis' profile ('energy' = charging
    power, 'connected' = occupancy) is proportional to target24. Returns weights (sessions per unit daily energy),
    fitted energy and occupancy shapes and goodness of fit."""
    names = list(lib)
    A = np.column_stack([lib[n][basis] for n in names])
    scale = A.sum(axis=0)
    w, _ = nnls(A / scale, np.asarray(target24, float) / np.sum(target24))
    counts = w / scale                                 # sessions per unit of 'basis' total
    e = np.column_stack([lib[n]["energy"] for n in names]) @ counts
    c = np.column_stack([lib[n]["connected"] for n in names]) @ counts
    ch = np.column_stack([lib[n]["charging"] for n in names]) @ counts
    kwh = e.sum()
    fit = (e if basis == "energy" else c)
    fit_n = fit / fit.sum()
    tn = np.asarray(target24) / np.sum(target24)
    return dict(counts_per_kwh={n: counts[i] / kwh for i, n in enumerate(names)},
                energy_shape=e / kwh, connected_per_kwh=c / kwh, charging_per_kwh=ch / kwh,
                r=float(np.corrcoef(fit_n, tn)[0, 1]), max_abs_err_pp=float(np.abs(fit_n - tn).max() * 100),
                sessions_per_mwh=counts.sum() / kwh * 1000)

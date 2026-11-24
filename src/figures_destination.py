"""Phase 3.1 figures (fig26-fig35). Same style and fixed entity colours as figures.py / figures_hourly.py."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as C
import destination as D
import hourly as H
from figures import AQUA, BLUE, INK2, MAGENTA, MUTED, ORANGE, SURFACE, VIOLET, YELLOW, _foot, _save, _style
from figures_hourly import LOC_COL, LOC_LAB, _hours, _shade_peak, _step

REF, IND = "evipro_reference", "industry_informed"
REF_COL, SH_COL = INK2, AQUA
CFG_COL = {"equal": AQUA, "lunch_dominant": BLUE, "after_work_dominant": ORANGE, "dinner_dominant": VIOLET}
CFG_LAB = {"equal": "Equal magnitudes (default, neutral)", "lunch_dominant": "Lunch-dominant (1.5x)",
           "after_work_dominant": "After-work-dominant (1.5x)", "dinner_dominant": "Dinner-dominant (1.5x)"}
NOTE = ("Peninsular Malaysia, 2030, MYT (UTC+08:00). Industry-informed = peak TIMING from qualitative observations of one industry practitioner "
        "(unverified; magnitudes, coverage and 'active usage' definition unknown); all magnitudes and widths are researcher-defined. ")
STACK_ORDER = ["residential", "workplace", "public_dc", "public_ac"]


def _windows(ax, day_type):
    wins = list(C.INDUSTRY_WEEKDAY_WINDOWS.values()) if day_type == "weekday" else [C.INDUSTRY_WEEKEND_WINDOW]
    for lo, hi in wins:
        ax.axvspan(lo, hi, ymin=0, ymax=0.035, color=AQUA, alpha=0.9, lw=0)
    lo0 = min(w[0] for w in wins)
    ax.text(lo0, 0.045, "reported window(s)", transform=ax.get_xaxis_transform(), fontsize=7.5, color=AQUA, va="bottom", ha="left")


def fig_shape(ctx, dt, fname, title):
    _style()
    fig, ax = plt.subplots(figsize=(11, 5))
    if dt == "weekday":
        _shade_peak(ax)
    _windows(ax, dt)
    _step(ax, H.fold24(ctx["ac_shapes"][REF][dt]) * 100, color=REF_COL, lw=1.8, ls="--", label="Existing reference: EVI-Pro Lite public L2 (US simulation)")
    _step(ax, H.fold24(ctx["ac_shapes"][IND][dt]) * 100, color=SH_COL, lw=2.4, label="Industry-informed (default: equal magnitudes, sigma 0.75 h)")
    ax.set_ylabel("% of daily public AC energy")
    ax.set_title(title)
    _hours(ax)
    ax.set_ylim(0, 16)
    ax.legend(fontsize=8.5, loc="upper left")
    _foot(fig, NOTE + ("Weekday and weekend shapes each sum to 100%; daily energy is set separately (equal per vehicle-day in the default)."))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, fname)


def fig_decomp(ctx, dt, fname, title):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    ax = axes[0]
    comps = D.industry_components(dt)
    tot = sum(comps.values())
    cols = {"background": MUTED, "lunch": BLUE, "after_work": ORANGE, "dinner": VIOLET, "weekend_plateau": AQUA}
    labs = {"background": "Floor + open-hours background (assumed levels)", "lunch": "Lunch 12-14", "after_work": "After work 17-18",
            "dinner": "Dinner 20-22", "weekend_plateau": "Weekend plateau 12-16"}
    bottom = np.zeros(24)
    for k, v in comps.items():
        vv = v / tot.sum() * 100
        ax.bar(np.arange(24) + 0.5, vv, bottom=bottom, width=0.92, color=cols[k], edgecolor=SURFACE, lw=0.6, label=labs[k])
        bottom += vv
    for r in D.peak_regions(tot / tot.sum()):
        h = r["hours"][0]
        ax.annotate(f"peak {h:02d}:00", (h + 0.5, bottom[h]), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=8, color=INK2)
    ax.set_title(f"Construction of the {dt.replace('_', '/')} shape")
    ax.set_ylabel("% of daily public AC energy")
    ax.set_ylim(0, 16.5)
    ax.legend(fontsize=8, loc="upper left")
    ax = axes[1]
    f = ctx["fits"][(dt, "energy")]
    fo = ctx["fits"][(dt, "connected")]
    _step(ax, H.fold24(ctx["ac_shapes"][IND][dt]) * 100, color=SH_COL, lw=2.4, label="Aggregate industry-informed shape (target)")
    _step(ax, f["energy_shape"] * 100, color=INK2, lw=1.6, ls="--", label=f"Session mix fitted to it: charging power (r = {f['r']:.2f})")
    _step(ax, fo["energy_shape"] * 100, color=ORANGE, lw=1.6, ls=":",
          label=f"Power if the reported timing were OCCUPANCY (connected vehicles)")
    ax.set_title("Physical-plausibility check: researcher-defined AC sessions (7.4/11 kW)")
    ax.set_ylabel("% of daily public AC energy")
    ax.set_ylim(0, 19)
    ax.legend(fontsize=8, loc="upper left")
    for a in axes:
        if dt == "weekday":
            _shade_peak(a)
        _hours(a)
    _windows(axes[1], dt)
    _foot(fig, NOTE + "Right: non-negative mix of 8 assumed visit types (arrival, dwell 1-9 h, energy <= power x dwell) - consistency check, not observed sessions.")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    _save(fig, fname)


def _avg_day(locs, cal, dt):
    m = (cal["behaviour_day_type"] == "weekday").values if dt == "weekday" else (cal["behaviour_day_type"] != "weekday").values
    hr = cal["hour"].values
    return {l: np.array([v[m & (hr == h)].mean() for h in range(24)]) for l, v in locs.items()}


def fig_combined(ctx):
    _style()
    cal, keep = ctx["cal"], ctx["keep"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5), sharey=True)
    for ax, dt, ttl in ((axes[0], "weekday", "Average weekday"), (axes[1], "weekend_holiday", "Average weekend / dated holiday")):
        if dt == "weekday":
            _shade_peak(ax)
        for case, ls, cl in (("unmanaged", "-", "Unmanaged"), ("managed_staggered_p50", "--", "ToU 50% staggered")):
            for v, col, lab in ((REF, REF_COL, "existing public AC"), (IND, SH_COL, "Industry-informed public AC")):
                d = _avg_day(keep[("20pct_xev", "base_17969km", case, v)], cal, dt)
                _step(ax, sum(d.values()), color=col, ls=ls, lw=2 if v == IND else 1.6, label=f"{cl}, {lab}")
        ax.set_title(f"{ttl} - total BEV charging load, 20% xEV base")
        _hours(ax)
        ax.set_ylim(0, 390)
    axes[1].text(0.98, 0.97, "Weekends are all off-peak, so ToU leaves weekend sessions unshifted;\n"
                 "the early-morning difference is carry-over from managed Friday-night sessions", transform=axes[1].transAxes,
                 ha="right", va="top", fontsize=8, color=INK2)
    axes[0].set_ylabel("Average charging load (MW)")
    axes[0].legend(fontsize=8.2, loc="upper left")
    _foot(fig, NOTE + "Residential, workplace and public DC are identical to Phase 3 in both cases; only the public AC (15%, 192.7 GWh) shape differs.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig30_combined_bev_profiles_existing_vs_industry.png")


def fig_stacked_day(ctx, date, fname, title):
    _style()
    cal, keep = ctx["cal"], ctx["keep"]
    sel = (cal["timestamp_local"].dt.strftime("%Y-%m-%d") == date).values
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), sharey=True)
    for ax, v, ttl in ((axes[0], REF, "Existing public AC (EVI-Pro Lite)"), (axes[1], IND, "Industry-informed public AC")):
        locs = keep[("20pct_xev", "base_17969km", "unmanaged", v)]
        bottom = np.zeros(24)
        for loc in STACK_ORDER:
            vv = locs[loc][sel]
            ax.bar(np.arange(24) + 0.5, vv, bottom=bottom, width=0.92, color=LOC_COL[loc], edgecolor=SURFACE, lw=0.6, label=LOC_LAB[loc])
            bottom += vv
        h = int(bottom.argmax())
        ax.annotate(f"max {bottom.max():,.1f} MW at {h:02d}:00\n(public AC {locs['public_ac'][sel][h]:.1f} MW)", (h + 0.5, bottom.max()),
                    xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8.3, color=INK2)
        if cal.loc[sel, "behaviour_day_type"].iloc[0] == "weekday":
            _shade_peak(ax)
        ax.set_title(ttl)
        _hours(ax)
        ax.set_ylim(0, 500)
    axes[0].set_ylabel("Hourly charging load (MW)")
    axes[0].legend(fontsize=8.2, loc="upper left")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    _foot(fig, NOTE + "Unmanaged charging, 20% xEV base mileage. Day chosen because it contains the 2030 maximum of its day type (largest fleet in late December).")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    _save(fig, fname)


def fig_magnitudes(ctx):
    _style()
    sens = ctx["sens"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axes[0]
    _shade_peak(ax)
    _windows(ax, "weekday")
    _step(ax, H.fold24(ctx["ac_shapes"][REF]["weekday"]) * 100, color=REF_COL, lw=1.5, ls="--", label="Existing reference (EVI-Pro Lite)")
    for cf in C.INDUSTRY_PEAK_CONFIGS:
        _step(ax, D.industry_shape24("weekday", cf) * 100, color=CFG_COL[cf], lw=2.2 if cf == "equal" else 1.6, label=CFG_LAB[cf])
    ax.set_title("Weekday public AC shapes by assumed relative peak magnitude")
    ax.set_ylabel("% of daily public AC energy")
    ax.set_ylim(0, 16)
    _hours(ax)
    ax.legend(fontsize=8, loc="upper left")
    ax = axes[1]
    f = sens[(sens.sensitivity_dimension == "peak_magnitude_x_width_x_weekend_multiplier") & (sens.weekend_energy_multiplier == 1.0) &
             (sens.public_ac_profile != REF)]
    rows = [(cf, w) for cf in C.INDUSTRY_PEAK_CONFIGS for w in C.INDUSTRY_PEAK_WIDTHS]
    y = np.arange(len(rows))[::-1]
    for case, col, mk, lab in (("unmanaged", BLUE, "o", "Unmanaged: max BEV load"), ("managed_staggered_p50", AQUA, "s", "ToU 50%: max WEEKDAY load"),
                               ("managed_synchronized_p100", ORANGE, "D", "Synchronized 100%: 22:00 max")):
        col_name = "delta_max_load_weekday_mw_vs_reference" if case == "managed_staggered_p50" else "delta_max_load_mw_vs_reference"
        vals = [f[(f.weekday_peak_config == cf) & (f.peak_width == w) & (f.charging_scenario == case)][col_name].iloc[0] for cf, w in rows]
        dy = {"unmanaged": 0.22, "managed_staggered_p50": 0.0, "managed_synchronized_p100": -0.22}[case]
        ax.scatter(vals, y + dy, color=col, marker=mk, s=40, label=lab, zorder=3, edgecolor=SURFACE, lw=1)
    ax.axvline(0, color=MUTED, lw=1)
    labels = []
    for cf, w in rows:
        tp = f[(f.weekday_peak_config == cf) & (f.peak_width == w)]["three_weekday_peaks_retained"].iloc[0]
        labels.append(f"{cf.replace('_dominant', '-dom.').replace('_', '-')}, {w}" + ("" if tp else " *"))
    ax.set_yticks(y, labels, fontsize=8.3)
    ax.set_xlabel("Change vs existing reference profile (MW)")
    ax.set_title("Effect on maximum BEV load (20% xEV base)")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=3)
    _foot(fig, NOTE + "Width = Gaussian edge smoothing sigma: narrow 0.5 h, default 0.75 h, wide 1.0 h; * = one weekday peak merges at this width. Weekend multiplier 1.0.")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    _save(fig, "fig33_weekday_peak_magnitude_sensitivity.png")


def fig_multiplier(ctx):
    _style()
    cal, ac, comp = ctx["cal"], ctx["ac_series"], ctx["comp"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    ax = axes[0]
    hr = cal["hour"].values
    wk = (cal["behaviour_day_type"] == "weekday").values
    shades = {1.0: AQUA, 1.25: BLUE, 1.5: VIOLET}
    for m in C.INDUSTRY_WEEKEND_MULTIPLIERS:
        vn = IND if m == 1.0 else f"{IND}__weekend_x{m:.2f}"
        v = ac[("20pct_xev", "base_17969km", vn)]
        for mask, ls, dl in ((wk, "--", "weekday"), (~wk, "-", "weekend")):
            _step(ax, np.array([v[mask & (hr == h)].mean() for h in range(24)]), color=shades[m], ls=ls, lw=1.9,
                  label=f"m = {m:.2f}, {dl}")
    v = ac[("20pct_xev", "base_17969km", REF)]
    _step(ax, np.array([v[~wk & (hr == h)].mean() for h in range(24)]), color=REF_COL, ls=":", lw=1.4, label="Existing reference, weekend")
    ax.set_title("Average public AC load by weekend:weekday daily-energy multiplier m")
    ax.set_ylabel("Average public AC load (MW)")
    _hours(ax)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=7.8, loc="upper left", ncol=2)
    ax = axes[1]
    d = comp[(comp.adoption_scenario == "20pct_xev") & (comp.mileage_case == "base_17969km") & (comp.charging_scenario == "unmanaged")]
    sh = d[d.public_ac_profile.str.startswith(IND)].sort_values("weekend_energy_multiplier")
    rf = d[d.public_ac_profile == REF].iloc[0]
    for col, c, lab in (("max_load_weekday_mw", BLUE, "Total BEV, weekday max"), ("max_load_weekend_holiday_mw", AQUA, "Total BEV, weekend max"),
                        ("public_ac_max_weekend_holiday_mw", VIOLET, "Public AC alone, weekend max")):
        ax.plot(sh.weekend_energy_multiplier, sh[col], marker="o", color=c, label=lab)
        ax.axhline(rf[col], color=c, ls=":", lw=1.1)
        for x, yv in zip(sh.weekend_energy_multiplier, sh[col]):
            ax.annotate(f"{yv:.0f}", (x, yv), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=7.8, color=INK2)
    ax.set_xticks(C.INDUSTRY_WEEKEND_MULTIPLIERS)
    ax.set_xlabel("Weekend:weekday public AC energy per vehicle-day (hypothetical m)")
    ax.set_ylabel("Maximum hourly load (MW)")
    ax.set_ylim(0, 420)
    ax.set_title("Unmanaged maxima vs m (dotted = existing reference)")
    ax.legend(fontsize=8, loc="center right")
    _foot(fig, NOTE + "Annual public AC energy fixed at 192.7 GWh: raising weekend energy lowers weekday energy (joint normalization).")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig34_weekend_multiplier_sensitivity.png")


def fig_managed(ctx):
    _style()
    comp, sens = ctx["comp"], ctx["sens"]
    d = comp[(comp.adoption_scenario == "20pct_xev") & (comp.mileage_case == "base_17969km")]
    occ = sens[sens.sensitivity_dimension == "activity_interpretation_occupancy_basis"]
    cases = [n for n, _, _ in C.P31_CHARGING_CASES]
    labs = ["Unmanaged", "ToU 50%\nstaggered", "ToU 100%\nstaggered", "ToU 50%\nsync 22:00", "ToU 100%\nsync 22:00"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), sharey=True)
    for ax, col, ttl in ((axes[0], "max_load_mw", "Maximum hourly BEV load (any day)"), (axes[1], "max_load_weekday_mw", "Maximum WEEKDAY BEV load")):
        x = np.arange(len(cases))
        series = [("Existing public AC", REF_COL, [d[(d.public_ac_profile == REF) & (d.charging_scenario == c)][col].iloc[0] for c in cases]),
                  ("Industry-informed (default)", SH_COL, [d[(d.public_ac_profile == IND) & (d.charging_scenario == c)][col].iloc[0] for c in cases]),
                  ("Industry timing read as occupancy", ORANGE, [occ[occ.charging_scenario == c][col].iloc[0] for c in cases])]
        w = 0.27
        for i, (lab, c, vals) in enumerate(series):
            ax.bar(x + (i - 1) * w, vals, width=w - 0.02, color=c, label=lab, edgecolor=SURFACE)
            for xi, v in zip(x + (i - 1) * w, vals):
                ax.annotate(f"{v:.0f}", (xi, v), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.3, color=INK2, rotation=90)
        ax.set_xticks(x, labs, fontsize=8.5)
        ax.set_title(ttl + " - 20% xEV base")
        ax.set_ylim(0, 1150)
    axes[0].set_ylabel("MW")
    axes[0].legend(fontsize=8.3, loc="upper left")
    _foot(fig, NOTE + "BEV charging maxima only - NOT the electricity-system peak (GSO demand profile not yet integrated).")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig35_bev_maximum_by_managed_case.png")


def make_all(ctx):
    fig_shape(ctx, "weekday", "fig26_public_ac_weekday_existing_vs_industry.png", "Public AC / destination charging - weekday shape: existing vs industry-informed")
    fig_shape(ctx, "weekend_holiday", "fig27_public_ac_weekend_existing_vs_industry.png", "Public AC / destination charging - weekend & holiday shape: existing vs industry-informed")
    fig_decomp(ctx, "weekday", "fig28_weekday_three_peak_profile.png", "Industry-informed weekday profile: three peaks (lunch, after work, dinner)")
    fig_decomp(ctx, "weekend_holiday", "fig29_weekend_afternoon_plateau.png", "Industry-informed weekend profile: sustained 12:00-16:00 plateau")
    fig_combined(ctx)
    fig_stacked_day(ctx, "2030-12-31", "fig31_location_stacked_weekday.png", "Location-stacked hourly load, Tuesday 31 Dec 2030 (day of the 2030 BEV maximum)")
    fig_stacked_day(ctx, "2030-12-29", "fig32_location_stacked_weekend.png", "Location-stacked hourly load, Sunday 29 Dec 2030 (day of the 2030 weekend maximum)")
    fig_magnitudes(ctx)
    fig_multiplier(ctx)
    fig_managed(ctx)

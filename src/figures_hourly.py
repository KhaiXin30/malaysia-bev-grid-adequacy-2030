"""Phase 3 figures (fig16-fig25). Same style and fixed entity colours as figures.py."""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

import config as C
import hourly as H
from figures import AQUA, BLUE, GRID, INK, INK2, MAGENTA, MUTED, ORANGE, SURFACE, YELLOW, _foot, _save, _style

LOC_COL = {"residential": BLUE, "workplace": YELLOW, "public_ac": AQUA, "public_dc": MAGENTA}
LOC_LAB = {"residential": "Residential", "workplace": "Workplace", "public_ac": "Public AC / destination", "public_dc": "Public DC fast"}
SCEN_COL = {"20pct_xev": BLUE, "30pct_xev": ORANGE, "historical_trend": AQUA}
SCEN_LAB = {"20pct_xev": "20% xEV (primary)", "30pct_xev": "30% xEV (sensitivity)", "historical_trend": "Historical trend"}
NOTE = ("Peninsular Malaysia, 2030, MYT (UTC+08:00), grid energy at the charger input (incl. charging losses, excl. T&D). "
        "Profiles are modelled from US reference behaviour adapted to Malaysia - not observed Malaysian charging. ")


def _shade_peak(ax, hours=True):
    ax.axvspan(14, 22, color=ORANGE, alpha=0.07, lw=0)
    ax.text(18, 0.98, "TNB peak (Mon-Fri)", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=8, color=INK2)


def _hours(ax):
    ax.set_xticks(range(0, 25, 3))
    ax.set_xlim(0, 24)
    ax.set_xlabel("Hour of day (MYT, hour-beginning)")


def _step(ax, v, **kw):
    x = np.arange(25)
    ax.step(x, np.append(v, v[-1]), where="post", **kw)


def fig_residential(ctx):
    _style()
    sh = ctx["shapes"]["residential"]
    fig, ax = plt.subplots(figsize=(11, 5))
    _shade_peak(ax)
    for key, col, lab, ls in [(("weekday", "unmanaged"), BLUE, "Unmanaged (weekday & weekend)", "-"),
                              (("weekday", "staggered"), AQUA, "ToU-managed, staggered start (weekday, 100% participation)", "-"),
                              (("weekday", "synchronized"), ORANGE, "ToU-managed, all start at 22:00 (weekday, 100%)", "--")]:
        _step(ax, H.fold24(sh[key]) * 100, color=col, lw=2, ls=ls, label=lab)
    ev = H.evipro_profiles()[("residential", "weekday")] * 100
    _step(ax, ev, color=MUTED, lw=1.3, ls=":", label="EVI-Pro Lite home, weekday (US simulation, reference)")
    ax.set_ylabel("% of daily residential charging energy")
    ax.set_title("Residential charging - normalized 24-hour profiles")
    _hours(ax)
    ax.legend(fontsize=8.3, loc="upper left")
    _foot(fig, NOTE + "Session model: plug-in/unplug timing from Liu et al. (2024) Figs 10-11 (approx. reading); Malaysian charger power/session energy assumed.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig16_residential_normalized_profiles.png")


def fig_workplace(ctx):
    _style()
    prof = ctx["prof"]
    fig, ax = plt.subplots(figsize=(11, 5))
    _shade_peak(ax)
    wk = H.fold24(ctx["shapes"]["workplace"][("weekday", "unmanaged")]) * 100
    _step(ax, wk, color=YELLOW, lw=2.2, label="Model: Malaysia (7.4/11 kW AC), unmanaged")
    ref = prof[prof.profile_type == "source_reference"]
    for name, col, ls, lab in [("Session model with NREL 3.3/6.6 kW mix (validation run)", INK2, "-", "Model with NREL 3.3/6.6 kW charger mix"),
                               ("NREL workplace Fig.15 pre-COVID power (observed, approx. reading)", BLUE, "--", "NREL campus, observed pre-COVID (Fig. 15, approx.)"),
                               ("EVI-Pro Lite weekday workplace (simulation)", MUTED, ":", "EVI-Pro Lite workplace (US simulation)")]:
        v = ref[ref.strategy == name].sort_values("hour")["value"].values * 100
        _step(ax, v, color=col, lw=1.6, ls=ls, label=lab)
    ax.set_ylabel("% of daily workplace charging energy")
    ax.set_title("Workplace charging - normalized weekday profiles and NREL validation")
    _hours(ax)
    ax.legend(fontsize=8.3, loc="upper right")
    _foot(fig, NOTE + "NREL: Neuman et al. (2021) NREL/TP-5400-77515; raw dataset unavailable (catalog offline), figure values read approximately.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig17_workplace_normalized_profiles.png")


def _avg_weekday(ctx, scen, case, mileage="base_17969km"):
    locs = ctx["profiles"][(scen, mileage, case)][1]
    wk = (ctx["cal"]["behaviour_day_type"] == "weekday").values
    hr = ctx["cal"]["hour"].values
    return {l: np.array([v[wk & (hr == h)].mean() for h in range(24)]) for l, v in locs.items()}


def _stack(ax, d):
    bottom = np.zeros(24)
    for loc in C.LOCATIONS:
        ax.bar(np.arange(24) + 0.5, d[loc], bottom=bottom, width=0.92, color=LOC_COL[loc], label=LOC_LAB[loc], edgecolor=SURFACE, lw=0.5)
        bottom += d[loc]
    return bottom


def fig_weekday(ctx, case, fname, title):
    _style()
    fig, ax = plt.subplots(figsize=(11, 5))
    _shade_peak(ax)
    tot = _stack(ax, _avg_weekday(ctx, "20pct_xev", case))
    ax.annotate(f"max {tot.max():,.0f} MW at {tot.argmax():02d}:00", (tot.argmax() + 0.5, tot.max()), xytext=(0, 6),
                textcoords="offset points", ha="center", fontsize=8.5, color=INK2)
    ax.set_ylabel("Average weekday charging load (MW)")
    ax.set_title(title)
    _hours(ax)
    ax.set_ylim(0, 420)
    ax.legend(fontsize=8.3, loc="upper left", ncol=2)
    _foot(fig, NOTE + "20% xEV base case (1,285 GWh/yr); average over all 2030 weekdays (includes fleet growth through the year).")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, fname)


def fig_week(ctx):
    _style()
    cal = ctx["cal"]
    sel = (cal["timestamp_local"] >= pd.Timestamp("2030-07-08", tz=C.LOCAL_TZ)) & (cal["timestamp_local"] < pd.Timestamp("2030-07-15", tz=C.LOCAL_TZ))
    t = cal.loc[sel, "timestamp_local"].dt.tz_localize(None)
    fig, ax = plt.subplots(figsize=(13, 5))
    pk = cal.loc[sel, "tnb_tou_period"].values == "peak"
    for i in np.where(pk)[0]:
        ax.axvspan(t.iloc[i], t.iloc[i] + pd.Timedelta(hours=1), color=ORANGE, alpha=0.07, lw=0)
    for case, col, lab, ls in [("unmanaged", BLUE, "Unmanaged", "-"), ("managed_staggered_p50", AQUA, "ToU-managed, 50% participation (provisional)", "-"),
                               ("managed_staggered_p100", INK2, "ToU-managed, 100% participation", "--")]:
        v = sum(ctx["profiles"][("20pct_xev", "base_17969km", case)][1].values())[sel.values]
        ax.step(t, v, where="post", color=col, lw=1.8, ls=ls, label=lab)
    ax.set_ylabel("Charging load (MW)")
    ax.set_title("Representative week, 8-14 July 2030 - 20% xEV base (shading = TNB peak hours)")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    ax.set_ylim(0, None)
    ax.legend(fontsize=8.5, loc="upper right")
    _foot(fig, NOTE)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig20_representative_week_unmanaged_vs_managed.png")


def fig_location_contrib(ctx):
    _style()
    cal = ctx["cal"]
    pk = cal["tnb_tou_period"].values == "peak"
    fig, ax = plt.subplots(figsize=(11, 5))
    cases = [("unmanaged", "Unmanaged"), ("managed_staggered_p50", "Managed 50%"), ("managed_staggered_p100", "Managed 100%")]
    x = np.arange(len(cases))
    for j, (period, mask, hatch) in enumerate([("TNB peak", pk, None), ("Off-peak", ~pk, "////")]):
        bottom = np.zeros(len(cases))
        for loc in C.LOCATIONS:
            vals = np.array([ctx["profiles"][("20pct_xev", "base_17969km", c)][1][loc][mask].sum() / 1000 for c, _ in cases])
            ax.bar(x + (j - 0.5) * 0.38, vals, bottom=bottom, width=0.36, color=LOC_COL[loc] if j == 0 else SURFACE,
                   edgecolor=LOC_COL[loc], hatch=hatch, lw=1.2, label=LOC_LAB[loc] if j == 0 else None)
            bottom += vals
        for xi, b in zip(x + (j - 0.5) * 0.38, bottom):
            ax.annotate(f"{period}\n{b:,.0f} GWh", (xi, b), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.8, color=INK2)
    ax.set_xticks(x, [c[1] for c in cases])
    ax.set_ylabel("Annual charging energy (GWh)")
    ax.set_title("Charging energy by location and TNB period - 20% xEV base (solid = peak, hatched = off-peak)")
    ax.set_ylim(0, 1400)
    ax.legend(fontsize=8.3, loc="upper left", ncol=2)
    _foot(fig, NOTE + "Location energy shares (base): residential 60%, workplace 5%, public AC 15%, public DC 20% - scenario assumption.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig21_location_contributions_peak_offpeak.png")


def fig_participation(ctx):
    _style()
    met = ctx["met"]
    m = met[(met.sensitivity == "main") & (met.mileage_case == "base_17969km")]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for s in ("20pct_xev", "30pct_xev", "historical_trend"):
        d = m[(m.adoption_scenario == s) & ~m.charging_scenario.str.contains("synchronized")].sort_values("participation_rate")
        axes[0].plot(d.participation_rate * 100, d.max_load_mw, marker="o", color=SCEN_COL[s], label=SCEN_LAB[s])
        axes[1].plot(d.participation_rate * 100, d.share_tnb_peak * 100, marker="o", color=SCEN_COL[s], label=SCEN_LAB[s])
        sy = m[(m.adoption_scenario == s) & m.charging_scenario.str.contains("synchronized")].sort_values("participation_rate")
        axes[0].plot(sy.participation_rate * 100, sy.max_load_mw, marker="x", ls="--", color=SCEN_COL[s], lw=1.2)
    axes[0].set_title("Maximum hourly BEV charging load vs ToU participation")
    axes[0].set_ylabel("Max BEV charging load (MW)")
    axes[1].set_title("Share of charging energy in TNB peak hours")
    axes[1].set_ylabel("% of annual charging energy")
    for ax in axes:
        ax.set_xlabel("Participation (% of residential charging sessions, ASSUMED)")
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_ylim(0, None)
    axes[0].legend(fontsize=8.3, loc="upper left")
    axes[0].text(0.98, 0.05, "dashed x = synchronized 22:00 starts", transform=axes[0].transAxes, ha="right", fontsize=8, color=INK2)
    axes[1].text(0.98, 0.92, "all three adoption scenarios coincide\n(same shapes and location mix)", transform=axes[1].transAxes,
                 ha="right", va="top", fontsize=8.5, color=INK2)
    _foot(fig, NOTE + "BEV-only peak; the effect on the SYSTEM peak depends on overlap with non-BEV demand (GSO data pending).")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig22_participation_vs_peak.png")


def fig_rebound(ctx):
    _style()
    fig, ax = plt.subplots(figsize=(11, 5))
    _shade_peak(ax)
    for case, col, lab, ls in [("unmanaged", BLUE, "Unmanaged", "-"), ("managed_staggered_p100", AQUA, "Managed 100%, staggered", "-"),
                               ("managed_synchronized_p50", YELLOW, "Managed 50%, all start 22:00", "--"),
                               ("managed_synchronized_p100", ORANGE, "Managed 100%, all start 22:00", "--")]:
        d = _avg_weekday(ctx, "20pct_xev", case)
        _step(ax, sum(d.values()), color=col, lw=2, ls=ls, label=lab)
    ax.set_ylabel("Average weekday charging load (MW)")
    ax.set_title("The 22:00 rebound: synchronized vs staggered ToU response - 20% xEV base")
    _hours(ax)
    ax.set_ylim(0, None)
    ax.legend(fontsize=8.5, loc="upper left")
    _foot(fig, NOTE + "Synchronized case = every participating home session starts at the first off-peak quarter-hour (22:00).")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig23_10pm_rebound.png")


def fig_monthly(ctx):
    _style()
    cal = ctx["cal"]
    fig, ax = plt.subplots(figsize=(11, 5))
    mon = cal["month"].values
    w = 0.27
    for i, s in enumerate(("20pct_xev", "30pct_xev", "historical_trend")):
        v = sum(ctx["profiles"][(s, "base_17969km", "unmanaged")][1].values())
        mm = np.array([v[mon == k].sum() / 1000 for k in range(1, 13)])
        ax.bar(np.arange(1, 13) + (i - 1) * w, mm, width=w, color=SCEN_COL[s], label=SCEN_LAB[s], edgecolor=SURFACE)
    ax.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylabel("Monthly charging energy (GWh)")
    ax.set_title("Monthly BEV charging energy, 2030 - fleet growth through the year (no seasonal travel factor)")
    ax.legend(fontsize=8.5, loc="upper left")
    _foot(fig, NOTE + "Monthly differences come from the growing active fleet (Phase 1.5 daily vehicle-days), days per month and weekday/weekend mix.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig24_monthly_charging_energy_2030.png")


def fig_sources(ctx):
    _style()
    ref = ctx["prof"][ctx["prof"].profile_type == "source_reference"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=False)
    ax = axes[0]
    v = ref[ref.strategy.str.startswith("Liu")].sort_values("hour")["value"].values * 100
    ax.bar(np.arange(24) + 0.5, v, width=0.9, color=MUTED, label="Liu et al. 2024: plug-in start (sessions, simulation)")
    _step(ax, H.fold24(ctx["shapes"]["residential"][("weekday", "unmanaged")]) * 100, color=BLUE, lw=2, label="This model: residential charging energy")
    _step(ax, H.evipro_profiles()[("residential", "weekday")] * 100, color=INK2, lw=1.3, ls=":", label="EVI-Pro Lite home energy (US sim.)")
    ax.set_title("Residential")
    ax = axes[1]
    for name, col, ls, lab in [("NREL workplace Fig.15 pre-COVID power (observed, approx. reading)", BLUE, "--", "NREL campus observed (approx.)"),
                               ("EVI-Pro Lite weekday workplace (simulation)", INK2, ":", "EVI-Pro Lite workplace")]:
        _step(ax, ref[ref.strategy == name].sort_values("hour")["value"].values * 100, color=col, ls=ls, lw=1.6, label=lab)
    _step(ax, H.fold24(ctx["shapes"]["workplace"][("weekday", "unmanaged")]) * 100, color=YELLOW, lw=2, label="This model (Malaysia)")
    ax.set_title("Workplace")
    ax = axes[2]
    for loc, col in (("public_ac", AQUA), ("public_dc", MAGENTA)):
        _step(ax, H.evipro_profiles()[(loc, "weekday")] * 100, color=col, lw=1.2, ls=":", label=f"EVI-Pro Lite {LOC_LAB[loc]} (raw)")
        _step(ax, H.fold24(ctx["shapes"][loc][("weekday", "unmanaged")]) * 100, color=col, lw=2, label=f"This model {LOC_LAB[loc]}")
    ax.set_title("Public")
    for ax in axes:
        _hours(ax)
        ax.set_ylabel("% of daily energy (or sessions)")
        ax.legend(fontsize=7.3, loc="upper left")
        ax.set_ylim(0, None)
    _foot(fig, "Sources: Liu et al. (2024) NREL/CP-5400-89286; Neuman et al. (2021) NREL/TP-5400-77515; EVI-Pro Lite API (30 C, 35 mi/day, BEV). "
               "Figure values from PDFs are approximate visual readings, not published data.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig25_source_profile_comparison.png")


def make_all(ctx):
    fig_residential(ctx)
    fig_workplace(ctx)
    fig_weekday(ctx, "unmanaged", "fig18_unmanaged_typical_weekday.png", "Unmanaged charging - average 2030 weekday by location (20% xEV base)")
    fig_weekday(ctx, f"managed_staggered_p{int(C.PROVISIONAL_PARTICIPATION * 100)}", "fig19_managed_typical_weekday.png",
                "ToU-managed charging (50% participation, staggered) - average 2030 weekday (20% xEV base)")
    fig_week(ctx)
    fig_location_contrib(ctx)
    fig_participation(ctx)
    fig_rebound(ctx)
    fig_monthly(ctx)
    fig_sources(ctx)

"""Phase 1.5 figures (fig09-fig12). Same style and fixed entity colours as figures.py."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

import config as C
from figures import (BLUE, GRID, INK, INK2, MUTED, ORANGE, SCEN, SCEN_LABEL, SOURCE_NOTE, SURFACE, _foot, _save,
                     _style, _thousands)

ORDER = ["policy_20pct", "policy_30pct", "historical_trend"]
PEN_NOTE = "Peninsular = estimate from JPJ state-of-registration proxy x cohort share; not an observed operating fleet."


def _k(v):
    return f"{v / 1000:,.0f}k"


def fig_new_registrations(expo: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.0), sharey=True)
    width = 0.26
    for ax, geo, title in [(axes[0], "national", "New BEV registrations - Malaysia (national)"),
                           (axes[1], "peninsular", "New BEV registrations - Peninsular Malaysia (estimated)")]:
        d = expo[expo.geography == geo]
        for y in (2025, 2026):
            v = d[(d.year == y) & (d.case == "base")]["new_registrations"].iloc[0]
            ax.bar(y, v, width=0.5, color=INK2 if y == 2025 else SURFACE, edgecolor=INK2, hatch=None if y == 2025 else "////", lw=1.2)
            ax.annotate(_k(v), (y, v), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8, color=INK2)
        for i, scen in enumerate(ORDER):
            p = d[d.scenario == scen].pivot_table(index="year", columns="case", values="new_registrations").loc[2027:]
            x = p.index.values + (i - 1) * (width + 0.02)
            ax.bar(x, p["base"], width=width, color=SCEN[scen], label=SCEN_LABEL[scen], edgecolor=SURFACE, lw=1)
            ax.errorbar(x, p["base"], yerr=[p["base"] - p["low"], p["high"] - p["base"]], fmt="none", ecolor=INK, elinewidth=1, capsize=2.5)
        ax.set_title(title)
        _thousands(ax)
        ax.set_xticks(C.EXPOSURE_YEARS, ["2025\nobserved", "2026\nJan-Oct obs.\n+ Nov-Dec est."] + [str(y) for y in range(2027, 2031)])
    axes[0].set_ylabel("BEV registrations per year")
    axes[0].legend(loc="upper left", fontsize=8.5)
    _foot(fig, SOURCE_NOTE + "Bars = base case; whiskers = low-high envelopes (not confidence intervals). " + PEN_NOTE)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig09_new_bev_registrations_2025_2030.png")


def fig_eoy_vs_average(trajs: dict, expo: pd.DataFrame):
    """trajs: {scenario: daily trajectory DataFrame} for the Peninsular base case."""
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=True)
    for ax, scen in zip(axes, ORDER):
        t = trajs[scen]
        t = t[t.date >= "2024-12-31"]
        ax.plot(t.date, t.stock_end_of_day, color=SCEN[scen], lw=1.6, label="Active stock N(t), daily")
        a = expo[(expo.scenario == scen) & (expo.case == "base") & (expo.geography == "peninsular")].set_index("year")
        for i, y in enumerate(C.EXPOSURE_YEARS):
            x0, x1 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
            ax.hlines(a.loc[y, "stock_annual_average"], x0, x1, color=INK, lw=2.2, label="Annual average" if i == 0 else None)
            ax.plot([x1], [a.loc[y, "stock_end"]], "o", ms=6, color=SCEN[scen], mec=SURFACE, mew=1.5,
                    label="31 Dec stock" if i == 0 else None, zorder=5)
        y = C.FORECAST_END
        ax.text(0.97, 0.04, f"2030 annual average: {_k(a.loc[y, 'stock_annual_average'])}\n2030 31-Dec stock: {_k(a.loc[y, 'stock_end'])}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=INK,
                bbox=dict(boxstyle="round,pad=0.4", fc=SURFACE, ec=GRID))
        ax.set_title(SCEN_LABEL[scen] + " - base", fontsize=10.5)
        _thousands(ax)
        ax.xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y"))
    top = max(t["stock_end_of_day"].max() for t in trajs.values())
    axes[0].set_ylim(0, top * 1.06)
    axes[0].set_ylabel("Active BEVs, Peninsular Malaysia (estimated)")
    axes[0].legend(loc="upper left", fontsize=8.5)
    _foot(fig, SOURCE_NOTE + "N(t) = daily cohorts x Weibull survival. Annual average = time integral of N(t) / 1 year; "
               "use it, not the 31-Dec stock, for annual energy. " + PEN_NOTE)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig10_eoy_vs_average_stock_peninsular.png")


def fig_scenario_comparison(expo: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    d = expo[expo.geography == "peninsular"]
    ends = []
    for scen in ORDER:
        p = d[d.scenario == scen].pivot_table(index="year", columns="case", values="stock_annual_average")
        ax.fill_between(p.index, p["low"], p["high"], color=SCEN[scen], alpha=0.13, lw=0)
        ax.plot(p.index, p["base"], color=SCEN[scen], marker="o", ms=4, mec=SURFACE, label=SCEN_LABEL[scen])
        ends.append((p["base"].iloc[-1], scen))
    ends.sort()
    last_y = -1e9
    for v, scen in ends:
        yy = max(v, last_y + 26000)
        ax.annotate(_k(v), (C.FORECAST_END, v), xytext=(C.FORECAST_END + 0.12, yy), textcoords="data", va="center", fontsize=8.5, color=INK2)
        last_y = yy
    ax.set_title("Annual average active BEVs - Peninsular Malaysia (estimated)")
    ax.set_xlim(2024.7, C.FORECAST_END + 0.6)
    ax.set_xticks(C.EXPOSURE_YEARS)
    _thousands(ax)
    ax.set_ylim(0, None)
    ax.set_ylabel("Vehicles (annual average)")
    ax.legend(loc="upper left", fontsize=8.5)

    ax = axes[1]
    d30 = d[d.year == C.FORECAST_END].set_index(["scenario", "case"])
    x = np.arange(len(ORDER))
    for i, scen in enumerate(ORDER):
        for j, (col, lab) in enumerate([("stock_annual_average", "Annual average"), ("stock_end", "31 Dec stock")]):
            b, lo, hi = (d30.loc[(scen, c), col] for c in ("base", "low", "high"))
            xx = i + (j - 0.5) * 0.36
            ax.bar(xx, b, width=0.34, color=SCEN[scen] if j == 0 else SURFACE, edgecolor=SCEN[scen], lw=1.6,
                   hatch=None if j == 0 else "////", label=lab if i == 0 else None)
            ax.errorbar(xx, b, yerr=[[b - lo], [hi - b]], fmt="none", ecolor=INK, elinewidth=1, capsize=2.5)
            ax.annotate(_k(b), (xx, hi), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(x, ["20% xEV\n(primary)", "30% xEV\n(sensitivity)", "Historical\ntrend"])
    ax.set_title("2030: annual average vs 31-Dec stock (Peninsular)")
    _thousands(ax)
    leg = ax.legend(loc="upper left", fontsize=8.5)
    for h in leg.legend_handles:
        h.set_edgecolor(INK2)
        h.set_facecolor(INK2 if h.get_label() == "Annual average" else SURFACE)
    _foot(fig, SOURCE_NOTE + "Lines/bars = base; bands/whiskers = combined low-high envelopes (not confidence intervals). " + PEN_NOTE)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig11_scenario_comparison_average_stock.png")


def fig_tornado(sens: pd.DataFrame, envelope: pd.DataFrame, baseline_scenario="20pct_xev"):
    _style()
    s = sens[(sens.baseline_scenario == baseline_scenario) & (sens.geography == "peninsular")]
    base = s[s.factor == "baseline"]["stock_annual_average_2030"].iloc[0]
    s = s[s.factor != "baseline"]
    rows = []
    for f, g in s.groupby("factor"):
        rows.append((f, g, g["delta_avg_vs_baseline"].abs().max()))
    rows.sort(key=lambda r: r[2])
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for i, (f, g, _) in enumerate(rows):
        for _, r in g.iterrows():
            dlt = r["delta_avg_vs_baseline"]
            col = BLUE if dlt >= 0 else ORANGE
            ax.barh(i, dlt, left=base, height=0.62, color=col, edgecolor=SURFACE, lw=1)
            ha, off = ("left", 4) if dlt >= 0 else ("right", -4)
            txt = f"{_k(r['stock_annual_average_2030'])} ({r['pct_avg_vs_baseline']:+.1%})"
            if not f.startswith("G"):
                txt = f"{r['setting']}\n" + txt
            ax.annotate(txt,
                        (base + dlt, i), xytext=(off, 0), textcoords="offset points", ha=ha, va="center", fontsize=7.3, color=INK2)
    ax.axvline(base, color=INK, lw=1.2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=9)
    env = envelope[(envelope.baseline_scenario == baseline_scenario) & (envelope.geography == "peninsular")].iloc[0]
    ax.set_title(f"2030 Peninsular annual-average BEV stock: one-at-a-time sensitivity (baseline 20% xEV base = {_k(base)})")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: _k(v)))
    lo = min(base + s["delta_avg_vs_baseline"].min(), base) - 120000
    hi = max(base + s["delta_avg_vs_baseline"].max(), base) + 150000
    ax.set_xlim(lo, hi)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("2030 annual average active BEVs, Peninsular Malaysia (estimated)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="raises the estimate"), Patch(color=ORANGE, label="lowers the estimate")],
              loc="lower right", fontsize=8.5)
    _foot(fig, SOURCE_NOTE + f"One-at-a-time changes around the baseline; other assumptions held at base. Combined envelope "
               f"(all-low / all-high): {_k(env['envelope_low'])}-{_k(env['envelope_high'])}. Ranges are scenario ranges, "
               "not statistical confidence intervals. " + PEN_NOTE)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig12_tornado_2030_peninsular_average_stock.png")

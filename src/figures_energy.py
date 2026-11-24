"""Phase 2 figures (fig13-fig15). Same style and fixed entity colours as figures.py."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

import config as C
from figures import (AQUA, BLUE, GRID, INK, INK2, MUTED, ORANGE, SURFACE, YELLOW, _foot, _save, _style)

SCEN = {"20pct_xev": BLUE, "30pct_xev": ORANGE, "historical_trend": AQUA}
LABEL = {"20pct_xev": "20% xEV policy (primary)", "30pct_xev": "30% xEV policy (sensitivity)", "historical_trend": "Historical trend"}
ORDER = ["20pct_xev", "30pct_xev", "historical_trend"]
NOTE = ("Source: JPJ via data.gov.my; Phase 1.5 vehicle-years; mileage MIROS; consumption EV Database + Malaysian road tests; "
        "charging efficiency fueleconomy.gov/ADAC. Grid-side energy at the charger input; T&D losses excluded. ")


def _gwh(ax):
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.0f}"))


def fig_energy(et: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    d = et[et.geography == "peninsular"]
    ends = []
    for s in ORDER:
        p = d[d.scenario == s].pivot_table(index="year", columns="case", values="annual_grid_energy_gwh")
        ax.fill_between(p.index, p["low"], p["high"], color=SCEN[s], alpha=0.12, lw=0)
        ax.plot(p.index, p["base"], color=SCEN[s], marker="o", ms=4, mec=SURFACE, label=LABEL[s])
        ends.append((p["base"].iloc[-1], s))
    last = -1e9
    for v, s in sorted(ends):
        yy = max(v, last + 75)
        ax.annotate(f"{v:,.0f} GWh", (C.FORECAST_END, v), xytext=(C.FORECAST_END + 0.12, yy), textcoords="data", va="center", fontsize=8.5, color=INK2)
        last = yy
    ax.set_title("BEV charging electricity - Peninsular Malaysia (estimated)")
    ax.set_xlim(2024.7, C.FORECAST_END + 0.9)
    ax.set_xticks(C.ENERGY_YEARS)
    ax.set_ylim(0, None)
    _gwh(ax)
    ax.set_ylabel("GWh per year (grid side)")
    ax.legend(loc="upper left", fontsize=8.5)

    ax = axes[1]
    d30 = et[et.year == C.FORECAST_END].set_index(["scenario", "case", "geography"])["annual_grid_energy_gwh"]
    for i, s in enumerate(ORDER):
        for j, geo in enumerate(["national", "peninsular"]):
            b, lo, hi = (d30.loc[(s, c, geo)] for c in ("base", "low", "high"))
            x = i + (j - 0.5) * 0.36
            ax.bar(x, b, width=0.34, color=SCEN[s] if geo == "peninsular" else SURFACE, edgecolor=SCEN[s], lw=1.6,
                   hatch=None if geo == "peninsular" else "////", label=("Peninsular (estimated)" if geo == "peninsular" else "National") if i == 0 else None)
            ax.errorbar(x, b, yerr=[[b - lo], [hi - b]], fmt="none", ecolor=INK, elinewidth=1, capsize=2.5)
            ax.annotate(f"{b:,.0f}", (x, b), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.8, color=INK2)
    ax.set_xticks(range(3), ["20% xEV\n(primary)", "30% xEV\n(sensitivity)", "Historical\ntrend"])
    ax.set_title("2030 annual grid energy (GWh)")
    _gwh(ax)
    leg = ax.legend(loc="upper left", fontsize=8.5)
    for h in leg.legend_handles:
        h.set_edgecolor(INK2)
        h.set_facecolor(INK2 if h.get_label().startswith("Peninsular") else SURFACE)
    _foot(fig, NOTE + "Lines/bars = base; bands/whiskers = combined low-high envelopes (not confidence intervals).")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig13_bev_grid_energy_2025_2030.png")


def fig_tornado(sens: pd.DataFrame, env: pd.DataFrame):
    _style()
    s = sens[sens.geography == "peninsular"]
    base = s[s.factor.str.startswith("baseline")]["grid_energy_gwh_2030"].iloc[0]
    s = s[~s.factor.str.startswith("baseline")]
    rows = sorted(((f, g, g["delta_gwh"].abs().max()) for f, g in s.groupby("factor")), key=lambda r: r[2])
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for i, (f, g, _) in enumerate(rows):
        for _, r in g.iterrows():
            dl = r["delta_gwh"]
            ax.barh(i, dl, left=base, height=0.62, color=BLUE if dl >= 0 else ORANGE, edgecolor=SURFACE, lw=1)
            ha, off = ("left", 4) if dl >= 0 else ("right", -4)
            ax.annotate(f"{r['setting']}\n{r['grid_energy_gwh_2030']:,.0f} GWh ({r['pct_vs_baseline']:+.1%})", (base + dl, i), xytext=(off, 0),
                        textcoords="offset points", ha=ha, va="center", fontsize=7.3, color=INK2)
    ax.axvline(base, color=INK, lw=1.2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=9)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(base + s['delta_gwh'].min() - 330, base + s['delta_gwh'].max() + 380)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlabel("2030 grid electricity for BEV charging, Peninsular Malaysia (GWh)")
    ax.set_title(f"2030 Peninsular BEV charging electricity: one-at-a-time sensitivity (baseline 20% xEV base = {base:,.0f} GWh)")
    ax.legend(handles=[Patch(color=BLUE, label="raises the estimate"), Patch(color=ORANGE, label="lowers the estimate")], loc="upper right", fontsize=8.5)
    e = env[(env.scenario == "20pct_xev") & (env.geography == "peninsular")].iloc[0]
    _foot(fig, NOTE + f"Other assumptions held at base. Combined envelope 20% xEV: {e['envelope_low_gwh']:,.0f}-{e['envelope_high_gwh']:,.0f} GWh "
                      "(scenario range, not a confidence interval).")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig14_energy_tornado_2030_peninsular.png")


def fig_consumption(mapping: pd.DataFrame, obs: pd.DataFrame, par_base: pd.DataFrame, factors: dict):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.0), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axes[0]
    top = mapping.head(15).iloc[::-1]
    y = np.arange(len(top))
    cols = [BLUE if t.startswith("direct") else (AQUA if t.startswith("twin") else YELLOW) for t in top.mapping_type]
    ax.barh(y, top.evdb_kwh_per_100km_battery, color=cols, height=0.62, edgecolor=SURFACE)
    for yi, (v, sh) in enumerate(zip(top.evdb_kwh_per_100km_battery, top.share_2022_2026oct)):
        ax.annotate(f"{v:.1f}  ({sh:.1%} of 2022-26 BEVs)", (v, yi), xytext=(4, 0), textcoords="offset points", va="center", fontsize=7.6, color=INK2)
    ax.set_yticks(y, [f"{a} {b}" for a, b in zip(top.maker, top.model)], fontsize=8.5)
    ax.set_xlim(0, 30)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("EV Database real-world 'Vehicle' consumption, kWh/100 km (battery side)")
    ax.set_title("Top-15 JPJ BEV models and the consumption value used")
    ax.legend(handles=[Patch(color=BLUE, label="direct match"), Patch(color=AQUA, label="twin model"), Patch(color=YELLOW, label="segment proxy (assumption)")],
              loc="upper center", bbox_to_anchor=(0.45, -0.11), ncol=3, fontsize=8)

    ax = axes[1]
    p30 = par_base.set_index("year").loc[C.FORECAST_END]
    items = []
    for _, r in obs.iterrows():
        items.append((f"{r['id']} {r['model']} (observed{'' if r['used_for_low_factor'] else ', not used'})", r["observed_kwh_per_100km"], MUTED))
    evf = p30["evdb_fleet_kwh_per_100km"]
    items += [("EVDB fleet-weighted, 2030 fleet (model-weighted)", evf, BLUE),
              ("EVDB all-model average (generic, unweighted)", C.EVDB_ALL_MODELS_AVERAGE_WH_PER_KM / 10, ORANGE),
              ("Case LOW battery-side (x%.3f)" % factors["low"], factors["low"] * evf, INK),
              ("Case BASE battery-side (x%.3f)" % factors["base"], factors["base"] * evf, INK),
              ("Case HIGH battery-side (x1.000)", evf, INK),
              ("BASE grid-side (BASE / 0.90)", factors["base"] * evf / C.CHARGING_EFFICIENCY["base"], AQUA)]
    items += [(f"{rid} {name} (rated, plug-side)", v, YELLOW) for rid, name, v, _, _ in C.RATED_REFERENCES]
    items = items[::-1]
    for i, (lab, v, col) in enumerate(items):
        ax.plot([v], [i], "o", ms=8, color=col, mec=SURFACE, mew=1.5)
        ax.annotate(f"{v:.1f}", (v, i), xytext=(7, 0), textcoords="offset points", va="center", fontsize=7.8, color=INK2)
    ax.set_yticks(range(len(items)), [it[0] for it in items], fontsize=7.6)
    ax.set_xlim(8, 22)
    ax.set_xlabel("kWh/100 km")
    ax.set_title("Model-weighted vs generic consumption and Malaysian evidence")
    _foot(fig, "Sources: EV Database (E07-E08), Malaysian/Singapore road tests (E09-E15), JPJ transactions (model mix). Observed road-test values are "
               "journalist trip-computer or derived readings - small, non-random sample. Battery side unless labelled plug-side.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig15_consumption_model_weighted_vs_generic.png")

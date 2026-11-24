"""Publication-quality PNG figures (matplotlib). Static output -> direct labels + legends,
single y-axis per panel, fixed entity colours (validated reference categorical palette)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

import config as C

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                                                      "#e87ba4", "#008300", "#6250d6")
ENTITY = {"bev": BLUE, "hybrid": ORANGE, "xev": AQUA, "total": INK2}
SCEN = {"policy_20pct": BLUE, "policy_30pct": ORANGE, "historical_trend": AQUA}
SCEN_LABEL = {"policy_20pct": "20% xEV policy (primary)", "policy_30pct": "30% xEV policy (sensitivity)",
              "historical_trend": "Historical trend"}
SOURCE_NOTE = "Source: JPJ via data.gov.my (registrations_type_fuel, registration_transactions_car); model outputs. "


def _style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 11.5,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False,
        "lines.linewidth": 2.0, "font.family": "DejaVu Sans"})


def _thousands(ax):
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k" if abs(v) >= 1000 else f"{v:,.0f}"))


def _pct(ax, dec=0):
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=dec))


def _foot(fig, text):
    fig.text(0.01, 0.005, text, fontsize=7.5, color=MUTED, ha="left", va="bottom", wrap=True)


def _save(fig, name):
    C.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIGURES / name, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _endlabel(ax, x, y, text, color, dy=0):
    ax.annotate(text, (x, y), xytext=(6, dy), textcoords="offset points", va="center", fontsize=8.5, color=INK2,
                path_effects=None)
    ax.plot([x], [y], "o", ms=5, color=color, mec=SURFACE, mew=1.5, zorder=5)


def fig_monthly(m: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True, gridspec_kw={"height_ratios": [1, 1.25]})
    d = m.loc["2015-01-01":]
    ax = axes[0]
    ax.plot(d.index, d["total_cars"], color=ENTITY["total"], lw=1.6)
    ax.set_title("Monthly car registrations - all fuels (JPJ, Malaysia)")
    ax.set_ylabel("Vehicles per month"); _thousands(ax); ax.set_ylim(0, None)
    ax.axvspan(pd.Timestamp("2020-03-15"), pd.Timestamp("2020-05-31"), color=GRID, alpha=0.9, lw=0)
    ax.text(pd.Timestamp("2020-03-01"), 92000, "COVID-19 MCO\n(Mar-May 2020)", fontsize=8, color=INK2, ha="right", va="top")
    ax = axes[1]
    ax.plot(d.index, d["bev"], color=ENTITY["bev"], label="BEV (fuel = electric)")
    ax.plot(d.index, d["hybrid"], color=ENTITY["hybrid"], label="Hybrid (JPJ 'hybrid', incl. PHEV)")
    ax.set_title("Monthly BEV and hybrid car registrations")
    ax.set_ylabel("Vehicles per month"); _thousands(ax); ax.set_ylim(0, None)
    for dt, txt, yy, off in [("2025-12-01", "Dec 2025: CBU BEV\nincentive-expiry rush", d.loc["2025-12-01", "bev"], (-150, 8)),
                             ("2026-02-01", "Feb 2026: e.MAS 7 PHEV launch\n(PHEVs coded as hybrid)", d.loc["2026-02-01", "hybrid"], (-300, 75))]:
        ax.annotate(txt, (pd.Timestamp(dt), yy), xytext=off, textcoords="offset points", fontsize=8,
                    color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.legend(loc="upper left")
    _endlabel(ax, d.index[-1], d["bev"].iloc[-1], f"BEV {d['bev'].iloc[-1]:,.0f}", ENTITY["bev"], -9)
    _endlabel(ax, d.index[-1], d["hybrid"].iloc[-1], f"Hybrid {d['hybrid'].iloc[-1]:,.0f}", ENTITY["hybrid"], 9)
    _foot(fig, SOURCE_NOTE + f"Data to {m.index.max():%b %Y}.")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "fig01_monthly_registrations.png")


def fig_annual(af: pd.DataFrame, rep: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    ytd = rep[rep["period"].str.startswith("YTD")].iloc[0]
    years = list(range(2015, C.PARTIAL_YEAR + 1))
    ax = axes[0]
    vals = [af.loc[y, "total_cars"] for y in years]
    bars = ax.bar(years[:-1], vals[:-1], color=ENTITY["total"], width=0.7)
    ax.bar(C.PARTIAL_YEAR, ytd["total_cars"], color=ENTITY["total"], width=0.7)
    ax.bar(C.PARTIAL_YEAR, vals[-1] - ytd["total_cars"], bottom=ytd["total_cars"], color=SURFACE,
           edgecolor=ENTITY["total"], hatch="////", width=0.7, lw=0.8)
    ax.set_title("Annual car registrations - all fuels"); _thousands(ax)
    ax.set_xticks(years); ax.set_xticklabels([str(y)[2:] if y < C.PARTIAL_YEAR else "26*" for y in years])
    ax.set_ylabel("Vehicles per year")
    ax = axes[1]
    yrs = list(range(2019, C.PARTIAL_YEAR + 1))
    w = 0.38
    for i, (s, lab) in enumerate([("bev", "BEV"), ("hybrid", "Hybrid")]):
        x = np.array(yrs) + (i - 0.5) * w
        full = [af.loc[y, s] for y in yrs]
        ax.bar(x[:-1], full[:-1], width=w - 0.03, color=ENTITY[s], label=lab)
        ax.bar(x[-1], ytd[s], width=w - 0.03, color=ENTITY[s])
        ax.bar(x[-1], full[-1] - ytd[s], bottom=ytd[s], width=w - 0.03, color=SURFACE, edgecolor=ENTITY[s],
               hatch="////", lw=0.8)
        ax.text(x[-1], full[-1], f"{full[-1]/1000:,.0f}k", ha="center", va="bottom", fontsize=8, color=INK2)
        ax.text(x[-2], full[-2], f"{full[-2]/1000:,.1f}k", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_title("Annual BEV and hybrid car registrations"); _thousands(ax)
    ax.set_xticks(yrs); ax.set_xticklabels([str(y) if y < C.PARTIAL_YEAR else "2026*" for y in yrs])
    ax.legend(loc="upper left")
    _foot(fig, SOURCE_NOTE + "*2026: solid = Jan-Oct observed (YTD); hatched = Nov-Dec estimate (not observed).")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig02_annual_registrations.png")


def fig_shares(af: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    yrs = list(range(2020, C.PARTIAL_YEAR + 1))
    d = af.loc[yrs]
    ax = axes[0]
    for col, lab, colr in [("xev_share_of_cars", "xEV proxy (BEV + hybrid)", ENTITY["xev"]),
                           ("bev_share_of_cars", "BEV", ENTITY["bev"])]:
        ax.plot(yrs, d[col], color=colr, marker="o", ms=5, mec=SURFACE, label=lab)
        ax.annotate(f"{d[col].iloc[-1]:.1%}", (yrs[-1], d[col].iloc[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK2)
        ax.annotate(f"{d[col].loc[2025]:.1%}", (2025, d[col].loc[2025]), xytext=(-8, 8), textcoords="offset points",
                    ha="right", fontsize=8.5, color=INK2)
    ax.set_title("Share of all car registrations"); _pct(ax); ax.set_ylim(0, None); ax.legend(loc="upper left")
    ax.set_xticks(yrs); ax.set_xticklabels([str(y) if y < C.PARTIAL_YEAR else "2026*" for y in yrs])
    ax = axes[1]
    ax.plot(yrs, d["bev_share_of_xev"], color=ENTITY["bev"], marker="o", ms=5, mec=SURFACE)
    for y in yrs[2:]:
        ax.annotate(f"{d.loc[y, 'bev_share_of_xev']:.0%}", (y, d.loc[y, "bev_share_of_xev"]), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8.5, color=INK2)
    ax.set_title("BEV share of xEV-proxy registrations"); _pct(ax); ax.set_ylim(0, 0.8)
    ax.set_xticks(yrs); ax.set_xticklabels([str(y) if y < C.PARTIAL_YEAR else "2026*" for y in yrs])
    _foot(fig, SOURCE_NOTE + "*2026 = Jan-Oct observed shares (Nov-Dec estimate uses the same shares). "
               "Hybrid includes PHEV; registration shares are not sales shares.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig03_adoption_shares.png")


def fig_models(af: pd.DataFrame, tf: pd.DataFrame):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    hist_yrs = list(range(2020, C.PARTIAL_YEAR + 1))
    ax.plot(hist_yrs, af.loc[hist_yrs, "bev"], color=INK, marker="o", ms=5, mec=SURFACE, label="Observed (2026 partly estimated)")
    sel = tf[(tf["fit_start"] == C.TREND_FIT_START) & (tf["market_case"] == "base")]
    models = [("A_linear_counts", "A  Linear trend in counts", BLUE, "-"),
              ("D_linear_share", "D  Linear trend in share x market", ORANGE, "-"),
              ("C_logistic_share_K30", "C  Logistic share, K = 30%", AQUA, "-"),
              ("C_logistic_share_K50", "C  Logistic share, K = 50%", YELLOW, "-"),
              ("B_exponential_counts", "B  Exponential/CAGR (capped at market)", MAGENTA, "--")]
    ymax = 0
    for mname, lab, colr, ls in models:
        s = sel[sel["model"] == mname].set_index("year")["bev_registrations"]
        xs = [C.PARTIAL_YEAR] + list(s.index)
        ys = [af.loc[C.PARTIAL_YEAR, "bev"]] + list(s.values)
        ax.plot(xs, ys, color=colr, ls=ls, label=lab)
        if mname != "B_exponential_counts":
            ymax = max(ymax, max(ys))
            dy = {"A_linear_counts": -7, "D_linear_share": 7}.get(mname, 0)
            ax.annotate(f"{ys[-1]/1000:,.0f}k", (xs[-1], ys[-1]), xytext=(6, dy), textcoords="offset points",
                        va="center", fontsize=8.5, color=INK2)
    ax.set_ylim(0, ymax * 1.15)
    ax.text(2028.15, ymax * 1.1, "B leaves the frame: implies 100% of\nthe car market by 2030 (implausible)",
            fontsize=8, color=INK2, va="top")
    ax.set_title(f"Historical-trend model comparison - annual BEV registrations (fit {C.TREND_FIT_START}-2026E, base market)")
    ax.set_ylabel("BEV registrations per year"); _thousands(ax); ax.legend(loc="upper left", fontsize=8.5)
    ax.set_xticks(range(2020, C.FORECAST_END + 1))
    _foot(fig, SOURCE_NOTE + "Short series (5 informative points); backtests in trend_backtests.csv. Selected trend case: "
               "low = A, base = D, high = C (K = 30%).")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "fig04_trend_model_comparison.png")


def fig_forecasts(af: pd.DataFrame, fc: pd.DataFrame):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    hy = list(range(2020, C.PARTIAL_YEAR + 1))
    ax.plot(hy, af.loc[hy, "bev"], color=INK, marker="o", ms=5, mec=SURFACE, label="Observed (2026 = Jan-Oct + Nov-Dec est.)")
    for scen in ["historical_trend", "policy_30pct", "policy_20pct"]:
        d = fc[fc["scenario"] == scen].pivot_table(index="year", columns="case", values="bev_registrations")
        d = d.loc[C.PARTIAL_YEAR:]
        ax.fill_between(d.index, d["low"], d["high"], color=SCEN[scen], alpha=0.13, lw=0)
        ax.plot(d.index, d["base"], color=SCEN[scen], label=SCEN_LABEL[scen] + " - base (band: low-high)")
        ax.annotate(f"{d['base'].iloc[-1]/1000:,.0f}k", (d.index[-1], d["base"].iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=INK2)
    ax.set_title("Annual new BEV registrations, Malaysia (national) - scenarios to 2030")
    ax.set_ylabel("BEV registrations per year"); _thousands(ax); ax.set_ylim(0, None)
    ax.legend(loc="upper left", fontsize=8.5); ax.set_xticks(range(2020, C.FORECAST_END + 1))
    _foot(fig, SOURCE_NOTE + "Policy cases: total cars x xEV share path x BEV share within xEV. "
               "Trend band = model structure (A to C K30).")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "fig05_bev_registration_forecasts.png")


def fig_share_paths(af: pd.DataFrame, grid: pd.DataFrame, trend_cases: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    hy = list(range(2020, C.PARTIAL_YEAR + 1))
    ax = axes[0]
    ax.plot(hy, af.loc[hy, "xev_share_of_cars"], color=INK, marker="o", ms=5, mec=SURFACE, label="Observed xEV proxy share")
    for scen in ["policy_30pct", "policy_20pct"]:
        d = grid[(grid["scenario"] == scen) & (grid["market_case"] == "base") & (grid["bev_in_xev_case"] == "base")]
        ax.plot(d["year"], d["xev_share"], color=SCEN[scen], marker="o", ms=4, mec=SURFACE, label=SCEN_LABEL[scen])
        ax.annotate(f"{d['xev_share'].iloc[-1]:.0%}", (d["year"].iloc[-1], d["xev_share"].iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=INK2)
    ax.set_title("xEV share of new car registrations: observed and policy paths"); _pct(ax); ax.set_ylim(0, 0.33)
    ax.legend(loc="upper left", fontsize=8.5); ax.set_xticks(range(2020, C.FORECAST_END + 1))
    ax = axes[1]
    ax.plot(hy, af.loc[hy, "bev_share_of_cars"], color=INK, marker="o", ms=5, mec=SURFACE, label="Observed BEV share")
    for scen in ["historical_trend", "policy_30pct", "policy_20pct"]:
        if scen == "historical_trend":
            d = trend_cases[trend_cases["case"] == "base"][["year", "bev_share_of_cars"]]
            d = pd.concat([pd.DataFrame({"year": [C.PARTIAL_YEAR], "bev_share_of_cars": [af.loc[C.PARTIAL_YEAR, "bev_share_of_cars"]]}), d])
        else:
            d = grid[(grid["scenario"] == scen) & (grid["market_case"] == "base") & (grid["bev_in_xev_case"] == "base")]
        ax.plot(d["year"], d["bev_share_of_cars"], color=SCEN[scen], marker="o", ms=4, mec=SURFACE,
                label=SCEN_LABEL[scen].replace(" (", ", ").replace(")", "") + " - base")
        ax.annotate(f"{d['bev_share_of_cars'].iloc[-1]:.1%}", (d["year"].iloc[-1], d["bev_share_of_cars"].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK2)
    ax.set_title("BEV share of new car registrations (base cases)"); _pct(ax); ax.set_ylim(0, 0.2)
    ax.yaxis.set_major_locator(mtick.MultipleLocator(0.04))
    ax.legend(loc="upper left", fontsize=8.5); ax.set_xticks(range(2020, C.FORECAST_END + 1))
    _foot(fig, SOURCE_NOTE + "xEV target applied to JPJ car registrations (assumption A04). BEV share of xEV base = 2026 Jan-Oct level held.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig06_share_paths.png")


def fig_stock(st: pd.DataFrame, pen: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.0), sharey=True)
    for ax, data, title in [(axes[0], st, "Active BEV stock - Malaysia (national)"),
                            (axes[1], pen, "Active BEV stock - Peninsular Malaysia (estimated)")]:
        for scen in ["historical_trend", "policy_30pct", "policy_20pct"]:
            d = data[data["scenario"] == scen].pivot_table(index="year", columns="case", values="active_stock").loc[2022:]
            ax.fill_between(d.index, d["low"], d["high"], color=SCEN[scen], alpha=0.13, lw=0)
            ax.plot(d.index, d["base"], color=SCEN[scen], marker="o", ms=4, mec=SURFACE, label=SCEN_LABEL[scen])
            ax.annotate(f"{d['base'].iloc[-1]/1000:,.0f}k", (d.index[-1], d["base"].iloc[-1]), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=8.5, color=INK2)
        ax.set_title(title); _thousands(ax); ax.set_ylim(0, None); ax.set_xticks(range(2022, C.FORECAST_END + 1))
        ax.set_xlim(2021.7, C.FORECAST_END + 0.6)
    axes[0].set_ylabel("Active BEVs at 31 Dec (cohort x survival)")
    axes[0].legend(loc="upper left", fontsize=8.5)
    _foot(fig, SOURCE_NOTE + "Stock = sum of cohorts x Weibull survival (not cumulative registrations). Bands: low-high envelopes. "
               "Peninsular = registration-state proxy, not operating location.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig07_active_bev_stock.png")


def fig_peninsular_share(bd: pd.DataFrame, allcars: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    b = bd[bd["year"] >= 2021]
    ax = axes[0]
    ax.plot(b["year"], b["known_state_peninsular_share"], color=BLUE, marker="o", ms=5, mec=SURFACE,
            label="BEV - state-identified rows only")
    ax.plot(b["year"], b["maker_reweighted_peninsular_share"], color=ORANGE, marker="o", ms=5, mec=SURFACE,
            label="BEV - maker-reweighted (incl. Rakan Niaga)")
    a = allcars[allcars["year"] >= 2021]
    ax.plot(a["year"], a["known_state_peninsular_share"], color=AQUA, marker="o", ms=5, mec=SURFACE,
            label="All cars - state-identified rows only")
    ax.set_ylim(0.7, 1.0); _pct(ax); ax.set_title("Peninsular share of registrations (registration-state proxy)")
    ax.legend(loc="lower left", fontsize=8.5)
    ax = axes[1]
    ax.plot(b["year"], b["rakan_niaga_share"], color=BLUE, marker="o", ms=5, mec=SURFACE, label="BEV")
    ax.plot(a["year"], a["rakan_niaga_share"], color=AQUA, marker="o", ms=5, mec=SURFACE, label="All cars")
    ax.set_ylim(0, 1); _pct(ax); ax.set_title("Share registered via 'Rakan Niaga' partner portal (state unknown)")
    ax.legend(loc="lower right", fontsize=8.5)
    _foot(fig, "Source: JPJ car registration transactions via data.gov.my. State = JPJ office of registration, not residence or "
               "operating location. Peninsular excludes Sabah, Sarawak, W.P. Labuan.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig08_peninsular_share_evidence.png")

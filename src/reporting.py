"""Step 8 - write machine-readable CSVs, the Excel workbook and the LEAP input table."""
import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import config as C
from data_io import load_transactions

NAT = "Malaysia (national)"
PEN = "Peninsular Malaysia"


def assumptions_table() -> pd.DataFrame:
    a = pd.DataFrame(C.ASSUMPTIONS, columns=["id", "category", "item", "value", "unit", "status", "source_ids", "note"])
    a.insert(0, "record_type", "assumption_or_definition")
    s = pd.DataFrame([dict(record_type="source", id=k, category="source", item=v["name"], value=v["url"],
                           unit="", status=v["publisher"], source_ids=k,
                           note=(v["note"] + (f" File: {v['file_url']}" if v["file_url"] else "")))
                      for k, v in C.SOURCES.items()])
    out = pd.concat([a, s], ignore_index=True)
    out["retrieval_date"] = C.RETRIEVAL_DATE
    return out


def sources_table() -> pd.DataFrame:
    return pd.DataFrame([dict(id=k, retrieval_date=C.RETRIEVAL_DATE, **v) for k, v in C.SOURCES.items()])


def crosscheck_table(m, af) -> pd.DataFrame:
    tx = load_transactions()
    tesla25 = int(((tx["year"] == 2025) & (tx["fuel"] == "electric") & (tx["maker"] == "Tesla")).sum())
    h1_26 = int(m.loc["2026-01-01":"2026-06-01", "bev"].sum())
    cum_nov23 = int(m.loc[:"2023-11-01", "bev"].sum())
    ytd_nov23 = int(m.loc["2023-01-01":"2023-11-01", "bev"].sum())
    r = [
        ("BEV car registrations 2025 (JPJ aggregate, fuel=electric, type=car)", int(af.loc[2025, "bev"]), 44813,
         "cited figure 44,813 (The Star/RHB 'JPJ ... 44,800'; paultan 44,813)", "exact match - same definition (JPJ registrations, cars)"),
        ("BEV 2025 - MAA sales basis", int(af.loc[2025, "bev"]), C.MAA["bev_2025"], "S09 AutoBuzz quoting MAA",
         "JPJ exceeds MAA by 45%: MAA covers member-company sales; JPJ includes non-MAA brands (e.g. Tesla: "
         f"{tesla25:,} JPJ BEV registrations in 2025), used/grey imports, and counts by registration date."),
        ("Hybrid 2025 - JPJ 'hybrid' vs MAA HEV", int(af.loc[2025, "hybrid"]), C.MAA["hev_2025"], "S09",
         "JPJ hybrid is 19% BELOW MAA HEV - unresolved; possibly some hybrids (e.g. mild hybrids) coded petrol in JPJ, or MAA "
         "classification differences. Flagged for review."),
        ("xEV 2025 - JPJ proxy (BEV+hybrid) vs MAA xEV", int(af.loc[2025, "xev_proxy"]), C.MAA["xev_2025"], "S09", "different measures; JPJ +9.6%"),
        ("xEV share 2025 - JPJ proxy share of car registrations vs MITI 'of total cars registered'",
         round(af.loc[2025, "xev_share_of_cars"], 4), C.MITI_2026["xev_share_cars_registered_2025"], "S04", "consistent (8.73% vs 8.7%)"),
        ("xEV share 2025 - MAA xEV / TIV vs MITI 'of new vehicle sales'", round(C.MAA["xev_2025"] / C.MAA["tiv_2025"], 4),
         C.MITI_2026["xev_share_sales_2025"], "S04;S09", "consistent (8.45% vs 8.5%)"),
        ("Total car registrations 2025 (JPJ) vs MAA TIV 2025", int(af.loc[2025, "total_cars"]), C.MAA["tiv_2025"], "S05",
         "JPJ 'car' incl. pick-ups/window vans and non-MAA brands; MAA TIV incl. commercial vehicles"),
        ("BEV registrations 1H 2026 (JPJ) vs paultan JPJ figure", h1_26, 31738, "S13", "exact match"),
        ("Cumulative BEV car registrations 2011-Nov 2023 vs MITI Dec-2023 '>12,000 since 2011'", cum_nov23,
         C.MITI_2023["bev_cum_since_2011_gt"], "S03", "consistent with 'more than' statement"),
        ("BEV car registrations Jan-Nov 2023 vs MITI '>9,000 this year'", ytd_nov23, C.MITI_2023["bev_2023_ytd_gt"], "S03",
         "consistent with 'surpassing' statement"),
    ]
    return pd.DataFrame(r, columns=["item", "this_project_value", "reference_value", "reference_source", "interpretation"])


def forecast_table(af, policy_cases, trend_cases) -> pd.DataFrame:
    rows = []
    for scen in ["historical_trend", "policy_20pct", "policy_30pct"]:
        for case in ["low", "base", "high"]:
            rows.append(dict(year=C.BASE_YEAR, scenario=scen, case=case, value_status="observed",
                             total_cars=af.loc[2025, "total_cars"], xev_share=af.loc[2025, "xev_share_of_cars"],
                             xev_registrations=af.loc[2025, "xev_proxy"], bev_share_of_xev=af.loc[2025, "bev_share_of_xev"],
                             bev_registrations=af.loc[2025, "bev"], bev_share_of_cars=af.loc[2025, "bev_share_of_cars"],
                             assumption_set="observed JPJ registrations"))
            rows.append(dict(year=C.PARTIAL_YEAR, scenario=scen, case=case,
                             value_status="partial_estimated (Jan-Oct observed + Nov-Dec estimated)",
                             total_cars=af.loc[2026, "total_cars"], xev_share=af.loc[2026, "xev_share_of_cars"],
                             xev_registrations=af.loc[2026, "xev_proxy"], bev_share_of_xev=af.loc[2026, "bev_share_of_xev"],
                             bev_registrations=af.loc[2026, "bev"], bev_share_of_cars=af.loc[2026, "bev_share_of_cars"],
                             assumption_set="A06;A07"))
            if scen == "historical_trend":
                t = trend_cases[trend_cases["case"] == case]
                for _, r in t.iterrows():
                    rows.append(dict(year=r["year"], scenario=scen, case=case, value_status="projected",
                                     total_cars=r["total_cars"], xev_share=np.nan, xev_registrations=np.nan,
                                     bev_share_of_xev=np.nan, bev_registrations=r["bev_registrations"],
                                     bev_share_of_cars=r["bev_share_of_cars"],
                                     assumption_set=f"model {r['model']}; fit {C.TREND_FIT_START}-2026E; market {r['market_case']}"))
            else:
                p = policy_cases[(policy_cases["scenario"] == scen) & (policy_cases["case"] == case) &
                                 (policy_cases["year"] > C.PARTIAL_YEAR)]
                for _, r in p.iterrows():
                    rows.append(dict(year=r["year"], scenario=scen, case=case, value_status="projected",
                                     total_cars=r["total_cars"], xev_share=r["xev_share"],
                                     xev_registrations=r["xev_registrations"], bev_share_of_xev=r["bev_share_of_xev"],
                                     bev_registrations=r["bev_registrations"], bev_share_of_cars=r["bev_share_of_cars"],
                                     assumption_set=f"market {r['market_case']}; BEV-in-xEV {r['bev_in_xev_case']}; A04;A08;A09;A10"))
    df = pd.DataFrame(rows)
    for c in ["total_cars", "xev_registrations", "bev_registrations"]:
        df[c] = df[c].round().astype("Int64")
    for c in ["xev_share", "bev_share_of_xev", "bev_share_of_cars"]:
        df[c] = df[c].round(6)
    df["geography"] = NAT
    df["unit"] = "vehicles registered per calendar year (passenger cars, JPJ type 'car')"
    return df.sort_values(["scenario", "case", "year"]).reset_index(drop=True)


def stock_output(st: pd.DataFrame) -> pd.DataFrame:
    d = st[st["year"].isin(C.STOCK_YEARS)].copy()
    d["median_life_years"] = d["survival_case"].map(lambda c: C.SURVIVAL[c]["median_life"])
    d["weibull_shape"] = d["survival_case"].map(lambda c: C.SURVIVAL[c]["shape"])
    d["value_status"] = np.select(
        [d["year"] <= C.BASE_YEAR, d["year"] == C.PARTIAL_YEAR],
        ["modelled: observed registrations x assumed survival",
         "modelled: Jan-Oct observed + Nov-Dec estimated registrations x assumed survival"],
        "modelled: projected registrations x assumed survival")
    out = d[["year", "scenario", "case", "active_stock", "cumulative_registrations", "registrations_in_year",
             "retirements_in_year", "survival_case", "median_life_years", "weibull_shape", "value_status"]].copy()
    out = out.rename(columns={"active_stock": "active_bev_stock_end_of_year",
                              "cumulative_registrations": "cumulative_bev_registrations_since_2009"})
    for c in ["active_bev_stock_end_of_year", "cumulative_bev_registrations_since_2009", "registrations_in_year",
              "retirements_in_year"]:
        out[c] = out[c].round().astype("Int64")
    out["geography"] = NAT
    out["unit"] = "vehicles (passenger BEVs, end of calendar year, 31 Dec)"
    return out.sort_values(["scenario", "case", "year"]).reset_index(drop=True)


def peninsular_output(st, pen, bd, m) -> pd.DataFrame:
    mg = pen.merge(st, on=["scenario", "case", "year"], suffixes=("_pen", "_nat"))
    mg = mg[mg["year"].isin(C.STOCK_YEARS)].copy()
    b = bd.set_index("year")
    obs_nat, obs_pen = {}, {}
    for y in C.STOCK_YEARS:
        if y <= C.PARTIAL_YEAR:
            obs_nat[y] = int(m.loc[:f"{y}-12-01", "bev"].sum())
            obs_pen[y] = int(b.loc[b.index <= y, "known_peninsular"].sum())
    out = pd.DataFrame({
        "year": mg["year"], "scenario": mg["scenario"], "case": mg["case"],
        "national_active_bev_stock": mg["active_stock_nat"].round().astype("Int64"),
        "peninsular_active_bev_stock": mg["active_stock_pen"].round().astype("Int64"),
        "peninsular_share_of_stock": (mg["active_stock_pen"] / mg["active_stock_nat"]).round(4),
        "peninsular_stock_status": "ESTIMATED (cohort stock x registration-state proxy share; not observed)",
        "observed_cum_bev_registrations_national": mg["year"].map(obs_nat).astype("Int64"),
        "observed_cum_bev_registrations_at_peninsular_jpj_offices": mg["year"].map(obs_pen).astype("Int64"),
    })
    out["observed_columns_note"] = np.where(
        out["year"] <= C.PARTIAL_YEAR,
        "DIRECTLY OBSERVED cumulative registration counts (flows, not stock); Peninsular-office count excludes Rakan Niaga "
        "registrations and is therefore a lower bound" + np.where(out["year"] == C.PARTIAL_YEAR, " (2026: Jan-Oct only)", ""),
        "no observed data (forecast year)")
    out["geography"] = PEN
    return out.sort_values(["scenario", "case", "year"]).reset_index(drop=True)


def leap_tables(st, pen):
    def pick(df, scen, case):
        return df[(df["scenario"] == scen) & (df["case"] == case)].set_index("year")["active_stock"].reindex(C.STOCK_YEARS)
    leap = pd.DataFrame({"year": C.STOCK_YEARS})
    leap["national_bev_stock_20pct"] = pick(st, "policy_20pct", "base").round().astype(int).values
    leap["national_bev_stock_30pct"] = pick(st, "policy_30pct", "base").round().astype(int).values
    leap["peninsular_bev_stock_20pct"] = pick(pen, "policy_20pct", "base").round().astype(int).values
    leap["peninsular_bev_stock_30pct"] = pick(pen, "policy_30pct", "base").round().astype(int).values
    unc = pd.DataFrame({"year": C.STOCK_YEARS})
    for scen, tag in [("policy_20pct", "20pct"), ("policy_30pct", "30pct"), ("historical_trend", "trend")]:
        for geo, df in [("national", st), ("peninsular", pen)]:
            for case in ["low", "base", "high"]:
                unc[f"{geo}_bev_stock_{tag}_{case}"] = pick(df, scen, case).round().astype(int).values
    return leap, unc


LEAP_NOTE = """# LEAP input notes - passenger BEV stock

File: `outputs/tables/leap_bev_stock_input.csv`  (uncertainty: `leap_bev_stock_uncertainty.csv`)

- **Quantity**: active passenger battery-electric cars (JPJ type `car`, fuel `electric`) on the road at **31 December** of each year.
- **Units**: vehicles (integer counts, no thousands separators).
- **Columns**: base case of each policy scenario; national = Malaysia; peninsular = Peninsular Malaysia (excludes Sabah, Sarawak, W.P. Labuan).
- **Status by year**: 2025 = observed registrations x assumed survival; 2026 = Jan-Oct observed + Nov-Dec estimated registrations x survival; 2027-2030 = projected.
- **Primary scenario**: 20% xEV share of new car registrations in 2030 (NETR target, applied to JPJ registrations - an assumption). 30% = sensitivity (MITI ministerial statement, 4 Feb 2026), not a confirmed replacement target.
- **Key assumptions**: total car registrations {g:+.1%}/yr after 2026; BEV share of xEV held at the 2026 Jan-Oct level ({bev_in_xev:.1%}); Weibull survival with an {median:.0f}-year median life; Peninsular share of new BEVs {pen:.0%} (from registration-state data, a proxy for location, not operating location).
- **Uncertainty**: low/high envelopes (market growth, BEV share within xEV, survival, Peninsular share moved together) are in the uncertainty file. Treat them as scenario ranges, not statistical confidence intervals.
- **Caveat**: the 2026 observed xEV share ({xev26:.1%}) is already well above the 2025 level. Reaching 20% in 2030 implies BEV registrations grow much more slowly than in 2022-2026. The historical-trend case gives higher stock than the 20% case.
"""


def write_excel(path, sheets: dict, readme_lines: list):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame({"BEV forecast summary - Peninsular Malaysia passenger BEV study (2030)": readme_lines}).to_excel(
            xw, sheet_name="README", index=False)
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
        wb = xw.book
        hdr_fill = PatternFill("solid", fgColor="E8EEF7")
        for ws in wb.worksheets:
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.fill = hdr_fill
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            ws.freeze_panes = "A2"
            for i, col in enumerate(ws.iter_cols(min_row=1, max_row=min(ws.max_row, 200)), start=1):
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                ws.column_dimensions[get_column_letter(i)].width = min(max(10, width + 2), 70 if ws.title != "README" else 140)
            for row in ws.iter_rows(min_row=2):
                for c in row:
                    if isinstance(c.value, float):
                        hdr = str(ws.cell(row=1, column=c.column).value)
                        if any(k in hdr for k in ["share", "ratio", "pct_error", "mape", "yoy"]):
                            c.number_format = "0.00%"
                        else:
                            c.number_format = "#,##0"
                    elif isinstance(c.value, int) and c.column > 1:
                        hdr = str(ws.cell(row=1, column=c.column).value)
                        if hdr not in ("year", "fit_start", "fit_end", "holdout_year", "month"):
                            c.number_format = "#,##0"

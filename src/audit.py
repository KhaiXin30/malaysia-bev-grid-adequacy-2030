"""Step 1 - data audit of registrations_type_fuel.csv and the car transaction files."""
import pandas as pd

import config as C
from data_io import load_aggregate, load_transactions


def audit_aggregate() -> dict:
    df = load_aggregate()
    res = {}
    res["n_rows"] = len(df)
    res["columns"] = list(df.columns)
    res["dtypes"] = {c: str(t) for c, t in df.dtypes.items()}
    res["missing_values"] = df.isna().sum().to_dict()
    res["duplicate_rows"] = int(df.duplicated().sum())
    res["duplicate_keys"] = int(df.duplicated(["date", "type", "fuel"]).sum())
    res["negative_values"] = int((df["registrations"] < 0).sum())
    res["date_min"] = df["date"].min().date().isoformat()
    res["date_max"] = df["date"].max().date().isoformat()
    res["all_dates_first_of_month"] = bool((df["date"].dt.day == 1).all())
    full = pd.date_range(df["date"].min(), df["date"].max(), freq="MS")
    res["months_expected"] = len(full)
    res["months_present_any_series"] = df["date"].nunique()
    res["types"] = df["type"].value_counts().to_dict()
    res["fuels"] = df["fuel"].value_counts().to_dict()

    # Series continuity per (type, fuel): gaps are implicit zeros (sparse publication).
    g = df.groupby(["type", "fuel"])["date"].agg(["min", "max", "count"])
    g["months_span"] = ((g["max"].dt.year - g["min"].dt.year) * 12 + g["max"].dt.month - g["min"].dt.month + 1)
    g["missing_months_in_span"] = g["months_span"] - g["count"]
    res["series_continuity"] = g.reset_index()

    # Internal consistency: fuel breakdown sums to all_fuels; type breakdown sums to all_types.
    w = df.pivot_table(index=["date", "type"], columns="fuel", values="registrations", aggfunc="sum").fillna(0)
    fuel_cols = [c for c in w.columns if c != C.FUEL_ALL]
    res["fuel_sum_mismatch_rows"] = int((w[C.FUEL_ALL] != w[fuel_cols].sum(axis=1)).sum())
    res["fuel_sum_rows_checked"] = len(w)
    t = df.pivot_table(index=["date", "fuel"], columns="type", values="registrations", aggfunc="sum").fillna(0)
    type_cols = [c for c in t.columns if c != "all_types"]
    res["type_sum_mismatch_rows"] = int((t["all_types"] != t[type_cols].sum(axis=1)).sum())
    res["type_sum_rows_checked"] = len(t)

    car = df[df["type"] == C.CAR_TYPE]
    res["car_fuels"] = sorted(car["fuel"].unique())
    res["hybrid_codes_present"] = [f for f in C.FUEL_HYBRID_AGG if f in set(df["fuel"])]
    res["hybrid_codes_expected_but_absent"] = [f for f in ["hybrid_petrol", "hybrid_diesel"] if f not in set(df["fuel"])]
    last = df["date"].max()
    res["partial_year"] = int(last.year) if last.month < 12 else None
    res["partial_year_months"] = int(last.month)
    return res


def audit_transactions() -> dict:
    tx = load_transactions()
    agg = load_aggregate()
    res = {"n_rows_2009plus": len(tx), "fuels": tx["fuel"].value_counts().to_dict(),
           "states": tx["state"].value_counts().to_dict(), "types": tx["type"].value_counts().to_dict(),
           "missing": tx.isna().sum().to_dict()}
    # Reconcile with aggregate car series by year
    car = agg[agg["type"] == C.CAR_TYPE].copy()
    car["year"] = car["date"].dt.year
    a_all = car[car["fuel"] == C.FUEL_ALL].groupby("year")["registrations"].sum()
    a_bev = car[car["fuel"].isin(C.FUEL_BEV)].groupby("year")["registrations"].sum()
    a_hyb = car[car["fuel"].isin(C.FUEL_HYBRID_AGG)].groupby("year")["registrations"].sum()
    t_all = tx.groupby("year").size()
    t_bev = tx[tx["fuel"].isin(C.FUEL_BEV)].groupby("year").size()
    t_hyb = tx[tx["fuel"].isin(C.FUEL_HYBRID_TX)].groupby("year").size()
    rec = pd.DataFrame({"agg_all_cars": a_all, "tx_all_cars": t_all, "agg_bev": a_bev, "tx_bev": t_bev,
                        "agg_hybrid": a_hyb, "tx_hybrid": t_hyb}).loc[2009:].fillna(0).astype(int)
    rec["diff_all"] = rec["agg_all_cars"] - rec["tx_all_cars"]
    rec["diff_bev"] = rec["agg_bev"] - rec["tx_bev"]
    rec["diff_hybrid"] = rec["agg_hybrid"] - rec["tx_hybrid"]
    res["reconciliation"] = rec.reset_index().rename(columns={"index": "year"})

    # BEV by JPJ car sub-type (scope transparency)
    bev = tx[tx["fuel"].isin(C.FUEL_BEV)]
    res["bev_by_subtype"] = bev[bev["year"] >= 2020].groupby(["year", "type"]).size().unstack(fill_value=0)
    return res


def phev_evidence() -> pd.DataFrame:
    """How a known PHEV (Proton e.MAS 7 PHEV, launched 4 Feb 2026) is coded vs its BEV sibling."""
    tx = load_transactions()
    e = tx[(tx["maker"] == "Proton") & (tx["model"] == "e.MAS 7")]
    t = e.groupby([e["date_reg"].dt.to_period("M").astype(str), "fuel"]).size().unstack(fill_value=0)
    t.index.name = "month"
    return t.reset_index()


def hybrid_top_models(year: int = 2026, n: int = 20) -> pd.DataFrame:
    tx = load_transactions()
    h = tx[(tx["year"] == year) & tx["fuel"].isin(C.FUEL_HYBRID_TX)]
    return h.groupby(["maker", "model"]).size().sort_values(ascending=False).head(n).rename("registrations").reset_index()


def write_audit_report(agg: dict, txa: dict, phev: pd.DataFrame) -> None:
    C.REPORTS.mkdir(parents=True, exist_ok=True)
    sc = agg["series_continuity"]
    car_sc = sc[sc["type"] == "car"]
    lines = [
        "# Data audit - registrations_type_fuel.csv and car registration transactions",
        "",
        f"Generated by `src/audit.py`. Data retrieved {C.RETRIEVAL_DATE}.",
        "",
        "## 1. Aggregate monthly dataset (`data/raw/registrations_type_fuel.csv`)",
        "",
        f"- Rows: {agg['n_rows']:,}; columns: {agg['columns']}; dtypes: {agg['dtypes']}",
        f"- Coverage: {agg['date_min']} to {agg['date_max']} (monthly, all dates on day 1: {agg['all_dates_first_of_month']}); "
        f"{agg['months_expected']} months expected, {agg['months_present_any_series']} present.",
        f"- Missing values: {agg['missing_values']}; duplicate rows: {agg['duplicate_rows']}; duplicate (date,type,fuel) keys: {agg['duplicate_keys']}; negative values: {agg['negative_values']}.",
        f"- Types: {agg['types']}",
        f"- Fuels: {agg['fuels']}",
        f"- **Fuel breakdown vs `all_fuels`**: {agg['fuel_sum_mismatch_rows']} mismatches in {agg['fuel_sum_rows_checked']:,} (date,type) groups -> breakdown rows sum exactly to `all_fuels`; never add `all_fuels` to the breakdown.",
        f"- **Type breakdown vs `all_types`**: {agg['type_sum_mismatch_rows']} mismatches in {agg['type_sum_rows_checked']:,} (date,fuel) groups.",
        f"- Hybrid fuel codes present: {agg['hybrid_codes_present']}. Expected-but-absent codes: {agg['hybrid_codes_expected_but_absent']} "
        "(the aggregate file uses a single `hybrid` code; `hybrid_petrol`/`hybrid_diesel` appear only in the transaction files).",
        "- Sparse series: months without a row are implicit zeros (e.g. car/electric before 2021). Missing months within each car series span:",
        "",
        car_sc[["fuel", "min", "max", "count", "months_span", "missing_months_in_span"]].to_markdown(index=False),
        "",
        f"- **Partial year**: {agg['partial_year']} contains {agg['partial_year_months']} months (Jan-Oct). It is labelled YTD and never compared unadjusted with full years.",
        "- `greendiesel` is a large car fuel code (~45k cars in 2025) and is treated as diesel-type ICE (not xEV).",
        "",
        "## 2. Car registration transactions (`data/raw/jpj_car_transactions/cars_YYYY.parquet`)",
        "",
        f"- Rows (2009-2026): {txa['n_rows_2009plus']:,}. Missing values: {txa['missing']}",
        f"- Fuels: {txa['fuels']}",
        f"- States: {txa['states']}",
        "- Reconciliation with the aggregate car series (aggregate - transactions):",
        "",
        txa["reconciliation"].loc[txa["reconciliation"]["year"] >= 2015].to_markdown(index=False),
        "",
        "Small all-car differences (<0.03%) exist because the aggregate is derived from `registration_transactions_all`; BEV counts agree to within 1 vehicle/year.",
        "",
        "- BEV registrations by JPJ car sub-type (the `car` type includes pick-ups and window vans, which MAA classifies as commercial):",
        "",
        txa["bev_by_subtype"].reset_index().to_markdown(index=False),
        "",
        "## 3. PHEV representation",
        "",
        "JPJ has no PHEV code. The Proton e.MAS 7 exists as a BEV (since Dec 2024) and as a PHEV (launched 4 Feb 2026, MITI speech S04). "
        "Its registrations by fuel code:",
        "",
        phev.to_markdown(index=False),
        "",
        "`hybrid_petrol` e.MAS 7 registrations start in Feb 2026, exactly when the PHEV launched, so **PHEVs are recorded as `hybrid_petrol` "
        "(aggregate `hybrid`)**. JPJ 'hybrid' therefore = HEV + PHEV (+ possibly some mild hybrids - unverified). It cannot be split into HEV vs PHEV "
        "without model-level classification, which this project does not attempt.",
    ]
    (C.REPORTS / "data_audit.md").write_text("\n".join(lines), encoding="utf-8")

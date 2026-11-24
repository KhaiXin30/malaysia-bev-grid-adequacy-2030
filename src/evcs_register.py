"""Energy Commission (Suruhanjaya Tenaga) EVCS licence register: cleaning and context summary.

    python src/evcs_register.py

Input : data/raw/EVCS_license_holders.csv  (exported by the project owner from the Energy Commission
        EVCS licensee dashboard, https://datastudio.google.com/s/jKQb-5TfRBg, on 23 Nov 2026)
Output: data/processed/evcs_register_clean.csv
        outputs/tables/evcs_register_summary.csv
        outputs/tables/evcs_register_data_quality.csv
        outputs/tables/evcs_register_vs_phase31_context.csv
        outputs/tables/evcs_register_key_results.json

CONTEXT ONLY. The register lists licensed charging installations (sites, units, bays, rated kW). It has no
session, energy or utilisation data, does not say which sites are open to the public, and is not a 2030
projection. Nothing here feeds the Phase 1-3.1 models; their outputs are unchanged.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import config as C

SRC = C.RAW / "EVCS_license_holders.csv"
EXPORT_DATE = "2026-11-23"
DASHBOARD_URL = "https://datastudio.google.com/s/jKQb-5TfRBg"

COLS = {"BIL.": "row_no", "NO. LESEN": "licence_no", "NAMA PEMEGANG LESEN": "licensee",
        "ALAMAT PEPASANGAN": "address", "NEGERI": "state", "DAERAH": "district",
        "KEUPAYAAN SETIAP UNIT PENGECAS": "unit_ratings_text", "JUMLAH BILANGAN UNIT PENGECAS": "units_total",
        "DC": "units_dc", "AC": "units_ac", "KAPASITI PEPASANGAN (kW)": "installed_kw",
        "TEMPOH SAH LESEN": "validity_text", "JUMLAH BAY": "bays_total", "AC BAY": "bays_ac", "DC BAY": "bays_dc"}
NUM = ["units_total", "units_dc", "units_ac", "installed_kw", "bays_total", "bays_ac", "bays_dc"]

RATING_RE = re.compile(r"(\d+(?:\.\d+)?)\s*kW\s*(AC|DC)\s*[:\-]?\s*(\d+)\s*unit", re.I)
AC_BINS = [0, 3.7, 7.5, 11.5, 22.5, np.inf]
AC_LABELS = ["<=3.7 kW", "3.7-7.4 kW", "~11 kW", "~22 kW", ">22 kW"]

# Address-keyword site categories. HEURISTIC: first match wins; many addresses match nothing.
SITE_KEYWORDS = [
    ("fuel station / highway", r"PETRONAS|SHELL|PETRON|CALTEX|BHPETROL|STESEN MINYAK|\bR&R\b|\bRNR\b|HENTIAN|LEBUHRAYA|HIGHWAY|TOL\b"),
    ("residential (condo / apartment / serviced / SOHO)", r"CONDO|RESIDEN|APARTMENT|APARTMEN|KONDOMINIUM|SERVICED|SUITES|PANGSAPURI|\bSOHO\b"),
    ("mall / retail", r"MALL|SHOPPING|AEON|LOTUS|TESCO|IOI CITY|PAVILION|MYTOWN|PYRAMID|GIANT|MYDIN|HYPERMARKET|PASARAYA|GALLERIA|DECATHLON|IKEA"),
    ("hotel / resort", r"HOTEL|RESORT"),
    ("office / tower", r"MENARA|TOWER|OFFICE|PEJABAT|HEADQUARTERS"),
    ("car dealer / service centre", r"SHOWROOM|\bAUTO|MOTOR|\b3S\b|\b4S\b|SERVICE CENTRE|BYD|PROTON|PERODUA"),
]


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _norm_name(s):
    s = s.upper().replace(".", " ").replace(",", " ").replace("(", " ").replace(")", " ")
    return re.sub(r"\s+", " ", s).strip()


def load():
    raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str)
    df = raw.rename(columns=COLS)
    for c in NUM:
        df[c] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")
    df["row_no"] = df["row_no"].astype(int)
    return raw, df


def clean(df):
    q = []  # data-quality log
    n0 = len(df)
    q.append(dict(check="rows in export", value=n0, action="—"))
    gaps = sorted(set(range(1, df.row_no.max() + 1)) - set(df.row_no))
    q.append(dict(check="row numbers (BIL.) missing from 1..max", value=len(gaps),
                  action="none; numbers " + ", ".join(map(str, gaps))))
    key = [c for c in df.columns if c != "row_no"]
    dup = df.duplicated(subset=key, keep="first")
    q.append(dict(check="exact duplicate rows (all fields except BIL.)", value=int(dup.sum()), action="removed"))
    df = df[~dup].copy()
    shared = df[df.licence_no.duplicated(keep=False)]
    q.append(dict(check="licence numbers shared by >1 remaining row (different sites/details)",
                  value=int(shared.licence_no.nunique()), action=f"kept all {len(shared)} rows; flagged"))
    df["flag_shared_licence_no"] = df.licence_no.duplicated(keep=False)

    # licence validity start
    start_txt = df.validity_text.str.extract(r"^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})")
    yr = start_txt[2].astype(float)
    two_digit = yr < 100
    yr = yr.where(~two_digit, 2000 + yr)
    df["licence_start"] = pd.to_datetime(dict(year=yr, month=start_txt[1].astype(float),
                                              day=start_txt[0].astype(float)), errors="coerce")
    q.append(dict(check="licence start year written with 2 digits", value=int(two_digit.sum()),
                  action="read as 20YY; flagged"))
    future = df.licence_start > pd.Timestamp(EXPORT_DATE)
    q.append(dict(check="licence start date after export date (likely typo)", value=int(future.sum()),
                  action="kept in totals; excluded from the by-year table"))
    df["flag_start_date"] = np.where(future, "after export date", np.where(two_digit, "2-digit year", ""))

    # per-unit ratings parsed from free text
    parsed = df.unit_ratings_text.fillna("").map(RATING_RE.findall)
    df["parsed_ac_units"] = parsed.map(lambda m: sum(int(n) for _, t, n in m if t.upper() == "AC"))
    df["parsed_dc_units"] = parsed.map(lambda m: sum(int(n) for _, t, n in m if t.upper() == "DC"))
    df["parsed_kw"] = parsed.map(lambda m: sum(float(k) * int(n) for k, _, n in m))
    df["flag_rating_text_mismatch"] = (df.parsed_ac_units != df.units_ac) | (df.parsed_dc_units != df.units_dc)
    q.append(dict(check="rows whose rating text does not reproduce the AC/DC unit columns",
                  value=int(df.flag_rating_text_mismatch.sum()),
                  action="AC/DC columns used for counts; these rows excluded from the kW-rating distribution"))
    q.append(dict(check="rows where units_ac + units_dc != units_total",
                  value=int((df.units_ac + df.units_dc != df.units_total).sum()), action="none"))
    kwdiff = (df.parsed_kw - df.installed_kw).abs() > 1
    q.append(dict(check="rows where parsed kW x units differs from installed kW by >1 kW (parse-consistent rows)",
                  value=int((kwdiff & ~df.flag_rating_text_mismatch).sum()), action="installed_kw column used"))
    df["_ratings"] = parsed

    df["licensee_norm"] = df.licensee.map(_norm_name)
    q.append(dict(check="licensee names: raw vs normalised (punctuation)",
                  value=f"{df.licensee.str.upper().str.strip().nunique()} -> {df.licensee_norm.nunique()}",
                  action="normalised name used"))
    addr = df.address.fillna("").str.upper()
    cat = pd.Series("unclassified", index=df.index)
    for name, pat in SITE_KEYWORDS:
        m = addr.str.contains(pat, regex=True) & (cat == "unclassified")
        cat[m] = name
    df["site_category_heuristic"] = cat
    return df, pd.DataFrame(q)


def summarise(df):
    rows = []

    def add(dim, g):
        for k, s in g:
            rows.append(dict(dimension=dim, category=k, sites=len(s), units_ac=int(s.units_ac.sum()),
                             units_dc=int(s.units_dc.sum()), bays_ac=int(s.bays_ac.sum()),
                             bays_dc=int(s.bays_dc.sum()), installed_kw=round(float(s.installed_kw.sum()), 1)))

    add("total", [("Peninsular Malaysia (all rows after de-duplication)", df)])
    add("state", sorted(df.groupby("state"), key=lambda x: -x[1].units_ac.sum()))
    ok = df.flag_start_date == ""
    add("licence start year", [(str(int(y)), s) for y, s in df[ok | (df.flag_start_date == "2-digit year")]
                               .groupby(df.licence_start.dt.year)])
    add("site category (address keywords, heuristic)", sorted(df.groupby("site_category_heuristic"),
                                                                key=lambda x: -x[1].units_ac.sum()))
    ops = df.groupby("licensee_norm")
    top = sorted(ops, key=lambda x: -x[1].units_ac.sum())
    add("licensee (top 10 by AC units)", top[:10])
    add("licensee (all others)", [(f"{len(top) - 10} other licensees", df[~df.licensee_norm.isin([k for k, _ in top[:10]])])])
    summ = pd.DataFrame(rows)

    # AC unit-rating distribution from parse-consistent rows
    good = df[~df.flag_rating_text_mismatch]
    u = pd.DataFrame([(float(k), t.upper(), int(n)) for m in good._ratings for k, t, n in m], columns=["kw", "type", "n"])
    ac = u[u.type == "AC"]
    b = pd.cut(ac.kw, AC_BINS, labels=AC_LABELS)
    dist = ac.groupby(b, observed=False).n.sum()
    for k, v in dist.items():
        rows.append(dict(dimension="AC unit rating (parse-consistent rows only)", category=k, sites=np.nan,
                         units_ac=int(v), units_dc=np.nan, bays_ac=np.nan, bays_dc=np.nan,
                         installed_kw=round(float((ac.kw * ac.n)[b == k].sum()), 1)))
    dc = u[u.type == "DC"]
    stats = dict(ac_units_rating_coverage=int(ac.n.sum()), ac_units_total=int(df.units_ac.sum()),
                 ac_mean_rated_kw=round(float((ac.kw * ac.n).sum() / ac.n.sum()), 2),
                 ac_share_22kw=round(float(dist["~22 kW"] / ac.n.sum()), 3),
                 ac_share_11kw=round(float(dist["~11 kW"] / ac.n.sum()), 3),
                 ac_share_7kw_or_less=round(float((dist["3.7-7.4 kW"] + dist["<=3.7 kW"]) / ac.n.sum()), 3),
                 dc_mean_rated_kw=round(float((dc.kw * dc.n).sum() / dc.n.sum()), 1),
                 top5_licensee_share_of_ac_units=round(float(sum(s.units_ac.sum() for _, s in top[:5]) / df.units_ac.sum()), 3),
                 n_licensees=int(df.licensee_norm.nunique()))
    return pd.DataFrame(rows), stats


def phase31_context(df, stats):
    p = pd.read_csv(C.TABLES / "public_ac_plausibility_check.csv")
    p = p[p.mileage_case == "base_17969km"].copy()
    p["evcs_register_ac_units_peninsular_2026"] = int(df.units_ac.sum())
    p["evcs_register_ac_bays_peninsular_2026"] = int(df.bays_ac.sum())
    p["ratio_implied_charging_vehicles_to_register_ac_bays"] = (
        p.implied_vehicles_charging_at_max_at_mean_power / p.evcs_register_ac_bays_peninsular_2026).round(2)
    p["status"] = ("CONTEXT ONLY: 2030 modelled vehicles vs Oct-2026 licensed AC bays (all licensed sites, "
                   "incl. residential/private; not a 2030 network projection)")
    keep = ["adoption_scenario", "public_ac_profile", "day_type", "max_public_ac_mw", "timestamp_of_max",
            "implied_vehicles_charging_at_max_at_mean_power", "mean_ac_power_kw_assumed",
            "evcs_register_ac_units_peninsular_2026", "evcs_register_ac_bays_peninsular_2026",
            "ratio_implied_charging_vehicles_to_register_ac_bays", "status"]
    return p[keep]


def main():
    raw, df = load()
    df, quality = clean(df)
    summ, stats = summarise(df)
    ctx = phase31_context(df, stats)

    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    out = df.drop(columns=["_ratings"])
    out.to_csv(C.PROCESSED / "evcs_register_clean.csv", index=False)
    summ.to_csv(C.TABLES / "evcs_register_summary.csv", index=False)
    quality.to_csv(C.TABLES / "evcs_register_data_quality.csv", index=False)
    ctx.to_csv(C.TABLES / "evcs_register_vs_phase31_context.csv", index=False)
    last = df.licence_start[df.flag_start_date == ""].max()
    key = dict(source="Energy Commission (Suruhanjaya Tenaga) EVCS licence register", dashboard=DASHBOARD_URL,
               raw_file=str(SRC.relative_to(C.ROOT)), raw_sha256=_sha(SRC), exported=EXPORT_DATE,
               latest_licence_start=str(last.date()), rows_raw=len(raw), rows_clean=len(df),
               sites=len(df), units_ac=int(df.units_ac.sum()), units_dc=int(df.units_dc.sum()),
               bays_ac=int(df.bays_ac.sum()), bays_dc=int(df.bays_dc.sum()),
               installed_kw=round(float(df.installed_kw.sum()), 1),
               states=sorted(df.state.unique().tolist()), **stats,
               status="context only; no sessions/energy/utilisation; public access not identified")
    (C.TABLES / "evcs_register_key_results.json").write_text(json.dumps(key, indent=2))
    print(json.dumps(key, indent=2))
    print(quality.to_string(index=False))
    print(summ.to_string(index=False))
    print(ctx.to_string(index=False))


if __name__ == "__main__":
    main()

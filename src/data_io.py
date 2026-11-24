"""Loading of raw data files."""
import glob
from functools import lru_cache

import pandas as pd

import config as C


@lru_cache(maxsize=1)
def load_aggregate() -> pd.DataFrame:
    """registrations_type_fuel.csv  (date, type, fuel, registrations)."""
    df = pd.read_csv(C.AGG_CSV, dtype={"type": str, "fuel": str, "registrations": "int64"})
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    return df


@lru_cache(maxsize=1)
def load_transactions(min_year: int = 2009) -> pd.DataFrame:
    """Car registration transactions (cars_YYYY.parquet). Only needed columns are kept."""
    files = sorted(glob.glob(str(C.TX_DIR / "cars_*.parquet")))
    if not files:
        raise FileNotFoundError(f"No transaction files in {C.TX_DIR}; run src/fetch_data.py")
    frames = []
    for f in files:
        year = int(f.rsplit("_", 1)[1].split(".")[0])
        if year < min_year:
            continue
        frames.append(pd.read_parquet(f, columns=["date_reg", "type", "maker", "model", "fuel", "state"]))
    tx = pd.concat(frames, ignore_index=True)
    tx["year"] = tx["date_reg"].dt.year
    tx["month"] = tx["date_reg"].dt.month
    return tx


def car_monthly_wide() -> pd.DataFrame:
    """Monthly car registrations by fuel (wide), zero-filled on a complete monthly index."""
    df = load_aggregate()
    car = df[df["type"] == C.CAR_TYPE]
    wide = car.pivot_table(index="date", columns="fuel", values="registrations", aggfunc="sum")
    full_idx = pd.date_range(df["date"].min(), df["date"].max(), freq="MS")
    wide = wide.reindex(full_idx).fillna(0).astype("int64")
    wide.index.name = "date"
    hyb_cols = [c for c in C.FUEL_HYBRID_AGG if c in wide.columns]
    out = pd.DataFrame(index=wide.index)
    out["total_cars"] = wide[C.FUEL_ALL]
    out["bev"] = wide[C.FUEL_BEV].sum(axis=1)
    out["hybrid"] = wide[hyb_cols].sum(axis=1)
    out["xev_proxy"] = out["bev"] + out["hybrid"]
    return out

"""Step 6 - Peninsular Malaysia share of BEV registrations from JPJ state-of-registration data.

The `state` field is the state of the JPJ office where the car was registered, or 'Rakan Niaga'
(official JPJ partner portal, typically dealer-submitted). It is NOT the owner's residence or the
vehicle's operating location, and it is unrelated to the number plate (data.gov.my, S02).

Estimate per cohort year:
  1. known-state share  = Peninsular / (Peninsular + East Malaysia) among state-identified rows
  2. maker-reweighted   : impute Rakan Niaga rows with each maker's known-state Peninsular share
                          (makers with < PEN_MAKER_MIN_OBS known rows use the overall share), then
                          combine with the known rows.
"""
import numpy as np
import pandas as pd

import config as C
from data_io import load_transactions


def _region(state: pd.Series) -> pd.Series:
    return np.where(state == C.RAKAN_NIAGA, "rakan_niaga",
                    np.where(state.isin(C.EAST_MALAYSIA_STATES), "east_malaysia", "peninsular"))


def state_breakdown(fuels=None, label="bev") -> pd.DataFrame:
    tx = load_transactions()
    if fuels is not None:
        tx = tx[tx["fuel"].isin(fuels)]
    tx = tx.assign(region=_region(tx["state"]))
    rows = []
    for y, g in tx.groupby("year"):
        known = g[g["region"] != "rakan_niaga"]
        rn = g[g["region"] == "rakan_niaga"]
        n_pen, n_east = int((known["region"] == "peninsular").sum()), int((known["region"] == "east_malaysia").sum())
        known_share = n_pen / (n_pen + n_east) if (n_pen + n_east) else np.nan
        # maker reweighting
        if len(known) and len(rn):
            ms = known.assign(pen=known["region"] == "peninsular").groupby("maker")["pen"].agg(["mean", "size"])
            share_m = ms["mean"].where(ms["size"] >= C.PEN_MAKER_MIN_OBS, known_share)
            rn_share = float(rn["maker"].map(share_m).fillna(known_share).mean())
        else:
            rn_share = known_share
        combined = (n_pen + rn_share * len(rn)) / len(g) if len(g) else np.nan
        rows.append(dict(year=int(y), series=label, registrations=len(g), known_peninsular=n_pen,
                         known_east_malaysia=n_east, rakan_niaga=len(rn), rakan_niaga_share=len(rn) / len(g),
                         known_state_peninsular_share=known_share, rakan_niaga_imputed_peninsular_share=rn_share,
                         maker_reweighted_peninsular_share=combined))
    return pd.DataFrame(rows)


def cohort_weights(bev_breakdown: pd.DataFrame) -> dict:
    """{case: Series(year -> Peninsular share)} for cohort years 2009..2030.
    base: data-derived maker-reweighted share for observed cohorts with >= PEN_MIN_KNOWN_OBS
          state-identified BEVs, otherwise PEN_SHARE_FORECAST['base']; forecast cohorts = base.
    low/high: PEN_SHARE_FORECAST low/high applied to every cohort (envelope)."""
    years = range(2009, C.FORECAST_END + 1)
    b = bev_breakdown.set_index("year")
    base = {}
    for y in years:
        if y in b.index and (b.loc[y, "known_peninsular"] + b.loc[y, "known_east_malaysia"]) >= C.PEN_MIN_KNOWN_OBS \
                and y <= C.PARTIAL_YEAR:
            base[y] = float(b.loc[y, "maker_reweighted_peninsular_share"])
        else:
            base[y] = C.PEN_SHARE_FORECAST["base"]
    return {"base": pd.Series(base),
            "low": pd.Series({y: C.PEN_SHARE_FORECAST["low"] for y in years}),
            "high": pd.Series({y: C.PEN_SHARE_FORECAST["high"] for y in years})}

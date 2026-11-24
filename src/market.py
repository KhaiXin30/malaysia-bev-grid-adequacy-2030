"""Step 3 - total new passenger-car market (JPJ registration basis) 2026-2030, plus MAA comparison."""
import pandas as pd

import config as C


def market_forecast(annual_full: pd.DataFrame) -> pd.DataFrame:
    """Total car registrations by year (2025 observed, 2026 estimated, 2027-2030 projected)
    for low/base/high growth cases. Long format: year, market_case, total_cars, status."""
    base_2026 = annual_full.loc[C.PARTIAL_YEAR, "total_cars"]
    rows = []
    for case, g in C.MARKET_GROWTH.items():
        rows.append(dict(year=C.BASE_YEAR, market_case=case,
                         total_cars=annual_full.loc[C.BASE_YEAR, "total_cars"], status="observed"))
        rows.append(dict(year=C.PARTIAL_YEAR, market_case=case, total_cars=base_2026,
                         status="partial_estimated"))
        for y in range(C.PARTIAL_YEAR + 1, C.FORECAST_END + 1):
            rows.append(dict(year=y, market_case=case,
                             total_cars=round(base_2026 * (1 + g) ** (y - C.PARTIAL_YEAR)), status="projected"))
    return pd.DataFrame(rows)


def jpj_vs_maa(annual_full: pd.DataFrame) -> pd.DataFrame:
    """Annual JPJ car registrations vs MAA TIV / passenger vehicles (different measures)."""
    rows = []
    for y in range(2015, 2026):
        tiv = C.MAA["hist_tiv"].get(y)
        pv = C.MAA["hist_pv"].get(y)
        if y == 2024:
            tiv, pv = C.MAA["tiv_2024_revised"], C.MAA["pv_2024_revised"]
        if y == 2025:
            tiv, pv = C.MAA["tiv_2025"], C.MAA["pv_2025"]
        jpj = annual_full.loc[y, "total_cars"]
        rows.append(dict(year=y, jpj_car_registrations=int(jpj), maa_tiv_sales=tiv, maa_passenger_sales=pv,
                         jpj_over_maa_tiv=jpj / tiv if tiv else None, jpj_over_maa_pv=jpj / pv if pv else None))
    df = pd.DataFrame(rows)
    df["note"] = ("JPJ = registrations of type 'car' (incl. pick-ups/window vans, non-MAA brands, used imports); "
                  "MAA TIV = new-vehicle sales by MAA members (PV+CV). 2024 MAA = revised (official TIV 816,747).")
    return df

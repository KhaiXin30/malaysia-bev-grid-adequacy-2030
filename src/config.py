"""Central configuration: paths, scope definitions, scenario assumptions and source register.

Every empirical number used by the model is either (a) computed from the raw data files,
or (b) listed in SOURCES / ASSUMPTIONS below with a URL or an explicit "assumption" label.
Change assumptions HERE only; all scripts read from this module.
"""
from pathlib import Path

# --------------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
REPORTS = ROOT / "reports"

AGG_CSV = RAW / "registrations_type_fuel.csv"
TX_DIR = RAW / "jpj_car_transactions"          # cars_YYYY.parquet (data.gov.my)

RETRIEVAL_DATE = "2026-11-22"                  # date all web sources/data were retrieved

# --------------------------------------------------------------------------------------
# Scope definitions (aggregate dataset: registrations_type_fuel)
# --------------------------------------------------------------------------------------
CAR_TYPE = "car"
FUEL_ALL = "all_fuels"
FUEL_BEV = ["electric"]
# NOTE: the brief anticipated 'hybrid_petrol'/'hybrid_diesel'. The aggregate CSV actually
# contains a single 'hybrid' code; the transaction-level files use hybrid_petrol/hybrid_diesel.
FUEL_HYBRID_AGG = ["hybrid", "hybrid_petrol", "hybrid_diesel"]   # whichever exist
FUEL_HYBRID_TX = ["hybrid_petrol", "hybrid_diesel"]

HIST_START = 2020                 # reporting start for annual history table
BASE_YEAR = 2025                  # last complete calendar year
PARTIAL_YEAR = 2026               # incomplete year in data (Jan-Oct)
FORECAST_END = 2030
STOCK_YEARS = list(range(2025, FORECAST_END + 1))

# Months used to estimate Nov-Dec 2026 for total car registrations: mean ratio of
# (Nov+Dec)/(Jan..Oct) over these complete years.
NOVDEC_RATIO_YEARS = [2022, 2023, 2024, 2025]

# --------------------------------------------------------------------------------------
# Total passenger-car registration market (JPJ basis), 2027-2030 growth (ASSUMPTIONS)
# Anchored on the 2026 estimate (Jan-Oct observed + Nov-Dec estimated).
# Rationale: JPJ car registrations 2010-2019 were ~flat (608,644 -> 612,973);
# 2023-2025 grew ~2.3%/yr; MAA forecasts 2026 TIV 800,000 (< 2025 record 820,752).
# --------------------------------------------------------------------------------------
MARKET_GROWTH = {"low": -0.015, "base": 0.010, "high": 0.025}

# --------------------------------------------------------------------------------------
# Policy scenarios: xEV share of annual new car registrations in 2030 (ASSUMED to apply
# to the JPJ passenger-car registration denominator; national scope).
# Path: linear interpolation from the 2026 estimated observed share to the 2030 target.
# --------------------------------------------------------------------------------------
POLICY_TARGETS = {"policy_20pct": 0.20, "policy_30pct": 0.30}

# BEV share within xEV (BEV / (BEV + JPJ 'hybrid')) - ASSUMPTIONS anchored on JPJ history
# (2023 37.5%, 2024 47.0%, 2025 59.0%, 2026 Jan-Oct 56.2%).
#   low : declines linearly from 2026 level to 45% in 2030 (PHEV/HEV gain; CBU BEV
#         incentive expiry; MAA's revised 2026 forecast splits xEV ~50/50 BEV:HEV)
#   base: held constant at the 2026 Jan-Oct level
#   high: rises linearly to 70% in 2030 (continuation of the 2023-2025 trend)
BEV_IN_XEV_2030 = {"low": 0.45, "base": None, "high": 0.70}   # None -> hold 2026 level

# --------------------------------------------------------------------------------------
# Historical-trend (independent) model settings
# --------------------------------------------------------------------------------------
TREND_FIT_START = 2022            # base fitting window start (start-year sensitivity below)
TREND_FIT_END = 2026              # 2026 = Jan-Oct observed + Nov-Dec estimated
TREND_START_YEAR_SENS = [2021, 2022, 2023]
LOGISTIC_K = {"K30": 0.30, "K50": 0.50, "K80": 0.80}   # assumed saturation BEV share
# Trend case definition (low / base / high) for downstream stock calculations
# All three use the base market; they differ by model structure. Backtests (fit 2022-2024)
# show linear models under-forecast (~-32%) and logistic K30 over-forecasts (~+35%) -> the
# trend-case uncertainty is skewed upward.
TREND_CASE_MODELS = {"low": "A_linear_counts", "base": "D_linear_share",
                     "high": "C_logistic_share_K30"}

# --------------------------------------------------------------------------------------
# Survival (scrappage/deregistration) - Weibull S(a) = exp(-(a/lambda)^k).
# ASSUMPTIONS: no official Malaysian BEV survival or deregistration data were found.
# Parameterised by median life (years) and shape k. Mid-year registration convention.
# --------------------------------------------------------------------------------------
SURVIVAL = {
    "low":  {"median_life": 14.0, "shape": 2.0},   # high attrition (write-offs, exports, early-model obsolescence)
    "base": {"median_life": 18.0, "shape": 2.5},
    "high": {"median_life": 22.0, "shape": 3.0},   # long-lived fleet
# Plausibility: cumulative car registrations Jan-2000..Sep-2026 (16.0M) ~= MOT-reported ~16M
# 'active' cars (S12), implying very high car survival or a loose 'active' definition; even the
# high curve gives fewer active cars than reported -> survival is unlikely to be LOWER than 'low'.
}

# --------------------------------------------------------------------------------------
# Peninsular Malaysia share of BEV registrations (forecast cohorts) - ASSUMPTIONS informed
# by JPJ transaction state-of-registration data (maker-reweighted estimate ~91.6-92.2% for
# 2024-2026). Historical cohorts use the year-specific data-derived estimate in 'base'.
# --------------------------------------------------------------------------------------
EAST_MALAYSIA_STATES = ["Sabah", "Sarawak", "W.P. Labuan"]
RAKAN_NIAGA = "Rakan Niaga"
PEN_SHARE_FORECAST = {"low": 0.88, "base": 0.92, "high": 0.95}
PEN_MIN_KNOWN_OBS = 30            # cohorts with fewer state-identified BEVs use base share
PEN_MAKER_MIN_OBS = 20            # makers with fewer known-state rows use the overall share

# --------------------------------------------------------------------------------------
# External reference values (official / published), used for cross-checks only
# --------------------------------------------------------------------------------------
MAA = {
    "tiv_2025": 820752, "pv_2025": 759098, "cv_2025": 61654,
    "tiv_2024_official": 816747, "tiv_2024_revised": 818773, "pv_2024_revised": 748929,
    "cv_2024_revised": 69844,
    "xev_2025": 69363, "hev_2025": 38515, "bev_2025": 30848,
    "tiv_2026_forecast_jan": 790000, "pv_2026_forecast_jan": 730000, "xev_2026_forecast_jan": 100000,
    "tiv_2026_forecast_jul": 800000, "pv_2026_forecast_jul": 744000, "cv_2026_forecast_jul": 56000,
    "xev_2026_forecast_jul": 120000,
    "tiv_2026_jan_oct": 673412, "tiv_2025_jan_oct": 655327,
    "hist_tiv": {2015: 666677, 2016: 580085, 2017: 576625, 2018: 598714, 2019: 604287,
                 2020: 529514, 2021: 508911, 2022: 720658, 2023: 799731},
    "hist_pv": {2015: 591275, 2016: 514594, 2017: 514675, 2018: 533202, 2019: 550179,
                2020: 480971, 2021: 452663, 2022: 641773, 2023: 719160},
}
MITI_2026 = {"xev_share_sales_2025": 0.085, "xev_share_cars_registered_2025": 0.087,
             "tiv_2025": 820752}
MITI_2023 = {"bev_cum_since_2011_gt": 12000, "bev_2023_ytd_gt": 9000, "xev_cum_gt": 100000}
MOT_ACTIVE_2026 = {"registered_total": 40.77e6, "active_total": 26.6e6, "active_cars_approx": 16.0e6,
                   "reference_date": "2026-09-30"}

# --------------------------------------------------------------------------------------
# Source register  (id -> metadata)   written to assumptions_and_sources.csv
# --------------------------------------------------------------------------------------
SOURCES = {
    "S01": dict(name="data.gov.my - Monthly vehicle registrations by type and fuel (registrations_type_fuel)",
                publisher="JPJ / Ministry of Transport via data.gov.my (CC BY 4.0)",
                url="https://data.gov.my/data-catalogue/registrations_type_fuel",
                file_url="https://storage.data.gov.my/transportation/registrations_type_fuel.csv",
                note="Data as of 31 Oct 2026; last updated 10 Nov 2026. Provided file is byte-identical to the download."),
    "S02": dict(name="data.gov.my - Car registration transactions (registration_transactions_car)",
                publisher="JPJ / Ministry of Transport via data.gov.my (CC BY 4.0)",
                url="https://data.gov.my/data-catalogue/registration_transactions_car",
                file_url="https://storage.data.gov.my/transportation/cars_YYYY.parquet (2000-2026)",
                note="State = state of the JPJ office of registration or 'Rakan Niaga' (official JPJ partner portal); not residence or operating location."),
    "S03": dict(name="MITI speech - Soft launch of Malaysia Autoshow 2024 (Tengku Zafrul, 12 Dec 2023)",
                publisher="Ministry of Investment, Trade and Industry (MITI)",
                url="https://www.miti.gov.my/miti/resources/Speech/Malaysia_Autoshow_Soft_Launch_231212.pdf",
                file_url="", note="Para 10: NETR national target '20% of our annual new car sales consists of Electrified Vehicles (xEV) by 2030, 50% by 2040 and 80% by 2050'."),
    "S04": dict(name="MITI speech - All New PROTON e.MAS 7 PHEV launch (Johari Abdul Ghani, 4 Feb 2026)",
                publisher="Ministry of Investment, Trade and Industry (MITI)",
                url="https://www.miti.gov.my/miti/resources/Speech/20260204_PROTONe.MAS7PHEVLaunch_A5_.pdf.pdf",
                file_url="", note="Para 8-9: 2025 TIV 820,752; xEV 8.5% of new vehicle sales; hybrid+electric 8.7% of cars registered in 2025; 'national target of 30 per cent xEV market share by 2030'."),
    "S05": dict(name="MAA press release: Production & sales for December 2025 (20 Jan 2026)",
                publisher="Malaysian Automotive Association",
                url="https://maa.org.my/pdf/2025/pressreleasefordec2025.pdf",
                file_url="", note="2025 PV 759,098; CV 61,654; TIV 820,752; 2024 revised 818,773 (official 816,747). Dec 2025 rush to buy CBU BEVs before tax-incentive expiry."),
    "S06": dict(name="MAA Market Review 2025 press statement (20 Jan 2026)",
                publisher="Malaysian Automotive Association",
                url="https://maa.org.my/pdf/2025/Market_Review_2025.pdf",
                file_url="", note="BEV sales +78% (MAA basis); CBU BEV incentives expired 31 Dec 2025. Forecast tables are images (not machine-readable)."),
    "S07": dict(name="MAA statistics page - new passenger & commercial vehicles registered 2010-2023",
                publisher="Malaysian Automotive Association",
                url="https://www.maa.org.my/statistics.html", file_url="",
                note="Annual PV/CV totals 2015-2023 used for TIV vs JPJ comparison."),
    "S08": dict(name="The Star - 'Momentum of car sales likely to moderate' (23 Jan 2026)",
                publisher="The Star (secondary, quoting MAA and RHB Research)",
                url="https://www.thestar.com.my/business/business-news/2026/01/23/momentum-of-car-sales-likely-to-moderate",
                file_url="", note="MAA categorises hybrids and EVs as xEV; 2025 xEV ~69,400 (HEV 38,500, EV 30,800); JPJ data 'includes non-MAA members' (EV 44,800); MAA Jan-2026 xEV forecast 100,000 (51k HEV / 49k BEV)."),
    "S09": dict(name="AutoBuzz - MAA 2025 TIV 820,752 (20 Jan 2026)",
                publisher="AutoBuzz.my (secondary, quoting MAA)",
                url="https://autobuzz.my/2026/01/20/maa-malaysia-hits-all-time-high-tiv-in-2025-with-820752-units-sold-surpassing-800k-2-years-in-a-row/",
                file_url="", note="2025 xEV 69,363 = HEV 38,515 + BEV 30,848."),
    "S10": dict(name="The Sun - MAA lifts 2026 vehicle sales forecast to 800,000 units (Jul 2026)",
                publisher="The Sun (secondary, quoting MAA)",
                url="https://thesun.my/business/malaysian-automotive-association-lifts-2026-vehicle-sales-forecast-to-800000-units/",
                file_url="", note="Revised 2026: TIV 800,000; PV 744,000; CV 56,000; xEV 120,000 (~60k BEV / ~60k HEV)."),
    "S11": dict(name="paultan.org - Oct 2026 Malaysian vehicle sales (19 Nov 2026)",
                publisher="paultan.org (secondary, quoting MAA)",
                url="https://paultan.org/2026/11/19/maa-malaysian-vehicle-sales-oct-2026/",
                file_url="", note="Jan-Oct 2026 TIV 673,412 (+3% vs 655,327)."),
    "S12": dict(name="The Star - '40.77 million vehicles registered, but only 26.6 million active' (7 Oct 2026)",
                publisher="The Star (secondary, quoting a Ministry of Transport parliamentary written reply)",
                url="https://www.thestar.com.my/news/nation/2026/10/07/4077-million-vehicles-registered-but-only-266-million-active",
                file_url="", note="As at 30 Sep 2026: 40.77M registered, 26.6M (65.3%) active, ~16M active cars. 'Active' not defined; no EV breakdown."),
    "S13": dict(name="paultan.org - EV sales in Malaysia, 1H 2026 (13 Jul 2026)",
                publisher="paultan.org (secondary, quoting JPJ data)",
                url="https://paultan.org/2026/07/13/ev-sales-in-malaysia-first-half-of-2026-31738-units-up-85-on-last-year-proton-drives-growth/",
                file_url="", note="JPJ 1H 2026 BEV 31,738; cross-check only."),
}

# --------------------------------------------------------------------------------------
# Assumption register (written to assumptions_and_sources.csv together with SOURCES)
# --------------------------------------------------------------------------------------
ASSUMPTIONS = [
    # id, category, item, value, unit, status, source_ids, note
    ("A01", "definition", "BEV", "fuel=='electric' (type=='car')", "-", "data definition", "S01",
     "Battery electric passenger 'car' per JPJ type (includes JPJ car sub-types motokar, MPV, jip, pick_up, window_van)."),
    ("A02", "definition", "xEV proxy", "BEV + JPJ 'hybrid' (aggregate) / hybrid_petrol+hybrid_diesel (transactions)", "-",
     "assumption (proxy)", "S01;S02;S04;S08",
     "JPJ hybrid class does not distinguish HEV from PHEV. Evidence that PHEVs are coded hybrid_petrol: Proton e.MAS 7 hybrid_petrol registrations begin Feb 2026, coinciding with the e.MAS 7 PHEV launch (4 Feb 2026). Mild hybrids' coding unverified. FCEV (fuel 'hydrogen') negligible (<=1/yr) and excluded."),
    ("A03", "definition", "Registrations vs sales", "JPJ registrations used as proxy for new sales", "-",
     "assumption", "S01;S05;S08",
     "JPJ counts registrations (incl. non-MAA brands such as Tesla, recond/used imports, registration date). MAA TIV counts member sales. 2025: JPJ cars 870,327 vs MAA TIV 820,752; JPJ BEV 44,813 vs MAA BEV 30,848."),
    ("A04", "scope", "Policy denominator", "xEV target applied to JPJ national passenger-car registrations", "-",
     "assumption", "S03;S04",
     "20% target is 'annual new car sales' (NETR); 30% is 'xEV market share'. 2025 check: JPJ registration-based xEV share 8.73% vs MITI-reported sales-based 8.5% and registered-cars 8.7%."),
    ("A05", "scope", "Geography of policy target", "National (Malaysia)", "-", "official", "S03;S04",
     "Peninsular Malaysia derived separately (A12-A13)."),
    ("A06", "data", "Nov-Dec 2026 total car registrations", "mean (Nov+Dec)/(Jan-Oct) ratio of 2022-2025 applied to Jan-Oct 2026", "-",
     "assumption", "S01", "2026 = Jan-Oct observed + Nov-Dec estimated; flagged as 'partial_estimated'."),
    ("A07", "data", "Nov-Dec 2026 BEV and hybrid registrations", "Jan-Oct 2026 BEV and hybrid shares applied to estimated Nov-Dec total", "-",
     "assumption", "S01", "2025 Nov-Dec BEV seasonality is distorted by the CBU BEV pre-buying rush (S05), so it is not used."),
    ("A08", "market", "Car registration growth 2027-2030", "low -1.5%/yr; base +1.0%/yr; high +2.5%/yr", "%/yr",
     "assumption", "S01;S05;S10", "Anchored on 2026 estimate. JPJ car registrations ~flat 2010-2019; +2.3%/yr 2023-2025; MAA expects 2026 TIV below 2025 record."),
    ("A09", "policy", "xEV share path 2027-2030", "linear interpolation from 2026 estimated share to 20% (primary) / 30% (sensitivity) in 2030", "share",
     "assumption", "S03;S04", "Identical market and BEV-in-xEV assumptions in both policy cases; difference isolates the xEV target."),
    ("A10", "policy", "BEV share within xEV", "low -> 45% in 2030; base = 2026 Jan-Oct level held; high -> 70% in 2030", "share",
     "assumption", "S01;S10", "Anchored on JPJ observed 2023-2026 BEV/(BEV+hybrid)."),
    ("A11", "stock", "Survival (Weibull)", "low median 14y k=2.0; base median 18y k=2.5; high median 22y k=3.0", "years",
     "assumption", "S12", "No official BEV deregistration/active-fleet data found. MOT reports 65.3% of all registered vehicles 'active' (undefined) - used only as a weak plausibility check."),
    ("A12", "geography", "Peninsular share - historical cohorts", "year-specific maker-reweighted share from JPJ state-of-registration", "share",
     "estimate (data-derived proxy)", "S02",
     "Peninsular = all states except Sabah, Sarawak, W.P. Labuan. 'Rakan Niaga' rows (78-84% of BEVs in 2025-26) imputed with maker-specific known-state shares."),
    ("A13", "geography", "Peninsular share - forecast cohorts", "low 88%; base 92%; high 95%", "share",
     "assumption", "S02", "Base equals rounded 2024-2026 data-derived estimate (91.6-92.2%)."),
    ("A14", "trend", "Trend model selection", "low=A linear counts; base=D linear share x base market; high=C logistic share K=30% x base market", "-",
     "modelling choice", "S01", "Short series (4-5 informative years); no model validated by backtest. Rolling holdouts: linear models under-forecast ~32%, logistic K30 over-forecasts ~35%."),
    ("A15", "trend", "Logistic saturation K", "30% / 50% / 80% of new car registrations", "share",
     "assumption", "S03", "K not identifiable from data; 50% is broadly consistent with NETR 80% xEV by 2050 x ~55-60% BEV share of xEV."),
]

# ======================================================================================
# PHASE 1.5 (Run 2) - fleet exposure: beginning / end / annual-average active stock and
# vehicle-years. Everything above this line is the Run 1 configuration and is unchanged.
# ======================================================================================
RUN1_ARCHIVE = ROOT / "outputs" / "archive" / "run1_2026-11-22"
EXPOSURE_START = 2009                     # first cohort year (no BEVs registered before 2009)
EXPOSURE_YEARS = list(range(2025, FORECAST_END + 1))
DAYS_PER_YEAR = 365.25                    # vehicle age unit for the Weibull curves
# Within-year registration timing (A16):
#   observed months (to Oct 2026): actual JPJ monthly BEV counts, spread over days by the
#                                  actual daily BEV transaction dates within each month
#   Nov-Dec 2026 and 2027-2030   : 'seasonal' (base) = mean monthly share of annual total car
#                                  registrations over SEASONAL_PROFILE_YEARS; 'uniform' = 1/12
SEASONAL_PROFILE_YEARS = NOVDEC_RATIO_YEARS   # 2022-2025, same window as the Nov-Dec estimate
TIMING_BASE = "seasonal"
TIMING_VARIANTS = {
    "seasonal": "Observed months at actual daily timing; estimated/forecast months by 2022-2025 total-car seasonality (BASE)",
    "uniform_forecast": "Observed months at actual daily timing; estimated/forecast months uniform (1/12 per month)",
    "history_uniform_within_month": "As base, but observed months spread uniformly over days (ignores daily dates)",
    "annual_midyear": "Run 1 convention: each annual cohort registered as a point at mid-year",
}
# Policy-denominator sensitivity (A17): xEV target applied to MAA TIV (sales) instead of JPJ
# registrations, using the Run 1 reconciliation assumptions of maa_basis_crosscheck():
#   TIV_y = MAA revised 2026 forecast x (1 + base growth)^(y-2026); BEV/xEV = 0.50 (MAA split);
#   JPJ registrations = MAA-basis BEV x JPJ/MAA 2025 BEV ratio.  2027-2029 (new for Run 2): xEV
#   share of TIV linear from MAA's 2026 forecast share (120,000 / 800,000 = 15%) to the target.
MAA_BASIS_BEV_IN_XEV = 0.50
# Peninsular allocation sensitivity variants (A18)
PEN_SENS_VARIANTS = {
    "all_cohorts": "88% / 95% applied to every cohort (Run 1 envelope convention)",
    "forecast_cohorts_only": "88% / 95% applied to 2027-2030 cohorts only; observed cohorts keep data-derived shares",
}

ASSUMPTIONS_RUN2 = [   # Run 1 register (ASSUMPTIONS) is left unchanged for traceability
    ("A16", "exposure", "Within-year registration timing",
     "observed months: actual monthly counts at actual daily dates; Nov-Dec 2026 and 2027-2030: 2022-2025 total-car monthly seasonality, uniform within month",
     "-", "assumption (data-informed)", "S01;S02",
     "Sensitivities: uniform monthly forecast registrations; uniform-within-month history; Run 1 annual mid-year convention. Vehicles enter at the midpoint of their registration day."),
    ("A17", "exposure", "Policy denominator sensitivity path (MAA TIV basis)",
     "2030 as Run 1 cross-check; 2027-2029 xEV share of TIV linear from 15% (MAA 2026 forecast) to target",
     "share", "assumption", "S05;S10",
     "Only used in the one-at-a-time sensitivity; 2026 held at the JPJ estimate (common to all runs)."),
    ("A18", "exposure", "Peninsular share in sensitivity",
     "envelope: 88/95% on all cohorts (as Run 1); additional variant: forecast cohorts only", "share",
     "assumption", "S02", "Base unchanged: data-derived shares for observed cohorts, 92% for 2027-2030 cohorts."),
    ("A19", "exposure", "Vehicle-year unit",
     "1 vehicle-year = 1 vehicle active for one full calendar year (T_y = 365 or 366 days)", "vehicle-years",
     "definition", "S01", "Hence vehicle_years equals stock_annual_average numerically for a one-year period."),
]

# Register of differences between Run 1 (2026-11-22) and Run 2 (Phase 1.5). Quantitative
# impacts are written by the pipeline to outputs/tables/run2_change_log.csv.
RUN2_CHANGES = [
    dict(id="C01", type="extension",
         item="Annual average active stock and vehicle-years",
         run1="Not computed (end-of-year stock only)",
         run2="Daily cohort integration of N(t); beginning, end, average stock, vehicle-years, retirements",
         reason="Electricity demand depends on vehicles operating during the year, not only on 31 Dec",
         impact="New outputs only; Run 1 end-of-year exports are regenerated unchanged"),
    dict(id="C02", type="method refinement (reported, not substituted)",
         item="Registration timing inside a year",
         run1="Annual cohorts registered at mid-year (age y-c+0.5 at 31 Dec)",
         run2="Monthly cohorts (actual daily dates for observed months; seasonal profile for forecast months)",
         reason="Brief asks to use registration dates where available",
         impact="End-of-year stock differs slightly from Run 1; see exposure_vs_run1_reconciliation.csv. Run 1 end-of-year files are kept as published"),
    dict(id="C03", type="extension",
         item="Sensitivity analysis scope",
         run1="One-at-a-time on national 31-Dec stock: market, BEV-in-xEV, survival",
         run2="Adds xEV target, Peninsular share, policy denominator and registration timing; metric = 2030 Peninsular annual-average stock",
         reason="Brief section 4",
         impact="New file fleet_exposure_sensitivity_2030.csv; Run 1 stock_sensitivity_2030.csv unchanged"),
    dict(id="C04", type="clarification",
         item="Policy-denominator effect quoted in Run 1 final report",
         run1="'changes 2030 flows by +/-15-20%'",
         run2="Under the Run 1 reconciliation assumptions the MAA-TIV basis gives +16.5% higher 2030 JPJ-equivalent registrations (one-sided); the -20% figure is MAA-basis sales not converted to registrations, so it is not a comparable registration estimate",
         reason="Recomputed from denominator_basis_crosscheck_2030.csv",
         impact="Wording only; no Run 1 number changes. final_report.md left untouched; see phase_1_5_summary.md"),
]

# ======================================================================================
# PHASE 2 (Run 3) - annual BEV charging electricity, 2025-2030. Everything above is Run 1/2
# configuration and is unchanged.
# E_grid[GWh] = vehicle_years x annual_km x kWh_per_100km / 100 / charging_efficiency / 1e6
# (charging_efficiency applied ONLY when consumption is battery-side; see ENERGY_BASIS)
# ======================================================================================
RUN2_ARCHIVE = ROOT / "outputs" / "archive" / "run2_2026-11-23"
LITERATURE = RAW / "literature"
ENERGY_ACCESS_DATE = "2026-11-23"
ENERGY_YEARS = list(range(2025, FORECAST_END + 1))

# ---- Annual driving distance (km per vehicle-year) -----------------------------------
# Zhao, Ottinger, Yip & Helveston (2023), Joule 7:2537-2551 (E05, full text verified): US used-vehicle
# odometer readings 2016-2022, vehicles aged 2-9 years. Annual miles (cars): BEV 7,165, CV 11,642,
# Tesla BEV 8,786, non-Tesla BEV 6,235; (SUVs): BEV 10,184, CV 12,979.
ZHAO2023_MILES = {"bev_car": 7165, "cv_car": 11642, "tesla_car": 8786, "nontesla_car": 6235,
                  "bev_suv": 10184, "cv_suv": 12979}
BEV_CV_RATIO_LONG_RANGE = ZHAO2023_MILES["tesla_car"] / ZHAO2023_MILES["cv_car"]   # 0.755
BEV_CV_RATIO_ALL_BEV = ZHAO2023_MILES["bev_car"] / ZHAO2023_MILES["cv_car"]        # 0.615
# base: 17,969  MIROS 2025 (IConCEES abstract): 49.23 km/day from 2022 vehicle inspection records (E01)
#              -> implies BEV/ICE mileage PARITY (Zhao et al. call parity 'optimistic' for the US)
# low : base x 0.755 = 13,561 km: US long-range (Tesla) BEV car / CV car ratio (E05). Run 3 first
#              used 15,000 (GIZ 2016 fleet-typical, E04); changed after the Joule paper was verified.
# high: 22,715  MIROS 2020 online odometer survey, motorcars, RSE 8.7%, n=63 (E02); new-car first-year
#              mileage ~24,000 km (E03/E04) shows the young-fleet upper side
ANNUAL_KM_BASE = 17969.23
ANNUAL_KM = {"low": round(ANNUAL_KM_BASE * BEV_CV_RATIO_LONG_RANGE, 2), "base": ANNUAL_KM_BASE, "high": 22715.0}

# ---- Energy accounting boundary -------------------------------------------------------
ENERGY_BASIS = "battery"   # consumption values are battery-side ('vehicle consumption')

# ---- Charging efficiency (grid energy -> energy into the battery), fleet average ----------
# Boundary: customer-side grid connection of the charger (home circuit / DC station input) to the
# battery; includes wallbox/EVSE, on-board charger or DC station conversion, cable, battery
# charging and thermal-management/standby loads during charging. EXCLUDES T&D network losses.
# low-energy case uses the HIGH efficiency and vice versa.
CHARGING_EFFICIENCY = {"low": 0.85, "base": 0.90, "high": 0.93}   # keyed by efficiency level
CHARGING_EVIDENCE = {   # informational ranges (efficiency = 1 - loss share of grid energy)
    "AC wallbox 11 kW (ADAC 2026)": (0.930, 0.949),
    "AC wallbox reduced 4.1 kW (ADAC 2026)": (0.872, 0.920),
    "AC household socket 2.3 kW (ADAC 2026)": (0.758, 0.873),
    "DC fast charging incl. station + battery conditioning (ADAC 2026)": (0.85, 0.95),
    "ORNL via fueleconomy.gov": (0.84, 0.93),
    "Argonne via fueleconomy.gov, combined cycle (10% loss)": (0.90, 0.90),
}

# ---- Battery-side consumption ----------------------------------------------------------
# Model-level values: EV Database 'Vehicle' consumption (battery energy for propulsion and
# on-board systems; real-world estimate, moderate climate) from the cheatsheet (E07, E08).
# Fleet-level case factors applied to the fleet-weighted EVDB value:
#   high = 1.00 (EVDB real-world level; European climate mix incl. heating, 110 km/h highway)
#   low  = median ratio of Malaysian/tropical road-test trip-computer readings to EVDB values for
#          the same models (CONSUMPTION_OBSERVATIONS, computed in energy.py)
#   base = midpoint of low and high (assumption)
EVDB_WH_PER_KM = {   # EV Database cheatsheet 'real-world' Wh/km (variants averaged equally)
    "Geely E5 (e.MAS 7 twin)": [182, 185, 190],
    "Geely E2 (e.MAS 5 proxy)": [164, 168],
    "BYD ATTO 3 (MY23-24)": [183],
    "Tesla Model 3": [130, 133, 136, 142, 150],
    "Tesla Model Y": [158, 159, 166, 172],
    "BYD SEALION 7": [196, 204, 208],
    "Zeekr 7X": [190, 192, 198],
    "BYD SEAL": [168, 172, 185],
    "BMW iX": [197, 202, 208],
    "XPENG X9": [193, 196, 196],
    "BYD DOLPHIN 60.4 kWh": [173],
    "BYD ATTO 2": [186, 191],
    "Omoda E5": [178],
    "XPENG G6": [174, 178, 182],
    "Porsche Taycan (sedan)": [166, 169, 168, 168, 172, 172, 181, 185, 181],
    "Smart #1 Brabus": [191],
    "Smart #1 Premium": [185],
    "Leapmotor C10": [197, 197, 200, 216],
    "BMW iX1": [163, 167],
    "MG MG4": [164, 165, 165, 171, 171, 190, 171],
    "Mini Cooper SE/E": [149, 146],
    "Leapmotor B10": [176, 181, 182],
    "BMW i5 (sedan)": [169, 175, 189],
    "Mercedes-Benz EQS": [159, 160],
    "BMW iX2": [161, 165],
    "MG MGS5": [171, 170],
    "BYD DOLPHIN SURF": [158, 160, 163],
    "Volvo EX30": [178, 178, 178, 178, 186, 191, 194],
}
EVDB_ALL_MODELS_AVERAGE_WH_PER_KM = 191   # cheatsheet "Average 191 Wh/km" (generic comparator)

# JPJ (maker, model) -> (EVDB key, mapping type). direct = same model; twin = same vehicle sold
# under another brand (source cited); proxy = similar segment/platform (ASSUMPTION).
JPJ_MODEL_MAP = {
    ("Proton", "e.MAS 5"): ("Geely E2 (e.MAS 5 proxy)", "proxy: e.MAS 5 is a rebadged Geely Geome Xingyuan (E16); EVDB lists Geely E2 with different battery sizes"),
    ("Proton", "e.MAS 7"): ("Geely E5 (e.MAS 7 twin)", "twin: co-developed with Geely Galaxy E5 (E16)"),
    ("BYD", "Atto 3"): ("BYD ATTO 3 (MY23-24)", "direct"),
    ("Tesla", "Model 3"): ("Tesla Model 3", "direct (variant mix unknown; variants averaged)"),
    ("Tesla", "Model Y"): ("Tesla Model Y", "direct (variant mix unknown; variants averaged)"),
    ("BYD", "Sealion"): ("BYD SEALION 7", "direct (JPJ 'Sealion' with fuel electric assumed = Sealion 7)"),
    ("Zeekr", "7X"): ("Zeekr 7X", "direct"),
    ("BYD", "Seal"): ("BYD SEAL", "direct"),
    ("BMW", "iX"): ("BMW iX", "direct"),
    ("BYD", "M6"): ("XPENG X9", "proxy: MPV segment (X9 is larger -> conservative)"),
    ("BYD", "Dolphin"): ("BYD DOLPHIN 60.4 kWh", "direct"),
    ("BYD", "Atto 2"): ("BYD ATTO 2", "direct"),
    ("BYD", "Seal 6"): ("BYD SEAL", "proxy: same brand D-segment sedan"),
    ("Chery", "iCaur V23"): ("Omoda E5", "proxy: same group compact SUV"),
    ("Chery", "iCaur 03"): ("Omoda E5", "proxy: same group compact SUV"),
    ("Xpeng", "G6"): ("XPENG G6", "direct"),
    ("Great Wall", "Ora"): ("BYD DOLPHIN 60.4 kWh", "proxy: compact hatch segment"),
    ("Denza", "D9"): ("XPENG X9", "proxy: large MPV segment"),
    ("Porsche", "Taycan"): ("Porsche Taycan (sedan)", "direct (variants averaged)"),
    ("Zeekr", "009"): ("XPENG X9", "proxy: large MPV segment"),
    ("Smart", "Brabus"): ("Smart #1 Brabus", "direct (JPJ 'Brabus' may include #3)"),
    ("Leapmotor", "C10"): ("Leapmotor C10", "direct"),
    ("BMW", "iX1"): ("BMW iX1", "direct"),
    ("Chery", "Omoda 5"): ("Omoda E5", "direct"),
    ("MG", "MG4"): ("MG MG4", "direct"),
    ("Mini", "Cooper"): ("Mini Cooper SE/E", "direct"),
    ("Leapmotor", "B10"): ("Leapmotor B10", "direct"),
    ("Xpeng", "X9"): ("XPENG X9", "direct"),
    ("BMW", "i5"): ("BMW i5 (sedan)", "direct"),
    ("BMW", "i7"): ("Mercedes-Benz EQS", "proxy: large luxury sedan"),
    ("BMW", "iX2"): ("BMW iX2", "direct"),
    ("MG", "S5"): ("MG MGS5", "direct"),
    ("TQ Wuling", "Bingo"): ("BYD DOLPHIN SURF", "proxy: small hatch segment"),
    ("Volvo", "EX30"): ("Volvo EX30", "direct"),
    ("Perodua", "QV-E"): ("BYD DOLPHIN SURF", "proxy: small hatch/crossover segment"),
}
# all other JPJ BEV models -> fleet-weighted mean of the mapped models ('residual')

# Malaysian / tropical road-test observations (battery-side unless noted). ratio_to_evdb uses
# the EVDB value of the mapped model. include_in_ratio: used to derive the 'low' factor.
CONSUMPTION_OBSERVATIONS = [
    # id, model, kWh/100km, basis, conditions, source_id, evdb_key, include_in_ratio
    ("O1", "Proton e.MAS 7 Premium", 11.2, "battery (car display)", "152 km mixed, ~30% congestion, Malaysia", "E09", "Geely E5 (e.MAS 7 twin)", True),
    ("O2", "Proton e.MAS 7 Premium", 11.3, "unclear (derived from % battery)", "152 km 'efficiency challenge' (eco-driving), Malaysia", "E10", "Geely E5 (e.MAS 7 twin)", False),
    ("O3", "Proton e.MAS 7", 14.35, "unclear (method not stated)", "range 13.5-15.2 (midpoint), Singapore road test", "E11", "Geely E5 (e.MAS 7 twin)", True),
    ("O4", "Proton e.MAS 5 Premium", 10.0, "battery (trip computer)", "Klang Valley and towards Genting Highlands; distance not stated (Zigwheels via Carz/Newswav)", "E15", "Geely E2 (e.MAS 5 proxy)", True),
    ("O5", "smart #1 Premium", 13.2, "unclear (method not stated)", "almost 500 km mixed, Malaysia", "E13", "Smart #1 Premium", True),
    ("O6", "BYD Dolphin Premium Extended Range", 13.8, "battery (car consumption graph)", "outbound leg Desa ParkCity-Putrajaya, Malaysia", "E14", "BYD DOLPHIN 60.4 kWh", True),
    ("O7", "BYD Dolphin Dynamic Standard Range", 16.1, "unclear (computed here: 24% of 44.92 kWh / 66.8 km)", "return leg, 'quite a bit of pedal pushing', Malaysia", "E14", "BYD DOLPHIN 60.4 kWh", False),
]
# Rated (plug-side) reference values, for boundary cross-checks only (not used in the base)
RATED_REFERENCES = [
    ("R1", "Proton e.MAS 7 (Singapore spec sheet)", 16.6, "rated, claimed (WLTP range 410 km cited)", "E11;E12"),
    ("R2", "BYD ATTO 3 (MY23-24) WLTP", 15.6, "rated WLTP incl. charging losses; EVDB WLTP vehicle-side 14.4", "E08"),
    ("R3", "BYD ATTO 3 Evo RWD WLTP", 16.4, "rated WLTP incl. charging losses; EVDB WLTP vehicle-side 14.7", "E08"),
    ("R4", "Tesla Model 3 RWD WLTP", 13.0, "official WLTP as cited by Carz/Newswav", "E15"),
    ("R5", "Tesla Model Y Premium RWD WLTP", 13.9, "official WLTP as cited by Carz/Newswav", "E15"),
]

# Fleet model mix for registration cohorts after the last observed month (A-E24)
MIX_WINDOWS = {"base": (2025, 2026), "small": (2026, 2026), "large": (2025, 2025)}
# 'small' (2026 Jan-Oct mix; e.MAS 5-heavy) gives LOWER consumption, 'large' (2025 mix) HIGHER.

# Combined envelope definitions (low = lowest energy, high = highest energy). The fleet case comes
# from Phase 1.5 (low/base/high vehicle-years).
ENERGY_CASES = {
    "low":  dict(fleet="low",  km="low",  consumption="low",  efficiency="high", mix="small"),
    "base": dict(fleet="base", km="base", consumption="base", efficiency="base", mix="base"),
    "high": dict(fleet="high", km="high", consumption="high", efficiency="low",  mix="large"),
}

ENERGY_SOURCES = {
    "E01": dict(name="Sarani R., Sharifah Allyana S.M.R., Nur Aziemah A., Rizati H. (MIROS) - 'Estimating the Vehicle Kilometres Travelled for Motorcycles and Cars', abstract ID 99, p.125, Book of Abstracts, 8th Int. Conf. on Civil and Environmental Engineering for Sustainability (IConCEES 2025), 29-30 Sep 2025",
                url="https://intl-conference.com/iconcees2025/docs/iconcees2025-book-of-abstracts.pdf", date="2025-09 (PDF created 2025-09-24)",
                note="Verbatim: VKT per day for motorcars 49.23 km = 17,969.23 km/yr; 2022 vehicle inspection records; Kruskal-Wallis: no significant difference by fuel type or vehicle age. Abstract only; full paper not found; sample size not stated. Local copy data/raw/literature/."),
    "E02": dict(name="Nurulhuda J., Sharifah Allyana M.R., Azzuhana R., NurZarifah H., Khairil Anwar A.K. (MIROS) - 'Vehicle Kilometer Travelled by Online Survey', IJARBSS 10(10), 2020, DOI 10.6007/IJARBSS/v10-i10/8274",
                url="https://hrmars.com/papers_submitted/8274/vehicle-kilometer-travelled-by-online-survey.pdf", date="2020-10-28",
                note="Motorcars 22,715 km/yr (RSE 8.7%); 226 respondents, 63 completed two odometer readings ~3 months apart; 68.3% Central region, 87% male; authors: sample does not represent the population. Local copy."),
    "E03": dict(name="MIROS - 'Car Annual Vehicle Kilometer Travelled Estimated from Car Manufacturer Data - An Improved Method' (UKM repository / ResearchGate)",
                url="https://ptsldigital.ukm.edu.my/handle/123456789/579117", date="c.2015-2016 (data year 2013)",
                note="NOT READ IN FULL: UKM server refused connections and ResearchGate returned 403 on 2026-11-23. Figures from search-result snippets of the ResearchGate abstract: 2013 average 24,129 km; Selangor 28,575; Johor 16,342; odometer data from three car manufacturers. Treat as partially verified."),
    "E04": dict(name="GIZ (ASEAN-German Technical Cooperation, Transport and Climate Change project) - 'Malaysia Stocktaking Report on Sustainable Transport and Climate Change: Data, Policy, and Monitoring' (hosted by MOT)",
                url="https://www.mot.gov.my/en/Documents/summary%20of%20malaysia%20stocktaking%20report-MY_StockTakingReport_Final.pdf", date="c.2016 (PDF created 2016-11-01)",
                note="PUSPAKOM/MIROS data indicate ~24,000 km in the first year of ownership (citing MIROS 2013); with this the car fleet fuel use was 64% above Energy Commission statistics; field work Jan 2016 (driver surveys, vehicle age, odometer checks) established typical ~15k km/yr. Local copy."),
    "E05": dict(name="Zhao L., Ottinger E.R., Yip A.H.C., Helveston J.P. (2023) 'Quantifying electric vehicle mileage in the United States', Joule 7:2537-2551, doi:10.1016/j.joule.2023.09.015",
                url="https://doi.org/10.1016/j.joule.2023.09.015", date="2023-11-15",
                note="FULL TEXT VERIFIED (PDF supplied by user 2026-11-23; local copy data/raw/literature/). 12.5M used car + 11.4M used SUV listings 2016-2022 (66,641 dealerships), ages 2-9 y; BEV n=175,773 cars, 12,623 SUVs. Annual miles: cars BEV 7,165 vs CV 11,642 (~39% less); Tesla 8,786 (~25% less), non-Tesla 6,235; SUVs BEV 10,184 vs CV 12,979. Range effect non-linear (+631 mi/yr per 10 mi range below 100 mi; +85 above 200 mi); weak evidence MY2019+ driven more. Limitations: used-listing selection, no owner demographics, early-adopter multi-car households, few recent model years. Authors: equal BEV/CV VMT is 'an optimistic assumption' in the short term."),
    "E06": dict(name="MIT CEEPR Working Paper 2023-01 'How Much Are Electric Vehicles Driven? Depends on the EV'",
                url="https://ceepr.mit.edu/wp-content/uploads/2023/01/MIT-CEEPR-WP-2023-01.pdf", date="2023-01",
                note="Search snippet only: difference in miles vs ICE vanishes for long-range EVs. Qualitative only."),
    "E07": dict(name="EV Database - Energy consumption of full electric vehicles cheatsheet (v5.2.0)",
                url="https://ev-database.org/cheatsheet/energy-consumption-electric-car", date="accessed 2026-11-23",
                note="'Data is based on real-world values.' Model values Wh/km transcribed in config.EVDB_WH_PER_KM; 'Average 191 Wh/km'."),
    "E08": dict(name="EV Database - BYD ATTO 3 (MY23-24) and ATTO 3 Evo RWD Design car pages",
                url="https://ev-database.org/car/1782/BYD-ATTO-3 ; https://ev-database.org/car/3474/BYD-ATTO-3-Evo-RWD-Design", date="accessed 2026-11-23",
                note="Definitions: 'Rated consumption and fuel equivalency figures include charging losses.' 'Vehicle = calculated battery energy consumption used by the vehicle for propulsion and on-board systems.' Mild weather 23 C no A/C; cold -10 C with heating; highway 110 km/h. ATTO 3: real 183 Wh/km, WLTP rated 156, WLTP vehicle 144; Evo: real 185, rated 164, vehicle 147; Evo combined-mild 163."),
    "E09": dict(name="PCauto Malaysia - First test drive review of the 2025 Proton e.MAS 7", url="https://www.pcauto.com/my/news/first-test-drive-review-of-the-2025-proton-emas-7-the-first-electric-car-from-a-domestic-brand-16039",
                date="2025-06-04", note="Premium 60.22 kWh, WLTP 410 km; 'displayed an energy consumption of 11.2kWh/100km' over 152 km with ~30% congestion."),
    "E10": dict(name="CarsOfMalaysia - The Proton e.MAS 7 driven: how far can it actually go on a full charge?", url="https://carsofmalaysia.com/car-reviews/the-proton-e-mas-7-driven-how-far-can-it-actually-go-on-a-full-charge/",
                date="2025-02-12", note="Efficiency challenge, 152 km, 11.3 kWh/100 km, 32% battery (internally inconsistent with 60.22 kWh); eco-driving - excluded from ratio."),
    "E11": dict(name="AutoApp.sg - Proton e.MAS 7 review", url="https://www.autoapp.sg/?p=283450", date="2025-09-16",
                note="Spec: 16.6 kWh/100km (claimed); 'Real-world testing delivered energy consumption between 13.5 to 15.2kWh/100km' (Singapore; method not stated)."),
    "E12": dict(name="OneShift - Proton e.MAS 7 Premium (100 kW) review", url="https://www.oneshift.com/articles/car-reviews/proton-e.mas-7-premium-(100-kw)-review:-more-than-just-a-good-deal/",
                date="2026-11-02", note="Singapore spec: 410 km (WLTP); efficiency 16.6 kWh/100 km (rated). No observed figure."),
    "E13": dict(name="paultan.org - 2024 smart #1 Premium review", url="https://paultan.org/2024/01/09/2024-smart-1-premium-review-the-good-and-the-bad/",
                date="2024-01-09", note="'in almost 500 km ... I averaged a power consumption of just 13.2 kWh/100 km'; method not stated."),
    "E14": dict(name="paultan.org - 2023 BYD Dolphin Malaysian review", url="https://paultan.org/2023/09/19/2023-byd-dolphin-malaysian-review-a-great-value-ev/",
                date="2023-09-19", note="Premium Extended Range: 'consumption graph recorded a 13.8 kWh/100 km average on the outbound run'; Standard Range used 24% of 44.92 kWh over 66.8 km."),
    "E15": dict(name="Newswav (Carz Automedia) - Malaysia's electricity protection is now 800 kWh: how much power does an EV use per 100 km?", url="https://newswav.com/article/malaysia-s-electricity-protection-is-now-800-kwh-how-much-power-does-an-ev-A2609_MRSDIn",
                date="2026-09-18", note="e.MAS 5 Premium trip computer 10 kWh/100 km (citing Zigwheels); e.MAS 7 Prime 11 kWh/100 km (citing paultan); Model 3 RWD WLTP 13.0; Model Y Premium RWD WLTP 13.9; iCaur V23 NEDC 22.0. Secondary aggregator."),
    "E16": dict(name="paultan.org - Proton e.MAS 5 previewed, rebadged Geome Xingyuan (2025-08-08); e.MAS 7 co-developed with Geely Galaxy E5 (2024-08-02)",
                url="https://paultan.org/2025/08/08/proton-emas-5-previewed-rebadged-geome-xingyuan-rwd-250-to-325-km-wltp-oct-launch", date="2025-08-08",
                note="e.MAS 5 Premium 40.16 kWh, 325 km WLTP; Prime 30.12 kWh, ~250 km WLTP. e.MAS 7 / Galaxy E5 relationship from search results (https://paultan.org/2024/08/02/proton-emas7-ev-suv-previewed-in-malaysia)."),
    "E17": dict(name="US DOE/EPA fueleconomy.gov - All-Electric Vehicles (EV technology; ORNL estimates)", url="https://www.fueleconomy.gov/feg/evtech.shtml", date="accessed 2026-11-23 (no page date)",
                note="'Battery charging efficiency can vary, but it is often 84% to 93%'; 'EVs convert over 77% of the electrical energy from the grid to power at the wheels.'"),
    "E18": dict(name="US DOE/EPA fueleconomy.gov - Where the Energy Goes: Electric Cars", url="https://www.fueleconomy.gov/feg/atv-ev.shtml", date="accessed 2026-11-23 (no page date)",
                note="Charging losses 16% city / 10% highway / 10% combined, 'based on tests of several EVs by Argonne National Laboratory'; excludes cabin heating/cooling."),
    "E19": dict(name="US EPA - Fuel Economy and EV Range Testing", url="https://www.epa.gov/greenvehicles/fuel-economy-and-ev-range-testing", date="last updated 2026-07-01",
                note="'MPGe values provided by EPA include charging losses'; 'assume level 2, alternating current (AC) charging'; measurement moved 'to the outlet in the wall'."),
    "E20": dict(name="ADAC - Ladeverluste beim Elektroauto: Wie hoch sind sie wirklich? (W. Rudschies)", url="https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/laden/ladeverluste-elektroauto-studie/", date="2026-08-06",
                note="AC 11 kW wallbox losses 5.1-7.0%; 4.1 kW 8.0-12.8%; 2.3 kW socket 12.7-24.2%; DC: charger ~3% + battery conditioning 2-8% = 5-15%; loss = grid energy not available for driving; incl. 100-300 W control-unit load during charging."),
    "E21": dict(name="Apostolaki-Iosifidou E., Codani P., Kempton W. (2017) 'Measurement of power loss during electric vehicle charging and discharging', Energy 127:730-742",
                url="https://ideas.repec.org/a/eee/energy/v127y2017icp730-742.html", date="2017",
                note="Abstract (via RePEc): one-way losses 12-36% in the tested conditions; largest losses in AC-DC power electronics, worse at low power and low SoC. Lab set-up incl. building circuits."),
    "E22": dict(name="Phase 1.5 fleet exposure (this project) - leap_bev_exposure_input.csv", url="outputs/tables/leap_bev_exposure_input.csv", date="2026-11-23",
                note="vehicle_years by year/scenario/case/geography (annual average active stock)."),
    "E23": dict(name="data.gov.my - Car registration transactions (JPJ) - BEV model mix", url="https://data.gov.my/data-catalogue/registration_transactions_car", date="data to 2026-10-31",
                note="maker/model of every BEV registration 2009-Oct 2026 (same files as Run 1, S02)."),
}

# ======================================================================================
# PHASE 3 (Run 4) - hourly BEV charging profiles 2030, unmanaged vs TNB-ToU managed.
# Everything above is Run 1-3 configuration and is unchanged.
# ======================================================================================
RUN3_ARCHIVE = ROOT / "outputs" / "archive" / "run3_2026-11-23"
HOURLY_YEAR = 2030
LOCAL_TZ = "Asia/Kuala_Lumpur"           # Malaysian Standard Time, UTC+08:00, no daylight saving
EVIPRO_DIR = LITERATURE / "evipro_lite"
# Mileage cases carried into the hourly model (project-owner decision 2026-11-23): working base
# 17,969 km; explicit GIZ/MOT 15,000 km sensitivity (base fleet, consumption, efficiency held).
HOURLY_MILEAGE_CASES = {"base_17969km": ANNUAL_KM_BASE, "giz_15000km": 15000.0}

# ---- TNB Time-of-Use (official: tnb.com.my ESG story + myTNB tariff page, retrieved 2026-11-23) ----
TOU_PEAK_HOURS_WEEKDAY = list(range(14, 22))   # hour-beginning 14:00..21:00 -> peak 2 PM-10 PM Mon-Fri
# TNB lists 15 named public holidays as all-day off-peak. Only those with a FIXED calendar date by
# definition are dated here; lunar/variable holidays (Chinese New Year x2, Hari Raya Aidilfitri x2,
# Wesak, Agong's Birthday, Hari Raya Aidiladha, Awal Muharram, Maulidur Rasul, Deepavali) have no
# official 2030 gazette yet and are NOT dated (treated as ordinary days - flagged limitation).
TOU_FIXED_DATE_HOLIDAYS_2030 = {"2030-01-01": "New Year's Day", "2030-05-01": "Labour Day",
                                "2030-08-31": "Independence Day", "2030-09-16": "Malaysia Day",
                                "2030-12-25": "Christmas Day"}
TOU_UNDATED_HOLIDAYS = ["Chinese New Year (day 1)", "Chinese New Year (day 2)", "Hari Raya Aidilfitri (day 1)",
                        "Hari Raya Aidilfitri (day 2)", "Wesak Day", "Yang di-Pertuan Agong's Birthday",
                        "Hari Raya Aidiladha", "Awal Muharram", "Maulidur Rasul", "Deepavali"]

# ---- Charging-location ENERGY shares (share of annual grid charging electricity) ----------------
# SCENARIO ASSUMPTIONS informed by: EVI-Pro Lite (US simulation, 30 C, 35 mi/day: home 37-73%,
# workplace 15-30%, public L2 12-29%, DC 1-5% depending on home access); INL EV Project (US early
# adopters with 100% home L2: 84-87% of charging EVENTS at home); Malaysian review (60% of users
# PREFER home, 29% public; limited interest in workplace charging - preference, not energy);
# MEVnet public charger count 5,839 incl. 1,971 DC (31 Mar 2026, secondary). No Malaysian measured
# energy shares were found.
LOCATION_MIX = {
    "base":      {"residential": 0.60, "workplace": 0.05, "public_ac": 0.15, "public_dc": 0.20},
    "home_low":  {"residential": 0.45, "workplace": 0.05, "public_ac": 0.20, "public_dc": 0.30},
    "home_high": {"residential": 0.75, "workplace": 0.05, "public_ac": 0.10, "public_dc": 0.10},
    "work_high": {"residential": 0.55, "workplace": 0.15, "public_ac": 0.12, "public_dc": 0.18},
}
LOCATIONS = ["residential", "workplace", "public_ac", "public_dc"]
# relative daily charging energy on weekend/holiday vs weekday, by location (EVI-Pro Lite HA100/Home80
# weekend vs weekday workplace energy ~0.25; others neutral)
WEEKEND_ENERGY_FACTOR = {"residential": 1.0, "workplace": 0.25, "public_ac": 1.0, "public_dc": 1.0}

# ---- Session model (residential and workplace) -------------------------------------------------
N_SESSIONS = 40000
SESSION_SEED = 20300101
STEP_MIN = 15
# Residential plug-in hour distribution: APPROXIMATE visual reading of Liu et al. (2024) Fig. 10,
# 'Simulation' series (EVI-Pro, Colorado). The figure's last bar spans hours 22-23 and is split evenly.
LIU2024_PLUG_START = [0.005, 0.003, 0.002, 0.002, 0.002, 0.002, 0.002, 0.005, 0.009, 0.014, 0.024, 0.040,
                      0.052, 0.055, 0.062, 0.087, 0.118, 0.143, 0.115, 0.100, 0.068, 0.052, 0.0275, 0.0275]
# Residential unplug hour (next morning): approximate reading of Liu et al. (2024) Fig. 11, hours 4-11
LIU2024_UNPLUG_MORNING = {4: 0.016, 5: 0.050, 6: 0.110, 7: 0.167, 8: 0.133, 9: 0.107, 10: 0.080, 11: 0.055}
HOME_SESSION_KWH = {"mean": 12.0, "cv": 0.6, "min": 2.0, "max": 60.0}   # grid-side kWh per home session (assumption)
HOME_POWER_MIX = {2.3: 0.20, 7.4: 0.70, 11.0: 0.10}                     # kW at the charger input (assumption)
# Workplace: NREL (Neuman et al. 2021) pre-COVID distributions - APPROXIMATE visual readings
NREL_WP_ARRIVAL_30MIN = {5.0: 0.2, 5.5: 1.0, 6.0: 2.4, 6.5: 6.7, 7.0: 11.9, 7.5: 17.5, 8.0: 17.5, 8.5: 9.9, 9.0: 4.2,
                         9.5: 2.6, 10.0: 1.8, 10.5: 1.7, 11.0: 2.0, 11.5: 3.0, 12.0: 3.5, 12.5: 4.3, 13.0: 3.3,
                         13.5: 2.1, 14.0: 1.5, 14.5: 1.0, 15.0: 0.7, 15.5: 0.7, 16.0: 0.3, 16.5: 0.2, 17.0: 0.1, 17.5: 0.1}
NREL_WP_PARK_HOURS_30MIN = {0.0: 1.2, 0.5: 0.7, 1.0: 1.5, 1.5: 2.3, 2.0: 3.3, 2.5: 3.8, 3.0: 5.9, 3.5: 6.5, 4.0: 5.9,
                            4.5: 5.1, 5.0: 3.7, 5.5: 3.8, 6.0: 3.4, 6.5: 3.9, 7.0: 4.5, 7.5: 5.7, 8.0: 7.8, 8.5: 8.8,
                            9.0: 8.7, 9.5: 5.8, 10.0: 3.5, 10.5: 1.9, 11.0: 0.95, 11.5: 0.5, 12.0: 0.3, 12.5: 0.1}
NREL_WP_ENERGY = {"median": 9.5, "mean": 11.1, "max": 68.3}            # energy_charged, Fig. 4 (exact text values)
NREL_WP_POWER_MIX = {3.3: 0.6, 6.6: 0.4}                                # max_charge_power median 3.3, mean 4.0 (Fig. 4)
WORKPLACE_POWER_MIX_MY = {7.4: 0.8, 11.0: 0.2}                          # Malaysian workplace AC (assumption)
# NREL Fig. 15 pre-COVID average EVSE power by hour (kW, APPROXIMATE visual reading; validation only)
NREL_WP_FIG15_KW = [0, 0, 0, 0, 0, 0.1, 3, 25, 62, 66, 52, 40, 32, 31, 26, 18, 9, 3, 1, 0.3, 0.2, 0, 0, 0]
DC_SMOOTH_HOURS = 3                                                     # circular moving average for EVI-Pro DC shape

# ---- Managed charging ----------------------------------------------------------------------
PARTICIPATION_LEVELS = [0.0, 0.25, 0.50, 0.75, 1.0]
PROVISIONAL_PARTICIPATION = 0.50     # ASSUMED intermediate case for LEAP comparison - not measured uptake
MANAGED_LOCATIONS = ["residential"]  # ToU is a household tariff; workplace/public charging not ToU-managed

# ======================================================================================
# PHASE 3.1 - Malaysian-informed public AC / destination charging profile (SENSITIVITY).
# Everything above is Run 1-4 configuration and is unchanged. Phase 3 outputs are frozen in RUN4_ARCHIVE.
# ======================================================================================
RUN4_ARCHIVE = ROOT / "outputs" / "archive" / "run4_2026-11-23"
INDUSTRY_EVIDENCE_DATE = "2026-11-23"    # date the project owner relayed the observations (personal communication)
# Peak TIMING from qualitative industry observations (industry practitioner, personal communication, anonymised;
# 'active usage' of AC destination chargers - malls, SOHO car parks; weekdays; several months of data; coverage, sample, power and the
# definition of 'active usage' NOT confirmed). Windows are the reported clock times (MYT, continuous hours).
INDUSTRY_WEEKDAY_WINDOWS = {"lunch": (12.0, 14.0), "after_work": (17.0, 18.0), "dinner": (20.0, 22.0)}
INDUSTRY_WEEKDAY_PEAK_HOURS = {"lunch": [12, 13], "after_work": [17], "dinner": [20, 21]}   # hour-beginning bins in each window
INDUSTRY_WEEKEND_WINDOW = (12.0, 16.0)   # sustained ~12:00-16:00 peak, unimodal (as reported)
# ---- RESEARCHER-DEFINED numerical assumptions (not observed) ----------------------------------------
# Every shape = overnight floor + smoothed 'open-hours' background + smoothed boxcar peak(s) over the reported windows.
# Levels are relative to the (largest) peak height of the day type before normalization.
INDUSTRY_FLOOR_LEVEL = 0.05              # overnight activity (SOHO residents, late visitors)
INDUSTRY_BACKGROUND_LEVEL = 0.30         # daytime activity outside the reported peaks
INDUSTRY_BACKGROUND_HOURS = {"weekday": (9.0, 23.0), "weekend_holiday": (10.0, 22.0)}   # typical mall opening hours
INDUSTRY_BACKGROUND_SMOOTH_H = 1.0
# Relative weekday peak MAGNITUDES (hourly maxima, lunch : after-work : dinner) - researcher-defined scenarios;
# magnitudes were NOT reported. 'equal' is the neutral (minimum-information) default.
INDUSTRY_PEAK_CONFIGS = {"equal": (1.0, 1.0, 1.0), "lunch_dominant": (1.5, 1.0, 1.0),
                      "after_work_dominant": (1.0, 1.5, 1.0), "dinner_dominant": (1.0, 1.0, 1.5)}
INDUSTRY_DEFAULT_CONFIG = "equal"
# Peak edge smoothing (Gaussian sigma, h) - width sensitivity. 'wide' is the identifiability limit: with unequal
# magnitudes one weekday peak merges into its neighbour (reported, flagged per variant).
INDUSTRY_PEAK_WIDTHS = {"narrow": 0.5, "default": 0.75, "wide": 1.0}
INDUSTRY_DEFAULT_WIDTH = "default"
# Weekend/holiday : weekday DAILY public AC energy per active vehicle-day (hypothetical; 1.0 = interpretation 1:
# higher instantaneous weekend activity with equal daily energy). Applied jointly so annual energy is unchanged.
INDUSTRY_WEEKEND_MULTIPLIERS = [1.0, 1.25, 1.50]
# Public AC share of annual BEV charging energy (baseline 15%); other locations rescaled pro rata to sum to 100%
PUBLIC_AC_SHARE_SENSITIVITY = [0.10, 0.15, 0.20, 0.25]
P31_CHARGING_CASES = [("unmanaged", 0.0, "unmanaged"), ("managed_staggered_p50", 0.5, "staggered"),
                      ("managed_staggered_p100", 1.0, "staggered"), ("managed_synchronized_p50", 0.5, "synchronized"),
                      ("managed_synchronized_p100", 1.0, "synchronized")]
# ---- Physical-plausibility check (session library; ALL values researcher-defined, not observed) ------------
# Destination visit types: (arrival mean h, arrival sd h, dwell median h, dwell lognormal sigma)
DEST_VISIT_TYPES = {
    "morning_errand":   (9.5, 0.6, 1.5, 0.4),
    "lunch":            (12.2, 0.35, 1.25, 0.3),
    "midday_long_stay": (12.5, 0.8, 3.0, 0.3),
    "afternoon":        (15.0, 0.8, 1.5, 0.4),
    "after_work_stop":  (16.9, 0.3, 1.0, 0.3),
    "dinner":           (19.9, 0.4, 1.75, 0.3),
    "late_evening":     (21.5, 0.5, 1.25, 0.4),
    "overnight_soho":   (22.5, 1.0, 9.0, 0.2),
}
DEST_POWER_MIX = {7.4: 0.6, 11.0: 0.4}                    # kW, AC (single-phase 32 A / three-phase 16 A), assumption
DEST_SESSION_KWH = {"median": 10.0, "mean": 12.0, "max": 60.0}   # requested grid kWh per visit (assumption)
DEST_N_PER_TYPE = 8000
DEST_SEED = 20300311
# Secondary context only (already in the Phase 3 register, H08): MEVnet 5,839 public chargers incl. 1,971 DC,
# national, 31 Mar 2026. NOT a 2030 capacity and NOT used in any calculation of load.
MEVNET_PUBLIC_CHARGERS_2026 = {"total": 5839, "dc": 1971, "date": "2026-03-31", "status": "secondary, national"}

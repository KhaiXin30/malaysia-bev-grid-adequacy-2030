# Phase 1.5 - BEV fleet exposure: methodology

*Run 2, 23 Nov 2026. This extends Run 1 (22 Nov 2026; `research_methodology.md`, `final_report.md`), which is not modified. Code: `src/exposure.py`, `src/phase15.py`, `src/validation_exposure.py`, `src/figures_exposure.py`. Run everything with `python src/run_all.py`.*

## 1. Purpose

Annual electricity use depends on how many BEVs operate *during* a year, not on how many are on the road at midnight on 31 December. In a fast-growing fleet the 31-December stock overstates the vehicles in service across the year. Run 2 adds the following for 2025-2030, nationally and for Peninsular Malaysia (estimated):
- beginning-of-year stock
- end-of-year stock
- **annual average stock**
- vehicle-years
- new registrations
- retirements

## 2. What is reused unchanged from Run 1
- **Annual BEV registration paths** for all 3 scenarios × 3 cases (`stock.registration_paths`): the 2025 observed figure (44,813), the 2026 estimate (71,911), and the 2027-2030 policy and trend projections. Validation confirms they match `bev_forecast_2025_2030.csv` exactly.
- **Policy definitions:**
  - 20% xEV is the PRIMARY case; 30% is a SENSITIVITY.
  - The target applies to JPJ registrations (A04).
  - The xEV share follows a linear path (A09).
  - BEV share within xEV: 45% / 56.2% / 70% (A10).
  - Market growth: −1.5% / +1.0% / +2.5% a year (A08).
- **Weibull survival** (A11):
  - low: median 14 years, k = 2.0
  - base: median 18 years, k = 2.5
  - high: median 22 years, k = 3.0
  - The survival case follows the scenario case, as in Run 1.
- **Peninsular allocation** (A12-A13):
  - Base: data-derived, maker-reweighted shares for observed cohorts, and 92% for the 2027-2030 cohorts.
  - Low and high: 88% and 95% applied to every cohort (the Run 1 envelope convention).
- **Run 1 outputs.** All Run 1 tables are regenerated and checked to be byte-identical to the archived copies in `outputs/archive/run1_2026-11-22/` (validation requirement 1).

## 3. Model

### 3.1 Cohorts and timing
Registrations are held as **daily cohorts**, 1 Jan 2009 to 31 Dec 2030. No BEVs were registered before 2009.

| Period | Monthly totals | Spread within the month |
|---|---|---|
| Jan 2009 - Oct 2026 (observed) | JPJ aggregate monthly BEV counts (`registrations_type_fuel`) | In proportion to the actual daily BEV registration dates in the transaction files (`registration_transactions_car`). Monthly totals are preserved exactly. |
| Nov-Dec 2026 (estimated) | Run 1's estimated remainder (71,911 − 58,130 = 13,781), split by the seasonal profile | Uniform across days |
| 2027-2030 (projected) | Run 1 annual totals × seasonal profile | Uniform across days |

**Seasonal profile (A16).** This is each month's mean share of annual *total-car* registrations over 2022-2025, the same window Run 1 used for the Nov-Dec estimate:

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 6.7% | 7.4% | 9.3% | 7.3% | 8.1% | 7.6% | 8.3% | 9.2% | 8.0% | 9.1% | 8.9% | 10.2% |

The full table is in `exposure_timing_profile.csv`.

Total cars are used rather than BEVs because BEV monthly patterns in 2023-2026 are dominated by growth and one-off events: the Dec 2025 rush to buy CBU BEVs before the incentive expired, and launch months.

### 3.2 Active stock and exposure
A vehicle enters the fleet at the midpoint of its registration day and survives with S(a), where age a is measured in years of 365.25 days. With w_c the Peninsular share of cohort year c (w = 1 nationally):

$$N(t)=\sum_{d:\,e_d\le t} r_d\,w_{c(d)}\,S(t-e_d)$$

| Quantity | Definition |
|---|---|
| `stock_end` | N at 24:00 on 31 December |
| `stock_beginning` | `stock_end` of the previous year |
| `vehicle_years` | $\int_{\text{year}} N(t)\,dt$, evaluated day by day (midpoint rule). A vehicle accrues 0.5 day on its registration day, S(k/365.25) days on the k-th day after it, and **nothing before registration**. |
| `stock_annual_average` | $N_{avg,y} = \frac{1}{T_y}\int N(t)\,dt$, with T_y = 1 calendar year (365 or 366 days). Because T_y is one year, `vehicle_years` equals `stock_annual_average` numerically; they differ only in unit (A19). |
| `retirements` | `stock_beginning` + `new_registrations` − `stock_end`. Validated separately against a cohort-by-cohort count of deaths. |

Both the stock and the vehicle-days are discrete convolutions of the daily registration series with survival kernels. That makes the calculation exact for the stated timing assumptions, and fast (all 18 runs take about 1 s).

### 3.3 Peninsular Malaysia
Each daily cohort is multiplied by the Peninsular share of its cohort year (§2), so the share applies consistently to registrations, stocks, vehicle-years and retirements.

Peninsular new registrations are therefore **estimates** (national × share). The JPJ state field is the office of registration: 78-84% of 2025-26 BEVs are "Rakan Niaga" with no state. It is not where the vehicle operates. Every Peninsular figure is an estimate, not an observed operating fleet.

## 4. Comparison with Run 1 and with the simple approximation

**End-of-year stock** (`exposure_vs_run1_reconciliation.csv`):
- With the Run 1 timing convention (annual cohorts at mid-year), the daily engine reproduces Run 1's 31-Dec stock within 0.01% everywhere (514,935 vs 514,932 for 2030, national, 20% base). The residual comes from day counting.
- With the refined base timing, 31-Dec stock is **+0.01% to +0.09%** above Run 1. For 2030, national, 20% base: 515,091 vs 514,932.
- This is immaterial. **The Run 1 31-Dec exports are kept as published**, and the refined values appear only in the new exposure files, labelled as such.

**Annual average vs the endpoint approximation** (N_beg + N_end)/2:
- The approximation is *not* used as the result.
- It overstates the cohort-integrated average:
  - by 9.2% in 2025, because the Dec 2025 CBU rush put many BEVs on the road only at the end of the year
  - by 2.2% in 2026
  - by about 0.5% in 2027-2030 (2030 Peninsular, 20% base: 427,534 vs 425,537), because December is the heaviest month in the seasonal profile

**Timing sensitivity (G)** on the 2030 Peninsular average, 20% base:
- uniform forecast months: +0.54%
- Run 1 mid-year cohorts: +0.46%
- uniform-within-month history, ignoring daily dates: −0.01%

Monthly integration therefore changes the 2030 result by about 0.5%. It matters much more for 2025-2026, where real registration dates are strongly back-loaded.

## 5. Sensitivity analysis (one at a time; `fleet_exposure_sensitivity_2030.csv`, fig12)
- **Metric:** 2030 Peninsular annual average active stock.
- **Baseline:** 20% xEV base (425,537). The 30%-baseline version is also in the CSV.
- **Method:** each factor is moved on its own; everything else stays at base.

| Factor | Setting | 2030 Pen. average | vs baseline |
|---|---|---|---|
| A. xEV target | 30% | 518,623 | +21.9% |
| F. Policy denominator | MAA TIV basis × JPJ/MAA BEV ratio (A17) | 477,561 | +12.2% |
| B. BEV share within xEV | 45% / 70% in 2030 | 391,561 / 467,075 | −8.0% / +9.8% |
| E1. Peninsular share, all cohorts | 88% / 95% | 407,030 / 439,408 | −4.3% / +3.3% |
| C. Market growth | −1.5% / +2.5% a year | 409,091 / 435,768 | −3.9% / +2.4% |
| E2. Peninsular share, 2027-30 cohorts only | 88% / 95% | 413,077 / 434,881 | −2.9% / +2.2% |
| D. Survival | low / high | 414,703 / 429,075 | −2.5% / +0.8% |
| G1-G3. Registration timing | see §4 | 425,515 - 427,819 | −0.0% to +0.5% |

**Combined envelopes** (all-low and all-high combinations, as in Run 1) for the 2030 Peninsular average:
- 20%: 350,976 - 498,409
- 30%: 422,236 - 615,581
- trend: 437,538 - 769,314

These are scenario ranges. They are **not** statistical confidence intervals.

**F, policy denominator (A17).** The 2030 value reuses the Run 1 cross-check exactly:
- MAA TIV of 800,000 × 1.01⁴
- × target
- × BEV/xEV of 0.50
- × the 2025 JPJ/MAA BEV ratio of 1.453

For 2027-2029, the xEV share of TIV runs linearly from MAA's 2026 forecast share (15%) to the target. 2026 stays at the JPJ estimate.

**Caveat on F.** The same reconciliation applied to 2026 implies about 87,200 JPJ BEVs, against the 71,911 estimate. The 2025 JPJ/MAA ratio was inflated by non-MAA brands and the Dec 2025 CBU rush, so F is probably an upper-side variant.

## 6. Review of the 20% policy scenario (`policy_path_review_2026_2030.csv`, `policy_path_review_summary.csv`)

**Internal consistency.** All checks pass:
- Within each path, BEV = total × xEV share × BEV-in-xEV exactly.
- The market and BEV-in-xEV paths are identical in the 20% and 30% cases.
- 2026 is common to all scenarios.
- All shares stay within [0, 1], and the xEV share rises monotonically to the target.

**What the 20% case implies.**

| Measure | Observed / estimated | 20% base, 2026E-2030 |
|---|---|---|
| xEV share of cars | 14.4% in 2026 | rises only 5.6 pp in four years, to 20% |
| BEV registrations | +119% a year (CAGR 2022-2026E) | **+9.6% a year**, to 103,800 in 2030 |
| BEV share of cars | 8.1% in 2026 | 11.25% in 2030 |
| Hybrid registrations | | +9.6% a year (BEV-in-xEV held at 56.2%) |

The 20% low case is the most restrictive:
- BEV registrations are almost flat: +1.1% a year, falling 0.3% in 2030.
- BEV-in-xEV falls to 45%.
- The market shrinks 1.5% a year.

**How the trend case relates.**
- The trend base (linear BEV share) gives 137,692 BEVs in 2030, a BEV share of 14.9%. That is practically the same as the 20% *high* case (137,023).
- If hybrids keep their 2026 share of cars (6.3%), the trend base implies an xEV share of about 21%.
- So the independent trend lands near or slightly above the 20% target, not at 30%. Trend high (logistic, K = 30%) implies about 34% xEV.

**Characterisation.**
- The 20% case is the **primary policy-target case**: it is the only target in a formal policy document (NETR, as cited by MITI).
- It is a **relatively conservative adoption trajectory**: it implies a sharp slowdown from the 2023-2026 growth rates, with BEV CAGR falling from over 100% to about 10%.
- It is a **reasonable lower-central baseline, but not necessarily the most likely forecast**.
- The other two cases bracket it:
  - The historical trend (base 476,922 Peninsular average in 2030) sits about 12% above it.
  - The 30% case (518,623) represents sustained policy-driven growth. It should be used as the demand stress test.

The scenario is not replaced.

## 7. Changes relative to Run 1 (also `outputs/tables/run2_change_log.csv`)

| id | Type | Change | Impact |
|---|---|---|---|
| C01 | extension | Adds annual average stock, vehicle-years, beginning stock and retirements from daily cohort integration | New outputs only. 2030 Peninsular 20% base: average 425,537 vs 31-Dec 473,886. |
| C02 | method refinement (reported, not substituted) | Monthly and daily cohort timing instead of Run 1's annual mid-year cohorts | 31-Dec stock +0.01% to +0.09% vs Run 1. Run 1 31-Dec exports kept unchanged. |
| C03 | extension | Sensitivity analysis widened to xEV target, Peninsular share, policy denominator and timing, using the Peninsular average stock | New file. Run 1 `stock_sensitivity_2030.csv` unchanged. |
| C04 | clarification | Run 1 final report said the policy denominator "changes 2030 flows by ±15-20%". Under the Run 1 reconciliation it is **+16.5%, one-sided**. The −20% figure is MAA-basis sales not converted to registrations. | Wording only. `final_report.md` left untouched; corrected in `phase_1_5_summary.md`. |

**No reproducible numerical error was found in Run 1.** All Run 1 numbers are retained.

## 8. Outputs

| File | Content |
|---|---|
| `outputs/tables/leap_bev_exposure_input.csv` | LEAP file. Columns as specified; 108 rows = 3 scenarios × 3 cases × 2 geographies × 6 years. Integer vehicles. |
| `outputs/tables/leap_bev_exposure_data_dictionary.csv` | Definition and unit of every column |
| `outputs/tables/annual_bev_fleet_exposure_2025_2030.csv` | Detail: adds vehicle-days, days in year, endpoint approximation, Run 1 31-Dec stock and difference, cohort Peninsular share, status labels |
| `outputs/tables/fleet_exposure_sensitivity_2030.csv` | One-at-a-time results plus combined envelopes |
| `outputs/tables/exposure_vs_run1_reconciliation.csv` | Every timing variant × scenario × case × geography × year |
| `outputs/tables/policy_path_review_*.csv` | Task 5 path review |
| `outputs/tables/run2_change_log.csv` | Change log |
| `outputs/tables/fleet_exposure_assumptions.csv` | Run 2 assumptions A16-A19 plus the reused Run 1 assumptions |
| `outputs/tables/fleet_exposure_validation_results.csv` | Validation results |
| `outputs/tables/BEV_fleet_exposure_summary.xlsx` | Workbook of the above |
| `outputs/figures/fig09`-`fig12` | Figures |
| `reports/fleet_exposure_validation.md` | Generated validation report |

## 9. Limitations
- **Survival** is assumed. There are no BEV deregistration data (A11).
- **Timing of forecast months** uses total-car seasonality.
- **Within-day timing** assumes midday entry. Its effect is below 0.01%.
- **"Active"** means registered and not yet retired under the survival curve. It does not mean "driven daily". Utilisation (km per year) belongs to the next stage.
- **Peninsular** values are an allocation proxy (§3.3).
- **The 2026 Nov-Dec estimate** uses the Jan-Oct BEV share (8.1%). October 2026 alone was 6.1%. If that lower share persists, 2026 would be about 3,400 BEVs lower.

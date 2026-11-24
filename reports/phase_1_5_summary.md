# Phase 1.5 summary: BEV fleet exposure, forecast refinement and uncertainty

*Run 2, 23 Nov 2026. Data: JPJ via data.gov.my to October 2026, the same files as Run 1 (hash-verified). Run 1's `final_report.md` is unchanged and archived with all Run 1 outputs in `outputs/archive/run1_2026-11-22/`. Method: `fleet_exposure_methodology.md`. Tests: `fleet_exposure_validation.md`.*

## 1. 2030 end-of-year stock vs annual average active stock (base cases)

| Scenario | National 31 Dec (Run 1) | National 31 Dec (Run 2 timing) | **National annual average** | Peninsular 31 Dec (Run 1) | Peninsular 31 Dec (Run 2 timing) | **Peninsular annual average** |
|---|---|---|---|---|---|---|
| 20% xEV (PRIMARY) | 514,932 | 515,091 | **462,535** | 473,740 | 473,886 | **425,537** |
| 30% xEV (SENSITIVITY) | 643,076 | 643,231 | **563,716** | 591,632 | 591,775 | **518,623** |
| Historical trend (COMPARISON) | 588,420 | 588,576 | **518,388** | 541,348 | 541,492 | **476,922** |

- **The 2030 annual average is 10-12% below the 31-Dec stock**, because the fleet is still growing fast.
- Using the 31-Dec stock for annual energy would overstate 2030 BEV exposure by about 48,000 Peninsular vehicles in the 20% case.
- All Peninsular values are estimates (state-of-registration proxy), not an observed operating fleet.

## 2. Recommended LEAP input

**2030 Peninsular Malaysia annual average active BEV stock: 425,537 vehicles** (20% xEV base case). This equals 425,537 vehicle-years in 2030.

The full 2025-2030 series is in `outputs/tables/leap_bev_exposure_input.csv`: `scenario = 20pct_xev`, `case = base`, `geography = peninsular`, column `stock_annual_average`.

| Year | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| Peninsular average active BEVs, 20% base | 51,772 | 107,510 | 177,503 | 253,424 | 336,227 | 425,537 |

**Also run the 30% case (518,623 in 2030) as the demand stress test.** The 20% case is a conservative path (§5).

## 3. Low/high ranges, 2030 Peninsular annual average

These are combined envelopes (all-low and all-high combinations). They are scenario ranges, **not** statistical confidence intervals.

| Scenario | Low | Base | High |
|---|---|---|---|
| 20% xEV | 350,976 | **425,537** | 498,409 |
| 30% xEV | 422,236 | 518,623 | 615,581 |
| Historical trend | 437,538 | 476,922 | 769,314 |

The national annual-average envelopes are:
- 20%: 398,836 - 462,535 - 524,641
- 30%: 479,813 - 563,716 - 647,980
- trend: 497,202 - 518,388 - 809,804

## 4. Largest contributors to uncertainty

Effect on the 2030 Peninsular average, changing one factor at a time from the 20% base (fig12):

| Rank | Factor | Effect |
|---|---|---|
| 1 | **xEV target, 30% instead of 20%** | +21.9% |
| 2 | **Policy denominator** (MAA TIV sales instead of JPJ registrations) | +12.2%. Probably an upper-side variant: the reconciliation over-predicts 2026. |
| 3 | **BEV share within xEV** (45% / 70%) | −8.0% / +9.8% |
| 4 | Peninsular share (88% / 95% on all cohorts) | −4.3% / +3.3%. Applied to new cohorts only: −2.9% / +2.2%. |
| 5 | Market growth (−1.5% / +2.5% a year) | −3.9% / +2.4% |
| 6 | Survival (low / high) | −2.5% / +0.8% |
| 7 | Registration timing (uniform vs seasonal vs mid-year) | ≤ 0.5% |

Beyond these, the choice of adoption path itself (the trend high case reaches 769k) is the dominant structural uncertainty.

## 5. Review of the 20% scenario
- **It remains the primary policy-target case.** It is the only target in a formal policy document.
- **It is a relatively conservative trajectory.**
  - The xEV share was already 14.4% in 2026.
  - Reaching exactly 20% in 2030 implies BEV registrations growing +9.6% a year after 2026, against +119% a year over 2022-2026 and +60% in 2026.
  - In the 20% low case, BEV registrations are flat (+1.1% a year) and fall slightly in 2030.
- **It is a reasonable lower-central baseline, but not necessarily the most likely forecast.**
  - The independent trend base gives 137.7k BEVs in 2030. That equals the 20% *high* case and implies about 21% xEV if hybrids keep their 2026 share.
  - The trend's 2030 Peninsular average is 12% higher than the 20% case.
- **How the other cases help:**
  - The 30% case bounds sustained policy-driven growth.
  - The trend case shows where momentum alone leads.
  - LEAP should carry the 20% case as primary and the 30% case as the stress case.
- **Consistency checks** on the 2026-2030 paths (market, xEV share, BEV-in-xEV, 2026 continuity, 20%/30% use the same inputs) all pass.

## 6. Errors or inconsistencies found in Run 1

**No reproducible numerical error was found.** All Run 1 tables regenerate byte-identically. Points noted:

1. **Policy-denominator wording (C04).** Run 1's report says the denominator "changes 2030 flows by ±15-20%". Under its own reconciliation the effect is **+16.5%, one-sided**. The −20% figure is MAA-basis sales that were never converted to registrations. The wording is corrected here; `final_report.md` is not edited.
2. **The MAA-basis reconciliation is not anchored to 2026.** Applied to 2026, it implies about 87,200 JPJ BEVs against the 71,911 estimate. The 2025 JPJ/MAA ratio (1.453) was inflated by non-MAA brands and the Dec 2025 CBU rush. Treat variant F as upper-side.
3. **The Peninsular low/high cases also override the data-derived shares of historical cohorts.** This is Run 1's convention, kept for comparability (E1). The tornado also shows the narrower variant that changes only the 2027-2030 cohorts (E2).
4. **The mid-year registration convention** is an approximation, not an error. It moves 31-Dec stock by at most 0.09%. However, the endpoint approximation (N_beg + N_end)/2 would overstate the 2025 annual average by 9.2%, because of the December 2025 rush, so it should not be used for 2025-2026.
5. **The Nov-Dec 2026 estimate** uses the Jan-Oct BEV share (8.1%). October 2026 alone was 6.1%. If the lower share holds, 2026 registrations fall by about 3,400. That is small, but it should be replaced with actual data (November data due 10 Dec 2026).

## 7. What changed between Run 1 and Run 2

| | Run 1 (22 Nov 2026) | Run 2 (23 Nov 2026) |
|---|---|---|
| Stock metric | 31-Dec active stock | Adds beginning stock, **annual average**, vehicle-years and retirements, nationally and for Peninsular |
| Cohort timing | Annual cohorts at mid-year | Daily cohorts: actual dates where observed, 2022-2025 seasonality for forecast months. The Run 1 convention is kept as a sensitivity. |
| Registrations, assumptions, scenarios | - | **Unchanged** (verified) |
| 31-Dec stock | 514,932 (2030, national, 20% base) | 515,091 with refined timing (+0.03%). Run 1 exports retained. |
| Sensitivity | National 31-Dec stock: 3 factors | Peninsular annual average: 7 factor groups (A-G), tornado chart, envelopes |
| Validation | 24 checks | Run 1's 24 checks + 33 new checks covering the 12 required tests |
| New files | - | `leap_bev_exposure_input.csv` (+ dictionary), `annual_bev_fleet_exposure_2025_2030.csv`, `fleet_exposure_sensitivity_2030.csv`, reconciliation, path review, change log, workbook, fig09-fig12, 3 reports |

## 8. Reproducibility and validation
- **One command:** `.venv/bin/python src/run_all.py` reruns Run 1 and Run 2, in about 20 s.
- **Run 1 checks:** 24 / 24 PASS.
- **Phase 1.5 checks:** the 33 checks covering requirements 1-12 all pass. See `fleet_exposure_validation.md`, which is generated on every run.
- **Exit code:** the run exits non-zero if any check fails.
- **Integrity:** raw-data and Run 1 output checksums are stored in the archive.

## 9. Next research stage: parameters for BEV electricity demand (not estimated here)

No values are assumed below. Each item lists what is needed and where to look. Sources are candidates to verify; none has yet been consulted for a number.

| Priority | Parameter | Why it matters | Candidate authoritative sources (to verify) |
|---|---|---|---|
| 1 | **Annual driving distance of passenger cars in Malaysia** (km per vehicle per year). Ideally for Peninsular Malaysia, by vehicle age and for EVs specifically. | Scales demand linearly. Probably the largest single uncertainty. | Ministry of Transport / JPJ (any odometer or VKT study); PUSPAKOM inspection odometer records; MIROS road-safety and exposure surveys; the transport VKT activity data behind Malaysia's UNFCCC Biennial Update Reports / Biennial Transparency Report; Energy Commission (Suruhanjaya Tenaga) National Energy Balance (transport fuel use, for a top-down cross-check); MGTC / Low Carbon Mobility Blueprint; TNB or CPO EV-charging data (energy per EV) |
| 2 | **BEV electricity consumption** (kWh per 100 km, at the battery or the plug). Should be real-world, by segment, and weighted by the Malaysian BEV model mix. | Second linear scaling factor. Hot climate and air-conditioning load matter. | Manufacturer WLTP / homologation values for the top-selling models (from the JPJ transaction `maker`/`model` fields); real-world datasets such as EV-database real-range estimates and ICCT real-world consumption studies; tropical-climate studies of air-conditioning penalties; any Malaysian fleet or telematics data (e.g. ride-hailing, utility fleets) |
| 3 | **Grid-to-battery charging efficiency** (%), split by AC home / AC public / DC fast, and including charger and on-board charger losses | Converts battery energy to grid energy. It must be consistent with the definition in priority 2: WLTP figures are typically "from the plug". | Laboratory charging-efficiency tests (e.g. U.S. national-laboratory test programmes); IEC / SAE charger efficiency standards; the IEA Global EV Outlook methodology notes; manufacturer charger specifications |
| 4 | **Variation across vehicle types and users**: compact vs SUV/MPV BEVs, private vs ride-hailing/fleet, PHEV electric share (if PHEVs enter scope), mileage decline with vehicle age | Needed for the low/base/high envelopes and for the segment mix (premium electric MPVs coded `window_van` were 6% of 2025 BEVs) | JPJ transaction `type`/`model` mix (already in the repo); ride-hailing operator disclosures; APAD (land public transport agency) e-hailing statistics; international mileage-by-age curves only as labelled proxies |
| 5 | (Later, for peak load) Charging timing and location profiles | Not part of this stage | TNB / CPO session data; the GSO 2025 hourly demand profile (awaited) |

**Definition to settle before collecting data.** Annual BEV energy = `stock_annual_average` × km per vehicle per year × kWh per km ÷ charging efficiency. That requires the consumption and efficiency figures to be on a consistent "battery" or "plug" basis, and the mileage figure to refer to an *average active vehicle*, not a new vehicle.

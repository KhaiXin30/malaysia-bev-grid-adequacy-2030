# Final report - passenger BEV registrations and active stock to 2030 (Malaysia / Peninsular Malaysia)

*Data: JPJ via data.gov.my, through October 2026 (retrieved 22 Nov 2026). All values are vehicles. Stock is measured at 31 December. Methods and sources: `research_methodology.md`.*

## 1. Observed 2025 BEV registrations
**44,813** passenger BEVs were registered in 2025.
- **Definition:** JPJ new registrations, `type == 'car'`, `fuel == 'electric'`, national, calendar year 2025.
- **Published figure:** this matches the cited 44,813 exactly.
- **Malaysian Automotive Association (MAA) figure (30,848):** this is a sales count limited to MAA members, so it is a different measure. JPJ also counts non-member brands (Tesla alone: 7,282), imports, and the date of registration rather than sale.
- **Shares:** BEVs were 5.15% of 870,327 car registrations. The xEV proxy (BEV + hybrid, including PHEV) was 8.73%, consistent with MITI's reported 8.7% of cars registered.

## 2. Latest 2026 data (YTD, January-October)

| Measure | Jan-Oct 2026 | Comparison |
|---|---|---|
| BEV registrations | **58,130** | +86% vs Jan-Oct 2025 |
| Hybrid registrations | 45,215 | |
| Total car registrations | 716,764 | +3.1% |
| BEV share of car registrations | 8.1% | |
| xEV share of car registrations | 14.4% | |

Estimated full-year 2026 (Nov-Dec estimated, not observed): **71,911 BEVs** out of 886,684 cars.

## 3. Forecast 2030 new BEV registrations (national)

| Scenario | Low | Base | High |
|---|---|---|---|
| 20% xEV policy (primary) | 75,120 | **103,800** | 137,023 |
| 30% xEV policy (sensitivity) | 112,680 | **155,700** | 205,534 |
| Historical trend | 132,434 | **137,692** | 251,127 |

## 4. Forecast 2030 active BEV stock (31 Dec 2030)

| Scenario | National low | National base | National high | Peninsular low | Peninsular base | Peninsular high |
|---|---|---|---|---|---|---|
| 20% xEV policy (primary) | 433,464 | **514,932** | 595,555 | 381,448 | **473,740** | 565,778 |
| 30% xEV policy (sensitivity) | 533,609 | **643,076** | 754,622 | 469,576 | **591,632** | 716,891 |
| Historical trend | 561,286 | **588,420** | 940,183 | 493,931 | **541,348** | 893,174 |

Estimated active stock at end-2025 is 83,427 nationally (cumulative registrations 83,611) and 76,947 for Peninsular Malaysia. End-2026 is estimated at 155,064 nationally.

## 5. Peninsular Malaysia - how confident are these numbers?
- **Every Peninsular figure is estimated.** No official data gives BEVs by operating location.
- **State data are thin.** The JPJ state-of-registration field records the JPJ office used, or "Rakan Niaga" (the dealer partner portal). It does not record where an owner lives or drives. Rakan Niaga accounts for 78-84% of 2025-26 BEV registrations, so the state is unknown for most BEVs.
- **Estimated share.** Among BEVs with a known state, about 93% were registered in Peninsular Malaysia. Reweighting Rakan Niaga rows by maker gives 91.6-92.2%. The model uses 92% (range 88-95%).
- **Possible bias.** The two estimators disagree by 5-8 pp for all cars, so a selection bias of unknown size is possible.
- **Directly observed lower bound.** 30,266 BEVs were registered at Peninsular JPJ offices through October 2026.

## 6. Which forecast should be the primary LEAP input?
**Use the 20% base case** (`leap_bev_stock_input.csv`) as the primary input: 514,932 BEVs nationally and **473,740 for Peninsular Malaysia** in 2030.
- It is the only target published in a formal government document (NETR, as cited by MITI).
- Its assumptions are fully traceable, and the study design specifies it as primary.

**Also run the 30% case as the grid-adequacy stress test.** The data show the 20% case is a slow-adoption path:
- The 2026 xEV share is already 14.4%.
- Reaching exactly 20% in 2030 means BEV registrations grow only about 10% a year after 2026, against +60% in 2026.
- The independent trend (588k national) sits between the two policy cases.
- For peak-load adequacy, under-estimating load is the costlier mistake. The 30% case (643k national / 592k Peninsular) and the trend-high case (940k) bound that risk.

## 7. Biggest sources of uncertainty, ranked by effect on 2030 stock
1. **Which adoption path materialises:** 515k-643k across base cases, and a 433k-940k envelope.
2. **BEV share within xEV:** −48k/+58k in the 20% case. It depends on PHEV and HEV growth, and on BEV prices after the CBU incentive expiry.
3. **Policy denominator:** whether the target applies to JPJ registrations or MAA sales changes 2030 flows by ±15-20%.
4. **Total market growth:** −23k/+14k.
5. **Peninsular share and registration-state bias:** about ±4% on Peninsular stock.
6. **Survival / retirements:** −15k/+5k. There are no BEV deregistration data.
7. **Short history:** 5 informative years, so the trend models cannot be validated. Linear models under-forecast in backtests and logistic models over-forecast.

## 8. Items for your review before finalisation
1. **30% status.** Confirm 30% stays a sensitivity. This project found no formal document replacing the NETR 20% target.
2. **Policy denominator** (A04). Confirm the target should apply to JPJ passenger-car registrations rather than MAA TIV sales; the choice changes 2030 flows by ±15-20%.
3. **xEV share path shape** (A09). The model uses a straight line from 14.4% in 2026 to the 2030 target, which implies a sharp slowdown under 20%. Consider whether a front- or back-loaded path is preferable.
4. **BEV share within xEV** (A10): 45% / 56.2% / 70% in 2030. This is the largest assumption-driven sensitivity.
5. **Market growth** (A08): −1.5% / +1.0% / +2.5% a year.
6. **Survival curves** (A11). They are assumed, with no data. Also confirm whether LEAP should count *operating* vehicles or *registered* vehicles.
7. **Peninsular share** (A13): 88/92/95%. Check whether JPJ, MOT or TNB can supply state-level or operating-location data, which would remove the Rakan Niaga limitation.
8. **Nov-Dec 2026 estimate.** Replace it with actual data when published (November data due 10 Dec 2026), then re-run `src/run_all.py`.
9. **JPJ hybrid vs MAA HEV gap.** JPJ hybrids are 19% below MAA HEVs in 2025, which is unresolved. It may affect the xEV-proxy anchor.
10. **Trend case selection** (A14): base = linear share, high = logistic with K = 30%.
11. **Scope.** JPJ `car` includes electric premium MPVs coded `window_van` (6% of 2025 BEVs, kept), pick-ups (≤0.4%) and used imports.
12. **MAA forecast sources.** The MAA 2026 forecast and xEV split come from press reports (S08-S10), because the MAA forecast table is an image. Verify them against the original MAA documents if they are cited.

# Research methodology - passenger BEV registrations and active stock, Malaysia & Peninsular Malaysia, 2025-2030

*Project: Passenger BEV Charging and Grid Adequacy in Peninsular Malaysia (2030). Work package: BEV adoption and active stock (input to LEAP).*
*All data and web sources retrieved **22 November 2026**. Latest observation in the data: **October 2026**.*

---

## 1. Scope, units and definitions

| Item | Definition used |
|---|---|
| BEV | JPJ registrations with `type == 'car'` and `fuel == 'electric'` |
| Hybrid | JPJ `fuel == 'hybrid'` in the aggregate file (the transaction files use `hybrid_petrol`, `hybrid_diesel`). The brief expected `hybrid_petrol`/`hybrid_diesel` in the aggregate file, but only a single `hybrid` code exists there. |
| xEV (proxy) | BEV + hybrid. It includes PHEVs (evidence in §3.3). FCEVs (`hydrogen`, ≤1 vehicle/yr) are excluded as negligible. |
| Total car market | JPJ `type == 'car'`, `fuel == 'all_fuels'`. It is never added to the fuel breakdown rows. |
| "Passenger car" | JPJ `car` type, which includes the sub-types motokar, MPV, jip (SUV), pick_up and window_van. MAA classifies pick-ups as commercial vehicles. BEV pick-ups are ≤0.4% of BEVs (e.g. Maxus T90: 165 in 2025). JPJ codes premium electric MPVs as `window_van` (Denza D9, Zeekr 009, Xpeng X9: 2,693 in 2025, 6.0% of BEVs). These are passenger vehicles and correctly stay in scope. |
| Registrations vs sales | JPJ **registrations** of vehicles for road use are not **sales** (MAA total industry volume, TIV). JPJ also covers non-MAA brands (e.g. Tesla) and used/grey imports, and it dates each vehicle by registration date. Registrations are used here as a proxy for new sales; §4.4 explains why. |
| Flow vs stock | Annual registrations are a **flow**. Active stock is the number of BEVs on the road at **31 December**, computed from cohorts with survival (§7). Cumulative registrations are reported only for comparison. |
| Geography | The JPJ data and policy targets are **national (Malaysia)**. Peninsular Malaysia = all states except Sabah, Sarawak and W.P. Labuan (Putrajaya and Kuala Lumpur are included). |
| Units | Vehicles (integer counts). Shares are fractions (0-1) in CSVs. |

---

## 2. Data sources (full URLs, retrieved 2026-11-22)

| ID | Source | URL | Use |
|---|---|---|---|
| S01 | JPJ/MOT via data.gov.my - *registrations_type_fuel* (monthly, by type and fuel, 2000-01 to 2026-10; updated 10 Nov 2026) | https://data.gov.my/data-catalogue/registrations_type_fuel ; file https://storage.data.gov.my/transportation/registrations_type_fuel.csv | Primary dataset. The supplied file is byte-identical to the download. |
| S02 | JPJ/MOT via data.gov.my - *registration_transactions_car* (one row per car registration; fields date_reg, type, maker, model, colour, fuel, state) | https://data.gov.my/data-catalogue/registration_transactions_car ; files https://storage.data.gov.my/transportation/cars_YYYY.parquet | PHEV coding, maker mix, state of registration |
| S03 | MITI speech, Soft Launch of Malaysia Autoshow 2024 (Tengku Zafrul, 12 Dec 2023) | https://www.miti.gov.my/miti/resources/Speech/Malaysia_Autoshow_Soft_Launch_231212.pdf | 20% target |
| S04 | MITI speech, All New PROTON e.MAS 7 PHEV launch (Johari Abdul Ghani, 4 Feb 2026) | https://www.miti.gov.my/miti/resources/Speech/20260204_PROTONe.MAS7PHEVLaunch_A5_.pdf.pdf | 30% statement; 2025 TIV and xEV shares; PHEV launch date |
| S05 | MAA press release, Production & Sales Dec 2025 (20 Jan 2026) | https://maa.org.my/pdf/2025/pressreleasefordec2025.pdf | 2024-2025 passenger vehicle (PV) / commercial vehicle (CV) sales; Dec-2025 rush to buy fully imported (CBU) BEVs before incentives expired |
| S06 | MAA Market Review 2025 (20 Jan 2026) | https://maa.org.my/pdf/2025/Market_Review_2025.pdf | CBU BEV incentives expired 31 Dec 2025; BEV sales +78% (MAA basis) |
| S07 | MAA statistics page (PV/CV 2010-2023) | https://www.maa.org.my/statistics.html | TIV history |
| S08 | The Star, 23 Jan 2026 (quoting MAA, RHB) | https://www.thestar.com.my/business/business-news/2026/01/23/momentum-of-car-sales-likely-to-moderate | MAA xEV definition; JPJ includes non-MAA members; MAA Jan-2026 forecast |
| S09 | AutoBuzz, 20 Jan 2026 (quoting MAA) | https://autobuzz.my/2026/01/20/maa-malaysia-hits-all-time-high-tiv-in-2025-with-820752-units-sold-surpassing-800k-2-years-in-a-row/ | 2025 xEV 69,363 = HEV 38,515 + BEV 30,848 |
| S10 | The Sun, Jul 2026 (quoting MAA) | https://thesun.my/business/malaysian-automotive-association-lifts-2026-vehicle-sales-forecast-to-800000-units/ | MAA revised 2026 forecast (TIV 800k; PV 744k; xEV 120k) |
| S11 | paultan.org, 19 Nov 2026 (quoting MAA) | https://paultan.org/2026/11/19/maa-malaysian-vehicle-sales-oct-2026/ | Jan-Oct 2026 TIV 673,412 |
| S12 | The Star, 7 Oct 2026 (quoting MOT parliamentary reply) | https://www.thestar.com.my/news/nation/2026/10/07/4077-million-vehicles-registered-but-only-266-million-active | 40.77M registered / 26.6M "active" vehicles (~16M cars) at 30 Sep 2026 |
| S13 | paultan.org, 13 Jul 2026 (quoting JPJ) | https://paultan.org/2026/07/13/ev-sales-in-malaysia-first-half-of-2026-31738-units-up-85-on-last-year-proton-drives-growth/ | Cross-check of 1H 2026 BEV count |

S08-S13 are secondary press reports of official or industry figures. They are used only for cross-checks and for the MAA forecast values. Copies of the MITI and MAA PDFs, with extracted text, are archived in `data/raw/`. The MAA Market Review's 2026 forecast table is an image, so its forecast values come from S08/S10.

**Policy wording (verbatim):**
- S03 ¶10: *"…National Energy Transition Roadmap (NETR)… we have a set a national target, which is 20% of our annual new car sales consists of Electrified Vehicles (xEV) by 2030, 50% by 2040 and 80% by 2050."*
- S04 ¶9: *"…sales of electrified vehicles (xEVs), comprising electric and hybrid models, expanded sharply by 52 per cent. As a result, xEVs accounted for 8.5 per cent of new vehicle sales whereas hybrid and electric vehicles accounted 8.7 per cent of total cars registered in 2025. This trajectory gives us confidence in achieving our national target of 30 per cent xEV market share by 2030."*

The 30% figure appears in a ministerial speech. This project found no document that formally replaces the NETR 20% target, so 30% is treated as a **sensitivity**.

---

## 3. Step 1 - data audit (details: `reports/data_audit.md`)

### 3.1 Aggregate dataset
- 10,910 rows; columns `date, type, fuel, registrations`. No missing values, duplicate rows, duplicate keys or negative values.
- Coverage: monthly, 2000-01 to 2026-10 (322 months), all dated on the 1st of the month.
- Types: all_types, car, motorcycle, lorry, van, bus, other. Fuels: all_fuels, petrol, diesel, greendiesel, electric, hybrid, other.
- **Internal consistency:** in all 2,249 (date, type) groups, the fuel breakdown sums exactly to `all_fuels`. In all 1,995 (date, fuel) groups, the type breakdown sums exactly to `all_types`.
- Sparse series: a missing row means zero registrations that month (e.g. car/electric has 142 rows over a 208-month span).
- **2026 is incomplete (Jan-Oct).** It is labelled YTD and never compared unadjusted with full years.

### 3.2 Transaction dataset
- 870,188 car registrations in 2025, 715,879 in Jan-Oct 2026.
- BEV counts match the aggregate file within 1 vehicle per year. All-car totals differ by <0.03%, because the aggregate is derived from `registration_transactions_all`.

### 3.3 PHEV representation (verified)
JPJ has no PHEV code. The Proton e.MAS 7 is sold as a BEV (from Dec 2024) and as a PHEV (launched 4 Feb 2026, S04). In JPJ data its `hybrid_petrol` registrations are zero through Jan 2026 and start in **Feb 2026** (96, 646, 1,013 … in Feb, Mar, Apr), while its `electric` registrations continue. **PHEVs are therefore coded `hybrid_petrol` (aggregate: `hybrid`).**

JPJ "hybrid" thus means HEV + PHEV, and whether mild hybrids are included is unverified. HEV and PHEV cannot be split without model-level classification, which this project does not attempt. The xEV proxy covers the same technologies as the policy definition ("electric and hybrid models", S04).

### 3.4 Cross-check of 2025 against published figures (`crosscheck_2025_and_published_figures.csv`)

| Item | This project | Reference | Interpretation |
|---|---|---|---|
| BEV cars 2025 (JPJ) | **44,813** | 44,813 (JPJ, as cited by press) | Exact match, same definition |
| BEV 2025, MAA sales | 44,813 | 30,848 | MAA covers member-company sales only. JPJ also includes non-MAA brands (Tesla: 7,282 JPJ BEV registrations in 2025), imports, and registration timing. The JPJ figure is the right measure for the vehicle fleet. |
| Hybrid 2025 | 31,190 | MAA HEV 38,515 | **Unresolved.** JPJ hybrid is 19% *below* MAA HEV, possibly because of mild-hybrid or other coding differences. Flagged for review. |
| xEV share 2025 | 8.73% of car registrations | MITI: 8.7% of cars registered; 8.5% of new vehicle sales | Consistent |
| 1H 2026 BEV | 31,738 | 31,738 (paultan, JPJ) | Exact match |
| BEV 2011 to Nov-2023 | 14,026 | MITI Dec-2023: ">12,000 since 2011" | Consistent |

---

## 4. Step 2 - historical adoption

### 4.1 Annual history (JPJ, national, cars)

| Year | Total cars | BEV | Hybrid | xEV proxy | BEV share | xEV share | BEV share of xEV | BEV YoY |
|---|---|---|---|---|---|---|---|---|
| 2020 | 552,359 | 71 | 1,928 | 1,999 | 0.01% | 0.36% | 3.6% | +61% |
| 2021 | 530,057 | 257 | 2,731 | 2,988 | 0.05% | 0.56% | 8.6% | +262% |
| 2022 | 744,762 | 3,129 | 15,377 | 18,506 | 0.42% | 2.48% | 16.9% | +1,118% |
| 2023 | 832,347 | 13,301 | 22,215 | 35,516 | 1.60% | 4.27% | 37.5% | +325% |
| 2024 | 856,292 | 21,789 | 24,526 | 46,315 | 2.54% | 5.41% | 47.0% | +64% |
| 2025 | 870,327 | **44,813** | 31,190 | 76,003 | 5.15% | 8.73% | 59.0% | +106% |
| 2026 YTD (Jan-Oct) | 716,764 | **58,130** | 45,215 | 103,345 | 8.11% | 14.42% | 56.2% | +86% vs Jan-Oct 2025 |
| 2026 estimate | 886,684 | 71,911 | 55,934 | 127,845 | 8.11% | 14.42% | 56.2% | +60% vs 2025 |

**Estimating Nov-Dec 2026.**
- Total cars: Nov-Dec = Jan-Oct × mean ratio of (Nov+Dec)/(Jan-Oct) over 2022-2025. The ratios are 0.240, 0.233, 0.223 and 0.251, giving a mean of 0.2371.
- BEV and hybrid: the Jan-Oct 2026 shares of total cars are applied to the estimated Nov-Dec total. The 2025 Nov-Dec BEV pattern is *not* used because the CBU incentive-expiry rush distorted it (S05).
- The estimate is labelled `partial_estimated` everywhere.

### 4.2 Trend breaks, outliers and seasonality
- **Structural break in 2022.** Annual BEV registrations rose about 12-fold (257 to 3,129) and hybrids about 5.6-fold. The total market also jumped 40%, which coincides with the post-COVID recovery. Growth of +262% and +1,118% in 2021-2022 comes from a near-zero base and is **excluded from trend fitting** (the base window starts in 2022).
- **Outliers** (`monthly_bev_outliers.csv`, more than ±35% log deviation from a centred 5-month median):
  - Dec 2023, Dec 2024 and **Dec 2025 (8,123)** are year-end peaks. MAA (S05) attributes Dec 2025 to buyers rushing to purchase CBU BEVs before the tax incentives expired on 31 Dec 2025.
  - Feb 2026 is low (Chinese New Year seasonality plus the post-rush hangover).
  - **Aug 2026 (8,834)** is a record month.
- **Seasonality** (`seasonality_index_total_cars.csv`): December is the strongest month (index 1.23 in 2022-2025) and Jan-Feb the weakest (0.80-0.89).
- **Composition change in 2026:** Proton's e.MAS 5 and e.MAS 7, which are locally assembled, account for 48% of Jan-Oct 2026 BEVs (27,673 of 58,129), while CBU brands fell after the incentive expired (BYD 14,407 in 2025 vs 8,420 in Jan-Oct 2026). The PHEV launch moved part of xEV growth into "hybrid", which lowered the BEV share of xEV from 59.0% to 56.2%.

### 4.3 Trend models (independent of policy)
These models are fitted to annual data for 2022-2026E. The 2026 point is 10 months observed plus 2 months estimated.

| Model | Specification | 2030 BEV registrations (fit 2022-26E, base market) |
|---|---|---|
| A - linear counts | BEV_t = a + b·t (OLS) | 132,434 |
| B - exponential/CAGR | ln BEV_t = a + b·t (implied CAGR ≈ 111%/yr) | 922,687, clipped at 100% of the market; **rejected** as implausible |
| C - logistic share | s_t = K / (1 + e^{−(a + b·t)}), estimated as logit(s_t/K) = a + b·t; K assumed | K=30%: 251,127; K=50%: 378,521; K=80%: 528,084 |
| D - linear share × market | s_t = a + b·t; BEV_t = s_t × Market_t | 137,692 (share 14.9%) |

Here s_t is the BEV share of car registrations. The share-based models (C and D) are preferred because they scale with the size of the total market.

**Start-year sensitivity** (2030 BEV registrations, base market):

| Model | Fit from 2021 | 2022 | 2023 |
|---|---|---|---|
| A | 117,203 | 132,434 | 147,323 |
| D | 122,483 | 137,692 | 152,500 |
| C K30 | 269,055 | 251,127 | 230,174 |
| C K50 | 435,332 | 378,521 | 318,466 |

**Backtests** (`trend_backtests.csv`). These are rolling-origin holdouts: fit to 2022-2024 and predict 2025 and 2026E; fit to 2022-2025 and predict 2026E. Share models are given the *actual* market so that only the share error is tested. Results for the 2022-start window, over 3 holdout points:

| Model | Mean absolute % error | Mean bias |
|---|---|---|
| D | 32% | −32% |
| A | 33% | −33% |
| C K30 | 35% | +35% |
| C K50 | 48% | +48% |
| B | 87% | +87% |

**With 3-5 fitting points and 1-3 holdout points, the sample is too short for reliable validation.** These numbers are diagnostics, not accuracy metrics. They show that linear models under-predicted during the acceleration phase and logistic models over-predicted.

**Selected trend case** (all on the base market):
- **low = A**
- **base = D**, which needs the fewest assumptions, requires no saturation level K, and does not extrapolate hypergrowth
- **high = C with K = 30%**, the best-performing bounded model in the backtests

The uncertainty is therefore **skewed upward**: linear models have historically under-forecast. K is not identifiable from the data. K = 50% is broadly consistent with NETR's 80% xEV share by 2050 times a 55-60% BEV share of xEV, and the K = 50% result is reported but not used as a case.

### 4.4 Why registrations are used as the sales proxy
- MITI itself reports both measures for 2025: 8.5% xEV share of sales and 8.7% of registrations. The JPJ proxy reproduces the registration figure (8.73%).
- The goal is vehicles on the road, which JPJ registrations measure. MAA sales miss non-member brands: JPJ BEVs were 1.45× MAA BEVs in 2025.
- For the policy scenarios, the target share is applied to the **JPJ registration denominator** (assumption A04). `denominator_basis_crosscheck_2030.csv` shows the alternative: applying the targets to MAA TIV with MAA's roughly 50:50 BEV:HEV split gives 83k (20%) and 125k (30%) BEV *sales* in 2030. Translating those to registrations with the 2025 JPJ/MAA ratio gives 121k and 181k, against 104k and 156k on the JPJ basis. **The choice of denominator matters by ±15-20%.**

---

## 5. Step 3 - total new passenger-car market (JPJ registration basis)

**History.**
- JPJ car registrations were flat in 2010-2019 (608,644 to 612,973).
- They fell during COVID (2020-21), then reached 744,762 / 832,347 / 856,292 / 870,327 in 2022-2025.
- Jan-Oct 2026 is +3.1% year on year, consistent with MAA's Jan-Oct TIV +3% (S11).

**JPJ vs MAA** (`jpj_registrations_vs_maa_tiv.csv`). JPJ `car` registrations are 0.5-6% above MAA TIV (PV+CV) and 11-17% above MAA passenger vehicles. The gap exists because the JPJ "car" type includes pick-ups and window vans, non-MAA brands and imports. MAA TIV is a sales measure that includes commercial vehicles.

**MAA forecast.** MAA projects 2026 TIV of 800,000 (PV 744,000; CV 56,000; xEV 120,000), revised in July from 790,000 (S10).

**Assumptions** (A08), anchored on the 2026 estimate of 886,684:

| Case | Growth 2027-30 | 2030 total car registrations |
|---|---|---|
| Low | −1.5%/yr | 834,668 |
| Base | +1.0%/yr | 922,687 |
| High | +2.5%/yr | 978,733 |

Rationale: 2010-19 was flat, 2023-25 grew about 2.3%/yr, and MAA expects 2026 to come in below the 2025 record. In the policy cases, market growth moves 2030 stock by −23k/+14k (20% case) and −32k/+20k (30% case) (`stock_sensitivity_2030.csv`).

---

## 6. Step 4 - policy scenarios

**Core relationship** (national, JPJ registration basis):

  New BEV_y = Total cars_y × xEV share_y × BEV share within xEV_y

- **xEV share path.** The path is a linear interpolation from the 2026 estimated observed share (14.42%) to the 2030 endpoint:
  - **20%** (primary): 15.8%, 17.2%, 18.6%, 20.0% in 2027-2030
  - **30%** (sensitivity): 18.3%, 22.2%, 26.1%, 30.0%
- **BEV share within xEV.** This is anchored on JPJ history: 37.5% in 2023, 47.0% in 2024, 59.0% in 2025 and 56.2% in Jan-Oct 2026.
  - *low*: falls linearly to 45% in 2030 (PHEV/HEV growth; MAA's 2026 forecast is roughly 50:50)
  - *base*: held at 56.2%
  - *high*: rises linearly to 70% (continuation of the 2023-25 trend)
- **The BEV share within xEV is NOT the policy target**, and the target is not a BEV share. In the base case, a 20% xEV share implies an 11.2% BEV share of new cars in 2030; 30% implies 16.9%.
- **Identical assumptions.** The 20% and 30% cases use the same market and BEV-within-xEV assumptions, so their difference isolates the xEV target. The full grid of 2 targets × 3 markets × 3 BEV-share cases is in `policy_scenario_grid_full.csv`.
- **Envelope.** *low* combines the low market and low BEV share; *high* combines the high market and high BEV share.

| 2030 new BEV registrations | Low | Base | High |
|---|---|---|---|
| Historical trend | 132,434 | 137,692 | 251,127 |
| 20% xEV policy (primary) | 75,120 | **103,800** | 137,023 |
| 30% xEV policy (sensitivity) | 112,680 | **155,700** | 205,534 |

**Key finding.** The observed xEV share in 2026 (14.4%) is already at 72% of the 20% target level. Reaching exactly 20% in 2030 means xEV share grows only about 1.4 pp/yr after 2026, against about 5.7 pp in 2025-26. Annual BEV registrations would grow about 10%/yr, against +60% in 2026. **The 20% case is therefore a slow-adoption case compared with the historical trend.** The 30% case is close to the linear-share trend.

---

## 7. Step 5 - cohort/survival stock model

  Stock_y = Σ_{c ≤ y} R_c · S(y − c + 0.5)
  S(a) = exp(−(a/λ)^k),  λ = median / (ln 2)^{1/k}
  Retirements_y = Stock_{y−1} + R_y − Stock_y

- R_c are BEV registrations of cohort c. Every cohort from 2009 is included, with 2009-2019 totalling 251 vehicles.
- Registrations are assumed to happen mid-year. 2026 uses Jan-Oct observed plus the Nov-Dec estimate.
- **Official active-fleet and deregistration data.** No official count of active BEVs and no deregistration or scrappage series could be found. The MOT reports 40.77M registered vehicles, of which 26.6M (65.3%) are "active", including about 16M cars, at 30 Sep 2026 (S12). "Active" is undefined and there is no EV breakdown. Malaysia has no comprehensive deregistration requirement ("a register for birth, but none for death").
- **Survival assumptions (A11)**, Weibull:
  - low: median 14 yr, k = 2.0
  - base: median 18 yr, k = 2.5
  - high: median 22 yr, k = 3.0
- **Plausibility check** (`survival_plausibility_check.csv`). Applying these curves to *all* car registrations from 2000 to Sep 2026 (16.03M) gives 9.6M / 11.5M / 13.1M surviving cars, against roughly 16M "active" cars reported. Cohorts from before 2000 would add more. So either car survival in Malaysia is very high, or "active" counts dormant vehicles; either way, survival is unlikely to be lower than the "low" case. The check cannot calibrate BEV-specific survival.
- **Effect on 2030 stock:** −15k/+5k. Survival is the *smallest* of the three policy-case sensitivities, because most BEVs are less than 5 years old in 2030.
- **Cases.** Survival case follows the scenario case (low with low, and so on).

| End-of-year national active BEV stock | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 (low - high) |
|---|---|---|---|---|---|---|
| Historical trend (base) | 83,427 | 155,064 | 237,251 | 336,845 | 453,904 | **588,420** (561,286 - 940,183) |
| 20% xEV (base) | 83,427 | 155,064 | 234,130 | 320,551 | 414,208 | **514,932** (433,464 - 595,555) |
| 30% xEV (base) | 83,427 | 155,064 | 246,722 | 358,565 | 490,680 | **643,076** (533,609 - 754,622) |

The 2025 range across survival cases is 82,875-83,563, against 83,611 cumulative registrations.

---

## 8. Step 6 - Peninsular Malaysia

**Evidence.** The JPJ transaction field `state` is the state of the JPJ office where the car was registered, or "Rakan Niaga" (the official JPJ partner portal, typically used by dealers). It does **not** show the owner's residence or where the vehicle is driven, and it is unrelated to the number plate (S02).
- Rakan Niaga covers 86% of all 2025 car registrations and **78% (2025) to 84% (2026) of BEVs**.
- Among BEVs with a known state, the Peninsular share was 94.3% (2022), 93.9%, 92.7%, 93.0% and 92.7% (2026). State-identified BEVs per year: 1.6k in 2022, rising to 9-10k in 2025-26.
- **Maker reweighting.** Rakan Niaga rows are imputed using each maker's known-state Peninsular share. This gives a combined **91.6-92.2% for 2024-2026** (`peninsular_share_evidence_by_year.csv`).

**Limitation.** The process that decides whether a car is registered through Rakan Niaga or a JPJ office is unknown.
- For *all cars*, the known-state share (79-83%) and the maker-reweighted share (86-88%) differ by about 5-8 pp. Registrations at JPJ offices are therefore not representative within makers, and the size of the bias is uncertain.
- For BEVs the two estimators agree within about 1.3 pp.

**Assumption (A12-A13).**
- Historical cohorts use the year-specific maker-reweighted share. Early cohorts with fewer than 30 known-state BEVs default to 92%.
- Forecast cohorts use low 88%, base 92%, high 95%. The low/high values are applied to all cohorts as an envelope.
- In each case, Peninsular stock = Σ_c R_c · p_c · S(y − c + 0.5).

| End-of-year Peninsular active BEV stock (ESTIMATED) | 2025 | 2030 low | 2030 base | 2030 high |
|---|---|---|---|---|
| Historical trend | 76,947 | 493,931 | 541,348 | 893,174 |
| 20% xEV (primary) | 76,947 | 381,448 | **473,740** | 565,778 |
| 30% xEV (sensitivity) | 76,947 | 469,576 | **591,632** | 716,891 |

*Directly observed* values are limited to registration counts, which `peninsular_bev_stock_2025_2030.csv` shows separately. To Oct 2026, 141,741 BEVs were registered nationally, of which 30,266 were registered at Peninsular JPJ offices. That second figure is a lower bound, since it excludes Rakan Niaga.

---

## 9. Step 7 - validation (`validation_results.csv`; all 24 checks PASS)

The checks cover:
- annual totals matching monthly totals and raw rows
- no double counting (`all_fuels` and `all_types` checks)
- handling of the 2026 partial year (labelled YTD; like-for-like YoY; estimate ≥ YTD)
- BEV ≤ xEV ≤ total cars, and BEV share ≤ xEV share, in history and forecasts
- trend forecasts bounded by the market (12 raw model-B predictions clipped)
- non-negativity
- the retirement identity, with retirements ≥ 0
- stock < cumulative registrations
- 30% ≥ 20% for all 45 identical-assumption combinations, and for stock
- Peninsular ≤ national
- the 2025 anchor of 44,813
- aggregate vs transaction BEV counts agreeing within 1
- the xEV share matching MITI's 8.7% within 0.5 pp
- every assumption having a source ID

---

## 10. Uncertainties and limitations (ranked by effect on 2030 stock)

1. **Scenario choice.** 2030 national stock ranges from 515k (20%) to 643k (30%) to 588k (trend) in the base cases. The full envelope is 433k-940k.
2. **BEV share within xEV.** Effect: −48k/+58k (20% case), −67k/+82k (30% case). This share depends on PHEV uptake (e.g. e.MAS 7 PHEV), the HEV/PHEV split (not observable in JPJ data) and BEV pricing after the CBU incentive expiry.
3. **Policy denominator** (JPJ registrations vs MAA sales; passenger vs all vehicles). Effect: about ±15-20% on 2030 BEV flows (§4.4).
4. **Market growth.** Effect: −23k to −32k / +14k to +20k on 2030 stock.
5. **Peninsular share** (88-95%). Effect: about ±4% on Peninsular stock, with possible unquantified selection bias in the registration-state proxy.
6. **Survival.** Effect: −15k/+5k. There are no BEV-specific Malaysian data.
7. **2026 Nov-Dec estimate** (2 of 12 months). The Dec-2025 rush shows December can swing by ±3k BEVs.
8. **Short series.** There are 5 informative annual points, so the trend models cannot be validated.
9. **Hybrid coding.** JPJ hybrid is 19% below MAA HEV in 2025 (unresolved), which may understate the xEV-proxy denominator.
10. **Scope.** JPJ `car` includes pick-ups (≤0.4% of BEVs) and window vans (mostly premium electric MPVs, which are passenger vehicles). Used and imported BEVs are included as first registrations. Vehicles registered in Peninsular Malaysia but driven elsewhere, and the reverse, cannot be identified.

No statistical confidence intervals are reported. The low/base/high values are **scenario envelopes**.

---

## 11. Addendum - Phase 1.5 (Run 2, 23 Nov 2026): fleet exposure

Sections 1-10 above describe Run 1 and are unchanged. The Run 1 version of this file is archived in `outputs/archive/run1_2026-11-22/reports/`. Run 2 extends the method as follows. Full details are in `fleet_exposure_methodology.md` and `phase_1_5_summary.md`.

- **New metric (C01).**
  - Adds beginning-of-year stock, **annual average active stock** (the time integral of N(t) divided by one year), vehicle-years and retirements for 2025-2030, nationally and for Peninsular Malaysia.
  - It uses daily cohorts and the §7 Weibull curves, and reuses the Run 1 registration paths exactly.
  - **Use the annual average, not the 31-Dec stock, for annual energy.**
  - 2030 Peninsular, 20% base: 425,537 average vs 473,886 at 31 December.
- **Timing (C02).**
  - Observed months use actual daily registration dates.
  - Forecast months use 2022-2025 total-car seasonality.
  - Compared with the §7 mid-year convention, 31-Dec stock changes by +0.01% to +0.09%. The Run 1 exports are kept.
- **Sensitivity (C03).**
  - One-at-a-time analysis of the 2030 Peninsular average across the xEV target, BEV share within xEV, market growth, survival, Peninsular share, policy denominator and timing.
  - Results are in `fleet_exposure_sensitivity_2030.csv` and fig12.
- **Clarification of §10 item 3 (C04).** Under the §6 reconciliation (`denominator_basis_crosscheck_2030.csv`), an MAA-TIV denominator gives **+16.5%** higher 2030 JPJ-equivalent BEV registrations, a one-sided effect. The unconverted MAA-basis count (−20%) is a sales figure, not a registration estimate.
- **Validation.** Run 2 adds 33 checks covering the brief's 12 exposure tests. Results are in `fleet_exposure_validation.md`.

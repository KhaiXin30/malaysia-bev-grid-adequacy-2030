# Annual driving distance of passenger cars in Malaysia: literature review for BEV energy (Phase 2)

*Retrieved 23 Nov 2026. Source IDs (E..) match `outputs/tables/bev_energy_assumptions_and_sources.csv`. Local copies of the readable documents are in `data/raw/literature/`. No source reports Malaysian BEV-specific mileage.*

## 1. Evidence found

| ID | Source | Data | Car result | Verification status |
|---|---|---|---|---|
| **E01 (Source A)** | Sarani, Sharifah Allyana, Nur Aziemah, Rizati (MIROS), *Estimating the Vehicle Kilometres Travelled for Motorcycles and Cars*, abstract ID 99, p.125, IConCEES 2025 Book of Abstracts (UTHM, 29-30 Sep 2025) | Vehicle inspection records collected in 2022, by vehicle type, age and fuel type | **49.23 km/day = 17,969.23 km/yr** (motorcycles 38.54 km/day). Kruskal-Wallis: "no significant difference in VKT values by fuel types and age of vehicles in the dataset" | **Verified verbatim** from the PDF (page 125). Abstract only: sample size, inspection type and selection were not reported, and no full paper was found. |
| **E02** | Nurulhuda et al. (MIROS), *Vehicle Kilometer Travelled by Online Survey*, IJARBSS 10(10), 2020, DOI 10.6007/IJARBSS/v10-i10/8274 | Opt-in Google Form + WhatsApp follow-up; two odometer readings about 3 months apart | **22,715 km/yr** for motorcars (RSE 8.7%) | **Verified** from the full text. 226 respondents, of whom **63** completed both readings. 68.3% were from the Central region and 87% were male. The authors state that the sample "does not represent the population". |
| **E03 (Source B)** | MIROS, *Car Annual Vehicle Kilometer Travelled Estimated from Car Manufacturer Data - An Improved Method* (UKM repository; ResearchGate) | Odometer data from three car manufacturers, scaled by registered cars | **24,129 km/yr (2013)**; Selangor 28,575, Johor 16,342 | **Partly verified.** The UKM server refused connections and ResearchGate returned HTTP 403. The figures come from search-engine extracts of the abstract. Not read in full. |
| **E04** | GIZ ASEAN-German Technical Cooperation, *Malaysia Stocktaking Report on Sustainable Transport and Climate Change* (hosted by MOT; PDF dated Nov 2016) | Reviews PUSPAKOM/MIROS data; own field work in Jan 2016 (driver surveys, vehicle age, odometer checks) | "Passenger cars are driven about **24,000** kilometres per year during their **first year of ownership**" (MIROS 2013). Field work: "typical annual passenger car mileage of around **15k km/year**" | **Verified** from the full text. The report finds that the 24k figure implies fleet petrol use **64% above** Energy Commission statistics, and that 15k km reproduces them closely. |
| **E05** | Zhao, Ottinger, Yip & Helveston, *Quantifying electric vehicle mileage in the United States*, Joule 7:2537-2551 (15 Nov 2023), doi:10.1016/j.joule.2023.09.015 | Odometer readings from 12.5 million used car and 11.4 million used SUV listings (66,641 US dealerships), 2016-2022, vehicles aged 2-9 years. BEV sample: 175,773 cars, 12,623 SUVs. | Annual miles, cars: **BEV 7,165 vs CV 11,642** (about 39% less); **Tesla 8,786** (about 25% less), non-Tesla 6,235. SUVs: BEV 10,184 vs CV 12,979. Range effect is non-linear: +631 mi/yr per extra 10 mi of range below 100 mi, but only +85 above 200 mi. | **Full text verified** (PDF supplied 23 Nov 2026; local copy). The authors call equal BEV/CV mileage "an optimistic assumption" in the short term. |
| E06 | MIT CEEPR WP 2023-01, *How Much Are Electric Vehicles Driven? Depends on the EV* | US | Gap vs ICE disappears for long-range EVs | Search extract only. Qualitative. |

## 2. Why Sources A and B differ (17,969 vs 24,129 km/yr)

1. **Different vehicles are observed.**
   - Manufacturer odometer data (B) come from cars that return to franchised service centres, which are mostly young cars under warranty.
   - GIZ (E04) explains that the PUSPAKOM/MIROS 24k figure reflects "newer and public vehicles", which "are generally driven more than older vehicles". It also notes that 10+-year-old vehicles (about 50% of the fleet) "are generally driven much less".
   - Inspection records (A) cover a different, older population, but the abstract does not say which inspections.
2. **Different years.** B uses 2013 and A uses 2022. Commuting patterns after the 2020-2021 movement-control period, fuel prices and the growth of public transport may all differ. This is not quantified.
3. **Different estimators.** B scales manufacturer totals by registered cars. A computes daily VKT from inspection odometer records. Neither has published sampling weights.
4. **Regional mix.** B reports a range from 16,342 (Johor) to 28,575 (Selangor) km. Any sample concentrated in the Klang Valley, as the E02 survey was, will read high.
5. **Consistency with fuel statistics.** GIZ found the ~24k figure inconsistent with national petrol sales, while ~15k matched. This top-down check favours the lower figures for the *whole* fleet.

## 3. Suitability for BEVs in 2030
- **Arguments for higher BEV mileage:**
  - The BEV fleet will be young in 2030: about two-thirds of the 2030 active fleet will come from 2027-2030 registrations, and 83% from 2026-2030 (Phase 1.5 cohorts, 20% base). Young cars are driven more (E04).
  - Low running costs reward driving.
  - Some BEVs are used for e-hailing. The share is not measured; this is a review item.
- **Arguments for lower mileage:**
  - BEV buyers are concentrated in urban, higher-income, often multi-car households.
  - **US odometer evidence (E05, verified):** BEV cars were driven 39% less than conventional cars in 2016-2022, and Teslas 25% less.
  - **Explanations the authors consider:** range anxiety, low-mileage buyers selecting BEVs, and multi-car early-adopter households. They find weak evidence that 2019+ models are driven more.
  - **Their limitations:** used-listing data only, no owner demographics, few recent model years.
  - **Relevance to Malaysia:** the Malaysian BEV fleet is mostly modern long-range models (e.g. e.MAS 7 410 km WLTP, about 255 mi). Range effects flatten above about 200 mi, so the long-range (Tesla) ratio of 0.755 is more relevant here than the all-BEV ratio of 0.615, which is dominated by early short-range US BEVs. The transfer is still uncertain: household vehicle ownership, trip lengths and charging access differ.
- **No direct evidence either way:**
  - A says there is no significant difference by fuel type or age. However, the 2022 inspection data would contain very few BEVs (about 3,100 were registered in 2022; Run 1 data), so this is **not evidence about BEVs**.
  - No Malaysian BEV mileage study, owner survey or telematics dataset was found.

## 4. Selected assumptions (`config.ANNUAL_KM`)

| Case | km/yr | Basis | Status |
|---|---|---|---|
| Low | **13,561** | Base × 0.755, the verified US long-range (Tesla) BEV/CV car ratio (E05) | Derived (Malaysian all-car mileage × US BEV ratio) |
| **Base** | **17,969** | MIROS 2022 inspection records (E01): the most recent Malaysian estimate | Observed Malaysian, all cars, **not BEV-specific**. **Implies BEV/ICE parity**, which E05 calls optimistic (US). |
| High | **22,715** | MIROS 2020 online survey (E02), with new-car first-year mileage of about 24,000 km (E03/E04) showing the young-fleet upper side | Observed Malaysian but non-representative |

**Additional sensitivities** (`bev_energy_sensitivity_2030.csv`):
- US all-BEV ratio, 17,969 × 0.615 = **11,059 km**: −38.5% on 2030 energy.
- GIZ 2016 fleet-typical **15,000 km**: −16.5%.

**Revision note (23 Nov 2026).** The first Phase 2 run used 15,000 km (GIZ) as the low case, while E05 was available only as a search extract. After the full paper was supplied and verified, the low case became 13,561 km. Base and high are unchanged.

**Limits of the evidence.** The base value is an observed Malaysian *all-car* average. Applying it to BEVs, i.e. assuming parity, is an **assumption**, and so is holding it constant over 2025-2030.

**Evidence that would remove the assumption:**
- Odometer readings from Malaysian BEV service records (Proton/BYD/Tesla)
- MIROS/PUSPAKOM BEV-specific VKT
- TNB or charge-point-operator energy per vehicle
- e-hailing operator data

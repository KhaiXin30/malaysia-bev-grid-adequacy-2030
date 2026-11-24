# BEV electricity consumption (kWh/100 km) for Malaysia: literature review (Phase 2)

*Retrieved 23 Nov 2026. Source IDs match `bev_energy_assumptions_and_sources.csv`. Model-level tables are in `outputs/tables/bev_model_consumption_mapping.csv` and `bev_consumption_observations.csv`. Figure: `fig15_consumption_model_weighted_vs_generic.png`.*

## 1. Measurement boundaries

| Boundary | Meaning | Examples in this review |
|---|---|---|
| **Battery side** | Energy taken from the traction battery for driving and on-board systems (incl. A/C) | EV Database "Vehicle" consumption, defined verbatim as "calculated battery energy consumption used by the vehicle for propulsion and on-board systems" (E08); in-car trip-computer readings |
| **Plug / grid side** | Energy drawn from the socket or charger, **including charging losses** | WLTP rated values: EV Database states "Rated consumption ... include charging losses" (E08). EPA label values: "MPGe values provided by EPA include charging losses" (E19). |
| Unclear | Method not stated, or derived from % battery × capacity | Several journalist tests (marked below) |

**No value in this project is computed as battery capacity ÷ advertised range.** Quoted ranges were not converted to consumption: CLTC and NEDC ranges in particular overstate real range, and capacity ÷ range mixes up the measurement boundaries.

## 2. Fleet: which BEVs Malaysians actually register (JPJ transactions, E23)
- **2022 to Oct 2026:** 141,159 BEVs in total. The top models are:

  | Model | Share |
  |---|---|
  | Proton e.MAS 5 | 16.2% |
  | Proton e.MAS 7 | 9.7% |
  | BYD Atto 3 | 9.7% |
  | Tesla Model 3 | 6.9% |
  | Tesla Model Y | 6.6% |
  | BYD Sealion | 4.8% |
  | Zeekr 7X | 3.2% |
  | BYD Seal | 3.0% |

- **The mix shifted sharply in 2026.** The e.MAS 5 (launched Oct 2025; a rebadged Geely Geome Xingyuan with 30.12/40.16 kWh LFP batteries, 250/325 km WLTP, E16) took 22,589 of 58,129 BEVs in Jan-Oct 2026 (39%).
- **Mapping to consumption values** (36 JPJ models; table in `bev_model_consumption_mapping.csv`), by share of 2022-Oct 2026 registrations:

  | Mapping type | Share |
  |---|---|
  | Direct EV Database match | 52.3% |
  | Twin model (e.MAS 7 ↔ Geely Galaxy E5, co-developed, E16) | 9.7% |
  | Segment proxy (**assumption**, e.g. e.MAS 5 ↔ EVDB "Geely E2"; BYD M6, Denza D9, Zeekr 009 ↔ XPENG X9 MPV; Chery iCaur ↔ Omoda E5) | 28.7% |
  | Residual (fleet-weighted mean) | 9.2% |

## 3. Model-level values (EV Database, battery side, real-world estimate; E07)
EV Database real-world values assume a moderate European climate: they average "mild" (23 °C, no A/C) and "cold" (−10 °C, heating) conditions, with highway figures at a constant 110 km/h (E08).

| JPJ model | EV Database reference | kWh/100 km (battery) |
|---|---|---|
| e.MAS 5 | Geely E2 (proxy) | 16.6 |
| e.MAS 7 | Geely E5 (twin) | 18.6 |
| BYD Atto 3 | ATTO 3 MY23-24 | 18.3 |
| Tesla Model 3 | variants averaged | 13.8 |
| Tesla Model Y | variants averaged | 16.4 |
| BYD Sealion | SEALION 7 | 20.3 |
| Zeekr 7X | 7X | 19.3 |
| BYD Seal | SEAL | 17.5 |

**BYD ATTO 3 example of the boundaries** (E08):
- Real-world: 18.3 battery-side.
- WLTP: 15.6 plug-side, 14.4 battery-side.
- EV Database's own split: 12.3 in city and mild conditions, 20.2 on the highway in mild conditions.

## 4. Malaysian and tropical road-test evidence (observations O1-O7)

| ID | Model | Observed kWh/100 km | Boundary | Conditions | Ratio to EVDB |
|---|---|---|---|---|---|
| O1 | e.MAS 7 Premium (PCauto, Jun 2025) | 11.2 | battery (display) | 152 km, ~30% congestion | 0.60 |
| O2 | e.MAS 7 Premium (CarsOfMalaysia, Feb 2025) | 11.3 | unclear | eco-driving "efficiency challenge" (excluded) | (0.61) |
| O3 | e.MAS 7 (AutoApp.sg, Sep 2025) | 13.5-15.2 | unclear | Singapore, tropical; method not stated | 0.77 |
| O4 | e.MAS 5 Premium (Zigwheels via Carz/Newswav, Sep 2026) | 10.0 | battery (trip computer) | Klang Valley and towards Genting | 0.60 |
| O5 | smart #1 Premium (paultan, Jan 2024) | 13.2 | unclear | ~500 km mixed | 0.71 |
| O6 | BYD Dolphin Extended Range (paultan, Sep 2023) | 13.8 | battery (graph) | one leg | 0.80 |
| O7 | BYD Dolphin Standard (paultan, Sep 2023) | ≈16.1 | derived (% SoC; computed here) | 66.8 km, "pedal pushing" (excluded) | (0.93) |

- **Rated (plug-side) values for comparison:**
  - e.MAS 7: 16.6 (Singapore spec sheets, E11/E12)
  - Tesla Model 3 RWD WLTP: 13.0
  - Tesla Model Y Premium RWD WLTP: 13.9 (E15, secondary)
- **What the readings show.** Malaysian trip-computer readings (10-15 kWh/100 km) are 20-40% below the EV Database real-world values and close to or below WLTP battery-side values.
- **Plausible reasons:**
  - No heating demand in the tropics.
  - Low-speed urban congestion with regenerative braking.
  - Journalists' short and sometimes efficiency-minded routes.
  - Trip computers that may omit some losses.
- **What pushes the other way:** tropical A/C runs all year, and expressway cruising at 110 km/h raises consumption. One Singapore modelling paper reports that A/C may cut urban range by up to 40%. This is from a search extract, not used numerically.
- **Not representative.** The observations are **few (5 usable), non-random and mostly single trips**.

## 5. Fleet-weighted consumption and selected cases
- **Fleet-weighted EVDB value.** For each year, every cohort's model mix (JPJ actual mix up to Oct 2026; 2027-2030 cohorts use the pooled 2025-Oct 2026 mix) is weighted by surviving vehicles. The 2030 fleet comes to **17.65 kWh/100 km** (EVDB basis, battery side). The fleet value barely changes over 2025-2030 (17.55-17.65).
- **Consumption factors (battery side, `config` / `energy.consumption_factors`):**

  | Case | Factor | 2030 battery-side kWh/100 km | Basis |
  |---|---|---|---|
  | Low | 0.714 | **12.5** | Median of the 5 Malaysian/tropical observation ratios (O1, O3-O6) |
  | **Base** | 0.857 | **15.1** | Midpoint (**assumption**). Roughly EVDB's "combined, mild, no A/C" level (ATTO 3 MY23-24: 15.9 vs 18.3, ratio 0.87). |
  | High | 1.000 | **17.7** | EVDB real-world level |

- **Cross-check.** The base battery-side figure ÷ 0.90 = **16.8 kWh/100 km plug-side**. That is close to the rated plug-side values of the leading models (e.MAS 7 16.6; ATTO 3 15.6-16.4), but above Tesla's WLTP values (13.0-13.9).
- **Vehicle-mix sensitivity:**
  - If 2027-2030 registrations follow the 2026 (e.MAS 5-heavy) mix: −1.1% energy.
  - If they follow the 2025 mix: +1.4%.
  - Model mix is therefore a minor driver compared with the uncertainty in the consumption level.

## 6. Model-weighted vs generic consumption
- **The difference.** The EV Database unweighted average across all models is 19.1 kWh/100 km (E07). That is **8.2% above** the Malaysian fleet-weighted value (17.65), because Malaysian buyers favour smaller and LFP-battery models such as the e.MAS 5, Atto 3 and Model 3.
- **Effect.** Using the generic average would raise every energy result by 8.2%. In the 20% base case for 2030, Peninsular demand would rise from 1,285 to about 1,390 GWh.
- **Secondary source.** A Malaysian review quotes a "typical" 15-20 kWh/100 km with no stated boundary (search extract only; not used).

## 7. Where evidence ends and assumptions begin
- **Observed:**
  - The JPJ model mix.
  - EV Database model values (a modelled real-world estimate, European climate).
  - 5 Malaysian/tropical trip-computer observations.
- **Assumptions:**
  - The proxy mappings (28.7% of the fleet).
  - The base midpoint factor.
  - The 2027-2030 cohort mix.
  - That consumption per model does not change by 2030 (no technology improvement assumed).
- **Highest-value missing data:** Malaysian fleet or telematics consumption by model (e.g. Proton/BYD connected-car data, e-hailing fleets), measured with A/C at Malaysian temperatures.

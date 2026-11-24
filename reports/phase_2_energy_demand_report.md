# Phase 2: annual electricity for passenger BEV charging, Peninsular Malaysia, 2025-2030

*Run 3, 23 Nov 2026; revised the same day after the Zhao et al. (2023) PDF was verified (the low mileage case changed from 15,000 to 13,561 km; base unchanged). This builds on Run 1 (registrations and stock) and Run 2 (fleet exposure), which are unchanged and archived in `outputs/archive/`. Reproduce with `.venv/bin/python src/run_all.py`. Detailed reviews: `bev_mileage_literature_review.md`, `bev_efficiency_literature_review.md`, `bev_charging_efficiency_review.md`. Tests: `bev_energy_validation.md`. Hourly charging profiles, peak load and reserve margins are out of scope (Phase 3).*

## Method

$$E_{grid,y}\,[\text{GWh}] = \frac{VY_y \times \text{km} \times c_y}{100 \times \eta \times 10^6}$$

| Term | Meaning |
|---|---|
| VY_y | Vehicle-years = annual average active BEVs from Phase 1.5 (`leap_bev_exposure_input.csv`). Not 31-Dec stock. |
| km | Annual km per active BEV |
| c_y | Fleet-average **battery-side** kWh/100 km in year y |
| η | Grid-to-battery charging efficiency. Applied once, because c is battery-side. |

- **Boundary.** Grid energy is measured at the charger's grid connection. Transmission and distribution losses are excluded.
- **Same assumptions in every adoption scenario.** km, c and η are identical across the scenarios, so scenario differences reflect fleet size only. c_y is computed from the primary (20%) fleet composition. Using each scenario's own composition would change 2030 consumption by at most 0.04% (`bev_energy_scenario_mix_check.csv`).

## 1. Annual mileage: selected 17,969 km/yr (low 13,561, high 22,715)
- **Base:** MIROS, 2022 vehicle-inspection records, 49.23 km/day (IConCEES 2025 abstract, p.125; verified verbatim).
- **High:** MIROS 2020 online odometer survey, 22,715 km (n = 63; not representative).
- **Upper reference, not used:** the new-car first-year figure of about 24,000 km (MIROS 2013 manufacturer data, 24,129 km). It is only partly verified, because the full text was unreachable.
- **Low: 13,561 km = base × 0.755.**
  - The ratio is the US long-range (Tesla) BEV/CV car mileage ratio from Zhao et al. 2023 (*Joule*), with the full text verified: US BEV cars drove 7,165 vs 11,642 mi/yr (−39%), and Teslas 8,786 (−25%), in 2016-2022 used-car odometer data.
  - Separate sensitivities: the all-BEV ratio (11,059 km) and the GIZ/MOT 2016 fleet-typical 15,000 km. The GIZ report also found that 24k km is inconsistent with national petrol sales.
- **Why A and B differ:** manufacturer and service data cover young cars under warranty, which are driven more; the years and estimators also differ.
- **No Malaysian BEV-specific mileage exists.** The base assumes BEV/ICE parity, which Zhao et al. call "an optimistic assumption" for the US. Malaysia's young, long-range fleet narrows the gap, but this is not measured.

## 2. Consumption: selected 15.1 kWh/100 km battery-side in 2030 (low 12.5, high 17.7)
- **Fleet-weighted value.** JPJ BEV registrations by model (e.MAS 5, e.MAS 7, Atto 3, Model 3, Model Y …) are mapped to EV Database battery-side real-world values and weighted by surviving cohorts. This gives **17.65 kWh/100 km** for the 2030 fleet.
  - 62% of registrations are direct or twin-model matches, 29% use segment proxies, and 9% use the residual mean.
- **Malaysian evidence is lower.** Malaysian and Singapore trip-computer readings for the same models run at **0.60-0.80×** the EV Database values (median 0.714, from 5 observations).
- **Cases:**

  | Case | Factor | 2030 battery-side kWh/100 km |
  |---|---|---|
  | Low | Malaysian median (0.714) | 12.5 |
  | Base | Midpoint (0.857, assumption) | **15.1** |
  | High | EV Database (1.0) | 17.7 |

- **Measurement basis: battery side.** At η = 0.90 the base equals **16.8 kWh/100 km plug-side**, consistent with the rated plug-side values of the leading models (e.MAS 7 16.6; Atto 3 WLTP 15.6-16.4).

## 3. Charging efficiency: selected 0.90 (range 0.85-0.93)
- **Evidence:**
  - ORNL: 84-93%.
  - Argonne: 10% combined charging loss.
  - ADAC 2026: 11 kW wallbox losses 5-7%, 4.1 kW 8-13%, 2.3 kW socket 13-24%, DC 5-15% including battery conditioning.
  - EPA confirms that its label values include charging losses.
- **What η includes:** EVSE, on-board charger or DC station conversion, battery charging, and thermal-management and standby loads.
- **What η excludes:** T&D losses.
- **Unknown:** the Malaysian AC/DC charging mix.

## 4. Annual grid electricity (GWh), base case

| Year | 20% xEV Pen. | 30% xEV Pen. | Trend Pen. | 20% xEV national | 30% xEV national | Trend national |
|---|---|---|---|---|---|---|
| 2025 | 155.5 | 155.5 | 155.5 | 168.0 | 168.0 | 168.0 |
| 2026 | 323.8 | 323.8 | 323.8 | 351.6 | 351.6 | 351.6 |
| 2027 | 534.1 | 550.7 | 538.2 | 580.5 | 598.6 | 585.0 |
| 2028 | 763.9 | 832.5 | 790.0 | 830.3 | 904.8 | 858.7 |
| 2029 | 1,014.6 | 1,171.2 | 1,090.9 | 1,102.8 | 1,273.0 | 1,185.7 |
| **2030** | **1,285.0** | **1,566.1** | **1,440.1** | 1,396.7 | 1,702.2 | 1,565.4 |

- This is about 3,020 kWh of grid electricity per active BEV per year in the base case.
- **2030 charging losses** included in the 20% Peninsular base: about 128 GWh.

## 5. Ranges and dominant uncertainties (2030, Peninsular)

**Combined envelopes** (all-low and all-high assumptions together). These are scenario ranges, **not confidence intervals**:

| Scenario | Low | Base | High |
|---|---|---|---|
| 20% xEV | 637.8 | 1,285.0 | 2,386.6 |
| 30% xEV | 767.3 | 1,566.1 | 2,947.6 |
| Historical trend | 795.1 | 1,440.1 | 3,683.8 |

**One-at-a-time changes around the 20% base** (fig14):

| Rank | Factor | Effect |
|---|---|---|
| 1 | Annual km (13,561 / 22,715) | **−24.5% / +26.4%** |
| 2 | 30% xEV fleet | +21.9% |
| 3 | Fleet size, Phase 1.5 low/high | −17.5% / +17.2% |
| 4 | Consumption level | ±16.7% |
| 5 | Historical-trend fleet | +12.1% |
| 6 | Charging efficiency | −3.2% / +5.9% |
| 7 | Vehicle mix of 2027-30 registrations | −1.1% / +1.4% |

**Extra mileage sensitivities:**
- US all-BEV mileage ratio (11,059 km): **−38.5%** (790.8 GWh). This is the largest single downside.
- GIZ fleet-typical 15,000 km: −16.5%.

**Variables that most need stronger Malaysian evidence**, in order:
1. BEV annual km. Base and high are all-car values. The only BEV-specific evidence is from the US (verified) and implies 25-39% less driving. There are no Malaysian BEV or e-hailing data.
2. Real-world consumption with A/C. Only 5 journalist readings; 29% of the fleet uses proxy models.
3. The AC/DC charging mix and losses in a hot climate.

## 6. Model-weighted vs generic consumption
- The EV Database all-model average (19.1 kWh/100 km) is **8.2% higher** than the Malaysian fleet-weighted value (17.65). Malaysia's fleet is dominated by smaller, efficient models, chiefly the e.MAS 5, Atto 3 and Tesla Model 3/Y.
- A generic value would therefore raise 2030 demand to about 1,390 GWh (20% base, Peninsular).
- Changing the mix of future registrations between the observed 2025 and 2026 mixes moves energy by only about ±1%.

## 7. Recommended LEAP input
**2030 Peninsular Malaysia: 1,285 GWh per year of grid-side BEV charging electricity** (20% xEV base case, excluding T&D losses). Use the full 2025-2030 series in `outputs/tables/leap_bev_annual_energy_input.csv` (`scenario = 20pct_xev`, `case = base`, `geography = peninsular`).
- Carry **1,566 GWh (30% xEV)** as the higher-adoption sensitivity.
- Report the 638-2,387 GWh envelope as the assumption range.
- In LEAP, add network losses only if the GSO baseline is defined at generation or sent-out level.

## 8. Limitations and items for your review

**Where observed Malaysian evidence ends and assumptions begin:**
- **Observed:** the JPJ BEV registrations and model mix; all-car Malaysian VKT studies; a handful of Malaysian road tests.
- **Taken from foreign sources:** EV Database values (European climate model) and charging-loss measurements (US/German).
- **Assumptions:** BEV km = all-car km (parity) in the base; the US BEV/CV ratio transferred to Malaysia in the low case; the base consumption midpoint; the proxy model mappings; η and the charging mix; future cohort mix; no technology improvement to 2030.

**Review items:**
1. **Mileage basis (largest driver).** Decide whether the base should keep BEV/ICE parity (17,969 km) or apply a BEV discount. Applying the verified US long-range ratio (0.755) to the base would cut 2030 energy by 24.5%, to about 970 GWh. Consider requesting the full MIROS paper and any BEV breakdown, and e-hailing BEV shares.
2. **Consumption base factor (0.857 = midpoint).** This is the main judgment in Phase 2; ±16.7% hangs on it. Malaysian fleet or telematics data would replace it.
3. **Proxy mappings** for e.MAS 5 (EVDB "Geely E2"), BYD M6, Denza D9, Zeekr 009 (XPENG X9) and Chery iCaur (Omoda E5).
4. **Charging efficiency 0.90 and the AC/DC mix.** Consider asking TNB or charge-point operators for session data.
5. **System boundary.** Grid energy is at the charger input with T&D excluded. Align this with how the GSO 2025 profile is metered (generation vs demand side).
6. **Constant per-model consumption and mileage to 2030.** No efficiency gains or rebound are assumed.
7. **Source verification gaps:**
   - MIROS 2013 manufacturer-data paper: full text was inaccessible. The US Joule 2023 paper is now verified from the PDF you supplied.
   - Newswav/Carz figures are secondary.
   - The carsofmalaysia long-drive review returned HTTP 429.
8. **Peninsular figures** inherit the registration-state proxy from Phase 1.5.

## 9. Reproducibility and validation
- **Pipeline:** `src/run_all.py` runs Run 1, Phase 1.5 and Phase 2.
- **Phase 2 code:** `src/energy.py`, `src/phase2.py`, `src/validation_energy.py`, `src/figures_energy.py`.
- **Parameters:** `src/config.py` (Phase 2 section).
- **Tests:** results are in `bev_energy_validation.md`. They cover units and the kWh→GWh conversion, the vehicle-years source, documented and plausible inputs, the energy boundary (losses applied once), non-negativity, monotonicity, identical assumptions across scenarios, 30% ≥ 20%, Peninsular ≤ national, and byte-identical reproduction of the archived Run 1 and Run 2 tables.

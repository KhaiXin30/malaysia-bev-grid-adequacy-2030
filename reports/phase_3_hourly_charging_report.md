# Phase 3: hourly BEV charging demand and ToU load shifting, Peninsular Malaysia 2030

*Run 4, 23 Nov 2026.*
- **Builds on:** Runs 1-3, archived under `outputs/archive/` and reproduced byte-identically (validation requirement 18).
- **Reproduce:** `.venv/bin/python src/run_all.py`.
- **Code:** `src/hourly.py`, `src/phase3.py`, `src/validation_hourly.py`, `src/figures_hourly.py`.
- **Tests:** `phase_3_validation.md`.
- **Companion documents:** `charging_profile_literature_review.md`, `residential_workplace_source_comparison.md`, `malaysia_charging_behavior_assumptions.md`, `tnb_tou_management_methodology.md`, `outputs/tables/leap_hourly_import_guide.md`.

**Scope:** BEV charging profiles only. **No system-peak or reserve-margin result is claimed** before the GSO hourly baseline is integrated.

## 1. Preserved inputs and the project owner's decision
- **Annual 2030 Peninsular grid energy** (charger input, including charging losses, excluding T&D), taken unrounded from Phase 2:

  | Scenario | GWh | Annual-average BEVs |
  |---|---|---|
  | 20% xEV | **1,284.977** | 425,537 |
  | 30% xEV | **1,566.066** | 518,623 |
  | Historical trend | **1,440.143** | 476,922 |

- **Mileage:** the working base remains **17,969 km**. Low (13,561) and high (22,715) are unchanged in Phase 2.
- **New mileage sensitivity: 15,000 km (GIZ/MOT)**, with fleet, 15.12 kWh/100 km and 90% efficiency held at base:

  | Scenario | 15,000 km sensitivity |
  |---|---|
  | 20% xEV | 1,072.6 GWh |
  | 30% xEV | 1,307.3 GWh |
  | Historical trend | 1,202.2 GWh |

  This is added under a new identifier (`giz_15000km`). Phase 2 files are unchanged.
- **Energy balance:** each hourly profile reconciles to these totals within 1e-9. Managed and unmanaged profiles have identical annual energy.

## 2. Profile construction (summary)
- **Calendar:** 8,760 hours of 2030 in MYT (UTC+08:00, no daylight saving), hour-beginning.
- **Location mix (base):** residential 60%, workplace 5%, public AC 15%, public DC 20%. This is a **scenario assumption**.
- **How each location is modelled:**
  - Residential and workplace use **session simulations** with connection windows and charger power limits. Timing is from Liu et al. (2024) and the NREL workplace report, adapted.
  - Public AC and DC use EVI-Pro Lite shapes (US simulation, 30 °C).
- **Fleet growth through 2030:** daily energy follows the Phase 1.5 daily active-fleet trajectory.
- **Seasonality:** none. Colorado's heating seasonality is explicitly excluded.
- **Managed charging:** TNB ToU applied to residential sessions only. **Staggered** starts are the working case; **synchronized** 22:00 starts show the rebound risk.

## 3. Results, 2030 (Peninsular Malaysia, base mileage)

| Scenario | Charging case | GWh | Max BEV load (MW) | Max weekday load (MW) | Energy in TNB peak | Shifted out of peak (GWh) | Peak/average | Max ramp (MW/h) |
|---|---|---|---|---|---|---|---|---|
| 20% xEV | Unmanaged | 1,285.0 | **375.5** (Tue 31 Dec 18:00) | 375.5 | 40.8% | — | 2.56 | 68 |
| 20% xEV | **Managed 50% staggered (provisional)** | 1,285.0 | 356.2 (Sun 29 Dec 18:00, weekend) | **240.0** | **26.2%** | **187.2** | 2.43 | 65 |
| 20% xEV | Managed 100% staggered | 1,285.0 | 356.2 (weekend) | 293.5 (overnight) | 11.7% | 374.3 | 2.43 | 113 |
| 20% xEV | Managed 100% synchronized | 1,285.0 | **974.0** (22:00) | 974.0 | 11.7% | 374.3 | 6.64 | 947 |
| 30% xEV | Unmanaged | 1,566.1 | **468.9** | 468.9 | 40.8% | — | 2.62 | 84 |
| 30% xEV | Managed 50% staggered | 1,566.1 | 444.7 (weekend) | **299.7** | 26.2% | 228.1 | 2.49 | 81 |
| 30% xEV | Managed 100% synchronized | 1,566.1 | 1,216.2 (22:00) | 1,216.2 | 11.6% | 456.2 | 6.80 | 1,183 |
| Historical trend | Unmanaged | 1,440.1 | 429.0 | 429.0 | 40.8% | — | 2.61 | 77 |
| Historical trend | Managed 50% staggered | 1,440.1 | 407.0 (weekend) | 274.2 | 26.2% | 209.8 | 2.48 | 74 |

- **Average load:** 146.7 MW (20%), 178.8 MW (30%), 164.4 MW (trend).
- **15,000 km sensitivity:** every load scales by 0.835. For example, 20% unmanaged is 313.4 MW, and 50% managed is 297.4 MW overall and 200.4 MW on weekdays.
- **Weekday vs weekend:**
  - Unmanaged weekday energy averages 3,570 MWh/day against 3,403 MWh/day on weekends and holidays (20%), because there is less workplace charging on weekends.
  - Under ToU, energy from Friday-night sessions shifts into Saturday hours.
- **Location-mix sensitivity** (20%, unmanaged maximum / 50%-managed weekday maximum):

  | Mix | Unmanaged max | 50%-managed weekday max |
  |---|---|---|
  | home_low | 351 MW | 249 MW |
  | home_high | 400 MW | 231 MW |
  | work_high | 339 MW | 298 MW |

  More home charging means a higher unmanaged evening peak but more shiftable energy: in home_high, 100% participation leaves only 7.1% in peak hours.
- **Other sensitivities** (unmanaged maximum, 20%):
  - home arrival +1 h: 360 MW
  - 20 kWh home sessions: 351 MW
  - no fleet growth: 337 MW

## 4. Answers to the brief's questions
1. **Sources obtained and analysed:**
   - Liu et al. 2024 (full preprint)
   - NREL workplace companion report (full)
   - EVI-Pro Lite API profiles (5 requests, 4 valid)
   - INL *Plugged In* (full)
   - TNB and myTNB ToU pages
   - JSDEWES Malaysian review (partially verbatim)
   - Baharin et al. (2024) IJAAS Malaysian ToU home-charging study (full PDF supplied by the project owner)
   - **Not obtainable:** the NREL raw workplace dataset (catalog offline / access denied) and any Malaysian charge-point operator data.
2. **Contribution of the two mandatory references:**
   - **NREL workplace:** measured US workplace arrival, duration and energy distributions. These drive the workplace model, which reproduces NREL's observed hourly profile with r = 0.96.
   - **Liu et al.:** simulated US home plug-in and unplug timing, which drives the residential model. It also explains that real controlled charging starts later, which is consistent with the managed case.
3. **Rejected or modified:**
   - Rejected: Liu's winter heating penalty and seasonal travel factors (tropical Malaysia), NREL COVID-era data, and US workplace-charging energy shares.
   - Modified: charger power (3.3/6.6 kW → 7.4/11 kW), and the EVI-Pro DC shape (smoothed).
   - Unavailable: DC Handal data.
4. **Energy shares:** home 60%, workplace 5%, public AC 15%, public DC 20% (base). Alternatives home 45-75%. **Scenario assumption.**
5. **Adapting US patterns to Malaysia:**
   - Local clock times, no daylight saving.
   - Malaysian charger powers.
   - Much lower workplace share.
   - Higher DC share.
   - No heating seasonality.
   - Weekend/holiday behaviour on the Malaysian calendar.
   - TNB ToU applied to households only.
6. **Peak loads, 2030, base mileage:**

   | Scenario | Unmanaged | Managed 50% staggered, weekday | Managed 50% staggered, overall (weekend evening) |
   |---|---|---|---|
   | 20% xEV | **375 MW** | 240 MW | 356 MW |
   | 30% xEV | **469 MW** | 300 MW | 445 MW |
   | Trend | 429 MW | — | — |

7. **Energy shifted out of TNB peak hours (20%):**
   - 187 GWh at 50% participation (peak share 40.8% → 26.2%).
   - 374 GWh at 100% (→ 11.7%).
   - The rest of the peak-hour energy is public, workplace or unshiftable.
8. **Participation levels:**
   - Peak-hour energy falls linearly.
   - The weekday BEV maximum falls to about 230-240 MW at 50-75%.
   - At 100% a new **off-peak overnight** hump (294 MW) appears.
   - The overall BEV maximum is set by **unmanaged weekend evenings** (356 MW) once p ≥ 25%.
9. **A new 22:00 peak?** **Yes, if starts are synchronized.** 100% synchronized gives 974 MW at 22:00 (2.6× unmanaged), and 50% gives 557 MW. **Staggered** scheduling avoids it (validated: lower maximum and lower ramp than synchronized).
   - The risk is credible in Malaysia: TNB advises charging after 22:00, and the Malaysian study by Baharin et al. (2024) assumes 22:00 starts as the ToU response.
10. **Biggest uncertainties:**
    - the location energy mix and home-charging access (no Malaysian data)
    - actual ToU participation and how starts are scheduled (synchronized vs staggered)
    - Malaysian arrival-time distributions
    - public DC timing
    - how the BEV profile overlaps the non-BEV system load (pending GSO data)
    - the annual-energy uncertainties carried from Phase 2 (mileage, consumption)
11. **Working managed case for LEAP:** `managed_staggered_p50`, an **assumed** 50% participation with staggered starts. Carry 100% staggered as an upper bound, and synchronized 50/100% as rebound stress tests.
12. **Ready once GSO data arrive:**
    - `leap_bev_hourly_load_2030_aggregated.csv` and `leap_bev_hourly_load_2030.csv`: 8,760-hour MYT profiles in MW = MWh per hour.
    - `leap_bev_hourly_shapes_2030.csv`: LEAP % of annual energy.
    - `leap_bev_timeslice_576_2030.csv`.
    - All share the 2030 MYT timestamp key.

## 5. Measured vs simulated vs assumed

| Element | Type |
|---|---|
| TNB ToU windows and holidays | official policy |
| Malaysian home-charging start times (18:00 / 22:00) and ~7 kW chargers in Baharin et al. 2024 | Malaysian researcher **assumptions** (validate only) |
| 2030 fixed-date holidays | calendar |
| Workplace arrival, duration and energy | measured, US (NREL), approximate chart readings |
| Residential plug-in and unplug timing | simulated, US (Liu / EVI-Pro), approximate chart readings |
| Public AC and DC shapes | simulated, US (EVI-Pro Lite) |
| Location mix, charger powers, home session energy, participation, weekend factors, neutral seasonality | **assumptions** |
| Fleet growth through the year | Phase 1.5 model |
| Annual energy | Phase 2 model |

## 6. GSO integration flags
- **Calendar:** 2025 starts on a Wednesday and 2030 on a Tuesday. Lunar holidays move between years. Align by day type.
- **Intervals:** confirm whether GSO hours are hour-beginning or hour-ending, and the averaging interval.
- **Measurement boundary:** BEV load here is at the charger input, excluding T&D. GSO is likely generation/sent-out. Add losses consistently.
- **Double counting:** determine whether the 2030 demand forecast already includes EV charging before adding BEV load.

## 7. Sensitivities carried
- **Mileage:** 15,000 km (all profiles).
- **Location mix:** 3 alternatives.
- **Home arrival:** +1 h.
- **Session energy:** 20 kWh.
- **Fleet growth:** a flat-fleet alternative.
- **Participation:** 0-100%.
- **Strategy:** staggered vs synchronized.
- The Phase 2 low/high energy envelopes are not yet expanded hourly. Scale the shapes by the Phase 2 annual totals if needed (shapes are energy-independent).

## 8. Files
- **Tables:**
  - `charging_profile_sources.csv`
  - `charging_location_mix_assumptions.csv`
  - `normalized_charging_profiles.csv`
  - `leap_bev_hourly_load_2030.csv`
  - `leap_bev_hourly_load_2030_aggregated.csv`
  - `charging_management_sensitivity_2030.csv`
  - `leap_bev_hourly_shapes_2030.csv`
  - `leap_bev_timeslice_576_2030.csv`
  - `hourly_annual_energy_targets_2030.csv`
  - `phase3_validation_results.csv`
  - `leap_hourly_import_guide.md`
- **Figures:** fig16-fig25.

## 9. Unavoidable approximations (not covered by automated tests)
1. **Readings off charts:** Liu Figs 10-11 and NREL Figs 7, 9 and 15 were read by eye from rendered PDF figures. Expect errors of about ±1 percentage point per bin.
2. **US travel behaviour stands in for Malaysian behaviour.**
3. **Expected-value profiles:** stochastic day-to-day variation is not represented. Profiles are expected values for a large fleet (more than 400k vehicles).
4. **Lunar holidays** are undated, so a few holiday afternoons are treated as peak.
5. **Weekday-arrival next day:** the day after a weekday arrival is treated as a weekday for ToU purposes (Friday to Saturday is conservative).
6. **Year-end wrap:** energy charged after midnight on 31 Dec wraps to 1 Jan 00:00-08:00, standing in for the 2029 carry-in. This puts a slightly high (end-of-year fleet) load into the first morning.
7. **EVI-Pro DC shape:** derived from a small simulated sample and smoothed over 3 hours.
8. **Single next-morning unplug distribution:** applied to weekdays and weekends alike.

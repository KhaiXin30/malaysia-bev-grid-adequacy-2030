# Malaysian charging-behaviour assumptions (Phase 3)

*All parameters are in `src/config.py` (Phase 3 section). Tables: `charging_location_mix_assumptions.csv`, `normalized_charging_profiles.csv`.*

**Status labels used below:**
- **M**: measured (Malaysia)
- **R**: foreign reference, measured or simulated
- **A**: assumption made in this project

**No Malaysian measured charging-timing or charging-location energy data were available.** The profiles are therefore US reference behaviour adapted to Malaysia, and must not be read as observed Malaysian behaviour.

## 1. Charging-location energy mix (share of annual grid charging energy)

| Case | Residential | Workplace | Public AC / destination | Public DC | Rationale |
|---|---|---|---|---|---|
| **base** | **60%** | **5%** | **15%** | **20%** | See below |
| home_low (more condominium / no-home-charging owners) | 45% | 5% | 20% | 30% | Malaysian high-rise housing barriers |
| home_high (landed-house owners dominate) | 75% | 5% | 10% | 10% | Closer to US households with home charging |
| work_high | 55% | 15% | 12% | 18% | Workplace charging expands |

All four cases sum to 100% (validated).

**Status: A**, informed by:
- **R:** EVI-Pro Lite at 30 °C gives home 37-73% of energy depending on home access (50-100%), and workplace 15-30% because US workplace charging is widely available.
- **R:** INL found 84-87% of *events* at home among owners who all had home Level 2.
- **Malaysian secondary evidence (preference, not energy):** 60% prefer home and 29% public, with "limited interest in workplace charging" (Umair et al. 2024, attributed to Deloitte 2023).
- **Malaysian secondary infrastructure evidence:** DC is about one third of public chargers (1,971 of 5,839; MEVnet via secondary source, Mar 2026). Condominium installation barriers are documented: approval by building management (JMB), electrical capacity, and RM5-8k cost.

**Why these values:**
- **Workplace is low (5%)** because the Malaysian evidence points to little workplace charging, unlike the US.
- **DC is high (20%)** because Malaysia's public network is DC-heavy and owners without home charging rely on DC and mall AC.
- **Home is 60%**, matching the Malaysian preference share. This is a coincidence of magnitude, not a measurement of energy.

**Malaysian research context:** Baharin et al. (2024, IJAAS) model only landed houses with home chargers. They exclude apartments and condominiums because their EV ports sit in the parking lot and are billed per service. This is consistent with the `home_low` case for condo-heavy ownership.

**Home-charging access is not modelled as a separate parameter.** It is reflected in the mix cases; no Malaysian survey of the share of EV owners with home charging was found.

## 2. Hourly shapes by location

| Location | Method | Inputs | Status |
|---|---|---|---|
| Residential | Session simulation (40,000 sessions, 15-min steps) | Plug-in hour from Liu et al. Fig. 10; unplug 04:00-11:00 next day from Fig. 11 (approximate readings) | R (adapted) |
| | | Session energy gamma-distributed, mean 12 kWh at the grid (= about 1.5 days of the 8.3 kWh/day average need), CV 0.6 | A |
| | | Charger power 2.3 kW (portable 10 A, 20%) / 7.4 kW (single-phase wallbox, 70%) / 11 kW (three-phase, 10%) | A |
| Workplace | Session simulation | Arrival, park duration and energy from NREL (pre-COVID, approximate readings) | R |
| | | 7.4 / 11 kW AC (80/20) | A |
| Public AC / destination | Shape-based | EVI-Pro Lite public L2 shape, averaged over the three home-access runs | R (simulated) |
| Public DC | Shape-based | EVI-Pro Lite DC shape, averaged, with 3-h circular smoothing to remove simulation noise | R (adapted) |

- **Plugged in vs charging:** for residential and workplace, the model tracks connected vehicles separately from charging power (`connected_share` rows in `normalized_charging_profiles.csv`).
  - Example: a 19:00 home arrival at 7.4 kW finishes a 12 kWh session by about 20:40, but stays connected until about 07:00. That idle window is what managed charging uses.
- **Truncation:** energy that would exceed charger power × connection time is cut off. This affects 0.2% of home energy and 2.6% of workplace energy. Every hourly shape is renormalised, so annual energy is always conserved.
- **Malaysian adaptations:**
  - Clock times are kept as local time (MYT), with no daylight saving.
  - Charger powers follow Malaysian AC norms.
  - US winter heating seasonality is **excluded**.
  - Weekend workplace energy is reduced.
- **Sensitivities:**
  - home arrival **+1 h** (later Malaysian commutes, or a daylight-saving ambiguity in the US source)
  - home session energy **20 kWh** (less frequent charging)

## 3. Weekday, weekend and holidays
- **Total daily charging energy** follows the active fleet (below). Each location is weighted on weekends and holidays by `WEEKEND_ENERGY_FACTOR`:
  - workplace **0.25** (EVI-Pro Lite weekend/weekday ratio)
  - all other locations **1.0** (neutral, A)
- **Holidays:** the five fixed-date TNB holidays in 2030 (1 Jan, 1 May, 31 Aug, 16 Sep, 25 Dec) behave like weekends. Lunar holidays are not dated (see the ToU methodology).

## 4. Fleet growth and seasonality within 2030
- **Fleet growth:** daily energy is proportional to **daily active-BEV vehicle-days** from the Phase 1.5 cohort model (Peninsular Malaysia, base case per scenario). Monthly energy therefore rises from 98.6 GWh in January to 120.2 GWh in December (20% xEV) as the fleet grows (`fig24`).
- **Seasonality:** **neutral** (no monthly travel or consumption factor). There is no Malaysian evidence for monthly variation in EV travel, and Colorado's heating seasonality must not be transferred.
- **Alternative tested:** a flat fleet (no growth) lowers the unmanaged maximum from 375 to 337 MW. The peak falls in late December because the fleet is largest then.

## 5. Daily energy need (consistency check)
The 20% base case gives 1,285 GWh ÷ 425,537 vehicle-years ÷ 365 days = **8.27 kWh per vehicle per day** at the grid (17,969 km ÷ 365 = 49 km/day). A 12 kWh mean home session therefore means a home charge every 1.5-2 days, consistent with INL's 1.1 charges per driving day for longer-range use.

## 6. Malaysian travel patterns
No Malaysian time-of-day travel survey with arrival-home distributions was found. Commuting times similar to the US are an **assumption**, tested with the +1 h home-arrival sensitivity (unmanaged maximum 360 MW vs 375 MW base).

The only Malaysian EV home-charging timing study found, Baharin et al. (2024), also *assumes* rather than measures home charging starting at **18:00 after work**, which is consistent with our unmanaged residential peak at 17:00-19:00. It uses a 6.6 kW charger, consistent with the 7.4 kW base.

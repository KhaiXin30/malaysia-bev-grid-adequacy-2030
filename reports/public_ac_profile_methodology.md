# Public AC / destination charging profile: methodology (Phase 3.1)

*Code: `src/destination.py`, `src/phase31.py`, with parameters in `src/config.py` under "PHASE 3.1". Phase 3 code and outputs are unchanged.*

## 1. Scope

The Phase 3 location mix and every non-public-AC profile are kept. Only the hourly **shape** of the public AC component is replaced, plus (in one sensitivity) its weekday/weekend energy split.
- Public AC is 15% of annual BEV charging electricity: **192.747 GWh** in 2030 at 20% xEV base (= 0.15 × 1,284.977 GWh).
- The comparison set covers:
  - 20% xEV, 30% xEV and historical trend
  - 17,969 km base mileage and the 15,000 km sensitivity
  - unmanaged; ToU staggered at 50% and 100%; synchronized 22:00 at 50% and 100%

## 2. Evidence classes

| Class | Items |
|---|---|
| **Observed / published evidence** | Phase 2 annual energy; Phase 1.5 daily fleet; TNB ToU calendar; EVI-Pro Lite public L2 reference shape (US simulation); Phase 3 residential, workplace and DC profiles |
| **Source-informed timing** (qualitative industry observations, unverified) | Weekday windows 12-14, 17-18 and 20-22 h; weekend single plateau 12-16 h; weekend instantaneous peak higher than weekday |
| **Researcher-selected numerical assumptions** | Relative peak magnitudes; edge smoothing σ; background and floor levels; open hours; weekend energy multipliers; holiday treatment; session-library parameters for the plausibility check |

## 3. Shape construction

All times are MYT in continuous hours. The density is computed on a 1-minute grid and averaged into hour-beginning bins:

```
density(t) = f + (b - f) · SBOX(t; open hours, 1.0 h) + Σ_k a_k · SBOX(t; window_k, σ)
SBOX(t; [L, R], s) = Φ((t − L)/s) − Φ((t − R)/s)        (box with Gaussian edges, circular over midnight)
shape_h = mean of density over hour h, normalised so that Σ_h shape_h = 1 for each day type
```

**Parameters:**
- f = 0.05: overnight floor.
- b = 0.30: daytime background outside the reported peaks.
- Open hours: 09-23 h on weekdays and 10-22 h on weekends (typical mall hours).
- Weekday windows: lunch [12, 14], after work [17, 18], dinner [20, 22]. Weekend window: [12, 16].
- **Amplitudes a_k** are solved by fixed-point iteration. The hourly maximum inside each window (hours {12, 13}, {17}, {20, 21}) must equal the requested **relative magnitude**. The largest is set to 1, so f and b are relative to the tallest peak.
- **Peak shape:** each peak is a smoothed box with plateau width equal to the reported window, not a spike. The default σ = 0.75 h spreads each window over about 3-4 hours. Validation confirms that no hour exceeds twice the mean of its neighbours.

**Default weekday and weekend shapes (% of daily public AC energy, hour-beginning 00..23):**

| | 00-05 | 06-08 | 09-11 | 12-14 | 15-17 | 18-20 | 21-23 |
|---|---|---|---|---|---|---|---|
| Industry-informed weekday | 0.7 0.5 0.5 0.5 0.5 0.5 | 0.5 0.7 1.3 | 2.2 3.1 5.5 | **9.8 9.8** 5.6 | 3.7 6.4 **9.8** | 6.7 6.0 **9.8** | **9.6** 4.8 1.6 |
| EVI-Pro reference weekday | 1.2 0.8 0.6 0.4 0.3 0.5 | 1.2 2.6 4.8 | 6.3 7.2 7.2 | 7.3 7.2 6.8 | 6.3 6.0 6.3 | 7.4 7.4 5.4 | 3.1 2.1 1.6 |
| Industry-informed weekend | 0.7 0.7 0.7 0.7 0.7 0.7 | 0.7 0.7 1.0 | 1.8 3.4 6.7 | **11.7 14.1 14.1** | **11.7** 7.0 4.5 | 4.2 4.2 4.0 | 3.1 1.8 1.0 |
| EVI-Pro reference weekend | 1.6 1.0 0.7 0.5 0.3 0.3 | 0.5 1.4 3.1 | 5.4 6.8 7.6 | 8.0 8.4 7.9 | 7.3 6.8 6.7 | 6.8 6.0 4.7 | 3.5 2.6 2.1 |

**How the shapes compare:**
- **Weekday:** the industry-informed shape puts **57.7%** of daily public AC energy in TNB peak hours (14:00-22:00), against 48.7% for the reference.
- **Weekend:** 51.6% of daily energy falls in 12:00-16:00.
- **Peak heights:** the weekend hourly maximum (14.1%) is 1.44× the weekday maximum (9.8%) at equal daily energy (interpretation 1).

**Configurations** (relative hourly maxima, lunch : after-work : dinner; researcher-defined, not observed):

| Configuration | Ratio | Note |
|---|---|---|
| `equal` (**default**) | 1 : 1 : 1 | Neutral, minimum-information choice: no peak is favoured without evidence |
| `lunch_dominant` | 1.5 : 1 : 1 | |
| `after_work_dominant` | 1 : 1.5 : 1 | Highest unmanaged BEV maximum of the four (overlaps the residential 17-19 h rise) |
| `dinner_dominant` | 1 : 1 : 1.5 | Largest 22:00 synchronized rebound |

**Widths:** σ = 0.5 (narrow), 0.75 (default) and 1.0 h (wide).
- At σ = 1.0 with unequal magnitudes, the smaller of the after-work and dinner peaks merges into its neighbour (prominence below 10%).
- These two variants (`after_work_dominant/wide`, `dinner_dominant/wide`) are flagged `three_weekday_peaks_retained = False`. They are reported, but they no longer represent the observation.
- All other variants keep three distinct peaks (validation requirement 7).

**Choice of default.**
- "Equal" is defensible because the observation gives no magnitude information.
- It is **not the most adverse variant**. It sits mid-range: unmanaged maximum 371.6 MW, against a range of 362.7-384.4 MW across all 12 magnitude × width variants.
- For a conservative screening, use `after_work_dominant` (unmanaged) or `dinner_dominant` (22:00 rebound) as the upper bounds. These are reported side by side.

## 4. Daily energy and the weekend multiplier

Daily public AC energy follows the Phase 3 rule (∝ daily active-BEV vehicle-days). It adds a weekend/holiday factor m, normalised jointly:

```
E_d = E_annual · s_AC · A_d · g_d / Σ_d' A_d' · g_d',    g_d = 1 (weekday) or m (weekend / dated holiday)
```

- With m = 1, the daily energies are identical to Phase 3 (`WEEKEND_ENERGY_FACTOR["public_ac"] = 1.0`).
- With m = 1.25 or 1.5, weekend energy per vehicle-day is m times the weekday value. Weekday energy falls so that annual energy is unchanged.
- 20% xEV base average daily public AC energy:

  | m | Weekday | Weekend/holiday |
  |---|---|---|
  | 1.0 | 528 | 528 |
  | 1.25 | 492 | 615 |
  | 1.5 | 460 | 690 |

  *(Average daily public AC energy, MWh/day.)*

**Holidays.** The 5 dated holidays use the weekend shape and multiplier. This is a researcher choice; the observations do not mention holidays. The lunar holidays remain undated, as in Phase 3.

## 5. Two readings of "active usage"

1. **Power reading (default).** The reported timing is taken to describe charging **power**: the aggregate shape above *is* the power profile.
2. **Occupancy reading (sensitivity `industry_informed__occupancy_basis`).** The reported timing describes **connected vehicles**.
   - A library of 8 destination visit types is simulated with the Phase 3 session engine (`hourly.schedule`, unmanaged). Each visit type has an arrival time, a dwell time (1-9 h), 7.4/11 kW AC power and requested energy (median 10, mean 12 kWh); energy delivered = min(request, power × dwell).
   - Non-negative least squares chooses visit counts so that the mixture's **connected-vehicle** profile matches the industry-informed shape.
   - That mixture's **charging-power** profile is then used.
   - Because charging is front-loaded, power peaks at the start of each window: 12 h, 17 h and 20 h on weekdays (about 15% of daily energy each), and 12-13 h on weekends.
   - The fit is r = 0.93 (weekday) and 0.97 (weekend). The visit types are researcher-defined, not observed.

## 6. Physical plausibility

| Aspect | What was checked | Result |
|---|---|---|
| Charger power and connection windows | Session library: power ≤ charger rating; energy only inside [arrival, departure) | Holds by construction (Phase 3 engine, requirement 10 in Phase 3) |
| Can real sessions produce the aggregate shape? | NNLS fit of the session library to the target **power** shape | r = 0.93 (weekday) and 0.97 (weekend); largest hourly error 5.2 and 3.6 percentage points. Plausible as an aggregate shape |
| Spikes | Each hour ≤ 2 × mean of its neighbours | Passes for all aggregate variants |
| Session energy and dwell | Library mean delivered 7.5-12 kWh per visit; 27-59% of short visits are dwell-limited | Consistent with 1-2 h destination stops at 7-11 kW |
| Overnight floor | 0.5-0.7% of daily energy per hour at 01-07 h | Needs some night arrivals (SOHO residents); the library reproduces about 0. Small energy, flagged |
| Simultaneous charging vehicles (20% xEV, 31 Dec weekday / 29 Dec Sunday maxima, mean AC power 8.84 kW) | Max MW ÷ mean power | Reference 4,900 / 5,600 vehicles; industry-informed 6,500 / 9,400 vehicles |
| Daily sessions | Daily kWh × library sessions per MWh | About 58,000-63,000 destination sessions per day in late 2030 |
| Charger capacity and utilisation | **Not assessable** | No 2030 installed AC capacity, connector count or utilisation data |

**Context, not a constraint.**
- MEVnet reported 5,839 public chargers nationally on 31 Mar 2026, including 1,971 DC (secondary source; whether these are sites or connectors is not stated). That leaves about 3,900 non-DC chargers.
- Both the reference and the industry-informed peaks imply more simultaneously *charging* vehicles than that 2026 total. This comes from the 15% public AC share and the 2030 fleet size, not from the shape. The 2030 AC network size is unknown and was not projected.

**Conclusion:**
- The industry-informed profile is an **aggregate shape approximation**. It is consistent with plausible AC destination sessions, but it is **not** a session-validated physical charging model.
- The relative weekend peak (14.1% of daily energy in one hour) is the most demanding feature. It needs about 1.4× more simultaneous chargers than the weekday peak at equal daily energy.

## 7. Sensitivity design (20% xEV, base mileage, `phase_3_1_peak_sensitivity.csv`)

| Dimension | Values | Held constant |
|---|---|---|
| Relative weekday magnitudes × width × weekend multiplier | 4 × 3 × 3 = 36 variants, each under 5 charging cases | Location mix (base), annual energy |
| Activity interpretation | Occupancy basis (session-derived) | m = 1 |
| Public AC energy share | 10%, 15%, 20%, 25%; other locations rescaled pro rata to sum to 100% | Shapes |
| Existing alternative mixes | home_low (AC 20%), home_high (10%), work_high (12%) | Shapes |
| Residential ToU participation | 0, 25, 50, 75, 100% (staggered) | — |

**What is not provided.** No statistical confidence intervals are given: the inputs have no sampling distribution. Ranges are scenario envelopes.

## 8. What is not done

- No system peak, net load or reserve margin: the GSO baseline is not integrated (validation requirement 15).
- No change to the Phase 3 main case, the location mix or any non-public-AC profile.
- No numerical magnitude taken from the qualitative statement.
- No charging-efficiency adjustment: all energies are grid-side from Phase 2 (÷0.90 once).

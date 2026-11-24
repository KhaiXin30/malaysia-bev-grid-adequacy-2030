# LEAP hourly import guide: BEV charging profiles 2030 (Phase 3)

**Status:** the files below are prepared for LEAP. **No LEAP import has been tested in this project.** The procedure is based on the SEI LEAP help pages read on 23 Nov 2026, listed in the last section. Verify it in your LEAP version.

## Files

| File | Rows | Content |
|---|---|---|
| `leap_bev_hourly_load_2030_aggregated.csv` | 42 profiles × 8,760 | Total BEV charging per hour, for 3 adoption scenarios × 2 mileage cases (17,969 km base; 15,000 km GIZ sensitivity) × 7 charging cases (unmanaged; staggered 25/50/75/100%; synchronized 50/100%). Columns: `timestamp_local` (MYT, +08:00, hour-beginning), `tnb_tou_period`, `hourly_energy_mwh` = `hourly_load_mw`, `normalized_hourly_weight` (sums to 1 per profile). |
| `leap_bev_hourly_load_2030.csv` | 72 location profiles × 8,760 | Same, split into residential / workplace / public_ac / public_dc, for unmanaged and staggered 50% and 100%. Location rows of one profile sum to the aggregated row. About 96 MB. |
| `leap_bev_hourly_shapes_2030.csv` | 8,760 | One column per key profile (base mileage) in **% of annual energy per hour**, plus hour_of_year 1..8760. This is the format LEAP describes for an "Energy Load Shape". |
| `leap_bev_timeslice_576_2030.csv` | 9 profiles × 576 | Example aggregation to 12 months × 2 day types × 24 hours, with % of annual energy, average MW and the **maximum hourly MW inside each slice** |
| `hourly_annual_energy_targets_2030.csv` | 6 | Annual GWh per adoption × mileage case (from Phase 2). Hourly energy = annual GWh × 1,000 × weight. |

## What the LEAP documentation states (SEI help, accessed 23 Nov 2026)
- **Yearly Shapes:** each yearly shape is specified by values for the time slices defined on the Time Slices screen. Shape types include **"Energy Load Shapes (% of annual energy load)"** and "Peak Load Shapes (% of peak load)".
- **Importing hourly profiles:** "You can also import a yearly shape from standard hourly load shape profiles, such as those disseminated by ITRON, EPRI and other companies." The help pages read did not specify the file layout. The SEI exercise material describes importing hourly spreadsheet data on the Yearly Shapes screen and mapping it automatically to the defined time slices.
- **Using shapes:** the System Load Shape can be a YearlyShape or ShapeFromDemand. With ShapeFromDemand, each demand device has a "Load Shape" variable that can reference a Yearly Shape.
- **Leap years:** search-result text attributed to the Time Slices help states that LEAP assumes 8,760 hours per year and no leap years (2030 has 8,760 hours). The Time Slices page itself returned HTTP 404 when fetched, so this is unverified.

## Suggested mapping (to be verified in LEAP)
1. Create a BEV-charging demand branch with electricity consumption equal to the annual GWh (Phase 2 values; already grid-side).
2. Import the matching `leap_bev_hourly_shapes_2030.csv` column as an Energy Load Shape (% of annual energy) on the Yearly Shapes screen. Let LEAP map the 8,760 hours to your time slices.
3. Use the 15,000 km sensitivity by changing annual energy only. Its hourly weights are identical to the base.

## Information lost when aggregating hourly data into time slices
- **Peak smoothing:**
  - At **576 slices** (month × weekday/weekend × hour), the maximum slice-average load is about 1% below the true hourly maximum (20% unmanaged: 371.7 vs 375.5 MW).
  - At **48 slices** (annual weekday/weekend × hour), the maximum average is 337 MW, **about 10% below** the hourly maximum.
  - Coarser seasonal or daily slices smooth more.
- **Calendar effects:**
  - Weekday/weekend and ToU boundaries survive only if slices respect 14:00 and 22:00 and the day type.
  - The intra-year fleet growth (Jan 98.6 → Dec 120.2 GWh/month) survives only with monthly slices.
- **Keep the 8,760-hour files for validation and for the GSO join.**

## Joining to the future GSO / 2030 baseline
- **Join key:** `timestamp_local` (MYT, hour-beginning, 2030).
- **Check the GSO interval convention:** confirm whether GSO hours are hour-ending, and whether values are half-hourly averages or instantaneous.
- **Calendar alignment:**
  - The 2025 GSO shape starts on a **Wednesday**; 2030 starts on a **Tuesday**. Align by weekday and holiday type, not by date.
  - Lunar holidays (Chinese New Year, Hari Raya, Deepavali etc.) fall on different dates in 2025 and 2030.
  - TNB ToU periods here use only the five fixed-date 2030 holidays.
- **Boundary:** BEV energy is at the **charger input, excluding T&D**. If the GSO baseline is **generation / sent-out**, add network losses to BEV load, or remove them from the baseline, before summing.
- **Double counting:** check whether the 2030 demand forecast to be used already includes EV charging. Only remove an embedded BEV component where the forecast documentation justifies it.

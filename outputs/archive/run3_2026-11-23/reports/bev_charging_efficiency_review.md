# Grid-to-battery charging efficiency: review (Phase 2)

*Retrieved 23 Nov 2026. Source IDs match `bev_energy_assumptions_and_sources.csv`.*

## 1. Accounting boundary used
- **Grid energy** = electricity entering the charging equipment at the customer's connection: the home circuit or wallbox for AC charging, and the DC station's grid input for DC charging.
- **Battery energy** = electricity stored in the traction battery and later used for driving and on-board systems. This is the boundary of the consumption values (`bev_efficiency_literature_review.md`).
- The calculation is:

  > **E_grid = E_battery / η**

  It is applied **once**. Validation (requirement 4) checks that grid/battery = 1/η exactly, and that grid-side inputs would not be divided by η.
- **η includes:**
  - the wallbox/EVSE
  - the cable
  - the on-board charger's AC→DC conversion (AC), or the station's conversion (DC)
  - battery charge losses
  - battery thermal management during charging
  - the vehicle's control electronics while plugged in (ADAC: 100-300 W)
- **η excludes:**
  - transmission and distribution losses upstream of the customer meter. These are to be handled consistently with the GSO/LEAP system boundary in Phase 3.
  - energy lost when the battery discharges while driving. That is already inside the battery-side consumption.

## 2. Evidence

| ID | Source | Finding | Boundary / notes |
|---|---|---|---|
| E17 | fueleconomy.gov *EV technology* (ORNL estimates) | "Battery charging efficiency can vary, but it is often **84% to 93%**" | Charging efficiency as used in ORNL's grid-to-wheels chain. The page is undated. |
| E18 | fueleconomy.gov *Where the energy goes: electric cars* (Argonne tests) | Charging losses **16% city, 10% highway, 10% combined** | "Based on tests of several EVs by Argonne National Laboratory". Excludes cabin heating and cooling. |
| E19 | US EPA *Fuel Economy and EV Range Testing* (updated 1 Jul 2026) | EPA values "include charging losses"; they "assume level 2, alternating current (AC) charging"; measured at "the outlet in the wall" | Confirms that EPA label values are **plug-side**. |
| E20 | ADAC, *Ladeverluste beim Elektroauto* (6 Aug 2026; Mercedes CLA, Renault 5, Tesla Model Y, Volvo EX30, VW ID.7; DC: Ioniq 6, Mégane, Model Y, ID.3) | AC 11 kW wallbox: losses **5.1-7.0%**. AC at 4.1 kW: **8.0-12.8%**. 2.3 kW household socket: **12.7-24.2%**. DC: charger about 3% plus battery conditioning 2-8%, giving **5-15%**. | Loss = grid energy "not available for driving". It includes standby electronics. Losses rise at low power and long charging times. Batteries tested at 20-30 °C (AC). |
| E21 | Apostolaki-Iosifidou, Codani & Kempton (2017), *Energy* 127:730-742 | One-way losses **12-36%** in the tested conditions; largest losses in the AC-DC power electronics, worse at low power and low state of charge | Laboratory set-up including building circuits. Abstract only (RePEc). Represents the low-efficiency tail. |
| E08 | EV Database (ATTO 3) | WLTP vehicle-side/rated ratio **0.90-0.92** | Implies about 8-10% loss inside WLTP rated values. This is a database conversion, not a measurement. |

## 3. AC vs DC, and Malaysian conditions
- **AC home/workplace charging:**
  - At wallbox powers of 7-11 kW, measured losses are about 5-10%, so efficiency is about 0.90-0.95.
  - At low power (portable 13 A or 2.3 kW socket), losses are 13-24%.
  - Higher on-board-charger power reduces the time-proportional losses from standby electronics (ADAC).
- **DC fast charging:**
  - Station conversion is about 3%. Battery thermal management adds 2-8%.
  - In Malaysia the battery mostly needs **cooling** during fast charging, not heating. Cooling energy at 30-35 °C ambient is not quantified in the sources found.
- **Charging mix:** Malaysian data on home vs public and AC vs DC were not found. It is a review item. A fleet-level η therefore stands for an unknown mix.

## 4. Selected fleet-level assumptions (`config.CHARGING_EFFICIENCY`)

| Level | η | Used in | Evidence |
|---|---|---|---|
| High efficiency | **0.93** | LOW-energy case | ADAC 11 kW wallbox (93.0-94.9%); ORNL upper bound 93% |
| **Base** | **0.90** | BASE | Argonne combined 10% loss; mid-range of ADAC reduced-power AC (8-13%) and DC (5-15%); EVDB WLTP ratio 0.90-0.92 |
| Low efficiency | **0.85** | HIGH-energy case | ORNL lower bound 84%; low-power AC charging; DC charging with heavy battery cooling; Apostolaki-Iosifidou low-power results |

**Effect on 2030 Peninsular energy (20% base):** −3.2% at η = 0.93 and +5.9% at η = 0.85. This is the smallest driver after vehicle mix.

# TNB Time-of-Use managed-charging methodology (Phase 3)

## 1. Official ToU rules (verified 23 Nov 2026)
- **Peak and off-peak hours:**
  - **Monday-Friday:** peak 14:00-22:00, off-peak 22:00-14:00.
  - **Saturday, Sunday and public holidays:** off-peak all day.
  - Sources: the TNB ESG story "Time-of-Use: Giving Customers More Choice for Smarter Energy Management", and the myTNB tariff page and ToU announcement (1 Jul 2026).
- **Public holidays:** the myTNB footnote lists **15 named holidays**:
  - New Year's Day; Chinese New Year (days 1 and 2); Hari Raya Aidilfitri (days 1 and 2); Labour Day; Wesak Day; Yang di-Pertuan Agong's Birthday; Hari Raya Aidiladha; Awal Muharram; Independence Day; Malaysia Day; Maulidur Rasul; Deepavali; Christmas Day.
  - **2030 dates:** only the **fixed-date** holidays can be dated without an official 2030 gazette: 1 Jan (Tue), 1 May (Wed), 31 Aug (Sat), 16 Sep (Mon), 25 Dec (Wed).
  - **Lunar and variable holidays are not dated** and are treated as ordinary days. This is a conservative choice: it leaves a few extra peak hours. They must be added when the 2030 calendar is gazetted (`config.TOU_UNDATED_HOLIDAYS`).
  - Whether state holidays count is not stated by TNB.
- **Eligibility and scope:**
  - ToU is **optional (opt-in via myTNB)**.
  - Available to domestic and non-domestic low-voltage customers (smart meter linked to participation), plus non-domestic MV/HV ToU tariffs.
  - Domestic rates for ≤1,500 kWh/month: peak 28.52 vs off-peak 24.43 sen/kWh; general tariff 27.03.
- **Uptake:** about **217,000 customers switched** between July 2025 and July 2026. TNB states that 94% of a sample of 83,163 domestic ToU customers used more than 70% of their electricity off-peak.
- **EV guidance:** TNB recommends EV charging after 22:00, and staggered overnight fleet charging.
- **No EV-specific tariff** was found.

**Implications for the model:**
- ToU is a **household** tariff, so management is applied to **residential charging only**.
- Workplace charging (employer tariff) and public charging (operator pricing) are not ToU-managed.
- Participation rates are **assumptions**. No data on ToU uptake among EV owners exist.

## 2. Managed-charging algorithm (session-based; `src/hourly.py: schedule`)
Each simulated residential session has:
- arrival (plug-in) time
- departure (unplug) time next morning
- required grid energy
- charger power

The connection window is [arrival, departure). Energy delivered = min(requested, power × window) and is **identical under every strategy**.

| Strategy | Rule |
|---|---|
| Unmanaged | Charge at full power from arrival until the energy is delivered |
| **Managed, staggered** (working case) | Allowed steps = window ∩ off-peak. A start offset is drawn uniformly from the slack (allowed steps − steps needed), so starts spread between 22:00 and the latest start that still finishes before departure. If off-peak capacity in the window is insufficient, all off-peak steps are used and the remainder charges as early as possible in peak steps ("unshiftable" energy: 0.6% of weekday home energy). |
| Managed, synchronized (rebound demonstration) | Same as staggered but with zero offset: every participating session starts at the first off-peak quarter-hour, i.e. 22:00 for evening arrivals |

- **Weekends and dated holidays** are all off-peak, so managed sessions charge as unmanaged.
- **Conservative calendar choice:** the day after a weekday arrival is treated as a weekday. Friday to Saturday is actually off-peak, so this choice only affects sessions running past 14:00 the next day.
- **Validation:** energy is never moved to a time when the vehicle is not connected, and power never exceeds the charger rating (validation requirement 10).
- **Participation p** = share of residential **sessions** under ToU management. The hourly residential shape is (1 − p) × unmanaged + p × managed, which is exact in expectation.
  - Share of **drivers** participating = p.
  - Share of **total charging energy** under management = p × 60% (the residential share). At most 60% of BEV charging energy can be shifted by household ToU in the base mix.

## 3. Results (20% xEV base, 2030 Peninsular Malaysia; `charging_management_sensitivity_2030.csv`)

| Participation | Energy in TNB peak | Shifted out of peak | Max weekday load | Max load overall (when) | Max hourly ramp |
|---|---|---|---|---|---|
| 0% (unmanaged) | 40.8% (524 GWh) | — | 375 MW | 375 MW (Tue 31 Dec 18:00) | 68 MW/h |
| 25% staggered | 33.5% | 94 GWh | 308 MW | 356 MW (Sun 29 Dec 18:00) | 66 MW/h |
| **50% staggered (provisional)** | **26.2% (337 GWh)** | **187 GWh** | **240 MW** | 356 MW (Sunday evening) | 65 MW/h |
| 75% staggered | 18.9% | 281 GWh | 229 MW | 356 MW (Sunday evening) | 72 MW/h |
| 100% staggered | 11.7% (150 GWh) | 374 GWh | 294 MW (overnight, off-peak) | 356 MW (Sunday evening) | 113 MW/h |
| 50% synchronized 22:00 | 26.2% | 187 GWh | **557 MW at 22:00** | 557 MW | 447 MW/h |
| 100% synchronized 22:00 | 11.7% | 374 GWh | **974 MW at 22:00** | 974 MW | 947 MW/h |

**Interpretation:**
- **Staggered management works:** it halves weekday-evening BEV load at 50% participation.
- **The BEV maximum moves to the weekend:** because ToU leaves weekends off-peak, the yearly maximum shifts to the weekend evening (356 MW), which management does not touch.
- **New overnight hump at full participation:** 100% staggered participation creates an off-peak overnight hump of 294 MW.
- **Synchronized starts create a severe 22:00 rebound** (2.6× the unmanaged peak) and a large ramp. A ToU tariff alone does not stagger starts: chargers timed to "22:00" would synchronize.
  - This is a realistic behaviour: both TNB's own advice ("charging an electric vehicle after 10.00 p.m.") and the Malaysian study by Baharin et al. (2024, IJAAS), which assumes 22:00 starts and finds them the cheapest, point owners to the same start time.
  - The same study notes that randomising charging times within off-peak periods reduces peak loads (citing earlier work). That is the rationale for the staggered working case.
- **Remaining peak-hour energy** at 100% (11.7%) is workplace (afternoon), public AC/DC and unshiftable home energy.

**What these results are not.** They are **BEV-only** loads. Whether a lower BEV evening peak lowers the **system** peak depends on the GSO non-BEV demand profile. In particular, the weekend evening and 22:00-02:00 overnight periods must be checked against the system load. Nothing here shows a system-peak reduction or a reserve-margin improvement.

## 4. Provisional working case for LEAP
**`managed_staggered_p50`**: 50% of residential sessions managed with staggered starts. This is **an assumed intermediate participation, not a measured Malaysian rate**.
- Carry the 100% staggered case as an upper bound.
- Carry the synchronized cases as a rebound-risk stress test.

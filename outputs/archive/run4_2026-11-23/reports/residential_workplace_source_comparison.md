# Residential and workplace charging-profile sources: comparison

*Phase 3, 23 Nov 2026. Machine-readable version: `outputs/tables/charging_profile_sources.csv`.*

**Decision key:**
- **use directly**: input taken as published
- **adapt**: used with documented changes
- **validate against**: used only to check model outputs
- **reject**: not used, with the reason given

## Comparison table

| Reference | Country & period | Setting | Observed / modelled | BEV-only? | Resolution | Downloadable numeric data | Charging-time findings | Strengths | Limitations | Applicability to Peninsular Malaysia | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A. NREL/NLR Workplace Charging Data** (data.nlr.gov/submissions/182; OpenEI 8237) | USA, Golden CO; Nov 2016-Jul 2021 | Workplace | **Observed** sessions | No: BEV + PHEV (Leaf 42%, Volt 31%) | Session timestamps (MST) | **No, as of 23 Nov 2026**: catalog offline (503), S3 AccessDenied, no archived copy | (via report) arrivals 07:30-08:30; aggregate power peak 09:00 | Real metered sessions; plugged-in vs charging fields; free vs paid; COVID flag | Single US lab campus; early adopters; 3.3/6.6 kW; MST/daylight-saving convention unclear | Shape of commuter workplace charging plausibly similar; volume not transferable | **Reject raw data (inaccessible)**, but see the report row below |
| **A'. Neuman, Meintz & Jun (2021)**, NREL/TP-5400-77515 (companion report) | Same | Workplace | **Observed** (summary statistics, figures) | No | 30-min arrival histograms; hourly average power | PDF only; figures digitised approximately | Bimodal park duration ~3.5 h / ~8.5 h; mean 11.1 kWh; paid sessions deliver more energy; COVID reduced use | Exact summary statistics; pre-COVID panels separable | No raw data; approximate chart readings; mixed BEV/PHEV | Arrival, duration and energy patterns plausible for Malaysian office commuters; power upgraded to 7.4/11 kW | **Adapt** (workplace session model) and **validate** (r = 0.96 vs Fig. 15) |
| **B. Liu et al. (2024)**, IEEE ITEC, NREL/CP-5400-89286 | USA, Boulder & Aurora CO; 2030 projection (NHTS 2017 travel) | Residential | **Modelled** (EVI-Pro, uncontrolled); 2 controlled real-world datasets used for timing comparison | No (light-duty EVs) | 1-week feeder profiles; hourly plug-start / unplug histograms | **No numerical series published** | Simulated plug-in peak 17:00-18:00; real controlled plug-ins later (20:00-22:00); unplug 07:00; winter loads highest | Data-driven itineraries; validated plug/unplug timing; feeder-level view | Simulation; Colorado; winter heating penalty 1.602 (January); figures only | Evening-arrival timing usable; **heating seasonality not transferable** | **Adapt** timing (approximate digitisation); **reject** seasonal/heating scaling |
| EVI-Pro Lite API (NREL), retrieved 23 Nov 2026 | USA travel data; user-set 30 °C, 35 mi/day | Home, work, public L2, DC | Modelled | Yes (BEV setting) | 15-min, weekday/weekend | **Yes** (JSON saved) | Home peak 18:00-19:00; work 08:00-09:00; public L2 09:00-19:00; DC midday | Consistent categories; temperature setting; reproducible | US travel; US charging availability | Public shapes adapted; location shares give an order of magnitude only | **Use (adapted) for public AC/DC; validate** home and work |
| INL *Plugged In* (2015) | USA EV Project 2012-13 | Home and away | Observed | No (Leaf, Volt) | Aggregate | PDF | 84-87% of events at home; overnight charging nearly all at home | Very large measured sample | Old vehicles; 100% home Level 2 access | Upper bound on home share for households with home charging | **Validate** |
| Umair et al. (2024) JSDEWES review | Malaysia, to 2023 | All | Secondary review (preference survey) | n/a | — | Web | 60% prefer home, 29% public; limited workplace interest | Malaysian | Preference, not energy; survey method not given on page | Direction only | **Validate** (direction of home share) |
| Baharin et al. (2024) IJAAS 13(4):773-780 | Malaysia; household loads Sep-Oct 2021 (TNB data) | Residential (landed houses) | **Modelled**: measured house loads + assumed EV charging | Yes (one Nissan Leaf, 6.6 kW) | Hourly, one month | PDF only (supplied); no EV time series | Assumed starts 18:00 / 22:00 / 09:00 "based on Malaysian driving styles"; condos excluded (parking-lot chargers) | Malaysian context, TNB data, Malaysian tariff analysis | EV timing assumed, not observed; one vehicle type; pre-2025 hypothetical ToU structures; unit inconsistencies | Directly Malaysian, but as researcher assumptions | **Validate** (18:00 arrival, about 7 kW, 22:00 ToU start, condo exclusion) |
| DC Handal / Gentari / JomCharge / ChargeSini / MEVnet | Malaysia 2025-26 | Public | — | — | — | **No session data published** | — | Would be first-best for public DC timing | Not available | — | **Reject (no data)**; request from operators |

## Main take-aways
1. **Neither mandatory source supplies directly usable Malaysian hourly data.**
   - Source A's raw dataset could not be downloaded, and its report gives US workplace behaviour that serves as a validation target.
   - Source B gives simulated US residential timing that is adapted for Malaysia; its seasonal heating effects are rejected.
2. **The shapes agree.** Residential (Liu), workplace (NREL) and EVI-Pro Lite shapes are mutually consistent:
   - Evening home peak at 17:00-20:00 (Liu simulation, EVI-Pro).
   - Morning workplace peak at 08:00-10:00 (NREL measured, EVI-Pro).
   - This consistency supports using them as reference behaviour.
3. **What remains unmeasured for Malaysia:** the *energy* split across locations and the real timing of public DC charging.

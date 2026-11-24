# Assessment of industry observations on AC destination charging (Phase 3.1)

*23 Nov 2026. Evidence status: **preliminary, qualitative, unverified**.*

## 1. The evidence

**Source.** Personal communication from an industry practitioner (anonymised) with experience analysing usage data from AC destination chargers in Malaysia, relayed by the project owner on 23 Nov 2026. In this project it is cited as *"industry practitioner, personal communication (anonymised), 2026"*.

**Summary of the observations** (paraphrased; the original wording is held by the project owner):

| Aspect | Observation as reported |
|---|---|
| Scope | AC (lower-power) destination chargers, such as shopping-mall and SOHO car parks. Highway ("on-the-go") chargers were not covered |
| Method | Several months of charger "active usage" data were overlaid to identify recurring peaks |
| Weekdays | Three peaks: lunch (12:00-14:00), after work (17:00-18:00) and dinner (20:00-22:00) |
| Weekends | A single, sustained peak from about 12:00 to 16:00. The practitioner was less certain about this pattern |
| Weekend vs weekday | Weekend activity was described as higher, with a markedly larger peak |

**How the source is handled:**
- The practitioner and their organisation are not identified in any project file.
- The observations are not a publication of any organisation, and no organisation has reviewed or endorsed the assumptions in this project.
- No dataset was provided or used. Only the qualitative description above enters the model.

## 2. What the statement does and does not establish

| Item | Stated? | Notes |
|---|---|---|
| Charger type | Yes: AC destination (malls, SOHO car parks); not highway DC | Matches the model's "public AC / destination" category. Charger power not given |
| Day type split | Yes: weekday vs weekend | Public holidays not mentioned |
| Weekday peak times | Yes: 12:00-14:00, 17:00-18:00, 20:00-22:00 | Clock times; time zone assumed MYT |
| Weekend shape | Yes: unimodal, sustained about 12:00-16:00 | Reported with less certainty than the weekday pattern |
| Weekend vs weekday | Higher weekend activity; markedly larger weekend peak | Ambiguous: higher peak, higher daily energy, or both |
| Relative heights of the 3 weekday peaks | **No** | — |
| Absolute magnitudes (kW, kWh, sessions) | **No** | — |
| Metric | "Active usage" | **Undefined.** Could mean active charging power, connected (occupied) chargers, or session counts |
| Geography | **Not confirmed** | Peninsular Malaysia is likely but not stated; sites and their mix unknown |
| Sample size, number of chargers, period | "A couple of months"; rest unknown | Year unknown, so it could be pre- or post-ToU (July 2025) |
| Data processing | "Overlaying" datasets | Unknown whether profiles were averaged, normalised or visually compared |

## 3. Why these gaps matter

1. **Occupancy is not power.**
   - A car can stay connected long after its battery is full. With a 1.5-2 h dwell at 7.4-11 kW, a session's charging is front-loaded at arrival.
   - If "active usage" means connected vehicles, the true power peaks are **earlier and narrower** than the reported windows.
   - This project tests both readings (section 5 of `public_ac_profile_methodology.md`).
2. **Sessions are not energy.**
   - Session counts weight a 3 kWh top-up the same as a 30 kWh charge.
   - Lunch sessions are short by construction, so a lunch *session* peak overstates the lunch *energy* peak.
3. **A larger weekend bump does not establish more weekend energy.**
   - A narrower, taller weekend peak can carry the same daily energy as a weekday with three peaks.
   - Two interpretations are therefore modelled separately:
     - **Interpretation 1 (default):** higher instantaneous weekend activity, with equal daily energy per active vehicle-day.
     - **Interpretation 2:** higher weekend daily energy, using hypothetical multipliers of 1.25 and 1.5 that are **not observed**.
4. **The magnitudes are unknown.**
   - This project never assigns a numerical peak height from the statement.
   - Relative heights are researcher-defined scenarios: equal (neutral), lunch-, after-work- and dinner-dominant at 1.5×.
5. **Representativeness is unknown.** The behaviour of mall and SOHO car parks in the practitioner's dataset may not describe all 2030 public AC charging in Peninsular Malaysia.
   - That category also covers hotels, offices and public car parks.
   - It also spans many operators: the Energy Commission register lists 310 EVCS licensees in Peninsular Malaysia (Oct 2026; `evcs_licence_register_assessment.md`).

## 4. Quality grading

| Criterion | Grade | Reason |
|---|---|---|
| Relevance to Malaysia | **High** | The only Malaysian, practitioner-reported timing information on public AC charging available to the project |
| Relevance to the category | **High** | Explicitly AC destination, explicitly not highway |
| Verifiability | **Low** | Personal communication; no data, method or sample description |
| Precision | **Low** | Timing windows only; no magnitudes; metric undefined |
| Independence | **Low-moderate** | A single practitioner and a single dataset |
| Recency | **Unknown** | The year of the dataset is not stated |

**Overall:** credible and useful as **timing evidence**, but insufficient to replace a documented reference shape. Most usefully, it confirms that Malaysian destination charging has a **midday (12-14 h) component** and an **evening (20-22 h) component**. The US EVI-Pro Lite reference spreads energy broadly over 09:00-19:00 and is low after 21:00 (5.4% at 20:00, 3.1% at 21:00).

## 5. How the evidence is used

| Use | Status |
|---|---|
| Weekday peak windows 12-14, 17-18, 20-22 h | **Informed by the observations** |
| Weekend single plateau 12-16 h | **Informed by the observations** |
| Weekend peak higher than weekday peak (same daily energy) | **Informed by the observations** (interpretation 1) |
| Relative heights of weekday peaks | **Researcher-defined** (4 configurations) |
| Width and edge smoothing of peaks | **Researcher-defined** (σ 0.5 / 0.75 / 1.0 h) |
| Background (0.30) and overnight floor (0.05) levels | **Researcher-defined** |
| Weekend:weekday daily energy (1.0 / 1.25 / 1.5) | **Hypothetical** |
| Public AC share of BEV energy (15%) | Unchanged Phase 3 **scenario assumption**; tested at 10-25% |
| Whether the timing describes power or occupancy | **Unknown**; both readings tested |
| Applying the weekend pattern to the 5 dated public holidays | **Researcher-defined** (holidays are not mentioned in the statement) |

## 6. Follow-up questions for the source (to upgrade the evidence)

1. What exactly does "active usage" measure: kW delivered, connectors occupied, or sessions started?
2. Which period and year, and how many chargers and sites? Were they Peninsular only?
3. What are the charger powers (7 kW, 11 kW or 22 kW AC)?
4. Can approximate relative heights be shared, such as lunch : after-work : dinner, and the weekend peak against the weekday peak?
5. Was weekend **daily** energy per charger higher than on weekdays, and by roughly how much?
6. Were public holidays and Ramadan / festive periods different?
7. Could an anonymised, normalised 24-hour profile be shared, for example hourly shares of daily kWh by day type?

Any one of answers 1, 4 or 7 would materially strengthen this sensitivity. The highest-value data would remain session records from a Malaysian charge-point operator (Phase 3 source register H08).

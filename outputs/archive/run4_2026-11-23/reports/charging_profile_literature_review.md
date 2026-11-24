# Charging-profile literature review (Phase 3)

*Retrieved 23 Nov 2026. Source register: `outputs/tables/charging_profile_sources.csv` (H01-H10). Readable local copies are in `data/raw/literature/` (the EVI-Pro Lite JSON files) and the session scratch area. Side-by-side table: `residential_workplace_source_comparison.md`.*

**How to read this document.** Each statement is labelled with one of three evidence types:
- **measured**: observed charging sessions or meter data
- **simulated**: a model output
- **assumption**: a choice made in this project

**No Malaysian measured charging-time data were found.** Every hourly shape used here is a US reference shape adapted to Malaysia.

## 1. Mandatory source A: NREL/NLR workplace charging data

### 1.1 Dataset (H01)
- **Where it is listed:** https://data.nlr.gov/submissions/182, also https://data.openei.org/submissions/8237. The file is `dataSet_Oct2021.csv`, licensed CC-BY 4.0.
- **Access result on 23 Nov 2026: not obtainable.**
  - The data catalog returned HTTP 503, "Data Catalog is Temporarily Offline".
  - The underlying S3 object (`nrel-datacat-public-prod`) returned "AccessDenied".
  - The OpenEI mirror path returned 404.
  - The Wayback Machine holds only 302 redirects to expired signed URLs, with no file content.
- **Consequence:** I could not separate BEVs from PHEVs session by session, split free from paid charging, filter COVID-affected periods, or rebuild an hourly profile from raw power data. **No values were invented to fill this gap.**

### 1.2 Companion report (H02)
Neuman, Meintz & Jun (2021), *Workplace Charging Data Collection and Behavior*, NREL/TP-5400-77515. Full PDF obtained from OSTI.

**Data dictionary:**
- **Timestamp fields:** `request_entry_time`, `start_date_time` / `end_date_time` (plugged in / unplugged) and `start_charge` / `termin_charge` (power flowing / power stopped). All are in **MST**. The report does not say whether daylight saving was applied; this is flagged.
- **Energy and power fields:** `energy_charged` (kWh delivered), `kwh_requested`, `max_charge_power` (3.3 or 6.6 kW, Level 2), `controlled_duration`.
- **Other fields:** `afterPaid` (free until May 2019, paid from June 2019) and `vehicle_model`.

**Descriptive statistics (exact values printed in Figs 3-4):**
- 39,303 sessions, Nov 2016 to Jul 2021.
- Vehicle mix: Nissan Leaf 41.9%, Chevrolet Volt (PHEV) 30.6%, BMW i3 4.5%, Bolt 4.1%, Model 3 3.2%, Prius Prime (PHEV) 2.6%. 17.6% of sessions have no model.
- Energy delivered: mean 11.1 kWh, median 9.5 kWh, maximum 68.3 kWh.
- Maximum charge power: median 3.3 kW, mean 4.0 kW.
- 33.2% of sessions are paid.

**Behaviour (Figs 7-16; measured, read approximately from the charts):**
- Pre-COVID arrivals peak at 07:30-08:30, with a second smaller peak at 12:00-13:30 (lunch returns).
- Park duration is bimodal: about 3.5 h ("until lunch") and about 8.5-9 h (a full working day).
- Over 95% of users plug in once per day.
- Paid charging delivered **more** energy per session than free charging: the report suggests opportunistic "free" top-ups disappeared once payment was required.
- COVID-19 remote work cut use sharply (Figs 6 and 16), so those months are not representative.
- Pre-COVID average hourly power across all chargers peaks at **09:00** (about 70-75 kW) and is near zero after 19:00 (Fig. 15).
- **Plugged in vs actively charging:** vehicles stay connected for 3.5-9 h, but at 3.3-6.6 kW the average 11 kWh session needs only about 2-3 h. Most connected time is therefore idle. This is visible in the separate departure-time distribution (Fig. 8).

**Biases:**
- **Who the drivers are:** a US national-laboratory workforce with early arrivals (Colorado science campus), free or cheap parking, and mostly first-generation, short-range BEVs and PHEVs.
- **Charger power:** low (3.3/6.6 kW).
- **Sample:** a single site, with paid and free periods confounded with fleet change.

**How it was used (adapt and validate):**
- The arrival and park-duration distributions and the energy-per-session statistics drive the workplace session model.
- A validation run using NREL's charger mix reproduces the shape of the observed Fig. 15 profile with **r = 0.96** (`fig17`, `fig25`).
- The Malaysian run uses 7.4/11 kW AC (assumption), so charging finishes sooner after arrival and the 08:00-10:00 peak is sharper.
- No COVID-era statistics were used; all distributions are the pre-COVID panels.

## 2. Mandatory source B: Liu et al. (2024), residential charging in Colorado (H03)
Liu, Alexeenko, Bruchon, Zhang & Kisacikoglu (2024), *Analyzing Residential Charging Demand for Light-Duty Electric Vehicles in Colorado*, IEEE ITEC 2024 (doi:10.1109/ITEC60657.2024.10598922). The full preprint NREL/CP-5400-89286 was read (obtained via `docs.nlr.gov`).

**Method (simulated):**
- **Adoption:** TEMPO projects adoption for 2030 (Boulder 26%, Aurora 16% EV share).
- **Travel:** itineraries are sampled from the 2017 NHTS and calibrated with NextGen NHTS origin-destination data.
- **Charging simulation:** EVI-Pro assumes cost minimisation, with **home charging preferred, then workplace and public Level 2, then DC fast**.
- **Seasons:** three representative months (Jan, Jul, Sep), each a one-week simulation.
- **Feeders:** results are assigned to 10 feeders.

**Unmanaged assumption:** "the EV charging simulation in this study assumes uncontrolled charging". Charging starts when the car is plugged in at home.

**Results:**
- **Winter feeder peaks:** less than 1 MW to more than 4 MW. 6 of 10 feeders were loaded above 1.3 per unit.
- **Weekly energy:** January needs are about 30% above July (Boulder 483 vs 373 MWh/week). This is driven by an **ambient penalty factor of 1.602 in January vs 1.059 in July** (cabin and battery heating, from FASTSim) and by travel scaling factors of 0.89 / 1.06 / 1.00.
- **Plug-in and unplug timing:** the simulated plug-in start peaks at **17:00-18:00** and unplug at **07:00** (Figs 10-11). These match two utility datasets of **controlled** real-world charging (439 EVs and 11k sessions; 278 Teslas and 39k sessions) on timing. The real-world controlled plug-ins sit later, at **20:00-22:00**: "real-world controlled EV charging might delay actual EV charging start time ... which is not considered in our simulation".

**Data availability:** **no numerical time series are published**, only figures. The hourly plug-in and unplug histograms were **read approximately from Figs 10-11** (stored in `config.LIU2024_PLUG_START` / `LIU2024_UNPLUG_MORNING` and labelled as approximate). The last plotted bar covers hours 22-23 and was split evenly. Feeder power traces (Figs 8-9) were not digitised.

**Transferability to Malaysia:**
- **Timing:** evening home arrival and morning departure are structurally similar for commuting households, so the timing is used (adapted).
- **Seasonality: rejected.** The January heating penalty (+60%) and winter travel factors must **not** be transferred to tropical Malaysia, which has no heating season and roughly year-round air-conditioning load. Malaysian consumption is already set in Phase 2.
- **Time zone:** local clock times are used as given. The paper does not state its timestamp or daylight-saving convention, so a one-hour daylight-saving ambiguity is possible and is covered by the +1 h home-arrival sensitivity.

## 3. Additional evidence

| ID | Source | Type | What it contributes |
|---|---|---|---|
| H04 | **NREL EVI-Pro Lite API** (`developer.nlr.gov`, retrieved 23 Nov 2026; demo key). BEV fleet of 10,000, 35 mi/day (about 56 km; Malaysia ≈ 49 km/day), 30 °C, mostly Level 2, unmanaged ("min_delay"). Home access 50/75/100%. | simulated (US travel) | **Weekday energy shares:** home 37-73%, workplace 15-30%, public L2 12-29%, DC 1-5%. **Timing:** home peaks 18:00-19:00; workplace 08:00-09:00; public L2 broad 09:00-19:00; DC midday. **Weekend:** workplace energy is about 0.25 of weekday. These shapes were **used, adapted, for public AC/DC**. The "midnight_charge" option returned HTTP 400 and was not used. |
| H05 | INL *Plugged In* (Smart & Salisbury 2015), EV Project 2012-13 | measured (US) | **84% (Leaf) / 87% (Volt) of charging events at home**, but every participant had a home Level 2 charger. Leafs charged 1.1 times per driving day. DOE Fact #909 (search extract only) gives energy shares of 57% home / 39% work for Leafs **with workplace access**. |
| H06 | TNB ToU pages | official | Tariff calendar. See `tnb_tou_management_methodology.md`. |
| H07 | Umair et al. (2024) JSDEWES review | secondary (Malaysia) | "60% of users in Malaysia prefer home charging, 29% ... public". This is a **preference**, attributed to Deloitte 2023, and was read from a page summary rather than verbatim. The review also reports limited interest in workplace charging, 1,500 public stations at end-2023, and over 70% of stations below 29 kW. |
| H08 | Malaysian charge-point operators (DC Handal, Gentari, JomCharge, ChargeSini), MEVnet | — | **No public session or utilisation data.** DC Handal publishes deployments and prices only. MEVnet counts 5,839 public chargers including 1,971 DC (31 Mar 2026, secondary). **The DC Handal data proposed in the original presentation are therefore unavailable.** Requesting them is a review item. |
| H09 | **Baharin, Sulaima, Dahlan & Mokhlis (2024)**, *Evaluation of the time-of-use tariff responsiveness for plug-in electric vehicle home charging in Malaysia*, IJAAS 13(4):773-780, doi:10.11591/ijaas.v13.i4.pp773-780. Full PDF supplied by the project owner on 23 Nov 2026. | **simulated (Malaysia)**: *measured* household base loads (Sep-Oct 2021, TNB-provided) + *assumed* EV charging | See section 3.1 |
| H10 | NREL TEMPO / dsgrid profiles | simulated (US) | Available as large parquet files on OEDI. Not downloaded: US county shapes add little beyond EVI-Pro Lite. |

### 3.1 The only Malaysia-specific EV home-charging timing study found (H09)
**Set-up:**
- Four landed house types: single-storey, double-storey, semi-detached and bungalow, with measured household load profiles. TNB provided the data.
- Apartments and condominiums are **excluded** "because the PEV charging port is usually installed in the parking lot and charges per service rate". This is Malaysian support for treating high-rise owners differently (the `home_low` mix).
- One homogeneous EV: Nissan Leaf, 40 kWh, 6.6 kW home charger, about 7 h from 20% to 100% state of charge.
- **Charging start times are assumptions** "based on the Malaysian driving styles":
  - 18:00, "when they arrive home after work"
  - 22:00, "during sleep time"
  - 09:00, "for people who stay home"
- Charging frequency: daily, every 2 days, every 3 days, or random (22 sessions per month).
- ToU structures S1-S4 are hypothetical designs with price elasticities of −0.02 and −0.27. They pre-date TNB's July 2025 ToU scheme.

**Findings:**
- The lowest bills come from 22:00 and 09:00 starts under the four-segment structure S1.
- Random charging under structure S4 incurs high costs at 21:00-22:00.

**Quality notes:**
- Some units in the text are inconsistent: "230 V/10 A" is stated alongside 6.6 kW, and the 7-h charge is given as "46.2 kW" where kWh is meant.
- No EV session data are measured. EV timing is fixed by assumption.

**Use in this project: validate only.**
- Malaysian researchers independently assume **18:00 home arrival**. Our Liu-based unmanaged residential peak is 17:00-19:00.
- They assume about **7 kW home charging**. Our base is 70% at 7.4 kW.
- They assume **22:00 as the ToU-driven start**, which supports treating a synchronized 22:00 rebound as a realistic risk rather than a modelling artefact.
- Their full-charge sessions (about 32 kWh into the battery) are larger than our 12 kWh mean. This is partly covered by the 20 kWh sensitivity: unmanaged maximum 351 MW and a smaller synchronized spike, 674 MW vs 974 MW.

## 4. Three distinct measures of charging location

| Measure | Evidence found | Status for Malaysia |
|---|---|---|
| 1. % of BEV owners **using** a location | Malaysian **preference**: 60% home, 29% public (H07) | Not measured |
| 2. % of **sessions** at a location | US: 84-87% of events at home (H05; all participants had home charging) | Not measured |
| 3. % of **charging energy** at a location (used by this model) | US simulations 37-73% home (H04); US measured 57% home among Leafs with workplace access (H05/Fact 909) | **Not measured. The mix is a scenario assumption** (`malaysia_charging_behavior_assumptions.md`) |

DC sessions deliver more energy per session but are fewer, so session shares understate DC's energy share, and owner-preference shares say nothing about energy.

## 5. Synthesis
- Residential unmanaged charging peaks in the early evening (17:00-20:00) in every source: Liu, EVI-Pro Lite, and INL's "nearly all overnight charging was at home".
- Workplace charging peaks at 08:00-10:00, as measured at NREL and simulated in EVI-Pro.
- Public AC is broad across daytime and evening. DC peaks around midday (simulated).
- The main gaps for Malaysia:
  - charging-energy shares by location
  - home-charging access in high-rise housing
  - public DC timing
  - actual ToU uptake among EV owners

  Charge-point operators, TNB smart-meter data and MGTC are the most promising data holders.

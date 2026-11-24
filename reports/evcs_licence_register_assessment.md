# Energy Commission EVCS licence register: assessment (context only)

*23 Nov 2026. Code: `src/evcs_register.py` (standalone; run `python src/evcs_register.py`). No Phase 1-3.1 model input or output is changed.*

## 1. Source

| Item | Value |
|---|---|
| Publisher | Suruhanjaya Tenaga (Energy Commission), list of Electric Vehicle Charging System (EVCS) licensees |
| Access | Looker Studio dashboard `https://datastudio.google.com/s/jKQb-5TfRBg`, exported to CSV by the project owner on 23 Nov 2026 |
| Raw file | `data/raw/EVCS_license_holders.csv`, SHA256 `b08a94de85fa00d4cd2bbe3ac4c056a905d532dad0680886b4f051e5ab8ccf5d` |
| Coverage | **Peninsular Malaysia only**: 11 states plus WP Kuala Lumpur and Putrajaya. There are no Sabah, Sarawak or Labuan rows |
| Latest licence start date | 27 Oct 2026 |
| Fields | Licence number, licensee, site address, state, district, per-unit ratings (free text), AC/DC unit counts, installed kW, licence validity (10 years), AC/DC bays |
| **Not included** | Sessions, energy, utilisation, operating hours, pricing, whether the site is open to the public, and commissioning or decommissioning dates |
| Status | **Official, observed, context only.** It describes the licensed charging stock, not charging behaviour |

## 2. Cleaning (`outputs/tables/evcs_register_data_quality.csv`)

| Check | Result | Action |
|---|---|---|
| Rows in export | 2,531 (row numbers run to 2,535; 4 numbers are missing) | — |
| Exact duplicate rows | 18 | Removed, leaving 2,513 sites |
| Licence numbers shared by different rows | 25 numbers (50 rows) | Kept; flagged |
| Licence start dates | 3 have 2-digit years; 4 fall after the export date (2035, probably typos for 2025) | 2-digit years read as 20YY; future dates kept in totals but left out of the by-year table |
| Per-unit rating text vs AC/DC columns | 170 rows do not reproduce the counts | The AC/DC columns are used for counts; these rows are left out of the kW-rating distribution, which covers 4,544 of the 4,901 AC units |
| Licensee names | 326 raw names, 310 after removing punctuation differences | Normalised names used |

## 3. What the register shows (after de-duplication, `outputs/tables/evcs_register_summary.csv`)

| Measure | AC | DC |
|---|---|---|
| Charging units | **4,901** | **1,186** |
| Bays | 4,959 | 2,383 |
| Mean rated power per unit | **17.9 kW** | 103.8 kW |

- **Installed capacity:** 208 MW in total (the register's installed-kW column). The 4,544 AC units with parseable ratings add up to 81 MW.
- **AC unit ratings** (rated, not delivered):
  - about 22 kW: 64.1%
  - about 11 kW: 24.4%
  - 7.4 kW or less: 10.9%
- **Geography:** WP Kuala Lumpur/Putrajaya (1,816 AC units), Selangor (1,608) and Pulau Pinang (663) hold 83% of AC units.
- **Operators:**
  - 310 licensees hold licences.
  - The top five (ChargeHere, Charge N Go, EV Connection, Greenergy EV, Green EV Charge) hold 53% of AC units.
- **New AC units licensed per year** (by licence start date):

  | Year | New AC units |
  |---|---|
  | 2022 | 11 |
  | 2023 | 531 |
  | 2024 | 1,714 |
  | 2025 | 1,288 |
  | 2026 (to 27 Oct) | 1,349 |

  - This shows when licences were granted, not when chargers were commissioned. It is **not projected to 2030**.

**Site type (address-keyword heuristic, first match wins; indicative only):**

| Category | Share of AC units |
|---|---|
| Residential (condo, apartment, serviced, SOHO) | ≥31.7% |
| Mall / retail | ≥10.1% |
| Office / tower | 6.8% |
| Hotel / resort | 4.7% |
| Unclassified | 42.9% |

- Many unclassified addresses are hospitals, named residences, airports and car parks. The categorised shares are therefore lower bounds.

## 4. Relevance to this project

| Question | What the register can say | What it cannot say |
|---|---|---|
| Public AC charger power in the session library (7.4 / 11 kW, mean 8.84 kW) | Licensed AC units are mostly **22 kW rated** | Delivered power. AC charging is limited by the vehicle's onboard charger, so the library's 8.84 kW is a **delivered-power assumption**. It remains unverified, and the register does not contradict it |
| Is all licensed AC "public AC / destination" in the model's sense? | At least about 32% of AC units are at residential buildings, which partly overlaps the model's home/residential category | Which sites are publicly accessible |
| Phase 3.1 plausibility (`outputs/tables/evcs_register_vs_phase31_context.csv`) | Vehicles implied charging at the 2030 public AC maximum, against Oct-2026 licensed AC bays (4,959), at 20% xEV base: reference 0.99× weekday / 1.12× weekend; industry-informed 1.32× / 1.89×. At 30% xEV: up to 2.36× | Whether the 2030 network can serve this. The network size, bay availability and utilisation in 2030 are unknown, and the bays include residential and private sites |
| Representativeness of the industry observations (Phase 3.1) | Public AC is spread across 310 licensees, and malls are only part of it | The charging behaviour at any operator's sites |
| Replacement for the MEVnet figure (5,839 chargers incl. 1,971 DC, national, Mar 2026, secondary) | An **official, Peninsular** count to use instead of the secondary national figure | A like-for-like comparison: definitions differ (units vs bays vs MEVnet's unstated basis) |

## 5. Conclusion

- The register does **not** change any Phase 1-3.1 result or the Phase 3.1 recommendation: the industry-informed shape stays a sensitivity, and the EVI-Pro reference stays the main case.
- It does strengthen the plausibility context:
  - It is the best available official, Peninsular count of licensed AC charging units and bays.
  - It shows that licensed AC hardware is mainly 22 kW rated.
  - It shows that the industry-informed weekend peak would need about 1.9× the Oct-2026 licensed AC bays charging at the same moment (20% xEV). That is a demanding feature of the profile, unless the 2030 network is much larger.
- The register is not evidence of charging timing or energy.

# Passenger BEV Charging and Grid Adequacy in Peninsular Malaysia (2030)
## Work package 1 - passenger BEV registrations, stock, fleet exposure, annual charging electricity and 2030 hourly charging profiles

This package estimates annual new passenger battery-electric vehicle (BEV) registrations and the **active BEV stock** for Malaysia and Peninsular Malaysia, 2025-2030. The results are inputs for a later LEAP electricity-demand and peak-load model. It does not model charging profiles or grid adequacy.

### Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/fetch_data.py     # only needed if data/raw is empty (downloads from data.gov.my)
.venv/bin/python src/run_all.py        # runs Run 1 + Phase 1.5 + Phase 2 + Phase 3 + Phase 3.1 (~1 min); exits non-zero if any validation check fails
```

All assumptions live in **`src/config.py`**. Edit them there and re-run.

### Layout

```
data/raw/                      registrations_type_fuel.csv (JPJ via data.gov.my, to Oct 2026)
data/raw/jpj_car_transactions/ cars_2000..2026.parquet (transaction-level, incl. state of registration)
data/raw/policy_docs/          MITI speeches (PDF + extracted text)  - 20% and 30% xEV targets
data/raw/maa_docs/             MAA Dec-2025 press release and Market Review 2025 (PDF + text)
data/processed/                monthly and annual car registration series
src/                           config, audit, history, market, trend_models, policy, stock, geography,
                               validation, figures, reporting, run_all, fetch_data
outputs/tables/                all CSV outputs + BEV_forecast_summary.xlsx + LEAP input
outputs/figures/               fig01-fig08 (PNG, 200 dpi)
reports/                       research_methodology.md, final_report.md, data_audit.md (generated)
outputs/archive/run1_2026-11-22/ frozen copy of Run 1 tables, figures and reports + SHA-256 checksums (traceability)
outputs/archive/run2_2026-11-23/ frozen copy of Run 2 (Phase 1.5) outputs + checksums
outputs/archive/run3_2026-11-23/ frozen copy of Run 3 (Phase 2) outputs + checksums
outputs/archive/run4_2026-11-23/ frozen Run 4 (Phase 3) outputs + checksums of ALL tables (the two large hourly CSVs hashed, not copied)
data/raw/literature/           Phase 2 source documents (MIROS VKT abstract book and survey, GIZ/MOT stocktaking report)
notebook/                      (empty placeholder notebook supplied with the project - untouched)
```

Phase 1.5 modules: `src/exposure.py` (daily cohort engine: average stock, vehicle-years), `src/phase15.py` (pipeline),
`src/validation_exposure.py` (exposure tests), `src/figures_exposure.py` (fig09-fig12).
Phase 2 modules: `src/energy.py` (mileage x consumption x charging efficiency), `src/phase2.py` (pipeline),
`src/validation_energy.py` (energy tests), `src/figures_energy.py` (fig13-fig15).
Phase 3 modules: `src/hourly.py` (calendar, TNB ToU, charging-session engine, 8,760-h assembly), `src/phase3.py` (pipeline),
`src/validation_hourly.py` (18 required tests), `src/figures_hourly.py` (fig16-fig25).
Phase 3.1 modules: `src/destination.py` (Industry-informed public AC shapes, peak-region diagnostics, destination-session
plausibility library), `src/phase31.py` (pipeline; reuses Phase 3 objects via `phase3.LAST_CTX`), `src/validation_destination.py`
(15 required tests + plausibility), `src/figures_destination.py` (fig26-fig35).

### Main deliverables

| # | File | Content |
|---|------|---------|
| 1 | `outputs/tables/annual_registration_history.csv` | 2020-2025 full years, 2026 YTD (Jan-Oct) and 2026 estimate; counts, shares, YoY |
| 2 | `outputs/tables/bev_forecast_2025_2030.csv` | New BEV registrations: historical trend, 20% (primary), 30% (sensitivity) x low/base/high |
| 3 | `outputs/tables/bev_stock_2025_2030.csv` | National active BEV stock (cohort x survival), with cumulative registrations and retirements |
| 4 | `outputs/tables/peninsular_bev_stock_2025_2030.csv` | Peninsular stock (ESTIMATED), with the directly observed registration counts shown alongside |
| 5 | `outputs/tables/assumptions_and_sources.csv` | Assumption register and source list (URLs, retrieval date) |
| 6 | `outputs/tables/BEV_forecast_summary.xlsx` | Workbook: history, forecasts, stock, LEAP, assumptions, sources, validation |
| 7 | `outputs/figures/*.png` | History, shares, model comparison, forecasts, share paths, stock, Peninsular evidence |
| 8 | `reports/research_methodology.md` | Formulas, sources, model rationale, scenarios, uncertainty, limitations |
| - | `outputs/tables/leap_bev_stock_input.csv` | **LEAP table**: year, national/peninsular stock for the 20% and 30% cases (base) |
| - | `outputs/tables/leap_bev_stock_uncertainty.csv`, `leap_input_notes.md` | Low/base/high ranges and the notes that go with the LEAP table |
| - | `outputs/tables/validation_results.csv` | 24 automated checks (all PASS in the delivered run) |

### Phase 1.5 (Run 2) deliverables - fleet exposure

| File | Content |
|------|---------|
| `outputs/tables/leap_bev_exposure_input.csv` | **LEAP exposure table**: year, scenario (20pct_xev / 30pct_xev / historical_trend), case, geography, new_registrations, stock_beginning, stock_end, **stock_annual_average**, vehicle_years, retirements |
| `outputs/tables/leap_bev_exposure_data_dictionary.csv` | Definition and unit of every column |
| `outputs/tables/annual_bev_fleet_exposure_2025_2030.csv` | Detailed exposure table (vehicle-days, endpoint approximation, Run 1 31-Dec stock and difference) |
| `outputs/tables/fleet_exposure_sensitivity_2030.csv` | One-at-a-time sensitivity (factors A-G) + combined envelopes, 2030 |
| `outputs/tables/exposure_vs_run1_reconciliation.csv` | All timing variants vs Run 1 31-Dec stock |
| `outputs/tables/policy_path_review_2026_2030.csv`, `policy_path_review_summary.csv` | Review of the 20% / 30% / trend adoption paths |
| `outputs/tables/run2_change_log.csv`, `fleet_exposure_assumptions.csv` | Changes vs Run 1; Run 2 assumptions (A16-A19) |
| `outputs/tables/BEV_fleet_exposure_summary.xlsx` | Workbook of the Phase 1.5 tables |
| `outputs/figures/fig09-fig12` | New registrations; 31-Dec vs average stock; scenario comparison; tornado |
| `reports/fleet_exposure_methodology.md`, `fleet_exposure_validation.md` (generated), `phase_1_5_summary.md` | Method, test results, summary and next-stage checklist |

### Phase 2 (Run 3) deliverables - annual BEV charging electricity

| File | Content |
|------|---------|
| `outputs/tables/leap_bev_annual_energy_input.csv` | **LEAP energy table**: year, scenario, case, geography, vehicle_years, annual_km, kwh_per_100km, consumption_basis (battery), charging_efficiency, annual_grid_energy_gwh |
| `outputs/tables/bev_energy_assumptions_and_sources.csv` | Parameters (low/base/high, boundary, status) and the source register (URL, date, verification note) |
| `outputs/tables/bev_energy_sensitivity_2030.csv` | One-at-a-time sensitivity + combined envelopes, 2030 |
| `outputs/tables/bev_annual_energy_2025_2030_detail.csv` | Detail incl. battery energy, charging losses, kWh per vehicle-year |
| `outputs/tables/bev_model_consumption_mapping.csv`, `bev_consumption_observations.csv` | JPJ model mix -> EV Database values; Malaysian road-test observations |
| `outputs/tables/BEV_energy_summary.xlsx` | Workbook of the Phase 2 tables |
| `outputs/figures/fig13-fig15` | Energy by scenario; tornado; model-weighted vs generic consumption |
| `reports/phase_2_energy_demand_report.md` | Phase 2 report (results, recommended LEAP input, review items) |
| `reports/bev_mileage_literature_review.md`, `bev_efficiency_literature_review.md`, `bev_charging_efficiency_review.md` | Literature reviews |
| `reports/bev_energy_validation.md` | Generated validation results |

### Phase 3 (Run 4) deliverables - hourly charging profiles 2030 (Peninsular Malaysia)

| File | Content |
|------|---------|
| `outputs/tables/leap_bev_hourly_load_2030_aggregated.csv` | 8,760-h total BEV load (MW = MWh/h), MYT, for 3 adoption x 2 mileage (17,969 / 15,000 km) x 7 charging cases (unmanaged; ToU-managed staggered 25-100%; synchronized 50/100%) |
| `outputs/tables/leap_bev_hourly_load_2030.csv` | Same by charging location (residential, workplace, public AC, public DC) for unmanaged and staggered 50%/100% (~96 MB) |
| `outputs/tables/leap_bev_hourly_shapes_2030.csv`, `leap_bev_timeslice_576_2030.csv`, `leap_hourly_import_guide.md` | LEAP % of annual energy shapes; time-slice example; import notes |
| `outputs/tables/charging_management_sensitivity_2030.csv` | Peak, timing, ToU-peak energy, ramps for every case + location-mix and behaviour sensitivities |
| `outputs/tables/normalized_charging_profiles.csv`, `charging_location_mix_assumptions.csv`, `charging_profile_sources.csv` | 24-h shapes (model + source references), location mixes, source register |
| `reports/phase_3_hourly_charging_report.md` | Phase 3 report and answers; `charging_profile_literature_review.md`, `residential_workplace_source_comparison.md`, `malaysia_charging_behavior_assumptions.md`, `tnb_tou_management_methodology.md`, `phase_3_validation.md` (generated) |
| `outputs/figures/fig16-fig25` | Normalized profiles, weekday/week comparisons, location contributions, participation, 22:00 rebound, monthly energy, source comparison |

### Phase 3.1 deliverables - Malaysian-informed public AC (destination) profile, SENSITIVITY only

The Phase 3 reference (EVI-Pro Lite public AC shape) is unchanged and remains the main case. Phase 3.1 replaces **only** the public AC
series (15% of BEV energy, 192.7 GWh in 2030 at 20% xEV) with a shape built from qualitative peak timings reported by one industry
practitioner (anonymised; unverified). Residential, workplace and public DC series are bit-identical to Phase 3; all Phase 3 files are regenerated
byte-identical (checked against `outputs/archive/run4_2026-11-23/SHA256SUMS.txt`).

| File | Content |
|------|---------|
| `outputs/tables/public_ac_industry_informed_hourly.csv` | 8,760-h public AC load (MW): reference vs industry-informed variants (peak magnitude, width, weekend multiplier, occupancy basis) |
| `outputs/tables/public_ac_profile_comparison.csv` | Reference vs industry-informed (m = 1.0/1.25/1.5) x 3 adoption x 2 mileage x 5 charging cases: public AC and combined BEV maxima, timing, TNB-peak energy, ramps, overlap |
| `outputs/tables/phase_3_1_peak_sensitivity.csv` | 20% xEV: magnitude x width x weekend multiplier factorial; occupancy interpretation; public AC share 10-25%; location mixes; ToU participation |
| `outputs/tables/leap_bev_hourly_load_2030_industry_sensitivity.csv` | LEAP-ready 8,760-h load by location + total for the industry-informed sensitivity (~61 MB) |
| `outputs/tables/public_ac_plausibility_check.csv`, `public_ac_session_library_fit.csv` | Implied simultaneous charging vehicles, session-library fit (researcher-defined sessions) |
| `outputs/tables/phase_3_1_validation_results.csv`, `phase3_1_key_results.json` | Validation results; key numbers |
| `reports/phase_3_1_destination_charging_report.md` | Phase 3.1 report and recommendation; `industry_evidence_assessment.md`, `public_ac_profile_methodology.md`, `phase_3_1_validation.md` (generated) |
| `outputs/figures/fig26-fig35` | Existing vs industry-informed shapes, construction and plausibility, combined profiles, stacked days, magnitude and weekend sensitivity, managed cases |

### Context data - Energy Commission EVCS licence register (not a model input)

`.venv/bin/python src/evcs_register.py` (standalone; not part of `run_all.py`) cleans `data/raw/EVCS_license_holders.csv`. This is the
Energy Commission EVCS licensee dashboard, exported 23 Nov 2026: Peninsular only, licences to 27 Oct 2026. Main results:
2,513 sites, 4,901 AC and 1,186 DC units, mostly 22 kW-rated AC. The script compares the register with the Phase 3.1 plausibility check.
It has no session, energy or utilisation data, and nothing in Phases 1-3.1 uses it.

| File | Content |
|------|---------|
| `reports/evcs_licence_register_assessment.md` | Source, cleaning, summary, relevance and limits |
| `outputs/tables/evcs_register_summary.csv`, `evcs_register_data_quality.csv`, `evcs_register_key_results.json` | Totals by state, licence year, heuristic site type, licensee and AC rating; cleaning log |
| `outputs/tables/evcs_register_vs_phase31_context.csv` | Implied 2030 simultaneous public AC charging vehicles vs Oct-2026 licensed AC bays (context only) |
| `data/processed/evcs_register_clean.csv` | De-duplicated register with parsed fields and flags |

### Reproducibility
`.venv/bin/python src/run_all.py` regenerates every table, figure and generated validation report from `data/raw` and `src/config.py`
(random draws use fixed seeds). Each phase compares its predecessors' regenerated outputs with the SHA-256 lists in `outputs/archive/`
(Run 1-3 in Phase 3 requirement 18; Run 4 in Phase 3.1 requirement 12). Figures (PNG) are not hash-checked. Phase 3.1 runs last and
writes only new file names.

### Key definitions
- **Registrations ≠ sales.** JPJ counts registrations; MAA counts member-company sales (TIV).
- **Flow vs stock.** Annual BEV registrations are a flow. The active stock is computed from registration cohorts and survival curves, not by summing registrations.
- **Energy boundary.** Consumption is battery-side; grid energy = battery energy / charging efficiency (applied once), measured at the charger input. T&D losses are excluded.
- **31-Dec stock vs annual average stock.** `stock_end` is the fleet at year end. `stock_annual_average` (= vehicle-years) is the time-average fleet during the year. Use the average for annual energy demand.
- **xEV proxy** = BEV + JPJ `hybrid`. JPJ's hybrid code includes plug-in hybrids (PHEV) and cannot separate them from conventional hybrids (HEV).
- **Geography.** The policy targets and the JPJ data are national. Peninsular values are estimated from the JPJ state-of-registration field, which is a proxy and does not show where a vehicle is driven.

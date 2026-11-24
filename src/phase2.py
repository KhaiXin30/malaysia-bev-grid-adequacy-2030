"""Phase 2 (Run 3) pipeline - annual grid electricity for passenger BEV charging, 2025-2030.
Called from run_all.py after Run 1 and Phase 1.5; reads the Phase 1.5 LEAP exposure file.

Writes (outputs/tables): leap_bev_annual_energy_input.csv, bev_annual_energy_2025_2030_detail.csv,
bev_energy_sensitivity_2030.csv, bev_energy_assumptions_and_sources.csv, bev_model_consumption_mapping.csv,
bev_consumption_observations.csv, bev_energy_scenario_mix_check.csv, bev_energy_validation_results.csv,
phase2_key_results.json, BEV_energy_summary.xlsx; figures fig13-fig15; reports/bev_energy_validation.md.
"""
import json

import pandas as pd

import config as C
import energy as E
import figures_energy as FE
import reporting as R
import validation_energy as VE


def assumptions_and_sources(factors: dict, par_base: pd.DataFrame) -> pd.DataFrame:
    c30 = par_base.set_index("year").loc[C.FORECAST_END]
    P = [
        ("P01", "mileage", "Annual km per active BEV - low", C.ANNUAL_KM["low"], "km/vehicle-year", "derived: Malaysian all-car base x US BEV/CV ratio", "E01;E05",
         "vehicle (odometer distance)", f"17,969 x {C.BEV_CV_RATIO_LONG_RANGE:.3f} (Zhao et al. 2023: US Tesla BEV cars 8,786 vs CV cars 11,642 mi/yr). "
         "All-BEV ratio 0.615 and GIZ 2016 fleet-typical 15,000 km shown as separate sensitivities."),
        ("P02", "mileage", "Annual km per active BEV - base", C.ANNUAL_KM["base"], "km/vehicle-year", "observed Malaysian (all cars, 2022); BEV parity ASSUMED", "E01;E05",
         "vehicle (odometer distance)", "MIROS: 49.23 km/day x 365 = 17,969.23 km/yr, 2022 vehicle inspection records; not BEV-specific. Assumes BEV/ICE parity, which Zhao et al. (2023) call optimistic for the US."),
        ("P03", "mileage", "Annual km per active BEV - high", C.ANNUAL_KM["high"], "km/vehicle-year", "observed Malaysian survey (small, non-representative)", "E02;E03;E04",
         "vehicle (odometer distance)", "MIROS 2020 online survey motorcars 22,715 km (RSE 8.7%, n=63); new cars ~24,000 km in first year (2013 data)."),
        ("P04", "consumption", "Fleet-weighted EVDB consumption (2030, base mix)", round(c30["evdb_fleet_kwh_per_100km"], 3), "kWh/100 km", "derived (EVDB values x JPJ model mix x survival)", "E07;E08;E23",
         "battery", "Real-world EVDB 'Vehicle' consumption (battery energy for propulsion and on-board systems), moderate European climate incl. heating; 2030 value shown."),
        ("P05", "consumption", "Consumption factor - low", round(factors["low"], 4), "ratio", "derived from observations", "E09;E11;E13;E14;E15",
         "battery", "Median ratio of Malaysian/Singapore road-test readings to EVDB values of the same models (5 observations)."),
        ("P06", "consumption", "Consumption factor - base", round(factors["base"], 4), "ratio", "assumption (midpoint)", "E07;E09;E13;E14;E15",
         "battery", "Midpoint between Malaysian road-test level and EVDB real-world level; ~EVDB 'combined, mild (23 C, no A/C)' level."),
        ("P07", "consumption", "Consumption factor - high", factors["high"], "ratio", "derived (EVDB real-world level)", "E07;E08", "battery", "EVDB real-world headline value."),
        ("P08", "consumption", "Battery-side consumption 2030 - low / base / high",
         f"{factors['low'] * c30['evdb_fleet_kwh_per_100km']:.2f} / {factors['base'] * c30['evdb_fleet_kwh_per_100km']:.2f} / {c30['evdb_fleet_kwh_per_100km']:.2f}",
         "kWh/100 km", "derived", "E07;E09;E13;E14;E15", "battery", "Year-specific values in leap_bev_annual_energy_input.csv (fleet mix changes by year)."),
        ("P09", "mix", "Model mix of 2027-2030 registration cohorts", "base: 2025-Oct 2026 pooled; small: 2026 (Jan-Oct); large: 2025", "-",
         "assumption (observed alternatives)", "E23", "-", "Observed cohorts 2009-2026 use their actual JPJ model mix."),
        ("P10", "charging", "Charging efficiency - high-efficiency (used in LOW energy case)", C.CHARGING_EFFICIENCY["high"], "fraction", "evidence-based assumption", "E17;E20",
         "grid connection of charger -> battery", "ADAC 11 kW wallbox losses 5.1-7.0%; ORNL upper value 93%."),
        ("P11", "charging", "Charging efficiency - base", C.CHARGING_EFFICIENCY["base"], "fraction", "evidence-based assumption", "E17;E18;E20;E08",
         "grid connection of charger -> battery", "Argonne combined-cycle charging loss 10%; ADAC reduced-power AC 8-13% and DC 5-15%; EVDB WLTP vehicle/rated 0.90-0.92."),
        ("P12", "charging", "Charging efficiency - low-efficiency (used in HIGH energy case)", C.CHARGING_EFFICIENCY["low"], "fraction", "evidence-based assumption", "E17;E20;E21",
         "grid connection of charger -> battery", "ORNL lower value 84%; low-power AC and battery-cooling during DC charging; Apostolaki-Iosifidou 12-36% at low power."),
        ("P13", "boundary", "Transmission & distribution losses", "excluded", "-", "definition", "E19",
         "-", "To be handled consistently with the GSO/LEAP system boundary in Phase 3."),
        ("P14", "fleet", "Vehicle-years (annual-average active BEVs)", "Phase 1.5 output", "vehicle-years", "model output", "E22", "-",
         "20% primary, 30% sensitivity, trend comparison; low/base/high fleet cases."),
    ]
    rows = [dict(record_type="parameter", id=p[0], category=p[1], item=p[2], value=p[3], unit=p[4], status=p[5], source_ids=p[6],
                 boundary=p[7], note=p[8], url="", date="") for p in P]
    for sid, s in C.ENERGY_SOURCES.items():
        rows.append(dict(record_type="source", id=sid, category="source", item=s["name"], value="", unit="", status="", source_ids=sid,
                         boundary="", note=s["note"], url=s["url"], date=s["date"]))
    return pd.DataFrame(rows)


def run(af) -> int:
    print("[12] Phase 2: annual BEV charging electricity ...")
    ex = E.load_exposure()
    et = E.energy_table(af, ex)
    leap = E.leap_energy(et)
    leap.to_csv(C.TABLES / "leap_bev_annual_energy_input.csv", index=False)
    et.round(6).to_csv(C.TABLES / "bev_annual_energy_2025_2030_detail.csv", index=False)

    mapping = E.model_mapping_table()
    mapping.round(4).to_csv(C.TABLES / "bev_model_consumption_mapping.csv", index=False)
    obs = E.observation_table()
    obs.round(4).to_csv(C.TABLES / "bev_consumption_observations.csv", index=False)
    factors = E.consumption_factors()
    par_base = E.parameters(af, ex)
    mixchk = E.scenario_specific_mix_check(af, ex)
    mixchk.round(6).to_csv(C.TABLES / "bev_energy_scenario_mix_check.csv", index=False)

    sens = E.sensitivity_2030(af, ex)
    env = E.envelope_rows(et)
    sens_out = pd.concat([sens, env], ignore_index=True)
    sens_out.round(4).to_csv(C.TABLES / "bev_energy_sensitivity_2030.csv", index=False)

    ass = assumptions_and_sources(factors, par_base)
    ass.to_csv(C.TABLES / "bev_energy_assumptions_and_sources.csv", index=False)

    print("      figures ...")
    FE.fig_energy(et)
    FE.fig_tornado(sens, env)
    FE.fig_consumption(mapping, obs, par_base, factors)

    print("      validation ...")
    val = VE.run_checks(dict(energy=et, leap=leap, exposure=ex, assumptions=ass, mapping=mapping, sensitivity=sens))
    val.to_csv(C.TABLES / "bev_energy_validation_results.csv", index=False)
    VE.write_report(val, C.REPORTS / "bev_energy_validation.md")
    n_fail = int((val.result == "FAIL").sum())
    print(val[["group", "result", "check"]].to_string(index=False))

    readme = ["Phase 2 - annual grid electricity for passenger BEV charging, Malaysia and Peninsular Malaysia, 2025-2030.",
              "annual_grid_energy_gwh = vehicle_years x annual_km x kwh_per_100km / 100 / charging_efficiency / 1e6 (battery-side consumption).",
              "Grid side = input to the charger (home circuit or DC station); transmission & distribution losses EXCLUDED.",
              "Scenarios: 20pct_xev (PRIMARY), 30pct_xev (SENSITIVITY), historical_trend (COMPARISON). Cases are combined envelopes, NOT confidence intervals.",
              "Peninsular values are estimates (registration-state proxy)."]
    R.write_excel(C.TABLES / "BEV_energy_summary.xlsx",
                  {"LEAP_Energy_Input": leap, "Energy_Detail": et.round(6), "Sensitivity_2030": sens_out.round(4),
                   "Assumptions_Sources": ass, "Model_Mapping": mapping.round(4), "Observations": obs.round(4),
                   "Scenario_Mix_Check": mixchk.round(6), "Validation": val}, readme)

    def g(s, c, geo, y=C.FORECAST_END):
        return round(float(et[(et.scenario == s) & (et.case == c) & (et.geography == geo) & (et.year == y)]["annual_grid_energy_gwh"].iloc[0]), 1)

    key = {"energy_2030_gwh": {s: {geo: {c: g(s, c, geo) for c in ("low", "base", "high")} for geo in ("peninsular", "national")} for s in E.SCEN_ORDER},
           "consumption_factors": factors, "evdb_fleet_2030": float(par_base.set_index("year").loc[C.FORECAST_END, "evdb_fleet_kwh_per_100km"]),
           "base_kwh_per_100km_2030": float(par_base.set_index("year").loc[C.FORECAST_END, "kwh_per_100km"]),
           "validation_checks": len(val), "validation_failures": n_fail}
    (C.TABLES / "phase2_key_results.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key["energy_2030_gwh"], indent=1))
    return n_fail

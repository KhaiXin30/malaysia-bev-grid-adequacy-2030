# LEAP input notes - passenger BEV stock

File: `outputs/tables/leap_bev_stock_input.csv`  (uncertainty: `leap_bev_stock_uncertainty.csv`)

- **Quantity**: active passenger battery-electric cars (JPJ type `car`, fuel `electric`) on the road at **31 December** of each year.
- **Units**: vehicles (integer counts, no thousands separators).
- **Columns**: base case of each policy scenario; national = Malaysia; peninsular = Peninsular Malaysia (excludes Sabah, Sarawak, W.P. Labuan).
- **Status by year**: 2025 = observed registrations x assumed survival; 2026 = Jan-Oct observed + Nov-Dec estimated registrations x survival; 2027-2030 = projected.
- **Primary scenario**: 20% xEV share of new car registrations in 2030 (NETR target, applied to JPJ registrations - an assumption). 30% = sensitivity (MITI ministerial statement, 4 Feb 2026), not a confirmed replacement target.
- **Key assumptions**: total car registrations +1.0%/yr after 2026; BEV share of xEV held at the 2026 Jan-Oct level (56.2%); Weibull survival with an 18-year median life; Peninsular share of new BEVs 92% (from registration-state data, a proxy for location, not operating location).
- **Uncertainty**: low/high envelopes (market growth, BEV share within xEV, survival, Peninsular share moved together) are in the uncertainty file. Treat them as scenario ranges, not statistical confidence intervals.
- **Caveat**: the 2026 observed xEV share (14.4%) is already well above the 2025 level. Reaching 20% in 2030 implies BEV registrations grow much more slowly than in 2022-2026. The historical-trend case gives higher stock than the 20% case.

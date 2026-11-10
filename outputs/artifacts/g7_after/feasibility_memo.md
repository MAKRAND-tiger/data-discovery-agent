
# UC1 Feasibility Memo: Air quality and traffic (Valdena Civic Health Office)

As of 2026-10-15. Draft for the analytics lead and data owners. Not a profiling plan.

## 1. Executive summary

Overall verdict: **feasible with conditions.** No must need is unmet, but N2 (hourly traffic) is only partially met, and the prototype and production paths both depend on access and licence steps that are not yet done.

Facts that drive the verdict:

1. **N3 (must, temperature and humidity) has a candidate for both windows.** Open-Meteo covers both windows at hourly grain. It is a grid reanalysis, not station data. The location is an assumption (Milan coordinates), not a client-confirmed site. The upstream C3S licence has not been read. (api.open_meteo_archive)
2. **N1 (must, hourly NO2/PM2.5) is covered for the prototype window only by the UCI dataset.** It covers 2004-03-10 to 2005-04-04 exactly. It is single-site, from an unnamed city, uses a -200 missing-value code, and has a licence conflict (CC BY 4.0 vs research-only). (link.uci_360)
3. **N1 for production depends on the city's own station data, which is access-restricted.** The catalog shows coverage from 2023-01-01, open-ended. A wiki page says station VR-03 was switched off on 2024-06-30, and the catalog does not reflect this. No sample has been read. (internal.airq.station_readings)
4. **N2 (must, traffic) is the main constraint.** The only source is internal traffic counts, production window only. The counting basis changed on 2024-03-18, inside the production window. There is no counter-to-station mapping, so "near the monitoring stations" cannot be shown. The catalog does not mention the change. (internal.traffic.hourly_counts)
5. **Two sources are blocked or unusable.** The Chicago link is not reachable (host not allowlisted), has no licence, and covers a US city. Eurostat PM2.5 deaths (N6, could) has an unknown licence, and its record ends in 2023, so it is unmet for production. (link.data_open_air_chicago_hour_aggre_d4970b, link.europa_sdg_11_52_099aa6)

## 2. Need coverage

| need id | need | priority | status | best source(s) | gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations (NO2, PM2.5) | must | met with conditions | link.uci_360 (prototype); internal.airq.station_readings (production) | Prototype: single site, unidentified city, -200 sentinel, licence conflict. Production: EMU access not granted; VR-03 stopped 2024-06-30; no sample read. |
| N2 | Hourly vehicle traffic near monitoring stations | must | partially met | internal.traffic.hourly_counts (production) | Access not granted; 2024-03-18 counting change with no adjustment method; no counter-to-station mapping; DST convention undocumented. |
| N3 | Hourly temperature and humidity | must | met with conditions | api.open_meteo_archive (both windows); link.uci_360 (prototype, single site) | Valdena location unconfirmed (Milan assumed); C3S licence not read; Legal sign-off open; full completeness not checked. |
| N4 | Daily respiratory clinic visits by district | should | met with conditions | internal.clinic.resp_visits_daily (production) | Access not verified; no district code list; visit_date meaning unknown; zero-day convention unknown; no small-cell disclosure rule. |
| N5 | Patient-level clinic visit records | could | unmet | none | Clinic policy excludes patient-level records from surveillance analysis. |
| N6 | National yearly context: PM2.5 deaths | could | partially met | link.europa_sdg_11_52_099aa6 | Covers 2005 only for the prototype window (about 24% of the window by the rule); no production coverage (ends 2023-12-31); licence unknown. |

## 3. Source assessments

Order: feasible (none), with conditions, then not feasible.

### api.open_meteo_archive: feasible with conditions
- **What it is (catalog summary):** Gridded reanalysis of hourly 2 m temperature and relative humidity, served by a JSON REST API. Probes returned 72 hourly rows for 3-day ranges. Covers 2004-03-10 to 2025-12-31 (record temporal field). Refresh cadence unknown.
- **Verdict:** Covers N3 for both windows at no agreement cost, subject to conditions.
- **Key flags:**
  - COV-GEO-MISMATCH (major): probe used Milan coordinates (45.46 N, 9.19 E). It returned grid cell 45.448 N, 9.169 E, 138 m. The client has not confirmed Valdena's location. The register default (Lisbon) must not be used.
  - LIC-MIXED (major): operator says CC BY 4.0; upstream C3S and DWD/ECMWF terms also apply. C3S licence linked but not read; commercial use unknown.
  - LIC-ATTRIBUTION (minor): attribution text required on outputs.
  - FRS-METADATA-DATE-MISLEADING (minor): metadata_last_updated 2026-11-10 is after the as-of date.
- **Conditions:** confirm coordinates; read and record upstream licences; Legal sign-off for production; confirm UTC convention; run full-range completeness check; read the docs page on variables and archive bounds.

### internal.airq.station_readings: feasible with conditions
- **What it is (catalog summary):** Hourly NO2 and PM2.5 (ug/m3) from city monitoring stations, keyed by station code and UTC hour start. Catalog coverage from 2023-01-01, open-ended, hourly refresh, about 4.2 million rows. Owner: Environment Monitoring Unit.
- **Verdict:** Only internal N1 source and the only production-window N1 source. Conditional on access and the VR-03 correction.
- **Key flags:**
  - ACC-RESTRICTED (major): auth required; access by request; no delivery date recorded.
  - GOV-CATALOG-WIKI-CONFLICT (major): wiki station_network (last edited 2024-07-01) says VR-03 was switched off 2024-06-30. The catalog shows the network as active with open-ended coverage and does not mention the stop. Catalog exported 2026-10-14.
- **Conditions:** EMU access and delivery date; confirm status of VR-03 and all stations after 2024-07-01; treat VR-03 as ending 2024-06-30; obtain missing-value coding, validation flag and station coordinates or district mapping; verify the "continuous from 2023-01-01" claim; sample a small extract after access.

### internal.clinic.resp_visits_daily: feasible with conditions
- **What it is (catalog summary):** Warehouse table of respiratory visit counts per day and district, owned by Clinical Analytics. Catalog says no patient identifiers. Coverage from 2022-01-01, open-ended, daily refresh, about 40,000 rows. The clinic data policy allows only this aggregated table for surveillance.
- **Verdict:** Meets N4 (should) if access is approved and the schema is documented.
- **Key flags:**
  - ACC-RESTRICTED (major): auth required; access not verified by the profiler.
  - DQ-UNDOCUMENTED-SCHEMA (major): no district code list; no statement whether visit_date is registration or clinical date; no zero-day convention.
  - INT-REPRESENTATIVENESS (major, disclosure): no small-cell suppression rule documented.
- **Conditions:** Clinical Analytics approval, used only for daily district counts; Data Protection Office confirms suppression rule before any district-day output leaves analysis; district code list, visit_date meaning, zero-day storage; confirm refresh completeness and clinic opening/closure effects.

### internal.traffic.hourly_counts: feasible with conditions (partially meets N2)
- **What it is (catalog summary):** Hourly vehicle counts per road counter, with counter code, local-time hour start and count. Described as counters near monitoring stations. Coverage from 2021-01-01 (catalog), open-ended, hourly refresh, about 15 million rows. Owner: Mobility Office.
- **Verdict:** Only N2 candidate. Partially met until mapping and counting-change adjustment are resolved.
- **Key flags:**
  - ACC-RESTRICTED (major): auth required; no delivery date recorded.
  - GOV-CATALOG-WIKI-CONFLICT (major): wiki counter_replacement_2024 (edited 2024-04-02) says counters were replaced 2024-03-18; counts were per direction before and combined after; do not compare across the change without adjustment. Catalog has no note.
  - INT-NO-JOIN-KEY (major): columns are counter_id, ts_local, vehicles only; no coordinates, direction or station mapping.
  - DQ-DST-ARTEFACTS (minor): ts_local has no UTC offset or DST rule documented.
- **Conditions:** access for 2024-01-01 to 2025-12-31; check the 2021 start claim; counter-to-station mapping and coordinates; adjustment method for the 2024-03-18 change, or post-change-only modelling; DST handling; whether outages are zero or missing; update catalog.

### link.uci_360: feasible with conditions (prototype only)
- **What it is (dataset record):** UCI ML Repository 360 "Air Quality". Hourly records from a metal-oxide multisensor at road level in one unnamed Italian city, with reference analyser values (CO, NMHC, benzene, NOx, NO2) plus T, RH, AH. Covers 2004-03-10 to 2005-04-04 per the file. Metadata last updated 2024-03-10. Licence CC BY 4.0 in the record.
- **Verdict:** The only usable public hourly NO2 source for the prototype. Method-building only, not city-representative.
- **Key flags:**
  - DQ-METADATA-CONTRADICTION (major): metadata says no missing values; documentation says -200 marks missing. Sample: NO2(GT) 1,642 cells = -200 (about 17.5%); NMHC(GT) 8,443 cells (about 90%).
  - LIC-NONCOMMERCIAL (major): UCI notes say research use only and commercial use excluded, which conflicts with CC BY 4.0.
  - INT-REPRESENTATIVENESS (major): single road-level site; fit to northern Italy unknown.
  - COV-GEO-MISMATCH (major): city not identified.
  - FRS-STALE (major): ends 2005; retained because the prototype window is 2004–2005 by design.
  - LIC-ATTRIBUTION (minor): attribution required (De Vito et al., 2008; DOI 10.24432/C59K5F).
- **Conditions:** recode -200 to missing; resolve licence conflict with the UCI owner or client legal team; reconcile end date (documentation February 2005 vs file 2005-04-04) and row count (9,358 declared vs 9,357 rows); use reference-analyser columns only; state single-site and unidentified-city limits in any output.

### link.europa_sdg_11_52_099aa6: feasible with conditions (context only)
- **What it is (dataset record):** Eurostat sdg_11_52, annual national count and rate of premature deaths linked to PM2.5 for Italy. 36 cells (2 units x 18 years), no missing cells declared. Covers 2005-01-01 to 2023-12-31. Last updated 2025-12-09 per response header.
- **Verdict:** Meets N6 (could) only as prototyping or context. The licence is unknown.
- **Key flags:**
  - LIC-UNKNOWN (blocker for use): no licence found; Eurostat copyright page redirected to a sign-in page. Register says context-only, not production, under an unknown licence.
  - COV-PARTIAL-WINDOW (major): prototype covered only for 2005; production 0%.
  - DQ-METADATA-CONTRADICTION (major): "no missing values" declared, but quality notes say sentinel absence is not verified at value level. Values not sampled.
- **Conditions:** obtain and record licence before any use; no production use; sample values for sentinels; explain the missing 2006 year; confirm the rate denominator.

### link.data_open_air_chicago_hour_aggre_d4970b: not feasible
- **What it is:** Human-supplied link to an hourly air-quality aggregation on catalog.data.gov. The URL slug indicates Chicago (US).
- **Verdict:** Not feasible. The host is not allowlisted, so no metadata, licence, schema or sample was read. No alternate route was attempted, per guardrail rules.
- **Key flags:**
  - ACC-UNREACHABLE (blocker): DOMAIN_NOT_ALLOWLISTED for catalog.data.gov.
  - LIC-UNKNOWN (blocker): no licence established.
  - COV-GEO-MISMATCH (major): US city; use case geography is Italy.
- **Conditions:** none usable. Reconsider only if the project owner allowlists the host, the licence is established, and the geography is shown to be relevant (unlikely for this use case).

## 4. Red-flag register

| source_id | code | severity | evidence | raised by |
|---|---|---|---|---|
| api.open_meteo_archive | COV-GEO-MISMATCH | major | Milan coordinates used; grid cell 45.448 N, 9.169 E; client location unconfirmed | judgement |
| api.open_meteo_archive | LIC-MIXED | major | Upstream C3S and DWD/ECMWF terms; C3S not read; commercial use unknown | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | CC BY 4.0; attribution required | rule |
| api.open_meteo_archive | FRS-METADATA-DATE-MISLEADING | minor | metadata_last_updated 2026-11-10, after as-of date | judgement |
| internal.airq.station_readings | ACC-RESTRICTED | major | Auth required; no delivery date | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Wiki: VR-03 off 2024-06-30; catalog shows active, open-ended | judgement |
| internal.clinic.resp_visits_daily | ACC-RESTRICTED | major | Auth required; access not verified | rule |
| internal.clinic.resp_visits_daily | DQ-UNDOCUMENTED-SCHEMA | major | No district code list; visit_date meaning and zero-day convention unknown | judgement |
| internal.clinic.resp_visits_daily | INT-REPRESENTATIVENESS | major | No small-cell suppression rule; disclosure risk | judgement |
| internal.traffic.hourly_counts | ACC-RESTRICTED | major | Auth required; no delivery date | rule |
| internal.traffic.hourly_counts | GOV-CATALOG-WIKI-CONFLICT | major | Wiki: counting basis change 2024-03-18; catalog silent | judgement |
| internal.traffic.hourly_counts | INT-NO-JOIN-KEY | major | No counter coordinates or station mapping | judgement |
| internal.traffic.hourly_counts | DQ-DST-ARTEFACTS | minor | Local time, no UTC offset or DST rule | judgement |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | Metadata says no missing; docs say -200 is missing; NO2 about 17.5% | rule |
| link.uci_360 | FRS-STALE | major | Data ends 2005-04-04; retained by design | rule |
| link.uci_360 | LIC-NONCOMMERCIAL | major | Research-only vs CC BY 4.0 conflict | judgement |
| link.uci_360 | INT-REPRESENTATIVENESS | major | Single road-level site | judgement |
| link.uci_360 | COV-GEO-MISMATCH | major | City unidentified | judgement |
| link.uci_360 | LIC-ATTRIBUTION | minor | Attribution text required | rule |
| link.europa_sdg_11_52_099aa6 | LIC-UNKNOWN | blocker | No licence found; sign-in redirect | rule |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | 2005 only for prototype; 0% production | rule |
| link.europa_sdg_11_52_099aa6 | DQ-METADATA-CONTRADICTION | major | No-missing declared; sentinel absence unverified | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | DOMAIN_NOT_ALLOWLISTED | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | No licence read | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | US city (Chicago) | judgement |

Note: the discovery run's generated_at (2026-11-10) is also later than the as-of date (2026-10-15). Treat run timestamps as unreliable until checked.

## 5. Conditions and owners

| condition | source(s) | who can resolve it | blocking which need |
|---|---|---|---|
| Confirm Valdena coordinates; re-probe and record grid cell; record the Milan assumption in decisions.md until then | api.open_meteo_archive | Client (Health Office) | N3 (both windows) |
| Read and record upstream C3S/DWD/ECMWF licence; confirm commercial status; Legal sign-off for production | api.open_meteo_archive | Client Legal; data provider terms | N3 production |
| Grant EMU access for 2024–2025; provide delivery date | internal.airq.station_readings | Environment Monitoring Unit | N1 production |
| Confirm VR-03 and other station status after 2024-07-01; correct catalog | internal.airq.station_readings | Environment Monitoring Unit | N1 production (and N2/N4 joins) |
| Provide missing-value coding, validation flag, station coordinates or district mapping | internal.airq.station_readings | Environment Monitoring Unit | N1 production; N2 and N4 joins |
| Grant Mobility Office access for 2024–2025 | internal.traffic.hourly_counts | Mobility Office | N2 |
| Provide counter-to-station mapping and coordinates | internal.traffic.hourly_counts | Mobility Office | N2 (partially met) |
| Provide method for 2024-03-18 counting change, or accept post-change-only modelling | internal.traffic.hourly_counts | Mobility Office with analytics lead decision | N2 |
| Confirm DST handling of ts_local and zero vs missing outages | internal.traffic.hourly_counts | Mobility Office | N2 |
| Approve access to daily district counts | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Confirm small-cell suppression rule | internal.clinic.resp_visits_daily | Data Protection Office | N4 (output release) |
| Provide district code list, visit_date meaning, zero-day convention | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Resolve UCI licence conflict (CC BY 4.0 vs research-only) | link.uci_360 | UCI owner or client Legal | N1 prototype (and N3 prototype via UCI) |
| Recode -200 and record missing shares | link.uci_360 | Analytics team (internal step) | N1 prototype |
| Establish Eurostat licence before any use | link.europa_sdg_11_52_099aa6 | Client Legal; Eurostat terms | N6 |
| Allowlist host and establish licence (not recommended) | link.data_open_air_chicago_hour_aggre_d4970b | Project owner | None (not needed; N1 prototype covered by UCI) |

## 6. Recommended next steps

1. **Raise access requests now.** Environment Monitoring Unit (station readings, 2024–2025). Mobility Office (traffic counts, 2024–2025). Clinical Analytics (daily district counts). Ask each for a delivery date, since none is recorded.
2. **Ask the Health Office to confirm Valdena's coordinates** for the Open-Meteo probe. Until confirmed, record Milan as the assumption in decisions.md. Do not use Lisbon.
3. **Raise a Legal request** for the C3S upstream licence (Open-Meteo), the UCI licence conflict, and the Eurostat licence. Each needs an answer before use.
4. **Ask the Environment Monitoring Unit to confirm the VR-03 stop** and correct the catalog. Ask the Mobility Office to add the 2024-03-18 change to the catalog.
5. **Decide the N2 approach** before profiling traffic: adjust for the counting change, restrict to post-change data, or accept a break-aware approach. Also decide whether N2 can be partially met without a station mapping.
6. **Decide the prototype path:** use the UCI dataset for N1 and N3 prototype, with the single-site and licence caveats stated. Do not use the Chicago link.
7. **Profile first, once access is granted:** (a) the station extract, to check content against the catalog and the VR-03 end date; (b) the Open-Meteo full range, for completeness and timezone; (c) the UCI file after recoding -200; (d) the traffic counts around 2024-03-18, to see the basis change before any modelling; (e) the clinic table, to confirm zero-day storage and visit_date meaning.
8. **Do not request patient-level records (N5).** The policy excludes them; N5 stays unmet.

## 7. Open questions for the human reviewer

1. Which city or coordinates should represent Valdena? The probe used Milan, which is an assumption.
2. Is the UCI prototype dataset acceptable for an internal method-building step given the licence conflict, or should Legal rule on it first?
3. Does the Health Office accept post-2024-03-18 traffic data only, or does it want a counting-change adjustment?
4. Will the Health Office accept a traffic-proximity claim without a counter-to-station mapping? If not, N2 stays partially met.
5. Does Legal accept the Open-Meteo reanalysis for production, given the unread C3S terms?
6. Who in the Data Protection Office decides the small-cell suppression rule for district counts?
7. Is the Eurostat N6 context worth pursuing given the unknown licence and the 2005-only prototype coverage?
8. Should the VR-03 stop be treated as the station being permanently retired, and is the rest of the network still running?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-10T17:21:09Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Blocker flags on sources not rejected (resolve or justify):**

- link.europa_sdg_11_52_099aa6: LIC-UNKNOWN

**Open questions:**

1. Which city or coordinates should represent Valdena? The Open-Meteo probe used Milan coordinates, which is an assumption and must be recorded in decisions.md.
2. Is the UCI prototype dataset acceptable for internal method-building given the licence conflict (CC BY 4.0 vs research-only), or should Legal rule on it first?
3. Does the Health Office accept post-2024-03-18 traffic data only, or does it want a counting-change adjustment method?
4. Will the Health Office accept a traffic-proximity claim without a counter-to-station mapping? If not, N2 stays partially met.
5. Does Legal accept the Open-Meteo reanalysis for production, given the C3S and DWD/ECMWF upstream terms have not been read?
6. Who in the Data Protection Office sets the small-cell suppression rule for district-day counts?
7. Is the Eurostat PM2.5 context (N6) worth pursuing given the unknown licence and 2005-only prototype coverage?
8. Is station VR-03 permanently retired, and are the other stations still running after 2024-07-01?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop

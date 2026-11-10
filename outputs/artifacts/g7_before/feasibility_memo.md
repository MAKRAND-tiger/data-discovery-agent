
# UC1 Feasibility Memo: Air quality and traffic (Valdena Civic Health Office)

As-of date: 2026-10-15. Overall verdict: **not feasible as it stands.** Two must-needs are unmet for the prototype window and one must-need (N3) is unmet for both windows. The production air-quality, traffic and clinic data are usable only after named access grants and documentation fixes.

## 1. Executive summary

The overall verdict is **not feasible as it stands**. Two must-needs are unmet and the production sources all carry open conditions.

Facts that drive the verdict:

1. **N3 (hourly temperature and humidity) is unmet for both windows.** The only full-coverage source, Open-Meteo, has a free tier licensed for non-commercial use only (terms page). The UCI file's licence conflicts with its own "commercial purposes fully excluded" note.
2. **The prototype cannot run on the sources assessed.** N1 prototype (hourly pollutants, 2004–2005) depends on the UCI file. Its licence is blocked. The Chicago link is unreachable (DOMAIN_NOT_ALLOWLISTED) and outside Italy. No other source covers 2004–2005 hourly pollutants.
3. **Production air quality is feasible with conditions.** The city station readings (internal.airq.station_readings) cover 2024–2025 hourly. Access is still pending, with no delivery date. The catalog has no station coordinates, so stations cannot be linked to traffic or districts. Station VR-03 reportedly stopped on 2024-06-30, which the catalog does not show.
4. **Traffic (N2) is only partially met.** The Mobility Office source covers production. No counter-to-station mapping exists. Counters were replaced on 2024-03-18, changing from per-direction to combined counts, and the catalog does not record this.
5. **Clinic counts (N4) are met with conditions.** The clinic data policy allows only daily district counts. The district code list, the visit_date meaning and zero-day handling are undocumented. Patient-level data (N5) is excluded by policy, so N5 has no source.

## 2. Need coverage

| Need | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations (prototype and production) | must | partially met | internal.airq.station_readings (production); link.uci_360 (prototype, blocked) | Prototype: no usable source. UCI blocked by licence conflict. Chicago unreachable and out of geography. Production: access pending, VR-03 gap, no station coordinates, QA status unknown. |
| N2 | Hourly vehicle traffic near monitoring stations (production) | must | partially met | internal.traffic.hourly_counts | No counter-to-station mapping, so "near the stations" is unverified. 2024-03-18 counting change undocumented in catalog. Access pending. |
| N3 | Hourly temperature and humidity (prototype and production) | must | **unmet** | none. Open-Meteo blocked (non-commercial free tier). UCI blocked (licence). | No feasible hourly source for either window. |
| N4 | Daily respiratory visits by district (production) | should | met with conditions | internal.clinic.resp_visits_daily | Access via Clinical Analytics. District code list, visit_date meaning, suppression rule and zero-day handling unknown. |
| N5 | Patient-level clinic visit records | could | **unmet** | none | Clinic data policy forbids patient-level records leaving clinic systems for this analysis. |
| N6 | National yearly PM2.5 deaths (context) | could | partially met | link.europa_sdg_11_52_099aa6 | Covers 2005 only within prototype. No 2024–2025 values. Licence unknown. |

## 3. Source assessments

### Feasible (no source is fully feasible without conditions)

None.

### Feasible with conditions

**internal.airq.station_readings** (City station readings, hourly, Environment Monitoring Unit)
- What it is: hourly NO2 and PM2.5 from city stations, timestamps in UTC. Catalog: about 4.2 million rows, coverage from 2023-01-01 with no end date, hourly refresh, last refreshed 2026-10-14. Owner: Environment Monitoring Unit. Licence: internal.
- Verdict: feasible with conditions. Serves N1 production only.
- Key flags:
  - ACC-RESTRICTED (major): auth required; request via the Environment Monitoring Unit; "No delivery date recorded".
  - GOV-CATALOG-WIKI-CONFLICT (major): wiki station_network (last edited 2024-07-01) says VR-03 was switched off on 2024-06-30, while the catalog still shows the network as active. VR-03 status after 2024-07-01 is unverified.
  - INT-NO-JOIN-KEY (major): no station coordinates or location fields.
  - DQ-UNDOCUMENTED-SCHEMA (minor): no validated/provisional QA flag; "QA status of readings is unknown"; no completeness figures.
- Conditions: access grant and delivery date; VR-03 status and a gap rule (treat as missing, not zero); station list with coordinates and QA flag; confirm whether any readings exist before 2023-01-01 (this source does not cover prototype).

**internal.clinic.resp_visits_daily** (Respiratory visits, daily by district, Clinical Analytics)
- What it is: daily counts per district (visit_date, district, visit_count), no patient identifiers. Catalog: coverage from 2022-01-01, daily refresh, last refreshed 2026-10-14, about 40,000 rows. Owner: Clinical Analytics. Licence: internal.
- Verdict: feasible with conditions. Serves N4 for production.
- Key flags:
  - ACC-RESTRICTED (major): auth required; request via Clinical Analytics; reachability not tested.
  - GOV-PURPOSE-LIMITATION (major): clinic data policy (Data Protection Office, last edited 2025-02-01) allows only daily district counts for this purpose.
  - INT-NO-JOIN-KEY (major): district codes are free text or undocumented; no district-to-station key.
  - DQ-UNDOCUMENTED-SCHEMA (major): unknown visit_date meaning, district code list, small-cell suppression rule, zero-day handling.
- Conditions: access from Clinical Analytics with requester approval; use daily district counts only; document code list, date meaning, suppression and zero-day handling. Treat zero days as missing until confirmed.

**internal.traffic.hourly_counts** (Road traffic counts, hourly, Mobility Office)
- What it is: hourly vehicle counts per counter (counter_id, ts_local, vehicles), described as counters near monitoring stations. Catalog: coverage from 2021-01-01, hourly refresh, last refreshed 2026-10-12, about 15 million rows. Owner: Mobility Office. Licence: internal.
- Verdict: feasible with conditions. Partially serves N2 for production.
- Key flags:
  - ACC-RESTRICTED (major): auth required; request via Mobility Office; no delivery date.
  - GOV-CATALOG-WIKI-CONFLICT (major): wiki counter_replacement_2024 (last edited 2024-04-02) says counters changed on 2024-03-18 from per-direction to combined counts. The wiki warns not to compare across the change without adjustment. The catalog has no note.
  - INT-NO-JOIN-KEY (major): no counter list, coordinates, counter-to-station mapping, direction field or outage flag.
  - DQ-DST-ARTEFACTS (minor): ts_local is local time with DST handling undocumented; autumn duplicates or ambiguity noted.
- Conditions: access and delivery date; counter list and counter-to-station mapping; documented adjustment for the 2024-03-18 change; confirm time zone and DST, convert to UTC; clarify how outages are recorded.

**link.europa_sdg_11_52_099aa6** (Eurostat SDG 11.5.2, premature deaths from PM2.5, Italy, annual)
- What it is: annual national series, one country (IT), 18 time points from 2005 to 2023 with 2006 absent, two units (NR number, RT rate). Temporal end 2023-12-31. Licence and owner: null (not stated in the record).
- Verdict: feasible with conditions. Context only, for N6 (could).
- Key flags:
  - LIC-UNKNOWN (blocker, rule): licence name null; copyright page redirected to EU Login; agreement_status "not_in_register".
  - COV-PARTIAL-WINDOW (major, rule): prototype coverage 24% (2005 only); production 0%.
  - FRS-METADATA-DATE-MISLEADING (minor, judgement): updated 2025-12-09 is the release date; data ends 2023.
  - DQ-UNDOCUMENTED-SCHEMA (minor, judgement): RT denominator not stated; model not documented; 2006 absent.
- Conditions: obtain and record the reuse licence and attribution before any use; do not compare RT with other sources until the denominator is confirmed; treat 2006 as absent; not for production use.

### Not feasible

**api.open_meteo_archive** (Open-Meteo Historical Weather API, hourly reanalysis-based archive)
- What it is: hourly temperature_2m and relative_humidity_2m for any lat/lon, from a grid model archive (ERA5, ERA5-Land, ECMWF IFS from 2017 per the docs). Probes used an assumed Milan point (45.46 N, 9.19 E; snapped to 45.448 N, 9.169 E). Probes returned data for 2004-03-10..12 and 2025-12-29..31. Owner: Open-Meteo.com. Licence: CC BY 4.0 for data; free API restricted to non-commercial use per the terms page.
- Verdict: not feasible. N3 is unmet for both windows.
- Key flags:
  - LIC-NONCOMMERCIAL (blocker, rule): terms page says free API is for non-commercial use only. The register approves production, but its own note says Legal sign-off is unresolved. The register's "not_required_open_data" status conflicts with the terms page.
  - COV-GEO-MISMATCH (major, judgement): grid-point model values, not station observations; the Milan location is unconfirmed and Valdena is not named anywhere.
  - LIC-MIXED (major, rule): underlying reanalysis is Copernicus C3S; its licence was not read.
  - DQ-UNDOCUMENTED-SCHEMA (minor, judgement): field list taken from probe responses, not a schema; model for 2004 and 2025 not stated.
- Conditions to revisit: a Legal ruling or a paid subscription that covers the warning use, recorded in the register before any request. Confirm coordinates with the Environment Monitoring Unit. Record which model produced each window.

**link.uci_360** (UCI 360 Air Quality, gas multisensor with reference analyser, Italian city, 2004–2005)
- What it is: 9,357 hourly rows (page states 9,358), 2004-03-10 to 2005-04-04, the whole file. Reference NO2, NOx, CO, benzene, NMHC plus T, RH, AH. No traffic. Licence stated as CC BY 4.0. Owner: null. City not named.
- Verdict: not feasible. N1 prototype and N3 prototype are unmet.
- Key flags:
  - LIC-NONCOMMERCIAL (blocker, judgement): UCI note says "used exclusively for research purposes. Commercial purposes are fully excluded," which conflicts with CC BY 4.0. No authority has resolved it.
  - DQ-METADATA-CONTRADICTION (major, rule): declared has_missing_values "no", but documentation says missing values are tagged -200; the sample confirms -200 in the reference and T/RH/AH columns.
  - DQ-SENTINEL-VALUES (major, judgement): -200 used as missing marker (NMHC(GT) about 90%, NO2(GT) about 17.5%, T/RH/AH 366 rows each). Recoding is required.
  - COV-GEO-MISMATCH (major, judgement): city not named; cannot be confirmed as Valdena.
  - FRS-STALE (major, rule): data ends 2005; historical by design.
  - LIC-ATTRIBUTION (minor, rule): CC BY attribution required (De Vito et al., 2008).
- Conditions to revisit: Legal resolves the licence conflict. If commercial use is confirmed, N1 and N3 prototype can be re-assessed. Recode -200 before aggregation. Confirm the city with the data owner or Legal.

**link.data_open_air_chicago_hour_aggre_d4970b** (Open Air Chicago hourly aggregations, data.gov listing)
- What it is: a candidate listing for hourly sensor data, title and slug indicating Chicago, US. Contents, coverage, licence and owner are unverified.
- Verdict: not feasible.
- Key flags:
  - ACC-UNREACHABLE (blocker, rule): catalog.data.gov not allowlisted (DOMAIN_NOT_ALLOWLISTED). The guardrail is recorded as a finding; no alternative route was tried.
  - LIC-UNKNOWN (blocker, rule): no licence readable.
  - COV-GEO-MISMATCH (major, judgement): US geography; UC1 is Italy only.
- Conditions: none usable. Would need a platform allowlist decision, a licence, a geography check, and still would not cover Valdena.

## 4. Red-flag register

| Source | Code | Severity | Evidence (short) | Raised by |
|---|---|---|---|---|
| api.open_meteo_archive | LIC-NONCOMMERCIAL | blocker | Terms: free API non-commercial only; register note says Legal sign-off unresolved | rule |
| api.open_meteo_archive | LIC-MIXED | major | Mixed sources; Copernicus C3S licence not read | rule |
| api.open_meteo_archive | COV-GEO-MISMATCH | major | Grid-point values; Milan location unconfirmed | judgement |
| api.open_meteo_archive | DQ-UNDOCUMENTED-SCHEMA | minor | Schema from probe shape; model for 2004/2025 not stated | judgement |
| internal.airq.station_readings | ACC-RESTRICTED | major | Auth required; no delivery date | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Wiki: VR-03 off since 2024-06-30; catalog shows active | judgement |
| internal.airq.station_readings | INT-NO-JOIN-KEY | major | No station coordinates | judgement |
| internal.airq.station_readings | DQ-UNDOCUMENTED-SCHEMA | minor | No QA flag; no completeness figures | judgement |
| internal.clinic.resp_visits_daily | ACC-RESTRICTED | major | Auth required; reachability not tested | rule |
| internal.clinic.resp_visits_daily | GOV-PURPOSE-LIMITATION | major | Policy: daily district counts only | judgement |
| internal.clinic.resp_visits_daily | INT-NO-JOIN-KEY | major | No district-to-station key | judgement |
| internal.clinic.resp_visits_daily | DQ-UNDOCUMENTED-SCHEMA | major | Date meaning, code list, suppression, zero days unknown | judgement |
| internal.traffic.hourly_counts | ACC-RESTRICTED | major | Auth required; no delivery date | rule |
| internal.traffic.hourly_counts | GOV-CATALOG-WIKI-CONFLICT | major | 2024-03-18 per-direction to combined change not in catalog | judgement |
| internal.traffic.hourly_counts | INT-NO-JOIN-KEY | major | No counter-to-station mapping or coordinates | judgement |
| internal.traffic.hourly_counts | DQ-DST-ARTEFACTS | minor | Local time; DST undocumented | judgement |
| link.europa_sdg_11_52_099aa6 | LIC-UNKNOWN | blocker | Licence null; not in register | rule |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | Prototype 24% (2005 only); production 0% | rule |
| link.europa_sdg_11_52_099aa6 | FRS-METADATA-DATE-MISLEADING | minor | 2025 date is release date; data ends 2023 | judgement |
| link.europa_sdg_11_52_099aa6 | DQ-UNDOCUMENTED-SCHEMA | minor | RT denominator not stated; 2006 absent | judgement |
| link.uci_360 | LIC-NONCOMMERCIAL | blocker | "Commercial purposes fully excluded" conflicts with CC BY 4.0 | judgement |
| link.uci_360 | LIC-ATTRIBUTION | minor | CC BY 4.0 attribution required | rule |
| link.uci_360 | FRS-STALE | major | Data ends 2005-04-04 | rule |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | has_missing_values "no" vs documented -200 tag | rule |
| link.uci_360 | DQ-SENTINEL-VALUES | major | -200 across reference columns; recode needed | judgement |
| link.uci_360 | COV-GEO-MISMATCH | major | City not named | judgement |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | DOMAIN_NOT_ALLOWLISTED | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | No licence readable | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | US geography | judgement |

## 5. Conditions and owners

Owners below come from the catalog and wiki. The discovery record did not name who can resolve each condition, so those fields are marked "not recorded".

| Condition | Source(s) | Who can resolve it | Blocking which need |
|---|---|---|---|
| Access grant and delivery date | internal.airq.station_readings | Environment Monitoring Unit (owner) | N1 production |
| VR-03 status after 2024-06-30 and gap rule | internal.airq.station_readings | Environment Monitoring Unit (not recorded) | N1 production |
| Station list with coordinates and QA flag | internal.airq.station_readings | Environment Monitoring Unit (not recorded) | N1 production; linkage |
| Confirm readings before 2023-01-01 (for prototype) | internal.airq.station_readings | Environment Monitoring Unit (not recorded) | N1 prototype (no alternative source) |
| Access grant and requester approval | internal.clinic.resp_visits_daily | Clinical Analytics (owner) | N4 |
| District code list, visit_date meaning, suppression rule, zero-day handling | internal.clinic.resp_visits_daily | Clinical Analytics (not recorded) | N4 |
| Keep to daily district counts; no patient fields | internal.clinic.resp_visits_daily | Data Protection Office (policy); clinic | N4 (N5 excluded) |
| Access grant and delivery date | internal.traffic.hourly_counts | Mobility Office (owner) | N2 |
| Counter list and counter-to-station mapping | internal.traffic.hourly_counts | Mobility Office (not recorded) | N2 |
| Adjustment for 2024-03-18 counting change | internal.traffic.hourly_counts | Mobility Office (not recorded) | N2 |
| Time zone and DST handling of ts_local | internal.traffic.hourly_counts | Mobility Office (not recorded) | N2 join to UTC |
| Eurostat reuse licence and attribution | link.europa_sdg_11_52_099aa6 | Not recorded (Eurostat terms; internal legal) | N6 |
| Licence ruling, or paid subscription, for Open-Meteo warning use | api.open_meteo_archive | Legal (register note); Open-Meteo (paid plan) | N3 (both windows) |
| Confirm Valdena/station coordinates | api.open_meteo_archive; link.uci_360 | Environment Monitoring Unit; data owner or Legal | N3; N1 prototype geography |
| Resolve UCI licence conflict | link.uci_360 | Legal (not recorded) | N1 prototype; N3 prototype |
| Recode -200 sentinel | link.uci_360 | Analyst, after licence ruling | N1 and N3 prototype |
| Platform allowlist, licence, geography check | link.data_open_air_chicago_hour_aggre_d4970b | Not recorded | N1 prototype (not pursued) |

## 6. Recommended next steps

1. **Raise access requests now** to the Environment Monitoring Unit (station readings), Clinical Analytics (daily district counts) and the Mobility Office (hourly counts). Ask each for a delivery date, as none is recorded. Request only the grain and fields the needs require.
2. **Ask Legal for a ruling** on two items: (a) the UCI licence conflict (CC BY 4.0 vs "commercial purposes fully excluded"); (b) whether the Open-Meteo free tier can be used for the warning use, or whether a paid plan is needed. Record the outcome in the register before any further request.
3. **Decide the Valdena location.** No source names the city. Confirm the station and clinic geography with the Environment Monitoring Unit. Until then, the Milan probe point is an assumption only. Record it in decisions.md.
4. **Decide the prototype route.** On current evidence, N1 and N3 prototype are unmet. Decide whether the prototype should wait for the Legal ruling or be dropped in favour of production-only work.
5. **Decide the VR-03 gap rule** (treat as missing, not zero) and the handling of zero-visit days (treat as missing until confirmed).
6. **Obtain the licence and attribution for the Eurostat series** before any use. Use it only as national context for N6.
7. **Once the access gate is passed, profile first:**
   - Station readings: VR-03 coverage after 2024-06-30; completeness per station; QA flag availability; station list.
   - Traffic: counter list; counter-to-station mapping; the 2024-03-18 change (count levels before and after); DST and outage handling.
   - Clinic: visit_date meaning; district code list; suppression; zero-day handling.
   Do not start any joins until the keys exist.

## 7. Open questions for the human reviewer

Also returned in `open_questions_for_human`.

1. Does the Health Office accept a not-feasible prototype, or should the prototype be dropped or deferred until the Legal ruling? The brief asked whether it can be prototyped now; the answer on current evidence is no.
2. Which city is Valdena's proxy location? The Milan point is a probe assumption, and no source names the client's city. Who confirms the coordinates?
3. Will Legal rule on the UCI licence conflict and on Open-Meteo's non-commercial free tier? Who is the Legal contact?
4. Is a paid Open-Meteo subscription within budget and approved for the warning use?
5. Should the Eurostat series be treated as feasible with conditions when its licence is unknown? The rule treats LIC-UNKNOWN as a blocker, but the verdict is accepted only because N6 is a could-priority context need. Is that the intended standard, and is it consistent with the Open-Meteo treatment?
6. Is the Environment Monitoring Unit's record that VR-03 stopped on 2024-06-30 current? Does the catalog need correcting?
7. Does the Mobility Office have a counter-to-station mapping, and how was the 2024-03-18 change handled?
8. Does Clinical Analytics confirm the district code list, the visit_date meaning, the suppression rule and zero-day storage?
9. Does the clinic data policy (Data Protection Office) allow daily district counts to be joined to station and traffic data at the same date grain?
10. Is the 2004–2005 prototype needed at all if the production window is the only feasible one?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-10T17:00:38Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Blocker flags on sources not rejected (resolve or justify):**

- link.europa_sdg_11_52_099aa6: LIC-UNKNOWN

**Open questions:**

1. Does the Health Office accept a not-feasible prototype, or should the prototype be dropped or deferred until the Legal ruling? On current evidence N1 and N3 prototype are unmet.
2. Which city is Valdena's proxy location? The Milan point is a probe assumption, and no source names the client's city. Who confirms the coordinates?
3. Will Legal rule on the UCI licence conflict and on whether Open-Meteo's non-commercial free tier can be used for the warning use? Who is the Legal contact?
4. Is a paid Open-Meteo subscription within budget and approved for the warning use?
5. Should the Eurostat series be feasible with conditions while its licence is unknown? The rule treats LIC-UNKNOWN as a blocker, but the verdict is accepted only because N6 is a could-priority context need. Is that consistent with the Open-Meteo treatment?
6. Is the Environment Monitoring Unit's record that VR-03 stopped on 2024-06-30 current? Does the catalog need correcting?
7. Does the Mobility Office have a counter-to-station mapping, and how was the 2024-03-18 counting change handled?
8. Does Clinical Analytics confirm the district code list, the visit_date meaning, the suppression rule and how zero-visit days are stored?
9. Does the clinic data policy (Data Protection Office) allow daily district counts to be joined to station and traffic data at the same date grain?
10. Is the 2004-2005 prototype still needed if the production window is the only feasible one?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop

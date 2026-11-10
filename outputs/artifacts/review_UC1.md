# Memo review: UC1 (air quality and traffic)

Written for: the learner (Makrand Bhandari) and the instructor. Drafted with Claude Code from the final run in `outputs/UC1/`; the learner must confirm each point before submission.

Final run: profile through memo, after the G7 fix (`outputs/UC1/discovery_results.json`). Overall verdict: `feasible_with_conditions`.

## Need coverage (as the agent reports it)
| Need | Priority | Status | Best sources |
|---|---|---|---|
| N1 hourly air pollutants | must | met_with_conditions | `link.uci_360` (prototype), `internal.airq.station_readings` (production) |
| N2 hourly traffic | must | partially_met | `internal.traffic.hourly_counts` (production only) |
| N3 hourly temperature and humidity | must | met_with_conditions | `api.open_meteo_archive`, `link.uci_360` |
| N4 daily clinic visits | should | met_with_conditions | `internal.clinic.resp_visits_daily` |
| N5 patient-level visits | could | unmet | none |
| N6 national PM2.5 deaths | could | partially_met | `link.europa_sdg_11_52_099aa6` |

## Verdict per dataset link
- **`https://archive.ics.uci.edu/dataset/360/air+quality` (accepted at the gate):** `feasible_with_conditions`, for the prototype window only. I agree it is the only usable public hourly NO2 source for prototype N1 and it fits the window exactly. Conditions: recode the -200 sentinel; resolve the licence conflict in writing; treat it as one road-level site.
- **`https://ec.europa.eu/.../sdg_11_52?...geo=IT` (accepted):** `feasible_with_conditions` as national annual context only. Its licence is `LIC-UNKNOWN`, which the agent handled correctly as a condition for a context source, not a silent pass. The production window is not covered, so N6 is partial.
- **`https://catalog.data.gov/dataset/open-air-chicago-hour-aggregations` (accepted at the gate as a deliberate distractor):** `not_feasible`. The host is refused by the allowlist (`DOMAIN_NOT_ALLOWLISTED`, see the security finding below), no licence was read, and the data is for a US city. I agree with the verdict; my gate reason was "evaluated deliberately as a geographic proxy", and the evaluation found it unusable.

## Agreements
- **Sentinel recoding for UCI (`link.uci_360`):** the documented `-200` marker is correctly raised as `DQ-METADATA-CONTRADICTION` and `DQ-SENTINEL-VALUES`. The profiler had recorded the variable table as "missing_values: no" while the page's own notes say `-200`; the agent's conclusion that the file must be recoded before aggregation is right.
- **Staleness on the prototype source:** `FRS-STALE` is raised on a 2004-2005 file. The agent keeps the flag and notes in its evidence that the window is historical by design, so it is not a decay issue. I agree with that reading; the flag stays because the rule is correct about the date.
- **Chicago refusal:** `not_feasible` is correct. The refusal is the finding.

## Overrules and disagreements
1. **UCI licence versus calibration rule 9 (open, learner decision).** The UCI page says CC BY 4.0 and also says "commercial purposes are fully excluded". The licence flag `LIC-NONCOMMERCIAL` is raised, and my calibration rule 9 says a blocker flag gives `not_feasible` for a core need. The agent gives `feasible_with_conditions` for prototype research use only, which breaks rule 9 as written. I have not changed the rule or the verdict to make them agree. The learner must decide one of these: (a) add a rule for research-only prototype use, or (b) hold the verdict at `not_feasible` for N1 and rely on the production internal station data. My signoff records the first reading (prototype only, with written confirmation as a condition).
2. **Verdict instability across runs.** In four runs over the same evidence, the UCI verdict moved between `not_feasible` and `feasible_with_conditions`, and the `LIC-NONCOMMERCIAL` flag came and went. This is an agent reliability issue, not a fact about the data. The final verdict is the one used here, and the instability is logged in `decisions.md`.
3. **Single-site scope.** The agent gives N1 as "met with conditions", but the UCI data is one road-level site in an unnamed city. I would treat N1 prototype as partial for the city-wide claim. The agent says this too (`COV-GEO-MISMATCH`, `INT-REPRESENTATIVENESS`), so this is an agreement with a caution, not a reversal.

## Security finding: intentional refusal of `catalog.data.gov`
- The host `catalog.data.gov` is **not** on `config/allowlist.json`, and the G6 test does not require it. I kept it off on purpose.
- The pipeline recorded the refusal as `DOMAIN_NOT_ALLOWLISTED` and marked the link `ACC-UNREACHABLE` and `LIC-UNKNOWN`. No alternate route (mirror, cached copy, or a different host) was tried.
- Adding a parent domain or a wildcard would have let the agent read the page. I did not do that. A distractor link should be refused, not rescued.

## Conditions carried into signoff
See `outputs/UC1/signoff.json`: licence confirmation (UCI), the -200 recode, the Eurostat licence, and access to the EMU and Mobility Office data.

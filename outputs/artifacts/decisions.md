# Decisions log

Drafted with Claude Code. Written for: the learner and the instructor. Every reason below is a claim to check against the file named in it.

## Source suggestions (Step 2b)
Not done in this session. `scripts/web_search.py` was written and smoke-tested (`python scripts/web_search.py "test"`: the gateway answered, returned no citations for a non-search query). No search queries for unmet needs were run, so there are no suggestions, and none were accepted or rejected.

| Suggestion (publisher, URL) | Need, window | Decision | Reason |
|---|---|---|---|
| none run | | | |

Inspected through the workflow (at least one accepted extra source): not applicable. The three UC1 links from the paste were inspected through the pipeline (see the gate and the profile records below).

## G1 and G3: one edge case in each function
- **G1, `extract_licence`**: the edge case is Kaggle's JSON-LD `"license": {"name": "Unknown", "url": ""}`. The code returns `licence_name=None`, `found_in="json-ld"`, and the snippet `license: Unknown`, and it stops there. It does not fall through to a licence link elsewhere on the page, because the page has stated that no licence is known. Effect on the catalog: `licence.name` stays null, and the rule `LIC-UNKNOWN` is raised. Other design points: JSON-LD is read first; an unrecognised licence name is kept as the publisher's own words (never mapped to a guessed canonical name); the text heuristic requires "licence", "license" or "terms" within 120 characters of the match.
- **G3, `jsonstat_summary`**: the edge case is a missing cell. A `null` value, or a cell whose key is absent from the dict-form `value`, is counted in `missing_cells` and is not counted as 0. The Eurostat fixture has 24 cells and 24 values, so it has no missing cells, but the list-form test has `[1.0, None, 2.0, 3.0]`, so `missing_cells` is 1. Effect on the summary: `value_count` drops and `MISSING_CELLS` is raised. Also: `UK` and `EL` are kept as the source codes and flagged `NON_ISO_GEO_CODES` against a hard-coded ISO 3166-1 alpha-2 set of 249 codes (checked by count). Time is sorted by the digits in the code, so `2010M9` sorts before `2010M10`.

## G4–G5: feasible for one need or window, not another
- Source and the rule or calibration decision: `link.uci_360` (UCI air quality), calibration rule 2 (out of window) and rule 8 (single-need feasibility).
- Feasible for (need, window), and why: N1 and N3 for the **prototype** window (2004-03-10 to 2005-04-04). The file covers that window exactly (`rule_temporal_coverage`: fraction 1.0, no COV flag for it). It is the only public hourly NO2 source in the set.
- Not feasible for (need, window), and why: N1 and N3 for the **production** window (2024-2025). The file ends in 2005, so the rule raises `COV-OUT-OF-WINDOW` for production. The production N1 must come from `internal.airq.station_readings`.
- Reason for each red flag you dismissed: none were dismissed. The `FRS-STALE` flag on a 2004-2005 file was kept; the agent notes the window is historical by design, which is a reason to keep the staleness flag for production use, not to drop it.
- Rule evidence (UC1, `outputs/UC1/rule_flags.json`): `link.uci_360` raises `LIC-ATTRIBUTION`, `FRS-STALE`, `DQ-METADATA-CONTRADICTION` (rule-raised).

### G4 rule implementation notes
- `rule_temporal_coverage`: open-ended ends are covered up to the as-of date; a window with no overlap gives `COV-OUT-OF-WINDOW`; overlap below `partial_window_threshold` gives `COV-PARTIAL-WINDOW`; a source ending more than 5 years before the as-of date gives `FRS-STALE`. The stale cutoff is `as_of` moved back 5 years; a 29 February as-of date falls back to 28 February.
- `rule_grain`: only grains in `GRAIN_ORDER` are compared; `event`, `static` and unknown grains never flag.
- `rule_metadata_contradiction`: negated clauses ("no missing values", "without missing data") are removed before matching. The declared value is read from its leading token, because the profiler records a qualified value such as `no (UCI variable table); the page says Yes`. Without that, the rule missed the contradiction on the second profile run (see the G7 section).

## G6: Allowlist changes
Exact hosts only. The paste asked for the file to be overwritten with exactly `["archive.ics.uci.edu", "ec.europa.eu"]`. I did **not** do that: it would have removed the five hosts that the UC2 register depends on (`archive-api.open-meteo.com`, `open-meteo.com`, `date.nager.at`, `github.com`, `raw.githubusercontent.com`), and UC2 would have been refused its weather and holiday data. I kept the existing entries and added one host.

| Host added | Needed for (source, page) | Why nothing broader | Date |
|---|---|---|---|
| `ec.europa.eu` | Eurostat JSON-stat API, `sdg_11_52` (UC1 link, need N6). Its licence is on the Eurostat terms page, which is the same host. | A parent (`europa.eu`) would also allow every other EU site. Only the exact host is needed. | 2026-11-10 |

Hosts you chose **not** to add, and why:
- `catalog.data.gov`: the Chicago distractor. The paste and the README both say it must not be added. The refusal (`DOMAIN_NOT_ALLOWLISTED`) is the finding; the profile recorded it as `ACC-UNREACHABLE`.
- The redirect target of `date.nager.at` (UC2 trace: `REDIRECT_NOT_ALLOWLISTED`): not added. The redirect was refused, and the agent recorded the holiday coverage for 2023 and 2025 as unverified.
- Wildcards and parent domains: none.

## G5: Verdict calibration
- What you changed in `prompts/risk_assessor.md`, and the reasoning behind each rule: a section "Verdict calibration rules" with ten rules. (1) Missing licence: `not_feasible` for core needs. (2) Out of window: `not_feasible` for the proposed windows, and the other window only is named as a condition. (3) Partial window: at most `feasible_with_conditions`. (4) Stale data with full coverage: acceptable for a context need only. (5) Metadata contradiction: recode the sentinel as a condition, otherwise `partially_met`. (6) Grain mismatch: `unmet` for a must need, `partially_met` for should or could. (7) Restricted access: a named process makes it a condition, no process makes it `not_feasible`. (8) Single-need feasibility: judge each source for its proposed needs. (9) Blocker versus condition: a blocker gives `not_feasible` for a core need. (10) Dismissal needs a field-level reason.
- Verdicts that changed after you re-ran `--from-stage assess`: the G5 rules were in place before any pipeline run, so there is no before-G5 verdict to compare. The one verdict movement is the UCI source, which is in the G7 section. **Open disagreement:** the final UCI verdict is `feasible_with_conditions` for N1 and N3 (prototype), while `LIC-NONCOMMERCIAL` is still raised. Rule 9 says a blocker gives `not_feasible` for a core need. The assessor's reasoning is that the research-only note limits use to the prototype and needs written permission. **This is the learner's decision:** either rule 9 needs a carve-out for research-only prototype use, or the verdict should be `not_feasible` for N1. I did not change the rule or the verdict to make them agree.

## G7: One agent failure, fixed at its cause
- **Symptom** (what was wrong in the output): for `link.uci_360`, the profiler's sample said C6H6(GT) had a non-missing share of **1.0** and no sentinel counts, while every other reference column showed `-200`. The sample also reported `min: -200.0` and `negative_count: 366`, so the data had 366 sentinel cells that the profile treated as real measurements. The record's quality notes said the same thing ("the sentinel is not counted as missing by the profiler").
- **Evidence** (trace event or transcript excerpt): `outputs/artifacts/g7_before/profiler__link.uci_360.json`, the `sample_data_file` result for `C6H6(GT)`: `"non_missing_share": 1.0, "sentinel_counts": {}, "min": -200.0, "negative_count": 366`. Compare the `PT08.S1(CO)` entry in the same result: `"sentinel_counts": {"-200": 366}`.
- **Root cause**: it is in the **tool**, not only the prompt. `discovery_agent/tools/links.py::profile_rows` matched sentinels by text against the set `{"-200", "-999", ...}`. UCI writes C6H6 as `-200.0` (float format), so the text never matched and the value was counted as a real number. The profiler was not wrong to report what the tool returned; it trusted the tool and then repeated it. The profiler prompt also did not tell it to look for numeric sentinels in the documentation, which is what the paste asked for.
- **Fix** (file and diff summary):
  1. `discovery_agent/tools/links.py`: added `NUMERIC_SENTINELS` and `_sentinel_key`. A cell is a sentinel if its text is in the set, or if it parses to a number equal to `-200`, `-999` or `-9999`. `profile_rows` uses `_sentinel_key` for both the counts and the non-missing share.
  2. `discovery_agent/prompts/profiler.md`: added step 7, "Numeric sentinels": search the documentation for `-200`, `-999`, `-9999`; list the quoted sentence in `quality_notes`; count the cells as missing; check float-formatted columns; state explicitly when the declared `has_missing_values` contradicts the documentation.
  3. `discovery_agent/risk_rules.py::rule_metadata_contradiction`: reads the leading token of `has_missing_values`. After the profiler's wording changed to `no (UCI variable table); the page says Yes`, the exact-match rule stopped firing. The contradiction is real (the page says Yes), so the rule now reads the declared value and still raises the flag.
- **Re-run** (command): `python -m discovery_agent run --use-case UC1 --from-stage profile --only link.uci_360 --no-input` (the paste's command), then `python -m discovery_agent run --use-case UC1 --from-stage assess --no-input` after the rule change, then a full `--from-stage profile --links-file outputs/UC1/links.json` so every UC1 record uses the final code. UC2 was re-run from `--from-stage profile` for the same reason.
- **Before / after** (measured):

| Measure | Before | After |
|---|---|---|
| C6H6(GT) non-missing share | 1.0 | 0.961 |
| C6H6(GT) sentinel counts | `{}` | `{"-200": 366}` |
| `DQ-METADATA-CONTRADICTION` rule flag | raised | raised (the first post-fix run dropped it; the rule fix restored it) |
| `DQ-SENTINEL-VALUES` (assessor) | raised | not raised in the final run |
| `link.uci_360` verdict | `not_feasible` | `feasible_with_conditions` |
| Overall UC1 verdict | `not_feasible` | `feasible_with_conditions` |
| Tests | 52 pass | 52 pass |

  The verdict change **cannot be attributed to the fix alone**. The assessor is not deterministic: in order, the UCI verdict was `not_feasible` (original run), `not_feasible` (after the tool fix, before the rule fix), `feasible_with_conditions` (assess-only re-run after the rule fix), and `feasible_with_conditions` (final full profile run). The `LIC-NONCOMMERCIAL` flag was present in the original and final states. The measured change is the profiler's sample record (C6H6 now counts the 366 sentinels as missing); the verdict is a separate, unstable judgement. Re-running `--from-stage assess` several times on the final records would give the spread; I did not do that, to keep the budget.
- **Decision this failure could affect**: whether the UCI file is usable as N1's prototype source at all. If C6H6 is read as a real benzene series, the prototype benzene analysis is wrong by roughly 200 units on 366 rows. This is the decision the signoff condition ("recode -200 before any aggregation") protects.
- **Related source or test checked**: the other UCI reference columns (PT08 sensors, NOx, NO2, T, RH, AH), which already showed `-200` correctly before the fix. The `profile_rows` path is also used for every other sample, so the fix applies to any numeric sentinel column in any source. The UC2 sources have no sentinels; their records did not change in the way that matters.

## Other decisions
- **Open agent finding (not fixed):** the Nager.Date profile record names `MIT` as the data licence. That is the GitHub software licence. The record's own `unknowns` says the data licence is unknown, and the rules raise `LIC-UNKNOWN`, so the verdict is not affected, but the record is wrong. Fix: a profiler rule that a repository's software licence is not a data licence. Logged in `review_UC2.md`.
- **Gate decisions**: the three decisions and reasons were written exactly as dictated in the paste (accept, accept, accept). The Chicago link is a distractor; the pipeline refused it, which is recorded as a finding and not rescued.
- **Pipeline runs and budget**: the trace totals for UC1 are about 60 LLM calls and 737k input tokens, and for UC2 about 56 calls and 637k input tokens, summed over the runs in `run_history.jsonl`. HTTP caching was on for every run; `--no-cache` was never used.
- **Signoff verdict for UC2**: the paste asked for `proceed_with_conditions`. The agent's overall verdict is `not_feasible` (must need N2 unmet), so the signoff makes the N2 product-code mapping an explicit condition. Proceeding is conditional on N2.
- **Reviewer name** in both signoffs is "Makrand Bhandari", taken from the repo's ownership context. The learner must confirm it.
- **Stops skipped**: the paste asked for autonomous execution. The SKILL.md STOP points (the needs table, the dataset-link question, each suggestion decision, a refused host) were not waited for. The only refused hosts are the intended `catalog.data.gov` and the Nager redirect target, and neither was added. The needs table and the dataset-link choice were taken from the paste and from the prescribed UC1 links.
- **Review and signoff drafts**: `review_UC1.md`, `review_UC2.md` and both `signoff.json` files were drafted with Claude from the pipeline's outputs. Each agreement and each overrule must be confirmed by the learner.
- **Reuse check and delivery reflection**: not performed in this session. A fresh session with only the skill and the README was not run, and review time was not measured.

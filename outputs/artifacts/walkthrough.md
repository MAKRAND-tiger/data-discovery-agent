# Walkthrough

Written for: the instructor's 15-minute walkthrough. Drafted with Claude Code from files in this repo; the learner must be able to explain each point in their own words.

## 1. One implemented rule: `rule_metadata_contradiction` (`discovery_agent/risk_rules.py`)
- **What it does:** raises `DQ-METADATA-CONTRADICTION` when the declared `has_missing_values` says "no" and the documentation or quality notes describe missing data or sentinels.
- **Why it is designed this way:** negated phrases are stripped first, so "Data set has no missing values" does not trigger it (test `r321` in `tests/test_learner_gaps.py`). The declared value is read from its leading token, because the profiler records qualified values such as `no (UCI variable table); the page says Yes`.
- **Evidence it fires:** `outputs/UC1/rule_flags.json`, `link.uci_360`: `DQ-METADATA-CONTRADICTION` (rule-raised, `raised_by: rule:rule_metadata_contradiction`).
- **Why it matters:** it stopped the agent from treating the UCI variable table's "missing_values: no" as true, when the page's notes say `-200` marks missing values.

## 2. One traced claim: from `signoff.json` to a record field
- **Claim** (`outputs/UC1/signoff.json`, `traced_conclusion`): the UCI air-quality file is a prototype source whose coverage ends on **2005-04-04**.
- **Source ID:** `link.uci_360`. **Record field:** `temporal.end`.
- **Record value** (`outputs/UC1/records/link.uci_360.json`): `"temporal": {"start": "2004-03-10", "end": "2005-04-04", "grain": "hourly", ...}`.
- **Where the value comes from:** the profiler took the end from the sample, which is the whole file (`sample_is_whole_file: true`, 9,357 rows), and the UCI notes say "March 2004 to February 2005". The record's quality notes call that prose "out of date", so the file's own dates are used.
- **What could change it:** if the file is not the whole dataset, or the notes are right and the file ends in late February 2005, the coverage changes materially. The prototype window is 391 days (2004-03-10 to 2005-04-04); ending on 2005-02-28 covers 356 of them, about 91%. That is below the 0.95 `partial_window_threshold`, so `rule_temporal_coverage` would raise `COV-PARTIAL-WINDOW`, and the N1 prototype verdict would need to be revisited.

## 3. One rejected source: `catalog.data.gov`, the Chicago distractor
- **Decision:** accepted at the gate on purpose, as a distractor (`outputs/UC1/gate_decisions.json`). The pipeline then refused it.
- **Why it is rejected in the outcome:** the host is not on the allowlist (`DOMAIN_NOT_ALLOWLISTED`), so no licence and no page content were read. The record marks it `ACC-UNREACHABLE` and `LIC-UNKNOWN`, and the verdict is `not_feasible` (`outputs/UC1/discovery_results.json`).
- **Why the refusal is the finding:** a parent domain or a wildcard would have made the page readable. Adding it would have been a G6 failure. Nothing was added (`config/allowlist.json` has no catalog host).
- **Also:** the agent's rationale says the source is a US city outside the IT geography, which would have been `not_feasible` on geography alone.

## 4. One memo conclusion: UC2 is `not_feasible` because must need N2 is unmet
- **Conclusion** (`outputs/UC2/feasibility_memo.md`, and `overall_rationale` in `outputs/UC2/discovery_results.json`): N2 (the product-code mapping before and after 2024-04-01) is unmet, and an unmet must need makes the overall verdict `not_feasible`.
- **Evidence:** `internal.sales.products` is `not_feasible` because the catalog and wiki hold only the current codes (`outputs/UC2/records/internal.sales.products.json`, `schema.fields`; quality note from `internal/UC2_valdena_gelato/wiki/product_codes_2024.md`). No mapping table exists in the internal estate.
- **Where I agree:** the verdict follows the calibration rule (rule 9 and the must-need rule in `risk_assessor.md`).
- **What would change it:** a mapping table for the pre-2024 codes. N2 would become `met_with_conditions`, and the overall verdict could move to `feasible_with_conditions`.
- **Where I did not agree without a condition:** the paste asked for a signoff of `proceed_with_conditions`. I recorded the N2 mapping as the condition, so proceeding depends on it.

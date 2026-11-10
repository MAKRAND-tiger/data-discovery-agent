# Memo review: UC2 (ice-cream sales, weather and holidays)

Written for: the learner (Makrand Bhandari) and the instructor. Drafted with Claude Code from the final run in `outputs/UC2/`; the learner must confirm each point before submission.

Final run: profile through memo, on the final code. Overall verdict: `not_feasible`, because must need N2 is unmet.

UC2 has no dataset links (`links_expected: false`), so every source here comes from the internal catalog or the register APIs.

## Need coverage (as the agent reports it)
| Need | Priority | Status | Best sources |
|---|---|---|---|
| N1 daily sales by product | must | met_with_conditions | `internal.sales.daily_by_product` |
| N2 product-code mapping before and after 2024 | must | **unmet** | none (`internal.sales.products` is not_feasible) |
| N3 daily maximum temperature | must | met_with_conditions | `api.open_meteo_archive` |
| N4 public holidays | should | partially_met | `api.nager_public_holidays` |
| N5 opening days and events | should | partially_met | `internal.store.calendar` |

## Verdict per source
- `internal.sales.products`: `not_feasible`. I agree. N2 is a must need for the history window; the table cannot supply the pre-2024-04-01 codes, the name match is not unique, and there is no mapping table.
- `internal.sales.daily_by_product`: `feasible_with_conditions` for N1. Restricted access, a code break at 2024, and a till gap to handle.
- `api.open_meteo_archive`: `feasible_with_conditions` for N3. CC BY 4.0 with attribution, mixed upstream terms, and shop coordinates to confirm.
- `api.nager_public_holidays`: `feasible_with_conditions` for N4. Licence unknown and owner unknown. I agree the licence is a context-level condition, because N4 is a should need.
- `internal.store.calendar`: `feasible_with_conditions` for N5. Undocumented schema, restricted access.

## Agreements
- **N2 unmet means `not_feasible` overall.** Under the calibration rules, an unmet must need makes the overall verdict `not_feasible`. The agent applies this correctly. The result is that UC2 cannot proceed as a feasibility-positive project until the code mapping exists.
- **Open-Meteo for temperature:** feasible with conditions, for the reasons above.

## Overrules and disagreements
- **Agent error, not fixed: the Nager.Date licence is recorded as `MIT`.** `outputs/UC2/records/api.nager_public_holidays.json` sets `licence.name = "MIT"`, citing the GitHub repository's software licence. That licence covers the code, not the holiday data. The same record's `unknowns` list says the data licence is unknown, and the rules raise `LIC-UNKNOWN`. The verdict (`feasible_with_conditions`, with the licence as a condition) is right; the `MIT` name is wrong and would mislead a reader of the record. The fix belongs in the profiler prompt (a software repository's licence is not a data licence unless the data is in that repository). It is logged as an open finding in `outputs/artifacts/decisions.md` and was not fixed in this pass.
- **Gate note on the Nager.Date redirect (not an overrule, a finding).** The trace records `REDIRECT_NOT_ALLOWLISTED` on `date.nager.at`: the API redirected to a host not on the allowlist, and the request was refused. I did not add the redirect target to `config/allowlist.json`. The redirected response was not read, so the 2023 and 2025 holiday coverage that the agent marks as unverified stays unverified. The agent's `feasible_with_conditions` for N4 should be read with that in mind.
- **Signoff verdict versus overall verdict.** The paste asks for `proceed_with_conditions` in signoff, while the agent's overall verdict is `not_feasible`. I have recorded the condition (the N2 mapping) in signoff, and the overall verdict stays `not_feasible` until that condition is met. The learner should confirm this reading: proceeding is conditional on N2.

## Security note
No refusal of an intentional distractor here. The only refusal is the redirect above, which the guardrail correctly stopped.

## Conditions carried into signoff
See `outputs/UC2/signoff.json`: the N2 product-code mapping, the Nager.Date licence and owner, and the Open-Meteo coordinates and attribution.

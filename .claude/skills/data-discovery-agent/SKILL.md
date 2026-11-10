---
name: data-discovery-agent
description: >
  Reusable skill for Stack AI Rewire, Assignment: AI-Native Data Discovery. Runs the first
  stage of any AI/DS project: locate, catalog and assess the feasibility of internal and
  external data sources for a business problem, before any pipeline is built. Works for
  any use case written to the use-case contract (use_cases/<ID>_*.json + brief + internal
  estate). It sets up and checks the agent, frames the use case, runs planning and scouting,
  suggests external sources for unmet needs (Step 2b), then pauses for human review. It
  deliberately does NOT cover profiling, risk assessment, the memo or the learner gaps (G1–G7).
  The learner builds those with Claude directly, and the learner's deliverable includes
  extending this file with Steps 3–5.
---

# AI-Native Data Discovery: Assignment Runner (Steps 0–2b only)

You are Claude, running the first steps of **Stack AI Rewire, Assignment: AI-Native Data
Discovery** in Claude Code, against the learner's copy of this repo. The repo
contains a multi-agent discovery system (`discovery_agent/`): Planner → Scout (internal catalog,
wiki, external register) → **candidate gate, where the human adds dataset links (any URL)** →
Profiler (one per source) → deterministic rules → Risk Assessor → Memo Writer, then a human review gate.

This skill gets a use case ready, checks the tooling, runs **plan + scout**, and suggests external
sources for the needs that remain unmet (Step 2b). Profiling, red-flag assessment, the feasibility
memo and the learner gaps are done in a normal Claude Code session, guided by `README.md`.

The skill is **use-case agnostic**. UC1 (air quality and traffic) and UC2 (ice-cream sales, weather and holidays) ship with
the repo, but any business problem written to the contract below runs the same way.

## Required input
- `use_cases/<ID>_<slug>.json`: the machine-readable use case (windows, needs, grains, geography).
  Contract: `use_cases/_TEMPLATE_use_case.json`.
- `use_cases/<ID>_<slug>.md`: the business brief: problem, decisions supported, scope, out of scope.
- `internal/<ID>_<client>/catalog_export.json` + `internal/<ID>_<client>/wiki/*.md`: the client's
  internal catalog export and documentation (metadata only, never data values).
- `config/external_sources_register.json`: the external sources the client has agreements for or
  has approved, tagged with the use case id.
- **Dataset links** (any https URL): supplied by the human at the candidate gate, from their own
  search or accepted from the Step 2b suggestions. For UC1 and UC2, README.md section 4 lists links
  whose expected assessment is known.
- **The learner's search script** `scripts/web_search.py` for Step 2b. It is not provided: the learner
  generates it with Claude Code (Assignment Task 3; the prompt is in README.md, section 4, "Suggest
  sources (Step 2b)"). Claude Code's built-in `WebSearch` does not work with the gateway key, so do not
  use it. If the script is missing, fails, or returns no citations, stop at Step 2b and tell the learner
  to generate or fix it. Do not write suggestions without search results.
- `config/allowlist.json`, `config/red_flags.json`, `config/settings.json`: provided. Do not loosen
  the allowlist or the caps to make a run pass.
- Gateway credentials in the environment: `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`,
  `ANTHROPIC_MODEL`. Never print, log or commit the token.

## Repo scaffold this skill produces
```
.
├── use_cases/<ID>_*.json, <ID>_*.md         <- provided, or written by you in Step 1 (new use case)
├── internal/<ID>_<client>/                  <- provided, or assembled in Step 1 (new use case)
├── outputs/<ID>/
│   ├── use_case_validation.txt              <- Step 1
│   ├── search_plan.json                     <- Step 2 (Planner)
│   ├── candidates.json                      <- Step 2 (Scout)
│   ├── trace.jsonl, transcripts/            <- Step 2 (evidence of every LLM/tool/HTTP call)
│   ├── run_summary.json                     <- Step 2 (tokens, tool calls, warnings)
│   ├── links.json                           <- Step 2 (copy of the prescribed links) and Step 2b (accepted suggestions appended): the ONE links file
└── outputs/artifacts/step0_checks.md        <- Step 0
```
Everything after `candidates.json` (records/, rule_flags.json, risk_assessment.json,
discovery_results.json, feasibility_memo.md) is produced later, outside this skill.

---

## Step 0: Set up and check the tooling (no LLM calls)
1. If no environment is active: `python3 -m venv .venv && source .venv/bin/activate`, then
   `pip install -r requirements.txt`.
2. Check that the gateway variables are **set**, without printing their values:
   `python -c "import os;print({k: bool(os.environ.get(k)) for k in ['ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_MODEL']})"`.
   If any is `False`, stop and tell the learner which one. Do not ask them to paste the token.
3. Run the offline tests: `python -m pytest tests/ -q`. `tests/test_tools_offline.py` and
   `tests/test_agent_loop.py` must pass. `tests/test_learner_gaps.py` is **expected to fail** until
   the learner implements G1, G3, G4, G5 and G6. Report which gap tests fail; do not implement them here.
4. Smoke-test the tools without the LLM:
   - `python -m discovery_agent tool search_internal_catalog '{"query": "<a need from the brief>"}' --use-case <ID>`
   - `python -m discovery_agent tool inspect_dataset_link '{"url": "https://archive.ics.uci.edu/dataset/360/air+quality"}' --use-case <ID>`
   - `python -m discovery_agent tool list_external_register '{}' --use-case <ID>`
   Each must return JSON, not a traceback. A `DOMAIN_NOT_ALLOWLISTED` result is the guardrail
   working, not a bug.
5. Write `outputs/artifacts/step0_checks.md`: test results (pass/fail counts per file), the tool
   smoke results (one line each), and the model id in use. Never write the token.

## Step 1: Frame the use case against the contract
**Existing use case** (UC1 or UC2, where `use_cases/<ID>_*.json`
and `internal/<ID>_*/` already exist): check that the files exist, then do item 4 and item 5 below.
Do not rewrite a contract that someone else wrote. If item 4 fails, report the error and ask the
learner before you change any input.

**New use case** (the learner gives you a business problem): write the inputs, do not invent data.
1. Copy `use_cases/_TEMPLATE_use_case.json` to `use_cases/<ID>_<slug>.json` and fill every field:
   - `windows`: one per analysis period, with ISO dates and a purpose. Do not use a single
     open-ended window to dodge coverage checks.
   - `needs`: one row per data need, in business words, with `priority` (must/should/could),
     `min_grain` (one of `minute, 15min, 30min, hourly, daily, weekly, monthly, quarterly, annual,
     event, static`) and the `windows` it applies to. Aim for 5–12 needs. Split compound needs.
   - `as_of`: the date the discovery is valid for. It drives staleness checks.
2. Write `use_cases/<ID>_<slug>.md` with the same sections as the UC1 brief: business problem,
   decisions supported, scope, needs table, where to look, out of scope.
3. Internal estate: if the learner has a real catalog export, convert it to the
   `catalog_export.json` entry shape used in `internal/UC1_valdena_health/` (null where the catalog
   holds nothing, never a guess), and put the documentation pages in `wiki/` with the same front
   matter (`page_id`, `title`, `owner`, `last_edited`). Add the client's approved external sources
   to `config/external_sources_register.json` with the new use-case id and their real
   `agreement_status`. If the learner has no internal estate, stop and ask. Do not fabricate one.
4. Validate: `python -m discovery_agent validate-use-case <ID> | tee outputs/<ID>/use_case_validation.txt`.
   Fix every error it reports in the inputs, not in the validator.
5. Show the learner the needs table (id, name, priority, min_grain, windows) and the windows.
   **Pause** (for a human learner in an interactive session; in a non-interactive run, write the table and stop). Wait for them to confirm or change it. The needs list decides what the agents
   search for and what the rules check, so a wrong need here gives wrong verdicts later.

## Step 2: Plan and scout, then stop at the candidate gate
1. Run: `python -m discovery_agent run --use-case <ID> --stop-after scout --no-input`.
   This runs the Planner (search plan per need, including hints on what external data to link) and
   the Scout (catalog, wiki and register search), and writes `search_plan.json`, `candidates.json`, `trace.jsonl` and `transcripts/`.
2. If the run fails, read the last events in `outputs/<ID>/trace.jsonl` and the failing agent's
   transcript before changing anything. Fix the cause (credentials, model id, a prompt, a tool
   bug) and re-run. Do not raise `max_turns` or the HTTP caps as a first response.
3. Review `candidates.json` against the needs, and give the learner a table:
   need id → candidate source ids → `unmet_needs`. Then name, from the trace:
   - needs with no candidate, or only one;
   - internal entries the Scout opened but did not read the wiki backlinks for;
   - internal searches that returned nothing and were not rephrased.
4. Show the learner the `unmet_needs` and the planner's `external_data_hints`. If a need is already met
   by internal or register sources, say so. Then ask: **do you already have dataset links that fill any
   of these needs?** For UC1, name the three prescribed links in README.md section 4; UC2 has none. Ask whether
   the learner will use them. Each link needs need ids and windows. If the learner uses them, copy
   `links/UC1_example_links.json` to `outputs/<ID>/links.json` once, only if that file does not exist yet (for UC2, start from `[]`). Never copy over it: it may already hold accepted suggestions. The Chicago
   link in README.md section 4 is one the learner accepts on purpose: its refusal is the finding. Claude
   does not make that decision for the learner. **STOP and wait for the reply.**
   Only then go to Step 2b.

## Step 2b: Suggest external sources (only for needs still unmet)
1. Only after the learner has answered Step 2, item 4. Check that `scripts/web_search.py` exists in the
   learner's repo. If it does not, **STOP**: ask the learner to generate it with Claude Code, using the
   prompt in README.md ("Suggest sources (Step 2b)"), and wait for it. Do not write the script yourself.
   Once it exists, search with it for up to **five** public datasets that could fill the unmet needs:
   `python scripts/web_search.py "<query>"`. Use the planner's `external_data_hints` as starting queries.
   Each result is a lead from a search model, not a verified source. Only a URL with a citation may be
   suggested, and each one still needs checking on its publisher's page.
2. For each suggestion, show the learner: publisher, exact URL (the dataset or record page, not a search
   page), need ids, coverage **as the page states it** (quote the page; write `"not stated"` if the page
   does not say), and what still needs checking (licence, population, access). Do not download data.
3. **STOP and wait.** For each suggestion the learner decides `accept`, `reject` or `revise` (with new
   need ids or windows), with a short reason. The learner may also add links they found. Never decide,
   and never write a reason, for the learner. Silence is not acceptance.
4. Record every decision and reason in `outputs/artifacts/decisions.md` under "Source suggestions". Append each
   accepted suggestion to `outputs/<ID>/links.json` (the same file as Step 2), in the shape of
   `links/_TEMPLATE_links.json`, with the learner's reason as `note`. Never overwrite the prescribed links.
   The **learner** writes `outputs/<ID>/gate_decisions.json` (`{"decisions": [{"url", "decision": "accept" or
   "reject", "reason"}]}`), one entry for every link in `links.json`, after inspecting each link themselves.
   If the learner asks you to write it, transcribe only the reasons they have dictated, word for word, and
   say so in `decisions.md`. Never write a reason the learner did not give. The pipeline refuses to profile
   a link without one.
5. For each accepted link, check its host is on `config/allowlist.json`:
   `python -m discovery_agent tool inspect_dataset_link '{"url": "<link>"}' --use-case <ID>`.
   If a host is refused, **STOP**: the learner decides whether to add it, with a G6 justification in
   `outputs/artifacts/decisions.md`. Do not add hosts yourself, and do not try an alternate URL. The Chicago host (`catalog.data.gov`) is refused by design: record that refusal as a finding. The Eurostat host waits for G6 in Task 6; re-run the inspection after it is added.

**Then stop.** Tell the learner the candidate list and accepted links are ready for review, and give
them the command for the next stage:
`python -m discovery_agent run --use-case <ID> --from-stage profile --links-file outputs/<ID>/links.json`
(the same file as Step 2; it must hold every link the learner has decided on).
This skill has nothing further to do. Profiling, rules, risk assessment, the memo and the gaps
happen in a normal session from here, guided by `README.md`.

---

## Rules that hold in every step
- **Metadata first, then a capped sample, never the whole dataset.** Read schemas, descriptions,
  coverage and terms; `sample_data_file` may read the first part of a file. Do not download whole
  datasets or copy personal data into any output.
- **Provenance on every claim.** Every statement about a source names a tool call, URL, catalog
  field or wiki page.
- **Unknown stays unknown.** Never infer a licence, owner, refresh cadence or consent. Use null and
  list it under unknowns.
- **Guardrails are not obstacles.** A refused host, an expired vendor agreement or a restricted
  table is a finding to record, not something to work around.
- **The agents are the product.** When an output is wrong, fix the agent (prompt, tool, rule,
  validator) and re-run. Never hand-edit `candidates.json`, records or results to look right.
- **A suggestion is not a verified source.** Selecting it grants no host access and no permission to
  use the data. Keep the exact-host allowlist.

---

## Step 3: Profile and rule-check

Run this after the learner's gate decisions exist (`outputs/<ID>/gate_decisions.json`, one entry per link in `outputs/<ID>/links.json`).

1. Run: `python -m discovery_agent run --use-case <ID> --from-stage profile --links-file outputs/<ID>/links.json --no-input`.
   It profiles every candidate (one Profiler per source, 4 in parallel), then runs the rules, the Risk Assessor and the Memo Writer. To re-profile one source after a fix, add `--only <source_id>` and keep the same command otherwise. `--only` reuses `candidates_final.json`.
   If the run stops with `Missing outputs/<ID>/gate_decisions.json`, the gate is not complete. Stop and tell the learner which link has no decision. Do not write a decision yourself.
2. For each `outputs/<ID>/records/*.json`, check, and write a one-line result per record in `outputs/artifacts/step3_checks.md`:
   - `provenance` has at least three entries, and each names a tool call, URL or catalog field.
   - `licence.found_in` and `licence.evidence` are set, or the licence is null and listed under `unknowns`. A licence from the profiler's memory is a failure.
   - `temporal.start`, `temporal.end` and `temporal.grain` come from documentation, not from the sample (unless the sample is the whole file).
   - `sample_findings` agree with `schema.fields` and with the documentation. Search the documentation for numeric sentinels (`-200`, `-999`, `-9999`) and check that the sample counts them as missing, including float forms such as `-200.0`.
   - `quality_notes` quote the documentation for each claim.
3. Read `outputs/<ID>/rule_flags.json`. Every flag must have a `raised_by` of `rule:<name>`. Read `rule_warnings` in `outputs/<ID>/run_summary.json`: it must be empty. A `NOT_IMPLEMENTED` or `skipped` warning means a gap is still open; fix it before going on.
4. Read `outputs/<ID>/trace.jsonl` for `refused` HTTP events. Each refusal is a finding to record in the memo and the review, with the host and the reason. Do not add the host to the allowlist.
5. **STOP** if a profiler record reports a refused host the learner did not expect, or a licence the learner has not seen. The learner decides what to do next.

## Step 4: Assess, calibrate and draft the memo

1. After Step 3 is clean, the verdicts come from the Risk Assessor, which follows the calibration rules in `discovery_agent/prompts/risk_assessor.md` (section "Verdict calibration rules"). To re-run only the assessment after a rule or prompt change: `python -m discovery_agent run --use-case <ID> --from-stage assess --no-input`. It re-runs the rules, the Risk Assessor and the Memo Writer on the saved records; it does not re-profile.
2. Check each verdict against the calibration rules, one source at a time. Write the result in `outputs/artifacts/decisions.md` under the calibration heading:
   - Does a blocker flag (`LIC-UNKNOWN`, `LIC-NONCOMMERCIAL`, `LIC-AGREEMENT-NOT-ACTIVE`, `ACC-UNREACHABLE`, `GOV-CONSENT-GAP`) give `not_feasible` for a core need? If not, the reason must be written down.
   - Does `COV-OUT-OF-WINDOW` apply to every window the source was proposed for?
   - Is each `dismissed_rule_flags` entry backed by a field in the record? "Looks fine" is not a reason.
   - Does `overall_verdict` follow from the must needs in `need_coverage`?
   If a verdict breaks a calibration rule, record it as a disagreement. Do not change the rule or the verdict to make them agree; the learner decides which is wrong.
3. Check `outputs/<ID>/feasibility_memo.md` has the seven sections the Memo Writer prompt requires: executive summary, need coverage, source assessments, red-flag register, conditions and owners, next steps, open questions for the reviewer. A missing section means the Memo Writer or its schema check failed; read `outputs/<ID>/transcripts/memo_writer.json` before re-running.
4. **STOP: human review gate.** The learner reads `feasibility_memo.md` and writes `outputs/artifacts/review_<ID>.md` (agreements, overrules with reasons, verdict per link, any security finding) and `outputs/<ID>/signoff.json` (verdict, reviewer, conditions with owner and due date, at least one agreement or override, one `traced_conclusion` whose `source_id` is in `discovery_results.json` and whose `record_field` is a non-null field of that record). Do not write the review or the sign-off in the learner's place unless they dictate the content, and say so in `decisions.md`.

## Step 5: Evaluate and hand off

1. Run the self-check for each use case and save it:
   `python -m discovery_agent check <ID> > outputs/artifacts/check_<ID>.json`.
   The `problems` list must be empty. Fix the signoff or the review, not the records. A null `record_field` counts as missing: pick a field with a value.
2. Record the run cost and the guardrail evidence from `outputs/<ID>/trace.jsonl` and `run_summary.json`: `llm_calls`, `input_tokens`, `output_tokens`, `tool_calls`, `http_live`, `http_refused` and the refused hosts. Note that each stage writes one line to `outputs/<ID>/run_history.jsonl`. The totals are per run, so re-runs add to them.
3. Measure the fix, if one was made (G7): the same command before and after, with the counts that changed (sentinel counts, flags, verdicts). Keep the before copies in `outputs/artifacts/` (copy, never hand-edit `outputs/<ID>/`).
4. Save the test evidence: `python -m pytest tests/ -q > outputs/artifacts/pytest_after.txt 2>&1`. All tests must pass. Do not edit the tests to make them pass.
5. Check for leaked credentials: `grep -rn "ANTHROPIC_AUTH_TOKEN" . --exclude-dir={.venv,.git}`. The only hits allowed are the variable name in code, `.env.example` and this file. A token value in any file is a failure: remove it, then rotate the key.
6. Hand-off: list what is in `outputs/artifacts/` for this use case (check, review, decisions, walkthrough) and what the learner still has to do. Stop there.

**Test for these steps:** give this file to a fresh session with a different use case (a new `use_cases/<ID>_*.json`, brief and internal estate). Steps 3 to 5 should produce the same kinds of file, with the same STOP points, without a UC1 or UC2 name appearing in the steps.

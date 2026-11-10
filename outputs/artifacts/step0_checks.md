# Step 0 checks

Written for: the learner and the instructor. Run in the repo root (`starter-code/`) with the project venv. No token values are recorded here.

## Environment
- Gateway variables: `ANTHROPIC_BASE_URL` set, `ANTHROPIC_AUTH_TOKEN` set, `ANTHROPIC_MODEL` set (checked for presence only).
- Model id in use: `claude-haiku-5-5` (from the run log, `model=claude-haiku-5-5`).
- Dependencies: installed in `.venv` (`anthropic` 1.17.0, `pytest` 9.2.0, `jsonschema`).

## Offline tests (per file)
| File | Result |
|---|---|
| `tests/test_tools_offline.py` | 24 passed |
| `tests/test_agent_loop.py` | 7 passed |
| `tests/test_learner_gaps.py` | 21 passed (after the gap work; 20 failed before it) |

Full suite after the gap work: 52 passed (`outputs/artifacts/pytest_after.txt`).

## Tool smoke tests (no LLM)
- `search_internal_catalog` with `{"query": "air quality hourly"}` (UC1): returned JSON with hits, top hit `internal.traffic.hourly_counts`.
- `inspect_dataset_link` with the UCI air-quality URL (UC1): returned JSON, `link_type: uci_dataset_page`, `source_id: link.uci_360`.
- `list_external_register` with `{}` (UC1): returned JSON with the register sources.

No tool returned a traceback. No `DOMAIN_NOT_ALLOWLISTED` was hit in these three calls.

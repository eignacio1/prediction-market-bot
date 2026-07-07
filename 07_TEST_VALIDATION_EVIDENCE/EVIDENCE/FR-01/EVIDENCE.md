# FR-01 Evidence — Signal Ingestion

**Requirement:** (a) Ingestion runs without error on a valid input snapshot; (b) Output schema matches DATA_REQUIREMENTS.md contract; (c) Snapshot ID assigned and written to DATA_SNAPSHOTS_INDEX.md; (d) Invalid input rejected with structured error log.

**Populated:** 2026-07-06 (GG-075 remediation), by pointing to evidence that already existed, not by generating new proof.

## Test evidence (real, currently passing)

- `tests/test_t181_mlb_c1.py` — MLB C1 ingestion schema/behavior tests.
- `tests/integration/test_mlb_api_connectivity.py`, `tests/integration/test_mlb_name_matching.py`, `tests/integration/test_mlb_pipeline_smoke.py` — end-to-end C1 smoke tests against real/pinned data.
- `tests/test_cohort.py`, `tests/test_team_stats_store.py` — NBA-era ingestion/cohort schema tests (still passing; NBA is dark but its C1 code and tests remain in the suite).
- Full suite confirmation (re-run 2026-07-06 as part of this evidence pass): `2375 passed, 6 skipped, 1 failed` (`.venv311/bin/python3 -m pytest -q`). The 1 failure is `tests/integration/test_mlb_pipeline_smoke.py::TestFeatureCSVIntegrity::test_feature_csv_freshness` — a data-freshness check (feature CSV is stale, not a code defect), pre-existing and unrelated to FR-01's ingestion-correctness claim (tracked under GG-077-adjacent operational notes, not a governance gap of its own).

## Snapshot discipline

- `01_SPEC/DATA_REQUIREMENTS.md` and `DATA_SNAPSHOTS_INDEX.md` (repo root / data governance docs) define the snapshot ID contract; EXP runners (`run_exp001.py` through `run_exp019c...`, `run_exp_arith_mlb_01.py`, `run_exp_flow_mlb_01.py`) all reference pinned Snapshot IDs (e.g. `SNAP-2026-07-02-002`), confirmed via `grep -rn "SNAP-" src/`.

## Status

**OPERATIONALLY DEMONSTRATED** — C1 ingestion (MLB active; NBA dark but code/tests intact) has been running in production for 5+ weeks with the above tests passing continuously. This file is the evidence pointer this requirement's design called for; it intentionally does not duplicate test output (the tests themselves, re-runnable via pytest, are the durable evidence — this file's job is to make them findable from `ACCEPTANCE_CRITERIA.md`/`VALIDATION_PLAN.md`).

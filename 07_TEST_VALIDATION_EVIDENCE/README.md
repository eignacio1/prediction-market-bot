# 07 Test, Validation & Evidence

**Last verified:** 2026-10-20 against `00_ADMIN/DOC_REGISTRY.toml`. **Owner (role):** Data Scientist (DS) + QA.

- `TEST_STRATEGY.md`, `VALIDATION_PLAN.md`: LIVING intent documents. The tests themselves are `tests/`, run by CI (`.github/workflows/tests.yml`).
- `EVIDENCE/`, `VALIDATION_REPORTS/`, `BENCHMARKS/`: **RECORD** files. Each carries a "Record as of <date>" header and is never rewritten to match later reality.
- Current experiment verdicts live in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`, not here.

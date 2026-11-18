# Session Handoff — 2026-09-29T05:15Z

<!-- session-meta
task_id: T-583
tier: MICRO
timestamp: 2026-09-29T05:15:00Z
commit: 7b4bbdd
one_line_summary: T-583 built a parallel T4 A/B harness (game-clustered paired Δ-Brier, loud refusals incl. T4M-PROJ); no real cohort scorable until 2027.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

Tier note: declared STANDARD at claim; work was scripts/tests/docs only (no src/, no GG/ADR), so routed MICRO.

## Strategic Decisions This Session
| Decision | Where recorded |
|---|---|
| Parallel T4 harness, not generalization of T1 `ab_harness.py`; shared core deferred to a third adapter | `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T583_t4_ab_harness_DESIGN.md`. NOT in DECISION_LOG (37.3 owns it) — 37.3 to record. |

## What changed
- New `scripts/ab_harness_t4.py`, `scripts/t4_forbidden_cohort_manifest.json` (879 tickers), `tests/test_ab_harness_t4.py` (13 tests); results in `T583_RESULTS_t4_ab_harness.md`.
- T1 harness files untouched; 75 tests pass (62 baseline + 13).
- Not run on ADR-0065's candidate. Real cohort not scorable before 2027 season (needs game-state logging first).

## One thing pending
Merge branch `session/20260929T050106Z-t4-ab-harness` to main (not merged; no src/ change so fast-path applies if origin/main is an ancestor — it has moved 4 commits, so rebase first).

## Resume
`git fetch origin && git log origin/main..session/20260929T050106Z-t4-ab-harness`

# Session Handoff — 2026-10-01T01:40Z

<!-- session-meta
task_id: T-599
tier: STANDARD
timestamp: 2026-10-01T01:40:00Z
commit: aaef16d
one_line_summary: T-599/EXP-031: surveyed 14 Kalshi families vs pre-registered rule; zero candidates, shortlist empty (GG-324).
gg_touched: GG-324
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** task complete. **Last commit:** `aaef16d` (session branch, pushed to origin/main).

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| Pre-registered E = B − null median − H, 99.5% own-n null; zero CANDIDATES result | DECISION_LOG 2026-09-30 EXP-031 |

## What changed
- `scripts/market_efficiency_survey.py` + 6 tests; EXP-031 outputs under `exp_output/EXP-031-MKT-EFF-SURVEY/`; prereg and results summary in 05_RESEARCH_EXPERIMENTS.
- GG-324 registered and updated. Capital: none, paper only. Bet count not re-checked.

## One thing pending
Decide whether to pre-register a follow-up on the last pre-game quote (first-seen rule penalises early-listed families). Also undiagnosed: 0-player T1 run 2026-09-28 (SemanticFloorViolation=1).

## Resume
`scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`, then read EXP031 results summary.

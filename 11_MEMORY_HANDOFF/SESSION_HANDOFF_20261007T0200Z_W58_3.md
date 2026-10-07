<!-- session-meta
task_id: T-716
tier: STANDARD
timestamp: 2026-10-07T02:00:00Z
commit: bcc5041
one_line_summary: W58.3 calibration engine live: sealed cells emit no scores, /project Calibration section, one daily cron line.
gg_touched: GG-498, GG-499
adr_touched: none
plan_deliverable_moved: no
-->

# Session handoff — W58.3 calibration engine

DONE | session/w58-3-calibration-engine @ f20f095 (PR #175 merged) + docs push | CI green (37557900216); Deploy 37558544298, t4-mlb restart not_needed | Engine, tests, /project Calibration section and one daily cron line (49 13) are live; 33 cells, 0 at a look, no sealed score read | No operator decision required.

Next undone deliverable: none. Follow-ups: GG-498 (cron.conf mirror drift), GG-499 (settled-row schema inconsistency). First look expected NFL ~2026-10-14: confirm the engine then emits scores only for the earliest 60 games per cell.
Results: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W58_3_calibration_engine_results.md

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| Engine PREREG table; unreadable GG state counts as open; one cron line 49 13 | DECISION_LOG 2026-10-07 |

Resume: `git fetch && git log origin/main -5`; one thing pending: NFL first look ~2026-10-14.

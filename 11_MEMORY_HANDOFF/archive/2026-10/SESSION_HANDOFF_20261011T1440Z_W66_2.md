# Session Handoff — 2026-10-11T14:40Z

<!-- session-meta
task_id: T-796
tier: STANDARD
timestamp: 2026-10-11T14:40:00Z
commit: dfc00e9
one_line_summary: W66.2 DONE: GG-560 cause = demo partial listing; ADR-0072 forward test ON (demo only, share 0.5); persisted cancel sweeper; GG-536 T1 fills-only.
gg_touched: GG-560, GG-564, GG-536
adr_touched: ADR-0072 (status -> ACCEPTED)
plan_deliverable_moved: yes
vision_pillar: EXECUTION
gap_measure: E1, E2, E3
gap_delta: none (measure not moved yet; first orders arrive with the next game, 2026-10-12 00:00Z)
-->

**Status:** DONE | main @ dfc00e9 (+ docs commit) | PR #220 merged; CI GitHub $0, local pytest 3950 passed / 10 pyarrow-env failures (pre-existing) | Forward test ON in the running t4-mlb (environ proven) | MEASURE MOVED: none (E1 3.9% / 17.5% unchanged; no order since the switch) | operator decisions below.

## Operator decisions
1. GG-564: pre-check demo listing before ordering (changes order behaviour) or only stratify E1 by demo-listed vs not?
2. Shadow pregame runners' cron lines do not load `deploy/demo_fill.env`; add it (an existing-cron-line edit, not authorized in 66.2)?

## Next
Read `logs/demo_fill_policy.jsonl` after 2026-10-12 00:00Z game and the 11:00Z T1 run: arm assignment, skips by reason, cancels with outcomes, cancel success rate. Turn-off: remove `deploy/demo_fill.env` + restart t4-mlb (idle only) + drop the W66.2 cron block.

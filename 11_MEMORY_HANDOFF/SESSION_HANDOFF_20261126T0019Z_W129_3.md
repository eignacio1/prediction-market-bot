# Handoff — W129.3 (MLB 2027 forward PREREG, daily-board install, full-slate dry run)

<!-- session-meta
task_id: W129.3
tier: STANDARD
timestamp: 2026-11-25
commit: see branch w129-3-mlb-2027-prereg
one_line_summary: 12-cell 2027 forward PREREG frozen; paused daily-board install (not run); 2026-08-15 slate through 7 D6 layers, 4 of 7 on 8 cells.
gg_touched: GG-1957
adr_touched: none
vision_pillar: PROOF P3, DEPTH D6 MLB
gap_measure: P3 MLB looks dated 0 -> 12 cells; D6 MLB dry run: 0 of 12 cells reach 7 layers, 8 of 12 reach 4 (L1,L2,L4,L6), 4 (T2) have no rows
gap_delta: see above (RESULT_W129_3_C.md, source dry_run_w129_3.py, 2026-08-15)
pattern_sweep: GG-1957 silent-exit: grep rows_written|silent_exit over scripts/ deploy/ -> only the new MLB board job carries the rule; other cron jobs not audited here (T-number needed)
surface_delta: +1 paused cron entry (mlb_board_daily, RUNTIME_REGISTRY), 0 live
-->

rules_first_line: "# Wave 129 common rules"
directive_conflicts: none found.

## Done
- A: `05_RESEARCH_EXPERIMENTS/EXP_MLBENGINE_SPLIT_2027_FORWARD_PREREGISTRATION_2026-11-25.md` (+ .sha256), frozen 2027-03-01; judged n, look dates (weekly Tue from 03-30; scored 04-13..06-15; season end 10-05), modal outcomes. Moneyline UNDERPOWERED at +0.02.
- B: `scripts/mlb_board_daily.py`, `scripts/mlb_board_install.py` (gate/install/readback/uninstall/healthcheck), `deploy/cron.mlb_board`, box tasks, paused registry entry, healthcheck block 12, 13 tests. Arm-date alarm and silent-exit alarm are code. NOT installed.
- C: dry run of 2026-08-15 (15 games priced). No outcome read. Table in `12_EXPLORATORY/mlb_engine/RESULT_W129_3_C.md`.
- Defect found by C and fixed: board file keys were `HOME|AWAY|DATE`, forecaster takes tuples; no engine price would ever have reached a row. `load_board` + test.

## operator decisions:
> approve mlb_board_install — must be run by 2027-03-18 (assumed opening day 2027-03-25 minus 7; the alarm re-derives it from the schedule cache). Not run.

## Pushback
- The install alone does not produce engine prices: the board needs synced Savant inputs built off-box, and none exist yet. Approving it early buys alarms, not rows.
## Surface
- Archive logs 22:00-05:59Z only, so T2 (4-8h) has no rows for evening games: T2 cannot be exercised on 2027 rows unless the shadow cadence covers daytime.
- L3 (MLB filter supply), L5 (forward nets) and L7 (any MLB fill) are absent on every cell.
- CLAUDE.md RIGHT NOW window-maintained lines are 8 days old (RED); window-owned, untouched.
- Session claim (Step 0) was not made formally.
## Dependencies
- Off-box Savant store build + sync to `exp_output/MLB_BOARD/inputs/` with `inputs.meta.json`; posted-lineup feed (does not exist); Stats API 406 on the box; Savant header-only for Oct 2026 (confirm in April); 2027 opening day assumed.
- Resume: PR for branch w129-3-mlb-2027-prereg, CI green, merge.

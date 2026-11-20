# Session handoff — W122.1 · NBA points priced by the engine, logged as shadow cells T1-T3 (D6 props)

<!-- session-meta
task_id: W122.1
tier: STANDARD
timestamp: 2026-11-20T17:50:00Z
commit: 63bb86c
one_line_summary: W122.1: NBA points priced by the engine and logged T1-T3 on the box; props D6 0 -> 0 (layer 2 missing)
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: BREADTH, DEPTH
gap_measure: B4, D6 props
gap_delta: B4 points rows live (T2 260 rows, box 17:39Z); D6 props 0 -> 0 (d6_read 2026-11-20 box @ 685c54c9)
pattern_sweep: grep SERIES/CELLS consumers of the prop runner in src/ scripts/ tests/ -> registry already had NBA_PLAYER_POINTS T1-T3 SHADOW; REB/AST/3PT hash unchanged
surface_delta: 0
-->
Common rules first line quoted: "# Wave 122 common rules". PR #543 merged (Test Suite + Docs Guard green on its head; rebased once after the gaps-by-arm index went stale on main).

## MEASURE MOVED
- **B4 (props logging): points joins rebounds / assists / threes.** `KXNBAPTS` priced by the engine, logged to `NBAENG_NBA_PLAYER_POINTS_T[123].jsonl`. Box HEAD 685c54c9 (deployed 17:13Z). First points rows at the 17:39Z cycle: T2 260 rows (T1 / T3 none yet). Each row carries model p, bid / ask / mid, fee, e_net and the model hash. Shadow only, kelly 0, v1 untouched.
- **D6 props wired: 0 -> 0.** D6 read 17:4xZ: NBA 7 wired (unchanged), all 117 cells 18 wired. No prop cell is wired. Nothing was waited on for a slate.
- **Points calibration, held out (2026-11-08 on, walk-forward, point-in-time rosters):** Brier beats the base-rate Brier at every line (10/15/20/25/30). Residual under-prediction at low lines (10+: mean p .505 vs hit .563; scored rows are players who played). Not tuned further. Script `scripts/nba_points_calibration.py`.
- Fit: `POINTS_REST = 0.0` fitted on 2026-11-01..11-07 (51 games), before the held-out window. Rotation mu summed 117 vs team 114.5, so the default 0.08 rest bucket under-predicted.

## One cause per unwired prop cell (box read)
- NBA_PLAYER_POINTS T1/T2/T3: layer 2 (market state) missing. d6 layer 2 = leaves for the cell in `decision_trees/leaf_map.json` (v1); the points leaves live only in the candidate file `leaf_maps/nba_props_v2.json` (W121.2). Layer 1 now present (box rows carry p).
- NBA_PLAYER_REBOUNDS / ASSISTS / THREES T1-T3 (and THREES T2/T3 on layer 1): layer 1 missing in the D6 read (`1 model p`). I did not dig into why rows from the same runner do not count.
- NBA_PLAYER_POINTS T4: dark cell, layer 1 missing; not examined.
- Note for the next D6 block: `d6_read` ledger evidence reads `exp_output/PREGAME_SHADOW`; the engine prop rows write to `exp_output/PREGAME_SHADOW_EXP047`. Check this before concluding it is a data gap. Not changed here.

## Tests
`tests/test_nba_engine_props_shadow.py` (+4): KXNBAPTS ticker parse; points row logged and monotone in line; consistency with the team total and a look-ahead mutation test; calibration script walk-forward smoke. 30 pass across the related files.

surface_delta: 0 (no cron, service or workflow; one more series in the existing prop runner)
pattern_sweep: `src/ scripts/ tests/` for `SERIES` / `CELLS` consumers of the prop runner; the registry already had NBA_PLAYER_POINTS T1-T3 as SHADOW. REB/AST/3PT model hash unchanged (points use `POINTS_SHA256`).
directive_conflicts: none
vision_pillar: BREADTH (B4) + DEPTH (D6)
Pushback: D6 will not move until the points leaves are in v1's leaf map or d6 reads the candidate map and the EXP047 ledger. Both are a decision, not a bug fix here.
Surface: no installs run. Dependencies: next d6_read after T1/T3 points rows exist.

# Session handoff — W129.2 (EXP-047-S, the shrunk-mean props challenger) — 2026-11-26T00:40Z

<!-- session-meta
task_id: W129.2
tier: STANDARD
timestamp: 2026-11-26T00:58:00Z
commit: 202373c
one_line_summary: W129.2 EXP-047-S shrunk-mean props challenger SUPPORTED (pooled D +0.00172, 4/4 stats); shadow beside C2, merged #595
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH, PROOF
gap_measure: D3 NBA props, P2, D5(b) PAM class 3
gap_delta: D3 NBA props +1, P2 +1, D5(b) PAM class 3 interpreted -> logged challenger, not applied (12_EXPLORATORY/nba_props_shrunk/results.json @ 202373c)
pattern_sweep: ledger-dir refs swept in scripts/ src/ deploy/ tests/ .claude/; registry writes list lacked C2 ledger, now lists C2 and S; subprocess/unfenced-write isolation defects fixed in run_shrunk.py and build_prev_table.py
surface_delta: 0 (existing cron run_nba_engine_props_shadow.py gains one ledger, registered)
-->

**Branch** `w129-2-props-shrunk`, squash-merged as #595 (`202373c`), CI green on 508380d.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| `PM_PROPS_SHRUNK` default on, shadow only, own ledger, no orders, Kelly 0; PREREG SHA a constant; prior table frozen | DECISION_LOG 2026-11-25 W129.2 |

## What changed
- PREREG pushed at `8d6b97e6` before any judged row; judged once on 2025-26 (1,131 games, 315,191 rows). **SUPPORTED:** pooled D +0.00172 [+0.00140, +0.00204], 4/4 stats BH-pass. Gain sits at 4-10 prior games, ~0 at 31+; nearly all from rate shrinkage. `12_EXPLORATORY/nba_props_shrunk/RESULT.md`.
- Challenger `NBAEnginePropsShrunk` logs beside C2 to `exp_output/PREGAME_SHADOW_EXP047_S/`; frozen table `data/reference/nba_prev_season_2025_26.json`. C2/v1 untouched.
- Known flaws: `players_without_prev` never incremented (rookie share unreported); threes use raw 3PA weights; log-loss, not net after costs; 2025-26 not fresh to the program.

## operator decisions:
- Cron `run_nba_engine_props_shadow.py` is paused pending `nba_engine_props_shadow_install`; nothing logs on the box until approved.

## One thing pending
Router scores the S arm per leaf on net after costs once forward rows exist; refresh the prior table each autumn.

## Resume
`cd pm-w129-2 && git fetch && python3 scripts/d6_read.py`

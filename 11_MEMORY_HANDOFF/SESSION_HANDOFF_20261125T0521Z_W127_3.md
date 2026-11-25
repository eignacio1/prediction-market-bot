# Session handoff W127.3 — Kalshi combos through RFQ in demo
**Last reviewed:** 2026-11-25. Branch merged via PRs #575, #576, #577, #578, #580; #581 (accept-cap fix) pending merge.

vision_pillar: EXECUTION E1/E2 on combos; BREADTH B4
gap_measure: combo demo fills / quotes received
gap_delta: E1 combos 0 -> 2 demo fills (unsettled); quotes recorded 3 of 12 RFQs (9 lost to a crash fixed in #581); B4 unchanged at 0 until the install is approved
surface_delta: +1 module (kalshi_rfq.py), +1 script (combo_rfq_demo.py), +5 allowlisted box tasks (combo_rfq_demo_run/_read, nba_combo_shadow_install/_readback/_uninstall); no new cron/service; install NOT run
pattern_sweep: grep kickoff_for_event("KXNBAGAME in src scripts tests: 2 hits (nba_combo_shadow.py, combo_rfq_demo.py), both fixed + test
directive_conflicts: none
defect found: nba_combo_shadow.py (W126.4) dropped every combo (tip lookup returned None). Fixed in #580. Any W126.4 dry-run showing rows was not exercising this path.

operator decisions:
> APPROVE nba_combo_shadow_install ? Adds one hourly cron line (41 * * * *) running scripts/nba_combo_shadow.py with PM_COMBO_SHADOW=on BOT_ENV=paper, logging to exp_output/COMBO_SHADOW. No orders, no capital. Surface check: install task is budget-gated (refuses unless SURFACE BUDGET is GREEN, Hard Rule 14); RUNTIME_REGISTRY entry exists, PAUSED until approved. Uninstall task: nba_combo_shadow_uninstall.

Next: merge #581; re-run combo_rfq_demo_run next UTC day; read ledger; check the 2 fills' settlement; re-score RESULT_W127_3.md with n=12.

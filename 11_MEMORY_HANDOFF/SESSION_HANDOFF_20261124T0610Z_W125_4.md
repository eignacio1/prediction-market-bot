# W125.4 handoff — lineup-cross usage shift reaches NBA props
branch: session/20261124T011335Z-w125-4-lineup-cross-props · PR #561 · prereg 437975c (before any outcome read)

## What shipped
- nba_engine/usage_redistribution.py: one shared rule (proportional absorption, f = 1/(1-V)). Game path (usage_missing / creator_out) uses it, bit-identical (test).
- nba_engine_props_c1_forecaster.py: EXP-047-C1, own MODEL_SHA256. Nobody Out = EXP-047 to the bit (test). Planted Out creator shifts teammates up (test).
- Runner switch PM_PROPS_C1 / --c1, default OFF, logs to exp_output/PREGAME_SHADOW_EXP047_C1/. Activation = dated proposal line in ACTIVE_QUEUE (not approved).
- HYPOTHESIS_DOCTRINE II.4 row; SEATS/nba.toml NBA-10 props-consumer note.
- Premise gap: no redistribution rule existed in the game path; this block defined it.

## Result (12_EXPLORATORY/nba_props_role/RESULT.md)
Verdict by PREREG rule: INDETERMINATE (mixed). 1,899 games, 357,010 rows, game-clustered bootstrap, BH q=0.10.
points improves (-0.027 log-loss [-0.031,-0.024]); assists +0.009, rebounds +0.023, threes +0.002 all worse. Points gain grows with vacated usage.
Uniform rule: hypothesis closed (EXP-047-C1, parked for R&D). Points-only C2 needs its own prereg (chosen after seeing this, cannot self-confirm).
Scored vs realised outcomes on a synthetic ladder; not a market comparison, not an edge claim.

## Required fields
pattern_sweep: usage_missing / creator_out consumers (grep src/ scripts/ tests/ 12_EXPLORATORY/) — only factors_applied.py computes them; routed through missing_usage(); test_nba_factors_applied + w110 tests unchanged and green.
surface_delta: 0 components. No cron/service; one ledger dir added to the existing nba_engine_props_shadow writes list (RUNTIME_MAP regenerated, 95 live).
directive_conflicts: none.
measure moved: D1 (personnel on NBA props): built and measured, NOT activated, so the reported D1 count does not change. D5(b) NBA-10 consumers: 1 -> 2 (game path + props challenger), props stage stays registered until forward log.
verification: local full suite 6,075 passed / 44 skipped; CI first run failed on the exploratory-fence test (write not via safe_out), fixed d00374a.

## Open
- Operator: approve PM_PROPS_C1 or not (recommendation: leave off).
- Next: pre-register points-only C2 (stat-specific absorption), then forward log.
- run_retro.py needs a data root with player_box, schedule, espn_schedule (symlink-assembled from two worktrees); rows file not committed (32 MB).

# W126.2 session handoff — session-meta

<!-- session-meta
task_id: W126.2
tier: STANDARD
timestamp: 2026-11-25T01:00:00Z
commit: 7d10d3d (PR #566, merged, CI green)
one_line_summary: W126.2 EXP-047-C2 per-stat absorption on NBA props built (default off); retro on unread 2023-24 SUPPORTED, all four stats improve.
gg_touched: GG-2003
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D1, D3
gap_delta: D3 +1 challenger on NBA props (EXP-047-C2, candidate, not logging); D1 unchanged until PM_PROPS_C2 is switched on
pattern_sweep: usage_redistribution consumers grep src/ scripts/ tests/ -> factors_applied (missing_usage), props C1, props C2; game path bit-identical (test_w125_4)
surface_delta: 0 (switch default off; +1 ledger dir only on activation)
-->

# W126.2 handoff — stat-specific usage absorption on NBA props
branch: session/20261125T002516Z-w126-2-props-c2 · prereg fc4e596 (before any outcome read) · fit frozen before 2023-24 scored

## Premise correction (say it in the report)
Block text: "one points-share rule moved every stat". The code did not: C1 moved each stat by its own share. What C1 assumed was FULL absorption of the vacated stat. C2 tests that assumption with a fitted fraction per stat.

## What shipped
- usage_redistribution.py: `absorb(w, p, lam)` and `absorb_threes` added; `redistribute` untouched; game path bit-identical (existing test).
- nba_engine_props_c2_forecaster.py: own MODEL_ID/SHA, lambdas frozen (rebounds 0.26, assists 0.31, 3PA 0.27; points full). Nobody Out = EXP-047 to the bit (test).
- Runner `--c2` / `PM_PROPS_C2`, default OFF, ledger exp_output/PREGAME_SHADOW_EXP047_C2/. Activation = dated proposal in ACTIVE_QUEUE (not activated).
- 12_EXPLORATORY/nba_props_role: PREREG_C2.md, FIT_C2.json, run_c2.py, RESULT_C2.md/.json. HYPOTHESIS_DOCTRINE row EXP-047-C2; SEATS/nba.toml B10 note.

## Result (2023-24, never scored for props; 899 games, 163,894 rows) — RESULT_C2.md
Verdict SUPPORTED (BH q=0.10). Log-loss diff vs EXP-047: points -0.0264 [-0.0312,-0.0216]; rebounds -0.00097 [-0.00194,-0.000002] (thin, p 0.0498); assists -0.0041 [-0.0051,-0.0032]; threes -0.0028 [-0.0037,-0.0020]. Vs C1: rebounds -0.016, assists -0.007, threes -0.004.
Modal outcome was "SUPPORTED on points only, INDETERMINATE close second": the result beat it (rebounds, assists, threes also improve). Lambdas came out lower than predicted (0.26-0.31, not 0.4-0.8).
Gross/cost/net per arm: forward only (no prices exist for 2023-24).

## Needs your decision
- Switch PM_PROPS_C2 ON as shadow logging (window plumbing after the Hard Rule 14 check; proposal line in ACTIVE_QUEUE).

## Limits
Rebounds gain over EXP-047 is borderline; pre-tip Out only; no position/role; one fit season; log-loss on a fixed ladder is calibration, not a price edge.

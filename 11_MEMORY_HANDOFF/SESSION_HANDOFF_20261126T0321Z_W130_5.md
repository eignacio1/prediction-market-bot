# Session handoff - W130.5 (PROOF / HANDOFF) - 20261126T0321Z
First read for SW-10 (B-125): **04_EXECUTION/STATE_OF_THE_BOT.md** (generated from box reads only; regenerate with box task `state_of_the_bot_read`, then `python3.11 scripts/state_of_the_bot.py --ingest`).

## Measure moved
- vision_pillar: PROOF (P1 counted from rows that exist) + PLUMBING for the probes.
- gap_measure: live row-writing components with a silent-arms probe or a written exemption: **every live writer is now probed or exempt-with-reason** (before: 14 probes, no coverage check; I did not count the unprobed writers before the change). tests/test_silent_arms_coverage.py fails when a live writer has neither - it caught W130.3's new combo_rfq_demo cron the same night, now probed.
- D6 fresh: box d6_read ran 2026-11-26T02:31Z and again 03:15Z, exit 0 (was exit 124 at 00:43Z): **18 / 129 wired**; distance_to_optimum reads it (distance_read 03:14Z) - nba 7/28, nhl 7/21, nfl 4/32, mlb 0/42, multi 0/6.
- STATE_OF_THE_BOT.md generated from the box (per sport: arms rows 24h/7d, demo orders/fills/settled/P&L, installs pending, verdicts, D6, red signals).
- gap_delta: d6_read timeout closed (code); new real alarm below.

## Finding (not a fix)
- **NBA props EXP-047-S (shrunk means) is SILENT**: 7 NBA games in the window, zero rows, ever (dir absent). Default-ON arm that never wrote. Surface budget is RED because of it. Owner: next NBA-props window. Not fixed here.
- EXP-047-C1 reads idle (off by default); combo and NHL in-play runners idle (paused installs).

## What shipped
- #602 (222df43): silent_arms probes for ride board, arm orders, props C1/C2/S, combo, NHL in-play; d6_read slim load + fills budget; scripts/state_of_the_bot.py + allowlisted box task. #606: D6 per-sport key fix (state page printed "not computed").

## Caveats (state these, do not hide them)
- d6_read timeout cause (155 MB arm-order log loaded in full) is inferred; the fix worked on the box (exit 0), the cause was not isolated.
- Legacy NBA paper cron lines are exempted as "frozen (GG-630)", not probed.
- Legacy MLB T2/T3 passes are approximated by the t1_mlb probe.
- `when_installed` trade-off: an arm installed but never writing is undetected until its directory exists (EXP-047-S was caught only because its probe is not install-gated).
- Fills in the state page come from a budgeted lookup (25 of 1686 NBA placed orders looked up in the 02:39Z read); P&L per filled contract is on that sample, before fees. Not a verdict.

## Required lines
- surface_delta: +1 allowlisted read-only box task (state_of_the_bot_read), +1 script, +8 silent-arm probes; no new cron/service; RUNTIME_MAP regenerated (95 live components).
- pattern_sweep: swept src/ scripts/ tests/ for live writers without probes (coverage test) and for the lowercase-sport-key mismatch (only state_of_the_bot.py).
- Guardrails: no real capital, Kelly untouched, $0, no install run.

## For SW-10
- Window-maintained lines in CLAUDE.md are RED (8 days old); regenerate at wave close.
- Decide who owns the EXP-047-S silence.

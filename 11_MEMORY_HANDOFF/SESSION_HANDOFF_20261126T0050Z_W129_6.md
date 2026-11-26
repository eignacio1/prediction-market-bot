# Session Handoff — 2026-11-26T00:50Z (W129.6)

<!-- session-meta
task_id: W129.6
tier: STANDARD
timestamp: 2026-11-26T00:50:00Z
commit: 188eddf
one_line_summary: W129.6 Parts A+B merged: NFL live feed proven from box, in-play pricer replayed; Part C (shadow runner, cells) not built.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: BREADTH, PROOF
gap_measure: B1, B3, feed latency
gap_delta: none yet (B1/B3 unmoved: T4NFL cells still NOT_IMPLEMENTED; latency unmeasured until a live game)
pattern_sweep: n/a (no defect fixed; sequenceNumber-not-chronological handled in nfl_live_feed.py only, grep sequenceNumber src/ found no other NFL consumer)
surface_delta: 0 (nothing running added; no install built)
-->

**Trigger:** operator-initiated /session-end. **Last commit:** `188eddf` (main).

## Done (PRs #590, #594 merged, CI green)
- Part A: `c1_signal_ingestion/nfl_live_feed.py`, saved-game known-answer test (ARI@KC 401873067), staleness check, `nfl_live_feed_probe` box task.
- Box proof 2026-11-26T00:44Z: REACHABLE, 173 plays, 172 with wallclock, rtt ~0.2 s, no bot check.
- Part B: `quant/inplay_nfl.py`, EXP-NFLINPLAY-001 prereg (+ addendum: sigma estimator changed after first look, both reported), `scripts/replay_nfl_inplay.py`.
- Replay, 2026 scored set (70 games): model beats held-constant pregame price on ML/spread/total (CIs exclude 0).
- Market set 2025 ML, 86 games: Brier 0.1638 vs Kalshi mid 0.1642, CI [-0.0094, +0.0081] spans 0. Half-spread 0.62c. Scoring play to 3c move: median 120 s, IQR 60-420 s (n=664). Hypothesis "model beats Kalshi mid" closed (EXP-NFLINPLAY-001, parked for R&D).

## Strategic Decisions This Session
None — implementation-only session.

## NOT done (Part C) — truncated at operator /session-end
- `scripts/run_nfl_inplay_shadow.py` behind `PM_NFL_INPLAY`; RUNTIME_REGISTRY entry; write-recency alarm in healthcheck.
- Install/readback/uninstall tasks (build, do not run; add names to the writers set in `test_box_tasks.py`).
- Promote 8 T4NFL cells to SHADOW; update `tests/test_market_type_registry.py:546-552`; check `test_silent_arms.py`.
- Registry: B1/B3 unmoved until the above lands.

## Facts for the next window
- Live feed lag is UNMEASURED: finished games have none. First live games 11-26 (Thanksgiving).
- Spread/total/team-total have no Kalshi candles; team total has no free lines. Moneyline only for the market compare.
- Kalshi archive is untracked, main checkout only; replay needs `--kalshi-store`.
- No replay test beyond pricer unit tests (7 pass).

## Operator decisions:
None yet. When Part C lands, the install approval line (`nfl_inplay_install`) will go here with the surface-budget gate result; not run.

directive_conflicts: none found.
One thing pending: Part C. Resume: re-claim W129.6b, read this file, start at the shadow runner.

# Session Handoff — 2026-11-05T01:25Z (W100.1 engine lane)

<!-- session-meta
task_id: T-1710
tier: STANDARD
timestamp: 2026-11-05T01:25:00Z
commit: aa51e14
one_line_summary: W100.1: NHL same-vintage league denominator fix (-0.080 to -0.059 bias, Brier flat); NBA v2/v3 misses traced to box OOM.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH, PROOF
gap_measure: D4 (NHL engine), P2; B-029 / B-001 / B-030
gap_delta: NHL held-out total bias -0.080 -> -0.059 (results_W100_1.md); NBA v3 silent 5 of 11 games on 11-04; no verdict moved.
pattern_sweep: stale lg_f5/lg_pp denominator; swept nhl_engine/ and scripts/, only inputs.expected_xg uses it; fix is new model_pit.py, not in cron.
surface_delta: 0 (no component added or retired; nothing installed)
-->

**Commit:** `aa51e14` (PR #414).

## Strategic Decisions This Session
| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| EXP-046 not earned | Brier flat within noise, all five families | results_W100_1.md | window |

## State
- **B-029 (NHL totals):** partly fixed; stale denominator was about a quarter of the bias. Rest is season xG drift and early-season level error. Predictions over-spread (slope 0.4-0.5): challenger candidate. Kalshi comparison not run.
- **B-001 (NBA v3):** 412 rows, silent for 5 games (ATLWAS, PHIDET, MILBOS, PORPHX, TORDEN).
- **B-030:** not met. v1 11/11; v2 5/11. Cause: box OOM (21 kernel kills, ~50 MB free), not lock or schedule code.

## For the window (nothing installed)
Stagger/serialise the T1/T2/T3 shadow chains, cap the long jobs or add memory; then a v3 coverage.jsonl PR; then re-read.

## Plain English
The hockey model's low totals were partly a bookkeeping mismatch, now fixed in a new module with no accuracy change. The basketball engines' code is fine; the small server runs out of memory and kills jobs, so games went unlogged.

**One thing pending:** relieve box memory, re-run the NBA coverage readback.
**Resume:** read results_W100_1.md.

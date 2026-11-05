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
gap_delta: NHL pooled held-out regulation-total bias -0.080 -> -0.059 (results_W100_1.md, run_w100_1.py); NBA v3 silent games 5 of 11 on 11-04 slate (box readback 2026-11-05 ~01:10Z); no cell or verdict moved.
pattern_sweep: Defect = league denominator from older xG vintage than team rates. Searched nhl_engine/ (inputs.py, model.py, goals.py) and scripts/ for other lg_f5/lg_pp uses; only inputs.expected_xg uses them; merged files left unchanged, fix is the new model_pit.py. Not wired into any cron.
surface_delta: 0 (no component added or retired; nothing installed)
-->

**Trigger:** operator-initiated close-out. **Last commit:** `aa51e14` (main, PR #414 squash-merged, CI green).

## Strategic Decisions This Session

| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| EXP-046 not earned | Brier unchanged within noise on all five families | results_W100_1.md | window |

## What changed
- `nhl_engine/model_pit.py` + 4 tests: same-vintage trailing league rate. Merged model files untouched.
- `results_W100_1.md`: Part A findings, Parts B/C readback.
- No src change touches live cron; no deploy needed.

## State of each backlog item
- **B-029 (NHL totals):** partly fixed. Stale denominator removed (about a quarter of the bias). Remainder is season xG drift (goals/xG 0.966/0.999/0.989/0.947) and early-season level error; shrinkage, half-life, power-play time ruled out. Predictions over-spread (slope 0.4-0.5): candidate challenger. 2026-vs-Kalshi descriptive comparison NOT run.
- **B-001 (NBA v3):** writing (412 rows) but silent for ATLWAS, PHIDET, MILBOS, PORPHX, TORDEN; CHABKN/CHINYK 1 of 4 families. No tip-60 quote (median 14.8 min). v3 has no coverage.jsonl or unlogged_past_tip.
- **B-030 (every NBA game logged):** not met. v1 11/11; v2 5/11 complete. Cause: box OOM (151 `Killed` in cron log, 21 kernel OOM kills, ~50 MB free), not lock or schedule code.

## For the window (nothing installed)
Cut concurrent memory load (stagger/serialise T1/T2/T3 shadow chains; cap the 65-min T1 `--refresh` and 1h53m NBA T2) or add memory. Then a small code PR for v3 coverage.jsonl, then re-read.

## Plain English for the next window
The NHL model's low totals were partly a bookkeeping mismatch, now fixed in a new module with no change in forecast accuracy; the rest is year-to-year drift and early-season uncertainty. The NBA engines are not failing in their code: the small server runs out of memory when many jobs overlap and kills them, so several games went unlogged. Fix the server load first.

**One thing pending:** relieve box memory, then re-run the NBA coverage readback.
**Resume:** read results_W100_1.md and this file.

# SESSION HANDOFF — W96.1 (20261030T1549Z)

Status: PARTIAL | B-001: Part B done (v3 study + module merged), Part A pending tonight's first tips (GG-1450 OPEN); B-009 (Part C) not started | branch session/20261030T153148Z-w96-1-nba-engine-v3 -> main @ 3f42ff6 | PR #385 merged, CI green (test pass 5m39s) | v3 (availability + lineups) beats v2 held-out on spread (Brier −0.00793 [−0.01074,−0.00514]) and team_total (−0.00264 [−0.00362,−0.00161]); not moneyline; slightly worse on total.

MEASURE MOVED: D5 NBA factor classes by stage: availability and lineups aggregated -> INTERPRETED for spread and team_total (held-out, n_games 2271, source 12_EXPLORATORY/nba_engine_v3/results_W96_1.md); officials stay aggregated only (not known before price, GG-1390). Engine arms logging with rows: 0 -> 0 (no game has tipped since install; unchanged).

Stage per factor: availability INTERPRETED; lineups INTERPRETED; officials aggregated. None APPLIED (no forward arm).

Part A: box readback 14:35Z showed v1 and v2 rows = 0, no log; no NBA game tipped since install, so no silent arm exists yet. After tonight's tips (~23:00Z+, rows by ~02:00Z) request box task nba_engine_cron_readback; any tipped game with no rows = silent arm, fix first. Observed only: B-017 (store 2 days behind), B-007 (517 MB runner on 961 MB box).

EXP-044c: NOT frozen, NOT installed. Needs live_v3 runner (tip-60 injury snapshot + rotation ratings from a lagging store). Next step: build it from live_v2 helpers, freeze EXP-044c (claims spread + team_total only) before first row, register in RUNTIME_REGISTRY, install on GREEN budget read.

Deploy read-back: engine_v3.py is a new module imported by no service; box deploy log not read this session. t4-mlb decision: no restart needed.

Operator decisions: none.

Not done: granularity-index parts "rank vs history" and "matchup cross" (marked not computed); Part C B-009. Untracked large artifacts (rows csv.gz, v3_factors.parquet) deliberately not committed (reproducible).

```
task_id: T-1530
vision_pillar: DEPTH
gap_measure: D5
gap_delta: NBA availability + lineups aggregated -> interpreted (spread, team_total)
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no live component added)
```

# Session Handoff — 2026-10-27T01:39Z

<!-- session-meta
task_id: T-1190
tier: STANDARD
timestamp: 2026-10-27T01:50:00Z
commit: e8de314
one_line_summary: W88.1: GPD tails fit for T4/T1 (T1 filled not fit-able); DRAFT ADR-0076 G6 per book and sport; GG-1190..1192
gg_touched: GG-1190, GG-1191, GG-1192
adr_touched: ADR-0076
plan_deliverable_moved: no
vision_pillar: PROOF, PLUMBING
gap_measure: G6 superseding ADR 0 -> DRAFT
gap_delta: G6 ADR 0 -> DRAFT (03_DECISIONS/ADR-0076_DRAFT @ 83c57f1)
pattern_sweep: sampler double-count of tail mass fixed in the new gpd.py only (no other instance); 12_EXPLORATORY t4_* import fence fixed in run_tails.py, the only importer
surface_delta: 0
-->

**Status:** DONE (Part A + Part B). PR #337 squash-merged as 83c57f1, CI green (test pass 4m53s).

## Result
- T4 filled (69 games, 177 bets, −$37.9): 1-in-100 per-game loss $7.18 [2.98, 12.04], 17 exceedances; 1-in-1000 is extrapolation, unusable.
- T4 paper: $13.09 [10.44, 15.94]. T1 paper: $53.57 [40.49, 62.48]. T1 filled: too few exceedances (14), no fit.
- Max drawdown at 90 games, flat stakes, $1,000 bankroll: T4 filled p99 $99.6 (under the $200 kill); T1 p99 $471 even at zero edge $293 (GG-135 geometry).
- `mc_empirical_bootstrap.py` is Gaussian on daily aggregates and carries no tail information.
- Binary contracts cap per-game loss at stake; the real control is a per-game aggregate exposure cap.

## Pushback
Tails rest on 14–99 exceedances; the T1 filled tail cannot be fit. The smallest positive Kelly row (ADR-0048 0.10x) was not run as a separate simulation: loss and drawdown scale linearly with stake.

## Stage per factor (ADR-0075)
Tail risk: aggregated and interpreted; not applied (no limit changes).

## Open
GG-1190, GG-1191, GG-1192 registered. Post-merge run 40433751721 (83c57f1) was CANCELLED (superseded); read run 40434217779 (head f91c2ee) instead. Its Deploy job, if any, was not yet visible at close; PR touched no `src/`, so expected t4-mlb decision is no restart. Next window should read it.

## Operator decision (one line)
Accept, change or reject ADR-0076 as the G6 definition (per book and sport, limits as in section 4; recommendation: accept with the blanks in section 4 left blank until a positive Kelly is proposed).

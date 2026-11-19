# Handoff — W120.1 (NFL layer 3 on box rows)

<!-- session-meta
task_id: W120.1
tier: STANDARD
timestamp: 2026-11-19T05:30:00Z
commit: abf5956 (PR #532, squash-merged on green CI: guard + test)
one_line_summary: W120.1: NFL box rows now log split verdicts (130 NFL index leaves in filter_splits, late weather no longer drops a row's filters); D6 recount waits for the deploy and the next NFL slate.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH (D6 layer 3 on box rows, NFL)
gap_measure: D6 NFL wired cells (scripts/d6_read.py)
gap_delta: NFL D6 0 -> not yet measured. Baseline 20261119T0449Z_d6_read: NFL per layer [12,12,0,9,9,9,4], wired 0 of 29. Recount queued.
pattern_sweep: PIT-violation drop-all-filters pattern: only nfl_adapter had it (grep assert_pit src/ -> nba_adapter keeps its own pit_violation path, deliberately not changed, no weather-only field there)
surface_delta: 0
directive_conflicts: none found
-->

## Part A — why NFL rows had no layer 3
1. filter_splits.json held no entries for the W113.2 NFL split filters the runtime emits -> every lookup "untested" -> split_kept / split_logged_only empty.
2. A forecast stamped after the row (beyond the 120 s grace) raised PITViolation and dropped ALL filters (25 of 150 NFL_SPREAD T1 rows).

## Part B — shipped (PR #532)
- nfl_adapter: late forecast -> weather "none" (never used, no look-ahead); other filters and verdicts kept.
- build_filter_splits_w112.py --nfl-index-only: merges 130 NFL leaves from granularity_index_nfl/leaf_scores.json (frozen scoring). Table 281 -> 411 entries; every prior entry byte-identical (tested). 36 kept in the table; kept NFL leaves may change the logged arm by design, others log only.
- Tests: late-forecast tests updated, verdict-present + additive-table tests added; 493 related tests pass.
- Do NOT run the full builder without --nfl-index-only: it re-reads newer NHL/NBA results and moves existing entries.

## Part C — open
- Box requests queued on main (f1380fb): deploy_truth_read, d6_read. Result files land in 04_EXECUTION/BOX_TASKS/results/.
- Next NFL slate: weekend of Nov 22-23. Rows from before deploy carry no verdicts. The window recounts D6 after that slate; report NFL 0 -> N named plus the one cause per unwired NFL cell then.
- Unmeasured: whether kept leaves wire all four one-layer-away cells (NFL_GAME_TOTAL T3, NFL_SPREAD T1/T3, NFL_TEAM_TOTAL T3). Only 4 NFL leaves are kept (3 team-total, 1 spread); layer 3 counts logged-only too, so rows should count once a leaf is hit.
- Hypothesis closed (EXP-W113.2-NFL-SPLITS-01, parked for R&D) stands; this block adds no new closure.

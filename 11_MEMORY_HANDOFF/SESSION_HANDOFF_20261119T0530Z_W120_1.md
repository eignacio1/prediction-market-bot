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

## Strategic Decisions This Session
None - implementation-only session.

## What changed (PR #532)
- Cause 1: filter_splits.json had no entries for the W113.2 NFL split filters, so lookups were "untested". Cause 2: a forecast stamped after the row dropped ALL its filters (25 of 150 NFL_SPREAD T1 rows).
- Fix: late forecast -> weather "none" (no look-ahead), other filters kept; 130 NFL index leaves merged additively (281 -> 411; 36 kept). Never run the builder without --nfl-index-only.

## One thing pending
D6 recount: box requests (deploy_truth_read, d6_read) are queued. Next NFL slate Nov 22-23; then report NFL 0 -> N named plus the one cause per unwired cell. Unmeasured until then.

## Resume
`git fetch origin && ls -t 04_EXECUTION/BOX_TASKS/results | head`

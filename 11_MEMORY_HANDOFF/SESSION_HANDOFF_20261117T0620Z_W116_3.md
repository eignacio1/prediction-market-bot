# Handoff: W116.3 (D6 finish), PARKED at ~85% context (operator asked us to park)

Status: PARTIAL. B-091 / B-092 in progress. Code is on branch `w116-3-code`; PR #503 has CI pending and is NOT merged.

## Done
- **Box reads** (stem 20261117T060933Z, box HEAD 48e3cada, includes #502):
  - t4-mlb runs box HEAD code; decision: no restart needed.
  - d6_trace_read covers 3 days and 38,796 arm rows.
- **D6 baseline on the box: 3 of 117 wired, all NBA.**
  - Per sport: mlb 0/42, nba 3/25, nfl 0/29, nhl 0/21.
  - Cells missing exactly one layer:
    - NBA_GAME_TOTAL T2 lacks 7 fills.
    - NBA_TEAM_TOTAL T3, NFL_GAME_TOTAL T3, NFL_SPREAD T1/T3 and NFL_TEAM_TOTAL T3 lack 3 filters.
- **Router ERROR root cause (GG-1939):**
  - LeafMap.row_for built a row without market_ticker / yes_bid / yes_ask.
  - So the MODEL_FADE branch, via retro_route.side_net, raised KeyError('market_ticker') whenever p_yes was present.
  - Box: NBA 2,851 + NFL 181 ERROR rows (KeyError) over 3 days.
  - Fix in PR #503: the router passes ticker and book; with no book the result is NO_BET `model_fade_needs_ticker_and_book`.
  - Fuzz: 0 errors in 5,760 runs.
- **Layer 6:** arm_orders.act calls row_decision on every non-ERROR routed row before any skip. coverage.order_evidence counts layer 6 only when size_for.arm is not NO_BET.
- **d6_read:** adds `wired_cells` (named) and `unwired_cause` (per sport, first missing layer → cells).
- **Tests:** 622 passed on the decision-tree selection; precheck 93 passed.

## Next session, in order
1. PR #503: merge if its CI is green on the current head. Then request deploy_truth_read (record the t4-mlb decision), then d6_read. Report D6 with named cells, unwired causes and ERROR rows before/after (before: 3,032 KeyError in 3 days).
2. **Part A not written:** the three trace tables (NBA / NFL / NHL). Source: scratchpad trace (re-request d6_trace_read if it is lost).
3. **Coverage-rule finding (unresolved):**
   - The box reports L3_rows_with_kept_split = 0 in every cell.
   - Yet a local replay of the NBA supply against filter_splits gives KXNBATOTAL 6 kept (arms conflict, so arm None) and KXNBASPREAD 1 kept (RIDE).
   - The layer-3 rule credits a cell from the split FILE, not from rows; the box rows show no kept split fired. Trace why (router `split` is set only after decide; check thin/unknown leaves and the trace's field read) before tightening layer 3. A tightened rule may drop D6.
   - NFL layer 3 = 0 because 0 of 28 NFL splits are kept; that is a routing result, not a box defect.
4. **Other trace findings, unfixed:**
   - NBA_PLAYER_POINTS filters "nba_event_ticker_unparsed".
   - NHL_PUCK_LINE T2/T3 rows carry no router.
   - The NHL store is absent on the box.
   - Arms skipped with size_zero (day cap).
5. NHL store shrink (streamed compile, ≤2 seasons, compact state) and a peak-RSS measure. Write the install task + approval sentence ONLY if it is under ~600 MB. Not started.
6. Register GG-1939..GG-1941 (+ GG-1951..1953 claimed) in GOVERNANCE_GAP_LOG.md. Not done.

pattern_sweep: row_for has one caller (router._route_leaf); the side_net row contract was grepped in decision_trees/.
surface_delta: 0 (no new service, cron or install).
vision_pillar: DEPTH (D6)
gap_measure: D6 cells wired end to end on the box
gap_delta: 3 -> 3 so far (fix not yet deployed)
directive_conflicts: none
Operator decisions: none yet; an NHL store install will be proposed only if it measures under ~600 MB.

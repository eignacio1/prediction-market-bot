# Handoff — W116.3 (finishes 115.3: B-091 + B-092) — 2026-11-18T01:16Z

Status: PARTIAL, parked. Code done and tested. PR #507 is red only because of main's backlog file (GG-1956). This handoff supersedes SESSION_HANDOFF_20261117T0620Z_W116_3.md.

## State
- **B-091 (Part A, trace + coverage rules): DONE.**
  - `04_EXECUTION/W116_3_D6_TRACE_TABLES.md` (6009f77) has the NBA / NFL / NHL tables and 5 coverage-rule findings.
  - Headline finding: layer 3 credits a cell from the split *file*, but the box's L3_rows_with_kept_split = 0 in every traced cell (GG-1951).
- **B-092 (Part B, fixes):**
  - **Merged earlier:**
    - Router ERROR fix: KeyError 'market_ticker' from LeafMap.row_for (GG-1939).
    - row_decision on every routed row (layer 6).
    - d6_read names the wired cells and the cause per unwired cell.
    - These deployed at 53c83e86.
  - **Open, PR #507 (`w116-3-nhl@632530d`):**
    - NHL store shrink: streamed 25-game chunks, two seasons, compact state.
    - Paused cron plus `nhl_event_store_install` (readback, uninstall, budget probe, allowlist, tests).
    - d6_trace_read gains `error_after` and `error_rerun_sample`.
    - Tests: 44 local passed; precheck 65 passed.
    - CI 44213394562: 5812 passed, 3 failed. All 3 failures come from main's ROLLING_BACKLOG.json ("duplicate order 16 (B-018)"; B-074 and B-018 both hold order 16). Still invalid at 01:16Z.
- **Part C (box, 010409Z, ran 01:05Z on 53c83e86): D6 = 3 of 117.**
  - Wired: NBA_GAME_TOTAL T3, NBA_SPREAD T2, NBA_SPREAD T3.
  - NFL 0, NHL 0, MLB 0.
  - Cause of each unwired cell:
    - NFL game families: layer 3, because 0 of 28 NFL splits are kept. That is a routing result, not a defect.
    - NHL: layer 3, because the store is absent on the box (#507 plus the install).
    - NBA_TEAM_TOTAL T1-3: layer 3.
    - NBA_SPREAD T1: layer 4.
    - NBA_GAME_TOTAL T1: layer 6.
    - NBA_GAME_TOTAL T2: layer 7 (fills).
    - T4/T5, moneylines and props: layer 1 (no model p).
    - MLB: off season.
- **ERROR rows (3-day window, all logged before the fix):** NBA 3,096, NFL 181, NHL 97.
  - Re-running the first ERROR row per sport on today's code raises nothing.
  - A true post-deploy count needs #507 deployed, which adds error_after.
- **NHL store memory, measured locally:** peak RSS 2,049 → 270 MB for the compile and 913 → 318 MB for the read. That fits under the ~600 MB bar.
  - Box: 961 MB RAM, ~126 MB free, swap in use. The risk is written into the approval item.
- **t4-mlb:** runs box HEAD code. No restart needed.
- **GG register:**
  - GG-1939 / 1940 / 1941 registered. Progress notes on GG-1939, 1951 and 1953.
  - GG-1956 (HIGH, OPEN) is new: the backlog file is invalid on main. The fix belongs to the strategic window.

## Next, in order
1. Once main's `python3 scripts/rolling_backlog.py --check` passes: rebase `w116-3-nhl` onto main (our branch; force-with-lease), push, wait for green on the head, squash-merge #507.
2. After the merge, request deploy_truth_read, d6_read and d6_trace_read. Read error_after / error_rerun_sample for the "ERROR after" count, and record the t4-mlb decision.
3. `nhl_event_store_install` runs ONLY after the operator approves it by name. Its approval sentence is item 4 in "Needs your decision". After it runs, the next d6_read should move NHL GAME_TOTAL T3 and PUCK_LINE T3 off layer 3, if a kept NHL split exists.
4. GG-1951: decide whether layer 3 must require a kept split to fire in rows (not just exist in the file). Tightening it may drop the NBA 3. Trace first.

## Operator decisions
- Approve `nhl_event_store_install`. This is a proposal: it fits at 318 MB read, but the box has ~126 MB free.
- GG-1956: the strategic window must fix the duplicate order 16 in ROLLING_BACKLOG.json (B-074 vs B-018). Until then, every code PR is red.

pattern_sweep: row_for has one caller (router._route_leaf). The side_net row contract was grepped across decision_trees/. The ERROR re-run sample covers every sport's cells.
surface_delta: +1 cron line (nhl_event_store, PAUSED in RUNTIME_REGISTRY; not installed), 0 live.
vision_pillar: DEPTH (D6)
gap_measure: D6 cells wired end to end on the box; router ERROR rows; NHL store peak RSS
gap_delta: D6 3 → 3 (NBA_GAME_TOTAL T3, NBA_SPREAD T2, NBA_SPREAD T3); ERROR re-run 0 raising (before: 3,374 rows in 3 days); NHL store 2,049→270 MB (compile), 913→318 MB (read)
directive_conflicts: "merge on green" vs a main branch whose backlog file breaks CI for every PR. Did not edit ROLLING_BACKLOG.json (block rule); registered GG-1956 and parked.

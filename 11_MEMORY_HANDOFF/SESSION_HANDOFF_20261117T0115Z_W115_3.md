# W115.3 handoff - STOPPED EARLY (usage limit), 2026-11-17 ~01:15Z

Status: PARTIAL - claim only; no code changed, no PR, nothing installed, nothing run on the box.
Ticket: B-091 + B-092 open. Claim: GG-1939..GG-1941 (none used). Branch: session/20261117T010353Z-w115-3-d6-one-game (no commits beyond this file).

## Done
- Rules read (04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W115.md), worktree, claim pushed 01:05:43Z.
- Box re-read from the window's 00:57Z results (04_EXECUTION/BOX_TASKS/results/20261117T005715Z_*): D6 3 / 117 (NBA),
  box HEAD 2472da23 = origin/main, SURFACE BUDGET GREEN, 94 live, arm-order log 60,942 rows, last row 00:51:50Z.
- Read: scripts/d6_read.py, decision_trees/coverage.py, filter_supply.py, shadow_route.py, row_sizing.py, nfl_engine/providers.py.

## Findings so far (from reading code against the box read; NOT yet traced on a real game)
1. coverage.d6_layers judges layers 1, 2, 4 and 5 from the repo's leaf_map.json, not from rows on the box. Only layers 3, 6, 7
   read the box. So "9 of 25 NBA cells have layer 1" is a statement about the leaf map, not about what a logged row carried.
   An evidence rule that a box row cannot fail is a finding in itself (Part A's last sentence). Not registered as a GG yet.
2. arm_orders_read: UNROUTED NHL skips 5,513 (was 1,415 in the block text); ERROR / unrouted NBA 5,193 and NFL 197 -
   router_fields returns branch ERROR with only the exception type name, so the cause is not visible in any current read.
3. default_nfl_providers() returns None only on FileNotFoundError from NflProviders(); the three snapshot files are committed,
   so on the box the likely cause is a different exception path or a missing file among nfl_schedule.csv / nfl_team_games.csv /
   nfl_snapshot_meta.json at the deployed path - UNVERIFIED, needs the trace.
4. Skips are dominated by size_zero "cap binds: day" (FADE 1,703, MOMENTUM 1,738, RIDE 4,111), not the daily breaker (690 total).

## Left (all of Parts A, B, C)
- A: write a read-only trace task (one game per sport through 7 layers: shadow ledger row, router fields, filters note,
  size_for, arm-order rows, fill lookups), allowlist it, PR, run it on the box, write the three trace tables.
- B: NHL rows routed; NFL provider on the box; row-level size_for on every routed row; layer 1 / 2 gaps; NHL event store
  install task (prepared, not run).
- C: recount, name wired cells, approval sentences in ACTIVE_QUEUE.md "Needs your decision".

vision_pillar: DEPTH · gap_measure: D6 wired on the box · gap_delta: 3 -> 3 (no change; source d6_read 2026-11-17 00:59Z)
pattern_sweep: n/a (no defect fixed) · surface_delta: 0 · directive_conflicts: none checked (OPERATOR_DIRECTIVES.md not read)

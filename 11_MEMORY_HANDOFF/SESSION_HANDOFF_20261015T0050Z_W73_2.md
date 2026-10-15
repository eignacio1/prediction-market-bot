<!-- session-meta
task_id: T-960
tier: STANDARD
timestamp: 2026-10-15T00:50:00Z
commit: 31dd1de
one_line_summary: W73.2 DONE: NFL taxonomy (Part A) and event-level data layer with point-in-time contract (Part B) merged; weekly Actions rebuild verified end to end.
gg_touched: GG-730, GG-731, GG-732, GG-733, GG-734
adr_touched: none
plan_deliverable_moved: yes
vision_pillar: DEPTH
gap_measure: D4 (NFL engine stage), D1
gap_delta: D4 NFL: none -> event-level data layer built (event_store_manifest.json: 165 ok files, 0 failures, 2026-10-15). D1 NFL: 20 factor classes mapped, 15 buildable free today.
-->

# SESSION HANDOFF W73.2 (2026-10-15) — supersedes SESSION_HANDOFF_20261015T0000Z_W73_2.md (PARTIAL)

Status: DONE | branch session/20261014T234416Z-w73-2-nfl-data-layer | PR #258 squash-merged at 07ebe26, CI green (run 38661274611) | one-line result: free nflverse event store (plays, participation, FTN charting, snaps, injuries, depth charts, rosters, PFR, officials, schedule; 1999-2026) built reproducibly, with a point-in-time contract and per-source/season checks, rebuilt weekly on Actions.

MEASURE MOVED: D4 NFL none -> event-level data layer built (02_ARCHITECTURE_DESIGN/NFL_ENGINE/event_store_manifest.json, 2026-10-15); D1 NFL none -> 20 classes mapped / 15 buildable (FACTOR_TAXONOMY.md, 2026-10-14).

Verification:
- `nfl_event_store.yml` dispatched on main (run 38661767620): build, checks, 23 tests on real data, schedule snapshot upload to release `nfl-games-snapshots`, manifest commit (31dd1de), all green.
- CI failures on the PR were mine and are fixed: GG-179 skip ceiling (real-store tests now not collected when store absent) and the runtime-registry check (workflow registered, reviewed, DEPTH).
Deploy: deploys are VPS-cron now (W67.3), no Actions Deploy job. Merge only adds new modules; t4-mlb imports none, so no restart needed.
Gaps (registered, none bought): GG-730 no 2026 participation file (picked up automatically when published), GG-731 no coordinator table, GG-732 no publication time for injuries/officials, GG-733 schedule lines overwritten (snapshots now kept), GG-734 no weather forecast archive.
Not done / next: stage 2 (feature builder through `PointInTime.view`) is a separate block. Nothing here touches orders, stakes, kelly or the ledger.
Operator decisions: none.

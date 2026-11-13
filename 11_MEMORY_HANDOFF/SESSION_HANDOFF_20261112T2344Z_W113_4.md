<!-- session-meta
task_id: W113.4 (B-087)
tier: STANDARD
timestamp: 2026-11-12T23:44:00Z
commit: 70a249a
one_line_summary: W113.4: bot reads Muse archive read-only, grades it (4 verified, 3 mismatch), 12 NBA index entries; PR #494 held on red main CI.
gg_touched: GG-1930, GG-1931, GG-1932
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D1, D-06 (NBA index entries)
gap_delta: NBA index entries 24 -> 36 (12_EXPLORATORY/archive_intake/entries_summary.json @ 70a249a)
pattern_sweep: fence scan (tests/test_exploratory_isolation.py) flagged write-shaped calls in 12_EXPLORATORY/archive_intake/*.py; swept the folder, all writes now via safe_out
surface_delta: 0
-->

# Session handoff - W113.4 (B-087), 20261112T2344Z

**Status:** Parts A, B, C built and pushed on PR #494 (branch session/20261112T230415Z-w113-4-archive-intake). NOT merged: CI is red only on tests/test_w109_3_props_shadow_install.py::test_registry_entry_is_paused_and_task_is_allowlisted, which also fails on main (run 43326790475). The test still expects status paused; the registry now says live after the 11-12 install approvals. Not a 113.4 file, not mine to edit. Merge PR #494 once main is green.

**Tables graded** (details in 12_EXPLORATORY/archive_intake/GRADES.md)
- VERIFIED: NBA Opponent Shooting by distance (All, 540/540); NBA Traditional Home/Road (mostly); NHL games/goals/takeaways/giveaways exact; NHL shots/misses/hits/faceoffs within 1%.
- MISMATCH: NBA home/road for neutral-site teams; NBA turnovers per game; NHL penaltiesFor (GG-1930).
- UNCHECKABLE: zones, quarters, clutch, tracking, hustle, Synergy, lineups, referees, xG family, 5on5, NHL goalie snapshots (GG-1931).

**MEASURE MOVED:** archive table families graded 6 recomputed (4 VERIFIED, 3 MISMATCH items); NBA index entries 24 to 36; D1 NBA/NHL unchanged until 113.1 wires filters; D-06 advanced.

**Filter interface for 113.1:** archive_intake.nba_distance_filters.distance_filters(home, away) returns "<name>@total" / "<name>@side" leaves; team percentiles in 12_EXPLORATORY/archive_intake/team_percentiles.json. 54 leaves scored on 43,056 shadow rows, 0 BH survivors, routed to NO_BET provisionally (GG-1932).

- pattern_sweep: fence scan (tests/test_exploratory_isolation.py) now clean for archive_intake scripts; grade scripts write only through safe_out.
- surface_delta: 0
- vision_pillar: DEPTH (D1, D-06) / gap_measure: GG-1930..1932 opened / gap_delta: +3
- directive_conflicts: none
- Pushback: none. Surface: main Test Suite red since the install approvals. Dependencies: 113.1 owns filter_supply.py.
- Classifier refusals: (1) first commit+push denied as Out-of-Place Publication; (2) commit of fixture rows copied from the private archive denied as Sensitive-Source Provenance. Resolved by synthetic fixtures; not worked around.
- No *_install box task run. Claim to close on merge.

# SESSION HANDOFF — W76.4 (B74-A Session 2) — PARTIAL, NOT MERGED

<!-- session-meta
task_id: W76.4
tier: STANDARD
timestamp: 2026-10-16T00:30:00Z
commit: a30625f
one_line_summary: W76.4 runtime map live on scan, /project, Live Terminal, Visual Dashboard (76/76 reviewed); PR #266 blocked on main CI
gg_touched: GG-742, GG-743, GG-753
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: registry entries reviewed against the box; live components with no alarm; SURFACE BUDGET live on both dashboards
gap_delta: reviewed 0/76 -> 76/76 (RUNTIME_REGISTRY.toml vs box, 2026-10-15); no-alarm 21 -> 0 unexplained, 9 with written reasons (runtime_registry.py live); SURFACE BUDGET GREEN computed live (box HEAD f2a980ad) — shown in scan, /project, Live Terminal, Visual Dashboard in PR #266 (not yet deployed)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

## Strategic Decisions This Session
None — implementation-only session.

## State
PR #266 (branch session/20261015T234931Z-w76-4-runtime-map-live @ a30625f): Parts C and D built. Full suite 4227 passed locally (two files, test_seat_interface and test_tensions, cannot import tomllib on local py3.9; unrelated; not checked on CI's 3.12).
NOT merged: CI `test` fails on `tests/test_exploratory_isolation.py::test_exploratory_file_is_isolated[availability.py]` and `[part_a_avail.py]` (write-shaped .copy()/.replace() not routed through safe_out()). Both files are 76.2's (12_EXPLORATORY/nfl_engine); main's own run at 1217dfb failed identically. Out of my permitted files, not fixed.

## Remaining (after main is green)
Re-run CI on #266, merge, read the Deploy job summary and record the t4-mlb decision, restart pmbot-web-dashboard, curl /project and / (check 390px, no horizontal scroll), paste results.

## Findings
t4-mlb.timer enabled but dead since 2026-07-04 (service runs persistently); MLB T1 `--refresh` shadow job in the fragment is not installed on the box; nhl_goalie_probe END_DATE has passed.

## One thing pending
Main CI green (76.2 safe_out fix), then merge #266 and do the deploy read-back.

## Resume
`gh pr checks 266`; then Remaining above.

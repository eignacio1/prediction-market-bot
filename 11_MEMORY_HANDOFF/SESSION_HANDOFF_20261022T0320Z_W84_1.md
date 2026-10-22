<!-- session-meta
task_id: W84.1
tier: STANDARD
timestamp: 2026-10-22T03:20:00Z
commit: 15ffbd8
one_line_summary: W84.1: dashboard cache (/project 50s->0.25s) + NBA injury-report relay live on box (GG-1030); Part C not done.
gg_touched: GG-1030
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING, DEPTH
gap_measure: PLUMBING (dashboard at cap); D5(b) NBA lineup factor testable on paper -> accruing
gap_delta: D5(b) NBA lineup: capture now finds official reports from the box (checks.jsonl 2026-10-22T03:15:46Z report 2026-10-21 23:00, 92 rows); accrual starts, not yet a scored look. Dashboard /project 50s -> 0.247s (dashboard_pages_read 2026-10-22T02:46Z)
pattern_sweep: n/a (no defect fixed; dashboard cache/heap pattern applied only to web_dashboard.py, other services not checked)
surface_delta: +1 workflow (nba_ir_relay.yml, registered); the 3 NBA preseason entry retirements NOT done
-->

# SESSION HANDOFF — W84.1 (stopped after Part B at operator's request)

**Part A ✅** PRs #318, #320: dashboard serves from a background-refreshed cache, malloc trim and arena cap. MemoryMax left at 128M (box has 961 MB RAM; steady anon ~61 MB, build peak touches the cap, oom_kill 0).
**Part B ✅** PRs #321, #323, #324: GitHub runner relay stores the official PDFs untouched (sha256 equal to a direct fetch on 2 reports) plus manifest on `data/nba-injury-reports`; capture falls back to it only if the direct fetch yields nothing. Pre-registration, source, parsing, 15-min cadence unchanged. First two dispatches failed (runner lacked `requests`); fixed, third succeeded.
**Caveat:** relay runs :01/:16/:31/:46 (GitHub cron jitter) vs box :03/:18/:33/:48, so detection can lag a slot; may shift `book_after` timing slightly.
**Part C ❌ NOT DONE:** install gate fix + test + gap entry + retire 3 NBA preseason registry entries. GG-1050..1054 unused.

## Strategic Decisions This Session
| None — implementation-only. |

**Factor stage:** NBA lineup/injury: aggregated (accruing); not interpreted/applied.
**One thing pending:** Part C.
**Resume:** `scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`, then block 84.1 Part C.

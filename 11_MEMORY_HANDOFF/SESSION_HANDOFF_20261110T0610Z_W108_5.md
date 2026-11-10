# Session Handoff — 2026-11-10T06:10Z (W108.5)

<!-- session-meta
task_id: W108.5
tier: MICRO
timestamp: 2026-11-10T06:10:00Z
commit: 05c5522
one_line_summary: W108.5 partial: dashboard read tasks merged (#455); HEAD-keyed /visual rebuild + footer in PR #458, unmerged, box reads and Part C not run.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: PLUMBING (red): /visual served-build age behind main; dashboard memory peak
gap_delta: none measured - box reads not run (before/after both outstanding)
pattern_sweep: n/a (no defect fixed yet; Part B is unmerged). Swept: _serve_cached callers and the str+bytes json.dumps pattern in web_dashboard.py only.
surface_delta: 0 (4 READ box tasks + 1 read-only script; no cron/service added)
-->

**Trigger:** operator going to sleep, asked for wrap-up. **Status: PARTIAL, TRUNCATED.**

## Strategic Decisions This Session
None - implementation-only. MemoryMax NOT changed; no install task prepared.

## Done
- PR #455 MERGED (a8003f6): read tasks `dashboard_visual_headline_read`, `dashboard_journal_read`, `dashboard_cgroup_read`, `dashboard_build_peak_read` + `scripts/dashboard_build_peak.py`.
- PR #458 OPEN (05c5522): `web_dashboard.py` /visual and /project cache keyed on checkout HEAD; failed rebuild logged, last-good kept, retry 15 s, `dash-build` footer (BEHIND / LAST REBUILD FAILED); /api/data streamed encode. Tests: 8 new + related suites pass. Not merged: CI result unread.

## NOT done
- Part A box reads never run; the one-sentence cause is UNSTATED. Hypothesis only: page served from TTL cache after a docs-only pull, refresh request-triggered (unconfirmed).
- Part C (headline marker, memory headroom) not run; no deploy_truth_read / t4-mlb decision recorded.
- Memory peak before/after unmeasured; MemoryMax decision open (unit is `scripts/pmbot-web-dashboard.service`, MemoryMax=128M).
- ACTIVE_QUEUE row not updated.

## Incident
I ran an unscoped `git stash` in my own worktree (violates Hard Rule 10); popped immediately, nothing lost, no other session's files touched.

## One thing pending
Read PR #458 CI; merge only if green on its current head. Then push request files for the four reads, quote output, state cause.

## Resume
`gh pr view 458`; worktree `PM-worktrees/20261110T054159Z-w108-5-dashboard-stale`.

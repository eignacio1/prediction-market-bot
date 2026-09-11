# Session Handoff — 2026-09-11T15:00Z

<!-- session-meta
task_id: T-541
tier: STANDARD
timestamp: 2026-09-11T15:00:00Z
commit: 982bb25
one_line_summary: Dashboard "Cannot fetch data" blind-panel incident (OOM-kill + latency + CPU throttle) fully root-caused, fixed, deployed, and live-verified — GG-270/GG-272/GG-273 all RESOLVED
gg_touched: GG-270, GG-272, GG-273
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** dashboard "Cannot fetch data" on every panel, MLB panels stuck Loading. TIER: SHORT. Deliverables: localize, root-cause, fix, verify like an operator.

## Status: COMPLETE, deployed, live-verified, reported

## Strategic Decisions
| Decision | Rationale |
|---|---|
| Raised `CPUQuota` 10%→50% (GG-273) | Operator-authorized scope exception; 10% throttled the fix to ~3.8-4.4s wall despite ~0.39s real CPU |
(Full narrative in `DECISION_LOG.md` — T-541/GG-273 `982bb25`; T-539/GG-270, T-540/GG-272 from earlier segments.)

## What was done
- **GG-270:** root cause = unbounded `json.load()` of 37.8MB `paper_portfolio_mlb_t4.json`, dominated by unused `rejected_positions` (~88%) → OOM loop under 128M cap. Fixed via O(1) `_strip_json_array_key()` + per-key `safe()` isolation.
- **GG-272:** verification found a latency regression in the strip path + full-scan tail reader; fixed via backward-chunked `_read_tail_lines()`.
- **GG-273:** still ~3.8-4.4s after above; root cause `CPUQuota=10%`. Raised to 50%. Deploy exposed a new gap: `/etc/systemd/system/...service` is a stale copy not synced by `git pull` — needs manual `cp`+`daemon-reload`+`restart`, now documented.
- **Final verification:** 5x curl HTTP 200 @ 0.733-0.879s, non-null MLB payload, `cpu.stat` confirms throttling drop (~3.38s→~0.40s/req), cron/archiver untouched. 121/121 tests (not re-run this segment).
- Flagged, not resolved: GG-269 (concurrent session's overlapping OOM gap) — cross-referenced, left for fresh re-check.

## Files touched
`scripts/web_dashboard.py`, `scripts/pmbot-web-dashboard.service`, tests, `GOVERNANCE_GAP_LOG.md`, `DECISION_LOG.md`.

## TODO_NEXT/MEMORY_BANK/PLAN
No edits — operational C8 bug fix, no gate/test-count/phase change, not a tracked deliverable.

## One-thing-pending
None — all four deliverables complete and reported. Next open item: fresh GG-269 re-check.

## Resume command
`git pull` on `main` (already merged, `982bb25`); no active work remains on this branch.

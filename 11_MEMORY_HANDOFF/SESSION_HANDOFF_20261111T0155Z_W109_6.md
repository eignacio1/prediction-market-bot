# SESSION HANDOFF — W109.6 RED ALERT (demo-fill forward test stalled since 2026-11-05)
<!-- session-meta
task_id: W109.6
tier: STANDARD
timestamp: 2026-11-11T01:55:00Z
commit: 6ac4f54
one_line_summary: W109.6: demo-fill stall was an un-epoch-gated markout turn-off; gated (#469-471), zero-orders alarm live, re-arm awaits approval.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E1 - days of forward test lost (5: 11-06..11-10); cause found; alarm live
gap_delta: cause + alarm delivered; E1 stays 0 new fills until re-arm (box healthcheck 2026-11-11T01:48Z)
pattern_sweep: markout_c called only in demo_fill_forward_report.py (grep scripts/ src/ tests/); no other un-gated markout turn-off found; other reports' epoch handling not swept.
surface_delta: 0 (check 11 inside registered healthcheck cron; 2 allowlisted bridge tasks, no cron)
-->

Rules quoted: `# Wave 109 common rules`

**Status: DONE** | branch session/20261111T011603Z-w109-6-demo-fill-red | PRs #469 #470 #471, CI green on each head, merged | box read back: HEAD dc6f95e3 (vps_deploy.log 01:48Z), t4-mlb restart decision not_needed.

## Part A — verdict: ARTIFACT
The 2026-11-05 `treatment_markout_30m_worse_than_control` turn-off tripped on pre-GG-1771-epoch data. The markout check used the 2026-10-21 collector epoch (`EPOCH.json`), not the GG-1771 floor; the cancel-failure/orphan checks were already gated. The markouts store is append-only (30,935 rows, last written 11-06 05:54Z), so the same rows re-tripped it daily, and `deploy/demo_fill.override.env` (both switches `off`, written 11-05 11:43Z) is sticky until deleted.
Recomputation (as run, since 10-21, all sides): NBA treatment−control −0.0305, se 0.010, upper95 −0.014, n 2777/561, judged (JUDGED_N 550) → TRIP. YES-only: +0.007, not judged (2019/286). NO-only: −0.129, not judged (758/275). Post-GG-1771 fills: 5, all YES — **there is essentially no clean post-epoch markout data.** The NO-side mirror-pricing link is consistent with, not directly proven by, this split. NFL holds; NHL not judged.

## Part B
`build_report`: markout epoch = later of EPOCH.json and `epoch_floor` (GG-754 pattern); planted pre-epoch-row test. Override file NOT touched. Re-arm prepared: bridge tasks `demo_fill_rearm_check` (read-only) and `demo_fill_rearm` (moves the override aside to logs/, refuses if the epoch-gated report still trips).

## Part C
Healthcheck check 11 (`pregame_shadow/demo_fill_stall.py`): WARN when 0 `shadow_order` in 24h while any game-market arm logged rows; names override file + turn-off text. First cut (#469) read 0 ledger files on the box (missing `SPORT_` prefix) — caught by reading the healthcheck after deploy, fixed in #470. Box now: `[WARN] demo-fill stall: DEMO ORDERS = 0 ... (NBA, NHL): demo_fill.override.env present ... treatment_markout_30m_worse_than_control`; `HEALTHY: 0 faults, 1 warning`.
Note: 3 pre-existing tests in test_healthcheck.py fail only on the operator laptop (disk 90%, check 10); CI green.

## Meta
vision_pillar: EXECUTION
gap_measure: E1 — days of forward test lost (5: 11-06..11-10); cause found; alarm live
gap_delta: cause + alarm delivered; E1 stays 0 new fills until re-arm
pattern_sweep: `markout_c` is called only in demo_fill_forward_report.py (grep scripts/src/tests); no other un-gated markout turn-off found. Same defect class (a sticky turn-off with no health signal) is now covered by check 11. Not swept: other reports' epoch handling.
surface_delta: 0 components (new check inside the registered healthcheck cron; 2 allowlisted bridge tasks, no cron). Budget unchanged GREEN at last read.
Reserved IDs: claim used TBD (violation of the claim rule); no T/GG numbers consumed; recommend registering GG for "turn-off check not epoch-gated + no zero-orders alarm" (resolved here).

## Operator decision (one line)
Re-arm: approve bridge task `demo_fill_rearm` by name (run `demo_fill_rearm_check` first) — recommended: yes; caveat, the next markout look has ~no clean data, so the forward test restarts at n≈0 post-epoch.

# Session Handoff — 2026-10-06T00:28Z

<!-- session-meta
task_id: T-689
tier: STANDARD
timestamp: 2026-10-06T00:28:00Z
commit: 7f3507e
one_line_summary: W56.2 Live Terminal NOW tab: decision stream + T1/T4M-PROJ drawdown vs 20% kill switch, live on VPS (PR #167, #169).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Status:** DONE. PRs #167 (ba2fe33) and #169 (1f15ebf) merged, CI + Deploy green; only `pmbot-web-dashboard` restarted (t4-mlb restart: not_needed). Full suite 3711 passed. Read-only change; no order/stake/kelly touched.

## Strategic Decisions This Session
| Decision | Detail |
|---|---|
| WOULD-FIRE definition | No repo fire rule exists; chose fee-adjusted net edge > 0, labelled shadow-only. Operator may redefine. |

Results + screenshots: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W56_2_live_terminal_results.md`.

## One thing pending
Operator to decide/route: (1) why 842+ open paper positions with $0.55–$1.00 sizes exist at kelly 0 (uninvestigated, no GG registered); (2) `jsonlines` missing in VPS dashboard python (C4 tile "not instrumented"); (3) blank empty-ticker cycle rows, phone status-bar overflow.

## Resume
`scripts/new_session_worktree.sh "<slug>"`, then register the GG items above.

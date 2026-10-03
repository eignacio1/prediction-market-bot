# Session Handoff — 2026-10-03T01:55Z

<!-- session-meta
task_id: 49.1-49.3
tier: STANDARD
timestamp: 2026-10-03T01:55:00Z
commit: 077558b1
one_line_summary: 49.1-49.3 (cloud): NFL+MLB shadow code, 48.3 dashboard fixes and NHL prereg landed on main; arm_shadow_crons.sh written; GG-400..GG-429 registered; nothing deployed (VPS unreachable from cloud).
gg_touched: GG-400..GG-429
adr_touched: ADR-0070 (landed PROPOSED)
plan_deliverable_moved: no
-->

**Trigger:** operator-requested close-out; cloud session, no VPS/Kalshi/NHL-API access.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| 48.3 code landed, nav/handoff files left on its branch (filename collision) | DECISION_LOG 2026-10-03 |
| arm_shadow_crons allowlist widened to inert paths only; live-reachable files need --allow | DECISION_LOG 2026-10-03 |
| Dashboard goes NOT LIVE (blank panels+badges) after 2 missed refreshes | DECISION_LOG 2026-10-03 |

## What changed (main @ 077558b1)
- 49.1: NFL (7 commits) + MLB (4) shadow code landed; suite 3596 passed, 15 sandbox-network failures only. NFL reached main before its suite ran via claim_session.sh pushing HEAD (GG-419).
- 49.2: real-browser check on fixtures; NOT LIVE fix + favicon 204; evidence in exp_output/dashboard_checks/.
- 49.3: EXP-036 prereg merged unchanged (0902d326); GG-400..GG-429; DECISION_LOG entries.
- Bet count / G6 progress: not re-checked this close-out.

## One thing pending
Local session: `bash scripts/arm_shadow_crons.sh` (review the 14 refused files, pass --allow per path), deploy dashboard, restart pmbot-web-dashboard only, re-run browser_check_dashboard.py against it. T1 MLB `--include-postseason` needs an operator authorization line.

## Resume
`git fetch origin && git checkout -B work origin/main`, read this file. Stray branches (not mine, not merged): session/20261003T000917Z-eyes-and-nhl (48.3 handoff), session/exp037-nfl-land and ...-rebased-0e, session/20261002T222218Z-fly-nfl-pregame — content landed, refs remain.

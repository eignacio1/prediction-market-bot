# Box task `deploy_truth_read` — 20261118T023410Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T023410Z_deploy_truth_read.toml`
- note: Operator approved nhl_event_store_install 2026-11-17 17:45 PT (yes approve on all 3). PR #507 merged 02:13Z.
- ran: 2026-11-18T02:35:04Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 6d5a1120 2026-11-17T18:32:40-08:00 Session close: B-098 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-18T02:33:04Z
  OK box HEAD 6d5a1120 = origin/main
  OK t4-mlb runs box HEAD code (6d5a1120; started 2026-11-18T01:58:45Z)
  OK pmbot-web-dashboard runs box HEAD code (6d5a1120; started 2026-11-18T02:18:47Z)

```

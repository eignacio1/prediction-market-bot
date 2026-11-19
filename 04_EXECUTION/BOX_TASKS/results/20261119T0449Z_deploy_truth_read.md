# Box task `deploy_truth_read` — 20261119T0449Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0449Z_deploy_truth_read.toml`
- note: W119.1: is ea75451 (nhl_v2 map, goalie/ST splits) on the box
- ran: 2026-11-19T04:53:02Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 9eed2933 2026-11-18T20:47:19-08:00 Session close: W119.3 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-19T04:48:05Z
  OK box HEAD 9eed2933 = origin/main
  OK t4-mlb runs box HEAD code (9eed2933; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (9eed2933; started 2026-11-19T04:30:31Z)

```

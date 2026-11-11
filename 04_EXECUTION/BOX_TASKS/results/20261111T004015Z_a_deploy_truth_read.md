# Box task `deploy_truth_read` — 20261111T004015Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T004015Z_a_deploy_truth_read.toml`
- note: pre-install check 2 (SW-9)
- ran: 2026-11-11T00:49:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 5494efe2 2026-11-10T16:47:19-08:00 ACTIVE_QUEUE: W109.1 Parts A+B pushed
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-11T00:48:10Z
  OK box HEAD 5494efe2 = origin/main
  OK t4-mlb runs box HEAD code (5494efe2; started 2026-11-06T05:43:33Z)
  OK pmbot-web-dashboard runs box HEAD code (5494efe2; started 2026-11-10T06:18:34Z)

```

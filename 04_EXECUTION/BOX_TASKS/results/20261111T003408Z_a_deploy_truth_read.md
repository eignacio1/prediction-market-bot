# Box task `deploy_truth_read` — 20261111T003408Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T003408Z_a_deploy_truth_read.toml`
- note: pre-install check (SW-9)
- ran: 2026-11-11T00:34:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD e8024bfb 2026-11-11T00:29:40+00:00 Box tasks: results 2026-11-11T00:29Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-11T00:33:06Z
  OK box HEAD e8024bfb = origin/main
  OK t4-mlb runs box HEAD code (e8024bfb; started 2026-11-06T05:43:33Z)
  OK pmbot-web-dashboard runs box HEAD code (e8024bfb; started 2026-11-10T06:18:34Z)

```

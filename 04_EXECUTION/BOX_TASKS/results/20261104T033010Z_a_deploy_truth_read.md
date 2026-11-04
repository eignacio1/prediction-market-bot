# Box task `deploy_truth_read` — 20261104T033010Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T033010Z_a_deploy_truth_read.toml`
- note: box has #412 (c9a9d555) before the retry
- ran: 2026-11-04T03:30:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 10e5b359 2026-11-04T03:25:54+00:00 Box tasks: results 2026-11-04T03:25Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-04T03:28:38Z
  OK box HEAD 10e5b359 = origin/main
  OK t4-mlb runs box HEAD code (10e5b359; started 2026-11-04T02:53:40Z)
  OK pmbot-web-dashboard runs box HEAD code (10e5b359; started 2026-11-04T03:28:38Z)

```

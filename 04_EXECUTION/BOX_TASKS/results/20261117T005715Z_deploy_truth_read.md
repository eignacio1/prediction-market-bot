# Box task `deploy_truth_read` — 20261117T005715Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261117T005715Z_deploy_truth_read.toml`
- note: SW-9 Monday 11-16: weekend state before the Fable wave
- ran: 2026-11-17T00:59:40Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 2472da23 2026-11-16T16:57:14-08:00 Box: Monday reads (D6, arm orders, deploy, budget) (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-17T00:58:03Z
  OK box HEAD 2472da23 = origin/main
  OK t4-mlb runs box HEAD code (2472da23; started 2026-11-14T06:18:11Z)
  OK pmbot-web-dashboard runs box HEAD code (2472da23; started 2026-11-14T06:18:09Z)

```

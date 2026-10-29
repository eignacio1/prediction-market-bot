# Box task `deploy_truth_read` — 20261029T051148Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261029T051148Z_deploy_truth_read.toml`
- note: #376 pulled?
- ran: 2026-10-29T05:11:52Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 1eb7fbba 2026-10-29T05:07:44+00:00 Box tasks: results 2026-10-29T05:07Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-29T05:08:34Z
  OK t4-mlb runs box HEAD code (1eb7fbba; started 2026-10-27T04:58:35Z)
  OK pmbot-web-dashboard runs box HEAD code (1eb7fbba; started 2026-10-29T05:08:34Z)

```

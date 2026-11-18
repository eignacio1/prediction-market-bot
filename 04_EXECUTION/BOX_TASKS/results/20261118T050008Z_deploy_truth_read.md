# Box task `deploy_truth_read` — 20261118T050008Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T050008Z_deploy_truth_read.toml`
- note: W117.3: recheck 40593d2 on box
- ran: 2026-11-18T05:00:28Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD ea9d08ee 2026-11-18T04:55:12+00:00 Box tasks: results 2026-11-18T04:55Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-18T04:58:42Z
  OK box HEAD ea9d08ee = origin/main
  OK t4-mlb runs box HEAD code (ea9d08ee; started 2026-11-18T04:55:12Z)
  OK pmbot-web-dashboard runs box HEAD code (ea9d08ee; started 2026-11-18T04:58:42Z)

```

# Box task `deploy_truth_read` — 20261118T005231Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T005231Z_deploy_truth_read.toml`
- note: W116.3: re-read after #503 (6f81a8c) is deployed - ERROR rows after, D6 recount
- ran: 2026-11-18T00:56:45Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 27729d04 2026-11-18T00:52:46+00:00 Box tasks: results 2026-11-18T00:52Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-18T00:54:51Z
  OK box HEAD 27729d04 = origin/main
  OK t4-mlb runs box HEAD code (27729d04; started 2026-11-14T06:18:11Z)
  OK pmbot-web-dashboard runs box HEAD code (27729d04; started 2026-11-18T00:54:50Z)

```

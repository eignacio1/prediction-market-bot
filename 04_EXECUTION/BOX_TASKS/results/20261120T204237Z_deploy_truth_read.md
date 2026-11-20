# Box task `deploy_truth_read` — 20261120T204237Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T204237Z_deploy_truth_read.toml`
- note: W123.3 post-merge deploy read
- ran: 2026-11-20T20:42:41Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD d7558ecc 2026-11-20T12:36:30-08:00 W123.3: H3 news latency result (NOT SUPPORTED NBA injury/starter; UNDERPOWERED confirm, NFL) (#550)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-20T20:39:24Z
  OK box HEAD d7558ecc = origin/main
  OK t4-mlb runs box HEAD code (d7558ecc; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (d7558ecc; started 2026-11-20T20:39:22Z)

```

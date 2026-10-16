# Box task `deploy_truth_read` — 20261016T1555Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1555Z_deploy_truth_read.toml`
- note: W80R.1 rerun after #284 (run 2 ran only the first request)
- ran: 2026-10-16T15:56:09Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 5564ba81 2026-10-16T15:48:48+00:00 Box tasks: results 2026-10-16T15:48Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-16T15:53:24Z
  ALARM t4-mlb runs dc84fa6c, box HEAD 5564ba81: 2 file(s) it uses changed (src/prediction_market_bot/c5_execution/demo_fill_policy.py, src/prediction_market_bot/c5_execution/paper_trader.py), 11.0h old (alarm > 6h)
  OK pmbot-web-dashboard runs box HEAD code (5564ba81; started 2026-10-16T15:53:24Z)

```

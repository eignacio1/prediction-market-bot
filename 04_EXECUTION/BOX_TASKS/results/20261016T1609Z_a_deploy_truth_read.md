# Box task `deploy_truth_read` — 20261016T1609Z_a_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1609Z_a_deploy_truth_read.toml`
- note: GG-920: confirm box HEAD carries 2fc1b58
- ran: 2026-10-16T16:09:59Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 08e8a056 2026-10-16T16:06:09+00:00 Box tasks: results 2026-10-16T16:06Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-10-16T16:08:24Z
  ALARM t4-mlb runs dc84fa6c, box HEAD 08e8a056: 2 file(s) it uses changed (src/prediction_market_bot/c5_execution/demo_fill_policy.py, src/prediction_market_bot/c5_execution/paper_trader.py), 11.2h old (alarm > 6h)
  OK pmbot-web-dashboard runs box HEAD code (08e8a056; started 2026-10-16T16:08:23Z)

```

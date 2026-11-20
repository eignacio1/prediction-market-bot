# Box task `deploy_truth_read` — 20261120T1510Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1510Z_deploy_truth_read.toml`
- note: W121.3: is capacity_read on the box
- ran: 2026-11-20T15:11:03Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD ec1e93fa 2026-11-20T07:10:47-08:00 W121.3: deploy truth read (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-20T15:08:43Z
  OK box HEAD ec1e93fa = origin/main
  OK t4-mlb runs box HEAD code (ec1e93fa; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs 3d03d5e0, box HEAD ec1e93fa: 2 file(s) it uses changed (src/prediction_market_bot/decision_trees/evidence/pipeline.py, src/prediction_market_bot/decision_trees/evidence/weekly.py), 0.0h old (alarm > 6h)

```

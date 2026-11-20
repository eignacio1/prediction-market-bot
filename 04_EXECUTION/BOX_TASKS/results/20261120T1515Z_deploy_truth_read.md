# Box task `deploy_truth_read` — 20261120T1515Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1515Z_deploy_truth_read.toml`
- note: W121.3: is capacity_read on the box
- ran: 2026-11-20T15:15:41Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 93981dad 2026-11-20T07:12:03-08:00 W121.4: deploy truth in handoff; GG-1958 Mac-copy row not visible from box (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-20T15:13:04Z
  OK box HEAD 93981dad = origin/main
  OK t4-mlb runs box HEAD code (93981dad; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs 3d03d5e0, box HEAD 93981dad: 2 file(s) it uses changed (src/prediction_market_bot/decision_trees/evidence/pipeline.py, src/prediction_market_bot/decision_trees/evidence/weekly.py), 0.1h old (alarm > 6h)

```

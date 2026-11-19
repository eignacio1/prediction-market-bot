# Box task `deploy_truth_read` — 20261119T0420Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0420Z_deploy_truth_read.toml`
- note: W119.3 post-merge read (#526)
- ran: 2026-11-19T04:24:59Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 9b527446 2026-11-18T20:20:54-08:00 W119.2: request deploy_truth_read, d6_read (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-19T04:18:03Z
  OK box HEAD 9b527446 = origin/main
  OK t4-mlb runs 43e3d10c, box HEAD 9b527446: 1 file(s) it uses changed (src/prediction_market_bot/c5_execution/market_type_registry.py), 0.1h old (alarm > 6h)
  OK pmbot-web-dashboard runs 43e3d10c, box HEAD 9b527446: 8 file(s) it uses changed (src/prediction_market_bot/c5_execution/market_type_registry.py, src/prediction_market_bot/decision_trees/coverage.py, src/prediction_market_bot/decision_trees/filter_data/nba_depth_profiles.json), 0.1h old (alarm > 6h)

```

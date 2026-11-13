# Box task `deploy_truth_read` — 20261113T0043Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261113T0043Z_deploy_truth_read.toml`
- note: W114.2: recheck box deploy of e8e06a1 (3rd)
- ran: 2026-11-13T00:44:05Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 70f9c8b9 2026-11-12T16:37:17-08:00 W114.3 session close: handoff and queue row (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-13T00:41:30Z
  OK box HEAD 70f9c8b9 behind origin/main a35b64d7: 3 file(s) a service uses (src/prediction_market_bot/decision_trees/filter_data/nba_team_percentiles.json, src/prediction_market_bot/decision_trees/filter_splits.json, src/prediction_market_bot/decision_trees/filter_supply.py) unpulled for 3.6 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (70f9c8b9; started 2026-11-12T05:33:44Z)
  OK pmbot-web-dashboard runs box HEAD code (70f9c8b9; started 2026-11-13T00:41:28Z)

```

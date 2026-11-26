# Box task `deploy_truth_read` — 20261126T0044Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0044Z_deploy_truth_read.toml`
- note: 129.1 Part A/C
- ran: 2026-11-26T00:45:18Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 350f17bc 2026-11-25T16:34:25-08:00 W129.6: box request nfl_live_feed_probe (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-26T00:41:28Z
  OK box HEAD 350f17bc behind origin/main ef458802: 3 file(s) a service uses (src/prediction_market_bot/pam/__init__.py, src/prediction_market_bot/pam/nba_state_backfill.py, src/prediction_market_bot/pam/state.py) unpulled for 5.5 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (350f17bc; started 2026-11-24T06:43:46Z)
  OK pmbot-web-dashboard runs box HEAD code (350f17bc; started 2026-11-26T00:41:27Z)

```

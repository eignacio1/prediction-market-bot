# Box task `deploy_truth_read` — 20261105T012716Z_w1003b_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T012716Z_w1003b_deploy_truth_read.toml`
- note: W100.3 read-only retry after deploy
- ran: 2026-11-05T01:27:40Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 29efb386 2026-11-05T00:57:45+00:00 Box tasks: results 2026-11-05T00:57Z
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-11-05T01:08:08Z
  OK box HEAD 29efb386 behind origin/main 97d143f0: 1 file(s) a service uses (src/prediction_market_bot/decision_trees/ride_cells.toml) unpulled for 18.7 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (29efb386; started 2026-11-04T02:53:40Z)
  OK pmbot-web-dashboard runs box HEAD code (29efb386; started 2026-11-04T03:28:38Z)

```

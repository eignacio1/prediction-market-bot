# Box task `deploy_truth_read` — 20261103T010042Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T010042Z_deploy_truth_read.toml`
- note: W97.1: read deploy after #395 merge
- ran: 2026-11-03T01:00:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 5ec8ff5f 2026-11-02T16:36:53-08:00 W97.3: handoff, queue row, decision log (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-03T00:54:48Z
  OK box HEAD 5ec8ff5f behind origin/main 3843413c: 1 file(s) a service uses (src/prediction_market_bot/nba_engine/player_availability.py) unpulled for 4.0 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (5ec8ff5f; started 2026-10-30T16:06:33Z)
  OK pmbot-web-dashboard runs box HEAD code (5ec8ff5f; started 2026-11-03T00:54:41Z)

```

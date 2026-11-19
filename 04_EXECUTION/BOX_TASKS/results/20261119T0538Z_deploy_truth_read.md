# Box task `deploy_truth_read` — 20261119T0538Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0538Z_deploy_truth_read.toml`
- note: W120.2: is 96e9790 (candidate arms default ON) on the box
- ran: 2026-11-19T05:38:21Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 2e8bfa2b 2026-11-18T21:31:26-08:00 W120.3: session-end artifacts (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-19T05:33:03Z
  OK box HEAD 2e8bfa2b behind origin/main 96e9790d: 1 file(s) a service uses (src/prediction_market_bot/decision_trees/shadow_route.py) unpulled for 0.7 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (2e8bfa2b; started 2026-11-19T04:24:51Z)
  OK pmbot-web-dashboard runs box HEAD code (2e8bfa2b; started 2026-11-19T05:24:00Z)

```

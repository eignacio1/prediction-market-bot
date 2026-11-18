# Box task `deploy_truth_read` — 20261118T045315Z_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261118T045315Z_deploy_truth_read.toml`
- note: W117.3: is 40593d2 (health_rerun) on the box
- ran: 2026-11-18T04:55:12Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD d6453f4e 2026-11-17T20:52:27-08:00 W117.1: box requests deploy_truth_read + arm_orders_read (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-11-18T04:48:05Z
  OK box HEAD d6453f4e = origin/main
  OK t4-mlb not running (no code to be stale)
  OK pmbot-web-dashboard runs 123037ad, box HEAD d6453f4e: 1 file(s) it uses changed (src/prediction_market_bot/c5_execution/market_type_registry.py), 0.1h old (alarm > 6h)

```

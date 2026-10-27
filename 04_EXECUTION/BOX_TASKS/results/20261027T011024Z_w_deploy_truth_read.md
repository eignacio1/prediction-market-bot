# Box task `deploy_truth_read` — 20261027T011024Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261027T011024Z_w_deploy_truth_read.toml`
- note: Window: Wave 87 close
- ran: 2026-10-27T01:10:48Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 57a497f1 2026-10-26T17:20:05-07:00 Session close: T-1173 — CLOSED
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: noop at 2026-10-27T01:08:05Z
  OK t4-mlb restart PENDING 1.0h (skipped 2026-10-27T01:08:05Z: skip_live_game); retried each tick, fires at the first no-live-game tick
  OK t4-mlb runs 0536a9ff, box HEAD 57a497f1: 3 file(s) it uses changed (src/prediction_market_bot/c4_risk_engine/exposure_gate.py, src/prediction_market_bot/c5_execution/kalshi_client.py, src/prediction_market_bot/c5_execution/paper_trader.py), 1.0h old (alarm > 6h)
  OK pmbot-web-dashboard runs box HEAD code (57a497f1; started 2026-10-27T00:13:31Z)

```

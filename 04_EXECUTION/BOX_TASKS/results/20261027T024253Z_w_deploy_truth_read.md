# Box task `deploy_truth_read` — 20261027T024253Z_w_deploy_truth_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261027T024253Z_w_deploy_truth_read.toml`
- note: Window: Wave 88 close
- ran: 2026-10-27T02:43:19Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check`

```
box HEAD 7003f9a0 2026-10-26T19:42:53-07:00 Box tasks: Wave 88 close reads (docs-only)
DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: docs_only at 2026-10-27T02:43:05Z
  OK t4-mlb restart PENDING 2.5h (skipped 2026-10-27T02:43:05Z: skip_live_game); retried each tick, fires at the first no-live-game tick
  OK t4-mlb runs 0536a9ff, box HEAD 7003f9a0: 3 file(s) it uses changed (src/prediction_market_bot/c4_risk_engine/exposure_gate.py, src/prediction_market_bot/c5_execution/kalshi_client.py, src/prediction_market_bot/c5_execution/paper_trader.py), 2.6h old (alarm > 6h)
  OK pmbot-web-dashboard runs box HEAD code (7003f9a0; started 2026-10-27T01:58:39Z)

```

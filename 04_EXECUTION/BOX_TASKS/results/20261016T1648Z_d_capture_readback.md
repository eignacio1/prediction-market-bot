# Box task `capture_readback` — 20261016T1648Z_d_capture_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261016T1648Z_d_capture_readback.toml`
- note: window: reinstall at :51 once the box has pulled #287
- ran: 2026-10-16T16:48:59Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/thin_capture_install.py readback`

```
CRONTAB BLOCK:
# BEGIN W80P.1 THIN MARKET DEPTH CAPTURE
# Forward order-book capture for the thinner NFL/NBA Kalshi families (Kalshi keeps no historical book; W78.2 manifest).
# Public unauthenticated GETs only; no order/ledger/model path. Writes ONLY exp_output/KALSHI_HISTORY/thin_capture/.
# Bounded in-script: 500 books/run, 60 candle markets/run, 80 MB/day, 4 GB total; flock; resumable state.json.
# Minute :51 only: :21 collides with EXP-039 (21 4,10,16,22, GG-477 stagger); :51 is used by no other job. Install ONLY when SURFACE BUDGET reads GREEN
# (Hard Rule 14), then set its RUNTIME_REGISTRY.toml entry to status = "live".
51 * * * * cd /opt/prediction-market-bot && PYTHONPATH=/opt/prediction-market-bot/src:/opt/prediction-market-bot /opt/prediction-market-bot/venv/bin/python scripts/thin_market_depth_capture.py >> logs/thin_capture_cron.log 2>&1
# END W80P.1 THIN MARKET DEPTH CAPTURE

LOG TAIL (logs/thin_capture_cron.log):
  (no log yet)

STORE:
  (store not created yet)

```

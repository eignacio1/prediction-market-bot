# Box task `capture_readback` — 20261020T0100Z_a_capture_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261020T0100Z_a_capture_readback.toml`
- note: W80.1: read back the 00:51Z run (event-time window)
- ran: 2026-10-20T01:00:41Z on root@157.230.91.33:/opt/prediction-market-bot
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
THIN_CAPTURE ts=2026-10-19T17:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-19T18:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-19T19:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-19T20:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-19T21:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-19T22:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-19T23:51:01Z listed=0 due=0 books=0 unchanged=0 errors=0 series_errors=0 candle_markets=0 candle_errors=0 dropped=0 rows=0 bytes_today=39162356 tracked=3164 cap=none http_calls=17 http_n429=0 http_errors=0
THIN_CAPTURE ts=2026-10-20T00:51:01Z listed=743 due=743 books=500 unchanged=0 errors=0 series_errors=0 fallback=0 candle_markets=0 candle_errors=0 dropped=0 candle_capped=0 rows=500 bytes_today=838723 tracked=3664 cap=none http_calls=517 http_n429=0 http_errors=0

STORE:
  books_2026-10-16.jsonl  316175 bytes  192 rows
  books_2026-10-17.jsonl  682929 bytes  441 rows
  books_2026-10-18.jsonl  4188892 bytes  3045 rows
  books_2026-10-19.jsonl  822322 bytes  544 rows
  books_2026-10-20.jsonl  838723 bytes  500 rows
  candles_2026-10-19.jsonl  38340034 bytes  1266 rows
  state.json tracked tickers: 3664

```

# EXP-034 D1(b)-2 — AMENDMENT (new test, not a fix) — written BEFORE any new sampling

Written 2026-10-02 (Wave 47 / 47.1, runner R1), before round 0 of the new sample. This commit is pushed to origin/main before the sampler is started.

## What this is
D1(b) as frozen (D1B_TOLERANCE_PREREG.md, commit 38b8490) FAILED: 56/84 pairs pass; 28 UNMATCHED. The original run, its sample, its gate result and its FAIL verdict stay on record unchanged and are NOT relabeled. This document defines a NEW, separate test, "D1(b)-2". It is an amendment: it states a lookback the frozen text left unspecified. It is not a fix of the original run, and a D1(b)-2 pass does not turn the original FAIL into a pass.

## The one thing stated that the frozen text did not
**Candle lookback = back to market open.** The frozen matching rule ("nearest EARLIER candle; if none exists, UNMATCHED") is executed against the market's candle history from its `open_time` to last read + 15 min, not against a short fixed window. Implementation: candles are pulled backward in 2-day chunks from last read + 15 min. Once a candle with `end_ts` earlier than the first read of that ticker is held, further pulling cannot change any match (the nearest earlier candle is already in hand) and stops; otherwise pulling continues to `open_time`. A ticker with no candle at all from open_time to last read is UNMATCHED (counted as a fail, unchanged).

## Unchanged (frozen, not re-opened)
- Ticker rule: first 2 open tickers from `GET /markets?series_ticker=S&status=open&limit=100` at round 0, S in KXHIGHNY, KXHIGHCHI, KXHIGHMIA, KXCPI, KXPAYROLLS, KXGDP (12 tickers), fixed after round 0, never swapped. Re-drawn at a NEW round 0 by the same rule (the draw may return the same or different tickers).
- Rounds >= 6, spaced >= 20 min (target 7 rounds, 21 min). Reads `GET /markets/{t}` -> yes_bid, yes_ask, retrieval UTC. Candles 1-minute, pulled after last round + 10 min.
- Matching rule (end_period_ts = ceil(t/60)*60, else nearest earlier close), per-side tolerance 0.01, pair passes iff both sides pass, gate >= 95% of pairs AND no pair misses by > 0.03, unmatched counted as fail, empty-book placeholders not excluded. Comparator code `board_survey_nonsports_candles.py` is reused unmodified.
- Failure => every candle-based number from the corrected test is VOID; stop, report, hand back.

## Operating limits
Read-only public GETs. Sampler and chunked candle pull each run one request in flight with 1.3 s spacing (<= 0.77 req/s, inside this runner's 0.8 req/s share); on any 429 spacing doubles. No orders, no writes outside EXP-034 paths. The sampler runs as a background process; its PID is recorded in `d1b2_sampler.pid`.
New artifact names (`d1b2_*`) so original files are never overwritten.

# W108.1 Part B — the NBA/NHL untested rows, on the 14-day archive

Claim GG-1811..1813 · purpose PROOF (P1/P2) · run 2026-11-09/10 · rules unchanged from `ride_board/RIDE_BOARD_PREREGISTRATION_2026-11-06.md` and `pot_of_gold/POT_OF_GOLD_PREREGISTRATION_2026-11-05.md`.

**Data.** Box `exp_output/PRICE_ARCHIVE/prices_2026-10-28 .. 2026-11-10` (14 days), the eight NBA/NHL game-line series (GAME, SPREAD, TOTAL, TEAMTOTAL), 820,923 two-sided quotes. Archive on the box since 2026-10-28 (W92.1 cron). Settlements: public Kalshi GETs, live endpoint (the `/historical` endpoint failed transiently on two series; tickers settled but unlisted by the live endpoint would show as unsettled, 354 did).

## 1. Ride board backward test (R09; replaces the NBA/NHL half of R07)

`ride_board/analyze.py`, frozen rules (k=3, 70/30 split by game in time order, 60-minute exit, refractory 1h, at least 15 held-out games, Holm over primary tests). Output: `ride_board_nba_nhl_14d.json`.

| Family | held-out games | held-out events |
|---|---|---|
| KXNBAGAME / SPREAD / TOTAL / TEAMTOTAL | 40 / 32 / 32 / 32 | 67 / 707 / 591 / 763 |
| KXNHLGAME / SPREAD / TOTAL / TEAMTOTAL | 41 / 34 / 34 / 30 | 32 / 57 / 333 / 239 |

All eight families clear the 15-game floor (the earlier run had NBA at 23). Primary tests: 12 (FADE and FOLLOW, all-books, net at 60 min, per testable family). **Holm rejections: 0 of 12.** Held-out net mean per contract, game-clustered 95% interval:

- Every primary cell except one is negative with an upper bound below zero: NBA GAME FADE −0.298 [−0.363, −0.248] (28 games); NHL TOTAL FADE −0.498 [−0.560, −0.447] (19 games); NHL TEAMTOTAL FADE −0.138 [−0.175, −0.102] (22 games).
- NBA SPREAD FOLLOW is the best primary: −0.003 [−0.122, +0.106] (24 games), which spans zero.
- Of all 58 reported cells, two (non-primary, not Holm-tested) have a positive held-out lower bound: NBA SPREAD FOLLOW tight-book exit-at-settle +0.127 [+0.007, +0.211] (179 events, 24 games, fit mean +0.012) and NHL SPREAD FOLLOW tight-book exit-at-settle +0.149 [+0.002, +0.257] (9 events, 6 games). With 58 cells examined, about three would clear a 95% lower bound by chance alone; the NHL one has 6 games. **Neither is promoted.** They are hypotheses for the forward look, not results.

## 2. Pot of gold, NBA and NHL (L03)

`pot_of_gold/measure.py` on the same archive and the fetched settlements: 60,284 settled tickers, 4,148 snapshots in the price buckets, 3,794 joined to a settlement (354 unsettled), 243 NBA games and 213 NHL games. Bar per route: net of the exact fee, 70/30 time split, game-clustered lower bound above 0, at least 30 fit contracts, 20 held-out games, 5 held-out minority outcomes, Holm. **Holm candidates 4, rejected 0.** Route status: NBA 62 UNTESTED (too thin), 40 FAILED, 4 IN_SAMPLE; NHL 44 UNTESTED, 26 FAILED, 2 IN_SAMPLE. No route is held-out positive net.

## 3. Candle scan (R07)

Not re-run for NBA/NHL: `ride_market_scan/holdout_scan.py` reads the W89.7 hourly-candle history, not the price archive, so re-running it would return the W90.1 result unchanged. The archive-based ride board above is the replacement test for NBA/NHL. R07 stays UNTESTED for NFL only.

## Rows after this block

- L03: UNTESTED → NO EFFECT NET (0 of 4 Holm candidates).
- R09 (new): NBA/NHL ride board on 14 days → NO EFFECT NET.
- R07: stays UNTESTED, narrowed to NFL candles.
- R02 (MLB backward test is void; only forward rows can answer), L04 (no multi-leg archive): cannot be answered from existing data. P04: Part C.
- UNTESTED 5 → 4, with one row added (40 hypotheses).

## Limits

- 14 days is one early stretch of the regular season, and the held-out part is the later 30% of games by time, so the window is narrow.
- Fills are assumed at bid/ask (no demo fill evidence for these series). Costs are whatever `ride_net` charges under the frozen rules; they were not re-derived against 106.2's wall for team totals.
- The ride-board `net` figures embed no queue-position or partial-fill effects.

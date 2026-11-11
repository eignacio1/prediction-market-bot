# W109.3 Part B — engine-priced NBA props vs the market's pre-game mid (2026-11-10)

**Verdict: NULL, in the market's favour.** On settled 2026-27 NBA prop markets the engine-priced probability has a *worse* Brier score than the market's pre-game mid in all four families; every game-clustered 95% interval excludes zero. Per the block this is a result and does not stop the cells (Part C proceeds, SHADOW, no orders).

## Method (all data existed at run time; public GETs only)
- Markets: Kalshi settled `KXNBAPTS/REB/AST/3PT` with `close_time` >= 2026-10-20 and volume > 0 (29,728 markets, 4 series). Price: last hourly candle with a two-sided quote ending >= 5h before `close_time` (W108.3's rule); mid = (yes_bid + yes_ask)/2.
- Engine: `engine_v2` with FIXED league constants (hca 2.0, tbias 0, sd_margin 13, sd_total 19 — fitted on no tested game), team ratings = shrunk (8 games of 114) mean points for/against from games dated strictly before the game; 4,000 joint draws per game. Props by `nba_engine/props.py`: player points split from the draw's team points; rebounds/assists/threes from a coupled team total split the same way. Player means = the player's prior-game means (>= 4 prior games, >= 10 mpg, top 10 by minutes per team).
- Scored: 15,364 markets in 96 games (ESPN box scores for 154 completed games). Skipped: 10,950 player not in prior rotation, 3,414 no two-sided quote, 605 unparsed/no candle. Intervals: bootstrap over games (2,000 draws). Brier diff = engine - market (positive = engine worse).

| family | n | games | yes rate | mean engine p | mean market | Brier engine | Brier market | diff [95% CI] |
|---|---|---|---|---|---|---|---|---|
| points | 3,664 | 96 | 0.380 | 0.336 | 0.385 | 0.1817 | 0.1661 | +0.0156 [+0.0106, +0.0210] |
| rebounds | 4,265 | 96 | 0.474 | 0.461 | 0.458 | 0.1647 | 0.1544 | +0.0103 [+0.0069, +0.0141] |
| assists | 3,149 | 96 | 0.406 | 0.389 | 0.397 | 0.1564 | 0.1493 | +0.0072 [+0.0029, +0.0114] |
| threes | 4,286 | 96 | 0.370 | 0.350 | 0.359 | 0.1606 | 0.1538 | +0.0068 [+0.0030, +0.0108] |

Robust to subsets (spread <= 0.10; mid in [0.10, 0.90]; both) — same sign and size, see `RESULT.json`.

## Reading it
- The engine prices below the observed yes rate in every family (points most: 0.336 vs 0.380) — a level bias, not noise. Likely causes, none tested here: early-season means from <= ~12 games, the rest-bucket/normalised-share construction, and no minutes/availability information (the market sees injuries and rotation news; this model does not).
- **Not tuned on this sample.** No parameter was adjusted after seeing these results; a recalibrated challenger would need its own pre-registration and a fresh out-of-sample window (it would be tuned on exactly these games).
- Caveats: one season-to-date window (21 days, 96 games scored); the market mid is the entry-time quote, not a fill; players absent from the prior rotation (new/low-minute) are unscored, which selects toward the easier-to-price players.
- Factor stage (ADR-0075): player stat history = aggregated; coupling to the game draw = interpreted; **applied = not yet (no edge against the market)**.

Files: `fetch_markets.py`, `backtest.py`, `analyze.py`, `RESULT.json`. The box-score fetch (`fetch_box`) was a throwaway ESPN public-GET scratch script; its source is inlined as the loader contract in `backtest.py` (`load_box`).

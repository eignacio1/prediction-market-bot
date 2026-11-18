# W117.2 pre-registration — NHL consensus: MOMENTUM and KALSHI-VS-BOOKS
Last reviewed: 2026-11-18. Written and committed BEFORE any outcome-bearing statistic is computed. Only counts were read
(1,394 consensus rows; 1,392 join to a Kalshi KXNHLGAME event by ET date + team pair; 2 unmatched).

## Data (free, read-only)
Muse archive `eignacio1/sports-intel-archive` @ 018634eca5555e3ab1936862b9842bf850e63084, folder
`L3-closing-lines/nhl/minmaxxxer-2025-26/`. Source: HuggingFace minmaxxxer/nhl-closing-odds-2025-26, CC-BY-4.0; "compiled from publicly
available game and odds information; not affiliated with the NHL, Flashscore or any bookmaker. For research and analysis."
File sha256 459588b3...cb62b345, 335,103 bytes, 1,394 rows (1,312 regular season + 82 playoff, where the file labels 80 matched as
`postseason`). Authorization: Earl 2026-11-17 16:13 PT, this source and table only. Regular season and playoffs are never pooled:
primary = regular season; playoffs reported separately, descriptive only.

## Test 1 — MOMENTUM (does the open-to-close move carry information past the close?)
Per market, regular season, one row per game:
- Moneyline: y = home wins; x1 = logit(close_home_win_prob); move = close_home_win_prob − open_home_win_prob.
- Puck line: y = home covers the CLOSE line (ats_result); x1 = logit(close_home_cover_prob); move = open_spread_home − close_spread_home
  (positive = line moved toward home). Limitation: the file has NO open cover probability, so the move is a line move, not a probability move.
- Total: y = over the CLOSE line (total_result); x1 = logit(close_over_prob); move = close_total − open_total (positive = toward over).
  Pushes dropped. Same limitation as puck line.
Model: logistic regression, x1 as offset with slope fixed at 1 (the close is taken as calibrated); fit beta on move only.
H1 (directional): beta > 0, i.e. the close under-reacts and a follow-the-move arm has a prior. Interval: game-clustered bootstrap,
2,000 resamples, seed 117, percentile 90% two-sided (matches the arm bar's 0.90). Verdict rule: interval wholly above 0 → "move carries
information, prior for the follow-the-move arm"; interval spans 0 → "hypothesis closed (EXP-W117.2-MOM, parked for R&D)" for that market;
wholly below 0 → "close over-reacts; routed to fade-the-move". Three markets, no multiplicity correction (reported as three separate looks).
Report beta with interval and n per market. Also report a 30% latest-games held-out beta fit on the first 70% (W110.5 split), descriptive.

## Test 2 — KALSHI VS BOOKS (moneyline only)
Series: KXNHLGAME hourly candles (kalshi_history/1, w84-3 cache, 3,330 rows, from 2025-08-01). No Kalshi puck-line or total candles
exist for 2025-26 (w89_7 manifest: 0), so those are reported as not testable.
Per matched regular-season game: Kalshi price = close of the last hourly candle with t ≤ start_time_utc − 3600, for the home ticker.
Include only if bid and ask both present and (ask − bid) ≤ 0.10; otherwise excluded, and the exclusion count is reported.
- Gap = Kalshi mid (home) − consensus close fair home probability. Mean, sd, game-clustered bootstrap 90% interval.
- Ride consensus: buy the side with consensus p ≥ 0.5 at Kalshi ask, fee 0.07·P·(1−P) per contract (taker). net = outcome − ask − fee.
  Mean net with game-clustered 90% bootstrap interval, n. Mirror (buy the other side) reported for symmetry.
- If matched, price-eligible n < 300, the result is called thin and no verdict is issued, only the gap and its interval.
Fallback if no overlap: state the number of 2026-27 games a free current-season consensus needs (to reach the power-calendar n for a
gap of 0.03 at sd observed here) and register it on the Monday Muse list. No scraping (KofSports or otherwise).

## Not allowed to change after this commit
Split, interval level, seed, ask/fee rule, exclusion rules. A change is a dated edit here plus a DECISION_LOG line.

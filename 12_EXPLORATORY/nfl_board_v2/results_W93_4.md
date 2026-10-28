# W93.4 results: NFL board v2 (market-anchored empirical joint) and N15 schedule geometry

Purpose: DEPTH. Measures: D4 NFL (scaffold -> whole board priced, market-anchored, tested); engine margin mass at key numbers 3/7/10; D5(b) N15 none -> interpreted.
Nothing here touches an order, stake, ledger, live model, shadow arm, registry cell or pre-registration.

## Premise checks
- 89.4 found the v0 engine put 0.07 of mass on a margin of 3 against 0.14-0.15 actual. Re-measured below on held-out games, same direction.
- Kalshi strike convention (verified, not assumed): yes = value > N, threshold N ("gt"). Kalshi's own Brier vs outcomes: spread 0.1436 (gt) vs 0.1545 (ge); total 0.1394 vs 0.1416; team total 0.1308 vs 0.1327.

## Method (`src/prediction_market_bot/nfl_engine/board_v2.py`)
1. Shape: kernel-weighted empirical joint of past (margin, total) among games with similar closing spread (h=1.75) and total (h=4.0).
2. Anchor: exponential tilt so the market's main spread and total are the medians. Key-number spikes survive because support stays on real final scores.
3. Every price (moneyline, any spread or total strike, both team totals) comes off that one pmf.
When it applies: a market with a main line and a ladder around it. When it does not: it says nothing about where the line should be.
Bandwidths are not tuned (stated limitation).

## Held-out key numbers (rolling origin 2012-2025, 3,829 games; `heldout_keynumbers.json`)
| |margin| | observed | engine (z) | same-median Gaussian (z) |
|---|---|---|---|
| 3 | 525 | 539.9 (-0.7) | 198.5 (+23.84) |
| 7 | 315 | 346.6 (-1.79) | z +10.29 |
| 10 | 188 | 209.3 (-1.52) | z +2.31 |
| 14 | 183 | 167.1 (+1.26) | z +5.1 |
| 6 | 244 | 212.5 (+2.23) | z +4.36 |
| 4 | 176 | 173.1 (+0.22) | |
Misses, stated: k=1 (z +2.2) and k=2 (z +2.78) are under-modelled. k=3 is now within sampling noise (89.4: 0.07 sim vs 0.14-0.15 actual).

## Against Kalshi (`kalshi_compare.py`; 86 settled 2026 games, last pre-kickoff snapshot, centre = ladder's own 0.5 crossing, strikes >=3 pts off centre)
Brier Kalshi minus engine (+ = engine better), game-clustered 95% CI; P&L net of fee per contract on strikes where engine disagreed.
| market | n strikes | dBrier | fired | net P&L/contract |
|---|---|---|---|---|
| game | 172 | +0.0013 [-0.0026,+0.0054] | 63 | +0.021 [-0.149,+0.186] |
| spread | 1784 | +0.0015 [-0.0009,+0.0037] | 1074 | +0.019 [-0.027,+0.060] |
| total | 1193 | +0.0007 [-0.0009,+0.0024] | 566 | +0.009 [-0.041,+0.062] |
| team total | 2335 | -0.0003 [-0.0019,+0.0013] | 1054 | -0.002 [-0.037,+0.035] |
At >=6 pts off centre: spread +0.0012 [-0.0015,+0.0036], total +0.0006 [-0.0009,+0.0022].
Verdict: the engine matches Kalshi's ladder; every interval includes 0. No demonstrated edge. n is 86 games of one in-progress season; strikes within a game are not independent (hence game clustering).

## N15 travel / time zone / short week (`nfl_schedule_geometry.py`, `n15_interpret.py`)
Built point-in-time from schedule fields: city-level miles, timezone shift, short week (rest<=5), post-bye, neutral/international, body-clock kickoff hour. Rolling-origin ridge of closing-line residuals on these vs intercept-only, paired MSE gain, per-game cluster bootstrap, 3,829 games:
- margin: gain -0.916 [-1.455, -0.374] (the geometry model is worse out of sample)
- total: gain -0.029 [-0.461, +0.374]
Full-sample OLS on margin (coef, SE): away miles/1000 0.644 (0.459); tz east -0.456 (0.321); tz west -0.575 (0.309); short-week diff -2.893 (4.396); bye diff -0.52 (0.458); away early body-clock 1.194 (0.669). Nothing separable from 0.
Stage: interpreted. No detectable effect beyond the closing line; not applied (nothing moves a price).

## Stage reached
- Board v2: applied (a tested path from history to a price against the market), no edge shown.
- N15: aggregated -> interpreted.

## Limitations
City-level miles; relocated teams use today's base; one season of Kalshi prices; k=1,2 under-modelled; bandwidths untuned; the ridge was not tuned beyond a default penalty.

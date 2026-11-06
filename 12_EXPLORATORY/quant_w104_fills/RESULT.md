# W104.1 (B-048) — why fills lose: fill probability and price impact

**Purpose / measure:** EXECUTION E3 (win rate on fills vs non-fills, adverse selection). Descriptive, held-out. No placement change.
**Method:** `src/prediction_market_bot/quant/fills.py` (7 known-answer tests, planted informed/uninformed flow). Runner: `run_w104_fills.py`; numbers: `result.json`.

## Operator paragraph
Fills lose because a resting order mostly fills when the market is about to move through it, not when someone wants to trade with us. Held-side mid is about 1.2c below our fill price one minute later (n=13,164 fills, 627 games), and the loss grows with the price paid: 0.5c under 20c, 4.1c at 80c or more (5-minute markout 6.4c at 80c or more, n=153). Orders that fill look like cheap, near-50/50 YES orders on contracts several days from the game; orders that fill AND win are not distinguishable from those that merely fill on anything we log. On the held-out days the fill-vs-non-fill win gap in this sample is small (-1.5pp, fills win less) and the observed covariates do not reliably explain it (share explained -74%, 90% CI -365% to +191%): the covariates we have do not separate information from noise.

## Population caveat — read first
This is the **NFL/NBA/NHL demo shadow-order population** (policy log, 141k orders; 99.9k usable here), **not the MLB paper-book fills** that produce the box's E3 numbers (T4 25.4% vs 48.3%, T1 28.9% vs 52.1%). MLB is absent from this sample. The E3 gap here is -1.5pp, not the MLB-scale gap, so "gap explained" is measured on a much smaller gap and should not be read as explaining the MLB gap.

## n and epoch rule
- Orders from collection start 2026-10-21T04:30:36Z; days 2026-10-21..2026-11-05; usable n=99,864 (NBA 77,202, NFL 13,121, NHL 9,541). Train: earlier 70% of days (< 2026-11-01, n=81,704); test: later 30% (n=18,160).
- **Pre-epoch YES-side only.** Pre-epoch NO-side fills (13,049 with known side) are mirror-priced (GG-1771/GG-1784) and excluded; their cache outcome is the YES-contract result (70% "won") and would invert E3. **Post-epoch n = 0:** the last pulled order (2026-11-05T10:23Z) precedes 2026-11-06T01:03:42Z.
- **Non-fills have no recoverable side.** The cache labels every order `side: yes`; a non-fill's intended side is unknown, so non-fills are scored as the YES contract. If NO-side orders are ~42% of orders (their share of fills), non-fill win rate is contaminated by an unknown amount. This caps what the E3 estimate can claim.

## Findings
1. **Fill model** (fills within the 60s resting window; held-out): AUC 0.62, ECE 0.021, Brier 0.1283 vs 0.1312 base. Train fill rate 17.5%, test 15.5% (drift). Coefficients (train, game-cluster bootstrap 90% CI): `|p-0.5|` -2.40 [-2.72,-2.09] (nearer 50/50 fills more); price_yes -0.36 [-0.64,-0.17]; NHL -1.07 [-1.28,-0.88]; days_ahead>=2 +1.30 [+1.01,+1.56]; days_ahead=1 +0.54 [+0.40,+0.66]; NFL +0.55, NBA +0.52 vs NHL-excluded base. Calibration is acceptable; discrimination is weak.
2. **Markout** (held-side mid minus fill price, YES fills): 1m -1.23c (n=13,164), 5m -1.55c (n=3,743), 30m -1.19c (n=3,409). By price: <0.2 -0.5c; 0.2-0.5 -0.9c; 0.5-0.8 -2.1c; >=0.8 -4.1c at 1m. By sport (1m): NFL -1.0c, NBA -1.3c, NHL -2.5c (n=219). Cluster-robust: price_yes -4.3c per 1.0 (se 1.4c) at 1m, -8.6c (se 2.7c) at 5m.
3. **E3 gap explained** (held-out, propensity from train days): raw -1.5pp (fills 2,821 vs non-fills 15,339, 643 games), adjusted -2.6pp [90% CI -7.8, +2.4]; share explained not distinguishable from 0. By sport: NFL raw +2.4pp, NBA -2.3pp, NHL n_fill=67 (too thin).

## Not measured (limits)
- **Distance from mid, book depth and exact time-to-start are not logged per order.** Price level and days-ahead are the proxies; depth archive is MLB-hits only and does not join to these game-winner markets. The "distance from mid" question is therefore answered only through price level.
- Time-to-fill is not reliable (the markout `fill_ts` is when the collector first saw the fill, hours after order). The censored hazard is built and tested (`fit_hazard`) but not run on real data; the fill model above is binary within the 60s window.
- h5/h30 markouts exist for far fewer fills than h1 (candle availability), so those are a subset.

## Candidate rules for a later pre-registration (NOT pre-registered, NOT applied)
- Do not rest YES orders at price >= 0.80: 1m markout -4.1c vs -0.5c under 0.20.
- Log the order's intended side, the pre-order best bid/ask and the book depth on every shadow order, so distance-from-mid and depth can be modeled instead of proxied (the missing logging is the blocker for an actual information-vs-noise test).
- Re-run this on MLB paper-book fills and on post-epoch all-sides data once n supports it.

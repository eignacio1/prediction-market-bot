# W106.2 (B-057) — The cost wall

**Purpose / measure:** EXECUTION E2 / PROOF — effects with a measured net-of-cost figure, and which cells are net-positive as maker or taker.
**Code:** `src/prediction_market_bot/quant/costs.py` (new functions only, 7 known-answer tests, PR #448). **Numbers:** `wall.json`, `spread.json`. **Builders:** `build_wall.py`, `spread_agg.py`.

## Operator paragraph
A Kalshi trade costs about **1.5-2.3c per contract each way as a taker** on game lines, spreads and totals (half-spread 0.5-3c plus a 0.3-1.75c fee), and **4-8c each way on props and team totals** (half-spreads of 3-6c at game day, 10-27c a day ahead). As a **maker** the fee is a quarter (at most 0.44c) but fills arrive just before the market moves through them: 1-minute markout is -0.5c under 20c rising to -4.1c at 80c+, so a resting fill nets **-0.6c to -4.3c in every price bucket**. No bucket turns positive. The only effects that clear the wall are the **11 in-sample 89.2 longshot cells held to settlement** (net +3.3c to +10.0c after the exact fee, interval lower bounds +0.65c to +5.1c); they pay one fee and no exit spread, and none is held out yet. Ride/fade round trips (103.2) pay the wall twice and do not clear it.

## A1 — Fees
- Rule (`money.fee`): round-up to a centicent of M x coef x C x P x (1-P); taker coef 0.07, maker 0.0175. Published check: 100 contracts at 50c taker = $1.75 (tested).
- Per contract: taker 0.33c at 5c, 1.12c at 20c, 1.75c at 50c; maker at most 0.08c / 0.28c / 0.44c.
- MLB is multiplier 0.5 pre-game, 1 live; `fee_k007` therefore overstates MLB pre-game by half the fee (tested).
- Source: Kalshi schedule via Muse's R-068 cards (PDF 2026-07-07; web page read 2026-10-27, **undated**). Live fetch of kalshi.com/fee-schedule returned HTTP 429; not retried.
- **UNCONFIRMED against our demo fills.** The demo order log carries no fee field and the paper book holds only model-assumed fees. A read-only `GET /portfolio/orders/{id}` probe on the box was refused by the classifier (remote write + credentials file); I did not work around it. Needs an allowlisted bridge task or the window.
- Known table gap: NFL spread/total, NBA game/spread/total/series and NHL game/series have no maker row, so their maker fee reads 0 (understated; the table above uses the upper-bound 0.0175 coef).

## A2 — Realized half-spread (archive 102 files, 20-minute snapshots, n-weighted)
Time-to-start is a **calendar-day proxy** (ticker date vs snapshot date: D0 game day, D1, D2+); the archive has no game-start field. By series (D0 / D1 / D2+, cents): MLB game 0.5/0.9/2.2; MLB spread 1.0/0.9/1.5; MLB total 1.0/1.4/3.3; MLB team total 3.0/10.7/7.2; MLB F5 2.4/12.2/5.7; MLB hit 5.8/4.2/3.0; NFL game 0.5/0.5/0.8; NFL spread 0.9/0.6/1.8; NFL total 0.9/0.6/2.9; NFL team total 2.5/1.5/2.4; NBA spread 1.7/7.2/-; NBA team total 4.2/13.2/-; NHL total 1.0/17.5/35.4; NHL team total 2.0/26.6/49.5. Full band x tts detail in `spread.json` (cells n>=30). Wide D1 values are thin overnight books, not tradable quotes.

## B1 — Effects against the wall (epoch: pre-epoch YES-only and sources that do not use demo fills; post-epoch n = 0 everywhere)
| Effect (source) | Net as taker, after spread + exact fee | Net as maker | n / interval |
|---|---|---|---|
| NFL team-total fade (103.2 -> 105.4) | -0.09 fit, -0.08 held out | not measurable (no maker markout for these cells) | interval below 0 |
| NFL total fade | -0.12 / -0.25 | - | held out |
| NHL total fade (strongest gross: R +0.51) | -0.37 / -0.52 | - | held out; tight-book +0.14 fit -> -0.04 held out (n=11 events) |
| NBA totals/team totals | -0.20 / -0.18 | - | 23 held-out games |
| MLB totals fade (105.4) | +0.022 fit, **+0.036 held out**, interval [-0.008, ...] includes 0 | - | not a win |
| KXMLBHIT fade (103.2, R +0.08) | gross shrinks to +0.008 in tight books (bid-ask bounce) -> below cost | - | 554 games |
| 11 longshot cells (89.2, W92.2 exact-fee net) | **+0.033 to +0.100**, lo bounds +0.0065 to +0.051 | not measured | **in-sample**, hold to settle |
| Resting fills any bucket (105.2/104.1) | - | **-0.6c to -4.3c per fill** | n=13,164 fills, 627 games, YES-only pre-epoch |

**Maker-positive cells with interval above 0: none.**

## B2 — Maker economics
Markout (105.2, 1 min) plus upper-bound maker fee, per fill: <0.20 -0.63c; 0.20-0.35 -1.00c; 0.35-0.50 -1.62c; 0.50-0.65 -2.39c; 0.65-0.80 -2.62c; >=0.80 -4.29c. The 105.2 "no rest >= 0.50" cap lifts the per-fill figure to -0.73c markout (about -1.0c with fee) and cuts the per-order loss (-0.16c [-0.23, -0.10]) but settle P&L per order is unchanged (-1.67c vs -1.71c). **Resting never becomes positive in any bucket.** Posting at best bid instead of mid gains +0.44c per order [+0.29, +0.61] at a cost of 28.8 points of fill rate. Held-out and post-epoch: post-epoch n = 0 (last pulled order precedes 2026-11-06T01:03:42Z); population is NFL/NBA/NHL, **MLB absent**.

## Limits
Half-spread is quote-based, not fills; markout is a 1-minute mid and only for YES-side pre-epoch fills; 89.2 cells are in-sample and unadjusted (pre-registered forward test needed); queue position and size impact not modeled.

## Recommendation (not applied)
Pre-register a forward, hold-to-settle test of the 11 89.2 cells with the exact-fee net as the metric and a pre-declared taker cost cap; do not pre-register any ride/fade or resting rule. Log intended side, pre-order best bid/ask and depth on shadow orders (also 104.1's ask).

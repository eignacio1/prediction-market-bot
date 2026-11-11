# W110.4 — Same-game correlation from one engine (B-072, parlay groundwork)

**Research only. No cells, orders, fills, stakes or Kelly changes.** Measure: B4 (parlay families) — groundwork; joint calibration per leg-pair type.

## Plain English

A same-game parlay is priced by the *joint* probability that all legs hit. If the legs move together (a team that wins also scores more; a player who scores more also hits more threes), multiplying the single-leg prices gets it wrong. The NBA engine simulates one game and draws every team and player outcome from that same simulation, so in principle it prices the pairs correctly. We tested whether it does, on 1,075 settled 2025-26 regular-season games, walk-forward (ratings and player means from earlier games only; lines set at the engine's own median, so no outcome picked a line).

**What held up:** pairs of a game leg with a team or player leg. Win × own-team total, win × player points, game total × player points, win × team total, game total × threes. The engine's dependence there matches what happened (gap between realised and engine dependence is within noise), and the engine joint beats the naive product on log loss and Brier with intervals above zero.

**What is wrong:** the engine splits a team's points among its players and draws each player's *other* stats (rebounds, assists, threes) independently of that split. Three consequences, all measured:
1. **Same-player combos (points × threes, points × rebounds, points × assists):** realised co-movement is far above the engine's. Points × threes: realised covariance +0.091 vs engine +0.005. Points × rebounds: +0.037 vs −0.002 (engine slightly negative). The engine joint is only marginally better than the naive product on points × assists and points × threes, and *worse* on points × rebounds. A parlay priced from this engine would be too cheap on these.
2. **Teammates' points:** the engine makes them negatively correlated (they share a fixed team total): covariance −0.016. Realised is slightly *positive* (+0.009; pace/minutes/blowout effects lift everyone). The engine joint is **worse than the naive product** here (log loss −0.008, interval excludes zero).
3. **Win × rebounds:** engine says ~0 (−0.004), realised +0.014.

**Verdict:** usable today for game-leg × team/player-points legs. Not usable for same-player multi-stat or teammate pairs until the player layer carries a shared latent (minutes/pace/usage). Triples were built (Part A) but not scored: the pair results already show where the structure is missing, and triples inherit it.

## Table — pairs by type (n pairs / n games; game-clustered bootstrap 95% CI, 1,000 resamples)

Δ log loss, Δ Brier = independent minus engine (positive = engine joint better). Covariances are measured against *realised* marginal rates so the engine's known marginal bias (W109.3: it under-prices over-the-median legs) cannot masquerade as a dependence error.

| Pair type | n / games | Δ log loss | Δ Brier | realised cov | engine cov | gap (real−engine) |
|---|---|---|---|---|---|---|
| ML × own team total | 1075 / 1075 | +0.0099 [−0.002, +0.021] | +0.0053 [+0.0003, +0.0102] | +0.101 | +0.091 | +0.010 [−0.004, +0.022] |
| Win × player points | 4631 / 1063 | +0.0087 [+0.0076, +0.0099] | +0.0037 [+0.0032, +0.0041] | +0.026 | +0.022 | +0.004 [−0.003, +0.011] |
| Team total × player points | 4631 / 1063 | +0.0119 [+0.0078, +0.0160] | +0.0049 [+0.0033, +0.0066] | +0.040 | +0.041 | −0.001 [−0.008, +0.006] |
| Game total × player points | 4631 / 1063 | +0.0067 [+0.0029, +0.0105] | +0.0027 [+0.0011, +0.0043] | +0.028 | +0.033 | −0.006 [−0.013, +0.001] |
| Game total × threes | 4392 / 1062 | +0.0001 [−0.002, +0.002] | +0.0000 | +0.016 | +0.016 | +0.000 [−0.006, +0.007] |
| ML × game total | 1075 / 1075 | +0.0000 | +0.0000 | +0.002 | −0.000 | +0.002 [−0.014, +0.016] |
| Spread × game total | 1075 / 1075 | +0.0003 | +0.0001 | +0.004 | −0.000 | +0.005 [−0.011, +0.019] |
| Points × assists, teammates | 7064 / 1003 | +0.0016 [+0.0011, +0.0020] | +0.0007 | +0.009 | +0.005 | +0.004 [−0.002, +0.009] |
| Points × points, opponents | 5091 / 957 | +0.0018 [+0.0014, +0.0023] | +0.0007 | +0.005 | +0.004 | +0.001 [−0.005, +0.009] |
| Rebounds × rebounds, teammates | 3532 / 1003 | −0.0003 [−0.0005, 0.000] | −0.0001 | +0.003 | +0.000 | +0.003 [−0.005, +0.011] |
| **Points × assists, same player** | 4631 / 1063 | +0.0022 [+0.0018, +0.0026] | +0.0010 | +0.016 | +0.005 | **+0.011 [+0.004, +0.018]** |
| **Points × threes, same player** | 4392 / 1062 | +0.0037 [+0.0033, +0.0042] | +0.0016 | +0.091 | +0.005 | **+0.086 [+0.080, +0.093]** |
| **Points × rebounds, same player** | 4631 / 1063 | −0.0010 [−0.0013, −0.0007] | −0.0004 | +0.037 | −0.002 | **+0.039 [+0.032, +0.045]** |
| **Points × points, teammates** | 3532 / 1003 | −0.0082 [−0.0097, −0.0065] | −0.0033 | +0.009 | −0.016 | **+0.025 [+0.017, +0.033]** |
| **Win × rebounds** | 4631 / 1063 | −0.0006 [−0.0009, −0.0003] | −0.0003 | +0.014 | −0.004 | **+0.017 [+0.011, +0.024]** |

Full numbers, including 5-bin predicted-vs-realised calibration per type: `sgp_2026_RESULT.json`, `sgp_2026_by_type.csv`, `sgp_2026_dependence.csv`. Row-level pairs: `sgp_2026_rows.csv.gz`.

## Caveats

- **Pairs from the same game are not independent**; all intervals cluster by game. Pairs *within* a type still overlap (a player appears in several pairs), which is why the games column is the honest n.
- **Fixed league constants** (hca 2.0, sd_margin 13, sd_total 19) as in W109.3; engine marginals are known-biased, which is why dependence is scored against realised marginals and the log-loss/Brier columns compare engine joint and naive product *under the same engine marginals*.
- **Lines are the engine median**, not market lines. Market-line parlays may sit in different tails.
- **2026-27 season not used.** The public box-score releases stop at 2025-26; the ~96 2026-27 games W109.3 scored come from ESPN and were not pulled here. Stated gap, not an omission of an adverse result.
- Players limited to the top 3 by prior minutes per team; legs with engine probability outside 15–85% dropped; voided (did-not-play) legs dropped.

## Part C — does Kalshi list NBA combos today?

Checked via public unauthenticated GETs on 2026-11-10.

- **The product exists:** `KXMVENBASINGLEGAME` (series), with 196 per-game collections (e.g. `KXMVENBASINGLEGAME-26OCT07PHXCHI`) tying together `KXNBAGAME` (moneyline), `KXNBASPREAD` and `KXNBATOTAL` events: "choose any combination of game stats and props", YES only if every selected leg is YES, minimum 2 legs. The collection list ends at 2026-10-07/08; **zero NBA single-game combo markets are open today**, and none are open for the 2026-27 regular season in the listing. The open multi-leg product is `KXMVESPORTSMULTIGAMEEXTENDED` (cross-game, mostly esports and other sports), not a same-game NBA parlay.
- **Settled combo markets carry a `last_price`** (e.g. "Portland wins by over 5.5, no Over 220.5" last 0.459) but order books show 0 / 1.00 and no volume figure, so those prices are not a usable benchmark. We did not compare the engine joint to them (the rows are from the 2026 spring playoffs; the engine backtest above covers regular-season games only).
- **Therefore: no live combo price to compare, net of fee.** The comparison the block asked for is not possible today.

**What a same-game parlay would need before it could be a cell:**
1. An open combo market with a two-sided book (it must show bid/ask and volume; settled `last_price` alone is not a price).
2. A player layer with a shared latent (minutes / pace / usage) so same-player multi-stat and teammate pairs have the right dependence — the measured gap above.
3. A line-matched backtest on *market* thresholds, not engine medians.
4. The fee schedule for combo contracts (not published in the market payload; read from the Kalshi fee schedule before sizing any comparison).
5. A pre-registration before the first row. This block opens none.

## Stage per factor (ADR-0075)

| Factor | Stage | Note |
|---|---|---|
| Game-leg × team/player dependence (win, total, team total × points) | **applied (research)** — validated against the board's shape, no market price to test against | split: shared draws; rank: n/a; matchup cross: n/a; market map: no open combo book; application: this table |
| Same-player multi-stat, teammates | **interpreted** — the gap is measured, not yet fixed | needs the shared latent |

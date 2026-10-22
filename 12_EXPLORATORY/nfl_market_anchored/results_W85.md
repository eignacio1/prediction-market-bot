# W85.1 Part A -- the NFL market-anchored price, built offline (EXP-041 candidate)

Code: `anchored_price.py`, `anchor_gap.py`. Numbers: `results_W85.json`, `anchor_gap.json`. Frozen arms untouched; nothing wired.
Inputs (free): W77.2 out-of-sample engine means and factor terms (1,612 games, 2020-2025), nflverse closing lines and moneylines, the 2025-26 Kalshi KXNFLGAME 1-minute candles.

## What was built
- **Anchor:** the de-vigged market probability. Moneyline = de-vigged nflverse close. Spread / total / team-total ladders = Normal around the closing line, sigma from prior seasons' (outcome - close). Strikes fixed before any outcome: spread and total at close +/- {-5.5, -2.5, +0.5, +3.5, +6.5}; team totals at the implied team mean + {-2.5, +0.5, +3.5}.
- **Adjustment:** unpriced part = factor term x (1 - share priced), in points, pushed through each strike. Share priced b is refit every season on earlier seasons only (close ~ a + b0*engine + b*term). Moneyline shift uses the market's own logit-per-point slope (0.135, from the close alone, no outcomes).
- **Weight:** w per family = the grid value in [0,1] that minimises Brier on earlier seasons' out-of-sample adjusted predictions. Never P&L. 2021 has no earlier season: w=1, flagged. Reported 2022-2025 (n=1,087) with held-out w, and 2021-2025 (n=1,359) at w=1.
- **Gate input:** per family, lambda = slope of (outcome - anchor) on (adjusted - anchor) on earlier seasons, with its bootstrap SE. A market clears when |w*(adjusted - anchor)| * max(lambda - SE, 0) > Kalshi fee (0.07*p*(1-p), rounded up to the cent).

## Result: the adjustment does not beat the market net of anything
Paired dBrier of (anchor + adjustment) minus anchor alone. Negative = better. Game-clustered bootstrap, B=2000, seed 20261022.

| family | held-out w, 2022-25 (n=1,087) | w=1, 2021-25 (n=1,359) |
|---|---|---|
| ML | -0.00001 [-0.00010, +0.00009] | -0.00003 [-0.00028, +0.00022] |
| SPREAD | -0.00005 [-0.00024, +0.00015] | -0.00009 [-0.00050, +0.00033] |
| TOTAL | +0.00010 [-0.00030, +0.00050] | +0.00046 [-0.00022, +0.00115] |
| TEAM TOTAL | +0.00003 [-0.00014, +0.00021] | +0.00003 [-0.00041, +0.00047] |
| **POOLED** (mean of four) | **+0.00002 [-0.00014, +0.00017]** | **+0.00010 [-0.00023, +0.00042]** |

- Variants (all F8 + gated C, and F8 + C at b=0 upper bound) are no better: pooled held-out +0.00003 [-0.00005, +0.00011] and +0.00003 [-0.00004, +0.00009].
- **Markets clearing fee + measured error: 0 of 1,087 moneylines, 0 of 5,435 spread, 0 of 5,435 total, 0 of 6,522 team-total strikes.** The mean departure from the anchor at w=1 is 0.4-1.3 points of probability (ML 0.4, spread 0.8, total 1.3, team total 1.1); a Kalshi fee near 50c is 1.75c. The adjustment is smaller than the fee before any error is counted.
- The held-out w is mostly 0 (2023, 2024: all families 0 or 0.1). The data say "stay on the market" in most seasons; 2025 gave ML 0.9 / spread 0.8, which is one season and not a pattern.
- F5/F6 (coverage x personnel): share priced is unidentified (CI spans 0 and 1: spread -0.20 [-1.34, 0.68], total 0.17 [-0.73, 1.00], ML -0.13 [-1.24, 0.97]). Gate rule gives it zero weight. The b=0 upper-bound variant moves pooled dBrier by +0.00001: no signal there either.
- F8 share priced, fit through 2024: spread 0.67 [0.46, 0.91], total 0.33 [0.15, 0.55], ML 0.86 [0.58, 1.10]. Matches W77.2. The market prices most of F8 on the side/ML and about a third on the total; the unpriced total part is real in size but too small and too noisy to pay.

**Plain statement: with the factors that exist today, the market-anchored price is the anchor. There is no edge to clear a fee in the NFL game markets; this is a rigorous NO on the 2020-2025 close, not a failure of method.**

## The anchor-timing gap (Part A.1)
Kalshi KXNFLGAME home-side mid at T1 (ko-36h), T2 (ko-24h), T3 (ko-6h), CLOSE (ko-30min) against the de-vigged nflverse close, 188 games of 2025 season to 2026-01 (the only candles that exist; none for 2026, and spreads/totals/team totals were never fetched).

| horizon | gap to nflverse close, mean | gap SD | mean abs gap | Brier mid - Brier close [95%] |
|---|---|---|---|---|
| T1 ko-36h | -0.0004 | 0.026 | 0.0175 | +0.0018 [-0.0015, +0.0051] |
| T2 ko-24h | -0.0019 | 0.021 | 0.0154 | +0.0015 [-0.0013, +0.0044] |
| T3 ko-6h | +0.0005 | 0.015 | 0.0113 | +0.0021 [-0.0000, +0.0043] |
| CLOSE ko-30min | +0.0030 | 0.010 | 0.0087 | +0.0006 [-0.0009, +0.0021] |

- A T1 price sits 1.5-2.6 points of probability from the close on a typical game, which is 2-3x the size of the whole adjustment (0.4-1.3 points). An adjustment trained against the close would be applied to an anchor that moves by more than the adjustment before the game. Whatever the adjustment adds at T1 is swamped by anchor movement; whatever the market learns between T1 and the close it learns without the adjustment's help: the T1-to-close drift loads on F8 at -0.0014 per point [-0.0066, +0.0031] (n=159), i.e. no measurable F8 information arrives after T1.
- The close is slightly better calibrated than every earlier mid (Brier gaps all > 0, small): consistent with a market that sharpens toward kickoff and an adjustment that has nothing left to add to the close.
- **Missing data, registered rather than guessed:** no 2026 candles; no spread, total or team-total candles. The live anchor for those families cannot be measured historically. (GG to be registered at close.)

## Stage and granularity-index parts per factor (D5(b))
| factor | split | rank vs history | matchup cross | market map | application | stage |
|---|---|---|---|---|---|---|
| F8 injuries/availability (N10) | non-QB unit availability by unit | not built | unit x opponent not built | built: share priced per family, rolling | built: priced from the line, W85.1 | **applied against the market (priced from the line): NO measurable unpriced gain** |
| F5/F6 coverage x personnel (N7) | man/zone, QB efficiency | not built | built (interpreted) | built: unidentified | built: b=0 bound only | interpreted; applied-from-line shows no signal |

D5(b) NFL factors priced FROM the market's line: **0 -> 2 built (F8, F5/F6), neither with measurable unpriced gain.** D3 NFL pre-registered challengers: 1 -> 2 on Part B commit.

## Recommendation (Part A)
Do not wire next wave. Wire only the pre-registration and, in 85.2, the gate (it is the part that is right regardless of the factors: one position per market per band, pulled toward the market by measured skill; today that pulls to zero). The cheapest EDGE move is not another NFL adjustment: it is a factor with a larger unpriced part than F8 has (W77.2: MDE ~0.0014-0.0017 vs F8 effect ~0.0007).

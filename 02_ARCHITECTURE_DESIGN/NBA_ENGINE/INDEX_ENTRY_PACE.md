# NBA granularity-index entry 1 - pace and efficiency (W80.2)

**Date:** 2026-10-20 - **Pillar/measure:** DEPTH D5(b) NBA, D4 - **Decisions logged:** true
**Stage reached: aggregated -> interpreted -> APPLIED, verdict REAL-AND-PRICED (no gain).** Pre-registered tool and rules: `scripts/nba_totals_applied.py` (module docstring, fixed before results, sha256(ticker) 300-game subset fixed before results). Part 1-3 numbers: `scripts/nba_pace_index_parts.py` -> `nba_pace_index_parts.json`; part 5: `nba_totals_applied_result.json`. Definition of the five parts: `GRANULARITY_INDEX.md`. Frame: point-in-time NBA game frame, 2016-2026 regular seasons (season label = end year, so 2026 = 2025-26); base total model OLS on 2016-2025 (n=10,421, sigma 18.6 pts).

## 1. Split - does pace behave differently by rest, venue, opponent pace tier?
Residual = actual total - base prediction (points); 2016-2025 pooled vs 2025-26.
- **Rest (either team on 0 days rest vs neither):** 2016-2025 -0.15 (CI -0.79 to +0.47, n=3,244) vs +0.14 (-0.29 to +0.57, n=6,982): **no difference** - back-to-backs do not move the total (consistent with FACTORS_FIRST_READ: rest moves the margin, not the total). 2025-26: -3.5 (-5.7 to -1.5, n=318) vs -4.0 (-5.3 to -2.6, n=738): also no difference.
- **Home vs away:** the home-minus-away gap in a team's own prior pace is zero (-0.01, CI -0.07 to +0.06, n=10,421) and uncorrelated with the residual (r -0.01). Pace is a property of the matchup, not of which side hosts it.
- **Opponent pace tier (the other side's year-to-date pace, tercile cuts from 2016-2025):** the base model under-predicts totals when the opponent is fast: home team vs fast opponent +1.27 (CI +0.62 to +1.93, n=3,467), vs slow -0.87 (-1.46 to -0.26, n=3,470); away team vs fast +0.64 (0.00 to +1.27) vs slow -0.46 (-1.05 to +0.15). **This is the one real split: the base total (a plain average of the two teams' scoring) mis-weights pace**, which is exactly what the pace term in the full model corrects.
- **Regime note (do not skip):** in 2025-26 the base model over-predicts by about 4 points in every cell (e.g. -3.5, -4.0 above), i.e. scoring fell against the 10-year fit. The opponent-pace gradient is still there (slow -7.3 to fast -2.2, home side), and the market priced the level shift (part 5).

## 2. Rank - is this season's pace unusual for the point in the season?
League-mean year-to-date pace at the game-N checkpoint, 2025-26 vs the ten prior seasons (+-2 games window): game 10: 102.1 (history 100.7, range 98.2-103.1, percentile 0.8); game 20: 102.1 (100.4, 97.7-102.5, 0.9); game 30: 101.9 (100.2, 97.4-102.1, 0.9); game 40: 101.5 (100.1, 97.2-102.0, 0.8). **2025-26 was a top-two pace season of eleven at every checkpoint** (n=10 history seasons; percentile resolution 0.1). A fast league alongside a lower total than the model expected is the regime break in part 1 - efficiency fell while pace rose.

## 3. Matchup cross - team pace x opponent pace
Total on home pace + away pace, with and without a centred product term, fitted 2016-2025, scored on 2025-26 (n=1,075): interaction coefficient -0.16; MSE additive 390.2 vs with cross 391.6, **gain -1.4 (CI -3.7 to +1.1): no gain.** Pace is additive in the two teams; the matchup "cross" carries nothing the sum does not. (Part 1's tier gradient is the main effect of the opponent's pace, not an interaction.)

## 4. Market map - which Kalshi markets does this factor touch?
- **Game total (`KXNBATOTAL`)** - direct; priced here (part 5). Listed and ledgered (`NBA_GAME_TOTAL_T1`).
- **Team totals (`KXNBATEAMTOTAL`)** - direct and now listed (GG-891's "never listed" premise is stale, see DECISION_LOG 2026-10-20): own pace x opponent defence, same factor family; not yet tested.
- **Spread / moneyline** - indirect: pace scales variance of the margin (more possessions, wider spread); no direct test run.
- **First-half lines** - the factor is a full-game quantity; no free first-half price history loaded. Gap, unregistered as a cell.
- **Player points props (EXP-039/040)** - pace is an input to a player's expected volume (minutes x team possessions); no test run.

## 5. Application - does the market already price it? (`scripts/nba_totals_applied.py`)
KXNBATOTAL 2025-26 regular season, 300 games drawn by sha256(ticker) order (fixed before results; 1,075 season games, 14,787 markets listed), one "Over X" per game nearest the base prediction, price = mid of the 1-minute quote at tip minus 60 min (299 priced; one without a usable quote). Bootstrap B=2000, seed 20261016.
- **REAL** (out-of-sample on 2025-26, n=1,075): the pace/efficiency terms predict the total with coefficient **0.96 (CI 0.47 to 1.48)** - lower bound above zero, so the factor is real.
- **PRICED**: the market's implied mean loads on the same term with coefficient **1.05 (CI 0.80 to 1.29, n=299)** - the market uses it about one-for-one.
- **RESIDUAL**: outcome minus market probability on the same term **-0.05 (CI -0.47 to +0.41, n=299)** - zero within error; Brier of the market mid 0.2356.
- **Verdict: REAL-AND-PRICED** (the tool's pre-stated modal expectation). Pace is a true factor and Kalshi's NBA total already contains it. **A rigorous NO for a pace-only totals shadow cell: no pre-registration is drafted** (the rule drafts one only for REAL-NOT-PRICED). Power caveat: the residual CI is +-0.45 on a unit scale, i.e. an unpriced slice smaller than about half the factor would not show at n=299; the finding rules out "unpriced", it does not rule out a small remainder.

## What this moves
D5(b) NBA: the engine's first factor class (pace/efficiency, taxonomy N1/N2) goes interpreted -> **applied** (seat `B9`), with no gain over the market. Other NBA classes unchanged.

## Next factor through the five parts, and why
**Availability (game-level, taxonomy N10 / seat B5-B6), then travel (N5).** Pace, the class every price already contains, is priced; the classes with a *timing* edge are the ones whose information arrives after the schedule and before tip-off. Availability is interpreted twice (W69.3, W79 games-availability) but its history before 2026-09-08 is a registered gap (GG-910), so its first applied test is a prospective one: take daily injury snapshots through the 2026-27 season and score "who is out for either side" against the same KXNBATOTAL/spread prices. Travel needs a small hand-built arena table (GG-913) and is the cheapest class that no efficiency argument says the market has already absorbed.

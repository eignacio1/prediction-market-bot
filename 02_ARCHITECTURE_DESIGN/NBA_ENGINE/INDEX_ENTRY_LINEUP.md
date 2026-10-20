# NBA granularity-index entry 2 - lineup cross (who absorbs a missing teammate's usage) (W81.2)

**Date:** 2026-10-20 - **Pillar/measure:** DEPTH D5(b) NBA (complete index entries 1 -> 2) - **Decisions logged:** true
**Stage reached: aggregated -> INTERPRETED. No verdict word issued.** Part 5 (application vs market) was not run: the absence times cannot be joined to the KXNBAPTS price history (GG-985). Pre-registered rules: `12_EXPLORATORY/20261020_nba_lineup_cross/lineup_cross.py` docstring. Numbers: `results_partA.md`, `results.md`, `price_join_markets.csv` in the same folder. EXPLORATORY, not a verdict. Definition of the five parts: `GRANULARITY_INDEX.md`.

Operator, 2026-10-16: "Do we have mechanisms within the bot, spots within our decision tree, ranges within our architecture - to identify these opportunities AND FUCKING BLEED EM OUT? Just one of many examples." And 08:18 PT: "Beating Kalshi or institutions is a tall task - beating buddy off his phone placing parlays, that's the first step."

## 1. Split - who is out, by role
Rotation player (average >= 20 min over his last 10 played games) absent with an injury/illness DNP, single absence only, 2016-2025 regular seasons, 19,203 team-games. Frequency: creator out 1.6%, starter out 5.4%, rotation out 3.4%, clean 89.5%. Net of the clean-game control (-0.23 pts), the absorbers' points vs their own trailing-10 baseline: **creator out +1.75 (CI +1.46 to +2.06; +1.72 min, +1.43 FGA; 1,742 absorber-games, 310 team-games); starter out +1.00 (+0.84 to +1.18; 5,857 / 1,013); rotation out +0.34 (+0.14 to +0.54; 3,943 / 648).** Bootstrap resamples whole games.

## 2. Rank - is the redistribution a stable trait of the player?
Role level: yes. Player level: mostly not. Split-half (odd/even game) Spearman of pair-level uplift r = 0.117 (CI -0.267 to +0.482, 30 absorber-team-seasons) - not distinguishable from zero. Year-to-year r = 0.435 over 25 absorber-season pairs - suggestive. Pair mean-uplift quantiles under a creator absence: p5 -3.49, p25 -1.23, p50 +0.95, p75 +2.31, p95 +5.41. Reading: "a creator is out, so the others score about 1.75 more in total" is a stable regularity; "this particular player takes the shots" is largely noise at the samples available.

## 3. Matchup cross - with frequency
Creator-out uplift by opponent defence (trailing-30 points allowed, terciles over all team-games of the season): good D +1.06 (0.50 to 1.68), mid +1.29, weak D +2.55 (2.07 to 3.08). By opponent pace: fast +2.57 (2.05 to 3.13), mid +1.06, slow +1.52. Descriptive; not an interaction test. The cell that matters is rare (creator out 1.6% of team-games, times a weak-D or fast opponent).

## 4. Market map
- **Player points ladder (`KXNBAPTS`)** - direct: the absorber's own strike ladder ("N+" at x.5 strikes; 5,805 player-games listed, median 4 strikes each, strikes cluster at 9.5 and 14.5). Candles exist for only 100 markets in 93 events, all 2025-26.
- **Rebound/assist/three-point props** - the same absence moves them; no price history loaded.
- **Team totals (`KXNBATEAMTOTAL`)** - the team's own scoring does not move with usage redistribution among its players (the total is conserved), so lineup uplift is a *share* effect, not a team-total effect; a team total moves instead with the absent player's own scoring. Named, not tested.
- **Spread / moneyline** - absence moves these too, but that is entry 3's availability factor (taxonomy N10), not a redistribution effect.

## 5. Application - NOT RUN (gap GG-985)
Of the 100 priced markets, 12 (10 game-absorber pairs) have a rule-defined single absence; the injury reports observe the absent player in only 2, and both precede market creation. No market holds a before/after-news price, so the pre-registered pricing share cannot be computed and the time was not approximated. **No verdict word.** To run it: a snapshot of KXNBAPTS prices at the moment each absence is first reported (a prospective capture across 2026-27, taken at the report cadence), which is also what the sealed 2026-27 shadow rows will provide at their scored look.

## What this moves
D5(b) NBA: lineup (taxonomy N10 availability, usage redistribution) aggregated -> **interpreted** (seat `B10`). Index entries complete 1 -> 2 in count of entries with parts 1-4 written; **no second factor reaches "applied"**, so the applied count is unchanged at 1.

## Next factor
Availability at game level (N10 / B5-B6) with prospective timestamped capture, then travel (N5) - unchanged from entry 1; entry 2 shows availability needs timestamps before it can be priced.

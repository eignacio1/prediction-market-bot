# W93.2 — NBA travel / time-zone / altitude geometry (Part A)

Module: `src/prediction_market_bot/c1_signal_ingestion/nba_schedule_geometry.py` (merged, PR #362). Run: `12_EXPLORATORY/nba_geometry/run_w93_2.py` -> `results_W93_2.json`.
Stage: **interpreted** (ADR-0075). Not applied to a live model; nothing here is a runner, arm, order or registry cell.

## What it is
Point-in-time per team-game: miles since last game, time zones crossed (+ = east), rest, games in last 4/6 days, miles in last 7 days, road/home run length, venue altitude and altitude gain, tip hour on the team's home-zone body clock. Every feature uses only that team's earlier games and the published schedule; unknown city -> NaN, never a guess (4 of 11,979 games unmatched).

Known-answer test: a hand-checked 4-game week (LA / Denver / Brooklyn / LA across the 2026-11-01 DST change): distances 830 / 1620 / 2450 mi (+-2%), tz 1 / 2 / -3, rest 0 / 1 / 1, alt_gain 1519 m, road_run 0/1/2/0, games-in-last-4 [0,1,2,2], last-6 [0,1,2,3]. Plus as-of (future rows never move earlier rows), row-order invariance, NaN-on-unknown-city. 7 tests, CI green.

## When it applies / does not
Applies to NBA regular-season games with a matched ESPN venue city. Does not apply to neutral-site games with a city outside the table (NaN), and carries no information about in-game state.

## Held-out protocol (fixed before results)
Train 2017-2024 seasons, test 2025 and 2026 (and pooled), regular season. Baseline = W92.3 baseline plus prior-season carry. Metric = paired MSE gain over baseline (positive = better), 1,000-rep bootstrap over test games, seed 93_2. "Moves" = 95% interval excludes 0.

| Target | Spec | Pooled MSE gain [95% CI] | Moves? |
|---|---|---|---|
| Margin | travel + tz + altitude | -0.28 [-0.85, 0.27] | no |
| Margin | schedule density | +0.03 [-0.16, 0.22] | no |
| Margin | all geometry, with prior | -0.48 [-1.12, 0.16] | no |
| Margin | all geometry, without prior | -0.55 [-1.24, 0.13] | no |
| Total | all geometry (5 features) | -0.52 [-1.98, 0.89] | no (noise hurts) |
| **Total** | **venue altitude only** | **+0.92 [0.43, 1.44], n=2,150** | **yes** |

Altitude -> total: 2025 +1.12 [0.44, 1.77]; 2026 +0.72 [0.02, 1.49]; coefficient +0.81 points per 1,000 m (about +1.3 points at Denver). Caveat: one of 7 specs x 3 windows, not multiplicity-corrected; the 2026 lower bound is marginal. Read it as a small, plausible, physically-motivated total adjustment, not a proven edge.

**Honest NO on margin:** nothing in travel, time zones or schedule density predicts margin beyond team strength and the prior-season carry.

## Descriptive splits (all 2017-2026; league home margin 2.09, total 223.2)
- Altitude venue (DEN/UTA) n=791: home margin 5.09 [4.06, 6.08] vs 1.88 elsewhere (+3.21, mostly team strength, absorbed by baseline); total 224.7 vs 223.07 (+1.63).
- Visitor 2+ zones east n=720: home margin 1.18 (-0.97 vs rest; confounded, opposite of the folklore). 2+ west n=612: 1.28.
- Visitor travel >= 1500 mi n=900: 1.24 (-0.92). Host travel >= 1500 mi n=653: 1.44.
- Visitor played >= 4 of prior 6 nights n=266: 4.02 (+1.97). Visitor 4th+ road game n=1,625: 2.69.
- Late-body-clock start: host n=13 (too small); visitor n=631, total 224.6 (+1.47).

## Granularity index (five parts)
1. **Split:** altitude venue vs sea level, by visitor altitude gain; zones crossed by direction; miles; road-run length.
2. **Rank vs history:** altitude home margin by season: 2017 1.4, 2018 5.1, 2019 6.9, 2020 3.3, 2021 9.5, 2022 4.7, 2023 3.1, 2024 3.9, **2025 -3.4, 2026 -1.7**. The recent reversal is the thing to watch, not the all-time average.
3. **Matchup cross:** visitor altitude gain x visitor back-to-back x visitor road-run; sea-level visitor into Denver/Utah on the second night.
4. **Market map:** total only (altitude), via a venue term; margin/spread: no supported use. Moneyline: none.
5. **Application:** descriptive only. This season's Kalshi NBA total/spread rows are too few (tens) to compare to a price; underpowered, stated, not tested.

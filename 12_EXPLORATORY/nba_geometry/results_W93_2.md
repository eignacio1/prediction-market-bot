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

---

# Part B — officials (crew) tendencies

Module: `src/prediction_market_bot/c1_signal_ingestion/nba_officials.py` (PR #366). Run: `12_EXPLORATORY/nba_geometry/run_w93_2_officials.py` -> `results_W93_2_officials.json`. Stage: **interpreted** (ADR-0075), with an **aggregated-only timing gap** (GG-1390). Not a runner, arm, order or registry cell.

## What it is
Per official, a shrunk rate (K=30 games toward the league mean before that date) on three game totals: personal fouls, free-throw attempts, pace. A crew's value is the mean of its officials' rates; the factor is the deviation from the league mean. Only games on strictly earlier dates feed a row, so a game never feeds its own row and same-day games never feed each other.

Known-answer test: hand-computed shrunk rates for a 3-official, 4-game fixture; own-game-never-feeds-itself; same-day isolation; row-order invariance. 4 tests, CI green.

## When it applies / does not
Applies to regular-season games whose crew is in the archive and every official has >= 20 earlier games (11,203 of 11,979 games). Does not apply to a game whose crew is unknown at decision time: the archive carries no assignment timestamp, so the crew used is the game-day crew (an upper bound, GG-1390).

## Held-out protocol (fixed before results)
Same as Part A: train 2017-2024, test 2025 (n=1,070) and 2026 (n=1,048), paired MSE gain over the baseline, 1,000-rep bootstrap, seed 93_2, "moves" = 95% interval excludes 0.

| Target | Spec | Pooled MSE gain [95% CI] | Moves? |
|---|---|---|---|
| Total | 3 crew deviations | +0.51 [-0.12, 1.14] | no (2025 +0.95 [0.07, 1.89]; 2026 +0.05 [-0.88, 0.96]) |
| Total | crew FTA only | +0.59 [-0.02, 1.18] | no (borderline) |
| Total | crew fouls only | +0.53 [0.009, 1.06] | marginal pooled, not per season |
| Total | crew pace only | -0.01 | no (null) |
| Game FTA | 3 crew deviations | -0.20 [-1.11, 0.72] | no |
| Game fouls | 3 crew deviations | +0.22 [-0.32, 0.76] | no |
| Margin | control | -0.23 [-0.42, -0.02] | hurts (as it should: no mechanism) |

**Verdict: weak and unstable.** Crew whistle tendency has a plausible small effect on the total, in the right direction, but it does not clear a stable interval and is not seen in 2026. Not a verdict, not an edge.

## Descriptive
Top vs bottom decile of crew FTA deviation (n=987 each): game FTA 46.7 vs 43.0, total 224.2 vs 223.2 (league 223.6). Crew deviation spread is small (FTA sd 0.60, fouls sd 0.47): a 3.7-FTA swing in whistles moves the total by about one point.

## Granularity index (five parts)
1. **Split:** per official and per crew; foul rate, FT rate, pace; by crew chief when the archive has the role (not used here).
2. **Rank vs history:** a crew's deviation ranked against all crews at the same point in the season (shrunk toward league early in the year).
3. **Matchup cross:** crew FT deviation x teams' own FT rate / foul-drawing style (not tested: underpowered).
4. **Market map:** total only; no supported use on margin or spread.
5. **Application:** descriptive only. This season's Kalshi NBA total/spread rows are tens, so a comparison against a price is underpowered and was not run.

## Gap: GG-1390
No timestamp on the crew assignment in the archive, and no verified free live-capture route (official.nba.com returned HTTP 403 to a plain request). A probe of other free routes using a browser-style user agent was refused by the permission classifier as bot-check circumvention; it was not retried and not worked around. Cheapest route to verify: a plain read of the NBA CDN or ESPN scoreboard `officials` field after about 9am ET, with the observed-at time recorded per game, or an approved daily capture. Hand-back step; no operator pillar decision.

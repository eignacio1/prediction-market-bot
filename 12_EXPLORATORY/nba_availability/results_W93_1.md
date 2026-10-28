# W93.1 — NBA engine: availability known before tip

Block: W93.1, 2026-10-28, T-1420. Purpose: DEPTH. Measures: D5(b) NBA B5/B6 interpreted -> applied (or a measured reason why not); D4 NBA factor classes built point-in-time 1 -> 2.
Code: `src/prediction_market_bot/c1_signal_ingestion/nba_availability.py`, tests `tests/test_nba_availability.py` (9 pass). Driver `run_w93_1.py`, numbers in `results_W93_1.json`.

## Rules fixed before the run
- Cutoff = earliest tip time (lead 0). Sensitivity: lead 240 min. A report timestamped after the cutoff is never used (`AvailabilityLeakError`, tested).
- "Played" = at least 60 s of floor time.
- Play rates estimated on train seasons 2023-24 only (injury reports exist from 2022-23). Test seasons 2025 and 2026 (season label 2026 = 2025-26).
- Paired MSE gain, 1000-rep bootstrap, seed 93_1.

## Part A — status at the last pre-tip report -> P(played), lead 0, 2023-2026 rotation rows

| Status | n | P(played) | 95% interval |
|---|---|---|---|
| Out | 14,356 | 0.0008 | [0.0005, 0.0015] |
| Doubtful | 242 | 0.008 | [0.002, 0.030] |
| Questionable | 1,972 | 0.514 | [0.492, 0.536] |
| Probable | 823 | 0.919 | [0.898, 0.935] |
| Available | 3,936 | 0.856 | [0.845, 0.867] |
| Unreported (rotation player not listed) | 114,775 | 0.762 | [0.759, 0.764] |

- Lead 240 (4 h before tip): Out 0.003, Doubtful 0.021, Questionable 0.503, Probable 0.907, Available 0.774, Unreported 0.757. Available loses 8 points because late scratches are not yet visible.
- Stable by season (lead 0): Questionable 0.50 / 0.55 / 0.49 / 0.52 over 2023-26; Available 0.83-0.87.
- Rates used (train 2023-24): Available 0.843, Doubtful 0.008, Out 0.001, Probable 0.944, Questionable 0.521, Unreported 0.768.
- Coverage: 93.1-94.1% of team-games have at least one report before tip. Listed players hold only 12-17% of rotation minutes, so most of the rotation is "Unreported" and carries the base rate.

## Part B — interpreted (margin; test 2025 / 2026 / pooled, n = 1007 / 1001 / 2008)
Paired MSE gain over the named baseline, pooled, [95% CI]:

| Spec | Gain |
|---|---|
| rotation + expected availability (lead 0), incremental over baseline + prior + rotation | 0.307 [-0.235, 0.829] — does NOT move |
| same, lead 240 | -0.164 [-1.264, 1.007] |
| rotation + actual availability (upper bound), incremental | 0.956 [-0.674, 2.779] |
| rotation level | 1.813 [0.034, 3.541] |
| expected level (lead 0) | 2.005 [0.180, 3.974] — moves, pooled only |
| actual level (upper bound, GG-985) | 2.433 [0.436, 4.669] |
| expected missing minutes (lead 0) | 2.641 [0.038, 5.082]; 2026 alone 4.393 [0.957, 8.259] |

Reading, stated plainly:
- Using only what was known at tip, availability retains about 82% of the upper-bound level gain (2.005 / 2.433).
- Its increment beyond the rotation baseline is not distinguishable from zero on 2008 games (0.307, interval spans 0). 92.3's availability delta of 0.267 was an upper bound; the known-at-tip version does not demonstrably add. This is an honest NO at this n, not a failure.
- Missing minutes is the one availability-specific quantity whose interval excludes zero; it is the lead to carry forward.

## Part C — applied: not computable this block (measured reason)
Applied = a tested path from the fact to a price against the market. Blocked on data, not on method:
- The event store ends at 2025-26: no PBP-derived rotation or ratings for 2026-27.
- Relay injury reports cover about 8 days (2026-10-21 onward).
- NBA pre-game price capture (92.1) starts 2026-10-28 05:03Z.
- Public settled `KXNBAGAME` listings return the result and times but no pre-tip price; candlesticks are rate-limited (GG-1341) and cover roughly 55 games.
Registered as GG-1420 for the flex lane: refresh the 2026-27 event data and let pre-game price accrue; no new running component is needed (injury relay and capture exist, GG-985, GG-1030).

## Quant bar
1. Known-answer test: planted play rates are recovered by `play_rates` (test_known_answer). Leakage test: a post-tip report is ignored.
2. Applies when: a pre-tip report exists (about 93% of team-games) and the question is "who is likely on the floor". Does not apply when: the report is missing, or for unlisted rotation players, who get the base rate only.
3. Measured result: table above, n = 2008 games, intervals shown.

## Stage per factor (ADR-0075)
- B5 own-player availability: interpreted (P(played | status) with intervals; applied not reached).
- B6 game-level availability: interpreted (expected missing minutes; applied not reached).

## Granularity index (five parts)
- split: last pre-tip status -> P(played), by season and by lead.
- rank vs history: not yet a column (needs the same point in prior seasons).
- matchup cross: home minus away expected lineup rating; expected missing minutes.
- market map: total via expected pace and total points; margin/spread only through missing minutes.
- application: none yet (price and 2026-27 data gap, GG-1420).

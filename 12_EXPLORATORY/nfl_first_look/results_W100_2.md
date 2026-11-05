# W100.2 Part B — why the NFL game-total model lost (all 72 games)

Source: box task `nfl_total_agg_read` (`04_EXECUTION/BOX_TASKS/results/20261105T0140Z_w1002c_nfl_total_agg_read.md`), 207 (game, band) rows covering 72 games: T1 = 72, T2 = 72, T3 = 63 (9 games have no T3 row). Weeks 4-8, 2026 season. Analysis by game-level bootstrap (2,000 resamples, 95% interval); intervals are only quoted for slices of 8 or more games.

**Sign convention:** dBrier = model Brier minus market-mid Brier, per rung. **Positive = the model is worse.** Brier here is over strike rungs (about 19 per game), so rungs within a game are correlated; the unit of independence is the game.

## 1. The loss, all 72 games

| Band | Games | Rungs | dBrier | 95% interval |
|---|---|---|---|---|
| T1 | 72 | 1368 | +0.0151 | +0.0039 to +0.0266 |
| T2 | 72 | 1368 | +0.0149 | +0.0026 to +0.0279 |
| T3 | 63 | 1195 | +0.0148 | +0.0006 to +0.0287 |

The earlier 18-game read is confirmed at 72 games: the model is worse than the market mid, and the interval excludes zero in every band. The three bands are nearly identical, which is expected because T2 and T3 re-price the same game with little new information; they are not three independent confirmations.

## 2. Direction and size: it is not a bias, it is noise

- **Direction.** Mean (model p_yes − market mid) is −0.0014 (T1), −0.0007 (T2), +0.0037 (T3). Median-total gap (model minus market) is +0.21 / +0.26 / +0.44 points against a game-to-game spread of 3.2-3.8 points. 20 games have the model total more than 2 points above the market, 17 more than 2 below. The model is not systematically high or low.
- **The loss splits evenly by direction.** Games where the model sits above the market: +0.0166 (T1). Below: +0.0136 (T1). Both worse than the market.
- **The loss lives in the disagreement.** T1 games with |mean p gap| under 0.03 (20 games): dBrier ≈ 0.000. Games at 0.03 or more (52 games): +0.0213 [+0.0045, +0.0374]. Splitting by median-total gap: the half with the smaller gap is +0.0021, the half with the larger gap is +0.0282 (T1; T2 +0.0017 / +0.0281; T3 +0.0009 / +0.0283). Correlation of gap size with loss: 0.37 / 0.30 / 0.15.

Reading: where the model agrees with the market it costs nothing; where it departs from the market, the departure is wrong on average. That is the signature of disagreement with no information behind it. The market mid already carries what the model knows, and the model's extra deviations add variance.

## 3. By market total, roof and week (T1; T2 and T3 match within about 0.003)

| Slice | Games | dBrier T1 | Interval |
|---|---|---|---|
| Market median total < 41 | 11 | +0.0415 | +0.0098 to +0.0709 |
| 41 to 47 | 37 | +0.0048 | −0.0065 to +0.0163 |
| 47 and above | 24 | +0.0189 | −0.0073 to +0.0428 |
| Dome or closed roof | 21 | +0.0310 | +0.0059 to +0.0546 |
| Outdoors or open roof | 51 | +0.0085 | −0.0042 to +0.0214 |
| Week 4 | 15 | +0.0318 | +0.0098 to +0.0536 |
| Weeks 5-6 | 29 | +0.0142 | −0.0085 to +0.0373 |
| Weeks 7-8 | 28 | +0.0070 | −0.0063 to +0.0213 |

- **Low-total games** are the worst slice: the model's distribution is least able to match a market that expects a slow game.
- **Dome and closed-roof games lose about 3.6x more than outdoor games** (+0.031 vs +0.0085). This is the surprise. With no weather to model, the dome games should be the easy ones, so the model is not failing on weather; it is failing on the baseline scoring environment.
- **The loss shrinks across the sample**: +0.032 in week 4, +0.014 in weeks 5-6, +0.007 in weeks 7-8. Consistent with a model with thin early-season information that firms up as team form data accrues, but this is three adjacent windows on one season, not a trend test.
- **By strike bin** (T1, rungs): low strikes (under 38.5) +0.0068; 38.5-44.5 +0.0260; 44.5-50.5 +0.0207; high (above 50.5) +0.0126. The loss concentrates in the middle of the distribution, where the market is least certain and the rungs carry the most information, not in the tails.

## 4. Weather: not testable from this data

Temperature and wind are present for only 11 of 72 games (61 are blank); among those 11 the maximum wind is 11 mph and none is under 45°F, so there is no cold-or-windy slice at all. **No weather conclusion can be drawn.** That 51 games are outdoors and only 11 have weather populated is a data-join gap (the schedule lookup, with its previous-day fallback, returns blank for most games), and it matters for the DEPTH pillar: the weather factor class is not applied in the NFL total model's inputs for most games. Registered as a finding in the handoff rather than fixed here.

## 5. Which inputs drove the misses

The aggregates carry the model's outputs, not its per-feature contributions, so this is inferred, not measured:

- The misses track **disagreement magnitude**, not direction, not weather, not total level alone. A model whose features were informative would show loss falling as disagreement grew; here it rises.
- The dome result points at the **base scoring-rate estimate** (team offence/defence rates entering the total), since weather cannot explain it.
- The early-weeks result points at **thin in-season sample** for those rates.
- No evidence in this cut for or against any specific feature; a per-feature attribution needs the model's feature vector per game, which is a separate box read.

## 6. Note for the NFL engine (ADR-0073 / D4, D5)

1. **Anchor to the market, then add.** Until a factor class beats the mid out of sample, the engine's total should shrink toward the market median. The measured gap says departures are currently cost, not edge.
2. **Fix the weather join first.** 61 of 72 games had no weather. A factor class that is built but blank for 85% of games is not "applied" in the D5 sense.
3. **Dome games are the cleanest test bed** for the base scoring-rate component (no weather, no wind): improve it there first.
4. **Judge by game, not rung.** About 19 rungs per game are not independent; the 72-game interval is the honest one.
5. This reading closes the loss decomposition; it does not reopen the RULED_OUT verdict. The arms keep logging, and any new engine is a new pre-registered cell.

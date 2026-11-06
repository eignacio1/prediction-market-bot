# W105.3 result — MLB engine data layer started (B-018)

**Status: DONE.** Descriptive only; no pre-registration (per block). Measure: D4 MLB, event-level data layer **0 → started**.

## What exists now
- `src/prediction_market_bot/mlb_engine/`: `fetch` (resumable Savant fetcher, one request per game date), `store` (clean / PA / games / lineups), `pit` (point-in-time pitcher + batter tables), `checks`, `model`. 12 tests, all passing (known-answer synthetic season, truncation invariance, perturbation, doubleheader, mocked box score).
- Data (off-box, outside the repo, `~/mlb_store`): **2024 and 2025 regular seasons, 1,424,427 pitches, 366,010 PAs, 4,859 games (2,429 + 2,430), 87,462 lineup rows.** Free sources only; nothing installed on the box.

## Checks (2025 sample unless stated)
| Check | Result |
|---|---|
| Duplicate pitches on (game, at-bat, pitch) | **0** of 1,424,427 |
| Player ids resolved against the Chadwick register | **pitchers 1,113/1,113, batters 788/788** |
| Pitch count vs Stats API box score, 25 random 2025 games | **19 exact; mean abs diff 0.84, max 6 pitches**; unexplained, likely pitches Statcast does not track (not investigated) |
| Final score vs box score, same 25 games | **25/25 match** |
| Point-in-time | truncation-invariance and perturbation tests pass: no row uses a later game's data |

## Part C — minimal game model (train 2024, hold out all of 2025, n = 2,430 games)
Poisson regression of a team's runs on shrunk lineup wOBA, opposing starter's shrunk wOBA-allowed and home flag (both from the PIT tables as of the game date); independent Poisson runs → P(home win) (ties split) and P(total > 8.5). Baseline: the 2024 home-win rate (0.5216) and over-8.5 rate (0.4850).

| Market | Brier model | Brier naive | Naive − model (positive = model better) | 95% game bootstrap |
|---|---|---|---|---|
| Moneyline | 0.24781 | 0.24862 | +0.00080 | [−0.00096, +0.00254] |
| Total 8.5 | 0.24933 | 0.24985 | +0.00052 | [−0.00137, +0.00250] |

**Reading it plainly:** the model is nominally ahead of a constant in both markets, but both intervals contain zero, so this is **not distinguishable from the naive baseline**. That is the expected size for a two-factor model; it prices no bullpen, park, weather, platoon or posted lineup. It is also **not a comparison with the market**, which the naive baseline is not. A known-answer test of the plumbing, not evidence of edge.

**When the technique applies / does not:** rolling PIT skill → run expectancy applies to ranking and pricing a game from skill known the day before. It does not price within-game state, bullpens, or anything the lineup card changes.

**Soft spots to carry forward:** (1) lineup = the first nine distinct batters of the game as played, so a late scratch leaks a little same-game information (a posted lineup card removes it); (2) the 8.5 total line is a fixed convention, not the market's line; (3) 2024 history is empty for early-2024 rows, so shrinkage dominates there.

## Next three steps
1. **Price against a market, not a constant:** pull historical MLB closing moneyline/total (free source) or the Kalshi book for 2025 and score the model's Brier and log-loss against implied probability; this is the only comparison that bears on edge.
2. **Add the factor classes already in the tables and the ones not yet built:** apply the platoon splits (`woba_vsL/vsR`, already computed) to the lineup–starter matchup; add bullpen usage, park factors and the posted lineup (fixes leak 1). Each reports its stage (aggregated → interpreted → applied).
3. **Move from a team-run model to the engine:** simulate plate appearances (batter × pitcher outcome probabilities) to get one joint distribution, then read moneyline, run line, total, team totals and props from it; extend the store back to 2015 for training depth.

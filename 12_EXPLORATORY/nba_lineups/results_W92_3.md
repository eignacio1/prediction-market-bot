# W92.3 — NBA engine, B7 lineups and on/off, built point-in-time from the play-by-play

Purpose (Hard Rule 12): DEPTH. Measures: D5(b) NBA B7 none → interpreted; D4 NBA first factor class built point-in-time from event-level data.
Code: `src/prediction_market_bot/c1_signal_ingestion/nba_lineups.py`, tests `tests/test_nba_lineups.py` (6, pass), driver `12_EXPLORATORY/nba_lineups/run_w92_3.py`, raw numbers `results_W92_3.json`.

## Verdict
- **Total (points scored by both teams): B7 reaches INTERPRETED.** Point-in-time rotation-weighted lineup pace/efficiency lowers held-out MSE of the total by 4.04 (95% CI 1.92 to 6.10; ~1% of ~330-385), n=2008 games, and the gain survives a prior-season-carry control (3.99, CI 1.89 to 6.23). 2025-26 alone: CI includes 0 (2.51, -0.45 to 5.30).
- **Margin: honest NO beyond prior-season carry.** Pooled gain 0.038 (0.008 to 0.066) over team form + rest, ~0.03% of MSE; over baseline + prior-season carry 0.060 (-0.067 to 0.187). On/off swing adds nothing (-0.008, -0.037 to 0.020).
- **Availability delta (who actually played minus who the rotation expected)** is the only margin-side signal: 0.267 (0.105 to 0.445), n=2008. It uses who played in game G, so it is an upper bound until an injury/active feed exists (B10, GG-985). Not usable as a pre-game input today.
- **Applied: NOT TESTED. Underpowered / infeasible.** Public Kalshi lists settled NBA markets since 2026-10-20 for 55 game events (moneyline), 31 spread events, 36 total events (read-only public GET, 2026-10-28). NBA pre-game price capture is not installed on the box (W91.3 cron lines registered, not installed; the archive holds MLB + NFL only), so no pre-game price exists for these; a ~1% MSE effect cannot be seen in n ≈ 30-55 regardless. Stage stays interpreted, not applied.

## Part A — stints from the play-by-play
- Per-event five-on-floor from PBP + lineups; possessions = FGA + 0.44 FTA − ORB + TOV; stints carry seconds, points, possessions.
- Games dropped, never repaired: null/duplicate player ids or reconstructed length off by more than 2%. About 3-9% of games per season (e.g. 2025: 1400 games, 92 bad player rows, 6 bad length, 1303 kept, 1230 kept and eligible).
- Validation against box minutes (2025): 25,917 player-games, 94.6% within 1 minute, median absolute error 0.067 min (~4 s), p95 1.13 min. Also run for 2019, 2023, 2026 (JSON).
- Ratings: per player-game as-of ratings (net, points-total, pace per 100 possessions, on/off swing), shrunk P/(P+K) toward the team mean with **K = 1000 possessions** (prior stated; not tuned), prior seasons decayed 0.5 per season gap; as-of rule: tip of the latest game used + 4 h ≤ tip of the target game, so same-day games never feed each other. 282,002 player-game ratings; 26,448 team-game feature rows.
- Team lineup features: trailing-10 same-season rotation floor-time weights × as-of player ratings (lineup_net, lineup_ptot, lineup_pace, lineup_swing); `_act` variants use who played in G.
- Tests: known-answer simulated league (rating recovery corr > 0.8); shrinkage ordering and zero rating at first game; leakage (perturbing own or future games leaves ratings for G and earlier unchanged); same-day isolation; feature equals manual rotation-weighted sum; toy stint build.

## Part B — held out (train 2017-2024 regular season; test 2024-25 and 2025-26)
Gain = baseline MSE − (baseline + factor) MSE; 95% CI from 1000 game-clustered bootstrap reps (seed 92_3). Baselines: margin = team-form net rating diff + deviation + rest + back-to-back; total = pace, efficiency, deviation, back-to-back (B1 and B9).

| Target | Variant | 2024-25 | 2025-26 | Pooled (n=2008) |
|---|---|---|---|---|
| margin | rotation (point-in-time) | 0.038 [−0.003, 0.081] | 0.039 [−0.001, 0.079] | 0.038 [0.008, 0.066] |
| margin | rotation + swing | | | −0.008 [−0.037, 0.020] |
| margin | availability-known (upper bound) | | | 0.073 [0.026, 0.119] |
| margin | availability delta over baseline + rotation | 0.228 [0.027, 0.453] | 0.306 [0.044, 0.593] | 0.267 [0.105, 0.445] |
| margin | rotation over baseline + prior-season carry | 0.126 [−0.043, 0.281] | −0.007 [−0.188, 0.172] | 0.060 [−0.067, 0.187] |
| total | rotation | 5.55 [2.87, 8.30] | 2.51 [−0.45, 5.30] | 4.04 [1.92, 6.10] |
| total | availability-known | | | 4.78 [2.44, 7.11] |
| total | rotation over baseline + prior-season carry | 5.34 [2.27, 8.25] | 2.62 [−0.45, 5.60] | 3.99 [1.89, 6.23] |

n by season: 1007 (2024-25), 1001 (2025-26). Ad-hoc, no valid CI (not cited as a result): the total gain looks larger in the first quarter of a season, which would fit the layer carrying roster information when year-to-date stats are noisy.

## When it applies, when it doesn't
Applies to totals, most where team year-to-date pace/efficiency are noisy (early season, roster turnover). Does not add to the margin once last season's team strength is known. Not usable on game day for availability until an injury/active feed is wired.

## Granularity index (five parts), B7
1. Split: player on/off and rotation-weighted relative rating per 100 possessions, by net, points-total, pace.
2. Rank vs history: shrunk rating ranked against the same point in prior seasons (computed in the ratings table; not yet surfaced as a rank column).
3. Matchup cross: home minus away lineup strength; availability delta (played minus expected).
4. Market map: total through rotation pace and points-total; margin and spread only via the availability delta.
5. Application: none yet. Blocked on NBA price capture (92.1) and an availability feed (GG-985).

## Caveats
K = 1000 and decay 0.5 were not tuned and no sensitivity was run. Only the dropped-game rate (3-9%) selects which games enter; dropped games are not special by construction but this was not tested. Single train/test split, two test seasons.

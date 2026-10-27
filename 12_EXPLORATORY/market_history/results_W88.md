# W88.3 — frozen models scored against the market, with intervals

Purpose (Hard Rule 12): PROOF. Measure: frozen models with a market-referenced held-out Brier, 2 → 5 of 6 (nfl_pregame_v1 from W87.3 plus NHL, NBA, MLB here; two are not scored, reasons below). Offline only; gate stays unwired; no frozen file, ledger, order or stake touched.

Method: frozen model files unchanged, live-runner feature code, inputs rebuilt point-in-time as of game start − 1h (the band decision time). Market price = de-vigged mid of the last Kalshi hourly candle ending ≤ start − 1h (public GETs), flipped to the home side. Paired Brier difference "market − model" (positive = model beats market) via `quant.scoring.brier_diff`, 95% game-clustered percentile bootstrap (2000 resamples, seed 20261002) via `quant.inference.cluster_bootstrap`. Skill weight = `position_gate.skill_weight` = clip(1 − Bm/Bk, 0, 1).

| Model | Season scored | n | Brier model | Brier market | market − model | 95% CI | skill weight |
|---|---|---|---|---|---|---|---|
| nhl_pregame_v1 | 2025-26 (held out) | 1,305 | 0.24720 | 0.24419 | −0.00301 | [−0.00623, −0.00005] | 0.0 |
| nba_pregame_v1 | 2025-26 (unseen; artifact held-out was 2024-25) | 1,228 | 0.20923 | 0.19422 | −0.01502 | [−0.02084, −0.00891] | 0.0 |
| nba_pregame_v1, ≥30 prior in-season games | same | 773 | 0.20472 | 0.18515 | −0.01956 | [−0.02697, −0.01198] | 0.0 |
| mlb_game_pregame_v1 | 2025 (held out) | 2,037 | 0.24236 | 0.24280 | +0.00043 | [−0.00300, +0.00374] | 0.0018 |
| nfl_pregame_v1 (W87.3, no interval) | — | 271 | 0.2193 | 0.2121 | −0.0072 | — | 0.0 |

Read plainly:
- NBA: the market is better, and the interval excludes zero. NHL: the market is better by a margin whose interval barely excludes zero. MLB: indistinguishable from the market (interval spans zero), skill weight 0.0018 — numerically non-zero, practically zero. No arm has shown it knows something the line doesn't.
- Gate replay (descriptive, `gate_replay_descriptive` in each JSON): at the implied weight the gate keeps 0 positions for all three (MLB's 0.0018 is too small to clear the gate). The counterfactual "model fully trusted" weight 1.0 is labelled as such; its realised flat 1-contract P&L (NHL +0.028, 257 kept; MLB +0.052, 417 kept; NBA −0.012, 280 kept) carries no interval, is selected on the model's own disagreement, and is not evidence of edge. The gate correctly places nothing.

Drops (never silent): NHL no_market 5, no_pre_game_quote 2. NBA no_pre_game_quote 2, no_market 1. MLB no_market 133, no_pre_game_quote 56, outcome_disagrees 18, ambiguous 3 (of 2,247 predicted; 153 of 2,400 season games skipped for insufficient prior history or ties).

## What could not be rebuilt, and why
- nba_player_points_v1: needs per-player predictions rebuilt point-in-time for 23,562 KXNBAPTS markets plus per-market candles; not feasible in the block ceiling at the public-GET rate. Not scored (`models/nba_player_points_v1_heldout_vs_market_w88.json`, status NOT_REBUILT).
- nfl_qb_challenger_v1: no held-out season exists (trained through 2024, calibrated 2025, 2026 sealed). NONE.
- NBA: Kalshi game history starts 2025-26, after the artifact's held-out season, so this is a post-held-out out-of-sample test, not the held-out set itself. 2024-25 history came from the schedule parquet with a synthetic 23:30Z start (affects early-season rest/back-to-back only).
- MLB: moneyline only; home_sp/away_sp are starters recorded after the fact (late scratches not modelled); features are date-cutoff.

## Quant bar for the technique added (paired per-game Brier difference with a game-clustered interval)
1. Known-answer test: `tests/test_market_history_score_vs_market.py::test_summarize_known_answer`.
2. Applies to paired per-game binary forecasts with game clusters; does not apply to serially correlated in-play rows (rows within a game are not independent and inflate n).
3. Measured results with n and interval: table above.

## ADR-0075 stage per factor
No new factor built. Existing factors stay as the frozen models have them; this block moves PROOF only: the scored look is the "tested" step, with no change to aggregated/interpreted/applied stages.

## Notes
- Auto-mode permission denial (verbatim): `scp`-ing a script to the box (`scp ... prediction-market-vps:/tmp/mlb_model_side.py`, then running it there) was denied: "Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Remote Shell Writes]." Workaround (read-only): scp'd the box's parquet to the scratchpad and ran locally. No retry.
- The 12_EXPLORATORY write fence flagged the first CI run (scripts wrote files / used `.replace`); fixed in-PR (#338): scripts emit JSON on stdout, shell redirects.
- Two-ended fetch (`fetch_game_hourly.py --reverse --meet-file`) cut MLB/NHL wall time; shards merged and deduplicated by ticker.
- Read these results as one season each for MLB/NHL and a post-held-out season for NBA; a pre-registered look at larger n is still the only thing that issues a verdict.

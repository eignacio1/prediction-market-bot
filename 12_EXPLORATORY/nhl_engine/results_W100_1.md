# W100.1 Part A: where the NHL regulation total comes from, and a new version (model_pit)

Held out 2023-2025 (walk-forward, fit on earlier seasons only). Exploratory; merged `model.py`/`inputs.py` unchanged. Scripts: `run_w100_1.py`, module `src/prediction_market_bot/nhl_engine/model_pit.py`, tests `tests/test_nhl_engine_model_pit.py`.

## Finding (plain)
The low total is a mix of three things, none of them shrinkage or half-life:
1. **Stale league denominator in the matchup cross** (fixable, fixed in `model_pit`). `lg_f5`/`lg_pp` come from earlier seasons (older xG vintage) while team rates come from the current vintage; the cross is scaled down by the vintage gap. Mean `lg_f5` vs mean team rate: 2.757 vs 2.676 (2023), 2.661 vs 2.555 (2024), 2.621 vs 2.605 (2025).
2. **Season-to-season xG drift** (not fixable here). Goals/xG in the event store: 0.966, 0.999, 0.989, 0.947 by season (about +-3%). League scoring moves with it.
3. **Early-season level error** (irreducible without new information). `level_adjust` prior_games=150 is about optimal on the noise/drift ratio (~178 games); bias is worst early in a season and in the lowest-predicted games.

Ruled out: shrinkage strength and half-life (grid: the merged setting hl=40, prior 3h has the best held-out log-likelihood; bias stays near -0.08 at every setting). Power-play and 5v5 time: expected vs actual seconds match within ~5% (2023 PP home 350 vs 352; 2024 335 vs 329; 2025 332 vs 346; 5v5 2861 vs 2858, 2862 vs 2915, 2882 vs 2879), no bias that could explain -0.1 goals.

Also seen: predictions are over-spread across games (slope of actual total on predicted total ~0.4-0.5, all settings). That is a calibration-slope issue on the rate, not a level issue; not addressed here (would need its own pre-registered challenger).

## Held-out regulation-total bias (predicted minus actual goals/game, after level_adjust)

| season | n | actual | merged | model_pit |
|---|---|---|---|---|
| 2023 | 1312 | 6.018 | -0.149 | -0.118 |
| 2024 | 1312 | 5.874 | -0.095 | -0.043 |
| 2025 | 1312 | 6.005 | +0.006 | -0.014 |
| pooled | 3936 | | -0.080 | -0.059 |

The fix removes about a quarter of the pooled bias. It is a partial fix, stated as such.

## Brier per Kalshi family (paired, game-clustered bootstrap, 2000 resamples; difference = model_pit minus merged, negative = better)

| family | n games | merged | model_pit | diff [95% CI] |
|---|---|---|---|---|
| ML | 3936 | 0.23929 | 0.23939 | +0.00010 [-0.00011, +0.00032] |
| SPREAD_HOME | 3936 | 0.19705 | 0.19699 | -0.00006 [-0.00021, +0.00008] |
| TEAMTOTAL_AWAY | 3936 | 0.23484 | 0.23495 | +0.00011 [-0.00011, +0.00033] |
| TEAMTOTAL_HOME | 3936 | 0.23282 | 0.23264 | -0.00018 [-0.00041, +0.00004] |
| TOTAL | 3936 | 0.22152 | 0.22138 | -0.00014 [-0.00041, +0.00013] |

Every interval includes zero: no family's Brier moves beyond noise. Applicability: regular-season frames from `game_features`; first games of a frame fall back to the original `lg_*`. 2026 vs Kalshi (descriptive): not run in this block; it needs the live 2026 archive and is left to the window.

## EXP-046
Not earned: bias shrinks but Brier does not move, and the remaining gap is not removed. No pre-registration filed. If the window wants one, the candidate is a rate-slope (over-dispersion) challenger, not this denominator.

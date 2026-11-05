# NHL totals challenger — pre-registration (W101.1 Part C, B-029)

Committed BEFORE any challenger row exists. Exploratory (12_EXPLORATORY); merged `model.py`/`inputs.py`/`model_pit.py` untouched; no orders, no cron, no registry cell.

## Reproduced baseline (this block, 2026-11-05, frame rebuilt from the local NHL event store, `run_w100_1.py`)
Held-out regulation-total bias, predicted minus actual goals/game after `level_adjust`: model_pit 2023 -0.118, 2024 -0.043, 2025 -0.014, **pooled -0.059** (merged -0.080); n = 1,312 x 3 = 3,936 games. Reproduces results_W100_1.md exactly. The calibration slope (0.4-0.5) is re-measured by the challenger run's own baseline row, on the same split, before the challenger is read.

## The problem
Predicted game totals are over-spread: regressing actual total on predicted total gives slope ~0.4-0.5 (< 1). The level problem (bias) was handled by W100.1 (denominator) and `level_adjust` (season-to-date level, prior 150 games, near-optimal by W100.1's grid). What remains is spread.

## Candidates considered (one is registered)
1. Season-to-date scoring level — ALREADY in the merged model (`level_adjust`); W100.1 grid found it near optimal. Not re-run.
2. **Registered: shrink the predicted total rate toward the league mean.**

## The challenger (fully specified)
For each game, with model_pit rates (lam_h, lam_a): T = lam_h + lam_a, share = lam_h / T. Replace T by `T' = m + s * (T - m)`, keep `share`, then apply the unchanged `level_adjust`, then the unchanged simulator.
- `m` = mean of T over the training seasons' games (constant per test season).
- `s` = slope of actual regulation total on predicted T, estimated from **training seasons only** by 2-fold cross-fitting (games split by game-date parity within the training window; fit on one fold, predict the other, pool), clipped to [0.3, 1.0]. No test-season outcome enters `s`. (Choosing s = 0.5 from the W100.1 table would have used the test seasons; this avoids it.)

## Split
Walk-forward exactly as W100.1: test seasons 2023, 2024, 2025 regular season; each fits on seasons strictly before. 2026 (partial) is not in the judged set; reserved for a later descriptive look against Kalshi.

## Metrics
Brier per Kalshi family (ML, SPREAD_HOME, TOTAL, TEAMTOTAL_HOME, TEAMTOTAL_AWAY, as `run_w97_4.probs`), challenger vs model_pit (primary) and vs merged (secondary), paired, game-clustered bootstrap 95% CI (2,000 resamples). Also reported: pooled and per-season regulation-total bias; held-out slope of actual on predicted total. Kalshi comparison is descriptive and not run here (no 2023-25 archive).

## Judged n
Primary: all 3,936 held-out games (minimum 3,000). Minimal effect of interest: Brier -0.0005 on TOTAL. W100.1's CIs on a comparable arm were about +-0.0003 at this n, so a -0.0005 effect is detectable; a smaller one is reported as "no detectable gain" rather than a pass.

## Decision rule (fixed now)
- **PASS (challenger earns a follow-up forward pre-registration):** TOTAL, TEAMTOTAL_HOME and TEAMTOTAL_AWAY all improve vs model_pit with 95% CI excluding zero, AND no family is worse with CI excluding zero, AND pooled held-out slope is within [0.8, 1.2] or closer to 1 than model_pit's.
- **NO:** any other outcome, including improvement on TOTAL alone. A NO is a result.
- A PASS here is a historical held-out finding, not edge: it grants a forward pre-registration, never a cell, an order or a Kelly fraction.

## Guardrails
No real capital, `kelly_fraction` 0, merged model untouched, no cron line, no production data written. Code: `src/prediction_market_bot/nhl_engine/spread_shrink.py` (new), tests `tests/test_nhl_engine_spread_shrink.py`, runner `12_EXPLORATORY/nhl_engine/run_w101_1.py`.

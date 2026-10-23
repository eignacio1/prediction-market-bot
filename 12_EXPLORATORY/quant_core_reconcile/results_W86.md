# W86.1 results: one measurement core, reconciled (2026-10-23)

PURPOSE: pillar PROOF. Measures: scorers agreeing with the core 0 -> 2 named paths (pregame_shadow scoring + calibration_engine, NHL, 6 cells); frozen models with a market-referenced held-out Brier 0 -> 1 of 6 (nfl_pregame_v1; the other five NONE).
Core: `src/prediction_market_bot/quant/` (merged, PR #328, 11 known-answer tests). Read-only on every ledger/model/runner.

## 1. Reconciliation (old value | core value | difference | reason)
Source: engine_20261022T134955Z.json + box copy of NHL ledgers (HEAD 2c8b2642). Delta = Brier(market) - Brier(model), positive = model better; 95% game-clustered bootstrap, B=10000, seed 20261002.

| Cell | n rows / games | delta (engine = core) [95% CI] | difference |
|---|---|---|---|
| NHL_GAME_TOTAL_T1 | 1053 / 117 | +0.021242 [0.014345, 0.027950] | <1e-6 |
| NHL_GAME_TOTAL_T2 | 1124 / 125 | -0.000328 [-0.004759, 0.004128] | <1e-6 |
| NHL_MONEYLINE_T1 | 234 / 117 | -0.001975 [-0.016197, 0.011360] | <1e-6 |
| NHL_MONEYLINE_T2 | 250 / 125 | -0.000745 [-0.014601, 0.012244] | <1e-6 |
| NHL_PUCK_LINE_T1 | 467 / 117 | -0.000778 [-0.008092, 0.005908] | <1e-6 |
| NHL_PUCK_LINE_T2 | 500 / 125 | -0.005018 [-0.012191, 0.001476] | <1e-6 |

Brier(model), Brier(market), log loss, Murphy reliability/resolution/uncertainty also agree to ~1e-15 on all six (full numbers: `nhl_recon.json` logic in `reconcile_nhl.py`). Engine's `brier_decomposition` is binned Murphy without a within-bin term; the core also reports `within_bin`. The core adds ECE and slope/intercept, which the engine does not report (GAME_TOTAL_T1: ECE 0.0535, slope 0.385, intercept 1.284 = the model is overconfident on that cell).
Not reconciled this block (named, not claimed): `analytics/calibration_diagnostics.py`, `pregame_shadow/fees.py` k007 vs `quant.money`, `distance_to_optimum.py` E2/E3, the forward-test (book, sport) figures, `c3_forecasting` scorers. 43 of 49 cells are SEALED: counts only, no score computed.
NFL held-out file: engine-file Brier 0.218528 (n=272) vs core on the same frozen model 0.219275 (n=271, ties excluded as in training). The 0.0007 gap is probably the tie game; NOT verified.

### D3 (challenger count 1, expected 2)
`scripts/distance_to_optimum.py d3()` counts only `.md` under `12_EXPLORATORY/` or `03_DECISIONS/` whose filename contains "challenger" and which carry `**Status:** PROPOSED|ACCEPTED`. EXP-041 (`05_RESEARCH_EXPERIMENTS/EXP041_NFL_MARKET_ANCHORED_PREREGISTRATION_2026-10-22.md`) is missed three independent ways: directory outside the scan, no "challenger" in the filename, status is `FROZEN`. The 1 counted is probably `12_EXPLORATORY/NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md` (D3 not run). Registered as GG-1100, not fixed.

## 2. Market-referenced held-out Brier per frozen model
| Model | Result |
|---|---|
| nfl_pregame_v1 | 2025 REG moneyline, n=271 games vs de-vigged nflverse close: model 0.21928, market 0.21214, paired diff (market - model) -0.00714 [-0.01976, +0.00549]. Model not distinguishable from, and point-estimate worse than, the close. Timing caveat (GG-1090): the close is later than the model's decision time, which flatters the market. |
| nfl_qb_challenger_v1 | NONE (no stored 2025 predictions; not scored) |
| nba_pregame_v1 | NONE (no pre-shadow NBA market history) |
| nba_player_points_v1 | NONE (no player-points price history) |
| nhl_pregame_v1 | NONE (no pre-shadow NHL market history; the shadow arm's own market-referenced figures are the section 1 table) |
| mlb_game_pregame_v1 | NONE (no 2025 game-market price history) |
Files: `models/<model>_heldout_vs_market.json` (new; models/ is gitignored, added with -f). For the five NONE arms the skill weight stays 0.

## 3. BH across the 49 registered cells, q = 0.10
Only 6 cells carry scores (all NHL PRELIMINARY); 43 SEALED cells have no p-value and enter at p=1. One-sided p from a normal approximation to the bootstrap interval (se = CI width / 3.92), NOT the bootstrap tail: GAME_TOTAL_T1 p<1e-5, the others 0.54-0.92. **1 of 49 survives (NHL_GAME_TOTAL_T1).** Caveats: preliminary (reached_look 0, judged n 2500 not reached); this is not a verdict and moves no registry cell.

## 4. One measured result per core function (NHL, n games, 95% interval)
- brier / brier_mean / log_loss: GAME_TOTAL_T1 model 0.12130, market 0.14254, model log loss 0.38247 (n=1053 rows, 117 games).
- brier_diff + cluster_bootstrap: +0.021242 [0.014345, 0.027950] (117 games); NFL ML -0.00714 [-0.01976, +0.00549] (271).
- murphy: GAME_TOTAL_T1 reliability 0.004552, resolution 0.124557, uncertainty 0.243095.
- reliability_bins / ece / slope_intercept: GAME_TOTAL_T1 ECE 0.0535; slope 0.385, intercept 1.284.
- benjamini_hochberg: 1 of 49 at q=0.10 (above). bonferroni, power_paired, mde_paired, pooled_cluster_test, fee_k007, net_edge, fill_pnl: known-answer tests only; no measured result this block (no fills or ladders read; W86.2/86.3 own those).

ADR-0075 stage: scoring/calibration infrastructure, not a factor. Granularity-index parts: none built (PLUMBING toward PROOF).

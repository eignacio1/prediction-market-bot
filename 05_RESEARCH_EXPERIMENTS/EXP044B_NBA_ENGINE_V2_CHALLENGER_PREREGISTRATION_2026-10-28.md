# EXP-044b — NBA engine v2 challenger, frozen forward test (pre-registration)

**Status:** FROZEN at merge of the PR that adds this file, before the arm's first row. **Date:** 2026-10-28. **Block:** W94.1 Part C.
**Pillar:** DEPTH + PROOF. **Challenger to:** EXP-044 (v1, pinned commit `cfdc423`, params hash `9019981832b8b15d`, frozen at merge `61ed3e0`).
**Guardrails:** prices are logged only. No order, stake, `kelly_fraction`, gate, ledger row or live model is touched. No real capital.

## What is frozen
- **Engine:** `src/prediction_market_bot/nba_engine/engine_v2.py` + `live_v2.py` at the merge commit of this PR ("v2_core").
  v1's as-of team means (K = 10, 2026 calibration season) plus (a) a score correlation **estimated** from out-of-sample margin and total residuals, and (b) a per-family logistic (Platt) step fit on training seasons only.
- **Training seasons:** 2024, 2025, 2026 (all before the first 2026-27 game). No refit during the arm.
- **Fitted at freeze (box-independent, from the 2016-2026 event store):** hca 1.867, total bias 1.137, SD margin 14.696, SD total 18.991 (rho = 0.251), Platt (intercept, slope): ml (-0.219, 2.195), spread (0.003, 1.030), total (-0.030, 0.966), team_total (-0.019, 1.003).
- **Params hash:** `d50932902832762d` (`live_v2.params_hash`); written into every row.
- **Factors tested and NOT kept** (no confidence interval excluded zero against v2_core on held-out 2021-26): venue altitude -> total, travel miles / games-in-last-4 / altitude gain -> margin and total. Availability (93.1), lineups -> total (92.3) and officials were not built in this block (sources not in the event store); they are future challengers, not part of v2_core.
- **Pricing instant and quote:** identical to EXP-044 (tip - 60 min; Kalshi archive quote no older than 45 min; mid price). Rows go to `exp_output/NBA_ENGINE_LIVE_V2/rows.jsonl`, same schema as v1 plus `engine_version="v2"`.

## Scoring (same as EXP-044)
Paired Brier, engine vs market, per family (moneyline, spread, total, team total), on the same tickers v1 is scored on. d = Brier(engine) - Brier(market), negative favors the engine. Skill weight w from the regression of outcome on the engine/market logit blend. Game-clustered bootstrap (2,000 resamples) intervals. **Additional paired contrast:** v2 minus v1 Brier per family on the rows both logged.

## Judged n and pass rule
Same as EXP-044: 300 games for full-effect detection, **1,200 games for a PASS call**. PASS (vs market) requires the game-clustered upper bound of mean d < 0 and w >= 0.01 at n >= 1,200. A v2-over-v1 claim additionally requires the upper bound of (v2 - v1) < 0 at the same n. Nothing is read as a verdict below judged n.

## Looks
- Descriptive checkpoint: **2027-01-31** (no verdict).
- Verdict look: **2027-04-20**.

## Modal outcome (stated before any row)
Undecided/FAIL against the market for moneyline and spread (the most-attended lines). Total and team total are the plausible winners. On held-out 2021-26, v2 beat v1 by -0.00554 [-0.00704, -0.00398] on moneyline Brier, -0.00143 [-0.00202, -0.00084] on total and -0.00058 [-0.00093, -0.00022] on team total, and tied on spread (+0.00004 [-0.00033, +0.00040]); the modal forward expectation is v2 <= v1 on all four, with the moneyline gain coming entirely from the calibration step.

## Not allowed to change
Parameters, strike rule, quote window, scoring or judged n after the first row. A change is a new pre-registration.

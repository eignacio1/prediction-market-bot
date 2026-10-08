# ADR-0070 — Probit-Platt Distributional Forecaster for Game-Market Ladders: Deviation from ADR-0004

**Status:** PROPOSED
**Date:** 2026-10-02
**Decisions logged:** pending (widening: DECISION_LOG 2026-10-07 operator entry; this commit)
**Author:** Session `fly-nfl-pregame` (EXP-037 / T-608, Wave 47 block 47.2)
**Approval required:** DS (Earl Ignacio) sign-off before ACCEPTED
**Deviates from:** ADR-0004 (model class selection: LR + Platt scaling)
**Does not touch:** ADR-0040/ADR-0048 (`kelly_fraction`), ADR-0016 (fees), every pool and ledger

Scope as widened 2026-10-08 (Wave 59.3, operator decision 2026-10-07 17:26 PT): the EXP-037 NFL/MLB models, the EXP-036 NHL shadow model (bivariate Poisson + Platt, `models/nhl_pregame_v1.json`) and the EXP-038 NBA shadow model (`models/nba_pregame_v1.json`, sha256 c351680a…, the same probit-Platt distributional class as NFL). All are SHADOW only.

This ADR authorises no order, position, sizing change or `CellStatus` beyond SHADOW, and it does not edit ADR-0004.

## 1. Context
ADR-0004 names logistic regression with Platt scaling for a binary target. The NFL game markets are ladders: for one game, Kalshi lists many strikes on the moneyline, spread, game total and team total. One binary LR per strike would give incoherent probabilities (non-monotone in strike; team totals not summing to the game total).

## 2. Deviation
`models/nfl_pregame_v1.json` fits ridge-linear means for margin and total (λ=100, fixed a priori) and reads every strike off one bivariate Gaussian per game. Recalibration is a two-parameter affine map (a, b) on the standardized margin, fitted on the probit scale rather than the logit scale. That is the same Platt idea (two parameters, fitted on a held calibration season), with a different link function and a distribution instead of a single binary output.
Frozen: train 2015–2023, calibrate 2024, held-out 2025 reported only; sha256 verified at load; no production retraining (Hard Rule 4).

## 3. Evidence (climatology only; no market history is validated)
2025 held-out, 272 games: moneyline Brier 0.2185 vs climatology 0.2476. RMSE margin 13.09 vs 14.16; total 13.37 vs 13.80. Reliability bins are noisy (n≈54 each) and the middle bins sit on the wrong side of the diagonal. One season, no CI claimed.

## 4. Known weaknesses
- Gaussian tie mass is about 2.8% against a real rate of about 0.4%.
- Features are identical at T1, T2 and T3: no point-in-time injury, QB, weather or travel source.
- Team-total p_yes near 0.996 against a 0.98/0.99 book looks extreme and is unreviewed.

## 5. Decision requested
Accept the probit-Platt distributional class for SHADOW evaluation of the 12 EXP-037 cells only. Decision rules are fixed in `05_RESEARCH_EXPERIMENTS/EXP037_NFL_PREGAME_SHADOW_PREREGISTRATION_2026-10-02.md`. Any use beyond SHADOW needs a further ADR.

## 5a. Widening to NHL (EXP-036) and NBA (EXP-038) — added before acceptance
**Same deviation from ADR-0004, same limits.** Each model departs from "binary LR + Platt on one target" by producing a distribution per game (NBA: ridge-linear margin/total means, one bivariate Gaussian, probit-Platt (a, b) as in §2; NHL: bivariate Poisson goals with Platt recalibration) and reading every strike of the ladder off it. Frozen artifacts, sha256 verified at load, trained on prior seasons with the latest held out, no production retraining (Hard Rule 4).
**Shadow only.** This widening authorises evaluate-and-log of the EXP-036 and EXP-038 cells. It authorises no order, position, fill, sizing or `kelly_fraction` change, and no `CellStatus` beyond SHADOW. Decision rules stay in each experiment's pre-registration. Any use beyond SHADOW needs a further ADR.
**Known NHL limitation carried in, not waived:** every NHL band uses a projected goalie; the W59.3 probe found no pre-puck-drop starter flag (GG-401 stays OPEN, no NHL T3 score may be read). This ADR does not resolve GG-401.
**Closes GG-400** (the NHL model's missing ADR coverage). No second ADR is written.

## 6. Collision check
No ADR-0070 file existed on origin/main (`1e097e0`) or on any local or remote branch at drafting; ADR-0069 is the latest. 47.3 should re-check before landing.

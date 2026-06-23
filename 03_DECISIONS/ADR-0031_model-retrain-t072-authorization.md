# ADR-0031 — T-072 Model Retrain Authorization (Supersedes ADR-0004 Scope Extension)

**Status:** DRAFT — pending DS sign-off  
**Date:** 2026-06-23  
**Proposed by:** SESSION 73  
**Owner (role):** DS — Earl Ignacio  
**Supersedes:** ADR-0004 §4 (frozen model policy) — **for this retrain only**; the no-automated-retraining rule remains in full force for all subsequent model changes  
**Implements:** DECISION_LOG S69 (Option C — feature-set diagnosis sprint); T-072 Part A/B authorization  
**Blocks:** Any execution of retrain scripts (T-072 Part B) and deployment of a new model version to paper trading

---

## Context

ADR-0004 (Compass OS model governance) establishes a **frozen model policy**: the production model is fixed at the version deployed at gate G4 (v1-28483b21, trained 2026-05-29) and may not be retrained without a superseding ADR. Hard rule #4 in CLAUDE.md enforces this.

Three developments have made a supervised retrain necessary:

1. **S69 diagnosis (GG-037/GG-004):** The T-177 edge monitor confirmed that the production model is ANTI-PREDICTIVE against Kalshi prices at p=0.0505 (n=144 clean bets). Root cause: missing playoff-context λ multiplier. The Poisson survival model uses `opp_adj_lambda` calibrated against regular-season opponent defensive ratings; NBA Finals scoring is 9–30% below model-implied λ, and this compression worsens at higher scoring thresholds and deepens across a series.

2. **Feature engineering gap:** The three fixes identified in S69 (playoff_round_multiplier, playoff-opponent defensive stats, within-series momentum) require adding new feature columns. Any change to C2 features requires a retrain under ADR-0004's feature-version policy (FEATURE_VERSION 1.3.0 → 1.4.0).

3. **Staleness:** Model v1-28483b21 was trained on data through 2026-05-29. Without a retrain, it will be 5+ months stale at the 2026-27 NBA regular season tip-off (2026-10-20). The DECISION_LOG 2026-05-29 entry made T-072 retrain a required task by 2026-10-15.

This ADR authorizes the retrain. It does NOT permanently relax the frozen model policy — that policy exists to prevent unsupervised production drift, and remains the default. This is a one-time, operator-supervised, gate-governed retrain.

---

## Decision

**Authorized:** A single supervised retrain of the production NBA forecasting model, proceeding as follows:

### Part A — C2 Feature Changes (prerequisite to retrain)

Three new features added to `src/prediction_market_bot/c2_feature_store/features.py`:

| Feature | Name | Derivation |
|---------|------|------------|
| F-041 | `playoff_round_multiplier` | Empirical multiplier on λ: 1.0 for regular season; calibrated from NBA playoff historical scoring data during the retrain (no guessed values). Represents the systematic scoring compression in playoff contexts. |
| F-042 | `opp_playoff_def_rating_l5_mean` | Opponent team's rolling mean pts_allowed over the **N most recent playoff games** (default N=5). Replaces regular-season `opp_def_rating_l10_mean` (F-040) for games identified as playoff context. F-040 retained for regular-season games. |
| F-043 | `series_scoring_delta` | Player's mean scoring in the current playoff series vs their regular-season `pts_l10_mean` entering the series. Captures within-series game-plan adjustment. For regular-season games: 0.0. |

FEATURE_VERSION increments from `"1.3.0"` to `"1.4.0"` when these features are committed.

**Temporal integrity (TI-01):** All three features must be computed strictly from prior-game data. No current-game look-ahead. Series scoring delta uses only games 1 … (N-1) within the series to compute the feature for game N.

**Data requirement:** Playoff-opponent defensive stats and historical playoff scoring data must be sourced from the same C1 pipeline or a companion historical extract. No guessed multipliers — all values must be derived from empirical NBA historical data.

### Part B — Retrain Execution

| Parameter | Value |
|-----------|-------|
| Training data | Full 2025-26 NBA regular season + playoffs (all available player-game rows with TI-01-clean features) |
| Feature version | 1.4.0 |
| Model class | LR + Platt scaling (ADR-0004 model class unchanged) |
| Calibration method | Temperature scaling per ADR-0027 (T=2.05 as prior; refit on new data if adequate holdout available) |
| Holdout | Chronological split — no random shuffle (TI-02) |
| New model version tag | v2-XXXXXXXX (git hash at retrain commit) |

### Part C — Shadow Gate (required before any deployment)

The retrained model must pass **both** of the following thresholds before it replaces v1-28483b21 in any execution path:

1. **Brier improvement:** Brier score on holdout set < Brier score of v1-28483b21 on the same holdout (improvement ≥ 0.001 required — not within noise floor). Any retrained model with equal or worse Brier must not be deployed; T-072 diagnosis must continue.

2. **ECE threshold:** Expected Calibration Error (ECE, 10 equal-frequency bins) ≤ 0.05 on holdout set. This is relaxed from the v1 ECE of 0.0342 to accommodate cross-sport scope, but remains a binding gate.

These are ADR-0009 shadow model gate criteria applied to this retrain. Both must pass. If either fails, the retrained model is NOT authorized for deployment and T-072 remains open.

### Part D — Anti-Predictive Backtest (Phase 3 gate prerequisite)

After shadow gate passes (Part C), run `scripts/run_t177_edge_monitor.py` on available NBA data using the retrained model. The result must be **INCONCLUSIVE or MONOTONIC** (p > 0.05, not ANTI-PREDICTIVE) before Phase 3 MLB C1 build begins. This is the Phase 3 start gate defined in DARK_PERIOD_PLAN.md.

---

## What this ADR does NOT authorize

- **Automated retraining:** This ADR authorizes a single operator-supervised retrain. The automated retraining prohibition (ADR-0004 §4, hard rule #4) remains unchanged for all subsequent changes.
- **Model class change:** LR + Platt scaling is unchanged. If the shadow gate fails and a different model class (e.g., gradient boosting, neural network) is considered, a new superseding ADR is required.
- **Live capital deployment:** No live capital until G6 gate is formally cleared (ADR-0005, 30 resolved paper bets with positive P&L, DS sign-off). The retrained model first runs in paper trading.
- **Permanent relaxation of ADR-0004:** The frozen model policy returns to full force after this retrain is executed. Any future retrain requires its own authorization ADR.

---

## Risk register

| Risk | Mitigation |
|------|-----------|
| Guessed playoff multiplier introduced | Hard requirement: all F-041/F-042/F-043 values must be empirically derived; any column containing a guessed constant must be blocked before merge |
| Shadow gate gaming (select holdout to make new model win) | Holdout split is chronological and fixed to the last N weeks of the 2025-26 season before the retrain begins; same holdout used for both v1 and v2 comparison |
| Feature version mismatch in production | C3 reads FEATURE_VERSION from the feature DataFrame; a version check at inference time guards against running v2 model on v1 features |
| Anti-predictive pattern survives feature fix | If Part D backtest returns ANTI-PREDICTIVE: escalation path defaults to Option A (halt paper trading + ADR-0004 supersession review for model class change) per S69 DS decision |

---

## Acceptance checklist

- [ ] DS sign-off (Earl Ignacio)
- [ ] F-041/F-042/F-043 implemented in `features.py`; FEATURE_VERSION = "1.4.0"
- [ ] All three features pass temporal integrity audit (no look-ahead)
- [ ] Retrain executed on 2025-26 full data; model hash recorded
- [ ] Shadow gate: Brier improvement confirmed, ECE ≤ 0.05 confirmed
- [ ] T-177 backtest on retrained model: result is not ANTI-PREDICTIVE (p > 0.05)
- [ ] New model version deployed to paper trading (kill switch reset with documentation)
- [ ] DECISION_LOG entry written with retrain results (Brier, ECE, T-177 result, model hash)

---

## DS Sign-Off

**Operator:** _____________________________ (Earl Ignacio)  
**Date:** _____________________________  
**Status on sign:** ACCEPTED

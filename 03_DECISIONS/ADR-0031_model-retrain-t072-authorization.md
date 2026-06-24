# ADR-0031 — T-072 Model Retrain Authorization (Supersedes ADR-0004 Scope Extension)

**Status:** ACCEPTED — DS sign-off Earl Ignacio 2026-06-23 SESSION 73  
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

## Known Limitations at Acceptance (SESSION 73 / 2026-06-23)

These limitations were identified at the time of DS sign-off and must be understood by any reader before treating v2 as a complete fix.

### 1. F-042 contributed zero signal — the core playoff opponent defensive fix is NOT in v2

`opp_playoff_def_rating_l5_mean` (F-042) was NaN everywhere in the training data because the playoff TeamGameLog pull was deferred during Part B execution. The LR model imputed NaN → 0.0, effectively zeroing the feature's weight. F-042 was designed to replace regular-season opponent defensive ratings with opponent's trailing playoff defensive performance — the most directly targeted fix for the λ compression identified in S69 (Finding 2: Kalshi incorporates playoff defensive information the model does not).

**Consequence:** v2-065b9510's playoff opponent adjustment consists entirely of:
- F-041: a single empirical multiplier of 0.959603 (≈4% λ reduction for all playoff contexts) — derived from only 31 in-training playoff rows
- F-043: within-series scoring delta (83 non-zero rows)

The S69 diagnosis found 9–30% compression at thr=10–20. A 4% global multiplier addresses perhaps 15–45% of the identified compression magnitude.

### 2. Brier improvement source — the shadow gate passed for the wrong reason

The primary Brier gain in v2 (Δ=+0.001507) came from F-039 (`is_home_game`) and F-040 (`opp_def_rating_l10_mean`) — features present in the training matrix but absent from v1's 78-feature set. This is an independent improvement unrelated to the playoff compression fix. The three Option C features (F-041/F-042/F-043) likely contributed marginally or zero to the Brier improvement; F-042 contributed definitively zero.

**What this means:** The shadow gate passing does NOT validate that the playoff compression problem is fixed. It validates that the new feature matrix, with additional baseline features included, is better calibrated than v1. The improvement would have appeared even without F-041/F-042/F-043.

### 3. T-177 INCONCLUSIVE interpretation

v2's T-177 result (p=0.1639, edge>0 winrate 67.6% vs edge≤0 53.5%) shows a direction reversal from v1's ANTI-PREDICTIVE pattern (edge>0 winrate 35.6%). This is directionally positive and meets the Phase 3 gate condition (p > 0.05). However:
- n=114 is below ADR-0024's structural adequacy threshold (n≥500, ≥15 opponents)
- The reversal is consistent with the F-039/F-040 improvements, not specifically the playoff compression fix
- The model deployed in October may still fail T-177 when tested at adequate sample in the 2026-27 regular season

### 4. Required follow-up before NBA 26-27 paper trading restarts (T-186)

Pull playoff TeamGameLog for 8-10 NBA teams (≈5-10 min via nba_api), repopulate F-042 for all playoff training rows, retrain v2b, re-run T-177. If T-186 completes before October 2026, deploy v2b instead of v2-065b9510. T-186 is registered in TODO_NEXT Phase 3 section.

### 5. Deployment framing

**Shadow gate PASSED ≠ alpha confirmed.** Deploying v2 in October 2026 is an evidence-collection decision on an improved feature set. The commercial question — does the model beat Kalshi prices? — is answered by EXP-017 at ADR-0024 adequate sample (GG-004, GG-037). Both governance gaps remain OPEN.

---

## Acceptance checklist

- [x] DS sign-off (Earl Ignacio)
- [x] F-041/F-042/F-043 implemented in `features.py`; FEATURE_VERSION = "1.4.0"
- [x] All three features pass temporal integrity audit (no look-ahead)
- [x] Retrain executed on 2025-26 full data; model hash recorded (v2-065b9510)
- [x] Shadow gate: Brier improvement confirmed (Δ=+0.001507), ECE ≤ 0.05 confirmed (ECE=0.0426)
- [x] T-177 backtest on retrained model: INCONCLUSIVE (p=0.1639 all, p=0.3131 clean) — not ANTI-PREDICTIVE
- [ ] New model version deployed to paper trading (kill switch reset with documentation)
- [x] DECISION_LOG entry written with retrain results (SESSION 73)

---

## DS Sign-Off

**Operator:** Earl Ignacio  
**Date:** 2026-06-23  
**Session:** SESSION 73  
**Status on sign:** ACCEPTED

**Acceptance checklist at sign-off (Part A — SESSION 73):**
- [x] F-041/F-042/F-043 implemented in `features.py`; FEATURE_VERSION = "1.4.0" (T-072 Part A, SESSION 73)
- [x] Temporal integrity audit passed (1293 tests green, including 13 new playoff feature tests)
- [x] KeyError guard added for missing `opponent_team_abbr` column (Q6 finding, SESSION 73)

**Acceptance checklist update (Part B/C — SESSION 73, same session):**
- [x] Retrain executed; model v2-065b9510 saved to `models/v2_model.joblib`
  - Training rows: 15,274 (through 2026-02-01 holdout cutoff)
  - Holdout rows: 1,179 (2026-02-01 onwards, incl. 72 playoff rows)
  - F-041 multiplier: 0.959603 (empirical, 31 in-training playoff rows)
  - F-042: NaN everywhere — playoff TeamGameLog pull deferred (see known limitations in `scripts/train_model_v2.py`)
  - F-043: 83 non-zero series delta rows
- [x] Shadow gate PASSED: Brier v1=0.246622 → v2=0.245115 (Δ=+0.001507 ≥ 0.001), ECE=0.0426 ≤ 0.05
- [x] T-177 backtest INCONCLUSIVE: v2 p=0.1639 (n=114 all) / p=0.3131 (n=109 clean). Phase 3 gate OPEN.
  - v2 edge signal direction correct: edge>0 winrate=67.6%, edge≤0 winrate=53.5% (monotonic tendency)
  - Note: original ANTI-PREDICTIVE finding (n=144, p=0.0505) used full clean dataset CSV incl. G5 (June 13 games); these are not in the live portfolio JSON. Full replication with G5 games pending future data pull.
- [ ] New model version deployed to paper trading; kill switch reset with documentation (pending operator action — dark period, no active games; document baseline at 2026-27 season start)

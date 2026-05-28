# Sensitivity and Stress Tests — Prediction Market Trading Bot

**Purpose:** Document sensitivity analyses and stress tests for model robustness. Required before paper trading deployment.  
**Owner (role):** Methodology Validator (MV)  
**Status:** DRAFT — ST-001 through ST-004 defined; ST-005 blocked (DS-02)  
**Last reviewed:** 2026-05-28 (T-053 — Phase 5; tests defined with pass/fail criteria)  
**Next review:** After each test is run; before G5  
**Staleness triggers:** Feature set change; model retrain; new failure mode identified  
**Upstream links:** MODEL_CARD.md, HYPOTHESES.md, METHODOLOGY.md  
**Downstream links:** G5 Evidence Gate checklist  
**Decision references:** ADR-0001, ADR-0004  
**Confidence:** 7/10 — Test definitions are complete; results pending execution

---

## Overview

These tests examine model sensitivity to input assumptions and operational conditions. They supplement the main experimental evidence (EXP-001–003) by stress-testing specific modeling decisions.

**Run all executable tests (ST-001 through ST-004) before G5 gate sign-off.**

---

## ST-001 — Imputation Sensitivity

**Hypothesis:** Brier score is robust to alternative NaN imputation strategies.  
**Rationale:** LIM-003 notes that rolling window features produce NaN for early-game rows. Column median imputation is the current strategy. If results are sensitive to imputation choice, it is a model fragility.

**Method:**
1. Rerun EXP-001 pipeline with alternative imputation strategies:
   - Strategy A (baseline): Column median imputation (current)
   - Strategy B: Forward-fill (last valid value per player per season)
   - Strategy C: Zero-fill (all NaN → 0.0)
2. Compare Brier scores and ECE across strategies.

**Pass criterion:** Brier improvement (vs null) is within ±0.005 of baseline (+0.0084) across all strategies.  
**Fail criterion:** Any strategy shifts Brier improvement by > 0.005 — indicates fragility; requires investigation and possible ADR.  
**Status:** 🔲 NOT RUN  
**Blocked by:** Nothing — runnable against EXP-001 raw CSV (SNAP-002)

---

## ST-002 — Training Window Size Sensitivity

**Hypothesis:** Brier performance is stable across longer and shorter training windows.  
**Rationale:** EXP-001 used half-season training (~5,000 rows for 50 players). If results are highly sensitive to training window size, the model has a fragile data requirement.

**Method:**
1. Vary training window size (keeping validation period fixed):
   - 25% of training data (smallest stable window above MIN_FIT_SAMPLES)
   - 50% (baseline — current EXP-001)
   - 100% (full available history for EXP-001 window)
2. Record Brier score and ECE for each window size.

**Pass criterion:** Brier improvement remains > 0 for all window sizes ≥ 1,000 rows.  
**Fail criterion:** Brier degrades below null model for any window above minimum — indicates training data threshold dependency; must document.  
**Status:** 🔲 NOT RUN  
**Blocked by:** Nothing — runnable against existing SNAP-002

---

## ST-003 — Regularization (C Parameter) Sensitivity

**Hypothesis:** Brier performance is robust to the logistic regression regularization parameter.  
**Rationale:** C=1.0 is the default sklearn regularization. If the model is sensitive to C, the hyperparameter should be tuned and the optimal value documented.

**Method:**
1. Rerun EXP-001 pipeline with C ∈ {0.01, 0.1, 1.0 (baseline), 10.0, 100.0}
2. Record Brier score, ECE, and AUC-ROC for each C.

**Pass criterion:** C=1.0 Brier is within ±0.005 of the best-performing C value.  
**Fail criterion:** Another C value outperforms C=1.0 by > 0.005 Brier improvement — indicates C should be tuned and ADR update required.  
**Status:** 🔲 NOT RUN  
**Blocked by:** Nothing — runnable against SNAP-002

---

## ST-004 — Permutation Feature Importance

**Hypothesis:** No single feature dominates the model (fragility check).  
**Rationale:** If one feature accounts for > 50% of model performance, the model has a single point of failure. Permuting key features should degrade performance but not collapse it.

**Method:**
1. Fit model on EXP-001 training set (FEATURE_VERSION 1.2.0, 31 features).
2. For each feature F-001 through F-031:
   a. Randomly shuffle values for that feature in the validation set.
   b. Recompute Brier score.
   c. Record `Δ Brier = shuffled_brier - baseline_brier` (positive = feature hurts if shuffled = important).
3. Rank features by permutation importance.

**Pass criterion:** No single feature contributes > 50% of total permutation importance.  
**Fail criterion:** One feature contributes > 50% — fragility flag; document and consider feature engineering diversification.  
**Status:** 🔲 NOT RUN  
**Blocked by:** Nothing — runnable against SNAP-002

---

## ST-005 — Vig Survival (Edge vs Kalshi Spread)

**Hypothesis:** Brier improvement +0.0084 generates positive expected value after Kalshi vig.  
**Rationale:** This is HYP-003 / EXP-004. If the edge does not survive the vig, the model is not profitable in live deployment. This is the primary open risk (LIM-003).

**Method:** See EXP-004 in `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/`.  
**Pass criterion:** Expected value per bet > 0 after applying Kalshi spread (DS-02 required).  
**Status:** 🔴 BLOCKED — requires DS-02 (live Kalshi venue prices). Unblocked when ACC-0002 approved (G5).

---

## Execution Summary

| Test | Status | Blocked by | Priority |
|------|--------|-----------|---------|
| ST-001 Imputation | 🔲 NOT RUN | — | MEDIUM |
| ST-002 Training window | 🔲 NOT RUN | — | MEDIUM |
| ST-003 C parameter | 🔲 NOT RUN | — | MEDIUM |
| ST-004 Permutation importance | 🔲 NOT RUN | — | MEDIUM |
| ST-005 Vig survival | 🔴 BLOCKED | DS-02 / ACC-0002 | HIGH |

Run ST-001 through ST-004 against existing SNAP-002 data before G5 gate. Record results in this document.

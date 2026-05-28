# Sensitivity and Stress Tests — Prediction Market Trading Bot

**Purpose:** Document planned and completed sensitivity analyses and stress tests for the prediction model. Identifies which assumptions and parameters the model is most sensitive to.  
**Owner (role):** Methodology Validator (MV)  
**Last reviewed:** 2026-05-28 (Created as Phase 5+ stub — no stress tests run in Phase 3; Phase 4 completed only Brier/ECE backtesting)  
**Next review:** Phase 5 (operational readiness); when live data is available  
**Staleness triggers:** New stress test run; new failure mode identified; model version promoted  
**Upstream links:** PERFORMANCE_METRICS.md, ASSUMPTIONS_LIMITATIONS.md, 05_RESEARCH_EXPERIMENTS/HYPOTHESES.md  
**Downstream links:** VALIDATION_SIGNOFF.md, MONITORING_DRIFT_PLAN.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (PROPOSED)  
**Confidence:** 2/10 — Stub only; stress tests deferred to Phase 5 when live data is available

---

## Status

⚠️ **STUB — Phase 5+ artifact.** No stress tests have been run in Phase 3/4. This file documents the planned test battery. Populate when Phase 5 live data is available.

---

## Planned Stress Tests

### ST-001 — Imputation Sensitivity
**Goal:** Determine whether column-median NaN imputation significantly affects Brier/ECE vs alternative strategies (mean, zero, or nearest-neighbor).  
**Method:** Re-run EXP-001 with 3 imputation strategies on SNAP-2026-05-28-001; compare Brier + ECE.  
**Gate:** Phase 5  
**Status:** 🔲 Not started

### ST-002 — Training Window Size Sensitivity
**Goal:** Determine the minimum TRAIN rows for reliable calibration (ECE < 0.05).  
**Method:** Re-run EXP-001 with 10/20/30/40/50 players; plot ECE vs TRAIN row count.  
**Gate:** Phase 5  
**Status:** 🔲 Not started (Phase 4 provided two data points: 10-player fails, 50-player passes)

### ST-003 — Calibration Parameter Sensitivity (C parameter in LR)
**Goal:** Confirm C=1.0 (L2 regularization default) is robust; test C=0.1, 0.5, 2.0, 5.0.  
**Method:** Grid search on same train/val splits as EXP-001; report Brier + ECE for each C.  
**Gate:** Phase 5  
**Status:** 🔲 Not started

### ST-004 — Feature Importance / Permutation Importance
**Goal:** Identify the top features by permutation importance. Confirm rolling mean features dominate.  
**Method:** Permutation importance on EXP-001 VALIDATION set; plot top 15 features.  
**Gate:** Phase 5  
**Status:** 🔲 Not started

### ST-005 — Signal Stability Under Distribution Shift (HYP-003 prerequisite)
**Goal:** Confirm model edge direction is consistent with live venue prices (not just null=0.50 baseline).  
**Method:** Requires DS-02 (live venue prices); run EXP-004 with live prices as market_implied_prob.  
**Gate:** Phase 5 / G5  
**Status:** 🔲 BLOCKED — requires DS-02 (Phase 5+)

### ST-006 — Drawdown Simulation (Kelly Fraction Sensitivity)
**Goal:** Simulate paper trading drawdown under different Kelly fractions (full, half, quarter, eighth).  
**Method:** Apply position sizing to EXP-001/002/003 VALIDATION outcomes; compute max drawdown per fraction.  
**Gate:** Phase 6  
**Status:** 🔲 Not started

---

## Completed Tests (Phase 4)

| Test | Description | Result | Date |
|------|-------------|--------|------|
| Feature ablation (T-044) | v1.1.0 (38 feat) vs v1.0.0 (31 feat); same data | Δ Brier = +0.0002; HYP-005 FALSIFIED | 2026-05-28 |
| Cohort size sensitivity (implicit) | 10-player vs 50-player cohort | ECE 0.06–0.09 (10 players) vs 0.028–0.037 (50 players) | 2026-05-28 |

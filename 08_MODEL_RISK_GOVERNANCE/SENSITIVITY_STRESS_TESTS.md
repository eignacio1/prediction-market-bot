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

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — real gap found, not just doc staleness.** Phase 5/G5 closed weeks ago and the system is deep into Phase 6 live paper trading, but this document was never updated to reflect it, and worse — one of its own planned tests has actually been run **outside** this document and never logged back into it:
- **ST-005** ("Signal Stability Under Distribution Shift," blocked on DS-02 live venue prices) — DS-02 has been live in production for weeks; its functional equivalent (real-price commercial validation) has been run repeatedly as EXP-017, most recently against MLB at n=151 (DIRECTIONAL_POSITIVE, ADR-0024 Tier 1 cleared) per CLAUDE.md/GG-004. Still marked 🔲 BLOCKED here.
- **ST-006** ("Drawdown Simulation (Kelly Fraction Sensitivity)," Gate: Phase 6, marked 🔲 Not started) — this exact test has been run: `scripts/mc_forward_projection.py` (GG-071/ADR-0040, 2026-07-03/07-04, confirmed present via repo search and `tests/test_mc_forward_projection.py`) is a forward-time compounding Monte Carlo that simulated T1 MLB drawdown/kill-switch-breach probability under the then-current Kelly fraction and directly produced a Kelly de-rating decision (ADR-0040: `kelly_fraction` 0.10 → 0.061). This is materially the same stress test ST-006 describes, run for a real risk decision, and this document — the canonical home for sensitivity/stress-test results — was never updated to record it. Recommend registering "ST-006 done but not logged" as its own small governance-gap candidate: a future reviewer checking this file alone would wrongly conclude no Kelly-sensitivity stress test has ever been run.
- ST-001–ST-004 (imputation, training-window, C-parameter grid, permutation importance) were not independently re-verified this pass — still plausibly not started, but confirm before relying on "Not started" here.
- This document remains NBA/Phase-3-4-scoped (EXP-001/002/003, SNAP-2026-05-28-001) throughout and has never been re-derived for MLB, which is now the ACTIVE pool — none of ST-001 through ST-006 have MLB-specific equivalents registered anywhere that this pass could find, beyond the T1-MLB-specific GG-071/ADR-0040 work noted above.

---

## Status

⚠️ **STUB — Phase 5+ artifact.** No stress tests have been run in Phase 3/4. This file documents the planned test battery. Populate when Phase 5 live data is available.

**See correction above — this "Status" line is itself stale: Phase 5/6 stress-test work has occurred (GG-071/ADR-0040's drawdown/Kelly-fraction simulation at minimum) but was never populated back into this file.**

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

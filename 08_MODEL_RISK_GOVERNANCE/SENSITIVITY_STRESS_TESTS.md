# Sensitivity and Stress Tests — Prediction Market Trading Bot

**Purpose:** Document planned and completed sensitivity analyses and stress tests for the prediction model. Identifies which assumptions and parameters the model is most sensitive to.  
**Owner (role):** Methodology Validator (MV)  
**Last reviewed:** 2026-07-12 (T-349/GG-096 remediation — ST-005/ST-006 rows updated to point at their completed evidence; see below)  
**Next review:** When ST-001–ST-004 are actioned, or when MLB-specific stress-test equivalents are registered  
**Staleness triggers:** New stress test run; new failure mode identified; model version promoted  
**Upstream links:** PERFORMANCE_METRICS.md, ASSUMPTIONS_LIMITATIONS.md, 05_RESEARCH_EXPERIMENTS/HYPOTHESES.md  
**Downstream links:** VALIDATION_SIGNOFF.md, MONITORING_DRIFT_PLAN.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (PROPOSED), ADR-0024, ADR-0040  
**Confidence:** 5/10 — ST-005/ST-006 now logged against real completed evidence (below); ST-001–ST-004 still plausibly not started (unverified this pass); no MLB-specific equivalents beyond ST-005/ST-006 registered.

**2026-07-06 (GG-074 remediation, GG-096 registered) — 2026-07-12 (GG-096 RESOLVED, T-349):** this document was stale through Phase 6 live paper trading, and two of its own planned tests (ST-005, ST-006) had actually been run **outside** this document without being logged back into it. GG-096 tracked closing that gap; the ST-005/ST-006 rows below and the Completed Tests table now carry the real evidence and dates. ST-001–ST-004 (imputation, training-window, C-parameter grid, permutation importance) were not independently re-verified this pass — still plausibly not started, confirm before relying on "Not started" below. This document remains NBA/Phase-3-4-scoped (EXP-001/002/003, SNAP-2026-05-28-001) for ST-001–ST-004; ST-005/ST-006 now carry MLB-specific evidence (EXP-017, GG-071/ADR-0040) but no MLB-specific *re-derivation* of ST-001–ST-004 exists yet.

---

## Status

**PARTIALLY POPULATED.** ST-005 and ST-006 (Phase 5+/Phase 6 gated tests) have real completed evidence, logged 2026-07-12 (GG-096). ST-001–ST-004 (Phase 5, NBA-scoped) remain unconfirmed/plausibly not started.

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
**Status:** ✅ DONE (via functional equivalent) — 2026-07-06. DS-02 has been live in production for weeks; the equivalent real-price commercial-validation test was run repeatedly as EXP-017 (`scripts/run_exp017_mlb.py`), most recently against MLB at n=151 (EV=+$0.1009/bet, DIRECTIONAL_POSITIVE, ADR-0024 Tier 1 cleared). See CLAUDE.md § "The commercial validation gap", GG-004. Direction-split/bootstrap-insignificance caveats (GG-098) apply — treat as a milestone, not a proven signal.

### ST-006 — Drawdown Simulation (Kelly Fraction Sensitivity)
**Goal:** Simulate paper trading drawdown under different Kelly fractions (full, half, quarter, eighth).  
**Method:** Apply position sizing to EXP-001/002/003 VALIDATION outcomes; compute max drawdown per fraction.  
**Gate:** Phase 6  
**Status:** ✅ DONE — 2026-07-03/04 (GG-071/ADR-0040). `scripts/mc_forward_projection.py` (`tests/test_mc_forward_projection.py`) is a forward-time compounding Monte Carlo that simulated T1 MLB drawdown/kill-switch-breach probability under the then-current Kelly fraction and directly produced a Kelly de-rating decision (ADR-0040: `kelly_fraction` 0.10 → 0.061, bringing 1yr breach probability to ~5.6%). T-342 (2026-07-11) extended the same tool with a `stake_mode={"proportional","flat"}` parameter to also cover T4M-PROJ's flat-sizing regime. Materially the same test this row describes, run for a real risk decision. See GG-096 (logged this gap 2026-07-06), GG-078 (T4M-PROJ flat-MC framing caveat).

---

## Completed Tests (Phase 4)

| Test | Description | Result | Date |
|------|-------------|--------|------|
| Feature ablation (T-044) | v1.1.0 (38 feat) vs v1.0.0 (31 feat); same data | Δ Brier = +0.0002; HYP-005 FALSIFIED | 2026-05-28 |
| Cohort size sensitivity (implicit) | 10-player vs 50-player cohort | ECE 0.06–0.09 (10 players) vs 0.028–0.037 (50 players) | 2026-05-28 |
| ST-005 (via EXP-017, MLB) | Model edge vs real live venue prices (Kalshi), not 0.50 null | n=151, EV=+$0.1009/bet, DIRECTIONAL_POSITIVE, ADR-0024 Tier 1 reached (caveats: GG-098) | 2026-07-06 |
| ST-006 (`mc_forward_projection.py`) | T1 MLB drawdown/kill-switch-breach MC across Kelly fractions | Original `kelly_fraction=0.10` → ~46% 1yr breach probability; de-rated to 0.061 → ~5.6% (ADR-0040) | 2026-07-03/04 |

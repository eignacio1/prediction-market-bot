# Results Index — Prediction Market Trading Bot

**Purpose:** Chronological index of all experiment results. Provides at-a-glance progress toward G4 evidence requirements.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-28 (EXP-005 COMPLETE — T-058 model data refresh; 5 seasons; TEST Brier +0.0024 on 2025-26; model version v1-9939a6a5)  
**Next review:** After each experiment completes  
**Staleness triggers:** Experiment completed; G4 evidence review  
**Upstream links:** EXPERIMENT_LOG/, HYPOTHESES.md  
**Downstream links:** 07_TEST_VALIDATION_EVIDENCE/VALIDATION_PLAN.md  
**Decision references:** ADR-0002  
**Confidence:** 9/10 — All 3 Phase 3 experiments complete; results reflect actual pipeline output

---

## G4 Evidence Requirements

Per ACCEPTANCE_CRITERIA.md (FR-03, FR-06):

- [x] ≥3 independent experiments with Brier score vs null model — **3/3 complete** (EXP-001/002/003, 50-player cohort)
- [x] All experiments use chronological splits with verified temporal integrity — TI-01/TI-02 enforced by C2
- [x] Calibration curve produced for at least one model — ECE computed for all 3 experiments
- [x] Model Brier score < null model Brier score on at least 2 of 3 experiments — **3/3** beat null ✅
- [x] Hold-out test set never accessed during model development — TEST rows held for G4 gate in all 3 experiments

**Current status: 3/3 experiments complete — ✅ G4 EVIDENCE REQUIREMENT MET (3/3 beat null; ECE < 0.05 in all 3)**

---

## Experiment Results Summary

| EXP ID | Cohort | Hypothesis | Status | Val Window | Train rows | Brier (Model) | Brier (Null) | Improvement | ECE | AUC-ROC | Date |
|--------|--------|-----------|--------|------------|-----------|---------------|-------------|-------------|-----|---------|------|
| EXP-001 (10-player) | SNAP-2026-05-27-001 | HYP-001, HYP-002 | ✅ ARCHIVED | 2023-02-01 – 2023-04-30 | 986 | 0.2454 | 0.2500 | +0.0046 | 0.0596 | 0.5906 | 2026-05-28 |
| EXP-001 (50-player) | SNAP-2026-05-28-001 | HYP-001, HYP-002 | ✅ CANONICAL | 2023-02-01 – 2023-04-30 | 5,042 | 0.2444 | 0.2500 | **+0.0056 ✓** | **0.0345 ✓** | 0.5785 | 2026-05-28 |
| EXP-001 ablation (v1.0.0) | SNAP-2026-05-28-001 | HYP-005 | ✅ COMPLETE | 2023-02-01 – 2023-04-30 | 5,042 | 0.2446 | 0.2500 | +0.0054 | 0.0314 | 0.5777 | 2026-05-28 |
| EXP-002 (50-player) | SNAP-2026-05-28-001 | HYP-001 (window 2) | ✅ CANONICAL | 2022-02-01 – 2022-04-10 | 1,821 | 0.2451 | 0.2500 | **+0.0049 ✓** | **0.0289 ✓** | 0.5866 | 2026-05-28 |
| EXP-003 (50-player) | SNAP-2026-05-28-001 | HYP-001 (window 3) + HYP-004 | ✅ CANONICAL | 2021-12-16 – 2022-01-31 | 1,020 | 0.2474 | 0.2500 | **+0.0026 ✓** | **0.0369 ✓** | 0.5673 | 2026-05-28 |
| EXP-004 (Parts A+B) | SNAP-2026-05-28-001 | HYP-003 (edge vs vig) | ✅ COMPLETE | TEST set 2023-24 | 5,042 | 0.2416 | 0.2500 | **+0.0084** | 0.0247 | 0.6062 | 2026-05-28 |
| EXP-005 (data refresh) | SNAP-2026-05-28-002 | T-058 (5-season refresh) | ✅ COMPLETE | 2025-26 reg season | 11,931 | 0.2476 | 0.2500 | **+0.0024 ✓** | **0.0456 ✓** | 0.5765 | 2026-05-28 |

---

## Key Findings (Phase 4 — 2026-05-28, T-043/044)

1. **G4 evidence requirement MET.** 50-player cohort (SNAP-2026-05-28-001): all 3 experiments beat null Brier (EXP-001 +0.0056, EXP-002 +0.0049, EXP-003 +0.0026). ECE < 0.05 in all 3 (0.0345, 0.0289, 0.0369). AUC-ROC 0.567–0.587 — consistent signal across all windows.

2. **Training data volume was the blocker, not absent signal.** 10-player cohort (197–986 TRAIN rows) failed G4; 50-player cohort (1,020–5,042 TRAIN rows) passes. The signal was always there — the logistic regression needed sufficient rows for Platt calibration to converge.

3. **HYP-005 FALSIFIED: ERI + schedule features add no meaningful incremental signal.** Ablation test (T-044): v1.1.0 (38 features) Brier +0.0056 vs v1.0.0 (31 features) +0.0054 — Δ=+0.0002, well below 0.005 threshold. ECE is actually slightly better without them (0.0314 vs 0.0345). Recommend pruning to FEATURE_VERSION 1.2.0 with v1.0.0 features only.

4. **Phase gate working correctly.** C4 correctly rejected all positions in all experiments (BOT_C4_ACTIVE not set — expected in ENV-01/ENV-02).

5. **C6 bug fix** (`_redact_payload` numpy int key crash) applied and verified — no data integrity impact.

6. **HYP-003 CONFIRMED (Parts A+B, EXP-004).** EV +$0.0855/bet on 2,481 bets (TEST set). Win rate 59%. Vig $0.01 is well below edge margin. Part B live: Fox Edge +0.405 YES, SGA Edge −0.116 NO (session EXP-004-FE3E2169). DS-02-B-001 RESOLVED.

7. **EXP-005 (T-058 refresh): model generalizes to 2025-26.** 5-season corpus (15,590 rows); 11,931 TRAIN; TEST = full 2025-26 regular season (2,692 rows). TEST Brier +0.0024 vs null ✓; ECE 0.0456 (< 0.05 threshold ✓); AUC 0.5765. Metrics lower than G4 (expected — newer season harder); model viable for Phase 6 paper trading. Model version: v1-9939a6a5 (SNAP-2026-05-28-002).

---

## Recommended Next Steps

| Priority | Action | Rationale |
|----------|--------|-----------|
| 1 | Prune to FEATURE_VERSION 1.2.0 (drop 7 v1.1.0 ERI/schedule features) | HYP-005 falsified — they add noise, not signal; simplify model |
| 2 | PRF taxonomy encoding (OQ-017) | Player archetype features may provide orthogonal signal; needs operationalization |
| 3 | ADR-0004 (model class confirmation) | G4 evidence is now available; ADR-0004 can be drafted to formally confirm LR+Platt |
| 4 | Prepare for G4 gate | All G4 evidence criteria met; assemble evidence package |

---

## Falsified Hypotheses

| ID | Hypothesis | Outcome | Date | Evidence |
|----|-----------|---------|------|---------|
| HYP-005 | ERI + schedule features provide incremental signal | FALSIFIED | 2026-05-28 | T-044 ablation: Δ Brier = +0.0002 (threshold: 0.005); v1.0.0 ECE better (0.0314 vs 0.0345) |

---

## Validated Hypotheses

| ID | Hypothesis | Outcome | Date | Evidence |
|----|-----------|---------|------|---------|
| HYP-001 | Player_Attribute_Matrix features beat null model | CONFIRMED | 2026-05-28 | 3/3 experiments (EXP-001 +0.0056, EXP-002 +0.0049, EXP-003 +0.0026), 50-player cohort |
| HYP-002 | Model probabilities are calibrated (ECE < 0.05) | CONFIRMED | 2026-05-28 | ECE: 0.0345, 0.0289, 0.0369 across 3 experiments |
| HYP-004 | Signal is stable across time windows | CONFIRMED | 2026-05-28 | AUC-ROC 0.567–0.587; no monotonic degradation across chronological windows |

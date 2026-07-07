# Assumptions and Limitations — Prediction Market Trading Bot

**Purpose:** Canonical record of model-specific assumptions and known limitations. Distinct from 03_DECISIONS/ASSUMPTIONS_REGISTER.md (which covers system-level assumptions). This artifact covers the model's validity boundaries, distributional assumptions, and operational limitations.  
**Owner (role):** Methodology Validator (MV) + Model Owner (MO)  
**Last reviewed:** 2026-05-28 (Created at G4 gate preparation — populated from MODEL_CARD.md and experiment results)  
**Next review:** After each model version promotion; when a new limitation is discovered; at each gate  
**Staleness triggers:** New model version; new experiment results revealing new limitation; limitation resolved  
**Upstream links:** MODEL_CARD.md, PERFORMANCE_METRICS.md, 05_RESEARCH_EXPERIMENTS/HYPOTHESES.md  
**Downstream links:** VALIDATION_SIGNOFF.md, MONITORING_DRIFT_PLAN.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (PROPOSED)  
**Confidence:** 8/10 — Limitations well-documented from Phase 3/4 experiments; FEATURE_VERSION 1.2.0

**⚠️ Corrected 2026-07-06 (GG-074 remediation).** This document is scoped entirely to the pre-MLB, NBA-points-only, Phase 3/4 research state (same vintage as `STRATEGY_OVERVIEW.md`/`BAND_ASSIGNMENT_FRAMEWORK.md`, corrected in the 2026-07-02 pass) and has several claims stale by two to three phases:
- **ADR-0004 (PROPOSED)** — accepted 2026-05-28. Not proposed.
- **MA-002 / LIM-002 (`market_implied_prob` defaults to 0.50, "no live venue prices available")** — this is exactly the EV-benchmark issue tracked as KI-017/GG-004 in `CLAUDE.md`. It is resolved for the current system: live Kalshi prices have been used in production for weeks, and EXP-017 (the real commercial-validation experiment superseding the HYP-003/EXP-004 placeholder referenced below) has run against actual market prices for MLB — n=151, DIRECTIONAL_POSITIVE, ADR-0024 Tier 1 cleared (Tier 2 still open, GG-004 remains OPEN for that reason only). Do not read MA-002's "Status: Active — unvalidated" as still describing the system's current evidence base.
- **Scope Boundaries ("Market type: NBA player prop markets only")** — MLB is now the ACTIVE paper-trading pool with its own T1–T4M-PROJ bands and its own EXP-017 MLB run; NBA is DARK/FROZEN. This entire document was never re-derived for MLB — treat it as an NBA-only historical artifact, not a description of the model-risk posture for the currently active book.

---

## Model Assumptions

| ID | Assumption | Basis | Evidence grade | Risk if wrong | Test to validate | Status |
|----|-----------|-------|---------------|--------------|-----------------|--------|
| MA-001 | NBA player scoring patterns are stationary enough for a rolling L10 mean baseline to be predictive within a season | 3 chronological backtest windows show consistent AUC 0.567–0.587 | 7/10 — 3 windows, all within 2 seasons | Model loses predictive validity; Brier drops toward null | Monitor rolling Brier in Phase 5+ (FM-03) | Active |
| MA-002 | Market-implied probability ≈ 0.50 is a valid null model baseline for Phase 3 research | No live venue prices available in Phase 3 (DS-02 deferred) | 5/10 — Assumption; not validated against real prices | Edge calculations are wrong; model may appear better or worse than actual | HYP-003 (EXP-004) at Phase 5 with real venue prices | Active — unvalidated |
| MA-003 | Platt scaling (CalibratedClassifierCV, sigmoid, cv=3) produces well-calibrated probabilities with ≥1,000 TRAIN rows | ECE 0.028–0.037 across 3 experiments at 1,020–5,042 TRAIN rows | 8/10 — 3 experiments confirm | Miscalibrated probabilities invalidate Kelly sizing | Monitor ECE in live deployment | Validated at Phase 4 |
| MA-004 | Column median imputation for NaN rolling features is a valid substitute for missing data | Rolling windows produce NaN for first MIN_PERIODS=3 games per player; median imputation applied | 6/10 — Industry standard; not sensitivity-tested | Model performance may be affected by imputation choice | Sensitivity test with mean/zero imputation (Phase 5+) | Active — untested |
| MA-005 | 50 players is a sufficient cohort for model training in Phase 3 (ECE < 0.05 criterion) | 10-player cohort failed ECE > 0.05; 50-player cohort passes ECE 0.028–0.037 | 8/10 — Direct experiment comparison | Cohort too small for Phase 5+ live deployment with more markets | Monitor per-player signal at Phase 5+ | Validated at Phase 4 |

---

## Known Limitations

| ID | Limitation | Impact | Severity | Mitigation | Resolved by |
|----|-----------|--------|----------|-----------|-------------|
| LIM-001 | Training data scope is NBA player points props only (DS-01). Performance on other stat categories (rebounds, assists) is unknown and likely degraded | Cannot generalize to non-points props without retraining | HIGH | Scope constraint documented in MODEL_CARD.md; OQ-003 resolved to NBA basketball | Retraining with expanded stat categories (Phase 6+) |
| LIM-002 | No live market prices in Phase 3. `market_implied_prob` defaults to 0.50. Edge calculations are relative to a 50/50 prior, not real venue prices | Actual edge vs vig is unknown until HYP-003 tested | HIGH | HYP-003 registered; EXP-004 blocked until Phase 5 | Phase 5 (DS-02 integration) |
| LIM-003 | Signal magnitude is modest: average Brier improvement +0.0044. May not survive venue vig | Strategy may not be profitable even if model is accurate | HIGH | Kill-switch and risk limits protect capital; HYP-003 must be tested before live trading | HYP-003 at Phase 5 |
| LIM-004 | ERI + schedule features (F-032–F-038) pruned from FEATURE_VERSION 1.2.0 (HYP-005 falsified). Player psychological context not captured by current feature set | May miss regime-change signals not captured by rolling box-score | MEDIUM | Future research: stronger ERI formulation; PRF taxonomy encoding (OQ-017) | Future experiment (Phase 5+) |
| LIM-005 | PRF taxonomy archetypes (Player_Attribute_Matrix_v4) are documented but not encoded as numeric features (OQ-017) | Potentially orthogonal signal not being used | MEDIUM | OQ-017 registered; Phase 5+ research item | OQ-017 experiment |
| LIM-006 | NaN imputation via column median is applied at inference with a 0.0 fallback for unknown players | First 3 games of any new player will have imputed features | LOW | Documented in MODEL_CARD.md; acceptable for Phase 3 | Sensitivity test at Phase 5+ |
| LIM-007 | Model is version-pinned (frozen model policy). Any feature set change requires FEATURE_VERSION bump, model retrain, and ADR update | Slows response to new insights | LOW — by design | This is intentional governance; retraining requires ADR | By design per CHANGE_CONTROL.md |

---

## Scope Boundaries

| Boundary | Detail |
|---------|--------|
| Market type | NBA player prop markets only (points over/under vs L10 rolling mean) |
| Venue | Kalshi primary (ADR-0003); Phase 3 uses historical data only |
| Feature version | FEATURE_VERSION 1.2.0 — F-001–F-031 only |
| Capital | NO LIVE CAPITAL until G6 |
| Stat categories | Points only; rebounds/assists require separate training |

---

## What Would Change These Conclusions

| Assumption/Limitation | What would change it |
|----------------------|---------------------|
| MA-002 (null model = 0.50) | Live venue prices from DS-02; HYP-003 test |
| LIM-003 (signal survives vig) | EXP-004 testing edge vs Kalshi vig; positive EV confirmed |
| LIM-004 (ERI features) | A new ERI formulation showing Δ Brier > 0.005 in 2+ independent experiments |
| LIM-005 (PRF encoding) | OQ-017 experiment showing PRF archetypes add predictive signal |

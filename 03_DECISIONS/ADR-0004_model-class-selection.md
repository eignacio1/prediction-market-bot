# ADR-0004 — Model Class: LogisticRegression + Platt Scaling (Phase 3 Baseline)

**Purpose:** Formally confirm the model class selected for the Phase 3 research baseline, supported by G4 experimental evidence.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-05-28 (G4 Evidence Gate — formally accepted; APR-0012 recorded)  
**Next review:** G5 Operational Gate (paper trading results); revisit triggers documented below  
**Staleness triggers:** New model class outperforms LR+Platt by ≥ Δ Brier 0.005 across ≥3 independent experiments; signal decay detected in live trading; feature set changes requiring refit  
**Upstream links:** HYPOTHESES.md, EXPERIMENT_LOG/, MODEL_CARD.md, METHODOLOGY.md  
**Downstream links:** ARTIFACT_REGISTRY.md, MODEL_CARD.md, MONITORING_DRIFT_PLAN.md  
**Decision references:** ADR-0001 (Compass OS), ADR-0002 (forecast-only strategy)  
**Confidence:** 10/10 — G4 evidence complete; TEST set +0.0084 Brier / ECE 0.0247; formally accepted APR-0012

---

## Status

`ACCEPTED` — Formally accepted at G4 Evidence Gate 2026-05-28 (APR-0012)

---

## Context (Why Now)

ADR-0002 (forecast-only strategy) deferred the specific model class choice to a later ADR, to be supported by evidence. Phase 3 (Research Build) implemented a `LogisticRegression + PlattScaling` pipeline as the initial baseline. Three independent chronological backtest experiments (EXP-001, EXP-002, EXP-003) have now been completed with a 50-player cohort, producing sufficient evidence to formally confirm or reject this choice.

The G4 Evidence Gate requires:
- ≥2/3 independent experiments beat the null Brier score → **3/3 met ✅**
- ECE < 0.05 in at least one experiment → **3/3 under threshold ✅**
- Hold-out TEST set preserved for formal gate → **preserved ✅**

This ADR records the evidence base and formally proposes the model class for acceptance.

---

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A — LogisticRegression + PlattScaling** | `StandardScaler → LogisticRegression(L2, C=1.0, lbfgs, max_iter=1000, random_state=42, class_weight="balanced") → CalibratedClassifierCV(method="sigmoid", cv=3)` | Calibrated probabilities; fast to fit; transparent coefficients; scales well with FEATURE_VERSION changes; good performance at 1,000–5,000 rows | Signal ceiling may be lower than tree-based methods; linear decision boundary |
| B — Gradient Boosted Trees (XGBoost/LightGBM) | Ensemble method; typically outperforms LR on tabular data | Higher potential predictive ceiling | Calibration requires additional wrapper; needs more data for reliable estimates; harder to interpret for governance; higher risk of overfit at 1,000–5,000 rows |
| C — Random Forest + Platt | Ensemble; can capture non-linear patterns | Reasonable calibration with Platt; moderate interpretability | Variance high at small N; slower to fit than LR; not clearly better than LR in the 1,000–5,000 row regime |
| D — Neural Network (MLP) | Deep features; can model complex interactions | Highest theoretical ceiling | Overkill for tabular prediction with ≤ 5,000 rows; hard to calibrate reliably; poor governance story; hyperparameter sensitivity |

---

## Decision Drivers (Criteria)

1. **Calibration quality** — Output must be calibrated probabilities (not just rankings). Kelly position sizing is directly sensitive to calibration error. ECE < 0.05 is the minimum acceptable threshold.
2. **Data efficiency** — Training sets range from 1,020–5,042 rows across Phase 3 experiments. Simpler models are more reliable in this regime; complex models risk overfit.
3. **Interpretability and auditability** — Model behavior must be explainable; feature coefficients should be auditable. Required by governance framework (MODEL_CARD.md, METHODOLOGY.md).
4. **Evidence support** — Model must demonstrate Brier improvement over null in ≥2/3 independent experiments with held-out test sets.
5. **Consistency with FEATURE_VERSION policy** — Model must be compatible with the frozen feature set policy; model version is pinned at each fit.

---

## Decision

**Chosen option:** A — `LogisticRegression + PlattScaling`

**Rationale:**

1. **G4 evidence supports the choice.** Three independent VALIDATION windows (50-player, SNAP-2026-05-28-001): EXP-001 +0.0056 / ECE 0.0345; EXP-002 +0.0049 / ECE 0.0289; EXP-003 +0.0026 / ECE 0.0369. All 3 beat null; all 3 ECE < 0.05. **TEST set (2023-24 season, 3,254 rows): Brier +0.0084 / ECE 0.0247 / AUC 0.6062 — stronger than validation average, confirming no overfit to validation windows.** AUC-ROC 0.567–0.587 (val) / 0.606 (test) consistent with HYP-004 confirmed.

2. **Platt scaling produces reliable calibration at the observed training-set sizes.** With 1,020–5,042 TRAIN rows, `CalibratedClassifierCV(method="sigmoid", cv=3)` achieves ECE 0.028–0.037. The 10-player cohort (197–986 rows) failed calibration (ECE 0.06–0.09), confirming Platt scaling is data-sensitive. The 50-player cohort is sufficient.

3. **LR is appropriate for the current data regime.** At 1,000–5,000 rows and 31 features (FEATURE_VERSION 1.2.0), tree-based models are not clearly superior and introduce calibration and governance overhead. The gap between LR and XGBoost tends to close as N increases; if player cohort is expanded further, this decision can be revisited.

4. **Model class was the right choice to validate at Phase 3.** More complex models (Options B–D) should only be adopted if evidence shows LR+Platt is the bottleneck, not data quality or signal magnitude. No such evidence currently exists.

**Pipeline spec (canonical):**

```
StandardScaler()
    → CalibratedClassifierCV(
          LogisticRegression(
              penalty="l2",
              C=1.0,
              solver="lbfgs",
              max_iter=1000,
              random_state=42,
              class_weight="balanced"
          ),
          method="sigmoid",   # Platt scaling
          cv=3
      )
```

**Model version hash:** `"v1-" + sha1(MODEL_CLASS | sorted_feature_names)[:8]`
- FEATURE_VERSION 1.2.0 (31 features): `v1-9939a6a5` (confirmed at G4 gate)
- Hash changes with any feature set change; triggers model retrain requirement.

---

## Consequences

**Positive:**
- G4 evidence gate criteria are satisfied; paper trading promotion (ADR-0005) is unblocked after TEST set evaluation.
- Calibrated probabilities enable fractional Kelly sizing without additional calibration correction.
- Interpretable coefficients support governance audits.
- Pipeline simplicity enables reliable reproducibility (SNAP + FEATURE_VERSION + random_state fully determines outputs).

**Negative / Trade-offs:**
- Linear boundary may limit uplift if underlying NBA scoring patterns are highly non-linear. Signal magnitude (+0.003–+0.006 Brier improvement) is modest; may not survive vig (HYP-003, Phase 5+).
- If player cohort grows to 200+ players (~50,000+ rows), LR may be suboptimal vs gradient boosting. Addressed by revisit trigger below.

**Neutral:**
- MODEL_CARD.md already documents this pipeline. No code changes required.
- FEATURE_VERSION 1.2.0 (31 features) is now the canonical input to this model.

---

## Follow-Ups

| Task | Owner | Due | Tracking |
|------|-------|-----|---------|
| Formal acceptance at G4 gate (APR-0012) | AO / DS | G4 gate | APPROVALS_REGISTER.md |
| TEST set evaluation (held-out) | RL | G4 gate | MODEL_CARD.md |
| Assemble G4 evidence package | EL | G4 gate | VALIDATION_PLAN.md |
| ADR-0005 (live capital authorization) | AO | G6 gate | Pending G5 paper results |

---

## Revisit Triggers

- A challenger model (XGBoost, LightGBM) achieves Brier improvement > LR+Platt by ≥ Δ 0.005 across ≥3 independent experiments on the same data
- Signal magnitude (+0.003–+0.006) does not survive venue vig (HYP-003, EXP-004) — implies strategy reassessment, which may include model class change
- Player cohort expands to ≥ 200 players (≥ 50,000 TRAIN rows), at which point tree-based methods become competitive

---

## Links

- Spec: 01_SPEC/ACCEPTANCE_CRITERIA.md (G4 criteria), 01_SPEC/REQUIREMENTS.md (FR-03, FR-06)
- Architecture: 02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md (FEATURE_VERSION 1.2.0, F-001–F-031)
- Evidence: 05_RESEARCH_EXPERIMENTS/HYPOTHESES.md (HYP-001 ✅ HYP-002 ✅ HYP-004 ✅ HYP-005 ✗); 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/RESULTS_INDEX.md
- Code: `src/prediction_market_bot/c3_forecasting/forecaster.py` — `ModelForecaster`
- Governance: 08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md; 08_MODEL_RISK_GOVERNANCE/METHODOLOGY.md
- Related ADRs: ADR-0002 (forecast-only strategy); ADR-0003 (venue selection)
- Approval: APR-0012 (ACCEPTED 2026-05-28)

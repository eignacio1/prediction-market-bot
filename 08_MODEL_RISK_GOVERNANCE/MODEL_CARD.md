# Model Card — Prediction Market Trading Bot

**Purpose:** Document the model's purpose, design, performance, limitations, and risk profile. Required for G4 Evidence Gate. Updated at each model version promotion.  
**Owner (role):** Methodology Validator (MV) + Model Owner (MO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified the 2026-07-02 addendum's claims below against `DECISION_LOG.md` and `MEMORY_BANK.md`. `v2-065b9510` is confirmed still the latest-trained NBA model (unchanged since SESSION 73/ADR-0031, no newer retrain since). One nuance the addendum's "Current production model" phrasing glosses over, worth flagging explicitly: **`v2-065b9510` is trained but was NOT actually deployed to the VPS as of the last confirming log** (SESSION 76, 2026-06-23: "Model v1-28483b21 still deployed — expected, v2 deploy deferred to October per Phase 4"). `v1-28483b21` remains the artifact actually running in production. This is moot for live behavior right now since NBA itself is DARK/FROZEN per operator directive (see `project_nba_deferred.md`) — no NBA inference is running at all — but if NBA work resumes ahead of the 2026-27 season, confirm the v2 deploy (ADR-0031/T-185 runbook, 8-step + DS witness) has actually executed before trusting this card's "production model" language as describing what the VPS is running, not just what was last trained. No other drift found.  
**Next review:** After EXP-004 (HYP-003) resolves vig survival; at each model version promotion  
**Staleness triggers:** New model version; new experiment results; new failure mode identified; paper/live performance data  
**Upstream links:** HYPOTHESES.md, EXPERIMENT_LOG/, VALIDATION_PLAN.md, METHODOLOGY.md  
**Downstream links:** ARTIFACT_REGISTRY.md, MONITORING_DRIFT_PLAN.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (ACCEPTED APR-0012 2026-05-28)  
**Confidence:** 10/10 — All performance metrics populated (VAL + TEST); G4 closed; C7 monitoring and drift thresholds wired (Phase 5)
**Decisions logged:** true — Model class, calibration approach, and promotion criteria captured in ADR-0004 (APR-0012) and G4 gate (APR-0006)

---

## ⚠️ Current Production Model (2026-07-02 documentation-remediation pass — read this before the sections below)

**This document's "Model Overview," "Performance Metrics," and most of "Known Limitations" describe the G4-gate model (`v1-9939a6a5`, FEATURE_VERSION 1.2.0, 31 features) as if it were still current. It is not; that TEST evaluation is retained below as the accurate, immutable G4 gate record — not rewritten — but a reader needs this addendum to avoid treating it as live.**

**Current production model (as of SESSION 73, 2026-06-23, ADR-0031):** `v2-065b9510` — LR L1+L2, **FEATURE_VERSION 1.4.0, 83 features** (adds the qualitative PRF layer: QS-2026-05-28-002, backdated to effective_from 2021-10-19, confirmed positive signal via EXP-007 +0.0017 Brier / +0.0159 ECE). Metrics: Brier 0.2451, ECE 0.0426, AUC-ROC 0.5822. `v1-28483b21` (an intermediate version) was superseded. Model retrained on the VPS per ADR-0031's authorization (T-072).

**Also missing from this document entirely: MLB.** MLB has its own C1/C2/C3 pipeline and its own model, trained and evaluated separately from the NBA model this card describes. This card has never been extended to cover it — a genuinely separate Model Card for the MLB model does not appear to exist in this folder as of this pass. That is a real gap, flagged rather than filled with invented figures.

Also note, since it directly contradicts this document's own header: **ADR-0004 is ACCEPTED** (APR-0012, 2026-05-28) — the Model Overview table below still says "ADR-0004 PENDING formal acceptance," which was already wrong relative to this very file's own Decision references line above it.

---

## Model Overview

| Field | Detail |
|-------|--------|
| Model ID | TBD (assigned at first promotion to ARTIFACT_REGISTRY.md) |
| Model version | `v1-` + sha1(`MODEL_CLASS` \| sorted_feature_names)[:8] — computed at `fit()` |
| Purpose | Generate calibrated probability estimates for NBA player prop prediction market outcomes |
| Target variable | Binary: 1 = player exceeded their L10 rolling mean in points for this game; 0 = did not |
| Output | `p_estimate ∈ [0,1]`; `ci_lower`/`ci_upper` (Wilson 90% CI); `edge`; `recommended_direction` (YES/NO/PASS) |
| Model class | `LogisticRegression+PlattScaling` — confirmed Phase 3 baseline (**ADR-0004 ACCEPTED, APR-0012, 2026-05-28** — corrected 2026-07-02; this row previously said "PENDING," contradicting this file's own Decision references line) |
| Training data | DS-01 via nba_api (C1 NBAIngestionClient); SNAP-001 registered; DS-02 deferred to Phase 6+ |
| Feature set version | FEATURE_VERSION 1.2.0 — 31 features (F-001 to F-031); F-032–F-038 pruned (HYP-005 falsified); see DATA_FLOWS_LINEAGE.md |
| Training window | EXP-001: 2021-22 season first half (TRAIN); 2022-23 season (VALIDATION) — exact dates in EXP-001 record |
| Minimum training samples | 30 (`MIN_FIT_SAMPLES`) — fit() returns False if fewer rows after NaN removal |
| Source code | `src/prediction_market_bot/c3_forecasting/forecaster.py` — `ModelForecaster` class |

---

## Training Procedure

### Pipeline

```
StandardScaler()
    → CalibratedClassifierCV(
          LogisticRegression(penalty="l2", C=1.0, solver="lbfgs",
                             max_iter=1000, random_state=42, class_weight="balanced"),
          method="sigmoid",   # Platt scaling
          cv=3
      )
```

- Scaler is fit on training data only; same scaler is applied at inference (no re-fit).
- Platt calibration (`CalibratedClassifierCV`) wraps the logistic regression to improve probability reliability.
- NaN imputation: column medians computed on training rows, applied at inference with 0.0 fallback.

### Feature Extraction

- Input: IF-C2-C3 DataFrame. Only columns in `feature_names` are used.
- Missing feature columns are filled with NaN and imputed.
- All 38 features are extracted in canonical order from `FeatureStore.get_feature_names()`.

### Edge Formula (ADR-0003)

```
edge = p̂ - mid_price(venue) - spread(venue)/2
```
- Phase 3: `spread = 0` (no live venue prices). `mid_price` defaults to `0.50`.
- Threshold YES: `edge ≥ 0.02` (+2%). Threshold NO: `edge ≤ −0.02`. Otherwise: PASS.

### Confidence Interval

Wilson score 90% CI (z = 1.645):
```
center = (p̂ + z²/2n) / (1 + z²/n)
margin = (z / (1 + z²/n)) × √(p̂(1-p̂)/n + z²/(4n²))
```
Lower/upper clamped to [0, 1].

---

## Performance Metrics

*Validation metrics from 50-player cohort (SNAP-2026-05-28-001, T-043). TEST set held for formal G4 gate.*

### Validation Results (3 independent chronological windows)

| Window | Exp | Train rows | Val rows | Brier (model) | Brier (null) | Improvement | ECE | AUC-ROC |
|--------|-----|-----------|---------|---------------|-------------|-------------|-----|---------|
| 2023-02 – 2023-04 | EXP-001 | 5,042 | 1,211 | **0.2444** | 0.2500 | **+0.0056 ✓** | **0.0345 ✓** | 0.5785 |
| 2022-02 – 2022-04 | EXP-002 | 1,821 | 1,155 | **0.2451** | 0.2500 | **+0.0049 ✓** | **0.0289 ✓** | 0.5866 |
| 2021-12 – 2022-01 | EXP-003 | 1,020 | 801 | **0.2474** | 0.2500 | **+0.0026 ✓** | **0.0369 ✓** | 0.5673 |
| **Average** | | | | **0.2456** | 0.2500 | **+0.0044** | **0.0334** | **0.5775** |

### Test Set (Held Out — 2023-24 season; 3,254 rows)

Evaluated at formal G4 gate (APR-0006 + APR-0012 signed 2026-05-28). Evidence file: `exp_output/EXP-001/EXP-001_test_evaluation.json`.

| Metric | Value | Null model | Improvement | Gate criterion | Pass |
|--------|-------|-----------|-------------|---------------|------|
| Brier Score (TEST) | **0.2416** | 0.2500 | **+0.0084** | > +0.005 | ✅ |
| ECE (TEST) | **0.0247** | — | — | < 0.05 | ✅ |
| AUC-ROC (TEST) | **0.6062** | 0.50 | — | > 0.55 | ✅ |

**Model version:** `v1-9939a6a5` (LR+Platt, FEATURE_VERSION 1.2.0, 31 features)
**ADR-0004 ACCEPTED** — LR+Platt confirmed as production model class (APR-0012 2026-05-28).

TEST Brier +0.0084 exceeds average validation Brier +0.0044 — signal appears to generalize to held-out season.

### Feature Ablation (T-044 — HYP-005)

| Feature set | Features | Brier improvement | ECE |
|-------------|----------|------------------|-----|
| FEATURE_VERSION 1.1.0 (ERI + schedule) | 38 | +0.0056 | 0.0345 |
| FEATURE_VERSION 1.0.0 (rolling box-score only) | 31 | +0.0054 | 0.0314 |
| **Δ (v1.1.0 − v1.0.0)** | | **+0.0002** | **+0.0031** |

**HYP-005 FALSIFIED**: ERI + schedule features (F-032–F-038) add Δ Brier = +0.0002 (threshold: 0.005). Pruned in FEATURE_VERSION 1.2.0 (T-046). Active model uses v1.0.0-equivalent 31-feature set.

**Calibration curve:** Brier improvement consistent across all 3 windows. ECE < 0.04 in all cases — Platt scaling performs well with ≥1,000 training rows.

**Null model:** Market-implied probability = 0.50 for all events (DS-02 not active in Phase 3). Brier null = 0.25.

---

## Intended Use

| Field | Detail |
|-------|--------|
| Intended use | Generate probability estimates to inform position sizing in a prediction market trading strategy |
| Intended users | Sole operator (Earl Ignacio) |
| Deployment environment | Paper trading (ENV-02); live capital (ENV-03, Phase 8+) |
| Decision role | Advisory — final position sizing governed by risk limits (RISK_APPETITE_CONSTRAINTS.md) |

---

## Out-of-Scope Use

| Prohibited Use | Reason |
|----------------|--------|
| Use in markets outside the training distribution | Model validity does not extend to untested market categories |
| Automated retraining without a new ADR | Frozen model policy |
| Use as sole basis for capital decisions without risk limit enforcement | Model may have calibration error; risk limits are a mandatory guardrail |
| Publication or sharing of model artifacts | Proprietary; governance scope |

---

## Known Limitations

1. **Training data scope:** Model is trained on NBA player points props only (DS-01, nba_api). Performance on other stat categories (rebounds, assists, etc.) is unknown and likely degraded without retraining.
2. **Null model baseline:** No live market prices available in Phase 3. `market_implied_prob` defaults to 0.50 — edge calculations are relative to a 50/50 prior, not real venue prices. Edge thresholds (+2%/−2%) are provisional until DS-02 is integrated (Phase 6+). Actual edge vs vig is unknown until HYP-003 is tested (EXP-004, Phase 5+).
3. **NaN imputation:** Rolling window features produce NaN for each player's first few games (min_periods=3). Column median imputation applied; sensitivity to imputation strategy not yet quantified.
4. **Minimum training data:** Model requires ≥1,000 TRAIN rows for reliable calibration (ECE < 0.05). With only 10 players (~200–900 rows per window), calibration fails. Confirmed: 50 players (~1,000–5,000 rows per window) achieves ECE 0.028–0.037.
5. **ERI + schedule features removed (HYP-005 falsified):** F-032–F-038 (season_type_is_playoffs, days_since_last_game, b2b_flag, load_games_l7d, eri_prev_hot/cold/consec) added Δ Brier = +0.0002 vs rolling box-score alone. Pruned in FEATURE_VERSION 1.2.0 (T-046). Active feature set is 31 features (F-001–F-031).
6. **Signal vs venue vig (LIM-003 — OPEN):** TEST Brier improvement +0.0084. Kalshi vig is typically 4–6% on binary markets. Whether +0.0084 signal survives the vig spread is untested (HYP-003, EXP-004). EXP-004 is blocked on DS-02 (live venue prices). If signal does not survive vig, a model retrain with larger player set or additional features may be required. This is the primary open risk before G6.
7. **PRF taxonomy not operationalized:** Player Attribute Matrix PRF archetypes (DS-01) are documented but not yet encoded as numeric features (OQ-017). May provide orthogonal signal not captured by rolling box-score.
8. **Feature version lock:** Model is version-pinned. Any feature set change requires FEATURE_VERSION bump, model retrain, and ADR update. Pending FEATURE_VERSION 1.2.0 (prune v1.1.0 features).

---

## Risk Profile

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Overfit to training data | HIGH | HIGH | Hold-out test set; ≥3 independent experiments |
| Signal decay in live market | MEDIUM | HIGH | Drift monitoring (FM-03); MONITORING_DRIFT_PLAN.md |
| Calibration failure | MEDIUM | HIGH | Calibration curve check at G4; temperature scaling if needed |
| Model used beyond distribution | MEDIUM | HIGH | Scope constraints documented here; operator training |

---

## Governance

| Field | Detail |
|-------|--------|
| Model approval required before paper use | ADR-0004 + G5 gate |
| Model approval required before live use | ADR-0005 + G6 gate |
| Drift threshold | Brier score > baseline(0.2416) + 0.05 → L2 alert; > baseline + 0.10 → L4 kill switch (C7 auto-trigger) |
| Drift monitoring | C7 SystemMonitor (`c7_monitoring/monitor.py`); Phase 5+ active; rolling 30-event window; wired to C6 audit log |
| Drift response | L1 Watch → log; L2 Alert → manual review; L3 Pause → halt new positions; L4 Kill → kill switch |
| Dashboard | C8 Visual Dashboard (`c8_dashboard/dashboard.py`); CLI: `python -m prediction_market_bot.c8_dashboard.dashboard` |
| Retraining policy | Prohibited in production; new ADR + new model version required |
| Retirement policy | Model retired when superseded by new version with ADR |

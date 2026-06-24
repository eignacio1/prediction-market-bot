# Artifact Registry — Prediction Market Trading Bot

**Purpose:** Track all versioned model artifacts, feature set definitions, and configuration files that are promoted to paper or live environments. Every artifact used in production must be registered here.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-05-22  
**Next review:** At each paper/live promotion; when any production artifact changes  
**Staleness triggers:** New model promoted; feature version changed; configuration updated for paper/live  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, PIPELINES_JOBS.md  
**Downstream links:** 08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (pending), ADR-0005 (pending)  
**Confidence:** N/A — No artifacts promoted yet; registry initialized for Phase 6+

---

## Registry Policy

1. **Every model promoted to paper or live must be registered here** before the pipeline activates
2. **Model version is immutable after registration** — retraining requires a new version entry
3. **The model version used in a production run must be cited in every C6 audit log entry** (IF-C3-C5 field: model_version)
4. **Artifact hash must be verified before any production run** to detect unauthorized modifications

---

## Model Artifact Registry

| Model ID | Version | Description | Feature Version | Training Window | Brier Score (Test) | Promotion Date | Environment | Promoted By | Notes |
|----------|---------|-------------|----------------|----------------|-------------------|---------------|-------------|-------------|-------|
| prod_model.joblib | v1-28483b21 | LR + Platt, 78 features (31 quant + 47 qual), 5-season regular season data | 1.3.0 | 5 NBA seasons through 2025-26 regular season (2026-05-29 cutoff) | Brier=0.246622 (holdout ≥2026-02-01, n=1179) | 2026-05-29 SESSION | paper | Earl Ignacio (ADR-0004) | Production model v1; superseded by v2-065b9510 per ADR-0031 |
| v2_model.joblib | v2-065b9510 | LR + Platt, 83 features (36 quant + 47 qual), adds F-041/F-042/F-043 playoff context | 1.4.0 | Same as v1 + additional rows; holdout cutoff 2026-02-01; 15,274 train rows | Brier=0.245115 (same holdout, n=1179); ECE=0.0426; AUC=0.5822 | 2026-06-23 SESSION 73 | paper (pending deployment) | Earl Ignacio (ADR-0031) | Shadow gate PASSED (Δ=+0.001507); T-177 INCONCLUSIVE (p=0.1639); F-042=NaN (known limitation); supersedes v1-28483b21 |

*v1-28483b21 superseded by ADR-0031. v2-065b9510 pending deployment to paper trading (dark period — deploy at 2026-27 season start).*

---

## Feature Set Registry

| Feature Version | Description | Features Included | Changes from Prior | Date |
|----------------|-------------|------------------|-------------------|------|
| — | — | — | — | — |

*Populated at Phase 3 when feature engineering begins.*

---

## Configuration Registry

| Config ID | Type | Description | Used In | Version | Date |
|-----------|------|-------------|---------|---------|------|
| — | — | — | — | — | — |

---

## Promotion Gate Checklist (required before any production registration)

Before registering a model artifact for paper or live use:

- [ ] Model version string confirmed unique
- [ ] Brier score vs null model confirmed on held-out test set
- [ ] Calibration curve within acceptable range (ECE < threshold confirmed at G4)
- [ ] Artifact hash computed and stored
- [ ] Dependency lock file version recorded
- [ ] ADR-0004 (paper) or ADR-0005 (live) accepted
- [ ] Artifact registered in this file before pipeline activation

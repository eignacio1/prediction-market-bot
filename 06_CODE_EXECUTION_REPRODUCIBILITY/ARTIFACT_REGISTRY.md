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
| — | — | — | — | — | — | — | — | — | — |

*No models promoted yet. First entry created at Phase 6 paper trading activation (requires ADR-0004).*

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

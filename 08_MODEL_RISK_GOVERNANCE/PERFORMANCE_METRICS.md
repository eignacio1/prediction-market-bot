# Performance Metrics — Prediction Market Trading Bot

**Purpose:** Canonical, version-controlled record of all model performance metrics across experiments. Distinct from MODEL_CARD.md narrative — this is the raw metric ledger.  
**Owner (role):** Methodology Validator (MV) + Model Owner (MO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review, two findings. (1) The 2026-07-02 addendum's `v2-065b9510` claim was re-checked against `DECISION_LOG.md`/`MEMORY_BANK.md` in this same pass (see `MODEL_CARD.md`'s 2026-07-23 note) — still the latest-trained NBA model, no newer retrain since. Same deploy-vs-trained nuance applies here as in `MODEL_CARD.md`: `v2-065b9510` is trained, not yet deployed to the VPS (deploy deferred to Oct 2026); moot while NBA remains DARK/FROZEN. (2) **Real drift found and fixed:** the EXP-004 section below (and its "Next review" line) described Part B as pending DS-02 connectivity — that was true as of the 2026-05-28 write time, but DS-02-B-001 was RESOLVED later that same day (mobile hotspot; session `EXP-004-FE3E2169`; see `04_EXECUTION/RID_LOG.md`, `00_ADMIN/APPROVALS_REGISTER.md` APR-0007) and Part B actually ran and confirmed HYP-003. See the updated EXP-004 section for the corrected result. The G4-gate tables otherwise remain an accurate closed-gate historical record and are correctly left unedited per this project's ADR-immutability culture.  
**Next review:** At G5 gate (EXP-004 Part B is complete — see below)  
**Staleness triggers:** New experiment run; model version bumped; FEATURE_VERSION changed  
**Upstream links:** 05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/, 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/RESULTS_INDEX.md  
**Downstream links:** MODEL_CARD.md, 07_TEST_VALIDATION_EVIDENCE/VALIDATION_REPORTS/  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (ACCEPTED — APR-0012)  
**Confidence:** 10/10 — Validation and TEST set metrics complete; G4 gate closed 2026-05-28 (this remains an accurate closed-gate record). 4/10 on whether this document reflects the *current* production model — it does not; see addendum immediately below, added 2026-07-02.

---

## ⚠️ Current Production Model Is Not What's Below (2026-07-02 documentation-remediation pass)

The "Current Model Version" table immediately below describes the G4-gate model (`v1-9939a6a5`), frozen as of 2026-05-28. **Production has since moved to `v2-065b9510`** (LR L1+L2, FEATURE_VERSION 1.4.0, 83 features, QS-2026-05-28-002 qualitative layer live, Brier 0.2451 / ECE 0.0426 / AUC 0.5822, ADR-0031, retrained SESSION 73 2026-06-23). The tables below are retained unedited as the accurate G4 gate evidence record — do not read "Current" in the section header literally without this note. **MLB has an entirely separate model/pipeline not represented anywhere in this document** — flagged as a gap, not filled with unverified figures.

---

## Current Model Version

| Field | Detail |
|-------|--------|
| Model class | `LogisticRegression + PlattScaling` (CalibratedClassifierCV, method="sigmoid", cv=3) |
| FEATURE_VERSION | 1.2.0 — 31 features (F-001–F-031); F-032–F-038 pruned |
| Data snapshot | SNAP-2026-05-28-001 — 50 players × 3 seasons |
| Model version hash | `v1-9939a6a5` (FEATURE_VERSION 1.2.0, 31 features; computed at `fit()`) |
| Null model baseline | `market_implied_prob = 0.50` (DS-02 not active in Phase 3) |

---

## Validation Metrics (Phase 4 — SNAP-2026-05-28-001)

*Three independent chronological windows. TEST rows held for formal G4 gate.*

| Experiment | Val Window | TRAIN rows | VAL rows | Brier (model) | Brier (null) | Improvement | ECE | AUC-ROC | Pass/Fail |
|-----------|-----------|-----------|---------|--------------|-------------|-------------|-----|---------|----------|
| EXP-001 | 2023-02-01 – 2023-04-30 | 5,042 | 1,211 | 0.2444 | 0.2500 | **+0.0056** | **0.0345** | 0.5785 | ✅ PASS |
| EXP-002 | 2022-02-01 – 2022-04-10 | 1,821 | 1,155 | 0.2451 | 0.2500 | **+0.0049** | **0.0289** | 0.5866 | ✅ PASS |
| EXP-003 | 2021-12-16 – 2022-01-31 | 1,020 | 801 | 0.2474 | 0.2500 | **+0.0026** | **0.0369** | 0.5673 | ✅ PASS |
| **Average** | — | — | — | **0.2456** | 0.2500 | **+0.0044** | **0.0334** | **0.5775** | ✅ G4 CRITERIA MET |

**G4 criteria:**
- Model beats null Brier in ≥2/3 experiments: **3/3 ✅**
- ECE < 0.05 in at least one experiment: **3/3 ✅**
- AUC-ROC > 0.50 in all experiments: **3/3 ✅**

---

## Feature Ablation Metrics (T-044 — HYP-005)

| Feature set | Features | Brier improvement | ECE | AUC-ROC |
|-------------|----------|------------------|-----|---------|
| FEATURE_VERSION 1.1.0 (38 feat, ERI + schedule) | 38 | +0.0056 | 0.0345 | 0.5785 |
| FEATURE_VERSION 1.0.0-equiv (31 feat, rolling box-score) | 31 | +0.0054 | 0.0314 | 0.5777 |
| **Δ (v1.1.0 − v1.0.0)** | | **+0.0002** | **+0.0031** | **+0.0008** |

**Conclusion:** Δ Brier = +0.0002 is below the 0.005 threshold. HYP-005 FALSIFIED. v1.2.0 (31 features) is the canonical feature set.

---

## Historical Metrics (Archived)

*10-player cohort (SNAP-2026-05-27-001, Phase 3 initial runs) — archived; superceded by 50-player results.*

| Experiment | TRAIN rows | Brier (model) | Brier (null) | Improvement | ECE | AUC-ROC | Status |
|-----------|-----------|--------------|-------------|-------------|-----|---------|--------|
| EXP-001 (10-player) | 986 | 0.2454 | 0.2500 | +0.0046 | 0.0596 | 0.5906 | ARCHIVED — sparsity failure |
| EXP-002 (10-player) | 340 | 0.2582 | 0.2500 | −0.0082 | 0.0941 | 0.5488 | ARCHIVED |
| EXP-003 (10-player) | 197 | 0.2568 | 0.2500 | −0.0068 | 0.0793 | 0.4364 | ARCHIVED |

*Root cause: Platt scaling unreliable at <1,000 TRAIN rows. Resolved by expanding to 50 players.*

---

## Test Set (EXP-001 — Evaluated at G4 Gate 2026-05-28)

**Test window:** 2023-10-24 – 2024-04-14 (2023-24 full season)  
**Test rows:** 3,254  |  **Model version:** `v1-9939a6a5`  |  **FEATURE_VERSION:** 1.2.0 (31 features)  
**Evidence artifact:** `exp_output/EXP-001/EXP-001_test_evaluation.json`

| Metric | Value | Null (0.50) | vs Null | G4 criterion | Status |
|--------|-------|------------|--------|--------------|--------|
| Brier Score | 0.2416 | 0.2500 | **+0.0084** | Brier > null | ✅ PASS |
| ECE (10-bin) | 0.0247 | — | — | ECE < 0.05 | ✅ PASS |
| AUC-ROC | 0.6062 | 0.50 | +0.1062 | AUC > 0.50 | ✅ PASS |

**Finding:** TEST set results are *stronger* than the VALIDATION average (+0.0084 vs +0.0044 Brier improvement). No degradation on unseen data. G4 gate closed.

---

## EXP-004 — Edge vs Vig Backtest (HYP-003 / Phase 5)

**Run at:** 2026-05-28T18:29:37Z | **Session:** EXP-004-2A47C378
**Test set:** 3,254 rows (2023-24 season) — same as G4 test evaluation
**Vig source:** MEASURED_VIG_20260528 = 0.01 (37 KXNBAPTS markets, mobile hotspot)

| Metric | Value |
|--------|-------|
| Brier model | 0.2416 |
| Brier null | 0.2500 |
| Brier improvement | **+0.0084** |
| ECE | 0.0247 |
| AUC-ROC | 0.6062 |
| Vig applied | 0.0100 |
| Half spread | 0.0050 |
| market_implied_prob | 0.50 (null; Part B below uses live Kalshi mid-prices) |
| YES bets (edge > 0.02+half_spread) | 1,380 |
| NO bets (edge < −0.02−half_spread) | 1,101 |
| Total bets | 2,481 of 3,254 (76.1%) |
| Win rate | **59.0%** |
| Total P&L (flat $1) | **+$212.10** |
| EV per bet | **+$0.0855** |
| HYP-003 verdict | **SUPPORTED (Part A)** |

**Part A caveat:** market_implied_prob=0.50 is a conservative null, used because Part A is a historical TEST-set backtest and does not have live venue prices to bet against.

**Part B — Live Market Alignment (completed 2026-05-28, same day as Part A, on mobile hotspot after DS-02-B-001 IP-block resolution; session `EXP-004-FE3E2169`):** 37 active KXNBAPTS markets (OKC-SAS game). Computed live edge = model_p − kalshi_mid − half_spread for the 2 players in the 50-player cohort with active markets that day: **Fox edge +0.405 (YES)**, **SGA edge −0.116 (NO)** — both directions consistent with model signal. **HYP-003 verdict: CONFIRMED (Parts A+B)** — this is Part B's directional confirmation on live prices, not an independent P&L/EV backtest; Part A's +$0.0855/bet EV figure remains the only quantified EV number and was not re-derived against live mid-prices at full TEST-set scale. See `04_EXECUTION/RID_LOG.md` (DS-02-B-001, RESOLVED) and `00_ADMIN/APPROVALS_REGISTER.md` (APR-0007) for the resolution record.

---

## Monitoring Thresholds (Phase 5+)

| Metric | Baseline (Phase 4 avg) | Alert threshold | Response |
|--------|----------------------|-----------------|---------|
| Brier score (30-event rolling) | 0.2456 | > 0.2956 (baseline + 0.05) | FM-03 drift response (RUNBOOK_model-drift.md) |
| ECE | 0.0334 | > 0.10 | Model review triggered |
| AUC-ROC | 0.5775 | < 0.52 | Model review triggered |

*Thresholds active at Phase 5 when C7 monitoring is wired.*

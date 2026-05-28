# Experiment Record — EXP-001: First Pipeline Run (C1→C2→C3→C4)

**Status:** RUNNING  
**Experiment ID:** EXP-001  
**Owner:** RL  
**Hypothesis tested:** HYP-001, HYP-002  
**Research question:** SQ-001, EQ-001  
**Started:** 2026-05-27  
**Completed:** TBD  

---

## Objective

EXP-001 establishes the first end-to-end execution of the research pipeline (C1 → C2 → C3 → C4) in ENV-01. The experiment ingests three seasons of NBA game log data for 10 target players, derives rolling features, fits a calibrated logistic regression model on a chronological TRAIN split, generates probability forecasts on a VALIDATION split, and presents each forecast to C4 (RiskEngine). C4 is expected to reject all forecasts with `REJECTED("phase_gate_not_reached")` because `BOT_C4_ACTIVE` is not set in ENV-01 (by design). The primary scientific question is whether the engineered rolling features allow the model to beat a uniform 0.50 baseline on Brier score — a direct test of HYP-001. ECE calibration (HYP-002) is measured concurrently. This experiment establishes the evidence baseline required for G4.

---

## Snapshot IDs Used

| Snapshot ID | Dataset | Description | Ingested |
|-------------|---------|-------------|----------|
| SNAP-2026-05-27-001 | DS-02 (nba_api) | Raw NBA game logs — 10 players × 3 seasons (2021-22, 2022-23, 2023-24) Regular Season | 2026-05-27 |

*SNAP-2026-05-27-001 registered in DATA_SNAPSHOTS_INDEX.md before experiment runs per snapshot discipline.*

---

## Code Reference

| Item | Detail |
|------|--------|
| Commit hash | TBD — populate after run |
| Script / notebook | `src/prediction_market_bot/run_exp001.py` |
| Entry point | `python -m prediction_market_bot.run_exp001` (from project root with `pip install -e .`) |
| Dependency lock | `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt` |
| Session ID | `EXP-001-{uuid}` (auto-generated per run) |
| Snapshot ID | `SNAP-2026-05-27-001` |

---

## Experimental Design

**Train window:** Game date ≤ 2023-01-31  
**Validation window:** 2023-02-01 – 2023-04-30  
**Test window:** 2023-24 full season (HELD OUT — accessed only at G4)  
**Split method:** Chronological (no random shuffling); labels assigned by `FeatureStore.assign_train_test_labels()`  

**Target players (10):**

| Player | Player ID |
|--------|-----------|
| LeBron James | 2544 |
| Kevin Durant | 201142 |
| Stephen Curry | 201939 |
| Giannis Antetokounmpo | 203507 |
| Nikola Jokic | 203999 |
| Joel Embiid | 203954 |
| Damian Lillard | 203081 |
| Luka Doncic | 1629029 |
| Jayson Tatum | 1628369 |
| Jimmy Butler | 202710 |

**Seasons ingested:** 2021-22, 2022-23, 2023-24 (Regular Season; `SeasonType="Regular Season"`)

**Target variable:**

```
y = 1  if pts >= pts_l10_mean (prior 10 games, shift(1) applied)
y = 0  otherwise
y = NA if pts or pts_l10_mean is missing
```

This binary target proxies a player prop "over/under" contract (points) without requiring live market data. Temporal integrity: `pts_l10_mean` is computed from strictly prior games only (no look-ahead; TI-01 compliant).

**Features used:**

| Feature ID | Feature Name | Window | Temporal Safety |
|-----------|-------------|--------|----------------|
| F-001 | pts_l10_mean | 10 | VERIFIED — shift(1) before rolling |
| F-002 | pts_l10_std | 10 | VERIFIED |
| F-003 | reb_l10_mean | 10 | VERIFIED |
| F-004 | ast_l10_mean | 10 | VERIFIED |
| F-005 | stl_l10_mean | 10 | VERIFIED |
| F-006 | blk_l10_mean | 10 | VERIFIED |
| F-007 | tov_l10_mean | 10 | VERIFIED |
| F-008 | fg_pct_l10_mean | 10 | VERIFIED |
| F-009 | fg3_pct_l10_mean | 10 | VERIFIED |
| F-010 | ft_pct_l10_mean | 10 | VERIFIED |
| F-011 | min_l10_mean | 10 | VERIFIED |
| F-012 | plus_minus_l10_mean | 10 | VERIFIED |
| F-013 through F-026 | Additional rolling features from FeatureStore | 10 | VERIFIED |

All features derived via `FeatureStore.compute_features_bulk()` with `FEATURE_VERSION = "1.0.0"`, `DEFAULT_WINDOW = 10`, `MIN_PERIODS = 3`.

**Model class:** LogisticRegression + PlattScaling (`CalibratedClassifierCV(method="sigmoid", cv=3)`)  
**Preprocessing:** `StandardScaler` (fit on TRAIN only; applied to TRAIN and VALIDATION)  
**Hyperparameters:** sklearn defaults + `max_iter=1000`, `solver="lbfgs"`  
**Model version:** `v1-{sha1[:8]}` where sha1 = SHA1(feature_names + model_class)  
**Null model:** Constant `p = 0.50` (uniform prior; no live venue price data until Phase 5 / ENV-02)  
**Market implied prob (C3 input):** `0.50` (Phase 3 placeholder — edge = p̂ - 0.50; no spread adjustment)  
**Kelly fraction:** 0.25 (DEFAULT_KELLY_FRACTION; C4 gate not active in ENV-01)  

---

## Temporal Integrity Check

- [x] All feature `temporal_cutoff` values precede `game_date` — enforced by `shift(1)` in `FeatureStore.compute_features_bulk()` (lines ~200-220); `temporal_cutoff = df["game_date"].shift(1)` (line ~300)
- [x] No outcome data appears in the feature set — `pts` (actual game points) excluded from feature matrix; used only to construct target variable after feature computation
- [x] Train/validation/test splits are strictly chronological with no overlap — `assign_train_test_labels()` uses date thresholds; TEST rows excluded from all training and validation metrics
- [x] Snapshot IDs are registered and immutable — SNAP-2026-05-27-001 registered in DATA_SNAPSHOTS_INDEX.md

---

## C4 Phase Gate Behavior (Expected)

In ENV-01, `BOT_C4_ACTIVE` is NOT set. C4 (`RiskEngine.evaluate_forecast()`) will return:

```python
{"status": "REJECTED", "reason": "phase_gate_not_reached", ...}
```

for every forecast record. The runner script validates this behavior — if C4 does NOT reject, the experiment errors loudly:

```
[UNEXPECTED GATE OPEN] C4 returned status '<status>' instead of REJECTED ...
```

This is a security control: no execution pathway can be activated accidentally in ENV-01.

---

## Results

*Populated after actual experiment run. Runner outputs: `exp_output/EXP-001/audit_exp001.jsonl`, `EXP-001_feature_matrix.csv`, `EXP-001_forecast_validation.csv`.*

| Metric | Train | Validation | Null Model (Val) | Notes |
|--------|-------|-----------|-----------------|-------|
| Brier Score | TBD | TBD | 0.25 (null = 0.50 baseline) | Lower is better |
| Log Loss | TBD | TBD | 0.6931 (null = ln(2)) | Lower is better |
| ECE (Calibration) | TBD | TBD | — | Lower is better; target < 0.05 |
| AUC-ROC | TBD | TBD | 0.50 | Higher is better |

**Row counts:** TBD after run  
**TRAIN rows used:** TBD  
**VALIDATION rows used:** TBD  
**TEST rows (held out):** TBD  

**Calibration curve:** TBD — saved to `exp_output/EXP-001/`  
**Edge distribution (p̂ - 0.50):** TBD — expected near-zero mean in Phase 3 (no asymmetric signal advantage)

---

## Look-Ahead Audit

- [x] Automated temporal overlap check — `temporal_cutoff` is set from `game_date.shift(1)` in C2; runner validates non-null `temporal_cutoff` before including rows
- [x] Manual review of `temporal_cutoff` for all features confirmed — all rolling windows use `.shift(1)` before `.rolling()` per C2 implementation
- [ ] Lineage register entries confirmed for all features used — pending post-run verification

---

## Interpretation

**Does this experiment confirm or falsify the hypothesis?**

*TBD — populate after run.*

**Key findings:**
- TBD

**Unexpected results:**
- TBD

---

## Confidence

**Confidence in this result:** TBD  
**Reason:** *Pending actual run; pipeline architecture is sound (temporal integrity verified at code review); model class (LR+Platt) is appropriate baseline for binary classification.*

---

## Follow-Up

| Action | Owner | Due |
|--------|-------|-----|
| Run EXP-001 locally (T-035 complete) | RL | 2026-07-20 |
| Populate Results section with actual metrics | RL | After run |
| Evaluate HYP-001 (Brier improvement > 0.01) | RL | After run |
| Evaluate HYP-002 (ECE < 0.05) | RL | After run |
| If HYP-001 confirmed: proceed to EXP-002 | RL | T-036 |
| If HYP-001 falsified: root-cause feature engineering | RL | As needed |

---

## Links

- Research questions: RESEARCH_QUESTIONS.md#SQ-001, #EQ-001
- Hypotheses: HYPOTHESES.md#HYP-001, #HYP-002
- Snapshots: DATA_SNAPSHOTS_INDEX.md#SNAP-2026-05-27-001
- Runner script: `src/prediction_market_bot/run_exp001.py`
- Results index: RESULTS_SUMMARIES/RESULTS_INDEX.md

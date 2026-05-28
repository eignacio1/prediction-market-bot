# Experiment Record — EXP-003: Backtest Window 3 (2021-22 Season Early-Mid)

**Status:** PLANNED  
**Experiment ID:** EXP-003  
**Owner:** RL  
**Hypothesis tested:** HYP-001 (third independent window) + HYP-004 (signal stability)  
**Research question:** SQ-001, RQ-001  
**Started:** TBD  
**Completed:** TBD  

---

## Objective

EXP-003 is the third independent backtesting window in the walk-forward framework (T-036). It uses the earliest temporal window of the three experiments, training on the first ~35 games of the 2021-22 NBA season (through 2021-12-15) and evaluating on games from 2021-12-16 through 2022-01-31. This design serves two purposes: (1) it completes the third independent experiment required for the G4 evidence threshold (HYP-001: Brier improvement confirmed across ≥3 windows); and (2) because it represents the smallest and oldest training window, it is the most stringent test for HYP-004 (signal stability across time). If the model still beats the null baseline with only ~35 prior-game rows per player in training, it provides evidence that the rolling feature signal is present even at the start of a season, supporting deployment viability.

---

## Snapshot IDs Used

| Snapshot ID | Dataset | Description | Ingested |
|-------------|---------|-------------|----------|
| SNAP-2026-05-27-001 | DS-02 (nba_api) | Raw NBA game logs — 10 players × 3 seasons (2021-22, 2022-23, 2023-24) Regular Season | 2026-05-27 |

*If run_backtest.py is invoked with --raw-csv, SNAP-2026-05-27-001 is reused (no re-ingestion). If a fresh pull is used, SNAP-2026-05-27-002 is cited instead. All datasets must be registered in DATA_SNAPSHOTS_INDEX.md before the experiment runs.*

---

## Code Reference

| Item | Detail |
|------|--------|
| Commit hash | TBD — populate after run |
| Script / notebook | `src/prediction_market_bot/run_backtest.py` |
| Entry point | `python -m prediction_market_bot.run_backtest --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv --window exp003` |
| Dependency lock | `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt` |
| Session ID | `BACKTEST-EXP-003-{uuid}` (auto-generated per run) |
| Snapshot ID | `SNAP-2026-05-27-001` (or `SNAP-2026-05-27-002` if fresh pull) |
| Framework | `src/prediction_market_bot/backtester.py` — `Backtester.run_window()` |

---

## Experimental Design

**Train window:** Game date ≤ 2021-12-15 (approx. first 35 games of 2021-22 season per player)  
**Validation window:** 2021-12-16 – 2022-01-31 (games ~36–55 of 2021-22 season; ~20 games per player)  
**Test window:** All game dates > 2022-01-31 (includes 2022-02-01 onwards — HELD OUT; accessed only at G4)  
**Split method:** Chronological (no random shuffling); labels assigned by `FeatureStore.assign_train_test_labels()`

**Independence from EXP-001 and EXP-002:**
- EXP-001 validation window: 2023-02-01 – 2023-04-30 (non-overlapping)
- EXP-002 validation window: 2022-02-01 – 2022-04-10 (non-overlapping)
- EXP-003 validation window: 2021-12-16 – 2022-01-31 (non-overlapping)

All three validation windows are non-overlapping. This window is the smallest (~20 games × 10 players ≈ 200 validation rows) and has the smallest training set (~35 games × 10 players ≈ 350 training rows after feature warm-up). This is intentional — if the signal holds even here, it provides stronger evidence for HYP-004.

**Target players (10):** Same cohort as EXP-001 — LeBron (2544), KD (201142), Curry (201939), Giannis (203507), Jokic (203999), Embiid (203954), Lillard (203081), Luka (1629029), Tatum (1628369), Butler (202710)

**Seasons in raw_df:** 2021-22, 2022-23, 2023-24 (all three seasons ingested; only early 2021-22 contributes to TRAIN and VALIDATION; post-2022-01-31 data is labeled TEST)

**Target variable:**

```
y = 1  if pts >= pts_l10_mean (prior 10 games, shift(1) applied)
y = 0  otherwise
y = NA if pts or pts_l10_mean is missing
```

**Note on small train set:** With only ~35 games per player and a 10-game rolling window (MIN_PERIODS=3), approximately 25–30 rows per player will have valid features. With 10 players this gives ~250–300 usable train rows, which exceeds MIN_TRAIN_SAMPLES=30 but is smaller than EXP-001's train set. Lower AUC-ROC and higher variance are expected. The experiment is still valid as a signal stability test.

**Features used:**

| Feature ID | Feature Name | Window | Temporal Safety |
|-----------|-------------|--------|----------------|
| F-001 | pts_l10_mean | 10 | VERIFIED — shift(1) before rolling |
| F-002 | pts_l10_std | 10 | VERIFIED |
| F-003 through F-026 | Additional rolling features from FeatureStore v1.0.0 | 10 | VERIFIED |

Feature version: `FEATURE_VERSION = "1.0.0"` (same as EXP-001 and EXP-002)

**Model class:** LogisticRegression + PlattScaling (`CalibratedClassifierCV(method="sigmoid", cv=3)`)  
**Preprocessing:** `StandardScaler` (fit on TRAIN only)  
**Hyperparameters:** sklearn defaults + `max_iter=1000`, `solver="lbfgs"`  
**Null model:** Constant `p = 0.50` (uniform prior; Phase 3 placeholder)  

---

## Temporal Integrity Check

- [x] All feature `temporal_cutoff` values precede `game_date` — enforced by `shift(1)` in `FeatureStore.compute_features_bulk()`
- [x] No outcome data appears in the feature set — `pts` excluded from feature matrix
- [x] Train/validation/test splits are strictly chronological with no overlap
- [x] Snapshot IDs are registered and immutable — SNAP-2026-05-27-001 registered before EXP-001 run
- [x] TEST rows (post 2022-01-31) not accessed at any point in this script

---

## C4 Phase Gate Behavior (Expected)

In ENV-01, `BOT_C4_ACTIVE` is NOT set. C4 will return `REJECTED(phase_gate_not_reached)` for the sample forecast routed through it. BOT_C4_ACTIVE must NEVER be set in ENV-01 or ENV-02.

---

## Results

*Populated after actual experiment run. Outputs: `exp_output/BACKTEST/EXP-003/`*

| Metric | Train | Validation | Null Model (Val) | Notes |
|--------|-------|-----------|-----------------|-------|
| Brier Score | TBD | TBD | 0.25 (null = 0.50 baseline) | Lower is better |
| Log Loss | TBD | TBD | 0.6931 (null = ln(2)) | Lower is better |
| ECE (Calibration) | TBD | TBD | — | Lower is better; target < 0.05 |
| AUC-ROC | TBD | TBD | 0.50 | Higher is better |

**Row counts:** TBD after run  
**TRAIN rows:** TBD (expected ~250–300 after feature warm-up)  
**VALIDATION rows:** TBD (expected ~150–200)  
**TEST rows (held out):** TBD  

---

## HYP-004 Evaluation Protocol

After all three experiments are run (EXP-001, EXP-002, EXP-003), HYP-004 is evaluated by plotting Brier score improvement (null Brier - model Brier) across the three validation windows in chronological order:

```
Window chronology (validation period start dates):
  EXP-003: 2021-12-16  ← earliest
  EXP-002: 2022-02-01
  EXP-001: 2023-02-01  ← most recent
```

HYP-004 is **confirmed** if: no systematic monotonic degradation in Brier improvement across windows.
HYP-004 is **falsified** if: Brier improvement shrinks to near-zero in the most recent window(s).

Note: Because EXP-003 has the smallest train set, lower performance there is not necessarily signal decay — it may reflect train set size. Confidence intervals should be considered when interpreting the stability trend.

---

## Look-Ahead Audit

- [x] Automated temporal overlap check — `temporal_cutoff` is set from `game_date.shift(1)` in C2
- [x] Manual review of `temporal_cutoff` confirmed — all rolling windows use `.shift(1)` before `.rolling()` per C2 implementation
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
**Reason:** *Pending actual run. The small train set (~250–300 rows) is the primary risk factor. CalibratedClassifierCV with cv=3 requires at least 3 samples per class per fold — with ~300 rows and ~50/50 class balance, each fold has ~100 rows, which is adequate. AUC-ROC may be unstable due to small validation set.*

---

## Follow-Up

| Action | Owner | Due |
|--------|-------|-----|
| Run EXP-003 via run_backtest.py | RL | 2026-06-21 |
| Populate Results section with actual metrics | RL | After run |
| Evaluate HYP-001 (third independent window) | RL | After run |
| Evaluate HYP-004 using all three experiment results | RL | After EXP-001 + EXP-002 + EXP-003 complete |
| If HYP-004 confirmed: proceed to G4 evidence collection | RL | After evaluation |

---

## Links

- Research questions: RESEARCH_QUESTIONS.md#SQ-001, #RQ-001
- Hypotheses: HYPOTHESES.md#HYP-001, #HYP-004
- Snapshots: DATA_SNAPSHOTS_INDEX.md#SNAP-2026-05-27-001
- Runner script: `src/prediction_market_bot/run_backtest.py`
- Framework: `src/prediction_market_bot/backtester.py`
- Results index: RESULTS_SUMMARIES/RESULTS_INDEX.md
- Related: EXP-001_first-pipeline-run.md, EXP-002_backtest-window-2.md

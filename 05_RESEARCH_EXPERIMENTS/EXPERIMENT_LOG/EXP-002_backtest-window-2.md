# Experiment Record — EXP-002: Backtest Window 2 (2021-22 Season Second Half)

**Status:** PLANNED  
**Experiment ID:** EXP-002  
**Owner:** RL  
**Hypothesis tested:** HYP-001 (second independent window)  
**Research question:** SQ-001, EQ-001  
**Started:** TBD  
**Completed:** TBD  

---

## Objective

EXP-002 is the second independent backtesting window in the walk-forward framework (T-036). It uses the same C1→C2→C3→C4 pipeline as EXP-001 but applies it to an earlier temporal window within the 2021-22 NBA season. The experiment trains a calibrated logistic regression model on game logs through 2022-01-31 (approximately the first 55 games of the 2021-22 regular season) and evaluates it on the final stretch of the 2021-22 regular season (2022-02-01 through 2022-04-10). The primary question is whether the rolling feature signal that was observed in EXP-001 (2022-23 season window) generalises to an independent temporal window. EXP-002 provides the second of three independent experiments required for the G4 evidence threshold (HYP-001: Brier improvement > 0.01 confirmed across ≥3 independent experiments). HYP-004 (signal stability) is partially informed by the comparison of this result against EXP-001 and EXP-003 outcomes.

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
| Entry point | `python -m prediction_market_bot.run_backtest --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv --window exp002` |
| Dependency lock | `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt` |
| Session ID | `BACKTEST-EXP-002-{uuid}` (auto-generated per run) |
| Snapshot ID | `SNAP-2026-05-27-001` (or `SNAP-2026-05-27-002` if fresh pull) |
| Framework | `src/prediction_market_bot/backtester.py` — `Backtester.run_window()` |

---

## Experimental Design

**Train window:** Game date ≤ 2022-01-31 (approx. first 55 games of 2021-22 season per player)  
**Validation window:** 2022-02-01 – 2022-04-10 (final ~35 games of 2021-22 regular season)  
**Test window:** All game dates > 2022-04-10 (includes 2022-23 and 2023-24 seasons — HELD OUT; accessed only at G4)  
**Split method:** Chronological (no random shuffling); labels assigned by `FeatureStore.assign_train_test_labels()`

**Independence from EXP-001 and EXP-003:**
- EXP-001 validation window: 2023-02-01 – 2023-04-30 (2022-23 season)
- EXP-002 validation window: 2022-02-01 – 2022-04-10 (2021-22 season second half)
- EXP-003 validation window: 2021-12-16 – 2022-01-31 (2021-22 season early-mid)

All three validation windows are non-overlapping. Each trains an independent model on a different TRAIN subset. This satisfies the "independent experiments" criterion for G4 evidence (HYP-001).

**Target players (10):** Same cohort as EXP-001 — LeBron (2544), KD (201142), Curry (201939), Giannis (203507), Jokic (203999), Embiid (203954), Lillard (203081), Luka (1629029), Tatum (1628369), Butler (202710)

**Seasons in raw_df:** 2021-22, 2022-23, 2023-24 (all three seasons ingested; only 2021-22 contributes to TRAIN and VALIDATION; 2022-23 and 2023-24 are labeled TEST)

**Target variable:**

```
y = 1  if pts >= pts_l10_mean (prior 10 games, shift(1) applied)
y = 0  otherwise
y = NA if pts or pts_l10_mean is missing
```

**Features used:**

| Feature ID | Feature Name | Window | Temporal Safety |
|-----------|-------------|--------|----------------|
| F-001 | pts_l10_mean | 10 | VERIFIED — shift(1) before rolling |
| F-002 | pts_l10_std | 10 | VERIFIED |
| F-003 through F-026 | Additional rolling features from FeatureStore v1.0.0 | 10 | VERIFIED |

Feature version: `FEATURE_VERSION = "1.0.0"` (same as EXP-001)

**Model class:** LogisticRegression + PlattScaling (`CalibratedClassifierCV(method="sigmoid", cv=3)`)  
**Preprocessing:** `StandardScaler` (fit on TRAIN only; applied to TRAIN and VALIDATION)  
**Hyperparameters:** sklearn defaults + `max_iter=1000`, `solver="lbfgs"`  
**Model version:** `v1-{sha1[:8]}` where sha1 = SHA1(feature_names + model_class) — same formula as EXP-001; model is independently fit on this window's TRAIN data  
**Null model:** Constant `p = 0.50` (uniform prior; Phase 3 placeholder)  
**Market implied prob (C3 input):** `0.50` (Phase 3 placeholder — no venue price data until Phase 5 / ENV-02)  

---

## Temporal Integrity Check

- [x] All feature `temporal_cutoff` values precede `game_date` — enforced by `shift(1)` in `FeatureStore.compute_features_bulk()`
- [x] No outcome data appears in the feature set — `pts` excluded from feature matrix
- [x] Train/validation/test splits are strictly chronological with no overlap
- [x] Snapshot IDs are registered and immutable — SNAP-2026-05-27-001 registered before EXP-001 run
- [x] TEST rows (post 2022-04-10) not accessed at any point in this script

---

## C4 Phase Gate Behavior (Expected)

In ENV-01, `BOT_C4_ACTIVE` is NOT set. C4 will return `REJECTED(phase_gate_not_reached)` for the sample forecast routed through it. If C4 does NOT return this status, the runner logs an error. BOT_C4_ACTIVE must NEVER be set in ENV-01 or ENV-02.

---

## Results

*Populated after actual experiment run. Outputs: `exp_output/BACKTEST/EXP-002/`*

| Metric | Train | Validation | Null Model (Val) | Notes |
|--------|-------|-----------|-----------------|-------|
| Brier Score | TBD | TBD | 0.25 (null = 0.50 baseline) | Lower is better |
| Log Loss | TBD | TBD | 0.6931 (null = ln(2)) | Lower is better |
| ECE (Calibration) | TBD | TBD | — | Lower is better; target < 0.05 |
| AUC-ROC | TBD | TBD | 0.50 | Higher is better |

**Row counts:** TBD after run  
**TRAIN rows:** TBD  
**VALIDATION rows:** TBD  
**TEST rows (held out):** TBD  

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
**Reason:** *Pending actual run. Pipeline architecture is sound. This window has a smaller train set (~55 games × 10 players) than EXP-001 (~90 games × 10 players), which may affect model stability. If model underperforms, root-cause via feature importance and class balance.*

---

## Follow-Up

| Action | Owner | Due |
|--------|-------|-----|
| Run EXP-002 via run_backtest.py | RL | 2026-06-21 |
| Populate Results section with actual metrics | RL | After run |
| Evaluate HYP-001 (Brier improvement > 0.01 on second window) | RL | After run |
| Compare EXP-002 result to EXP-001 — first signal stability data point | RL | After run |
| Proceed to EXP-003 for third independent window | RL | T-036 |

---

## Links

- Research questions: RESEARCH_QUESTIONS.md#SQ-001, #EQ-001
- Hypotheses: HYPOTHESES.md#HYP-001, #HYP-004
- Snapshots: DATA_SNAPSHOTS_INDEX.md#SNAP-2026-05-27-001
- Runner script: `src/prediction_market_bot/run_backtest.py`
- Framework: `src/prediction_market_bot/backtester.py`
- Results index: RESULTS_SUMMARIES/RESULTS_INDEX.md
- Related: EXP-001_first-pipeline-run.md, EXP-003_backtest-window-3.md

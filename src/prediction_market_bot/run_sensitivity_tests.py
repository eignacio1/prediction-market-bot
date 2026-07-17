"""
Sensitivity and Stress Tests — ST-001 through ST-004
=====================================================
Script:   src/prediction_market_bot/run_sensitivity_tests.py
Phase:    Phase 5 (Operational Readiness)
Evidence: G5 gate prerequisite — SENSITIVITY_STRESS_TESTS.md

Tests:
  ST-001  Imputation strategy sensitivity (median / ffill / zero)
  ST-002  Training window size sensitivity (25% / 50% / 100%)
  ST-003  Regularization C parameter sensitivity (0.01 / 0.1 / 1.0 / 10.0 / 100.0)
  ST-004  Permutation feature importance (no single feature > 50% of total)

How to run (from project root):
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_sensitivity_tests.py
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_sensitivity_tests.py \
        --feature-csv exp_output/EXP-001/EXP-001_feature_matrix.csv \
        --output-dir exp_output/SENSITIVITY_TESTS/

Baseline references (ADR-0004 / G4):
    Validation Brier null: 0.2500
    Model Brier improvement over null: +0.0084 (TEST set; used as benchmark)
    ECE (TEST): 0.0247
    AUC (TEST): 0.6062
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from typing import Any

# Ensure src/ is on path when run directly
_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# ---------------------------------------------------------------------------
# Constants — mirrors run_exp001.py
# ---------------------------------------------------------------------------

FEATURE_VERSION_TARGET = "1.2.0"

# V1.2.0 features: 31 columns (ERI + schedule features pruned per T-046)
_PRUNED_V110 = {
    "season_type_is_playoffs",
    "days_since_last_game",
    "b2b_flag",
    "load_games_l7d",
    "eri_prev_hot",
    "eri_prev_cold",
    "eri_consec_cold_games",
}

# EXP-001 temporal split boundaries (must match run_exp001.py)
TRAIN_END_DATE = "2023-01-31"
VAL_END_DATE = "2023-04-30"
FEATURE_WINDOW = 10
PLACEHOLDER_MARKET_IMPLIED_PROB = 0.50
NULL_BRIER = 0.2500   # null model at p=0.50

# G4 baseline (ADR-0004 / TEST set)
BASELINE_BRIER_IMPROVEMENT = 0.0084
PASS_TOLERANCE = 0.005     # ST-001 and ST-003 pass band


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _brier_improvement(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """null_brier - model_brier. Positive = beats null."""
    return float(NULL_BRIER - brier_score_loss(y_true, y_prob))


def _ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    y_prob_c = np.clip(y_prob, 1e-6, 1 - 1e-6)
    frac_pos, mean_pred = calibration_curve(y_true, y_prob_c, n_bins=n_bins, strategy="uniform")
    counts = np.histogram(y_prob_c, bins=n_bins, range=(0.0, 1.0))[0]
    counts = counts[counts > 0]
    n = min(len(frac_pos), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac_pos[:n] - mean_pred[:n])))


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan] * len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    prior_mean = pd.to_numeric(df[col], errors="coerce")
    target = (pts >= prior_mean).astype("Int8")
    target[pts.isna() | prior_mean.isna()] = pd.NA
    return target


def _fit_predict(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    C: float = 1.0,
) -> np.ndarray:
    """Fit LR+Platt on training data and return validation probabilities."""
    base = LogisticRegression(
        C=C,
        solver="lbfgs",
        max_iter=1000,
        random_state=42,
        class_weight="balanced",
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
    ])
    pipeline.fit(X_train, y_train)
    return pipeline.predict_proba(X_val)[:, 1]


def _impute_median(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    col_medians = np.nanmedian(X, axis=0)
    mask = np.isnan(X)
    X[mask] = np.take(col_medians, np.where(mask)[1])
    return X


def _impute_zero(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    X[np.isnan(X)] = 0.0
    return X


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_feature_data(feature_csv: Path) -> tuple[np.ndarray, np.ndarray, list[str], pd.DataFrame]:
    """
    Load feature matrix CSV and return train/val arrays plus feature names.

    Returns
    -------
    X_train, y_train, X_val, y_val, feature_names, raw_df
    """
    df = pd.read_csv(feature_csv)

    # Identify feature columns: all except ID/metadata cols and pruned v1.1.0 features
    non_feature = {
        "player_id", "player_name", "team_id", "team_abbreviation",
        "game_id", "game_date", "season", "season_type",
        "min", "pts", "reb", "ast", "stl", "blk", "tov", "pf",
        "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct",
        "ftm", "fta", "ft_pct", "plus_minus",
        "snapshot_id", "ingestion_run_id", "ingested_at",
        "temporal_cutoff", "feature_run_id", "feature_version",
        "train_test_label", "y_target",
    } | _PRUNED_V110

    feature_names = [c for c in df.columns if c not in non_feature]
    print(f"[DATA] Feature columns (v1.2.0): {len(feature_names)}")

    # Build target variable
    df["y_target"] = _build_target(df)

    # Assign labels if not present (fallback for older CSVs)
    if "train_test_label" not in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"])
        df["train_test_label"] = "TEST"
        df.loc[df["game_date"] <= TRAIN_END_DATE, "train_test_label"] = "TRAIN"
        df.loc[
            (df["game_date"] > TRAIN_END_DATE) & (df["game_date"] <= VAL_END_DATE),
            "train_test_label",
        ] = "VALIDATION"
    else:
        df["game_date"] = pd.to_datetime(df["game_date"])

    # Filter to usable rows
    usable = df[df["y_target"].notna() & df["temporal_cutoff"].notna()].copy()
    train_df = usable[usable["train_test_label"] == "TRAIN"]
    val_df = usable[usable["train_test_label"] == "VALIDATION"]

    print(f"[DATA] TRAIN: {len(train_df):,}  VALIDATION: {len(val_df):,}")

    X_train_raw = train_df[feature_names].to_numpy(dtype=float)
    y_train = train_df["y_target"].astype(int).to_numpy()
    X_val_raw = val_df[feature_names].to_numpy(dtype=float)
    y_val = val_df["y_target"].astype(int).to_numpy()

    return X_train_raw, y_train, X_val_raw, y_val, feature_names, train_df, val_df


# ---------------------------------------------------------------------------
# ST-001: Imputation Sensitivity
# ---------------------------------------------------------------------------


def run_st001(
    X_train_raw: np.ndarray,
    y_train: np.ndarray,
    X_val_raw: np.ndarray,
    y_val: np.ndarray,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_names: list[str],
) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("ST-001: Imputation Strategy Sensitivity")
    print("=" * 60)

    # Strategy B: forward-fill per player per season, then fall back to median
    def _ffill_strategy(tr_df: pd.DataFrame, va_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        combined = pd.concat([tr_df, va_df], ignore_index=False)
        combined = combined.sort_values(["player_id", "season", "game_date"])
        for col in feature_names:
            if col in combined.columns:
                combined[col] = combined.groupby(["player_id", "season"])[col].transform(
                    lambda s: s.ffill()
                )
        tr_filled = combined.loc[tr_df.index]
        va_filled = combined.loc[va_df.index]
        X_tr = tr_filled[feature_names].to_numpy(dtype=float)
        X_va = va_filled[feature_names].to_numpy(dtype=float)
        # Residual NaN → median (first game of season has no prior)
        X_tr = _impute_median(X_tr)
        X_va = _impute_median(X_va)
        return X_tr, X_va

    strategies = {
        "A_median_baseline": (
            _impute_median(X_train_raw),
            _impute_median(X_val_raw),
        ),
        "B_forward_fill": _ffill_strategy(train_df, val_df),
        "C_zero_fill": (
            _impute_zero(X_train_raw),
            _impute_zero(X_val_raw),
        ),
    }

    results = {}
    baseline_improvement = None
    for name, (X_tr, X_va) in strategies.items():
        y_prob = _fit_predict(X_tr, y_train, X_va)
        imp = _brier_improvement(y_val, y_prob)
        ece = _ece(y_val, y_prob)
        results[name] = {"brier_improvement": round(imp, 6), "ece": round(ece, 6)}
        if name == "A_median_baseline":
            baseline_improvement = imp
        print(f"  {name:30s}  Δ Brier={imp:+.4f}  ECE={ece:.4f}")

    # Pass/fail
    passed = True
    for name, r in results.items():
        delta = abs(r["brier_improvement"] - (baseline_improvement or 0))
        r["delta_vs_baseline"] = round(delta, 6)
        r["pass"] = delta <= PASS_TOLERANCE
        if not r["pass"]:
            passed = False
        print(f"    {name}: Δ vs baseline = {delta:+.4f}  "
              f"{'PASS' if r['pass'] else 'FAIL (> 0.005 tolerance)'}")

    overall = "PASS" if passed else "FAIL"
    print(f"\nST-001 Overall: {overall}")
    return {"st_id": "ST-001", "status": overall, "results": results}


# ---------------------------------------------------------------------------
# ST-002: Training Window Size Sensitivity
# ---------------------------------------------------------------------------


def run_st002(
    X_train_raw: np.ndarray,
    y_train: np.ndarray,
    X_val_raw: np.ndarray,
    y_val: np.ndarray,
) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("ST-002: Training Window Size Sensitivity")
    print("=" * 60)

    X_tr_imp = _impute_median(X_train_raw)
    X_va_imp = _impute_median(X_val_raw)

    total = len(X_tr_imp)
    fractions = {"25pct": 0.25, "50pct_baseline": 0.50, "100pct": 1.0}

    results = {}
    passed = True
    for label, frac in fractions.items():
        n = max(30, int(total * frac))
        X_sub = X_tr_imp[-n:]   # most recent n rows (chronological)
        y_sub = y_train[-n:]
        print(f"  {label:20s}  n_train={n:,}", end="")
        y_prob = _fit_predict(X_sub, y_sub, X_va_imp)
        imp = _brier_improvement(y_val, y_prob)
        results[label] = {"n_train": n, "brier_improvement": round(imp, 6), "pass": imp > 0}
        print(f"  Δ Brier={imp:+.4f}  {'PASS' if imp > 0 else 'FAIL (Δ Brier ≤ 0)'}")
        if imp <= 0:
            passed = False

    overall = "PASS" if passed else "FAIL"
    print(f"\nST-002 Overall: {overall}")
    return {"st_id": "ST-002", "status": overall, "results": results}


# ---------------------------------------------------------------------------
# ST-003: Regularization C Parameter Sensitivity
# ---------------------------------------------------------------------------


def run_st003(
    X_train_raw: np.ndarray,
    y_train: np.ndarray,
    X_val_raw: np.ndarray,
    y_val: np.ndarray,
) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("ST-003: Regularization (C Parameter) Sensitivity")
    print("=" * 60)

    X_tr_imp = _impute_median(X_train_raw)
    X_va_imp = _impute_median(X_val_raw)

    c_values = [0.01, 0.1, 1.0, 10.0, 100.0]
    results = {}
    best_imp = -np.inf
    for c in c_values:
        y_prob = _fit_predict(X_tr_imp, y_train, X_va_imp, C=c)
        imp = _brier_improvement(y_val, y_prob)
        label = f"C_{c}"
        results[label] = {"C": c, "brier_improvement": round(imp, 6)}
        if imp > best_imp:
            best_imp = imp
        print(f"  C={c:<8.2f}  Δ Brier={imp:+.4f}")

    baseline_imp = results["C_1.0"]["brier_improvement"]
    delta_from_best = abs(baseline_imp - best_imp)
    pass_result = delta_from_best <= PASS_TOLERANCE

    for label, r in results.items():
        r["best_improvement"] = round(best_imp, 6)
        r["delta_from_best"] = round(abs(r["brier_improvement"] - best_imp), 6)

    print(f"\n  C=1.0 (baseline) Δ Brier={baseline_imp:+.4f}  "
          f"best={best_imp:+.4f}  delta={delta_from_best:.4f}  "
          f"{'PASS (C=1.0 within 0.005 of best)' if pass_result else 'FAIL — C should be tuned'}")

    overall = "PASS" if pass_result else "FAIL"
    print(f"\nST-003 Overall: {overall}")
    return {"st_id": "ST-003", "status": overall, "results": results, "best_C_improvement": round(best_imp, 6)}


# ---------------------------------------------------------------------------
# ST-004: Permutation Feature Importance
# ---------------------------------------------------------------------------


def run_st004(
    X_train_raw: np.ndarray,
    y_train: np.ndarray,
    X_val_raw: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str],
    n_repeats: int = 5,
) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("ST-004: Permutation Feature Importance")
    print("=" * 60)

    X_tr_imp = _impute_median(X_train_raw)
    X_va_imp = _impute_median(X_val_raw)

    # Fit baseline model
    base_proba = _fit_predict(X_tr_imp, y_train, X_va_imp)
    base_brier = float(brier_score_loss(y_val, base_proba))
    print(f"  Baseline Brier = {base_brier:.4f}")

    rng = np.random.default_rng(42)
    importances: dict[str, float] = {}

    for i, feat in enumerate(feature_names):
        deltas = []
        for _ in range(n_repeats):
            X_va_perm = X_va_imp.copy()
            rng.shuffle(X_va_perm[:, i])
            perm_proba = _fit_predict(X_tr_imp, y_train, X_va_perm)
            # Positive delta = shuffling hurts (feature was helping)
            deltas.append(float(brier_score_loss(y_val, perm_proba)) - base_brier)
        importances[feat] = round(float(np.mean(deltas)), 6)

    # Rank by absolute importance (positive = feature is meaningful)
    ranked = sorted(importances.items(), key=lambda kv: kv[1], reverse=True)

    # Compute share of total positive importance
    total_positive_imp = sum(v for v in importances.values() if v > 0)
    if total_positive_imp == 0:
        total_positive_imp = 1e-9  # avoid div-by-zero

    print(f"\n  Top 10 features by permutation importance (Δ Brier when shuffled):")
    max_share = 0.0
    max_feat = ""
    for feat, imp in ranked[:10]:
        share = max(0.0, imp) / total_positive_imp
        if share > max_share:
            max_share = share
            max_feat = feat
        print(f"    {feat:45s}  Δ Brier={imp:+.4f}  share={share:.1%}")

    print(f"\n  Dominant feature: '{max_feat}' with {max_share:.1%} share of positive importance")
    pass_result = max_share <= 0.50
    overall = "PASS" if pass_result else "FAIL"
    print(f"  Pass criterion (< 50%): {overall}")

    results = {
        "baseline_brier": round(base_brier, 6),
        "n_features": len(feature_names),
        "n_permutation_repeats": n_repeats,
        "dominant_feature": max_feat,
        "dominant_feature_share": round(max_share, 4),
        "total_positive_importance": round(total_positive_imp, 6),
        "feature_importances": {k: v for k, v in ranked},
        "pass": pass_result,
    }

    print(f"\nST-004 Overall: {overall}")
    return {"st_id": "ST-004", "status": overall, "results": results}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sensitivity and Stress Tests ST-001–ST-004")
    parser.add_argument(
        "--feature-csv",
        type=Path,
        default=Path("exp_output/EXP-001/EXP-001_feature_matrix.csv"),
        help="Path to pre-computed feature matrix CSV (default: exp_output/EXP-001/EXP-001_feature_matrix.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("exp_output/SENSITIVITY_TESTS"),
        help="Directory to write test results JSON (default: exp_output/SENSITIVITY_TESTS/)",
    )
    args = parser.parse_args(argv)

    print(f"\n{'='*60}")
    print("SENSITIVITY & STRESS TESTS — ST-001 through ST-004")
    print(f"Run at: {_utc_now()}")
    print(f"Feature CSV: {args.feature_csv}")
    print(f"{'='*60}")

    if not args.feature_csv.exists():
        print(f"ERROR: Feature CSV not found: {args.feature_csv}", file=sys.stderr)
        print("Run EXP-001 first: PYTHONPATH=src .venv/bin/python3 -m prediction_market_bot.run_exp001 --no-api", file=sys.stderr)
        sys.exit(1)

    # Load data
    X_train_raw, y_train, X_val_raw, y_val, feature_names, train_df, val_df = (
        load_feature_data(args.feature_csv)
    )

    # Run tests
    results = {}
    results["ST-001"] = run_st001(X_train_raw, y_train, X_val_raw, y_val, train_df, val_df, feature_names)
    results["ST-002"] = run_st002(X_train_raw, y_train, X_val_raw, y_val)
    results["ST-003"] = run_st003(X_train_raw, y_train, X_val_raw, y_val)
    results["ST-004"] = run_st004(X_train_raw, y_train, X_val_raw, y_val, feature_names)

    # Summary
    print(f"\n{'='*60}")
    print("SENSITIVITY TEST SUMMARY")
    print(f"{'='*60}")
    all_pass = True
    for st_id, result in results.items():
        status = result["status"]
        print(f"  {st_id}: {status}")
        if status != "PASS":
            all_pass = False

    overall = "ALL PASS" if all_pass else "SOME FAILED — review results"
    print(f"\nOverall: {overall}")

    # Write results
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "sensitivity_test_results.json"
    summary = {
        "run_at": _utc_now(),
        "feature_csv": str(args.feature_csv),
        "feature_version": FEATURE_VERSION_TARGET,
        "baseline_brier_improvement_g4": BASELINE_BRIER_IMPROVEMENT,
        "overall": overall,
        "tests": results,
    }
    output_path.write_text(json.dumps(summary, indent=2))
    print(f"\nResults written to: {output_path}")


if __name__ == "__main__":
    main()

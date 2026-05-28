"""
EXP-006: Qualitative Signal Brier Measurement (DS-01 PAM — QS-2026-05-28-001)
===============================================================================
Experiment ID:   EXP-006
Phase:           Phase 6 Planning (qualitative feature integration)
Status:          CANONICAL RUNNER — 2026-05-28
Hypothesis:      Do PAM v4 qualitative features (PRF archetypes + modifiers)
                 improve Brier score vs the quantitative-only EXP-005 baseline?

Design:
  Reuses EXP-005 feature matrix (SNAP-2026-05-28-002, cached CSV) — no API pull.
  Enriches with DS-01 PAM qualitative features via QualitativeSignalStore.
  Runs C3 with combined feature set (31 quantitative + 35 qualitative = 66 features).
  Compares TEST Brier vs EXP-005 baseline (+0.0024 improvement).

Known limitation — effective_from constraint:
  QS-2026-05-28-001 has effective_from = 2025-10-22 (start of 2025-26 season).
  EXP-005 TRAIN/VAL cover games through 2025-04-13 — all before effective_from.
  Qualitative features are therefore NaN for all TRAIN and VAL rows.
  After all-NaN column imputation (0.0 fallback), the model trains on qualitative
  features as all-zero columns → L2 regularisation pushes their coefficients to ~0.
  At TEST time (2025-26 games), qualitative values are real — but the model has
  near-zero coefficients for them. Expected result: Brier Δ ≈ 0 vs EXP-005.

  This measurement is valid — it documents what the current QS snapshot produces
  given the temporal integrity constraints. The finding informs whether backdated
  classifications (QTI-03) are needed to activate qualitative signal in training.

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp006.py

    Requires: exp_output/EXP-005/EXP-005_feature_matrix.csv (from EXP-005 run)
              qualitative_data/pam_v4/QS-2026-05-28-001_classifications.csv

Security (NFR-05, NFR-07):
    - No API keys required (uses cached feature matrix).
    - BOT_C4_ACTIVE must NOT be set.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore,
    DS01_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXP_ID = "EXP-006"
SESSION_ID = f"EXP-006-{uuid.uuid4().hex[:8].upper()}"

# Reuse EXP-005 cached feature matrix (no API call needed)
FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV = Path("qualitative_data/pam_v4/QS-2026-05-28-001_classifications.csv")
QS_ID = "QS-2026-05-28-001"
OUTPUT_DIR = Path("exp_output/EXP-006")

# Same split as EXP-005
TRAIN_END_DATE = "2025-02-28"
VAL_END_DATE = "2025-04-13"
FEATURE_WINDOW = 10

# EXP-005 baseline for comparison
EXP005_TEST_BRIER = 0.2476
EXP005_TEST_IMPROVEMENT = 0.0024
NULL_BRIER = 0.2500

SNAPSHOT_ID = "SNAP-2026-05-28-002"  # same game-log snapshot as EXP-005

# Non-feature columns (same as EXP-005)
_PRUNED_V110 = {
    "season_type_is_playoffs", "days_since_last_game", "b2b_flag",
    "load_games_l7d", "eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games",
}
_NON_FEATURE_BASE = {
    "player_id", "player_name", "team_id", "team_abbreviation",
    "game_id", "game_date", "season", "season_type",
    "min", "pts", "reb", "ast", "stl", "blk", "tov", "pf",
    "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct",
    "ftm", "fta", "ft_pct", "plus_minus",
    "snapshot_id", "ingestion_run_id", "ingested_at",
    "temporal_cutoff", "feature_run_id", "feature_version",
    "train_test_label", "y_target",
} | _PRUNED_V110


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan] * len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    prior_mean = pd.to_numeric(df[col], errors="coerce")
    target = (pts >= prior_mean).astype("Int8")
    target[pts.isna() | prior_mean.isna()] = pd.NA
    return target


def _impute_median(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    col_medians = np.nanmedian(X, axis=0)
    # All-NaN columns fall back to 0 (e.g. qualitative features absent from TRAIN)
    col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)
    mask = np.isnan(X)
    X[mask] = np.take(col_medians, np.where(mask)[1])
    return X


def _fit_model(X_train: np.ndarray, y_train: np.ndarray) -> Pipeline:
    base = LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=1000,
        random_state=42, class_weight="balanced",
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def _compute_ece(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    y_p = np.clip(y_prob, 1e-6, 1 - 1e-6)
    frac_pos, mean_pred = calibration_curve(y_true, y_p, n_bins=10, strategy="uniform")
    counts = np.histogram(y_p, bins=10, range=(0.0, 1.0))[0]
    counts = counts[counts > 0]
    n = min(len(frac_pos), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac_pos[:n] - mean_pred[:n])))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR / "audit_exp006.jsonl"
    logger = AuditLogger(log_path=log_path, min_severity="DEBUG")

    print(f"\n{'='*60}")
    print(f"EXP-006: Qualitative Signal Brier Measurement")
    print(f"Session: {SESSION_ID}")
    print(f"QS snapshot: {QS_ID}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 1. Load feature matrix (cached from EXP-005 — no API call)
    # ------------------------------------------------------------------
    if not FEATURE_CSV.exists():
        print(f"ERROR: Feature CSV not found: {FEATURE_CSV}", file=sys.stderr)
        print("Run EXP-005 first to generate the feature matrix.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] Loaded {len(df):,} rows from {FEATURE_CSV}")

    # ------------------------------------------------------------------
    # 2. Load and apply qualitative enrichment
    # ------------------------------------------------------------------
    print(f"\n[QS] Loading DS-01 snapshot {QS_ID}...")
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)

    ok = qs.load_ds01_snapshot(
        csv_path=QS_CSV,
        qs_id=QS_ID,
        session_id=SESSION_ID,
    )
    if not ok:
        print("ERROR: Failed to load QS snapshot.", file=sys.stderr)
        sys.exit(1)
    print(f"[QS] Loaded {QS_ID} — {len(qs._ds01_df)} player classifications")

    ok, df_enriched = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: QS enrichment failed.", file=sys.stderr)
        sys.exit(1)

    # Count how many rows received qualitative features vs NaN
    game_dates = pd.to_datetime(df_enriched["game_date"], errors="coerce")
    eff_from = pd.Timestamp("2025-10-22")
    n_with_qual = int((game_dates >= eff_from).sum())
    n_without_qual = int((game_dates < eff_from).sum())
    print(f"[QS] Rows with qualitative features (game_date >= {eff_from.date()}): {n_with_qual:,}")
    print(f"[QS] Rows with NaN qualitative (game_date < {eff_from.date()}): {n_without_qual:,}")

    # ------------------------------------------------------------------
    # 3. Build feature name lists
    # ------------------------------------------------------------------
    qual_feature_names = qs.get_qualitative_feature_names()
    quant_feature_names = [
        c for c in df_enriched.columns
        if c not in _NON_FEATURE_BASE
        and c not in set(qual_feature_names)
    ]
    all_feature_names = quant_feature_names + qual_feature_names

    print(f"\n[FEATURES] Quantitative: {len(quant_feature_names)}")
    print(f"[FEATURES] Qualitative:  {len(qual_feature_names)}")
    print(f"[FEATURES] Total:        {len(all_feature_names)}")

    # ------------------------------------------------------------------
    # 4. Build target + splits
    # ------------------------------------------------------------------
    df_enriched["y_target"] = _build_target(df_enriched)
    usable = df_enriched[
        df_enriched["y_target"].notna() & df_enriched["temporal_cutoff"].notna()
    ].copy()

    train_df = usable[usable["train_test_label"] == "TRAIN"].copy()
    val_df = usable[usable["train_test_label"] == "VALIDATION"].copy()
    test_df = usable[usable["train_test_label"] == "TEST"].copy()

    print(f"\n[SPLIT] TRAIN: {len(train_df):,} | VAL: {len(val_df):,} | TEST: {len(test_df):,}")

    # Count non-NaN qualitative values in each split (diagnostic)
    prf_col = "prf_primary"
    if prf_col in train_df.columns:
        train_qual_filled = int(train_df[prf_col].notna().sum())
        val_qual_filled = int(val_df[prf_col].notna().sum())
        test_qual_filled = int(test_df[prf_col].notna().sum())
        print(f"[QS] Non-NaN prf_primary — TRAIN: {train_qual_filled} | VAL: {val_qual_filled} | TEST: {test_qual_filled}")

    # ------------------------------------------------------------------
    # 5. Fit and evaluate — combined feature set (66 features)
    # ------------------------------------------------------------------
    print(f"\n[MODEL] Fitting on TRAIN ({len(all_feature_names)} features)...")
    X_train = _impute_median(train_df[all_feature_names].to_numpy(dtype=float))
    y_train = train_df["y_target"].astype(int).to_numpy()
    model = _fit_model(X_train, y_train)
    print("[MODEL] Fit complete.")

    print(f"\n[EVAL] Predicting on TEST ({len(test_df):,} rows)...")
    X_test = _impute_median(test_df[all_feature_names].to_numpy(dtype=float))
    y_test = test_df["y_target"].astype(int).to_numpy()
    p_test = model.predict_proba(X_test)[:, 1]

    brier = float(brier_score_loss(y_test, p_test))
    brier_improvement = NULL_BRIER - brier
    ece = _compute_ece(y_test, p_test)
    auc = float(roc_auc_score(y_test, p_test))

    # Also evaluate quantitative-only baseline on same split (control)
    print(f"[EVAL] Predicting quantitative-only baseline (control)...")
    X_train_quant = _impute_median(train_df[quant_feature_names].to_numpy(dtype=float))
    model_quant = _fit_model(X_train_quant, y_train)
    X_test_quant = _impute_median(test_df[quant_feature_names].to_numpy(dtype=float))
    p_test_quant = model_quant.predict_proba(X_test_quant)[:, 1]
    brier_quant = float(brier_score_loss(y_test, p_test_quant))
    ece_quant = _compute_ece(y_test, p_test_quant)
    auc_quant = float(roc_auc_score(y_test, p_test_quant))

    # ------------------------------------------------------------------
    # 6. Results
    # ------------------------------------------------------------------
    delta_brier = brier_quant - brier  # positive = qualitative features help
    delta_ece = ece_quant - ece        # positive = qualitative features improve calibration

    print(f"\n{'='*60}")
    print("EXP-006 RESULTS — QUALITATIVE SIGNAL BRIER MEASUREMENT")
    print(f"{'='*60}")
    print(f"Feature set:          {len(all_feature_names)} total ({len(quant_feature_names)} quant + {len(qual_feature_names)} qual)")
    print(f"QS snapshot:          {QS_ID}")
    print(f"Qualitative eff_from: 2025-10-22 (2025-26 season only)")
    print(f"\nTEST set (2025-26 regular season, n={len(test_df):,}):")
    print(f"                    {'QUANT ONLY':>12}  {'QUANT+QUAL':>12}  {'DELTA':>10}")
    print(f"  Brier score:      {brier_quant:>12.4f}  {brier:>12.4f}  {delta_brier:>+10.4f}")
    print(f"  Brier improvement:{NULL_BRIER - brier_quant:>+12.4f}  {brier_improvement:>+12.4f}")
    print(f"  ECE:              {ece_quant:>12.4f}  {ece:>12.4f}  {delta_ece:>+10.4f}")
    print(f"  AUC-ROC:          {auc_quant:>12.4f}  {auc:>12.4f}  {auc - auc_quant:>+10.4f}")
    print(f"\nEXP-005 baseline (same test set, quant only): Brier {EXP005_TEST_BRIER:.4f}")
    print(f"Qual feature signal:  {'POSITIVE' if delta_brier > 0.0005 else 'NEGLIGIBLE' if abs(delta_brier) <= 0.0005 else 'NEGATIVE'}")

    print(f"\nFINDING:")
    if abs(delta_brier) <= 0.0005:
        print(
            f"  Qualitative features add negligible Brier signal (Δ={delta_brier:+.4f}).\n"
            f"  Root cause: effective_from=2025-10-22 means all TRAIN rows have NaN\n"
            f"  qualitative features. After 0-imputation, LR regularisation drives\n"
            f"  qualitative coefficients to ~0. Features are real in TEST but\n"
            f"  untrained — model cannot exploit them.\n"
            f"  Next step: backdate QS classifications (QTI-03) with per-player\n"
            f"  rationale so training rows carry qualitative signal."
        )
    elif delta_brier > 0:
        print(f"  Qualitative features IMPROVE Brier by {delta_brier:+.4f}.")
    else:
        print(f"  Qualitative features HURT Brier by {delta_brier:+.4f} — investigate.")

    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 7. Save results
    # ------------------------------------------------------------------
    output = {
        "exp_id": EXP_ID,
        "session_id": SESSION_ID,
        "run_at": _utc_now(),
        "qs_id": QS_ID,
        "qs_effective_from": "2025-10-22",
        "feature_counts": {
            "quantitative": len(quant_feature_names),
            "qualitative": len(qual_feature_names),
            "total": len(all_feature_names),
        },
        "split": {
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "test_rows": len(test_df),
            "train_rows_with_qual_features": train_qual_filled if prf_col in train_df.columns else 0,
            "test_rows_with_qual_features": test_qual_filled if prf_col in test_df.columns else 0,
        },
        "quant_only_baseline": {
            "brier": round(brier_quant, 6),
            "brier_improvement": round(NULL_BRIER - brier_quant, 6),
            "ece": round(ece_quant, 6),
            "auc_roc": round(auc_quant, 6),
        },
        "quant_plus_qual": {
            "brier": round(brier, 6),
            "brier_improvement": round(brier_improvement, 6),
            "ece": round(ece, 6),
            "auc_roc": round(auc, 6),
        },
        "delta": {
            "brier": round(delta_brier, 6),
            "ece": round(delta_ece, 6),
            "auc_roc": round(auc - auc_quant, 6),
        },
        "exp005_baseline_brier": EXP005_TEST_BRIER,
        "null_brier": NULL_BRIER,
        "finding": (
            "negligible_signal_effective_from_constraint"
            if abs(delta_brier) <= 0.0005
            else "positive_signal" if delta_brier > 0
            else "negative_signal"
        ),
    }

    out_path = OUTPUT_DIR / "EXP-006_results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr)
        sys.exit(1)
    main()

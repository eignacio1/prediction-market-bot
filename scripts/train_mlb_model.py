"""
T-183 — MLB C3 Model Training (ADR-0004 / ADR-0031)
=====================================================

Script ID:    T-183
ADR:          ADR-0004 (LR + Platt scaling); ADR-0031 (multi-sport)
Status:       CANONICAL — run once per MLB_FEATURE_VERSION bump
Feature ver:  1.0.0 (MLB_FEATURE_VERSION in mlb_features.py)
Base data:    exp_output/MLB/mlb_feature_matrix.csv  (C1→C2 offline run)
Output:       models/mlb_v1_model.joblib, models/mlb_v1_model_meta.json

Target variable
---------------
MLB hits markets (KXMLBHIT) offer thresholds: 1+, 2+, 3+ hits per game.
Each game row is expanded to one row per threshold:
    y_target  = 1 if actual_h >= threshold else 0  (Int8 / NA when h is missing)
    threshold = the threshold k as a float feature in the LR model

A single LR model scores any threshold at inference time by passing the
threshold value in the feature vector.  The model learns:
    P(hits >= k | batter features, k)

Shadow gate (ADR-0009 criteria — BOTH must pass before deployment):
  1. Brier(model) < Brier(null_baseline) - 0.001
     Null baseline: always predict the holdout class prior (mean(y_holdout)).
     No prior MLB model exists; the baseline is the naive constant predictor.
  2. ECE(model, 10 equal-frequency bins) <= 0.05

Holdout (anti-gaming — fixed before training begins):
  game_date > 2026-01-01  (2026 MLB season data)
  MUST NOT change once committed to DECISION_LOG.

Architecture note (ADR-0031)
-----------------------------
C3 remains sport-agnostic at the class level (ModelForecaster).
This script is the sport-specific training path for MLB.
The saved artifact {"pipeline", "col_medians", "feature_names", "model_version"}
is consumed at inference by ModelForecaster.fit() loading the serialized pipeline,
matching the NBA artifact schema produced by train_and_save_model.py.

How to run:
    PYTHONPATH=src .venv/bin/python3 scripts/train_mlb_model.py
    PYTHONPATH=src .venv/bin/python3 scripts/train_mlb_model.py --dry-run
    PYTHONPATH=src .venv/bin/python3 scripts/train_mlb_model.py --csv path/to/matrix.csv

Security:
  - BOT_C4_ACTIVE must NOT be set (frozen model policy — ADR-0004).
  - No venue API calls.
  - No hardcoded secrets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_SRC_ROOT = Path(__file__).parent.parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FEATURE_CSV = Path("exp_output/MLB/mlb_feature_matrix.csv")
MODEL_DIR = Path("models")
MLB_V1_MODEL_PATH = MODEL_DIR / "mlb_v1_model.joblib"
MLB_V1_META_PATH = MODEL_DIR / "mlb_v1_model_meta.json"

FEATURE_VERSION = "1.0.0"
THRESHOLDS: list[int] = [1, 2, 3]
HOLDOUT_CUTOFF = "2026-01-01"  # Fixed before training — do not change

SHADOW_GATE_BRIER_DELTA = 0.001
SHADOW_GATE_ECE_MAX = 0.05
MIN_TRAIN_SAMPLES = 30
MIN_HOLDOUT_SAMPLES = 10

# Columns that must never enter the feature matrix.
# "h" is the raw hit count — it is the outcome; using it would be data leakage.
# All other raw box-score columns from C1 are also excluded.
_NON_FEATURE_MLB: frozenset[str] = frozenset({
    # Identity / metadata (IF-C2-C3 _ID_COLUMNS)
    "player_id", "player_name", "team_abbreviation",
    "game_id", "game_date",
    "season", "season_type", "matchup", "opponent_team_abbr",
    "snapshot_id", "feature_run_id", "feature_version",
    "temporal_cutoff", "train_test_label",
    # C1 ingestion audit columns
    "ingestion_run_id", "ingested_at",
    # Raw box-score outcomes — target basis; must not enter feature matrix
    "ab", "h", "doubles", "triples", "hr", "rbi", "bb", "k", "hbp", "sf",
    # Training artifacts
    "y_target",
    # Temporal helper
    "game_date_dt",
})


# ---------------------------------------------------------------------------
# Helpers (importable by tests)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _mlb_model_version(feature_names: list[str]) -> str:
    """Deterministic version hash for a given MLB feature set."""
    digest = "LogisticRegression+PlattScaling|MLB|" + ",".join(sorted(feature_names))
    return "mlb-v1-" + hashlib.sha1(digest.encode()).hexdigest()[:8]


def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    """Replace NaN entries with column medians (in-place copy)."""
    X = X.copy().astype(float)
    mask = np.isnan(X)
    if mask.any():
        # nanmedian falls back to 0.0 for all-NaN columns
        safe_medians = np.where(np.isnan(medians), 0.0, medians)
        X[mask] = np.take(safe_medians, np.where(mask)[1])
    return X


def _compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error using equal-frequency bins (ADR-0009)."""
    order = np.argsort(y_prob)
    y_true_sorted = y_true[order]
    y_prob_sorted = y_prob[order]
    bins = np.array_split(np.arange(len(y_prob)), n_bins)
    ece = 0.0
    n = len(y_prob)
    for b in bins:
        if len(b) == 0:
            continue
        ece += (len(b) / n) * abs(float(y_true_sorted[b].mean()) - float(y_prob_sorted[b].mean()))
    return float(ece)


def _build_mlb_target(
    df: pd.DataFrame,
    thresholds: list[int] = THRESHOLDS,
) -> pd.DataFrame:
    """Expand each game row to one row per threshold.

    Adds:
        threshold  — float; the hits threshold k (1.0 / 2.0 / 3.0)
        y_target   — Int8; 1 if h >= threshold, 0 otherwise, NA when h is NaN

    The expanded DataFrame has len(df) * len(thresholds) rows.
    """
    h = pd.to_numeric(
        df["h"] if "h" in df.columns else pd.Series([np.nan] * len(df), index=df.index),
        errors="coerce",
    )
    chunks: list[pd.DataFrame] = []
    for t in thresholds:
        chunk = df.copy()
        chunk["threshold"] = float(t)
        target = (h >= t).astype("Int8")
        target[h.isna()] = pd.NA
        chunk["y_target"] = target
        chunks.append(chunk)
    if not chunks:
        return df.copy()
    return pd.concat(chunks, ignore_index=True)


def _extract_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Return (X, feature_names) after excluding _NON_FEATURE_MLB columns.

    feature_names is sorted alphabetically for deterministic model versioning.
    """
    feature_cols = sorted(c for c in df.columns if c not in _NON_FEATURE_MLB)
    X = df[feature_cols].to_numpy(dtype=np.float64)
    return X, feature_cols


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(
    csv_path: Path = FEATURE_CSV,
    dry_run: bool = False,
    force_save: bool = False,
    model_path: Path = MLB_V1_MODEL_PATH,
    meta_path: Path = MLB_V1_META_PATH,
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(str(model_path.parent / "train_mlb_v1.jsonl"), min_severity="INFO")
    session_id = f"TRAIN-MLB-V1-{uuid.uuid4().hex[:8].upper()}"

    print(f"\n{'='*65}")
    print("T-183 — MLB C3 Model Training (ADR-0004 / ADR-0031)")
    print(f"Session:     {session_id}")
    print(f"Feature ver: {FEATURE_VERSION}")
    print(f"Thresholds:  {THRESHOLDS}")
    print(f"Holdout:     game_date > {HOLDOUT_CUTOFF}")
    if dry_run:
        print("MODE: DRY RUN — model will not be saved")
    print(f"{'='*65}\n")

    # Guards
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — refusing to run.", file=sys.stderr)
        sys.exit(1)

    if not csv_path.exists():
        print(f"ERROR: Feature matrix not found at {csv_path}.", file=sys.stderr)
        sys.exit(1)

    # 1. Load feature matrix
    print("[1/8] Loading feature matrix...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"      {len(df):,} rows loaded")
    df["game_date"] = pd.to_datetime(df["game_date"])

    # 2. Filter: exclude rows with no prior games (temporal_cutoff = NaT / None)
    #    These rows have no rolling features and must not enter train or holdout.
    print("[2/8] Filtering to rows with valid temporal_cutoff...")
    if "temporal_cutoff" in df.columns:
        valid_df = df[df["temporal_cutoff"].notna()].copy()
    else:
        valid_df = df.copy()
    print(f"      {len(valid_df):,} valid rows (of {len(df):,})")

    # 3. Expand to (game, threshold) pairs
    print("[3/8] Expanding to threshold rows...")
    expanded = _build_mlb_target(valid_df, THRESHOLDS)
    print(f"      {len(expanded):,} expanded rows ({len(valid_df):,} × {len(THRESHOLDS)} thresholds)")

    # 4. Split: train / holdout (HOLDOUT_CUTOFF fixed anti-gaming — do not change)
    print(f"[4/8] Splitting on HOLDOUT_CUTOFF = {HOLDOUT_CUTOFF}...")
    game_dates = pd.to_datetime(expanded["game_date"])
    train_mask = (game_dates <= pd.Timestamp(HOLDOUT_CUTOFF)) & expanded["y_target"].notna()
    holdout_mask = (game_dates > pd.Timestamp(HOLDOUT_CUTOFF)) & expanded["y_target"].notna()

    train_df = expanded[train_mask].copy()
    holdout_df = expanded[holdout_mask].copy()
    print(f"      Train:   {len(train_df):,} rows")
    print(f"      Holdout: {len(holdout_df):,} rows")

    if len(train_df) < MIN_TRAIN_SAMPLES:
        print(
            f"ERROR: Insufficient training samples: {len(train_df)} < {MIN_TRAIN_SAMPLES}.",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(holdout_df) < MIN_HOLDOUT_SAMPLES:
        print(
            f"ERROR: Insufficient holdout samples: {len(holdout_df)} < {MIN_HOLDOUT_SAMPLES}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 5. Build feature matrices
    print("[5/8] Building feature matrices...")
    X_train, feature_names = _extract_feature_matrix(train_df)
    X_holdout, _ = _extract_feature_matrix(holdout_df)

    y_train = train_df["y_target"].astype(int).to_numpy()
    y_holdout = holdout_df["y_target"].astype(int).to_numpy()

    col_medians = np.nanmedian(X_train, axis=0)
    X_train = _impute(X_train, col_medians)
    X_holdout = _impute(X_holdout, col_medians)
    print(f"      Features: {len(feature_names)}")

    model_version = _mlb_model_version(feature_names)

    # 6. Fit: StandardScaler → CalibratedClassifierCV(LR, cv=3, sigmoid)
    #    Matches forecaster.py pipeline (ADR-0004).
    print("[6/8] Fitting LR + Platt calibration (ADR-0004)...")
    base_clf = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=1000,
        random_state=42,
        class_weight="balanced",
    )
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base_clf, method="sigmoid", cv=3)),
    ])
    pipe.fit(X_train, y_train)

    # 7. Evaluate shadow gate (ADR-0009)
    print("[7/8] Evaluating shadow gate (ADR-0009)...")
    y_prob = pipe.predict_proba(X_holdout)[:, 1]

    brier_model = float(brier_score_loss(y_holdout, y_prob))
    null_positive_rate = float(y_holdout.mean())
    brier_null = float(brier_score_loss(y_holdout, np.full_like(y_prob, null_positive_rate)))
    brier_delta = brier_null - brier_model

    ece = _compute_ece(y_holdout, y_prob)
    auc = (
        float(roc_auc_score(y_holdout, y_prob))
        if len(np.unique(y_holdout)) > 1
        else float("nan")
    )

    gate_brier = brier_delta >= SHADOW_GATE_BRIER_DELTA
    gate_ece = ece <= SHADOW_GATE_ECE_MAX
    gate_pass = gate_brier and gate_ece

    print(f"      Brier(model):  {brier_model:.4f}")
    print(f"      Brier(null):   {brier_null:.4f}")
    print(f"      Brier delta:   {brier_delta:+.4f}  (need >= +{SHADOW_GATE_BRIER_DELTA})")
    print(f"      ECE:           {ece:.4f}  (need <= {SHADOW_GATE_ECE_MAX})")
    print(f"      AUC-ROC:       {auc:.4f}")
    print(f"\n      Brier gate:  {'PASS' if gate_brier else 'FAIL'}")
    print(f"      ECE gate:    {'PASS' if gate_ece else 'FAIL'}")
    print(f"      Shadow gate: {'PASS' if gate_pass else 'FAIL'}")

    if not gate_pass and not force_save:
        logger.log(
            "C3_MLB",
            "mlb_shadow_gate_fail",
            payload={
                "model_version": model_version,
                "brier_model": round(brier_model, 6),
                "brier_null": round(brier_null, 6),
                "brier_delta": round(brier_delta, 6),
                "ece": round(ece, 4),
                "gate_brier": gate_brier,
                "gate_ece": gate_ece,
            },
            session_id=session_id,
            severity="ERROR",
        )
        print(
            "\nFATAL: Shadow gate FAIL — model NOT saved. T-183 remains OPEN.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not gate_pass and force_save:
        print("\nWARNING: Shadow gate FAIL — saving with --force-save (not for production use).")

    # 8. Save
    if dry_run:
        print("\n[8/8] Dry run — model NOT saved.")
    else:
        print("\n[8/8] Saving model artifact...")
        artifact = {
            "pipeline": pipe,
            "feature_names": feature_names,
            "col_medians": col_medians,
            "model_version": model_version,
            "thresholds": THRESHOLDS,
            "sport": "mlb",
        }
        joblib.dump(artifact, model_path)

        meta = {
            "model_version": model_version,
            "feature_version": FEATURE_VERSION,
            "model_class": "LogisticRegression+PlattScaling (ADR-0004)",
            "sport": "mlb",
            "thresholds": THRESHOLDS,
            "feature_names": feature_names,
            "feature_count": len(feature_names),
            "holdout_cutoff": HOLDOUT_CUTOFF,
            "trained_at": _utc_now(),
            "session_id": session_id,
            "train_rows": int(len(train_df)),
            "holdout_rows": int(len(holdout_df)),
            "null_positive_rate": round(null_positive_rate, 6),
            "brier_model": round(brier_model, 6),
            "brier_null": round(brier_null, 6),
            "brier_delta": round(brier_delta, 6),
            "ece": round(ece, 4),
            "auc_roc": round(auc, 4) if not np.isnan(auc) else None,
            "shadow_gate_pass": gate_pass,
            "shadow_gate_brier_delta_required": SHADOW_GATE_BRIER_DELTA,
            "shadow_gate_ece_max": SHADOW_GATE_ECE_MAX,
            "adr": "ADR-0004",
        }
        meta_path.write_text(json.dumps(meta, indent=2))

        print(f"      Saved: {model_path}")
        print(f"      Saved: {meta_path}")

        logger.log(
            "C3_MLB",
            "mlb_model_trained",
            payload=meta,
            session_id=session_id,
        )

    print(f"\n{'='*65}")
    print("T-183 COMPLETE" if not dry_run else "T-183 DRY RUN COMPLETE")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MLB C3 model (T-183 / ADR-0004)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate pipeline without saving model artifact",
    )
    parser.add_argument(
        "--force-save",
        action="store_true",
        help="Save even if shadow gate fails (development only — not for production)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=FEATURE_CSV,
        help="Feature matrix CSV path (default: exp_output/MLB/mlb_feature_matrix.csv)",
    )
    args = parser.parse_args()
    main(csv_path=args.csv, dry_run=args.dry_run, force_save=args.force_save)

"""
Production Model Training + Serialization
==========================================
Purpose:  Train the production L1+L2 model (78 features) on the full dataset
          and serialize it to models/prod_model.joblib for use by the pre-game
          runner on VPS. Run once locally or on VPS after initial data pull.

Model:    LR + Platt scaling (ADR-0004)
Features: 31 quantitative (F-001–F-031) + 47 qualitative (QS-2026-05-28-002)
Input:    exp_output/EXP-005/EXP-005_feature_matrix.csv (5-season data)
Output:   models/prod_model.joblib + models/prod_model_meta.json

Governance:
  - Class B change: new artifact registered in ARTIFACT_REGISTRY.md
  - Model version: deterministic hash of feature names + model class (same as EXP-008)
  - Frozen once serialized: no retraining without new EXP + ADR amendment

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/train_and_save_model.py
"""

from __future__ import annotations

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

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore, DS01_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

FEATURE_CSV  = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV       = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID        = "QS-2026-05-28-002"
MODEL_DIR    = Path("models")
MODEL_PATH   = MODEL_DIR / "prod_model.joblib"
META_PATH    = MODEL_DIR / "prod_model_meta.json"
SNAPSHOT_ID  = "SNAP-2026-05-28-002"
FEATURE_WINDOW = 10

_PRUNED_V110 = {
    "season_type_is_playoffs","days_since_last_game","b2b_flag",
    "load_games_l7d","eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
}
_NON_FEATURE = {
    "player_id","player_name","team_id","team_abbreviation",
    "game_id","game_date","season","season_type",
    "matchup","opponent_team_abbr",  # EXP-012 columns — not model features
    "min","pts","reb","ast","stl","blk","tov","pf",
    "fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm","fta","ft_pct","plus_minus",
    "snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    "prf_primary","prf_secondary","prf_hybrid_weight",
} | _PRUNED_V110


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def _model_version(feature_names: list[str]) -> str:
    digest = "LogisticRegression+PlattScaling|" + ",".join(sorted(feature_names))
    return "v1-" + hashlib.sha1(digest.encode()).hexdigest()[:8]

def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X

def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan]*len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df[col], errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return t


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger("logs/train_model.jsonl", min_severity="INFO")
    session_id = f"TRAIN-{uuid.uuid4().hex[:8].upper()}"

    print(f"\n{'='*60}")
    print(f"Production Model Training + Serialization")
    print(f"Session: {session_id}")
    print(f"{'='*60}\n")

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load + enrich
    # ------------------------------------------------------------------
    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows")

    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=session_id):
        print("ERROR: QS load failed", file=sys.stderr); sys.exit(1)
    ok, df_q = qs.enrich_features(df, session_id=session_id)
    if not ok:
        print("ERROR: enrichment failed", file=sys.stderr); sys.exit(1)

    qual_names  = qs.get_qualitative_feature_names()
    quant_names = [c for c in df_q.columns
                   if c not in _NON_FEATURE and c not in set(qual_names)]
    feature_names = quant_names + qual_names
    print(f"[FEATURES] {len(feature_names)} total ({len(quant_names)} quant + {len(qual_names)} qual)")

    # ------------------------------------------------------------------
    # 2. Train on ALL usable rows (TRAIN + VALIDATION — TEST not touched)
    #    Rationale: for deployment we train on the maximum historical data
    #    while still holding TEST out for future auditing.
    # ------------------------------------------------------------------
    df_q["y_target"] = _build_target(df_q)
    usable = df_q[df_q["y_target"].notna() & df_q["temporal_cutoff"].notna()].copy()

    train_val = usable[usable["train_test_label"].isin(["TRAIN", "VALIDATION"])].copy()
    test_df   = usable[usable["train_test_label"] == "TEST"].copy()

    print(f"[SPLIT] TRAIN+VAL {len(train_val):,} | TEST (held) {len(test_df):,}")

    X_raw = train_val[feature_names].to_numpy(dtype=float)
    y_tr  = train_val["y_target"].astype(int).to_numpy()

    # Compute and store imputation medians (needed at inference time)
    col_medians = np.nanmedian(X_raw, axis=0)
    col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)
    X_tr = _impute(X_raw, col_medians)

    # ------------------------------------------------------------------
    # 3. Fit LR + Platt
    # ------------------------------------------------------------------
    print("[MODEL] Fitting LR + Platt...")
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                               random_state=42, class_weight="balanced")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X_tr, y_tr)

    # In-sample TRAIN+VAL check
    p_tr = pipe.predict_proba(X_tr)[:, 1]
    b_tr = float(brier_score_loss(y_tr, p_tr))
    print(f"[MODEL] Train+Val Brier (in-sample): {b_tr:.4f}")

    model_version = _model_version(feature_names)
    print(f"[MODEL] Version: {model_version}")

    # ------------------------------------------------------------------
    # 4. Serialize model + metadata
    # ------------------------------------------------------------------
    artifact = {
        "pipeline":       pipe,
        "feature_names":  feature_names,
        "col_medians":    col_medians,
        "model_version":  model_version,
        "qs_id":          QS_ID,
        "snapshot_id":    SNAPSHOT_ID,
    }
    joblib.dump(artifact, MODEL_PATH)
    print(f"[SAVE] Model: {MODEL_PATH}  ({MODEL_PATH.stat().st_size / 1024:.0f} KB)")

    meta = {
        "model_version":  model_version,
        "model_class":    "LogisticRegression+PlattScaling (ADR-0004)",
        "feature_count":  len(feature_names),
        "quant_features": len(quant_names),
        "qual_features":  len(qual_names),
        "qs_id":          QS_ID,
        "snapshot_id":    SNAPSHOT_ID,
        "train_rows":     len(train_val),
        "test_rows_held": len(test_df),
        "train_brier_insample": round(b_tr, 6),
        "trained_at":     _utc_now(),
        "session_id":     session_id,
        "feature_names":  feature_names,
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"[SAVE] Metadata: {META_PATH}")

    logger.info("TRAIN", "model_serialized",
                payload={"model_version": model_version, "model_path": str(MODEL_PATH),
                         "feature_count": len(feature_names)},
                session_id=session_id, snapshot_id=SNAPSHOT_ID)

    print(f"\nModel ready for deployment. Register in ARTIFACT_REGISTRY.md before promoting to ENV-02.")
    print(f"Copy to VPS:  scp {MODEL_PATH} {META_PATH} user@<VPS_IP>:/opt/prediction-market-bot/models/\n")


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr); sys.exit(1)
    main()

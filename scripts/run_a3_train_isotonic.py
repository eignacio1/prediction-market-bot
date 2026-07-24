#!/usr/bin/env python3
"""A3 (Window A, GG-105) -- isotonic-recalibration contingency, triggered
because A2's straight LR+Platt refit on the A1 shrunk ba_l10 feature did NOT
clear the calibration gate (edge-tercile direction stayed inverted:
winrate_edge_pos=0.475 < winrate_edge_neg=0.580, candidate_vs_baseline_report.json,
2026-07-24). Per the user's own A2 instruction, the FAIL contingency is
"isotonic/feature expansion superseding ADR-0004; NOT temperature scaling" --
temperature scaling was already ruled out for MAIN's sibling problem (GG-105
memory: "makes tercile anti-predictive pattern worse").

This trains a THIRD variant -- same A1-shrunk-ba_l10 feature CSV as A2's
candidate (exp_output/MLB/a2_refit_full/candidate.csv), same train/holdout
split and shadow-gate discipline as train_mlb_model.py, but swaps
CalibratedClassifierCV(method="sigmoid") for method="isotonic" (ADR-0004's
Platt-scaling choice is what gets superseded here, not the LR base
estimator or the feature set -- this isolates ONE variable change from A2's
candidate, same discipline as A1->A2's own single-variable-swap design,
DECISION_LOG.md commit d12393d).

train_mlb_model.py itself is intentionally NOT imported for its main()/save
path and NOT modified -- only its pure helper functions are reused, to keep
Hard Rule 4 (frozen production training entrypoint, no automated retraining
in production) unambiguous: this script has its own isolated model_path/
meta_path under models/a2_refit/, never touches the live artifact or the
canonical training script.

Run:
  PYTHONPATH=src python3 scripts/run_a3_train_isotonic.py
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_mlb_model as tm  # noqa: E402  reuse pure helpers only, see module docstring

CSV_PATH = Path("exp_output/MLB/a2_refit_full/candidate.csv")
MODEL_PATH = Path("models/a2_refit/candidate_isotonic_model.joblib")
META_PATH = Path("models/a2_refit/candidate_isotonic_model_meta.json")


def run() -> None:
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found -- run build_a2_refit_variants.py first.",
              file=sys.stderr)
        sys.exit(1)

    session_id = f"TRAIN-MLB-A3-ISO-{uuid.uuid4().hex[:8].upper()}"
    print(f"\n{'='*65}\nA3 -- isotonic recalibration refit (GG-105 A2-FAIL contingency)"
          f"\nSession: {session_id}\ncsv: {CSV_PATH}\n{'='*65}\n")

    print("[1/6] Loading feature matrix...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    df["game_date"] = pd.to_datetime(df["game_date"])
    print(f"      {len(df):,} rows loaded")

    print("[2/6] Filtering to rows with valid temporal_cutoff...")
    valid_df = df[df["temporal_cutoff"].notna()].copy() if "temporal_cutoff" in df.columns else df.copy()
    print(f"      {len(valid_df):,} valid rows (of {len(df):,})")

    print("[3/6] Expanding to threshold rows...")
    expanded = tm._build_mlb_target(valid_df, tm.THRESHOLDS)
    print(f"      {len(expanded):,} expanded rows")

    print(f"[4/6] Splitting on HOLDOUT_CUTOFF = {tm.HOLDOUT_CUTOFF}...")
    game_dates = pd.to_datetime(expanded["game_date"])
    train_mask = (game_dates <= pd.Timestamp(tm.HOLDOUT_CUTOFF)) & expanded["y_target"].notna()
    holdout_mask = (game_dates > pd.Timestamp(tm.HOLDOUT_CUTOFF)) & expanded["y_target"].notna()
    train_df = expanded[train_mask].copy()
    holdout_df = expanded[holdout_mask].copy()
    print(f"      Train:   {len(train_df):,} rows")
    print(f"      Holdout: {len(holdout_df):,} rows")
    if len(train_df) < tm.MIN_TRAIN_SAMPLES or len(holdout_df) < tm.MIN_HOLDOUT_SAMPLES:
        print("ERROR: insufficient train/holdout samples.", file=sys.stderr)
        sys.exit(1)

    print("[5/6] Building shared feature matrix + fitting per-threshold "
          "LR + ISOTONIC pipelines (A3 supersedes ADR-0004's sigmoid choice)...")
    X_train_all, feature_names = tm._extract_feature_matrix(train_df)
    col_medians = np.nanmedian(X_train_all, axis=0)
    model_version = tm._mlb_model_version(feature_names) + "-a3iso"

    pipelines: dict[int, Pipeline] = {}
    threshold_metrics: dict[int, dict] = {}

    for t in tm.THRESHOLDS:
        t_train = train_df[train_df["threshold"] == float(t)].copy()
        t_hold = holdout_df[holdout_df["threshold"] == float(t)].copy()

        X_t_train, _ = tm._extract_feature_matrix(t_train)
        X_t_hold, _ = tm._extract_feature_matrix(t_hold)
        y_t_train = t_train["y_target"].astype(int).to_numpy()
        y_t_hold = t_hold["y_target"].astype(int).to_numpy()

        X_t_train = tm._impute(X_t_train, col_medians)
        X_t_hold = tm._impute(X_t_hold, col_medians)

        base_clf = LogisticRegression(
            C=1.0, solver="lbfgs", max_iter=1000, random_state=42, class_weight="balanced",
        )
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", CalibratedClassifierCV(base_clf, method="isotonic", cv=3)),
        ])
        pipe.fit(X_t_train, y_t_train)

        y_prob = pipe.predict_proba(X_t_hold)[:, 1]
        null_rate = float(y_t_hold.mean())
        brier_m = float(brier_score_loss(y_t_hold, y_prob))
        brier_n = float(brier_score_loss(y_t_hold, np.full_like(y_prob, null_rate)))
        bd = brier_n - brier_m
        ece = tm._compute_ece(y_t_hold, y_prob)
        auc = float(roc_auc_score(y_t_hold, y_prob)) if len(np.unique(y_t_hold)) > 1 else float("nan")

        g_brier = bd >= tm.SHADOW_GATE_BRIER_DELTA
        g_ece = ece <= tm.SHADOW_GATE_ECE_MAX
        print(f"      t={t}: Brier delta={bd:+.4f} ({'PASS' if g_brier else 'FAIL'})  "
              f"ECE={ece:.4f} ({'PASS' if g_ece else 'FAIL'})  AUC={auc:.4f}")

        pipelines[t] = pipe
        threshold_metrics[t] = {
            "null_positive_rate": round(null_rate, 6),
            "brier_model": round(brier_m, 6),
            "brier_null": round(brier_n, 6),
            "brier_delta": round(bd, 6),
            "ece": round(ece, 4),
            "auc_roc": round(auc, 4) if not np.isnan(auc) else None,
            "gate_brier": g_brier,
            "gate_ece": g_ece,
            "gate_pass": g_brier and g_ece,
        }

    gate_pass = all(m["gate_pass"] for m in threshold_metrics.values())
    print(f"\n      Combined shadow gate: {'PASS' if gate_pass else 'FAIL'} "
          f"(informational only -- A3's real gate is the D1 harness calibration "
          f"criteria, saving regardless, same discipline as A2)")

    print("[6/6] Saving isolated A3 artifact (Hard Rule 4: never models/mlb_v1_model.*)...")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "pipelines": pipelines,
        "feature_names": feature_names,
        "col_medians": col_medians,
        "model_version": model_version,
        "thresholds": tm.THRESHOLDS,
        "sport": "mlb",
    }
    joblib.dump(artifact, MODEL_PATH)
    meta = {
        "model_version": model_version,
        "feature_version": tm.FEATURE_VERSION,
        "model_class": "LogisticRegression+IsotonicCalibration per-threshold (A3, supersedes ADR-0004 sigmoid choice)",
        "sport": "mlb",
        "thresholds": tm.THRESHOLDS,
        "excluded_thresholds": tm._EXCLUDED_THRESHOLDS,
        "feature_names": feature_names,
        "feature_count": len(feature_names),
        "holdout_cutoff": tm.HOLDOUT_CUTOFF,
        "trained_at": tm._utc_now(),
        "session_id": session_id,
        "train_rows": int(len(train_df)),
        "holdout_rows": int(len(holdout_df)),
        "threshold_metrics": threshold_metrics,
        "shadow_gate_pass": gate_pass,
        "shadow_gate_brier_delta_required": tm.SHADOW_GATE_BRIER_DELTA,
        "shadow_gate_ece_max": tm.SHADOW_GATE_ECE_MAX,
        "adr": "ADR-0004 (superseded by A3 pending GG-105 resolution)",
        "gg": "GG-105",
        "supersedes": "A2 candidate (sigmoid/Platt) -- see DECISION_LOG.md 2026-07-24",
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"      Saved: {MODEL_PATH}")
    print(f"      Saved: {META_PATH}")


if __name__ == "__main__":
    run()

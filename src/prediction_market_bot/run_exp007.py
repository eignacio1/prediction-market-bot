"""
EXP-007: Qualitative Signal Brier Measurement — Backdated QS Snapshot (QS-2026-05-28-002)
===========================================================================================
Experiment ID:   EXP-007
Phase:           Phase 6 Planning (qualitative feature integration)
Status:          CANONICAL RUNNER — 2026-05-28
Hypothesis:      With backdated PAM v4 classifications (QTI-03), do qualitative
                 features (PRF archetypes + modifiers) improve Brier score vs
                 the quantitative-only EXP-006 baseline?

Design:
  Identical to EXP-006 except uses QS-2026-05-28-002 (backdated snapshot):
    - 42 players: effective_from = 2021-10-19 (start of earliest training season)
    -  7 players: effective_from = 2022-10-18 (archetype solidified that season)
    -  1 player:  effective_from = 2023-10-24 (Barnes; too young pre-2023-24)
  Backdating rationale documented per player in QS-002 (QTI-03 compliant).

  TRAIN rows (game_date ≤ 2025-02-28) now receive qualitative feature values
  for players within their effective window. Model can learn PRF + modifier
  coefficients. This is the test of whether qualitative features carry signal.

EXP-006 baseline (quant only, same test set): Brier 0.2476 (+0.0024 vs null)

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp007.py

    Requires: exp_output/EXP-005/EXP-005_feature_matrix.csv (cached from EXP-005)
              qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv

Security (NFR-05, NFR-07):
    - No API keys required.
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

EXP_ID = "EXP-007"
SESSION_ID = f"EXP-007-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID = "QS-2026-05-28-002"
OUTPUT_DIR = Path("exp_output/EXP-007")

TRAIN_END_DATE = "2025-02-28"
VAL_END_DATE   = "2025-04-13"
FEATURE_WINDOW = 10

# Baselines
EXP006_QUANT_BRIER = 0.2476   # EXP-006 quantitative-only on same TEST set
NULL_BRIER = 0.2500
SNAPSHOT_ID = "SNAP-2026-05-28-002"

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
    target[pts.isna() | prior_mean.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return target


def _impute(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    col_medians = np.nanmedian(X, axis=0)
    col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)
    mask = np.isnan(X)
    X[mask] = np.take(col_medians, np.where(mask)[1])
    return X


def _fit(X: np.ndarray, y: np.ndarray) -> Pipeline:
    base = LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=1000,
        random_state=42, class_weight="balanced",
    )
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
    ])
    pipe.fit(X, y)
    return pipe


def _ece(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    yp = np.clip(y_prob, 1e-6, 1 - 1e-6)
    frac, mean = calibration_curve(y_true, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0.0, 1.0))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac[:n] - mean[:n])))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp007.jsonl", min_severity="DEBUG")

    print(f"\n{'='*60}")
    print(f"EXP-007: Qualitative Signal — Backdated QS Snapshot")
    print(f"Session:  {SESSION_ID}")
    print(f"QS snap:  {QS_ID}  (effective_from: 2021-10-19 / 2022-10-18 / 2023-10-24)")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 1. Load feature matrix (cached — no API call)
    # ------------------------------------------------------------------
    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows from {FEATURE_CSV}")

    # ------------------------------------------------------------------
    # 2. Load and apply qualitative enrichment
    # ------------------------------------------------------------------
    print(f"\n[QS] Loading {QS_ID}...")
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: Failed to load QS snapshot.", file=sys.stderr)
        sys.exit(1)
    assert qs._ds01_df is not None  # load_ds01_snapshot succeeded above
    print(f"[QS] Loaded — {len(qs._ds01_df)} player classifications")

    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: QS enrichment failed.", file=sys.stderr)
        sys.exit(1)

    # Diagnostics: how many training rows now have qualitative values?
    game_dates = pd.to_datetime(df_q["game_date"], errors="coerce")
    prf_col = "prf_primary"
    train_mask = df_q["train_test_label"] == "TRAIN"
    val_mask   = df_q["train_test_label"] == "VALIDATION"
    test_mask  = df_q["train_test_label"] == "TEST"

    for split_name, mask in [("TRAIN", train_mask), ("VAL", val_mask), ("TEST", test_mask)]:
        n_filled = int(df_q.loc[mask, prf_col].notna().sum()) if prf_col in df_q.columns else 0
        n_total  = int(mask.sum())
        print(f"[QS] {split_name}: {n_filled:,}/{n_total:,} rows with qualitative features")

    # ------------------------------------------------------------------
    # 3. Feature name lists
    # ------------------------------------------------------------------
    qual_names  = qs.get_qualitative_feature_names()
    quant_names = [
        c for c in df_q.columns
        if c not in _NON_FEATURE_BASE and c not in set(qual_names)
    ]
    all_names = quant_names + qual_names
    print(f"\n[FEATURES] {len(quant_names)} quant + {len(qual_names)} qual = {len(all_names)} total")

    # ------------------------------------------------------------------
    # 4. Target + splits
    # ------------------------------------------------------------------
    df_q["y_target"] = _build_target(df_q)
    usable = df_q[df_q["y_target"].notna() & df_q["temporal_cutoff"].notna()].copy()
    train = usable[usable["train_test_label"] == "TRAIN"].copy()
    val   = usable[usable["train_test_label"] == "VALIDATION"].copy()
    test  = usable[usable["train_test_label"] == "TEST"].copy()
    print(f"[SPLIT] TRAIN {len(train):,} | VAL {len(val):,} | TEST {len(test):,}")

    # ------------------------------------------------------------------
    # 5. Fit + evaluate — quantitative only (control)
    # ------------------------------------------------------------------
    print(f"\n[CTRL] Fitting quant-only ({len(quant_names)} features)...")
    Xtr_q  = _impute(train[quant_names].to_numpy(dtype=float))
    Xte_q  = _impute(test[quant_names].to_numpy(dtype=float))
    y_tr   = train["y_target"].astype(int).to_numpy()
    y_te   = test["y_target"].astype(int).to_numpy()
    m_ctrl = _fit(Xtr_q, y_tr)
    p_ctrl = m_ctrl.predict_proba(Xte_q)[:, 1]
    b_ctrl = float(brier_score_loss(y_te, p_ctrl))
    e_ctrl = _ece(y_te, p_ctrl)
    a_ctrl = float(roc_auc_score(y_te, p_ctrl))

    # ------------------------------------------------------------------
    # 6. Fit + evaluate — quantitative + qualitative
    # ------------------------------------------------------------------
    print(f"[FULL] Fitting quant+qual ({len(all_names)} features)...")
    Xtr_all = _impute(train[all_names].to_numpy(dtype=float))
    Xte_all = _impute(test[all_names].to_numpy(dtype=float))
    m_full  = _fit(Xtr_all, y_tr)
    p_full  = m_full.predict_proba(Xte_all)[:, 1]
    b_full  = float(brier_score_loss(y_te, p_full))
    e_full  = _ece(y_te, p_full)
    a_full  = float(roc_auc_score(y_te, p_full))

    # ------------------------------------------------------------------
    # 7. Results
    # ------------------------------------------------------------------
    d_brier = b_ctrl - b_full   # positive = qual features help
    d_ece   = e_ctrl - e_full
    d_auc   = a_full - a_ctrl

    print(f"\n{'='*60}")
    print("EXP-007 RESULTS — BACKDATED QUALITATIVE SIGNAL")
    print(f"{'='*60}")
    print(f"QS snapshot:   {QS_ID}")
    print(f"effective_from: 2021-10-19 (42 players) / 2022-10-18 (7) / 2023-10-24 (1)")
    print(f"\nTEST set (2025-26 regular season, n={len(test):,}):")
    print(f"                    {'QUANT ONLY':>12}  {'QUANT+QUAL':>12}  {'DELTA':>10}")
    print(f"  Brier score:      {b_ctrl:>12.4f}  {b_full:>12.4f}  {d_brier:>+10.4f}")
    print(f"  Brier vs null:    {NULL_BRIER-b_ctrl:>+12.4f}  {NULL_BRIER-b_full:>+12.4f}")
    print(f"  ECE:              {e_ctrl:>12.4f}  {e_full:>12.4f}  {d_ece:>+10.4f}")
    print(f"  AUC-ROC:          {a_ctrl:>12.4f}  {a_full:>12.4f}  {d_auc:>+10.4f}")
    print(f"\nEXP-006 baseline (non-backdated QS, Δ=0.0000): Brier {EXP006_QUANT_BRIER:.4f}")

    if d_brier > 0.001:
        finding = "POSITIVE_SIGNAL"
        summary = f"Qualitative features IMPROVE Brier by {d_brier:+.4f}. PRF archetypes carry predictive signal."
    elif d_brier > 0:
        finding = "MARGINAL_POSITIVE"
        summary = f"Qualitative features show marginal improvement ({d_brier:+.4f}). Signal present but small."
    elif abs(d_brier) <= 0.001:
        finding = "NEGLIGIBLE"
        summary = f"Qualitative features add negligible Brier signal ({d_brier:+.4f}). PRF archetype may need further operationalization."
    else:
        finding = "NEGATIVE"
        summary = f"Qualitative features HURT Brier by {d_brier:+.4f}. Investigate multicollinearity or feature noise."

    print(f"\nFINDING: {finding}")
    print(f"  {summary}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 8. Save
    # ------------------------------------------------------------------
    out = {
        "exp_id": EXP_ID,
        "session_id": SESSION_ID,
        "run_at": _utc_now(),
        "qs_id": QS_ID,
        "backdated": True,
        "effective_from_distribution": {"2021-10-19": 42, "2022-10-18": 7, "2023-10-24": 1},
        "feature_counts": {"quantitative": len(quant_names), "qualitative": len(qual_names), "total": len(all_names)},
        "split": {"train": len(train), "val": len(val), "test": len(test)},
        "train_rows_with_qual": int(train[prf_col].notna().sum()) if prf_col in train.columns else 0,
        "test_rows_with_qual": int(test[prf_col].notna().sum()) if prf_col in test.columns else 0,
        "quant_only": {"brier": round(b_ctrl, 6), "brier_improvement": round(NULL_BRIER - b_ctrl, 6), "ece": round(e_ctrl, 6), "auc_roc": round(a_ctrl, 6)},
        "quant_plus_qual": {"brier": round(b_full, 6), "brier_improvement": round(NULL_BRIER - b_full, 6), "ece": round(e_full, 6), "auc_roc": round(a_full, 6)},
        "delta": {"brier": round(d_brier, 6), "ece": round(d_ece, 6), "auc_roc": round(d_auc, 6)},
        "exp006_baseline_brier": EXP006_QUANT_BRIER,
        "null_brier": NULL_BRIER,
        "finding": finding,
        "summary": summary,
    }
    out_path = OUTPUT_DIR / "EXP-007_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr)
        sys.exit(1)
    main()

"""
EXP-008: PRF Weighted One-Hot Encoding — Brier Measurement
===========================================================
Experiment ID:   EXP-008
Phase:           Phase 6 Planning (qualitative feature operationalization)
Status:          CANONICAL RUNNER — 2026-05-28

Change vs EXP-007:
  prf_primary / prf_secondary / prf_hybrid_weight (3 integer/float columns, spurious ordinality)
  →  prf_w01 … prf_w15  (15 weighted continuous features, F-103–F-117)

  Encoding: per PAM v4 weighted hybrid notation
    Pure player   (prf_secondary == 0): prf_w{primary} = 1.0
    Hybrid player:                      prf_w{primary} = prf_hybrid_weight
                                        prf_w{secondary} = 1 - prf_hybrid_weight

  This removes spurious ordinality (PRF-9 > PRF-1 in integer encoding is meaningless)
  and allows the model to learn separate LR coefficients per archetype.

Feature counts:
  EXP-007: 31 quant + 35 qual (3 PRF int + 32 mod) = 66
  EXP-008: 31 quant + 47 qual (15 PRF one-hot + 32 mod) = 78

EXP-007 baseline (backdated QS, integer PRF): Brier 0.2459 (+0.0041 vs null)

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp008.py
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
    QualitativeSignalStore, DS01_FEATURE_NAMES, PRF_ONEHOT_FEATURES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

EXP_ID    = "EXP-008"
SESSION_ID = f"EXP-008-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
OUTPUT_DIR  = Path("exp_output/EXP-008")
FEATURE_WINDOW = 10
NULL_BRIER = 0.2500
EXP007_BRIER = 0.2459
SNAPSHOT_ID = "SNAP-2026-05-28-002"

_PRUNED_V110 = {
    "season_type_is_playoffs","days_since_last_game","b2b_flag",
    "load_games_l7d","eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
}
_NON_FEATURE_BASE = {
    "player_id","player_name","team_id","team_abbreviation",
    "game_id","game_date","season","season_type",
    "min","pts","reb","ast","stl","blk","tov","pf",
    "fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm","fta","ft_pct","plus_minus",
    "snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    # raw PRF integer columns are dropped by enrich_features() now, but guard here too
    "prf_primary","prf_secondary","prf_hybrid_weight",
} | _PRUNED_V110


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan]*len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df[col], errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA
    return t

def _impute(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X

def _fit(X: np.ndarray, y: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                               random_state=42, class_weight="balanced")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X, y)
    return pipe

def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1-1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0.,1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n]/counts[:n].sum()) * np.abs(frac[:n]-mean[:n])))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp008.jsonl", min_severity="DEBUG")

    print(f"\n{'='*60}")
    print(f"EXP-008: PRF Weighted One-Hot Encoding")
    print(f"Session: {SESSION_ID}")
    print(f"Change:  prf_primary/secondary/weight (3 int cols) → prf_w01…prf_w15 (15 weighted)")
    print(f"{'='*60}\n")

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows")

    # Load QS and enrich (one-hot encoding applied inside enrich_features)
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: QS load failed", file=sys.stderr); sys.exit(1)

    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: enrich failed", file=sys.stderr); sys.exit(1)

    # Report encoding diagnostic
    prf_w_col = "prf_w01"  # check a known PRF-1 player (Curry, SGA, etc.)
    qual_names = qs.get_qualitative_feature_names()   # prf_w01…prf_w15 + mod_01…mod_32
    quant_names = [c for c in df_q.columns if c not in _NON_FEATURE_BASE and c not in set(qual_names)]
    all_names = quant_names + qual_names

    print(f"[FEATURES] {len(quant_names)} quant + {len(qual_names)} qual = {len(all_names)} total")
    print(f"  Qual breakdown: {len(PRF_ONEHOT_FEATURES)} PRF one-hot + 32 modifiers")

    # Splits
    df_q["y_target"] = _build_target(df_q)
    usable = df_q[df_q["y_target"].notna() & df_q["temporal_cutoff"].notna()].copy()
    train = usable[usable["train_test_label"] == "TRAIN"].copy()
    val   = usable[usable["train_test_label"] == "VALIDATION"].copy()
    test  = usable[usable["train_test_label"] == "TEST"].copy()
    print(f"[SPLIT] TRAIN {len(train):,} | VAL {len(val):,} | TEST {len(test):,}")

    # PRF fill diagnostic
    if prf_w_col in train.columns:
        train_prf = int(train[prf_w_col].notna().sum())
        test_prf  = int(test[prf_w_col].notna().sum())
        print(f"[QS] prf_w01 non-NaN — TRAIN: {train_prf:,}/{len(train):,} | TEST: {test_prf:,}/{len(test):,}")

    y_tr = train["y_target"].astype(int).to_numpy()
    y_te = test["y_target"].astype(int).to_numpy()

    # Control: quant only
    print(f"\n[CTRL] quant-only ({len(quant_names)} features)...")
    m_ctrl = _fit(_impute(train[quant_names].to_numpy(dtype=float)), y_tr)
    p_ctrl = m_ctrl.predict_proba(_impute(test[quant_names].to_numpy(dtype=float)))[:, 1]
    b_ctrl, e_ctrl, a_ctrl = (float(brier_score_loss(y_te, p_ctrl)),
                               _ece(y_te, p_ctrl),
                               float(roc_auc_score(y_te, p_ctrl)))

    # EXP-008: quant + one-hot PRF qualitative
    print(f"[FULL] quant+qual one-hot ({len(all_names)} features)...")
    m_full = _fit(_impute(train[all_names].to_numpy(dtype=float)), y_tr)
    p_full = m_full.predict_proba(_impute(test[all_names].to_numpy(dtype=float)))[:, 1]
    b_full, e_full, a_full = (float(brier_score_loss(y_te, p_full)),
                               _ece(y_te, p_full),
                               float(roc_auc_score(y_te, p_full)))

    d_brier = b_ctrl - b_full
    d_ece   = e_ctrl - e_full
    d_auc   = a_full - a_ctrl
    vs_exp007 = EXP007_BRIER - b_full   # positive = EXP-008 better than EXP-007

    print(f"\n{'='*60}")
    print("EXP-008 RESULTS — PRF WEIGHTED ONE-HOT ENCODING")
    print(f"{'='*60}")
    print(f"\nTEST set (2025-26 regular season, n={len(test):,}):")
    print(f"                    {'QUANT ONLY':>12}  {'QUANT+QUAL':>12}  {'DELTA':>10}")
    print(f"  Brier score:      {b_ctrl:>12.4f}  {b_full:>12.4f}  {d_brier:>+10.4f}")
    print(f"  Brier vs null:    {NULL_BRIER-b_ctrl:>+12.4f}  {NULL_BRIER-b_full:>+12.4f}")
    print(f"  ECE:              {e_ctrl:>12.4f}  {e_full:>12.4f}  {d_ece:>+10.4f}")
    print(f"  AUC-ROC:          {a_ctrl:>12.4f}  {a_full:>12.4f}  {d_auc:>+10.4f}")
    print(f"\nEXP-007 baseline (integer PRF): Brier {EXP007_BRIER:.4f}")
    print(f"One-hot vs integer PRF:         {vs_exp007:>+.4f} ({'improvement' if vs_exp007 > 0 else 'regression' if vs_exp007 < -0.0003 else 'negligible'})")

    if d_brier > 0.001:
        finding = "POSITIVE — one-hot encoding improves over integer PRF"
    elif d_brier > 0:
        finding = "MARGINAL_POSITIVE"
    elif abs(d_brier) <= 0.0005:
        finding = "NEGLIGIBLE — encoding change has minimal effect at this scale"
    else:
        finding = "NEGATIVE — investigate"

    print(f"\nFINDING: {finding}")
    print(f"{'='*60}\n")

    out = {
        "exp_id": EXP_ID, "session_id": SESSION_ID, "run_at": _utc_now(),
        "qs_id": QS_ID, "encoding": "weighted_one_hot_prf",
        "feature_counts": {"quantitative": len(quant_names), "qualitative": len(qual_names),
                           "prf_onehot": len(PRF_ONEHOT_FEATURES), "modifiers": 32,
                           "total": len(all_names)},
        "split": {"train": len(train), "val": len(val), "test": len(test)},
        "quant_only": {"brier": round(b_ctrl,6), "brier_improvement": round(NULL_BRIER-b_ctrl,6),
                       "ece": round(e_ctrl,6), "auc_roc": round(a_ctrl,6)},
        "quant_plus_qual": {"brier": round(b_full,6), "brier_improvement": round(NULL_BRIER-b_full,6),
                            "ece": round(e_full,6), "auc_roc": round(a_full,6)},
        "delta": {"brier": round(d_brier,6), "ece": round(d_ece,6), "auc_roc": round(d_auc,6)},
        "vs_exp007_brier": round(vs_exp007, 6),
        "exp007_baseline_brier": EXP007_BRIER, "null_brier": NULL_BRIER,
        "finding": finding,
    }
    out_path = OUTPUT_DIR / "EXP-008_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr); sys.exit(1)
    main()

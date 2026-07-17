"""
EXP-009: Layer 3 Qualitative Amplification — Context-Conditional Features
==========================================================================
Experiment ID:   EXP-009
Phase:           Phase 6 Planning (OQ-021 — amplification study)
Status:          CANONICAL RUNNER — 2026-05-28

Tests whether qualitative × context interaction features (F-300+) add Brier
signal beyond Layer 1 + Layer 2 alone (EXP-008 baseline).

Feature composition:
  Layer 1: 31 quantitative (F-001–F-031)
  Layer 2: 47 qualitative (15 PRF one-hot + 32 modifiers) — QS-2026-05-28-002
  Layer 3: 35 amplification (F-300–F-334):
    CTX-2: prf_w01…prf_w15 × pts_cold_flag   (15 features)
    CTX-3: prf_w01…prf_w15 × pts_hot_flag    (15 features)
    CTX-4: mod_16 × season_stage              (1)
    CTX-4b: mod_17 × cold_flag / hot_flag     (2)
    CTX-5: mod_19 × late-season / mod_31 × stage (2)
  Total: 113 features

EXP-008 baseline (78 features): Brier 0.2461 (+0.0039 vs null) / ECE 0.0342

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp009.py
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
from prediction_market_bot.c2_feature_store.qualitative_amplifier import (
    QualitativeAmplifier, AMP_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from typing import Any

EXP_ID     = "EXP-009"
SESSION_ID = f"EXP-009-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
OUTPUT_DIR  = Path("exp_output/EXP-009")
FEATURE_WINDOW = 10
NULL_BRIER  = 0.2500
EXP008_BRIER = 0.2461
SNAPSHOT_ID  = "SNAP-2026-05-28-002"

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
    logger = AuditLogger(OUTPUT_DIR / "audit_exp009.jsonl", min_severity="DEBUG")

    print(f"\n{'='*60}")
    print(f"EXP-009: Layer 3 Qualitative Amplification (OQ-021)")
    print(f"Session:  {SESSION_ID}")
    print(f"Features: 31 quant + 47 qual + 35 amp = 113 total")
    print(f"{'='*60}\n")

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows")

    # ------------------------------------------------------------------
    # Layer 2: qualitative enrichment
    # ------------------------------------------------------------------
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: QS load failed", file=sys.stderr); sys.exit(1)

    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: QS enrich failed", file=sys.stderr); sys.exit(1)

    # ------------------------------------------------------------------
    # Layer 3: amplification
    # ------------------------------------------------------------------
    amp = QualitativeAmplifier(logger=logger, snapshot_id=SNAPSHOT_ID)
    ok, df_a = amp.compute_amplification(df_q, session_id=SESSION_ID)
    if not ok:
        print("ERROR: amplification failed", file=sys.stderr); sys.exit(1)

    qual_names = qs.get_qualitative_feature_names()
    amp_names  = amp.get_amplification_feature_names()
    quant_names = [
        c for c in df_a.columns
        if c not in _NON_FEATURE_BASE
        and c not in set(qual_names)
        and c not in set(amp_names)
    ]

    all_names   = quant_names + qual_names + amp_names
    l12_names   = quant_names + qual_names   # L1+L2 only (EXP-008 equivalent)

    print(f"[FEATURES] {len(quant_names)} quant + {len(qual_names)} qual + {len(amp_names)} amp = {len(all_names)} total")

    # Amplification diagnostic
    cold_amp = "amp_prf_cold_01"
    hot_amp  = "amp_prf_hot_01"
    if cold_amp in df_a.columns:
        n_cold = int((df_a[cold_amp] > 0).sum())
        n_hot  = int((df_a[hot_amp] > 0).sum()) if hot_amp in df_a.columns else 0
        print(f"[AMP] PRF-1 cold events: {n_cold:,} | PRF-1 hot events: {n_hot:,}")

    # ------------------------------------------------------------------
    # Splits + target
    # ------------------------------------------------------------------
    df_a["y_target"] = _build_target(df_a)
    usable = df_a[df_a["y_target"].notna() & df_a["temporal_cutoff"].notna()].copy()
    train = usable[usable["train_test_label"] == "TRAIN"].copy()
    val   = usable[usable["train_test_label"] == "VALIDATION"].copy()
    test  = usable[usable["train_test_label"] == "TEST"].copy()
    print(f"[SPLIT] TRAIN {len(train):,} | VAL {len(val):,} | TEST {len(test):,}")

    y_tr = train["y_target"].astype(int).to_numpy()
    y_te = test["y_target"].astype(int).to_numpy()

    # ------------------------------------------------------------------
    # Control: L1 only (31 features)
    # ------------------------------------------------------------------
    print(f"\n[CTRL] L1 quant-only ({len(quant_names)} features)...")
    m_ctrl = _fit(_impute(train[quant_names].to_numpy(dtype=float)), y_tr)
    p_ctrl = m_ctrl.predict_proba(_impute(test[quant_names].to_numpy(dtype=float)))[:,1]
    b_ctrl = float(brier_score_loss(y_te, p_ctrl))
    e_ctrl = _ece(y_te, p_ctrl)
    a_ctrl = float(roc_auc_score(y_te, p_ctrl))

    # ------------------------------------------------------------------
    # EXP-008 equivalent: L1 + L2 (78 features)
    # ------------------------------------------------------------------
    print(f"[L1+L2] quant+qual ({len(l12_names)} features)...")
    m_l12 = _fit(_impute(train[l12_names].to_numpy(dtype=float)), y_tr)
    p_l12 = m_l12.predict_proba(_impute(test[l12_names].to_numpy(dtype=float)))[:,1]
    b_l12 = float(brier_score_loss(y_te, p_l12))
    e_l12 = _ece(y_te, p_l12)
    a_l12 = float(roc_auc_score(y_te, p_l12))

    # ------------------------------------------------------------------
    # EXP-009: L1 + L2 + L3 (113 features)
    # ------------------------------------------------------------------
    print(f"[FULL] L1+L2+L3 ({len(all_names)} features)...")
    m_full = _fit(_impute(train[all_names].to_numpy(dtype=float)), y_tr)
    p_full = m_full.predict_proba(_impute(test[all_names].to_numpy(dtype=float)))[:,1]
    b_full = float(brier_score_loss(y_te, p_full))
    e_full = _ece(y_te, p_full)
    a_full = float(roc_auc_score(y_te, p_full))

    # ------------------------------------------------------------------
    # Per-context contribution: ablation by context group
    # ------------------------------------------------------------------
    print(f"[ABLATION] Running per-context contribution...")
    context_groups = {
        "CTX-2 PRF×cold": [c for c in amp_names if c.startswith("amp_prf_cold")],
        "CTX-3 PRF×hot":  [c for c in amp_names if c.startswith("amp_prf_hot")],
        "CTX-4/5 mod×ctx": [c for c in amp_names if c.startswith("amp_m")],
    }
    ctx_results: dict[str, dict[str, Any]] = {}
    for ctx_name, ctx_cols in context_groups.items():
        feats = l12_names + ctx_cols
        m_ctx = _fit(_impute(train[feats].to_numpy(dtype=float)), y_tr)
        p_ctx = m_ctx.predict_proba(_impute(test[feats].to_numpy(dtype=float)))[:,1]
        b_ctx = float(brier_score_loss(y_te, p_ctx))
        ctx_results[ctx_name] = {
            "features_added": len(ctx_cols),
            "brier": round(b_ctx, 6),
            "delta_vs_l12": round(b_l12 - b_ctx, 6),
        }

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    d12  = b_ctrl - b_l12   # L2 adds over L1
    d_amp = b_l12 - b_full  # L3 adds over L1+L2

    print(f"\n{'='*60}")
    print("EXP-009 RESULTS — LAYER 3 AMPLIFICATION")
    print(f"{'='*60}")
    print(f"\nTEST set (2025-26 regular season, n={len(test):,}):")
    print(f"                    {'L1 ONLY':>12}  {'L1+L2':>12}  {'L1+L2+L3':>12}")
    print(f"  Brier score:      {b_ctrl:>12.4f}  {b_l12:>12.4f}  {b_full:>12.4f}")
    print(f"  Brier vs null:    {NULL_BRIER-b_ctrl:>+12.4f}  {NULL_BRIER-b_l12:>+12.4f}  {NULL_BRIER-b_full:>+12.4f}")
    print(f"  ECE:              {e_ctrl:>12.4f}  {e_l12:>12.4f}  {e_full:>12.4f}")
    print(f"  AUC-ROC:          {a_ctrl:>12.4f}  {a_l12:>12.4f}  {a_full:>12.4f}")
    print(f"\n  L2 adds over L1:       Brier {d12:>+.4f}")
    print(f"  L3 adds over L1+L2:    Brier {d_amp:>+.4f}")
    print(f"  L3 adds over L1:       Brier {b_ctrl-b_full:>+.4f}")
    print(f"\nPer-context contribution (each adds to L1+L2 baseline):")
    for ctx_name, r in ctx_results.items():
        signal = "✓" if r["delta_vs_l12"] > 0.0003 else "~"
        print(f"  {ctx_name:<25} {r['features_added']} features  Δ={r['delta_vs_l12']:>+.4f} {signal}")
    print(f"\nEXP-008 baseline (one-hot PRF, 78 features): Brier {EXP008_BRIER:.4f}")
    amp_signal = "POSITIVE" if d_amp > 0.001 else "MARGINAL" if d_amp > 0 else "NEGLIGIBLE" if abs(d_amp) <= 0.001 else "NEGATIVE"
    print(f"Amplification signal:  {amp_signal}")
    print(f"{'='*60}\n")

    out = {
        "exp_id": EXP_ID, "session_id": SESSION_ID, "run_at": _utc_now(),
        "feature_counts": {"quant": len(quant_names), "qual": len(qual_names),
                           "amp": len(amp_names), "total": len(all_names)},
        "split": {"train": len(train), "val": len(val), "test": len(test)},
        "l1_only":  {"brier": round(b_ctrl,6), "ece": round(e_ctrl,6), "auc_roc": round(a_ctrl,6)},
        "l1_l2":    {"brier": round(b_l12,6),  "ece": round(e_l12,6),  "auc_roc": round(a_l12,6)},
        "l1_l2_l3": {"brier": round(b_full,6), "ece": round(e_full,6), "auc_roc": round(a_full,6)},
        "deltas": {
            "l2_over_l1": round(d12, 6),
            "l3_over_l12": round(d_amp, 6),
            "l3_over_l1": round(b_ctrl - b_full, 6),
        },
        "per_context_ablation": ctx_results,
        "exp008_baseline_brier": EXP008_BRIER,
        "null_brier": NULL_BRIER,
        "amp_signal": amp_signal,
    }
    out_path = OUTPUT_DIR / "EXP-009_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr); sys.exit(1)
    main()

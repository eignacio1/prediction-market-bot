"""
EXP-011: Gradient Boosting Model Class Experiment (T-065)
==========================================================
Experiment ID:   EXP-011
Phase:           Phase 6 Planning (T-065 — model class evolution)
Status:          CANONICAL RUNNER — 2026-05-28

Tests whether sklearn HistGradientBoostingClassifier (HGBC) outperforms
LogisticRegression on this problem, and specifically whether HGBC can
exploit Layer 3 amplification features that LR proved unable to use.

Context:
  EXP-009 showed Layer 3 (F-300+) Δ = -0.0004 for LR — interaction features
  create collinearity noise in a linear model. HGBC naturally splits on
  individual features: prf_w01 × cold_flag interactions emerge from tree
  structure without explicit interaction columns. If HGBC significantly
  outperforms LR (especially on L1+L2+L3), it validates:
    (a) the Layer 3 signal exists — just needs a non-linear model
    (b) a model class change (ADR-0004 amendment) is warranted

Four configurations compared:
  A. LR  L1+L2          — control (EXP-008 baseline)
  B. HGBC L1            — does GBM help without qualitative features?
  C. HGBC L1+L2         — does GBM exploit qualitative features better?
  D. HGBC L1+L2+L3      — does GBM find Layer 3 signal? (KEY TEST)

HGBC advantages over LR for this problem:
  - Native NaN handling: no imputation needed (qualitative NaN → native split)
  - Non-linear: learns PRF × context interactions from tree structure
  - No spurious ordinality: prf_w01=0.6 vs prf_w01=1.0 is a real split point
  - Automatic feature interaction discovery

Governance:
  If HGBC improvement over LR > 0.003 Brier: recommend ADR-0004 amendment.
  ADR-0004 accepted LR+Platt as model class; upgrading requires new ADR.

LR baselines (EXP-008/EXP-009):
  L1 only:   Brier 0.2476 (+0.0024 vs null)
  L1+L2:     Brier 0.2461 (+0.0039) — best LR result
  L1+L2+L3:  Brier 0.2464 (+0.0036) — L3 adds nothing for LR

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp011.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier
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
from prediction_market_bot.c2_feature_store.qualitative_amplifier import (
    QualitativeAmplifier, AMP_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

EXP_ID     = "EXP-011"
SESSION_ID = f"EXP-011-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
OUTPUT_DIR  = Path("exp_output/EXP-011")
FEATURE_WINDOW = 10
NULL_BRIER  = 0.2500
SNAPSHOT_ID = "SNAP-2026-05-28-002"

# Baselines for comparison
LR_L1_BRIER  = 0.2476
LR_L12_BRIER = 0.2461
LR_L123_BRIER = 0.2464

# ADR-0004 amendment threshold
ADR_TRIGGER_DELTA = 0.003   # HGBC must beat best LR by this much to trigger ADR recommendation

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
    """LR imputation: NaN → column median (0 for all-NaN columns)."""
    X = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X

def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1-1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0.,1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n]/counts[:n].sum()) * np.abs(frac[:n]-mean[:n])))

def _fit_lr(X: np.ndarray, y: np.ndarray) -> Pipeline:
    """LR + Platt (current production model class, ADR-0004)."""
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                               random_state=42, class_weight="balanced")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X, y)
    return pipe

def _fit_hgbc(X_df: pd.DataFrame, y: np.ndarray) -> CalibratedClassifierCV:
    """
    HGBC + isotonic calibration.

    HGBC handles NaN natively — pass raw DataFrame values including NaN.
    Isotonic calibration (cv=5) is preferred over Platt for GBM since the
    isotonic regression makes no parametric assumption about the shape of
    the calibration correction.
    """
    base = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=0.01,
        random_state=42,
    )
    cal = CalibratedClassifierCV(base, method="isotonic", cv=5)
    cal.fit(X_df.to_numpy(dtype=float), y)
    return cal

def _eval(model, X, y, name: str) -> dict:
    t0 = time.monotonic()
    p = model.predict_proba(X)[:, 1]
    elapsed = time.monotonic() - t0
    b = float(brier_score_loss(y, p))
    e = _ece(y, p)
    a = float(roc_auc_score(y, p))
    print(f"  {name:<22} Brier={b:.4f}  ECE={e:.4f}  AUC={a:.4f}  ({elapsed*1000:.0f}ms)")
    return {"brier": round(b,6), "ece": round(e,6), "auc_roc": round(a,6),
            "brier_improvement": round(NULL_BRIER-b,6), "inference_ms": round(elapsed*1000,1)}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp011.jsonl", min_severity="DEBUG")

    print(f"\n{'='*60}")
    print(f"EXP-011: Gradient Boosting Model Class Experiment (T-065)")
    print(f"Session:  {SESSION_ID}")
    print(f"Model:    HistGradientBoostingClassifier vs LogisticRegression")
    print(f"{'='*60}\n")

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load + Layer 2 + Layer 3 enrichment
    # ------------------------------------------------------------------
    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows")

    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
        print("ERROR: QS load failed", file=sys.stderr); sys.exit(1)
    ok, df_q = qs.enrich_features(df, session_id=SESSION_ID)
    if not ok:
        print("ERROR: QS enrich failed", file=sys.stderr); sys.exit(1)

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
    l1  = quant_names
    l12 = quant_names + qual_names
    l123 = quant_names + qual_names + amp_names
    print(f"[FEATURES] L1={len(l1)}  L1+L2={len(l12)}  L1+L2+L3={len(l123)}")

    # ------------------------------------------------------------------
    # 2. Splits + target
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
    # 3. Fit all four configurations
    # ------------------------------------------------------------------
    print(f"\n[FIT] Training 4 configurations...")
    t_start = time.monotonic()

    # A: LR L1+L2 (control — current production model class)
    print("  A. LR  L1+L2 (control)...")
    m_lr_l12 = _fit_lr(_impute(train[l12].to_numpy(dtype=float)), y_tr)

    # B: HGBC L1
    print("  B. HGBC L1...")
    m_hgbc_l1 = _fit_hgbc(train[l1].astype(float), y_tr)

    # C: HGBC L1+L2
    print("  C. HGBC L1+L2...")
    m_hgbc_l12 = _fit_hgbc(train[l12].astype(float), y_tr)

    # D: HGBC L1+L2+L3 (key test — does GBM find L3 signal?)
    print("  D. HGBC L1+L2+L3...")
    m_hgbc_l123 = _fit_hgbc(train[l123].astype(float), y_tr)

    print(f"  [All fits: {time.monotonic()-t_start:.1f}s]")

    # ------------------------------------------------------------------
    # 4. Evaluate on TEST
    # ------------------------------------------------------------------
    print(f"\n[EVAL] TEST set (n={len(test):,}):")
    X_te_l12 = _impute(test[l12].to_numpy(dtype=float))  # LR needs imputation
    r_lr_l12   = _eval(m_lr_l12,   X_te_l12,                   y_te, "A. LR  L1+L2")
    r_hgbc_l1  = _eval(m_hgbc_l1,  test[l1].to_numpy(dtype=float),   y_te, "B. HGBC L1")
    r_hgbc_l12 = _eval(m_hgbc_l12, test[l12].to_numpy(dtype=float),  y_te, "C. HGBC L1+L2")
    r_hgbc_l123= _eval(m_hgbc_l123,test[l123].to_numpy(dtype=float), y_te, "D. HGBC L1+L2+L3")

    # ------------------------------------------------------------------
    # 5. Results analysis
    # ------------------------------------------------------------------
    best_hgbc_brier = min(r_hgbc_l1["brier"], r_hgbc_l12["brier"], r_hgbc_l123["brier"])
    hgbc_vs_lr      = r_lr_l12["brier"] - best_hgbc_brier  # positive = HGBC better
    l3_effect_hgbc  = r_hgbc_l12["brier"] - r_hgbc_l123["brier"]  # positive = L3 helps HGBC

    print(f"\n{'='*60}")
    print("EXP-011 RESULTS — GRADIENT BOOSTING vs LOGISTIC REGRESSION")
    print(f"{'='*60}")
    print(f"\n  {'Config':<22} {'Brier':>8}  {'vs null':>8}  {'ECE':>8}  {'AUC':>7}")
    print(f"  {'-'*58}")
    for label, r, note in [
        ("A. LR  L1+L2",   r_lr_l12,    "(EXP-008 baseline)"),
        ("B. HGBC L1",      r_hgbc_l1,   ""),
        ("C. HGBC L1+L2",   r_hgbc_l12,  ""),
        ("D. HGBC L1+L2+L3",r_hgbc_l123, "← KEY TEST"),
    ]:
        print(f"  {label:<22} {r['brier']:>8.4f}  {r['brier_improvement']:>+8.4f}  "
              f"{r['ece']:>8.4f}  {r['auc_roc']:>7.4f}  {note}")

    print(f"\n  LR baselines (for reference):")
    print(f"    L1 only:    {LR_L1_BRIER:.4f}  |  L1+L2: {LR_L12_BRIER:.4f}  |  L1+L2+L3: {LR_L123_BRIER:.4f}")

    print(f"\n  HGBC vs LR (best HGBC vs best LR):  {hgbc_vs_lr:>+.4f}")
    print(f"  L3 effect on HGBC (L1+L2 vs L1+L2+L3): {l3_effect_hgbc:>+.4f}")

    if hgbc_vs_lr >= ADR_TRIGGER_DELTA:
        model_rec = "ADR_AMENDMENT_RECOMMENDED"
        model_msg = (f"HGBC outperforms LR by {hgbc_vs_lr:.4f} Brier (≥ threshold {ADR_TRIGGER_DELTA}). "
                     f"Recommend ADR-0004 amendment to promote HGBC as model class.")
    elif hgbc_vs_lr > 0:
        model_rec = "HGBC_MARGINAL_IMPROVEMENT"
        model_msg = (f"HGBC improves Brier by {hgbc_vs_lr:.4f} — below ADR threshold ({ADR_TRIGGER_DELTA}). "
                     f"Marginal improvement; LR remains justified for now.")
    else:
        model_rec = "LR_RETAINED"
        model_msg = (f"HGBC does not improve over LR at this dataset scale. "
                     f"LR (ADR-0004) remains the appropriate model class.")

    if l3_effect_hgbc >= 0.002:
        l3_rec = "L3_SIGNAL_CONFIRMED_FOR_HGBC"
        l3_msg = f"Layer 3 adds {l3_effect_hgbc:.4f} Brier improvement for HGBC — validates amplification architecture."
    elif l3_effect_hgbc > 0:
        l3_rec = "L3_MARGINAL_FOR_HGBC"
        l3_msg = f"Layer 3 adds marginal Brier improvement for HGBC ({l3_effect_hgbc:.4f})."
    else:
        l3_rec = "L3_NOT_EXPLOITED_BY_HGBC"
        l3_msg = f"Layer 3 does not improve HGBC ({l3_effect_hgbc:.4f}). Amplification contexts may need refinement."

    print(f"\n  FINDING — Model class:    {model_rec}")
    print(f"    {model_msg}")
    print(f"  FINDING — Layer 3:        {l3_rec}")
    print(f"    {l3_msg}")
    print(f"{'='*60}\n")

    out = {
        "exp_id": EXP_ID, "session_id": SESSION_ID, "run_at": _utc_now(),
        "feature_counts": {"l1": len(l1), "l12": len(l12), "l123": len(l123)},
        "split": {"train": len(train), "val": len(val), "test": len(test)},
        "results": {
            "A_lr_l12":    r_lr_l12,
            "B_hgbc_l1":   r_hgbc_l1,
            "C_hgbc_l12":  r_hgbc_l12,
            "D_hgbc_l123": r_hgbc_l123,
        },
        "lr_baselines": {"l1": LR_L1_BRIER, "l12": LR_L12_BRIER, "l123": LR_L123_BRIER},
        "hgbc_vs_lr_brier_delta": round(hgbc_vs_lr, 6),
        "l3_effect_on_hgbc": round(l3_effect_hgbc, 6),
        "adr_trigger_threshold": ADR_TRIGGER_DELTA,
        "model_class_finding": model_rec,
        "l3_finding": l3_rec,
        "model_class_message": model_msg,
        "l3_message": l3_msg,
        "null_brier": NULL_BRIER,
    }
    out_path = OUTPUT_DIR / "EXP-011_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr); sys.exit(1)
    main()

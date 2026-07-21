"""
EXP-013: Strategy I — Poisson/NB Scoring Distribution Model
=============================================================
Experiment ID:  EXP-013
Phase:          Phase 7 (T-076 — Strategy I implementation)
Status:         RUNNER — 2026-05-29

Hypothesis:
  HYP-007: The Negative Binomial scoring distribution model prices any threshold
  line with Brier score competitive with LR+Platt on same-threshold comparison.

Key advantage over Strategy A (LR):
  LR requires one trained model per specific threshold line.
  NB fits one distribution per player → prices ALL threshold lines.
  This multiplies addressable markets without retraining.

Evaluation approach:
  1. Fit NB distribution per player on TRAIN pts values
  2. For each TRAIN threshold (pts_l10_mean), compute P(X ≥ threshold) from NB
  3. Compare NB Brier vs LR Brier on TEST set for same player/threshold combos
  4. Secondary: show that NB can price 5 threshold lines per player correctly

Uses existing EXP-005 feature matrix (no new data pull required).

How to run:
  PYTHONPATH=src python3 src/prediction_market_bot/run_exp013.py

Security (NFR-05):
  No API keys required. BOT_C4_ACTIVE must NOT be set.
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

from prediction_market_bot.c3_forecasting.scoring_distribution import ScoringDistributionModel
from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from typing import Any

EXP_ID     = "EXP-013"
SESSION_ID = f"EXP-013-{uuid.uuid4().hex[:8].upper()}"
OUTPUT_DIR = Path("exp_output/EXP-013")

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
SNAPSHOT_ID = "SNAP-2026-05-28-002"

FEATURE_WINDOW = 10
NULL_BRIER     = 0.2500

# Baseline: EXP-007 production LR model
LR_BRIER   = 0.2461
LR_ECE     = 0.0342
LR_AUC     = 0.5765

# HYP-007: NB Brier within this delta of LR is "competitive"
COMPETITIVE_GATE = 0.010

_NON_FEATURE = {
    "player_id","player_name","team_id","team_abbreviation","game_id","game_date",
    "season","season_type","min","pts","reb","ast","stl","blk","tov","pf",
    "fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm","fta","ft_pct","plus_minus",
    "snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    "prf_primary","prf_secondary","prf_hybrid_weight",
    "season_type_is_playoffs","days_since_last_game","b2b_flag","load_games_l7d",
    "eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
}


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return t


def _impute(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X


def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1 - 1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0., 1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac[:n] - mean[:n])))


def _fit_lr(X_tr: np.ndarray, y_tr: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                              random_state=42, class_weight="balanced", penalty="l2")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X_tr, y_tr)
    return pipe


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp013.jsonl", min_severity="DEBUG")

    print(f"\n{'='*65}")
    print(f"EXP-013: Strategy I — Poisson/NB Scoring Distribution Model")
    print(f"Session:  {SESSION_ID}")
    print(f"Baseline: LR Brier {LR_BRIER} | ECE {LR_ECE} | AUC {LR_AUC}")
    print(f"Gate:     NB Brier within {COMPETITIVE_GATE} of LR to confirm HYP-007")
    print(f"{'='*65}\n")

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr)
        sys.exit(1)

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run EXP-005 first.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load + enrich feature matrix
    # ------------------------------------------------------------------
    df = pd.read_csv(FEATURE_CSV)
    print(f"[DATA] {len(df):,} rows")

    if QS_CSV.exists():
        qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
        if qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
            ok, df = qs.enrich_features(df, session_id=SESSION_ID)
            if not ok:
                print("WARNING: QS enrichment failed — running without qualitative features")
    else:
        print(f"[QS] Not found — running without qualitative features")

    # ------------------------------------------------------------------
    # 2. Splits
    # ------------------------------------------------------------------
    df["y_target"] = _build_target(df)
    usable = df[df["y_target"].notna() & df["temporal_cutoff"].notna()].copy()
    train_df = usable[usable["train_test_label"] == "TRAIN"].copy()
    test_df  = usable[usable["train_test_label"] == "TEST"].copy()
    print(f"[SPLIT] TRAIN {len(train_df):,} | TEST {len(test_df):,}")

    # ------------------------------------------------------------------
    # 3. LR baseline on TEST (for direct comparison)
    # ------------------------------------------------------------------
    try:
        qual_names = (
            QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
            .get_qualitative_feature_names()
            if QS_CSV.exists() else []
        )
    except Exception:
        qual_names = []

    quant_names = [c for c in train_df.columns
                   if c not in _NON_FEATURE and c not in set(qual_names)]
    lr_feature_names = quant_names + qual_names

    print(f"\n[LR] Fitting baseline on TRAIN ({len(lr_feature_names)} features)...")
    X_tr = _impute(train_df[lr_feature_names].to_numpy(dtype=float))
    y_tr = train_df["y_target"].astype(int).to_numpy()
    lr_model = _fit_lr(X_tr, y_tr)

    X_te = _impute(test_df[lr_feature_names].to_numpy(dtype=float))
    y_te = test_df["y_target"].astype(int).to_numpy()
    p_lr = lr_model.predict_proba(X_te)[:, 1]
    lr_brier = float(brier_score_loss(y_te, p_lr))
    lr_ece   = _ece(y_te, p_lr)
    lr_auc   = float(roc_auc_score(y_te, p_lr))
    print(f"[LR]  TEST Brier {lr_brier:.4f} | ECE {lr_ece:.4f} | AUC {lr_auc:.4f}")

    # ------------------------------------------------------------------
    # 4. NB scoring distribution model
    # ------------------------------------------------------------------
    print(f"\n[NB] Building per-player pts distributions on TRAIN set...")
    pts_by_player: dict[int, np.ndarray] = {}
    for pid, grp in train_df.groupby("player_id"):
        pts_vals = pd.to_numeric(grp["pts"], errors="coerce").dropna().to_numpy()
        if len(pts_vals) > 0:
            pts_by_player[int(pid)] = pts_vals

    nb_model = ScoringDistributionModel()
    nb_model.fit(pts_by_player)
    print(f"[NB] Fitted {nb_model.n_fitted_players}/{len(pts_by_player)} players "
          f"(skipped those with < {nb_model._min_samples} games)")

    # NB predictions on TEST set
    pts_col = f"pts_l{FEATURE_WINDOW}_mean"
    nb_probs: list[float] = []
    nb_y: list[int] = []
    nb_lr_probs: list[float] = []
    players_priced = set()

    for idx, row in test_df.iterrows():
        pid = int(row["player_id"])
        threshold = float(row.get(pts_col, np.nan))
        if np.isnan(threshold):
            continue

        p_nb = nb_model.predict_threshold_prob(pid, threshold)
        if p_nb is None:
            continue

        nb_probs.append(p_nb)
        nb_y.append(int(row["y_target"]))
        players_priced.add(pid)

        # LR prediction for same row (for direct per-row comparison)
        row_X = _impute(row[lr_feature_names].to_frame().T.to_numpy(dtype=float))
        nb_lr_probs.append(float(lr_model.predict_proba(row_X)[0, 1]))

    nb_probs_arr = np.array(nb_probs)
    nb_y_arr = np.array(nb_y)
    nb_lr_arr = np.array(nb_lr_probs)

    if len(nb_y_arr) == 0:
        print("[NB] No NB predictions produced — check player ID coverage")
        return

    nb_brier = float(brier_score_loss(nb_y_arr, nb_probs_arr))
    nb_ece   = _ece(nb_y_arr, nb_probs_arr)
    nb_auc   = float(roc_auc_score(nb_y_arr, nb_probs_arr)) if len(set(nb_y_arr)) > 1 else float("nan")

    # LR on same subset
    lr_subset_brier = float(brier_score_loss(nb_y_arr, nb_lr_arr))

    print(f"\n[NB]  TEST ({len(nb_y_arr)} rows, {len(players_priced)} players)")
    print(f"  NB  Brier {nb_brier:.4f} | ECE {nb_ece:.4f} | AUC {nb_auc:.4f}")
    print(f"  LR  Brier {lr_subset_brier:.4f} (same subset, same thresholds)")
    delta_nb_lr = lr_subset_brier - nb_brier
    print(f"  Δ (LR - NB Brier): {delta_nb_lr:+.4f} (positive = NB better)")

    # ------------------------------------------------------------------
    # 5. Multi-line pricing demonstration
    # ------------------------------------------------------------------
    print(f"\n[NB] Multi-line pricing demonstration:")
    sample_players = list(nb_model.get_fitted_player_ids())[:5]
    thresholds = [15.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0]
    for pid in sample_players:
        dist = nb_model.get_distribution(pid)
        probs = nb_model.price_all_lines(pid, thresholds)
        name = train_df[train_df["player_id"] == pid]["player_name"].iloc[0] \
               if len(train_df[train_df["player_id"] == pid]) > 0 else str(pid)
        dist_type = dist.dist_type if dist else "?"
        mu_str = f"{dist.mu:.1f}" if dist else "0"
        print(f"  {name:<28} ({dist_type}, μ={mu_str})")
        for t, p in zip(thresholds, probs):
            bar = "★" if p is not None and 0.40 < p < 0.60 else " "
            p_str = f"{p:.3f}" if p is not None else "N/A "
            print(f"    P(≥{int(t):>2}) = {p_str} {bar}")

    # ------------------------------------------------------------------
    # 6. HYP-007 verdict
    # ------------------------------------------------------------------
    delta_vs_gate = lr_subset_brier - nb_brier
    hyp_verdict = "CONFIRMED" if delta_vs_gate > -COMPETITIVE_GATE else "FALSIFIED"

    print(f"\n{'='*65}")
    print(f"HYP-007: NB within {COMPETITIVE_GATE} Brier of LR on same-threshold comparison")
    print(f"  NB Brier:  {nb_brier:.4f}")
    print(f"  LR Brier:  {lr_subset_brier:.4f} (same subset)")
    print(f"  Δ: {delta_vs_gate:+.4f}")
    print(f"  Verdict:   {hyp_verdict}")
    if hyp_verdict == "FALSIFIED":
        print(f"  Note: NB is worse by >{COMPETITIVE_GATE} Brier — LR+Platt remains superior")
    print(f"{'='*65}")

    # ------------------------------------------------------------------
    # 7. Save
    # ------------------------------------------------------------------
    dist_summary: list[dict[str, Any]] = []
    for pid in nb_model.get_fitted_player_ids()[:20]:
        d = nb_model.get_distribution(pid)
        if d:
            dist_summary.append({
                "player_id": pid, "dist_type": d.dist_type,
                "mu": round(d.mu, 2), "r": round(d.r, 3) if d.r else None,
                "n_samples": d.n_samples,
            })

    out = {
        "exp_id": EXP_ID, "session_id": SESSION_ID, "run_at": _utc_now(),
        "n_fitted_players": nb_model.n_fitted_players,
        "test_rows_nb": len(nb_y_arr),
        "nb_brier": round(nb_brier, 6), "nb_ece": round(nb_ece, 6), "nb_auc": round(nb_auc, 6) if not np.isnan(nb_auc) else None,
        "lr_brier_full": round(lr_brier, 6), "lr_brier_subset": round(lr_subset_brier, 6),
        "delta_nb_lr_brier": round(delta_nb_lr, 6),
        "hyp_007_verdict": hyp_verdict, "competitive_gate": COMPETITIVE_GATE,
        "dist_summary_sample": dist_summary,
        "lr_comparison": {"brier": round(LR_BRIER, 6), "ece": round(LR_ECE, 6), "auc": LR_AUC},
    }
    out_path = OUTPUT_DIR / "EXP-013_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()

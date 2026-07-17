"""
EXP-012: Strategy B — Opponent Defensive Rating + Home/Away (FEATURE_VERSION 1.3.0)
=====================================================================================
Experiment ID:  EXP-012
Phase:          Phase 7 (T-075 — Strategy B feature enhancement)
Status:         RUNNER — 2026-05-29

Hypothesis:
  HYP-006: Adding opponent defensive rating (F-040) and home/away context (F-039)
  improves Brier score vs. the v1.2.0 baseline by ≥ 0.001.

  Rationale from sports analytics literature:
    - Opponent defensive rating explains ~15% of player scoring variance
    - Home court advantage is quantifiable (~3 pts/game; NBA median)
    - These features are game-specific context, not player load —
      distinguishing from HYP-005 schedule features (falsified at v1.1.0)

Feature version: 1.3.0 (31 quant + 2 new = 33 features)
  F-039: is_home_game — binary (1=home, 0=away) from C1 MATCHUP parsing
  F-040: opp_def_rating_l10_mean — opponent team's rolling avg pts allowed

Data requirement:
  EXP-012 requires a FRESH data pull (v1.3.0 columns not in EXP-005 matrix).
  Expected pull time: ~20 min (50 players × 5 seasons + 30 teams × 5 seasons)
  The runner caches the feature matrix; subsequent runs use the cached file.

Comparison baseline:
  EXP-007 production model: Brier 0.2461, ECE 0.0342, AUC 0.5765
  (v1.2.0, 31 features, QS-2026-05-28-002, 5 seasons)

How to run:
  PYTHONPATH=src python3 src/prediction_market_bot/run_exp012.py

  First run: pulls fresh data (slow, ~20 min). Saves feature matrix to
  exp_output/EXP-012/EXP-012_feature_matrix.csv for subsequent runs.

  Skip data pull (use cached matrix):
  EXP012_SKIP_PULL=1 PYTHONPATH=src python3 src/prediction_market_bot/run_exp012.py

Security (NFR-05):
  No API keys required for data pull (nba_api is public).
  BOT_C4_ACTIVE must NOT be set.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.ingestion import (
    NBAIngestionClient,
    SEASON_TYPE_REGULAR,
    SUPPORTED_SEASONS,
)
from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore
from prediction_market_bot.c2_feature_store.features import FeatureStore, FEATURE_VERSION
from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore, DS01_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.cohort import get_player_ids_v2, cohort_summary
from typing import Any

EXP_ID      = "EXP-012"
SESSION_ID  = f"EXP-012-{uuid.uuid4().hex[:8].upper()}"
OUTPUT_DIR  = Path("exp_output/EXP-012")
MATRIX_CSV  = OUTPUT_DIR / "EXP-012_feature_matrix.csv"
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
SNAPSHOT_ID = "SNAP-EXP-012-001"

# Comparison baseline (EXP-007 production model)
BASELINE_BRIER = 0.2461
BASELINE_ECE   = 0.0342
BASELINE_AUC   = 0.5765
NULL_BRIER     = 0.2500

IMPROVEMENT_GATE = 0.001  # Minimum Δ Brier to declare HYP-006 confirmed

# Full v2 cohort (~80 players) — imported from canonical cohort.py (T-071)
PLAYER_IDS: list[int] = get_player_ids_v2()

SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

TRAIN_END_DATE = "2024-04-14"
VAL_END_DATE   = "2025-04-13"

_NON_FEATURE = {
    "player_id","player_name","team_id","team_abbreviation","game_id","game_date",
    "season","season_type","matchup","opponent_team_abbr","min","pts","reb","ast",
    "stl","blk","tov","pf","fgm","fga","fg_pct","fg3m","fg3a","fg3_pct","ftm",
    "fta","ft_pct","plus_minus","snapshot_id","ingestion_run_id","ingested_at",
    "temporal_cutoff","feature_run_id","feature_version","train_test_label","y_target",
    "prf_primary","prf_secondary","prf_hybrid_weight",
    "season_type_is_playoffs","days_since_last_game","b2b_flag","load_games_l7d",
    "eri_prev_hot","eri_prev_cold","eri_consec_cold_games",
}


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = "pts_l10_mean"
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce")
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


def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1 - 1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0., 1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac[:n] - mean[:n])))


def _fit_model(X_tr: np.ndarray, y_tr: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000,
                              random_state=42, class_weight="balanced",
                              penalty="l2")
    pipe = Pipeline([("sc", StandardScaler()),
                     ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X_tr, y_tr)
    return pipe


# ---------------------------------------------------------------------------
# Data pull
# ---------------------------------------------------------------------------

def pull_feature_matrix(logger: AuditLogger) -> pd.DataFrame:
    """Pull fresh game logs + team logs, derive v1.3.0 features, return matrix."""
    print(f"\n[PULL] Fetching game logs for {len(PLAYER_IDS)} players × {len(SEASONS)} seasons...")

    ingestion = NBAIngestionClient(logger=logger, snapshot_id=SNAPSHOT_ID)

    # -- Player game logs ---------------------------------------------------
    frames: list[pd.DataFrame] = []
    for season in SEASONS:
        print(f"  Season {season} — {len(PLAYER_IDS)} players...")
        for i, pid in enumerate(PLAYER_IDS, 1):
            ok, df = ingestion.fetch_player_game_log(pid, season, SEASON_TYPE_REGULAR)
            if ok and not df.empty:
                frames.append(df)
            if i % 10 == 0:
                print(f"    [{i}/{len(PLAYER_IDS)}]")

    if not frames:
        raise RuntimeError("No player game log data fetched — check connectivity")

    game_log_df = pd.concat(frames, ignore_index=True)
    print(f"[PULL] {len(game_log_df):,} player-game rows")

    # -- Team game logs for opponent defensive rating -----------------------
    print("\n[PULL] Fetching team game logs for opponent defensive rating...")
    store = TeamStatsStore()
    all_teams = NBAIngestionClient.get_all_teams()
    for season in SEASONS:
        for team in all_teams:
            ok, tlog = ingestion.fetch_team_game_log(team["id"], season, SEASON_TYPE_REGULAR)
            if ok and not tlog.empty:
                store.add_team_log(team["abbreviation"], tlog)
    print(f"[PULL] {len(store)} team-season logs loaded into TeamStatsStore")

    # -- Feature derivation -------------------------------------------------
    print("\n[C2] Deriving v1.3.0 features...")
    feat_store = FeatureStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    ok, feature_df = feat_store.compute_features_bulk(
        game_log_df, team_stats_store=store
    )
    if not ok:
        raise RuntimeError("C2 feature derivation failed")

    ok, feature_df = feat_store.assign_train_test_labels(
        feature_df, TRAIN_END_DATE, VAL_END_DATE
    )
    if not ok:
        raise RuntimeError("Train/test labeling failed")

    feature_df["y_target"] = _build_target(feature_df)
    print(f"[C2] {len(feature_df):,} rows | FEATURE_VERSION={FEATURE_VERSION}")
    return feature_df


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(OUTPUT_DIR / "audit_exp012.jsonl", min_severity="DEBUG")

    print(f"\n{'='*65}")
    print(f"EXP-012: Strategy B — Opponent Def Rating + Home/Away")
    print(f"FEATURE_VERSION {FEATURE_VERSION} (31→33 features)")
    print(f"Session:  {SESSION_ID}")
    print(f"Baseline: Brier {BASELINE_BRIER} | ECE {BASELINE_ECE} | AUC {BASELINE_AUC}")
    print(f"Gate:     Δ Brier ≥ {IMPROVEMENT_GATE} to confirm HYP-006")
    print(f"{'='*65}\n")

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load or pull feature matrix
    # ------------------------------------------------------------------
    skip_pull = os.environ.get("EXP012_SKIP_PULL", "").strip() == "1"

    if MATRIX_CSV.exists() and skip_pull:
        print(f"[DATA] Loading cached matrix: {MATRIX_CSV}")
        df = pd.read_csv(MATRIX_CSV)
        print(f"[DATA] {len(df):,} rows loaded")
    else:
        if MATRIX_CSV.exists():
            print(f"[DATA] Cached matrix exists — re-pulling fresh (EXP012_SKIP_PULL=1 to skip)")
        df = pull_feature_matrix(logger)
        df.to_csv(MATRIX_CSV, index=False)
        print(f"[DATA] Cached: {MATRIX_CSV}")

    # ------------------------------------------------------------------
    # 2. Qualitative enrichment (PRF archetypes — same as production)
    # ------------------------------------------------------------------
    if QS_CSV.exists():
        qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
        if qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=SESSION_ID):
            ok, df = qs.enrich_features(df, session_id=SESSION_ID)
            if not ok:
                print("WARNING: QS enrichment failed — running without qualitative features")
    else:
        print(f"[QS] {QS_CSV} not found — running quantitative-only (HYP-006 partial)")

    # ------------------------------------------------------------------
    # 3. Feature selection
    # ------------------------------------------------------------------
    qual_names  = []
    if QS_CSV.exists():
        try:
            qual_names = QualitativeSignalStore(
                logger=logger, snapshot_id=SNAPSHOT_ID
            ).get_qualitative_feature_names()
        except Exception:
            pass

    quant_names = [c for c in df.columns if c not in _NON_FEATURE and c not in set(qual_names)]
    feature_names_v13 = quant_names + qual_names

    # v1.2.0 subset (exclude new features for ablation comparison)
    v12_exclude = {"is_home_game", "opp_def_rating_l10_mean"}
    feature_names_v12 = [f for f in feature_names_v13 if f not in v12_exclude]

    print(f"[FEATURES] v1.3.0: {len(feature_names_v13)} | v1.2.0 subset: {len(feature_names_v12)}")

    # ------------------------------------------------------------------
    # 4. Train / test split
    # ------------------------------------------------------------------
    if "y_target" not in df.columns:
        df["y_target"] = _build_target(df)

    usable = df[df["y_target"].notna() & df["temporal_cutoff"].notna()].copy()
    train_df = usable[usable["train_test_label"] == "TRAIN"].copy()
    val_df   = usable[usable["train_test_label"] == "VALIDATION"].copy()
    test_df  = usable[usable["train_test_label"] == "TEST"].copy()
    print(f"[SPLIT] TRAIN {len(train_df):,} | VAL {len(val_df):,} | TEST {len(test_df):,}")

    # ------------------------------------------------------------------
    # 5. Fit and evaluate both versions
    # ------------------------------------------------------------------
    results: dict[str, Any] = {"exp_id": EXP_ID, "session_id": SESSION_ID, "run_at": _utc_now(),
                     "feature_version": FEATURE_VERSION, "baseline_brier": BASELINE_BRIER}

    for label, fnames in [("v1.3.0", feature_names_v13), ("v1.2.0_subset", feature_names_v12)]:
        print(f"\n[{label}] Fitting on TRAIN ({len(fnames)} features)...")
        # Filter to features present in df
        available = [f for f in fnames if f in train_df.columns]
        if not available:
            print(f"  No features available for {label} — skipping")
            continue

        X_tr = _impute(train_df[available].to_numpy(dtype=float))
        y_tr = train_df["y_target"].astype(int).to_numpy()
        model = _fit_model(X_tr, y_tr)

        for split_name, split_df in [("VAL", val_df), ("TEST", test_df)]:
            if split_df.empty:
                continue
            X_ev = _impute(split_df[available].to_numpy(dtype=float))
            y_ev = split_df["y_target"].astype(int).to_numpy()
            p_ev = model.predict_proba(X_ev)[:, 1]

            brier = float(brier_score_loss(y_ev, p_ev))
            ece   = _ece(y_ev, p_ev)
            auc   = float(roc_auc_score(y_ev, p_ev))
            delta = NULL_BRIER - brier

            print(f"  [{split_name}] Brier {brier:.4f} (Δ vs null: {delta:+.4f}) "
                  f"| ECE {ece:.4f} | AUC {auc:.4f}")

            results[f"{label}_{split_name.lower()}"] = {
                "brier": round(brier, 6), "ece": round(ece, 6),
                "auc_roc": round(auc, 6), "brier_improvement": round(delta, 6),
                "n_features": len(available), "n_rows": len(split_df),
            }

    # ------------------------------------------------------------------
    # 6. HYP-006 verdict
    # ------------------------------------------------------------------
    v13_test = results.get("v1.3.0_test", {})
    v12_test = results.get("v1.2.0_subset_test", {})

    if v13_test and v12_test:
        delta_vs_v12 = v12_test["brier"] - v13_test["brier"]
        delta_vs_baseline = BASELINE_BRIER - v13_test["brier"]
        hyp_verdict = "CONFIRMED" if delta_vs_v12 >= IMPROVEMENT_GATE else "FALSIFIED"

        print(f"\n{'='*65}")
        print(f"HYP-006 RESULT: {hyp_verdict}")
        print(f"  v1.3.0 TEST Brier: {v13_test['brier']:.4f}")
        print(f"  v1.2.0 TEST Brier: {v12_test['brier']:.4f}")
        print(f"  Δ (v1.3.0 vs v1.2.0): {delta_vs_v12:+.4f} (gate: {IMPROVEMENT_GATE})")
        print(f"  Δ vs production baseline (EXP-007): {delta_vs_baseline:+.4f}")
        print(f"{'='*65}")

        results["hyp_006_verdict"]      = hyp_verdict
        results["delta_vs_v12"]         = round(delta_vs_v12, 6)
        results["delta_vs_baseline"]    = round(delta_vs_baseline, 6)
    else:
        print("\n[WARN] Insufficient results for HYP-006 verdict")
        results["hyp_006_verdict"] = "INCONCLUSIVE"

    # ------------------------------------------------------------------
    # 7. Save
    # ------------------------------------------------------------------
    out_path = OUTPUT_DIR / "EXP-012_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()

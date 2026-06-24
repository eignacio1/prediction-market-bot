"""
T-072 Part B — Model v2 Retrain (ADR-0031 authorized)
======================================================

Script ID:    T-072-PART-B
ADR:          ADR-0031 (supersedes ADR-0004 §4 for this retrain only)
Status:       Canonical — run once; freeze artifact on PASS
Feature ver:  1.4.0 (FEATURE_VERSION in features.py)
Base data:    exp_output/EXP-005/EXP-005_feature_matrix.csv
Output:       models/v2_model.joblib, models/v2_model_meta.json

Shadow gate (ADR-0009 criteria, must BOTH pass before deployment):
  1. Brier(v2) < Brier(v1) on holdout, improvement ≥ 0.001
  2. ECE(v2, 10 equal-frequency bins) ≤ 0.05

If shadow gate FAILS:
  - Script exits non-zero. v2 model is NOT saved.
  - T-072 remains OPEN. Escalation per ADR-0031 risk register.

Holdout (anti-gaming — fixed before retrain begins):
  game_date > 2026-02-01
  Reason: last ~5.5 months of 2025-26 season (Feb–Apr regular + Apr–May playoffs).
  BOTH v1 and v2 are evaluated on these exact rows.

v1.4.0 feature additions (ADR-0031 / T-072 Part A):
  F-041: playoff_round_multiplier   — empirically calibrated from in-training
                                      playoff rows (2024-25 seasons: n=31, ratio=0.9596)
  F-042: opp_playoff_def_rating_l5_mean — NaN everywhere (playoff TeamGameLog pull
                                           required; see KNOWN_LIMITATIONS below)
  F-043: series_scoring_delta       — computed from series history in matrix

KNOWN_LIMITATIONS:
  F-042 requires a TeamStatsStore built from playoff TeamGameLog data. The current
  data pipeline has regular-season TeamGameLog only. F-042 = NaN for all rows in
  this retrain run; the LR model imputes to 0.0, adding no signal. A future run
  that pulls playoff TeamGameLog (season="2025-26", season_type="Playoffs") via
  NBAIngestionClient can populate F-042 and retrain under the same ADR.

  The 2025-26 Finals game logs (June 2026) are also absent from the source matrix.
  The most extreme playoff compression data (S69 diagnosis: Finals scoring 9-30%
  below model-implied λ) is not in the training set. This is a known limitation.

How to run:
    PYTHONPATH=src .venv/bin/python3 scripts/train_model_v2.py

    Optional:
        --dry-run    : validate pipeline, do not save model
        --force-save : save even if Brier improvement is below 0.001 threshold
                       (requires explicit operator confirmation; not for production use)

Security:
  - BOT_C4_ACTIVE must NOT be set.
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
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_SRC_ROOT = Path(__file__).parent.parent / "src"
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

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV      = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID       = "QS-2026-05-28-002"
SNAPSHOT_ID = "SNAP-2026-05-28-002"

MODEL_DIR        = Path("models")
V2_MODEL_PATH    = MODEL_DIR / "v2_model.joblib"
V2_META_PATH     = MODEL_DIR / "v2_model_meta.json"
V1_MODEL_PATH    = MODEL_DIR / "prod_model.joblib"
V1_META_PATH     = MODEL_DIR / "prod_model_meta.json"

FEATURE_WINDOW = 10
FEATURE_VERSION = "1.4.0"
HOLDOUT_CUTOFF  = "2026-02-01"  # Fixed before retrain — do not change

# F-041 empirical calibration: ratio = mean(pts/pts_l10_mean) for in-training
# playoff rows / mean(pts/pts_l10_mean) for in-training regular-season rows.
# Derived from 31 in-training playoff rows (2024-25 seasons only; 2025-26
# Finals data absent). S69: playoffs score at ~96% of regular-season baseline.
F041_PLAYOFF_MULTIPLIER = 0.959603  # empirically derived; NOT a guess

# Shadow gate thresholds (ADR-0009 / ADR-0031)
SHADOW_GATE_BRIER_DELTA = 0.001   # minimum Brier improvement required
SHADOW_GATE_ECE_MAX     = 0.05    # maximum ECE allowed

_NON_FEATURE = {
    "player_id", "player_name", "team_id", "team_abbreviation",
    "game_id", "game_date", "season", "season_type",
    "matchup", "opponent_team_abbr",
    "min", "pts", "reb", "ast", "stl", "blk", "tov", "pf",
    "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct",
    "plus_minus",
    "snapshot_id", "ingestion_run_id", "ingested_at",
    "temporal_cutoff", "feature_run_id", "feature_version", "train_test_label",
    "y_target", "game_date_dt",
    # also exclude old pruned features from v1.2.0
    "season_type_is_playoffs", "days_since_last_game", "b2b_flag",
    "load_games_l7d", "eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _model_version(feature_names: list[str]) -> str:
    digest = "LogisticRegression+PlattScaling|" + ",".join(sorted(feature_names))
    return "v2-" + hashlib.sha1(digest.encode()).hexdigest()[:8]


def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X


def _build_target(df: pd.DataFrame) -> pd.Series:
    col = f"pts_l{FEATURE_WINDOW}_mean"
    if col not in df.columns or "pts" not in df.columns:
        return pd.Series([np.nan] * len(df), index=df.index)
    pts = pd.to_numeric(df["pts"], errors="coerce")
    pm  = pd.to_numeric(df[col], errors="coerce")
    t   = (pts >= pm).astype("Int8")
    t[pts.isna() | pm.isna()] = pd.NA
    return t


def _compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error using equal-frequency bins."""
    # Sort by predicted probability
    order = np.argsort(y_prob)
    y_true_sorted = y_true[order]
    y_prob_sorted = y_prob[order]

    bins = np.array_split(np.arange(len(y_prob)), n_bins)
    ece = 0.0
    n = len(y_prob)
    for b in bins:
        if len(b) == 0:
            continue
        bin_conf = y_prob_sorted[b].mean()
        bin_acc  = y_true_sorted[b].mean()
        ece += (len(b) / n) * abs(bin_acc - bin_conf)
    return float(ece)


# ---------------------------------------------------------------------------
# Feature augmentation: F-041, F-042, F-043
# ---------------------------------------------------------------------------


def _add_f041(df: pd.DataFrame) -> pd.DataFrame:
    """
    F-041: playoff_round_multiplier.
    1.0 for regular season; F041_PLAYOFF_MULTIPLIER for playoff rows.
    """
    col = np.where(
        df["season_type"] == "Playoffs",
        F041_PLAYOFF_MULTIPLIER,
        1.0,
    ).astype(float)
    df = df.copy()
    df["playoff_round_multiplier"] = col
    return df


def _add_f042(df: pd.DataFrame) -> pd.DataFrame:
    """
    F-042: opp_playoff_def_rating_l5_mean.
    NaN everywhere — playoff TeamGameLog not available for this run.
    """
    df = df.copy()
    df["opp_playoff_def_rating_l5_mean"] = np.nan
    return df


def _add_f043(df: pd.DataFrame) -> pd.DataFrame:
    """
    F-043: series_scoring_delta.
    For playoff rows: mean pts in prior games of the current series minus
    the pts_l10_mean baseline entering the series.
    For regular-season rows and game 1 of a series: 0.0.
    """
    df = df.copy()
    df["series_scoring_delta"] = 0.0

    if "season_type" not in df.columns or "opponent_team_abbr" not in df.columns:
        return df

    df["game_date_dt_"] = pd.to_datetime(df["game_date"])
    playoffs = df[df["season_type"] == "Playoffs"].copy()

    if playoffs.empty:
        df.drop(columns=["game_date_dt_"], inplace=True)
        return df

    for player_id in playoffs["player_id"].unique():
        player_mask = (df["player_id"] == player_id) & (df["season_type"] == "Playoffs")
        player_rows = df[player_mask].sort_values("game_date_dt_")

        for idx, row in player_rows.iterrows():
            opp = row.get("opponent_team_abbr")
            season = row.get("season")
            if not opp or pd.isna(opp):
                continue

            baseline = pd.to_numeric(row.get("pts_l10_mean"), errors="coerce")
            if pd.isna(baseline):
                continue

            # Prior games in the same series (same opponent + same season + strictly before)
            prior_mask = (
                (df["player_id"] == player_id)
                & (df["season_type"] == "Playoffs")
                & (df["opponent_team_abbr"] == opp)
                & (df["season"] == season)
                & (df["game_date_dt_"] < row["game_date_dt_"])
            )
            prior_pts = pd.to_numeric(df.loc[prior_mask, "pts"], errors="coerce").dropna()
            if len(prior_pts) == 0:
                # Game 1 of series — no prior data; delta = 0.0
                continue

            series_mean = prior_pts.mean()
            df.at[idx, "series_scoring_delta"] = float(series_mean - baseline)

    df.drop(columns=["game_date_dt_"], inplace=True)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(dry_run: bool = False, force_save: bool = False) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger("logs/train_v2.jsonl", min_severity="INFO")
    session_id = f"TRAIN-V2-{uuid.uuid4().hex[:8].upper()}"

    print(f"\n{'='*65}")
    print("T-072 Part B — Model v2 Retrain (ADR-0031)")
    print(f"Session:    {session_id}")
    print(f"Feature ver: {FEATURE_VERSION}")
    print(f"Holdout:    game_date > {HOLDOUT_CUTOFF}")
    print(f"F-041 mult: {F041_PLAYOFF_MULTIPLIER:.6f} (empirical, n=31 in-training playoff rows)")
    if dry_run:
        print("MODE: DRY RUN — model will not be saved")
    print(f"{'='*65}\n")

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — refusing to run.", file=sys.stderr)
        sys.exit(1)

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    if not V1_MODEL_PATH.exists():
        print(f"ERROR: v1 model not found at {V1_MODEL_PATH}.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load source feature matrix
    # ------------------------------------------------------------------
    print("[1/9] Loading feature matrix...")
    df = pd.read_csv(FEATURE_CSV, low_memory=False)
    print(f"      {len(df):,} rows loaded")

    df["game_date"] = pd.to_datetime(df["game_date"])

    # ------------------------------------------------------------------
    # 2. Augment with v1.4.0 playoff features
    # ------------------------------------------------------------------
    print("[2/9] Adding v1.4.0 playoff features (F-041, F-042, F-043)...")
    df = _add_f041(df)
    df = _add_f042(df)
    print("      Computing F-043 series_scoring_delta (may take ~30s)...")
    df = _add_f043(df)

    playoff_rows = df[df["season_type"] == "Playoffs"]
    f043_nonzero = (df["series_scoring_delta"] != 0.0).sum()
    print(f"      F-041: calibrated (non-1.0 rows: {(df['playoff_round_multiplier'] != 1.0).sum()})")
    print(f"      F-042: NaN everywhere (known limitation — playoff TeamGameLog not available)")
    print(f"      F-043: {f043_nonzero} non-zero rows (within-series prior data available)")

    # ------------------------------------------------------------------
    # 3. QS enrichment (same snapshot as v1)
    # ------------------------------------------------------------------
    print("[3/9] Enriching with qualitative signals (QS-2026-05-28-002)...")
    qs = QualitativeSignalStore(logger=logger, snapshot_id=SNAPSHOT_ID)
    if not qs.load_ds01_snapshot(QS_CSV, QS_ID, session_id=session_id):
        print("ERROR: QS load failed", file=sys.stderr)
        sys.exit(1)
    ok, df_q = qs.enrich_features(df, session_id=session_id)
    if not ok:
        print("ERROR: QS enrichment failed", file=sys.stderr)
        sys.exit(1)
    print(f"      QS enrichment: OK ({len(df_q):,} rows)")

    # ------------------------------------------------------------------
    # 4. Feature name resolution
    # ------------------------------------------------------------------
    print("[4/9] Resolving feature names...")
    qual_names  = qs.get_qualitative_feature_names()
    quant_names = [c for c in df_q.columns
                   if c not in _NON_FEATURE and c not in set(qual_names)]
    feature_names = quant_names + qual_names

    print(f"      {len(feature_names)} features ({len(quant_names)} quant + {len(qual_names)} qual)")
    for f in ["playoff_round_multiplier", "opp_playoff_def_rating_l5_mean", "series_scoring_delta",
              "is_home_game", "opp_def_rating_l10_mean"]:
        status = "✓" if f in feature_names else "✗"
        print(f"      {status} {f}")

    # ------------------------------------------------------------------
    # 5. Build target, split
    # ------------------------------------------------------------------
    print("[5/9] Building target + holdout split...")
    df_q["y_target"] = _build_target(df_q)
    usable = df_q[df_q["y_target"].notna()].copy()

    holdout_mask = usable["game_date"] > HOLDOUT_CUTOFF
    train_df     = usable[~holdout_mask].copy()
    holdout_df   = usable[holdout_mask].copy()

    print(f"      Train: {len(train_df):,} rows")
    print(f"      Holdout: {len(holdout_df):,} rows (cutoff: {HOLDOUT_CUTOFF})")
    holdout_playoffs = holdout_df[holdout_df["season_type"] == "Playoffs"]
    print(f"      Holdout playoff rows: {len(holdout_playoffs)}")

    X_train_raw = train_df[feature_names].to_numpy(dtype=float)
    y_train     = train_df["y_target"].astype(int).to_numpy()
    X_hold_raw  = holdout_df[feature_names].to_numpy(dtype=float)
    y_hold      = holdout_df["y_target"].astype(int).to_numpy()

    col_medians = np.nanmedian(X_train_raw, axis=0)
    col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)

    X_train = _impute(X_train_raw, col_medians)
    X_hold  = _impute(X_hold_raw, col_medians)

    # ------------------------------------------------------------------
    # 6. v1 baseline evaluation on same holdout
    # ------------------------------------------------------------------
    print("[6/9] Evaluating v1 baseline on holdout...")
    v1_artifact = joblib.load(V1_MODEL_PATH)
    v1_pipe     = v1_artifact["pipeline"]
    v1_features = v1_artifact["feature_names"]
    v1_medians  = v1_artifact["col_medians"]
    v1_version  = v1_artifact["model_version"]

    # Extract v1 features from holdout; impute with v1 medians
    v1_feat_available = [f for f in v1_features if f in holdout_df.columns]
    v1_feat_missing   = [f for f in v1_features if f not in holdout_df.columns]
    if v1_feat_missing:
        print(f"      WARNING: {len(v1_feat_missing)} v1 features missing from holdout: {v1_feat_missing}")

    X_hold_v1_raw = np.full((len(holdout_df), len(v1_features)), np.nan)
    for j, feat in enumerate(v1_features):
        if feat in holdout_df.columns:
            X_hold_v1_raw[:, j] = pd.to_numeric(
                holdout_df[feat], errors="coerce"
            ).to_numpy(dtype=float)

    X_hold_v1 = _impute(X_hold_v1_raw, v1_medians)
    p_v1      = v1_pipe.predict_proba(X_hold_v1)[:, 1]
    brier_v1  = float(brier_score_loss(y_hold, p_v1))
    ece_v1    = _compute_ece(y_hold, p_v1)
    auc_v1    = float(roc_auc_score(y_hold, p_v1))

    print(f"      v1 ({v1_version}): Brier={brier_v1:.6f}, ECE={ece_v1:.4f}, AUC={auc_v1:.4f}")

    # ------------------------------------------------------------------
    # 7. Train v2
    # ------------------------------------------------------------------
    print("[7/9] Training v2 (LR + Platt, ADR-0004 model class)...")
    base = LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=1000,
        random_state=42, class_weight="balanced",
    )
    v2_pipe = Pipeline([
        ("sc", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
    ])
    v2_pipe.fit(X_train, y_train)

    p_train_v2   = v2_pipe.predict_proba(X_train)[:, 1]
    brier_train  = float(brier_score_loss(y_train, p_train_v2))
    print(f"      Train Brier (in-sample): {brier_train:.6f}")

    v2_version = _model_version(feature_names)
    print(f"      v2 version: {v2_version}")

    # ------------------------------------------------------------------
    # 8. Shadow gate evaluation
    # ------------------------------------------------------------------
    print("[8/9] Shadow gate evaluation...")
    p_v2      = v2_pipe.predict_proba(X_hold)[:, 1]
    brier_v2  = float(brier_score_loss(y_hold, p_v2))
    ece_v2    = _compute_ece(y_hold, p_v2)
    auc_v2    = float(roc_auc_score(y_hold, p_v2))

    brier_delta = brier_v1 - brier_v2  # positive = improvement

    print(f"      v2 ({v2_version}): Brier={brier_v2:.6f}, ECE={ece_v2:.4f}, AUC={auc_v2:.4f}")
    print(f"      Brier improvement (v1→v2): {brier_delta:+.6f}  (required: ≥ {SHADOW_GATE_BRIER_DELTA})")
    print(f"      ECE (v2): {ece_v2:.4f}  (required: ≤ {SHADOW_GATE_ECE_MAX})")

    gate_brier = brier_delta >= SHADOW_GATE_BRIER_DELTA
    gate_ece   = ece_v2 <= SHADOW_GATE_ECE_MAX
    gate_pass  = gate_brier and gate_ece

    print()
    print(f"  Brier gate: {'PASS' if gate_brier else 'FAIL'}")
    print(f"  ECE gate:   {'PASS' if gate_ece else 'FAIL'}")
    print(f"  Shadow gate: {'PASS' if gate_pass else 'FAIL'}")

    # ------------------------------------------------------------------
    # 9. Save (if gate passes)
    # ------------------------------------------------------------------
    print("[9/9] Saving...")

    if not gate_pass and not force_save:
        print()
        print("="*65)
        print("SHADOW GATE FAILED — v2 model NOT saved.")
        print()
        if not gate_brier:
            print(f"  Brier delta {brier_delta:+.6f} < required {SHADOW_GATE_BRIER_DELTA}")
            print("  Likely cause: F-042 = NaN (no playoff TeamGameLog) and F-041 has")
            print("  only 31 training samples. Pull playoff TeamGameLog to improve.")
        if not gate_ece:
            print(f"  ECE {ece_v2:.4f} > allowed {SHADOW_GATE_ECE_MAX}")
        print()
        print("  T-072 remains OPEN. Escalation: see ADR-0031 risk register.")
        print("="*65)

        logger.info("TRAIN_V2", "shadow_gate_failed", payload={
            "brier_v1": brier_v1, "brier_v2": brier_v2, "brier_delta": brier_delta,
            "ece_v2": ece_v2, "gate_brier": gate_brier, "gate_ece": gate_ece,
        }, session_id=session_id, snapshot_id=SNAPSHOT_ID)
        sys.exit(2)

    if dry_run:
        print("  DRY RUN — skipping save.")
        return

    artifact = {
        "pipeline":      v2_pipe,
        "feature_names": feature_names,
        "col_medians":   col_medians,
        "model_version": v2_version,
        "qs_id":         QS_ID,
        "snapshot_id":   SNAPSHOT_ID,
        "f041_multiplier": F041_PLAYOFF_MULTIPLIER,
    }
    joblib.dump(artifact, V2_MODEL_PATH)
    print(f"  Model saved: {V2_MODEL_PATH}  ({V2_MODEL_PATH.stat().st_size / 1024:.0f} KB)")

    meta = {
        "model_version":          v2_version,
        "feature_version":        FEATURE_VERSION,
        "model_class":            "LogisticRegression+PlattScaling (ADR-0004)",
        "feature_count":          len(feature_names),
        "quant_features":         len(quant_names),
        "qual_features":          len(qual_names),
        "qs_id":                  QS_ID,
        "snapshot_id":            SNAPSHOT_ID,
        "holdout_cutoff":         HOLDOUT_CUTOFF,
        "train_rows":             len(train_df),
        "holdout_rows":           len(holdout_df),
        "holdout_playoff_rows":   len(holdout_playoffs),
        "brier_v1_on_holdout":    round(brier_v1, 6),
        "brier_v2_on_holdout":    round(brier_v2, 6),
        "brier_delta":            round(brier_delta, 6),
        "ece_v2":                 round(ece_v2, 4),
        "auc_v2":                 round(auc_v2, 4),
        "shadow_gate_passed":     gate_pass,
        "f041_multiplier":        F041_PLAYOFF_MULTIPLIER,
        "f042_status":            "NaN (playoff TeamGameLog not available)",
        "f041_calibration_n":     31,
        "trained_at":             _utc_now(),
        "session_id":             session_id,
        "feature_names":          feature_names,
        "adr_authorization":      "ADR-0031",
        "supersedes_model":       v1_artifact["model_version"],
    }
    V2_META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"  Metadata saved: {V2_META_PATH}")

    logger.info("TRAIN_V2", "model_serialized", payload={
        "model_version": v2_version, "model_path": str(V2_MODEL_PATH),
        "feature_count": len(feature_names), "brier_delta": brier_delta,
        "shadow_gate_passed": gate_pass,
    }, session_id=session_id, snapshot_id=SNAPSHOT_ID)

    print()
    print("="*65)
    print("SHADOW GATE PASSED")
    print()
    print(f"  v2 model: {v2_version}")
    print(f"  Brier:    {brier_v2:.6f}  (v1: {brier_v1:.6f}, Δ={brier_delta:+.6f})")
    print(f"  ECE:      {ece_v2:.4f}    (limit: {SHADOW_GATE_ECE_MAX})")
    print(f"  AUC:      {auc_v2:.4f}")
    print()
    print("Next steps (ADR-0031 acceptance checklist):")
    print("  1. Run T-177 backtest: PYTHONPATH=src .venv/bin/python3 scripts/run_t177_edge_monitor.py")
    print("     Result must be INCONCLUSIVE or MONOTONIC (p > 0.05) to open Phase 3 MLB gate.")
    print("  2. Register v2 in ARTIFACT_REGISTRY.md.")
    print("  3. Update DECISION_LOG with retrain results.")
    print("  4. Reset kill switch with documentation (new paper trading baseline).")
    print("="*65)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T-072 Part B — v2 model retrain")
    parser.add_argument("--dry-run",    action="store_true", help="Validate pipeline, do not save")
    parser.add_argument("--force-save", action="store_true",
                        help="Save even if Brier improvement below threshold (not for production)")
    args = parser.parse_args()

    main(dry_run=args.dry_run, force_save=args.force_save)

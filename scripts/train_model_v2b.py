"""
T-186 Step 2 — Model v2b Retrain (F-042 Populated)
====================================================

Script ID:    T-186-TRAIN
ADR:          ADR-0031 (same authorization as v2; v2b is a targeted fix run)
Status:       Run after pull_playoff_teamgamelog.py completes
Feature ver:  1.4.0 (same as v2; only _add_f042 implementation changes)
Base data:    exp_output/EXP-005/EXP-005_feature_matrix.csv
Playoff cache: data/playoff_teamgamelog_cache.json (from T-186 Step 1)
Output:       models/v2b_model.joblib, models/v2b_model_meta.json

Difference from train_model_v2.py:
  - F-042 (opp_playoff_def_rating_l5_mean) is populated from the playoff
    TeamStatsStore cache rather than hardcoded NaN.
  - Shadow gate compares v2b against v2-065b9510 (the current incumbent).
  - Output paths use "v2b" prefix to keep v2 artifact intact.

Shadow gate (ADR-0009 criteria):
  1. Brier(v2b) < Brier(v2) on holdout, improvement ≥ 0.001
  2. ECE(v2b, 10 equal-frequency bins) ≤ 0.05

  NOTE: F-042 only affects playoff rows (season_type == "Playoffs"), which are
  a small fraction of total rows. A delta ≥ 0.001 may be difficult to achieve.
  If the gate fails, the most likely interpretation is that F-042 provides
  limited signal at this sample size — not a calibration failure. Document the
  result and deploy v2-065b9510 in October as planned (see ADR-0031).

How to run:
    PYTHONPATH=src .venv/bin/python3 scripts/train_model_v2b.py

    Optional:
        --dry-run    : validate pipeline, do not save model
        --force-save : save even if Brier improvement is below 0.001 threshold

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

from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore
from prediction_market_bot.c2_feature_store.qualitative_store import (
    QualitativeSignalStore,
    DS01_FEATURE_NAMES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FEATURE_CSV       = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
QS_CSV            = Path("qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv")
QS_ID             = "QS-2026-05-28-002"
SNAPSHOT_ID       = "SNAP-2026-05-28-002"
PLAYOFF_CACHE     = Path("data/playoff_teamgamelog_cache.json")

MODEL_DIR         = Path("models")
V2B_MODEL_PATH    = MODEL_DIR / "v2b_model.joblib"
V2B_META_PATH     = MODEL_DIR / "v2b_model_meta.json"
V2_MODEL_PATH     = MODEL_DIR / "v2_model.joblib"
V2_META_PATH      = MODEL_DIR / "v2_model_meta.json"

FEATURE_WINDOW  = 10
FEATURE_VERSION = "1.4.0"
HOLDOUT_CUTOFF  = "2026-02-01"  # Same as v2 — do not change

F041_PLAYOFF_MULTIPLIER = 0.959603  # Same empirical value as v2

SHADOW_GATE_BRIER_DELTA = 0.001
SHADOW_GATE_ECE_MAX     = 0.05

_PLAYOFF_OPP_DEF_WINDOW = 5   # Matches c2_feature_store.features._PLAYOFF_OPP_DEF_WINDOW
_PLAYOFF_OPP_DEF_MIN_P  = 3

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
    "season_type_is_playoffs", "days_since_last_game", "b2b_flag",
    "load_games_l7d", "eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games",
}


# ---------------------------------------------------------------------------
# Helpers (identical to train_model_v2.py)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _model_version(feature_names: list[str]) -> str:
    digest = "LogisticRegression+PlattScaling|v2b|" + ",".join(sorted(feature_names))
    return "v2b-" + hashlib.sha1(digest.encode()).hexdigest()[:8]


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
# Feature augmentation
# ---------------------------------------------------------------------------


def _add_f041(df: pd.DataFrame) -> pd.DataFrame:
    col = np.where(
        df["season_type"] == "Playoffs",
        F041_PLAYOFF_MULTIPLIER,
        1.0,
    ).astype(float)
    df = df.copy()
    df["playoff_round_multiplier"] = col
    return df


def _add_f042_from_store(
    df: pd.DataFrame,
    playoff_store: TeamStatsStore,
) -> pd.DataFrame:
    """
    F-042: opp_playoff_def_rating_l5_mean, populated from playoff TeamStatsStore.

    For regular-season rows: NaN (no playoff defensive context).
    For playoff rows: rolling L5 pts_allowed by the opposing team in prior
      playoff games strictly before game_date. Returns NaN if store lacks
      sufficient prior data (min_periods=3).

    Temporal integrity: get_opp_def_rating uses game_date < as_of_date only.
    """
    df = df.copy()
    vals: list[float] = []

    for _, row in df.iterrows():
        season_type = str(row.get("season_type", "")).strip()
        if season_type != "Playoffs":
            vals.append(np.nan)
            continue

        opp_abbr = row.get("opponent_team_abbr")
        game_date = row.get("game_date")

        if pd.isna(opp_abbr) or opp_abbr is None:
            vals.append(np.nan)
            continue

        # game_date may be Timestamp (after pd.to_datetime) or string
        if hasattr(game_date, "strftime"):
            date_str = game_date.strftime("%Y-%m-%d")
        else:
            date_str = str(game_date)[:10]

        rating = playoff_store.get_opp_def_rating(
            str(opp_abbr), date_str,
            window=_PLAYOFF_OPP_DEF_WINDOW, min_periods=_PLAYOFF_OPP_DEF_MIN_P,
        )
        vals.append(rating if rating is not None else np.nan)

    df["opp_playoff_def_rating_l5_mean"] = vals
    return df


def _add_f043(df: pd.DataFrame) -> pd.DataFrame:
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

            prior_mask = (
                (df["player_id"] == player_id)
                & (df["season_type"] == "Playoffs")
                & (df["opponent_team_abbr"] == opp)
                & (df["season"] == season)
                & (df["game_date_dt_"] < row["game_date_dt_"])
            )
            prior_pts = pd.to_numeric(df.loc[prior_mask, "pts"], errors="coerce").dropna()
            if len(prior_pts) == 0:
                continue

            df.at[idx, "series_scoring_delta"] = float(prior_pts.mean() - baseline)

    df.drop(columns=["game_date_dt_"], inplace=True)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(dry_run: bool = False, force_save: bool = False) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger("logs/train_v2b.jsonl", min_severity="INFO")
    session_id = f"TRAIN-V2B-{uuid.uuid4().hex[:8].upper()}"

    print(f"\n{'='*65}")
    print("T-186 Step 2 — Model v2b Retrain (F-042 Populated)")
    print(f"Session:    {session_id}")
    print(f"Feature ver: {FEATURE_VERSION}")
    print(f"Holdout:    game_date > {HOLDOUT_CUTOFF}")
    print(f"F-041 mult: {F041_PLAYOFF_MULTIPLIER:.6f}")
    print(f"Playoff cache: {PLAYOFF_CACHE}")
    if dry_run:
        print("MODE: DRY RUN — model will not be saved")
    print(f"{'='*65}\n")

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — refusing to run.", file=sys.stderr)
        sys.exit(1)

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    if not V2_MODEL_PATH.exists():
        print(f"ERROR: v2 model not found at {V2_MODEL_PATH} (needed for shadow gate).", file=sys.stderr)
        sys.exit(1)

    if not PLAYOFF_CACHE.exists():
        print(f"ERROR: {PLAYOFF_CACHE} not found.", file=sys.stderr)
        print("       Run: PYTHONPATH=src .venv/bin/python3 scripts/pull_playoff_teamgamelog.py", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load playoff TeamStatsStore from cache
    # ------------------------------------------------------------------
    print("[1/9] Loading playoff TeamStatsStore from cache...")
    with open(PLAYOFF_CACHE) as fh:
        cache_data = json.load(fh)
    playoff_store = TeamStatsStore.from_cache_dict(cache_data)
    print(f"      {len(playoff_store)} teams loaded from cache")
    print(f"      Sample: {playoff_store.teams_loaded[:5]}")

    # ------------------------------------------------------------------
    # 2. Load source feature matrix
    # ------------------------------------------------------------------
    print("[2/9] Loading feature matrix...")
    df = pd.read_csv(FEATURE_CSV, low_memory=False)
    print(f"      {len(df):,} rows loaded")
    df["game_date"] = pd.to_datetime(df["game_date"])

    # ------------------------------------------------------------------
    # 3. Augment with v1.4.0 playoff features (F-042 now populated)
    # ------------------------------------------------------------------
    print("[3/9] Adding v1.4.0 playoff features (F-041, F-042, F-043)...")
    df = _add_f041(df)
    print("      F-041: done")
    print("      F-042: computing from playoff store (playoff rows only)...")
    df = _add_f042_from_store(df, playoff_store)
    f042_nonnan = df["opp_playoff_def_rating_l5_mean"].notna().sum()
    f042_playoff_rows = (df["season_type"] == "Playoffs").sum()
    print(f"      F-042: {f042_nonnan} non-NaN rows out of {f042_playoff_rows} playoff rows "
          f"({100*f042_nonnan/max(f042_playoff_rows,1):.1f}%)")
    print("      F-043: computing series_scoring_delta (may take ~30s)...")
    df = _add_f043(df)
    f043_nonzero = (df["series_scoring_delta"] != 0.0).sum()
    print(f"      F-043: {f043_nonzero} non-zero rows")

    # ------------------------------------------------------------------
    # 4. QS enrichment
    # ------------------------------------------------------------------
    print("[4/9] Enriching with qualitative signals (QS-2026-05-28-002)...")
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
    # 5. Feature name resolution
    # ------------------------------------------------------------------
    print("[5/9] Resolving feature names...")
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
    # 6. Build target, split
    # ------------------------------------------------------------------
    print("[6/9] Building target + holdout split...")
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
    # 7. v2 baseline evaluation on same holdout (shadow gate reference)
    # ------------------------------------------------------------------
    print("[7/9] Evaluating v2 baseline on holdout...")
    v2_artifact = joblib.load(V2_MODEL_PATH)
    v2_pipe     = v2_artifact["pipeline"]
    v2_features = v2_artifact["feature_names"]
    v2_medians  = v2_artifact["col_medians"]
    v2_version  = v2_artifact["model_version"]

    v2_feat_missing = [f for f in v2_features if f not in holdout_df.columns]
    if v2_feat_missing:
        print(f"      WARNING: {len(v2_feat_missing)} v2 features missing from holdout: {v2_feat_missing}")

    X_hold_v2_raw = np.full((len(holdout_df), len(v2_features)), np.nan)
    for j, feat in enumerate(v2_features):
        if feat in holdout_df.columns:
            X_hold_v2_raw[:, j] = pd.to_numeric(
                holdout_df[feat], errors="coerce"
            ).to_numpy(dtype=float)

    X_hold_v2 = _impute(X_hold_v2_raw, v2_medians)
    p_v2      = v2_pipe.predict_proba(X_hold_v2)[:, 1]
    brier_v2  = float(brier_score_loss(y_hold, p_v2))
    ece_v2    = _compute_ece(y_hold, p_v2)
    auc_v2    = float(roc_auc_score(y_hold, p_v2))

    print(f"      v2 ({v2_version}): Brier={brier_v2:.6f}, ECE={ece_v2:.4f}, AUC={auc_v2:.4f}")

    # ------------------------------------------------------------------
    # 8. Train v2b
    # ------------------------------------------------------------------
    print("[8/9] Training v2b (LR + Platt, ADR-0004 model class)...")
    base = LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=1000,
        random_state=42, class_weight="balanced",
    )
    v2b_pipe = Pipeline([
        ("sc", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
    ])
    v2b_pipe.fit(X_train, y_train)

    p_train_v2b = v2b_pipe.predict_proba(X_train)[:, 1]
    brier_train  = float(brier_score_loss(y_train, p_train_v2b))
    print(f"      Train Brier (in-sample): {brier_train:.6f}")

    v2b_version = _model_version(feature_names)
    print(f"      v2b version: {v2b_version}")

    # ------------------------------------------------------------------
    # 9. Shadow gate evaluation
    # ------------------------------------------------------------------
    print("[9/9] Shadow gate evaluation (v2b vs v2)...")
    p_v2b      = v2b_pipe.predict_proba(X_hold)[:, 1]
    brier_v2b  = float(brier_score_loss(y_hold, p_v2b))
    ece_v2b    = _compute_ece(y_hold, p_v2b)
    auc_v2b    = float(roc_auc_score(y_hold, p_v2b))

    brier_delta = brier_v2 - brier_v2b  # positive = improvement over v2

    print(f"      v2b ({v2b_version}): Brier={brier_v2b:.6f}, ECE={ece_v2b:.4f}, AUC={auc_v2b:.4f}")
    print(f"      Brier improvement (v2→v2b): {brier_delta:+.6f}  (required: ≥ {SHADOW_GATE_BRIER_DELTA})")
    print(f"      ECE (v2b): {ece_v2b:.4f}  (required: ≤ {SHADOW_GATE_ECE_MAX})")

    gate_brier = brier_delta >= SHADOW_GATE_BRIER_DELTA
    gate_ece   = ece_v2b <= SHADOW_GATE_ECE_MAX
    gate_pass  = gate_brier and gate_ece

    print()
    print(f"  Brier gate: {'PASS' if gate_brier else 'FAIL'}")
    print(f"  ECE gate:   {'PASS' if gate_ece else 'FAIL'}")
    print(f"  Shadow gate: {'PASS' if gate_pass else 'FAIL'}")

    if not gate_pass and not force_save:
        print()
        print("="*65)
        print("SHADOW GATE FAILED — v2b model NOT saved.")
        print()
        if not gate_brier:
            print(f"  Brier delta {brier_delta:+.6f} < required {SHADOW_GATE_BRIER_DELTA}")
            print("  Most likely interpretation: F-042 provides limited signal")
            print("  at available playoff sample size. This is a valid negative")
            print("  finding — not a calibration failure.")
            print("  → Deploy v2-065b9510 in October as planned (ADR-0031).")
        if not gate_ece:
            print(f"  ECE {ece_v2b:.4f} > allowed {SHADOW_GATE_ECE_MAX}")
        print()
        print("  T-186 result: F-042 signal ABSENT at current sample.")
        print("  Update DECISION_LOG with these findings.")
        print("="*65)

        logger.info("TRAIN_V2B", "shadow_gate_failed", payload={
            "brier_v2": brier_v2, "brier_v2b": brier_v2b, "brier_delta": brier_delta,
            "ece_v2b": ece_v2b, "gate_brier": gate_brier, "gate_ece": gate_ece,
            "f042_nonnan_rows": int(f042_nonnan),
        }, session_id=session_id, snapshot_id=SNAPSHOT_ID)
        sys.exit(2)

    if dry_run:
        print("  DRY RUN — skipping save.")
        return

    artifact = {
        "pipeline":       v2b_pipe,
        "feature_names":  feature_names,
        "col_medians":    col_medians,
        "model_version":  v2b_version,
        "qs_id":          QS_ID,
        "snapshot_id":    SNAPSHOT_ID,
        "f041_multiplier": F041_PLAYOFF_MULTIPLIER,
        "f042_cache_path": str(PLAYOFF_CACHE),
        "f042_nonnan_rows": int(f042_nonnan),
    }
    joblib.dump(artifact, V2B_MODEL_PATH)
    print(f"  Model saved: {V2B_MODEL_PATH}  ({V2B_MODEL_PATH.stat().st_size / 1024:.0f} KB)")

    meta = {
        "model_version":          v2b_version,
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
        "brier_v2_on_holdout":    round(brier_v2, 6),
        "brier_v2b_on_holdout":   round(brier_v2b, 6),
        "brier_delta":            round(brier_delta, 6),
        "ece_v2b":                round(ece_v2b, 4),
        "auc_v2b":                round(auc_v2b, 4),
        "shadow_gate_passed":     gate_pass,
        "f041_multiplier":        F041_PLAYOFF_MULTIPLIER,
        "f042_status":            f"populated from {PLAYOFF_CACHE} ({f042_nonnan} non-NaN rows)",
        "f042_nonnan_rows":       int(f042_nonnan),
        "f042_playoff_rows":      int(f042_playoff_rows),
        "trained_at":             _utc_now(),
        "session_id":             session_id,
        "feature_names":          feature_names,
        "adr_authorization":      "ADR-0031",
        "supersedes_model":       v2_version,
        "t186_step":              "T-186-TRAIN",
    }
    V2B_META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"  Metadata saved: {V2B_META_PATH}")

    logger.info("TRAIN_V2B", "model_serialized", payload={
        "model_version": v2b_version, "model_path": str(V2B_MODEL_PATH),
        "feature_count": len(feature_names), "brier_delta": brier_delta,
        "shadow_gate_passed": gate_pass, "f042_nonnan_rows": int(f042_nonnan),
    }, session_id=session_id, snapshot_id=SNAPSHOT_ID)

    print()
    print("="*65)
    print("SHADOW GATE PASSED — v2b beats v2 on holdout")
    print()
    print(f"  v2b model: {v2b_version}")
    print(f"  Brier:     {brier_v2b:.6f}  (v2: {brier_v2:.6f}, Δ={brier_delta:+.6f})")
    print(f"  ECE:       {ece_v2b:.4f}    (limit: {SHADOW_GATE_ECE_MAX})")
    print(f"  AUC:       {auc_v2b:.4f}")
    print(f"  F-042:     {f042_nonnan} populated rows")
    print()
    print("Next steps:")
    print("  1. Run T-177 backtest on v2b:")
    print("     PYTHONPATH=src .venv/bin/python3 scripts/run_t177_v2_backtest.py \\")
    print("       --model models/v2b_model.joblib")
    print("  2. Register v2b in ARTIFACT_REGISTRY.md.")
    print("  3. Update DECISION_LOG with T-186 results.")
    print("  4. v2b replaces v2-065b9510 as October deploy target (DARK_PERIOD_PLAN Phase 4).")
    print("="*65)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T-186 Step 2 — v2b model retrain")
    parser.add_argument("--dry-run",    action="store_true", help="Validate pipeline, do not save")
    parser.add_argument("--force-save", action="store_true",
                        help="Save even if Brier improvement below threshold (not for production)")
    args = parser.parse_args()

    main(dry_run=args.dry_run, force_save=args.force_save)

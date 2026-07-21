"""
EXP-005: Model Data Refresh — 2024-25 + 2025-26 Seasons
=========================================================
Experiment ID:   EXP-005
Phase:           Phase 6 Planning (T-058 — model data refresh)
Status:          CANONICAL RUNNER — 2026-05-28
Snapshot:        SNAP-2026-05-28-002 (to be registered in DATA_SNAPSHOTS_INDEX.md)

Purpose:
    Refresh the production model with 2024-25 and 2025-26 Regular Season data.
    G4 model was trained on 2021-24 only; Part B of EXP-004 showed large edge
    magnitudes because Kalshi has repriced players since the 2023-24 season.
    This experiment produces a production-ready model anchored to current seasons.

Dataset (5 seasons — Regular Season only):
    2021-22  2022-23  2023-24  2024-25  2025-26
    50-player cohort (same as EXP-001/002/003)

Chronological split (TI-02):
    TRAIN       : game_date ≤ 2025-02-28   (~60% of 2024-25 regular season)
    VALIDATION  : 2025-03-01 – 2025-04-13  (final stretch of 2024-25 reg season)
    TEST        : game_date > 2025-04-13   (2025-26 full regular season)

Governance:
    - Class B change: new experiment; same model class (ADR-0004 accepted)
    - No new ADR required — expanding seasons, not changing model architecture
    - CHANGELOG entry required after run
    - Frozen model policy applies to ENV-02/03; this is ENV-01 research training

How to run:
    PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_exp005.py

    Optional args:
        --no-api         Skip C1 pull; load cached raw_game_logs.csv
        --dry-run        Validate pipeline without writing to disk
        --output-dir     Custom output directory

Security (NFR-05, NFR-07):
    - No API keys required (nba_api is a public endpoint scraper).
    - BOT_C4_ACTIVE must NOT be set.
    - No venue API calls in this runner.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.ingestion import NBAIngestionClient
from prediction_market_bot.c2_feature_store.features import FeatureStore
from prediction_market_bot.c3_forecasting.forecaster import ModelForecaster
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.cohort import get_player_ids_v1
from typing import Any

# ---------------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------------

EXP_ID = "EXP-005"
SESSION_ID = f"EXP-005-{uuid.uuid4().hex[:8].upper()}"
SNAPSHOT_ID = "SNAP-2026-05-28-002"

# 5 seasons: adds 2024-25 and 2025-26 to the existing 3-season corpus
TARGET_SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
SEASON_TYPE = "Regular Season"

# Updated split — TRAIN through most of 2024-25 regular season;
# TEST is the full 2025-26 regular season (current, most realistic evaluation window)
TRAIN_END_DATE = "2025-02-28"    # ~60% through 2024-25 regular season
VAL_END_DATE = "2025-04-13"      # end of 2024-25 regular season
# TEST: 2025-26 season (game_date > 2025-04-13)

# G4 baseline metrics (ADR-0004 / EXP-004 TEST set, 2023-24 season)
G4_BASELINE_BRIER = 0.2416
G4_BASELINE_ECE = 0.0247
G4_BASELINE_AUC = 0.6062
NULL_BRIER = 0.2500

PLACEHOLDER_MARKET_IMPLIED_PROB = 0.50
FEATURE_WINDOW = 10
MIN_TRAIN_SAMPLES = 30

# v1 cohort (50 players) — imported from canonical cohort.py (T-071)
TARGET_PLAYER_IDS: list[int] = get_player_ids_v1()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _kill_switch(reason: str) -> None:
    print(f"\n[KILL SWITCH TRIGGERED] {reason}", file=sys.stderr)
    sys.exit(1)


def build_target(feature_df: pd.DataFrame) -> pd.Series:
    """Binary target: 1 if pts >= pts_l10_mean (prior games). Same definition as EXP-001."""
    col_name = f"pts_l{FEATURE_WINDOW}_mean"
    if col_name not in feature_df.columns or "pts" not in feature_df.columns:
        return pd.Series([np.nan] * len(feature_df), index=feature_df.index)
    pts = pd.to_numeric(feature_df["pts"], errors="coerce")
    prior_mean = pd.to_numeric(feature_df[col_name], errors="coerce")
    target = (pts >= prior_mean).astype("Int8")
    target[pts.isna() | prior_mean.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return target


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, set_name: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {"set": set_name, "n_samples": len(y_true)}
    if len(y_true) == 0:
        return metrics
    y_clip = np.clip(y_prob, 1e-6, 1 - 1e-6)
    try:
        metrics["brier_score"] = float(brier_score_loss(y_true, y_prob))
    except Exception as e:
        metrics["brier_score_error"] = str(e)
    try:
        metrics["log_loss"] = float(log_loss(y_true, y_clip))
    except Exception as e:
        metrics["log_loss_error"] = str(e)
    try:
        if len(np.unique(y_true)) >= 2:
            metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob))
    except Exception as e:
        metrics["auc_roc_error"] = str(e)
    try:
        frac_pos, mean_pred = calibration_curve(y_true, y_clip, n_bins=10, strategy="uniform")
        bin_weights = np.histogram(y_clip, bins=10, range=(0.0, 1.0))[0]
        bin_weights = bin_weights[bin_weights > 0]
        n = len(frac_pos)
        bw = bin_weights[:n]
        metrics["ece"] = float(np.sum((bw / bw.sum()) * np.abs(frac_pos - mean_pred)))
        metrics["ece_n_bins"] = int(n)
    except Exception as e:
        metrics["ece_error"] = str(e)
    return metrics


def compute_null_metrics(y_true: np.ndarray, set_name: str) -> dict[str, Any]:
    y_null = np.full(len(y_true), PLACEHOLDER_MARKET_IMPLIED_PROB)
    m = compute_metrics(y_true, y_null, f"{set_name}_null")
    m["null_model"] = True
    return m


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_experiment(
    output_dir: Path,
    skip_api: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "audit_exp005.jsonl"
    logger = AuditLogger(log_path=log_path, min_severity="DEBUG")

    ok = logger.info(
        "SYSTEM", "experiment_start",
        payload={
            "exp_id": EXP_ID,
            "session_id": SESSION_ID,
            "snapshot_id": SNAPSHOT_ID,
            "target_seasons": TARGET_SEASONS,
            "train_end_date": TRAIN_END_DATE,
            "val_end_date": VAL_END_DATE,
            "player_count": len(TARGET_PLAYER_IDS),
            "g4_baseline_brier": G4_BASELINE_BRIER,
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 AuditLogger write failure at experiment_start")

    print(f"\n{'='*60}")
    print(f"EXP-005: Model Data Refresh — 2024-25 + 2025-26 Seasons")
    print(f"Session: {SESSION_ID}")
    print(f"Seasons: {TARGET_SEASONS}")
    print(f"Split:   TRAIN ≤ {TRAIN_END_DATE} | VAL ≤ {VAL_END_DATE} | TEST = 2025-26")
    print(f"Log:     {log_path}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 1. C1 — Pull game logs
    # ------------------------------------------------------------------
    raw_csv_path = output_dir / f"{SNAPSHOT_ID}_raw_game_logs.csv"

    if skip_api and raw_csv_path.exists():
        print(f"[C1] Loading cached game logs from {raw_csv_path}")
        raw_df = pd.read_csv(raw_csv_path)
        print(f"[C1] Loaded {len(raw_df):,} rows from cache.")
    else:
        print(f"[C1] Fetching game logs for {len(TARGET_PLAYER_IDS)} players "
              f"across {len(TARGET_SEASONS)} seasons (~{len(TARGET_PLAYER_IDS) * len(TARGET_SEASONS) * 0.6:.0f}s)...")
        client = NBAIngestionClient(logger=logger, snapshot_id=SNAPSHOT_ID, request_delay=0.6)
        all_frames: list[pd.DataFrame] = []
        for season in TARGET_SEASONS:
            print(f"  Season {season}:")
            ok, season_df = client.fetch_player_game_logs_bulk(
                player_ids=TARGET_PLAYER_IDS,
                season=season,
                season_type=SEASON_TYPE,
                session_id=SESSION_ID,
            )
            if not ok:
                logger.error("C1", "bulk_fetch_failed",
                             payload={"season": season}, session_id=SESSION_ID,
                             snapshot_id=SNAPSHOT_ID)
                print(f"  WARNING: Fetch failed for season {season}. Continuing...")
            else:
                print(f"    ✓ {len(season_df):,} rows fetched.")
                all_frames.append(season_df)

        if not all_frames:
            _kill_switch("C1 produced no data — all seasons failed")

        raw_df = pd.concat(all_frames, ignore_index=True)
        print(f"\n[C1] Total: {len(raw_df):,} rows | "
              f"{raw_df['player_id'].nunique()} players | "
              f"{raw_df['season'].nunique()} seasons | "
              f"date range: {raw_df['game_date'].min()} → {raw_df['game_date'].max()}")

        if not dry_run:
            raw_df.to_csv(raw_csv_path, index=False)
            print(f"[C1] Snapshot saved: {raw_csv_path}")

    ok = logger.info(
        "C1", "raw_data_registered",
        payload={
            "snapshot_id": SNAPSHOT_ID,
            "total_rows": len(raw_df),
            "player_count": int(raw_df["player_id"].nunique()),
            "season_count": int(raw_df["season"].nunique()),
            "seasons_present": sorted(raw_df["season"].unique().tolist()),
            "date_range": f"{raw_df['game_date'].min()} → {raw_df['game_date'].max()}",
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 write failure after C1 snapshot registration")

    # ------------------------------------------------------------------
    # 2. C2 — Feature derivation
    # ------------------------------------------------------------------
    print(f"\n[C2] Computing features (window={FEATURE_WINDOW} games, v1.2.0)...")
    store = FeatureStore(logger=logger, snapshot_id=SNAPSHOT_ID, window=FEATURE_WINDOW)
    ok, feature_df = store.compute_features_bulk(game_log_df=raw_df, session_id=SESSION_ID)
    if not ok:
        _kill_switch("C2 compute_features_bulk failed (C6 write failure)")
    feature_names = store.get_feature_names()
    print(f"[C2] {len(feature_df):,} feature rows | {len(feature_names)} features (FEATURE_VERSION 1.2.0)")

    # ------------------------------------------------------------------
    # 3. Train/val/test split
    # ------------------------------------------------------------------
    ok, feature_df = store.assign_train_test_labels(
        feature_df=feature_df,
        train_end_date=TRAIN_END_DATE,
        val_end_date=VAL_END_DATE,
        session_id=SESSION_ID,
    )
    if not ok:
        _kill_switch("C2 assign_train_test_labels failed (C6 write failure)")
    label_counts = feature_df["train_test_label"].value_counts(dropna=False).to_dict()
    print(f"[C2] Split labels: {label_counts}")

    if not dry_run:
        feat_csv_path = output_dir / "EXP-005_feature_matrix.csv"
        feature_df.to_csv(feat_csv_path, index=False)
        print(f"[C2] Feature matrix saved: {feat_csv_path}")

    # ------------------------------------------------------------------
    # 4. Target variable
    # ------------------------------------------------------------------
    feature_df["y_target"] = build_target(feature_df)
    usable_mask = feature_df["y_target"].notna() & feature_df["temporal_cutoff"].notna()
    usable_df = feature_df[usable_mask].copy()
    train_df = usable_df[usable_df["train_test_label"] == "TRAIN"].copy()
    val_df = usable_df[usable_df["train_test_label"] == "VALIDATION"].copy()
    test_df = usable_df[usable_df["train_test_label"] == "TEST"].copy()

    print(f"\n[TARGET] TRAIN: {len(train_df):,} | VAL: {len(val_df):,} | TEST: {len(test_df):,}")
    print(f"  Class balance (TRAIN): {train_df['y_target'].value_counts().to_dict()}")

    if len(train_df) < MIN_TRAIN_SAMPLES:
        _kill_switch(f"Insufficient training samples: {len(train_df)} < {MIN_TRAIN_SAMPLES}")

    # ------------------------------------------------------------------
    # 5. C3 — Fit on TRAIN
    # ------------------------------------------------------------------
    print(f"\n[C3] Fitting model on {len(train_df):,} TRAIN rows...")
    forecaster = ModelForecaster(logger=logger, snapshot_id=SNAPSHOT_ID, feature_names=feature_names)
    fit_ok = forecaster.fit(feature_df=train_df, target=train_df["y_target"].astype(int),
                             session_id=SESSION_ID)
    if not fit_ok:
        _kill_switch("C3 ModelForecaster.fit() failed")
    print(f"[C3] Model: {forecaster.model_version}")

    # ------------------------------------------------------------------
    # 6. Evaluate on VALIDATION
    # ------------------------------------------------------------------
    print(f"\n[C3] Predicting on {len(val_df):,} VALIDATION rows...")
    ok, val_forecast_df = forecaster.predict(
        feature_df=val_df,
        market_implied_prob=PLACEHOLDER_MARKET_IMPLIED_PROB,
        session_id=SESSION_ID,
    )
    if not ok:
        _kill_switch("C3 predict() failed on VALIDATION (C6 write failure)")

    y_val = val_df["y_target"].astype(int).to_numpy()
    y_prob_val = val_forecast_df["p_estimate"].to_numpy()
    val_metrics = compute_metrics(y_val, y_prob_val, "VALIDATION")
    val_null = compute_null_metrics(y_val, "VALIDATION")

    # ------------------------------------------------------------------
    # 7. Evaluate on TEST (2025-26 season — G5 closed, TEST now accessible)
    # ------------------------------------------------------------------
    print(f"\n[C3] Predicting on {len(test_df):,} TEST rows (2025-26 season)...")
    ok, test_forecast_df = forecaster.predict(
        feature_df=test_df,
        market_implied_prob=PLACEHOLDER_MARKET_IMPLIED_PROB,
        session_id=SESSION_ID,
    )
    if not ok:
        _kill_switch("C3 predict() failed on TEST (C6 write failure)")

    y_test = test_df["y_target"].astype(int).to_numpy()
    y_prob_test = test_forecast_df["p_estimate"].to_numpy()
    test_metrics = compute_metrics(y_test, y_prob_test, "TEST")
    test_null = compute_null_metrics(y_test, "TEST")

    if not dry_run:
        test_out_path = output_dir / "EXP-005_test_evaluation.json"
        test_out_path.write_text(json.dumps({
            "exp_id": EXP_ID,
            "session_id": SESSION_ID,
            "snapshot_id": SNAPSHOT_ID,
            "model_version": forecaster.model_version,
            "test_set": "2025-26 Regular Season",
            "test_rows": len(test_df),
            "test_metrics": test_metrics,
            "test_null_metrics": test_null,
            "g4_baseline_brier": G4_BASELINE_BRIER,
            "g4_baseline_ece": G4_BASELINE_ECE,
        }, indent=2))
        test_forecast_df.to_csv(output_dir / "EXP-005_forecast_test.csv", index=False)
        print(f"[C3] TEST evaluation saved: {test_out_path}")

    # ------------------------------------------------------------------
    # 8. C4 gate check (expects REJECTED in ENV-01)
    # ------------------------------------------------------------------
    if len(val_forecast_df) > 0:
        engine = RiskEngine(logger=logger, snapshot_id=SNAPSHOT_ID, bankroll=10000.0)
        # portfolio_equity_usd omitted (T-175): expects phase-gate rejection;
        # BOT_C4_ACTIVE is not set in ENV-01, so CHECK 8 is never reached.
        ok, c4_decision = engine.evaluate_forecast(
            forecast_record={str(k): v for k, v in val_forecast_df.iloc[0].to_dict().items()},
            session_id=SESSION_ID,
        )
        if not ok:
            _kill_switch("C6 write failure during C4 gate check")
        print(f"\n[C4] Gate: {c4_decision.get('approval_status')} "
              f"({c4_decision.get('rejection_reason')}) — expected in ENV-01")

    # ------------------------------------------------------------------
    # 9. Results summary
    # ------------------------------------------------------------------
    val_bs = val_metrics.get("brier_score")
    val_nbs = val_null.get("brier_score")
    test_bs = test_metrics.get("brier_score")
    test_nbs = test_null.get("brier_score")
    val_imp = (val_nbs - val_bs) if isinstance(val_bs, float) and isinstance(val_nbs, float) else None
    test_imp = (test_nbs - test_bs) if isinstance(test_bs, float) and isinstance(test_nbs, float) else None

    print(f"\n{'='*60}")
    print("EXP-005 RESULTS — MODEL DATA REFRESH")
    print(f"{'='*60}")
    print(f"Model version: {forecaster.model_version}")
    print(f"Training data: {len(TARGET_SEASONS)} seasons ({TARGET_SEASONS[0]}–{TARGET_SEASONS[-1]})")
    print(f"\nVALIDATION set (n={val_metrics.get('n_samples', '?'):,}) — end of 2024-25 season:")
    print(f"  Brier model: {val_bs:.4f}" if isinstance(val_bs, float) else "  Brier model: N/A")
    print(f"  Brier null:  {val_nbs:.4f}" if isinstance(val_nbs, float) else "  Brier null:  N/A")
    print(f"  Improvement: {val_imp:+.4f}" if isinstance(val_imp, float) else "  Improvement: N/A")
    print(f"  ECE:         {val_metrics.get('ece'):.4f}" if isinstance(val_metrics.get('ece'), float) else "  ECE:         N/A")
    print(f"  AUC-ROC:     {val_metrics.get('auc_roc'):.4f}" if isinstance(val_metrics.get('auc_roc'), float) else "  AUC-ROC:     N/A")
    print(f"\nTEST set (n={test_metrics.get('n_samples', '?'):,}) — 2025-26 Regular Season:")
    print(f"  Brier model: {test_bs:.4f}" if isinstance(test_bs, float) else "  Brier model: N/A")
    print(f"  Brier null:  {test_nbs:.4f}" if isinstance(test_nbs, float) else "  Brier null:  N/A")
    print(f"  Improvement: {test_imp:+.4f} {'✓' if test_imp and test_imp > 0 else '✗'}" if isinstance(test_imp, float) else "  Improvement: N/A")
    print(f"  ECE:         {test_metrics.get('ece'):.4f}" if isinstance(test_metrics.get('ece'), float) else "  ECE:         N/A")
    print(f"  AUC-ROC:     {test_metrics.get('auc_roc'):.4f}" if isinstance(test_metrics.get('auc_roc'), float) else "  AUC-ROC:     N/A")
    print(f"\nG4 baseline (2023-24 TEST): Brier {G4_BASELINE_BRIER} | ECE {G4_BASELINE_ECE} | AUC {G4_BASELINE_AUC}")
    if isinstance(test_imp, float):
        vs_g4 = test_imp - (NULL_BRIER - G4_BASELINE_BRIER)
        print(f"Δ vs G4 improvement: {vs_g4:+.4f} (positive = refreshed model better than G4 on its own test set)")
    print(f"{'='*60}\n")

    ok = logger.info(
        "SYSTEM", "experiment_complete",
        payload={
            "exp_id": EXP_ID,
            "session_id": SESSION_ID,
            "model_version": forecaster.model_version,
            "val_brier": val_bs,
            "val_ece": val_metrics.get("ece"),
            "test_brier": test_bs,
            "test_ece": test_metrics.get("ece"),
            "test_auc_roc": test_metrics.get("auc_roc"),
            "g4_baseline_brier": G4_BASELINE_BRIER,
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 write failure at experiment_complete")

    print(f"Outputs: {output_dir}")
    return {
        "exp_id": EXP_ID,
        "session_id": SESSION_ID,
        "snapshot_id": SNAPSHOT_ID,
        "model_version": forecaster.model_version,
        "seasons": TARGET_SEASONS,
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "val_brier_model": val_bs,
        "val_brier_improvement": val_imp,
        "val_ece": val_metrics.get("ece"),
        "val_auc_roc": val_metrics.get("auc_roc"),
        "test_brier_model": test_bs,
        "test_brier_improvement": test_imp,
        "test_ece": test_metrics.get("ece"),
        "test_auc_roc": test_metrics.get("auc_roc"),
        "g4_baseline_brier": G4_BASELINE_BRIER,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EXP-005: Model Data Refresh (2024-25 + 2025-26)")
    parser.add_argument("--output-dir", type=Path, default=Path("exp_output/EXP-005"))
    parser.add_argument("--no-api", action="store_true",
                        help="Skip C1 pull; load cached raw CSV from --output-dir")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate pipeline without writing to disk")
    return parser.parse_args()


if __name__ == "__main__":
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — unset before running research experiments.",
              file=sys.stderr)
        sys.exit(1)
    args = _parse_args()
    run_experiment(output_dir=args.output_dir, skip_api=args.no_api, dry_run=args.dry_run)
    sys.exit(0)

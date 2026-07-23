"""
EXP-001: First Pipeline Run — NBA Player Props Forecasting
===========================================================
Experiment ID:   EXP-001
Phase:           Phase 3 (Research Build)
Status:          CANONICAL RUNNER — 2026-05-27
Snapshot:        SNAP-2026-05-27-001 (registered in DATA_SNAPSHOTS_INDEX.md)
Script path:     src/prediction_market_bot/run_exp001.py

Hypotheses tested:
  HYP-001 — Player_Attribute_Matrix features beat null model
  HYP-002 — Model probability estimates are calibrated (ECE < 0.05)

Pipeline: C1 → C2 → C3 → C4 (C4 will REJECT at phase gate — expected)

How to run:
    From project root (with package installed: pip install -e .):
        python -m prediction_market_bot.run_exp001

    Or directly (adds src/ to sys.path automatically):
        python src/prediction_market_bot/run_exp001.py

    Optional args:
        --output-dir <path>  Directory for output CSVs (default: exp_output/EXP-001/)
        --no-api             Skip C1 API pull; expect raw_game_logs.csv in --output-dir
        --dry-run            Run pipeline validation without writing results to disk

Security (NFR-05, NFR-07):
    - No API keys required. nba_api is a public endpoint scraper.
    - BOT_C4_ACTIVE must NOT be set in ENV-01 / ENV-02.
    - No live capital. No venue API calls.

Temporal integrity (TI-01–TI-04):
    - All features computed from prior games only (.shift(1) before .rolling()).
    - Train/validation/test splits are chronological.
    - No look-ahead: target variable y = (pts >= pts_l10_mean) where pts_l10_mean
      is computed from the rolling window of PRIOR games only.
    - Test set accessed only at G4 gate — NOT printed by this script.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

# ---------------------------------------------------------------------------
# Ensure src/ is on sys.path when run directly (not via -m)
# ---------------------------------------------------------------------------
_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.ingestion import NBAIngestionClient  # noqa: E402
from prediction_market_bot.c2_feature_store.features import FeatureStore  # noqa: E402
from prediction_market_bot.c3_forecasting.forecaster import ModelForecaster  # noqa: E402
from prediction_market_bot.c4_risk_engine.risk import RiskEngine  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

# ---------------------------------------------------------------------------
# Experiment Configuration
# ---------------------------------------------------------------------------

EXP_ID = "EXP-001"
SESSION_ID = f"EXP-001-{uuid.uuid4().hex[:8].upper()}"
SNAPSHOT_ID = "SNAP-2026-05-28-001"  # T-043: 50-player cohort registered 2026-05-28

# Seasons to ingest (nba_api "YYYY-YY" format)
TARGET_SEASONS = ["2021-22", "2022-23", "2023-24"]
SEASON_TYPE = "Regular Season"

# Chronological split boundaries (TI-02 — no random shuffle)
TRAIN_END_DATE = "2023-01-31"    # Through first half of 2022-23 season
VAL_END_DATE = "2023-04-30"      # Rest of 2022-23 season
# TEST: 2023-24 season onwards (NEVER accessed in this script — held for G4)

# Phase 4 players — expanded to 50 for T-043 (OQ-018).
# Phase 3 (10 players, 986 TRAIN rows) failed G4: only 1/3 experiments beat null.
# Root cause: training data too sparse in earlier windows (EXP-003: 197 rows, EXP-002: 358 rows).
# Expansion target: 50 players × ~70 games × 3 seasons ≈ ~10,500 rows.
# Selection criteria: consistent starters across all 3 seasons (2021-22, 2022-23, 2023-24);
# diverse positions and statistical profiles.
TARGET_PLAYER_IDS: list[int] = [
    # Original Phase 3 cohort (10)
    2544,      # LeBron James
    201142,    # Kevin Durant
    201939,    # Stephen Curry
    203507,    # Giannis Antetokounmpo
    203999,    # Nikola Jokic
    203954,    # Joel Embiid
    203081,    # Damian Lillard
    1629029,   # Luka Doncic
    1628369,   # Jayson Tatum
    202710,    # Jimmy Butler
    # Phase 4 additions — guards (15)
    1629630,   # Ja Morant
    1626164,   # Devin Booker
    1628378,   # Donovan Mitchell
    1629027,   # Trae Young
    203897,    # Zach LaVine
    1630162,   # Anthony Edwards
    1628368,   # De'Aaron Fox
    201942,    # DeMar DeRozan
    202681,    # Kyrie Irving
    203078,    # Bradley Beal
    203468,    # CJ McCollum
    1629639,   # Tyler Herro
    1630169,   # Tyrese Haliburton
    1628386,   # Dejounte Murray
    1628983,   # Shai Gilgeous-Alexander
    # Phase 4 additions — wings/forwards (15)
    202695,    # Kawhi Leonard
    203471,    # Paul George
    1627783,   # Pascal Siakam
    203944,    # Julius Randle
    1627742,   # Brandon Ingram
    203114,    # Khris Middleton
    1630567,   # Scottie Barnes
    203952,    # Andrew Wiggins
    1628973,   # Jalen Brunson
    1628969,   # Mikal Bridges
    1628384,   # OG Anunoby
    203932,    # Aaron Gordon
    203110,    # Draymond Green
    1629628,   # RJ Barrett
    1630532,   # Franz Wagner
    # Phase 4 additions — bigs/centers (10)
    1628389,   # Bam Adebayo
    1626157,   # Karl-Anthony Towns
    203497,    # Rudy Gobert
    1627734,   # Domantas Sabonis
    202696,    # Nikola Vucevic
    203991,    # Clint Capela
    1630596,   # Evan Mobley
    201572,    # Brook Lopez
    1629636,   # Darius Garland
    1628991,   # Jaren Jackson Jr.
]

# Phase 3 placeholder: no live market data. Use 0.50 (uniform prior) as the
# market_implied_prob for all forecasts. This is an acknowledged research-phase
# simplification; venue mid-prices are available only at Phase 5 (ENV-02).
PLACEHOLDER_MARKET_IMPLIED_PROB = 0.50

# Rolling window (matches FeatureStore default)
FEATURE_WINDOW = 10

# Minimum training samples for C3 fit
MIN_TRAIN_SAMPLES = 30


# ---------------------------------------------------------------------------
# Kill-switch helper (research environment)
# ---------------------------------------------------------------------------

def _kill_switch(reason: str) -> None:
    """
    Research-phase kill switch.
    In ENV-01 this halts the runner with a non-zero exit code.
    In ENV-02/03 this would halt all components within ≤60 seconds (NFR-03).
    """
    print(f"\n[KILL SWITCH TRIGGERED] {reason}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Target variable construction
# ---------------------------------------------------------------------------

def build_target(feature_df: pd.DataFrame) -> pd.Series:
    """
    Binary target variable for HYP-001 / HYP-002 (player props proxy).

    y = 1 if player's actual points in this game >= their rolling L10 mean
    from PRIOR games (pts_l10_mean — computed by C2 with .shift(1) before .rolling()).
    y = 0 otherwise.

    Rationale:
        This proxies a "player over/under" contract: 'Will this player score
        at or above their rolling form line tonight?'
        - pts is the current game outcome (target — not a feature).
        - pts_l10_mean is from prior games only (no look-ahead).
        - Rows without a valid pts_l10_mean (first game in window, NaN) are
          excluded; they will have NaN in the target and must be dropped before
          model fitting.

    Temporal integrity: VALID — target uses current-game pts; features use
    prior-game statistics only.

    Returns
    -------
    pd.Series (int8), NaN where pts or pts_l10_mean is missing.
    """
    col_name = f"pts_l{FEATURE_WINDOW}_mean"
    if col_name not in feature_df.columns or "pts" not in feature_df.columns:
        return pd.Series([np.nan] * len(feature_df), index=feature_df.index)

    pts = pd.to_numeric(feature_df["pts"], errors="coerce")
    pts_prior_mean = pd.to_numeric(feature_df[col_name], errors="coerce")
    target = (pts >= pts_prior_mean).astype("Int8")
    target[pts.isna() | pts_prior_mean.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return target


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def compute_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    set_name: str,
) -> dict[str, Any]:
    """
    Compute Brier score, log loss, ECE, AUC-ROC for a prediction set.

    ECE (Expected Calibration Error):
        Computed over 10 equal-width bins [0, 0.1), [0.1, 0.2), ..., [0.9, 1.0].
        ECE = sum_over_bins( |bin_size| / |total| * |fraction_positive - mean_prob| )
    """
    metrics = {
        "set": set_name,
        "n_samples": len(y_true),
        "brier_score": None,
        "log_loss": None,
        "ece": None,
        "auc_roc": None,
    }

    if len(y_true) == 0:
        return metrics

    # Clip probabilities to avoid log(0) in log_loss
    y_prob_clipped = np.clip(y_prob, 1e-6, 1 - 1e-6)

    try:
        metrics["brier_score"] = float(brier_score_loss(y_true, y_prob))
    except Exception as e:
        metrics["brier_score_error"] = str(e)

    try:
        metrics["log_loss"] = float(log_loss(y_true, y_prob_clipped))
    except Exception as e:
        metrics["log_loss_error"] = str(e)

    try:
        if len(np.unique(y_true)) >= 2:
            metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob))
        else:
            metrics["auc_roc"] = None
            metrics["auc_roc_note"] = "Only one class present in y_true"
    except Exception as e:
        metrics["auc_roc_error"] = str(e)

    # ECE — 10 equal-width bins
    try:
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_true, y_prob_clipped, n_bins=10, strategy="uniform"
        )
        bin_weights = np.histogram(y_prob_clipped, bins=10, range=(0.0, 1.0))[0]
        bin_weights = bin_weights[bin_weights > 0]  # non-empty bins only
        n_bins_used = len(fraction_of_positives)
        bin_sizes = bin_weights[:n_bins_used]
        total = bin_sizes.sum()
        ece = float(
            np.sum(
                (bin_sizes / total) * np.abs(fraction_of_positives - mean_predicted_value)
            )
        )
        metrics["ece"] = ece
        metrics["ece_n_bins"] = int(n_bins_used)
    except Exception as e:
        metrics["ece_error"] = str(e)

    return metrics


# ---------------------------------------------------------------------------
# Null model
# ---------------------------------------------------------------------------

def compute_null_model_metrics(y_true: np.ndarray, set_name: str) -> dict[str, Any]:
    """
    Null model: constant prediction = market_implied_prob (0.50 in Phase 3).
    Brier score for the null model is the baseline to beat (ASM-002).
    """
    y_null = np.full(len(y_true), PLACEHOLDER_MARKET_IMPLIED_PROB)
    metrics = compute_metrics(y_true, y_null, set_name=f"{set_name}_null")
    metrics["null_model"] = True
    metrics["null_prob"] = PLACEHOLDER_MARKET_IMPLIED_PROB
    return metrics


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_experiment(
    output_dir: Path,
    skip_api: bool = False,
    dry_run: bool = False,
    ablation_v10: bool = False,
    source_csv: Path | None = None,
) -> dict[str, Any]:
    """
    Execute the full EXP-001 pipeline and return a results summary dict.

    Steps:
        1. Initialize C6 AuditLogger
        2. Pull game logs via C1 NBAIngestionClient (or load from disk if skip_api)
        3. Compute features via C2 FeatureStore
        4. Assign chronological train/val/test labels
        5. Build binary target variable
        6. Fit C3 ModelForecaster on TRAIN subset
        7. Predict on VALIDATION subset; compute metrics
        8. Compute null model metrics for comparison
        9. Route one forecast through C4 RiskEngine (expects REJECT at phase gate)
       10. Log all results; save outputs to disk

    Returns
    -------
    dict — metrics summary for experiment record.
    """
    # EXP-001 outputs go into a dedicated EXP-001/ subdirectory so that
    # run_backtest --raw-csv exp_output/EXP-001/SNAP-... resolves correctly.
    subdir = "EXP-001-ablation-v10" if ablation_v10 else "EXP-001"
    output_dir = output_dir / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Initialize C6 AuditLogger
    # ------------------------------------------------------------------
    log_path = output_dir / "audit_exp001.jsonl"
    logger = AuditLogger(log_path=log_path, min_severity="DEBUG")

    ok = logger.info(
        "SYSTEM",
        "experiment_start",
        payload={
            "exp_id": EXP_ID,
            "session_id": SESSION_ID,
            "snapshot_id": SNAPSHOT_ID,
            "target_seasons": TARGET_SEASONS,
            "train_end_date": TRAIN_END_DATE,
            "val_end_date": VAL_END_DATE,
            "player_count": len(TARGET_PLAYER_IDS),
            "market_implied_prob_placeholder": PLACEHOLDER_MARKET_IMPLIED_PROB,
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 AuditLogger write failure at experiment_start")

    print(f"\n{'='*60}")
    print(f"EXP-001: NBA Player Props Forecasting — Pipeline Run")
    print(f"Session: {SESSION_ID}")
    print(f"Log: {log_path}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 2. C1 — Pull game logs
    # ------------------------------------------------------------------
    raw_csv_path = output_dir / f"{SNAPSHOT_ID}_raw_game_logs.csv"

    if source_csv is not None:
        print(f"[C1] Loading game logs from --source-csv {source_csv}")
        raw_df = pd.read_csv(source_csv)
        print(f"[C1] Loaded {len(raw_df):,} rows.")
    elif skip_api and raw_csv_path.exists():
        print(f"[C1] Loading cached game logs from {raw_csv_path}")
        raw_df = pd.read_csv(raw_csv_path)
        print(f"[C1] Loaded {len(raw_df):,} rows from cache.")
    else:
        print(f"[C1] Fetching game logs for {len(TARGET_PLAYER_IDS)} players "
              f"across seasons {TARGET_SEASONS}...")

        client = NBAIngestionClient(
            logger=logger,
            snapshot_id=SNAPSHOT_ID,
            request_delay=0.6,
        )

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
                ok = logger.error(
                    "C1", "bulk_fetch_failed",
                    payload={"season": season},
                    session_id=SESSION_ID,
                    snapshot_id=SNAPSHOT_ID,
                )
                if not ok:
                    _kill_switch(f"C6 write failure after C1 bulk fetch failed for season {season}")
                print(f"  WARNING: Fetch failed for season {season}. Continuing...")
            else:
                print(f"    ✓ {len(season_df):,} rows fetched.")
                all_frames.append(season_df)

        if not all_frames:
            _kill_switch("C1 produced no data — all seasons failed")

        raw_df = pd.concat(all_frames, ignore_index=True)
        print(f"\n[C1] Total game logs: {len(raw_df):,} rows | "
              f"{raw_df['player_id'].nunique()} players | "
              f"{raw_df['season'].nunique()} seasons")

        # Register SNAP-2026-05-27-001 — save raw data
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
            "date_range": f"{raw_df['game_date'].min()} → {raw_df['game_date'].max()}",
            "file_path": str(raw_csv_path),
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 write failure after C1 snapshot registration")

    # ------------------------------------------------------------------
    # 3. C2 — Feature derivation
    # ------------------------------------------------------------------
    print(f"\n[C2] Computing features (window={FEATURE_WINDOW} games)...")

    store = FeatureStore(logger=logger, snapshot_id=SNAPSHOT_ID, window=FEATURE_WINDOW)
    ok, feature_df = store.compute_features_bulk(
        game_log_df=raw_df,
        session_id=SESSION_ID,
    )
    if not ok:
        _kill_switch("C2 compute_features_bulk failed (C6 write failure)")

    feature_names = store.get_feature_names()
    if ablation_v10:
        # T-044 / HYP-005: drop the 7 FEATURE_VERSION 1.1.0 additions (F-032..F-038)
        # to isolate the signal from v1.0.0 rolling box-score features only.
        feature_names = [f for f in feature_names if f not in {
            "season_type_is_playoffs", "days_since_last_game", "b2b_flag",
            "load_games_l7d", "eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games",
        }]
        print(f"[C2] Ablation mode: dropped v1.1.0 features → {len(feature_names)} features (v1.0.0 only)")
    print(f"[C2] Features computed: {len(feature_df):,} rows | "
          f"{len(feature_names)} features | version {store._window}")

    # ------------------------------------------------------------------
    # 4. Assign train/val/test labels
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

    # Save feature matrix
    if not dry_run:
        feat_csv_path = output_dir / "EXP-001_feature_matrix.csv"
        feature_df.to_csv(feat_csv_path, index=False)
        print(f"[C2] Feature matrix saved: {feat_csv_path}")

    # ------------------------------------------------------------------
    # 5. Build target variable
    # ------------------------------------------------------------------
    print("\n[TARGET] Building binary target: pts >= pts_l10_mean (prior games)")
    feature_df["y_target"] = build_target(feature_df)

    # Filter: only rows with valid features AND valid target AND valid temporal_cutoff
    # Rows with null temporal_cutoff are first-game rows (no prior window) — exclude
    usable_mask = (
        feature_df["y_target"].notna()
        & feature_df["temporal_cutoff"].notna()
    )
    usable_df = feature_df[usable_mask].copy()
    print(f"[TARGET] Usable rows (target+temporal_cutoff valid): {len(usable_df):,} / {len(feature_df):,}")
    print(f"  Class balance: {usable_df['y_target'].value_counts().to_dict()}")

    # TRAIN subset — strictly chronological; no TEST data
    train_df = usable_df[usable_df["train_test_label"] == "TRAIN"].copy()
    val_df = usable_df[usable_df["train_test_label"] == "VALIDATION"].copy()
    # TEST: defined but not accessed in this script (held for G4 gate)
    test_count = int((usable_df["train_test_label"] == "TEST").sum())

    print(f"[TARGET] TRAIN: {len(train_df):,} | VALIDATION: {len(val_df):,} | "
          f"TEST: {test_count} (HELD OUT — not accessed)")

    ok = logger.info(
        "C2", "target_construction_complete",
        payload={
            "target_definition": "pts >= pts_l10_mean (prior games)",
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "test_rows": test_count,
            "usable_rows": len(usable_df),
            "total_feature_rows": len(feature_df),
            "null_temporal_cutoff_rows": int((~usable_mask).sum()),
            "class_balance": usable_df["y_target"].value_counts().to_dict(),
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 write failure after target construction")

    if len(train_df) < MIN_TRAIN_SAMPLES:
        _kill_switch(
            f"Insufficient training samples: {len(train_df)} < {MIN_TRAIN_SAMPLES}. "
            "Check data ingestion."
        )

    # ------------------------------------------------------------------
    # 6. C3 — Fit model on TRAIN data
    # ------------------------------------------------------------------
    print(f"\n[C3] Fitting ModelForecaster on {len(train_df):,} TRAIN rows...")

    forecaster = ModelForecaster(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
        feature_names=feature_names,
    )

    y_train = train_df["y_target"].astype(int)
    fit_ok = forecaster.fit(
        feature_df=train_df,
        target=y_train,
        session_id=SESSION_ID,
    )
    if not fit_ok:
        _kill_switch("C3 ModelForecaster.fit() failed")

    print(f"[C3] Model fitted: {forecaster.model_version}")

    # ------------------------------------------------------------------
    # 7. C3 — Predict on VALIDATION data
    # ------------------------------------------------------------------
    print(f"\n[C3] Generating forecasts on {len(val_df):,} VALIDATION rows...")

    ok, forecast_df = forecaster.predict(
        feature_df=val_df,
        market_implied_prob=PLACEHOLDER_MARKET_IMPLIED_PROB,
        session_id=SESSION_ID,
    )
    if not ok:
        _kill_switch("C3 ModelForecaster.predict() failed (C6 write failure)")

    print(f"[C3] Forecasts generated: {len(forecast_df):,} rows")
    direction_counts = forecast_df["recommended_direction"].value_counts().to_dict()
    print(f"  Direction distribution: {direction_counts}")

    if not dry_run:
        fcst_csv_path = output_dir / "EXP-001_forecast_validation.csv"
        forecast_df.to_csv(fcst_csv_path, index=False)
        print(f"[C3] Forecast output saved: {fcst_csv_path}")

    # ------------------------------------------------------------------
    # 8. Compute metrics (VALIDATION set only — TEST held for G4)
    # ------------------------------------------------------------------
    print("\n[METRICS] Computing validation metrics...")

    # Align y_true with forecast rows
    y_val = val_df["y_target"].astype(int).to_numpy()
    y_prob_val = forecast_df["p_estimate"].to_numpy()

    model_metrics = compute_metrics(y_val, y_prob_val, "VALIDATION")
    null_metrics = compute_null_model_metrics(y_val, "VALIDATION")

    # Train set metrics (in-sample — informational only)
    ok2, train_forecast_df = forecaster.predict(
        feature_df=train_df,
        market_implied_prob=PLACEHOLDER_MARKET_IMPLIED_PROB,
        session_id=SESSION_ID,
    )
    if ok2 and len(train_forecast_df) > 0:
        y_train_true = train_df["y_target"].astype(int).to_numpy()
        y_prob_train = train_forecast_df["p_estimate"].to_numpy()
        train_metrics = compute_metrics(y_train_true, y_prob_train, "TRAIN")
    else:
        train_metrics = {"set": "TRAIN", "n_samples": len(train_df), "note": "predict failed"}

    null_train_metrics = compute_null_model_metrics(
        train_df["y_target"].astype(int).to_numpy(), "TRAIN"
    )

    print(f"\n{'─'*50}")
    print("RESULTS SUMMARY — EXP-001")
    print(f"{'─'*50}")
    print(f"Model version: {forecaster.model_version}")
    print(f"\nTRAIN  (n={train_metrics.get('n_samples', '?'):,}):")
    print(f"  Brier (model) : {train_metrics.get('brier_score', 'N/A'):.4f}"
          if isinstance(train_metrics.get('brier_score'), float) else f"  Brier (model) : N/A")
    print(f"  Brier (null)  : {null_train_metrics.get('brier_score', 'N/A'):.4f}"
          if isinstance(null_train_metrics.get('brier_score'), float) else f"  Brier (null)  : N/A")
    print(f"\nVALIDATION (n={model_metrics.get('n_samples', '?'):,}):")
    _bs = model_metrics.get('brier_score')
    _nbs = null_metrics.get('brier_score')
    print(f"  Brier (model) : {_bs:.4f}" if isinstance(_bs, float) else "  Brier (model) : N/A")
    print(f"  Brier (null)  : {_nbs:.4f}" if isinstance(_nbs, float) else "  Brier (null)  : N/A")
    if isinstance(_bs, float) and isinstance(_nbs, float):
        improvement = _nbs - _bs
        print(f"  Improvement   : {improvement:+.4f} ({'✓ beats null' if improvement > 0 else '✗ worse than null'})")
    _ll = model_metrics.get('log_loss')
    _ece = model_metrics.get('ece')
    _auc = model_metrics.get('auc_roc')
    print(f"  Log Loss      : {_ll:.4f}" if isinstance(_ll, float) else "  Log Loss      : N/A")
    print(f"  ECE           : {_ece:.4f}" if isinstance(_ece, float) else "  ECE           : N/A")
    print(f"  AUC-ROC       : {_auc:.4f}" if isinstance(_auc, float) else "  AUC-ROC       : N/A")
    print(f"{'─'*50}")
    print("TEST SET: HELD OUT — not accessed (accessed only at G4 gate)")
    print(f"{'─'*50}\n")

    # Log metrics to C6
    ok = logger.info(
        "C3", "experiment_metrics_complete",
        payload={
            "exp_id": EXP_ID,
            "model_version": forecaster.model_version,
            "snapshot_id": SNAPSHOT_ID,
            "validation_metrics": {
                "brier_score": model_metrics.get("brier_score"),
                "log_loss": model_metrics.get("log_loss"),
                "ece": model_metrics.get("ece"),
                "auc_roc": model_metrics.get("auc_roc"),
                "n_samples": model_metrics.get("n_samples"),
            },
            "null_model_metrics": {
                "brier_score": null_metrics.get("brier_score"),
                "null_prob": PLACEHOLDER_MARKET_IMPLIED_PROB,
                "n_samples": null_metrics.get("n_samples"),
            },
            "train_metrics": {
                "brier_score": train_metrics.get("brier_score"),
                "n_samples": train_metrics.get("n_samples"),
            },
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 write failure when logging experiment metrics")

    # ------------------------------------------------------------------
    # 9. C4 — Route one forecast through RiskEngine (gate check)
    # NOTE: Expects REJECTED(phase_gate_not_reached) — C4 is disabled in ENV-01
    # BOT_C4_ACTIVE must NOT be set in ENV-01 or ENV-02 (NFR-07 / ARCHITECTURE)
    # ------------------------------------------------------------------
    print("[C4] Routing first validation forecast through RiskEngine (phase gate check)...")

    if len(forecast_df) > 0:
        sample_forecast = {str(k): v for k, v in forecast_df.iloc[0].to_dict().items()}
        engine = RiskEngine(
            logger=logger,
            snapshot_id=SNAPSHOT_ID,
            bankroll=10000.0,  # EXP-001 experiment bankroll; no live capital
        )
        # portfolio_equity_usd omitted (T-175): this call expects REJECTED at the
        # phase gate (BOT_C4_ACTIVE not set in ENV-01); CHECK 8 is never reached.
        ok, c4_decision = engine.evaluate_forecast(
            forecast_record=sample_forecast,
            session_id=SESSION_ID,
        )
        if not ok:
            _kill_switch("C6 write failure during C4 evaluate_forecast")

        c4_status = c4_decision.get("approval_status", "UNKNOWN")
        c4_reason = c4_decision.get("rejection_reason", "")
        print(f"[C4] Status: {c4_status} | Reason: {c4_reason}")

        if c4_status != "REJECTED" or c4_reason != "phase_gate_not_reached":
            ok = logger.error(
                "C4", "unexpected_gate_state",
                payload={
                    "expected_status": "REJECTED",
                    "expected_reason": "phase_gate_not_reached",
                    "actual_status": c4_status,
                    "actual_reason": c4_reason,
                    "note": (
                        "C4 should return REJECTED(phase_gate_not_reached) in ENV-01. "
                        "If BOT_C4_ACTIVE is set, remove it immediately — "
                        "it must NOT be set in ENV-01 or ENV-02."
                    ),
                },
                severity="ERROR",
                session_id=SESSION_ID,
                snapshot_id=SNAPSHOT_ID,
            )
            if not ok:
                _kill_switch("C6 write failure after C4 unexpected gate state")
        else:
            print(f"[C4] ✓ Phase gate correctly rejected (expected in ENV-01)")

    # ------------------------------------------------------------------
    # 10. Session close
    # ------------------------------------------------------------------
    ok = logger.info(
        "SYSTEM", "experiment_complete",
        payload={
            "exp_id": EXP_ID,
            "session_id": SESSION_ID,
            "model_version": forecaster.model_version,
            "snapshot_id": SNAPSHOT_ID,
            "validation_brier_model": model_metrics.get("brier_score"),
            "validation_brier_null": null_metrics.get("brier_score"),
            "validation_ece": model_metrics.get("ece"),
            "output_dir": str(output_dir),
        },
        session_id=SESSION_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    if not ok:
        _kill_switch("C6 write failure at experiment_complete")

    print(f"\n[COMPLETE] EXP-001 pipeline run finished.")
    print(f"Outputs: {output_dir}")
    print(f"Audit log: {log_path}\n")

    return {
        "exp_id": EXP_ID,
        "session_id": SESSION_ID,
        "model_version": forecaster.model_version,
        "snapshot_id": SNAPSHOT_ID,
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows_held_out": test_count,
        "train_end_date": TRAIN_END_DATE,
        "val_end_date": VAL_END_DATE,
        "validation_brier_model": model_metrics.get("brier_score"),
        "validation_brier_null": null_metrics.get("brier_score"),
        "validation_log_loss": model_metrics.get("log_loss"),
        "validation_ece": model_metrics.get("ece"),
        "validation_auc_roc": model_metrics.get("auc_roc"),
        "train_brier_model": train_metrics.get("brier_score"),
        "train_brier_null": null_train_metrics.get("brier_score"),
        "c4_gate_result": c4_decision.get("approval_status") if len(forecast_df) > 0 else "no_forecasts",
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EXP-001: NBA Player Props Forecasting Pipeline Runner"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("exp_output/EXP-001"),
        help="Directory for output CSVs and audit log (default: exp_output/EXP-001/)",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip C1 API pull; load from cached raw_game_logs.csv in --output-dir",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline validation without writing results to disk",
    )
    parser.add_argument(
        "--ablation-v10",
        action="store_true",
        help=(
            "T-044 / HYP-005: drop FEATURE_VERSION 1.1.0 additions (ERI + schedule features) "
            "and run with v1.0.0 rolling box-score features only (31 features instead of 38). "
            "Used to isolate the incremental signal of v1.1.0 features."
        ),
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=None,
        help="Load raw game logs from this CSV instead of pulling via nba_api. "
             "Used with --ablation-v10 to reuse an existing snapshot.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    results = run_experiment(
        output_dir=args.output_dir,
        skip_api=args.no_api,
        dry_run=args.dry_run,
        ablation_v10=args.ablation_v10,
        source_csv=args.source_csv,
    )
    # Exit 0 on success — non-zero already handled by _kill_switch()
    sys.exit(0)

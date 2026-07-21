"""
BACKTEST: Walk-Forward Backtesting Framework
=============================================
Component:    BACKTEST (Research utility — no component ID assigned)
Phase active: Phase 3 (Research Build)
Status:       CANONICAL — 2026-05-27
Upstream:     C1 Signal Ingestion (raw game log DataFrame)
Downstream:   C2 Feature Store → C3 Forecasting Engine → C4 Risk Engine (gate check)
              C6 Audit Logger (IF-ALL-C6)
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only)
Policy refs:  05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/,
              06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md,
              07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md

Purpose:
    Implements walk-forward (chronological) backtesting across multiple independent
    time windows. Each window produces experiment-level metrics (Brier, LogLoss,
    ECE, AUC-ROC) in a format directly comparable to EXP-001. The framework
    provides the ≥3 independent experiments required for G4 evidence (HYP-001).

Design constraints (must be verified before each session):
    1. Chronological only — no shuffling, no forward-looking windows (TI-01–TI-04)
    2. Same C1→C2→C3 pipeline as run_exp001.py (same feature version, same model class)
    3. Each BacktestWindowDef produces one experiment record (EXP-002, EXP-003, ...)
    4. C4 remains phase-gated (BOT_C4_ACTIVE not set in ENV-01; expects REJECTED)
    5. All public methods return (bool, ...) — False = C6 write failure = kill switch
    6. No hardcoded secrets (NFR-05); nba_api is a public endpoint, no API key required
    7. TEST rows are NEVER accessed during training or validation computation
    8. Model is re-fit per window (independent evidence); frozen model policy applies
       to ENV-02/03 production only — not to Phase 3 research

Metric definitions (same as run_exp001.py):
    Brier score   — lower is better; null = (p_null * (1-p_null)) = 0.25 at p=0.50
    Log Loss      — lower is better; null = -log(0.50) = 0.6931
    ECE           — Expected Calibration Error; 10 equal-width bins; lower = better calibrated
    AUC-ROC       — higher is better; null = 0.50

Kill switch constraint (NFR-03):
    All public methods return (bool, result).
    False on any C6 write failure. Callers must trigger kill switch.
    run_backtest.py handles kill switch escalation; callers of run_window() should
    check the bool return and call _kill_switch() if False.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from prediction_market_bot.c2_feature_store.features import FeatureStore
from prediction_market_bot.c3_forecasting.forecaster import ModelForecaster
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "BACKTEST"

# Must match EXP-001 constants exactly (same feature version, same model class)
FEATURE_WINDOW = 10
PLACEHOLDER_MARKET_IMPLIED_PROB = 0.50
MIN_TRAIN_SAMPLES = 30


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BacktestWindowDef:
    """
    Configuration for one backtesting window.

    Each window produces one experiment record (EXP-002, EXP-003, ...).
    Windows must be non-overlapping in their VALIDATION periods to satisfy
    the "independent experiments" requirement for G4 evidence (HYP-001).
    """
    exp_id: str           # e.g., "EXP-002"
    train_end_date: str   # Last date included in TRAIN (inclusive, "YYYY-MM-DD")
    val_end_date: str     # Last date included in VALIDATION (inclusive, "YYYY-MM-DD")
    description: str      # Human-readable window description
    snapshot_id: str      # SNAP-YYYY-MM-DD-NNN — must be pre-registered


@dataclass
class BacktestResult:
    """
    Metrics and metadata produced by one backtesting window run.

    All float fields are None if the corresponding metric could not be computed
    (e.g., insufficient samples, only one class present in y_true).
    """
    exp_id: str
    session_id: str
    snapshot_id: str
    model_version: str
    window_def: BacktestWindowDef
    train_rows: int
    val_rows: int
    test_rows_held_out: int
    # Validation set model metrics
    validation_brier_model: float | None
    validation_brier_null: float | None
    validation_log_loss: float | None
    validation_ece: float | None
    validation_auc_roc: float | None
    # Train set model metrics (in-sample, informational only)
    train_brier_model: float | None
    train_brier_null: float | None
    # Derived
    brier_improvement: float | None  # null_brier - model_brier (positive = model beats null)
    beats_null: bool | None          # True if brier_improvement > 0
    # C4 gate check
    c4_gate_result: str
    # Output paths
    output_dir: str
    audit_log_path: str
    # Errors (populated only if something failed non-fatally)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Metric helpers
# (defined here independently of run_exp001.py to avoid cross-module coupling)
# ---------------------------------------------------------------------------


def _build_target(feature_df: pd.DataFrame, window: int = FEATURE_WINDOW) -> pd.Series:
    """
    Binary target: y = 1 if pts >= pts_l{window}_mean (prior games), else 0.

    Temporal integrity: pts_l{window}_mean is from prior games only
    (C2 applies .shift(1) before .rolling()). pts is the current-game outcome
    and is excluded from the feature matrix — used only here for target construction.
    """
    col_name = f"pts_l{window}_mean"
    if col_name not in feature_df.columns or "pts" not in feature_df.columns:
        return pd.Series([np.nan] * len(feature_df), index=feature_df.index)

    pts = pd.to_numeric(feature_df["pts"], errors="coerce")
    pts_prior_mean = pd.to_numeric(feature_df[col_name], errors="coerce")
    target = (pts >= pts_prior_mean).astype("Int8")
    target[pts.isna() | pts_prior_mean.isna()] = pd.NA  # type: ignore[call-overload]  # pandas-stubs: no NAType overload for bool-mask key
    return target


def _compute_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    set_name: str,
) -> dict[str, Any]:
    """
    Brier score, log loss, ECE (10 equal-width bins), AUC-ROC.

    Returns a dict with None values for any metric that fails to compute.
    All errors are stored in the dict for audit purposes, not raised.
    """
    metrics: dict[str, Any] = {
        "set": set_name,
        "n_samples": len(y_true),
        "brier_score": None,
        "log_loss": None,
        "ece": None,
        "auc_roc": None,
    }

    if len(y_true) == 0:
        return metrics

    y_prob_clipped = np.clip(y_prob, 1e-6, 1 - 1e-6)

    try:
        metrics["brier_score"] = float(brier_score_loss(y_true, y_prob))
    except Exception as exc:
        metrics["brier_score_error"] = str(exc)

    try:
        metrics["log_loss"] = float(log_loss(y_true, y_prob_clipped))
    except Exception as exc:
        metrics["log_loss_error"] = str(exc)

    try:
        if len(np.unique(y_true)) >= 2:
            metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob))
        else:
            metrics["auc_roc_note"] = "Only one class present in y_true"
    except Exception as exc:
        metrics["auc_roc_error"] = str(exc)

    # ECE — 10 equal-width bins (strategy="uniform" matches run_exp001.py)
    try:
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_true, y_prob_clipped, n_bins=10, strategy="uniform"
        )
        bin_weights = np.histogram(y_prob_clipped, bins=10, range=(0.0, 1.0))[0]
        bin_weights = bin_weights[bin_weights > 0]
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
    except Exception as exc:
        metrics["ece_error"] = str(exc)

    return metrics


def _compute_null_metrics(y_true: np.ndarray, set_name: str) -> dict[str, Any]:
    """Null model: constant p = 0.50 (Phase 3 placeholder — no live venue price)."""
    y_null = np.full(len(y_true), PLACEHOLDER_MARKET_IMPLIED_PROB)
    metrics = _compute_metrics(y_true, y_null, set_name=f"{set_name}_null")
    metrics["null_model"] = True
    metrics["null_prob"] = PLACEHOLDER_MARKET_IMPLIED_PROB
    return metrics


# ---------------------------------------------------------------------------
# Backtester
# ---------------------------------------------------------------------------


class Backtester:
    """
    Walk-forward backtesting framework for the C1→C2→C3→C4 pipeline.

    Accepts a pre-ingested raw game log DataFrame (output of C1
    NBAIngestionClient) and runs it through C2→C3→C4 for each window
    definition supplied, producing one BacktestResult per window.

    The raw DataFrame is NOT modified. Each window applies fresh feature
    computation and model fitting via independent C2 and C3 instances.
    This satisfies the "independent experiments" requirement for G4 (HYP-001).

    Usage::

        backtester = Backtester(logger=audit_logger, snapshot_id="SNAP-2026-05-27-002")

        ok, result = backtester.run_window(
            raw_df=raw_game_logs,
            window_def=BacktestWindowDef(
                exp_id="EXP-002",
                train_end_date="2022-01-31",
                val_end_date="2022-04-10",
                description="Window 2 — 2021-22 season second half",
                snapshot_id="SNAP-2026-05-27-002",
            ),
            output_dir=Path("exp_output/EXP-002"),
            session_id="BACKTEST-EXP-002-ABCD1234",
        )
        if not ok:
            _kill_switch("Backtester.run_window failed — C6 write failure")
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        window: int = FEATURE_WINDOW,
        market_implied_prob: float = PLACEHOLDER_MARKET_IMPLIED_PROB,
    ) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._window = window
        self._market_implied_prob = market_implied_prob

    # ------------------------------------------------------------------
    # Single-window runner
    # ------------------------------------------------------------------

    def run_window(
        self,
        raw_df: pd.DataFrame,
        window_def: BacktestWindowDef,
        output_dir: Path,
        session_id: str,
        dry_run: bool = False,
    ) -> tuple[bool, BacktestResult | None]:
        """
        Run one backtest window: C2 → C3 → C4 → metrics.

        Parameters
        ----------
        raw_df:
            Full raw game log DataFrame (C1 output, IF-C1-C2 schema).
            All three seasons may be present; only rows within the
            train/val windows are used for fitting and evaluation.
            TEST rows (post val_end_date) are never accessed.
        window_def:
            Window configuration (dates, exp_id, snapshot_id).
        output_dir:
            Per-window output directory. Created if it does not exist.
        session_id:
            Unique run identifier for this window (propagated to all C6 events).
        dry_run:
            If True, skip writing output CSVs to disk.

        Returns
        -------
        (bool, BacktestResult | None)
            bool — False if any C6 write failed (caller must trigger kill switch).
            BacktestResult — None only if a fatal error occurred before metrics.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / f"audit_{window_def.exp_id.lower()}.jsonl"

        ok = self._logger.info(
            COMPONENT,
            "backtest_window_start",
            payload={
                "exp_id": window_def.exp_id,
                "session_id": session_id,
                "snapshot_id": window_def.snapshot_id,
                "train_end_date": window_def.train_end_date,
                "val_end_date": window_def.val_end_date,
                "description": window_def.description,
                "feature_window": self._window,
                "market_implied_prob": self._market_implied_prob,
            },
            session_id=session_id,
            snapshot_id=window_def.snapshot_id,
        )
        if not ok:
            return False, None

        print(f"\n{'='*60}")
        print(f"{window_def.exp_id}: {window_def.description}")
        print(f"  Train: ≤ {window_def.train_end_date} | Val: {window_def.train_end_date} → {window_def.val_end_date}")
        print(f"  Session: {session_id}")
        print(f"{'='*60}")

        # ------------------------------------------------------------------
        # C2 — Feature derivation
        # ------------------------------------------------------------------
        print(f"\n[C2] Computing features (window={self._window} games)...")

        store = FeatureStore(
            logger=self._logger,
            snapshot_id=window_def.snapshot_id,
            window=self._window,
        )
        ok, feature_df = store.compute_features_bulk(
            game_log_df=raw_df,
            session_id=session_id,
        )
        if not ok:
            return False, None

        feature_names = store.get_feature_names()
        print(f"[C2] {len(feature_df):,} rows | {len(feature_names)} features")

        # Assign chronological train/val/test labels
        ok, feature_df = store.assign_train_test_labels(
            feature_df=feature_df,
            train_end_date=window_def.train_end_date,
            val_end_date=window_def.val_end_date,
            session_id=session_id,
        )
        if not ok:
            return False, None

        label_counts = feature_df["train_test_label"].value_counts(dropna=False).to_dict()
        print(f"[C2] Split labels: {label_counts}")

        if not dry_run:
            feat_path = output_dir / f"{window_def.exp_id}_feature_matrix.csv"
            feature_df.to_csv(feat_path, index=False)
            print(f"[C2] Feature matrix saved: {feat_path}")

        # ------------------------------------------------------------------
        # Target variable construction
        # ------------------------------------------------------------------
        print(f"[TARGET] Building binary target: pts >= pts_l{self._window}_mean (prior games)")
        feature_df["y_target"] = _build_target(feature_df, window=self._window)

        usable_mask = (
            feature_df["y_target"].notna()
            & feature_df["temporal_cutoff"].notna()
        )
        usable_df = feature_df[usable_mask].copy()
        print(f"[TARGET] Usable rows: {len(usable_df):,} / {len(feature_df):,}")
        print(f"  Class balance: {usable_df['y_target'].value_counts().to_dict()}")

        train_df = usable_df[usable_df["train_test_label"] == "TRAIN"].copy()
        val_df = usable_df[usable_df["train_test_label"] == "VALIDATION"].copy()
        test_count = int((usable_df["train_test_label"] == "TEST").sum())

        print(f"[TARGET] TRAIN: {len(train_df):,} | VALIDATION: {len(val_df):,} | "
              f"TEST: {test_count} (HELD OUT — not accessed)")

        ok = self._logger.info(
            COMPONENT,
            "target_construction_complete",
            payload={
                "exp_id": window_def.exp_id,
                "train_rows": len(train_df),
                "val_rows": len(val_df),
                "test_rows": test_count,
                "usable_rows": len(usable_df),
                "class_balance": usable_df["y_target"].value_counts().to_dict(),
            },
            session_id=session_id,
            snapshot_id=window_def.snapshot_id,
        )
        if not ok:
            return False, None

        if len(train_df) < MIN_TRAIN_SAMPLES:
            ok = self._logger.error(
                COMPONENT,
                "insufficient_train_samples",
                payload={
                    "exp_id": window_def.exp_id,
                    "train_rows": len(train_df),
                    "minimum": MIN_TRAIN_SAMPLES,
                },
                session_id=session_id,
                snapshot_id=window_def.snapshot_id,
            )
            result = BacktestResult(
                exp_id=window_def.exp_id,
                session_id=session_id,
                snapshot_id=window_def.snapshot_id,
                model_version="FAILED_INSUFFICIENT_TRAIN",
                window_def=window_def,
                train_rows=len(train_df),
                val_rows=len(val_df),
                test_rows_held_out=test_count,
                validation_brier_model=None,
                validation_brier_null=None,
                validation_log_loss=None,
                validation_ece=None,
                validation_auc_roc=None,
                train_brier_model=None,
                train_brier_null=None,
                brier_improvement=None,
                beats_null=None,
                c4_gate_result="SKIPPED_INSUFFICIENT_TRAIN",
                output_dir=str(output_dir),
                audit_log_path=str(log_path),
                errors=[f"Insufficient train samples: {len(train_df)} < {MIN_TRAIN_SAMPLES}"],
            )
            return (ok if ok else False), result

        # ------------------------------------------------------------------
        # C3 — Fit and predict
        # ------------------------------------------------------------------
        print(f"\n[C3] Fitting ModelForecaster on {len(train_df):,} TRAIN rows...")

        forecaster = ModelForecaster(
            logger=self._logger,
            snapshot_id=window_def.snapshot_id,
            feature_names=feature_names,
        )

        y_train = train_df["y_target"].astype(int)
        fit_ok = forecaster.fit(
            feature_df=train_df,
            target=y_train,
            session_id=session_id,
        )
        if not fit_ok:
            return False, None

        print(f"[C3] Model fitted: {forecaster.model_version}")

        print(f"\n[C3] Generating forecasts on {len(val_df):,} VALIDATION rows...")
        ok, forecast_df = forecaster.predict(
            feature_df=val_df,
            market_implied_prob=self._market_implied_prob,
            session_id=session_id,
        )
        if not ok:
            return False, None

        direction_counts = forecast_df["recommended_direction"].value_counts().to_dict()
        print(f"[C3] Forecasts generated: {len(forecast_df):,} | directions: {direction_counts}")

        if not dry_run:
            fcst_path = output_dir / f"{window_def.exp_id}_forecast_validation.csv"
            forecast_df.to_csv(fcst_path, index=False)
            print(f"[C3] Forecast output saved: {fcst_path}")

        # ------------------------------------------------------------------
        # Metrics — VALIDATION set
        # ------------------------------------------------------------------
        print("\n[METRICS] Computing validation metrics...")

        y_val = val_df["y_target"].astype(int).to_numpy()
        y_prob_val = forecast_df["p_estimate"].to_numpy()

        model_metrics = _compute_metrics(y_val, y_prob_val, "VALIDATION")
        null_metrics = _compute_null_metrics(y_val, "VALIDATION")

        # Train metrics (in-sample, informational only)
        ok2, train_forecast_df = forecaster.predict(
            feature_df=train_df,
            market_implied_prob=self._market_implied_prob,
            session_id=session_id,
        )
        if ok2 and len(train_forecast_df) > 0:
            y_train_true = train_df["y_target"].astype(int).to_numpy()
            y_prob_train = train_forecast_df["p_estimate"].to_numpy()
            train_metrics = _compute_metrics(y_train_true, y_prob_train, "TRAIN")
        else:
            train_metrics = {"set": "TRAIN", "n_samples": len(train_df), "note": "predict failed"}

        null_train_metrics = _compute_null_metrics(
            train_df["y_target"].astype(int).to_numpy(), "TRAIN"
        )

        # Print summary
        _bs = model_metrics.get("brier_score")
        _nbs = null_metrics.get("brier_score")
        _ll = model_metrics.get("log_loss")
        _ece = model_metrics.get("ece")
        _auc = model_metrics.get("auc_roc")

        print(f"\n{'─'*50}")
        print(f"RESULTS — {window_def.exp_id} ({window_def.description})")
        print(f"{'─'*50}")
        print(f"Model version: {forecaster.model_version}")
        print(f"\nTRAIN  (n={len(train_df):,}):")
        _t_bs = train_metrics.get("brier_score")
        _t_nbs = null_train_metrics.get("brier_score")
        print(f"  Brier (model) : {_t_bs:.4f}" if isinstance(_t_bs, float) else "  Brier (model) : N/A")
        print(f"  Brier (null)  : {_t_nbs:.4f}" if isinstance(_t_nbs, float) else "  Brier (null)  : N/A")
        print(f"\nVALIDATION (n={len(val_df):,}):")
        print(f"  Brier (model) : {_bs:.4f}" if isinstance(_bs, float) else "  Brier (model) : N/A")
        print(f"  Brier (null)  : {_nbs:.4f}" if isinstance(_nbs, float) else "  Brier (null)  : N/A")
        if isinstance(_bs, float) and isinstance(_nbs, float):
            improvement = _nbs - _bs
            print(f"  Improvement   : {improvement:+.4f} ({'✓ beats null' if improvement > 0 else '✗ worse than null'})")
        print(f"  Log Loss      : {_ll:.4f}" if isinstance(_ll, float) else "  Log Loss      : N/A")
        print(f"  ECE           : {_ece:.4f}" if isinstance(_ece, float) else "  ECE           : N/A")
        print(f"  AUC-ROC       : {_auc:.4f}" if isinstance(_auc, float) else "  AUC-ROC       : N/A")
        print(f"{'─'*50}")
        print(f"TEST SET: HELD OUT — not accessed (accessed only at G4 gate)")
        print(f"{'─'*50}\n")

        # Log metrics to C6
        brier_improvement = None
        if isinstance(_bs, float) and isinstance(_nbs, float):
            brier_improvement = _nbs - _bs

        ok = self._logger.info(
            COMPONENT,
            "backtest_window_metrics_complete",
            payload={
                "exp_id": window_def.exp_id,
                "model_version": forecaster.model_version,
                "snapshot_id": window_def.snapshot_id,
                "validation_metrics": {
                    "brier_score": _bs,
                    "log_loss": _ll,
                    "ece": _ece,
                    "auc_roc": _auc,
                    "n_samples": model_metrics.get("n_samples"),
                },
                "null_model_metrics": {
                    "brier_score": _nbs,
                    "null_prob": self._market_implied_prob,
                },
                "train_metrics": {
                    "brier_score": _t_bs,
                    "n_samples": len(train_df),
                },
                "brier_improvement": brier_improvement,
                "beats_null": (brier_improvement > 0) if brier_improvement is not None else None,
            },
            session_id=session_id,
            snapshot_id=window_def.snapshot_id,
        )
        if not ok:
            return False, None

        # ------------------------------------------------------------------
        # C4 — Phase gate check (expect REJECTED in ENV-01)
        # ------------------------------------------------------------------
        print(f"[C4] Routing first validation forecast through RiskEngine (phase gate check)...")

        c4_gate_result = "no_forecasts"
        c4_decision: dict[str, Any] = {}
        if len(forecast_df) > 0:
            sample_forecast = forecast_df.iloc[0].to_dict()
            engine = RiskEngine(
                logger=self._logger,
                snapshot_id=window_def.snapshot_id,
                bankroll=10000.0,
            )
            # portfolio_equity_usd omitted (T-175): backtester calls C4 as a
            # gate check only; BOT_C4_ACTIVE is not set, so CHECK 8 is never reached.
            ok, c4_decision = engine.evaluate_forecast(
                forecast_record=sample_forecast,
                session_id=session_id,
            )
            if not ok:
                return False, None

            c4_gate_result = c4_decision.get("approval_status", "UNKNOWN")
            c4_reason = c4_decision.get("rejection_reason", "")
            print(f"[C4] Status: {c4_gate_result} | Reason: {c4_reason}")

            if c4_gate_result != "REJECTED" or c4_reason != "phase_gate_not_reached":
                ok = self._logger.error(
                    "C4",
                    "unexpected_gate_state",
                    payload={
                        "exp_id": window_def.exp_id,
                        "expected_status": "REJECTED",
                        "expected_reason": "phase_gate_not_reached",
                        "actual_status": c4_gate_result,
                        "actual_reason": c4_reason,
                        "note": (
                            "C4 should return REJECTED(phase_gate_not_reached) in ENV-01. "
                            "BOT_C4_ACTIVE must NOT be set in ENV-01 or ENV-02."
                        ),
                    },
                    session_id=session_id,
                    snapshot_id=window_def.snapshot_id,
                )
                if not ok:
                    return False, None
            else:
                print(f"[C4] ✓ Phase gate correctly rejected (expected in ENV-01)")

        # ------------------------------------------------------------------
        # Session close
        # ------------------------------------------------------------------
        ok = self._logger.info(
            COMPONENT,
            "backtest_window_complete",
            payload={
                "exp_id": window_def.exp_id,
                "session_id": session_id,
                "model_version": forecaster.model_version,
                "snapshot_id": window_def.snapshot_id,
                "validation_brier_model": _bs,
                "validation_brier_null": _nbs,
                "brier_improvement": brier_improvement,
                "output_dir": str(output_dir),
            },
            session_id=session_id,
            snapshot_id=window_def.snapshot_id,
        )
        if not ok:
            return False, None

        result = BacktestResult(
            exp_id=window_def.exp_id,
            session_id=session_id,
            snapshot_id=window_def.snapshot_id,
            model_version=forecaster.model_version,
            window_def=window_def,
            train_rows=len(train_df),
            val_rows=len(val_df),
            test_rows_held_out=test_count,
            validation_brier_model=_bs,
            validation_brier_null=_nbs,
            validation_log_loss=_ll,
            validation_ece=_ece,
            validation_auc_roc=_auc,
            train_brier_model=_t_bs if isinstance(_t_bs, float) else None,
            train_brier_null=_t_nbs if isinstance(_t_nbs, float) else None,
            brier_improvement=brier_improvement,
            beats_null=(brier_improvement > 0) if brier_improvement is not None else None,
            c4_gate_result=c4_gate_result,
            output_dir=str(output_dir),
            audit_log_path=str(log_path),
        )

        print(f"[COMPLETE] {window_def.exp_id} window finished. Outputs: {output_dir}\n")
        return True, result

    # ------------------------------------------------------------------
    # Multi-window runner (sequential — chronological order)
    # ------------------------------------------------------------------

    def run_windows(
        self,
        raw_df: pd.DataFrame,
        windows: list[BacktestWindowDef],
        base_output_dir: Path,
        dry_run: bool = False,
    ) -> tuple[bool, list[BacktestResult]]:
        """
        Run multiple backtesting windows in sequence.

        Windows are executed in the order supplied. Callers are responsible
        for ordering windows chronologically (oldest-first) to match the
        walk-forward convention.

        Returns (bool, list[BacktestResult]).
        bool is False if any window's C6 write failed.
        The list contains results for all windows attempted (including partial
        results for windows that failed non-fatally).
        """
        results: list[BacktestResult] = []

        for window_def in windows:
            session_id = f"BACKTEST-{window_def.exp_id}-{uuid.uuid4().hex[:8].upper()}"
            window_output_dir = base_output_dir / window_def.exp_id

            ok, result = self.run_window(
                raw_df=raw_df,
                window_def=window_def,
                output_dir=window_output_dir,
                session_id=session_id,
                dry_run=dry_run,
            )

            if result is not None:
                results.append(result)

            if not ok:
                # C6 write failure — caller must trigger kill switch
                return False, results

        return True, results

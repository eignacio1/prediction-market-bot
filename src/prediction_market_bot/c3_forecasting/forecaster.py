"""
C3: Forecasting Engine — PRF-Aligned Probability Estimation
============================================================
Component:    C3 (Forecasting Engine)
Phase active: Phase 3+ (Research/Backtest)
Status:       SKELETON — CANONICAL (Phase 3 2026-05-26)
Upstream:     C2 Feature Store (IF-C2-C3 feature DataFrame)
Downstream:   C4 Risk Engine (IF-C3-C4 forecast record)
              C6 Audit Logger (IF-ALL-C6)
Interfaces:   IF-C2-C3 (input); IF-C3-C4 (output)
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only),
              ADR-0003 (edge formula: p̂ - mid_price - spread/2)
              ADR-0004 (model class confirmation — PENDING)
Policy refs:  METHODOLOGY.md, ARCHITECTURE_OVERVIEW.md,
              08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md

Model policy (NFR — frozen model):
  - Model is version-pinned at deployment. No automated retraining.
  - model_version is immutable once a model enters ENV-02 or ENV-03.
  - Each experiment must cite model_version and snapshot_id used.
  - Phase 3 model class: LogisticRegression (baseline / null-model comparison).
    Model class confirmed at ADR-0004.

Edge formula (ADR-0003):
  edge = p̂ - mid_price(venue) - (spread(venue) / 2)
  where mid_price = (bid + ask) / 2
  Recommended direction:
    edge > EDGE_THRESHOLD_YES  → YES
    edge < EDGE_THRESHOLD_NO   → NO (fade)
    otherwise                  → PASS

Calibration requirement (FR-03):
  - ECE < 0.05 (Expected Calibration Error)
  - Evaluated in backtesting framework (T-036)
  - Phase 3 baseline: logistic regression with Platt scaling

Kill switch constraint (NFR-03):
  - All public methods return (bool, ...).
  - False on any C6 write failure; callers must trigger kill switch.

Audit events emitted:
  - model_fit_start          (INFO)
  - model_fit_complete       (INFO) — includes model_version, feature_count, sample_count
  - model_fit_error          (ERROR)
  - forecast_start           (INFO)
  - forecast_complete        (INFO) — includes forecast_id, p_estimate, edge
  - forecast_error           (ERROR)
  - edge_threshold_pass      (INFO)
  - model_version_mismatch   (CRITICAL) — serialized version ≠ runtime version

Temporal integrity (TI-01):
  - Model trained only on TRAIN-labelled rows.
  - Inference at backtesting time uses only features with temporal_cutoff
    ≤ the prediction date (enforced by C2 shift(1) window).
  - Model must not be retrained in production (frozen model policy).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C3"

# Phase 3 model class — confirmed at ADR-0004 (pending)
MODEL_CLASS = "LogisticRegression+PlattScaling"

# Edge thresholds — directional signal boundaries
# YES: take the YES side of the market
# NO:  fade the YES side (take NO)
# PASS: insufficient edge to trade
EDGE_THRESHOLD_YES: float = 0.02   # +2% edge minimum to recommend YES
EDGE_THRESHOLD_NO: float = -0.02   # -2% edge minimum to recommend NO (fade)

# Direction labels (IF-C3-C4)
DIR_YES = "YES"
DIR_NO = "NO"
DIR_PASS = "PASS"

# Confidence interval method
CI_Z_90 = 1.645  # z-score for 90% CI

# Minimum samples required to fit a model
MIN_FIT_SAMPLES = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _forecast_id() -> str:
    return f"FCST-{uuid.uuid4().hex[:12].upper()}"


def _model_version_hash(feature_names: list[str], model_class: str) -> str:
    """
    Deterministic model version string derived from feature set and model class.
    Changes whenever the feature set or model class changes — signals that
    downstream consumers (backtesting records, audit log) must cite the new version.
    """
    digest_input = model_class + "|" + ",".join(sorted(feature_names))
    return "v1-" + hashlib.sha1(digest_input.encode()).hexdigest()[:8]


def _compute_ci(p_estimate: float, n_samples: int) -> dict[str, float]:
    """
    Wilson score 90% confidence interval for a proportion.
    Avoids the 0/1 boundary artifacts of normal approximation.
    """
    z = CI_Z_90
    p = max(min(p_estimate, 1.0 - 1e-6), 1e-6)
    n = max(n_samples, 1)
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    margin = (z / (1 + z * z / n)) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return {
        "lower": float(max(0.0, center - margin)),
        "upper": float(min(1.0, center + margin)),
    }


# ---------------------------------------------------------------------------
# ModelForecaster
# ---------------------------------------------------------------------------


class ModelForecaster:
    """
    Phase 3 PRF-aligned probability forecaster.

    Wraps a scikit-learn Pipeline (StandardScaler → LogisticRegression → Platt
    calibration) with full C6 audit trail and kill-switch-compatible return values.

    Usage::

        forecaster = ModelForecaster(
            logger=audit_logger,
            snapshot_id="SNAP-2024-10-01-001",
            feature_names=feature_store.get_feature_names(),
        )

        # Fit on training data
        ok = forecaster.fit(train_feature_df, target_series, session_id=session_id)
        if not ok:
            trigger_kill_switch()

        # Generate forecasts for test data
        ok, forecast_df = forecaster.predict(
            feature_df=test_feature_df,
            market_implied_prob=0.55,   # venue mid-price
            session_id=session_id,
        )

    The model is immutable after fit() — call fit() once, then predict() many times.
    Do NOT call fit() again in ENV-02 or ENV-03 (frozen model policy).
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        feature_names: list[str],
    ) -> None:
        """
        Parameters
        ----------
        logger:
            Shared AuditLogger (C6) instance.
        snapshot_id:
            DS-01 snapshot anchor. Flows through to all forecast records.
        feature_names:
            Ordered list of feature column names expected in input DataFrames.
            Must match FeatureStore.get_feature_names(). Used to enforce
            feature set consistency across fit/predict calls.
        """
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._feature_names = feature_names
        self._model: Pipeline | None = None
        self._model_version: str | None = None
        self._fit_sample_count: int = 0
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(
        self,
        event_type: str,
        payload: dict[str, Any],
        severity: str = "INFO",
        session_id: str | None = None,
        forecast_id: str | None = None,
    ) -> bool:
        return self._logger.log(
            component=COMPONENT,
            event_type=event_type,
            payload=payload,
            severity=severity,
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            forecast_id=forecast_id,
        )

    def _extract_feature_matrix(self, feature_df: pd.DataFrame) -> np.ndarray:
        """
        Extract the feature matrix from a feature DataFrame.

        Only uses columns in self._feature_names that are present in feature_df.
        Fills any missing feature columns with NaN (not silently dropped —
        the model will produce NaN outputs, which are caught downstream).
        """
        available = [f for f in self._feature_names if f in feature_df.columns]
        X = feature_df[available].copy()

        # Add any missing features as NaN columns
        for fname in self._feature_names:
            if fname not in X.columns:
                X[fname] = np.nan

        # Reorder to canonical feature order
        X = X[self._feature_names]
        return X.to_numpy(dtype=np.float64)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        feature_df: pd.DataFrame,
        target: pd.Series,
        session_id: str | None = None,
    ) -> bool:
        """
        Fit the forecasting model on training data.

        Only call once. In ENV-02/03 the model must be loaded from a
        serialized artifact, not re-fitted (frozen model policy).

        Parameters
        ----------
        feature_df:
            IF-C2-C3 DataFrame filtered to TRAIN-labelled rows only.
            Must have train_test_label == "TRAIN" for all rows.
        target:
            Binary Series (0/1) aligned to feature_df rows.
            1 = player achieved the prop threshold for this game.
            Must not include any TEST or VALIDATION rows (TI-02).
        session_id:
            Current run session ID.

        Returns
        -------
        bool — False on C6 write failure; caller triggers kill switch.
        """
        model_version = _model_version_hash(self._feature_names, MODEL_CLASS)

        ok = self._log(
            "model_fit_start",
            {
                "model_class": MODEL_CLASS,
                "model_version": model_version,
                "feature_count": len(self._feature_names),
                "sample_count": len(feature_df),
            },
            session_id=session_id,
        )
        if not ok:
            return False

        if len(feature_df) < MIN_FIT_SAMPLES:
            ok = self._log(
                "model_fit_error",
                {
                    "error": f"Insufficient training samples: {len(feature_df)} < {MIN_FIT_SAMPLES}",
                    "model_version": model_version,
                },
                severity="ERROR",
                session_id=session_id,
            )
            return False

        try:
            # Validate train_test_label — must be TRAIN only
            if "train_test_label" in feature_df.columns:
                non_train = feature_df["train_test_label"].ne("TRAIN").sum()
                if non_train > 0:
                    ok = self._log(
                        "model_fit_error",
                        {
                            "error": f"TI-02 violation: {non_train} non-TRAIN rows in fit() input. "
                                     "Refusing to fit — temporal integrity breach.",
                        },
                        severity="CRITICAL",
                        session_id=session_id,
                    )
                    return False

            X = self._extract_feature_matrix(feature_df)
            y = target.to_numpy()

            # Drop rows where all features are NaN
            valid_mask = ~np.all(np.isnan(X), axis=1)
            X_clean = X[valid_mask]
            y_clean = y[valid_mask]

            if len(X_clean) < MIN_FIT_SAMPLES:
                ok = self._log(
                    "model_fit_error",
                    {
                        "error": f"After NaN removal only {len(X_clean)} valid rows remain (minimum {MIN_FIT_SAMPLES})",
                    },
                    severity="ERROR",
                    session_id=session_id,
                )
                return False

            # Replace remaining NaN with column median (imputation strategy v1)
            col_medians = np.nanmedian(X_clean, axis=0)
            nan_mask = np.isnan(X_clean)
            X_clean[nan_mask] = np.take(col_medians, np.where(nan_mask)[1])

            # Build Pipeline: scaler → logistic → Platt calibration
            base_clf = LogisticRegression(
                C=1.0,
                solver="lbfgs",
                max_iter=1000,
                random_state=42,
                class_weight="balanced",
            )
            pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", CalibratedClassifierCV(base_clf, method="sigmoid", cv=3)),
            ])
            pipeline.fit(X_clean, y_clean)

            self._model = pipeline
            self._model_version = model_version
            self._fit_sample_count = int(len(X_clean))
            self._is_fitted = True

            ok = self._log(
                "model_fit_complete",
                {
                    "model_class": MODEL_CLASS,
                    "model_version": model_version,
                    "feature_count": len(self._feature_names),
                    "sample_count_used": self._fit_sample_count,
                    "sample_count_dropped_nan": int(valid_mask.sum() - len(X_clean)) + int((~valid_mask).sum()),
                },
                session_id=session_id,
            )
            return ok

        except Exception as exc:
            ok = self._log(
                "model_fit_error",
                {"error": repr(exc), "model_version": model_version},
                severity="ERROR",
                session_id=session_id,
            )
            return False

    def predict(
        self,
        feature_df: pd.DataFrame,
        market_implied_prob: float | pd.Series,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Generate probability forecasts and edge calculations for a feature DataFrame.

        Parameters
        ----------
        feature_df:
            IF-C2-C3 DataFrame (VALIDATION or TEST labelled rows, or unseen data).
            Must not include TRAIN rows (TI-02 — use only future data).
        market_implied_prob:
            Venue mid-price probability. Either a scalar (applied to all rows)
            or a Series aligned to feature_df index.
            Formula: mid_price = (bid + ask) / 2  (ADR-0003)
            Pass np.nan for rows with no live market price (research mode).
        session_id:
            Current run session ID.

        Returns
        -------
        (all_ok, forecast_df):
            all_ok — False if C6 write failed; caller triggers kill switch.
            forecast_df — IF-C3-C4 DataFrame with one row per input row.
                          Empty DataFrame on unhandled exception.
        """
        if not self._is_fitted or self._model is None:
            ok = self._log(
                "forecast_error",
                {"error": "Model has not been fitted. Call fit() before predict()."},
                severity="ERROR",
                session_id=session_id,
            )
            return False, pd.DataFrame()

        forecast_id = _forecast_id()
        all_ok = True

        ok = self._log(
            "forecast_start",
            {
                "forecast_id": forecast_id,
                "model_version": self._model_version,
                "input_rows": len(feature_df),
            },
            session_id=session_id,
            forecast_id=forecast_id,
        )
        if not ok:
            all_ok = False

        try:
            X = self._extract_feature_matrix(feature_df)

            # Impute NaN with zeros (inference-time: median not available from test set)
            X = np.where(np.isnan(X), 0.0, X)

            # Predict class probabilities — column 1 = P(YES)
            p_estimates = self._model.predict_proba(X)[:, 1]

            # Market implied probability alignment
            if isinstance(market_implied_prob, (int, float)):
                mip_arr = np.full(len(feature_df), float(market_implied_prob))
            else:
                mip_arr = market_implied_prob.to_numpy(dtype=np.float64)

            # Edge = p̂ - mid_price  (spread/2 = 0 for research — no live spread data)
            # ADR-0003: edge = p̂ - mid_price(venue) - (spread(venue)/2)
            # Spread component deferred to Phase 6 when live venue prices are available.
            edges = p_estimates - mip_arr

            # Directional recommendation
            directions = np.where(
                edges >= EDGE_THRESHOLD_YES, DIR_YES,
                np.where(edges <= EDGE_THRESHOLD_NO, DIR_NO, DIR_PASS)
            )

            # Build IF-C3-C4 output DataFrame
            result_rows = []
            for i in range(len(feature_df)):
                row_in = feature_df.iloc[i]
                p_est = float(p_estimates[i])
                ci = _compute_ci(p_est, self._fit_sample_count)
                result_rows.append({
                    # Traceability
                    "forecast_id": forecast_id,
                    "model_version": self._model_version,
                    "snapshot_id": self._snapshot_id,
                    "feature_version": row_in.get("feature_version", None),
                    "feature_run_id": row_in.get("feature_run_id", None),
                    # Identity
                    "player_id": row_in.get("player_id", None),
                    "player_name": row_in.get("player_name", None),
                    "game_id": row_in.get("game_id", None),
                    "game_date": row_in.get("game_date", None),
                    "season": row_in.get("season", None),
                    "season_type": row_in.get("season_type", None),
                    # IF-C3-C4 contract fields
                    "p_estimate": p_est,
                    "ci_lower": ci["lower"],
                    "ci_upper": ci["upper"],
                    "market_implied_prob": float(mip_arr[i]),
                    "edge": float(edges[i]),
                    "recommended_direction": str(directions[i]),
                    # Temporal integrity
                    "temporal_cutoff": row_in.get("temporal_cutoff", None),
                    "train_test_label": row_in.get("train_test_label", None),
                    # Timestamp
                    "forecast_timestamp": _utc_now_iso(),
                })

            forecast_df = pd.DataFrame(result_rows)

            # Summary log entry
            valid_edges = edges[~np.isnan(edges)]
            ok = self._log(
                "forecast_complete",
                {
                    "forecast_id": forecast_id,
                    "model_version": self._model_version,
                    "output_rows": len(forecast_df),
                    "edge_threshold_yes": EDGE_THRESHOLD_YES,
                    "edge_threshold_no": EDGE_THRESHOLD_NO,
                    "direction_counts": {
                        DIR_YES: int((directions == DIR_YES).sum()),
                        DIR_NO: int((directions == DIR_NO).sum()),
                        DIR_PASS: int((directions == DIR_PASS).sum()),
                    },
                    "p_estimate_mean": float(np.nanmean(p_estimates)) if len(p_estimates) > 0 else None,
                    "edge_mean": float(np.nanmean(valid_edges)) if len(valid_edges) > 0 else None,
                },
                session_id=session_id,
                forecast_id=forecast_id,
            )
            if not ok:
                all_ok = False

            return all_ok, forecast_df

        except Exception as exc:
            ok = self._log(
                "forecast_error",
                {"error": repr(exc), "forecast_id": forecast_id},
                severity="ERROR",
                session_id=session_id,
                forecast_id=forecast_id,
            )
            if not ok:
                all_ok = False
            return False, pd.DataFrame()

    @property
    def model_version(self) -> str | None:
        """The version string of the currently fitted model. None if not fitted."""
        return self._model_version

    @property
    def is_fitted(self) -> bool:
        """True if the model has been successfully fitted."""
        return self._is_fitted

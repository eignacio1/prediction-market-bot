"""
C3: Shadow Model Forecaster (ADR-0009)
=======================================
Component:    C3 (Forecasting Engine — shadow arm)
Phase active: Phase 6+ (optional parallel monitoring)
Status:       ACTIVE when models/shadow_model.joblib is present; INACTIVE otherwise
Upstream:     PIPE-02 (run_pregame.py) — receives feature row per player
Downstream:   C6 Audit Logger only — NEVER routes to C4
ADR refs:     ADR-0009 (shadow model policy)
Policy refs:  Shadow is monitoring-only. Promotion requires ADR-0010 + DS sign-off.

Isolation guarantee (ADR-0009 §1):
  Shadow output never reaches C4. No bet is ever sized or placed from
  a shadow estimate. Any code path routing shadow output to C4 is a defect.

Artifact spec (ADR-0009 §2):
  models/shadow_model.joblib — same structure as prod_model.joblib:
    pipeline       — fitted sklearn pipeline
    feature_names  — list of feature column names (may differ from prod)
    col_medians    — per-feature medians for imputation
    model_version  — deterministic version hash

Optional presence (ADR-0009 §3):
  System operates normally if shadow_model.joblib is absent.
  shadow.available == False → caller skips shadow inference; no error raised.

C6 logging (ADR-0009 §4):
  Every shadow prediction → event_type: shadow_forecast_emitted, shadow: True
  Errors            → event_type: shadow_forecast_error, shadow: True (WARNING)
  Load failures     → event_type: shadow_load_failed (WARNING)

Kill switch constraint (NFR-03):
  All public methods return without raising. Shadow failure is non-fatal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

COMPONENT = "C3"
DEFAULT_SHADOW_PATH = Path("models/shadow_model.joblib")


def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    if mask.any():
        X[mask] = np.take(medians, np.where(mask)[1])
    return X


class ShadowForecaster:
    """
    Optional parallel forecaster for calibration comparison against production.

    Loads models/shadow_model.joblib if present. Runs inference independently
    of production at PIPE-02 time. Output is C6-only — never reaches C4.

    Usage::

        shadow = ShadowForecaster(logger=audit_logger, snapshot_id=SNAPSHOT_ID)

        if shadow.available:
            print(f"[SHADOW] {shadow.model_version} loaded")

        # In the player inference loop:
        p_shadow = shadow.predict_shadow(row, session_id=session_id)
        # p_shadow is float or None (None if unavailable or inference failed)
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        shadow_model_path: Path | str | None = None,
    ) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._path = Path(shadow_model_path) if shadow_model_path else DEFAULT_SHADOW_PATH

        self._pipeline: Any = None
        self._feature_names: list[str] = []
        self._col_medians: np.ndarray = np.array([])
        self._model_version: str | None = None
        self._available: bool = False

        self._load()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            artifact = joblib.load(self._path)
            self._pipeline     = artifact["pipeline"]
            self._feature_names = list(artifact["feature_names"])
            self._col_medians  = np.array(artifact["col_medians"], dtype=float)
            self._model_version = str(artifact["model_version"])
            self._available = True
        except Exception as exc:
            self._logger.log(
                component=COMPONENT,
                event_type="shadow_load_failed",
                payload={"path": str(self._path), "error": repr(exc), "shadow": True},
                severity="WARNING",
            )

    def _log(self, event_type: str, payload: dict[str, Any], severity: str = "INFO",
             session_id: str | None = None) -> None:
        self._logger.log(
            component=COMPONENT,
            event_type=event_type,
            payload=payload,
            severity=severity,
            session_id=session_id,
            snapshot_id=self._snapshot_id,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """True if shadow_model.joblib was loaded successfully."""
        return self._available

    @property
    def model_version(self) -> str | None:
        """Version hash of the shadow artifact. None if not loaded."""
        return self._model_version

    def predict_shadow(
        self,
        row: pd.Series,
        session_id: str | None = None,
    ) -> float | None:
        """
        Run shadow inference on a feature row.

        Parameters
        ----------
        row:
            A pandas Series from the feature matrix (same format as prod).
            Shadow model may have a different feature set — handled by index lookup.
        session_id:
            Current PIPE-02 session ID (for C6 traceability).

        Returns
        -------
        float | None
            Shadow p_estimate in [0, 1], or None if unavailable or inference failed.
            Never raises — shadow failure is non-fatal.
        """
        if not self._available:
            return None
        try:
            X = np.array(
                [[row[c] if c in row.index else np.nan for c in self._feature_names]],
                dtype=float,
            )
            X = _impute(X, self._col_medians)
            p_shadow = float(self._pipeline.predict_proba(X)[0, 1])

            self._log(
                "shadow_forecast_emitted",
                {
                    "shadow_model_version": self._model_version,
                    "shadow_p_estimate": round(p_shadow, 4),
                    "shadow": True,
                },
                session_id=session_id,
            )
            return p_shadow

        except Exception as exc:
            self._log(
                "shadow_forecast_error",
                {"shadow_model_version": self._model_version, "error": repr(exc), "shadow": True},
                severity="WARNING",
                session_id=session_id,
            )
            return None

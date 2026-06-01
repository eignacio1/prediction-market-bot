"""
Tests for src/prediction_market_bot/c3_forecasting/shadow_forecaster.py

Coverage areas:
  - ShadowForecaster.available: False when file absent
  - ShadowForecaster.available: True when valid artifact present
  - ShadowForecaster.model_version: None when not loaded; str when loaded
  - ShadowForecaster.predict_shadow: returns None when unavailable
  - ShadowForecaster.predict_shadow: returns float in [0,1] from loaded model
  - ShadowForecaster.predict_shadow: handles missing feature columns (NaN fallback)
  - ShadowForecaster.predict_shadow: logs shadow_forecast_emitted to C6
  - ShadowForecaster.predict_shadow: returns None on inference error (non-fatal)
  - ShadowForecaster._load: handles corrupted artifact gracefully (logs WARNING)
  - Isolation guarantee: shadow output never modifies production state
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c3_forecasting.shadow_forecaster import ShadowForecaster


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_logger(write_ok: bool = True) -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = write_ok
    return logger


def _make_artifact(feature_names: list[str]) -> dict:
    """Build a minimal valid shadow model artifact for testing."""
    X = np.random.default_rng(0).random((100, len(feature_names)))
    y = (X[:, 0] > 0.5).astype(int)
    base = LogisticRegression(C=1.0, random_state=42, max_iter=200)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
    ])
    pipeline.fit(X, y)
    medians = np.median(X, axis=0)
    return {
        "pipeline": pipeline,
        "feature_names": feature_names,
        "col_medians": medians,
        "model_version": "v1-shadow-test",
    }


def _write_artifact(artifact: dict, path: Path) -> None:
    joblib.dump(artifact, path)


def _make_row(feature_names: list[str], seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series({f: float(rng.random()) for f in feature_names})


# ---------------------------------------------------------------------------
# Absent model
# ---------------------------------------------------------------------------


class TestAbsentModel:
    @pytest.mark.unit
    def test_available_false_when_no_file(self, tmp_path):
        logger = _make_logger()
        shadow = ShadowForecaster(
            logger=logger,
            snapshot_id="SNAP-TEST",
            shadow_model_path=tmp_path / "shadow_model.joblib",
        )
        assert shadow.available is False

    @pytest.mark.unit
    def test_model_version_none_when_not_loaded(self, tmp_path):
        logger = _make_logger()
        shadow = ShadowForecaster(
            logger=logger,
            snapshot_id="SNAP-TEST",
            shadow_model_path=tmp_path / "shadow_model.joblib",
        )
        assert shadow.model_version is None

    @pytest.mark.unit
    def test_predict_returns_none_when_unavailable(self, tmp_path):
        logger = _make_logger()
        shadow = ShadowForecaster(
            logger=logger,
            snapshot_id="SNAP-TEST",
            shadow_model_path=tmp_path / "shadow_model.joblib",
        )
        row = pd.Series({"feature_a": 0.5})
        result = shadow.predict_shadow(row)
        assert result is None

    @pytest.mark.unit
    def test_no_c6_log_when_unavailable(self, tmp_path):
        logger = _make_logger()
        shadow = ShadowForecaster(
            logger=logger,
            snapshot_id="SNAP-TEST",
            shadow_model_path=tmp_path / "shadow_model.joblib",
        )
        row = pd.Series({"feature_a": 0.5})
        shadow.predict_shadow(row)
        logger.log.assert_not_called()


# ---------------------------------------------------------------------------
# Valid artifact loaded
# ---------------------------------------------------------------------------


class TestValidArtifact:
    @pytest.mark.unit
    def test_available_true_when_file_present(self, tmp_path):
        features = ["f1", "f2", "f3"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        assert shadow.available is True

    @pytest.mark.unit
    def test_model_version_set(self, tmp_path):
        features = ["f1", "f2"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        assert shadow.model_version == "v1-shadow-test"

    @pytest.mark.unit
    def test_predict_returns_float_in_unit_interval(self, tmp_path):
        features = ["f1", "f2", "f3"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        row = _make_row(features)
        p = shadow.predict_shadow(row, session_id="SES-TEST")
        assert isinstance(p, float)
        assert 0.0 <= p <= 1.0

    @pytest.mark.unit
    def test_predict_logs_shadow_event_to_c6(self, tmp_path):
        features = ["f1", "f2"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        row = _make_row(features)
        shadow.predict_shadow(row, session_id="SES-001")

        logger.log.assert_called_once()
        call_kwargs = logger.log.call_args
        assert call_kwargs.kwargs["event_type"] == "shadow_forecast_emitted"
        payload = call_kwargs.kwargs["payload"]
        assert payload["shadow"] is True
        assert "shadow_p_estimate" in payload
        assert "shadow_model_version" in payload

    @pytest.mark.unit
    def test_predict_handles_missing_features_gracefully(self, tmp_path):
        """Row missing some shadow model features → NaN imputed → still returns float."""
        features = ["f1", "f2", "f3"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        # Row only has f1 — f2, f3 are absent → should NaN-impute and return float
        row = pd.Series({"f1": 0.7})
        p = shadow.predict_shadow(row)
        assert isinstance(p, float)
        assert 0.0 <= p <= 1.0

    @pytest.mark.unit
    def test_predict_does_not_raise_on_broken_pipeline(self, tmp_path):
        """Shadow inference failure is non-fatal — returns None, logs WARNING."""
        features = ["f1", "f2"]
        artifact = _make_artifact(features)
        # Replace pipeline with a broken object
        artifact["pipeline"] = "not_a_pipeline"
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        row = _make_row(features)
        result = shadow.predict_shadow(row)
        assert result is None

        # Should have logged a warning
        logger.log.assert_called_once()
        call_kwargs = logger.log.call_args
        assert call_kwargs.kwargs["severity"] == "WARNING"
        assert call_kwargs.kwargs["event_type"] == "shadow_forecast_error"

    @pytest.mark.unit
    def test_load_failure_logs_warning_not_raises(self, tmp_path):
        """Corrupted joblib file → available=False, WARNING logged, no exception."""
        path = tmp_path / "shadow_model.joblib"
        path.write_bytes(b"corrupted data not a joblib file")

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        assert shadow.available is False
        logger.log.assert_called_once()
        call_kwargs = logger.log.call_args
        assert call_kwargs.kwargs["severity"] == "WARNING"
        assert call_kwargs.kwargs["event_type"] == "shadow_load_failed"


# ---------------------------------------------------------------------------
# Isolation guarantee
# ---------------------------------------------------------------------------


class TestIsolationGuarantee:
    @pytest.mark.unit
    def test_shadow_predict_does_not_modify_row(self, tmp_path):
        """predict_shadow must not mutate the input row."""
        features = ["f1", "f2", "f3"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        row = _make_row(features)
        original_values = row.copy()
        shadow.predict_shadow(row)
        pd.testing.assert_series_equal(row, original_values)

    @pytest.mark.unit
    def test_shadow_predict_returns_independent_values(self, tmp_path):
        """Multiple predict_shadow calls return independent floats."""
        features = ["f1", "f2"]
        artifact = _make_artifact(features)
        path = tmp_path / "shadow_model.joblib"
        _write_artifact(artifact, path)

        logger = _make_logger()
        shadow = ShadowForecaster(logger=logger, snapshot_id="SNAP-TEST",
                                  shadow_model_path=path)
        row1 = _make_row(features, seed=1)
        row2 = _make_row(features, seed=2)
        p1 = shadow.predict_shadow(row1)
        p2 = shadow.predict_shadow(row2)
        # Both valid floats; different inputs may produce different outputs
        assert isinstance(p1, float) and isinstance(p2, float)

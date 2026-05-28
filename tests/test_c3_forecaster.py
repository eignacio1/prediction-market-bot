"""
Tests for C3 ModelForecaster.

Covers: _model_version_hash, _compute_ci, ModelForecaster.fit(), ModelForecaster.predict().
All tests use real file-backed AuditLogger (tmp_path) to avoid mocking C6 internals.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from prediction_market_bot.c3_forecasting.forecaster import (
    ModelForecaster,
    _compute_ci,
    _model_version_hash,
    DIR_NO,
    DIR_PASS,
    DIR_YES,
    EDGE_THRESHOLD_NO,
    EDGE_THRESHOLD_YES,
    MIN_FIT_SAMPLES,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_FEATURE_NAMES = ["f1", "f2", "f3"]


def _make_logger(tmp_path) -> AuditLogger:
    return AuditLogger(log_path=tmp_path / "audit.jsonl", min_severity="DEBUG")


def _make_forecaster(logger: AuditLogger, feature_names=None) -> ModelForecaster:
    if feature_names is None:
        feature_names = _FEATURE_NAMES
    return ModelForecaster(
        logger=logger,
        snapshot_id="SNAP-2026-01-01-001",
        feature_names=feature_names,
    )


def _make_feature_df(n: int, label: str = "TRAIN", feature_names=None, rng=None) -> pd.DataFrame:
    if feature_names is None:
        feature_names = _FEATURE_NAMES
    if rng is None:
        rng = np.random.default_rng(42)
    data = {f: rng.standard_normal(n) for f in feature_names}
    data["train_test_label"] = [label] * n
    data["player_id"] = [f"P{i}" for i in range(n)]
    data["game_date"] = ["2024-01-01"] * n
    data["season"] = ["2023-24"] * n
    data["season_type"] = ["Regular Season"] * n
    return pd.DataFrame(data)


def _make_target(n: int) -> pd.Series:
    """Balanced binary target — first half 1, second half 0."""
    y = np.zeros(n, dtype=int)
    y[: n // 2] = 1
    return pd.Series(y)


def _fit_forecaster(forecaster: ModelForecaster, n: int = 60) -> bool:
    """Fit forecaster with a balanced synthetic dataset. Returns fit() bool."""
    df = _make_feature_df(n, label="TRAIN")
    target = _make_target(n)
    return forecaster.fit(df, target)


# ---------------------------------------------------------------------------
# _model_version_hash
# ---------------------------------------------------------------------------


class TestModelVersionHash:
    def test_is_deterministic(self):
        h1 = _model_version_hash(["f1", "f2", "f3"], "MyModel")
        h2 = _model_version_hash(["f1", "f2", "f3"], "MyModel")
        assert h1 == h2

    def test_order_independent(self):
        h1 = _model_version_hash(["f1", "f2", "f3"], "MyModel")
        h2 = _model_version_hash(["f3", "f1", "f2"], "MyModel")
        assert h1 == h2

    def test_changes_on_feature_set_change(self):
        h1 = _model_version_hash(["f1", "f2", "f3"], "MyModel")
        h2 = _model_version_hash(["f1", "f2", "f4"], "MyModel")
        assert h1 != h2

    def test_changes_on_model_class_change(self):
        h1 = _model_version_hash(["f1", "f2", "f3"], "ModelA")
        h2 = _model_version_hash(["f1", "f2", "f3"], "ModelB")
        assert h1 != h2

    def test_prefix_v1(self):
        h = _model_version_hash(["f1"], "M")
        assert h.startswith("v1-")

    def test_length(self):
        h = _model_version_hash(["f1"], "M")
        assert len(h) == len("v1-") + 8


# ---------------------------------------------------------------------------
# _compute_ci
# ---------------------------------------------------------------------------


class TestComputeCI:
    def test_returns_lower_upper_keys(self):
        ci = _compute_ci(0.5, 100)
        assert "lower" in ci and "upper" in ci

    def test_lower_less_than_upper(self):
        ci = _compute_ci(0.5, 100)
        assert ci["lower"] < ci["upper"]

    def test_bounds_within_zero_one(self):
        for p in [0.1, 0.5, 0.9]:
            ci = _compute_ci(p, 50)
            assert 0.0 <= ci["lower"] <= 1.0
            assert 0.0 <= ci["upper"] <= 1.0

    def test_wider_ci_for_small_n(self):
        ci_small = _compute_ci(0.5, 10)
        ci_large = _compute_ci(0.5, 1000)
        assert (ci_small["upper"] - ci_small["lower"]) > (ci_large["upper"] - ci_large["lower"])

    def test_p_near_zero_does_not_crash(self):
        ci = _compute_ci(0.0, 50)
        assert 0.0 <= ci["lower"] <= ci["upper"] <= 1.0

    def test_p_near_one_does_not_crash(self):
        ci = _compute_ci(1.0, 50)
        assert 0.0 <= ci["lower"] <= ci["upper"] <= 1.0

    def test_n_one_does_not_crash(self):
        ci = _compute_ci(0.5, 1)
        assert isinstance(ci["lower"], float)
        assert isinstance(ci["upper"], float)


# ---------------------------------------------------------------------------
# ModelForecaster.fit()
# ---------------------------------------------------------------------------


class TestModelForecasterFit:
    def test_insufficient_samples_returns_false(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        df = _make_feature_df(MIN_FIT_SAMPLES - 1, label="TRAIN")
        target = _make_target(MIN_FIT_SAMPLES - 1)
        assert forecaster.fit(df, target) is False

    def test_insufficient_samples_leaves_unfitted(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        df = _make_feature_df(MIN_FIT_SAMPLES - 1, label="TRAIN")
        target = _make_target(MIN_FIT_SAMPLES - 1)
        forecaster.fit(df, target)
        assert not forecaster.is_fitted

    def test_ti02_violation_non_train_rows_returns_false(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        df = _make_feature_df(60, label="TRAIN")
        df.loc[0, "train_test_label"] = "TEST"
        target = _make_target(60)
        assert forecaster.fit(df, target) is False

    def test_ti02_violation_leaves_unfitted(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        df = _make_feature_df(60, label="TRAIN")
        df.loc[0, "train_test_label"] = "TEST"
        target = _make_target(60)
        forecaster.fit(df, target)
        assert not forecaster.is_fitted

    def test_happy_path_returns_true(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        assert _fit_forecaster(forecaster) is True

    def test_happy_path_sets_is_fitted(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        assert forecaster.is_fitted is True

    def test_happy_path_sets_model_version(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        assert forecaster.model_version is not None
        assert forecaster.model_version.startswith("v1-")

    def test_model_version_matches_hash(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        from prediction_market_bot.c3_forecasting.forecaster import MODEL_CLASS
        expected = _model_version_hash(_FEATURE_NAMES, MODEL_CLASS)
        assert forecaster.model_version == expected

    def test_c6_write_failure_on_fit_start_returns_false(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        df = _make_feature_df(60, label="TRAIN")
        target = _make_target(60)
        with patch(
            "prediction_market_bot.c6_audit_logger.audit_logger.jsonlines.open",
            side_effect=IOError("disk full"),
        ):
            result = forecaster.fit(df, target)
        assert result is False


# ---------------------------------------------------------------------------
# ModelForecaster.predict()
# ---------------------------------------------------------------------------


class TestModelForecasterPredict:
    def test_not_fitted_returns_false_empty_df(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        ok, df = forecaster.predict(
            feature_df=_make_feature_df(5, label="TEST"),
            market_implied_prob=0.5,
        )
        assert ok is False
        assert len(df) == 0

    def test_happy_path_returns_true_and_nonempty_df(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        ok, df = forecaster.predict(
            feature_df=_make_feature_df(10, label="TEST"),
            market_implied_prob=0.5,
        )
        assert ok is True
        assert len(df) == 10

    def test_output_schema_required_columns(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(5, label="TEST"),
            market_implied_prob=0.5,
        )
        for col in [
            "forecast_id", "model_version", "snapshot_id",
            "p_estimate", "ci_lower", "ci_upper",
            "market_implied_prob", "edge", "recommended_direction",
            "forecast_timestamp",
        ]:
            assert col in df.columns, f"Missing column: {col}"

    def test_edge_equals_p_estimate_minus_mip(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        mip = 0.50
        _, df = forecaster.predict(
            feature_df=_make_feature_df(5, label="TEST"),
            market_implied_prob=mip,
        )
        np.testing.assert_allclose(
            df["edge"].to_numpy(),
            df["p_estimate"].to_numpy() - mip,
            atol=1e-6,
        )

    def test_direction_yes_when_high_edge(self, tmp_path):
        """market_implied_prob=0 → edge ≈ p_estimate ≥ 0.02 → all YES."""
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(20, label="TEST"),
            market_implied_prob=0.0,
        )
        assert (df["recommended_direction"] == DIR_YES).all(), (
            f"Expected all YES; got {df['recommended_direction'].value_counts().to_dict()}"
        )

    def test_direction_no_when_negative_edge(self, tmp_path):
        """market_implied_prob=1.0 → edge ≈ p_estimate - 1.0 ≤ -0.02 → all NO."""
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(20, label="TEST"),
            market_implied_prob=1.0,
        )
        assert (df["recommended_direction"] == DIR_NO).all(), (
            f"Expected all NO; got {df['recommended_direction'].value_counts().to_dict()}"
        )

    def test_direction_pass_when_small_edge(self, tmp_path):
        """market_implied_prob close to p_estimate → abs(edge) < threshold → PASS."""
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster, n=60)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(20, label="TEST"),
            market_implied_prob=0.5,
        )
        # With random features and balanced classes, p_estimates cluster near 0.5.
        # Edges should be small enough for at least some PASS directions.
        # Verify the threshold boundaries are applied correctly.
        for _, row in df.iterrows():
            edge = row["edge"]
            direction = row["recommended_direction"]
            if edge >= EDGE_THRESHOLD_YES:
                assert direction == DIR_YES
            elif edge <= EDGE_THRESHOLD_NO:
                assert direction == DIR_NO
            else:
                assert direction == DIR_PASS

    def test_ci_lower_less_than_upper(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(10, label="TEST"),
            market_implied_prob=0.5,
        )
        assert (df["ci_lower"] < df["ci_upper"]).all()

    def test_ci_bounds_within_zero_one(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(10, label="TEST"),
            market_implied_prob=0.5,
        )
        assert (df["ci_lower"] >= 0.0).all()
        assert (df["ci_upper"] <= 1.0).all()

    def test_market_implied_series_accepted(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        feature_df = _make_feature_df(5, label="TEST")
        mip_series = pd.Series([0.45, 0.50, 0.55, 0.60, 0.65])
        ok, df = forecaster.predict(
            feature_df=feature_df,
            market_implied_prob=mip_series,
        )
        assert ok is True
        assert len(df) == 5
        np.testing.assert_allclose(
            df["market_implied_prob"].to_numpy(),
            mip_series.to_numpy(),
            atol=1e-6,
        )

    def test_forecast_id_consistent_within_batch(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(10, label="TEST"),
            market_implied_prob=0.5,
        )
        assert df["forecast_id"].nunique() == 1

    def test_snapshot_id_flows_to_output(self, tmp_path):
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        _, df = forecaster.predict(
            feature_df=_make_feature_df(5, label="TEST"),
            market_implied_prob=0.5,
        )
        assert (df["snapshot_id"] == "SNAP-2026-01-01-001").all()

    def test_c6_write_failure_returns_false(self, tmp_path):
        """Patch C6 after fit — predict continues but all_ok=False due to log failure."""
        logger = _make_logger(tmp_path)
        forecaster = _make_forecaster(logger)
        _fit_forecaster(forecaster)
        with patch(
            "prediction_market_bot.c6_audit_logger.audit_logger.jsonlines.open",
            side_effect=IOError("disk full"),
        ):
            ok, df = forecaster.predict(
                feature_df=_make_feature_df(5, label="TEST"),
                market_implied_prob=0.5,
            )
        assert ok is False

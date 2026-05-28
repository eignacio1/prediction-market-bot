"""
Tests for src/prediction_market_bot/backtester.py

Coverage areas:
  - BacktestWindowDef and BacktestResult dataclass construction
  - _build_target: target variable construction + edge cases
  - _compute_metrics: Brier, LogLoss, ECE, AUC-ROC + error handling
  - _compute_null_metrics: null model constant-probability baseline
  - Backtester.run_window: end-to-end with mocked C2/C3/C4/C6
  - Backtester.run_windows: multi-window sequential runner
  - Kill switch propagation on C6 write failure
  - Temporal integrity: train/val non-overlap enforced by label assignment
  - C4 gate: REJECTED(phase_gate_not_reached) expected in ENV-01
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Ensure src/ is on the path when running from project root
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.backtester import (
    Backtester,
    BacktestResult,
    BacktestWindowDef,
    FEATURE_WINDOW,
    MIN_TRAIN_SAMPLES,
    PLACEHOLDER_MARKET_IMPLIED_PROB,
    _build_target,
    _compute_metrics,
    _compute_null_metrics,
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _make_mock_logger(write_ok: bool = True) -> MagicMock:
    """Return a mock AuditLogger whose write methods return write_ok."""
    logger = MagicMock()
    logger.info.return_value = write_ok
    logger.warning.return_value = write_ok
    logger.error.return_value = write_ok
    logger.critical.return_value = write_ok
    return logger


def _make_feature_df(n_train: int = 80, n_val: int = 40, n_test: int = 30) -> pd.DataFrame:
    """
    Minimal feature DataFrame matching IF-C2-C3 schema.
    Includes pts (needed for target construction) and pts_l10_mean (rolling feature).
    """
    total = n_train + n_val + n_test
    rng = np.random.default_rng(42)

    dates = pd.date_range("2021-10-01", periods=total, freq="3D")
    pts = rng.integers(10, 40, size=total).astype(float)
    pts_prior_mean = rng.uniform(15.0, 30.0, size=total)

    labels = (
        ["TRAIN"] * n_train
        + ["VALIDATION"] * n_val
        + ["TEST"] * n_test
    )

    df = pd.DataFrame(
        {
            "player_id": 2544,
            "player_name": "LeBron James",
            "game_id": [f"G{i:04d}" for i in range(total)],
            "game_date": dates.strftime("%Y-%m-%d"),
            "season": "2021-22",
            "season_type": "Regular Season",
            "snapshot_id": "SNAP-2026-05-27-001",
            "feature_run_id": "C2-RUN-TEST",
            "feature_version": "1.0.0",
            "temporal_cutoff": pd.date_range("2021-09-28", periods=total, freq="3D").strftime("%Y-%m-%d"),
            "train_test_label": labels,
            "pts": pts,
            f"pts_l{FEATURE_WINDOW}_mean": pts_prior_mean,
            "reb_l10_mean": rng.uniform(4, 10, total),
            "ast_l10_mean": rng.uniform(3, 8, total),
        }
    )
    return df


def _make_forecast_df(n: int = 40) -> pd.DataFrame:
    """Minimal forecast DataFrame matching IF-C3-C4 schema."""
    rng = np.random.default_rng(7)
    return pd.DataFrame(
        {
            "forecast_id": [f"FCST-{i:04d}" for i in range(n)],
            "player_id": 2544,
            "game_id": [f"G{i:04d}" for i in range(n)],
            "p_estimate": rng.uniform(0.3, 0.7, n),
            "edge": rng.uniform(-0.1, 0.1, n),
            "recommended_direction": ["YES" if e > 0.02 else "PASS" for e in rng.uniform(-0.1, 0.1, n)],
            "market_implied_prob": 0.50,
        }
    )


def _make_window_def(exp_id: str = "EXP-002") -> BacktestWindowDef:
    return BacktestWindowDef(
        exp_id=exp_id,
        train_end_date="2022-01-31",
        val_end_date="2022-04-10",
        description="Test window",
        snapshot_id="SNAP-2026-05-27-001",
    )


# ---------------------------------------------------------------------------
# BacktestWindowDef and BacktestResult
# ---------------------------------------------------------------------------


class TestDataclasses:
    @pytest.mark.unit
    def test_window_def_fields(self):
        w = _make_window_def("EXP-002")
        assert w.exp_id == "EXP-002"
        assert w.train_end_date == "2022-01-31"
        assert w.val_end_date == "2022-04-10"
        assert w.snapshot_id == "SNAP-2026-05-27-001"

    @pytest.mark.unit
    def test_result_beats_null_true(self):
        w = _make_window_def()
        r = BacktestResult(
            exp_id="EXP-002",
            session_id="SID",
            snapshot_id="SNAP",
            model_version="v1-abcd1234",
            window_def=w,
            train_rows=80,
            val_rows=40,
            test_rows_held_out=30,
            validation_brier_model=0.20,
            validation_brier_null=0.25,
            validation_log_loss=0.58,
            validation_ece=0.03,
            validation_auc_roc=0.62,
            train_brier_model=0.18,
            train_brier_null=0.25,
            brier_improvement=0.05,
            beats_null=True,
            c4_gate_result="REJECTED",
            output_dir="/tmp",
            audit_log_path="/tmp/audit.jsonl",
        )
        assert r.beats_null is True
        assert r.brier_improvement == pytest.approx(0.05)

    @pytest.mark.unit
    def test_result_beats_null_false(self):
        w = _make_window_def()
        r = BacktestResult(
            exp_id="EXP-002",
            session_id="SID",
            snapshot_id="SNAP",
            model_version="v1-abcd1234",
            window_def=w,
            train_rows=80,
            val_rows=40,
            test_rows_held_out=30,
            validation_brier_model=0.27,
            validation_brier_null=0.25,
            validation_log_loss=0.70,
            validation_ece=0.08,
            validation_auc_roc=0.48,
            train_brier_model=None,
            train_brier_null=None,
            brier_improvement=-0.02,
            beats_null=False,
            c4_gate_result="REJECTED",
            output_dir="/tmp",
            audit_log_path="/tmp/audit.jsonl",
        )
        assert r.beats_null is False

    @pytest.mark.unit
    def test_result_errors_list_default_empty(self):
        w = _make_window_def()
        r = BacktestResult(
            exp_id="EXP-002",
            session_id="SID",
            snapshot_id="SNAP",
            model_version="v1",
            window_def=w,
            train_rows=80, val_rows=40, test_rows_held_out=30,
            validation_brier_model=None, validation_brier_null=None,
            validation_log_loss=None, validation_ece=None, validation_auc_roc=None,
            train_brier_model=None, train_brier_null=None,
            brier_improvement=None, beats_null=None,
            c4_gate_result="SKIPPED",
            output_dir="/tmp", audit_log_path="/tmp/a.jsonl",
        )
        assert r.errors == []


# ---------------------------------------------------------------------------
# _build_target
# ---------------------------------------------------------------------------


class TestBuildTarget:
    @pytest.mark.unit
    def test_over_line_is_1(self):
        df = pd.DataFrame({
            "pts": [25.0, 30.0, 15.0],
            f"pts_l{FEATURE_WINDOW}_mean": [20.0, 25.0, 20.0],
        })
        result = _build_target(df)
        assert list(result[:2]) == [1, 1]

    @pytest.mark.unit
    def test_under_line_is_0(self):
        df = pd.DataFrame({
            "pts": [10.0, 18.0],
            f"pts_l{FEATURE_WINDOW}_mean": [20.0, 25.0],
        })
        result = _build_target(df)
        assert list(result) == [0, 0]

    @pytest.mark.unit
    def test_exact_line_is_1(self):
        df = pd.DataFrame({
            "pts": [20.0],
            f"pts_l{FEATURE_WINDOW}_mean": [20.0],
        })
        result = _build_target(df)
        assert list(result) == [1]

    @pytest.mark.unit
    def test_nan_pts_gives_na(self):
        df = pd.DataFrame({
            "pts": [float("nan"), 20.0],
            f"pts_l{FEATURE_WINDOW}_mean": [20.0, 20.0],
        })
        result = _build_target(df)
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == 1

    @pytest.mark.unit
    def test_nan_prior_mean_gives_na(self):
        df = pd.DataFrame({
            "pts": [20.0, 25.0],
            f"pts_l{FEATURE_WINDOW}_mean": [float("nan"), 20.0],
        })
        result = _build_target(df)
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == 1

    @pytest.mark.unit
    def test_missing_pts_column_returns_nan_series(self):
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        result = _build_target(df)
        assert result.isna().all()
        assert len(result) == 3

    @pytest.mark.unit
    def test_missing_rolling_column_returns_nan_series(self):
        df = pd.DataFrame({"pts": [20.0, 25.0]})
        result = _build_target(df)
        assert result.isna().all()

    @pytest.mark.unit
    def test_empty_dataframe(self):
        df = pd.DataFrame({"pts": [], f"pts_l{FEATURE_WINDOW}_mean": []})
        result = _build_target(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# _compute_metrics
# ---------------------------------------------------------------------------


class TestComputeMetrics:
    @pytest.mark.unit
    def test_perfect_predictor_brier_near_zero(self):
        y_true = np.array([1, 1, 0, 0])
        y_prob = np.array([0.99, 0.99, 0.01, 0.01])
        m = _compute_metrics(y_true, y_prob, "TEST")
        assert m["brier_score"] < 0.01

    @pytest.mark.unit
    def test_null_model_brier_is_0_25(self):
        y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        y_prob = np.full(8, 0.50)
        m = _compute_metrics(y_true, y_prob, "TEST")
        assert m["brier_score"] == pytest.approx(0.25, abs=1e-6)

    @pytest.mark.unit
    def test_auc_roc_returned(self):
        rng = np.random.default_rng(1)
        y_true = rng.integers(0, 2, 100)
        y_prob = rng.uniform(0, 1, 100)
        m = _compute_metrics(y_true, y_prob, "TEST")
        assert m["auc_roc"] is not None
        assert 0.0 <= m["auc_roc"] <= 1.0

    @pytest.mark.unit
    def test_ece_returned_for_good_predictor(self):
        # Perfect predictor: ECE should be near 0
        y_true = np.array([1] * 50 + [0] * 50)
        y_prob = np.array([0.95] * 50 + [0.05] * 50)
        m = _compute_metrics(y_true, y_prob, "TEST")
        assert isinstance(m["ece"], float)
        assert m["ece"] >= 0.0

    @pytest.mark.unit
    def test_empty_array_returns_none_metrics(self):
        m = _compute_metrics(np.array([]), np.array([]), "TEST")
        assert m["brier_score"] is None
        assert m["log_loss"] is None
        assert m["ece"] is None
        assert m["auc_roc"] is None
        assert m["n_samples"] == 0

    @pytest.mark.unit
    def test_single_class_auc_returns_none(self):
        # Only class 1 — AUC-ROC undefined
        y_true = np.array([1, 1, 1, 1])
        y_prob = np.array([0.9, 0.8, 0.7, 0.85])
        m = _compute_metrics(y_true, y_prob, "TEST")
        assert m["auc_roc"] is None

    @pytest.mark.unit
    def test_set_name_preserved(self):
        y_true = np.array([1, 0])
        y_prob = np.array([0.7, 0.3])
        m = _compute_metrics(y_true, y_prob, "VALIDATION")
        assert m["set"] == "VALIDATION"

    @pytest.mark.unit
    def test_n_samples_correct(self):
        y_true = np.array([1, 0, 1])
        y_prob = np.array([0.7, 0.3, 0.6])
        m = _compute_metrics(y_true, y_prob, "TRAIN")
        assert m["n_samples"] == 3


# ---------------------------------------------------------------------------
# _compute_null_metrics
# ---------------------------------------------------------------------------


class TestComputeNullMetrics:
    @pytest.mark.unit
    def test_null_prob_is_0_50(self):
        y_true = np.array([1, 0, 1, 0])
        m = _compute_null_metrics(y_true, "VALIDATION")
        assert m["null_prob"] == PLACEHOLDER_MARKET_IMPLIED_PROB
        assert m["null_model"] is True

    @pytest.mark.unit
    def test_null_brier_matches_expected(self):
        # Null model constant p=0.5 → Brier = (1-0.5)^2 * n_pos/n + (0.5)^2 * n_neg/n
        # For balanced y: = 0.25 always
        y_true = np.array([1, 1, 0, 0])
        m = _compute_null_metrics(y_true, "VALIDATION")
        assert m["brier_score"] == pytest.approx(0.25, abs=1e-6)

    @pytest.mark.unit
    def test_null_set_name_has_suffix(self):
        y_true = np.array([1, 0])
        m = _compute_null_metrics(y_true, "VALIDATION")
        assert m["set"] == "VALIDATION_null"


# ---------------------------------------------------------------------------
# Backtester.run_window — mocked C2/C3/C4/C6
# ---------------------------------------------------------------------------


class TestBacktesterRunWindow:
    """
    Tests for Backtester.run_window using mocked C2/C3/C4/C6 components.
    Real data is replaced with minimal DataFrames; the test validates
    orchestration logic, kill switch propagation, and result fields.
    """

    def _make_backtester(self, write_ok: bool = True) -> tuple[Backtester, MagicMock]:
        logger = _make_mock_logger(write_ok)
        bt = Backtester(
            logger=logger,
            snapshot_id="SNAP-2026-05-27-001",
            window=FEATURE_WINDOW,
            market_implied_prob=PLACEHOLDER_MARKET_IMPLIED_PROB,
        )
        return bt, logger

    @pytest.mark.unit
    def test_run_window_success_returns_true_and_result(self, tmp_path):
        bt, logger = self._make_backtester()
        feature_df = _make_feature_df(n_train=80, n_val=40, n_test=30)
        feature_df["y_target"] = 1  # will be overridden in run_window
        forecast_df = _make_forecast_df(40)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
            patch("prediction_market_bot.backtester.ModelForecaster") as MockForecaster,
            patch("prediction_market_bot.backtester.RiskEngine") as MockEngine,
        ):
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (True, feature_df)
            store_instance.assign_train_test_labels.return_value = (True, feature_df)
            store_instance.get_feature_names.return_value = ["pts_l10_mean", "reb_l10_mean"]

            forecaster_instance = MockForecaster.return_value
            forecaster_instance.fit.return_value = True
            forecaster_instance.predict.return_value = (True, forecast_df)
            forecaster_instance.model_version = "v1-abc12345"

            engine_instance = MockEngine.return_value
            engine_instance.evaluate_forecast.return_value = (
                True,
                {"approval_status": "REJECTED", "rejection_reason": "phase_gate_not_reached"},
            )

            ok, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def("EXP-002"),
                output_dir=tmp_path,
                session_id="BACKTEST-EXP-002-TEST0001",
                dry_run=True,
            )

        assert ok is True
        assert result is not None
        assert result.exp_id == "EXP-002"
        assert result.model_version == "v1-abc12345"
        assert result.c4_gate_result == "REJECTED"

    @pytest.mark.unit
    def test_run_window_c6_write_failure_propagates(self, tmp_path):
        bt, logger = self._make_backtester(write_ok=False)

        ok, result = bt.run_window(
            raw_df=pd.DataFrame(),
            window_def=_make_window_def("EXP-002"),
            output_dir=tmp_path,
            session_id="BACKTEST-EXP-002-FAIL0001",
            dry_run=True,
        )

        assert ok is False
        assert result is None

    @pytest.mark.unit
    def test_run_window_c2_compute_failure_propagates(self, tmp_path):
        bt, logger = self._make_backtester()

        with patch("prediction_market_bot.backtester.FeatureStore") as MockStore:
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (False, pd.DataFrame())
            store_instance.get_feature_names.return_value = []

            ok, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def(),
                output_dir=tmp_path,
                session_id="SID",
                dry_run=True,
            )

        assert ok is False
        assert result is None

    @pytest.mark.unit
    def test_run_window_insufficient_train_returns_result_with_error(self, tmp_path):
        bt, logger = self._make_backtester()

        # feature_df with only 5 TRAIN rows — below MIN_TRAIN_SAMPLES=30
        small_df = _make_feature_df(n_train=5, n_val=10, n_test=5)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
        ):
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (True, small_df)
            store_instance.assign_train_test_labels.return_value = (True, small_df)
            store_instance.get_feature_names.return_value = ["pts_l10_mean"]

            ok, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def(),
                output_dir=tmp_path,
                session_id="SID",
                dry_run=True,
            )

        # bool is True (write succeeded) but result has errors
        assert result is not None
        assert len(result.errors) > 0
        assert "Insufficient" in result.errors[0]
        assert result.model_version == "FAILED_INSUFFICIENT_TRAIN"

    @pytest.mark.unit
    def test_run_window_c3_fit_failure_propagates(self, tmp_path):
        bt, logger = self._make_backtester()
        feature_df = _make_feature_df(n_train=80, n_val=40, n_test=30)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
            patch("prediction_market_bot.backtester.ModelForecaster") as MockForecaster,
        ):
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (True, feature_df)
            store_instance.assign_train_test_labels.return_value = (True, feature_df)
            store_instance.get_feature_names.return_value = ["pts_l10_mean"]

            forecaster_instance = MockForecaster.return_value
            forecaster_instance.fit.return_value = False  # C3 fit failure

            ok, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def(),
                output_dir=tmp_path,
                session_id="SID",
                dry_run=True,
            )

        assert ok is False
        assert result is None

    @pytest.mark.unit
    def test_run_window_c4_unexpected_gate_logs_error(self, tmp_path):
        bt, logger = self._make_backtester()
        feature_df = _make_feature_df(n_train=80, n_val=40, n_test=30)
        forecast_df = _make_forecast_df(40)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
            patch("prediction_market_bot.backtester.ModelForecaster") as MockForecaster,
            patch("prediction_market_bot.backtester.RiskEngine") as MockEngine,
        ):
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (True, feature_df)
            store_instance.assign_train_test_labels.return_value = (True, feature_df)
            store_instance.get_feature_names.return_value = ["pts_l10_mean"]

            forecaster_instance = MockForecaster.return_value
            forecaster_instance.fit.return_value = True
            forecaster_instance.predict.return_value = (True, forecast_df)
            forecaster_instance.model_version = "v1-test"

            engine_instance = MockEngine.return_value
            # Simulate C4 incorrectly returning APPROVED (should never happen in ENV-01)
            engine_instance.evaluate_forecast.return_value = (
                True,
                {"approval_status": "APPROVED", "rejection_reason": ""},
            )

            ok, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def(),
                output_dir=tmp_path,
                session_id="SID",
                dry_run=True,
            )

        # C6 error should have been logged for the unexpected gate state
        logger.error.assert_called()
        error_calls = [str(c) for c in logger.error.call_args_list]
        assert any("unexpected_gate_state" in c for c in error_calls)

    @pytest.mark.unit
    def test_run_window_result_has_correct_train_val_counts(self, tmp_path):
        bt, _ = self._make_backtester()
        feature_df = _make_feature_df(n_train=80, n_val=40, n_test=30)
        forecast_df = _make_forecast_df(40)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
            patch("prediction_market_bot.backtester.ModelForecaster") as MockForecaster,
            patch("prediction_market_bot.backtester.RiskEngine") as MockEngine,
        ):
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (True, feature_df)
            store_instance.assign_train_test_labels.return_value = (True, feature_df)
            store_instance.get_feature_names.return_value = ["pts_l10_mean"]

            forecaster_instance = MockForecaster.return_value
            forecaster_instance.fit.return_value = True
            forecaster_instance.predict.return_value = (True, forecast_df)
            forecaster_instance.model_version = "v1-test"

            engine_instance = MockEngine.return_value
            engine_instance.evaluate_forecast.return_value = (
                True,
                {"approval_status": "REJECTED", "rejection_reason": "phase_gate_not_reached"},
            )

            ok, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def(),
                output_dir=tmp_path,
                session_id="SID",
                dry_run=True,
            )

        assert ok is True
        assert result is not None
        # After target construction usable rows depend on non-NaN target + temporal_cutoff
        # All rows have both valid in _make_feature_df, so counts match splits
        assert result.train_rows == 80
        assert result.val_rows == 40
        assert result.test_rows_held_out == 30


# ---------------------------------------------------------------------------
# Backtester.run_windows — multi-window sequential runner
# ---------------------------------------------------------------------------


class TestBacktesterRunWindows:

    def _make_backtester_with_successful_window(self) -> tuple[Backtester, MagicMock]:
        logger = _make_mock_logger(write_ok=True)
        bt = Backtester(
            logger=logger,
            snapshot_id="SNAP-2026-05-27-001",
            window=FEATURE_WINDOW,
        )
        return bt, logger

    @pytest.mark.unit
    def test_run_windows_returns_all_results(self, tmp_path):
        bt, _ = self._make_backtester_with_successful_window()

        windows = [
            BacktestWindowDef("EXP-002", "2022-01-31", "2022-04-10", "W2", "SNAP-001"),
            BacktestWindowDef("EXP-003", "2021-12-15", "2022-01-31", "W3", "SNAP-001"),
        ]

        feature_df = _make_feature_df()
        forecast_df = _make_forecast_df(40)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
            patch("prediction_market_bot.backtester.ModelForecaster") as MockForecaster,
            patch("prediction_market_bot.backtester.RiskEngine") as MockEngine,
        ):
            store_instance = MockStore.return_value
            store_instance.compute_features_bulk.return_value = (True, feature_df)
            store_instance.assign_train_test_labels.return_value = (True, feature_df)
            store_instance.get_feature_names.return_value = ["pts_l10_mean"]

            forecaster_instance = MockForecaster.return_value
            forecaster_instance.fit.return_value = True
            forecaster_instance.predict.return_value = (True, forecast_df)
            forecaster_instance.model_version = "v1-test"

            engine_instance = MockEngine.return_value
            engine_instance.evaluate_forecast.return_value = (
                True,
                {"approval_status": "REJECTED", "rejection_reason": "phase_gate_not_reached"},
            )

            ok, results = bt.run_windows(
                raw_df=pd.DataFrame(),
                windows=windows,
                base_output_dir=tmp_path,
                dry_run=True,
            )

        assert ok is True
        assert len(results) == 2
        assert results[0].exp_id == "EXP-002"
        assert results[1].exp_id == "EXP-003"

    @pytest.mark.unit
    def test_run_windows_aborts_on_c6_failure(self, tmp_path):
        """If run_window returns (False, ...), run_windows propagates False and stops."""
        logger = _make_mock_logger()
        bt = Backtester(logger=logger, snapshot_id="SNAP-001")

        windows = [
            BacktestWindowDef("EXP-002", "2022-01-31", "2022-04-10", "W2", "SNAP-001"),
            BacktestWindowDef("EXP-003", "2021-12-15", "2022-01-31", "W3", "SNAP-001"),
        ]

        # First call succeeds, second call returns C6 write failure
        from prediction_market_bot.backtester import BacktestResult
        success_result = BacktestResult(
            exp_id="EXP-002", session_id="S1", snapshot_id="SNAP-001",
            model_version="v1", window_def=windows[0],
            train_rows=80, val_rows=40, test_rows_held_out=30,
            validation_brier_model=0.22, validation_brier_null=0.25,
            validation_log_loss=0.60, validation_ece=0.03,
            validation_auc_roc=0.61, train_brier_model=0.20,
            train_brier_null=0.25, brier_improvement=0.03, beats_null=True,
            c4_gate_result="REJECTED", output_dir="/tmp",
            audit_log_path="/tmp/a.jsonl",
        )
        call_results = [(True, success_result), (False, None)]
        call_idx = [0]

        def fake_run_window(raw_df, window_def, output_dir, session_id, dry_run):
            result = call_results[call_idx[0]]
            call_idx[0] += 1
            return result

        with patch.object(bt, "run_window", side_effect=fake_run_window):
            ok, results = bt.run_windows(
                raw_df=pd.DataFrame(),
                windows=windows,
                base_output_dir=tmp_path,
                dry_run=True,
            )

        assert ok is False
        # First window result is included; second window returned None (not appended)
        assert len(results) == 1
        assert results[0].exp_id == "EXP-002"

    @pytest.mark.unit
    def test_run_windows_empty_list_succeeds(self, tmp_path):
        bt, _ = self._make_backtester_with_successful_window()
        ok, results = bt.run_windows(
            raw_df=pd.DataFrame(),
            windows=[],
            base_output_dir=tmp_path,
            dry_run=True,
        )
        assert ok is True
        assert results == []


# ---------------------------------------------------------------------------
# Temporal integrity
# ---------------------------------------------------------------------------


class TestTemporalIntegrity:
    @pytest.mark.temporal
    def test_build_target_uses_prior_game_mean_not_current(self):
        """
        Verify the binary target uses pts_l10_mean (computed from PRIOR games
        via shift(1) in C2) not the current game's pts in the mean.
        This is a white-box check of the formula in _build_target.
        """
        # Game where current pts (35) > prior mean (20) → y=1
        df = pd.DataFrame({
            "pts": [35.0],
            f"pts_l{FEATURE_WINDOW}_mean": [20.0],  # from prior games only
        })
        result = _build_target(df)
        assert result.iloc[0] == 1

        # Game where current pts (10) < prior mean (20) → y=0
        df2 = pd.DataFrame({
            "pts": [10.0],
            f"pts_l{FEATURE_WINDOW}_mean": [20.0],
        })
        result2 = _build_target(df2)
        assert result2.iloc[0] == 0

    @pytest.mark.temporal
    def test_test_rows_are_excluded_from_metrics(self, tmp_path):
        """
        TEST-labeled rows must never appear in validation metrics.
        After assign_train_test_labels, Backtester filters to TRAIN/VALIDATION only.
        Verify that result.test_rows_held_out > 0 and val_rows does not include TEST rows.
        """
        logger = _make_mock_logger()
        bt = Backtester(logger=logger, snapshot_id="SNAP-001")

        feature_df = _make_feature_df(n_train=80, n_val=40, n_test=30)
        forecast_df = _make_forecast_df(40)

        with (
            patch("prediction_market_bot.backtester.FeatureStore") as MockStore,
            patch("prediction_market_bot.backtester.ModelForecaster") as MockForecaster,
            patch("prediction_market_bot.backtester.RiskEngine") as MockEngine,
        ):
            MockStore.return_value.compute_features_bulk.return_value = (True, feature_df)
            MockStore.return_value.assign_train_test_labels.return_value = (True, feature_df)
            MockStore.return_value.get_feature_names.return_value = ["pts_l10_mean"]

            MockForecaster.return_value.fit.return_value = True
            MockForecaster.return_value.predict.return_value = (True, forecast_df)
            MockForecaster.return_value.model_version = "v1-test"

            MockEngine.return_value.evaluate_forecast.return_value = (
                True,
                {"approval_status": "REJECTED", "rejection_reason": "phase_gate_not_reached"},
            )

            _, result = bt.run_window(
                raw_df=pd.DataFrame(),
                window_def=_make_window_def(),
                output_dir=tmp_path,
                session_id="SID",
                dry_run=True,
            )

        assert result is not None
        assert result.test_rows_held_out == 30
        assert result.val_rows == 40  # TEST rows not mixed into validation
        assert result.train_rows == 80

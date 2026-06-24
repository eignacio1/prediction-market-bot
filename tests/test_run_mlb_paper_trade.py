"""
Tests for run_mlb_paper_trade.py (T-187D).

Scope:
  - _ticker_to_game_date: KXMLBHIT date parsing
  - _build_mlb_feature_vector: threshold injection, imputation, column ordering
  - _is_mlb_game_in_progress: mocked HTTP; returns False on failure
  - BOT_ENV guard (sys.exit if not paper)
  - BOT_C4_ACTIVE is set after BOT_ENV check
  - main() smoke-test via mocked VenueRouter + feature CSV + model artifact

Excluded (require real API/network):
  - Live Kalshi market fetch
  - Live MLB Stats API calls
  - Real model inference (tested in test_train_mlb_model.py / T-183)
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT  = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


# ---------------------------------------------------------------------------
# Module import helper (run_mlb_paper_trade is guarded by BOT_ENV check)
# ---------------------------------------------------------------------------


def _import_runner(monkeypatch: pytest.MonkeyPatch):
    """Import run_mlb_paper_trade with BOT_ENV=paper set, clearing any stale cache."""
    monkeypatch.setenv("BOT_ENV", "paper")
    # Remove cached module so the BOT_ENV check re-fires on each import
    sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
    import prediction_market_bot.run_mlb_paper_trade as runner
    return runner


# ---------------------------------------------------------------------------
# BOT_ENV guard
# ---------------------------------------------------------------------------


class TestBotEnvGuard:
    def test_exits_if_bot_env_not_paper(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BOT_ENV", "live")
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        with pytest.raises(SystemExit) as exc_info:
            import prediction_market_bot.run_mlb_paper_trade  # noqa: F401
        assert exc_info.value.code == 1

    def test_exits_if_bot_env_missing(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("BOT_ENV", raising=False)
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        with pytest.raises(SystemExit) as exc_info:
            import prediction_market_bot.run_mlb_paper_trade  # noqa: F401
        assert exc_info.value.code == 1

    def test_c4_active_is_set_after_env_check(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BOT_ENV", "paper")
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        import prediction_market_bot.run_mlb_paper_trade  # noqa: F401
        assert os.environ.get("BOT_C4_ACTIVE") == "true"


# ---------------------------------------------------------------------------
# _ticker_to_game_date
# ---------------------------------------------------------------------------


class TestTickerToGameDate:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._ticker_to_game_date

    def test_standard_format(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # KXMLBHIT-26JUN241607BALLAA-LAAJADELL7-4
        result = fn("KXMLBHIT-26JUN241607BALLAA-LAAJADELL7-4")
        assert result == "2024-06-26"

    def test_different_month(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # 15APR25 = 2025-04-15
        result = fn("KXMLBHIT-15APR251900NYYBOS-NYYAAJUDG7-2")
        assert result == "2025-04-15"

    def test_invalid_ticker_returns_today(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        result = fn("KXMLBHIT-INVALID-TICKER")
        # Should return today's date (GAME_DATE_ISO)
        from datetime import datetime, timezone
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        assert result == today

    def test_january(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        result = fn("KXMLBHIT-01JAN261200NYYBOS-NYYAAJUDG7-1")
        assert result == "2026-01-01"


# ---------------------------------------------------------------------------
# _is_mlb_game_in_progress
# ---------------------------------------------------------------------------


class TestIsMLBGameInProgress:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._is_mlb_game_in_progress

    def _make_schedule_resp(self, states: list[str]) -> MagicMock:
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        games = [{"status": {"abstractGameState": s}} for s in states]
        resp.json.return_value = {"dates": [{"games": games}]}
        return resp

    def test_live_game_returns_true(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        with patch("prediction_market_bot.run_mlb_paper_trade.requests") as mock_req:
            mock_req.get.return_value = self._make_schedule_resp(["Final", "Live", "Preview"])
            result = fn("2026-06-24")
        assert result is True

    def test_no_live_games_returns_false(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        with patch("prediction_market_bot.run_mlb_paper_trade.requests") as mock_req:
            mock_req.get.return_value = self._make_schedule_resp(["Final", "Final", "Preview"])
            result = fn("2026-06-24")
        assert result is False

    def test_empty_schedule_returns_false(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        with patch("prediction_market_bot.run_mlb_paper_trade.requests") as mock_req:
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            resp.json.return_value = {"dates": []}
            mock_req.get.return_value = resp
            result = fn("2026-06-24")
        assert result is False

    def test_api_error_returns_false(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        with patch("prediction_market_bot.run_mlb_paper_trade.requests") as mock_req:
            mock_req.get.side_effect = Exception("connection refused")
            result = fn("2026-06-24")
        assert result is False


# ---------------------------------------------------------------------------
# _build_mlb_feature_vector
# ---------------------------------------------------------------------------


class TestBuildMLBFeatureVector:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._build_mlb_feature_vector

    def _make_row(self) -> pd.Series:
        return pd.Series({
            "player_id": 660670,
            "ba_l10": 0.280,
            "slg_l10": 0.450,
            "obp_l10": 0.380,
            "ops_l10": 0.830,
            "h_l10_mean": 1.0,
            "k_rate_l10": 0.22,
            "bb_rate_l10": 0.15,
            "hr_rate_l10": 0.03,
            "days_rest": 1,
            "b2b_flag": 0,
            "is_home_game": 1,
            "opp_sp_era_l5": 4.0,
            "opp_sp_k9_l5": 8.0,
            "opp_sp_bb9_l5": 3.0,
            "opp_sp_is_known": 1,
            "opp_runs_allowed_l10": 4.5,
            "park_factor_hits": 1.0,
        })

    def test_threshold_injected_in_vector(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["ba_l10", "days_rest", "threshold"]  # simplified
        medians = np.array([0.250, 1, 1.5])

        X = fn(row, threshold=2.0, feature_names=feature_names, col_medians=medians)
        assert X.shape == (1, 3)
        assert X[0, 2] == pytest.approx(2.0)  # threshold at index 2

    def test_threshold_1_vs_3_differ(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["ba_l10", "threshold"]
        medians = np.array([0.250, 1.5])

        X1 = fn(row, threshold=1.0, feature_names=feature_names, col_medians=medians)
        X3 = fn(row, threshold=3.0, feature_names=feature_names, col_medians=medians)
        # Only threshold column should differ
        assert X1[0, 0] == pytest.approx(X3[0, 0])  # ba_l10 same
        assert X1[0, 1] == pytest.approx(1.0)
        assert X3[0, 1] == pytest.approx(3.0)

    def test_nan_imputed_with_median(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = pd.Series({"known_col": np.nan, "threshold": None})
        feature_names = ["known_col", "threshold"]
        medians = np.array([0.300, 1.5])

        X = fn(row, threshold=1.0, feature_names=feature_names, col_medians=medians)
        # known_col was NaN → imputed with median 0.300
        assert X[0, 0] == pytest.approx(0.300)
        # threshold is explicitly injected → 1.0 (not NaN → not imputed from median)
        assert X[0, 1] == pytest.approx(1.0)

    def test_missing_column_treated_as_nan(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = pd.Series({"ba_l10": 0.280})  # missing "ops_l10"
        feature_names = ["ba_l10", "ops_l10", "threshold"]
        medians = np.array([0.250, 0.750, 1.5])

        X = fn(row, threshold=2.0, feature_names=feature_names, col_medians=medians)
        assert X.shape == (1, 3)
        assert X[0, 0] == pytest.approx(0.280)
        assert X[0, 1] == pytest.approx(0.750)  # imputed from median
        assert X[0, 2] == pytest.approx(2.0)

    def test_output_shape(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        n_features = 19
        feature_names = [f"f{i}" for i in range(n_features - 1)] + ["threshold"]
        medians = np.zeros(n_features)

        X = fn(row, threshold=1.0, feature_names=feature_names, col_medians=medians)
        assert X.shape == (1, n_features)


# ---------------------------------------------------------------------------
# _NON_FEATURE_MLB mirrors train_mlb_model.py
# ---------------------------------------------------------------------------


class TestNonFeatureMLBConsistency:
    """Validate that _NON_FEATURE_MLB in runner matches train_mlb_model.py."""

    def test_threshold_not_in_non_features(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert "threshold" not in runner._NON_FEATURE_MLB

    def test_player_id_in_non_features(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert "player_id" in runner._NON_FEATURE_MLB

    def test_y_target_in_non_features(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert "y_target" in runner._NON_FEATURE_MLB

    def test_h_in_non_features(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        # h (actual hits) is a target/label column — not a model feature
        assert "h" in runner._NON_FEATURE_MLB


# ---------------------------------------------------------------------------
# main() smoke test — model wrong sport guard
# ---------------------------------------------------------------------------


class TestMainWrongSportGuard:
    """main() must exit if the model artifact has sport != mlb."""

    def test_exits_on_wrong_sport_in_artifact(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BOT_ENV", "paper")
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        import prediction_market_bot.run_mlb_paper_trade as runner

        fake_artifact = {
            "pipeline": MagicMock(),
            "feature_names": ["ba_l10", "threshold"],
            "col_medians": np.array([0.25, 1.5]),
            "model_version": "mlb_v1_wrong",
            "thresholds": [1, 2, 3],
            "sport": "nba",          # wrong sport
        }
        model_path = tmp_path / "mlb_v1_model.joblib"
        csv_path = tmp_path / "mlb_feature_matrix.csv"

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", csv_path),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "PORTFOLIO_PATH", tmp_path / "portfolio.json"),
            patch("prediction_market_bot.run_mlb_paper_trade.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_paper_trade.KalshiMarketClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.PaperTrader") as MockTrader,
            patch("prediction_market_bot.run_mlb_paper_trade.BAND_REGISTRY") as mock_reg,
        ):
            mock_jl.load.return_value = fake_artifact
            model_path.write_bytes(b"fake")
            mock_reg.validate.return_value = []
            MockTrader.return_value.get_state.return_value = {
                "bankroll_usd": 1000.0,
                "initial_bankroll_usd": 1000.0,
                "total_realized_pnl": 0.0,
                "current_daily_loss": 0.0,
                "daily_loss_date": "2026-01-01",
                "open_positions": [],
            }

            with pytest.raises(SystemExit) as exc_info:
                runner.main()
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# main() smoke test — no markets available
# ---------------------------------------------------------------------------


class TestMainNoMarkets:
    """main() must exit cleanly with code 0 when no KXMLBHIT markets are available."""

    def _make_artifact(self) -> dict:
        return {
            "pipeline": MagicMock(),
            "feature_names": ["ba_l10", "threshold"],
            "col_medians": np.array([0.25, 1.5]),
            "model_version": "mlb_v1_test",
            "thresholds": [1, 2, 3],
            "sport": "mlb",
        }

    def _make_state(self) -> dict:
        return {
            "bankroll_usd": 1000.0,
            "initial_bankroll_usd": 1000.0,
            "total_realized_pnl": 0.0,
            "current_daily_loss": 0.0,
            "daily_loss_date": "2026-01-01",
            "open_positions": [],
            "closed_positions": [],
        }

    def test_exits_0_when_no_markets(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BOT_ENV", "paper")
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        import prediction_market_bot.run_mlb_paper_trade as runner

        feature_csv = tmp_path / "mlb_feature_matrix.csv"
        feature_csv.write_text("player_id,player_name,game_date,ba_l10,threshold\n"
                                "660670,Juan Soto,2024-04-01,0.280,1\n")
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")

        mock_snap = MagicMock()
        mock_snap.markets = []

        mock_router = MagicMock()
        mock_router.check_all_connectivity.return_value = {"kalshi": (True, {})}
        mock_router.fetch_all_markets.return_value = (True, mock_snap)
        mock_router.active_venues = ["kalshi"]

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "PORTFOLIO_PATH", tmp_path / "portfolio.json"),
            patch.object(runner, "REPORT_PATH", tmp_path / "report.json"),
            patch("prediction_market_bot.run_mlb_paper_trade.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_paper_trade.KalshiMarketClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.PaperTrader") as MockTrader,
            patch("prediction_market_bot.run_mlb_paper_trade.VenueRouter") as MockRouter,
            patch("prediction_market_bot.run_mlb_paper_trade.BAND_REGISTRY") as mock_reg,
        ):
            mock_jl.load.return_value = self._make_artifact()
            state = self._make_state()
            mock_trader_instance = MagicMock()
            mock_trader_instance.get_state.return_value = state
            mock_trader_instance.summary.return_value = {
                **state,
                "open_positions": 0,
                "closed_positions": 0,
                "win_rate": None,
                "realized_drawdown_pct": 0.0,
                "deployed_pct": 0.0,
            }
            MockTrader.return_value = mock_trader_instance
            MockRouter.from_env.return_value = mock_router
            mock_reg.validate.return_value = []

            with pytest.raises(SystemExit) as exc_info:
                runner.main()
        assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Model thresholds constant
# ---------------------------------------------------------------------------


class TestModelThresholds:
    def test_model_thresholds_match_training(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert runner._MODEL_THRESHOLDS == frozenset({1, 2, 3})

    def test_threshold_4_not_in_model(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert 4 not in runner._MODEL_THRESHOLDS

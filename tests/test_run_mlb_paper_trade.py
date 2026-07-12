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
        # CREATE_DD=26, MON=JUN, GAME_DD=27 → June 27 game
        from datetime import datetime, timezone
        year = datetime.now(tz=timezone.utc).year
        result = fn("KXMLBHIT-26JUN271310NYYBOS-BOSWABREU52-2")
        assert result == f"{year}-06-27"

    def test_multi_day_early_creation(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # Kalshi created June 26 for a June 29 game (3 days early): GAME_DD=29
        from datetime import datetime, timezone
        year = datetime.now(tz=timezone.utc).year
        result = fn("KXMLBHIT-26JUN291840PITPHI-PITTCALLIHAN37-3")
        assert result == f"{year}-06-29"

    def test_different_month(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # CREATE_DD=15, MON=APR, GAME_DD=16 → April 16 game
        from datetime import datetime, timezone
        year = datetime.now(tz=timezone.utc).year
        result = fn("KXMLBHIT-15APR161900NYYBOS-NYYAAJUDG7-2")
        assert result == f"{year}-04-16"

    def test_invalid_ticker_returns_game_date_iso(self, monkeypatch):
        mod = _import_runner(monkeypatch)
        fn = mod._ticker_to_game_date
        result = fn("KXMLBHIT-INVALID-TICKER")
        # Fallback is GAME_DATE_ISO. An unparseable ticker resolves to the target date.
        assert result == mod.GAME_DATE_ISO

    def test_january(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # CREATE_DD=01, MON=JAN, GAME_DD=02 → January 2 game
        from datetime import datetime, timezone
        year = datetime.now(tz=timezone.utc).year
        result = fn("KXMLBHIT-01JAN021200NYYBOS-NYYAAJUDG7-1")
        assert result == f"{year}-01-02"

    def test_month_boundary_created_in_prior_month(self, monkeypatch):
        """GG-055: market created 30-Jun for a 1-Jul game.

        This is the exact class of bug that has bitten this function twice:
        T-205 assumed a fixed CREATE_DD→GAME_DD offset (broke on non-1-day
        creation lead times); T-206a switched to extracting GAME_DD/MON
        directly from the ticker instead of doing offset arithmetic — but no
        test previously exercised a ticker where CREATE_DD's implied month
        (Jun) differs from MON (Jul), which is exactly where an offset-based
        approach would silently produce the wrong month while a direct
        extraction approach (the current implementation) is unaffected.
        CREATE_DD=30 (June, implied — not itself parsed), MON=JUL, GAME_DD=01.
        """
        fn = self._get_fn(monkeypatch)
        from datetime import datetime, timezone
        year = datetime.now(tz=timezone.utc).year
        result = fn("KXMLBHIT-30JUL011200NYYBOS-NYYAAJUDG7-1")
        assert result == f"{year}-07-01"

    def test_month_boundary_short_month_to_long_month(self, monkeypatch):
        """GG-055: market created 31-Jul (month-end) for a 1-Aug game."""
        fn = self._get_fn(monkeypatch)
        from datetime import datetime, timezone
        year = datetime.now(tz=timezone.utc).year
        result = fn("KXMLBHIT-31AUG011200NYYBOS-NYYAAJUDG7-1")
        assert result == f"{year}-08-01"


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

    def test_known_column_value_preserved(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["ba_l10", "days_rest"]
        medians = np.array([0.250, 1.0])

        X = fn(row, feature_names=feature_names, col_medians=medians)
        assert X.shape == (1, 2)
        assert X[0, 0] == pytest.approx(0.280)  # ba_l10 from row

    def test_nan_imputed_with_median(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = pd.Series({"known_col": np.nan})
        feature_names = ["known_col"]
        medians = np.array([0.300])

        X = fn(row, feature_names=feature_names, col_medians=medians)
        assert X[0, 0] == pytest.approx(0.300)

    def test_missing_column_treated_as_nan(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = pd.Series({"ba_l10": 0.280})  # missing "ops_l10"
        feature_names = ["ba_l10", "ops_l10"]
        medians = np.array([0.250, 0.750])

        X = fn(row, feature_names=feature_names, col_medians=medians)
        assert X.shape == (1, 2)
        assert X[0, 0] == pytest.approx(0.280)
        assert X[0, 1] == pytest.approx(0.750)  # imputed from median

    def test_output_shape(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        n_features = 18
        feature_names = [f"f{i}" for i in range(n_features)]
        medians = np.zeros(n_features)

        X = fn(row, feature_names=feature_names, col_medians=medians)
        assert X.shape == (1, n_features)


# ---------------------------------------------------------------------------
# _NON_FEATURE_MLB mirrors train_mlb_model.py
# ---------------------------------------------------------------------------


class TestNonFeatureMLBConsistency:
    """Validate that _NON_FEATURE_MLB in runner matches train_mlb_model.py."""

    def test_threshold_in_non_features(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert "threshold" in runner._NON_FEATURE_MLB

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
            "pipelines": {1: MagicMock(), 2: MagicMock()},
            "feature_names": ["ba_l10", "days_rest"],
            "col_medians": np.array([0.25, 1.0]),
            "model_version": "mlb_v1_wrong",
            "thresholds": [1, 2],
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
            "pipelines": {1: MagicMock(), 2: MagicMock()},
            "feature_names": ["ba_l10", "days_rest"],
            "col_medians": np.array([0.25, 1.0]),
            "model_version": "mlb_v1_test",
            "thresholds": [1, 2],
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
        # Use today's date so the freshness guard (T-193) does not halt before
        # the "no markets" exit path is reached.
        from datetime import date
        today_iso = date.today().isoformat()
        header = (
            "player_id,player_name,team_id,team_abbreviation,game_id,game_date,"
            "season,season_type,matchup,is_home_game,opponent_team_abbr,ab,h,"
            "doubles,triples,hr,rbi,bb,k,hbp,sf,snapshot_id,ingestion_run_id,"
            "ingested_at,temporal_cutoff,ba_l10,slg_l10,obp_l10,ops_l10,"
            "h_l10_mean,k_rate_l10,bb_rate_l10,hr_rate_l10,days_rest,b2b_flag,"
            "opp_runs_allowed_l10,opp_sp_era_l5,opp_sp_k9_l5,opp_sp_bb9_l5,"
            "opp_sp_is_known,park_factor_hits,feature_run_id,feature_version,"
            "train_test_label,threshold"
        )
        row = (
            f"660670,Juan Soto,147,NYY,717465,{today_iso},2024,Regular Season,"
            "NYY vs BOS,1,BOS,4,1,0,0,0,1,1,1,0,0,SNAP,IRD-001,"
            f"{today_iso}T12:00:00Z,{today_iso},0.280,0.450,0.380,0.830,"
            "1.0,0.22,0.15,0.03,1,0,"
            "4.5,4.0,8.0,3.0,"
            "1,1.0,FRD-001,1.0.0,"
            "train,1"
        )
        feature_csv.write_text(f"{header}\n{row}\n")
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
# GG-054 drill — SemanticFloorViolation guard fires live, end-to-end
# ---------------------------------------------------------------------------


class TestMainSemanticFloorViolationFiresLive:
    """
    GG-054: the guard at run_mlb_paper_trade.py's SemanticFloorGuard call site
    (games_fetched > 0, matched_players == 0) had never been exercised past
    the unit level for _count_scheduled_mlb_games / the exception class alone
    — every existing "no markets" test (TestMainNoMarkets) passes an empty
    `snap.markets`, which exits at the earlier `if not snap.markets: sys.exit(0)`
    guard (step 5) and never reaches the SemanticFloorGuard call site (step 7).

    This test drives main() through the real branch: `snap.markets` is
    non-empty (so step 5 does not short-circuit), no market groups into
    `markets_by_player` (ticker date deliberately mismatched — simulates a
    broken market-matching filter), the game-in-progress guard is mocked
    False, and `_count_scheduled_mlb_games` is mocked > 0 — the exact
    "games fetched but 0 matched" condition SemanticFloorGuard exists to
    catch. Confirms end-to-end: sys.exit(2), and a real CRITICAL
    `semantic_floor_violation` entry written to the actual C6 JSONL file
    (AuditLogger is not mocked — only LOG_DIR is redirected to tmp_path).
    """

    def _make_artifact(self) -> dict:
        return {
            "pipelines": {1: MagicMock(), 2: MagicMock()},
            "feature_names": ["ba_l10", "days_rest"],
            "col_medians": np.array([0.25, 1.0]),
            "model_version": "mlb_v1_test",
            "thresholds": [1, 2],
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

    def test_guard_fires_and_writes_critical_c6_event(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BOT_ENV", "paper")
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        import prediction_market_bot.run_mlb_paper_trade as runner

        from datetime import date
        today_iso = date.today().isoformat()

        feature_csv = tmp_path / "mlb_feature_matrix.csv"
        header = (
            "player_id,player_name,team_id,team_abbreviation,game_id,game_date,"
            "season,season_type,matchup,is_home_game,opponent_team_abbr,ab,h,"
            "doubles,triples,hr,rbi,bb,k,hbp,sf,snapshot_id,ingestion_run_id,"
            "ingested_at,temporal_cutoff,ba_l10,slg_l10,obp_l10,ops_l10,"
            "h_l10_mean,k_rate_l10,bb_rate_l10,hr_rate_l10,days_rest,b2b_flag,"
            "opp_runs_allowed_l10,opp_sp_era_l5,opp_sp_k9_l5,opp_sp_bb9_l5,"
            "opp_sp_is_known,park_factor_hits,feature_run_id,feature_version,"
            "train_test_label,threshold"
        )
        row = (
            f"660670,Juan Soto,147,NYY,717465,{today_iso},2024,Regular Season,"
            "NYY vs BOS,1,BOS,4,1,0,0,0,1,1,1,0,0,SNAP,IRD-001,"
            f"{today_iso}T12:00:00Z,{today_iso},0.280,0.450,0.380,0.830,"
            "1.0,0.22,0.15,0.03,1,0,"
            "4.5,4.0,8.0,3.0,"
            "1,1.0,FRD-001,1.0.0,"
            "train,1"
        )
        feature_csv.write_text(f"{header}\n{row}\n")
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")

        # A non-empty market list whose ticker date does NOT match today —
        # simulates a broken market-matching filter: markets exist, quotes
        # exist, but zero players end up matched to today's game date.
        mock_market = MagicMock()
        mock_market.status = "active"
        mock_market.has_live_quotes = True
        mock_market.vig = 0.05
        mock_market.player_name = "Juan Soto"
        mock_market.ticker = "KXMLBHIT-01JAN010000NYYBOS-BOSWABREU52-2"  # wrong month/day

        mock_snap = MagicMock()
        mock_snap.markets = [mock_market]

        mock_router = MagicMock()
        mock_router.check_all_connectivity.return_value = {"kalshi": (True, {})}
        mock_router.fetch_all_markets.return_value = (True, mock_snap)
        mock_router.active_venues = ["kalshi"]

        audit_log_path = tmp_path / "audit_mlb.jsonl"

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "PORTFOLIO_PATH", tmp_path / "portfolio.json"),
            patch.object(runner, "REPORT_PATH", tmp_path / "report.json"),
            patch.object(runner, "_is_mlb_game_in_progress", return_value=False),
            patch.object(runner, "_count_scheduled_mlb_games", return_value=2),
            patch.object(runner, "_build_live_sp_override", return_value={}),
            patch("prediction_market_bot.run_mlb_paper_trade.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_paper_trade.KalshiMarketClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.PaperTrader") as MockTrader,
            patch("prediction_market_bot.run_mlb_paper_trade.VenueRouter") as MockRouter,
            patch("prediction_market_bot.run_mlb_paper_trade.BAND_REGISTRY") as mock_reg,
            patch("prediction_market_bot.run_mlb_paper_trade.time.sleep") as mock_sleep,
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

        # 1. The guard actually halts the pipeline with the documented exit code.
        assert exc_info.value.code == 2

        # 2. A real CRITICAL event was written to the actual C6 audit log file
        #    (not a mock assertion — the file on disk is read back and parsed).
        assert audit_log_path.exists(), "C6 audit log file was never created"
        lines = [
            json.loads(line)
            for line in audit_log_path.read_text().splitlines()
            if line.strip()
        ]
        violation_events = [
            e for e in lines
            if e.get("event_type") == "semantic_floor_violation"
            and e.get("severity") == "CRITICAL"
        ]
        assert len(violation_events) == 1, (
            f"Expected exactly one CRITICAL semantic_floor_violation event, "
            f"found {len(violation_events)} in {lines}"
        )
        event = violation_events[0]
        assert event["payload"]["scheduled_preview_games"] == 2
        assert event["payload"]["kalshi_markets_total"] == 1
        assert event["component"] == "PIPE-05"

        # 3. T-343/GG-110: the bounded retry loop exhausted its full attempt
        #    budget (games are scheduled but never match) before falling
        #    through to the guard — confirms retries ran, and confirms
        #    real sleeps were never invoked (mocked out for test speed).
        retry_events = [
            e for e in lines
            if e.get("event_type") == "semantic_floor_retry"
        ]
        assert len(retry_events) == runner.PIPE05_FLOOR_RETRY_ATTEMPTS
        assert mock_sleep.call_count == runner.PIPE05_FLOOR_RETRY_ATTEMPTS

    def test_retry_recovers_when_later_fetch_matches_players(self, monkeypatch, tmp_path):
        """
        T-343/GG-110: if the first fetch attempt returns 0 matched players
        (games scheduled, Kalshi hasn't published same-day markets yet) but a
        later retry attempt returns a market that DOES match, main() should
        proceed normally — no SemanticFloorViolation, no sys.exit(2).
        """
        monkeypatch.setenv("BOT_ENV", "paper")
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        import prediction_market_bot.run_mlb_paper_trade as runner

        from datetime import date
        today_iso = date.today().isoformat()

        feature_csv = tmp_path / "mlb_feature_matrix.csv"
        header = (
            "player_id,player_name,team_id,team_abbreviation,game_id,game_date,"
            "season,season_type,matchup,is_home_game,opponent_team_abbr,ab,h,"
            "doubles,triples,hr,rbi,bb,k,hbp,sf,snapshot_id,ingestion_run_id,"
            "ingested_at,temporal_cutoff,ba_l10,slg_l10,obp_l10,ops_l10,"
            "h_l10_mean,k_rate_l10,bb_rate_l10,hr_rate_l10,days_rest,b2b_flag,"
            "opp_runs_allowed_l10,opp_sp_era_l5,opp_sp_k9_l5,opp_sp_bb9_l5,"
            "opp_sp_is_known,park_factor_hits,feature_run_id,feature_version,"
            "train_test_label,threshold"
        )
        row = (
            f"660670,Juan Soto,147,NYY,717465,{today_iso},2024,Regular Season,"
            "NYY vs BOS,1,BOS,4,1,0,0,0,1,1,1,0,0,SNAP,IRD-001,"
            f"{today_iso}T12:00:00Z,{today_iso},0.280,0.450,0.380,0.830,"
            "1.0,0.22,0.15,0.03,1,0,"
            "4.5,4.0,8.0,3.0,"
            "1,1.0,FRD-001,1.0.0,"
            "train,1"
        )
        feature_csv.write_text(f"{header}\n{row}\n")
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")

        # Attempt 1: non-empty markets, but ticker date does NOT match today
        # (0 players matched — the "Kalshi hasn't published yet" condition).
        mock_market_stale = MagicMock()
        mock_market_stale.status = "active"
        mock_market_stale.has_live_quotes = True
        mock_market_stale.vig = 0.05
        mock_market_stale.player_name = "Juan Soto"
        mock_market_stale.ticker = "KXMLBHIT-01JAN010000NYYBOS-BOSWABREU52-2"

        mock_snap_attempt1 = MagicMock()
        mock_snap_attempt1.markets = [mock_market_stale]

        # Attempt 2: ticker date DOES match today — retry recovers. Ticker
        # date parsing is exercised elsewhere (_ticker_to_game_date tests);
        # here we patch _ticker_to_game_date directly to avoid re-deriving
        # the real ticker format.
        # threshold=99 is deliberately outside the model's trained threshold
        # set ([1, 2] per _make_artifact) so the per-market loop hits the
        # existing "threshold_out_of_model_range" SKIP and `continue`s
        # immediately — this test's scope is the retry loop recovering a
        # matched player, not the downstream forecast/order pipeline.
        mock_market_live = MagicMock()
        mock_market_live.status = "active"
        mock_market_live.has_live_quotes = True
        mock_market_live.vig = 0.05
        mock_market_live.player_name = "Juan Soto"
        mock_market_live.ticker = "KXMLBHIT-LIVE-TICKER"
        mock_market_live.threshold = 99

        mock_snap_attempt2 = MagicMock()
        mock_snap_attempt2.markets = [mock_market_live]

        mock_router = MagicMock()
        mock_router.check_all_connectivity.return_value = {"kalshi": (True, {})}
        mock_router.fetch_all_markets.side_effect = [
            (True, mock_snap_attempt1),
            (True, mock_snap_attempt2),
        ]
        mock_router.active_venues = ["kalshi"]

        def _fake_ticker_to_date(ticker):
            return today_iso if ticker == "KXMLBHIT-LIVE-TICKER" else "2001-01-01"

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "PORTFOLIO_PATH", tmp_path / "portfolio.json"),
            patch.object(runner, "REPORT_PATH", tmp_path / "report.json"),
            patch.object(runner, "_is_mlb_game_in_progress", return_value=False),
            patch.object(runner, "_count_scheduled_mlb_games", return_value=2),
            patch.object(runner, "_ticker_to_game_date", side_effect=_fake_ticker_to_date),
            patch.object(runner, "_build_live_sp_override", return_value={}),
            patch("prediction_market_bot.run_mlb_paper_trade.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_paper_trade.KalshiMarketClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.PaperTrader") as MockTrader,
            patch("prediction_market_bot.run_mlb_paper_trade.VenueRouter") as MockRouter,
            patch("prediction_market_bot.run_mlb_paper_trade.BAND_REGISTRY") as mock_reg,
            patch("prediction_market_bot.run_mlb_paper_trade.time.sleep") as mock_sleep,
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

            # main() should complete normally (falls off the end, no
            # sys.exit call at all on the happy path) — not raise
            # SemanticFloorViolation/exit(2).
            runner.main()

        assert mock_router.fetch_all_markets.call_count == 2
        assert mock_sleep.call_count == 1  # exactly one retry before recovery

        audit_log_path = tmp_path / "audit_mlb.jsonl"
        lines = [
            json.loads(line)
            for line in audit_log_path.read_text().splitlines()
            if line.strip()
        ] if audit_log_path.exists() else []
        violation_events = [
            e for e in lines
            if e.get("event_type") == "semantic_floor_violation"
        ]
        assert len(violation_events) == 0

    def test_no_retry_on_genuine_zero_games_day(self, monkeypatch, tmp_path):
        """
        T-343/GG-110: if _count_scheduled_mlb_games returns 0 (a genuine
        off-day, not a Kalshi-publishing race), the retry loop must not
        burn attempts/delay — it should fall straight through to the
        SemanticFloorGuard on the first pass.
        """
        monkeypatch.setenv("BOT_ENV", "paper")
        sys.modules.pop("prediction_market_bot.run_mlb_paper_trade", None)
        import prediction_market_bot.run_mlb_paper_trade as runner

        from datetime import date
        today_iso = date.today().isoformat()

        feature_csv = tmp_path / "mlb_feature_matrix.csv"
        header = (
            "player_id,player_name,team_id,team_abbreviation,game_id,game_date,"
            "season,season_type,matchup,is_home_game,opponent_team_abbr,ab,h,"
            "doubles,triples,hr,rbi,bb,k,hbp,sf,snapshot_id,ingestion_run_id,"
            "ingested_at,temporal_cutoff,ba_l10,slg_l10,obp_l10,ops_l10,"
            "h_l10_mean,k_rate_l10,bb_rate_l10,hr_rate_l10,days_rest,b2b_flag,"
            "opp_runs_allowed_l10,opp_sp_era_l5,opp_sp_k9_l5,opp_sp_bb9_l5,"
            "opp_sp_is_known,park_factor_hits,feature_run_id,feature_version,"
            "train_test_label,threshold"
        )
        row = (
            f"660670,Juan Soto,147,NYY,717465,{today_iso},2024,Regular Season,"
            "NYY vs BOS,1,BOS,4,1,0,0,0,1,1,1,0,0,SNAP,IRD-001,"
            f"{today_iso}T12:00:00Z,{today_iso},0.280,0.450,0.380,0.830,"
            "1.0,0.22,0.15,0.03,1,0,"
            "4.5,4.0,8.0,3.0,"
            "1,1.0,FRD-001,1.0.0,"
            "train,1"
        )
        feature_csv.write_text(f"{header}\n{row}\n")
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")

        mock_market = MagicMock()
        mock_market.status = "active"
        mock_market.has_live_quotes = True
        mock_market.vig = 0.05
        mock_market.player_name = "Juan Soto"
        mock_market.ticker = "KXMLBHIT-01JAN010000NYYBOS-BOSWABREU52-2"  # never matches

        mock_snap = MagicMock()
        mock_snap.markets = [mock_market]

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
            patch.object(runner, "_is_mlb_game_in_progress", return_value=False),
            patch.object(runner, "_count_scheduled_mlb_games", return_value=0),
            patch.object(runner, "_build_live_sp_override", return_value={}),
            patch("prediction_market_bot.run_mlb_paper_trade.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_paper_trade.KalshiMarketClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_paper_trade.PaperTrader") as MockTrader,
            patch("prediction_market_bot.run_mlb_paper_trade.VenueRouter") as MockRouter,
            patch("prediction_market_bot.run_mlb_paper_trade.BAND_REGISTRY") as mock_reg,
            patch("prediction_market_bot.run_mlb_paper_trade.time.sleep") as mock_sleep,
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

            # games_fetched=0 means SemanticFloorGuard.assert_floor does NOT
            # raise (0 matched players is expected/consistent when 0 games
            # are scheduled) — main() completes normally, no SystemExit.
            runner.main()

        assert mock_router.fetch_all_markets.call_count == 1  # no retry occurred
        assert mock_sleep.call_count == 0

        audit_log_path = tmp_path / "audit_mlb.jsonl"
        lines = [
            json.loads(line)
            for line in audit_log_path.read_text().splitlines()
            if line.strip()
        ] if audit_log_path.exists() else []
        violation_events = [
            e for e in lines
            if e.get("event_type") == "semantic_floor_violation"
        ]
        assert len(violation_events) == 0


# ---------------------------------------------------------------------------
# Model thresholds constant
# ---------------------------------------------------------------------------


class TestModelThresholds:
    def test_model_thresholds_match_training(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert runner._MODEL_THRESHOLDS == frozenset({1, 2})

    def test_threshold_4_not_in_model(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert 4 not in runner._MODEL_THRESHOLDS


# ---------------------------------------------------------------------------
# T-187G: _safe_int
# ---------------------------------------------------------------------------


class TestSafeInt:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._safe_int

    def test_none_returns_none(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        assert fn(None) is None

    def test_nan_returns_none(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        assert fn(float("nan")) is None

    def test_valid_int_string(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        assert fn("660670") == 660670

    def test_valid_float(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        assert fn(123.9) == 123

    def test_non_numeric_string_returns_none(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        assert fn("abc") is None


# ---------------------------------------------------------------------------
# GG-077: _directional_edge — CHECK 3 must gate on the bet's true,
# direction-effective edge, not the raw YES-frame gross_edge - fee.
# ---------------------------------------------------------------------------


class TestDirectionalEdge:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._directional_edge

    def test_yes_bet_edge_unchanged(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # YES bet: gross_edge already direction-aligned, just subtract fee.
        assert fn("YES", 0.10, 0.0173) == pytest.approx(0.0827)

    def test_no_bet_flips_sign_before_fee(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # NO bet with gross_edge=-0.10 (YES-frame) is a *good* NO bet: true
        # directional edge is +0.10 net of fee, not -0.10 - fee.
        assert fn("NO", -0.10, 0.0173) == pytest.approx(0.0827)

    def test_no_bet_matches_paper_trader_directional_gross(self, monkeypatch):
        # Cross-check against paper_trader.py's independent flip so the two
        # gating paths (CHECK 3 pre-fire, stored fee_net_edge post-fire)
        # never disagree on the sign convention again.
        fn = self._get_fn(monkeypatch)
        gross_edge, mid = -0.15, 0.40
        fee = round(0.07 * mid * (1.0 - mid), 6)
        assert fn("NO", gross_edge, fee) == pytest.approx(-gross_edge - fee)


# ---------------------------------------------------------------------------
# T-187G: _SP_OVERRIDE_FIELDS constant
# ---------------------------------------------------------------------------


class TestSpOverrideFields:
    def test_contains_expected_keys(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        assert runner._SP_OVERRIDE_FIELDS == frozenset({
            "opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_sp_is_known"
        })


# ---------------------------------------------------------------------------
# T-187G: _build_mlb_feature_vector with sp_override
# ---------------------------------------------------------------------------


class TestBuildMLBFeatureVectorSpOverride:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._build_mlb_feature_vector

    def _make_row(self) -> pd.Series:
        return pd.Series({
            "ba_l10": 0.280,
            "opp_sp_era_l5": 4.0,   # stale historical SP
            "opp_sp_k9_l5": 8.0,
            "opp_sp_bb9_l5": 3.0,
            "opp_sp_is_known": 1.0,
        })

    def test_sp_override_replaces_sp_field(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["opp_sp_era_l5"]
        medians = np.array([4.0])
        override = {"opp_sp_era_l5": 2.50}

        X = fn(row, feature_names=feature_names, col_medians=medians, sp_override=override)
        assert X[0, 0] == pytest.approx(2.50)

    def test_sp_override_none_value_imputed_from_median(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["opp_sp_era_l5"]
        medians = np.array([3.75])
        override = {"opp_sp_era_l5": None}   # API returned no value

        X = fn(row, feature_names=feature_names, col_medians=medians, sp_override=override)
        assert X[0, 0] == pytest.approx(3.75)

    def test_non_sp_field_still_uses_row_when_override_provided(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["ba_l10", "opp_sp_era_l5"]
        medians = np.array([0.25, 4.0])
        override = {"opp_sp_era_l5": 2.50}

        X = fn(row, feature_names=feature_names, col_medians=medians, sp_override=override)
        assert X[0, 0] == pytest.approx(0.280)  # ba_l10 from row
        assert X[0, 1] == pytest.approx(2.50)   # era from override

    def test_sp_override_none_falls_back_to_row(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["opp_sp_era_l5"]
        medians = np.array([4.0])

        X = fn(row, feature_names=feature_names, col_medians=medians, sp_override=None)
        assert X[0, 0] == pytest.approx(4.0)   # historical value from row

    def test_opp_sp_is_known_from_override(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        row = self._make_row()
        feature_names = ["opp_sp_is_known"]
        medians = np.array([1.0])
        override = {"opp_sp_is_known": 0.0}   # SP unknown tonight

        X = fn(row, feature_names=feature_names, col_medians=medians, sp_override=override)
        assert X[0, 0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# T-187G: _build_live_sp_override
# ---------------------------------------------------------------------------


def _make_pitcher_log_df() -> pd.DataFrame:
    """5 starts prior to 2026-06-24 for a pitcher with pid=999."""
    return pd.DataFrame({
        "game_date": ["2026-06-01", "2026-06-06", "2026-06-11",
                      "2026-06-16", "2026-06-21"],
        "ip":        [6.0, 7.0, 5.0, 6.0, 7.0],
        "er":        [2.0, 1.0, 3.0, 2.0, 1.0],
        "k":         [7.0, 9.0, 5.0, 8.0, 10.0],
        "bb":        [2.0, 1.0, 3.0, 1.0, 2.0],
        "is_start":  [1, 1, 1, 1, 1],
    })


class TestBuildLiveSpOverride:
    def _get_fn(self, monkeypatch):
        return _import_runner(monkeypatch)._build_live_sp_override

    def _make_logger(self) -> MagicMock:
        m = MagicMock()
        m.info = MagicMock()
        m.warning = MagicMock()
        return m

    def _make_client(self, starters_ok=True, starters=None, log_ok=True, log_df=None):
        c = MagicMock()
        c.fetch_game_starters.return_value = (starters_ok, starters or {})
        c.fetch_pitcher_game_log.return_value = (log_ok, log_df)
        return c

    def test_returns_empty_on_api_failure(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        client = self._make_client(starters_ok=False)
        latest_df = pd.DataFrame({"player_id": [660670], "team_id": [147]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        assert result == {}

    def test_returns_empty_when_no_starters(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        client = self._make_client(starters_ok=True, starters={})
        latest_df = pd.DataFrame({"player_id": [660670], "team_id": [147]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        assert result == {}

    def test_player_not_playing_tonight_excluded(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # Game only has team_id=147 (NYY) vs team_id=111 (BOS)
        starters = {1001: {
            "home_team_id": 147, "away_team_id": 111,
            "home_sp_id": 999,  "away_sp_id": 888,
        }}
        client = self._make_client(starters=starters, log_df=_make_pitcher_log_df())
        # Player is on team 133 (OAK) — not playing tonight
        latest_df = pd.DataFrame({"player_id": [777777], "team_id": [133]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        assert result == {}

    def test_home_player_gets_away_sp(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # Player 660670 is on the HOME team (147); opp SP is the AWAY SP (888)
        starters = {1001: {
            "home_team_id": 147, "away_team_id": 111,
            "home_sp_id": 999,  "away_sp_id": 888,
        }}
        client = self._make_client(starters=starters, log_df=_make_pitcher_log_df())
        latest_df = pd.DataFrame({"player_id": [660670], "team_id": [147]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        # fetch_pitcher_game_log should have been called with away SP id = 888
        client.fetch_pitcher_game_log.assert_called_once_with(
            888, "2026", session_id="SID-001",
        )
        assert 660670 in result
        assert result[660670]["opp_sp_is_known"] == pytest.approx(1.0)

    def test_away_player_gets_home_sp(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # Player 660670 is on the AWAY team (111); opp SP is the HOME SP (999)
        starters = {1001: {
            "home_team_id": 147, "away_team_id": 111,
            "home_sp_id": 999,  "away_sp_id": 888,
        }}
        client = self._make_client(starters=starters, log_df=_make_pitcher_log_df())
        latest_df = pd.DataFrame({"player_id": [660670], "team_id": [111]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        # fetch_pitcher_game_log should have been called with home SP id = 999
        client.fetch_pitcher_game_log.assert_called_once_with(
            999, "2026", session_id="SID-001",
        )
        assert 660670 in result

    def test_unknown_sp_sets_is_known_zero(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        # SP not yet announced (None)
        starters = {1001: {
            "home_team_id": 147, "away_team_id": 111,
            "home_sp_id": None, "away_sp_id": None,
        }}
        client = self._make_client(starters=starters)
        latest_df = pd.DataFrame({"player_id": [660670], "team_id": [147]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        assert 660670 in result
        assert result[660670]["opp_sp_is_known"] == pytest.approx(0.0)
        assert result[660670]["opp_sp_era_l5"] is None
        client.fetch_pitcher_game_log.assert_not_called()

    def test_happy_path_stats_populated(self, monkeypatch):
        fn = self._get_fn(monkeypatch)
        starters = {1001: {
            "home_team_id": 147, "away_team_id": 111,
            "home_sp_id": 999,  "away_sp_id": 888,
        }}
        client = self._make_client(starters=starters, log_df=_make_pitcher_log_df())
        latest_df = pd.DataFrame({"player_id": [660670], "team_id": [147]})

        result = fn("2026-06-24", latest_df, client, self._make_logger(), "SID-001")
        assert 660670 in result
        override = result[660670]
        assert override["opp_sp_is_known"] == pytest.approx(1.0)
        # ERA = 9 ER / 31 IP * 9 ≈ 2.613; k9 = 39k/31ip*9 ≈ 11.32; bb9 = 9bb/31ip*9 ≈ 2.61
        assert override["opp_sp_era_l5"] == pytest.approx(9.0 / 31.0 * 9, rel=1e-3)
        assert override["opp_sp_k9_l5"] == pytest.approx(39.0 / 31.0 * 9, rel=1e-3)
        assert override["opp_sp_bb9_l5"] == pytest.approx(9.0 / 31.0 * 9, rel=1e-3)


# ---------------------------------------------------------------------------
# SemanticFloorViolation — Session 101 (semantic oracle guard)
# ---------------------------------------------------------------------------


class TestSemanticFloorViolation:
    """
    _count_scheduled_mlb_games and the SemanticFloorViolation guard logic.

    The guard fires when scheduled_preview_games > 0 AND 0 players matched.
    It must NOT fire when no games are scheduled (quiet day / off-season).
    """

    def _get_count_fn(self, monkeypatch):
        runner = _import_runner(monkeypatch)
        return runner._count_scheduled_mlb_games

    def test_count_returns_preview_games(self, monkeypatch):
        """_count_scheduled_mlb_games counts only Preview-state games."""
        runner = _import_runner(monkeypatch)
        api_resp = {
            "dates": [{
                "games": [
                    {"status": {"abstractGameState": "Preview"}},
                    {"status": {"abstractGameState": "Preview"}},
                    {"status": {"abstractGameState": "Final"}},
                ]
            }]
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_resp

        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   return_value=mock_resp):
            count = runner._count_scheduled_mlb_games("2026-06-29")

        assert count == 2

    def test_count_excludes_final_games(self, monkeypatch):
        """Final-only games return 0 — prevents end-of-day false alarm."""
        runner = _import_runner(monkeypatch)
        api_resp = {
            "dates": [{"games": [
                {"status": {"abstractGameState": "Final"}},
                {"status": {"abstractGameState": "Final"}},
            ]}]
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_resp

        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   return_value=mock_resp):
            count = runner._count_scheduled_mlb_games("2026-06-29")

        assert count == 0

    def test_count_returns_zero_on_api_failure(self, monkeypatch):
        """API failure returns 0 — T1 not blocked by schedule endpoint outage."""
        runner = _import_runner(monkeypatch)
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   side_effect=Exception("timeout")):
            count = runner._count_scheduled_mlb_games("2026-06-29")
        assert count == 0

    def test_count_returns_zero_when_no_dates(self, monkeypatch):
        """Empty dates array (off-season / no games today) returns 0."""
        runner = _import_runner(monkeypatch)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"dates": []}

        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   return_value=mock_resp):
            count = runner._count_scheduled_mlb_games("2026-01-15")

        assert count == 0

    def test_violation_class_is_exception(self, monkeypatch):
        """SemanticFloorViolation is an Exception subclass (canonical ADR-0034 class)."""
        runner = _import_runner(monkeypatch)
        assert issubclass(runner.SemanticFloorViolation, Exception)

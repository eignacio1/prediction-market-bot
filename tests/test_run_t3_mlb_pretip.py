"""
Tests for run_t3_mlb_pretip.py (T-190 Step 2 — PIPE-06 MLB).

Scope:
  - _load_pregame_context: most-recent pregame_mlb_*.json selection
  - Momentum signal logic: CONFIRM/FADE/NEUTRAL for YES and NO directions
  - _write_empty_report: output schema validation
  - main() no pregame file → exits 0, writes empty report
  - main() no KXMLBHIT markets → exits 0, writes empty report
  - main() happy path → writes t3_mlb_YYYYMMDD_HHMM.json with CONFIRM/FADE/NEUTRAL rows
  - main() ticker not in live quotes → skipped in output
  - Constants: MOMENTUM_THRESHOLD, CONFIRM_MULTIPLIER, FADE_MULTIPLIER

Excluded:
  - Real Kalshi API calls
  - Real MLB Stats API calls
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT  = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


# ---------------------------------------------------------------------------
# Module import helper
# ---------------------------------------------------------------------------


def _import_runner():
    sys.modules.pop("prediction_market_bot.run_t3_mlb_pretip", None)
    import prediction_market_bot.run_t3_mlb_pretip as runner
    return runner


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_momentum_threshold(self):
        r = _import_runner()
        assert r.MOMENTUM_THRESHOLD == pytest.approx(0.025)

    def test_confirm_multiplier(self):
        r = _import_runner()
        assert r.CONFIRM_MULTIPLIER == pytest.approx(1.15)

    def test_fade_multiplier(self):
        r = _import_runner()
        assert r.FADE_MULTIPLIER == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# _load_pregame_context
# ---------------------------------------------------------------------------


def _write_pregame(tmp_path: Path, filename: str, forecasts: list[dict]) -> Path:
    p = tmp_path / filename
    p.write_text(json.dumps({"forecasts": forecasts, "sport": "mlb"}))
    return p


class TestLoadPregameContext:
    def test_returns_most_recent_file(self, tmp_path):
        _write_pregame(tmp_path, "pregame_mlb_20260620.json",
                       [{"player_name": "Old", "kalshi_ticker": "T-OLD"}])
        _write_pregame(tmp_path, "pregame_mlb_20260624.json",
                       [{"player_name": "Current", "kalshi_ticker": "T-NEW"}])

        runner = _import_runner()
        with patch.object(runner, "LOG_DIR", tmp_path):
            # Re-read to pick up patched LOG_DIR
            sys.modules.pop("prediction_market_bot.run_t3_mlb_pretip", None)
            import prediction_market_bot.run_t3_mlb_pretip as r2
            import importlib
            r2.LOG_DIR = tmp_path
            forecasts, path = r2._load_pregame_context()

        assert len(forecasts) == 1
        assert forecasts[0]["player_name"] == "Current"

    def test_no_file_returns_empty(self, tmp_path):
        runner = _import_runner()
        runner.LOG_DIR = tmp_path
        forecasts, path = runner._load_pregame_context()
        assert forecasts == []
        assert path is None


# ---------------------------------------------------------------------------
# Momentum signal logic — unit tests via main() happy path
# ---------------------------------------------------------------------------


def _make_pregame(tmp_path: Path, forecasts: list[dict]) -> Path:
    p = tmp_path / f"pregame_mlb_20260624.json"
    p.write_text(json.dumps({"forecasts": forecasts, "sport": "mlb"}))
    return p


def _make_live_market(ticker: str, mid: float) -> MagicMock:
    m = MagicMock()
    m.ticker = ticker
    m.mid_price = mid
    m.has_live_quotes = True
    return m


def _run_main_with_mocks(tmp_path: Path, forecasts: list[dict],
                         live_mids: dict[str, float]) -> dict:
    runner = _import_runner()

    _make_pregame(tmp_path, forecasts)
    output_path = tmp_path / "t3_mlb_20260624_2130.json"

    live_mkts = [_make_live_market(ticker, mid) for ticker, mid in live_mids.items()]
    mock_snap = MagicMock()
    mock_snap.markets = live_mkts

    mock_client = MagicMock()
    mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
    mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

    with (
        patch.object(runner, "LOG_DIR", tmp_path),
        patch.object(runner, "OUTPUT_PATH", output_path),
        patch("prediction_market_bot.run_t3_mlb_pretip.KalshiMarketClient") as MockClient,
    ):
        runner.LOG_DIR = tmp_path
        MockClient.from_env.return_value = mock_client
        runner.main()

    return json.loads(output_path.read_text())


TICKER = "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-1"


class TestMomentumSignalLogic:
    def _fc(self, direction: str, mid: float) -> dict:
        return {
            "player_name": "Juan Soto",
            "player_id": 660670,
            "kalshi_ticker": TICKER,
            "kalshi_threshold": 1,
            "direction": direction,
            "mid_price": mid,
            "edge": 0.08,
            "p_estimate": 0.55,
        }

    def test_yes_price_up_is_confirm(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("YES", 0.35)], {TICKER: 0.38})
        assert report["forecasts"][0]["momentum_signal"] == "CONFIRM"
        assert report["confirmed"] == 1

    def test_yes_price_down_is_fade(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("YES", 0.35)], {TICKER: 0.32})
        assert report["forecasts"][0]["momentum_signal"] == "FADE"
        assert report["faded"] == 1

    def test_yes_small_drift_is_neutral(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("YES", 0.35)], {TICKER: 0.36})
        assert report["forecasts"][0]["momentum_signal"] == "NEUTRAL"
        assert report["neutral"] == 1

    def test_no_price_down_is_confirm(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("NO", 0.65)], {TICKER: 0.62})
        assert report["forecasts"][0]["momentum_signal"] == "CONFIRM"

    def test_no_price_up_is_fade(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("NO", 0.65)], {TICKER: 0.68})
        assert report["forecasts"][0]["momentum_signal"] == "FADE"

    def test_confirm_multiplier_applied(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("YES", 0.35)], {TICKER: 0.38})
        fc = report["forecasts"][0]
        assert fc["t3_edge_adjusted"] == pytest.approx(0.08 * 1.15, abs=1e-4)

    def test_fade_multiplier_applied(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("YES", 0.35)], {TICKER: 0.32})
        fc = report["forecasts"][0]
        assert fc["t3_edge_adjusted"] == pytest.approx(0.08 * 0.75, abs=1e-4)

    def test_neutral_edge_unchanged(self, tmp_path):
        report = _run_main_with_mocks(
            tmp_path, [self._fc("YES", 0.35)], {TICKER: 0.36})
        fc = report["forecasts"][0]
        assert fc["t3_edge_adjusted"] == pytest.approx(0.08, abs=1e-4)


# ---------------------------------------------------------------------------
# main() — no pregame file → exits 0, writes empty report
# ---------------------------------------------------------------------------


class TestMainNoPregameFile:
    def test_exits_0_writes_empty(self, tmp_path):
        runner = _import_runner()
        output_path = tmp_path / "t3_mlb_20260624_2130.json"

        with (
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_t3_mlb_pretip.KalshiMarketClient"),
        ):
            runner.LOG_DIR = tmp_path
            with pytest.raises(SystemExit) as exc_info:
                runner.main()
        assert exc_info.value.code == 0
        assert output_path.exists()
        report = json.loads(output_path.read_text())
        assert report["reason"] == "no_pregame_file"
        assert report["forecasts"] == []
        assert report["sport"] == "mlb"


# ---------------------------------------------------------------------------
# main() — no live markets → exits 0, writes empty report
# ---------------------------------------------------------------------------


class TestMainNoMarkets:
    def test_exits_0_on_no_markets(self, tmp_path):
        runner = _import_runner()
        _make_pregame(tmp_path, [{
            "player_name": "Juan Soto", "player_id": 660670,
            "kalshi_ticker": TICKER, "kalshi_threshold": 1,
            "direction": "YES", "mid_price": 0.35, "edge": 0.08, "p_estimate": 0.55,
        }])
        output_path = tmp_path / "t3_mlb_20260624_2130.json"

        mock_snap = MagicMock()
        mock_snap.markets = []
        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_t3_mlb_pretip.KalshiMarketClient") as MockClient,
        ):
            runner.LOG_DIR = tmp_path
            MockClient.from_env.return_value = mock_client
            with pytest.raises(SystemExit) as exc_info:
                runner.main()
        assert exc_info.value.code == 0
        report = json.loads(output_path.read_text())
        assert report["reason"] == "no_live_markets"


# ---------------------------------------------------------------------------
# main() — ticker not in live quotes is skipped
# ---------------------------------------------------------------------------


class TestMainTickerNotInLiveMarkets:
    def test_missing_ticker_skipped(self, tmp_path):
        runner = _import_runner()
        _make_pregame(tmp_path, [{
            "player_name": "Juan Soto", "player_id": 660670,
            "kalshi_ticker": "KXMLBHIT-TICKER-NOT-LIVE",
            "kalshi_threshold": 1,
            "direction": "YES", "mid_price": 0.35, "edge": 0.08, "p_estimate": 0.55,
        }])
        output_path = tmp_path / "t3_mlb_20260624_2130.json"

        # Live market has a DIFFERENT ticker
        live = _make_live_market("KXMLBHIT-DIFFERENT-TICKER", 0.40)
        mock_snap = MagicMock()
        mock_snap.markets = [live]
        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_t3_mlb_pretip.KalshiMarketClient") as MockClient,
        ):
            runner.LOG_DIR = tmp_path
            MockClient.from_env.return_value = mock_client
            runner.main()

        report = json.loads(output_path.read_text())
        assert report["t3_evaluated"] == 0
        assert report["forecasts"] == []


# ---------------------------------------------------------------------------
# main() — PASS forecasts from T1 are excluded
# ---------------------------------------------------------------------------


class TestMainPassForecastsExcluded:
    def test_pass_direction_not_evaluated(self, tmp_path):
        runner = _import_runner()
        _make_pregame(tmp_path, [{
            "player_name": "Juan Soto", "player_id": 660670,
            "kalshi_ticker": TICKER, "kalshi_threshold": 1,
            "direction": "PASS", "mid_price": 0.35, "edge": 0.01, "p_estimate": 0.48,
        }])
        output_path = tmp_path / "t3_mlb_20260624_2130.json"

        live = _make_live_market(TICKER, 0.38)
        mock_snap = MagicMock()
        mock_snap.markets = [live]
        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_t3_mlb_pretip.KalshiMarketClient") as MockClient,
        ):
            runner.LOG_DIR = tmp_path
            MockClient.from_env.return_value = mock_client
            with pytest.raises(SystemExit) as exc_info:
                runner.main()
        assert exc_info.value.code == 0
        report = json.loads(output_path.read_text())
        assert report["reason"] == "no_actionable_t1"


# ---------------------------------------------------------------------------
# main() — report output schema
# ---------------------------------------------------------------------------


class TestReportSchema:
    def test_report_keys_present(self, tmp_path):
        report = _run_main_with_mocks(tmp_path, [{
            "player_name": "Juan Soto", "player_id": 660670,
            "kalshi_ticker": TICKER, "kalshi_threshold": 1,
            "direction": "YES", "mid_price": 0.35, "edge": 0.08, "p_estimate": 0.55,
        }], {TICKER: 0.38})

        required = {"session_id", "band", "game_date", "sport", "run_at",
                    "t1_actionable", "t3_evaluated", "confirmed", "faded", "neutral",
                    "forecasts"}
        assert required.issubset(report.keys())
        assert report["sport"] == "mlb"

    def test_forecast_row_keys(self, tmp_path):
        report = _run_main_with_mocks(tmp_path, [{
            "player_name": "Juan Soto", "player_id": 660670,
            "kalshi_ticker": TICKER, "kalshi_threshold": 1,
            "direction": "YES", "mid_price": 0.35, "edge": 0.08, "p_estimate": 0.55,
        }], {TICKER: 0.38})

        fc = report["forecasts"][0]
        required = {
            "player_name", "player_id", "kalshi_ticker", "kalshi_threshold",
            "t1_mid_price", "current_mid_price", "price_drift",
            "momentum_signal", "t1_edge", "t3_edge_adjusted",
            "t1_p_estimate", "t1_direction", "band", "kelly_fraction", "sport",
        }
        assert required.issubset(fc.keys())

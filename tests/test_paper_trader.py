"""
Tests for c5_execution.paper_trader — PaperTrader core logic.

Coverage areas:
  - open_position: deducts bankroll, records position, returns position dict
  - resolve_pending: skips positions whose game_date == today
  - resolve_pending: attempts Playoffs fallback when Regular Season returns empty DataFrame
  - resolve_pending: correct P&L formula (win: size*(1-ask)/ask; loss: -size)
  - resolve_pending: bankroll updated correctly on win and loss
  - summary: correct drawdown and win_rate calculations
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c5_execution.paper_trader import PaperTrader, INITIAL_BANKROLL_USD

_PAST_DATE = "2026-05-30"
_TODAY = "2026-05-31"
_MOCK_TODAY = "prediction_market_bot.c5_execution.paper_trader._today"
_PGL = "nba_api.stats.endpoints.PlayerGameLog"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_logger():
    logger = MagicMock()
    logger.info.return_value = True
    logger.warning.return_value = True
    logger.error.return_value = True
    logger.log.return_value = True
    return logger


def _make_approval(size: float, direction: str = "YES") -> dict:
    return {
        "approval_status": "APPROVED",
        "approved_size": size,
        "approved_direction": direction,
        "risk_eval_id": "RISK-TEST001",
        "forecast_id": "FCST-TEST001",
    }


def _make_position(game_date: str, direction: str = "YES",
                   threshold: int = 20, size: float = 50.0,
                   mid: float = 0.45, vig: float = 0.02) -> dict:
    return {
        "position_id": "POS-TEST001",
        "player_name": "Test Player",
        "player_id": 999999,
        "kalshi_ticker": "KXNBAPTS-26MAY30SASOKC-TST-20",
        "kalshi_threshold": threshold,
        "direction": direction,
        "mid_price_at_entry": mid,
        "vig_at_entry": vig,
        "size_usd": size,
        "game_date": game_date,
        "entered_at": "2026-05-30T00:00:00.000Z",
        "risk_eval_id": "RISK-TEST001",
        "forecast_id": "FCST-TEST001",
        "status": "OPEN",
    }


def _mock_pgl(game_date: str, pts: float) -> MagicMock:
    """Return a mock PlayerGameLog that yields one row matching game_date."""
    df = pd.DataFrame({"GAME_DATE": [game_date], "PTS": [pts]})
    m = MagicMock()
    m.get_data_frames.return_value = [df]
    return m


def _empty_pgl() -> MagicMock:
    """Return a mock PlayerGameLog with no matching rows."""
    df = pd.DataFrame({"GAME_DATE": ["2000-01-01"], "PTS": [0.0]})
    m = MagicMock()
    m.get_data_frames.return_value = [df]
    return m


# ---------------------------------------------------------------------------
# open_position
# ---------------------------------------------------------------------------

class TestOpenPosition:
    @pytest.mark.unit
    def test_deducts_bankroll(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        initial = trader.get_state()["bankroll_usd"]
        ok, pos = trader.open_position(
            approval=_make_approval(50.0, "YES"),
            player_name="Test", player_id=999,
            kalshi_ticker="KXNBAPTS-TEST", kalshi_threshold=20,
            mid_price=0.45, vig=0.02, game_date=_PAST_DATE,
        )
        assert ok
        assert trader.get_state()["bankroll_usd"] == round(initial - 50.0, 4)

    @pytest.mark.unit
    def test_records_position(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        ok, pos = trader.open_position(
            approval=_make_approval(30.0, "NO"),
            player_name="SGA", player_id=1628983,
            kalshi_ticker="KXNBAPTS-TEST-30", kalshi_threshold=30,
            mid_price=0.58, vig=0.02, game_date=_PAST_DATE,
        )
        assert ok
        assert pos["direction"] == "NO"
        assert pos["size_usd"] == 30.0
        assert len(trader.get_state()["open_positions"]) == 1

    @pytest.mark.unit
    def test_rejects_zero_size(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        ok, pos = trader.open_position(
            approval=_make_approval(0.0, "YES"),
            player_name="Test", player_id=1,
            kalshi_ticker="KXNBAPTS-TEST", kalshi_threshold=20,
            mid_price=0.45, vig=0.02, game_date=_PAST_DATE,
        )
        assert ok
        assert pos == {}
        assert len(trader.get_state()["open_positions"]) == 0


# ---------------------------------------------------------------------------
# resolve_pending — date filtering
# ---------------------------------------------------------------------------

class TestResolvePendingFilter:
    @pytest.mark.unit
    def test_skips_positions_with_today_game_date(self, tmp_path):
        """Positions with game_date == today are skipped — game hasn't finished."""
        today = date.today().isoformat()
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(_make_position(game_date=today))
        trader._state["bankroll_usd"] -= 50.0

        # nba_api not imported at module level — patch its module path
        with patch(_MOCK_TODAY, return_value=today):
            ok, resolved = trader.resolve_pending()

        assert resolved == []

    @pytest.mark.unit
    def test_attempts_positions_with_past_game_date(self, tmp_path):
        """Positions with game_date < today trigger nba_api lookup."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(_make_position(game_date=_PAST_DATE))
        trader._state["bankroll_usd"] -= 50.0

        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 22.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        assert len(resolved) == 1


# ---------------------------------------------------------------------------
# resolve_pending — Playoffs fallback (Bug E regression test)
# ---------------------------------------------------------------------------

class TestPlayoffsFallback:
    @pytest.mark.unit
    def test_tries_playoffs_when_regular_season_empty(self, tmp_path):
        """
        Bug E regression: when Regular Season returns data but no matching
        game_date row, the Playoffs endpoint MUST be attempted.
        Old code: Playoffs only tried on exception (not on empty result).
        Fixed code: always tries Playoffs when actual_pts is None.
        """
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="YES",
                           threshold=15, size=50.0, mid=0.44, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 50.0

        call_count = 0

        def make_pgl(**kwargs):
            nonlocal call_count
            call_count += 1
            if kwargs.get("season_type_all_star") == "Regular Season":
                return _empty_pgl()       # No matching date — playoff game
            return _mock_pgl(_PAST_DATE, 22.0)  # Playoffs: actual game data

        with patch(_PGL, side_effect=make_pgl):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        assert call_count == 2, (
            f"Expected 2 nba_api calls (Regular Season + Playoffs fallback), got {call_count}. "
            "Bug E regression: Playoffs fallback not triggered when Regular Season returns empty."
        )
        assert len(resolved) == 1
        assert resolved[0]["actual_pts"] == 22.0

    @pytest.mark.unit
    def test_does_not_call_playoffs_when_regular_season_has_data(self, tmp_path):
        """Regular season games resolve in one call — Playoffs endpoint not needed."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(
            _make_position(game_date="2026-04-01", direction="YES",
                           threshold=20, size=40.0, mid=0.50, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 40.0

        call_count = 0

        def make_pgl(**kwargs):
            nonlocal call_count
            call_count += 1
            return _mock_pgl("2026-04-01", 25.0)

        with patch(_PGL, side_effect=make_pgl):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value="2026-04-02"):
                    ok, resolved = trader.resolve_pending()

        assert call_count == 1
        assert len(resolved) == 1

    @pytest.mark.unit
    def test_playoffs_fallback_on_exception(self, tmp_path):
        """Playoffs endpoint must be tried when Regular Season throws an exception."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="NO",
                           threshold=30, size=35.0, mid=0.57, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 35.0

        def make_pgl(**kwargs):
            if kwargs.get("season_type_all_star") == "Regular Season":
                raise Exception("API timeout")
            return _mock_pgl(_PAST_DATE, 28.0)

        with patch(_PGL, side_effect=make_pgl):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        assert len(resolved) == 1
        assert resolved[0]["actual_pts"] == 28.0


# ---------------------------------------------------------------------------
# resolve_pending — P&L formula (Bug B regression test)
# ---------------------------------------------------------------------------

class TestPnLFormula:
    @pytest.mark.unit
    def test_yes_win_pnl(self, tmp_path):
        """YES WIN: pnl = size * (1 - ask) / ask — NOT (1 - ask) * size."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        # mid=0.44, vig=0.02 → yes_ask = 0.44 + 0.01 = 0.45
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="YES",
                           threshold=15, size=100.0, mid=0.44, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 100.0

        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 22.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        yes_ask = 0.44 + 0.02 / 2  # 0.45
        expected_pnl = round(100.0 * (1.0 - yes_ask) / yes_ask, 4)
        assert resolved[0]["pnl"] == expected_pnl
        assert resolved[0]["outcome"] == "WIN"

    @pytest.mark.unit
    def test_yes_loss_pnl(self, tmp_path):
        """YES LOSS: pnl = -size exactly."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="YES",
                           threshold=30, size=75.0, mid=0.44, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 75.0

        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 14.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        assert resolved[0]["pnl"] == -75.0
        assert resolved[0]["outcome"] == "LOSS"

    @pytest.mark.unit
    def test_no_win_pnl(self, tmp_path):
        """NO WIN: pnl = size * (1 - no_ask) / no_ask."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        # mid=0.57, vig=0.02 → no_ask = (1 - 0.57) + 0.01 = 0.44
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="NO",
                           threshold=30, size=80.0, mid=0.57, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 80.0

        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 25.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        no_ask = (1.0 - 0.57) + 0.02 / 2  # 0.44
        expected_pnl = round(80.0 * (1.0 - no_ask) / no_ask, 4)
        assert resolved[0]["pnl"] == expected_pnl
        assert resolved[0]["outcome"] == "WIN"

    @pytest.mark.unit
    def test_no_loss_pnl(self, tmp_path):
        """NO LOSS: pnl = -size exactly."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="NO",
                           threshold=20, size=60.0, mid=0.57, vig=0.02)
        )
        trader._state["bankroll_usd"] -= 60.0

        # pts >= threshold (25 >= 20) → YES wins → NO loses
        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 25.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    ok, resolved = trader.resolve_pending()

        assert resolved[0]["pnl"] == -60.0
        assert resolved[0]["outcome"] == "LOSS"


# ---------------------------------------------------------------------------
# resolve_pending — bankroll update
# ---------------------------------------------------------------------------

class TestBankrollUpdate:
    @pytest.mark.unit
    def test_bankroll_net_zero_on_loss(self, tmp_path):
        """On loss: bankroll += size + (-size) = 0 → bankroll stays at post-bet level."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        initial = trader.get_state()["bankroll_usd"]
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="YES",
                           threshold=40, size=50.0, mid=0.44, vig=0.02)
        )
        trader._state["bankroll_usd"] = initial - 50.0

        # pts=10 < threshold=40 → YES loses
        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 10.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    trader.resolve_pending()

        # Bankroll stays at (initial - 50) because loss pnl=-50 cancels the +50 return
        assert trader.get_state()["bankroll_usd"] == round(initial - 50.0, 4)

    @pytest.mark.unit
    def test_bankroll_increases_on_win(self, tmp_path):
        """On win: bankroll grows above pre-bet level by pnl amount."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        initial = trader.get_state()["bankroll_usd"]
        # mid=0.44, vig=0.02 → ask=0.45 → win pnl = 100*(0.55/0.45) = 122.22
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="YES",
                           threshold=15, size=100.0, mid=0.44, vig=0.02)
        )
        trader._state["bankroll_usd"] = initial - 100.0

        with patch(_PGL, return_value=_mock_pgl(_PAST_DATE, 22.0)):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    trader.resolve_pending()

        yes_ask = 0.45
        expected_pnl = round(100.0 * (1.0 - yes_ask) / yes_ask, 4)
        expected_bankroll = round(initial - 100.0 + 100.0 + expected_pnl, 4)
        assert trader.get_state()["bankroll_usd"] == expected_bankroll
        assert trader.get_state()["bankroll_usd"] > initial


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

class TestSummary:
    @pytest.mark.unit
    def test_realized_drawdown_zero_when_only_open_stakes(self, tmp_path):
        """Bankroll depleted by open stakes is NOT drawdown — no money is lost yet."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["bankroll_usd"] = 683.41
        trader._state["initial_bankroll_usd"] = 1000.0
        trader._state["total_realized_pnl"] = 0.0
        summary = trader.summary()
        assert summary["realized_drawdown_pct"] == 0.0
        assert summary["deployed_pct"] == round((1000.0 - 683.41) / 1000.0 * 100, 2)

    @pytest.mark.unit
    def test_realized_drawdown_reflects_closed_losses(self, tmp_path):
        """realized_drawdown_pct tracks permanent losses from resolved positions only."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["initial_bankroll_usd"] = 1000.0
        trader._state["total_realized_pnl"] = -150.0
        trader._state["bankroll_usd"] = 850.0  # 1000 - 150 lost
        summary = trader.summary()
        assert summary["realized_drawdown_pct"] == 15.0
        assert summary["deployed_pct"] == 0.0   # no open stakes

    @pytest.mark.unit
    def test_deployed_pct_and_realized_drawdown_independent(self, tmp_path):
        """Both metrics can be nonzero simultaneously."""
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["initial_bankroll_usd"] = 1000.0
        trader._state["total_realized_pnl"] = -100.0   # $100 realized loss
        trader._state["bankroll_usd"] = 700.0           # $900 - $200 in open stakes
        summary = trader.summary()
        assert summary["realized_drawdown_pct"] == 10.0
        assert summary["deployed_pct"] == 20.0  # 200 in open stakes / 1000

    @pytest.mark.unit
    def test_win_rate_none_when_no_closed(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        assert trader.summary()["win_rate"] is None

    @pytest.mark.unit
    def test_win_rate_calculation(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _make_logger())
        trader._state["closed_positions"] = [
            {"outcome": "WIN"}, {"outcome": "WIN"}, {"outcome": "LOSS"}
        ]
        assert trader.summary()["win_rate"] == round(2 / 3, 3)


class TestIdempotencyFilter:
    """
    Verify the idempotency guard filtering logic used in run_paper_trade.py.

    The guard must block re-placement only for CONFIRMED positions. Positions
    with kalshi_order_status starting "failed:" are transient placement errors
    (503/429) and must NOT block a retry bet on a later cron run.
    """

    @staticmethod
    def _confirmed_tickers(open_positions: list) -> set:
        """Mirrors the set comprehension in run_paper_trade.py idempotency guard."""
        return {
            p["kalshi_ticker"]
            for p in open_positions
            if not str(p.get("kalshi_order_status", "")).startswith("failed:")
        }

    @pytest.mark.unit
    def test_confirmed_position_blocks_retry(self):
        pos = {**_make_position(_PAST_DATE), "kalshi_order_status": "resting"}
        result = self._confirmed_tickers([pos])
        assert pos["kalshi_ticker"] in result

    @pytest.mark.unit
    def test_local_only_position_blocks_retry(self):
        pos = {**_make_position(_PAST_DATE), "kalshi_order_status": "local_only"}
        result = self._confirmed_tickers([pos])
        assert pos["kalshi_ticker"] in result

    @pytest.mark.unit
    def test_missing_status_field_blocks_retry(self):
        pos = _make_position(_PAST_DATE)  # no kalshi_order_status key
        result = self._confirmed_tickers([pos])
        assert pos["kalshi_ticker"] in result

    @pytest.mark.unit
    def test_failed_503_does_not_block_retry(self):
        pos = {**_make_position(_PAST_DATE), "kalshi_order_status": "failed: http_503"}
        result = self._confirmed_tickers([pos])
        assert pos["kalshi_ticker"] not in result

    @pytest.mark.unit
    def test_failed_429_does_not_block_retry(self):
        pos = {**_make_position(_PAST_DATE), "kalshi_order_status": "failed: http_429"}
        result = self._confirmed_tickers([pos])
        assert pos["kalshi_ticker"] not in result

    @pytest.mark.unit
    def test_mixed_positions_only_confirmed_block(self):
        confirmed = {
            **_make_position(_PAST_DATE),
            "kalshi_ticker": "KXNBAPTS-26JUN08TICKER-A",
            "kalshi_order_status": "resting",
        }
        failed = {
            **_make_position(_PAST_DATE),
            "kalshi_ticker": "KXNBAPTS-26JUN08TICKER-B",
            "kalshi_order_status": "failed: http_503",
        }
        result = self._confirmed_tickers([confirmed, failed])
        assert "KXNBAPTS-26JUN08TICKER-A" in result
        assert "KXNBAPTS-26JUN08TICKER-B" not in result


class TestResolveExceptionLogging:
    @pytest.mark.unit
    def test_regular_season_exception_is_logged(self, tmp_path):
        """Exceptions from nba_api must be logged as warnings — not silently swallowed."""
        logger = _make_logger()
        trader = PaperTrader(tmp_path / "p.json", logger)
        trader._state["open_positions"].append(
            _make_position(game_date=_PAST_DATE, direction="YES",
                           threshold=20, size=50.0)
        )
        trader._state["bankroll_usd"] -= 50.0

        def raise_error(**kwargs):
            raise ConnectionError("403 Forbidden")

        with patch(_PGL, side_effect=raise_error):
            with patch("time.sleep"):
                with patch(_MOCK_TODAY, return_value=_TODAY):
                    trader.resolve_pending(session_id="TEST-SESSION")

        # Warning must have been called with the error detail
        warning_calls = logger.warning.call_args_list
        assert any(
            "403 Forbidden" in str(call) or "player_stats_fetch_failed" in str(call)
            for call in warning_calls
        ), f"Expected warning with error detail, got: {warning_calls}"

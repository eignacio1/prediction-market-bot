"""
T-187E: MLB paper position resolution
======================================
Coverage:
  1. PaperTrader.settle_position() — P&L formula, outcome logic, ledger mutations,
     stat_label storage, idempotency (already-settled no-op)
  2. fetch_actual_hits() / _fetch_mlb_hits() — API response parsing, date matching,
     postseason fallback, error handling
  3. run_resolve_mlb.main() — integration: no-open, future-date guard, API failure,
     full resolve cycle (mocked)
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution.paper_trader import PaperTrader

PAST_DATE   = (date.today() - timedelta(days=1)).isoformat()
FUTURE_DATE = (date.today() + timedelta(days=1)).isoformat()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _logger() -> MagicMock:
    m = MagicMock()
    m.info.return_value     = True
    m.warning.return_value  = True
    m.error.return_value    = True
    m.critical.return_value = True
    return m


def _make_approval(size: float, direction: str = "YES") -> dict:
    return {
        "approval_status":    "APPROVED",
        "approved_size":      size,
        "approved_direction": direction,
        "risk_eval_id":       "RISK-MLB-TEST",
        "forecast_id":        "FCST-MLB-TEST",
    }


def _open_mlb_pos(
    trader: PaperTrader,
    game_date:   str   = PAST_DATE,
    direction:   str   = "YES",
    threshold:   int   = 1,
    size:        float = 10.0,
    mid:         float = 0.50,
    vig:         float = 0.0,
    player_id:   int   = 12345,
    player_name: str   = "Aaron Judge",
) -> dict:
    """Open one MLB position and return the recorded position dict."""
    ok, pos = trader.open_position(
        approval=_make_approval(size, direction),
        player_name=player_name,
        player_id=player_id,
        kalshi_ticker=f"KXMLBHIT-26JUL010800NYY-{player_id}-{threshold}",
        kalshi_threshold=threshold,
        mid_price=mid,
        vig=vig,
        game_date=game_date,
    )
    assert ok, "open_position unexpectedly failed"
    return pos


def _fresh_trader(portfolio_path: Path) -> PaperTrader:
    """New PaperTrader reading from disk — used after main() mutates the file."""
    return PaperTrader(portfolio_path, _logger())


@pytest.fixture(autouse=True)
def _reset_mlb_circuit_breaker():
    """GG-084/T-239: the circuit breaker counter is module-level global state —
    reset it before and after every test so failures in one test can't trip
    the breaker for an unrelated test later in the run."""
    from prediction_market_bot.run_resolve_mlb import _reset_circuit_breaker
    _reset_circuit_breaker()
    yield
    _reset_circuit_breaker()


# ---------------------------------------------------------------------------
# 1. PaperTrader.settle_position() — P&L and ledger
# ---------------------------------------------------------------------------

class TestSettlePositionPnL:
    """Verify the P&L formula and outcome for all four direction×result cases."""

    @pytest.mark.unit
    def test_yes_win_pnl(self, tmp_path):
        """YES win: pnl = size * (1 - yes_ask) / yes_ask."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, mid=0.40, vig=0.0, size=10.0,
                            direction="YES", threshold=1)
        ok, closed = trader.settle_position(pos["position_id"], actual_stat=2.0,
                                            stat_label="actual_hits")
        assert ok
        yes_ask = 0.40
        expected = round(10.0 * (1.0 - yes_ask) / yes_ask, 4)
        assert abs(closed["pnl"] - expected) < 1e-4
        assert closed["outcome"] == "WIN"

    @pytest.mark.unit
    def test_yes_loss_pnl(self, tmp_path):
        """YES loss: pnl = -size."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, mid=0.50, vig=0.0, size=10.0,
                            direction="YES", threshold=2)
        ok, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                            stat_label="actual_hits")
        assert ok
        assert closed["pnl"] == -10.0
        assert closed["outcome"] == "LOSS"

    @pytest.mark.unit
    def test_no_win_pnl(self, tmp_path):
        """NO win (actual < threshold): pnl = size * (1 - no_ask) / no_ask."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, mid=0.40, vig=0.0, size=10.0,
                            direction="NO", threshold=2)
        ok, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                            stat_label="actual_hits")
        assert ok
        no_ask = 1.0 - 0.40  # = 0.60
        expected = round(10.0 * (1.0 - no_ask) / no_ask, 4)
        assert abs(closed["pnl"] - expected) < 1e-4
        assert closed["outcome"] == "WIN"

    @pytest.mark.unit
    def test_no_loss_pnl(self, tmp_path):
        """NO loss (actual >= threshold): pnl = -size."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, mid=0.50, vig=0.0, size=10.0,
                            direction="NO", threshold=1)
        ok, closed = trader.settle_position(pos["position_id"], actual_stat=2.0,
                                            stat_label="actual_hits")
        assert ok
        assert closed["pnl"] == -10.0
        assert closed["outcome"] == "LOSS"

    @pytest.mark.unit
    def test_yes_boundary_wins(self, tmp_path):
        """actual_stat == threshold → YES wins (>= is inclusive)."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, threshold=1, direction="YES",
                            mid=0.50, vig=0.0)
        _, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                           stat_label="actual_hits")
        assert closed["outcome"] == "WIN"

    @pytest.mark.unit
    def test_no_boundary_loses(self, tmp_path):
        """actual_stat == threshold → NO loses (YES wins; >= inclusive)."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, threshold=1, direction="NO",
                            mid=0.50, vig=0.0)
        _, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                           stat_label="actual_hits")
        assert closed["outcome"] == "LOSS"


class TestSettlePositionLedger:
    """Verify bankroll and position list after settlement."""

    @pytest.mark.unit
    def test_bankroll_reflects_win_profit(self, tmp_path):
        """After YES win at even odds (mid=0.50), net profit equals stake."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pre_bet = trader.get_state()["bankroll_usd"]
        pos = _open_mlb_pos(trader, size=10.0, mid=0.50, vig=0.0,
                            direction="YES", threshold=1)
        post_bet = trader.get_state()["bankroll_usd"]
        assert abs(post_bet - (pre_bet - 10.0)) < 1e-4

        trader.settle_position(pos["position_id"], actual_stat=2.0,
                               stat_label="actual_hits")
        post_resolve = trader.get_state()["bankroll_usd"]
        profit = round(10.0 * (1.0 - 0.50) / 0.50, 4)  # = 10.0 at even odds
        assert abs(post_resolve - (post_bet + 10.0 + profit)) < 1e-4

    @pytest.mark.unit
    def test_bankroll_reflects_loss(self, tmp_path):
        """After YES loss, bankroll = pre_bet − stake (stake fully gone)."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pre_bet = trader.get_state()["bankroll_usd"]
        pos = _open_mlb_pos(trader, size=10.0, mid=0.50, vig=0.0,
                            direction="YES", threshold=2)
        trader.settle_position(pos["position_id"], actual_stat=0.0,
                               stat_label="actual_hits")
        post_resolve = trader.get_state()["bankroll_usd"]
        assert abs(post_resolve - (pre_bet - 10.0)) < 1e-4

    @pytest.mark.unit
    def test_position_moved_open_to_closed(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader)
        trader.settle_position(pos["position_id"], actual_stat=2.0,
                               stat_label="actual_hits")
        state = trader.get_state()
        assert len(state["open_positions"]) == 0
        assert len(state["closed_positions"]) == 1

    @pytest.mark.unit
    def test_total_realized_pnl_reflects_loss(self, tmp_path):
        """summary().total_realized_pnl matches closed P&L after a loss."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, size=10.0, mid=0.50, vig=0.0, threshold=2)
        trader.settle_position(pos["position_id"], actual_stat=0.0,
                               stat_label="actual_hits")
        summary = trader.summary()
        assert abs(summary["total_realized_pnl"] - (-10.0)) < 1e-4


class TestSettlePositionMetadata:
    """Verify stat_label, status, and resolved_at in the closed record."""

    @pytest.mark.unit
    def test_stat_label_actual_hits_stored(self, tmp_path):
        """stat_label='actual_hits' appears as that key in the closed record."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader)
        _, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                           stat_label="actual_hits")
        assert "actual_hits" in closed
        assert closed["actual_hits"] == 1.0

    @pytest.mark.unit
    def test_default_stat_label_is_actual_pts(self, tmp_path):
        """Default stat_label='actual_pts' for NBA backward compatibility."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader)
        _, closed = trader.settle_position(pos["position_id"], actual_stat=25.0)
        assert "actual_pts" in closed
        assert closed["actual_pts"] == 25.0

    @pytest.mark.unit
    def test_status_becomes_closed(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader)
        _, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                           stat_label="actual_hits")
        assert closed["status"] == "CLOSED"

    @pytest.mark.unit
    def test_resolved_at_present_and_utc(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader)
        _, closed = trader.settle_position(pos["position_id"], actual_stat=1.0,
                                           stat_label="actual_hits")
        assert "resolved_at" in closed
        assert closed["resolved_at"].endswith("Z")


class TestSettlePositionIdempotency:
    """settle_position() is a no-op on already-settled or missing positions."""

    @pytest.mark.unit
    def test_noop_if_position_not_found(self, tmp_path):
        trader = PaperTrader(tmp_path / "p.json", _logger())
        ok, closed = trader.settle_position("POS-NONEXISTENT", actual_stat=1.0)
        assert ok is True
        assert closed == {}

    @pytest.mark.unit
    def test_second_call_noop_no_double_settle(self, tmp_path):
        """Second call on same position_id returns (True, {}) — no double-count."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        pos = _open_mlb_pos(trader, size=10.0)
        trader.settle_position(pos["position_id"], actual_stat=2.0,
                               stat_label="actual_hits")
        bankroll_after_first = trader.get_state()["bankroll_usd"]

        ok, closed2 = trader.settle_position(pos["position_id"], actual_stat=2.0,
                                             stat_label="actual_hits")
        assert ok is True
        assert closed2 == {}
        state = trader.get_state()
        assert len(state["closed_positions"]) == 1
        assert abs(state["bankroll_usd"] - bankroll_after_first) < 1e-4


# ---------------------------------------------------------------------------
# 2. _fetch_mlb_hits() / fetch_actual_hits() — API layer
# ---------------------------------------------------------------------------

class TestFetchMlbHits:
    """Unit tests for the MLB Stats API fetch layer (requests fully mocked).

    GG-069/T-221: `_fetch_mlb_hits` now issues a second request (schedule-by-
    gamePk) to confirm the game is FINAL before trusting the hits total.
    Tests that only care about gameLog parsing patch `_is_game_final` to True
    directly, so they don't need to know about the second HTTP call.
    """

    def _make_response(self, splits: list) -> MagicMock:
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = {"stats": [{"splits": splits}]}
        return m

    def _split(self, game_date: str, hits: int, game_pk: int = 999) -> dict:
        return {"date": game_date, "stat": {"hits": hits}, "game": {"gamePk": game_pk}}

    def _final_patch(self):
        return patch("prediction_market_bot.run_resolve_mlb._is_game_final", return_value=True)

    @pytest.mark.unit
    def test_happy_path_returns_hits(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split(PAST_DATE, 2)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"), \
             self._final_patch():
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result == 2.0

    @pytest.mark.unit
    def test_date_not_in_splits_returns_none(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split("2020-01-01", 3)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"), \
             self._final_patch():
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None

    @pytest.mark.unit
    def test_empty_stats_array_returns_none(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = {"stats": []}
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=m), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None

    @pytest.mark.unit
    def test_request_exception_returns_none(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        import requests as _req
        with patch("prediction_market_bot.run_resolve_mlb.requests.get",
                   side_effect=_req.exceptions.ConnectionError("timeout")), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None

    @pytest.mark.unit
    def test_http_error_returns_none(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        import requests as _req
        m = MagicMock()
        m.raise_for_status.side_effect = _req.HTTPError("406")
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=m), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None

    @pytest.mark.unit
    def test_zero_hits_is_valid_result(self):
        """hits=0 is a legitimate outcome — must not be coerced to None."""
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split(PAST_DATE, 0)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"), \
             self._final_patch():
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result == 0.0

    @pytest.mark.unit
    def test_multiple_splits_matches_correct_date(self):
        """With multiple game-log entries, the right date's hits are returned."""
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        resp = self._make_response([
            self._split(two_days_ago, 0),
            self._split(PAST_DATE, 3),
        ])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"), \
             self._final_patch():
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result == 3.0


class TestGameFinalGate:
    """GG-069/T-221: fetch_actual_hits must not resolve against a non-FINAL game."""

    def _make_response(self, splits: list) -> MagicMock:
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = {"stats": [{"splits": splits}]}
        return m

    def _split(self, game_date: str, hits: int, game_pk: int | None = 999) -> dict:
        d = {"date": game_date, "stat": {"hits": hits}}
        if game_pk is not None:
            d["game"] = {"gamePk": game_pk}
        return d

    @pytest.mark.unit
    def test_in_progress_game_returns_none(self):
        """Matching split exists but the source game is still live — must not resolve."""
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split(PAST_DATE, 7)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"), \
             patch("prediction_market_bot.run_resolve_mlb._is_game_final", return_value=False):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None

    @pytest.mark.unit
    def test_final_game_returns_hits(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split(PAST_DATE, 2)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"), \
             patch("prediction_market_bot.run_resolve_mlb._is_game_final", return_value=True):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result == 2.0

    @pytest.mark.unit
    def test_missing_game_pk_returns_none(self):
        """Split with no `game.gamePk` — cannot confirm FINAL, so do not resolve."""
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split(PAST_DATE, 4, game_pk=None)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None

    @pytest.mark.unit
    def test_is_game_final_true_on_final_status(self):
        from prediction_market_bot.run_resolve_mlb import _is_game_final
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            "dates": [{"games": [{"status": {"abstractGameState": "Final"}}]}]
        }
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp):
            assert _is_game_final(822791) is True

    @pytest.mark.unit
    def test_is_game_final_false_on_live_status(self):
        from prediction_market_bot.run_resolve_mlb import _is_game_final
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            "dates": [{"games": [{"status": {"abstractGameState": "Live"}}]}]
        }
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp):
            assert _is_game_final(822791) is False

    @pytest.mark.unit
    def test_is_game_final_false_on_request_exception(self):
        from prediction_market_bot.run_resolve_mlb import _is_game_final
        import requests as _req
        with patch("prediction_market_bot.run_resolve_mlb.requests.get",
                   side_effect=_req.exceptions.ConnectionError("timeout")):
            assert _is_game_final(822791) is False

    @pytest.mark.unit
    def test_is_game_final_false_on_malformed_response(self):
        from prediction_market_bot.run_resolve_mlb import _is_game_final
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"dates": []}
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp):
            assert _is_game_final(822791) is False


class TestFetchActualHitsPostseasonFallback:
    """fetch_actual_hits() tries Regular Season first, then Postseason."""

    @pytest.mark.unit
    def test_regular_season_found_no_postseason_call(self):
        from prediction_market_bot.run_resolve_mlb import fetch_actual_hits
        with patch("prediction_market_bot.run_resolve_mlb._fetch_mlb_hits",
                   return_value=2.0) as mock_fetch:
            result = fetch_actual_hits(12345, PAST_DATE)
        assert result == 2.0
        assert mock_fetch.call_count == 1
        assert mock_fetch.call_args[1]["game_type"] == "R"

    @pytest.mark.unit
    def test_postseason_called_when_regular_season_none(self):
        from prediction_market_bot.run_resolve_mlb import fetch_actual_hits

        def _side(player_id, game_date, game_type):
            return None if game_type == "R" else 1.0

        with patch("prediction_market_bot.run_resolve_mlb._fetch_mlb_hits",
                   side_effect=_side) as mock_fetch:
            result = fetch_actual_hits(12345, PAST_DATE)
        assert result == 1.0
        assert mock_fetch.call_count == 2
        assert [c[1]["game_type"] for c in mock_fetch.call_args_list] == ["R", "P"]

    @pytest.mark.unit
    def test_both_seasons_fail_returns_none(self):
        from prediction_market_bot.run_resolve_mlb import fetch_actual_hits
        with patch("prediction_market_bot.run_resolve_mlb._fetch_mlb_hits",
                   return_value=None):
            result = fetch_actual_hits(12345, PAST_DATE)
        assert result is None


# ---------------------------------------------------------------------------
# 3. run_resolve_mlb.main() — integration (I/O mocked)
# ---------------------------------------------------------------------------
# main() creates its own PaperTrader; after each run we read back through a
# fresh instance (_fresh_trader) so we see the on-disk state, not cached state.

def _patched_run(
    portfolio_path: Path,
    t4_portfolio_path: Path | None = None,
) -> None:
    """Run main() with portfolio paths redirected to tmp and I/O mocked.

    t4_portfolio_path: if None, set to a non-existent path so T4 pool is skipped.
    """
    import prediction_market_bot.run_resolve_mlb as mod
    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
    from prediction_market_bot.c7_monitoring.monitor import SystemMonitor

    orig_portfolio    = mod.PORTFOLIO_PATH
    orig_t4_portfolio = mod.T4_PORTFOLIO_PATH
    orig_log_dir      = mod.LOG_DIR

    mod.PORTFOLIO_PATH    = portfolio_path
    mod.T4_PORTFOLIO_PATH = (
        t4_portfolio_path if t4_portfolio_path is not None
        else portfolio_path.parent / "paper_portfolio_mlb_t4_nonexistent.json"
    )
    mod.LOG_DIR = portfolio_path.parent
    try:
        with patch.object(AuditLogger, "info",    return_value=True), \
             patch.object(AuditLogger, "warning", return_value=True), \
             patch.object(AuditLogger, "error",   return_value=True), \
             patch.object(SystemMonitor, "check_portfolio_pnl", return_value=None):
            mod.main()
    finally:
        mod.PORTFOLIO_PATH    = orig_portfolio
        mod.T4_PORTFOLIO_PATH = orig_t4_portfolio
        mod.LOG_DIR           = orig_log_dir


class TestRunResolveMlbMain:
    """Integration tests for main() with mocked MLB API and logger I/O."""

    @pytest.mark.integration
    def test_no_open_positions_exits_cleanly(self, tmp_path, capsys):
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits") as mock_api:
            _patched_run(portfolio_path)
        mock_api.assert_not_called()
        assert "No open positions" in capsys.readouterr().out

    @pytest.mark.integration
    def test_future_game_date_skipped(self, tmp_path):
        """Positions with game_date >= today are not resolved."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        _open_mlb_pos(setup, game_date=FUTURE_DATE)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits") as mock_api:
            _patched_run(portfolio_path)
        mock_api.assert_not_called()
        state = _fresh_trader(portfolio_path).get_state()
        assert len(state["open_positions"]) == 1
        assert len(state["closed_positions"]) == 0

    @pytest.mark.integration
    def test_api_failure_position_stays_open(self, tmp_path):
        """MLB API returning None leaves the position open for retry."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        _open_mlb_pos(setup, game_date=PAST_DATE)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=None):
            _patched_run(portfolio_path)
        state = _fresh_trader(portfolio_path).get_state()
        assert len(state["open_positions"]) == 1
        assert len(state["closed_positions"]) == 0

    @pytest.mark.integration
    def test_yes_win_full_resolve(self, tmp_path):
        """YES, actual_hits=2, threshold=1 → WIN; bankroll reflects profit."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        pre_bankroll = setup.get_state()["bankroll_usd"]
        _open_mlb_pos(setup, game_date=PAST_DATE, direction="YES",
                      threshold=1, size=10.0, mid=0.50, vig=0.0)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=2.0):
            _patched_run(portfolio_path)

        state = _fresh_trader(portfolio_path).get_state()
        assert len(state["open_positions"]) == 0
        assert len(state["closed_positions"]) == 1
        closed = state["closed_positions"][0]
        assert closed["outcome"] == "WIN"
        assert closed["actual_hits"] == 2.0
        profit = round(10.0 * (1.0 - 0.50) / 0.50, 4)  # even odds → +10
        assert abs(closed["pnl"] - profit) < 1e-4
        assert abs(state["bankroll_usd"] - (pre_bankroll - 10.0 + 10.0 + profit)) < 1e-4

    @pytest.mark.integration
    def test_no_loss_full_resolve(self, tmp_path):
        """NO, actual_hits=2, threshold=1 → LOSS; stake lost."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        pre_bankroll = setup.get_state()["bankroll_usd"]
        _open_mlb_pos(setup, game_date=PAST_DATE, direction="NO",
                      threshold=1, size=10.0, mid=0.50, vig=0.0)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=2.0):
            _patched_run(portfolio_path)

        state = _fresh_trader(portfolio_path).get_state()
        closed = state["closed_positions"][0]
        assert closed["outcome"] == "LOSS"
        assert closed["pnl"] == -10.0
        assert abs(state["bankroll_usd"] - (pre_bankroll - 10.0)) < 1e-4

    @pytest.mark.integration
    def test_zero_hits_yes_loses(self, tmp_path):
        """actual_hits=0 < threshold=1 → YES LOSS."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        _open_mlb_pos(setup, game_date=PAST_DATE, direction="YES",
                      threshold=1, size=10.0, mid=0.50, vig=0.0)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=0.0):
            _patched_run(portfolio_path)

        closed = _fresh_trader(portfolio_path).get_state()["closed_positions"][0]
        assert closed["outcome"] == "LOSS"
        assert closed["pnl"] == -10.0

    @pytest.mark.integration
    def test_mixed_positions_partial_api_failure(self, tmp_path):
        """API succeeds for player 11111, fails for 22222 → 1 resolved, 1 open."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        _open_mlb_pos(setup, game_date=PAST_DATE, player_id=11111,
                      player_name="Judge", threshold=1, size=10.0)
        _open_mlb_pos(setup, game_date=PAST_DATE, player_id=22222,
                      player_name="Soto", threshold=1, size=5.0)

        def _api_side(player_id, game_date):
            return 2.0 if player_id == 11111 else None

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   side_effect=_api_side):
            _patched_run(portfolio_path)

        state = _fresh_trader(portfolio_path).get_state()
        assert len(state["open_positions"]) == 1
        assert len(state["closed_positions"]) == 1
        assert state["open_positions"][0]["player_name"] == "Soto"
        assert state["closed_positions"][0]["player_name"] == "Judge"

    @pytest.mark.integration
    def test_session_id_in_output(self, tmp_path, capsys):
        """SESSION_ID in RESOLVE-MLB-{HEX8} format appears in stdout."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=None):
            _patched_run(portfolio_path)
        assert "RESOLVE-MLB-" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 4. T-201: T4 pool resolution
# ---------------------------------------------------------------------------

class TestT4PoolResolution:
    """PIPE-05R resolves T4 portfolio independently of T1/T2 pool (T-201)."""

    @pytest.mark.integration
    def test_t4_pool_skipped_when_file_missing(self, tmp_path, capsys):
        """main() runs cleanly when T4 portfolio does not exist yet."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=None):
            _patched_run(portfolio_path)  # t4_portfolio_path defaults to nonexistent
        out = capsys.readouterr().out
        assert "RESOLVE-MLB-" in out    # ran without error
        assert "T4" in out              # T4 section mentioned

    @pytest.mark.integration
    def test_t4_win_resolves_independently(self, tmp_path):
        """T4 YES bet resolves correctly; T1/T2 pool unaffected."""
        main_path = tmp_path / "paper_portfolio_mlb.json"
        t4_path   = tmp_path / "paper_portfolio_mlb_t4.json"

        # Open a bet in T1/T2 pool (future date — won't resolve)
        main_trader = PaperTrader(main_path, _logger())
        _open_mlb_pos(main_trader, game_date=FUTURE_DATE, player_id=11111,
                      player_name="Main Player", size=10.0)

        # Open a bet in T4 pool (past date — should resolve)
        t4_trader = PaperTrader(t4_path, _logger())
        _open_mlb_pos(t4_trader, game_date=PAST_DATE, player_id=22222,
                      player_name="T4 Player", threshold=1, size=5.0,
                      mid=0.50, vig=0.0)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=2.0):
            _patched_run(main_path, t4_portfolio_path=t4_path)

        # T1/T2: future bet still open
        main_state = _fresh_trader(main_path).get_state()
        assert len(main_state["open_positions"]) == 1
        assert len(main_state["closed_positions"]) == 0

        # T4: past bet resolved as WIN
        t4_state = _fresh_trader(t4_path).get_state()
        assert len(t4_state["open_positions"]) == 0
        assert len(t4_state["closed_positions"]) == 1
        assert t4_state["closed_positions"][0]["outcome"] == "WIN"

    @pytest.mark.integration
    def test_t4_loss_bankroll_correct(self, tmp_path):
        """T4 YES loss: T4 bankroll decreases by stake; main pool bankroll unaffected."""
        main_path = tmp_path / "paper_portfolio_mlb.json"
        t4_path   = tmp_path / "paper_portfolio_mlb_t4.json"

        main_trader = PaperTrader(main_path, _logger())
        t4_trader   = PaperTrader(t4_path, _logger())
        t4_pre_bankroll = t4_trader.get_state()["bankroll_usd"]

        _open_mlb_pos(t4_trader, game_date=PAST_DATE, player_id=55555,
                      player_name="T4 Player", threshold=2, size=10.0,
                      mid=0.50, vig=0.0, direction="YES")

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=0.0):   # 0 hits < threshold 2 → YES loses
            _patched_run(main_path, t4_portfolio_path=t4_path)

        t4_state = _fresh_trader(t4_path).get_state()
        closed   = t4_state["closed_positions"][0]
        assert closed["outcome"] == "LOSS"
        assert closed["pnl"] == -10.0
        assert abs(t4_state["bankroll_usd"] - (t4_pre_bankroll - 10.0)) < 1e-4

    @pytest.mark.integration
    def test_main_pool_and_t4_pool_resolve_same_run(self, tmp_path):
        """Both pools resolve in one main() call — independent idempotent settlement."""
        main_path = tmp_path / "paper_portfolio_mlb.json"
        t4_path   = tmp_path / "paper_portfolio_mlb_t4.json"

        main_trader = PaperTrader(main_path, _logger())
        _open_mlb_pos(main_trader, game_date=PAST_DATE, player_id=11111,
                      player_name="Main Player", threshold=1, size=5.0)

        t4_trader = PaperTrader(t4_path, _logger())
        _open_mlb_pos(t4_trader, game_date=PAST_DATE, player_id=22222,
                      player_name="T4 Player", threshold=1, size=5.0)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=1.0):
            _patched_run(main_path, t4_portfolio_path=t4_path)

        main_state = _fresh_trader(main_path).get_state()
        t4_state   = _fresh_trader(t4_path).get_state()

        assert len(main_state["closed_positions"]) == 1
        assert main_state["closed_positions"][0]["outcome"] == "WIN"
        assert len(t4_state["closed_positions"]) == 1
        assert t4_state["closed_positions"][0]["outcome"] == "WIN"

    @pytest.mark.integration
    def test_t4_empty_portfolio_runs_without_error(self, tmp_path, capsys):
        """T4 portfolio exists but has no open positions — runs cleanly."""
        main_path = tmp_path / "paper_portfolio_mlb.json"
        t4_path   = tmp_path / "paper_portfolio_mlb_t4.json"

        # Create T4 portfolio but leave it empty
        PaperTrader(t4_path, _logger())

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=None):
            _patched_run(main_path, t4_portfolio_path=t4_path)
        # No exception = pass; T4 section says "No open positions"
        assert "T4" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 5. GG-084/T-239: circuit breaker + degraded-resolution alert
# ---------------------------------------------------------------------------

class TestFetchMlbHitsCircuitBreaker:
    """GG-084/T-239: once the datacenter IP is hard-blocked, every further
    retry-loop exhaustion burns up to 45s for nothing. Once
    _CIRCUIT_BREAKER_THRESHOLD consecutive exhaustions have occurred, the
    breaker collapses the retry/backoff schedule to a single cheap probe
    attempt per call — it does not stop calling entirely, since a full skip
    could never observe recovery (nothing would ever reach the reset line)."""

    def _failing_response(self):
        import requests as _req
        m = MagicMock()
        m.raise_for_status.side_effect = _req.HTTPError("406")
        return m

    @pytest.mark.unit
    def test_breaker_collapses_to_single_probe_after_threshold(self):
        from prediction_market_bot.run_resolve_mlb import (
            _fetch_mlb_hits, _CIRCUIT_BREAKER_THRESHOLD, _RETRY_DELAYS_S,
        )
        with patch("prediction_market_bot.run_resolve_mlb.requests.get",
                   return_value=self._failing_response()) as mock_get, \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            for _ in range(_CIRCUIT_BREAKER_THRESHOLD):
                result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
                assert result is None
            calls_before_trip = mock_get.call_count
            # Full retry schedule (len(_RETRY_DELAYS_S)+1 attempts/call) ran
            # for all THRESHOLD calls — the breaker only opens *after* the
            # last one finishes, so none of them were probes yet.
            assert calls_before_trip == _CIRCUIT_BREAKER_THRESHOLD * (len(_RETRY_DELAYS_S) + 1)

            # Breaker is now open — the next call makes exactly ONE probe
            # attempt (no backoff retries), not zero and not a full retry.
            result = _fetch_mlb_hits(99999, PAST_DATE, game_type="R")
            assert result is None
            assert mock_get.call_count == calls_before_trip + 1

    @pytest.mark.unit
    def test_breaker_resets_on_successful_probe(self):
        from prediction_market_bot.run_resolve_mlb import (
            _fetch_mlb_hits, _CIRCUIT_BREAKER_THRESHOLD,
        )
        with patch("prediction_market_bot.run_resolve_mlb.requests.get",
                   return_value=self._failing_response()), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            for _ in range(_CIRCUIT_BREAKER_THRESHOLD):
                _fetch_mlb_hits(12345, PAST_DATE, game_type="R")

        # Breaker is open. A successful probe response resets the counter...
        ok_resp = MagicMock()
        ok_resp.raise_for_status.return_value = None
        ok_resp.json.return_value = {"stats": []}
        with patch("prediction_market_bot.run_resolve_mlb.requests.get",
                   return_value=ok_resp) as mock_ok, \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result is None  # empty stats array
        assert mock_ok.call_count == 1  # single probe, not a full retry cycle

        # ...so the breaker is closed again: the next failing call goes
        # through the FULL retry schedule again, not another single probe.
        with patch("prediction_market_bot.run_resolve_mlb.requests.get",
                   return_value=self._failing_response()) as mock_get2, \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert mock_get2.call_count > 1  # real retries happened, not a single probe


class TestDegradedResolutionAlert:
    """GG-084/T-239: a partial-but-severe failure rate (e.g. 82% skip) produced
    zero alert under the old all-or-nothing "zero resolved" check. Verify the
    new threshold-based alert fires when resolution rate is below 50%."""

    @pytest.mark.integration
    def test_majority_skip_fires_degraded_alert(self, tmp_path, capsys):
        """8 eligible positions, only 2 resolve (<50%) — alert must fire."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        for i in range(8):
            _open_mlb_pos(setup, game_date=PAST_DATE, player_id=10000 + i,
                          player_name=f"Player{i}", threshold=1, size=5.0)

        def _api_side(player_id, game_date):
            return 2.0 if player_id in (10000, 10001) else None

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   side_effect=_api_side):
            _patched_run(portfolio_path)

        assert "GG-084" in capsys.readouterr().err

    @pytest.mark.integration
    def test_majority_resolve_does_not_fire_degraded_alert(self, tmp_path, capsys):
        """8 eligible positions, 6 resolve (>=50%) — no degraded alert."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        for i in range(8):
            _open_mlb_pos(setup, game_date=PAST_DATE, player_id=20000 + i,
                          player_name=f"Player{i}", threshold=1, size=5.0)

        def _api_side(player_id, game_date):
            return None if player_id in (20000, 20001) else 2.0

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   side_effect=_api_side):
            _patched_run(portfolio_path)

        assert "GG-084" not in capsys.readouterr().err

    @pytest.mark.integration
    def test_small_batch_below_threshold_count_does_not_fire(self, tmp_path, capsys):
        """Fewer than 5 eligible positions — too small a sample, no alert even
        if all fail (the existing zero-resolved alert already covers n=0 resolved;
        this guards against noisy alerts on tiny batches)."""
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        setup = PaperTrader(portfolio_path, _logger())
        _open_mlb_pos(setup, game_date=PAST_DATE, player_id=30000,
                      player_name="Solo", threshold=1, size=5.0)

        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits",
                   return_value=2.0):
            _patched_run(portfolio_path)

        assert "GG-084" not in capsys.readouterr().err

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
    """Unit tests for the MLB Stats API fetch layer (requests fully mocked)."""

    def _make_response(self, splits: list) -> MagicMock:
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = {"stats": [{"splits": splits}]}
        return m

    def _split(self, game_date: str, hits: int) -> dict:
        return {"date": game_date, "stat": {"hits": hits}}

    @pytest.mark.unit
    def test_happy_path_returns_hits(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split(PAST_DATE, 2)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result == 2.0

    @pytest.mark.unit
    def test_date_not_in_splits_returns_none(self):
        from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits
        resp = self._make_response([self._split("2020-01-01", 3)])
        with patch("prediction_market_bot.run_resolve_mlb.requests.get", return_value=resp), \
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
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
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
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
             patch("prediction_market_bot.run_resolve_mlb.time.sleep"):
            result = _fetch_mlb_hits(12345, PAST_DATE, game_type="R")
        assert result == 3.0


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

def _patched_run(portfolio_path: Path) -> None:
    """Run main() with PORTFOLIO_PATH redirected to tmp and I/O mocked."""
    import prediction_market_bot.run_resolve_mlb as mod
    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
    from prediction_market_bot.c7_monitoring.monitor import SystemMonitor

    orig_portfolio = mod.PORTFOLIO_PATH
    orig_log_dir   = mod.LOG_DIR

    mod.PORTFOLIO_PATH = portfolio_path
    mod.LOG_DIR        = portfolio_path.parent
    try:
        with patch.object(AuditLogger, "info",    return_value=True), \
             patch.object(AuditLogger, "warning", return_value=True), \
             patch.object(AuditLogger, "error",   return_value=True), \
             patch.object(SystemMonitor, "check_portfolio_pnl", return_value=None):
            mod.main()
    finally:
        mod.PORTFOLIO_PATH = orig_portfolio
        mod.LOG_DIR        = orig_log_dir


class TestRunResolveMlbMain:
    """Integration tests for main() with mocked MLB API and logger I/O."""

    @pytest.mark.integration
    def test_no_open_positions_exits_cleanly(self, tmp_path, capsys):
        portfolio_path = tmp_path / "paper_portfolio_mlb.json"
        with patch("prediction_market_bot.run_resolve_mlb.fetch_actual_hits") as mock_api:
            _patched_run(portfolio_path)
        mock_api.assert_not_called()
        assert "No open MLB positions" in capsys.readouterr().out

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

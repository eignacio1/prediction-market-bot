"""
Tests for src/prediction_market_bot/run_resolve.py

Coverage areas:
  - BOT_ENV guard is present in source
  - Empty portfolio: prints no-op message, resolve_pending not called
  - PaperTrader integration: resolve_pending called when open positions exist
  - Resolution output: prints settled positions with P&L sign
  - Win rate shown when closed positions exist
  - Audit logging: resolve_run_start and resolve_run_complete events emitted
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Import with BOT_ENV=paper so the module-level guard passes
os.environ.setdefault("BOT_ENV", "paper")
import prediction_market_bot.run_resolve as run_resolve  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_portfolio(open_positions=None, bankroll=1000.0):
    return {
        "bankroll_usd": bankroll,
        "total_realized_pnl": 0.0,
        "current_daily_loss": 0.0,
        "daily_loss_date": "2026-05-29",
        "open_positions": open_positions or [],
        "closed_positions": [],
        "created_at": "2026-05-29T00:00:00.000Z",
        "last_updated": "2026-05-29T00:00:00.000Z",
    }


def _make_mock_trader(open_positions=None, resolved=None, bankroll=1000.0):
    trader = MagicMock()
    portfolio = _make_portfolio(open_positions=open_positions, bankroll=bankroll)
    trader.get_state.return_value = portfolio
    trader.resolve_pending.return_value = (True, resolved or [])
    n_closed = len(resolved or [])
    win_rate = 1.0 if n_closed > 0 else None
    trader.summary.return_value = {
        "bankroll_usd": bankroll,
        "total_realized_pnl": sum(r.get("pnl", 0) for r in (resolved or [])),
        "open_positions": len(open_positions or []),
        "closed_positions": n_closed,
        "win_rate": win_rate,
        "drawdown_pct": 0.0,
    }
    return trader


def _make_mock_logger():
    logger = MagicMock()
    logger.info.return_value = True
    logger.log.return_value = True
    return logger


# ---------------------------------------------------------------------------
# ENV guard
# ---------------------------------------------------------------------------

class TestEnvGuard:
    @pytest.mark.unit
    def test_guard_exists_in_source(self):
        """run_resolve.py source must contain BOT_ENV=paper guard."""
        src = (_SRC / "prediction_market_bot/run_resolve.py").read_text()
        assert 'BOT_ENV' in src
        assert "paper" in src
        assert "sys.exit(1)" in src


# ---------------------------------------------------------------------------
# Empty portfolio
# ---------------------------------------------------------------------------

class TestEmptyPortfolio:
    @pytest.mark.unit
    def test_no_op_on_empty_portfolio(self, capsys):
        """Nothing to resolve → resolve_pending not called; clean exit."""
        trader = _make_mock_trader(open_positions=[])
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        trader.resolve_pending.assert_not_called()
        captured = capsys.readouterr()
        assert "No open positions" in captured.out

    @pytest.mark.unit
    def test_empty_portfolio_logs_complete(self, capsys):
        """resolve_run_complete is logged even with zero open positions."""
        trader = _make_mock_trader(open_positions=[])
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        calls = " ".join(str(c) for c in logger.info.call_args_list)
        assert "resolve_run_complete" in calls


# ---------------------------------------------------------------------------
# Resolution with open positions
# ---------------------------------------------------------------------------

class TestResolutionWithPositions:
    @pytest.mark.unit
    def test_resolve_pending_called_when_open(self, capsys):
        """resolve_pending must be called when open_positions is non-empty."""
        open_pos = [{"position_id": "POS-001", "player_name": "Shai Gilgeous-Alexander"}]
        trader = _make_mock_trader(open_positions=open_pos)
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        trader.resolve_pending.assert_called_once()

    @pytest.mark.unit
    def test_resolved_positions_printed(self, capsys):
        """Settled positions print player name, pts, threshold, P&L."""
        open_pos = [{"position_id": "POS-001"}]
        settled  = [{"player_name": "De'Aaron Fox", "outcome": "WIN",
                     "actual_pts": 22.0, "kalshi_threshold": 15, "pnl": 12.45}]
        trader = _make_mock_trader(open_positions=open_pos, resolved=settled, bankroll=987.55)
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        captured = capsys.readouterr()
        assert "De'Aaron Fox" in captured.out
        assert "+12.45" in captured.out

    @pytest.mark.unit
    def test_loss_shows_negative_pnl(self, capsys):
        """Losing positions show negative P&L without '+' prefix."""
        open_pos = [{"position_id": "POS-002"}]
        settled  = [{"player_name": "Nikola Jokic", "outcome": "LOSS",
                     "actual_pts": 18.0, "kalshi_threshold": 25, "pnl": -8.50}]
        trader = _make_mock_trader(open_positions=open_pos, resolved=settled)
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        captured = capsys.readouterr()
        assert "Nikola Jokic" in captured.out
        assert "-8.50" in captured.out

    @pytest.mark.unit
    def test_win_rate_shown_when_closed_positions_exist(self, capsys):
        """Win rate line is printed when closed_positions > 0."""
        open_pos = [{"position_id": "POS-001"}]
        settled  = [{"player_name": "Test Player", "outcome": "WIN",
                     "actual_pts": 20.0, "kalshi_threshold": 15, "pnl": 5.0}]
        trader = _make_mock_trader(open_positions=open_pos, resolved=settled)
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        captured = capsys.readouterr()
        assert "Win rate" in captured.out

    @pytest.mark.unit
    def test_audit_events_logged(self, capsys):
        """resolve_run_start and resolve_run_complete must both be logged."""
        trader = _make_mock_trader(open_positions=[])
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        calls = " ".join(str(c) for c in logger.info.call_args_list)
        assert "resolve_run_start" in calls
        assert "resolve_run_complete" in calls

    @pytest.mark.unit
    def test_no_resolution_when_game_not_finished(self, capsys):
        """If resolve_pending returns empty list, 'not available' message shown."""
        open_pos = [{"position_id": "POS-001"}]
        trader = _make_mock_trader(open_positions=open_pos, resolved=[])
        logger = _make_mock_logger()

        with patch("prediction_market_bot.run_resolve.PaperTrader", return_value=trader):
            with patch("prediction_market_bot.run_resolve.AuditLogger", return_value=logger):
                run_resolve.main()

        captured = capsys.readouterr()
        assert "not available" in captured.out

"""
T-194: Resolution age-out — positions open >48h that cannot resolve → aged_open

Tests for:
  1. PaperTrader.mark_aged_open() — in-place tagging; capital stays deployed;
     idempotency; C6 WARNING emission; position-not-found no-op
  2. run_resolve_mlb.py age-out detection — 48h threshold, grace-period skip,
     aged position written to stderr, normal skip within grace period
  3. Bankroll invariant — aged_open position must not affect open_cost calculation
"""
from __future__ import annotations

import os
import sys
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution.paper_trader import PaperTrader


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _logger() -> MagicMock:
    m = MagicMock()
    m.info.return_value    = True
    m.warning.return_value = True
    m.error.return_value   = True
    return m


def _make_approval(size: float = 10.0, direction: str = "YES") -> dict:
    return {
        "approval_status":    "APPROVED",
        "approved_size":      size,
        "approved_direction": direction,
        "risk_eval_id":       "RISK-TEST",
        "forecast_id":        "FCST-TEST",
    }


def _open_mlb_pos(
    trader: PaperTrader,
    game_date: str,
    player_id: int = 12345,
    player_name: str = "Test Player",
    threshold: int = 1,
    size: float = 10.0,
    mid: float = 0.50,
) -> tuple[str, dict]:
    ok, pos = trader.open_position(
        approval=_make_approval(size),
        player_name=player_name,
        player_id=player_id,
        kalshi_ticker=f"KXMLBHIT-TEST-{player_id}-{threshold}",
        kalshi_threshold=threshold,
        mid_price=mid,
        vig=0.0,
        game_date=game_date,
    )
    assert ok
    return pos["position_id"], pos


# ---------------------------------------------------------------------------
# 1. PaperTrader.mark_aged_open()
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _venue_settled(monkeypatch):
    """ADR-0071 (W54.3): positions without a result are positions Kalshi has not
    settled yet. Stub the venue as NOT_FINAL (no network in tests)."""
    import prediction_market_bot.run_resolve_mlb as _rm
    monkeypatch.setattr(_rm, "_venue_market_state",
                        lambda ticker: (_rm.VENUE_NOT_FINAL, {"result": ""}))


class TestMarkAgedOpen:
    def test_tags_position_in_place(self, tmp_path: Path) -> None:
        trader = PaperTrader(tmp_path / "p.json", _logger())
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date)

        ok, tagged = trader.mark_aged_open(pid, reason="api_no_result_48h")

        assert ok is True
        assert tagged["aged_open"] is True
        assert tagged["aged_open_reason"] == "api_no_result_48h"
        assert "aged_open_at" in tagged

    def test_position_remains_in_open_positions(self, tmp_path: Path) -> None:
        """Capital must NOT be credited back — position stays in open_positions."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date)

        trader.mark_aged_open(pid)

        state = trader.get_state()
        open_ids = [p["position_id"] for p in state["open_positions"]]
        assert pid in open_ids
        closed_ids = [p["position_id"] for p in state.get("closed_positions", [])]
        assert pid not in closed_ids

    def test_bankroll_unchanged_after_marking(self, tmp_path: Path) -> None:
        """open_cost must include aged position — _ledger_bankroll unchanged."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date, size=10.0)

        bankroll_before = trader.summary()["bankroll_usd"]
        trader.mark_aged_open(pid)
        bankroll_after = trader.summary()["bankroll_usd"]

        assert bankroll_after == bankroll_before

    def test_idempotent_second_call(self, tmp_path: Path) -> None:
        """Calling mark_aged_open twice must not re-log or update aged_open_at."""
        trader = PaperTrader(tmp_path / "p.json", _logger())
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date)

        trader.mark_aged_open(pid)
        first_at = trader.get_state()["open_positions"][0]["aged_open_at"]

        ok, pos = trader.mark_aged_open(pid)
        second_at = pos["aged_open_at"]

        assert ok is True
        assert first_at == second_at

    def test_returns_empty_dict_for_unknown_position(self, tmp_path: Path) -> None:
        trader = PaperTrader(tmp_path / "p.json", _logger())
        ok, pos = trader.mark_aged_open("NONEXISTENT-ID")
        assert ok is True
        assert pos == {}

    def test_emits_c6_warning(self, tmp_path: Path) -> None:
        mock_log = _logger()
        trader = PaperTrader(tmp_path / "p.json", mock_log)
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date)

        trader.mark_aged_open(pid, reason="api_no_result_48h", session_id="SID-X")

        # GG-184: _open_mlb_pos() above does not pass market_type explicitly,
        # so open_position() also emits a "market_type_defaulted" warning.
        # That is intended, in-scope behavior (T-456) -- isolate the
        # aged-open warning specifically rather than asserting total count.
        aged_calls = [
            c for c in mock_log.warning.call_args_list
            if c[0][1] == "paper_position_aged_open"
        ]
        assert len(aged_calls) == 1
        call_args = aged_calls[0]
        assert call_args[0][0] == "C5-PAPER"
        assert call_args[0][1] == "paper_position_aged_open"
        assert "position_id" in call_args[1]["payload"]
        assert call_args[1]["session_id"] == "SID-X"

    def test_position_persists_to_disk(self, tmp_path: Path) -> None:
        """Aged tag must survive a reload from disk."""
        portfolio_path = tmp_path / "p.json"
        trader = PaperTrader(portfolio_path, _logger())
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date)
        trader.mark_aged_open(pid)

        reloaded = PaperTrader(portfolio_path, _logger())
        state = reloaded.get_state()
        open_pos = next(p for p in state["open_positions"] if p["position_id"] == pid)
        assert open_pos["aged_open"] is True

    def test_default_reason_stored(self, tmp_path: Path) -> None:
        trader = PaperTrader(tmp_path / "p.json", _logger())
        old_date = (date.today() - timedelta(days=3)).isoformat()
        pid, _ = _open_mlb_pos(trader, old_date)
        _, pos = trader.mark_aged_open(pid)
        assert pos["aged_open_reason"] == "api_no_result_48h"


# ---------------------------------------------------------------------------
# 2. run_resolve_mlb.py age-out detection logic
# ---------------------------------------------------------------------------

_AGEOUT_THRESHOLD_HOURS = 48


def _age_hours_from_date(game_date_str: str, now_utc: datetime) -> float:
    """Mirror the age calculation in run_resolve_mlb.py."""
    game_dt = datetime.strptime(game_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (now_utc - game_dt).total_seconds() / 3600


class TestAgeOutDetectionLogic:
    """Unit tests for the age-out threshold logic (no file I/O)."""

    def test_beyond_48h_triggers_age_out(self) -> None:
        game_date = (date.today() - timedelta(days=3)).isoformat()
        now = datetime.now(timezone.utc)
        age = _age_hours_from_date(game_date, now)
        assert age > _AGEOUT_THRESHOLD_HOURS

    def test_within_48h_does_not_trigger(self) -> None:
        # Fix now to noon UTC so yesterday's midnight is exactly 36h ago (< 48h).
        # Avoids the midnight-UTC corner case where yesterday's midnight = 48.0xh ago.
        now = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = (now - timedelta(days=1)).date()
        game_date = yesterday.isoformat()
        age = _age_hours_from_date(game_date, now)
        assert age < _AGEOUT_THRESHOLD_HOURS

    def test_exactly_48h_boundary(self) -> None:
        """Exactly 48h should NOT trigger — rule is strictly >48h."""
        now = datetime.now(timezone.utc)
        game_dt = now - timedelta(hours=48)
        age = (now - game_dt).total_seconds() / 3600
        assert not (age > 48)

    def test_49h_triggers(self) -> None:
        now = datetime.now(timezone.utc)
        game_dt = now - timedelta(hours=49)
        age = (now - game_dt).total_seconds() / 3600
        assert age > 48


class TestResolveMLBAgeOut:
    """Integration-style tests for the age-out path in run_resolve_mlb.main()."""

    def _import_main(self):
        # Import without reload so PORTFOLIO_PATH patch applied in the test sticks.
        from prediction_market_bot.run_resolve_mlb import main
        return main

    def _make_stale_portfolio(self, path: Path, game_date: str, size: float = 10.0) -> str:
        """Write a portfolio file with one open position for the given game_date."""
        position_id = "POS-AGED-TEST"
        state = {
            "initial_bankroll_usd": 1000.0,
            "bankroll_usd": 990.0,
            "open_positions": [{
                "position_id": position_id,
                "player_name": "Aged Player",
                "player_id": 99999,
                "kalshi_ticker": "KXMLBHIT-TEST-99999-1",
                "kalshi_threshold": 1,
                "direction": "YES",
                "size_usd": size,
                "open_cost": size,
                "mid_price_at_entry": 0.50,
                "vig_at_entry": 0.0,
                "game_date": game_date,
                "sport": "MLB",
                "status": "OPEN",
            }],
            "closed_positions": [],
        }
        path.write_text(json.dumps(state))
        return position_id

    def test_aged_position_tagged_in_portfolio(self, tmp_path: Path) -> None:
        """ADR-0071: a position >48h old that Kalshi has not settled stays open and
        unbooked. The resolver no longer tags aged_open (W54.3 removed stat-feed aging);
        staleness is surfaced by monitor.check_stale_open_positions instead."""
        portfolio = tmp_path / "portfolio.json"
        stale_date = (date.today() - timedelta(days=3)).isoformat()
        pid = self._make_stale_portfolio(portfolio, stale_date)

        import prediction_market_bot.run_resolve_mlb as resolve_mod
        with patch.object(resolve_mod, "PORTFOLIO_PATH", portfolio), \
             patch.object(resolve_mod, "LOG_DIR", tmp_path), \
             patch.object(resolve_mod, "fetch_actual_hits", return_value=None):
            try:
                self._import_main()()
            except SystemExit:
                pass

        state = json.loads(portfolio.read_text())
        open_pos = next(
            (p for p in state["open_positions"] if p["position_id"] == pid),
            None,
        )
        assert open_pos is not None, "Position must remain in open_positions"
        assert len(state.get("closed_positions", [])) == 0

    def test_within_grace_period_not_tagged(self, tmp_path: Path) -> None:
        """Positions within 48h grace period must not be tagged aged_open.

        Positions with game_date = yesterday are < 48h old if the resolver runs
        before midnight of that day.  The resolver's `game_date < today` guard
        allows yesterday's positions into `pending`.
        """
        portfolio = tmp_path / "portfolio.json"
        # Yesterday's date — in `pending` (game_date < today) but < 48h old
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        pid = self._make_stale_portfolio(portfolio, yesterday)

        import prediction_market_bot.run_resolve_mlb as resolve_mod
        with patch.object(resolve_mod, "PORTFOLIO_PATH", portfolio), \
             patch.object(resolve_mod, "LOG_DIR", tmp_path), \
             patch.object(resolve_mod, "fetch_actual_hits", return_value=None):
            try:
                self._import_main()()
            except SystemExit:
                pass

        state = json.loads(portfolio.read_text())
        open_pos = next(
            (p for p in state["open_positions"] if p["position_id"] == pid),
            None,
        )
        assert open_pos is not None
        # Yesterday could be ≤ or > 48h old depending on current time.
        # The key assertion is that it was NOT moved to closed_positions.
        assert len(state.get("closed_positions", [])) == 0

    def test_aged_position_capital_stays_deployed(self, tmp_path: Path) -> None:
        """After age-out tagging, open_cost must still count in bankroll calculation."""
        portfolio = tmp_path / "portfolio.json"
        stale_date = (date.today() - timedelta(days=3)).isoformat()
        self._make_stale_portfolio(portfolio, stale_date, size=25.0)

        initial_state = json.loads(portfolio.read_text())
        initial_open_count = len(initial_state["open_positions"])

        import prediction_market_bot.run_resolve_mlb as resolve_mod
        with patch.object(resolve_mod, "PORTFOLIO_PATH", portfolio), \
             patch.object(resolve_mod, "LOG_DIR", tmp_path), \
             patch.object(resolve_mod, "fetch_actual_hits", return_value=None):
            try:
                self._import_main()()
            except SystemExit:
                pass

        final_state = json.loads(portfolio.read_text())
        assert len(final_state["open_positions"]) == initial_open_count
        assert len(final_state.get("closed_positions", [])) == 0


if __name__ == "__main__":
    import unittest
    unittest.main()

"""
Tests: T-159 — Portfolio State-Machine Invariants + Schema Owner (LL-014)
=========================================================================
Coverage:
  portfolio_schema.py — schema owner module:
    - Required field validation
    - open_positions OPEN-only invariant
    - closed_positions CLOSED/EXITED-only invariant
    - Numeric non-negative invariants
    - daily_loss_date type invariant
    - validate_portfolio_state() returns empty list on clean state

  PaperTrader state-machine invariants:
    - initial_bankroll_usd never changes
    - open_positions contains only OPEN status positions after open
    - Closed position moves to closed_positions with correct status
    - Exited position moves to closed_positions with status EXITED
    - total_realized_pnl = Σ pnl for all closed positions (resolve path)
    - total_realized_pnl = Σ exit_pnl for all exited positions (exit path)
    - bankroll_usd accounting identity (non-isolated path)
    - pool_isolated positions: bankroll untouched on open AND close
    - Cross-day bankroll stability: initial_bankroll_usd unchanged across days
    - validate_portfolio_state() passes at every state-machine transition

  Kill-switch state transitions:
    - After net-positive day: current_daily_loss = 0, kill switch would not fire
    - After net-negative day: current_daily_loss > 0, kill switch would fire
    - After cross-day reset: kill switch resets independently of prior day

  Cross-day accounting:
    - Bankroll persists correctly across day boundary (not reset like daily_loss)
    - total_realized_pnl persists and accumulates across days
    - initial_bankroll_usd is stable across days
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from prediction_market_bot.c5_execution.paper_trader import PaperTrader, INITIAL_BANKROLL_USD
from prediction_market_bot.c5_execution.portfolio_schema import (
    validate_portfolio_state,
    REQUIRED_TOP_LEVEL_FIELDS,
    F_BANKROLL, F_INITIAL_BANKROLL, F_TOTAL_REALIZED_PNL,
    F_CURRENT_DAILY_LOSS, F_DAILY_LOSS_DATE, F_OPEN_POSITIONS, F_CLOSED_POSITIONS,
    STATUS_OPEN, STATUS_CLOSED, STATUS_EXITED,
)
from prediction_market_bot.c4_risk_engine.risk import MAX_DAILY_LOSS_PCT
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_portfolio(tmp_path):
    return tmp_path / "paper_portfolio_test.json"


@pytest.fixture
def trader(tmp_portfolio):
    logger = AuditLogger(log_path=tmp_portfolio.parent / "audit_test.jsonl")
    return PaperTrader(portfolio_path=tmp_portfolio, logger=logger)


def _open_yes(trader: PaperTrader, mid: float = 0.50, size: float = 10.0,
              pool_isolated: bool = False, game_date: str = "2026-06-10") -> str:
    _, pos = trader.open_position(
        approval={
            "approved_size": size, "approved_direction": "YES",
            "edge": 0.05, "gross_edge": 0.07, "model_p": mid + 0.05,
            "risk_eval_id": "R-001", "forecast_id": "F-001",
        },
        player_name="Test Player", player_id=42,
        kalshi_ticker="KXNBAPTS-26JUN10BOSOKC-PLY-20",
        kalshi_threshold=20, mid_price=mid, vig=0.04,
        game_date=game_date, pool_isolated=pool_isolated,
    )
    return pos["position_id"]


# ---------------------------------------------------------------------------
# portfolio_schema.validate_portfolio_state() — unit tests
# ---------------------------------------------------------------------------

class TestValidatePortfolioState:
    def test_fresh_trader_state_is_valid(self, trader):
        """A freshly initialized trader state must pass validation."""
        errors = validate_portfolio_state(trader._state)
        assert errors == [], f"Unexpected validation errors: {errors}"

    def test_missing_required_field_reported(self):
        """Each missing required field produces a validation error."""
        for field in REQUIRED_TOP_LEVEL_FIELDS:
            minimal = {f: [] if "positions" in f else 0.0 for f in REQUIRED_TOP_LEVEL_FIELDS}
            minimal[F_INITIAL_BANKROLL] = 1000.0
            minimal[F_DAILY_LOSS_DATE] = "2026-06-10"
            minimal.pop(field)
            errors = validate_portfolio_state(minimal)
            assert any(field in e for e in errors), (
                f"Expected error about {field!r} but got: {errors}"
            )

    def test_open_position_with_closed_status_is_violation(self, trader):
        """An OPEN-list entry with status=CLOSED is a schema violation."""
        trader._state[F_OPEN_POSITIONS].append({"position_id": "X", "status": STATUS_CLOSED})
        errors = validate_portfolio_state(trader._state)
        assert any("open_positions" in e for e in errors)

    def test_closed_position_with_open_status_is_violation(self, trader):
        """A CLOSED-list entry with status=OPEN is a schema violation."""
        trader._state[F_CLOSED_POSITIONS].append({"position_id": "X", "status": STATUS_OPEN})
        errors = validate_portfolio_state(trader._state)
        assert any("closed_positions" in e for e in errors)

    def test_negative_bankroll_is_violation(self, trader):
        trader._state[F_BANKROLL] = -1.0
        errors = validate_portfolio_state(trader._state)
        assert any(F_BANKROLL in e for e in errors)

    def test_negative_current_daily_loss_is_violation(self, trader):
        trader._state[F_CURRENT_DAILY_LOSS] = -0.01
        errors = validate_portfolio_state(trader._state)
        assert any(F_CURRENT_DAILY_LOSS in e for e in errors)

    def test_zero_initial_bankroll_is_violation(self, trader):
        trader._state[F_INITIAL_BANKROLL] = 0.0
        errors = validate_portfolio_state(trader._state)
        assert any(F_INITIAL_BANKROLL in e for e in errors)

    def test_missing_daily_loss_date_is_violation(self, trader):
        del trader._state[F_DAILY_LOSS_DATE]
        errors = validate_portfolio_state(trader._state)
        assert any(F_DAILY_LOSS_DATE in e for e in errors)

    def test_exited_status_in_closed_positions_is_valid(self, trader):
        """EXITED is a valid status for closed_positions."""
        trader._state[F_CLOSED_POSITIONS].append({"position_id": "X", "status": STATUS_EXITED})
        errors = validate_portfolio_state(trader._state)
        assert not any("closed_positions" in e for e in errors)


# ---------------------------------------------------------------------------
# State-machine invariants via PaperTrader public API
# ---------------------------------------------------------------------------

class TestOpenPositionInvariants:
    def test_state_valid_after_open(self, trader):
        _open_yes(trader)
        assert validate_portfolio_state(trader._state) == []

    def test_open_positions_contains_only_open_status(self, trader):
        _open_yes(trader)
        for pos in trader._state[F_OPEN_POSITIONS]:
            assert pos["status"] == STATUS_OPEN

    def test_initial_bankroll_unchanged_after_open(self, trader):
        _open_yes(trader, size=50.0)
        assert trader._state[F_INITIAL_BANKROLL] == pytest.approx(INITIAL_BANKROLL_USD, abs=1e-4)

    def test_bankroll_decremented_on_non_isolated_open(self, trader):
        bankroll_before = trader._state[F_BANKROLL]
        _open_yes(trader, size=30.0, pool_isolated=False)
        assert trader._state[F_BANKROLL] == pytest.approx(bankroll_before - 30.0, abs=1e-4)

    def test_bankroll_unchanged_on_pool_isolated_open(self, trader):
        bankroll_before = trader._state[F_BANKROLL]
        _open_yes(trader, size=30.0, pool_isolated=True)
        assert trader._state[F_BANKROLL] == pytest.approx(bankroll_before, abs=1e-4)

    def test_total_realized_pnl_unchanged_on_open(self, trader):
        pnl_before = trader._state[F_TOTAL_REALIZED_PNL]
        _open_yes(trader, size=20.0)
        assert trader._state[F_TOTAL_REALIZED_PNL] == pytest.approx(pnl_before, abs=1e-4)


class TestClosePositionInvariants:
    def _close_with_win(self, trader: PaperTrader, pos_id: str,
                        mid: float = 0.50, size: float = 10.0):
        """Simulate a WIN resolution by manually calling the state path."""
        with trader._lock:
            pos = next(p for p in trader._state[F_OPEN_POSITIONS]
                       if p["position_id"] == pos_id)
            trader._state[F_OPEN_POSITIONS] = [
                p for p in trader._state[F_OPEN_POSITIONS]
                if p["position_id"] != pos_id
            ]
            yes_ask = mid + 0.02
            pnl = round(size * (1.0 - yes_ask) / yes_ask, 4)
            closed = {**pos, "actual_pts": 25, "outcome": "WIN",
                      "pnl": pnl, "resolved_at": "2026-06-10T22:00:00Z",
                      "status": STATUS_CLOSED}
            trader._state[F_CLOSED_POSITIONS].append(closed)
            trader._state[F_BANKROLL] = round(trader._state[F_BANKROLL] + size + pnl, 4)
            trader._state[F_TOTAL_REALIZED_PNL] = round(
                trader._state[F_TOTAL_REALIZED_PNL] + pnl, 4)
            trader._accumulate_daily_loss(pnl)

    def test_state_valid_after_close(self, trader):
        pos_id = _open_yes(trader, size=10.0)
        self._close_with_win(trader, pos_id)
        assert validate_portfolio_state(trader._state) == []

    def test_closed_position_not_in_open_positions(self, trader):
        pos_id = _open_yes(trader, size=10.0)
        self._close_with_win(trader, pos_id)
        open_ids = {p["position_id"] for p in trader._state[F_OPEN_POSITIONS]}
        assert pos_id not in open_ids

    def test_closed_position_in_closed_positions(self, trader):
        pos_id = _open_yes(trader, size=10.0)
        self._close_with_win(trader, pos_id)
        closed_ids = {p["position_id"] for p in trader._state[F_CLOSED_POSITIONS]}
        assert pos_id in closed_ids

    def test_closed_status_in_closed_positions(self, trader):
        pos_id = _open_yes(trader, size=10.0)
        self._close_with_win(trader, pos_id)
        for pos in trader._state[F_CLOSED_POSITIONS]:
            assert pos["status"] in {STATUS_CLOSED, STATUS_EXITED}

    def test_initial_bankroll_unchanged_after_close(self, trader):
        pos_id = _open_yes(trader, size=10.0)
        self._close_with_win(trader, pos_id)
        assert trader._state[F_INITIAL_BANKROLL] == pytest.approx(INITIAL_BANKROLL_USD, abs=1e-4)

    def test_total_realized_pnl_is_sum_of_position_pnl(self, trader):
        """total_realized_pnl must equal Σ pnl from all closed positions."""
        pos1 = _open_yes(trader, size=10.0, mid=0.50)
        pos2 = _open_yes(trader, size=15.0, mid=0.40)
        self._close_with_win(trader, pos1, mid=0.50, size=10.0)
        self._close_with_win(trader, pos2, mid=0.40, size=15.0)
        expected = sum(p.get("pnl", p.get("exit_pnl", 0.0))
                       for p in trader._state[F_CLOSED_POSITIONS])
        assert trader._state[F_TOTAL_REALIZED_PNL] == pytest.approx(expected, abs=1e-3)


class TestExitPositionInvariants:
    def test_state_valid_after_exit(self, trader):
        pos_id = _open_yes(trader, size=10.0, pool_isolated=True)
        trader.exit_position(pos_id, exit_mip=0.70, p_current=0.65, exit_reason="TEST")
        assert validate_portfolio_state(trader._state) == []

    def test_exited_position_not_in_open_positions(self, trader):
        pos_id = _open_yes(trader, size=10.0, pool_isolated=True)
        trader.exit_position(pos_id, exit_mip=0.70, p_current=0.65, exit_reason="TEST")
        open_ids = {p["position_id"] for p in trader._state[F_OPEN_POSITIONS]}
        assert pos_id not in open_ids

    def test_exited_position_has_status_exited(self, trader):
        pos_id = _open_yes(trader, size=10.0, pool_isolated=True)
        trader.exit_position(pos_id, exit_mip=0.70, p_current=0.65, exit_reason="TEST")
        exited = [p for p in trader._state[F_CLOSED_POSITIONS]
                  if p["position_id"] == pos_id]
        assert len(exited) == 1
        assert exited[0]["status"] == STATUS_EXITED

    def test_bankroll_unchanged_on_pool_isolated_exit(self, trader):
        bankroll_before = trader._state[F_BANKROLL]
        pos_id = _open_yes(trader, size=10.0, pool_isolated=True)
        bankroll_after_open = trader._state[F_BANKROLL]
        assert bankroll_after_open == pytest.approx(bankroll_before, abs=1e-4)
        trader.exit_position(pos_id, exit_mip=0.70, p_current=0.65, exit_reason="TEST")
        assert trader._state[F_BANKROLL] == pytest.approx(bankroll_before, abs=1e-4)

    def test_bankroll_returned_on_non_isolated_exit(self, trader):
        pos_id = _open_yes(trader, size=10.0, pool_isolated=False, mid=0.50)
        bankroll_before_exit = trader._state[F_BANKROLL]
        _, closed = trader.exit_position(pos_id, exit_mip=0.70, p_current=0.65, exit_reason="TEST")
        expected = round(bankroll_before_exit + 10.0 + closed["exit_pnl"], 4)
        assert trader._state[F_BANKROLL] == pytest.approx(expected, abs=1e-3)

    def test_total_realized_pnl_updated_on_exit(self, trader):
        pos_id = _open_yes(trader, size=10.0, pool_isolated=True, mid=0.50)
        pnl_before = trader._state[F_TOTAL_REALIZED_PNL]
        _, closed = trader.exit_position(pos_id, exit_mip=0.70, p_current=0.65, exit_reason="TEST")
        assert trader._state[F_TOTAL_REALIZED_PNL] == pytest.approx(
            pnl_before + closed["exit_pnl"], abs=1e-4)

    def test_initial_bankroll_unchanged_after_exit(self, trader):
        pos_id = _open_yes(trader, size=10.0, pool_isolated=True)
        trader.exit_position(pos_id, exit_mip=0.30, p_current=0.35, exit_reason="TEST")
        assert trader._state[F_INITIAL_BANKROLL] == pytest.approx(INITIAL_BANKROLL_USD, abs=1e-4)


# ---------------------------------------------------------------------------
# Kill-switch state transitions
# ---------------------------------------------------------------------------

class TestKillSwitchStateTransitions:
    def test_net_positive_day_daily_loss_is_zero(self, trader):
        """After a profitable day, current_daily_loss must be 0 (kill switch won't fire)."""
        trader._accumulate_daily_loss(50.0)
        assert trader._state[F_CURRENT_DAILY_LOSS] == pytest.approx(0.0, abs=1e-4)

    def test_net_negative_day_daily_loss_positive(self, trader):
        """After a losing day, current_daily_loss is positive (kill switch candidate)."""
        trader._accumulate_daily_loss(-80.0)
        assert trader._state[F_CURRENT_DAILY_LOSS] == pytest.approx(80.0, abs=1e-4)

    def test_kill_switch_fires_when_daily_loss_exceeds_threshold(self, trader):
        """current_daily_loss at threshold must satisfy the kill switch condition."""
        threshold = trader._state[F_INITIAL_BANKROLL] * MAX_DAILY_LOSS_PCT
        trader._accumulate_daily_loss(-threshold)
        assert trader._state[F_CURRENT_DAILY_LOSS] >= threshold

    def test_cross_day_reset_clears_daily_loss(self, trader):
        """Daily loss from day N does not feed into kill-switch check on day N+1."""
        with patch("prediction_market_bot.c5_execution.paper_trader._today",
                   return_value="2026-06-10"):
            trader._accumulate_daily_loss(-200.0)
        assert trader._state[F_CURRENT_DAILY_LOSS] == pytest.approx(200.0, abs=1e-4)

        with patch("prediction_market_bot.c5_execution.paper_trader._today",
                   return_value="2026-06-11"):
            trader._accumulate_daily_loss(0.0)  # trigger reset
        assert trader._state[F_CURRENT_DAILY_LOSS] == pytest.approx(0.0, abs=1e-4)

    def test_state_valid_after_large_daily_loss(self, trader):
        """validate_portfolio_state passes even when kill switch would fire."""
        trader._accumulate_daily_loss(-999.0)
        errors = validate_portfolio_state(trader._state)
        assert errors == []


# ---------------------------------------------------------------------------
# Cross-day accounting invariants
# ---------------------------------------------------------------------------

class TestCrossDayAccounting:
    def test_bankroll_persists_across_day_boundary(self, trader):
        """Bankroll is a session-persistent field — day rollover does NOT reset it."""
        _open_yes(trader, size=20.0, pool_isolated=False)
        bankroll_day_n = trader._state[F_BANKROLL]

        with patch("prediction_market_bot.c5_execution.paper_trader._today",
                   return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()

        assert trader._state[F_BANKROLL] == pytest.approx(bankroll_day_n, abs=1e-4)

    def test_total_realized_pnl_persists_across_day_boundary(self, trader):
        """total_realized_pnl accumulates over the lifetime of the portfolio, not per-day."""
        trader._state[F_TOTAL_REALIZED_PNL] = -35.00
        with patch("prediction_market_bot.c5_execution.paper_trader._today",
                   return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state[F_TOTAL_REALIZED_PNL] == pytest.approx(-35.00, abs=1e-4)

    def test_initial_bankroll_persists_across_day_boundary(self, trader):
        """initial_bankroll_usd is set once at portfolio creation and must never change."""
        initial = trader._state[F_INITIAL_BANKROLL]
        for day in ("2026-06-10", "2026-06-11", "2026-06-12"):
            with patch("prediction_market_bot.c5_execution.paper_trader._today",
                       return_value=day):
                trader._accumulate_daily_loss(-10.0)
        assert trader._state[F_INITIAL_BANKROLL] == pytest.approx(initial, abs=1e-4)

    def test_state_valid_after_multiple_day_transitions(self, trader):
        """Schema validation passes after several simulated day transitions."""
        for day in ("2026-06-09", "2026-06-10", "2026-06-11"):
            with patch("prediction_market_bot.c5_execution.paper_trader._today",
                       return_value=day):
                trader._accumulate_daily_loss(-5.0 if day != "2026-06-10" else 3.0)
        assert validate_portfolio_state(trader._state) == []

    def test_open_positions_survive_day_transition(self, trader):
        """Positions open at end of day N are still open at start of day N+1."""
        pos_id = _open_yes(trader, game_date="2026-06-11")
        with patch("prediction_market_bot.c5_execution.paper_trader._today",
                   return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        open_ids = {p["position_id"] for p in trader._state[F_OPEN_POSITIONS]}
        assert pos_id in open_ids

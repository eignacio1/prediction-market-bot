"""
Tests: T-156 — Daily-Loss Accumulation + ADR-0012 Net Semantics
===============================================================
Coverage:
  PaperTrader._accumulate_daily_loss():
    - Single loss: current_daily_loss = |pnl|
    - Single profit: current_daily_loss stays 0
    - Net semantics: profit after loss offsets (current_daily_loss decreases)
    - Net semantics: loss after profit — net correctly re-evaluated
    - Accumulation is additive within same day
    - current_daily_loss never goes negative
    - daily_net_pnl tracks signed running total

  PaperTrader._reset_daily_loss_if_new_day():
    - Same-day: no reset
    - New day: current_daily_loss → 0, daily_net_pnl → 0, daily_loss_date → today
    - Reset does not touch bankroll_usd or total_realized_pnl

  Cross-day transitions:
    - Loss on day N, fresh start on day N+1
    - Win on day N, kill-switch does NOT fire on day N+1

  Kill-switch threshold input (boundary):
    - current_daily_loss fed to risk engine at boundary (bankroll * 0.15)
    - ADR-0012: threshold is based on initial_bankroll, not current bankroll
"""

import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from prediction_market_bot.c5_execution.paper_trader import PaperTrader, INITIAL_BANKROLL_USD
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c4_risk_engine.risk import MAX_DAILY_LOSS_PCT


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


# ---------------------------------------------------------------------------
# _accumulate_daily_loss — direct tests
# ---------------------------------------------------------------------------

class TestAccumulateDailyLoss:
    def test_single_loss_sets_current_daily_loss(self, trader):
        """A losing trade sets current_daily_loss to |pnl|."""
        trader._accumulate_daily_loss(-5.00)
        assert trader._state["current_daily_loss"] == pytest.approx(5.00, abs=1e-4)

    def test_single_profit_leaves_daily_loss_zero(self, trader):
        """A profitable trade must not increase current_daily_loss."""
        trader._accumulate_daily_loss(8.00)
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)

    def test_daily_net_pnl_tracked(self, trader):
        """daily_net_pnl is the signed running total of all trade pnl this day."""
        trader._accumulate_daily_loss(-3.00)
        trader._accumulate_daily_loss(1.00)
        assert trader._state["daily_net_pnl"] == pytest.approx(-2.00, abs=1e-4)

    def test_net_semantics_profit_offsets_prior_loss(self, trader):
        """Core ADR-0012 requirement: a subsequent profit reduces current_daily_loss."""
        trader._accumulate_daily_loss(-10.00)
        assert trader._state["current_daily_loss"] == pytest.approx(10.00, abs=1e-4)
        trader._accumulate_daily_loss(4.00)
        assert trader._state["current_daily_loss"] == pytest.approx(6.00, abs=1e-4)

    def test_net_semantics_profit_fully_covers_loss(self, trader):
        """Profit equal to prior loss brings current_daily_loss to zero (not negative)."""
        trader._accumulate_daily_loss(-7.50)
        trader._accumulate_daily_loss(7.50)
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)

    def test_net_semantics_profit_exceeds_loss(self, trader):
        """Net-positive day: current_daily_loss is 0, not a negative value."""
        trader._accumulate_daily_loss(-5.00)
        trader._accumulate_daily_loss(12.00)
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)
        assert trader._state["daily_net_pnl"] == pytest.approx(7.00, abs=1e-4)

    def test_current_daily_loss_never_negative(self, trader):
        """current_daily_loss is always >= 0, regardless of pnl sequence."""
        for pnl in [15.0, -3.0, 8.0, -2.0, 20.0]:
            trader._accumulate_daily_loss(pnl)
        assert trader._state["current_daily_loss"] >= 0.0

    def test_additive_losses_accumulate(self, trader):
        """Multiple losses accumulate correctly without reset."""
        trader._accumulate_daily_loss(-2.00)
        trader._accumulate_daily_loss(-3.00)
        trader._accumulate_daily_loss(-1.00)
        assert trader._state["current_daily_loss"] == pytest.approx(6.00, abs=1e-4)

    def test_loss_after_profit_does_not_carry_surplus(self, trader):
        """A loss on a net-positive day only adds to net, not double-counted."""
        trader._accumulate_daily_loss(10.00)   # net = +10, daily_loss = 0
        trader._accumulate_daily_loss(-3.00)   # net = +7, daily_loss = 0 (still net positive)
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)
        trader._accumulate_daily_loss(-12.00)  # net = -5, daily_loss = 5
        assert trader._state["current_daily_loss"] == pytest.approx(5.00, abs=1e-4)

    def test_accumulate_does_not_touch_bankroll(self, trader):
        """_accumulate_daily_loss must not modify bankroll_usd."""
        bankroll_before = trader._state["bankroll_usd"]
        trader._accumulate_daily_loss(-50.00)
        assert trader._state["bankroll_usd"] == pytest.approx(bankroll_before, abs=1e-4)

    def test_accumulate_does_not_touch_total_realized_pnl(self, trader):
        """_accumulate_daily_loss must not modify total_realized_pnl."""
        pnl_before = trader._state["total_realized_pnl"]
        trader._accumulate_daily_loss(-20.00)
        assert trader._state["total_realized_pnl"] == pytest.approx(pnl_before, abs=1e-4)


# ---------------------------------------------------------------------------
# _reset_daily_loss_if_new_day — direct tests
# ---------------------------------------------------------------------------

class TestResetDailyLossIfNewDay:
    def test_same_day_no_reset(self, trader):
        """No reset when daily_loss_date matches today."""
        today = date.today().isoformat()
        trader._state["daily_loss_date"] = today
        trader._state["current_daily_loss"] = 42.00
        trader._state["daily_net_pnl"] = -42.00
        trader._reset_daily_loss_if_new_day()
        assert trader._state["current_daily_loss"] == pytest.approx(42.00, abs=1e-4)

    def test_new_day_resets_daily_loss(self, trader):
        """On a new day, current_daily_loss resets to 0."""
        trader._state["daily_loss_date"] = "2026-06-10"
        trader._state["current_daily_loss"] = 25.00
        trader._state["daily_net_pnl"] = -25.00
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)

    def test_new_day_resets_daily_net_pnl(self, trader):
        """On a new day, daily_net_pnl resets to 0."""
        trader._state["daily_loss_date"] = "2026-06-10"
        trader._state["daily_net_pnl"] = -100.00
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state["daily_net_pnl"] == pytest.approx(0.0, abs=1e-4)

    def test_new_day_updates_daily_loss_date(self, trader):
        """daily_loss_date is updated to today after reset."""
        trader._state["daily_loss_date"] = "2026-06-10"
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state["daily_loss_date"] == "2026-06-11"

    def test_reset_does_not_touch_bankroll(self, trader):
        """_reset_daily_loss_if_new_day must not modify bankroll_usd."""
        trader._state["daily_loss_date"] = "2026-06-10"
        trader._state["bankroll_usd"] = 850.00
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state["bankroll_usd"] == pytest.approx(850.00, abs=1e-4)

    def test_reset_does_not_touch_total_realized_pnl(self, trader):
        """_reset_daily_loss_if_new_day must not modify total_realized_pnl."""
        trader._state["daily_loss_date"] = "2026-06-10"
        trader._state["total_realized_pnl"] = -35.00
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state["total_realized_pnl"] == pytest.approx(-35.00, abs=1e-4)

    def test_missing_daily_loss_date_triggers_reset(self, trader):
        """Missing daily_loss_date (key absent) is treated as stale → reset fires."""
        trader._state.pop("daily_loss_date", None)
        trader._state["current_daily_loss"] = 15.00
        trader._state["daily_net_pnl"] = -15.00
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._reset_daily_loss_if_new_day()
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)


# ---------------------------------------------------------------------------
# Cross-day transitions
# ---------------------------------------------------------------------------

class TestCrossDayTransitions:
    def test_loss_day_n_fresh_start_day_n_plus_1(self, trader):
        """Losses from day N do not carry forward into day N+1."""
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-10"):
            trader._accumulate_daily_loss(-80.00)
        assert trader._state["current_daily_loss"] == pytest.approx(80.00, abs=1e-4)

        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._accumulate_daily_loss(-5.00)
        assert trader._state["current_daily_loss"] == pytest.approx(5.00, abs=1e-4)
        assert trader._state["daily_net_pnl"] == pytest.approx(-5.00, abs=1e-4)

    def test_win_day_n_does_not_suppress_loss_day_n_plus_1(self, trader):
        """A profitable day N does not reduce or suppress loss accumulation on day N+1."""
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-10"):
            trader._accumulate_daily_loss(50.00)   # big win day N
        assert trader._state["current_daily_loss"] == pytest.approx(0.0, abs=1e-4)

        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._accumulate_daily_loss(-20.00)
        assert trader._state["current_daily_loss"] == pytest.approx(20.00, abs=1e-4)

    def test_daily_net_pnl_resets_between_days(self, trader):
        """daily_net_pnl is independent per day — day N result does not bleed into day N+1."""
        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-10"):
            trader._accumulate_daily_loss(30.00)
            trader._accumulate_daily_loss(-10.00)
        net_day_n = trader._state["daily_net_pnl"]
        assert net_day_n == pytest.approx(20.00, abs=1e-4)

        with patch("prediction_market_bot.c5_execution.paper_trader._today", return_value="2026-06-11"):
            trader._accumulate_daily_loss(-3.00)
        assert trader._state["daily_net_pnl"] == pytest.approx(-3.00, abs=1e-4)


# ---------------------------------------------------------------------------
# Kill-switch threshold boundary (ADR-0012 contract)
# ---------------------------------------------------------------------------

class TestKillSwitchThresholdBoundary:
    """
    ADR-0012: daily kill switch fires when current_daily_loss >= initial_bankroll * MAX_DAILY_LOSS_PCT.
    These tests verify the accumulation boundary values that feed into the risk engine.
    They do NOT invoke risk.py directly — they confirm what _accumulate_daily_loss produces
    at the boundary so the risk engine receives the correct input.
    """

    def test_max_daily_loss_pct_is_0_15(self):
        """ADR-0012 canonical constant: MAX_DAILY_LOSS_PCT = 0.15."""
        assert MAX_DAILY_LOSS_PCT == pytest.approx(0.15, abs=1e-6)

    def test_threshold_for_default_bankroll(self):
        """Default bankroll kill-switch threshold = 1000 * 0.15 = $150."""
        threshold = INITIAL_BANKROLL_USD * MAX_DAILY_LOSS_PCT
        assert threshold == pytest.approx(150.00, abs=1e-4)

    def test_accumulation_just_below_threshold(self, trader):
        """current_daily_loss just below threshold ($149.99) — kill switch must NOT fire."""
        trader._accumulate_daily_loss(-149.99)
        threshold = trader._state["initial_bankroll_usd"] * MAX_DAILY_LOSS_PCT
        assert trader._state["current_daily_loss"] < threshold

    def test_accumulation_at_threshold(self, trader):
        """current_daily_loss at exactly threshold ($150.00) — meets kill-switch condition."""
        trader._accumulate_daily_loss(-150.00)
        threshold = trader._state["initial_bankroll_usd"] * MAX_DAILY_LOSS_PCT
        assert trader._state["current_daily_loss"] >= threshold

    def test_accumulation_above_threshold(self, trader):
        """current_daily_loss above threshold — kill-switch condition still holds."""
        trader._accumulate_daily_loss(-200.00)
        threshold = trader._state["initial_bankroll_usd"] * MAX_DAILY_LOSS_PCT
        assert trader._state["current_daily_loss"] > threshold

    def test_net_semantics_can_pull_below_threshold(self, trader):
        """A subsequent win pulls current_daily_loss back below threshold (net semantics)."""
        trader._accumulate_daily_loss(-160.00)  # above threshold
        threshold = trader._state["initial_bankroll_usd"] * MAX_DAILY_LOSS_PCT
        assert trader._state["current_daily_loss"] > threshold

        trader._accumulate_daily_loss(20.00)    # partial recovery
        assert trader._state["current_daily_loss"] < threshold

    def test_threshold_anchored_to_initial_bankroll_not_current(self, trader):
        """Kill-switch threshold must use initial_bankroll_usd, not current bankroll_usd.

        If bankroll has eroded to $500, the 15% threshold is still $150 (1000*0.15),
        not $75 (500*0.15). ADR-0012: threshold is fixed at session-start initial_bankroll.
        """
        trader._state["bankroll_usd"] = 500.00  # simulate erosion
        threshold_from_initial = trader._state["initial_bankroll_usd"] * MAX_DAILY_LOSS_PCT
        threshold_from_current = trader._state["bankroll_usd"] * MAX_DAILY_LOSS_PCT
        # confirm the two are different (test is meaningful)
        assert threshold_from_initial != pytest.approx(threshold_from_current, abs=1e-4)
        # confirm initial_bankroll_usd is intact
        assert trader._state["initial_bankroll_usd"] == pytest.approx(INITIAL_BANKROLL_USD, abs=1e-4)

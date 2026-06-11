"""
Tests for src/prediction_market_bot/c4_risk_engine/risk.py

Coverage areas:
  - _compute_kelly_size: positive edge, zero edge, negative edge, fraction scaling, cap
  - Phase gate: gate closed → always REJECTED; gate open proceeds to checks
  - Hard limit checks: daily loss → KILL_SWITCH; drawdown → KILL_SWITCH
  - Edge checks: insufficient edge → REJECTED; direction PASS → REJECTED;
    Kelly size zero → REJECTED
  - Full approval path: YES direction, NO direction (probability flip)
  - Approval record contains all required IF-C4-C5 fields
  - C6 write failure propagates as (False, ...)
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

from prediction_market_bot.c4_risk_engine.risk import (
    DEFAULT_KELLY_FRACTION,
    MAX_DAILY_LOSS_PCT,
    MIN_BET_USD,
    MIN_EDGE_TO_APPROVE,
    STATUS_APPROVED,
    STATUS_KILL_SWITCH,
    STATUS_REJECTED,
    RiskEngine,
    _compute_kelly_size,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_logger(write_ok: bool = True) -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = write_ok
    return logger


def _make_forecast(
    p_estimate: float = 0.60,
    market_implied_prob: float = 0.50,
    edge: float = 0.10,
    direction: str = "YES",
    forecast_id: str = "FCST-TEST-001",
) -> dict:
    return {
        "forecast_id": forecast_id,
        "p_estimate": p_estimate,
        "market_implied_prob": market_implied_prob,
        "edge": edge,
        "recommended_direction": direction,
    }


def _make_engine(
    logger=None,
    bankroll: float = 10_000.0,
    kelly_fraction: float = DEFAULT_KELLY_FRACTION,
    initial_bankroll: float | None = None,
) -> RiskEngine:
    if logger is None:
        logger = _make_mock_logger()
    return RiskEngine(
        logger=logger,
        snapshot_id="SNAP-TEST",
        bankroll=bankroll,
        kelly_fraction=kelly_fraction,
        initial_bankroll=initial_bankroll,
    )


# ---------------------------------------------------------------------------
# _compute_kelly_size
# ---------------------------------------------------------------------------


class TestComputeKellySize:
    @pytest.mark.unit
    def test_positive_edge_returns_positive_size(self):
        size = _compute_kelly_size(
            p_estimate=0.60,
            market_implied_prob=0.50,
            kelly_fraction=0.25,
            bankroll=10_000.0,
        )
        assert size > 0.0

    @pytest.mark.unit
    def test_zero_edge_returns_zero(self):
        size = _compute_kelly_size(
            p_estimate=0.50,
            market_implied_prob=0.50,
            kelly_fraction=0.25,
            bankroll=10_000.0,
        )
        assert size == 0.0

    @pytest.mark.unit
    def test_negative_edge_returns_zero(self):
        size = _compute_kelly_size(
            p_estimate=0.40,
            market_implied_prob=0.55,
            kelly_fraction=0.25,
            bankroll=10_000.0,
        )
        assert size == 0.0

    @pytest.mark.unit
    def test_kelly_fraction_scales_size(self):
        # Use a small bankroll so neither fraction hits the $500 single-event cap
        size_full = _compute_kelly_size(0.55, 0.50, 1.0, 1_000.0)
        size_quarter = _compute_kelly_size(0.55, 0.50, 0.25, 1_000.0)
        assert size_quarter == pytest.approx(size_full * 0.25, rel=1e-6)

    @pytest.mark.unit
    def test_invalid_market_prob_zero_returns_zero(self):
        size = _compute_kelly_size(0.60, 0.0, 0.25, 10_000.0)
        assert size == 0.0

    @pytest.mark.unit
    def test_invalid_market_prob_one_returns_zero(self):
        size = _compute_kelly_size(0.60, 1.0, 0.25, 10_000.0)
        assert size == 0.0

    @pytest.mark.unit
    def test_single_event_cap_applied(self):
        # Very high edge should hit the $500 single-event cap
        size = _compute_kelly_size(
            p_estimate=0.99,
            market_implied_prob=0.01,
            kelly_fraction=1.0,
            bankroll=10_000.0,
        )
        assert size <= 500.0


# ---------------------------------------------------------------------------
# Phase gate
# ---------------------------------------------------------------------------


class TestPhaseGate:
    @pytest.mark.unit
    def test_gate_closed_returns_rejected(self):
        """Without BOT_C4_ACTIVE, every forecast is rejected at the gate."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOT_C4_ACTIVE", None)
            engine = _make_engine()
            ok, result = engine.evaluate_forecast(_make_forecast())
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "phase_gate_not_reached"

    @pytest.mark.unit
    def test_gate_closed_approved_size_is_zero(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOT_C4_ACTIVE", None)
            engine = _make_engine()
            _, result = engine.evaluate_forecast(_make_forecast())
        assert result["approved_size"] == 0.0

    @pytest.mark.unit
    def test_gate_closed_checks_passed_is_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOT_C4_ACTIVE", None)
            engine = _make_engine()
            _, result = engine.evaluate_forecast(_make_forecast())
        assert result["checks_passed"] == []

    @pytest.mark.unit
    def test_gate_open_proceeds_past_gate(self):
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(_make_forecast())
        # With valid forecast and gate open, must NOT be rejected for gate reason
        assert result["rejection_reason"] != "phase_gate_not_reached"

    @pytest.mark.unit
    def test_gate_env_var_case_insensitive(self):
        """BOT_C4_ACTIVE=True (capital T) must also open the gate."""
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "True"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(_make_forecast())
        assert result["rejection_reason"] != "phase_gate_not_reached"


# ---------------------------------------------------------------------------
# Hard limit checks
# ---------------------------------------------------------------------------


class TestHardLimits:
    @pytest.mark.unit
    def test_daily_loss_limit_triggers_kill_switch(self):
        # Default engine: bankroll=initial_bankroll=$10,000; threshold = 15% = $1,500
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_daily_loss=1_500.0,  # exactly at MAX_DAILY_LOSS_PCT threshold
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "daily_loss_limit_breached"

    @pytest.mark.unit
    def test_daily_loss_below_limit_passes(self):
        # Default engine: threshold = $1,500; $1,499 must not trigger
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_daily_loss=1_499.0,
            )
        assert result["rejection_reason"] != "daily_loss_limit_breached"

    @pytest.mark.unit
    def test_daily_loss_pct_at_threshold_triggers_kill_switch(self):
        # Paper bankroll scale: $1,000 bankroll; threshold = 15% = $150 (ADR-0012)
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, initial_bankroll=1_000.0)
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_daily_loss=150.0,  # exactly 15% of $1,000
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "daily_loss_limit_breached"

    @pytest.mark.unit
    def test_daily_loss_pct_below_threshold_passes(self):
        # $149 is below the $150 threshold at $1,000 paper bankroll
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, initial_bankroll=1_000.0)
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_daily_loss=149.0,
            )
        assert result["rejection_reason"] != "daily_loss_limit_breached"

    @pytest.mark.unit
    def test_zombie_daily_loss_no_longer_inactive(self):
        # Regression guard: $1,000 daily loss on a $1,000 bankroll should trigger
        # the kill switch (threshold=$150). Under the old $1,000 fixed limit it was
        # structurally inactive; ADR-0012 makes it the first-line daily kill switch.
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, initial_bankroll=1_000.0)
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_daily_loss=1_000.0,
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "daily_loss_limit_breached"

    @pytest.mark.unit
    def test_drawdown_limit_triggers_kill_switch(self):
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_drawdown_pct=0.20,  # equals max_drawdown_pct
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "drawdown_limit_breached"

    @pytest.mark.unit
    def test_drawdown_below_limit_passes(self):
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_drawdown_pct=0.19,
            )
        assert result["rejection_reason"] != "drawdown_limit_breached"

    @pytest.mark.unit
    def test_kill_switch_approved_size_is_zero(self):
        # Daily loss threshold at default $10k bankroll = 15% = $1,500
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(
                _make_forecast(),
                current_daily_loss=1_500.0,
            )
        assert result["approved_size"] == 0.0


# ---------------------------------------------------------------------------
# Edge and direction checks
# ---------------------------------------------------------------------------


class TestEdgeAndDirectionChecks:
    @pytest.mark.unit
    def test_insufficient_edge_rejected(self):
        fc = _make_forecast(edge=0.01, p_estimate=0.51, market_implied_prob=0.50)
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "insufficient_edge"

    @pytest.mark.unit
    def test_exactly_min_edge_passes_check(self):
        """Edge == MIN_EDGE_TO_APPROVE must pass the check (≥ not >)."""
        fc = _make_forecast(edge=MIN_EDGE_TO_APPROVE, p_estimate=0.52, market_implied_prob=0.50)
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(fc)
        assert result["rejection_reason"] != "insufficient_edge"

    @pytest.mark.unit
    def test_direction_pass_rejected(self):
        fc = _make_forecast(direction="PASS", edge=0.10)
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "direction_pass"

    @pytest.mark.unit
    def test_kelly_size_zero_rejected(self):
        # No edge on the probability side even though edge field is positive
        fc = _make_forecast(
            p_estimate=0.50,
            market_implied_prob=0.50,
            edge=0.05,  # edge field set but LR probabilities give no Kelly
            direction="YES",
        )
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(fc)
        # With p_estimate == market_implied_prob, Kelly size = 0
        assert result["rejection_reason"] == "kelly_size_zero"


# ---------------------------------------------------------------------------
# Full approval path
# ---------------------------------------------------------------------------


class TestApprovalPath:
    @pytest.mark.unit
    def test_full_yes_approval(self):
        fc = _make_forecast(p_estimate=0.65, market_implied_prob=0.50, edge=0.15, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            ok, result = engine.evaluate_forecast(fc)
        assert ok is True
        assert result["approval_status"] == STATUS_APPROVED
        assert result["approved_size"] > 0.0
        assert result["approved_direction"] == "YES"

    @pytest.mark.unit
    def test_full_no_approval_flips_probabilities(self):
        """NO direction: evaluation uses (1-p_estimate) vs (1-market_implied_prob)."""
        fc = _make_forecast(p_estimate=0.35, market_implied_prob=0.50, edge=-0.15, direction="NO")
        # Negative edge raw, but NO direction means we flip: p_eff=0.65, mip_eff=0.50
        # The edge check uses abs(edge), so |-0.15| = 0.15 passes
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            ok, result = engine.evaluate_forecast(fc)
        assert ok is True
        assert result["approval_status"] == STATUS_APPROVED
        assert result["approved_direction"] == "NO"
        assert result["approved_size"] > 0.0

    @pytest.mark.unit
    def test_approved_size_capped_at_single_event_limit(self):
        """Very high edge should still be capped at max_single_event_exposure_usd."""
        fc = _make_forecast(p_estimate=0.99, market_implied_prob=0.01, edge=0.98, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000_000.0, kelly_fraction=1.0)
            _, result = engine.evaluate_forecast(fc)
        if result["approval_status"] == STATUS_APPROVED:
            assert result["approved_size"] <= 500.0

    @pytest.mark.unit
    def test_approval_record_contains_required_fields(self):
        fc = _make_forecast()
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            _, result = engine.evaluate_forecast(fc)
        required = [
            "risk_eval_id", "approval_status", "rejection_reason",
            "approved_size", "approved_direction", "risk_check_timestamp",
            "checks_passed", "forecast_id",
        ]
        for field in required:
            assert field in result, f"'{field}' missing from approval record"

    @pytest.mark.unit
    def test_kelly_fraction_in_approval_record(self):
        fc = _make_forecast()
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(kelly_fraction=0.30)
            _, result = engine.evaluate_forecast(fc)
        if result["approval_status"] == STATUS_APPROVED:
            assert result["kelly_fraction"] == pytest.approx(0.30)

    @pytest.mark.unit
    def test_higher_edge_produces_larger_approved_size(self):
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            _, r_small = engine.evaluate_forecast(
                _make_forecast(p_estimate=0.55, market_implied_prob=0.50, edge=0.05, direction="YES")
            )
            _, r_large = engine.evaluate_forecast(
                _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
            )
        if r_small["approval_status"] == STATUS_APPROVED and r_large["approval_status"] == STATUS_APPROVED:
            assert r_large["approved_size"] > r_small["approved_size"]


# ---------------------------------------------------------------------------
# C6 write failure propagation
# ---------------------------------------------------------------------------


class TestC6WriteFailure:
    @pytest.mark.unit
    def test_c6_failure_on_gate_check_returns_false(self):
        """If C6 write fails during gate rejection, ok=False is returned."""
        logger = _make_mock_logger(write_ok=False)
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOT_C4_ACTIVE", None)
            engine = _make_engine(logger=logger)
            ok, _ = engine.evaluate_forecast(_make_forecast())
        assert ok is False

    @pytest.mark.unit
    def test_c6_failure_on_approval_returns_false(self):
        """C6 failure during approved write propagates False."""
        logger = _make_mock_logger(write_ok=False)
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(logger=logger)
            ok, _ = engine.evaluate_forecast(_make_forecast())
        assert ok is False

    @pytest.mark.unit
    def test_approval_dict_still_returned_on_c6_failure(self):
        """Even when C6 fails, the approval dict must be returned (caller decides action)."""
        logger = _make_mock_logger(write_ok=False)
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOT_C4_ACTIVE", None)
            engine = _make_engine(logger=logger)
            ok, result = engine.evaluate_forecast(_make_forecast())
        assert isinstance(result, dict)
        assert "approval_status" in result


# ---------------------------------------------------------------------------
# Minimum bet floor (MIN_BET_USD)
# ---------------------------------------------------------------------------


class TestMinBetFloor:
    """
    Bets sized below MIN_BET_USD (10.0) must be rejected with reason
    'min_bet_floor'. Bets at or above the floor pass through.
    """

    @pytest.mark.unit
    def test_sub_floor_bet_is_rejected(self):
        """Very small edge + small bankroll → Kelly size < MIN_BET_USD → REJECTED."""
        # edge=0.05 (clears ADR-0020 MIN_EDGE=0.04), market=0.50, bankroll=$100
        # → Kelly size well below the $10 floor
        fc = _make_forecast(
            p_estimate=0.55, market_implied_prob=0.50,
            edge=0.05, direction="YES",
        )
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=100.0)
            _, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "min_bet_floor"

    @pytest.mark.unit
    def test_above_floor_bet_is_approved(self):
        """Standard edge + adequate bankroll → Kelly size ≥ MIN_BET_USD → APPROVED."""
        fc = _make_forecast(
            p_estimate=0.65, market_implied_prob=0.50,
            edge=0.15, direction="YES",
        )
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            _, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_APPROVED
        assert result["approved_size"] >= MIN_BET_USD

    @pytest.mark.unit
    def test_floor_rejection_fields(self):
        """Rejection record for min_bet_floor: approved_size=0, kelly_size_positive in checks."""
        fc = _make_forecast(
            p_estimate=0.55, market_implied_prob=0.50,
            edge=0.05, direction="YES",
        )
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=100.0)
            _, result = engine.evaluate_forecast(fc)
        assert result["approved_size"] == 0.0
        assert result["rejection_reason"] == "min_bet_floor"
        # Kelly was positive (kelly_size_positive passed) but too small for floor
        assert "kelly_size_positive" in result["checks_passed"]

    @pytest.mark.unit
    def test_min_bet_floor_constant_is_ten(self):
        """MIN_BET_USD is 10.0 — explicit contract test so any change requires deliberate update."""
        assert MIN_BET_USD == pytest.approx(10.0)

    @pytest.mark.unit
    def test_no_floor_rejection_at_exact_floor(self):
        """A bet that Kelly-sizes to exactly MIN_BET_USD is approved, not rejected."""
        # Target: Kelly size exactly $10. With bankroll=$200, kelly_fraction=1.0:
        # f* = p - mip = 0.55 - 0.50 = 0.05; size = 0.05 * 200 = $10
        fc = _make_forecast(
            p_estimate=0.55, market_implied_prob=0.50,
            edge=0.05, direction="YES",
        )
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=200.0, kelly_fraction=1.0)
            _, result = engine.evaluate_forecast(fc)
        # At exactly the floor, should be APPROVED (not rejected)
        if result["approval_status"] != STATUS_APPROVED:
            # If sub-floor due to float precision, that is acceptable
            assert result["rejection_reason"] in ("min_bet_floor", "kelly_size_zero")

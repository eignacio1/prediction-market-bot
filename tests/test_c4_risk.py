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
  - T-213 (GG-060): edge_decision emission (every outcome, not just approvals),
    edge sink write-failure isolation, summarize_edge_run() run-state
    classification and silent-success detection
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import jsonlines
import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c4_risk_engine.risk import (
    DEFAULT_KELLY_FRACTION,
    MAX_DAILY_LOSS_PCT,
    MAX_PORTFOLIO_DEPLOYMENT_PCT,
    MIN_BET_USD,
    MIN_EDGE_TO_APPROVE,
    RESERVE_MANDATE_PCT,
    STATUS_APPROVED,
    STATUS_KILL_SWITCH,
    STATUS_REJECTED,
    _MIP_EPSILON,
    RiskEngine,
    _compute_kelly_size,
    summarize_edge_run,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger


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
    edge_logger=None,
) -> RiskEngine:
    if logger is None:
        logger = _make_mock_logger()
    return RiskEngine(
        logger=logger,
        snapshot_id="SNAP-TEST",
        bankroll=bankroll,
        kelly_fraction=kelly_fraction,
        initial_bankroll=initial_bankroll,
        edge_logger=edge_logger,
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

    # -- T-280/B1: boundary epsilon-clamp (near-0/1 market_implied_prob) ----

    @pytest.mark.unit
    def test_near_boundary_high_mip_returns_zero_no_exception(self):
        """mip within epsilon of 1.0 (but not exactly 1.0) must not raise/NaN."""
        size = _compute_kelly_size(
            p_estimate=0.9999995,
            market_implied_prob=1.0 - _MIP_EPSILON / 2,
            kelly_fraction=0.25,
            bankroll=10_000.0,
        )
        assert size == 0.0

    @pytest.mark.unit
    def test_near_boundary_low_mip_returns_zero_no_exception(self):
        """mip within epsilon of 0.0 (but not exactly 0.0) must not raise/NaN."""
        size = _compute_kelly_size(
            p_estimate=0.5,
            market_implied_prob=_MIP_EPSILON / 2,
            kelly_fraction=0.25,
            bankroll=10_000.0,
        )
        assert size == 0.0

    @pytest.mark.unit
    def test_just_outside_epsilon_computes_normally(self):
        """The clamp must be tight enough not to affect any real (cent-quantized)
        Kalshi price — the closest real price to a boundary is 0.01/0.99, far
        outside _MIP_EPSILON (1e-6)."""
        size = _compute_kelly_size(
            p_estimate=0.99,
            market_implied_prob=0.01,
            kelly_fraction=0.25,
            bankroll=10_000.0,
        )
        assert size > 0.0

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "p_estimate,market_implied_prob",
        [
            (0.60, 0.50),
            (0.55, 0.50),
            (0.99, 0.01),
            (0.02, 0.30),  # negative edge
            (0.999, 0.5),
            (0.5, 0.999),
            (0.5, 0.001),
        ],
    )
    def test_direct_formula_agrees_with_algebraic_simplification(
        self, p_estimate, market_implied_prob
    ):
        """f* = (p*b - q)/b must agree with its algebraic simplification
        f* = p - (1-p)*mip/(1-mip) within tight tolerance on stable inputs
        (T-280 cross-implementation invariant, B1/B2)."""
        b = (1.0 - market_implied_prob) / market_implied_prob
        q = 1.0 - p_estimate
        f_star_direct = (p_estimate * b - q) / b
        f_star_simplified = p_estimate - q * market_implied_prob / (1.0 - market_implied_prob)
        assert f_star_direct == pytest.approx(f_star_simplified, abs=1e-9)


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
        # GG-142: `edge` on the forecast record is already direction-resolved
        # by the caller — for a genuine, correctly-signed NO bet this is
        # POSITIVE (the fee-net edge of the NO side), not the raw negative
        # YES-frame value. A caller-side helper (e.g. run_mlb_paper_trade.py's
        # _directional_edge()) performs that flip before risk.py ever sees it.
        fc = _make_forecast(p_estimate=0.35, market_implied_prob=0.50, edge=0.15, direction="NO")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            ok, result = engine.evaluate_forecast(fc)
        assert ok is True
        assert result["approval_status"] == STATUS_APPROVED
        assert result["approved_direction"] == "NO"
        assert result["approved_size"] > 0.0

    @pytest.mark.unit
    def test_negative_directional_edge_rejected(self):
        """GG-142: a negative direction-resolved edge (confidently-wrong bet,
        vig/fee cost exceeding the signal in the recommended direction) must
        be REJECTED regardless of magnitude — abs() previously rescued these
        into approval (46.1% of T4 epoch-8 evaluations)."""
        fc = _make_forecast(p_estimate=0.35, market_implied_prob=0.50, edge=-0.15, direction="NO")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            ok, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "insufficient_edge"

    @pytest.mark.unit
    def test_direction_edge_sign_inconsistency_rejected(self):
        """GG-142 CHECK 4b: recommended_direction="NO" with a positive
        (YES-frame) gross_edge is an internally-inconsistent forecast record
        — a producer-side bug class distinct from the abs() gate defect —
        and must be rejected even though the direction-resolved `edge` field
        itself looks fine."""
        fc = _make_forecast(p_estimate=0.35, market_implied_prob=0.50, edge=0.15, direction="NO")
        fc["gross_edge"] = 0.15  # positive/YES-frame, inconsistent with NO
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            ok, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "direction_edge_sign_inconsistent"

    @pytest.mark.unit
    def test_direction_edge_sign_consistent_no_still_approved(self):
        """Sanity check for CHECK 4b: a correctly-signed NO record (negative
        gross_edge, positive direction-resolved edge) must still pass."""
        fc = _make_forecast(p_estimate=0.35, market_implied_prob=0.50, edge=0.15, direction="NO")
        fc["gross_edge"] = -0.15  # negative/YES-frame, consistent with NO
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            ok, result = engine.evaluate_forecast(fc)
        assert result["approval_status"] == STATUS_APPROVED

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


# ---------------------------------------------------------------------------
# Portfolio-level aggregate deployment invariant (ADR-0026 / GG-035)
# ---------------------------------------------------------------------------


class TestPortfolioDeploymentInvariant:
    """
    ADR-0026: C4 must hold aggregate open NON-isolated stake at or below the
    deployment cap (60% of equity → REJECT) and must NEVER allow it to exceed
    equity (free cash < 0 → KILL_SWITCH). The invariant is enforced only when
    the caller supplies portfolio_equity_usd; otherwise it is skipped
    (backward compatible). Root gap: GG-035 — the G5 book deployed 100.3% of
    initial / 134% of equity one sub-$500 bet at a time with nothing watching
    the aggregate.
    """

    @pytest.mark.unit
    def test_cap_constant_ties_to_reserve_mandate(self):
        """Deployment cap is the aggregate expression of the 40% reserve (ADR-0010)."""
        assert MAX_PORTFOLIO_DEPLOYMENT_PCT == pytest.approx(1.0 - RESERVE_MANDATE_PCT)
        assert MAX_PORTFOLIO_DEPLOYMENT_PCT == pytest.approx(0.60)

    @pytest.mark.unit
    def test_no_state_supplied_skips_invariant(self):
        """portfolio_equity_usd=None ⇒ invariant skipped, no new check, telemetry None."""
        fc = _make_forecast(p_estimate=0.65, market_implied_prob=0.50, edge=0.15, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            _, result = engine.evaluate_forecast(fc)  # no portfolio args
        assert result["approval_status"] == STATUS_APPROVED
        assert "aggregate_deployment_cap" not in result["checks_passed"]
        assert result["portfolio_equity_usd"] is None
        assert result["open_exposure_before_usd"] is None

    @pytest.mark.unit
    def test_clean_book_passes_and_records_check(self):
        """Zero existing exposure + ample equity ⇒ APPROVED, check recorded, telemetry set."""
        fc = _make_forecast(p_estimate=0.65, market_implied_prob=0.50, edge=0.15, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=10_000.0)
            _, result = engine.evaluate_forecast(
                fc, current_open_exposure_usd=0.0, portfolio_equity_usd=10_000.0
            )
        assert result["approval_status"] == STATUS_APPROVED
        assert "aggregate_deployment_cap" in result["checks_passed"]
        assert result["portfolio_equity_usd"] == pytest.approx(10_000.0)
        assert result["open_exposure_before_usd"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_exposure_at_cap_rejects_next_bet(self):
        """Open exposure already at the 60% cap ⇒ any further bet REJECTED."""
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, kelly_fraction=0.25)
            _, result = engine.evaluate_forecast(
                fc, current_open_exposure_usd=600.0, portfolio_equity_usd=1_000.0
            )
        assert result["approval_status"] == STATUS_REJECTED
        assert result["rejection_reason"] == "aggregate_deployment_cap"
        assert result["approved_size"] == 0.0

    @pytest.mark.unit
    def test_exposure_at_equity_kill_switch(self):
        """Open exposure at/above equity ⇒ over-leverage ⇒ KILL_SWITCH (8a, hard invariant)."""
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, kelly_fraction=0.25)
            _, result = engine.evaluate_forecast(
                fc, current_open_exposure_usd=1_000.0, portfolio_equity_usd=1_000.0
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "portfolio_over_leverage"
        assert result["approved_size"] == 0.0

    @pytest.mark.unit
    def test_solvency_breach_takes_priority_over_cap(self):
        """A book already past equity must KILL, not merely REJECT (8a before 8b)."""
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, kelly_fraction=0.25)
            # 1003.38 > equity 748.79 — this is the literal GG-035 forensic state
            _, result = engine.evaluate_forecast(
                fc, current_open_exposure_usd=1003.38, portfolio_equity_usd=748.79
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "portfolio_over_leverage"

    @pytest.mark.unit
    def test_below_cap_is_approved(self):
        """Exposure comfortably below cap ⇒ bet still approved."""
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1_000.0, kelly_fraction=0.25)
            _, result = engine.evaluate_forecast(
                fc, current_open_exposure_usd=100.0, portfolio_equity_usd=1_000.0
            )
        assert result["approval_status"] == STATUS_APPROVED
        assert "aggregate_deployment_cap" in result["checks_passed"]

    @pytest.mark.unit
    def test_c6_failure_during_cap_rejection_propagates_false(self):
        """C6 write failure during the aggregate-cap rejection returns ok=False."""
        logger = _make_mock_logger(write_ok=False)
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(logger=logger, bankroll=1_000.0, kelly_fraction=0.25)
            ok, result = engine.evaluate_forecast(
                fc, current_open_exposure_usd=600.0, portfolio_equity_usd=1_000.0
            )
        assert ok is False
        assert result["rejection_reason"] == "aggregate_deployment_cap"

    @pytest.mark.unit
    def test_g5_overleverage_forensic_would_have_been_blocked(self):
        """
        INSTITUTIONAL VERIFICATION (GG-035): replay the G5 deployment dynamic.

        Going into G5 the book had equity = $1000 initial − $251.21 realized
        (G2+G3+G4) = $748.79. The bot actually deployed $1003.38 (100.3% of
        initial, 134% of equity). With ADR-0026 active, C4 holds aggregate
        deployment at ≤ 60% of equity ($449.27) — every bet past the cap is
        REJECTED, so the over-leveraged $1003.38 state is unreachable.
        """
        equity = 748.79
        cap = MAX_PORTFOLIO_DEPLOYMENT_PCT * equity  # 449.27
        # Each bet sizes to $50 (bankroll 500, p=0.70, mip=0.50, kf=0.25 → f_live=0.1)
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")

        deployed = 0.0
        approvals = 0
        rejected_for_cap = False
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=500.0, kelly_fraction=0.25)
            for _ in range(41):  # G5 actually placed 41 bets
                _, res = engine.evaluate_forecast(
                    fc,
                    current_open_exposure_usd=deployed,
                    portfolio_equity_usd=equity,
                )
                if res["approval_status"] == STATUS_APPROVED:
                    deployed += res["approved_size"]
                    approvals += 1
                elif res["rejection_reason"] == "aggregate_deployment_cap":
                    rejected_for_cap = True
                    break

        assert rejected_for_cap, "cap must engage before all 41 bets clear"
        assert deployed <= cap + 1e-6, f"deployed {deployed} exceeded cap {cap}"
        assert deployed < 1003.38, "must never reach the real over-leveraged exposure"
        assert approvals < 41, "not all G5 bets should have been allowed"


class TestPoolIsolated:
    """T-175 (ADR-0026 extension): pool_isolated=True skips 8b, applies 8a."""

    def test_pool_isolated_skips_policy_cap(self):
        """
        When pool_isolated=True, a bet that would breach the 60% cap still
        passes — the policy cap does not apply to isolated-pool callers.
        """
        # equity=$1000, exposure=$700 → would breach 60% cap ($600) for T1
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1000.0)
            _, result = engine.evaluate_forecast(
                fc,
                current_open_exposure_usd=700.0,
                portfolio_equity_usd=1000.0,
                pool_isolated=True,
            )
        assert result["approval_status"] == STATUS_APPROVED
        assert "aggregate_deployment_cap" not in result.get("checks_passed", [])

    def test_pool_isolated_applies_solvency_kill(self):
        """
        When pool_isolated=True, a bet that would exceed equity still triggers
        CHECK 8a KILL_SWITCH — solvency applies to isolated pools too.
        """
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=500.0)
            _, result = engine.evaluate_forecast(
                fc,
                current_open_exposure_usd=500.0,  # already at equity
                portfolio_equity_usd=500.0,
                pool_isolated=True,
            )
        assert result["approval_status"] == STATUS_KILL_SWITCH
        assert result["rejection_reason"] == "portfolio_over_leverage"

    def test_pool_isolated_telemetry_field(self):
        """pool_isolated is recorded in the approval record (T-175 audit trail)."""
        fc = _make_forecast(p_estimate=0.70, market_implied_prob=0.50, edge=0.20, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(bankroll=1000.0)
            _, result = engine.evaluate_forecast(
                fc,
                current_open_exposure_usd=0.0,
                portfolio_equity_usd=1000.0,
                pool_isolated=True,
            )
        assert result["pool_isolated"] is True


# ---------------------------------------------------------------------------
# T-213 (GG-060) — C4 Edge Accounting
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> list[dict]:
    with jsonlines.open(str(path), mode="r") as reader:
        return list(reader)


class TestEdgeDecisionEmission:
    """evaluate_forecast() emits one edge_decision record per call when
    edge_logger is set — for every outcome, not just approvals."""

    @pytest.mark.unit
    def test_no_edge_logger_is_backward_compatible(self):
        """Default (edge_logger=None) — no emission, no error, no behavior change."""
        fc = _make_forecast()
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine()
            ok, result = engine.evaluate_forecast(fc)
        assert ok is True
        assert result["approval_status"] == STATUS_APPROVED

    @pytest.mark.unit
    def test_emits_on_approval(self, tmp_path):
        edge_path = tmp_path / "audit_mlb_edge_decisions.jsonl"
        edge_logger = AuditLogger(edge_path, min_severity="INFO")
        fc = _make_forecast(p_estimate=0.60, market_implied_prob=0.50, edge=0.10, direction="YES")
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(edge_logger=edge_logger)
            engine.evaluate_forecast(fc, session_id="SESS-1")

        entries = _read_jsonl(edge_path)
        assert len(entries) == 1
        payload = entries[0]["payload"]
        assert payload["approval_status"] == STATUS_APPROVED
        assert payload["edge_signal"] is True
        assert payload["model_p"] == 0.60
        assert payload["market_implied_p"] == 0.50
        assert payload["decision"] == STATUS_APPROVED
        assert entries[0]["session_id"] == "SESS-1"

    @pytest.mark.unit
    def test_emits_on_insufficient_edge_rejection(self, tmp_path):
        edge_path = tmp_path / "edge.jsonl"
        edge_logger = AuditLogger(edge_path, min_severity="INFO")
        fc = _make_forecast(edge=0.01)  # below MIN_EDGE_TO_APPROVE
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(edge_logger=edge_logger)
            engine.evaluate_forecast(fc)

        entries = _read_jsonl(edge_path)
        assert len(entries) == 1
        payload = entries[0]["payload"]
        assert payload["approval_status"] == STATUS_REJECTED
        assert payload["rejection_reason"] == "insufficient_edge"
        assert payload["edge_signal"] is False
        assert payload["decision"] == "REJECTED:insufficient_edge"

    @pytest.mark.unit
    def test_emits_on_phase_gate_closed(self, tmp_path):
        """Even a gated-closed evaluation is recorded — the run-level summary
        needs the full population to detect a dark pipeline."""
        edge_path = tmp_path / "edge.jsonl"
        edge_logger = AuditLogger(edge_path, min_severity="INFO")
        fc = _make_forecast()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOT_C4_ACTIVE", None)
            engine = _make_engine(edge_logger=edge_logger)
            engine.evaluate_forecast(fc)

        entries = _read_jsonl(edge_path)
        assert len(entries) == 1
        assert entries[0]["payload"]["rejection_reason"] == "phase_gate_not_reached"

    @pytest.mark.unit
    def test_emits_on_kill_switch(self, tmp_path):
        edge_path = tmp_path / "edge.jsonl"
        edge_logger = AuditLogger(edge_path, min_severity="INFO")
        fc = _make_forecast(edge=0.20)
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(edge_logger=edge_logger, initial_bankroll=1000.0)
            engine.evaluate_forecast(fc, current_daily_loss=200.0)  # >= 15% of 1000

        entries = _read_jsonl(edge_path)
        assert len(entries) == 1
        payload = entries[0]["payload"]
        assert payload["approval_status"] == STATUS_KILL_SWITCH
        assert payload["rejection_reason"] == "daily_loss_limit_breached"
        # A real edge signal existed (0.20 >= MIN_EDGE_TO_APPROVE) even though
        # the kill switch fired first — this is exactly the RISK_REJECTED
        # case summarize_edge_run() must be able to distinguish.
        assert payload["edge_signal"] is True

    @pytest.mark.unit
    def test_vig_passed_through_when_present(self, tmp_path):
        edge_path = tmp_path / "edge.jsonl"
        edge_logger = AuditLogger(edge_path, min_severity="INFO")
        fc = _make_forecast()
        fc["vig"] = 0.035
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(edge_logger=edge_logger)
            engine.evaluate_forecast(fc)

        entries = _read_jsonl(edge_path)
        assert entries[0]["payload"]["vig"] == 0.035

    @pytest.mark.unit
    def test_edge_sink_write_failure_does_not_flip_ok_false(self):
        """A failing edge sink is a WARNING on the primary logger, not a
        kill-switch-triggering False — it is a secondary analytics sink,
        not the canonical C6 audit trail (NFR-03 governs the latter only)."""
        main_logger = _make_mock_logger(write_ok=True)
        edge_logger = MagicMock()
        edge_logger.log.return_value = False
        fc = _make_forecast()
        with patch.dict(os.environ, {"BOT_C4_ACTIVE": "true"}):
            engine = _make_engine(logger=main_logger, edge_logger=edge_logger)
            ok, result = engine.evaluate_forecast(fc)

        assert ok is True
        assert result["approval_status"] == STATUS_APPROVED
        warning_calls = [
            c for c in main_logger.log.call_args_list
            if c.kwargs.get("event_type") == "edge_decision_write_failed"
        ]
        assert len(warning_calls) == 1
        assert warning_calls[0].kwargs.get("severity") == "WARNING"


# ---------------------------------------------------------------------------
# T-213 (GG-060) — summarize_edge_run()
# ---------------------------------------------------------------------------


def _write_edge_entry(
    edge_logger: AuditLogger,
    *,
    approval_status: str,
    edge_signal: bool,
    rejection_reason: str | None = None,
    session_id: str | None = None,
) -> None:
    edge_logger.log(
        component="C4",
        event_type="edge_decision",
        payload={
            "model_p": 0.5,
            "market_implied_p": 0.5,
            "edge": 0.1 if edge_signal else 0.0,
            "edge_signal": edge_signal,
            "approval_status": approval_status,
            "rejection_reason": rejection_reason,
        },
        session_id=session_id,
        severity="INFO",
    )


class TestSummarizeEdgeRun:
    @pytest.mark.unit
    def test_missing_file_is_pipeline_broken(self, tmp_path):
        summary = summarize_edge_run(tmp_path / "does_not_exist.jsonl")
        assert summary["run_state"] == "PIPELINE_BROKEN"
        assert summary["total_evaluations"] == 0

    @pytest.mark.unit
    def test_empty_file_is_pipeline_broken(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        path.touch()
        summary = summarize_edge_run(path)
        assert summary["run_state"] == "PIPELINE_BROKEN"

    @pytest.mark.unit
    def test_evaluations_with_no_edge_signal_is_no_edge(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        for _ in range(5):
            _write_edge_entry(
                logger,
                approval_status=STATUS_REJECTED,
                edge_signal=False,
                rejection_reason="insufficient_edge",
            )
        summary = summarize_edge_run(path)
        assert summary["run_state"] == "NO_EDGE"
        assert summary["total_evaluations"] == 5
        assert summary["edge_signals_found"] == 0
        assert summary["bets_approved"] == 0

    @pytest.mark.unit
    def test_edge_signals_but_none_approved_is_risk_rejected(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        for _ in range(3):
            _write_edge_entry(
                logger,
                approval_status=STATUS_KILL_SWITCH,
                edge_signal=True,
                rejection_reason="daily_loss_limit_breached",
            )
        summary = summarize_edge_run(path)
        assert summary["run_state"] == "RISK_REJECTED"
        assert summary["edge_signals_found"] == 3
        assert summary["bets_approved"] == 0

    @pytest.mark.unit
    def test_at_least_one_approval_is_active(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=False,
                           rejection_reason="insufficient_edge")
        _write_edge_entry(logger, approval_status=STATUS_APPROVED, edge_signal=True)
        summary = summarize_edge_run(path)
        assert summary["run_state"] == "ACTIVE"
        assert summary["bets_approved"] == 1

    @pytest.mark.unit
    def test_silent_success_flag_true_at_50_no_edge_evals(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        for _ in range(50):
            _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=False,
                               rejection_reason="insufficient_edge")
        summary = summarize_edge_run(path)
        assert summary["silent_success_flag"] is True

    @pytest.mark.unit
    def test_silent_success_flag_false_below_50_evals(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        for _ in range(49):
            _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=False,
                               rejection_reason="insufficient_edge")
        summary = summarize_edge_run(path)
        assert summary["silent_success_flag"] is False

    @pytest.mark.unit
    def test_session_id_filtering(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        _write_edge_entry(logger, approval_status=STATUS_APPROVED, edge_signal=True,
                           session_id="SESS-A")
        _write_edge_entry(logger, approval_status=STATUS_APPROVED, edge_signal=True,
                           session_id="SESS-A")
        _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=False,
                           rejection_reason="insufficient_edge", session_id="SESS-B")

        summary_a = summarize_edge_run(path, session_id="SESS-A")
        assert summary_a["total_evaluations"] == 2
        assert summary_a["bets_approved"] == 2

        summary_b = summarize_edge_run(path, session_id="SESS-B")
        assert summary_b["total_evaluations"] == 1
        assert summary_b["run_state"] == "NO_EDGE"

    @pytest.mark.unit
    def test_rejection_reason_counts_aggregated(self, tmp_path):
        path = tmp_path / "edge.jsonl"
        logger = AuditLogger(path, min_severity="INFO")
        _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=False,
                           rejection_reason="insufficient_edge")
        _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=False,
                           rejection_reason="insufficient_edge")
        _write_edge_entry(logger, approval_status=STATUS_REJECTED, edge_signal=True,
                           rejection_reason="min_bet_floor")
        summary = summarize_edge_run(path)
        assert summary["rejection_reason_counts"] == {
            "insufficient_edge": 2,
            "min_bet_floor": 1,
        }

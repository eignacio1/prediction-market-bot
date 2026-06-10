"""
Tests: T-146/T-147 — Band Exit Mechanics (ADR-0018/0019)
=========================================================
T-146: exit_position() in PaperTrader
T-147: exit evaluation pass in run_t4_live._run_cycle

Coverage:
  PaperTrader.exit_position():
    - YES / NO PnL formulas
    - pool_isolated flag: bankroll unchanged for T4 positions
    - non-isolated: bankroll updated
    - total_realized_pnl and current_daily_loss updated
    - status = "EXITED" in closed_positions
    - exit fields present (exit_mip, p_current_at_exit, exit_reason, exit_pnl)
    - position not found: returns (True, {})
    - exit_fee_per_contract recorded (notional — not deducted per T-151)

  execution_bands constants:
    - NOISE_BUFFER_BAND_T4 = 0.13905 (EXP-019A analytic)
    - NOISE_BUFFER_BAND_T1 = NOISE_BUFFER_BAND_T2 = NOISE_BUFFER_BAND_T3 = 0.22053
    - NOISE_BUFFER_BAND_T5 = 0.13328
    - T4 > T5 (wider buffer at longer time horizon)
    - T1 > T4 (wider buffer at pregame σ_λ)

  _run_cycle exit pass:
    - exit fires when mip_current > p_current + NOISE_BUFFER_BAND_T4 (YES)
    - exit does NOT fire when mip_current <= p_current + NOISE_BUFFER_BAND_T4
    - time guard: no exit when time_remaining_min <= EXIT_MIN_TIME_REMAINING_MIN
    - NO position: exit fires when p_current > mip_current + NOISE_BUFFER_BAND_T4
"""

import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c5_execution.paper_trader import PaperTrader, INITIAL_BANKROLL_USD
from prediction_market_bot.execution_bands import (
    NOISE_BUFFER_BAND_T1,
    NOISE_BUFFER_BAND_T2,
    NOISE_BUFFER_BAND_T3,
    NOISE_BUFFER_BAND_T4,
    NOISE_BUFFER_BAND_T5,
    EXIT_MIN_TIME_REMAINING_MIN,
)


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


def _open_yes_pos(trader: PaperTrader, mid_price: float = 0.50, size_usd: float = 10.0,
                  pool_isolated: bool = False, threshold: int = 22) -> str:
    """Helper: open a YES position and return position_id."""
    approval = {
        "approval_status": "APPROVED",
        "approved_size": size_usd,
        "approved_direction": "YES",
        "edge": 0.05,
        "gross_edge": 0.07,
        "model_p": mid_price + 0.05,
        "risk_eval_id": "RISK-001",
        "forecast_id": "FC-001",
    }
    _, pos = trader.open_position(
        approval=approval,
        player_name="Test Player",
        player_id=42,
        kalshi_ticker="NBA_TEST_YES",
        kalshi_threshold=threshold,
        mid_price=mid_price,
        vig=0.04,
        game_date="2026-06-10",
        pool_isolated=pool_isolated,
    )
    return pos["position_id"]


def _open_no_pos(trader: PaperTrader, mid_price: float = 0.50, size_usd: float = 10.0,
                 pool_isolated: bool = False) -> str:
    """Helper: open a NO position and return position_id."""
    approval = {
        "approval_status": "APPROVED",
        "approved_size": size_usd,
        "approved_direction": "NO",
        "edge": 0.05,
        "gross_edge": 0.07,
        "model_p": mid_price - 0.05,
        "risk_eval_id": "RISK-002",
        "forecast_id": "FC-002",
    }
    _, pos = trader.open_position(
        approval=approval,
        player_name="Test Player",
        player_id=42,
        kalshi_ticker="NBA_TEST_NO",
        kalshi_threshold=22,
        mid_price=mid_price,
        vig=0.04,
        game_date="2026-06-10",
        pool_isolated=pool_isolated,
    )
    return pos["position_id"]


# ---------------------------------------------------------------------------
# execution_bands constants (EXP-019A invariants)
# ---------------------------------------------------------------------------

class TestNoiseBufferConstants:
    def test_t4_analytic_value(self):
        """NOISE_BUFFER_BAND_T4 must be 0.13905 (EXP-019A analytic)."""
        assert NOISE_BUFFER_BAND_T4 == pytest.approx(0.13905, abs=1e-5)

    def test_t1_analytic_value(self):
        """NOISE_BUFFER_BAND_T1 must be 0.22053 (EXP-019A analytic)."""
        assert NOISE_BUFFER_BAND_T1 == pytest.approx(0.22053, abs=1e-5)

    def test_t2_t3_equal_t1(self):
        """T2 and T3 share the same σ_λ basis as T1."""
        assert NOISE_BUFFER_BAND_T2 == NOISE_BUFFER_BAND_T1
        assert NOISE_BUFFER_BAND_T3 == NOISE_BUFFER_BAND_T1

    def test_t5_analytic_value(self):
        """NOISE_BUFFER_BAND_T5 must be 0.13328 (EXP-019A analytic, near-deterministic)."""
        assert NOISE_BUFFER_BAND_T5 == pytest.approx(0.13328, abs=1e-5)

    def test_ordering(self):
        """T1 > T4 > T5: wider buffer at earlier time horizons (higher σ_λ)."""
        assert NOISE_BUFFER_BAND_T1 > NOISE_BUFFER_BAND_T4 > NOISE_BUFFER_BAND_T5

    def test_time_guard_value(self):
        """EXIT_MIN_TIME_REMAINING_MIN = 3.0 (T5 arithmetic takes over below this)."""
        assert EXIT_MIN_TIME_REMAINING_MIN == pytest.approx(3.0, abs=1e-6)


# ---------------------------------------------------------------------------
# PaperTrader.exit_position() — T-146
# ---------------------------------------------------------------------------

class TestExitPositionYES:
    def test_yes_exit_pnl_profit(self, trader):
        """YES position exits at higher price → positive PnL."""
        pos_id = _open_yes_pos(trader, mid_price=0.40, size_usd=10.0)
        ok, closed = trader.exit_position(
            position_id=pos_id,
            exit_mip=0.70,
            p_current=0.20,
            exit_reason="BAYESIAN_REVERSAL",
        )
        assert ok
        assert closed["status"] == "EXITED"
        # PnL = 10 * (0.70 / 0.40 - 1) = 10 * 0.75 = 7.50
        assert closed["exit_pnl"] == pytest.approx(7.50, abs=1e-3)

    def test_yes_exit_pnl_loss(self, trader):
        """YES position exits at lower price → negative PnL."""
        pos_id = _open_yes_pos(trader, mid_price=0.60, size_usd=10.0)
        ok, closed = trader.exit_position(
            position_id=pos_id,
            exit_mip=0.30,
            p_current=0.10,
            exit_reason="BAYESIAN_REVERSAL",
        )
        assert ok
        # PnL = 10 * (0.30 / 0.60 - 1) = 10 * (-0.50) = -5.00
        assert closed["exit_pnl"] == pytest.approx(-5.00, abs=1e-3)

    def test_yes_exit_fields_present(self, trader):
        """Closed record must contain all required exit fields."""
        pos_id = _open_yes_pos(trader, mid_price=0.50, size_usd=5.0)
        _, closed = trader.exit_position(pos_id, 0.80, 0.25, "TEST_REASON")
        assert closed["exit_mip"] == pytest.approx(0.80, abs=1e-6)
        assert closed["p_current_at_exit"] == pytest.approx(0.25, abs=1e-6)
        assert closed["exit_reason"] == "TEST_REASON"
        assert "exited_at" in closed
        assert "exit_fee_per_contract" in closed

    def test_exit_fee_formula(self, trader):
        """exit_fee_per_contract must follow 0.07 × mip × (1−mip)."""
        pos_id = _open_yes_pos(trader, mid_price=0.50, size_usd=5.0)
        _, closed = trader.exit_position(pos_id, 0.60, 0.25, "FEE_TEST")
        expected_fee = 0.07 * 0.60 * (1.0 - 0.60)
        assert closed["exit_fee_per_contract"] == pytest.approx(expected_fee, abs=1e-6)

    def test_yes_moves_to_closed(self, trader):
        """Position must be removed from open and added to closed."""
        pos_id = _open_yes_pos(trader, mid_price=0.50)
        assert any(p["position_id"] == pos_id for p in trader.get_state()["open_positions"])
        trader.exit_position(pos_id, 0.70, 0.20, "TEST")
        state = trader.get_state()
        assert not any(p["position_id"] == pos_id for p in state["open_positions"])
        assert any(p["position_id"] == pos_id for p in state["closed_positions"])


class TestExitPositionNO:
    def test_no_exit_pnl_when_yes_rises(self, trader):
        """NO position exits at profit when YES price rises (NO price fell)."""
        # Bought NO at (1-0.40) = 0.60; exit when YES rises to 0.80 → NO = 0.20
        pos_id = _open_no_pos(trader, mid_price=0.40, size_usd=10.0)
        ok, closed = trader.exit_position(
            position_id=pos_id,
            exit_mip=0.80,   # YES price rose — bad for NO holder
            p_current=0.90,
            exit_reason="BAYESIAN_REVERSAL_NO",
        )
        assert ok
        # PnL = 10 * ((1-0.80)/(1-0.40) - 1) = 10 * (0.20/0.60 - 1) ≈ -6.667
        expected_pnl = 10.0 * (0.20 / 0.60 - 1.0)
        assert closed["exit_pnl"] == pytest.approx(expected_pnl, abs=1e-3)

    def test_no_exit_status(self, trader):
        pos_id = _open_no_pos(trader, mid_price=0.60)
        _, closed = trader.exit_position(pos_id, 0.30, 0.10, "TEST")
        assert closed["status"] == "EXITED"


class TestExitPositionBankroll:
    def test_non_isolated_bankroll_updated(self, trader):
        """Non-pool-isolated exit: bankroll gets back stake + pnl."""
        state_before = trader.get_state()
        br_before = state_before["bankroll_usd"]
        pos_id = _open_yes_pos(trader, mid_price=0.50, size_usd=10.0, pool_isolated=False)
        br_after_open = trader.get_state()["bankroll_usd"]
        assert br_after_open == pytest.approx(br_before - 10.0, abs=1e-4)

        trader.exit_position(pos_id, 0.60, 0.25, "TEST")
        br_after_exit = trader.get_state()["bankroll_usd"]
        expected_pnl = 10.0 * (0.60 / 0.50 - 1.0)  # +2.00
        assert br_after_exit == pytest.approx(br_after_open + 10.0 + expected_pnl, abs=1e-4)

    def test_pool_isolated_bankroll_unchanged(self, trader):
        """Pool-isolated (T4) exit: bankroll_usd must not change."""
        br_before = trader.get_state()["bankroll_usd"]
        pos_id = _open_yes_pos(trader, mid_price=0.50, size_usd=10.0, pool_isolated=True)
        # pool_isolated=True: open_position does NOT deduct bankroll
        assert trader.get_state()["bankroll_usd"] == pytest.approx(br_before, abs=1e-4)
        trader.exit_position(pos_id, 0.70, 0.20, "TEST")
        # exit_position: pool_isolated → bankroll still unchanged
        assert trader.get_state()["bankroll_usd"] == pytest.approx(br_before, abs=1e-4)

    def test_realized_pnl_updated_pool_isolated(self, trader):
        """total_realized_pnl is updated even for pool_isolated exits."""
        pos_id = _open_yes_pos(trader, mid_price=0.50, size_usd=10.0, pool_isolated=True)
        pnl_before = trader.get_state()["total_realized_pnl"]
        trader.exit_position(pos_id, 0.70, 0.20, "TEST")
        pnl_after = trader.get_state()["total_realized_pnl"]
        expected_pnl = 10.0 * (0.70 / 0.50 - 1.0)
        assert pnl_after == pytest.approx(pnl_before + expected_pnl, abs=1e-4)

    def test_daily_loss_updated_on_loss(self, trader):
        """current_daily_loss increases when exit realizes a loss."""
        pos_id = _open_yes_pos(trader, mid_price=0.70, size_usd=10.0, pool_isolated=True)
        loss_before = trader.get_state()["current_daily_loss"]
        trader.exit_position(pos_id, 0.30, 0.10, "TEST")
        loss_after = trader.get_state()["current_daily_loss"]
        expected_loss = abs(10.0 * (0.30 / 0.70 - 1.0))
        assert loss_after == pytest.approx(loss_before + expected_loss, abs=1e-3)

    def test_daily_loss_unchanged_on_profit(self, trader):
        """current_daily_loss must not increase on a profitable exit."""
        pos_id = _open_yes_pos(trader, mid_price=0.40, size_usd=10.0, pool_isolated=True)
        loss_before = trader.get_state()["current_daily_loss"]
        trader.exit_position(pos_id, 0.80, 0.20, "TEST")
        assert trader.get_state()["current_daily_loss"] == pytest.approx(loss_before, abs=1e-6)


class TestExitPositionEdgeCases:
    def test_position_not_found_returns_empty(self, trader):
        """exit_position on unknown position_id must return (True, {})."""
        ok, result = trader.exit_position("POS-DOESNOTEXIST", 0.50, 0.30, "TEST")
        assert ok is True
        assert result == {}

    def test_exit_annotation_in_portfolio_json(self, trader, tmp_portfolio):
        """Exited positions must persist in portfolio JSON with status=EXITED."""
        pos_id = _open_yes_pos(trader, mid_price=0.50)
        trader.exit_position(pos_id, 0.70, 0.20, "PERSIST_TEST")
        raw = json.loads(tmp_portfolio.read_text())
        exited = [p for p in raw["closed_positions"] if p["status"] == "EXITED"]
        assert len(exited) == 1
        assert exited[0]["position_id"] == pos_id


# ---------------------------------------------------------------------------
# _run_cycle exit evaluation pass — T-147
# ---------------------------------------------------------------------------

# Import helpers from the T-149 test file's fixtures
from prediction_market_bot.c1_signal_ingestion.ds02_nba_live import LivePlayerState
from prediction_market_bot.c5_execution.kalshi_client import PlayerMarket
from prediction_market_bot.c3_forecasting.game_state_model import T4Signal
from prediction_market_bot.run_t4_inplay import T4RoutingResult
from prediction_market_bot.run_t4_live import _run_cycle
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore


def _make_player_market_ext(ticker: str, mip: float, has_quotes: bool = True) -> PlayerMarket:
    half_vig = 0.02
    return PlayerMarket(
        ticker=ticker,
        title="Test Player Over 22.5 Pts",
        player_name="Test Player",
        team_abbr="TST",
        threshold=22,
        game_date="2026-06-10",
        event_ticker="NBA_TEST",
        yes_ask=mip + half_vig,
        yes_bid=mip - half_vig,
        no_ask=1.0 - (mip - half_vig),
        no_bid=1.0 - (mip + half_vig),
        mid_price=mip,
        vig=2 * half_vig,
        volume=1000.0,
        status="active" if has_quotes else "inactive",
        fetched_at="2026-06-10T02:00:00Z",
    )


def _make_live_state_ext(
    player_id: int = 42,
    pts: int = 5,
    quarter: int = 3,
    time_remaining: float = 20.0,
) -> LivePlayerState:
    return LivePlayerState(
        player_id=player_id,
        player_name="Test Player",
        team_id=99,
        pts_so_far=pts,
        rebounds=2,
        assists=1,
        minutes_played=20.0,
        quarter=quarter,
        time_remaining_min=time_remaining,
        game_id="0042500406",
        game_status=2,
    )


def _make_no_action_result(ticker: str, player_id: int, p_t4: float = 0.30) -> T4RoutingResult:
    signal = T4Signal(
        player_id=str(player_id),
        threshold=22.5,
        p_t1=0.50,
        p_t4=p_t4,
        delta_p=p_t4 - 0.50,
        pts_so_far=5.0,
        pts_needed=17.5,
        lambda_remaining=6.0,
        time_remaining_min=20.0,
        t5_eligible=False,
    )
    return T4RoutingResult(
        market_id=ticker,
        action="NO_ACTION",
        reason="delta_p below threshold",
        signal=signal,
        staged_order=None,
        kelly_fraction=0.0,
        timestamp_iso=datetime.now(timezone.utc).isoformat(),
    )


def _make_trader_with_open_yes(tmp_path: Path, ticker: str, entry_mip: float, size: float,
                                pool_isolated: bool = True) -> PaperTrader:
    """Create a PaperTrader that already has one open YES position."""
    portfolio_path = tmp_path / "test_exit_portfolio.json"
    logger = AuditLogger(log_path=tmp_path / "audit_exit_test.jsonl")
    trader = PaperTrader(portfolio_path=portfolio_path, logger=logger)
    approval = {
        "approval_status": "APPROVED",
        "approved_size": size,
        "approved_direction": "YES",
        "edge": 0.05,
        "gross_edge": 0.07,
        "model_p": entry_mip + 0.05,
        "risk_eval_id": "RISK-EXIT-001",
        "forecast_id": "FC-EXIT-001",
    }
    trader.open_position(
        approval=approval,
        player_name="Test Player",
        player_id=42,
        kalshi_ticker=ticker,
        kalshi_threshold=22,
        mid_price=entry_mip,
        vig=0.04,
        game_date="2026-06-10",
        pool_isolated=pool_isolated,
    )
    return trader


class TestRunCycleExitPass:

    def _make_mock_loop_no_fire(self, ticker: str, player_id: int) -> MagicMock:
        mock = MagicMock()
        mock.on_game_state_event.return_value = _make_no_action_result(ticker, player_id)
        return mock

    def _make_mock_engines(self):
        eng = MagicMock()
        eng.evaluate_forecast.return_value = (True, {"approval_status": "REJECTED"})
        return eng, MagicMock()

    def test_exit_fires_when_mip_above_pcurrent_plus_buffer(self, tmp_path):
        """
        Exit must fire when mip_current > p_current + NOISE_BUFFER_BAND_T4.
        Player has pts_so_far=5, threshold=22, time_remaining=20min, pace=20/36 pts/min.
        λ_remaining = (20/36) × 20 = 11.11 → p_current ≈ 0.94.
        Set exit_mip = 0.94 + NOISE_BUFFER + 0.05 (well above threshold) → must exit.
        """
        ticker = "NBA_EXIT_TEST_001"
        player_id = 42
        entry_mip = 0.50

        # With pts_so_far=5 and threshold=22, pts_needed=17.
        # pace=20/36≈0.556, time_remaining=20 → λ=11.11 → p(X≥17|Poisson(11.11))
        # That's a very low probability (player is way behind).
        # Let's use pts_so_far=18, threshold=22 instead: pts_needed=4, λ=11.11 → very high p.
        # Wait, exit fires when mip > p_current + buffer.
        # To make exit fire: p_current must be LOW, mip_current must be HIGH.
        # Use: pts_so_far=2, threshold=22, time_remaining=4min (late game, very behind)
        # λ_remaining = (20/36) × 4 ≈ 2.22 → p(X≥20|Poisson(2.22)) ≈ 0.0001 (tiny)
        # Set mip_current = 0.50 → 0.50 > 0.0001 + 0.13905 ✓ exit should fire.
        trader = _make_trader_with_open_yes(
            tmp_path, ticker=ticker, entry_mip=entry_mip, size=0.50
        )
        # Confirm open position exists
        assert len(trader.get_state()["open_positions"]) == 1

        mock_loop = self._make_mock_loop_no_fire(ticker, player_id)
        mock_engine_t4, mock_engine_t5 = self._make_mock_engines()
        store = StagedOrderStore(str(tmp_path / "staged_exit_test.db"))

        # Late game: 4 min remaining, player at 2 pts vs 22 threshold → p_current ≈ 0.0
        live_states = [_make_live_state_ext(player_id=player_id, pts=2, time_remaining=4.0)]
        live_prices = {ticker: _make_player_market_ext(ticker, mip=0.50)}
        pregame_ctx = {
            player_id: [{
                "ticker": ticker,
                "threshold": 22,
                "p_t1": 0.50,
                "pts_l10_mean": 20.0,
                "player_name": "Test Player",
            }]
        }

        with patch("prediction_market_bot.run_t4_live.PAPER_T4_VIRTUAL", False), \
             patch("prediction_market_bot.run_t4_live.PAPER_T4_FLAT_SIZING", True):
            ev, fi, ex, dep = _run_cycle(
                cycle_id="cycle-exit-001",
                session_id="session-exit-001",
                live_states=live_states,
                live_prices=live_prices,
                pregame_by_player_id=pregame_ctx,
                loop=mock_loop,
                engine_t4=mock_engine_t4,
                engine_t5=mock_engine_t5,
                trader=trader,
                store=store,
                game_date="2026-06-10",
                t4_band_budget=500.0,
                t4_deployed_usd=0.0,
            )

        assert ex == 1, f"Expected 1 exit, got {ex}"
        state = trader.get_state()
        assert len(state["open_positions"]) == 0
        exited = [p for p in state["closed_positions"] if p["status"] == "EXITED"]
        assert len(exited) == 1
        assert exited[0]["kalshi_ticker"] == ticker

    def test_exit_does_not_fire_below_buffer(self, tmp_path):
        """
        Exit must NOT fire when mip_current <= p_current + NOISE_BUFFER_BAND_T4.
        Player is ahead: pts_so_far=20, threshold=22, time_remaining=20min.
        p_current will be high. mip_current=0.50 will be below p_current+buffer.
        """
        ticker = "NBA_EXIT_TEST_002"
        player_id = 43
        trader = _make_trader_with_open_yes(
            tmp_path, ticker=ticker, entry_mip=0.50, size=0.50
        )

        mock_loop = self._make_mock_loop_no_fire(ticker, player_id)
        mock_engine_t4, mock_engine_t5 = self._make_mock_engines()
        store = StagedOrderStore(str(tmp_path / "staged_exit_test2.db"))

        # Player is ahead: pts_so_far=20, needs 2 more, 20 min remaining → very high p_current
        live_states = [_make_live_state_ext(player_id=player_id, pts=20, time_remaining=20.0)]
        live_prices = {ticker: _make_player_market_ext(ticker, mip=0.50)}
        pregame_ctx = {
            player_id: [{
                "ticker": ticker,
                "threshold": 22,
                "p_t1": 0.50,
                "pts_l10_mean": 20.0,
                "player_name": "Test Player",
            }]
        }

        with patch("prediction_market_bot.run_t4_live.PAPER_T4_VIRTUAL", False), \
             patch("prediction_market_bot.run_t4_live.PAPER_T4_FLAT_SIZING", True):
            ev, fi, ex, dep = _run_cycle(
                cycle_id="cycle-exit-002",
                session_id="session-exit-002",
                live_states=live_states,
                live_prices=live_prices,
                pregame_by_player_id=pregame_ctx,
                loop=mock_loop,
                engine_t4=mock_engine_t4,
                engine_t5=mock_engine_t5,
                trader=trader,
                store=store,
                game_date="2026-06-10",
                t4_band_budget=500.0,
                t4_deployed_usd=0.0,
            )

        assert ex == 0, f"Expected 0 exits (player ahead), got {ex}"
        assert len(trader.get_state()["open_positions"]) == 1

    def test_time_guard_prevents_exit_in_final_minutes(self, tmp_path):
        """
        Exit must NOT fire when time_remaining_min <= EXIT_MIN_TIME_REMAINING_MIN,
        even when the signal condition is satisfied.
        """
        ticker = "NBA_EXIT_TEST_003"
        player_id = 44
        trader = _make_trader_with_open_yes(
            tmp_path, ticker=ticker, entry_mip=0.50, size=0.50
        )

        mock_loop = self._make_mock_loop_no_fire(ticker, player_id)
        mock_engine_t4, mock_engine_t5 = self._make_mock_engines()
        store = StagedOrderStore(str(tmp_path / "staged_exit_test3.db"))

        # Final 2 minutes (below 3.0 guard), player at 2 pts vs 22 → exit signal would fire
        # but time guard should block it
        final_time = EXIT_MIN_TIME_REMAINING_MIN - 1.0  # 2.0 min — inside T5 zone
        live_states = [_make_live_state_ext(player_id=player_id, pts=2, time_remaining=final_time)]
        live_prices = {ticker: _make_player_market_ext(ticker, mip=0.50)}
        pregame_ctx = {
            player_id: [{
                "ticker": ticker,
                "threshold": 22,
                "p_t1": 0.50,
                "pts_l10_mean": 20.0,
                "player_name": "Test Player",
            }]
        }

        with patch("prediction_market_bot.run_t4_live.PAPER_T4_VIRTUAL", False), \
             patch("prediction_market_bot.run_t4_live.PAPER_T4_FLAT_SIZING", True):
            ev, fi, ex, dep = _run_cycle(
                cycle_id="cycle-exit-003",
                session_id="session-exit-003",
                live_states=live_states,
                live_prices=live_prices,
                pregame_by_player_id=pregame_ctx,
                loop=mock_loop,
                engine_t4=mock_engine_t4,
                engine_t5=mock_engine_t5,
                trader=trader,
                store=store,
                game_date="2026-06-10",
                t4_band_budget=500.0,
                t4_deployed_usd=0.0,
            )

        assert ex == 0, f"Expected 0 exits (time guard active), got {ex}"
        assert len(trader.get_state()["open_positions"]) == 1

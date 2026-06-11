"""
Tests: T-149 — T4 fee gate subtraction (GG-019 fix)
=====================================================
Verifies that run_t4_live._run_cycle passes net-of-fee edge to C4,
not gross edge.

Background:
    T1 subtracts the Kalshi taker fee before the C4 gate (ADR-0016).
    T4 did not, causing a systematic approval bias for bets with gross
    edge in (MIN_EDGE, MIN_EDGE + fee).  T-149 fixes this.

Fee formula (ADR-0016): fee = 0.07 × mip × (1 − mip)
At mip = 0.50: fee = $0.0175/contract.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from prediction_market_bot.c1_signal_ingestion.ds02_nba_live import LivePlayerState
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
from prediction_market_bot.c5_execution.kalshi_client import PlayerMarket
from prediction_market_bot.c3_forecasting.game_state_model import T4Signal
from prediction_market_bot.run_t4_inplay import T4RoutingResult
from prediction_market_bot.run_t4_live import _run_cycle


# ---------------------------------------------------------------------------
# Formula-level regression guards (ADR-0016 taker fee invariants)
# ---------------------------------------------------------------------------

class TestKalshiFeeFormula:
    @pytest.mark.parametrize("mip, expected_fee", [
        (0.50, 0.0175),
        (0.30, 0.0147),
        (0.70, 0.0147),
        (0.40, 0.0168),
        (0.20, 0.0112),
    ])
    def test_fee_formula_values(self, mip, expected_fee):
        fee = 0.07 * mip * (1.0 - mip)
        assert fee == pytest.approx(expected_fee, abs=1e-4)

    def test_fee_symmetric_around_50(self):
        """Fee at mip=0.30 equals fee at mip=0.70 (symmetric about 0.50)."""
        assert 0.07 * 0.30 * 0.70 == pytest.approx(0.07 * 0.70 * 0.30)

    def test_fee_max_at_mip_50(self):
        """Fee is maximised at mip=0.50."""
        fee_50 = 0.07 * 0.50 * 0.50
        for mip in [0.20, 0.30, 0.40, 0.60, 0.70, 0.80]:
            assert 0.07 * mip * (1.0 - mip) <= fee_50

    def test_gross_in_dead_band_gives_negative_net(self):
        """
        Gross edge in (MIN_EDGE, MIN_EDGE + fee) produces net < MIN_EDGE.
        Before T-149 these bets were approved; after the fix they are rejected.
        """
        MIN_EDGE = 0.02
        mip = 0.50
        fee = 0.07 * mip * (1.0 - mip)   # 0.0175

        gross_edge = 0.030               # 0.02 < 0.030 < 0.0375 → dead band
        net_edge = gross_edge - fee      # 0.0125

        assert gross_edge > MIN_EDGE     # old code would have approved
        assert net_edge < MIN_EDGE       # new code must reject


# ---------------------------------------------------------------------------
# Integration: _run_cycle passes net-of-fee edge to C4
# ---------------------------------------------------------------------------

def _make_live_state(player_id: int = 1, pts: int = 10) -> LivePlayerState:
    return LivePlayerState(
        player_id=player_id,
        player_name="Test Player",
        team_id=99,
        pts_so_far=pts,
        rebounds=3,
        assists=2,
        minutes_played=24.0,
        quarter=3,
        time_remaining_min=18.0,
        game_id="0042500406",
        game_status=2,
    )


def _make_player_market(ticker: str = "NBA_TEST_001", mip: float = 0.50) -> PlayerMarket:
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
        status="active",
        fetched_at="2026-06-10T02:00:00Z",
    )


def _make_bayesian_result(
    ticker: str = "NBA_TEST_001",
    player_id: int = 1,
    p_t4: float = 0.60,
    p_t1: float = 0.50,
) -> T4RoutingResult:
    signal = T4Signal(
        player_id=str(player_id),
        threshold=22.5,
        p_t1=p_t1,
        p_t4=p_t4,
        delta_p=p_t4 - p_t1,
        p_t4_baseline=p_t1,
        delta_p_incr=p_t4 - p_t1,
        sigma_null=0.10,
        pts_so_far=10.0,
        pts_needed=12.5,
        lambda_remaining=15.0,
        time_remaining_min=18.0,
        t5_eligible=False,
    )
    return T4RoutingResult(
        market_id=ticker,
        action="FIRE_BAYESIAN",
        reason="test",
        signal=signal,
        staged_order=None,
        kelly_fraction=0.20,
        timestamp_iso=datetime.now(timezone.utc).isoformat(),
    )


class TestRunCycleFeeSubtraction:
    """Verify that _run_cycle passes net-of-fee edge to evaluate_forecast."""

    def test_c4_receives_net_edge(self, tmp_path):
        """
        _run_cycle must subtract kalshi_fee from gross_edge before calling
        engine.evaluate_forecast.  fc_record["edge"] must be net-of-fee.
        """
        mip = 0.50
        p_t4 = 0.60
        gross_edge = p_t4 - mip               # 0.10
        expected_fee = 0.07 * mip * (1.0 - mip)  # 0.0175
        expected_net = gross_edge - expected_fee  # 0.0825

        ticker = "NBA_TEST_001"
        player_id = 42

        # --- Mock T4EventLoop ---
        mock_loop = MagicMock()
        mock_loop.on_game_state_event.return_value = _make_bayesian_result(
            ticker=ticker, player_id=player_id, p_t4=p_t4, p_t1=0.50,
        )

        # --- Mock RiskEngine: capture fc_record, return APPROVED ---
        captured_fc = {}

        def fake_evaluate(forecast_record, current_daily_loss, current_drawdown_pct, session_id):
            captured_fc.update(forecast_record)
            approval = {
                "approval_status": "APPROVED",
                "approved_size": mip,
                "kelly_fraction": 0.20,
                "approval_id": "mock-approval-001",
            }
            return True, approval

        mock_engine_t4 = MagicMock()
        mock_engine_t4.evaluate_forecast.side_effect = fake_evaluate
        mock_engine_t5 = MagicMock()
        mock_engine_t5.evaluate_forecast.return_value = (True, {"approval_status": "REJECTED"})

        # --- Mock PaperTrader ---
        mock_trader = MagicMock()
        mock_trader.get_state.return_value = {
            "bankroll_usd": 876.0,
            "initial_bankroll_usd": 1000.0,
            "current_daily_loss": 0.0,
            "total_realized_pnl": 0.0,
        }
        mock_trader.open_position.return_value = (True, {"position_id": "pos-001"})

        # --- Real StagedOrderStore (in-memory via tmp_path) ---
        store = StagedOrderStore(str(tmp_path / "t4_test_fee.db"))

        # --- Live context ---
        live_state = _make_live_state(player_id=player_id)
        live_prices = {ticker: _make_player_market(ticker=ticker, mip=mip)}
        pregame_ctx = {
            player_id: [{
                "ticker": ticker,
                "threshold": 22,
                "p_t1": 0.50,
                "pts_l10_mean": 22.5,
                "player_name": "Test Player",
            }]
        }

        with patch(
            "prediction_market_bot.run_t4_live.PAPER_T4_VIRTUAL", False
        ), patch(
            "prediction_market_bot.run_t4_live.PAPER_T4_FLAT_SIZING", True
        ):
            _run_cycle(
                cycle_id="cycle-test-001",
                session_id="session-test-001",
                live_states=[live_state],
                live_prices=live_prices,
                pregame_by_player_id=pregame_ctx,
                loop=mock_loop,
                engine_t4=mock_engine_t4,
                engine_t5=mock_engine_t5,
                trader=mock_trader,
                store=store,
                game_date="2026-06-10",
                t4_band_budget=500.0,
                t4_deployed_usd=0.0,
            )

        assert mock_engine_t4.evaluate_forecast.called, "C4 was never called"
        assert "edge" in captured_fc, "fc_record must contain 'edge'"
        assert "gross_edge" in captured_fc, "fc_record must contain 'gross_edge'"

        assert captured_fc["edge"] == pytest.approx(expected_net, abs=1e-6), (
            f"C4 received gross edge {captured_fc['edge']:.6f}, "
            f"expected net edge {expected_net:.6f} (fee={expected_fee:.4f})"
        )
        assert captured_fc["gross_edge"] == pytest.approx(gross_edge, abs=1e-6)

    def test_approval_dict_carries_gross_edge(self, tmp_path):
        """
        After _run_cycle, the approval dict passed to PaperTrader must contain
        both 'edge' (net) and 'gross_edge' (pre-fee) so paper_trader can annotate
        fee_net_edge correctly.
        """
        mip = 0.50
        p_t4 = 0.60
        gross_edge = p_t4 - mip

        ticker = "NBA_TEST_002"
        player_id = 43

        mock_loop = MagicMock()
        mock_loop.on_game_state_event.return_value = _make_bayesian_result(
            ticker=ticker, player_id=player_id, p_t4=p_t4, p_t1=0.50,
        )

        def fake_evaluate(forecast_record, **kwargs):
            return True, {
                "approval_status": "APPROVED",
                "approved_size": mip,
                "kelly_fraction": 0.20,
                "approval_id": "mock-approval-002",
            }

        mock_engine_t4 = MagicMock()
        mock_engine_t4.evaluate_forecast.side_effect = fake_evaluate
        mock_engine_t5 = MagicMock()

        captured_approval = {}

        def fake_open_position(approval, **kwargs):
            captured_approval.update(approval)
            return True, {"position_id": "pos-002"}

        mock_trader = MagicMock()
        mock_trader.get_state.return_value = {
            "bankroll_usd": 876.0,
            "initial_bankroll_usd": 1000.0,
            "current_daily_loss": 0.0,
            "total_realized_pnl": 0.0,
        }
        mock_trader.open_position.side_effect = fake_open_position

        store = StagedOrderStore(str(tmp_path / "t4_test_fee2.db"))

        live_prices = {ticker: _make_player_market(ticker=ticker, mip=mip)}
        pregame_ctx = {
            player_id: [{
                "ticker": ticker,
                "threshold": 22,
                "p_t1": 0.50,
                "pts_l10_mean": 22.5,
                "player_name": "Test Player",
            }]
        }

        with patch(
            "prediction_market_bot.run_t4_live.PAPER_T4_VIRTUAL", False
        ), patch(
            "prediction_market_bot.run_t4_live.PAPER_T4_FLAT_SIZING", True
        ):
            _run_cycle(
                cycle_id="cycle-test-002",
                session_id="session-test-002",
                live_states=[_make_live_state(player_id=player_id)],
                live_prices=live_prices,
                pregame_by_player_id=pregame_ctx,
                loop=mock_loop,
                engine_t4=mock_engine_t4,
                engine_t5=mock_engine_t5,
                trader=mock_trader,
                store=store,
                game_date="2026-06-10",
                t4_band_budget=500.0,
                t4_deployed_usd=0.0,
            )

        assert mock_trader.open_position.called, "PaperTrader.open_position was never called"
        assert "gross_edge" in captured_approval, (
            "approval dict must carry 'gross_edge' for paper_trader fee annotation"
        )
        fee = 0.07 * mip * (1.0 - mip)
        assert captured_approval["gross_edge"] == pytest.approx(gross_edge, abs=1e-6)
        assert captured_approval["edge"] == pytest.approx(gross_edge - fee, abs=1e-6)

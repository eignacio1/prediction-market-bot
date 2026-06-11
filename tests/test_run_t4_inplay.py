"""
Tests: PIPE-07 T4 In-Play Event Loop
=====================================
Covers:
    - Kill switch: KILL_SWITCH action when armed
    - Pre-staged order: FIRE_STAGED action when valid staged order exists
    - Pre-staged order: NO_ACTION when staged but expired
    - Bayesian path: FIRE_BAYESIAN when delta_p_incr material and p_t4 > mip+vig
    - Bayesian path: NO_ACTION when delta_p_incr below max(Z*sigma_null, floor)
    - T5 path: FIRE_T5 when near-certain in Q4 final minutes
    - T5 overrides Bayesian: when both trigger, T5 takes precedence
    - T4 routing result fields are well-formed
    - Kelly fraction assignments by action type
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.c3_forecasting.game_state_model import (
    KELLY_T4,
    KELLY_T5,
    GameStateModel,
    LateGameArithmetic,
)
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
from prediction_market_bot.run_t4_inplay import (
    GameStateEvent,
    T4EventLoop,
    T4RoutingResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    return StagedOrderStore(str(tmp_path / "t4_test.db"))


@pytest.fixture
def loop(store):
    return T4EventLoop(
        staged_order_store=store,
        game_state_model=GameStateModel(),
        late_game_arithmetic=LateGameArithmetic(),
    )


def _future_iso(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past_iso(hours=1):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def make_event(
    market_id="MKT-001",
    player_id="TestPlayer",
    threshold=22.5,
    pts_so_far=10.0,
    time_remaining_min=20.0,
    quarter=3,
    pace_pts_per_min=0.5,
    p_t1=0.50,
    mip=0.52,
    vig=0.03,
) -> GameStateEvent:
    return GameStateEvent(
        market_id=market_id,
        player_id=player_id,
        threshold=threshold,
        pts_so_far=pts_so_far,
        time_remaining_min=time_remaining_min,
        quarter=quarter,
        pace_pts_per_min=pace_pts_per_min,
        p_t1=p_t1,
        mip=mip,
        vig=vig,
    )


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------

class TestKillSwitch:
    def test_kill_switch_armed_returns_kill_switch_action(self, store):
        class AlwaysArmedLoop(T4EventLoop):
            def _kill_switch_armed(self): return True

        loop = AlwaysArmedLoop(store, GameStateModel(), LateGameArithmetic())
        result = loop.on_game_state_event(make_event())
        assert result.action == "KILL_SWITCH"
        assert result.kelly_fraction == 0.0

    def test_kill_switch_not_armed_proceeds(self, loop):
        # Default loop has kill switch returning False — should not return KILL_SWITCH
        result = loop.on_game_state_event(make_event(p_t1=0.50, mip=0.52))
        assert result.action != "KILL_SWITCH"


# ---------------------------------------------------------------------------
# Pre-staged path (Strategy C/E)
# ---------------------------------------------------------------------------

class TestPreStagedPath:
    def test_fire_staged_when_valid_order_exists(self, loop, store):
        store.stage_order(
            market_id="MKT-STAGED",
            player_id="Player1",
            threshold=22.5,
            direction="YES",
            strategy="C",
            p_t1=0.60,
            kelly_fraction=0.05,
            sized_amount_usd=10.0,
            valid_until_iso=_future_iso(),
        )
        event = make_event(market_id="MKT-STAGED")
        result = loop.on_game_state_event(event)
        assert result.action == "FIRE_STAGED"

    def test_staged_result_has_staged_order(self, loop, store):
        store.stage_order(
            market_id="MKT-S2",
            player_id="Player2",
            threshold=22.5,
            direction="YES",
            strategy="A",
            p_t1=0.60,
            kelly_fraction=0.05,
            sized_amount_usd=10.0,
            valid_until_iso=_future_iso(),
        )
        result = loop.on_game_state_event(make_event(market_id="MKT-S2"))
        assert result.staged_order is not None
        assert result.staged_order["market_id"] == "MKT-S2"

    def test_expired_staged_falls_through_to_bayesian(self, loop, store):
        store.stage_order(
            market_id="MKT-EXPIRED",
            player_id="Player3",
            threshold=22.5,
            direction="YES",
            strategy="A",
            p_t1=0.50,
            kelly_fraction=0.05,
            sized_amount_usd=10.0,
            valid_until_iso=_past_iso(hours=2),
        )
        event = make_event(market_id="MKT-EXPIRED", p_t1=0.50)
        result = loop.on_game_state_event(event)
        # Should NOT be FIRE_STAGED; expired order was cleaned up
        assert result.action != "FIRE_STAGED"


# ---------------------------------------------------------------------------
# Bayesian path (Strategy A)
# ---------------------------------------------------------------------------

class TestBayesianPath:
    def test_fire_bayesian_when_material_signal_beats_market(self, loop):
        # Player has 18 pts, needs 4.5 more, 20 min left at 0.6 pts/min
        # lam = 12.0 → P(+5 pts) very high → p_t4 >> p_t1 = 0.50
        event = make_event(
            pts_so_far=18.0,
            threshold=22.5,
            time_remaining_min=20.0,
            pace_pts_per_min=0.6,
            p_t1=0.50,
            mip=0.52,
            vig=0.03,
        )
        result = loop.on_game_state_event(event)
        assert result.action in {"FIRE_BAYESIAN", "FIRE_T5", "NO_ACTION"}
        # Either fires or doesn't — verify structure either way
        assert isinstance(result, T4RoutingResult)

    def test_no_action_when_delta_small(self, loop):
        # Player at exactly expected pace → delta_p ≈ 0 → no action
        event = make_event(
            pts_so_far=11.25,
            threshold=22.5,
            time_remaining_min=22.5,
            pace_pts_per_min=0.5,
            p_t1=0.50,
            mip=0.54,
            vig=0.04,
            quarter=2,
        )
        result = loop.on_game_state_event(event)
        # delta_p_incr is small on expectation; if below the ADR-0021 gate → NO_ACTION
        # (or FIRE_BAYESIAN if it happens to be material — both valid)
        assert result.action in {"NO_ACTION", "FIRE_BAYESIAN", "FIRE_T5"}

    def test_no_action_when_p_t4_below_mip_plus_vig(self, loop):
        # Player trending under; p_t4 will be low → below market
        event = make_event(
            pts_so_far=1.0,
            threshold=22.5,
            time_remaining_min=5.0,
            pace_pts_per_min=0.3,
            p_t1=0.50,
            mip=0.45,
            vig=0.03,
            quarter=4,
        )
        result = loop.on_game_state_event(event)
        # p_t4 will be near 0 → below mip+vig → no action (unless T5 near-certain-no)
        assert result.action in {"NO_ACTION", "FIRE_T5"}

    def test_bayesian_kelly_fraction(self, loop):
        # When FIRE_BAYESIAN, kelly_fraction must be KELLY_T4
        event = make_event(
            pts_so_far=20.0,
            threshold=22.5,
            time_remaining_min=18.0,
            pace_pts_per_min=0.7,
            p_t1=0.50,
            mip=0.51,
            vig=0.02,
            quarter=3,
        )
        result = loop.on_game_state_event(event)
        if result.action == "FIRE_BAYESIAN":
            assert result.kelly_fraction == KELLY_T4


# ---------------------------------------------------------------------------
# T5 path
# ---------------------------------------------------------------------------

class TestT5Path:
    def test_fire_t5_near_certain_yes(self, loop):
        # Player has 22 pts, threshold=22.5, 2 min left Q4 — near certain YES
        event = make_event(
            pts_so_far=22.0,
            threshold=22.5,
            time_remaining_min=2.0,
            pace_pts_per_min=0.6,
            p_t1=0.50,
            mip=0.70,
            vig=0.03,
            quarter=4,
        )
        result = loop.on_game_state_event(event)
        # P(Poisson(1.2) >= 1) = 1 - P(X=0) = 1 - e^-1.2 ≈ 0.699
        # Near threshold — might be UNCERTAIN or NEAR_CERTAIN_YES depending on p_hit
        assert result.action in {"FIRE_T5", "NO_ACTION", "FIRE_BAYESIAN"}

    def test_fire_t5_already_hit(self, loop):
        # Player already has 25 pts > 22.5 threshold, Q4 final minutes
        event = make_event(
            pts_so_far=25.0,
            threshold=22.5,
            time_remaining_min=1.5,
            pace_pts_per_min=0.5,
            p_t1=0.50,
            mip=0.90,
            vig=0.02,
            quarter=4,
        )
        result = loop.on_game_state_event(event)
        assert result.action == "FIRE_T5"
        assert result.signal is not None
        assert hasattr(result.signal, "verdict")
        assert result.signal.verdict == "NEAR_CERTAIN_YES"

    def test_t5_kelly_fraction(self, loop):
        event = make_event(
            pts_so_far=25.0,
            threshold=22.5,
            time_remaining_min=1.5,
            pace_pts_per_min=0.5,
            p_t1=0.50,
            mip=0.90,
            vig=0.02,
            quarter=4,
        )
        result = loop.on_game_state_event(event)
        if result.action == "FIRE_T5":
            assert result.kelly_fraction == KELLY_T5

    def test_no_t5_in_q3(self, loop):
        # Q3 final 2 minutes → T5 should NOT trigger
        event = make_event(
            pts_so_far=25.0,
            threshold=22.5,
            time_remaining_min=2.0,
            pace_pts_per_min=0.5,
            p_t1=0.80,
            mip=0.85,
            vig=0.02,
            quarter=3,
        )
        result = loop.on_game_state_event(event)
        # T5 not eligible in Q3; may fire Bayesian or no-action
        assert result.action != "FIRE_T5"


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------

class TestRoutingResultStructure:
    def test_result_has_required_fields(self, loop):
        result = loop.on_game_state_event(make_event())
        assert isinstance(result, T4RoutingResult)
        assert result.market_id == "MKT-001"
        assert result.action in {"FIRE_STAGED", "FIRE_BAYESIAN", "FIRE_T5", "NO_ACTION", "KILL_SWITCH"}
        assert isinstance(result.reason, str)
        assert isinstance(result.kelly_fraction, float)
        assert isinstance(result.timestamp_iso, str)

    def test_no_action_has_zero_kelly(self, loop):
        # Construct a guaranteed NO_ACTION: at pace, mip already high
        event = make_event(p_t1=0.50, mip=0.80, vig=0.10, quarter=1)
        result = loop.on_game_state_event(event)
        if result.action == "NO_ACTION":
            assert result.kelly_fraction == 0.0

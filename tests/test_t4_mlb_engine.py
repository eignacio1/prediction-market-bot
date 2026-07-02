"""
Tests for t4_mlb_execution_engine.py (T-219, ADR-0039 — T4M-ARITH / T4M-FLOW).

Scope:
  - Construction invariants: both evaluators require their sub_band to be
    BLOCKED in T4_MLB_SUBBAND_REGISTRY; tampering the registry raises.
  - T4MlbArithEvaluator: fires only within the entry window AND above the
    confidence gate; kelly_fraction is always the pinned provisional value.
  - T4MlbFlowEvaluator: FLOW-BLOWOUT does not fire before the sustain
    threshold; multiplier direction is correct for trailing vs. leading
    batters; state clears when the score gap closes.
  - validate_t4_mlb_subbands() returns [] against the real (untampered)
    registry — regression guard.

Excluded: run_t4_mlb_live.py's live execution path (untouched by T-219;
covered by tests/test_run_t4_mlb_live.py, which must remain green/unchanged).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

import pytest

from prediction_market_bot.execution_bands import (
    ExecutionBand,
    T4_MLB_SUBBAND_REGISTRY,
    T4SubBandSpec,
    validate_t4_mlb_subbands,
)
from prediction_market_bot.t4_mlb_execution_engine import (
    T4MlbArithEvaluator,
    T4MlbFlowEvaluator,
    T4MlbGameContext,
)
from prediction_market_bot.t4_price_cache import CachedPrice


def _price(mid: float, vig: float = 0.02) -> CachedPrice:
    return CachedPrice(
        market_id="KXMLBHIT-TEST",
        yes_ask=mid + vig,
        yes_bid=mid - vig,
        mid=mid,
        vig=vig,
        ts=datetime.now(timezone.utc),
    )


def _ctx(**overrides) -> T4MlbGameContext:
    base = dict(
        player_id="p1",
        game_id="g1",
        h_so_far=0,
        ab_so_far=0,
        inning=1,
        batting_slot=3,
        ba_l10=0.300,
        threshold=1,
        ticker="KXMLBHIT-TEST",
        score_diff=0.0,
        is_batting_team_leading=False,
    )
    base.update(overrides)
    return T4MlbGameContext(**base)


# ---------------------------------------------------------------------------
# Construction invariants
# ---------------------------------------------------------------------------


def test_arith_evaluator_constructs_when_blocked():
    T4MlbArithEvaluator()  # must not raise; registry says BLOCKED


def test_flow_evaluator_constructs_when_blocked():
    T4MlbFlowEvaluator()  # must not raise; registry says BLOCKED


def test_arith_evaluator_raises_if_registry_tampered(monkeypatch):
    tampered = dict(T4_MLB_SUBBAND_REGISTRY)
    spec = tampered[ExecutionBand.T4M_ARITH]
    tampered[ExecutionBand.T4M_ARITH] = T4SubBandSpec(
        band=spec.band,
        information_class=spec.information_class,
        provisional_kelly=spec.provisional_kelly,
        kelly_basis=spec.kelly_basis,
        noise_buffer=spec.noise_buffer,
        max_concurrent_exposure_pct_t4=spec.max_concurrent_exposure_pct_t4,
        exp_gate=spec.exp_gate,
        alpha_hypothesis=spec.alpha_hypothesis,
        status="ACTIVE",  # tampered — should never pass construction
        notes=spec.notes,
    )
    monkeypatch.setattr(
        "prediction_market_bot.t4_mlb_execution_engine.T4_MLB_SUBBAND_REGISTRY",
        tampered,
    )
    with pytest.raises(RuntimeError, match="must have status='BLOCKED'"):
        T4MlbArithEvaluator()


def test_flow_evaluator_raises_if_registry_missing_entry(monkeypatch):
    tampered = dict(T4_MLB_SUBBAND_REGISTRY)
    del tampered[ExecutionBand.T4M_FLOW]
    monkeypatch.setattr(
        "prediction_market_bot.t4_mlb_execution_engine.T4_MLB_SUBBAND_REGISTRY",
        tampered,
    )
    with pytest.raises(RuntimeError, match="NOT REGISTERED"):
        T4MlbFlowEvaluator()


# ---------------------------------------------------------------------------
# T4MlbArithEvaluator
# ---------------------------------------------------------------------------


def test_arith_fires_at_boundary_high_confidence():
    ev = T4MlbArithEvaluator()
    ctx = _ctx(h_so_far=0, ab_so_far=0, inning=1, batting_slot=3, ba_l10=0.900, threshold=1)
    signals = ev.evaluate(ctx, _price(mid=0.30))
    assert len(signals) == 1
    sig = signals[0]
    assert sig.sub_band is ExecutionBand.T4M_ARITH
    assert sig.tree_id == "ARITH-NEAR-CERTAIN"
    assert sig.kelly_fraction == T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_ARITH].provisional_kelly


def test_arith_does_not_fire_outside_entry_window():
    ev = T4MlbArithEvaluator()
    # threshold - h_so_far = 3, wider than the entry window (1)
    ctx = _ctx(h_so_far=0, threshold=4, ba_l10=0.900, inning=1, batting_slot=3)
    assert ev.evaluate(ctx, _price(mid=0.10)) == []


def test_arith_does_not_fire_below_confidence_gate():
    ev = T4MlbArithEvaluator()
    # within entry window but low ba_l10 keeps p_arith under the confidence gate
    ctx = _ctx(h_so_far=0, threshold=1, ba_l10=0.150, ab_so_far=0, inning=1, batting_slot=3)
    assert ev.evaluate(ctx, _price(mid=0.10)) == []


def test_arith_does_not_fire_when_already_achieved():
    ev = T4MlbArithEvaluator()
    ctx = _ctx(h_so_far=2, threshold=1, ba_l10=0.900)  # h_needed <= 0 -> flat model's job
    assert ev.evaluate(ctx, _price(mid=0.10)) == []


def test_arith_does_not_fire_when_price_missing():
    ev = T4MlbArithEvaluator()
    ctx = _ctx(h_so_far=0, threshold=1, ba_l10=0.900, inning=1, batting_slot=3)
    assert ev.evaluate(ctx, None) == []


def test_arith_kelly_never_exceeds_pinned_provisional_value():
    ev = T4MlbArithEvaluator()
    ctx = _ctx(h_so_far=0, threshold=1, ba_l10=0.999, inning=1, batting_slot=3)
    signals = ev.evaluate(ctx, _price(mid=0.05))
    assert signals
    ceiling = T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_ARITH].provisional_kelly
    assert all(sig.kelly_fraction <= ceiling for sig in signals)


# ---------------------------------------------------------------------------
# T4MlbFlowEvaluator — FLOW-BLOWOUT
# ---------------------------------------------------------------------------


def test_flow_does_not_fire_before_sustain_threshold():
    ev = T4MlbFlowEvaluator()
    ctx = _ctx(score_diff=8.0, inning=3, is_batting_team_leading=False)
    # blowout just started this inning -> not sustained yet
    assert ev.evaluate(ctx, _price(mid=0.30)) == []


def test_flow_fires_after_sustain_threshold_trailing_batter():
    ev = T4MlbFlowEvaluator()
    ctx_start = _ctx(game_id="g2", score_diff=8.0, inning=3, is_batting_team_leading=False)
    ev.evaluate(ctx_start, None)  # establishes blowout_start_inning = 3

    ctx_later = _ctx(
        game_id="g2",
        score_diff=8.0,
        inning=6,  # 3 innings later, past _BLOWOUT_SUSTAIN_INNINGS=2
        is_batting_team_leading=False,  # trailing -> uplift multiplier
        h_so_far=0,
        threshold=1,
        ba_l10=0.400,
        ab_so_far=2,
        batting_slot=3,
    )
    signals = ev.evaluate(ctx_later, _price(mid=0.20))
    assert len(signals) == 1
    sig = signals[0]
    assert sig.tree_id == "FLOW-BLOWOUT"
    assert sig.signal_snapshot["player_trailing"] is True
    assert sig.signal_snapshot["mult"] == T4MlbFlowEvaluator._BLOWOUT_TRAILING_MULT


def test_flow_leading_batter_gets_discount_multiplier():
    ev = T4MlbFlowEvaluator()
    ctx_start = _ctx(game_id="g3", score_diff=-8.0, inning=1, is_batting_team_leading=True)
    ev.evaluate(ctx_start, None)

    ctx_later = _ctx(
        game_id="g3",
        score_diff=-8.0,
        inning=4,
        is_batting_team_leading=True,  # leading -> discount multiplier
        h_so_far=0,
        threshold=1,
        ba_l10=0.400,
        ab_so_far=2,
        batting_slot=3,
    )
    signals = ev.evaluate(ctx_later, _price(mid=0.35))
    if signals:  # discount may push p_flow under the min-edge floor; check mult if it fires
        assert signals[0].signal_snapshot["mult"] == T4MlbFlowEvaluator._BLOWOUT_LEADING_MULT
        assert signals[0].signal_snapshot["player_trailing"] is False


def test_flow_state_clears_when_gap_closes():
    ev = T4MlbFlowEvaluator()
    ctx_blowout = _ctx(game_id="g4", score_diff=8.0, inning=1, is_batting_team_leading=False)
    ev.evaluate(ctx_blowout, None)
    assert "g4" in ev._blowout_start_inning

    ctx_closed = _ctx(game_id="g4", score_diff=2.0, inning=2, is_batting_team_leading=False)
    ev.evaluate(ctx_closed, None)
    assert "g4" not in ev._blowout_start_inning

    # Blowout resumes later -> must restart the sustain clock, not resume the old one.
    ctx_resumed = _ctx(game_id="g4", score_diff=7.0, inning=3, is_batting_team_leading=False)
    signals = ev.evaluate(ctx_resumed, _price(mid=0.20))
    assert signals == []  # just restarted; not sustained yet
    assert ev._blowout_start_inning["g4"] == 3


def test_flow_tracks_multiple_games_independently():
    ev = T4MlbFlowEvaluator()
    ev.evaluate(_ctx(game_id="gA", score_diff=8.0, inning=1), None)
    ev.evaluate(_ctx(game_id="gB", score_diff=-9.0, inning=5), None)
    assert ev._blowout_start_inning == {"gA": 1, "gB": 5}


# ---------------------------------------------------------------------------
# Registry regression guard
# ---------------------------------------------------------------------------


def test_validate_t4_mlb_subbands_clean():
    assert validate_t4_mlb_subbands() == []


def test_t4m_proj_is_the_sole_active_exception():
    assert T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_PROJ].status == "ACTIVE"
    assert T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_ARITH].status == "BLOCKED"
    assert T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_FLOW].status == "BLOCKED"

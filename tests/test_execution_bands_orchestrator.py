"""Tests for execution_bands_orchestrator.py — MultiBandOrchestrator P6 rules."""
import pytest

from prediction_market_bot.execution_bands import ExecutionBand, get_band_config
from prediction_market_bot.execution_bands_orchestrator import (
    BandDecision,
    BandSignal,
    MultiBandOrchestrator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _t1(direction="YES", edge=0.05, kelly=0.25, p=0.60, ticker="KXNBAPTS-TEST-SGA-25"):
    return BandSignal(
        band=ExecutionBand.T1_MULTI_DAY,
        player_name="Shai Gilgeous-Alexander",
        ticker=ticker,
        direction=direction,
        edge=edge,
        p_estimate=p,
        kelly_fraction=kelly,
        momentum_signal="NEUTRAL",
    )

def _t2(direction="YES", edge=0.048, kelly=0.20, ticker="KXNBAPTS-TEST-SGA-25"):
    return BandSignal(
        band=ExecutionBand.T2_SAME_DAY,
        player_name="Shai Gilgeous-Alexander",
        ticker=ticker,
        direction=direction,
        edge=edge,
        p_estimate=0.58,
        kelly_fraction=kelly,
        momentum_signal="NEUTRAL",
    )

def _t3(signal="NEUTRAL", edge=0.045, kelly=0.10, ticker="KXNBAPTS-TEST-SGA-25"):
    return BandSignal(
        band=ExecutionBand.T3_PRE_TIP,
        player_name="Shai Gilgeous-Alexander",
        ticker=ticker,
        direction="YES",
        edge=edge,
        p_estimate=0.57,
        kelly_fraction=kelly,
        momentum_signal=signal,
    )


# ---------------------------------------------------------------------------
# BandSignal
# ---------------------------------------------------------------------------

class TestBandSignal:
    def test_is_actionable_yes_with_positive_edge(self):
        assert _t1(direction="YES", edge=0.05).is_actionable is True

    def test_is_actionable_no_with_positive_edge(self):
        assert _t1(direction="NO", edge=0.03).is_actionable is True

    def test_not_actionable_when_pass(self):
        assert _t1(direction="PASS", edge=0.0).is_actionable is False

    def test_not_actionable_when_zero_edge(self):
        assert _t1(direction="YES", edge=0.0).is_actionable is False

    def test_not_actionable_when_negative_edge(self):
        assert _t1(direction="YES", edge=-0.01).is_actionable is False

    def test_default_momentum_signal_neutral(self):
        assert _t1().momentum_signal == "NEUTRAL"


# ---------------------------------------------------------------------------
# BandDecision
# ---------------------------------------------------------------------------

class TestBandDecision:
    def _decision(self, action="PROCEED", direction="YES", band=ExecutionBand.T1_MULTI_DAY):
        return BandDecision(
            player_name="Shai Gilgeous-Alexander",
            ticker="KXNBAPTS-TEST-SGA-25",
            action=action,
            direction=direction,
            final_band=band,
            final_kelly=0.25,
            final_edge=0.05,
            rationale="test",
        )

    def test_should_proceed_true(self):
        assert self._decision(action="PROCEED").should_proceed is True

    def test_should_proceed_false_for_hold(self):
        assert self._decision(action="HOLD").should_proceed is False

    def test_should_proceed_false_for_pass(self):
        assert self._decision(action="PASS").should_proceed is False

    def test_frozen(self):
        d = self._decision()
        with pytest.raises((AttributeError, TypeError)):
            d.action = "HOLD"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T1 only
# ---------------------------------------------------------------------------

class TestT1Only:
    def _orch(self):
        return MultiBandOrchestrator()

    def test_proceed_on_actionable_t1(self):
        d = self._orch().decide(_t1())
        assert d.action == "PROCEED"

    def test_final_band_is_t1(self):
        d = self._orch().decide(_t1())
        assert d.final_band == ExecutionBand.T1_MULTI_DAY

    def test_kelly_from_t1(self):
        d = self._orch().decide(_t1(kelly=0.25))
        assert d.final_kelly == pytest.approx(0.25)

    def test_direction_preserved(self):
        d = self._orch().decide(_t1(direction="NO"))
        assert d.direction == "NO"

    def test_pass_when_t1_not_actionable(self):
        d = self._orch().decide(_t1(direction="PASS", edge=0.0))
        assert d.action == "PASS"

    def test_pass_direction_is_pass(self):
        d = self._orch().decide(_t1(direction="PASS", edge=0.0))
        assert d.direction == "PASS"

    def test_pass_final_band_still_t1(self):
        d = self._orch().decide(_t1(direction="PASS", edge=0.0))
        assert d.final_band == ExecutionBand.T1_MULTI_DAY

    def test_rationale_not_empty(self):
        d = self._orch().decide(_t1())
        assert len(d.rationale) > 0


# ---------------------------------------------------------------------------
# T1 + T2
# ---------------------------------------------------------------------------

class TestT1AndT2:
    def _orch(self):
        return MultiBandOrchestrator()

    def test_proceed_with_t2(self):
        d = self._orch().decide(_t1(), t2=_t2())
        assert d.action == "PROCEED"

    def test_final_band_is_t2(self):
        d = self._orch().decide(_t1(), t2=_t2())
        assert d.final_band == ExecutionBand.T2_SAME_DAY

    def test_kelly_is_min_of_t1_and_t2(self):
        d = self._orch().decide(_t1(kelly=0.25), t2=_t2(kelly=0.20))
        assert d.final_kelly == pytest.approx(0.20)

    def test_direction_from_t1(self):
        d = self._orch().decide(_t1(direction="NO"), t2=_t2(direction="NO"))
        assert d.direction == "NO"

    def test_t2_not_actionable_falls_back_to_t1(self):
        t2_pass = _t2(direction="PASS", edge=0.0)
        d = self._orch().decide(_t1(), t2=t2_pass)
        assert d.final_band == ExecutionBand.T1_MULTI_DAY

    def test_t1_pass_blocks_t2(self):
        d = self._orch().decide(_t1(direction="PASS", edge=0.0), t2=_t2())
        assert d.action == "PASS"


# ---------------------------------------------------------------------------
# T3 CONFIRM
# ---------------------------------------------------------------------------

class TestT3Confirm:
    def _orch(self):
        return MultiBandOrchestrator()

    def test_proceed_on_t3_confirm(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="CONFIRM"))
        assert d.action == "PROCEED"

    def test_final_band_is_t3(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="CONFIRM"))
        assert d.final_band == ExecutionBand.T3_PRE_TIP

    def test_kelly_is_min_across_active_bands(self):
        # T1=0.25, T3=0.10 → min=0.10
        d = self._orch().decide(_t1(kelly=0.25), t3=_t3(signal="CONFIRM", kelly=0.10))
        assert d.final_kelly == pytest.approx(0.10)

    def test_edge_from_t3(self):
        d = self._orch().decide(_t1(edge=0.05), t3=_t3(signal="CONFIRM", edge=0.058))
        assert d.final_edge == pytest.approx(0.058)

    def test_t3_confirm_with_t2_kelly_min(self):
        # T1=0.25, T2=0.20, T3=0.10 → min=0.10
        d = self._orch().decide(_t1(kelly=0.25), t2=_t2(kelly=0.20), t3=_t3(signal="CONFIRM", kelly=0.10))
        assert d.final_kelly == pytest.approx(0.10)

    def test_rationale_mentions_confirm(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="CONFIRM"))
        assert "CONFIRM" in d.rationale


# ---------------------------------------------------------------------------
# T3 FADE
# ---------------------------------------------------------------------------

class TestT3Fade:
    def _orch(self):
        return MultiBandOrchestrator()

    def test_hold_on_t3_fade(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="FADE"))
        assert d.action == "HOLD"

    def test_direction_preserved_on_hold(self):
        d = self._orch().decide(_t1(direction="YES"), t3=_t3(signal="FADE"))
        assert d.direction == "YES"

    def test_final_band_is_t3_on_fade(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="FADE"))
        assert d.final_band == ExecutionBand.T3_PRE_TIP

    def test_rationale_mentions_fade(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="FADE"))
        assert "FADE" in d.rationale

    def test_t1_pass_still_passes_despite_t3_fade(self):
        d = self._orch().decide(_t1(direction="PASS", edge=0.0), t3=_t3(signal="FADE"))
        assert d.action == "PASS"


# ---------------------------------------------------------------------------
# T3 NEUTRAL
# ---------------------------------------------------------------------------

class TestT3Neutral:
    def _orch(self):
        return MultiBandOrchestrator()

    def test_proceed_on_t3_neutral(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="NEUTRAL"))
        assert d.action == "PROCEED"

    def test_proceeds_at_t1_band_when_no_t2(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="NEUTRAL"))
        assert d.final_band == ExecutionBand.T1_MULTI_DAY

    def test_proceeds_at_t2_band_when_t2_present(self):
        d = self._orch().decide(_t1(), t2=_t2(), t3=_t3(signal="NEUTRAL"))
        assert d.final_band == ExecutionBand.T2_SAME_DAY

    def test_kelly_is_min_of_base_and_t3(self):
        # T1 kelly=0.25, T3 kelly=0.10 → min=0.10
        d = self._orch().decide(_t1(kelly=0.25), t3=_t3(signal="NEUTRAL", kelly=0.10))
        assert d.final_kelly == pytest.approx(0.10)

    def test_rationale_mentions_neutral(self):
        d = self._orch().decide(_t1(), t3=_t3(signal="NEUTRAL"))
        assert "NEUTRAL" in d.rationale


# ---------------------------------------------------------------------------
# batch_decide
# ---------------------------------------------------------------------------

class TestBatchDecide:
    def _orch(self):
        return MultiBandOrchestrator()

    def test_returns_one_decision_per_t1(self):
        t1a = _t1(ticker="T1")
        t1b = _t1(ticker="T2")
        decisions = self._orch().batch_decide([t1a, t1b])
        assert len(decisions) == 2

    def test_matches_t3_by_ticker(self):
        t1 = _t1(ticker="KXNBAPTS-A")
        t3 = _t3(signal="CONFIRM", ticker="KXNBAPTS-A")
        decisions = self._orch().batch_decide([t1], t3_signals=[t3])
        assert decisions[0].final_band == ExecutionBand.T3_PRE_TIP

    def test_t3_ticker_mismatch_not_applied(self):
        t1 = _t1(ticker="KXNBAPTS-A")
        t3 = _t3(signal="CONFIRM", ticker="KXNBAPTS-B")  # different ticker
        decisions = self._orch().batch_decide([t1], t3_signals=[t3])
        assert decisions[0].final_band == ExecutionBand.T1_MULTI_DAY

    def test_empty_t1_returns_empty(self):
        assert self._orch().batch_decide([]) == []

    def test_t2_t3_both_matched(self):
        t1 = _t1(ticker="KXNBAPTS-X")
        t2 = _t2(ticker="KXNBAPTS-X")
        t3 = _t3(signal="CONFIRM", ticker="KXNBAPTS-X")
        decisions = self._orch().batch_decide([t1], t2_signals=[t2], t3_signals=[t3])
        assert decisions[0].action == "PROCEED"
        assert decisions[0].final_band == ExecutionBand.T3_PRE_TIP

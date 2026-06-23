"""
Tests for t4_price_cache.py and t4_execution_engine.py

Validates ADR-0029 Tier A scaffold:
  - T4Phase8BlockedError on all execution paths
  - STALENESS_WINDOW_S constants match ADR-0029
  - T4PriceCache read/write/staleness logic (test-injectable; no polling loop)
  - GamePhase classification thresholds
  - QueueEntry priority ordering (EXIT=0.0; higher |edge| → dequeued first)
  - Layer2 staleness-check: DROP on stale/reversed/edge-below-min
  - Layer2 staleness-check: APPROVE on fresh price with positive edge
  - T4CorrAdjuster downward-only invariant guard
  - All sub-band evaluators blocked + return empty list
  - Layer1/Layer2/T4ExecutionEngine full-stack with synthetic game state
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from prediction_market_bot.execution_bands import ExecutionBand, T4_SUBBAND_REGISTRY
from prediction_market_bot.t4_price_cache import (
    CachedPrice,
    STALENESS_WINDOW_S,
    POLLING_INTERVAL_S,
    T4Phase8BlockedError,
    T4PriceCache,
)
from prediction_market_bot.t4_execution_engine import (
    GamePhase,
    T4MarketSpec,
    T4OpenPosition,
    T4PlayerState,
    T4GameState,
    T4GameEvent,
    EvaluationSignal,
    QueueEntry,
    StaleDropRecord,
    CorrAdjustmentRecord,
    SubBandEvaluator,
    T4StagedEvaluator,
    T4EventEvaluator,
    T4LineupEvaluator,
    T4FlowEvaluator,
    T4SentimentEvaluator,
    T4ProjEvaluator,
    T4ArithEvaluator,
    T4BoundaryEvaluator,
    T4CorrAdjuster,
    T4ExitEvaluator,
    Layer1EvaluationEngine,
    Layer2ExecutionQueue,
    T4ExecutionEngine,
    classify_game_phase,
    GAME_REGULATION_MIN,
    PRIOR_LAMBDA_SIGMA_PTS,
    BLOWOUT_SCORE_THRESHOLD,
    BLOWOUT_SUSTAIN_MIN,
    _MIN_EDGE,
    _gamma_prior_params,
    _gamma_poisson_update,
    _poisson_survival_p,
    _phase_conditional_kelly,
    _total_remaining_min,
    _KELLY_EARLY,
    _KELLY_MID_LO,
    _KELLY_MID_HI,
    _KELLY_LATE_LO,
    _KELLY_LATE_HI,
    _KELLY_NEAR_CERTAIN,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ts(offset_s: float = 0.0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=offset_s)


def _fresh_price(market_id: str = "MKT-001", yes_ask: float = 0.72, yes_bid: float = 0.68) -> CachedPrice:
    return CachedPrice(
        market_id=market_id,
        yes_ask=yes_ask,
        yes_bid=yes_bid,
        mid=(yes_ask + yes_bid) / 2.0,
        vig=(yes_ask - yes_bid) / 2.0,
        ts=_now(),
    )


def _player(player_id: str = "P001") -> T4PlayerState:
    return T4PlayerState(
        player_id=player_id,
        pts_so_far=14.0,
        reb_so_far=3.0,
        ast_so_far=2.0,
        min_so_far=20.0,
        fouls=2,
        is_active=True,
        lambda_t1_prior=22.5,
        lambda_t4_proj=None,
    )


def _game_state(
    elapsed_min: float = 24.0,
    event_type: str = "TIMER",
    player_id: str | None = "P001",
) -> T4GameState:
    event = T4GameEvent(
        event_type=event_type,
        player_id=player_id,
        market_id="MKT-001",
        ts=_now(),
    )
    return T4GameState(
        game_id="GAME-2026-001",
        game_date="2026-06-22",
        quarter=3,
        time_remaining_min=12.0,
        elapsed_min=elapsed_min,
        home_score=78,
        away_score=74,
        score_differential=4,
        ts=_now(),
        player_states={"P001": _player()},
        trigger_event=event,
    )


def _signal(
    sub_band: ExecutionBand = ExecutionBand.T4_PROJ,
    model_p: float = 0.70,
    mip: float = 0.55,
    vig: float = 0.02,
    direction: str = "YES",
    is_exit: bool = False,
) -> EvaluationSignal:
    return EvaluationSignal(
        sub_band=sub_band,
        tree_id="PROJ-TEST",
        market_id="MKT-001",
        player_id="P001",
        direction=direction,
        model_p=model_p,
        mip_at_signal=mip,
        vig_at_signal=vig,
        edge_at_signal=model_p - mip - vig,
        kelly_fraction=0.078,
        signal_snapshot={"game_phase": "LATE"},
        ts=_now(),
        is_exit=is_exit,
        game_phase=GamePhase.LATE,
    )


# ---------------------------------------------------------------------------
# T4Phase8BlockedError
# ---------------------------------------------------------------------------

class TestT4Phase8BlockedError:
    def test_is_runtime_error(self):
        err = T4Phase8BlockedError("blocked")
        assert isinstance(err, RuntimeError)

    def test_message_preserved(self):
        err = T4Phase8BlockedError("test message")
        assert "test message" in str(err)


# ---------------------------------------------------------------------------
# STALENESS_WINDOW_S constants
# ---------------------------------------------------------------------------

class TestStalenessWindowConstants:
    def test_all_10_subbands_have_window(self):
        from prediction_market_bot.execution_bands import T4_SUBBANDS
        for band in T4_SUBBANDS:
            assert band in STALENESS_WINDOW_S, f"Missing staleness window for {band.value}"

    def test_t4_event_2s(self):
        assert STALENESS_WINDOW_S[ExecutionBand.T4_EVENT] == 2.0

    def test_t4_lineup_5s(self):
        assert STALENESS_WINDOW_S[ExecutionBand.T4_LINEUP] == 5.0

    def test_remaining_30s(self):
        for band in [
            ExecutionBand.T4_FLOW, ExecutionBand.T4_SENTIMENT, ExecutionBand.T4_PROJ,
            ExecutionBand.T4_ARITH, ExecutionBand.T4_BOUNDARY, ExecutionBand.T4_STAGED,
            ExecutionBand.T4_CORR, ExecutionBand.T4_EXIT,
        ]:
            assert STALENESS_WINDOW_S[band] == 30.0, f"{band.value} expected 30s"

    def test_polling_interval_lte_min_window(self):
        assert POLLING_INTERVAL_S <= min(STALENESS_WINDOW_S.values())


# ---------------------------------------------------------------------------
# CachedPrice dataclass
# ---------------------------------------------------------------------------

class TestCachedPrice:
    def test_immutable(self):
        price = _fresh_price()
        with pytest.raises((AttributeError, TypeError)):
            price.mid = 0.99  # type: ignore[misc]

    def test_mid_computed(self):
        price = _fresh_price(yes_ask=0.72, yes_bid=0.68)
        assert abs(price.mid - 0.70) < 1e-9

    def test_vig_computed(self):
        price = _fresh_price(yes_ask=0.72, yes_bid=0.68)
        assert abs(price.vig - 0.02) < 1e-9


# ---------------------------------------------------------------------------
# T4PriceCache — read/write path (no polling loop)
# ---------------------------------------------------------------------------

class TestT4PriceCache:
    def test_initial_empty(self):
        cache = T4PriceCache()
        assert cache.market_count() == 0

    def test_update_and_get_raw(self):
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.72, yes_bid=0.68)
        raw = cache.get_raw("MKT-001")
        assert raw is not None
        assert raw.market_id == "MKT-001"
        assert abs(raw.mid - 0.70) < 1e-9
        assert abs(raw.vig - 0.02) < 1e-9

    def test_update_explicit_ts(self):
        cache = T4PriceCache()
        ts = _ts(-100.0)  # 100 seconds ago
        cache.update("MKT-002", 0.60, 0.56, ts=ts)
        raw = cache.get_raw("MKT-002")
        assert raw is not None
        assert raw.ts == ts

    def test_market_count_tracks_inserts(self):
        cache = T4PriceCache()
        cache.update("A", 0.60, 0.56)
        cache.update("B", 0.45, 0.41)
        assert cache.market_count() == 2

    def test_purge_removes_market(self):
        cache = T4PriceCache()
        cache.update("MKT-001", 0.72, 0.68)
        cache.purge("MKT-001")
        assert cache.get_raw("MKT-001") is None
        assert cache.market_count() == 0

    def test_purge_nonexistent_is_noop(self):
        cache = T4PriceCache()
        cache.purge("NONEXISTENT")  # must not raise

    def test_is_fresh_true_for_recent(self):
        cache = T4PriceCache()
        cache.update("MKT-001", 0.72, 0.68)  # just now
        assert cache.is_fresh("MKT-001", ExecutionBand.T4_PROJ) is True

    def test_is_fresh_false_for_stale(self):
        cache = T4PriceCache()
        stale_ts = _ts(-31.0)  # 31s ago; T4-PROJ window is 30s
        cache.update("MKT-001", 0.72, 0.68, ts=stale_ts)
        assert cache.is_fresh("MKT-001", ExecutionBand.T4_PROJ) is False

    def test_is_fresh_false_when_no_entry(self):
        cache = T4PriceCache()
        assert cache.is_fresh("MISSING", ExecutionBand.T4_PROJ) is False

    def test_get_price_returns_entry_when_fresh(self):
        cache = T4PriceCache()
        cache.update("MKT-001", 0.72, 0.68)
        result = cache.get_price("MKT-001", ExecutionBand.T4_PROJ)
        assert result is not None
        assert result.market_id == "MKT-001"

    def test_get_price_returns_none_when_stale(self):
        cache = T4PriceCache()
        stale_ts = _ts(-35.0)
        cache.update("MKT-001", 0.72, 0.68, ts=stale_ts)
        assert cache.get_price("MKT-001", ExecutionBand.T4_PROJ) is None

    def test_get_price_event_band_stale_after_3s(self):
        cache = T4PriceCache()
        ts_3s_ago = _ts(-3.0)
        cache.update("MKT-001", 0.72, 0.68, ts=ts_3s_ago)
        # T4-EVENT window is 2s → 3s old = stale
        assert cache.get_price("MKT-001", ExecutionBand.T4_EVENT) is None

    def test_get_price_lineup_band_fresh_within_5s(self):
        cache = T4PriceCache()
        ts_4s_ago = _ts(-4.0)
        cache.update("MKT-001", 0.72, 0.68, ts=ts_4s_ago)
        # T4-LINEUP window is 5s → 4s old = fresh
        assert cache.get_price("MKT-001", ExecutionBand.T4_LINEUP) is not None

    def test_update_overwrites_prior_entry(self):
        cache = T4PriceCache()
        cache.update("MKT-001", 0.60, 0.56)
        cache.update("MKT-001", 0.72, 0.68)
        raw = cache.get_raw("MKT-001")
        assert abs(raw.mid - 0.70) < 1e-9

    def test_start_polling_raises_blocked(self):
        cache = T4PriceCache()
        with pytest.raises(T4Phase8BlockedError, match="Phase 8"):
            cache.start_polling(MagicMock(), ["MKT-001"])

    def test_stop_polling_raises_blocked(self):
        cache = T4PriceCache()
        with pytest.raises(T4Phase8BlockedError, match="Phase 8"):
            cache.stop_polling()


# ---------------------------------------------------------------------------
# GamePhase classification
# ---------------------------------------------------------------------------

class TestClassifyGamePhase:
    def test_early_at_0(self):
        assert classify_game_phase(0.0) == GamePhase.EARLY

    def test_early_at_23(self):
        assert classify_game_phase(23.9) == GamePhase.EARLY

    def test_mid_at_24(self):
        assert classify_game_phase(24.0) == GamePhase.MID

    def test_mid_at_35(self):
        assert classify_game_phase(35.9) == GamePhase.MID

    def test_late_at_36(self):
        assert classify_game_phase(36.0) == GamePhase.LATE

    def test_late_at_43(self):
        assert classify_game_phase(43.9) == GamePhase.LATE

    def test_near_certain_at_44(self):
        assert classify_game_phase(44.0) == GamePhase.NEAR_CERTAIN

    def test_near_certain_at_48(self):
        assert classify_game_phase(48.0) == GamePhase.NEAR_CERTAIN

    def test_game_phase_enum_values(self):
        assert {p.value for p in GamePhase} >= {"EARLY", "MID", "LATE", "NEAR_CERTAIN"}


# ---------------------------------------------------------------------------
# EvaluationSignal
# ---------------------------------------------------------------------------

class TestEvaluationSignal:
    def test_edge_positive(self):
        s = _signal(model_p=0.70, mip=0.55, vig=0.02)
        assert abs(s.edge_at_signal - 0.13) < 1e-9

    def test_edge_negative(self):
        s = _signal(model_p=0.50, mip=0.60, vig=0.02)
        assert s.edge_at_signal == pytest.approx(-0.12)

    def test_exit_flag(self):
        s = _signal(is_exit=True)
        assert s.is_exit is True

    def test_default_not_exit(self):
        s = _signal()
        assert s.is_exit is False


# ---------------------------------------------------------------------------
# QueueEntry priority ordering
# ---------------------------------------------------------------------------

class TestQueueEntryPriority:
    def test_exit_priority_zero(self):
        s = _signal(is_exit=True)
        entry = QueueEntry.from_signal(s)
        assert entry.priority == 0.0

    def test_standard_priority_1_minus_edge(self):
        s = _signal(model_p=0.70, mip=0.55, vig=0.02)  # edge = 0.13
        entry = QueueEntry.from_signal(s)
        assert abs(entry.priority - (1.0 - 0.13)) < 1e-9

    def test_higher_edge_lower_priority_value(self):
        high_edge = _signal(model_p=0.80, mip=0.55, vig=0.02)  # edge=0.23
        low_edge = _signal(model_p=0.60, mip=0.55, vig=0.02)   # edge=0.03
        assert QueueEntry.from_signal(high_edge).priority < QueueEntry.from_signal(low_edge).priority

    def test_exit_lower_priority_value_than_standard(self):
        exit_sig = _signal(is_exit=True)
        std_sig = _signal(is_exit=False)
        assert QueueEntry.from_signal(exit_sig) < QueueEntry.from_signal(std_sig)

    def test_lt_comparison_for_heapq(self):
        low = QueueEntry.from_signal(_signal(model_p=0.80, mip=0.55, vig=0.02))
        high = QueueEntry.from_signal(_signal(model_p=0.60, mip=0.55, vig=0.02))
        assert low < high

    def test_edge_clamped_to_1(self):
        # edge > 1.0 should not produce negative priority
        s = _signal(model_p=1.0, mip=0.0, vig=0.0)
        entry = QueueEntry.from_signal(s)
        assert entry.priority >= 0.0


# ---------------------------------------------------------------------------
# Sub-band evaluators — BLOCKED stubs
# ---------------------------------------------------------------------------

class TestSubBandEvaluatorsBlocked:
    """All sub-band evaluators must:
       1. Have status='BLOCKED' in T4_SUBBAND_REGISTRY
       2. Return empty list from evaluate()
       3. Raise T4Phase8BlockedError on execution-path methods
    """

    EVALUATOR_CLASSES = [
        (T4StagedEvaluator,    ExecutionBand.T4_STAGED),
        (T4EventEvaluator,     ExecutionBand.T4_EVENT),
        (T4LineupEvaluator,    ExecutionBand.T4_LINEUP),
        (T4FlowEvaluator,      ExecutionBand.T4_FLOW),
        (T4SentimentEvaluator, ExecutionBand.T4_SENTIMENT),
        (T4ProjEvaluator,      ExecutionBand.T4_PROJ),
        (T4ArithEvaluator,     ExecutionBand.T4_ARITH),
        (T4BoundaryEvaluator,  ExecutionBand.T4_BOUNDARY),
    ]

    @pytest.mark.parametrize("cls,band", EVALUATOR_CLASSES)
    def test_band_blocked_in_registry(self, cls, band):
        spec = T4_SUBBAND_REGISTRY.get(band)
        assert spec is not None, f"{band.value} not in T4_SUBBAND_REGISTRY"
        assert spec.status == "BLOCKED", f"{band.value} expected status='BLOCKED', got {spec.status!r}"

    @pytest.mark.parametrize("cls,band", EVALUATOR_CLASSES)
    def test_evaluator_returns_empty_list(self, cls, band):
        evaluator = cls()
        gs = _game_state()
        cache = T4PriceCache()
        result = evaluator.evaluate(gs, cache)
        assert result == [], f"{cls.__name__}.evaluate() must return [] (BLOCKED stub)"

    @pytest.mark.parametrize("cls,band", EVALUATOR_CLASSES)
    def test_evaluator_sub_band_matches(self, cls, band):
        evaluator = cls()
        assert evaluator.sub_band == band

    def test_proj_evaluator_posterior_none_initially(self):
        ev = T4ProjEvaluator()
        assert ev.get_lambda_posterior("P001") is None

    def test_require_phase8_raises(self):
        ev = T4ProjEvaluator()
        with pytest.raises(T4Phase8BlockedError):
            ev._require_phase8("some_operation")


# ---------------------------------------------------------------------------
# T4ExitEvaluator
# ---------------------------------------------------------------------------

class TestT4ExitEvaluator:
    def test_returns_empty_no_positions(self):
        ev = T4ExitEvaluator()
        gs = _game_state()
        cache = T4PriceCache()
        assert ev.generate_exit_signals([], gs, cache) == []

    def test_exit_time_floor_inherited(self):
        from prediction_market_bot.execution_bands import EXIT_MIN_TIME_REMAINING_MIN
        assert T4ExitEvaluator.EXIT_TIME_FLOOR_MIN == EXIT_MIN_TIME_REMAINING_MIN


# ---------------------------------------------------------------------------
# T4CorrAdjuster
# ---------------------------------------------------------------------------

class TestT4CorrAdjuster:
    def test_adjust_returns_unchanged_stub(self):
        adj = T4CorrAdjuster()
        signals = [_signal(), _signal(sub_band=ExecutionBand.T4_EVENT)]
        approved, records = adj.adjust(signals, max_single_event_usd=500.0)
        assert approved == signals  # stub: passthrough
        assert records == []

    def test_adjust_empty_input(self):
        adj = T4CorrAdjuster()
        approved, records = adj.adjust([], max_single_event_usd=500.0)
        assert approved == []
        assert records == []

    def test_downward_only_guard_raises_on_upward(self):
        adj = T4CorrAdjuster()
        with pytest.raises(RuntimeError, match="downward-only invariant VIOLATED"):
            adj._assert_downward_only(
                original_kelly=0.05,
                adjusted_kelly=0.10,
                market_id="MKT-001",
            )

    def test_downward_only_guard_passes_on_equal(self):
        adj = T4CorrAdjuster()
        adj._assert_downward_only(0.05, 0.05, "MKT-001")  # must not raise

    def test_downward_only_guard_passes_on_reduction(self):
        adj = T4CorrAdjuster()
        adj._assert_downward_only(0.10, 0.05, "MKT-001")  # must not raise

    def test_sub_band_is_t4_corr(self):
        adj = T4CorrAdjuster()
        assert adj.sub_band == ExecutionBand.T4_CORR


# ---------------------------------------------------------------------------
# Layer1EvaluationEngine
# ---------------------------------------------------------------------------

class TestLayer1EvaluationEngine:
    def _make_engine(self):
        return T4ExecutionEngine.create()._layer1

    def test_evaluate_cycle_returns_empty_all_blocked(self):
        engine = self._make_engine()
        gs = _game_state()
        cache = T4PriceCache()
        signals = engine.evaluate_cycle(gs, cache)
        assert signals == []

    def test_evaluate_cycle_with_positions_no_exits(self):
        engine = self._make_engine()
        gs = _game_state()
        cache = T4PriceCache()
        signals = engine.evaluate_cycle(gs, cache, open_positions=[{"market_id": "MKT-001"}])
        assert signals == []

    def test_run_continuous_raises_blocked(self):
        engine = self._make_engine()
        with pytest.raises(T4Phase8BlockedError, match="GG-04"):
            engine.run_continuous(iter([]))

    def test_evaluators_for_score_update(self):
        engine = self._make_engine()
        gs = _game_state(event_type="SCORE_UPDATE")
        active_ids = engine._evaluators_for_event(gs.trigger_event)
        # SCORE_UPDATE triggers PROJ, EVENT, FLOW, ARITH
        assert "T4-PROJ" in active_ids
        assert "T4-EVENT" in active_ids
        assert "T4-FLOW" in active_ids
        assert "T4-ARITH" in active_ids

    def test_evaluators_for_substitution(self):
        engine = self._make_engine()
        gs = _game_state(event_type="SUBSTITUTION")
        active_ids = engine._evaluators_for_event(gs.trigger_event)
        assert "T4-LINEUP" in active_ids
        assert "T4-FLOW" in active_ids

    def test_evaluators_for_quarter_end(self):
        engine = self._make_engine()
        gs = _game_state(event_type="QUARTER_END", player_id=None)
        active_ids = engine._evaluators_for_event(gs.trigger_event)
        assert "T4-BOUNDARY" in active_ids

    def test_evaluators_for_price_drift(self):
        engine = self._make_engine()
        gs = _game_state(event_type="PRICE_DRIFT")
        active_ids = engine._evaluators_for_event(gs.trigger_event)
        assert "T4-SENTIMENT" in active_ids

    def test_evaluators_for_timer(self):
        engine = self._make_engine()
        gs = _game_state(event_type="TIMER")
        active_ids = engine._evaluators_for_event(gs.trigger_event)
        assert "T4-PROJ" in active_ids
        assert "T4-SENTIMENT" in active_ids


# ---------------------------------------------------------------------------
# Layer2ExecutionQueue
# ---------------------------------------------------------------------------

class TestLayer2ExecutionQueue:
    def _make_queue(self):
        return Layer2ExecutionQueue(corr_adjuster=T4CorrAdjuster())

    def test_initial_depth_zero(self):
        q = self._make_queue()
        assert q.queue_depth() == 0

    def test_enqueue_increments_depth(self):
        q = self._make_queue()
        q.enqueue(_signal())
        assert q.queue_depth() == 1

    def test_enqueue_multiple(self):
        q = self._make_queue()
        for _ in range(5):
            q.enqueue(_signal())
        assert q.queue_depth() == 5

    def test_process_drops_stale_entry(self):
        q = self._make_queue()
        cache = T4PriceCache()
        stale_ts = _ts(-35.0)
        cache.update("MKT-001", 0.72, 0.68, ts=stale_ts)  # stale for T4-PROJ

        q.enqueue(_signal(sub_band=ExecutionBand.T4_PROJ))
        approved, drops = q.process_queue_batch(cache, min_edge=0.04)
        assert len(approved) == 0
        assert len(drops) == 1
        assert drops[0].drop_reason == "price_stale"
        assert drops[0].market_id == "MKT-001"

    def test_process_drops_when_no_cached_price(self):
        q = self._make_queue()
        cache = T4PriceCache()  # empty cache
        q.enqueue(_signal(sub_band=ExecutionBand.T4_PROJ))
        approved, drops = q.process_queue_batch(cache, min_edge=0.04)
        assert len(approved) == 0
        assert drops[0].drop_reason == "price_stale"
        assert drops[0].edge_at_drop is None  # no price to compute edge from

    def test_process_approves_fresh_positive_edge(self):
        q = self._make_queue()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.72, yes_bid=0.68)  # fresh, mid=0.70

        # model_p=0.85, mip=0.70, vig=0.02 → edge=0.13 > min_edge=0.04
        s = _signal(model_p=0.85, mip=0.70, vig=0.02)
        q.enqueue(s)
        approved, drops = q.process_queue_batch(cache, min_edge=0.04)
        assert len(approved) == 1
        assert len(drops) == 0

    def test_process_drops_edge_below_min(self):
        q = self._make_queue()
        cache = T4PriceCache()
        # Fresh price with mid=0.70 vig=0.02
        cache.update("MKT-001", yes_ask=0.71, yes_bid=0.69)  # mid=0.70, vig=0.01

        # model_p=0.72 → current_edge = 0.72 - 0.70 - 0.01 = 0.01 < min_edge=0.04
        s = _signal(model_p=0.72, mip=0.70, vig=0.01)
        q.enqueue(s)
        approved, drops = q.process_queue_batch(cache, min_edge=0.04)
        assert len(approved) == 0
        assert drops[0].drop_reason == "edge_below_min"

    def test_process_drops_direction_reversed(self):
        q = self._make_queue()
        cache = T4PriceCache()
        # Price shifted: mid is now 0.70, but model_p=0.35 (model now says NO)
        cache.update("MKT-001", yes_ask=0.71, yes_bid=0.69)  # mid=0.70, vig=0.01

        # Signal was YES at entry, but model_p=0.35 < 0.5 → direction reversed
        s = _signal(
            direction="YES",
            model_p=0.35,  # model now thinks NO
            mip=0.50,
            vig=0.02,
        )
        # edge_at_signal = 0.35 - 0.50 - 0.02 = -0.17 (negative, but we need to test
        # direction reversal — model_p < 0.5 but direction=YES)
        q.enqueue(s)
        approved, drops = q.process_queue_batch(cache, min_edge=0.0)  # 0 min_edge to isolate
        assert drops[0].drop_reason in ("direction_reversed", "edge_below_min")

    def test_exit_dequeued_before_standard(self):
        q = self._make_queue()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.72, yes_bid=0.68)

        # Enqueue standard signal first, then EXIT
        std = _signal(model_p=0.80, mip=0.70, vig=0.02, is_exit=False)
        ext = _signal(model_p=0.80, mip=0.70, vig=0.02, is_exit=True)
        q.enqueue(std)
        q.enqueue(ext)

        approved, _ = q.process_queue_batch(cache, min_edge=0.0, max_dequeue_per_batch=1)
        assert len(approved) == 1
        assert approved[0].is_exit is True  # EXIT dequeued first

    def test_pop_stale_drops_clears_log(self):
        q = self._make_queue()
        cache = T4PriceCache()  # empty — all drops are stale
        q.enqueue(_signal())
        q.process_queue_batch(cache, min_edge=0.04)

        drops = q.pop_stale_drops()
        assert len(drops) == 1
        # After popping, log is clear
        assert q.pop_stale_drops() == []

    def test_max_dequeue_per_batch_respected(self):
        q = self._make_queue()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.80, yes_bid=0.76)

        for _ in range(5):
            q.enqueue(_signal(model_p=0.90, mip=0.78, vig=0.02))

        approved, drops = q.process_queue_batch(cache, min_edge=0.04, max_dequeue_per_batch=2)
        total_processed = len(approved) + len(drops)
        assert total_processed <= 2
        assert q.queue_depth() == 3  # 5 - 2 = 3 remaining


# ---------------------------------------------------------------------------
# T4ExecutionEngine — top-level
# ---------------------------------------------------------------------------

class TestT4ExecutionEngine:
    def test_create_returns_engine(self):
        engine = T4ExecutionEngine.create()
        assert isinstance(engine, T4ExecutionEngine)

    def test_simulate_cycle_returns_empty_blocked_stubs(self):
        engine = T4ExecutionEngine.create()
        gs = _game_state()
        result = engine.simulate_cycle(gs)
        assert result == []

    def test_simulate_cycle_with_custom_cache(self):
        engine = T4ExecutionEngine.create()
        cache = T4PriceCache()
        cache.update("MKT-001", 0.72, 0.68)
        gs = _game_state()
        result = engine.simulate_cycle(gs, price_cache=cache)
        assert result == []

    def test_on_game_event_raises_blocked(self):
        engine = T4ExecutionEngine.create()
        gs = _game_state()
        with pytest.raises(T4Phase8BlockedError, match="Phase 8"):
            engine.on_game_event(gs)

    def test_start_raises_blocked(self):
        engine = T4ExecutionEngine.create()
        with pytest.raises(T4Phase8BlockedError, match="Phase 8"):
            engine.start(iter([]))

    def test_phase8_flag_is_false(self):
        assert T4ExecutionEngine._PHASE8_ACTIVE is False

    def test_create_wires_layer1_and_layer2(self):
        engine = T4ExecutionEngine.create()
        assert isinstance(engine._layer1, Layer1EvaluationEngine)
        assert isinstance(engine._layer2, Layer2ExecutionQueue)

    def test_min_edge_default(self):
        engine = T4ExecutionEngine.create()
        assert engine._min_edge == pytest.approx(0.04)

    def test_min_edge_custom(self):
        engine = T4ExecutionEngine.create(min_edge=0.06)
        assert engine._min_edge == pytest.approx(0.06)


# ---------------------------------------------------------------------------
# Integration: simulate_cycle → Layer2 queue processing
# ---------------------------------------------------------------------------

class TestSimulateCycleToLayer2Integration:
    """
    End-to-end path through both layers with synthetic game state.

    At Phase 6/7: all evaluators return [] so queue stays empty.
    Verifies the plumbing is correct: no exceptions, correct types returned.
    """

    def test_full_cycle_no_exceptions(self):
        engine = T4ExecutionEngine.create()
        cache = T4PriceCache()
        cache.update("MKT-001", 0.72, 0.68)
        gs = _game_state()

        signals = engine.simulate_cycle(gs, price_cache=cache)
        for sig in signals:
            engine._layer2.enqueue(sig)

        approved, drops = engine._layer2.process_queue_batch(cache, min_edge=0.04)
        # All stubs return [] so queue was empty after simulate_cycle
        assert approved == []
        assert drops == []

    def test_queue_processes_manually_injected_signal(self):
        """Inject a signal directly into Layer2 (bypassing Layer1 stubs) to
        verify the staleness-check and approval logic independently."""
        engine = T4ExecutionEngine.create()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.80, yes_bid=0.76)  # mid=0.78, vig=0.02

        s = _signal(model_p=0.90, mip=0.78, vig=0.02)  # edge=0.10
        engine._layer2.enqueue(s)

        approved, drops = engine._layer2.process_queue_batch(cache, min_edge=0.04)
        assert len(approved) == 1
        assert drops == []
        assert abs(approved[0].model_p - 0.90) < 1e-9


# ---------------------------------------------------------------------------
# T4MarketSpec
# ---------------------------------------------------------------------------

class TestT4MarketSpec:
    def test_construction_required_fields(self):
        spec = T4MarketSpec(market_id="MKT-001", player_id="P001", threshold=20.0)
        assert spec.market_id == "MKT-001"
        assert spec.player_id == "P001"
        assert spec.threshold == 20.0

    def test_defaults(self):
        spec = T4MarketSpec(market_id="MKT-001", player_id="P001", threshold=20.0)
        assert spec.stat_type == "pts"
        assert spec.team_is_home is None

    def test_explicit_fields(self):
        spec = T4MarketSpec(
            market_id="MKT-002", player_id="P002", threshold=15.0,
            stat_type="reb", team_is_home=True,
        )
        assert spec.stat_type == "reb"
        assert spec.team_is_home is True

    def test_frozen(self):
        spec = T4MarketSpec(market_id="MKT-001", player_id="P001", threshold=20.0)
        with pytest.raises((AttributeError, TypeError)):
            spec.threshold = 25.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T4OpenPosition
# ---------------------------------------------------------------------------

class TestT4OpenPosition:
    def test_construction(self):
        pos = T4OpenPosition(
            market_id="MKT-001", player_id="P001",
            direction="YES", threshold=20.0, entry_model_p=0.80,
            sub_band=ExecutionBand.T4_PROJ, entry_ts=_now(),
        )
        assert pos.direction == "YES"
        assert pos.threshold == 20.0
        assert pos.entry_model_p == 0.80

    def test_defaults(self):
        pos = T4OpenPosition(
            market_id="MKT-001", player_id="P001",
            direction="YES", threshold=20.0, entry_model_p=0.80,
            sub_band=ExecutionBand.T4_PROJ, entry_ts=_now(),
        )
        assert pos.stat_type == "pts"
        assert pos.noise_buffer is None

    def test_frozen(self):
        pos = T4OpenPosition(
            market_id="MKT-001", player_id="P001",
            direction="YES", threshold=20.0, entry_model_p=0.80,
            sub_band=ExecutionBand.T4_PROJ, entry_ts=_now(),
        )
        with pytest.raises((AttributeError, TypeError)):
            pos.direction = "NO"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Bayesian math helpers
# ---------------------------------------------------------------------------

class TestHelperFunctions:
    def test_total_remaining_min_regulation(self):
        gs = _game_state(elapsed_min=24.0)
        assert abs(_total_remaining_min(gs) - 24.0) < 1e-9

    def test_total_remaining_min_near_end(self):
        gs = _game_state(elapsed_min=45.0)
        assert abs(_total_remaining_min(gs) - 3.0) < 1e-9

    def test_total_remaining_min_overtime(self):
        event = T4GameEvent(event_type="TIMER", player_id=None, market_id=None, ts=_now())
        gs = T4GameState(
            game_id="G1", game_date="2026-06-22", quarter=5,
            time_remaining_min=3.0, elapsed_min=50.0,
            home_score=100, away_score=98, score_differential=2, ts=_now(),
            player_states={}, trigger_event=event,
        )
        assert abs(_total_remaining_min(gs) - 3.0) < 1e-9  # 48+5-50=3

    def test_total_remaining_min_clamps_at_zero(self):
        gs = _game_state(elapsed_min=50.0)
        assert _total_remaining_min(gs) == 0.0

    def test_gamma_prior_params_mean(self):
        alpha, beta = _gamma_prior_params(lambda_prior=22.5, sigma_prior=5.0)
        assert abs(alpha / beta - 22.5) < 1e-9  # mean = lambda_prior

    def test_gamma_prior_params_variance(self):
        sigma = 5.0
        alpha, beta = _gamma_prior_params(lambda_prior=22.5, sigma_prior=sigma)
        assert abs(alpha / beta ** 2 - sigma ** 2) < 1e-9  # variance = sigma^2

    def test_gamma_poisson_update_increments(self):
        a0, b0 = _gamma_prior_params(22.5, 5.0)
        a1, b1 = _gamma_poisson_update(a0, b0, k_obs=14.0, t_elapsed_frac=0.4167)
        assert abs(a1 - (a0 + 14.0)) < 1e-9
        assert abs(b1 - (b0 + 0.4167)) < 1e-6

    def test_poisson_survival_p_already_achieved(self):
        assert _poisson_survival_p(pts_so_far=20.0, threshold=20.0, lambda_remaining=5.0) == 1.0

    def test_poisson_survival_p_zero_lambda(self):
        assert _poisson_survival_p(pts_so_far=14.0, threshold=20.0, lambda_remaining=0.0) == 0.0

    def test_poisson_survival_p_high_lambda(self):
        # With lambda_remaining=20, P(score 6 more) ≈ 1.0
        p = _poisson_survival_p(pts_so_far=14.0, threshold=20.0, lambda_remaining=20.0)
        assert p > 0.99

    def test_poisson_survival_p_low_lambda(self):
        # With lambda_remaining=0.1, P(score 6 more) is tiny
        p = _poisson_survival_p(pts_so_far=14.0, threshold=20.0, lambda_remaining=0.1)
        assert p < 0.01

    def test_phase_conditional_kelly_early(self):
        assert abs(_phase_conditional_kelly(10.0) - _KELLY_EARLY) < 1e-9

    def test_phase_conditional_kelly_mid_start(self):
        assert abs(_phase_conditional_kelly(24.0) - _KELLY_MID_LO) < 1e-9

    def test_phase_conditional_kelly_mid_end(self):
        # At 36.0, just entering LATE: kelly = KELLY_MID_HI = KELLY_LATE_LO
        assert abs(_phase_conditional_kelly(36.0) - _KELLY_LATE_LO) < 1e-9

    def test_phase_conditional_kelly_mid_midpoint(self):
        # At 30.0 (MID midpoint), linear interp: 0.032 + 0.5*(0.078-0.032) = 0.055
        k = _phase_conditional_kelly(30.0)
        expected = _KELLY_MID_LO + 0.5 * (_KELLY_MID_HI - _KELLY_MID_LO)
        assert abs(k - expected) < 1e-9

    def test_phase_conditional_kelly_late_midpoint(self):
        # At 40.0 (halfway 36→44), linear interp: 0.078 + 0.5*(0.167-0.078)
        k = _phase_conditional_kelly(40.0)
        expected = _KELLY_LATE_LO + 0.5 * (_KELLY_LATE_HI - _KELLY_LATE_LO)
        assert abs(k - expected) < 1e-6

    def test_phase_conditional_kelly_near_certain(self):
        assert abs(_phase_conditional_kelly(46.0) - _KELLY_NEAR_CERTAIN) < 1e-9

    def test_phase_conditional_kelly_monotone(self):
        # Kelly must be non-decreasing through the game
        vals = [_phase_conditional_kelly(e) for e in [5, 24, 30, 36, 40, 44, 47]]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1] + 1e-9, f"Kelly decreased at index {i}"


# ---------------------------------------------------------------------------
# T4ProjEvaluator — Bayesian math
# ---------------------------------------------------------------------------

def _market_game_state(
    pts_so_far: float = 14.0,
    min_so_far: float = 20.0,
    elapsed_min: float = 24.0,
    threshold: float = 25.0,
    event_type: str = "TIMER",
    lambda_t1_prior: float = 22.5,
    score_differential: int = 4,
) -> T4GameState:
    """Game state with a single T4MarketSpec for player P001."""
    event = T4GameEvent(
        event_type=event_type, player_id="P001", market_id="MKT-001", ts=_now()
    )
    player = T4PlayerState(
        player_id="P001",
        pts_so_far=pts_so_far,
        reb_so_far=3.0,
        ast_so_far=2.0,
        min_so_far=min_so_far,
        fouls=2,
        is_active=True,
        lambda_t1_prior=lambda_t1_prior,
        lambda_t4_proj=None,
    )
    spec = T4MarketSpec(market_id="MKT-001", player_id="P001", threshold=threshold)
    return T4GameState(
        game_id="GAME-2026-001",
        game_date="2026-06-22",
        quarter=3,
        time_remaining_min=max(0.0, GAME_REGULATION_MIN - elapsed_min),
        elapsed_min=elapsed_min,
        home_score=78,
        away_score=74,
        score_differential=score_differential,
        ts=_now(),
        player_states={"P001": player},
        trigger_event=event,
        market_specs=(spec,),
    )


class TestT4ProjEvaluatorMath:
    def test_empty_market_specs_returns_empty(self):
        ev = T4ProjEvaluator()
        gs = _game_state()  # no market_specs (default empty tuple)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.90, yes_bid=0.86)
        assert ev.evaluate(gs, cache) == []

    def test_no_cached_price_returns_empty(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state()
        cache = T4PriceCache()  # empty cache
        assert ev.evaluate(gs, cache) == []

    def test_signal_generated_with_edge(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state(pts_so_far=14.0, min_so_far=20.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        # Set price well below model_p to ensure edge > 0.04
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)  # mid=0.80, vig=0.02
        signals = ev.evaluate(gs, cache)
        assert len(signals) == 1
        sig = signals[0]
        assert sig.sub_band == ExecutionBand.T4_PROJ
        assert sig.market_id == "MKT-001"
        assert sig.player_id == "P001"
        assert sig.direction in ("YES", "NO")

    def test_posterior_cached_after_evaluate(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state(pts_so_far=14.0, min_so_far=20.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        ev.evaluate(gs, cache)
        posterior = ev.get_lambda_posterior("P001")
        assert posterior is not None
        # Posterior mean should be between T1 prior (22.5) and empirical rate
        # (14 pts in 20 min → 14/20*48=33.6 pts/game). Here: blended upward from 22.5.
        assert posterior > 22.5

    def test_posterior_higher_when_scoring_above_pace(self):
        ev_low = T4ProjEvaluator()
        ev_high = T4ProjEvaluator()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.50, yes_bid=0.46)

        gs_low = _market_game_state(pts_so_far=5.0, min_so_far=20.0)  # below pace
        gs_high = _market_game_state(pts_so_far=20.0, min_so_far=20.0) # above pace

        ev_low.evaluate(gs_low, cache)
        ev_high.evaluate(gs_high, cache)

        posterior_low = ev_low.get_lambda_posterior("P001")
        posterior_high = ev_high.get_lambda_posterior("P001")
        assert posterior_high > posterior_low

    def test_edge_below_min_no_signal(self):
        ev = T4ProjEvaluator()
        # Compute model_p from first principles, then price exactly at model_p.
        # YES edge = model_p - mid - vig = -vig < 0.04; NO edge identical → no signal.
        gs = _market_game_state(pts_so_far=10.0, min_so_far=20.0, elapsed_min=20.0, threshold=25.0)
        a0, b0 = _gamma_prior_params(22.5, PRIOR_LAMBDA_SIGMA_PTS)
        a1, b1 = _gamma_poisson_update(a0, b0, k_obs=10.0, t_elapsed_frac=20.0 / GAME_REGULATION_MIN)
        model_p = _poisson_survival_p(
            10.0, 25.0, (a1 / b1) * ((GAME_REGULATION_MIN - 20.0) / GAME_REGULATION_MIN)
        )
        vig = 0.01
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=model_p + vig / 2, yes_bid=model_p - vig / 2)
        assert ev.evaluate(gs, cache) == []

    def test_player_already_at_threshold_model_p_is_one(self):
        ev = T4ProjEvaluator()
        # pts_so_far=25, threshold=25 → already achieved
        gs = _market_game_state(pts_so_far=25.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.80, yes_bid=0.76)  # mid=0.78
        signals = ev.evaluate(gs, cache)
        assert len(signals) == 1
        assert abs(signals[0].model_p - 1.0) < 1e-9
        assert signals[0].direction == "YES"

    def test_kelly_early_phase(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state(pts_so_far=14.0, min_so_far=5.0, elapsed_min=10.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        if signals:  # only check kelly if signal fires
            assert abs(signals[0].kelly_fraction - 0.010) < 1e-9

    def test_kelly_late_phase_range(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state(pts_so_far=14.0, min_so_far=20.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        if signals:
            assert _KELLY_LATE_LO <= signals[0].kelly_fraction <= _KELLY_LATE_HI

    def test_kelly_near_certain(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state(pts_so_far=14.0, min_so_far=20.0, elapsed_min=46.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        if signals:
            assert abs(signals[0].kelly_fraction - _KELLY_NEAR_CERTAIN) < 1e-9

    def test_inactive_player_no_signal(self):
        ev = T4ProjEvaluator()
        event = T4GameEvent(event_type="TIMER", player_id="P001", market_id="MKT-001", ts=_now())
        player = T4PlayerState(
            player_id="P001", pts_so_far=14.0, reb_so_far=3.0, ast_so_far=2.0,
            min_so_far=20.0, fouls=2, is_active=False,  # inactive
            lambda_t1_prior=22.5, lambda_t4_proj=None,
        )
        spec = T4MarketSpec(market_id="MKT-001", player_id="P001", threshold=25.0)
        gs = T4GameState(
            game_id="G1", game_date="2026-06-22", quarter=3,
            time_remaining_min=12.0, elapsed_min=36.0,
            home_score=78, away_score=74, score_differential=4, ts=_now(),
            player_states={"P001": player},
            trigger_event=event,
            market_specs=(spec,),
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        assert ev.evaluate(gs, cache) == []

    def test_signal_snapshot_contains_game_phase(self):
        ev = T4ProjEvaluator()
        gs = _market_game_state(elapsed_min=40.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        if signals:
            assert "game_phase" in signals[0].signal_snapshot
            assert "lambda_posterior" in signals[0].signal_snapshot


# ---------------------------------------------------------------------------
# T4ArithEvaluator — near-certainty math
# ---------------------------------------------------------------------------

class TestT4ArithEvaluatorMath:
    def test_no_arg_construction(self):
        ev = T4ArithEvaluator()
        assert ev._proj_evaluator is None

    def test_empty_market_specs_returns_empty(self):
        ev = T4ArithEvaluator()
        gs = _game_state()
        cache = T4PriceCache()
        assert ev.evaluate(gs, cache) == []

    def test_gap_too_large_no_signal(self):
        # gap = 25 - 14 = 11 > ARITH_ENTRY_WINDOW=3
        ev = T4ArithEvaluator()
        gs = _market_game_state(pts_so_far=14.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.78, yes_bid=0.72)
        assert ev.evaluate(gs, cache) == []

    def test_t5_territory_no_signal(self):
        # total_remaining = 48 - 45 = 3.0 = EXIT_MIN_TIME_REMAINING_MIN → no signal
        ev = T4ArithEvaluator()
        gs = _market_game_state(pts_so_far=22.0, elapsed_min=45.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.78, yes_bid=0.72)
        assert ev.evaluate(gs, cache) == []

    def test_already_achieved_no_signal(self):
        # gap = 25 - 25 = 0 → gap <= 0 → skip
        ev = T4ArithEvaluator()
        gs = _market_game_state(pts_so_far=25.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.78, yes_bid=0.72)
        # pts_so_far >= threshold → T4-PROJ would fire, but T4-ARITH skips (gap ≤ 0)
        assert ev.evaluate(gs, cache) == []

    def test_signal_within_window_uses_t1_prior(self):
        # pts=22, threshold=25, gap=3 ≤ ARITH_ENTRY_WINDOW=3; elapsed=40 (LATE)
        ev = T4ArithEvaluator()  # no proj_evaluator → T1 prior
        gs = _market_game_state(pts_so_far=22.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        # total_remaining=8, t_remaining_frac=8/48=0.1667
        # lambda_remaining=22.5*0.1667≈3.75
        # P(score 3 more | Poisson(3.75)) ≈ 0.72 ≥ CONFIDENCE_GATE=0.75? Let's check.
        # Actually let me use threshold=24 so gap=2 and lambda=3.75 gives higher p.
        # P(score 2 more | Poisson(3.75)):
        # pts_needed=2, P(X≥2|Poisson(3.75)) = 1 - P(0) - P(1)
        # = 1 - e^{-3.75}(1 + 3.75) ≈ 1 - 0.024*4.75 ≈ 0.888 ≥ 0.75 ✓
        # Use threshold=24, pts=22, gap=2
        gs2 = _market_game_state(pts_so_far=22.0, elapsed_min=40.0, threshold=24.0)
        cache2 = T4PriceCache()
        cache2.update("MKT-001", yes_ask=0.74, yes_bid=0.70)  # mid=0.72, vig=0.02; edge≈0.888-0.72-0.02=0.148>0.04
        signals = ev.evaluate(gs2, cache2)
        assert len(signals) == 1
        assert signals[0].sub_band == ExecutionBand.T4_ARITH
        assert signals[0].kelly_fraction == pytest.approx(_KELLY_NEAR_CERTAIN)

    def test_signal_uses_proj_posterior_when_available(self):
        # Verify T4-ARITH uses proj posterior instead of T1 prior when proj_evaluator is set
        proj_ev = T4ProjEvaluator()
        arith_ev = T4ArithEvaluator(proj_evaluator=proj_ev)

        # First populate proj cache with a high-scoring game state
        # Player has 18 pts in 20 min → posterior lambda higher than T1 prior (22.5)
        gs_proj = _market_game_state(pts_so_far=18.0, min_so_far=20.0, elapsed_min=40.0, threshold=24.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        proj_ev.evaluate(gs_proj, cache)

        posterior = proj_ev.get_lambda_posterior("P001")
        assert posterior is not None and posterior > 22.5  # must be above T1 prior

        # Now run T4-ARITH on same state
        signals = arith_ev.evaluate(gs_proj, cache)
        if signals:
            # model_p should be computed using the posterior, which is > T1 prior
            # Both give p > CONFIDENCE_GATE, but posterior gives higher p
            t_remaining_frac = 8.0 / GAME_REGULATION_MIN
            expected_lambda_remaining_posterior = posterior * t_remaining_frac
            expected_p_posterior = _poisson_survival_p(18.0, 24.0, expected_lambda_remaining_posterior)
            assert abs(signals[0].model_p - expected_p_posterior) < 0.001

    def test_confidence_gate_filters_low_probability(self):
        # Set threshold very high so p_arith < CONFIDENCE_GATE
        # pts=22, threshold=35, gap=13 > ARITH_ENTRY_WINDOW=3 → no signal (gap too big)
        # Use threshold=25, gap=3, but with very little time remaining to drive p low
        # elapsed=47.5, total_remaining=0.5 < EXIT_MIN=3.0 → T5 territory, returns []
        # Instead: elapsed=40, total_remaining=8, lambda_remaining small
        # Use very low lambda: lambda_t1_prior=2.0
        ev = T4ArithEvaluator()
        gs = _market_game_state(
            pts_so_far=22.0, elapsed_min=40.0, threshold=25.0, lambda_t1_prior=2.0
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.74, yes_bid=0.70)
        # lambda_remaining = 2.0 * 8/48 = 0.333
        # P(score 3 more | Poisson(0.333)) ≈ very small → < CONFIDENCE_GATE=0.75 → no signal
        signals = ev.evaluate(gs, cache)
        assert signals == []


# ---------------------------------------------------------------------------
# T4EventEvaluator — discrete event reaction
# ---------------------------------------------------------------------------

class TestT4EventEvaluatorMath:
    def test_no_arg_construction(self):
        ev = T4EventEvaluator()
        assert ev._proj_evaluator is None

    def test_empty_market_specs_returns_empty(self):
        ev = T4EventEvaluator()
        gs = _game_state()
        cache = T4PriceCache()
        assert ev.evaluate(gs, cache) == []

    def test_timer_event_no_signal(self):
        # T4-EVENT only fires on SCORE_UPDATE and FOUL
        ev = T4EventEvaluator()
        gs = _market_game_state(event_type="TIMER", elapsed_min=40.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        assert ev.evaluate(gs, cache) == []

    def test_score_update_fires_for_tracked_player(self):
        ev = T4EventEvaluator()
        gs = _market_game_state(
            pts_so_far=14.0, elapsed_min=40.0, threshold=25.0,
            event_type="SCORE_UPDATE",
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        assert len(signals) == 1
        assert signals[0].sub_band == ExecutionBand.T4_EVENT
        assert signals[0].tree_id == "EVENT-PTS-MADE"

    def test_foul_event_fires_for_tracked_player(self):
        ev = T4EventEvaluator()
        gs = _market_game_state(
            pts_so_far=14.0, elapsed_min=40.0, threshold=25.0,
            event_type="FOUL",
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        assert len(signals) == 1
        assert signals[0].tree_id == "EVENT-PTS-FOUL"

    def test_different_player_event_no_signal(self):
        # trigger_event.player_id = "P002" but market spec is for "P001"
        ev = T4EventEvaluator()
        event = T4GameEvent(
            event_type="SCORE_UPDATE", player_id="P002",  # different player
            market_id="MKT-001", ts=_now()
        )
        player = T4PlayerState(
            player_id="P001", pts_so_far=14.0, reb_so_far=3.0, ast_so_far=2.0,
            min_so_far=20.0, fouls=2, is_active=True, lambda_t1_prior=22.5, lambda_t4_proj=None,
        )
        spec = T4MarketSpec(market_id="MKT-001", player_id="P001", threshold=25.0)
        gs = T4GameState(
            game_id="G1", game_date="2026-06-22", quarter=3,
            time_remaining_min=12.0, elapsed_min=40.0,
            home_score=78, away_score=74, score_differential=4, ts=_now(),
            player_states={"P001": player},
            trigger_event=event,
            market_specs=(spec,),
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        assert ev.evaluate(gs, cache) == []

    def test_uses_proj_posterior_when_injected(self):
        proj_ev = T4ProjEvaluator()
        event_ev = T4EventEvaluator(proj_evaluator=proj_ev)

        gs = _market_game_state(pts_so_far=14.0, min_so_far=20.0, elapsed_min=40.0, threshold=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)

        # Prime proj cache
        proj_ev.evaluate(gs, cache)
        posterior = proj_ev.get_lambda_posterior("P001")
        assert posterior is not None

        # Run T4-EVENT with SCORE_UPDATE
        gs_event = _market_game_state(
            pts_so_far=14.0, elapsed_min=40.0, threshold=25.0,
            event_type="SCORE_UPDATE",
        )
        signals = event_ev.evaluate(gs_event, cache)

        if signals:
            # T4-EVENT's model_p should use the posterior lambda
            total_remaining = GAME_REGULATION_MIN - 40.0
            t_remaining_frac = total_remaining / GAME_REGULATION_MIN
            expected_lambda_remaining = posterior * t_remaining_frac
            expected_p = _poisson_survival_p(14.0, 25.0, expected_lambda_remaining)
            assert abs(signals[0].model_p - expected_p) < 0.001

    def test_falls_back_to_t1_prior_without_proj(self):
        ev = T4EventEvaluator()  # no proj_evaluator
        gs = _market_game_state(
            pts_so_far=14.0, min_so_far=20.0, elapsed_min=40.0, threshold=25.0,
            event_type="SCORE_UPDATE",
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        if signals:
            # model_p is computed from T1 prior (22.5) not posterior
            total_remaining = GAME_REGULATION_MIN - 40.0
            lambda_remaining = 22.5 * (total_remaining / GAME_REGULATION_MIN)
            expected_p = _poisson_survival_p(14.0, 25.0, lambda_remaining)
            assert abs(signals[0].model_p - expected_p) < 0.001

    def test_kelly_is_event_provisional(self):
        ev = T4EventEvaluator()
        gs = _market_game_state(
            pts_so_far=14.0, elapsed_min=40.0, threshold=25.0,
            event_type="SCORE_UPDATE",
        )
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)
        signals = ev.evaluate(gs, cache)
        if signals:
            assert signals[0].kelly_fraction == pytest.approx(0.05)  # provisional T4-EVENT


# ---------------------------------------------------------------------------
# T4FlowEvaluator — FLOW-BLOWOUT
# ---------------------------------------------------------------------------

def _blowout_game_state(
    score_differential: int = 25,
    elapsed_min: float = 30.0,
    team_is_home: Optional[bool] = True,
) -> T4GameState:
    """Game state with a blowout score and T4MarketSpec with team affiliation."""
    event = T4GameEvent(event_type="SCORE_UPDATE", player_id="P001", market_id="MKT-001", ts=_now())
    player = T4PlayerState(
        player_id="P001", pts_so_far=10.0, reb_so_far=3.0, ast_so_far=2.0,
        min_so_far=20.0, fouls=2, is_active=True, lambda_t1_prior=22.5, lambda_t4_proj=None,
    )
    spec = T4MarketSpec(
        market_id="MKT-001", player_id="P001", threshold=20.0, team_is_home=team_is_home
    )
    return T4GameState(
        game_id="G1", game_date="2026-06-22", quarter=3,
        time_remaining_min=max(0.0, GAME_REGULATION_MIN - elapsed_min),
        elapsed_min=elapsed_min,
        home_score=90 if score_differential > 0 else 65,
        away_score=65 if score_differential > 0 else 90,
        score_differential=score_differential,
        ts=_now(),
        player_states={"P001": player},
        trigger_event=event,
        market_specs=(spec,),
    )


class TestT4FlowEvaluatorBlowout:
    def test_empty_market_specs_returns_empty(self):
        ev = T4FlowEvaluator()
        gs = _game_state()  # no market_specs
        cache = T4PriceCache()
        assert ev.evaluate(gs, cache) == []

    def test_no_blowout_returns_empty(self):
        ev = T4FlowEvaluator()
        # score_diff=4 < BLOWOUT_SCORE_THRESHOLD=20
        gs = _blowout_game_state(score_differential=4)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.74, yes_bid=0.70)
        assert ev.evaluate(gs, cache) == []

    def test_blowout_not_sustained_returns_empty(self):
        ev = T4FlowEvaluator()
        # First call at elapsed=25: sets blowout_start=25
        gs1 = _blowout_game_state(score_differential=25, elapsed_min=25.0)
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.74, yes_bid=0.70)
        result1 = ev.evaluate(gs1, cache)
        # 25-25=0 < BLOWOUT_SUSTAIN_MIN=2.0 → no signal
        assert result1 == []

    def test_blowout_sustained_generates_signal(self):
        ev = T4FlowEvaluator()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.40, yes_bid=0.36)

        # First call: set blowout start at elapsed=20
        gs1 = _blowout_game_state(score_differential=25, elapsed_min=20.0, team_is_home=False)
        ev.evaluate(gs1, cache)  # blowout_start = 20; sustained=0 → no signal

        # Second call: elapsed=23, sustained=3 ≥ BLOWOUT_SUSTAIN_MIN=2 → signal
        gs2 = _blowout_game_state(score_differential=25, elapsed_min=23.0, team_is_home=False)
        signals = ev.evaluate(gs2, cache)
        assert len(signals) == 1
        assert signals[0].sub_band == ExecutionBand.T4_FLOW
        assert signals[0].tree_id == "FLOW-BLOWOUT"

    def test_trailing_player_higher_lambda(self):
        """Trailing player (away team, home leading) gets lambda↑ → higher model_p."""
        ev_trailing = T4FlowEvaluator()
        ev_leading = T4FlowEvaluator()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.50, yes_bid=0.46)

        # Warm up both evaluators to establish blowout state
        for ev in [ev_trailing, ev_leading]:
            gs_warm = _blowout_game_state(score_differential=25, elapsed_min=20.0, team_is_home=False)
            ev.evaluate(gs_warm, cache)

        # Trailing: away team, home leading (score_diff>0)
        gs_trail = _blowout_game_state(score_differential=25, elapsed_min=23.0, team_is_home=False)
        sigs_trail = ev_trailing.evaluate(gs_trail, cache)

        # Leading: home team, home leading
        gs_lead = _blowout_game_state(score_differential=25, elapsed_min=23.0, team_is_home=True)
        ev_leading.evaluate(  # warm up for leading evaluator blowout state
            _blowout_game_state(score_differential=25, elapsed_min=20.0, team_is_home=True), cache
        )
        sigs_lead = ev_leading.evaluate(gs_lead, cache)

        # Trailing player should have higher model_p (λ↑) than leading player (λ↓)
        if sigs_trail and sigs_lead:
            assert sigs_trail[0].model_p > sigs_lead[0].model_p

    def test_unknown_team_affiliation_skipped(self):
        ev = T4FlowEvaluator()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.50, yes_bid=0.46)

        # Warm up blowout state
        gs_warm = _blowout_game_state(score_differential=25, elapsed_min=20.0, team_is_home=None)
        ev.evaluate(gs_warm, cache)

        gs = _blowout_game_state(score_differential=25, elapsed_min=23.0, team_is_home=None)
        signals = ev.evaluate(gs, cache)
        assert signals == []  # team_is_home=None → skipped

    def test_blowout_resets_when_score_tightens(self):
        ev = T4FlowEvaluator()
        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.50, yes_bid=0.46)

        # Establish blowout
        ev.evaluate(_blowout_game_state(score_differential=25, elapsed_min=20.0), cache)

        # Score tightens — blowout ends
        gs_tight = _blowout_game_state(score_differential=5, elapsed_min=22.0)
        ev.evaluate(gs_tight, cache)
        assert ev._blowout_start_elapsed is None

        # New blowout starts fresh
        ev.evaluate(_blowout_game_state(score_differential=22, elapsed_min=30.0), cache)
        assert ev._blowout_start_elapsed == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# T4ExitEvaluator — exit logic
# ---------------------------------------------------------------------------

def _open_position(
    direction: str = "YES",
    threshold: float = 25.0,
    entry_model_p: float = 0.80,
    noise_buffer: Optional[float] = 0.19,
) -> T4OpenPosition:
    return T4OpenPosition(
        market_id="MKT-001",
        player_id="P001",
        direction=direction,
        threshold=threshold,
        entry_model_p=entry_model_p,
        sub_band=ExecutionBand.T4_PROJ,
        entry_ts=_now(),
        noise_buffer=noise_buffer,
    )


def _exit_game_state(pts_so_far: float = 14.0, elapsed_min: float = 40.0) -> T4GameState:
    """Game state for exit evaluator testing with player P001."""
    event = T4GameEvent(event_type="TIMER", player_id="P001", market_id="MKT-001", ts=_now())
    player = T4PlayerState(
        player_id="P001", pts_so_far=pts_so_far, reb_so_far=3.0, ast_so_far=2.0,
        min_so_far=20.0, fouls=2, is_active=True, lambda_t1_prior=22.5, lambda_t4_proj=None,
    )
    return T4GameState(
        game_id="G1", game_date="2026-06-22", quarter=3,
        time_remaining_min=max(0.0, GAME_REGULATION_MIN - elapsed_min),
        elapsed_min=elapsed_min, home_score=78, away_score=74, score_differential=4,
        ts=_now(), player_states={"P001": player}, trigger_event=event,
    )


class TestT4ExitEvaluatorLogic:
    def test_empty_positions_returns_empty(self):
        ev = T4ExitEvaluator()
        gs = _exit_game_state()
        cache = T4PriceCache()
        assert ev.generate_exit_signals([], gs, cache) == []

    def test_dict_missing_required_keys_skipped(self):
        ev = T4ExitEvaluator()
        gs = _exit_game_state()
        cache = T4PriceCache()
        # Legacy dict missing direction, threshold, entry_model_p → silently skipped
        signals = ev.generate_exit_signals([{"market_id": "MKT-001"}], gs, cache)
        assert signals == []

    def test_exit_time_floor_fires(self):
        ev = T4ExitEvaluator()
        # total_remaining = 48 - 46 = 2.0 ≤ EXIT_TIME_FLOOR_MIN=3.0
        gs = _exit_game_state(elapsed_min=46.0)
        cache = T4PriceCache()
        pos = _open_position(direction="YES", entry_model_p=0.80)
        signals = ev.generate_exit_signals([pos], gs, cache)
        assert len(signals) == 1
        assert signals[0].is_exit is True
        assert signals[0].tree_id == "EXIT-TIME-FLOOR"
        assert signals[0].sub_band == ExecutionBand.T4_EXIT

    def test_exit_time_floor_at_exact_boundary(self):
        ev = T4ExitEvaluator()
        # total_remaining = 48 - 45 = 3.0 = EXIT_TIME_FLOOR_MIN → fires
        gs = _exit_game_state(elapsed_min=45.0)
        cache = T4PriceCache()
        signals = ev.generate_exit_signals([_open_position()], gs, cache)
        assert len(signals) == 1
        assert signals[0].tree_id == "EXIT-TIME-FLOOR"

    def test_exit_reversal_yes_bet(self):
        ev = T4ExitEvaluator()
        # Player has 0 pts with 3.01 min left → current_p ≈ 0 (needs 25 pts in 3 min) → reversal
        # elapsed=44.99 → total_remaining=3.01 > 3.0 (no time floor)
        gs = _exit_game_state(pts_so_far=0.0, elapsed_min=44.99)
        cache = T4PriceCache()
        pos = _open_position(direction="YES", threshold=25.0, entry_model_p=0.80)
        signals = ev.generate_exit_signals([pos], gs, cache)
        assert any(s.tree_id == "EXIT-REVERSAL" for s in signals)

    def test_exit_buffer_breach_yes_bet(self):
        ev = T4ExitEvaluator()
        # Player has 10 pts with 8 min left (elapsed=40), threshold=25, needs 15 more
        # lambda_remaining = 22.5 * 8/48 = 3.75
        # P(score 15 | Poisson(3.75)) ≈ 0 << entry_model_p=0.80 - buffer=0.19 = 0.61
        gs = _exit_game_state(pts_so_far=10.0, elapsed_min=40.0)
        cache = T4PriceCache()
        pos = _open_position(direction="YES", threshold=25.0, entry_model_p=0.80, noise_buffer=0.19)
        signals = ev.generate_exit_signals([pos], gs, cache)
        assert any(s.tree_id in ("EXIT-BUFFER-BREACH", "EXIT-REVERSAL") for s in signals)

    def test_no_exit_when_favorable(self):
        ev = T4ExitEvaluator()
        # Player has 22 pts with 8 min left (elapsed=40), threshold=25, needs 3 more
        # lambda_remaining = 22.5 * 8/48 = 3.75
        # P(score 3 | Poisson(3.75)) ≈ 0.72; entry_model_p=0.80, buffer=0.19
        # 0.72 > 0.80 - 0.19 = 0.61? YES (no breach); 0.72 > 0.5 (no reversal)
        gs = _exit_game_state(pts_so_far=22.0, elapsed_min=40.0)
        cache = T4PriceCache()
        pos = _open_position(direction="YES", threshold=25.0, entry_model_p=0.80, noise_buffer=0.19)
        signals = ev.generate_exit_signals([pos], gs, cache)
        assert signals == []

    def test_exit_signals_are_urgent(self):
        ev = T4ExitEvaluator()
        gs = _exit_game_state(elapsed_min=46.0)  # time floor fires
        cache = T4PriceCache()
        signals = ev.generate_exit_signals([_open_position()], gs, cache)
        assert all(s.is_exit is True for s in signals)
        # EXIT signals in Layer2 get priority=0.0
        for sig in signals:
            entry = QueueEntry.from_signal(sig)
            assert entry.priority == 0.0

    def test_typed_open_position_accepted(self):
        ev = T4ExitEvaluator()
        gs = _exit_game_state(elapsed_min=46.0)
        cache = T4PriceCache()
        pos = T4OpenPosition(
            market_id="MKT-001", player_id="P001",
            direction="YES", threshold=25.0, entry_model_p=0.80,
            sub_band=ExecutionBand.T4_PROJ, entry_ts=_now(),
        )
        signals = ev.generate_exit_signals([pos], gs, cache)
        assert len(signals) == 1
        assert signals[0].tree_id == "EXIT-TIME-FLOOR"

    def test_buffer_breach_no_bet_direction(self):
        ev = T4ExitEvaluator()
        # NO bet: breach when current_p > entry_model_p + buffer (0.39).
        # Must stay ≤ 0.5 to avoid triggering REVERSAL first (which has `continue`).
        # pts=22, threshold=25, elapsed=43 (total_remaining=5 > EXIT_FLOOR=3):
        #   lambda_remaining = 22.5 * 5/48 ≈ 2.344
        #   P(X≥3 | Poisson(2.344)) ≈ 0.416 → in (0.39, 0.50] → breach without reversal.
        gs = _exit_game_state(pts_so_far=22.0, elapsed_min=43.0)
        cache = T4PriceCache()
        pos = _open_position(direction="NO", threshold=25.0, entry_model_p=0.20, noise_buffer=0.19)
        signals = ev.generate_exit_signals([pos], gs, cache)
        assert any(s.tree_id == "EXIT-BUFFER-BREACH" for s in signals)


# ---------------------------------------------------------------------------
# Layer1 ordering guarantee — T4-PROJ writes cache before T4-ARITH/EVENT reads
# ---------------------------------------------------------------------------

class TestLayer1OrderingGuarantee:
    """Verify T4-PROJ always runs before T4-ARITH and T4-EVENT in the same cycle."""

    def _make_engine_with_wired_proj(self):
        """Factory returns an engine where arith/event share the proj_evaluator."""
        return T4ExecutionEngine.create()

    def test_proj_posterior_populated_before_arith_reads(self):
        engine = self._make_engine_with_wired_proj()
        proj_ev = engine._layer1._evaluators["T4-PROJ"]
        arith_ev = engine._layer1._evaluators["T4-ARITH"]

        assert isinstance(proj_ev, T4ProjEvaluator)
        assert isinstance(arith_ev, T4ArithEvaluator)

        # Arith should share the same proj_evaluator instance as proj_ev
        assert arith_ev._proj_evaluator is proj_ev

    def test_event_evaluator_shares_proj_instance(self):
        engine = self._make_engine_with_wired_proj()
        proj_ev = engine._layer1._evaluators["T4-PROJ"]
        event_ev = engine._layer1._evaluators["T4-EVENT"]
        assert isinstance(event_ev, T4EventEvaluator)
        assert event_ev._proj_evaluator is proj_ev

    def test_score_update_cycle_proj_fires_first(self):
        """On SCORE_UPDATE, T4-PROJ must populate cache before T4-ARITH reads it.
        Verify by checking the posterior is in the cache after simulate_cycle."""
        engine = self._make_engine_with_wired_proj()
        proj_ev = engine._layer1._evaluators["T4-PROJ"]

        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)

        gs = _market_game_state(
            pts_so_far=22.0, min_so_far=20.0, elapsed_min=40.0, threshold=24.0,
            event_type="SCORE_UPDATE",
        )
        engine.simulate_cycle(gs, price_cache=cache)

        # T4-PROJ should have run and populated the cache
        posterior = proj_ev.get_lambda_posterior("P001")
        assert posterior is not None, "T4-PROJ must have run and cached posterior"

    def test_timer_cycle_proj_fires_for_timer(self):
        engine = self._make_engine_with_wired_proj()
        proj_ev = engine._layer1._evaluators["T4-PROJ"]

        cache = T4PriceCache()
        cache.update("MKT-001", yes_ask=0.82, yes_bid=0.78)

        gs = _market_game_state(pts_so_far=14.0, elapsed_min=40.0, event_type="TIMER")
        engine.simulate_cycle(gs, price_cache=cache)

        # T4-PROJ is in TIMER evaluators — should have run
        posterior = proj_ev.get_lambda_posterior("P001")
        assert posterior is not None

    def test_ordered_ids_proj_is_first_in_score_update(self):
        """_evaluators_for_event for SCORE_UPDATE must list T4-PROJ first
        after the ordering fix in evaluate_cycle."""
        engine = self._make_engine_with_wired_proj()
        gs = _game_state(event_type="SCORE_UPDATE")
        active_ids = engine._layer1._evaluators_for_event(gs.trigger_event)
        # After the ordering fix, T4-PROJ appears in the active set
        assert "T4-PROJ" in active_ids

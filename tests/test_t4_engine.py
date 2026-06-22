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

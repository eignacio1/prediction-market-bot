"""
Tests for t4_live_runner.py — Phase 8 live execution path design.

Coverage targets:
  - T4FastHalt: halt/resume/is_halted state machine
  - T4PositionRegistry: open/close/snapshot/exposure/drawdown accounting
  - build_forecast_record: EvaluationSignal → C4 IF-C3-C4 dict
  - T4LiveRunner.run_cycle: kill switch gates, C4/C5/C6 wiring paths
  - T4GameStateBuilder: SCORE_UPDATE detection, T4GameState construction
  - T4ExecutionEngine.on_game_event: Layer1+Layer2 pipeline (via Phase8 engine)
  - T4ExecutionEngine.create_phase8: factory sets _PHASE8_ACTIVE per-instance

All tests run offline (no VPS, no Kalshi API, no ESPN).
Phase 8 engine created via create_phase8() or mock injection.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import MagicMock, call, patch

import pytest

from prediction_market_bot.execution_bands import ExecutionBand
from prediction_market_bot.t4_execution_engine import (
    EvaluationSignal,
    GamePhase,
    StaleDropRecord,
    T4ExecutionEngine,
    T4GameEvent,
    T4GameState,
    T4MarketSpec,
    T4OpenPosition,
    T4PlayerState,
    GAME_REGULATION_MIN,
)
from prediction_market_bot.t4_live_runner import (
    T4FastHalt,
    T4GameStateBuilder,
    T4LiveRunner,
    T4PositionRegistry,
    build_forecast_record,
)
from prediction_market_bot.t4_price_cache import T4Phase8BlockedError, T4PriceCache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _ts() -> datetime:
    return datetime(2026, 6, 22, 21, 0, 0, tzinfo=timezone.utc)


def _signal(
    market_id: str = "MKT-001",
    player_id: str = "P-001",
    direction: str = "YES",
    model_p: float = 0.72,
    mip: float = 0.55,
    vig: float = 0.02,
    edge: float = 0.15,
    kelly: float = 0.032,
    sub_band: ExecutionBand = ExecutionBand.T4_PROJ,
    tree_id: str = "T4-PROJ",
    is_exit: bool = False,
    game_phase: GamePhase = GamePhase.MID,
) -> EvaluationSignal:
    return EvaluationSignal(
        sub_band=sub_band,
        tree_id=tree_id,
        market_id=market_id,
        player_id=player_id,
        direction=direction,
        model_p=model_p,
        mip_at_signal=mip,
        vig_at_signal=vig,
        edge_at_signal=edge,
        kelly_fraction=kelly,
        signal_snapshot={},
        ts=_ts(),
        is_exit=is_exit,
        game_phase=game_phase,
    )


def _open_pos(
    market_id: str = "MKT-001",
    player_id: str = "P-001",
    direction: str = "YES",
    threshold: float = 25.0,
    entry_model_p: float = 0.72,
) -> T4OpenPosition:
    return T4OpenPosition(
        market_id=market_id,
        player_id=player_id,
        direction=direction,
        threshold=threshold,
        entry_model_p=entry_model_p,
        sub_band=ExecutionBand.T4_PROJ,
        entry_ts=_ts(),
    )


def _game_state(
    game_id: str = "G-001",
    game_date: str = "2026-06-22",
    quarter: int = 2,
    elapsed_min: float = 28.0,
) -> T4GameState:
    return T4GameState(
        game_id=game_id,
        game_date=game_date,
        quarter=quarter,
        time_remaining_min=GAME_REGULATION_MIN - elapsed_min,
        elapsed_min=elapsed_min,
        home_score=55,
        away_score=50,
        score_differential=5,
        ts=_ts(),
        player_states={},
        trigger_event=T4GameEvent(
            event_type="TIMER",
            player_id=None,
            market_id=None,
            ts=_ts(),
        ),
        market_specs=(),
    )


def _fake_approval(approved: bool = True, size: float = 5.00) -> tuple[bool, dict]:
    """Simulate C4 evaluate_forecast() return."""
    return True, {
        "approval_status": "APPROVED" if approved else "REJECTED",
        "approved_size": size,
        "rejection_reason": None if approved else "insufficient_edge",
    }


def _mock_monitor(kill_active: bool = False) -> MagicMock:
    m = MagicMock()
    type(m).is_kill_switch_active = property(lambda self: kill_active)
    return m


def _mock_risk(approved: bool = True, size: float = 5.00) -> MagicMock:
    m = MagicMock()
    m.evaluate_forecast.return_value = _fake_approval(approved, size)
    return m


def _mock_trader() -> MagicMock:
    m = MagicMock()
    m.open_position.return_value = (True, {"position_id": "POS-001"})
    return m


def _mock_audit() -> MagicMock:
    return MagicMock()


def _make_runner(
    engine: Any = None,
    risk: Any = None,
    trader: Any = None,
    audit: Any = None,
    monitor: Any = None,
    price_cache: Optional[T4PriceCache] = None,
    fast_halt: Optional[T4FastHalt] = None,
    registry: Optional[T4PositionRegistry] = None,
    market_specs: Optional[dict] = None,
    player_names: Optional[dict] = None,
    t4_band_budget: float = 100.0,
    session_id: str = "sess-001",
) -> T4LiveRunner:
    return T4LiveRunner(
        engine=engine or MagicMock(),
        risk_engine=risk or _mock_risk(),
        trader=trader or _mock_trader(),
        audit=audit or _mock_audit(),
        monitor=monitor or _mock_monitor(),
        price_cache=price_cache or T4PriceCache(),
        fast_halt=fast_halt or T4FastHalt(),
        position_registry=registry or T4PositionRegistry(),
        market_specs=market_specs or {"MKT-001": T4MarketSpec(
            market_id="MKT-001", player_id="P-001", threshold=25.0
        )},
        player_names=player_names or {"P-001": "Test Player"},
        t4_band_budget=t4_band_budget,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# TestT4FastHalt
# ---------------------------------------------------------------------------

class TestT4FastHalt:
    def test_initial_not_halted(self):
        h = T4FastHalt()
        assert h.is_halted() is False

    def test_halt_sets_flag(self):
        h = T4FastHalt()
        h.halt()
        assert h.is_halted() is True

    def test_resume_clears_flag(self):
        h = T4FastHalt()
        h.halt()
        h.resume()
        assert h.is_halted() is False

    def test_halt_idempotent(self):
        h = T4FastHalt()
        h.halt()
        h.halt()  # second call must not raise
        assert h.is_halted() is True

    def test_resume_on_non_halted_is_safe(self):
        h = T4FastHalt()
        h.resume()  # should not raise
        assert h.is_halted() is False

    def test_is_halted_thread_safe(self):
        """halt() from a background thread must be visible to the main thread."""
        h = T4FastHalt()
        results: list[bool] = []

        def _halt():
            h.halt()
            results.append(h.is_halted())

        t = threading.Thread(target=_halt)
        t.start()
        t.join()
        assert True in results
        assert h.is_halted() is True


# ---------------------------------------------------------------------------
# TestT4PositionRegistry
# ---------------------------------------------------------------------------

class TestT4PositionRegistry:
    def test_empty_snapshot(self):
        reg = T4PositionRegistry()
        assert reg.snapshot() == []

    def test_open_adds_to_snapshot(self):
        reg = T4PositionRegistry()
        pos = _open_pos()
        reg.open(pos, size_usd=5.0, game_date="2026-06-22")
        snap = reg.snapshot()
        assert len(snap) == 1
        assert snap[0].market_id == "MKT-001"

    def test_close_removes_from_snapshot(self):
        reg = T4PositionRegistry()
        pos = _open_pos()
        reg.open(pos, size_usd=5.0, game_date="2026-06-22")
        closed = reg.close("MKT-001", "P-001", "YES", realized_pnl_usd=1.50)
        assert closed is True
        assert reg.snapshot() == []

    def test_close_unknown_returns_false(self):
        reg = T4PositionRegistry()
        assert reg.close("UNKNOWN", "P-001", "YES") is False

    def test_open_exposure_usd(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos("MKT-001"), size_usd=5.0, game_date="2026-06-22")
        reg.open(_open_pos("MKT-002", player_id="P-002"), size_usd=8.0, game_date="2026-06-22")
        assert reg.open_exposure_usd() == pytest.approx(13.0)

    def test_open_exposure_excludes_closed(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos("MKT-001"), size_usd=5.0, game_date="2026-06-22")
        reg.open(_open_pos("MKT-002", player_id="P-002"), size_usd=8.0, game_date="2026-06-22")
        reg.close("MKT-001", "P-001", "YES", realized_pnl_usd=2.0)
        assert reg.open_exposure_usd() == pytest.approx(8.0)

    def test_closed_pnl_usd(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos("MKT-001"), size_usd=5.0, game_date="2026-06-22")
        reg.open(_open_pos("MKT-002", player_id="P-002"), size_usd=8.0, game_date="2026-06-22")
        reg.close("MKT-001", "P-001", "YES", realized_pnl_usd=2.50)
        reg.close("MKT-002", "P-002", "YES", realized_pnl_usd=-1.00)
        assert reg.closed_pnl_usd() == pytest.approx(1.50)

    def test_pool_drawdown_pct_zero_when_profitable(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos(), size_usd=5.0, game_date="2026-06-22")
        reg.close("MKT-001", "P-001", "YES", realized_pnl_usd=3.00)
        # free_cash = 100 + 3 - 0 = 103 > 100 → drawdown = 0
        assert reg.pool_drawdown_pct(initial_budget=100.0) == 0.0

    def test_pool_drawdown_pct_reflects_loss(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos(), size_usd=5.0, game_date="2026-06-22")
        reg.close("MKT-001", "P-001", "YES", realized_pnl_usd=-10.00)
        # free_cash = 100 - 10 - 0 = 90 → drawdown = 10/100 = 0.10
        dd = reg.pool_drawdown_pct(initial_budget=100.0)
        assert dd == pytest.approx(0.10)

    def test_pool_drawdown_pct_open_exposure_reduces_free_cash(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos(), size_usd=20.0, game_date="2026-06-22")
        # free_cash = 100 + 0 - 20 = 80 → drawdown = 20/100 = 0.20
        dd = reg.pool_drawdown_pct(initial_budget=100.0)
        assert dd == pytest.approx(0.20)

    def test_pool_drawdown_pct_zero_budget_safe(self):
        reg = T4PositionRegistry()
        assert reg.pool_drawdown_pct(initial_budget=0.0) == 0.0

    def test_all_records_full_history(self):
        reg = T4PositionRegistry()
        reg.open(_open_pos("MKT-001"), size_usd=5.0, game_date="2026-06-22")
        reg.open(_open_pos("MKT-002", player_id="P-002"), size_usd=8.0, game_date="2026-06-22")
        reg.close("MKT-001", "P-001", "YES", realized_pnl_usd=2.0)
        recs = reg.all_records()
        assert len(recs) == 2
        closed = next(r for r in recs if r["market_id"] == "MKT-001")
        assert closed["closed"] is True
        assert closed["realized_pnl_usd"] == pytest.approx(2.0)

    def test_multiple_open_positions_same_market_different_player(self):
        """Two players on the same market ID — distinct positions."""
        reg = T4PositionRegistry()
        reg.open(_open_pos("MKT-001", "P-001"), size_usd=5.0, game_date="2026-06-22")
        reg.open(_open_pos("MKT-001", "P-002"), size_usd=3.0, game_date="2026-06-22")
        assert len(reg.snapshot()) == 2
        assert reg.open_exposure_usd() == pytest.approx(8.0)


# ---------------------------------------------------------------------------
# TestBuildForecastRecord
# ---------------------------------------------------------------------------

class TestBuildForecastRecord:
    def test_required_c4_keys_present(self):
        sig = _signal()
        rec = build_forecast_record(sig, session_id="sess-001")
        for key in ("p_estimate", "market_implied_prob", "edge", "recommended_direction",
                    "forecast_id", "kelly_fraction"):
            assert key in rec, f"missing key: {key}"

    def test_p_estimate_equals_model_p(self):
        sig = _signal(model_p=0.72)
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["p_estimate"] == pytest.approx(0.72)

    def test_market_implied_prob_equals_mip(self):
        sig = _signal(mip=0.55)
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["market_implied_prob"] == pytest.approx(0.55)

    def test_edge_equals_edge_at_signal(self):
        sig = _signal(edge=0.15)
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["edge"] == pytest.approx(0.15)

    def test_kelly_fraction_passed_through(self):
        sig = _signal(kelly=0.078)
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["kelly_fraction"] == pytest.approx(0.078)

    def test_direction_maps_to_recommended_direction(self):
        sig = _signal(direction="NO")
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["recommended_direction"] == "NO"

    def test_forecast_id_encodes_sub_band_and_market(self):
        sig = _signal(market_id="MKT-999", sub_band=ExecutionBand.T4_PROJ)
        rec = build_forecast_record(sig, session_id="sess-001")
        assert "MKT-999" in rec["forecast_id"]
        assert "T4-PROJ" in rec["forecast_id"]

    def test_forecast_id_encodes_direction(self):
        sig = _signal(direction="NO")
        rec = build_forecast_record(sig, session_id="sess-001")
        assert "NO" in rec["forecast_id"]

    def test_sub_band_value_in_record(self):
        sig = _signal(sub_band=ExecutionBand.T4_PROJ)
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["sub_band"] == ExecutionBand.T4_PROJ.value

    def test_tree_id_in_record(self):
        sig = _signal(tree_id="T4-ARITH")
        rec = build_forecast_record(sig, session_id="sess-001")
        assert rec["tree_id"] == "T4-ARITH"

    def test_session_id_in_record(self):
        sig = _signal()
        rec = build_forecast_record(sig, session_id="my-session-42")
        assert rec["session_id"] == "my-session-42"


# ---------------------------------------------------------------------------
# TestT4LiveRunnerRunCycle — kill switch gating
# ---------------------------------------------------------------------------

class TestT4LiveRunnerKillSwitchGating:
    def test_fast_halt_blocks_cycle(self):
        """If T4FastHalt is set, run_cycle must return without calling the engine."""
        fast_halt = T4FastHalt()
        fast_halt.halt()
        engine = MagicMock()
        runner = _make_runner(engine=engine, fast_halt=fast_halt)
        runner.run_cycle(_game_state())
        engine.on_game_event.assert_not_called()

    def test_monitor_kill_switch_blocks_cycle(self):
        """If C7 kill switch is active, run_cycle must return without calling the engine."""
        engine = MagicMock()
        monitor = _mock_monitor(kill_active=True)
        runner = _make_runner(engine=engine, monitor=monitor)
        runner.run_cycle(_game_state())
        engine.on_game_event.assert_not_called()

    def test_t4_pool_drawdown_kill_halts_and_sets_fast_halt(self):
        """When T4 pool drawdown ≥ kill threshold, T4FastHalt is set and cycle exits."""
        fast_halt = T4FastHalt()
        registry = T4PositionRegistry()
        # Budget=100, close with −25 loss → 25% drawdown ≥ 20% kill threshold
        registry.open(_open_pos(), size_usd=5.0, game_date="2026-06-22")
        registry.close("MKT-001", "P-001", "YES", realized_pnl_usd=-25.0)

        monitor = _mock_monitor()
        monitor.trigger_kill_switch = MagicMock()
        engine = MagicMock()

        runner = _make_runner(
            engine=engine, fast_halt=fast_halt, registry=registry,
            monitor=monitor, t4_band_budget=100.0,
        )
        runner.run_cycle(_game_state())

        assert fast_halt.is_halted() is True
        engine.on_game_event.assert_not_called()

    def test_normal_cycle_calls_engine(self):
        """No kill switch, no drawdown — engine.on_game_event() must be called."""
        engine = MagicMock()
        engine.on_game_event.return_value = ([], [])
        runner = _make_runner(engine=engine)
        runner.run_cycle(_game_state())
        engine.on_game_event.assert_called_once()


# ---------------------------------------------------------------------------
# TestT4LiveRunnerEntryPath — C4/C5 wiring
# ---------------------------------------------------------------------------

class TestT4LiveRunnerEntryPath:
    def _runner_with_engine_returning(
        self, approved_signals, drops=None
    ) -> tuple[T4LiveRunner, MagicMock, MagicMock, MagicMock, T4PositionRegistry]:
        engine = MagicMock()
        engine.on_game_event.return_value = (approved_signals, drops or [])
        risk = _mock_risk(approved=True, size=5.00)
        trader = _mock_trader()
        audit = _mock_audit()
        registry = T4PositionRegistry()
        runner = _make_runner(
            engine=engine, risk=risk, trader=trader, audit=audit, registry=registry
        )
        return runner, engine, risk, trader, registry

    def test_approved_signal_calls_c4(self):
        sig = _signal()
        runner, _, risk, _, _ = self._runner_with_engine_returning([sig])
        runner.run_cycle(_game_state())
        risk.evaluate_forecast.assert_called_once()

    def test_approved_signal_calls_c4_with_kelly_fraction(self):
        sig = _signal(kelly=0.078)
        runner, _, risk, _, _ = self._runner_with_engine_returning([sig])
        runner.run_cycle(_game_state())
        call_kwargs = risk.evaluate_forecast.call_args
        fc = call_kwargs[1]["forecast_record"]
        assert fc["kelly_fraction"] == pytest.approx(0.078)

    def test_approved_signal_calls_c5_when_c4_approves(self):
        sig = _signal()
        runner, _, _, trader, _ = self._runner_with_engine_returning([sig])
        runner.run_cycle(_game_state())
        trader.open_position.assert_called_once()

    def test_approved_signal_registered_in_registry(self):
        sig = _signal()
        runner, _, _, _, registry = self._runner_with_engine_returning([sig])
        runner.run_cycle(_game_state())
        assert len(registry.snapshot()) == 1
        assert registry.snapshot()[0].market_id == "MKT-001"

    def test_c4_rejected_signal_not_sent_to_c5(self):
        sig = _signal()
        engine = MagicMock()
        engine.on_game_event.return_value = ([sig], [])
        risk = _mock_risk(approved=False)
        trader = _mock_trader()
        runner = _make_runner(engine=engine, risk=risk, trader=trader)
        runner.run_cycle(_game_state())
        trader.open_position.assert_not_called()

    def test_c4_rejected_signal_not_registered(self):
        sig = _signal()
        engine = MagicMock()
        engine.on_game_event.return_value = ([sig], [])
        risk = _mock_risk(approved=False)
        registry = T4PositionRegistry()
        runner = _make_runner(engine=engine, risk=risk, registry=registry)
        runner.run_cycle(_game_state())
        assert registry.snapshot() == []

    def test_empty_signals_no_c4_call(self):
        engine = MagicMock()
        engine.on_game_event.return_value = ([], [])
        risk = _mock_risk()
        runner = _make_runner(engine=engine, risk=risk)
        runner.run_cycle(_game_state())
        risk.evaluate_forecast.assert_not_called()

    def test_multiple_signals_each_routed_to_c4(self):
        sigs = [_signal("MKT-001"), _signal("MKT-002", player_id="P-002")]
        engine = MagicMock()
        engine.on_game_event.return_value = (sigs, [])
        risk = _mock_risk()
        trader = _mock_trader()
        registry = T4PositionRegistry()
        market_specs = {
            "MKT-001": T4MarketSpec(market_id="MKT-001", player_id="P-001", threshold=25.0),
            "MKT-002": T4MarketSpec(market_id="MKT-002", player_id="P-002", threshold=30.0),
        }
        runner = _make_runner(engine=engine, risk=risk, trader=trader,
                              registry=registry, market_specs=market_specs)
        runner.run_cycle(_game_state())
        assert risk.evaluate_forecast.call_count == 2

    def test_pool_isolated_true_passed_to_c4(self):
        """T4 positions must call C4 with pool_isolated=True (ADR-0023)."""
        sig = _signal()
        engine = MagicMock()
        engine.on_game_event.return_value = ([sig], [])
        risk = _mock_risk()
        runner = _make_runner(engine=engine, risk=risk)
        runner.run_cycle(_game_state())
        call_kwargs = risk.evaluate_forecast.call_args[1]
        assert call_kwargs.get("pool_isolated") is True


# ---------------------------------------------------------------------------
# TestT4LiveRunnerExitPath
# ---------------------------------------------------------------------------

class TestT4LiveRunnerExitPath:
    def test_exit_signal_closes_registry_position(self):
        registry = T4PositionRegistry()
        pos = _open_pos()
        registry.open(pos, size_usd=5.0, game_date="2026-06-22")

        exit_sig = _signal(is_exit=True, tree_id="EXIT-REVERSAL")
        engine = MagicMock()
        engine.on_game_event.return_value = ([exit_sig], [])

        runner = _make_runner(engine=engine, registry=registry)
        runner.run_cycle(_game_state())

        assert registry.snapshot() == []

    def test_exit_signal_does_not_call_c4(self):
        registry = T4PositionRegistry()
        registry.open(_open_pos(), size_usd=5.0, game_date="2026-06-22")
        exit_sig = _signal(is_exit=True, tree_id="EXIT-TIME-FLOOR")
        engine = MagicMock()
        engine.on_game_event.return_value = ([exit_sig], [])
        risk = _mock_risk()
        runner = _make_runner(engine=engine, risk=risk, registry=registry)
        runner.run_cycle(_game_state())
        risk.evaluate_forecast.assert_not_called()

    def test_exit_signal_no_matching_position_is_safe(self):
        """Exit signal for a position not in registry — must not raise."""
        exit_sig = _signal(is_exit=True, market_id="UNKNOWN-MKT")
        engine = MagicMock()
        engine.on_game_event.return_value = ([exit_sig], [])
        runner = _make_runner(engine=engine)
        runner.run_cycle(_game_state())  # must not raise


# ---------------------------------------------------------------------------
# TestT4LiveRunnerStaleDrops
# ---------------------------------------------------------------------------

class TestT4LiveRunnerStaleDrops:
    def test_stale_drops_logged_to_c6(self):
        drop = StaleDropRecord(
            market_id="MKT-001",
            sub_band_value=ExecutionBand.T4_PROJ.value,
            tree_id="T4-PROJ",
            edge_at_entry=0.15,
            edge_at_drop=0.02,
            queue_wait_ms=120.0,
            drop_reason="price_stale",
            ts=_ts(),
        )
        engine = MagicMock()
        engine.on_game_event.return_value = ([], [drop])
        audit = _mock_audit()
        runner = _make_runner(engine=engine, audit=audit)
        runner.run_cycle(_game_state())
        audit.log.assert_called()
        log_call_args = audit.log.call_args_list[-1]
        assert log_call_args[0][0] == "t4_stale_drop"

    def test_no_drops_no_extra_audit_calls(self):
        engine = MagicMock()
        engine.on_game_event.return_value = ([], [])
        audit = _mock_audit()
        runner = _make_runner(engine=engine, audit=audit)
        runner.run_cycle(_game_state())
        # Only one audit call expected: runner_start is not triggered by run_cycle
        # Audit calls for drops = 0
        drop_calls = [c for c in audit.log.call_args_list
                      if c[0][0] == "t4_stale_drop"]
        assert drop_calls == []


# ---------------------------------------------------------------------------
# TestT4ExecutionEngineOnGameEvent
# ---------------------------------------------------------------------------

class TestT4ExecutionEngineOnGameEvent:
    def _phase8_engine(self):
        """Return a T4ExecutionEngine with per-instance _PHASE8_ACTIVE=True."""
        return T4ExecutionEngine.create_phase8(min_edge=0.04)

    def test_create_phase8_instance_active(self):
        engine = self._phase8_engine()
        assert engine._PHASE8_ACTIVE is True

    def test_class_default_still_false_after_create_phase8(self):
        """create_phase8() must NOT set the class-level default (only instance)."""
        _ = self._phase8_engine()
        fresh = T4ExecutionEngine.create(min_edge=0.04)
        assert fresh._PHASE8_ACTIVE is False

    def test_on_game_event_blocked_without_phase8(self):
        engine = T4ExecutionEngine.create()
        gs = _game_state()
        with pytest.raises(T4Phase8BlockedError):
            engine.on_game_event(gs)

    def test_on_game_event_returns_tuple_when_active(self):
        engine = self._phase8_engine()
        gs = _game_state()
        result = engine.on_game_event(gs, open_positions=[], price_cache=T4PriceCache())
        assert isinstance(result, tuple)
        assert len(result) == 2
        approved, drops = result
        assert isinstance(approved, list)
        assert isinstance(drops, list)

    def test_on_game_event_no_specs_returns_empty(self):
        """Engine with no market_specs in game_state → Layer 1 produces no signals."""
        engine = T4ExecutionEngine.create_phase8()
        gs = _game_state()  # market_specs=() in _game_state()
        approved, drops = engine.on_game_event(gs, open_positions=[], price_cache=T4PriceCache())
        assert approved == []
        assert drops == []

    def test_on_game_event_accepts_positional_game_state(self):
        """Backward-compat: engine.on_game_event(gs) still works (no_specs → no signals)."""
        engine = T4ExecutionEngine.create_phase8()
        result = engine.on_game_event(_game_state())
        assert result == ([], [])

    def test_on_game_event_passes_open_positions_to_layer1(self):
        """Open positions passed to on_game_event reach Layer1 evaluate_cycle."""
        engine = self._phase8_engine()
        pos = _open_pos()
        gs = _game_state()
        # With no price cache entries, T4-EXIT generates no signals because
        # ExitEvaluator can't compute model_p. So just verify no exception.
        approved, drops = engine.on_game_event(
            gs, open_positions=[pos], price_cache=T4PriceCache()
        )
        assert isinstance(approved, list)

    def test_start_raises_blocked_without_phase8(self):
        engine = T4ExecutionEngine.create()
        with pytest.raises(T4Phase8BlockedError):
            engine.start(iter([]))

    def test_start_raises_not_implemented_with_phase8(self):
        """start() is delegated to T4LiveRunner; engine itself raises NotImplementedError."""
        engine = T4ExecutionEngine.create_phase8()
        with pytest.raises(NotImplementedError):
            engine.start(iter([]))


# ---------------------------------------------------------------------------
# TestT4GameStateBuilder
# ---------------------------------------------------------------------------

class TestT4GameStateBuilder:
    def _builder(self) -> T4GameStateBuilder:
        return T4GameStateBuilder(
            pregame_lambdas={"P-001": 22.5, "P-002": 18.0},
            market_specs=(
                T4MarketSpec(market_id="MKT-001", player_id="P-001", threshold=25.0),
            ),
        )

    def _box(self, pts=10, reb=3, ast=2, fouls=1, is_active=True, min_played=20) -> dict:
        return {
            "pts": pts, "reb": reb, "ast": ast,
            "fouls": fouls, "is_active": is_active, "min": min_played,
        }

    def test_first_build_emits_timer_event(self):
        """No previous score reference → trigger_event must be TIMER."""
        builder = self._builder()
        gs = builder.build(
            game_id="G-001", game_date="2026-06-22",
            quarter=2, time_remaining_min=20.0, elapsed_min=28.0,
            home_score=55, away_score=50,
            player_box_scores={"P-001": self._box()},
        )
        assert gs.trigger_event.event_type == "TIMER"

    def test_no_score_change_emits_timer(self):
        builder = self._builder()
        builder.build(
            "G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
            player_box_scores={"P-001": self._box()},
        )
        gs = builder.build(
            "G-001", "2026-06-22", 2, 19.0, 29.0, 55, 50,  # same score
            player_box_scores={"P-001": self._box(pts=11)},
        )
        assert gs.trigger_event.event_type == "TIMER"

    def test_score_change_emits_score_update(self):
        builder = self._builder()
        builder.build("G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
                      player_box_scores={"P-001": self._box()})
        gs = builder.build("G-001", "2026-06-22", 2, 19.0, 29.0, 57, 50,  # home +2
                           player_box_scores={"P-001": self._box(pts=12)})
        assert gs.trigger_event.event_type == "SCORE_UPDATE"

    def test_away_score_change_emits_score_update(self):
        builder = self._builder()
        builder.build("G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
                      player_box_scores={"P-001": self._box()})
        gs = builder.build("G-001", "2026-06-22", 2, 19.0, 29.0, 55, 53,  # away +3
                           player_box_scores={"P-001": self._box(pts=10)})
        assert gs.trigger_event.event_type == "SCORE_UPDATE"

    def test_player_state_populated_from_box_score(self):
        builder = self._builder()
        gs = builder.build(
            "G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
            player_box_scores={"P-001": self._box(pts=14, reb=5, fouls=2)},
        )
        ps = gs.player_states["P-001"]
        assert ps.pts_so_far == pytest.approx(14.0)
        assert ps.reb_so_far == pytest.approx(5.0)
        assert ps.fouls == 2

    def test_lambda_t1_prior_from_pregame_lambdas(self):
        builder = self._builder()
        gs = builder.build(
            "G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
            player_box_scores={"P-001": self._box()},
        )
        assert gs.player_states["P-001"].lambda_t1_prior == pytest.approx(22.5)

    def test_unknown_player_gets_default_lambda(self):
        """Player not in pregame_lambdas falls back to default (20.0)."""
        builder = self._builder()
        gs = builder.build(
            "G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
            player_box_scores={"UNKNOWN": self._box()},
        )
        assert gs.player_states["UNKNOWN"].lambda_t1_prior == pytest.approx(20.0)

    def test_game_state_fields_populated(self):
        builder = self._builder()
        gs = builder.build(
            "G-001", "2026-06-22", 3, 12.0, 36.0, 80, 75,
            player_box_scores={"P-001": self._box()},
        )
        assert gs.game_id == "G-001"
        assert gs.game_date == "2026-06-22"
        assert gs.quarter == 3
        assert gs.home_score == 80
        assert gs.away_score == 75
        assert gs.score_differential == 5
        assert gs.elapsed_min == pytest.approx(36.0)

    def test_score_update_then_reset_to_timer_on_no_change(self):
        """After a SCORE_UPDATE cycle, if score doesn't change next cycle → TIMER."""
        builder = self._builder()
        builder.build("G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
                      player_box_scores={"P-001": self._box()})
        builder.build("G-001", "2026-06-22", 2, 19.0, 29.0, 57, 50,  # SCORE_UPDATE
                      player_box_scores={"P-001": self._box(pts=12)})
        gs3 = builder.build("G-001", "2026-06-22", 2, 18.0, 30.0, 57, 50,  # no change
                            player_box_scores={"P-001": self._box(pts=12)})
        assert gs3.trigger_event.event_type == "TIMER"

    def test_last_event_player_id_forwarded(self):
        builder = self._builder()
        builder.build("G-001", "2026-06-22", 2, 20.0, 28.0, 55, 50,
                      player_box_scores={"P-001": self._box()})
        gs = builder.build(
            "G-001", "2026-06-22", 2, 19.0, 29.0, 57, 50,
            player_box_scores={"P-001": self._box(pts=12)},
            last_event_player_id="P-001",
        )
        assert gs.trigger_event.player_id == "P-001"

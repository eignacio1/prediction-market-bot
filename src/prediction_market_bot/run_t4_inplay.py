"""
PIPE-07: T4 In-Play Event Loop — Skeleton
==========================================
Pipeline:     PIPE-07
Band:         T4 (Bayesian in-play)
Phase active: SKELETON — Phase 8+ only. BLOCKED on:
              1. DS-02 real-time game state feed (source not selected — ADR required)
              2. Kill switch redesign (<5s SLA — NFR-03 supersession ADR required)
              3. Phase 8 infrastructure ADR (T4/T5 activation gate)
Status:       DO NOT activate in production until all three blockers resolved.
Upstream:     DS-02 real-time feed → GameStateEvent
              StagedOrderStore (pre-staged orders from T1/T2 cron)
              C7 MonitorAgent (kill switch state)
Downstream:   C4 RiskEngine (evaluate_forecast)
              C5 VenueRouter (execute)
              C6 AuditLogger (always)
ADR refs:     ADR-0004 (base model); ADR-0006 (risk framework);
              Phase 8 infra ADR (pending — required before activation)

Architecture:
    Pre-staging principle: detection band ≠ execution band.
    T1/T2 computes heavy inference. T3 verifies. T4 fires from lookup table.
    No API calls at execution time — StagedOrderStore read is the only I/O.

    Event routing (per game-state event):
        1. Kill switch check (<5ms)
        2. StagedOrderStore.get_staged(market_id) — pre-staged path (Strategy C/E)
           If found and not expired: fire pre-built order → C4 → C5
        3. GameStateModel.update(gs, threshold, p_t1) — Bayesian path (Strategy A)
           If |delta_p| >= T4_MIN_DELTA_P AND p_t4 > mip + vig: → C4 → C5
        4. T5 eligibility check: Q4 ≤ 3 min → LateGameArithmetic.evaluate()
           If NEAR_CERTAIN: → C4 → C5 (Kelly 0.15)

    SLA: 5s end-to-end (event received → order submitted or dropped)
    Compute budget: 50ms inference (GameStateModel), 5ms T5 arithmetic
    Kill switch: MUST halt all activity in <5s (vs. current 60s for T1 — ADR required)

Usage (when DS-02 is active — Phase 8+):
    loop = T4EventLoop(store, model, arithmetic, risk_engine, router, audit)
    loop.on_game_state_event(event)    # call on every DS-02 game-state event

Usage (testing with synthetic events — available now):
    python3 -m prediction_market_bot.run_t4_inplay --demo
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from prediction_market_bot.c3_forecasting.game_state_model import (
    KELLY_T4,
    KELLY_T5,
    T4_MIN_DELTA_P,
    GameState,
    GameStateModel,
    LateGameArithmetic,
    T4Signal,
    T5Signal,
)
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event data structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GameStateEvent:
    """
    Incoming game-state event from DS-02 real-time feed.

    DS-02 (when active) fires one of these on every scoring update.
    Fields mirror GameState but include market context (market_id, p_t1, mip, vig)
    needed for the routing decision.

    p_t1:  T1 model probability (from C3 pre-game forecast, stored at T1 time)
    mip:   current market implied probability (mid-price from DS-02 price feed)
    vig:   current market vig estimate (ask - bid spread / 2)
    """
    market_id: str             # kalshi_ticker
    player_id: str
    threshold: float
    pts_so_far: float
    time_remaining_min: float
    quarter: int
    pace_pts_per_min: float    # rolling pts/min from C2 feature store (updated at T1)
    p_t1: float                # T1 prior from C3
    mip: float                 # current market implied probability
    vig: float                 # current vig estimate


# ---------------------------------------------------------------------------
# Routing result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class T4RoutingResult:
    """Result of routing a GameStateEvent through the T4 decision tree."""
    market_id: str
    action: str            # "FIRE_STAGED" | "FIRE_BAYESIAN" | "FIRE_T5" | "NO_ACTION" | "KILL_SWITCH"
    reason: str
    signal: Optional[T4Signal | T5Signal]
    staged_order: Optional[dict]
    kelly_fraction: float
    timestamp_iso: str


# ---------------------------------------------------------------------------
# T4 Event Loop
# ---------------------------------------------------------------------------

class T4EventLoop:
    """
    PIPE-07 event loop: routes game-state events through the T4 decision tree.

    BLOCKED on DS-02 and kill switch redesign (Phase 8+).
    Fully testable now with synthetic GameStateEvent inputs.

    Kill switch integration:
        _kill_switch_armed() must complete in <5ms and return True if halted.
        Current C7 MonitorAgent kill switch SLA is 60s (NFR-03) — incompatible
        with T4. A new ADR must supersede NFR-03 scope for T4/T5 before activation.
        Placeholder implementation: reads a file flag (fast, no network).
    """

    def __init__(
        self,
        staged_order_store: StagedOrderStore,
        game_state_model: GameStateModel,
        late_game_arithmetic: LateGameArithmetic,
        # Injected at Phase 8 activation — stubs for now:
        risk_engine=None,    # C4 RiskEngine.evaluate_forecast()
        venue_router=None,   # C5 VenueRouter.execute()
        audit_logger=None,   # C6 AuditLogger.log_event()
    ) -> None:
        self._store = staged_order_store
        self._model = game_state_model
        self._arithmetic = late_game_arithmetic
        self._risk_engine = risk_engine
        self._router = venue_router
        self._audit = audit_logger

    def _kill_switch_armed(self) -> bool:
        """
        Check kill switch state in <5ms.

        BLOCKED: Phase 8 kill switch redesign ADR required. Current C7 kill
        switch SLA is 60s — too slow for T4. Placeholder reads a file flag.
        Replace with C7 MonitorAgent in-memory state check at Phase 8.
        """
        # BLOCKED: replace with C7 in-memory flag at Phase 8
        # For now: always returns False (kill switch not armed)
        # Do not activate in production until this is wired to C7.
        return False

    def _to_game_state(self, event: GameStateEvent) -> GameState:
        return GameState(
            player_id=event.player_id,
            pts_so_far=event.pts_so_far,
            time_remaining_min=event.time_remaining_min,
            quarter=event.quarter,
            pace_pts_per_min=event.pace_pts_per_min,
        )

    def _route_pre_staged(
        self, event: GameStateEvent, staged_order: dict
    ) -> T4RoutingResult:
        """Strategy C/E path: fire pre-built order from StagedOrderStore."""
        logger.info(
            "T4 STAGED path: market=%s order_id=%s strategy=%s",
            event.market_id, staged_order["order_id"], staged_order["strategy"],
        )
        # BLOCKED: C4 approve + C5 execute at Phase 8
        # self._risk_engine.evaluate_forecast(...)
        # self._router.execute(...)
        return T4RoutingResult(
            market_id=event.market_id,
            action="FIRE_STAGED",
            reason=f"pre-staged order found (strategy={staged_order['strategy']})",
            signal=None,
            staged_order=staged_order,
            kelly_fraction=staged_order.get("kelly_fraction", KELLY_T4),
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )

    def _route_bayesian(
        self, event: GameStateEvent, signal: T4Signal
    ) -> T4RoutingResult:
        """Strategy A path: Bayesian update exceeds threshold and beats market."""
        logger.info(
            "T4 BAYESIAN path: market=%s p_t1=%.3f p_t4=%.3f delta=%.3f",
            event.market_id, signal.p_t1, signal.p_t4, signal.delta_p,
        )
        # BLOCKED: C4 approve + C5 execute at Phase 8
        return T4RoutingResult(
            market_id=event.market_id,
            action="FIRE_BAYESIAN",
            reason=f"delta_p={signal.delta_p:.3f} >= threshold; p_t4={signal.p_t4:.3f} > mip+vig",
            signal=signal,
            staged_order=None,
            kelly_fraction=KELLY_T4,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )

    def _route_t5(
        self, event: GameStateEvent, t5_signal: T5Signal
    ) -> T4RoutingResult:
        """T5 path: near-certain late-game arithmetic result."""
        logger.info(
            "T5 path: market=%s verdict=%s p_hit=%.3f",
            event.market_id, t5_signal.verdict, t5_signal.p_hit,
        )
        # BLOCKED: C4 approve + C5 execute at Phase 8
        return T4RoutingResult(
            market_id=event.market_id,
            action="FIRE_T5",
            reason=f"T5 {t5_signal.verdict}: p_hit={t5_signal.p_hit:.3f}",
            signal=t5_signal,
            staged_order=None,
            kelly_fraction=KELLY_T5,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )

    def on_game_state_event(self, event: GameStateEvent) -> T4RoutingResult:
        """
        Main entry point: process one DS-02 game-state event.

        SLA: 5s end-to-end. Compute budget: 50ms inference.
        Returns T4RoutingResult regardless of action taken.
        All NO_ACTION returns are logged to C6 with reason.
        """
        ts = datetime.now(timezone.utc).isoformat()

        # Step 1: Kill switch — must be < 5ms
        if self._kill_switch_armed():
            logger.warning("T4 KILL SWITCH ARMED — dropping event market=%s", event.market_id)
            return T4RoutingResult(
                market_id=event.market_id,
                action="KILL_SWITCH",
                reason="kill switch armed",
                signal=None,
                staged_order=None,
                kelly_fraction=0.0,
                timestamp_iso=ts,
            )

        # Step 2: Expire stale staged orders before lookup
        self._store.expire_stale()

        # Step 3: Pre-staged path (Strategy C/E — table lookup)
        staged = self._store.get_staged(event.market_id)
        if staged is not None:
            return self._route_pre_staged(event, staged)

        # Step 4: Bayesian update path (Strategy A)
        gs = self._to_game_state(event)
        signal = self._model.update(gs, event.threshold, event.p_t1)

        if self._model.is_material(signal) and signal.p_t4 > event.mip + event.vig:
            # Check T5 eligibility first — T5 supersedes T4 if both trigger
            if signal.t5_eligible:
                t5_signal = self._arithmetic.evaluate(gs, event.threshold)
                if t5_signal.verdict != "UNCERTAIN":
                    return self._route_t5(event, t5_signal)

            return self._route_bayesian(event, signal)

        # Step 5: T5 eligibility even if Bayesian delta is not material
        if signal.t5_eligible:
            t5_signal = self._arithmetic.evaluate(gs, event.threshold)
            if t5_signal.verdict != "UNCERTAIN":
                return self._route_t5(event, t5_signal)

        # No action
        reason = (
            f"delta_p={signal.delta_p:.3f} < {T4_MIN_DELTA_P} or p_t4={signal.p_t4:.3f}"
            f" <= mip+vig={event.mip + event.vig:.3f}"
        )
        logger.debug("T4 NO_ACTION: market=%s %s", event.market_id, reason)
        return T4RoutingResult(
            market_id=event.market_id,
            action="NO_ACTION",
            reason=reason,
            signal=signal,
            staged_order=None,
            kelly_fraction=0.0,
            timestamp_iso=ts,
        )


# ---------------------------------------------------------------------------
# Demo / smoke test (synthetic events — no DS-02 required)
# ---------------------------------------------------------------------------

def _run_demo() -> None:
    """
    Smoke test with synthetic game-state events.
    Demonstrates the routing decision tree without real-time data.
    """
    import tempfile, os
    from pathlib import Path

    print("T4 Event Loop — Demo (synthetic events, no DS-02)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "staged_orders.db")
        store = StagedOrderStore(db_path)
        model = GameStateModel()
        arithmetic = LateGameArithmetic()
        loop = T4EventLoop(store, model, arithmetic)

        scenarios = [
            {
                "label": "Midgame — player trending over (Bayesian fires)",
                "event": GameStateEvent(
                    market_id="KXNBAPTS-25-LBJ-22",
                    player_id="LeBronJames",
                    threshold=22.5,
                    pts_so_far=14.0,
                    time_remaining_min=18.0,  # Q3 ~6 min + Q4 12 min
                    quarter=3,
                    pace_pts_per_min=0.52,
                    p_t1=0.51,
                    mip=0.52,
                    vig=0.03,
                ),
            },
            {
                "label": "Late Q4 — near certain YES (T5 fires)",
                "event": GameStateEvent(
                    market_id="KXNBAPTS-25-SC-28",
                    player_id="StephenCurry",
                    threshold=28.5,
                    pts_so_far=27.0,
                    time_remaining_min=2.5,
                    quarter=4,
                    pace_pts_per_min=0.60,
                    p_t1=0.48,
                    mip=0.55,
                    vig=0.03,
                ),
            },
            {
                "label": "No action — signal not material",
                "event": GameStateEvent(
                    market_id="KXNBAPTS-25-KD-25",
                    player_id="KevinDurant",
                    threshold=25.5,
                    pts_so_far=12.0,
                    time_remaining_min=20.0,
                    quarter=3,
                    pace_pts_per_min=0.45,
                    p_t1=0.50,
                    mip=0.51,
                    vig=0.03,
                ),
            },
            {
                "label": "Pre-staged order — Strategy A fires from store",
                "event": GameStateEvent(
                    market_id="KXNBAPTS-25-GW-18",
                    player_id="GiannisAntetokounmpo",
                    threshold=18.5,
                    pts_so_far=8.0,
                    time_remaining_min=24.0,
                    quarter=2,
                    pace_pts_per_min=0.55,
                    p_t1=0.58,
                    mip=0.50,
                    vig=0.03,
                ),
            },
        ]

        # Stage an order for the 4th scenario
        store.stage_order(
            market_id="KXNBAPTS-25-GW-18",
            player_id="GiannisAntetokounmpo",
            threshold=18.5,
            direction="YES",
            strategy="A",
            p_t1=0.58,
            p_entry=0.50,
            kelly_fraction=0.05,
            sized_amount_usd=10.0,
            valid_until_iso="2099-01-01T00:00:00+00:00",
            notes="demo staged order",
        )

        for scenario in scenarios:
            print(f"\n  {scenario['label']}")
            result = loop.on_game_state_event(scenario["event"])
            print(f"  → ACTION: {result.action}")
            print(f"  → REASON: {result.reason}")
            if result.signal and hasattr(result.signal, "p_t4"):
                s = result.signal
                print(f"  → p_t1={s.p_t1:.3f}  p_t4={s.p_t4:.3f}  delta={s.delta_p:.3f}")
            if result.signal and hasattr(result.signal, "verdict"):
                s = result.signal
                print(f"  → T5 verdict={s.verdict}  p_hit={s.p_hit:.3f}")

    print("\n" + "=" * 60)
    print("Demo complete. T4 event loop skeleton verified.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PIPE-07 T4 in-play event loop")
    parser.add_argument("--demo", action="store_true",
                        help="Run synthetic demo (no DS-02 required)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.demo:
        _run_demo()
    else:
        print("BLOCKED: T4 event loop requires DS-02 real-time feed (Phase 8+).")
        print("Run with --demo for synthetic smoke test.")

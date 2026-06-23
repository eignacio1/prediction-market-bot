"""
T4 Live Runner — Phase 8 Execution Path Design
===============================================
Module:  t4_live_runner
Phase:   Phase 8+ ONLY — BLOCKED on GG-038 / GG-039 / GG-040

Implements the outer shell that wires T4ExecutionEngine (ADR-0029 Layer 1 +
Layer 2) to C4/C5/C6/C7.  This is the Phase 8 replacement for the monolithic
run_t4_live.py (which uses the old GameStateModel / T4EventLoop primitives).

Execution path per cycle:
  T4LiveRunner.run_cycle(game_state)
    │
    ├─ [Gate]    T4FastHalt.is_halted() + C7 monitor.is_kill_switch_active
    ├─ [Layer 1] engine._layer1.evaluate_cycle()   — sub-band math
    ├─ [Layer 2] engine._layer2.process_queue_batch() — staleness + CORR
    ├─ [C4]      RiskEngine.evaluate_forecast()    — per approved signal
    ├─ [C5]      PaperTrader.open_position()       — per C4-approved bet
    ├─ [C6]      AuditLogger                       — every event
    └─ [C7]      Monitor                           — drawdown + kill switch

GG-038 — Kill switch ≤5s (Phase 8 prerequisite):
  T4FastHalt wraps threading.Event.  halt() is O(1) and completes in < 1ms.
  The evaluation loop checks is_halted() before every batch dequeue, giving
  a worst-case lag equal to one batch dequeue cycle (~10 signals at ~50μs
  each = ≈ 0.5ms total).  SLA: ≤5s from halt() call to the last *new* order
  blocked.  Any in-flight orders submitted before halt() are logged by C6 and
  flagged for manual review (Phase 8 obligation: add C5 cancel_order() path).

GG-039 — Price cache ADR (Phase 8 prerequisite):
  T4PriceCacheUpdater polls Kalshi REST at PRICE_POLL_INTERVAL_S=2.0.
  Phase 8 production: replace with Kalshi WebSocket tick subscription (sub-ADR
  required before live capital).  REST polling is the bootstrap design only;
  staleness check in Layer 2 discards signals older than the cache TTL.

GG-040 — Real-time data sources (Phase 8 prerequisite):
  T4GameStateBuilder wraps the existing ESPN live score polling from
  run_t4_live.py.  Phase 8 production: replace ESPN with NBA Stats live
  play-by-play API (≤2s event detection latency; sub-ADR required).
  Required feeds per ADR-0029:
    (1) Live box score ≤2s — T4-EVENT, T4-ARITH
    (2) Live lineups ≤5s  — T4-LINEUP (Phase 8; not yet implemented)
    (3) Kalshi tick feed  — T4-MICRO, T4-SENTIMENT (Phase 8; deferred)

T4 pool invariant (ADR-0023 / ADR-0026):
  T4 positions are pool_isolated=True.  Main T1 bankroll is never touched.
  T4 pool budget = PAPER_T4_POOL_USD (paper) or t4_band_budget (production).
  T4PositionRegistry tracks pool equity independently of the main portfolio.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from prediction_market_bot.execution_bands import NOISE_BUFFER_BAND_T4, ExecutionBand
from prediction_market_bot.t4_execution_engine import (
    EvaluationSignal,
    StaleDropRecord,
    T4ExecutionEngine,
    T4GameEvent,
    T4GameState,
    T4MarketSpec,
    T4OpenPosition,
    T4PlayerState,
    GAME_REGULATION_MIN,
)
from prediction_market_bot.t4_price_cache import T4Phase8BlockedError, T4PriceCache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GG-038: T4 Fast-Halt (≤5s kill switch SLA)
# ---------------------------------------------------------------------------

class T4FastHalt:
    """
    T4-specific kill switch (GG-038 Phase 8 prerequisite).

    threading.Event-based: halt() completes in < 1ms; is_halted() is O(1)
    and non-blocking.  The evaluation loop checks is_halted() before every
    Layer 2 batch dequeue.

    Kill switch hierarchy:
      - T4FastHalt (≤5s SLA)    — halts the T4 evaluation loop only
      - C7 SystemMonitor (≤60s) — halts the entire system including T4

    Both are checked independently in run_cycle().  Either halts T4.

    SLA guarantee: worst-case lag from halt() to last new order blocked =
      one dequeue batch cycle (10 signals × 50μs ≈ 0.5ms).
    Phase 8 obligation: add C5 cancel_order() for any in-flight unfilled orders.
    """

    def __init__(self) -> None:
        self._event = threading.Event()

    def halt(self, reason: str = "operator_halt") -> None:
        """Set the halt flag. O(1), thread-safe. Logs reason via module logger."""
        logger.critical("T4FastHalt: halt triggered — reason=%s", reason)
        self._event.set()

    def resume(self) -> None:
        """Clear the halt flag. Only called after operator investigation."""
        logger.warning("T4FastHalt: halt cleared — resuming evaluation loop")
        self._event.clear()

    def is_halted(self) -> bool:
        """Non-blocking O(1) check. True → do not process further events."""
        return self._event.is_set()


# ---------------------------------------------------------------------------
# Position registry
# ---------------------------------------------------------------------------

@dataclass
class _PositionRecord:
    """Internal record stored in T4PositionRegistry."""
    position: T4OpenPosition
    size_usd: float
    game_date: str
    closed: bool = False
    realized_pnl_usd: float = 0.0


class T4PositionRegistry:
    """
    In-memory registry of T4 open positions.

    Thread-safe via threading.Lock.  Snapshot is passed to Layer1.evaluate_cycle()
    each cycle so T4ExitEvaluator can generate exit signals for open positions.

    Pool accounting:
      open_exposure_usd()  — Σ size_usd of non-closed positions
      closed_pnl_usd()     — Σ realized P&L of closed positions
      pool_drawdown_pct()  — pool-level drawdown (T4 pool independent of T1)
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[_PositionRecord] = []

    def open(self, position: T4OpenPosition, size_usd: float, game_date: str) -> None:
        """Register a new open position."""
        with self._lock:
            self._records.append(_PositionRecord(
                position=position, size_usd=size_usd, game_date=game_date,
            ))
        logger.debug(
            "T4Registry open: market=%s player=%s dir=%s size=$%.2f",
            position.market_id, position.player_id, position.direction, size_usd,
        )

    def close(
        self,
        market_id: str,
        player_id: str,
        direction: str,
        realized_pnl_usd: float = 0.0,
    ) -> bool:
        """Mark a position closed with its realized P&L. Returns True if found."""
        with self._lock:
            for rec in self._records:
                if (not rec.closed
                        and rec.position.market_id == market_id
                        and rec.position.player_id == player_id
                        and rec.position.direction == direction):
                    rec.closed = True
                    rec.realized_pnl_usd = realized_pnl_usd
                    logger.debug(
                        "T4Registry close: market=%s pnl=$%.4f", market_id, realized_pnl_usd
                    )
                    return True
        logger.warning("T4Registry.close: position not found: %s %s %s", market_id, player_id, direction)
        return False

    def snapshot(self) -> list[T4OpenPosition]:
        """Return list of all currently open T4OpenPosition objects (for Layer1 exit eval)."""
        with self._lock:
            return [r.position for r in self._records if not r.closed]

    def open_exposure_usd(self) -> float:
        """Σ size_usd of non-closed positions (capital in-flight for this T4 pool)."""
        with self._lock:
            return sum(r.size_usd for r in self._records if not r.closed)

    def closed_pnl_usd(self) -> float:
        """Σ realized P&L across all closed T4 positions."""
        with self._lock:
            return sum(r.realized_pnl_usd for r in self._records if r.closed)

    def pool_drawdown_pct(self, initial_budget: float) -> float:
        """
        T4 pool drawdown as a fraction of initial_budget.

        drawdown = max(0, (initial − free_cash) / initial)
        where free_cash = initial + Σ closed_pnl − open_exposure
        """
        if initial_budget <= 0.0:
            return 0.0
        with self._lock:
            closed_pnl = sum(r.realized_pnl_usd for r in self._records if r.closed)
            open_exp = sum(r.size_usd for r in self._records if not r.closed)
        free_cash = initial_budget + closed_pnl - open_exp
        return max(0.0, (initial_budget - free_cash) / initial_budget)

    def all_records(self) -> list[dict[str, Any]]:
        """Full record dump for C6 audit (called at end of game)."""
        with self._lock:
            return [
                {
                    "market_id": r.position.market_id,
                    "player_id": r.position.player_id,
                    "direction": r.position.direction,
                    "threshold": r.position.threshold,
                    "sub_band": r.position.sub_band.value,
                    "size_usd": r.size_usd,
                    "closed": r.closed,
                    "realized_pnl_usd": r.realized_pnl_usd,
                    "game_date": r.game_date,
                }
                for r in self._records
            ]


# ---------------------------------------------------------------------------
# GG-039: Price cache updater (Phase 8 bootstrap design)
# ---------------------------------------------------------------------------

class T4PriceCacheUpdater(threading.Thread):
    """
    GG-039 design: polls Kalshi REST to maintain T4PriceCache freshness.

    Phase 8 bootstrap: REST at PRICE_POLL_INTERVAL_S=2.0 (≤ Layer2 TTL).
    Phase 8 production obligation: replace with WebSocket tick subscription
    once the Kalshi WebSocket ADR is signed (sub-ADR of GG-039 resolution).

    Each poll cycle fetches yes_ask/yes_bid for every tracked ticker and
    calls cache.update().  Failed fetches are logged; the cache retains the
    previous value (Layer2 staleness check guards against using stale prices).
    """

    PRICE_POLL_INTERVAL_S: float = 2.0  # EXP-CACHE-01 must validate ≤ Layer2 TTL

    def __init__(
        self,
        kalshi_client: Any,             # KalshiMarketClient — typed as Any to avoid import cycle
        cache: T4PriceCache,
        market_tickers: list[str],
        fast_halt: T4FastHalt,
    ) -> None:
        super().__init__(daemon=True, name="T4PriceCacheUpdater")
        self._client = kalshi_client
        self._cache = cache
        self._tickers = market_tickers
        self._halt = fast_halt

    def run(self) -> None:
        logger.info("T4PriceCacheUpdater started — polling %d tickers at %.1fs",
                    len(self._tickers), self.PRICE_POLL_INTERVAL_S)
        while not self._halt.is_halted():
            for ticker in self._tickers:
                try:
                    ok, market = self._client.fetch_market_detail(ticker)
                    if ok and market is not None:
                        self._cache.update(
                            ticker,
                            yes_ask=float(market.yes_ask),
                            yes_bid=float(market.yes_bid),
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("T4PriceCacheUpdater: fetch failed for %s: %s", ticker, exc)
            time.sleep(self.PRICE_POLL_INTERVAL_S)
        logger.info("T4PriceCacheUpdater stopped (fast_halt set)")


# ---------------------------------------------------------------------------
# GG-040: Game state builder (Phase 8 bootstrap design)
# ---------------------------------------------------------------------------

class T4GameStateBuilder:
    """
    GG-040 design: converts live polling data to T4GameState.

    Phase 8 bootstrap: wraps ESPN live score polling (reuses _espn_poll_once
    from run_t4_live.py).  Tracks previous scores to detect SCORE_UPDATE events.

    Phase 8 production obligation: replace ESPN with NBA Stats live play-by-play
    API at ≤2s event detection latency (sub-ADR of GG-040 resolution).

    Pre-game context required at construction:
      pregame_lambdas  — dict[player_id_str, opp_adj_lambda]  (from C3 PIPE-02)
      market_specs     — tuple[T4MarketSpec, ...]              (from C1/VenueRouter)
    """

    def __init__(
        self,
        pregame_lambdas: dict[str, float],
        market_specs: tuple[T4MarketSpec, ...],
    ) -> None:
        self._pregame_lambdas = pregame_lambdas
        self._market_specs = market_specs
        self._prev_home_score: Optional[int] = None
        self._prev_away_score: Optional[int] = None

    def build(
        self,
        game_id: str,
        game_date: str,
        quarter: int,
        time_remaining_min: float,
        elapsed_min: float,
        home_score: int,
        away_score: int,
        player_box_scores: dict[str, dict],  # player_id → {pts, reb, ast, min, fouls, is_active}
        last_event_player_id: Optional[str] = None,
    ) -> T4GameState:
        """
        Build a T4GameState from parsed polling data.

        Detects SCORE_UPDATE by comparing current scores to the previous cycle.
        Falls back to TIMER event if no score change or no previous reference.

        player_box_scores dict keys per player:
          pts, reb, ast, min, fouls, is_active
        """
        # Detect event type from score delta
        score_changed = (
            self._prev_home_score is not None
            and self._prev_away_score is not None
            and (home_score != self._prev_home_score or away_score != self._prev_away_score)
        )
        event_type = "SCORE_UPDATE" if score_changed else "TIMER"
        self._prev_home_score = home_score
        self._prev_away_score = away_score

        # Build trigger event
        trigger_event = T4GameEvent(
            event_type=event_type,
            player_id=last_event_player_id,
            market_id=None,
            ts=datetime.now(timezone.utc),
        )

        # Build player states
        player_states: dict[str, T4PlayerState] = {}
        for player_id, box in player_box_scores.items():
            lambda_t1 = self._pregame_lambdas.get(player_id, 20.0)
            player_states[player_id] = T4PlayerState(
                player_id=player_id,
                pts_so_far=float(box.get("pts", 0.0)),
                reb_so_far=float(box.get("reb", 0.0)),
                ast_so_far=float(box.get("ast", 0.0)),
                min_so_far=float(box.get("min", 0.0)),
                fouls=int(box.get("fouls", 0)),
                is_active=bool(box.get("is_active", True)),
                lambda_t1_prior=lambda_t1,
                lambda_t4_proj=None,  # T4ProjEvaluator updates this via posterior cache
            )

        score_diff = home_score - away_score
        return T4GameState(
            game_id=game_id,
            game_date=game_date,
            quarter=quarter,
            time_remaining_min=time_remaining_min,
            elapsed_min=elapsed_min,
            home_score=home_score,
            away_score=away_score,
            score_differential=score_diff,
            ts=datetime.now(timezone.utc),
            player_states=player_states,
            trigger_event=trigger_event,
            market_specs=self._market_specs,
        )


# ---------------------------------------------------------------------------
# Forecast record bridge (EvaluationSignal → C4 IF-C3-C4 format)
# ---------------------------------------------------------------------------

def build_forecast_record(
    signal: EvaluationSignal,
    session_id: str,
) -> dict[str, Any]:
    """
    Convert a Layer 2 approved EvaluationSignal to the C4 IF-C3-C4 format.

    Key mapping:
      signal.model_p           → p_estimate
      signal.mip_at_signal     → market_implied_prob
      signal.edge_at_signal    → edge (gross, pre-fee)
      signal.direction         → recommended_direction
      signal.kelly_fraction    → kelly_fraction (read by C4 to override DEFAULT_KELLY)

    The C4 RiskEngine reads fc.get("kelly_fraction", self._kelly_fraction) — so
    a T4 phase-conditional kelly (0.010 EARLY → 0.167 NEAR_CERTAIN) overrides
    the engine's constructor default while all guardrails (drawdown, solvency,
    min_bet) still apply.
    """
    forecast_id = (
        f"{signal.sub_band.value}"
        f"-{signal.market_id}"
        f"-{signal.direction}"
        f"-{signal.ts.strftime('%H%M%S%f')}"
    )
    return {
        "p_estimate": signal.model_p,
        "market_implied_prob": signal.mip_at_signal,
        "edge": signal.edge_at_signal,
        "gross_edge": signal.edge_at_signal,   # pre-fee; same as edge at T4 signal time
        "recommended_direction": signal.direction,
        "forecast_id": forecast_id,
        "kelly_fraction": signal.kelly_fraction,  # phase-conditional; C4 reads this key
        "sub_band": signal.sub_band.value,
        "tree_id": signal.tree_id,
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# T4 Live Runner — orchestrator
# ---------------------------------------------------------------------------

class T4LiveRunner:
    """
    Phase 8 orchestrator: wires T4ExecutionEngine to C4/C5/C6/C7.

    BLOCKED: run_cycle() calls engine.on_game_event(), which raises
    T4Phase8BlockedError unless T4ExecutionEngine._PHASE8_ACTIVE = True.
    That flag is set only by the Phase 8 activation ADR, which gates on
    GG-038 + GG-039 + GG-040 resolution.

    Lifecycle:
      1. Construct with all dependencies (see __init__ docstring).
      2. Call start(game_state_iter) to begin the evaluation loop.
         game_state_iter must yield T4GameState objects.
      3. Stop by calling fast_halt.halt() (T4-only) or monitor.trigger_kill_switch()
         (system-wide).

    Position lifecycle:
      Entry: _handle_entry() → C4 approve → C5 open → registry.open()
      Exit:  _handle_exit()  → C5 close   → registry.close()
      Exit signals come from T4ExitEvaluator, fed open positions from the registry.

    T4 pool accounting:
      T4 positions are pool_isolated=True (ADR-0023).
      T4LiveRunner passes t4_band_budget as portfolio_equity_usd to C4,
      and position_registry.open_exposure_usd() as current_open_exposure_usd.
      C4 CHECK 8a enforces pool solvency (projected exposure ≤ equity).
    """

    # T4 pool drawdown kill switch (mirrors C7 MAX_DRAWDOWN_PCT for the T4 pool).
    # Phase 8 calibration: revise via ADR-0018 when live bankroll is set.
    T4_POOL_DRAWDOWN_KILL_PCT: float = 0.20  # 20% T4 pool loss halts T4

    def __init__(
        self,
        engine: T4ExecutionEngine,
        risk_engine: Any,              # C4 RiskEngine
        trader: Any,                   # C5 PaperTrader (or live VenueAdapter at G6+)
        audit: Any,                    # C6 AuditLogger
        monitor: Any,                  # C7 SystemMonitor
        price_cache: T4PriceCache,
        fast_halt: T4FastHalt,
        position_registry: T4PositionRegistry,
        market_specs: dict[str, T4MarketSpec],  # market_id → spec (for threshold lookup)
        player_names: dict[str, str],           # player_id → display name (for C5)
        t4_band_budget: float,
        session_id: str,
    ) -> None:
        self._engine = engine
        self._risk = risk_engine
        self._trader = trader
        self._audit = audit
        self._monitor = monitor
        self._price_cache = price_cache
        self._fast_halt = fast_halt
        self._registry = position_registry
        self._market_specs = market_specs
        self._player_names = player_names
        self._t4_band_budget = t4_band_budget
        self._session_id = session_id

    # ------------------------------------------------------------------
    # Main cycle
    # ------------------------------------------------------------------

    def run_cycle(self, game_state: T4GameState) -> None:
        """
        One T4 evaluation cycle: Layer 1 → Layer 2 → C4/C5/C6.

        Kill switch checks:
          1. T4FastHalt (≤5s — T4-specific)
          2. C7 SystemMonitor (≤60s — system-wide)
        Either halts the cycle immediately.  C6 logs the halt reason.
        """
        # Gate: kill switches (non-blocking O(1))
        if self._fast_halt.is_halted():
            logger.warning("run_cycle skipped: T4FastHalt active")
            return
        if self._monitor.is_kill_switch_active:
            logger.warning("run_cycle skipped: C7 system kill switch active")
            return

        # T4 pool drawdown gate (pool-level kill, separate from system kill switch)
        pool_dd = self._registry.pool_drawdown_pct(self._t4_band_budget)
        if pool_dd >= self.T4_POOL_DRAWDOWN_KILL_PCT:
            logger.critical(
                "T4 pool drawdown %.1f%% ≥ kill threshold %.1f%% — halting T4",
                pool_dd * 100, self.T4_POOL_DRAWDOWN_KILL_PCT * 100,
            )
            self._fast_halt.halt(reason=f"t4_pool_drawdown_{pool_dd:.3f}")
            self._log_event("t4_pool_drawdown_halt", {"pool_drawdown_pct": pool_dd})
            return

        # Layer 1 + Layer 2 via engine.on_game_event()
        open_positions = self._registry.snapshot()
        try:
            approved, drops = self._engine.on_game_event(
                game_state,
                open_positions=open_positions,
                price_cache=self._price_cache,
            )
        except T4Phase8BlockedError:
            # Should not reach here in Phase 8. Propagate if it does.
            raise
        except Exception as exc:
            logger.error("run_cycle: engine error — halting: %s", exc, exc_info=True)
            self._fast_halt.halt(reason="engine_exception")
            self._monitor.trigger_kill_switch(
                reason=f"T4 engine exception: {exc}",
                session_id=self._session_id,
            )
            return

        # C6: log stale drops
        for drop in drops:
            self._log_event("t4_stale_drop", {
                "market_id": drop.market_id,
                "sub_band": drop.sub_band_value,
                "tree_id": drop.tree_id,
                "edge_at_entry": drop.edge_at_entry,
                "edge_at_drop": drop.edge_at_drop,
                "queue_wait_ms": drop.queue_wait_ms,
                "drop_reason": drop.drop_reason,
            })

        # C4/C5 per approved signal
        game_date = game_state.game_date
        for sig in approved:
            # Re-check kill switch between signals (GG-038 SLA)
            if self._fast_halt.is_halted() or self._monitor.is_kill_switch_active:
                logger.warning("run_cycle: kill switch fired mid-batch — %d signals dropped",
                               len(approved))
                break
            if sig.is_exit:
                self._handle_exit(sig, game_date)
            else:
                self._handle_entry(sig, game_date)

    def _handle_entry(self, sig: EvaluationSignal, game_date: str) -> None:
        """C4 approve → C5 open position → registry.open()."""
        fc = build_forecast_record(sig, session_id=self._session_id)

        # Snapshot exposure from registry (pool_isolated T4 positions tracked here)
        open_exposure = self._registry.open_exposure_usd()
        pool_equity = self._t4_band_budget + self._registry.closed_pnl_usd()

        ok, approval = self._risk.evaluate_forecast(
            forecast_record=fc,
            current_daily_loss=0.0,            # T4 pool: no separate daily loss tracking
            current_drawdown_pct=self._registry.pool_drawdown_pct(self._t4_band_budget),
            session_id=self._session_id,
            current_open_exposure_usd=open_exposure,
            portfolio_equity_usd=pool_equity,
            pool_isolated=True,
        )

        if not ok:
            logger.error("_handle_entry: C4 audit write failure — halting")
            self._fast_halt.halt(reason="c4_audit_write_failure")
            self._monitor.trigger_kill_switch(
                reason="T4 C4 audit write failure",
                session_id=self._session_id,
            )
            return

        if approval.get("approval_status") != "APPROVED":
            self._log_event("t4_signal_rejected", {
                "market_id": sig.market_id,
                "player_id": sig.player_id,
                "sub_band": sig.sub_band.value,
                "tree_id": sig.tree_id,
                "reason": approval.get("rejection_reason"),
                "edge": sig.edge_at_signal,
            })
            return

        approved_size = float(approval.get("approved_size", 0.0))
        spec = self._market_specs.get(sig.market_id)
        threshold = int(spec.threshold) if spec else 0
        player_name = self._player_names.get(sig.player_id, sig.player_id)

        ok, pos_record = self._trader.open_position(
            approval=approval,
            player_name=player_name,
            player_id=sig.player_id,
            kalshi_ticker=sig.market_id,
            kalshi_threshold=threshold,
            mid_price=sig.mip_at_signal,
            vig=sig.vig_at_signal,
            game_date=game_date,
            session_id=self._session_id,
            pool_isolated=True,
        )

        if not ok:
            logger.error("_handle_entry: C5 open_position write failure — halting")
            self._fast_halt.halt(reason="c5_write_failure")
            self._monitor.trigger_kill_switch(
                reason="T4 C5 write failure",
                session_id=self._session_id,
            )
            return

        t4_pos = T4OpenPosition(
            market_id=sig.market_id,
            player_id=sig.player_id,
            direction=sig.direction,
            threshold=float(threshold),
            entry_model_p=sig.model_p,
            sub_band=sig.sub_band,
            entry_ts=sig.ts,
            noise_buffer=NOISE_BUFFER_BAND_T4,
        )
        self._registry.open(t4_pos, size_usd=approved_size, game_date=game_date)

        self._log_event("t4_bet_opened", {
            "market_id": sig.market_id,
            "player_id": sig.player_id,
            "direction": sig.direction,
            "sub_band": sig.sub_band.value,
            "tree_id": sig.tree_id,
            "model_p": sig.model_p,
            "mip": sig.mip_at_signal,
            "edge": sig.edge_at_signal,
            "kelly_fraction": sig.kelly_fraction,
            "approved_size_usd": approved_size,
            "game_phase": sig.game_phase.value,
        })

    def _handle_exit(self, sig: EvaluationSignal, game_date: str) -> None:
        """
        Exit an open position: close in registry, log to C6.

        Phase 8: add C5 close_order() call (Kalshi order cancellation or
        opposing position close).  Paper mode: registry.close() is sufficient
        because PaperTrader.resolve_pending() handles P&L on game resolution.
        """
        closed = self._registry.close(
            market_id=sig.market_id,
            player_id=sig.player_id,
            direction=sig.direction,
            realized_pnl_usd=0.0,  # P&L determined at resolution, not exit signal
        )

        if not closed:
            logger.warning("_handle_exit: no open position found for %s %s %s",
                           sig.market_id, sig.player_id, sig.direction)
            return

        self._log_event("t4_bet_exited", {
            "market_id": sig.market_id,
            "player_id": sig.player_id,
            "direction": sig.direction,
            "exit_reason": sig.tree_id,
            "model_p_at_exit": sig.model_p,
            "sub_band": sig.sub_band.value,
            "game_phase": sig.game_phase.value,
        })

    # ------------------------------------------------------------------
    # Main event loop
    # ------------------------------------------------------------------

    def start(self, game_state_iter) -> None:
        """
        Continuous evaluation loop: iterate T4GameState objects from a feed
        and call run_cycle() for each.

        game_state_iter: any iterable of T4GameState (polling loop, WebSocket
        event stream, or synthetic test feed).

        Stops when:
          - game_state_iter is exhausted (game over)
          - T4FastHalt is set
          - C7 SystemMonitor kill switch is active

        Phase 8: run in a dedicated thread launched by the main PIPE-07 script.
        """
        self._log_event("t4_runner_start", {
            "t4_band_budget": self._t4_band_budget,
            "session_id": self._session_id,
        })

        for game_state in game_state_iter:
            if self._fast_halt.is_halted() or self._monitor.is_kill_switch_active:
                logger.warning("T4LiveRunner.start: halt detected — exiting loop")
                break
            try:
                self.run_cycle(game_state)
            except Exception as exc:  # noqa: BLE001
                logger.error("T4LiveRunner: unhandled error in run_cycle: %s", exc, exc_info=True)
                self._fast_halt.halt(reason=f"unhandled_exception: {exc}")
                break

        # End-of-game audit dump
        all_recs = self._registry.all_records()
        self._log_event("t4_runner_stop", {
            "total_positions": len(all_recs),
            "open_positions": sum(1 for r in all_recs if not r["closed"]),
            "closed_pnl_usd": self._registry.closed_pnl_usd(),
            "pool_drawdown_pct": self._registry.pool_drawdown_pct(self._t4_band_budget),
        })

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log_event(self, event_type: str, payload: dict) -> None:
        """Log to C6 AuditLogger. Tolerates None audit (test mode)."""
        if self._audit is None:
            return
        try:
            self._audit.log(event_type, payload, session_id=self._session_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("T4LiveRunner: C6 audit write failed: %s", exc)
            # C6 write failure → kill switch (hard rule from CLAUDE.md)
            self._fast_halt.halt(reason="c6_audit_write_failure")
            self._monitor.trigger_kill_switch(
                reason=f"T4 C6 audit write failure: {exc}",
                session_id=self._session_id,
            )

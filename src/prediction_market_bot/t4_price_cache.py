"""
T4 Price Cache — Read-Only Kalshi Market Price Polling Loop
============================================================
Module:   t4_price_cache
Phase:    Phase 8+ ONLY — BLOCKED on GG-039 resolution
Purpose:  In-memory per-market Kalshi price cache that supplies the Layer 2
          staleness check in the T4 execution engine (t4_execution_engine.py).
          The cache is populated by a dedicated read-only polling loop running
          independently of the execution queue — it does NOT consume execution
          API rate-limit budget. Layer 2 reads this cache; it never makes live
          API calls at dequeue time (ADR-0029 Principle 1 + Venue constraint
          max_api_calls_per_decision=0 for T4, execution_bands.py).

Architecture (ADR-0029 §Staleness Check):
    - Polling loop: independent background thread, polls Kalshi read-only
      endpoint for all open T4-tracked market prices.
    - Cache: in-memory dict keyed by market_id; thread-safe (RLock).
    - Layer 2: reads T4PriceCache.get_price(market_id, sub_band) which returns
      None when the cached price is stale; Layer 2 treats None as DROP.
    - Polling interval is calibrated to the SHORTEST staleness window across
      active sub-bands (currently T4-EVENT: ≤2s). If T4-EVENT is not active,
      the polling interval can be relaxed to the shortest window among active
      sub-bands.

Staleness windows per sub-band (ADR-0029):
    T4-EVENT:                  ≤ 2 seconds
    T4-LINEUP:                 ≤ 5 seconds
    T4-FLOW, T4-SENTIMENT:     ≤ 30 seconds
    T4-PROJ, T4-ARITH:         ≤ 30 seconds
    T4-BOUNDARY, T4-STAGED,
    T4-CORR, T4-EXIT:          ≤ 30 seconds (structural overlays inherit PROJ window)

BLOCKED until ALL of:
    GG-039 — price cache architecture + implementation ADR accepted
    GG-038 — T4 kill switch ≤5s SLA resolved (polling loop must halt in ≤5s)
    GG-040 — T4 real-time data sources confirmed (Kalshi tick feed provisioned)

Do NOT start the polling loop outside Phase 8.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from prediction_market_bot.execution_bands import ExecutionBand, T4_SUBBANDS


# ---------------------------------------------------------------------------
# Phase 8 guard
# ---------------------------------------------------------------------------

class T4Phase8BlockedError(RuntimeError):
    """
    Raised when Phase 8 T4 infrastructure is invoked before its activation gate.

    Every execution path in the T4 engine stack (price cache polling start,
    Layer 1 continuous evaluation, Layer 2 queue processing) raises this error
    if the Phase 8 gate has not been explicitly cleared.

    Clearing the gate requires:
      1. GG-038 RESOLVED (T4 kill switch ≤5s SLA)
      2. GG-039 RESOLVED (this module's design ADR accepted)
      3. GG-040 RESOLVED (real-time data sources confirmed)
      4. Per-sub-band activation ADR (APR-XXXX) for each sub-band
      5. T4ExecutionEngine._phase8_active = True (set by Phase 8 activation ADR
         implementation — not a runtime flag; must be wired in by an ADR-governed
         code change)
    """


# ---------------------------------------------------------------------------
# Staleness windows
# ---------------------------------------------------------------------------

# Per-sub-band maximum acceptable cache age (seconds).
# From ADR-0029 §Staleness Check. Provisional — EXP may tighten these.
# Key: ExecutionBand; Value: float (maximum seconds since last price update).
STALENESS_WINDOW_S: dict[ExecutionBand, float] = {
    ExecutionBand.T4_EVENT:     2.0,   # edge window is seconds; 2s stale is acceptable
    ExecutionBand.T4_LINEUP:    5.0,   # cascading multi-market; slightly more tolerance
    ExecutionBand.T4_FLOW:      30.0,  # sustained pattern; 30s cache adequate
    ExecutionBand.T4_SENTIMENT: 30.0,  # re-evaluated every 30–120s by design
    ExecutionBand.T4_PROJ:      30.0,  # primary signal; 30s is conservative
    ExecutionBand.T4_ARITH:     30.0,  # near-certainty; 30s adequate for gap check
    ExecutionBand.T4_BOUNDARY:  30.0,  # structural overlay; inherits PROJ window
    ExecutionBand.T4_STAGED:    30.0,  # resting order; price movement is slow
    ExecutionBand.T4_CORR:      30.0,  # overlay; uses PROJ window
    ExecutionBand.T4_EXIT:      30.0,  # exit monitor; continuous but 30s cache ok
}

# Polling interval (seconds): calibrated to shortest staleness window to guarantee
# freshness for the most time-sensitive sub-band. When T4-EVENT is active (≤2s),
# this must be ≤ 1s to maintain cache freshness with margin. Provisional.
POLLING_INTERVAL_S: float = 1.0


# ---------------------------------------------------------------------------
# CachedPrice
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CachedPrice:
    """
    A single cached Kalshi market price snapshot.

    Attributes
    ----------
    market_id : str
        Kalshi market ticker.
    yes_ask : float
        Current YES ask price (probability).
    yes_bid : float
        Current YES bid price (probability).
    mid : float
        Mid-price: (yes_ask + yes_bid) / 2. Used as market_implied_probability.
    vig : float
        Half-spread: (yes_ask - yes_bid) / 2. Used as fee proxy in edge calc.
    ts : datetime
        UTC timestamp when this price was cached.
    """
    market_id: str
    yes_ask: float
    yes_bid: float
    mid: float
    vig: float
    ts: datetime


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# T4PriceCache
# ---------------------------------------------------------------------------

class T4PriceCache:
    """
    In-memory cache of current Kalshi market prices for T4 staleness arbitration.

    Thread-safe via RLock: the polling thread writes; the Layer 2 execution queue
    reads. Writes and reads are non-blocking in the normal case (RLock is reentrant
    and uncontested under Kalshi's polling cadence).

    Usage (Phase 8 only):
        cache = T4PriceCache()
        cache.start_polling(kalshi_client, market_ids, interval_s=1.0)  # Phase 8 BLOCKED
        ...
        # Layer 2 dequeue cycle:
        price = cache.get_price("KXNBAPTS-LEBRON-25+", sub_band=ExecutionBand.T4_PROJ)
        if price is None:
            drop(reason="price_stale")

    Usage (testing / development):
        cache = T4PriceCache()
        cache.update("KXNBAPTS-LEBRON-25+", yes_ask=0.72, yes_bid=0.68, ts=now)
        price = cache.get_price("KXNBAPTS-LEBRON-25+", sub_band=ExecutionBand.T4_PROJ)
        assert price is not None
    """

    _PHASE8_ACTIVE: bool = False  # Set True only by Phase 8 activation ADR wiring.

    def __init__(self) -> None:
        self._cache: dict[str, CachedPrice] = {}
        self._lock = threading.RLock()
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()

    # --- write path (polling loop only) ---

    def update(
        self,
        market_id: str,
        yes_ask: float,
        yes_bid: float,
        ts: Optional[datetime] = None,
    ) -> None:
        """
        Write a fresh price snapshot to the cache.

        Called exclusively by the polling loop. May also be called in tests
        to inject synthetic prices without starting the polling loop.
        """
        if ts is None:
            ts = _now_utc()
        mid = (yes_ask + yes_bid) / 2.0
        vig = (yes_ask - yes_bid) / 2.0
        entry = CachedPrice(
            market_id=market_id,
            yes_ask=yes_ask,
            yes_bid=yes_bid,
            mid=mid,
            vig=vig,
            ts=ts,
        )
        with self._lock:
            self._cache[market_id] = entry

    # --- read path (Layer 2 dequeue cycles) ---

    def get_raw(self, market_id: str) -> Optional[CachedPrice]:
        """Return the raw cached entry for market_id, regardless of staleness."""
        with self._lock:
            return self._cache.get(market_id)

    def is_fresh(self, market_id: str, sub_band: ExecutionBand) -> bool:
        """
        Return True if the cached price for market_id is within the staleness
        window for sub_band. Returns False if no entry exists or is too old.
        """
        window_s = STALENESS_WINDOW_S.get(sub_band, 30.0)
        entry = self.get_raw(market_id)
        if entry is None:
            return False
        age_s = (_now_utc() - entry.ts).total_seconds()
        return age_s <= window_s

    def get_price(
        self, market_id: str, sub_band: ExecutionBand
    ) -> Optional[CachedPrice]:
        """
        Return CachedPrice if fresh for sub_band's staleness window, else None.

        Layer 2 dequeue cycles call this. Returning None means DROP the queued
        bet — the edge was computed against a stale price; we cannot validate it.
        """
        if not self.is_fresh(market_id, sub_band):
            return None
        return self.get_raw(market_id)

    def market_count(self) -> int:
        """Number of markets currently in the cache (for monitoring)."""
        with self._lock:
            return len(self._cache)

    def purge(self, market_id: str) -> None:
        """Remove a market from the cache (called when market resolves)."""
        with self._lock:
            self._cache.pop(market_id, None)

    # --- polling loop (BLOCKED — Phase 8 only) ---

    def start_polling(
        self,
        kalshi_client,
        market_ids: list[str],
        interval_s: float = POLLING_INTERVAL_S,
    ) -> None:
        """
        Start the background polling loop.

        BLOCKED until GG-039 RESOLVED and Phase 8 activation ADR wired.

        The polling loop:
          1. Fetches current YES ask/bid for all market_ids from Kalshi.
          2. Calls self.update() for each market.
          3. Sleeps for interval_s.
          4. Repeats until stop_polling() is called.

        The loop's API calls are read-only (GET orderbook or ticker price) and
        are interleaved with execution calls — they share the Kalshi rate budget
        but are time-separated (not competing in bursts with submission calls).

        Parameters
        ----------
        kalshi_client :
            Kalshi API client with a get_market_price(ticker) method.
            Injected at Phase 8 — not available now.
        market_ids :
            Tickers to track. Updated dynamically by Layer 1 as new markets
            become eligible.
        interval_s :
            Sleep interval between polling cycles. Must be ≤ min(STALENESS_WINDOW_S)
            to guarantee freshness.
        """
        if not self._PHASE8_ACTIVE:
            raise T4Phase8BlockedError(
                "T4PriceCache.start_polling() is Phase 8 infrastructure. "
                "Blocked until GG-038/GG-039/GG-040 resolved and Phase 8 "
                "activation ADR wires T4PriceCache._PHASE8_ACTIVE = True."
            )
        # Phase 8 implementation: start background thread that polls Kalshi
        # and calls self.update() for each market. Deferred to Phase 8 ADR.
        raise NotImplementedError(
            "Phase 8 polling loop implementation deferred to GG-039 resolution."
        )

    def stop_polling(self) -> None:
        """
        Signal the polling loop to stop and join the thread.

        BLOCKED until Phase 8 (no thread to stop before that).
        Must complete within ≤5s (GG-038 T4 kill switch SLA requirement).
        """
        if not self._PHASE8_ACTIVE:
            raise T4Phase8BlockedError(
                "T4PriceCache.stop_polling() is Phase 8 infrastructure. "
                "No polling loop is running before Phase 8 activation."
            )
        raise NotImplementedError(
            "Phase 8 polling loop implementation deferred to GG-039 resolution."
        )

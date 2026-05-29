"""
C5: Venue Router
================
Module:   c5_execution.venue_router
Phase:    Phase 7 (skeleton active Phase 6 idle period)
Purpose:  Routes market data queries to the best available venue.
          Transparent to all upstream components (C3, C4) and all pipelines.
          Currently supports Kalshi only; Polymarket US and DFS pick'em
          slot in when API access is provisioned (T-077).

Routing modes (VENUE_ROUTER_MODE env var):
  "kalshi_only"  — Use Kalshi exclusively (default; safe fallback)
  "best_price"   — Query all registered adapters; return best-priced market
                   for each player/threshold/direction combination

Best-price logic:
  For YES direction: lowest yes_ask wins (cheapest to buy)
  For NO direction:  lowest no_ask wins
  Tie-break: Kalshi preferred (primary venue per ADR-0003)

Cross-venue complement lock detection:
  get_all_quotes() returns prices from all venues for the same market.
  ComplementLockScanner consumes this to detect lock conditions.
  (Complement lock scanner is a separate module — see complement_lock_scanner.py)

Security (NFR-05):
  No API keys stored here. Each adapter handles its own credentials.
  Router only holds references to adapter instances.
"""

from __future__ import annotations

import os
from typing import Optional

from prediction_market_bot.c5_execution.kalshi_client import DS02Snapshot, PlayerMarket, _utc_now
from prediction_market_bot.c5_execution.market_mapper import market_key
from prediction_market_bot.c5_execution.venue_adapter import (
    KalshiVenueAdapter,
    PolymarketVenueAdapter,
    VenueAdapter,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VENUE_ROUTER_MODE_ENV = "VENUE_ROUTER_MODE"
DEFAULT_MODE = "kalshi_only"
PRIMARY_VENUE = "kalshi"          # Tie-break preference (ADR-0003)


# ---------------------------------------------------------------------------
# VenueRouter
# ---------------------------------------------------------------------------


class VenueRouter:
    """
    Routes market queries across all registered venue adapters.

    Transparent to C3, C4, and all pipeline runners — they call VenueRouter
    the same way they previously called KalshiMarketClient directly.

    Usage::

        # Single-venue (Kalshi only — current default):
        router = VenueRouter.from_env()
        ok, snapshot = router.fetch_all_markets()

        # Best-price routing (when Polymarket is live):
        # Set VENUE_ROUTER_MODE=best_price in .env
        router = VenueRouter.from_env()
        ok, market = router.get_best_market("Gilgeous-Alexander", 30.0, "YES")

    Kill-switch contract:
        All methods return (bool, data). bool=False on any adapter failure.
        In best_price mode, a single adapter failure degrades gracefully to
        remaining adapters (logged as WARNING). If ALL adapters fail: bool=False.
    """

    def __init__(
        self,
        adapters: dict[str, VenueAdapter],
        mode: str = DEFAULT_MODE,
    ) -> None:
        if not adapters:
            raise ValueError("VenueRouter requires at least one venue adapter")
        self._adapters = adapters
        self._mode = mode

    @classmethod
    def from_env(cls) -> "VenueRouter":
        """
        Construct from environment variables (NFR-05).

        Always registers KalshiVenueAdapter.
        Registers PolymarketVenueAdapter if POLYMARKET_API_KEY is set.
        Mode from VENUE_ROUTER_MODE (default: kalshi_only).
        """
        mode = os.environ.get(VENUE_ROUTER_MODE_ENV, DEFAULT_MODE)
        adapters: dict[str, VenueAdapter] = {
            "kalshi": KalshiVenueAdapter.from_env(),
        }

        # Polymarket: register only when key is present (T-077)
        poly_key = os.environ.get("POLYMARKET_API_KEY", "")
        if poly_key:
            try:
                adapters["polymarket"] = PolymarketVenueAdapter.from_env()
            except (EnvironmentError, NotImplementedError):
                pass  # Polymarket not yet implemented; Kalshi-only fallback

        return cls(adapters=adapters, mode=mode)

    # ------------------------------------------------------------------
    # Primary interface (replaces KalshiMarketClient in pipelines)
    # ------------------------------------------------------------------

    def check_all_connectivity(self) -> dict[str, tuple[bool, dict]]:
        """
        Check connectivity for all registered adapters.
        Returns {venue_id: (ok, status_dict)}.
        """
        return {
            venue_id: adapter.check_connectivity()
            for venue_id, adapter in self._adapters.items()
        }

    def fetch_all_markets(
        self,
        sport: str = "NBA",
        status: str = "open",
    ) -> tuple[bool, DS02Snapshot]:
        """
        Fetch markets from all registered adapters and merge into one snapshot.

        In 'kalshi_only' mode: returns Kalshi snapshot directly.
        In 'best_price' mode: merges all venues; deduplicates by
          (player_name, threshold) keeping best ask per direction.

        Returns (ok, snapshot). ok=False only if ALL adapters fail.
        """
        if self._mode == "kalshi_only" or len(self._adapters) == 1:
            primary = self._adapters.get(PRIMARY_VENUE) or next(iter(self._adapters.values()))
            return primary.fetch_player_points_markets(sport=sport, status=status)

        # Best-price mode — query all, merge
        all_markets: list[PlayerMarket] = []
        any_ok = False

        for venue_id, adapter in self._adapters.items():
            ok, snapshot = adapter.fetch_player_points_markets(sport=sport, status=status)
            if ok:
                any_ok = True
                all_markets.extend(snapshot.markets)

        if not any_ok:
            return False, DS02Snapshot(fetched_at=_utc_now(), markets=[])

        merged = _deduplicate_best_price(all_markets)
        return True, DS02Snapshot(fetched_at=_utc_now(), markets=merged)

    def get_best_market(
        self,
        player_name_fragment: str,
        target_threshold: float,
        direction: str,
    ) -> tuple[bool, Optional[PlayerMarket]]:
        """
        Return the best-priced market for a player/threshold/direction.

        Queries all adapters independently (bypasses fetch_all_markets deduplication)
        to compare direction-specific execution prices across venues:
          YES direction → lowest yes_ask
          NO  direction → lowest no_ask
          Tie-break:    → Kalshi preferred (ADR-0003 primary venue)

        Parameters
        ----------
        player_name_fragment:
            Case-insensitive fragment matched against player_name.
        target_threshold:
            Points threshold to match (closest available market).
        direction:
            'YES' or 'NO'.
        """
        # Query all adapters independently — do NOT use fetch_all_markets() here
        # because that deduplicates by vig before direction-based price comparison.
        all_candidates: list[PlayerMarket] = []
        any_ok = False

        for adapter in self._adapters.values():
            ok, snapshot = adapter.fetch_player_points_markets()
            if ok:
                any_ok = True
                all_candidates.extend(snapshot.for_player(player_name_fragment))

        if not any_ok:
            return False, None
        if not all_candidates:
            return True, None

        # Find closest threshold across all venues
        closest_thresh = min(all_candidates, key=lambda m: abs(m.threshold - target_threshold)).threshold
        threshold_markets = [m for m in all_candidates if m.threshold == closest_thresh]

        if not threshold_markets:
            return True, None

        # Best execution price for direction; tie-break to primary venue
        if direction == "YES":
            best = min(threshold_markets, key=lambda m: (m.yes_ask, 0 if m.venue == PRIMARY_VENUE else 1))
        else:
            best = min(threshold_markets, key=lambda m: (m.no_ask, 0 if m.venue == PRIMARY_VENUE else 1))

        return True, best

    def get_all_quotes(
        self,
        player_name_fragment: str,
        target_threshold: float,
    ) -> dict[str, Optional[PlayerMarket]]:
        """
        Return one market per venue for a player/threshold.
        Used by ComplementLockScanner to detect cross-venue lock conditions.

        Returns {venue_id: PlayerMarket or None}.
        """
        result: dict[str, Optional[PlayerMarket]] = {}

        for venue_id, adapter in self._adapters.items():
            ok, snapshot = adapter.fetch_player_points_markets()
            if not ok:
                result[venue_id] = None
                continue
            candidates = snapshot.for_player(player_name_fragment)
            if not candidates:
                result[venue_id] = None
                continue
            closest = min(candidates, key=lambda m: abs(m.threshold - target_threshold))
            result[venue_id] = closest

        return result

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active_venues(self) -> list[str]:
        """List of venue IDs currently registered."""
        return list(self._adapters.keys())

    @property
    def mode(self) -> str:
        """Current routing mode."""
        return self._mode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deduplicate_best_price(markets: list[PlayerMarket]) -> list[PlayerMarket]:
    """
    Given a flat list of PlayerMarket from multiple venues, return one market
    per (normalized_player_name, threshold) keeping the one with the tightest vig.

    Uses market_mapper.market_key() for cross-venue normalization so that
    minor display-name differences (accents, apostrophes) across venues do not
    create spurious duplicates in the merged snapshot.

    YES/NO best-price selection happens in get_best_market() at execution time.
    """
    from prediction_market_bot.c5_execution.market_mapper import PlayerMarketKey
    seen: dict[PlayerMarketKey, PlayerMarket] = {}
    for m in markets:
        key = market_key(m)
        if key not in seen:
            seen[key] = m
        else:
            existing = seen[key]
            # Prefer tighter spread (lower vig = more liquid market)
            if m.vig < existing.vig:
                seen[key] = m
            # Tie-break: prefer primary venue
            elif m.vig == existing.vig and m.venue == PRIMARY_VENUE:
                seen[key] = m
    return list(seen.values())

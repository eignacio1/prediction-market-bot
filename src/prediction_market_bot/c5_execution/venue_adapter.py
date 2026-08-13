"""
C5: Venue Adapter Protocol + KalshiVenueAdapter
================================================
Module:   c5_execution.venue_adapter
Phase:    Phase 7 (design skeleton active Phase 6 idle period)
Purpose:  Abstract interface for all prediction market / DFS venue integrations.
          New venues (Polymarket US, PrizePicks, Underdog) implement this protocol
          and plug into VenueRouter without changes to C3, C4, or any pipeline.

Design principles:
  - VenueAdapter is a typing.Protocol (structural subtyping — no inheritance required)
  - KalshiVenueAdapter wraps KalshiMarketClient (composition; zero changes to existing client)
  - All adapters return PlayerMarket with venue field populated
  - Normalize all venue-specific market formats into PlayerMarket before returning

CA-eligible venue registry:
  "kalshi"      — KalshiVenueAdapter       (live, ADR-0003)
  "polymarket"  — PolymarketVenueAdapter   (Phase 7, T-077; ADR-0003 permits)
  "prizepicks"  — PrizePicksVenueAdapter   (Phase 7+, new ADR required)
  "underdog"    — UnderdogVenueAdapter     (Phase 7+, new ADR required)
  "sleeper"     — SleeperVenueAdapter      (Phase 7+, new ADR required)

DFS pick-em note (PrizePicks/Underdog/Sleeper):
  These venues use bookmaker-set lines, not market-set prices.
  implied_probability = 0.50 for all lines (bookmaker targets 50/50 action).
  Edge formula: edge = p̂ - 0.50  (vs. Kalshi: edge = p̂ - mid_price)
  This typically yields LARGER edges than Kalshi because lines are less efficient.
  Payout structure differs — fixed multiplier (2x) vs. $0/$1 binary.
  Requires new ADR before activation.

Security (NFR-05):
  API keys loaded from environment only. Never hardcoded. Never logged.
  Each venue has its own key variable (KALSHI_API_KEY, POLYMARKET_API_KEY, etc.)
"""

from __future__ import annotations

import os
from typing import Any, Optional, runtime_checkable, Protocol

from prediction_market_bot.c5_execution.kalshi_client import (
    DS02Snapshot,
    KalshiMarketClient,
    PlayerMarket,
    SERIES_MLB_PLAYER_HITS,
    SERIES_PLAYER_POINTS,
    _utc_now,
)
from prediction_market_bot.c5_execution.market_type_registry import (
    MarketType,
    series_ticker_for,
)


# ---------------------------------------------------------------------------
# VenueAdapter Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class VenueAdapter(Protocol):
    """
    Structural protocol for all venue integrations.

    Implementing classes do not need to inherit from this — they just need
    to provide matching method signatures. Use isinstance(obj, VenueAdapter)
    to check conformance at runtime (runtime_checkable).

    All methods return (bool, data) tuples following the kill-switch contract:
      bool=False signals a failure; caller must not use data and must
      treat as a kill-switch-level event if in production.
    """

    @property
    def venue_id(self) -> str:
        """Unique venue identifier: 'kalshi', 'polymarket', 'prizepicks', etc."""
        ...

    @property
    def implied_prob_method(self) -> str:
        """
        How this venue prices contracts:
          'market'    — dynamic price via supply/demand (Kalshi, Polymarket)
          'bookmaker' — static bookmaker-set line (PrizePicks, Underdog, Sleeper)
        """
        ...

    def check_connectivity(self) -> tuple[bool, dict[str, Any]]:
        """Verify API key and connectivity. Call before any other method."""
        ...

    def fetch_markets(
        self,
        market_type: MarketType,
        status: str = "open",
    ) -> tuple[bool, DS02Snapshot]:
        """
        Fetch all open markets for the given market family (box 1.2, T-442).
        Returns (ok, snapshot) where each PlayerMarket has venue field set.
        """
        ...

    def fetch_player_points_markets(
        self,
        sport: str = "NBA",
        status: str = "open",
    ) -> tuple[bool, DS02Snapshot]:
        """
        Legacy sport-string interface — thin shim over fetch_markets() (box 1.2).
        Returns (ok, snapshot) where each PlayerMarket has venue field set.
        """
        ...

    def fetch_market_detail(
        self, ticker: str
    ) -> tuple[bool, Optional[PlayerMarket]]:
        """Fetch a single market by ticker. Returns (ok, PlayerMarket or None)."""
        ...


# ---------------------------------------------------------------------------
# KalshiVenueAdapter
# ---------------------------------------------------------------------------


class KalshiVenueAdapter:
    """
    Wraps KalshiMarketClient to conform to VenueAdapter protocol.

    Composition over inheritance — zero changes to KalshiMarketClient.
    Adds venue='kalshi' tag to all returned PlayerMarket objects.

    Usage::
        adapter = KalshiVenueAdapter.from_env()
        ok, snapshot = adapter.fetch_player_points_markets()
        # Each market in snapshot.markets has venue='kalshi'
    """

    venue_id: str = "kalshi"
    implied_prob_method: str = "market"   # Dynamic supply/demand pricing

    def __init__(self, client: KalshiMarketClient) -> None:
        self._client = client

    @classmethod
    def from_env(cls) -> "KalshiVenueAdapter":
        """Construct from VENUE_API_KEY environment variable (NFR-05)."""
        return cls(KalshiMarketClient.from_env())

    def check_connectivity(self) -> tuple[bool, dict[str, Any]]:
        return self._client.check_connectivity()

    def fetch_markets(
        self,
        market_type: MarketType,
        status: str = "open",
    ) -> tuple[bool, DS02Snapshot]:
        series = series_ticker_for(market_type)
        ok, snapshot = self._client.fetch_player_points_markets(status=status, series_ticker=series)
        if not ok:
            return False, snapshot
        tagged = [_tag_market(m, self.venue_id) for m in snapshot.markets]
        return True, DS02Snapshot(fetched_at=snapshot.fetched_at, markets=tagged)

    # Legacy sport-string interface (box 1.2, T-442) — thin shim over fetch_markets().
    _SPORT_TO_MARKET_TYPE: dict[str, MarketType] = {
        "nba": MarketType.NBA_PLAYER_POINTS,
        "mlb": MarketType.MLB_PLAYER_PROP_HITS,
    }

    def fetch_player_points_markets(
        self,
        sport: str = "NBA",
        status: str = "open",
    ) -> tuple[bool, DS02Snapshot]:
        market_type = self._SPORT_TO_MARKET_TYPE.get(sport.lower(), MarketType.NBA_PLAYER_POINTS)
        return self.fetch_markets(market_type, status=status)

    def fetch_market_detail(
        self, ticker: str
    ) -> tuple[bool, Optional[PlayerMarket]]:
        ok, market = self._client.fetch_market_detail(ticker)
        if ok and market is not None:
            return True, _tag_market(market, self.venue_id)
        return ok, market


# ---------------------------------------------------------------------------
# Phase 7+ venue adapters
# ---------------------------------------------------------------------------


class PolymarketVenueAdapter:
    """
    Polymarket US venue adapter — Phase 7 (T-077).
    ADR-0003 permits Polymarket US as Phase 6+ secondary venue.

    Polymarket US relaunched under CFTC regulation in December 2025.
    API: REST + CLOB (Central Limit Order Book); binary YES/NO contracts.
    Authentication: Bearer token from POLYMARKET_API_KEY env var (NFR-05).

    Activation prerequisite: ACC-0003 granted (operator provisions API key).
    See 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_polymarket-activation.md

    Market structure mirrors Kalshi:
      - Binary YES/NO settling at $1.00 / $0.00
      - Price = probability implied by order book
      - Edge formula: edge = p̂ - mid_price  (same as Kalshi)
      - Vig estimated ~2% (lower than Kalshi's ~3%)

    Mapping from Polymarket market format to PlayerMarket:
      condition_id  → ticker (Polymarket's unique market ID)
      token_id_yes  → yes-side token; best_ask from order book = yes_ask
      token_id_no   → no-side token; best_ask from order book = no_ask
      question      → title + player_name + threshold parsed via regex
    """

    venue_id: str = "polymarket"
    implied_prob_method: str = "market"

    # Polymarket US REST base URL (CFTC-regulated; confirm with API docs on provisioning)
    _BASE_URL: str = "https://clob.polymarket.com"
    _MARKETS_ENDPOINT: str = "/markets"
    _BOOK_ENDPOINT: str = "/book"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise EnvironmentError("POLYMARKET_API_KEY not set — check .env (NFR-05)")
        self._api_key = api_key
        self._session_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls) -> "PolymarketVenueAdapter":
        """Construct from POLYMARKET_API_KEY environment variable (NFR-05)."""
        key = os.environ.get("POLYMARKET_API_KEY", "")
        if not key:
            raise EnvironmentError("POLYMARKET_API_KEY not set — check .env (NFR-05)")
        return cls(key)

    def check_connectivity(self) -> tuple[bool, dict[str, Any]]:
        """
        Verify API key and connectivity to Polymarket US CLOB API.

        Returns (ok, status_dict).
        """
        try:
            import requests
            resp = requests.get(
                f"{self._BASE_URL}/",
                headers=self._session_headers,
                timeout=10,
            )
            ok = resp.status_code in (200, 404)  # 404 = reachable but no root endpoint
            return ok, {
                "status_code": resp.status_code,
                "venue": "polymarket",
                "reachable": ok,
            }
        except Exception as exc:
            return False, {"error": str(exc), "venue": "polymarket", "reachable": False}

    def fetch_markets(
        self, market_type: MarketType, status: str = "open"
    ) -> tuple[bool, DS02Snapshot]:
        """
        Fetch open markets from Polymarket US CLOB (box 1.2, T-442).

        Only MarketType.NBA_PLAYER_POINTS is implemented today — Polymarket's
        _parse_market() regex and tag param are NBA-player-points-shaped.
        Any other market_type returns an empty, ok=False snapshot rather than
        silently mis-parsing a different market shape as NBA player points.

        NOTE: Endpoint paths and response schema need verification against
        live API docs when ACC-0003 is provisioned. The structure below
        reflects Polymarket's known CLOB architecture.
        """
        if market_type is not MarketType.NBA_PLAYER_POINTS:
            return False, DS02Snapshot(fetched_at=_utc_now(), markets=[])
        try:
            import requests
            params = {
                "active": "true",
                "closed": "false",
                "tag": "nba",      # KI-019 — Polymarket NBA tag unconfirmed until T-077
            }
            resp = requests.get(
                f"{self._BASE_URL}{self._MARKETS_ENDPOINT}",
                headers=self._session_headers,
                params=params,
                timeout=15,
            )
            if resp.status_code != 200:
                return False, DS02Snapshot(fetched_at=_utc_now(), markets=[])

            markets_raw = resp.json()
            markets = []
            for raw in (markets_raw if isinstance(markets_raw, list)
                        else markets_raw.get("data", [])):
                market = self._parse_market(raw)
                if market is not None:
                    markets.append(market)

            return True, DS02Snapshot(fetched_at=_utc_now(), markets=markets)

        except Exception as exc:
            return False, DS02Snapshot(fetched_at=_utc_now(), markets=[])

    def fetch_player_points_markets(
        self, sport: str = "NBA", status: str = "open"
    ) -> tuple[bool, DS02Snapshot]:
        """Legacy sport-string interface — thin shim over fetch_markets() (box 1.2)."""
        return self.fetch_markets(MarketType.NBA_PLAYER_POINTS, status=status)

    def fetch_market_detail(self, ticker: str) -> tuple[bool, Optional[PlayerMarket]]:
        """Fetch a single market by condition_id (Polymarket's ticker equivalent)."""
        try:
            import requests
            resp = requests.get(
                f"{self._BASE_URL}{self._MARKETS_ENDPOINT}/{ticker}",
                headers=self._session_headers,
                timeout=10,
            )
            if resp.status_code != 200:
                return False, None
            market = self._parse_market(resp.json())
            return (True, market) if market else (True, None)
        except Exception:
            return False, None

    # ------------------------------------------------------------------
    # Internal: Polymarket raw market → PlayerMarket
    # ------------------------------------------------------------------

    def _parse_market(self, raw: dict[str, Any]) -> Optional[PlayerMarket]:
        """
        Convert a raw Polymarket market dict to PlayerMarket.

        Polymarket market schema (CLOB):
          condition_id: str   — unique market ID (our "ticker")
          question: str       — e.g. "Will Shai score 25+ pts on 2026-05-28?"
          tokens: list[dict]  — [{outcome: "Yes", token_id: ..., price: ...},
                                  {outcome: "No",  token_id: ..., price: ...}]
          end_date_iso: str   — settlement date

        Player name and threshold are parsed from question text.
        """
        import re

        try:
            condition_id = raw.get("condition_id", raw.get("id", ""))
            question = raw.get("question", raw.get("title", ""))

            # Parse player name and threshold from question string
            # Expected format: "Will [NAME] score [N]+ points..."
            match = re.search(
                r"Will (.+?) score (\d+)\+?\s*(?:or more\s*)?points?",
                question,
                re.IGNORECASE,
            )
            if not match:
                return None

            player_name = match.group(1).strip()
            threshold = int(match.group(2))

            # Extract YES/NO prices from tokens
            tokens = raw.get("tokens", raw.get("outcomes", []))
            yes_ask = no_ask = 0.50
            yes_bid = no_bid = 0.48

            for token in tokens:
                outcome = str(token.get("outcome", token.get("name", ""))).upper()
                price = float(token.get("price", token.get("ask", 0.50)))
                if outcome == "YES":
                    yes_ask = price
                    yes_bid = max(0.01, price - 0.02)
                elif outcome == "NO":
                    no_ask = price
                    no_bid = max(0.01, price - 0.02)

            mid_price = (yes_ask + yes_bid) / 2
            vig = yes_ask - yes_bid

            # Parse game date from end_date if available
            game_date_raw = raw.get("end_date_iso", raw.get("end_date", ""))
            try:
                from datetime import datetime as dt
                game_date = dt.fromisoformat(
                    game_date_raw.replace("Z", "+00:00")
                ).strftime("%Y-%m-%d")
            except Exception:
                game_date = "unknown"

            return PlayerMarket(
                ticker=condition_id,
                title=question[:120],
                player_name=player_name,
                team_abbr="",           # Polymarket does not provide team
                threshold=threshold,
                game_date=game_date,
                event_ticker=condition_id,
                yes_ask=round(yes_ask, 4),
                yes_bid=round(yes_bid, 4),
                no_ask=round(no_ask, 4),
                no_bid=round(no_bid, 4),
                mid_price=round(mid_price, 4),
                vig=round(vig, 4),
                volume=float(raw.get("volume", 0.0)),
                status=raw.get("active", True) and "active" or "closed",
                fetched_at=_utc_now(),
                venue="polymarket",
            )

        except Exception:
            return None


class DFSPickemVenueAdapter:
    """
    Base stub for DFS pick'em venues (PrizePicks, Underdog, Sleeper).
    Phase 7+ — requires new ADR before activation.

    Key difference from market-priced venues:
      implied_prob_method = 'bookmaker'
      mid_price = 0.50 for all lines (bookmaker targets balanced action)
      edge = p̂ - 0.50 (typically LARGER than Kalshi edge)
      Payout: fixed multiplier (2x typical) vs. binary $0/$1

    Concrete subclasses: PrizePicksVenueAdapter, UnderdogVenueAdapter, SleeperVenueAdapter
    """

    venue_id: str = "dfs_pickem_base"
    implied_prob_method: str = "bookmaker"

    def check_connectivity(self) -> tuple[bool, dict[str, Any]]:
        raise NotImplementedError("DFS pick'em adapter not yet implemented — new ADR required")

    def fetch_markets(
        self, market_type: MarketType, status: str = "open"
    ) -> tuple[bool, DS02Snapshot]:
        raise NotImplementedError("DFS pick'em adapter not yet implemented — new ADR required")

    def fetch_player_points_markets(
        self, sport: str = "NBA", status: str = "open"
    ) -> tuple[bool, DS02Snapshot]:
        """Legacy sport-string interface — thin shim over fetch_markets() (box 1.2)."""
        return self.fetch_markets(MarketType.NBA_PLAYER_POINTS, status=status)

    def fetch_market_detail(self, ticker: str) -> tuple[bool, Optional[PlayerMarket]]:
        raise NotImplementedError("DFS pick'em adapter not yet implemented — new ADR required")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tag_market(market: PlayerMarket, venue: str) -> PlayerMarket:
    """Return a copy of market with venue field set. PlayerMarket is frozen."""
    # Use __class__ to preserve subclass type if ever extended
    fields = {f: getattr(market, f) for f in market.__dataclass_fields__}
    fields["venue"] = venue
    return market.__class__(**fields)

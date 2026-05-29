"""
C5: Kalshi Market Data Client — DS-02 Price Feed
==================================================
Component:    C5 (Execution Engine) — market data sub-module
Phase active: Phase 5+ (Operational Readiness; DS-02)
Status:       CANONICAL (Phase 5 2026-05-28)
Upstream:     Kalshi trading API (api.elections.kalshi.com)
Downstream:   C3 Forecasting (market_implied_prob), C4 Risk Engine (edge calc)
Interfaces:   IF-C5-VENUE (read-only market data; ADR-0003)

Connectivity requirement (DS-02-B-001 resolved 2026-05-28):
  - REQUIRES Homebrew Python 3.11 (/usr/local/bin/python3.11) or .venv311
  - OpenSSL 3.6.2+ required for TLS handshake with api.elections.kalshi.com
  - LibreSSL (system Python) and older OpenSSL fail the TLS handshake (CloudFront WAF)

Security (NFR-05):
  - API key loaded from environment variable VENUE_API_KEY
  - Key never logged, never hardcoded, never written to disk
  - Read-only scope only — no order submission (ENV-01/02 guard in RiskEngine)

Series used:
  - KXNBAPTS: Pro Basketball Player Points (individual game thresholds)
  - Ticker format: KXNBAPTS-{DATE}{HOMETEAM}{AWAYTEAM}-{TEAMABBRV}{PLAYERID}-{THRESHOLD}
  - Example: KXNBAPTS-26MAY28OKCSAS-OKCSGILGEOUSALEXANDER2-25

Market structure:
  - Binary market: YES = player scores >= threshold points in the game
  - Price in USD (0.00–1.00); YES ask + NO ask typically = $1.01 (1% vig)
  - mid_price = (yes_ask + yes_bid) / 2
  - vig = yes_ask - yes_bid (half-spread for one side)

Kill switch constraint (NFR-03):
  - All public methods return (bool, data).
  - False on any API error or key validation failure.
  - Caller must check bool before using data.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C5"
KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
SERIES_PLAYER_POINTS = "KXNBAPTS"

# Request timeouts and retry config
REQUEST_TIMEOUT_S = 15
MAX_RETRIES = 3
RETRY_DELAY_S = 1.0

# Vig threshold — markets with vig > this are too wide to trade (per risk policy)
MAX_ACCEPTABLE_VIG = 0.05


# ---------------------------------------------------------------------------
# Data classes (DS-02 output schema — IF-C5-C3/C4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlayerMarket:
    """
    Single Kalshi player-points market with pricing.

    Represents the market for "player scores >= threshold points in game."
    mid_price is the fair value estimate: (yes_ask + yes_bid) / 2.
    vig is the full spread (yes_ask - yes_bid); half-spread is the cost to enter.
    """
    ticker: str
    title: str
    player_name: str
    team_abbr: str
    threshold: int
    game_date: str           # YYYY-MM-DD
    event_ticker: str
    yes_ask: float           # USD (0.00–1.00)
    yes_bid: float
    no_ask: float
    no_bid: float
    mid_price: float         # (yes_ask + yes_bid) / 2
    vig: float               # yes_ask - yes_bid (full spread)
    volume: float            # total volume in dollars
    status: str              # "active", "closed", etc.
    fetched_at: str          # UTC ISO timestamp
    venue: str = "kalshi"    # venue identifier — default "kalshi"; overridden by VenueAdapter

    @property
    def half_spread(self) -> float:
        return self.vig / 2.0

    @property
    def has_live_quotes(self) -> bool:
        return self.yes_ask > 0 and self.yes_bid > 0


@dataclass
class DS02Snapshot:
    """
    Collection of PlayerMarket records for one or more players/games.
    Consumed by EXP-004 and the edge calculation in C3/C4.
    """
    fetched_at: str
    markets: list[PlayerMarket] = field(default_factory=list)

    def for_player(self, player_name_fragment: str) -> list[PlayerMarket]:
        """Return all markets matching a player name fragment (case-insensitive)."""
        frag = player_name_fragment.upper()
        return [m for m in self.markets if frag in m.player_name.upper()]

    def closest_to_threshold(
        self,
        player_name_fragment: str,
        target_threshold: float,
    ) -> PlayerMarket | None:
        """
        Return the market with threshold closest to target_threshold.
        Used to align Kalshi fixed thresholds to our model's rolling-mean threshold.
        """
        candidates = self.for_player(player_name_fragment)
        if not candidates:
            return None
        return min(candidates, key=lambda m: abs(m.threshold - target_threshold))


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class KalshiMarketClient:
    """
    Read-only Kalshi market data client for DS-02.

    Retrieves player-points markets from api.elections.kalshi.com using
    a Bearer token. No order submission — read-only price feed.

    Requires:
        VENUE_API_KEY environment variable set to a valid Kalshi API key.
        Python linked against OpenSSL 3.6+ (Homebrew Python 3.11).

    Usage::

        client = KalshiMarketClient.from_env()
        ok, snapshot = client.fetch_player_points_markets()
        if not ok:
            trigger_kill_switch("DS-02 price feed unavailable")
        sga_markets = snapshot.for_player("Gilgeous-Alexander")
    """

    def __init__(self, api_key: str) -> None:
        if not api_key or len(api_key) < 10:
            raise ValueError("VENUE_API_KEY is missing or too short — check .env (NFR-05)")
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "prediction-market-bot/0.1.0",
        })

    @classmethod
    def from_env(cls) -> "KalshiMarketClient":
        """Construct from VENUE_API_KEY environment variable (NFR-05)."""
        key = os.environ.get("VENUE_API_KEY", "")
        if not key:
            raise EnvironmentError(
                "VENUE_API_KEY not set. Load .env before importing: "
                "python-dotenv or `export VENUE_API_KEY=...`"
            )
        return cls(key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> tuple[bool, Any]:
        """
        GET request with retry. Returns (ok, response_data).
        ok=False on any network/API error.
        """
        url = f"{KALSHI_BASE_URL}{path}"
        for attempt in range(MAX_RETRIES):
            try:
                r = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT_S)
                if r.status_code == 200:
                    return True, r.json()
                if r.status_code == 401:
                    return False, {"error": "Unauthorized — check VENUE_API_KEY"}
                if r.status_code == 429:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
                    continue
                return False, {"error": f"HTTP {r.status_code}", "body": r.text[:200]}
            except requests.exceptions.SSLError as e:
                return False, {
                    "error": "TLS handshake failed — requires Homebrew Python 3.11 (OpenSSL 3.6+)",
                    "detail": str(e),
                }
            except requests.exceptions.ConnectionError as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S)
                    continue
                return False, {"error": "Connection failed", "detail": str(e)}
            except Exception as e:
                return False, {"error": type(e).__name__, "detail": str(e)}
        return False, {"error": f"Max retries ({MAX_RETRIES}) exceeded"}

    @staticmethod
    def _parse_market(raw: dict) -> PlayerMarket | None:
        """Parse a raw Kalshi market dict into a PlayerMarket. Returns None on parse failure."""
        try:
            ticker = raw.get("ticker", "")
            title = raw.get("title", "")

            # Extract threshold from ticker (last segment after final "-")
            parts = ticker.split("-")
            try:
                threshold = int(parts[-1])
            except (ValueError, IndexError):
                return None

            # Extract game date from event_ticker (format: KXNBAPTS-26MAY28GAMEID)
            event_ticker = raw.get("event_ticker", "")
            game_date = ""
            date_match = re.search(r"(\d{2})([A-Z]{3})(\d{2})", event_ticker)
            if date_match:
                yr, mon_str, day = date_match.groups()
                months = {
                    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
                    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
                    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
                }
                game_date = f"20{yr}-{months.get(mon_str, '00')}-{day}"

            # Extract player name and team from title ("Player Name: 25+ points")
            player_name = title.split(":")[0].strip() if ":" in title else title
            # Team abbr from ticker segment before player ID
            team_abbr = ""
            if len(parts) >= 3:
                team_segment = parts[2]
                team_match = re.match(r"^([A-Z]{3})", team_segment)
                if team_match:
                    team_abbr = team_match.group(1)

            # Prices — API returns *_dollars fields in detail view
            yes_ask = float(raw.get("yes_ask_dollars") or raw.get("yes_ask") or 0)
            yes_bid = float(raw.get("yes_bid_dollars") or raw.get("yes_bid") or 0)
            no_ask = float(raw.get("no_ask_dollars") or raw.get("no_ask") or 0)
            no_bid = float(raw.get("no_bid_dollars") or raw.get("no_bid") or 0)

            mid_price = (yes_ask + yes_bid) / 2.0 if (yes_ask + yes_bid) > 0 else 0.0
            vig = max(0.0, yes_ask - yes_bid)

            volume = float(raw.get("volume_fp") or raw.get("volume_24h_fp") or 0)
            status = raw.get("status", "unknown")

            return PlayerMarket(
                ticker=ticker,
                title=title,
                player_name=player_name,
                team_abbr=team_abbr,
                threshold=threshold,
                game_date=game_date,
                event_ticker=event_ticker,
                yes_ask=yes_ask,
                yes_bid=yes_bid,
                no_ask=no_ask,
                no_bid=no_bid,
                mid_price=mid_price,
                vig=vig,
                volume=volume,
                status=status,
                fetched_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_connectivity(self) -> tuple[bool, dict]:
        """
        Verify API key and connectivity. Returns (ok, status_dict).
        Call this before any other method.
        """
        ok, data = self._get("/exchange/status")
        if not ok:
            return False, data
        exchange_active = data.get("exchange_active", False)
        trading_active = data.get("trading_active", False)
        return True, {
            "exchange_active": exchange_active,
            "trading_active": trading_active,
            "api_reachable": True,
        }

    def fetch_player_points_markets(
        self,
        status: str = "open",
        limit: int = 200,
    ) -> tuple[bool, DS02Snapshot]:
        """
        Fetch all open NBA player-points markets (KXNBAPTS series).

        Returns (ok, snapshot) where snapshot.markets contains PlayerMarket records.
        ok=False if the API call fails — caller must check before use.

        Parameters
        ----------
        status:
            "open", "closed", or "settled". Default: "open".
        limit:
            Max markets to fetch (Kalshi max per page = 200). Default: 200.
        """
        ok, data = self._get(
            "/markets",
            params={"limit": limit, "status": status, "series_ticker": SERIES_PLAYER_POINTS},
        )
        if not ok:
            return False, DS02Snapshot(fetched_at=_utc_now(), markets=[])

        raw_markets = data.get("markets", [])
        fetched_at = _utc_now()
        markets: list[PlayerMarket] = []

        for raw in raw_markets:
            # Fetch detailed view for each market to get dollar prices
            ticker = raw.get("ticker", "")
            ok_detail, detail = self._get(f"/markets/{ticker}")
            if ok_detail:
                market_data = detail.get("market", detail)
                parsed = self._parse_market(market_data)
            else:
                parsed = self._parse_market(raw)
            if parsed is not None:
                markets.append(parsed)

        return True, DS02Snapshot(fetched_at=fetched_at, markets=markets)

    def fetch_market_detail(self, ticker: str) -> tuple[bool, PlayerMarket | None]:
        """
        Fetch a single market by ticker. Returns (ok, PlayerMarket or None).
        """
        ok, data = self._get(f"/markets/{ticker}")
        if not ok:
            return False, None
        market_data = data.get("market", data)
        parsed = self._parse_market(market_data)
        return parsed is not None, parsed


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

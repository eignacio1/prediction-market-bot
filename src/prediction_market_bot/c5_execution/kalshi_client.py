"""
C5: Kalshi Market Data + Order Execution Client
================================================
Component:    C5 (Execution Engine)
Phase active: Phase 5+ (market data); Phase 6+ (order execution — ADR-0008)
Status:       CANONICAL (ADR-0008 2026-05-31)
Upstream:     Kalshi trading API (demo: external-api.demo.kalshi.co; live: external-api.kalshi.com)
Downstream:   C3 Forecasting (market_implied_prob), C4 Risk Engine (edge calc),
              C5 PaperTrader (order submission)
Interfaces:   IF-C5-VENUE (ADR-0003 read; ADR-0008 write)

Connectivity requirement (DS-02-B-001 resolved 2026-05-28):
  - REQUIRES Homebrew Python 3.11 (/usr/local/bin/python3.11) or .venv311
  - OpenSSL 3.6.2+ required for TLS handshake with Kalshi APIs
  - LibreSSL (system Python) and older OpenSSL fail the TLS handshake (CloudFront WAF)
  - T-111 (2026-05-31): legacy api.elections.kalshi.com returns 404 on authenticated endpoints.
    Correct URLs: demo=external-api.demo.kalshi.co, live=external-api.kalshi.com.
    Base URL now selected by BOT_ENV at runtime.

URL routing (T-114 2026-06-01):
  - Market data / price discovery (unauthenticated GETs) → always production.
    BOT_ENV=paper suppresses order submission only. Edge = model_p - market_price
    requires real market prices or the calculation is meaningless.
  - Order submission and portfolio endpoints (authenticated) → follow BOT_ENV:
    paper → demo sandbox; live → production.

Authentication (ADR-0008):
  - Kalshi v2 API uses RSA-PS256 (PSS+SHA256) request signing for all authenticated endpoints
  - Public endpoints (/exchange/status, /markets) require no auth
  - Authenticated endpoints (/portfolio/balance, /portfolio/orders) require:
      KALSHI-ACCESS-KEY:       API key ID (VENUE_API_KEY env var)
      KALSHI-ACCESS-TIMESTAMP: Unix milliseconds as string
      KALSHI-ACCESS-SIGNATURE: base64(RSA-SHA256(private_key, timestamp+METHOD+path))
  - Private key loaded from path in VENUE_PRIVATE_KEY_PATH env var
  - Private key file must NOT be in VCS (NFR-05)

Security (NFR-05):
  - API key ID and private key path loaded from environment only
  - Private key never logged, never hardcoded, never written to disk
  - ENV guard: BOT_ENV=paper permits demo orders; BOT_ENV=live permits live orders

Series used:
  - KXNBAPTS: Pro Basketball Player Points (individual game thresholds)
  - Ticker format: KXNBAPTS-{DATE}{HOMETEAM}{AWAYTEAM}-{TEAMABBRV}{PLAYERID}-{THRESHOLD}
  - Example: KXNBAPTS-26MAY28OKCSAS-OKCSGILGEOUSALEXANDER2-25

Market structure:
  - Binary market: YES = player scores >= threshold points in the game
  - Price in USD (0.00–1.00); YES ask + NO ask typically = $1.01 (1% vig)
  - mid_price = (yes_ask + yes_bid) / 2
  - vig = yes_ask - yes_bid (full spread)

Order sizing (ADR-0008):
  - contracts = floor(approved_size_usd / mid_price)
  - yes_price_cents = round(mid_price * 100)
  - Actual cost = contracts * yes_price_cents / 100
  - Minimum 1 contract per order

Kill switch constraint (NFR-03):
  - All public methods return (bool, data).
  - False on any API error or key validation failure.
  - Caller must check bool before using data.
"""

from __future__ import annotations

import base64
import hashlib
import math
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C5"

# Environment-aware base URLs (T-111: legacy api.elections.kalshi.com returns 404
# on authenticated endpoints — correct URLs confirmed from Kalshi official docs).
# BOT_ENV=paper routes to demo sandbox; BOT_ENV=live routes to production.
_KALSHI_DEMO_BASE_URL = "https://external-api.demo.kalshi.co/trade-api/v2"
_KALSHI_LIVE_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"


def _kalshi_base_url() -> str:
    """Authenticated endpoints (portfolio balance, order submission) — follow BOT_ENV."""
    env = os.environ.get("BOT_ENV", "paper").lower()
    return _KALSHI_LIVE_BASE_URL if env == "live" else _KALSHI_DEMO_BASE_URL


def _price_discovery_url() -> str:
    """Market data (prices, quotes, status) — always production regardless of BOT_ENV.

    T-114: paper mode suppresses order submission only. Using demo prices for edge
    calculations produces edge = model_p - fake_price which is meaningless.
    """
    return _KALSHI_LIVE_BASE_URL


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
    venue: str = "kalshi"    # venue identifier

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
        frag = player_name_fragment.upper()
        return [m for m in self.markets if frag in m.player_name.upper()]

    def closest_to_threshold(
        self,
        player_name_fragment: str,
        target_threshold: float,
    ) -> PlayerMarket | None:
        candidates = self.for_player(player_name_fragment)
        if not candidates:
            return None
        return min(candidates, key=lambda m: abs(m.threshold - target_threshold))


@dataclass
class KalshiOrder:
    """
    Result of a submitted Kalshi order (ADR-0008).

    Returned by submit_order(). ok=False if the order was rejected or failed.
    order_id is Kalshi's server-assigned ID; client_order_id is ours.
    contracts and filled_price_cents reflect what actually got filled.
    """
    ok: bool
    order_id: str            # Kalshi's order ID (empty string on failure)
    client_order_id: str     # Our UUID
    ticker: str
    side: str                # "yes" or "no"
    contracts: int           # number of contracts submitted
    yes_price_cents: int     # limit price in cents
    actual_cost_usd: float   # contracts * price / 100
    status: str              # "resting", "filled", "canceled", "rejected", "error"
    error: str = ""          # populated on failure


# ---------------------------------------------------------------------------
# RSA signing utilities (ADR-0008)
# ---------------------------------------------------------------------------


def _load_private_key(key_path: str):
    """Load RSA private key from PEM file. Returns cryptography key object."""
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        pem_bytes = Path(key_path).read_bytes()
        return load_pem_private_key(pem_bytes, password=None)
    except ImportError:
        raise ImportError(
            "cryptography package required for RSA signing: pip install cryptography"
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"RSA private key not found at {key_path}. "
            "Set VENUE_PRIVATE_KEY_PATH to the path of your Kalshi RSA private key .pem file. "
            "Do NOT commit this file to VCS (NFR-05)."
        )


def _sign_request(private_key, timestamp_ms: str, method: str, path: str) -> str:
    """
    Produce base64-encoded RSA-PS256 signature for a Kalshi API request.

    Kalshi v2 uses RSA-PSS with SHA-256 (PS256). PKCS1v15 is rejected.
    Signature message: timestamp_ms + METHOD_UPPER + path_without_query
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    path_no_query = path.split("?")[0]
    message = (timestamp_ms + method.upper() + path_no_query).encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _auth_headers(key_id: str, private_key, method: str, path: str) -> dict:
    """Build Kalshi authentication headers for a signed request."""
    timestamp_ms = str(int(time.time() * 1000))
    signature = _sign_request(private_key, timestamp_ms, method, path)
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
        "KALSHI-ACCESS-SIGNATURE": signature,
    }


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class KalshiMarketClient:
    """
    Kalshi market data + order execution client (ADR-0003 read; ADR-0008 write).

    Read-only methods (no RSA key required):
        check_connectivity(), fetch_player_points_markets(), fetch_market_detail()

    Authenticated methods (RSA key required — set VENUE_PRIVATE_KEY_PATH):
        get_balance(), submit_order()

    Usage::

        client = KalshiMarketClient.from_env()
        ok, snapshot = client.fetch_player_points_markets()
        ok, balance = client.get_balance()
        ok, order = client.submit_order(ticker, side, size_usd, mid_price)
    """

    def __init__(self, api_key_id: str, private_key=None) -> None:
        if not api_key_id or len(api_key_id) < 10:
            raise ValueError("VENUE_API_KEY is missing or too short — check .env (NFR-05)")
        self._key_id = api_key_id
        self._private_key = private_key  # None → authenticated endpoints unavailable
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "prediction-market-bot/0.1.0",
        })

    @classmethod
    def from_env(cls) -> "KalshiMarketClient":
        """
        Construct from environment variables (NFR-05).

        Required:  VENUE_API_KEY       — Kalshi API key ID
        Optional:  VENUE_PRIVATE_KEY_PATH — path to RSA private key .pem file
                   (required for get_balance() and submit_order())
        """
        key_id = os.environ.get("VENUE_API_KEY", "")
        if not key_id:
            raise EnvironmentError(
                "VENUE_API_KEY not set. Load .env before importing."
            )
        private_key = None
        key_path = os.environ.get("VENUE_PRIVATE_KEY_PATH", "")
        if key_path:
            private_key = _load_private_key(key_path)
        return cls(api_key_id=key_id, private_key=private_key)

    def has_signing_key(self) -> bool:
        """True if RSA private key is loaded — authenticated endpoints available."""
        return self._private_key is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None, authenticated: bool = False) -> tuple[bool, Any]:
        """GET with retry. Returns (ok, response_data).

        Unauthenticated (market data) → _price_discovery_url() always production.
        Authenticated (portfolio) → _kalshi_base_url() follows BOT_ENV.
        """
        base = _kalshi_base_url() if authenticated else _price_discovery_url()
        url = f"{base}{path}"
        full_path = f"/trade-api/v2{path}"

        for attempt in range(MAX_RETRIES):
            try:
                headers = {}
                if authenticated:
                    if not self._private_key:
                        return False, {"error": "RSA private key not loaded — set VENUE_PRIVATE_KEY_PATH"}
                    headers = _auth_headers(self._key_id, self._private_key, "GET", full_path)

                r = self._session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_S)
                if r.status_code == 200:
                    return True, r.json()
                if r.status_code == 401:
                    return False, {"error": "Unauthorized", "detail": r.text[:200]}
                if r.status_code in (429, 503):
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

    def _post(self, path: str, body: dict) -> tuple[bool, Any]:
        """POST with RSA signing and exponential backoff on 429. Returns (ok, response_data)."""
        if not self._private_key:
            return False, {"error": "RSA private key not loaded — set VENUE_PRIVATE_KEY_PATH"}

        url = f"{_kalshi_base_url()}{path}"
        full_path = f"/trade-api/v2{path}"

        for attempt in range(MAX_RETRIES):
            try:
                headers = _auth_headers(self._key_id, self._private_key, "POST", full_path)
                r = self._session.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT_S)
                if r.status_code in (200, 201):
                    return True, r.json()
                if r.status_code in (429, 503):
                    # T-138/GG-014: exponential backoff on rate-limit and transient server errors
                    delay = RETRY_DELAY_S * (2 ** (attempt + 1))
                    time.sleep(delay)
                    continue
                return False, {"error": f"HTTP {r.status_code}", "body": r.text[:500]}
            except Exception as e:
                return False, {"error": type(e).__name__, "detail": str(e)}
        return False, {"error": f"transient error — max retries ({MAX_RETRIES}) exceeded"}

    @staticmethod
    def _parse_market(raw: dict) -> PlayerMarket | None:
        try:
            ticker = raw.get("ticker", "")
            title = raw.get("title", "")

            parts = ticker.split("-")
            try:
                threshold = int(parts[-1])
            except (ValueError, IndexError):
                return None

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

            player_name = title.split(":")[0].strip() if ":" in title else title
            team_abbr = ""
            if len(parts) >= 3:
                team_segment = parts[2]
                team_match = re.match(r"^([A-Z]{3})", team_segment)
                if team_match:
                    team_abbr = team_match.group(1)

            yes_ask = float(raw.get("yes_ask_dollars") or raw.get("yes_ask") or 0)
            yes_bid = float(raw.get("yes_bid_dollars") or raw.get("yes_bid") or 0)
            no_ask = float(raw.get("no_ask_dollars") or raw.get("no_ask") or 0)
            no_bid = float(raw.get("no_bid_dollars") or raw.get("no_bid") or 0)

            mid_price = (yes_ask + yes_bid) / 2.0 if (yes_ask + yes_bid) > 0 else 0.0
            vig = max(0.0, yes_ask - yes_bid)

            volume = float(raw.get("volume_fp") or raw.get("volume_24h_fp") or 0)
            status = raw.get("status", "unknown")

            return PlayerMarket(
                ticker=ticker, title=title, player_name=player_name,
                team_abbr=team_abbr, threshold=threshold, game_date=game_date,
                event_ticker=event_ticker, yes_ask=yes_ask, yes_bid=yes_bid,
                no_ask=no_ask, no_bid=no_bid, mid_price=mid_price, vig=vig,
                volume=volume, status=status,
                fetched_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public API — read-only (no RSA required)
    # ------------------------------------------------------------------

    def check_connectivity(self) -> tuple[bool, dict]:
        """Verify connectivity. Does NOT require RSA key."""
        ok, data = self._get("/exchange/status")
        if not ok:
            return False, data
        return True, {
            "exchange_active": data.get("exchange_active", False),
            "trading_active": data.get("trading_active", False),
            "api_reachable": True,
            "signing_key_loaded": self.has_signing_key(),
        }

    def fetch_player_points_markets(
        self,
        status: str = "open",
        page_size: int = 200,
    ) -> tuple[bool, DS02Snapshot]:
        """Fetch ALL open NBA player-points markets (KXNBAPTS series) with cursor pagination."""
        all_raw: list[dict] = []
        cursor: str | None = None

        while True:
            params: dict = {
                "limit": page_size,
                "status": status,
                "series_ticker": SERIES_PLAYER_POINTS,
            }
            if cursor:
                params["cursor"] = cursor

            ok, data = self._get("/markets", params=params)
            if not ok:
                if not all_raw:
                    return False, DS02Snapshot(fetched_at=_utc_now(), markets=[])
                break

            page = data.get("markets", [])
            all_raw.extend(page)

            cursor = data.get("cursor")
            if not cursor or len(page) < page_size:
                break

        fetched_at = _utc_now()
        markets: list[PlayerMarket] = []

        for raw in all_raw:
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
        """Fetch a single market by ticker."""
        ok, data = self._get(f"/markets/{ticker}")
        if not ok:
            return False, None
        market_data = data.get("market", data)
        parsed = self._parse_market(market_data)
        return parsed is not None, parsed

    # ------------------------------------------------------------------
    # Public API — authenticated (RSA key required)
    # ------------------------------------------------------------------

    def get_balance(self) -> tuple[bool, dict]:
        """
        Fetch portfolio balance from Kalshi. Requires RSA private key.

        Returns (ok, {"balance_usd": float, "payout_usd": float}).
        """
        ok, data = self._get("/portfolio/balance", authenticated=True)
        if not ok:
            return False, data
        # Response: {"balance": <cents int>, "balance_dollars": "<str>",
        #            "portfolio_value": <cents int>, "updated_ts": <unix>}
        balance_cents = data.get("balance", 0)
        portfolio_value_cents = data.get("portfolio_value", 0)
        return True, {
            "balance_usd": balance_cents / 100.0,
            "portfolio_value_usd": portfolio_value_cents / 100.0,
            "balance_dollars": data.get("balance_dollars", ""),
        }

    def submit_order(
        self,
        ticker: str,
        side: str,
        size_usd: float,
        mid_price: float,
        client_order_id: str | None = None,
    ) -> KalshiOrder:
        """
        Submit a limit order to Kalshi (ADR-0008).

        Parameters
        ----------
        ticker:          Kalshi market ticker (e.g. KXNBAPTS-26JUN03...-20)
        side:            "yes" or "no"
        size_usd:        Kelly-approved bet size in USD
        mid_price:       Market mid price (0.00–1.00) — used as limit price
        client_order_id: Optional idempotency key; auto-generated if None

        Returns KalshiOrder with ok=True on success, ok=False on any failure.
        """
        if not self._private_key:
            return KalshiOrder(
                ok=False, order_id="", client_order_id=client_order_id or "",
                ticker=ticker, side=side, contracts=0,
                yes_price_cents=0, actual_cost_usd=0.0,
                status="error", error="RSA private key not loaded",
            )

        client_order_id = client_order_id or str(uuid.uuid4())

        # Convert USD size + mid_price to contract count + cent price
        if side == "yes":
            price = mid_price
        else:
            price = 1.0 - mid_price

        price_cents = max(1, min(99, round(price * 100)))
        contracts = max(1, math.floor(size_usd / (price_cents / 100.0)))
        actual_cost = round(contracts * price_cents / 100.0, 4)

        # API requires exactly one of yes_price or no_price (not both)
        body: dict[str, Any] = {
            "ticker": ticker,
            "client_order_id": client_order_id,
            "type": "limit",
            "action": "buy",
            "side": side,
            "count": contracts,
            "yes_price" if side == "yes" else "no_price": price_cents,
        }

        ok, data = self._post("/portfolio/orders", body)

        if not ok:
            return KalshiOrder(
                ok=False, order_id="", client_order_id=client_order_id,
                ticker=ticker, side=side, contracts=contracts,
                yes_price_cents=price_cents, actual_cost_usd=actual_cost,
                status="error", error=str(data.get("error", data)),
            )

        order_data = data.get("order", data)
        return KalshiOrder(
            ok=True,
            order_id=order_data.get("order_id", ""),
            client_order_id=client_order_id,
            ticker=ticker,
            side=side,
            contracts=contracts,
            yes_price_cents=price_cents,
            actual_cost_usd=actual_cost,
            status=order_data.get("status", "submitted"),
        )


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

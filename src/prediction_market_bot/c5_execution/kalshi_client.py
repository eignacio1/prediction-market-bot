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
  - KXMLBHIT: Pro Baseball Hits (individual game thresholds, confirmed 2026-06-23)
  - Ticker format: KXMLBHIT-{DATE}{TIME}{AWAYTEAM}{HOMETEAM}-{TEAMABBRV}{PLAYERID}-{THRESHOLD}
  - Example: KXMLBHIT-26JUN241607BALLAA-LAAJADELL7-4
  - Note: MLB uses AWAY-HOME team order (vs NBA HOME-AWAY); includes 4-digit time (HHMM EDT)

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
import logging
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

from prediction_market_bot.c5_execution.market_type_registry import (
    MarketType,
    series_ticker_for,
)

logger = logging.getLogger(__name__)

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
    """Authenticated endpoints (portfolio balance, order submission) — follow BOT_ENV.

    GG-152: BOT_ENV's only two literal accepted values are "paper" and "live"
    (case-insensitive) — "ENV-01"/"ENV-02"/"ENV-03" are documentation labels for
    those states (see .env.example), never values this function should receive.
    An explicitly-set, unrecognized value fails loud rather than silently
    routing order submission to the demo sandbox — silent fallback here would
    let a live-capital activation believe it was hitting production when it
    was not. Unset (not set at all) still defaults safely to demo, unchanged.
    """
    raw = os.environ.get("BOT_ENV")
    if raw is None:
        return _KALSHI_DEMO_BASE_URL
    env = raw.lower()
    if env == "live":
        return _KALSHI_LIVE_BASE_URL
    if env == "paper":
        return _KALSHI_DEMO_BASE_URL
    raise ValueError(
        f"BOT_ENV={raw!r} is not a recognized value — must be 'paper' or 'live' "
        "(case-insensitive). Refusing to silently route order submission to the "
        "demo sandbox (GG-152)."
    )


# GG-666/W72.1: order-write path host guard. No ADR authorising live capital exists, so this is
# None; a future accepted ADR sets it to its id AND the operator exports KALSHI_LIVE_CAPITAL_ADR
# with the same id. Both must agree, otherwise any non-demo host is refused.
LIVE_CAPITAL_ADR: str | None = None


def _order_write_host_refusal() -> str | None:
    """Return a refusal reason if order writes (POST/DELETE) must not go to the resolved host."""
    try:
        base = _kalshi_base_url()
    except ValueError as e:
        return f"unrecognised BOT_ENV: {e}"
    if base == _KALSHI_DEMO_BASE_URL:
        return None
    if LIVE_CAPITAL_ADR and os.environ.get("KALSHI_LIVE_CAPITAL_ADR") == LIVE_CAPITAL_ADR:
        return None
    return f"non-demo host {base} refused: no accepted live-capital ADR (GG-666)"


def _price_discovery_url() -> str:
    """Market data (prices, quotes, status) — always production regardless of BOT_ENV.

    T-114: paper mode suppresses order submission only. Using demo prices for edge
    calculations produces edge = model_p - fake_price which is meaningless.
    """
    return _KALSHI_LIVE_BASE_URL


# Box 1.3 (Market Expansion Phase 1): these resolve through market_type_registry.py
# rather than hardcoding series tickers here. Names kept as aliases so no downstream
# caller (venue_adapter.py, run_t2/t3/t4_mlb_*.py, tests) needs to change.
SERIES_PLAYER_POINTS: str = series_ticker_for(MarketType.NBA_PLAYER_POINTS)

SERIES_MLB_PLAYER_HITS: str = series_ticker_for(MarketType.MLB_PLAYER_PROP_HITS)

# Request timeouts and retry config
REQUEST_TIMEOUT_S = 15
MAX_RETRIES = 4      # T-164/GG-014: raised 3→4; delays 4+8+16+32=60s covers most rate-limit windows
RETRY_DELAY_S = 2.0  # T-164/GG-014: raised 1.0→2.0; delays = RETRY_DELAY_S × 2^(attempt+1)

# Vig threshold — markets with vig > this are too wide to trade (per risk policy)
MAX_ACCEPTABLE_VIG = 0.05

# GG-252: NFL game-market series (moneyline/spread/totals/team-totals). These are
# team-vs-team shaped, not player-prop shaped — _parse_market() dispatches tickers
# from these series to _parse_nfl_game_market() / GameMarket instead of
# _parse_player_market() / PlayerMarket. Grammar derived from live tickers fetched
# 2026-09-07 (see GG-252 resolution note), not from a spec:
#   KXNFLGAME-{event}-{TEAM}            e.g. KXNFLGAME-26SEP21NYGLAR-NYG
#     strike_type="structured", floor_strike=null, custom_strike.football_team=<uuid>
#   KXNFLSPREAD-{event}-{TEAM}{N}       e.g. KXNFLSPREAD-26SEP14DENKC-KC8 (floor_strike=7.5)
#     strike_type="greater", floor_strike=<float>, custom_strike.football_team=<uuid>
#   KXNFLTOTAL-{event}-{N}              e.g. KXNFLTOTAL-26SEP14DENKC-64 (floor_strike=63.5)
#     strike_type="greater", floor_strike=<float>, custom_strike=null (not team-scoped)
#   KXNFLTEAMTOTAL-{event}-{TEAM}{N}    e.g. KXNFLTEAMTOTAL-26SEP10SFLAR-SF43 (floor_strike=42.5)
#     strike_type="greater", floor_strike=<float>, custom_strike.football_team=<uuid>
# Team codes are variable-length (2-3 chars: KC, SF, NYG, LAR) — the ticker-tail
# digit suffix (N = ceil(floor_strike)) is NOT parsed for the threshold; floor_strike
# is read directly from the raw payload, which is why team-code length doesn't matter.
_NFL_GAME_SERIES = frozenset({
    "KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL",
})

# GG-255/T-538: MLB game-market series (moneyline/run_line/game_total/team_total/
# partial_game). Same team-vs-team shape as _NFL_GAME_SERIES above — dispatched
# to _parse_mlb_game_market() / GameMarket, additive to the NFL dispatch, not a
# replacement. Grammar derived from live tickers fetched 2026-09-10 (not a spec):
#   KXMLBGAME-{event}-{TEAM}            e.g. KXMLBGAME-26SEP122010TEXAZ-TEX
#     strike_type="structured", floor_strike=null, custom_strike.baseball_team=<uuid>
#   KXMLBSPREAD-{event}-{TEAM}{N}       e.g. KXMLBSPREAD-26SEP091940AZKC-KC5 (floor_strike=4.5)
#     strike_type="greater", floor_strike=<float>, custom_strike.baseball_team=<uuid>
#   KXMLBTOTAL-{event}-{N}              e.g. KXMLBTOTAL-26SEP091840NYMMIA-25 (floor_strike=24.5)
#     strike_type="greater", floor_strike=<float>, custom_strike=null (not team-scoped)
#   KXMLBTEAMTOTAL-{event}-{TEAM}{N}    e.g. KXMLBTEAMTOTAL-26SEP101940PITCWS-PIT8 (floor_strike=7.5)
#     strike_type="greater", floor_strike=<float>, custom_strike.baseball_team=<uuid>
#   KXMLBF3/F5/F7-{event}-{TEAM|TIE}    e.g. KXMLBF3-26SEP101940PITCWS-PIT, ...-TIE
#     strike_type="structured", floor_strike=null, custom_strike.baseball_team=<uuid>
#     (F3/F5/F7 = first-3/5/7-innings partial-game winner; MLB, unlike NFL, has
#     a real three-way outcome here — a "TIE" ticker tail exists alongside team
#     tails. TIE is NOT a team code; it is passed through as team_abbr="TIE" so
#     it round-trips visibly rather than being silently misparsed as one.)
# Key difference from NFL's custom_strike key ("football_team" vs "baseball_team")
# is why this cannot share _parse_nfl_game_market() unmodified.
_MLB_GAME_SERIES = frozenset({
    "KXMLBGAME", "KXMLBSPREAD", "KXMLBTOTAL", "KXMLBTEAMTOTAL",
    "KXMLBF3", "KXMLBF5", "KXMLBF7",
})


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


@dataclass(frozen=True)
class GameMarket:
    """
    Single Kalshi team-vs-team game market (GG-252).

    Sibling to PlayerMarket, not a variant of it — game markets have no player
    and no guaranteed numeric threshold (moneyline markets are a bare "team A
    wins" proposition with strike_type="structured" and no floor_strike at all).
    market_type distinguishes the NFL and MLB series this represents:
      "moneyline"    — KXNFLGAME / KXMLBGAME (threshold is always None)
      "spread"       — KXNFLSPREAD (threshold = floor_strike, team-scoped)
      "run_line"     — KXMLBSPREAD, MLB's spread equivalent (threshold = floor_strike, team-scoped)
      "total"        — KXNFLTOTAL / KXMLBTOTAL (threshold = floor_strike, game-level, no team)
      "team_total"   — KXNFLTEAMTOTAL / KXMLBTEAMTOTAL (threshold = floor_strike, team-scoped)
      "partial_game" — KXMLBF3/F5/F7, MLB-only, no NFL analogue (threshold is
                        always None; team_abbr may be "TIE" — see _MLB_GAME_SERIES
                        comment above for why that is not a real team code)
    team_abbr is "" for game-level totals (not team-scoped). outcome_desc is
    Kalshi's own pre-rendered human-readable description (yes_sub_title).
    """
    ticker: str
    title: str
    market_type: str         # "moneyline" | "spread" | "run_line" | "total" | "team_total" | "partial_game"
    team_abbr: str           # "" when not team-scoped (e.g. game-level total)
    threshold: float | None  # floor_strike; None for moneyline (structured)
    outcome_desc: str        # yes_sub_title — clean human-readable outcome text
    game_date: str            # YYYY-MM-DD
    event_ticker: str
    yes_ask: float           # USD (0.00-1.00)
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


class KalshiThresholdUndefined(ValueError):
    """Raised by derive_kalshi_threshold() when a GameMarket has no numeric
    threshold and is not one of the known structured (bare-proposition)
    market types. See derive_kalshi_threshold()'s docstring — this exists so
    a settleable position is refused at open_position() call time rather
    than silently written with kalshi_threshold=None (GG-291)."""


def derive_kalshi_threshold(mkt: "GameMarket") -> float:
    """Return the kalshi_threshold value a caller must pass to
    PaperTrader.open_position() for this market, never None (GG-291).

    mkt.threshold (GameMarket.threshold, sourced from Kalshi's own
    floor_strike) is the single source of truth for spread/run_line/total/
    team_total lines -- returned as-is, unrounded.

    moneyline and partial_game are the two market_types where
    GameMarket.threshold is legitimately always None (see GameMarket's own
    docstring: both are "structured" bare-proposition strikes with no
    floor_strike at all). Both settle on a point-margin-vs-zero basis, so
    0.0 is the correct threshold, not a placeholder -- this mirrors
    game_market_settlement.py's "a moneyline is a spread at zero" design
    note.

    Any other market_type with threshold is None is not a data value this
    function has ever been told how to handle -- refuse (raise) rather than
    write a null threshold into a settleable position. Never parse the
    ticker's strike-suffix digits here; see the ticker-shape comment above
    GameMarket and game_market_settlement.py's module docstring for why.
    """
    if mkt.threshold is not None:
        return float(mkt.threshold)
    if mkt.market_type in ("moneyline", "partial_game"):
        return 0.0
    raise KalshiThresholdUndefined(
        f"no derivable kalshi_threshold for ticker={mkt.ticker!r} "
        f"market_type={mkt.market_type!r}: threshold is None and "
        f"market_type is not one of the known structured types "
        f"('moneyline', 'partial_game'). Refusing to open a position with "
        f"a null threshold."
    )


@dataclass
class DS02Snapshot:
    """
    Collection of PlayerMarket records for one or more players/games.
    Consumed by EXP-004 and the edge calculation in C3/C4.
    """
    fetched_at: str
    markets: list[PlayerMarket] = field(default_factory=list)
    unparsed_count: int = 0  # GG-252: raw markets fetched but dropped by the parser

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
class GameMarketSnapshot:
    """Collection of GameMarket records for one or more NFL games (GG-252)."""
    fetched_at: str
    markets: list[GameMarket] = field(default_factory=list)
    unparsed_count: int = 0  # raw markets fetched but dropped by the parser

    def for_event(self, event_ticker: str) -> list[GameMarket]:
        return [m for m in self.markets if m.event_ticker == event_ticker]


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


def _load_private_key(key_path: str) -> Any:
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


def _sign_request(private_key: Any, timestamp_ms: str, method: str, path: str) -> str:
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


def _auth_headers(key_id: str, private_key: Any, method: str, path: str) -> dict[str, Any]:
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

    def __init__(self, api_key_id: str, private_key: Any = None) -> None:
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

    def _get(self, path: str, params: dict[str, Any] | None = None, authenticated: bool = False) -> tuple[bool, Any]:
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
                    # T-138/GG-014: exponential backoff on rate-limit and transient server errors
                    time.sleep(RETRY_DELAY_S * (2 ** (attempt + 1)))
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

    def _post(self, path: str, body: dict[str, Any]) -> tuple[bool, Any]:
        """POST with RSA signing and exponential backoff on 429. Returns (ok, response_data)."""
        if not self._private_key:
            return False, {"error": "RSA private key not loaded — set VENUE_PRIVATE_KEY_PATH"}

        refusal = _order_write_host_refusal()
        if refusal:
            return False, {"error": "host_refused", "detail": refusal}
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
    def _parse_market(raw: dict[str, Any]) -> PlayerMarket | GameMarket | None:
        """Dispatch to the player-prop or NFL-game parser based on series (GG-252).

        _NFL_GAME_SERIES tickers (KXNFLGAME/KXNFLSPREAD/KXNFLTOTAL/KXNFLTEAMTOTAL)
        and _MLB_GAME_SERIES tickers (KXMLBGAME/KXMLBSPREAD/KXMLBTOTAL/
        KXMLBTEAMTOTAL/KXMLBF3/F5/F7 — GG-255/T-538) are team-vs-team shaped and
        cannot be represented by PlayerMarket's player_name/team_abbr/
        threshold:int fields — they route to _parse_nfl_game_market()/
        _parse_mlb_game_market()/GameMarket instead. Everything else (KXNBAPTS,
        KXMLBHIT, future player-prop series) is unchanged from before GG-252 —
        this dispatcher only ever ADDS a new routing branch, never alters the
        fallback path player-prop series already take.
        """
        ticker = raw.get("ticker", "")
        series = ticker.split("-")[0] if ticker else ""
        if series in _NFL_GAME_SERIES:
            return KalshiMarketClient._parse_nfl_game_market(raw)
        if series in _MLB_GAME_SERIES:
            return KalshiMarketClient._parse_mlb_game_market(raw)
        return KalshiMarketClient._parse_player_market(raw)

    @staticmethod
    def _game_date_from_event_ticker(event_ticker: str) -> str:
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
        return game_date

    @staticmethod
    def _parse_player_market(raw: dict[str, Any]) -> PlayerMarket | None:
        ticker = raw.get("ticker", "")
        try:
            title = raw.get("title", "")

            parts = ticker.split("-")
            try:
                threshold = int(parts[-1])
            except (ValueError, IndexError):
                logger.warning(
                    "GG-252: unparseable player-prop market — non-numeric ticker "
                    "tail (expected trailing threshold int): ticker=%s", ticker,
                )
                return None

            event_ticker = raw.get("event_ticker", "")
            game_date = KalshiMarketClient._game_date_from_event_ticker(event_ticker)

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
        except Exception as e:
            logger.warning(
                "GG-252: unparseable player-prop market — ticker=%s error=%s: %s",
                ticker, type(e).__name__, e,
            )
            return None

    @staticmethod
    def _parse_nfl_game_market(raw: dict[str, Any]) -> GameMarket | None:
        """Parse an NFL game-market (moneyline/spread/total/team_total) — GG-252.

        Reads strike_type/floor_strike/custom_strike directly from the raw
        payload rather than parsing a threshold out of the ticker tail — Kalshi
        already exposes the authoritative numeric line (floor_strike) and the
        team scope (custom_strike.football_team), and team codes in these
        tickers are variable-length (2-3 chars: KC, SF, NYG, LAR), which makes
        fixed-width ticker-suffix parsing unreliable for recovering them.
        """
        ticker = raw.get("ticker", "")
        try:
            title = raw.get("title", "")
            event_ticker = raw.get("event_ticker", "")
            series = ticker.split("-")[0] if ticker else ""
            parts = ticker.split("-")
            game_date = KalshiMarketClient._game_date_from_event_ticker(event_ticker)
            outcome_desc = raw.get("yes_sub_title", "") or title
            floor_strike = raw.get("floor_strike")
            has_team = bool((raw.get("custom_strike") or {}).get("football_team"))

            if series == "KXNFLGAME":
                market_type = "moneyline"
                threshold = None
                tail = parts[-1] if parts else ""
                team_match = re.match(r"^([A-Z]{2,3})$", tail)
                team_abbr = team_match.group(1) if team_match else ""
            elif series == "KXNFLTOTAL":
                market_type = "total"
                team_abbr = ""
                if floor_strike is None:
                    logger.warning(
                        "GG-252: unparseable KXNFLTOTAL market — missing "
                        "floor_strike: ticker=%s", ticker,
                    )
                    return None
                threshold = float(floor_strike)
            elif series in ("KXNFLSPREAD", "KXNFLTEAMTOTAL"):
                market_type = "spread" if series == "KXNFLSPREAD" else "team_total"
                tail = parts[-1] if parts else ""
                team_match = re.match(r"^([A-Z]{2,3})", tail)
                team_abbr = team_match.group(1) if team_match else ""
                if floor_strike is None:
                    logger.warning(
                        "GG-252: unparseable %s market — missing floor_strike: "
                        "ticker=%s", series, ticker,
                    )
                    return None
                threshold = float(floor_strike)
            else:
                # Should be unreachable — _parse_market only dispatches here for
                # tickers whose series is in _NFL_GAME_SERIES.
                logger.warning(
                    "GG-252: _parse_nfl_game_market called for unrecognized "
                    "series: ticker=%s series=%s", ticker, series,
                )
                return None

            yes_ask = float(raw.get("yes_ask_dollars") or raw.get("yes_ask") or 0)
            yes_bid = float(raw.get("yes_bid_dollars") or raw.get("yes_bid") or 0)
            no_ask = float(raw.get("no_ask_dollars") or raw.get("no_ask") or 0)
            no_bid = float(raw.get("no_bid_dollars") or raw.get("no_bid") or 0)

            mid_price = (yes_ask + yes_bid) / 2.0 if (yes_ask + yes_bid) > 0 else 0.0
            vig = max(0.0, yes_ask - yes_bid)

            volume = float(raw.get("volume_fp") or raw.get("volume_24h_fp") or 0)
            status = raw.get("status", "unknown")

            return GameMarket(
                ticker=ticker, title=title, market_type=market_type,
                team_abbr=team_abbr, threshold=threshold, outcome_desc=outcome_desc,
                game_date=game_date, event_ticker=event_ticker,
                yes_ask=yes_ask, yes_bid=yes_bid, no_ask=no_ask, no_bid=no_bid,
                mid_price=mid_price, vig=vig, volume=volume, status=status,
                fetched_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            )
        except Exception as e:
            logger.warning(
                "GG-252: unparseable NFL game market — ticker=%s error=%s: %s",
                ticker, type(e).__name__, e,
            )
            return None

    @staticmethod
    def _parse_mlb_game_market(raw: dict[str, Any]) -> GameMarket | None:
        """Parse an MLB game-market (moneyline/run_line/total/team_total/
        partial_game) — GG-255/T-538. Modeled on _parse_nfl_game_market();
        the one structural difference is Kalshi's custom_strike key for MLB
        is "baseball_team", not "football_team" (confirmed live 2026-09-10).

        Reads strike_type/floor_strike/custom_strike directly from the raw
        payload rather than parsing a threshold out of the ticker tail, for
        the same reason as the NFL parser: floor_strike is the authoritative
        numeric line and team codes are variable-length (2-3 chars).

        KXMLBF3/F5/F7 (partial_game) have a genuine three-way outcome MLB
        alone among the sports covered here — a "TIE" ticker tail exists
        alongside team tails (first-N-innings can end tied). "TIE" is passed
        through as team_abbr verbatim rather than matched against the team
        regex and silently treated as a team code.
        """
        ticker = raw.get("ticker", "")
        try:
            title = raw.get("title", "")
            event_ticker = raw.get("event_ticker", "")
            series = ticker.split("-")[0] if ticker else ""
            parts = ticker.split("-")
            game_date = KalshiMarketClient._game_date_from_event_ticker(event_ticker)
            outcome_desc = raw.get("yes_sub_title", "") or title
            floor_strike = raw.get("floor_strike")

            if series == "KXMLBGAME":
                market_type = "moneyline"
                threshold = None
                tail = parts[-1] if parts else ""
                team_match = re.match(r"^([A-Z]{2,3})$", tail)
                team_abbr = team_match.group(1) if team_match else tail
            elif series == "KXMLBTOTAL":
                market_type = "total"
                team_abbr = ""
                if floor_strike is None:
                    logger.warning(
                        "GG-255: unparseable KXMLBTOTAL market — missing "
                        "floor_strike: ticker=%s", ticker,
                    )
                    return None
                threshold = float(floor_strike)
            elif series == "KXMLBSPREAD":
                market_type = "run_line"
                tail = parts[-1] if parts else ""
                team_match = re.match(r"^([A-Z]{2,3})", tail)
                team_abbr = team_match.group(1) if team_match else ""
                if floor_strike is None:
                    logger.warning(
                        "GG-255: unparseable KXMLBSPREAD market — missing "
                        "floor_strike: ticker=%s", ticker,
                    )
                    return None
                threshold = float(floor_strike)
            elif series == "KXMLBTEAMTOTAL":
                market_type = "team_total"
                tail = parts[-1] if parts else ""
                team_match = re.match(r"^([A-Z]{2,3})", tail)
                team_abbr = team_match.group(1) if team_match else ""
                if floor_strike is None:
                    logger.warning(
                        "GG-255: unparseable KXMLBTEAMTOTAL market — missing "
                        "floor_strike: ticker=%s", ticker,
                    )
                    return None
                threshold = float(floor_strike)
            elif series in ("KXMLBF3", "KXMLBF5", "KXMLBF7"):
                market_type = "partial_game"
                threshold = None
                tail = parts[-1] if parts else ""
                # "TIE" deliberately not matched by the team regex — passed
                # through verbatim so a tie outcome is visible, not silently
                # mistaken for a team code (see class-level docstring/GG-255).
                if tail == "TIE":
                    team_abbr = "TIE"
                else:
                    team_match = re.match(r"^([A-Z]{2,3})$", tail)
                    team_abbr = team_match.group(1) if team_match else tail
            else:
                # Should be unreachable — _parse_market only dispatches here
                # for tickers whose series is in _MLB_GAME_SERIES.
                logger.warning(
                    "GG-255: _parse_mlb_game_market called for unrecognized "
                    "series: ticker=%s series=%s", ticker, series,
                )
                return None

            yes_ask = float(raw.get("yes_ask_dollars") or raw.get("yes_ask") or 0)
            yes_bid = float(raw.get("yes_bid_dollars") or raw.get("yes_bid") or 0)
            no_ask = float(raw.get("no_ask_dollars") or raw.get("no_ask") or 0)
            no_bid = float(raw.get("no_bid_dollars") or raw.get("no_bid") or 0)

            mid_price = (yes_ask + yes_bid) / 2.0 if (yes_ask + yes_bid) > 0 else 0.0
            vig = max(0.0, yes_ask - yes_bid)

            volume = float(raw.get("volume_fp") or raw.get("volume_24h_fp") or 0)
            status = raw.get("status", "unknown")

            return GameMarket(
                ticker=ticker, title=title, market_type=market_type,
                team_abbr=team_abbr, threshold=threshold, outcome_desc=outcome_desc,
                game_date=game_date, event_ticker=event_ticker,
                yes_ask=yes_ask, yes_bid=yes_bid, no_ask=no_ask, no_bid=no_bid,
                mid_price=mid_price, vig=vig, volume=volume, status=status,
                fetched_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            )
        except Exception as e:
            logger.warning(
                "GG-255: unparseable MLB game market — ticker=%s error=%s: %s",
                ticker, type(e).__name__, e,
            )
            return None

    # ------------------------------------------------------------------
    # Public API — read-only (no RSA required)
    # ------------------------------------------------------------------

    def check_connectivity(self) -> tuple[bool, dict[str, Any]]:
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
        series_ticker: str = SERIES_PLAYER_POINTS,
    ) -> tuple[bool, DS02Snapshot]:
        """Fetch ALL open markets for the given series with cursor pagination.

        series_ticker selects the sport:
          SERIES_PLAYER_POINTS   (KXNBAPTS) — NBA points markets (default)
          SERIES_MLB_PLAYER_HITS (KXMLBHIT) — MLB hits markets
        """
        all_raw: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {
                "limit": page_size,
                "status": status,
                "series_ticker": series_ticker,
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
        unparsed_count = 0

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
            else:
                unparsed_count += 1

        if unparsed_count:
            logger.warning(
                "GG-252: %d of %d raw %s markets failed to parse and were dropped",
                unparsed_count, len(all_raw), series_ticker,
            )

        return True, DS02Snapshot(
            fetched_at=fetched_at, markets=markets, unparsed_count=unparsed_count,
        )

    def fetch_game_markets(
        self,
        series_ticker: str,
        status: str = "open",
        page_size: int = 200,
    ) -> tuple[bool, GameMarketSnapshot]:
        """Fetch ALL open game markets for one series (GG-252/GG-255).

        series_ticker must be one of _NFL_GAME_SERIES (KXNFLGAME, KXNFLSPREAD,
        KXNFLTOTAL, KXNFLTEAMTOTAL) or _MLB_GAME_SERIES (KXMLBGAME,
        KXMLBSPREAD, KXMLBTOTAL, KXMLBTEAMTOTAL, KXMLBF3, KXMLBF5, KXMLBF7).
        This method itself was never NFL-hardcoded — it delegates parsing to
        _parse_market(), whose series dispatch is what determines NFL vs.
        MLB vs. player-prop handling (confirmed by direct read, GG-255
        Deliverable 2: zero changes needed here for MLB support). Mirrors
        fetch_player_points_markets' pagination/detail-fetch pattern but
        returns GameMarket records.
        """
        all_raw: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {
                "limit": page_size,
                "status": status,
                "series_ticker": series_ticker,
            }
            if cursor:
                params["cursor"] = cursor

            ok, data = self._get("/markets", params=params)
            if not ok:
                if not all_raw:
                    return False, GameMarketSnapshot(fetched_at=_utc_now(), markets=[])
                break

            page = data.get("markets", [])
            all_raw.extend(page)

            cursor = data.get("cursor")
            if not cursor or len(page) < page_size:
                break

        fetched_at = _utc_now()
        markets: list[GameMarket] = []
        unparsed_count = 0

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
            else:
                unparsed_count += 1

        if unparsed_count:
            logger.warning(
                "GG-252: %d of %d raw %s markets failed to parse and were dropped",
                unparsed_count, len(all_raw), series_ticker,
            )

        return True, GameMarketSnapshot(
            fetched_at=fetched_at, markets=markets, unparsed_count=unparsed_count,
        )

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

    def get_balance(self) -> tuple[bool, dict[str, Any]]:
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
        band: str | None = None,
    ) -> KalshiOrder:
        """
        Submit a limit order to Kalshi (ADR-0008).

        GG-745/NFR-03: every order path funnels through here, so the kill switch is checked
        HERE (kill_switch_state.halt_reason): the global flag halts all, a band flag only its
        ``band``; an unlabeled caller is halted by any flag. A halted call places nothing.

        Parameters
        ----------
        ticker:          Kalshi market ticker (e.g. KXNBAPTS-26JUN03...-20)
        side:            "yes" or "no"
        size_usd:        Kelly-approved bet size in USD
        mid_price:       Market mid price (0.00–1.00) — used as limit price
        client_order_id: Optional idempotency key; auto-generated if None

        Returns KalshiOrder with ok=True on success, ok=False on any failure.
        """
        from prediction_market_bot.c5_execution import kill_switch_state as _ksw
        _halt = _ksw.halt_reason(band_name=band)
        if _halt:
            logger.warning("submit_order REFUSED (kill switch): %s ticker=%s band=%s", _halt, ticker, band)
            return KalshiOrder(
                ok=False, order_id="", client_order_id=client_order_id or "",
                ticker=ticker, side=side, contracts=0,
                yes_price_cents=0, actual_cost_usd=0.0,
                status="halted", error=f"kill_switch_halted:{_halt}",
            )
        # W87.2/GG-1082: the exposure gate (open + realized + settled-unresolved stake, per book and
        # system-wide). Log mode records the would-halt and places; enforce mode refuses.
        from prediction_market_bot.c4_risk_engine import exposure_gate as _xg
        _xg_halt = _xg.gate_for_order(band)
        if _xg_halt:
            logger.warning("submit_order REFUSED (exposure gate): %s ticker=%s band=%s", _xg_halt, ticker, band)
            return KalshiOrder(
                ok=False, order_id="", client_order_id=client_order_id or "",
                ticker=ticker, side=side, contracts=0,
                yes_price_cents=0, actual_cost_usd=0.0,
                status="halted", error=f"exposure_gate_halted:{_xg_halt}",
            )

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

        # GG-063/T-217: /portfolio/orders (v1) is hard-deprecated by Kalshi —
        # every MLB order hit HTTP 410 "deprecated_v1_order_endpoint". Migrated
        # to /portfolio/events/orders (v2), which collapses yes/no + buy/sell
        # into a single book_side (bid=buy-yes, ask=buy-no) per Kalshi's
        # published legacy->v2 mapping (docs.kalshi.com/getting_started/order_direction),
        # and represents count/price as fixed-point decimal strings, not ints.
        body: dict[str, Any] = {
            "ticker": ticker,
            "client_order_id": client_order_id,
            "side": "bid" if side == "yes" else "ask",
            "count": f"{contracts}.00",
            "price": f"{price_cents / 100.0:.2f}",
            "time_in_force": "good_till_canceled",
            "self_trade_prevention_type": "taker_at_cross",
        }

        ok, data = self._post("/portfolio/events/orders", body)

        if not ok:
            # GG-063/T-217: _post() captures the real Kalshi response body under
            # "body" (HTTP error) or "detail" (exception), but data.get("error", data)
            # alone discarded it — every MLB order failure surfaced as a bare
            # "HTTP 410" with no indication of *why* Kalshi rejected the order.
            error_msg = str(data.get("error", data))
            error_detail = data.get("body") or data.get("detail")
            if error_detail:
                error_msg = f"{error_msg}: {error_detail}"
            return KalshiOrder(
                ok=False, order_id="", client_order_id=client_order_id,
                ticker=ticker, side=side, contracts=contracts,
                yes_price_cents=price_cents, actual_cost_usd=actual_cost,
                status="error", error=error_msg,
            )

        order_data = data.get("order", data)
        returned_order_id = order_data.get("order_id", "")

        # GG-303/T-576: an HTTP 200/201 response alone is not acknowledgement.
        # A response body with no resolvable order_id must not be treated as a
        # confirmed order -- refuse the write rather than persist a fabricated id.
        if not returned_order_id:
            return KalshiOrder(
                ok=False, order_id="", client_order_id=client_order_id,
                ticker=ticker, side=side, contracts=contracts,
                yes_price_cents=price_cents, actual_cost_usd=actual_cost,
                status="error",
                error=(
                    "Kalshi returned HTTP success with no order_id in the "
                    f"response body -- not acknowledged as a real order (raw: {data!r})"
                ),
            )

        return KalshiOrder(
            ok=True,
            order_id=returned_order_id,
            client_order_id=client_order_id,
            ticker=ticker,
            side=side,
            contracts=contracts,
            yes_price_cents=price_cents,
            actual_cost_usd=actual_cost,
            status=order_data.get("status", "submitted"),
        )


    # ------------------------------------------------------------------
    # W64.2: book read + order cancel (used only by the OFF-by-default
    # demo_fill_policy; nothing here is called unless that switch is ON)
    # ------------------------------------------------------------------

    def get_market_book(self, ticker: str) -> tuple[bool, dict[str, float]]:
        """Top-of-book YES bid/ask in dollars for one market (read-only GET).

        Returns (ok, {"yes_bid": float, "yes_ask": float}); 0.0 means that side is empty."""
        ok, data = self._get(f"/markets/{ticker}")
        if not ok:
            return False, {}
        raw = data.get("market", data)
        try:
            bid = float(raw.get("yes_bid_dollars") or raw.get("yes_bid") or 0)
            ask = float(raw.get("yes_ask_dollars") or raw.get("yes_ask") or 0)
        except (TypeError, ValueError):
            return False, {}
        if bid > 1.0 or ask > 1.0:  # legacy cent-denominated fields
            bid, ask = bid / 100.0, ask / 100.0
        return True, {"yes_bid": bid, "yes_ask": ask}

    def is_listed_on_demo(self, ticker: str) -> bool | None:
        """W67.2/GG-564: is this ticker listed on the venue orders are routed to (demo under
        BOT_ENV=paper)? Signed GET against the ORDER base URL, not the production price-discovery
        URL ``get_market_book`` reads. True = 200; False = HTTP 404 (the demo venue lists only a
        subset of production tickers, so an order here would 404); None = unknown (any other
        failure) -- the caller must not treat unknown as listed."""
        ok, data = self._get(f"/markets/{ticker}", authenticated=True)
        if ok:
            return True
        if isinstance(data, dict) and data.get("error") == "HTTP 404":
            return False
        return None

    def _delete(self, path: str, params: dict[str, Any] | None = None) -> tuple[bool, Any]:
        """Signed DELETE, single attempt (a cancel must not silently retry-loop)."""
        if not self._private_key:
            return False, {"error": "RSA private key not loaded"}
        refusal = _order_write_host_refusal()
        if refusal:
            return False, {"error": "host_refused", "detail": refusal}
        url = f"{_kalshi_base_url()}{path}"
        full_path = f"/trade-api/v2{path}"
        try:
            headers = _auth_headers(self._key_id, self._private_key, "DELETE", full_path)
            r = self._session.delete(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT_S)
            if r.status_code in (200, 201, 204):
                return True, (r.json() if r.content else {})
            return False, {"error": f"HTTP {r.status_code}", "body": r.text[:300]}
        except Exception as e:
            return False, {"error": type(e).__name__, "detail": str(e)}

    def cancel_order(self, order_id: str, market_ticker: str | None = None) -> tuple[bool, dict[str, Any]]:
        """Cancel a resting order (DELETE /portfolio/events/orders/{id}).

        GG-623/W71.1: Kalshi shards orders by exchange_index. Without `exchange_index` or
        `market_ticker` the DELETE defaults to shard 0, so an order on another shard answers
        HTTP 404 not_found while the order is plainly resting (every MLB-family demo order sits on
        shard 3; NFL/NHL on 0). `market_ticker` makes the exchange auto-route to the right shard.
        The query string is not part of the signed path."""
        params = {"market_ticker": market_ticker} if market_ticker else None
        return self._delete(f"/portfolio/events/orders/{order_id}", params=params)

    def get_order(self, order_id: str) -> tuple[bool, Any]:
        """Authenticated GET of one order (status / fill counts)."""
        return self._get(f"/portfolio/orders/{order_id}", authenticated=True)


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

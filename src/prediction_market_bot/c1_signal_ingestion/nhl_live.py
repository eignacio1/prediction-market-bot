"""C1 -- NHL live game-state feed (W129.7, BREADTH: NHL in-play cells).

Source: the NHL's free public API (``api-web.nhle.com/v1``): ``/score/now`` lists today's games and
``/gamecenter/<id>/play-by-play`` carries the point-in-time state of one game (score, period, clock, strength,
shots, penalty timer). Read-only, no credentials, <=1 req/s throttle shared with ``nhl_ingest``.

DATA RULE: NHL domains carry Content-Signal ai-train=no. This module FETCHES data and trains nothing on it.

Every state carries ``fetched_at_utc`` and the measured HTTP ``latency_ms`` so feed lag is audited, not assumed
(ADR-0068). Pure functions (``state_from_pbp``, ``staleness``, ``write_recency``) take dicts / values so tests
need no network. No order or position code is imported here.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from prediction_market_bot.c1_signal_ingestion.nhl_event_store import mmss, parse_situation
from prediction_market_bot.c1_signal_ingestion.nhl_ingest import BASE, Throttle, http_get_json
from prediction_market_bot.quant.inplay_nhl import classify_state

LIVE_STATES = ("LIVE", "CRIT")  # NHL gameState values while play is on (CRIT = last minutes)
STALE_FETCH_S = 45.0       # a fetched state older than this when priced is stale
STALE_CLOCK_S = 90.0       # running clock that has not advanced for this long = frozen feed
WRITE_RECENCY_S = 600.0    # a live game with no row written for this long = FAIL


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def state_from_pbp(payload: dict, fetched_at: datetime, latency_ms: Optional[float] = None) -> dict:
    """Point-in-time game state from one play-by-play payload.

    Strength comes from the top-level ``situation`` (current, includes the penalty timer) and falls back to the
    last play's ``situationCode``. ``minutes_left_reg`` is regulation minutes remaining (0 in OT/SO).
    """
    per = payload.get("periodDescriptor") or {}
    clock = payload.get("clock") or {}
    sit = payload.get("situation") or {}
    plays = payload.get("plays") or []
    home, away = payload.get("homeTeam") or {}, payload.get("awayTeam") or {}
    code = sit.get("situationCode") or (plays[-1].get("situationCode") if plays else None)
    sk = parse_situation(code)
    period = per.get("number")
    ptype = per.get("periodType")
    secs = clock.get("secondsRemaining")
    if secs is None:
        secs = mmss(clock.get("timeRemaining"))
    n_reg = per.get("maxRegulationPeriods") or payload.get("regPeriods") or 3
    if ptype == "REG" and isinstance(period, int) and secs is not None:
        minutes_left = ((n_reg - period) * 20 * 60 + secs) / 60.0
    else:
        minutes_left = 0.0 if ptype in ("OT", "SO") else None
    have_sk = None not in sk.values()
    strength = (classify_state(sk["home_skaters"], sk["away_skaters"], sk["home_goalie"], sk["away_goalie"])
                if have_sk else None)
    return {
        "game_id": payload.get("id"),
        "game_state": payload.get("gameState"),
        "start_time_utc": payload.get("startTimeUTC"),
        "home": home.get("abbrev"), "away": away.get("abbrev"),
        "score_h": home.get("score"), "score_a": away.get("score"),
        "sog_h": home.get("sog"), "sog_a": away.get("sog"),
        "period": period, "period_type": ptype,
        "clock_s": secs, "clock_running": clock.get("running"), "in_intermission": clock.get("inIntermission"),
        "minutes_left_reg": minutes_left,
        "situation_code": code, "strength": strength,
        "home_skaters": sk["home_skaters"], "away_skaters": sk["away_skaters"],
        "home_goalie": sk["home_goalie"], "away_goalie": sk["away_goalie"],
        "empty_net": (None if strength is None else strength in ("H_EN", "A_EN")),
        "pp_secs_left": sit.get("secondsRemaining"),
        "last_event_id": plays[-1].get("eventId") if plays else None,
        "n_plays": len(plays),
        "fetched_at_utc": _iso(fetched_at), "latency_ms": latency_ms,
    }


def is_live(state: dict) -> bool:
    return state.get("game_state") in LIVE_STATES


def _timed(opener: Optional[Callable], box: dict) -> Callable:
    """Opener that records ONLY the request time (the throttle's sleep is not feed latency)."""
    import urllib.error
    import urllib.request

    def go(url: str) -> tuple[int, bytes]:
        t0 = time.monotonic()
        try:
            if opener is not None:
                return opener(url)
            req = urllib.request.Request(url, headers={"User-Agent": "pmbot-nhl-shadow/1"})
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read() or b""
        finally:
            box["ms"] = (time.monotonic() - t0) * 1000.0
    return go


def fetch_state(game_id: int, throttle: Throttle, opener: Optional[Callable] = None,
                clock: Callable[[], datetime] = utcnow) -> dict:
    """GET play-by-play for ``game_id``; returns the state with the measured request latency (ms, request only).
    NOTE the feed's ``clock`` is a snapshot refreshed at events: while ``running`` it does NOT tick between
    refreshes, so ``minutes_left_reg`` can lag the true clock by the refresh gap (measured by the probe)."""
    box: dict = {}
    payload = http_get_json(f"{BASE}/gamecenter/{game_id}/play-by-play", throttle, opener=_timed(opener, box))
    return state_from_pbp(payload, clock(), box.get("ms"))


def list_live_game_ids(throttle: Throttle, opener: Optional[Callable] = None) -> list[int]:
    """Game ids whose ``gameState`` is live per ``/score/now``."""
    sc = http_get_json(f"{BASE}/score/now", throttle, opener=opener)
    return [int(g["id"]) for g in sc.get("games", []) if g.get("gameState") in LIVE_STATES]


def staleness(state: dict, prev: Optional[dict], now: datetime,
              fetch_s: float = STALE_FETCH_S, clock_s: float = STALE_CLOCK_S) -> Optional[str]:
    """Reason a state must not be priced, else None. Mirrors the MLB live loop's staleness / contamination rule
    (GG-085: never price on a state older than the move it should lead; GG-163: a feed that answers 200 proves
    nothing about whether it advances)."""
    fetched = datetime.fromisoformat(state["fetched_at_utc"])
    if (now - fetched).total_seconds() > fetch_s:
        return "fetch_age"
    if not is_live(state):
        return "not_live"
    if state.get("minutes_left_reg") is None or state.get("strength") is None:
        return "incomplete_state"
    if state.get("score_h") is None or state.get("score_a") is None:
        return "no_score"
    if prev is not None and prev.get("game_id") == state.get("game_id") and state.get("clock_running"):
        same = (prev.get("period"), prev.get("clock_s")) == (state.get("period"), state.get("clock_s"))
        dt = (fetched - datetime.fromisoformat(prev["fetched_at_utc"])).total_seconds()
        if same and prev.get("clock_running") and dt >= clock_s:
            return "clock_frozen"
        if (state.get("period"), -(state.get("clock_s") or 0)) < (prev.get("period"), -(prev.get("clock_s") or 0)):
            return "state_regressed"  # earlier game time than an already-seen state: a cached / out-of-order read
    return None


def write_recency(live_game_ids: list[int], last_row_utc: Optional[datetime], now: datetime,
                  max_age_s: float = WRITE_RECENCY_S) -> tuple[str, str]:
    """('OK'|'FAIL'|'IDLE', detail). A live game with no row written within ``max_age_s`` is FAIL (GG-163)."""
    if not live_game_ids:
        return "IDLE", "no live games"
    if last_row_utc is None:
        return "FAIL", f"{len(live_game_ids)} live game(s), no row ever written"
    age = (now - last_row_utc).total_seconds()
    if age > max_age_s:
        return "FAIL", f"{len(live_game_ids)} live game(s), last row {age:.0f}s ago (> {max_age_s:.0f}s)"
    return "OK", f"{len(live_game_ids)} live game(s), last row {age:.0f}s ago"

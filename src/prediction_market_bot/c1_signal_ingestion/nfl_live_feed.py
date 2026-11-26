"""
NFL live game-state feed (W129.6, ADR-0068): point-in-time state per play from ESPN's free core API.

Source: ``sports.core.api.espn.com/v2/.../events/{id}/competitions/{id}/plays`` (every play carries score, period,
clock in seconds, down / distance / yard line, the possessing team, and ``wallclock`` UTC real time) plus the site
scoreboard for which games are live. Same host family and the same empty-headers convention as
``nfl_espn_results.py`` (GG-163: a browser-spoofed User-Agent draws a 403; send none, never get past a bot check).

Latency is MEASURED, never assumed (ADR-0068): every state row carries ``fetch_time_utc`` and the play's own
``wallclock``; ``feed_lag_s = fetch_time - wallclock``. A live lag exists only once a game is live; a replay of a
finished game has ``feed_lag_s = None`` by construction.

Staleness (GG-085 / GG-163 shape, as in ``run_t4_mlb_live.LiveDataFreshnessGuard``): a state is stale when the newest
play is older than ``STALE_AFTER_S`` while ESPN still reports the game in progress, or the fetch itself is older
than ``FETCH_FRESH_S``. A stale or failed fetch is a FAIL the caller must log, never a silent skip.

Timeouts: the core ``/situation`` endpoint has them live; a recorded game does not, so ``derive_timeouts`` counts the
"Timeout #n by XXX" plays per half (3 per half, 2 in overtime). Both paths set ``timeouts_source``.
"""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

import requests

__all__ = ["PlayState", "fetch_plays", "fetch_live_event_ids", "states_from_plays", "derive_timeouts",
           "is_stale", "STALE_AFTER_S", "FETCH_FRESH_S"]

_CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{eid}/competitions/{eid}/plays"
_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
_HEADERS: dict[str, str] = {}      # GG-163: no User-Agent override
_TIMEOUT_S = 15
_RETRY_DELAYS_S: tuple[int, ...] = (5, 10, 30)
STALE_AFTER_S = 300.0              # a live game with no new play for 5 min (a long TV timeout / review is ~3-4 min)
FETCH_FRESH_S = 90.0               # same 2 x 45 s window as the MLB freshness guard
_ABBR_ALIAS = {"ARZ": "ARI", "WSH": "WAS", "LAR": "LA", "JAC": "JAX"}
_TO_RE = re.compile(r"Timeout #(\d) by ([A-Z]{2,3})")


@dataclass(frozen=True)
class PlayState:
    """State AFTER the play (score) and the situation going INTO the next snap (down/dist/yard line)."""
    event_id: str
    play_id: str
    seq: int
    play_type: str
    period: int
    clock_s: float                 # seconds left in the period
    secs_left_reg: float           # seconds left in regulation (0 in overtime)
    home_score: int
    away_score: int
    down: int
    distance: int
    yards_to_endzone: Optional[int]
    possession: str                # "home" | "away" | ""
    home_timeouts: int
    away_timeouts: int
    timeouts_source: str
    scoring_play: bool
    wallclock_utc: Optional[str]   # ESPN's own real-time stamp of the play
    fetch_time_utc: str            # when WE read it
    feed_lag_s: Optional[float]    # fetch_time - wallclock; None for a replay or a missing stamp

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get(url: str, params: Optional[dict] = None, delays: tuple[int, ...] = _RETRY_DELAYS_S) -> tuple[Any, Optional[str]]:
    last: Optional[str] = None
    for delay in (*delays, None):
        try:
            r = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT_S)
            r.raise_for_status()
            return r.json(), None
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            last = f"{type(exc).__name__}: {exc}"
            if delay is None:
                break
            time.sleep(delay)
    return None, last


def fetch_live_event_ids(date_yyyymmdd: Optional[str] = None) -> tuple[list[str], Optional[str]]:
    """Event ids ESPN reports STATUS_IN_PROGRESS right now. (ids, error)."""
    params = {"dates": date_yyyymmdd} if date_yyyymmdd else None
    js, err = _get(_SCOREBOARD, params)
    if js is None:
        return [], err
    out = [e["id"] for e in js.get("events", [])
           if (e.get("status", {}).get("type", {}).get("name") == "STATUS_IN_PROGRESS")]
    return out, None


def fetch_plays(event_id: str, limit: int = 500) -> tuple[list[dict], Optional[str], str]:
    """Raw play dicts + error + fetch_time_utc (taken right after the response lands)."""
    js, err = _get(_CORE.format(eid=event_id), {"limit": limit})
    ft = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if js is None:
        return [], err, ft
    return js.get("items", []), None, ft


def _tid(ref: Optional[str]) -> str:
    return (ref or "").split("/teams/")[-1].split("?")[0]


def normalise(play: dict) -> dict:
    """Raw ESPN play -> the flat fields this module uses (also the fixture shape)."""
    if "type" in play and isinstance(play["type"], dict):
        s = play.get("start") or {}
        return {"id": play["id"], "seq": int(play["sequenceNumber"]), "type": play["type"]["text"],
                "text": play.get("text", ""), "awayScore": play["awayScore"], "homeScore": play["homeScore"],
                "period": play["period"]["number"], "clock": play["clock"]["value"],
                "wallclock": play.get("wallclock"), "scoringPlay": play.get("scoringPlay", False),
                "start": {k: s.get(k) for k in ("down", "distance", "yardLine", "yardsToEndzone")},
                "start_team": _tid((s.get("team") or {}).get("$ref")),
                "team": _tid((play.get("team") or {}).get("$ref"))}
    return play


def derive_timeouts(plays: Iterable[dict], home_abbr: str, away_abbr: str) -> list[tuple[int, int]]:
    """(home, away) timeouts remaining AFTER each play, counted from "Timeout #n by XXX" plays; resets each half."""
    home_abbr, away_abbr = (_ABBR_ALIAS.get(home_abbr, home_abbr), _ABBR_ALIAS.get(away_abbr, away_abbr))
    used = {"home": 0, "away": 0}
    half = 1
    out: list[tuple[int, int]] = []
    for p in plays:
        h = 1 if p["period"] <= 2 else (2 if p["period"] <= 4 else 3)
        if h != half:
            half, used = h, {"home": 0, "away": 0}
        m = _TO_RE.search(p.get("text", "")) if p["type"] == "Timeout" else None
        if m:
            ab = _ABBR_ALIAS.get(m.group(2), m.group(2))
            if ab == home_abbr:
                used["home"] += 1
            elif ab == away_abbr:
                used["away"] += 1
        cap = 2 if half == 3 else 3
        out.append((max(cap - used["home"], 0), max(cap - used["away"], 0)))
    return out


def states_from_plays(raw: list[dict], event_id: str, home_id: str, home_abbr: str, away_abbr: str,
                      fetch_time_utc: str, replay: bool = False) -> list[PlayState]:
    """One PlayState per play, point-in-time: only that play and earlier plays feed it."""
    # ESPN's sequenceNumber is NOT chronological (seen on a saved game); game order is (period, clock desc), stable
    plays = sorted((normalise(p) for p in raw), key=lambda p: (int(p["period"]), -float(p["clock"])))
    tos = derive_timeouts(plays, home_abbr, away_abbr)
    ft = datetime.strptime(fetch_time_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    out: list[PlayState] = []
    for p, (hto, ato) in zip(plays, tos):
        per = int(p["period"])
        clock = float(p["clock"])
        reg_left = max(0.0, (4 - per) * 900.0 + clock) if per <= 4 else 0.0
        st = p.get("start") or {}
        poss = p.get("start_team") or p.get("team") or ""
        side = "" if not poss else ("home" if poss == home_id else "away")
        lag: Optional[float] = None
        if not replay and p.get("wallclock"):
            wc = datetime.strptime(p["wallclock"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            lag = (ft - wc).total_seconds()
        out.append(PlayState(
            event_id=event_id, play_id=str(p["id"]), seq=int(p["seq"]), play_type=p["type"], period=per,
            clock_s=clock, secs_left_reg=reg_left, home_score=int(p["homeScore"]), away_score=int(p["awayScore"]),
            down=int(st.get("down") or 0), distance=int(st.get("distance") or 0),
            yards_to_endzone=st.get("yardsToEndzone"), possession=side, home_timeouts=hto, away_timeouts=ato,
            timeouts_source="derived_from_timeout_plays", scoring_play=bool(p.get("scoringPlay")),
            wallclock_utc=p.get("wallclock"), fetch_time_utc=fetch_time_utc, feed_lag_s=lag))
    return out


def is_stale(states: list[PlayState], now: datetime, espn_status_in_progress: bool) -> Optional[str]:
    """None if fresh; else the reason. A live game whose newest play is old, or a fetch that is old, is stale."""
    if not states:
        return "no_plays" if espn_status_in_progress else None
    last = states[-1]
    ft = datetime.strptime(last.fetch_time_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if (now - ft).total_seconds() > FETCH_FRESH_S:
        return "fetch_old"
    if espn_status_in_progress and last.wallclock_utc:
        wc = datetime.strptime(last.wallclock_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if (now - wc).total_seconds() > STALE_AFTER_S:
            return "newest_play_old"
    return None

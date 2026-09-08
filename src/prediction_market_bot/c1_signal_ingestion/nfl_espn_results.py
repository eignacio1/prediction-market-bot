"""
NFL final-score result fetcher via ESPN's public site API (T-527, GG-254 follow-on).

Modeled on run_resolve_mlb.py's ESPN-fallback pattern (`_espn_game_ids_for_date` /
`_espn_fetch_hits`, GG-084/T-241) -- NOT on `ds02_nba_live.py`, which consumes the
NBA Stats API (a different upstream entirely), despite
`04_EXECUTION/NFL_PREGAME_MONEYLINE_READINESS_AUDIT_2026-09-07.md` (GG-254)
pointing there. Same base host (`site.api.espn.com`), same empty-headers
convention (GG-163: a browser-spoofed User-Agent draws a 403 from ESPN;
sending none lets `requests`' own default UA through, which is not blocked),
same terminal-status gating (STATUS_FINAL/STATUS_POSTPONED), same T-207
retry/backoff schedule.

Unlike MLB's player-level box score lookup, NFL game markets only need each
team's final score, and ESPN's scoreboard endpoint already returns that
directly per competitor -- no separate summary/boxscore call is needed for
this use case. ESPN's team abbreviations were confirmed identical to
Kalshi's own team-code alphabet for every code cross-checked in T-527 (PIT,
MIN, TEN, DAL, CHI, PHI, IND, NO, HOU, GB, ...) -- no mapping table needed.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests

__all__ = ["NFLGameResult", "fetch_nfl_final_score"]

_ESPN_NFL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
_ESPN_HEADERS: dict[str, str] = {}
_ESPN_STATUS_FINAL = "STATUS_FINAL"
_ESPN_STATUS_POSTPONED = "STATUS_POSTPONED"
_ESPN_TERMINAL_STATUSES = (_ESPN_STATUS_FINAL, _ESPN_STATUS_POSTPONED)
_REQUEST_TIMEOUT_S = 15
_RETRY_DELAYS_S: tuple[int, ...] = (5, 10, 30)  # T-207: exponential backoff


@dataclass(frozen=True)
class NFLGameResult:
    """A confirmed-final NFL game score, ready for game_market_settlement.py."""

    home_team_code: str
    away_team_code: str
    home_score: float
    away_score: float
    status: str


def _espn_scoreboard_events(
    game_date: str,
    *,
    delays: tuple[int, ...] = _RETRY_DELAYS_S,
) -> list[dict]:
    """Fetch raw ESPN scoreboard events for game_date (YYYY-MM-DD).

    Retries per _RETRY_DELAYS_S (T-207), then gives up and returns [] --
    identical shape to run_resolve_mlb.py's _espn_game_ids_for_date, except
    this returns the full event dicts (NFL needs each competitor's score,
    not just the game id MLB's per-player lookup needs).
    """
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y%m%d")
    params: dict[str, str | int] = {"dates": date_str, "limit": 30}
    for attempt, delay in enumerate((*delays, None), start=1):
        try:
            resp = requests.get(
                _ESPN_NFL_SCOREBOARD,
                params=params,
                headers=_ESPN_HEADERS,
                timeout=_REQUEST_TIMEOUT_S,
            )
            resp.raise_for_status()
            return resp.json().get("events", [])
        except Exception as exc:
            if delay is None:
                print(
                    f"  [ESPN-NFL] game_date={game_date} "
                    f"attempt={attempt}/{len(delays) + 1}: "
                    f"{type(exc).__name__}: {exc} -- giving up",
                    file=sys.stderr,
                )
            else:
                print(
                    f"  [ESPN-NFL] game_date={game_date} "
                    f"attempt={attempt}/{len(delays) + 1}: "
                    f"{type(exc).__name__}: {exc} -- retrying in {delay}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
    return []


def fetch_nfl_final_score(
    game_date: str,
    home_team_code: str,
    away_team_code: str,
) -> Optional[NFLGameResult]:
    """Fetch the final score for one NFL game from ESPN's scoreboard.

    game_date: YYYY-MM-DD. home_team_code/away_team_code: Kalshi's team-code
    alphabet, matched case-insensitively against ESPN's own abbreviations.

    Returns None if: the game isn't found on that date, its status hasn't
    reached a terminal state, it reached STATUS_POSTPONED (terminal, but no
    score exists to report), or the API call fails after retries. A live or
    scheduled game's in-progress score is never returned as if it were
    final -- callers must be able to treat None as "not resolvable yet"
    without a second check.
    """
    home_up = home_team_code.upper()
    away_up = away_team_code.upper()

    for event in _espn_scoreboard_events(game_date):
        competitions = event.get("competitions", [])
        if not competitions:
            continue
        comp = competitions[0]
        competitors = comp.get("competitors", [])
        codes = {
            c.get("homeAway"): c.get("team", {}).get("abbreviation", "").upper()
            for c in competitors
        }
        if codes.get("home") != home_up or codes.get("away") != away_up:
            continue

        status_name = comp.get("status", {}).get("type", {}).get("name", "")
        if status_name not in _ESPN_TERMINAL_STATUSES:
            return None  # still live or scheduled -- not resolvable yet
        if status_name != _ESPN_STATUS_FINAL:
            return None  # STATUS_POSTPONED: terminal, but no score to report

        scores = {c.get("homeAway"): c.get("score") for c in competitors}
        try:
            home_score = float(scores["home"])
            away_score = float(scores["away"])
        except (KeyError, TypeError, ValueError):
            return None

        return NFLGameResult(
            home_team_code=home_up,
            away_team_code=away_up,
            home_score=home_score,
            away_score=away_score,
            status=status_name,
        )

    return None

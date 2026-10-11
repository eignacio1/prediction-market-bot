"""NBA player-points PregameForecaster (EXP-039): KXNBAPTS ticker -> player + game -> feature row -> one NB
distribution -> p_yes for 'player scores >= n points'. Players are resolved by name across ALL teams (stars
change teams in the offseason; the ticker carries the CURRENT team), with jersey and last-seen team as
tie-breakers. An ambiguous or unknown player yields no forecast -- never a guess."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from prediction_market_bot.c1_signal_ingestion.nba_player_features import PlayerFeatureBuilder
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.nba_forecaster import (
    _MON, KALSHI_CODES, NBAScheduleIndex)
from prediction_market_bot.pregame_shadow.nba_player_points_model import NBAPlayerPointsModel

MARKET_TYPE = "NBA_PLAYER_POINTS"
SERIES = "KXNBAPTS"
_EVENT = re.compile(r"^KXNBAPTS-(\d{2})([A-Z]{3})(\d{2})([A-Z]{6})$")
_PLAYER = re.compile(r"^([A-Z]{3})([A-Z])([A-Z]+?)(\d{1,2})$")
_SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}


def parse_event_ticker(event_ticker: str) -> Optional[tuple[str, str, str]]:
    """-> (ET game date ISO, away, home) or None."""
    m = _EVENT.match(event_ticker)
    if not m or m.group(2) not in _MON:
        return None
    a, h = m.group(4)[:3], m.group(4)[3:]
    if a not in KALSHI_CODES or h not in KALSHI_CODES:
        return None
    return f"20{m.group(1)}-{_MON[m.group(2)]:02d}-{m.group(3)}", a, h


def parse_market_ticker(market_ticker: str) -> Optional[dict]:
    """KXNBAPTS-26OCT08BOSCLE-BOSPGEORGE13-25 -> player 'P GEORGE' #13 on BOS, strike 24.5 (>= 25 points)."""
    parts = market_ticker.split("-")
    if len(parts) != 4 or not parts[3].isdigit():
        return None
    event = "-".join(parts[:2])
    ev = parse_event_ticker(event)
    pm = _PLAYER.match(parts[2])
    if ev is None or pm is None or pm.group(1) not in KALSHI_CODES:
        return None
    date, away, home = ev
    team = pm.group(1)
    if team not in (away, home):
        return None
    n = int(parts[3])
    return {"event_ticker": event, "market_type": MARKET_TYPE, "game_date": date, "away": away, "home": home,
            "team": team, "initial": pm.group(2), "surname": pm.group(3), "jersey": pm.group(4),
            "points_threshold": n, "strike": n - 0.5}


def _norm_surname(name: str) -> str:
    toks = [t for t in re.split(r"\s+", name.strip()) if t]
    toks = [t for t in toks[1:] if re.sub(r"[^A-Za-z]", "", t).upper() not in _SUFFIXES] or toks[-1:]
    return re.sub(r"[^A-Z]", "", " ".join(toks).upper())


def _initial(name: str) -> str:
    return re.sub(r"[^A-Z]", "", name.strip().upper())[:1]


class NBAPlayerResolver:
    def __init__(self, roster: dict[str, list[dict[str, Any]]]) -> None:
        self._by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for team, players in roster.items():
            for p in players:
                self._by_key.setdefault((_initial(p["name"]), _norm_surname(p["name"])), []).append(
                    {**p, "team": team})

    def resolve(self, parsed: dict) -> Optional[str]:
        """-> player_id, or None when unknown / ambiguous."""
        cands = self._by_key.get((parsed["initial"], parsed["surname"]), [])
        if not cands:
            return None
        ids = {c["player_id"] for c in cands}
        if len(ids) == 1:
            return next(iter(ids))
        for narrow in (lambda c: c["jersey"] == parsed["jersey"] and c["team"] == parsed["team"],
                       lambda c: c["team"] == parsed["team"], lambda c: c["jersey"] == parsed["jersey"]):
            hit = {c["player_id"] for c in cands if narrow(c)}
            if len(hit) == 1:
                return next(iter(hit))
        return None


class NBAPlayerPointsForecaster:
    sport = "NBA"

    def __init__(self, model: NBAPlayerPointsModel, builder: PlayerFeatureBuilder, schedule: NBAScheduleIndex,
                 season_for: Any) -> None:
        self.model, self.builder, self.schedule = model, builder, schedule
        self.resolver = NBAPlayerResolver(builder.roster)
        self._season_for = season_for       # callable(game dict) -> season (ending year)

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None:
            return None
        g = self.schedule.game(p["game_date"], p["home"], p["away"])
        if g is None:
            return None
        pid = self.resolver.resolve(p)
        if pid is None:
            return None
        opp = p["away"] if p["team"] == p["home"] else p["home"]
        row = self.builder.row(pid, p["team"], opp, p["team"] == g["home"], self._season_for(g),
                               g["tip_utc"], as_of_utc)
        if row is None:
            return None
        p_yes = min(max(self.model.p_at_least(row["features"], p["points_threshold"]), 1e-4), 1 - 1e-4)
        return PregameForecast("NBA", MARKET_TYPE, p["event_ticker"], market_ticker, p_yes, as_of_utc,
                               self.model.model_id, self.model.sha256, row["sha256"])


def kickoff_for_event(schedule: NBAScheduleIndex, event_ticker: str):
    ev = parse_event_ticker(event_ticker)
    g = schedule.game(ev[0], ev[1], ev[2]) if ev else None
    return (g["tip_utc"], "espn_scoreboard_start_time") if g else None

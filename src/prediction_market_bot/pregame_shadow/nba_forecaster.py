"""NBA PregameForecaster (EXP-038): ticker -> game -> feature row -> one distribution -> p_yes."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from prediction_market_bot.c1_signal_ingestion.nba_ingest import KALSHI_TEAMS
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import NBAFeatureBuilder, _dt, et_date
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.nba_model import NBAPregameModel, p_yes_for

KALSHI_CODES = set(KALSHI_TEAMS)
_MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
_EVENT = re.compile(r"^(KXNBA[A-Z]+)-(\d{2})([A-Z]{3})(\d{2})([A-Z]{6})$")
_SUFFIX = re.compile(r"^([A-Z]{3})?(\d+)$")
_SERIES_TO_TYPE = {"KXNBAGAME": "NBA_MONEYLINE", "KXNBASPREAD": "NBA_SPREAD",
                   "KXNBATOTAL": "NBA_GAME_TOTAL", "KXNBATEAMTOTAL": "NBA_TEAM_TOTAL"}


def parse_event_ticker(event_ticker: str) -> Optional[tuple[str, str, str, str]]:
    """-> (market_type_name, ET game date ISO, away, home) or None."""
    m = _EVENT.match(event_ticker)
    if not m or m.group(1) not in _SERIES_TO_TYPE or m.group(3) not in _MON:
        return None
    a, h = m.group(5)[:3], m.group(5)[3:]
    if a not in KALSHI_CODES or h not in KALSHI_CODES:
        return None
    return _SERIES_TO_TYPE[m.group(1)], f"20{m.group(2)}-{_MON[m.group(3)]:02d}-{m.group(4)}", a, h


def parse_market_ticker(market_ticker: str) -> Optional[dict]:
    """Strike = n - 0.5 for spread / total / team total."""
    if "-" not in market_ticker:
        return None
    event, suffix = market_ticker.rsplit("-", 1)
    ev = parse_event_ticker(event)
    if ev is None:
        return None
    mt, date, away, home = ev
    out = {"event_ticker": event, "market_type": mt, "game_date": date, "away": away, "home": home,
           "subject": None, "strike": None}
    if mt == "NBA_MONEYLINE":
        if suffix not in KALSHI_CODES:
            return None
        out["subject"] = suffix
        return out
    m = _SUFFIX.match(suffix)
    if not m:
        return None
    team, n = m.group(1), int(m.group(2))
    out["strike"] = n - 0.5
    if mt != "NBA_GAME_TOTAL":
        if team not in KALSHI_CODES:
            return None
        out["subject"] = team
    return out


class NBAScheduleIndex:
    """(ET game date, {home, away}) -> game dict with UTC tip-off (ESPN schedule; Kalshi lists no start time)."""

    def __init__(self, games: list[dict[str, Any]], season_types: tuple[int, ...] = (2,)) -> None:
        # default = regular season only (judged evidence); (1,) = preseason smoke-test index (W59.3)
        self._g: dict[tuple[str, frozenset], dict] = {}
        for g in games:
            if g["season_type"] not in season_types:
                continue
            start = _dt(g["start_time_utc"])
            self._g[(et_date(start).isoformat(), frozenset((g["home"], g["away"])))] = {
                **g, "tip_utc": start}

    def game(self, game_date: str, a: str, b: str) -> Optional[dict]:
        return self._g.get((game_date, frozenset((a, b))))

    def kickoff_for_event(self, event_ticker: str):
        ev = parse_event_ticker(event_ticker)
        g = self.game(ev[1], ev[2], ev[3]) if ev else None
        return (g["tip_utc"], "espn_scoreboard_start_time") if g else None


class NBAForecaster:
    sport = "NBA"

    def __init__(self, model: NBAPregameModel, builder: NBAFeatureBuilder, schedule: NBAScheduleIndex) -> None:
        self.model, self.builder, self.schedule = model, builder, schedule

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None:
            return None
        g = self.schedule.game(p["game_date"], p["home"], p["away"])
        if g is None:
            return None
        row = self.builder.row(g["home"], g["away"], g["tip_utc"], as_of_utc)
        if row is None:
            return None
        p_yes = p_yes_for(self.model, row["features"], p["market_type"],
                          subject_is_home=(p["subject"] == g["home"]) if p["subject"] else None,
                          strike=p["strike"])
        p_yes = min(max(p_yes, 1e-4), 1 - 1e-4)
        return PregameForecast("NBA", p["market_type"], p["event_ticker"], market_ticker, p_yes,
                               as_of_utc, self.model.model_id, self.model.sha256, row["sha256"])

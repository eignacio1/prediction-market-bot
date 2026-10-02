"""NFL PregameForecaster (EXP-037 / D3): ticker -> game -> feature row -> one distribution -> p_yes."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel, p_yes_for

KALSHI_TO_NFLVERSE = {"LAR": "LA", "JAC": "JAX"}  # Kalshi uses WAS for Washington (live 2026-10-02)
NFLVERSE_TEAMS = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND",
    "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF",
    "TB", "TEN", "WAS",
}
_REV = {v: k for k, v in KALSHI_TO_NFLVERSE.items()}
KALSHI_CODES = {_REV.get(t, t) for t in NFLVERSE_TEAMS}
_MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
_EVENT = re.compile(r"^(KXNFL[A-Z]+)-(\d{2})([A-Z]{3})(\d{2})([A-Z]+)$")
_SUFFIX = re.compile(r"^([A-Z]+?)?(\d+)$")
_SERIES_TO_TYPE = {"KXNFLGAME": "NFL_MONEYLINE", "KXNFLSPREAD": "NFL_SPREAD",
                   "KXNFLTOTAL": "NFL_GAME_TOTAL", "KXNFLTEAMTOTAL": "NFL_TEAM_TOTAL"}


def kalshi_to_nflverse(code: str) -> str:
    return KALSHI_TO_NFLVERSE.get(code, code)


def parse_event_ticker(event_ticker: str) -> Optional[tuple[str, str, str, str]]:
    """-> (market_type_name, game_date ISO, away_nflverse, home_nflverse) or None."""
    m = _EVENT.match(event_ticker)
    if not m or m.group(1) not in _SERIES_TO_TYPE or m.group(3) not in _MON:
        return None
    date = f"20{m.group(2)}-{_MON[m.group(3)]:02d}-{m.group(4)}"
    teams = m.group(5)
    for i in (2, 3):
        a, h = teams[:i], teams[i:]
        if a in KALSHI_CODES and h in KALSHI_CODES:
            return _SERIES_TO_TYPE[m.group(1)], date, kalshi_to_nflverse(a), kalshi_to_nflverse(h)
    return None


def parse_market_ticker(market_ticker: str) -> Optional[dict]:
    """Event + strike suffix. Strike = n - 0.5 for spread / total / team total (half-point lines)."""
    if "-" not in market_ticker:
        return None
    event, suffix = market_ticker.rsplit("-", 1)
    ev = parse_event_ticker(event)
    if ev is None:
        return None
    mt, date, away, home = ev
    out = {"event_ticker": event, "market_type": mt, "game_date": date, "away": away, "home": home,
           "subject": None, "strike": None}
    if mt == "NFL_MONEYLINE":
        if suffix not in KALSHI_CODES:
            return None
        out["subject"] = kalshi_to_nflverse(suffix)
        return out
    m = _SUFFIX.match(suffix)
    if not m:
        return None
    team, n = m.group(1), int(m.group(2))
    out["strike"] = n - 0.5
    if mt != "NFL_GAME_TOTAL":
        if team not in KALSHI_CODES:
            return None
        out["subject"] = kalshi_to_nflverse(team)
    return out


class NFLScheduleIndex:
    """(game_date, {home, away}) -> game row with UTC kickoff (nflverse gameday + gametime, US/Eastern)."""

    def __init__(self, schedule_df: pd.DataFrame) -> None:
        self._g: dict[tuple[str, frozenset], dict] = {}
        for r in schedule_df.itertuples():
            ko = None
            gt = getattr(r, "gametime", None)
            if isinstance(gt, str) and ":" in gt:
                hh, mm = gt.split(":")[:2]
                local = datetime.fromisoformat(str(r.gameday)).replace(
                    hour=int(hh), minute=int(mm), tzinfo=ZoneInfo("America/New_York"))
                ko = local.astimezone(timezone.utc)
            self._g[(str(r.gameday), frozenset((r.home_team, r.away_team)))] = {
                "home": r.home_team, "away": r.away_team, "kickoff_utc": ko,
                "home_rest": r.home_rest, "away_rest": r.away_rest}

    def game(self, game_date: str, a: str, b: str) -> Optional[dict]:
        return self._g.get((game_date, frozenset((a, b))))

    def kickoff_for_event(self, event_ticker: str):
        ev = parse_event_ticker(event_ticker)
        if ev is None:
            return None
        g = self.game(ev[1], ev[2], ev[3])
        if g is None or g["kickoff_utc"] is None:
            return None
        return g["kickoff_utc"], "nflverse_gameday_gametime_ET"


class NFLForecaster:
    sport = "NFL"

    def __init__(self, model: NFLPregameModel, builder: NFLPregameFeatureBuilder,
                 schedule: NFLScheduleIndex) -> None:
        self.model, self.builder, self.schedule = model, builder, schedule

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None:
            return None
        g = self.schedule.game(p["game_date"], p["home"], p["away"])
        if g is None:
            return None
        row = self.builder.row(g["home"], g["away"], as_of_utc, g["home_rest"], g["away_rest"])
        if row is None:
            return None
        p_yes = p_yes_for(self.model, row["features"], p["market_type"],
                          subject_is_home=(p["subject"] == g["home"]) if p["subject"] else None,
                          strike=p["strike"])
        p_yes = min(max(p_yes, 1e-4), 1 - 1e-4)
        return PregameForecast("NFL", p["market_type"], p["event_ticker"], market_ticker, p_yes,
                               as_of_utc, self.model.model_id, self.model.sha256, row["sha256"])

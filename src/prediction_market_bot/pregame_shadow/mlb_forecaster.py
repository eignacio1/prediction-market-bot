"""MLB PregameForecaster (EXP-037 / T-608): ticker -> game -> feature row -> one distribution -> p_yes.

Kalshi MLB event tail is ``YYMONDDHHMM`` + away+home codes, with HHMM the scheduled first pitch in US
Eastern time. The Stats API schedule snapshot supplies the probable starters; the confirmed starter is the
T1-vs-T3 difference (a starter not shown in the snapshot at as_of is simply unknown -> team fallback).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import (
    CANON, MLBGameFeatureBuilder, canon)
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.mlb_model import MLBPregameModel, p_yes_for

ET = ZoneInfo("America/New_York")
MLB_CODES = {"ATH", "ATL", "AZ", "BAL", "BOS", "CHC", "CIN", "CLE", "COL", "CWS", "DET", "HOU", "KC", "LAA",
             "LAD", "MIA", "MIL", "MIN", "NYM", "NYY", "PHI", "PIT", "SD", "SEA", "SF", "STL", "TB", "TEX",
             "TOR", "WSH"}
ALL_CODES = MLB_CODES | set(CANON)
_MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
_EVENT = re.compile(r"^(KXMLB[A-Z0-9]+)-(\d{2})([A-Z]{3})(\d{2})(\d{4})([A-Z]+)$")
_SUFFIX = re.compile(r"^([A-Z]+?)?(\d+)$")
SERIES_TO_TYPE = {"KXMLBGAME": "MLB_MONEYLINE", "KXMLBSPREAD": "MLB_RUN_LINE",
                  "KXMLBTOTAL": "MLB_GAME_TOTAL", "KXMLBTEAMTOTAL": "MLB_TEAM_TOTAL"}


def parse_event_ticker(event_ticker: str) -> Optional[dict]:
    m = _EVENT.match(event_ticker)
    if not m or m.group(1) not in SERIES_TO_TYPE or m.group(3) not in _MON:
        return None
    hh, mm = int(m.group(5)[:2]), int(m.group(5)[2:])
    if hh > 23 or mm > 59:
        return None
    local = datetime(2000 + int(m.group(2)), _MON[m.group(3)], int(m.group(4)), hh, mm, tzinfo=ET)
    teams = m.group(6)
    splits = [(teams[:i], teams[i:]) for i in (2, 3, 4) if teams[:i] in ALL_CODES and teams[i:] in ALL_CODES]
    if len(splits) != 1:           # none, or ambiguous: refuse rather than guess
        return None
    away, home = splits[0]
    return {"market_type": SERIES_TO_TYPE[m.group(1)], "start_utc": local.astimezone(timezone.utc),
            "away": canon(away), "home": canon(home)}


def parse_market_ticker(market_ticker: str) -> Optional[dict]:
    if "-" not in market_ticker:
        return None
    event, suffix = market_ticker.rsplit("-", 1)
    ev = parse_event_ticker(event)
    if ev is None:
        return None
    out = {"event_ticker": event, **ev, "subject": None, "strike": None}
    mt = ev["market_type"]
    if mt == "MLB_MONEYLINE":
        if suffix not in ALL_CODES:
            return None
        out["subject"] = canon(suffix)
    else:
        sm = _SUFFIX.match(suffix)
        if not sm:
            return None
        out["strike"] = int(sm.group(2)) - 0.5
        if mt == "MLB_GAME_TOTAL":
            if sm.group(1):
                return None
        else:
            if not sm.group(1) or sm.group(1) not in ALL_CODES:
                return None
            out["subject"] = canon(sm.group(1))
    if out["subject"] is not None and out["subject"] not in (ev["home"], ev["away"]):
        return None
    return out


class MLBScheduleIndex:
    """Stats API snapshot -> kickoff (UTC) and probable starters, matched on teams + start time."""
    TOL = timedelta(minutes=45)

    def __init__(self, games: pd.DataFrame) -> None:
        self.games = games[games.start_utc.notna()].copy()
        self.games["_h"] = self.games.home.map(canon)
        self.games["_a"] = self.games.away.map(canon)
        self.games["_t"] = pd.to_datetime(self.games.start_utc, utc=True)

    def game(self, home: str, away: str, start_utc: datetime) -> Optional[dict]:
        g = self.games[(self.games._h == home) & (self.games._a == away)]
        g = g[(g._t - pd.Timestamp(start_utc)).abs() <= self.TOL]
        if len(g) != 1:
            return None
        r = g.iloc[0]
        return {"start_utc": r._t.to_pydatetime(),
                "home_sp": None if pd.isna(r.home_sp) else int(r.home_sp),
                "away_sp": None if pd.isna(r.away_sp) else int(r.away_sp)}

    def kickoff_for_event(self, event_ticker: str) -> Optional[tuple[datetime, str]]:
        ev = parse_event_ticker(event_ticker)
        if ev is None:
            return None
        g = self.game(ev["home"], ev["away"], ev["start_utc"])
        return (g["start_utc"], "stats_api_schedule") if g else None


class MLBForecaster:
    sport = "MLB"

    def __init__(self, model: MLBPregameModel, builder: MLBGameFeatureBuilder, schedule: MLBScheduleIndex) -> None:
        self.model, self.builder, self.schedule = model, builder, schedule

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None:
            return None
        g = self.schedule.game(p["home"], p["away"], p["start_utc"])
        if g is None:
            return None
        row = self.builder.row(p["home"], p["away"], as_of_utc, g["home_sp"], g["away_sp"])
        if row is None:
            return None
        p_yes = p_yes_for(self.model, row["features"], p["market_type"],
                          subject_is_home=(p["subject"] == p["home"]) if p["subject"] else None,
                          strike=p["strike"])
        p_yes = min(max(p_yes, 1e-4), 1 - 1e-4)
        return PregameForecast(self.sport, p["market_type"], p["event_ticker"], market_ticker, p_yes,
                               as_of_utc, self.model.model_id, self.model.sha256, row["sha256"])

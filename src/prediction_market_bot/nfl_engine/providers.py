"""NFL providers for decision_trees.filter_supply.nfl_adapter (W113.2 Part A, B-089).

Reads committed snapshots (decision_trees/filter_data/): nfl_schedule.csv, nfl_team_games.csv, nfl_snapshot_meta.json.
  weather(row) -> (WeatherContext, issued_utc)   live Open-Meteo forecast (cached, appended to the capture store); dome /
                                                 closed roof needs no fetch; unreachable / out of horizon -> source 'none'
  terms(row)   -> (Terms_home, Terms_away, data_through_utc)   MatchupBook built from prior weeks only
  lines(row)   -> (spread, total)   from the schedule snapshot; NaN when no line is published
Point-in-time: `data_through_utc` for the matchup book is the end of the last game day BEFORE the row's week, so a row is
never handed a later game. A live capture is stamped a few seconds after the row's ts_utc; issued_utc within CAPTURE_GRACE_S
of the row is clipped to the row time (a capture made while building the row is known to that row). Anything later raises.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from . import weather_forecast as wf
from .matchup_cross import MatchupBook, Terms
from .weather_factor import WeatherContext, is_indoor

DATA = Path(__file__).resolve().parents[1] / "decision_trees" / "filter_data"
CAPTURE_GRACE_S = 120.0


class NflProviders:
    def __init__(self, data_dir: Path = DATA, forecaster: Optional[wf.CachedForecaster] = None, live: bool = True):
        self.sched = pd.read_csv(data_dir / "nfl_schedule.csv")
        self.tg = pd.read_csv(data_dir / "nfl_team_games.csv")
        self.meta = json.loads((data_dir / "nfl_snapshot_meta.json").read_text())
        self.book = MatchupBook(self.tg)
        self.forecaster = forecaster if forecaster is not None else (wf.CachedForecaster() if live else None)

    def game(self, row: dict) -> dict:
        from prediction_market_bot.pregame_shadow.nfl_forecaster import parse_event_ticker

        ev = parse_event_ticker(row.get("event_ticker", ""))
        if ev is None:
            raise ValueError("nfl_event_ticker_unparsed")
        _, date, away, home = ev
        s = self.sched
        d = pd.to_datetime(s.gameday)
        m = s[(s.home == home) & (s.away == away) & ((d - pd.Timestamp(date)).abs() <= pd.Timedelta(days=1))]
        if m.empty:
            raise ValueError(f"nfl_game_not_in_schedule:{away}@{home}:{date}")
        return m.iloc[0].to_dict()

    def weather(self, row: dict) -> Tuple[WeatherContext, str]:
        g = self.game(row)
        roof = g["roof"] if isinstance(g["roof"], str) else None
        ts = _ts(row["ts_utc"])
        if is_indoor(roof):
            return WeatherContext("forecast", roof, None, None, None, 99.0), ts.isoformat()
        rec = self.forecaster.get(g["stadium_id"], g["kickoff_utc"]) if self.forecaster else None
        if rec is None:
            return WeatherContext("none", roof), ts.isoformat()
        issued = _ts(rec["issued_utc"])
        if 0 < (issued - ts).total_seconds() <= CAPTURE_GRACE_S:
            issued = ts
        ctx, _ = wf.to_context(rec, roof)
        return ctx, issued.isoformat()

    def terms(self, row: dict) -> Tuple[Terms, Terms, str]:
        g = self.game(row)
        season, week = int(g["season"]), int(g["week"])
        prior = self.tg[(self.tg.season < season) | ((self.tg.season == season) & (self.tg.week < week))]
        through = (pd.to_datetime(prior.game_date).max() + pd.Timedelta(hours=30)) if len(prior) else pd.Timestamp("1970-01-01")
        th = self.book.terms(season, week, g["home"], g["away"])
        ta = self.book.terms(season, week, g["away"], g["home"])
        return th, ta, through.strftime("%Y-%m-%dT%H:%M:%SZ")

    def lines(self, row: dict) -> Tuple[Optional[float], Optional[float]]:
        g = self.game(row)
        f = lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)   # noqa: E731
        return f(g["spread_line"]), f(g["total_line"])


def _ts(s) -> datetime:
    from prediction_market_bot.decision_trees.filter_supply import parse_ts

    return parse_ts(s)


_DEFAULT: Optional[NflProviders] = None


def default_nfl_providers() -> Optional[NflProviders]:
    """Lazy singleton; None when the snapshots are not on disk (the row then records filters_unavailable)."""
    global _DEFAULT
    if _DEFAULT is None:
        try:
            _DEFAULT = NflProviders()
        except FileNotFoundError:
            return None
    return _DEFAULT

"""W112.1 Part A -- per-sport filter adapters: what the shadow writers hand the router as tree splits (D6 layer 3).

One adapter per sport, each returns ``(filters | None, note | None)`` for a shadow row from data known BEFORE the row's
timestamp. A data source that is newer than the row raises PITViolation inside the adapter, which the supply turns into
``(None, "pit_violation:...")``: a later game's filter is never handed to the router. Nothing here prices, sizes or orders.
Applies when: logging a row for NBA (prior-season team percentiles). NFL needs a weather FORECAST and a MatchupBook, neither
of which any runner stores yet: injected providers only, else ``filters_unavailable``. NHL calls 112.4's filters only if that
module is merged. MLB is idle until 2027 (no adapter). Never raises.
"""
from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timezone
from typing import Callable, Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_data")


class PITViolation(ValueError):
    """A filter input is dated after the row it would be attached to."""


def parse_ts(s) -> datetime:
    """Tolerant ISO-8601 parse (box Python is 3.9: fromisoformat rejects 'Z')."""
    if isinstance(s, datetime):
        d = s
    else:
        t = str(s).strip()
        if t.endswith("Z"):
            t = t[:-1] + "+00:00"
        d = datetime.fromisoformat(t)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def assert_pit(data_ts, row_ts, what: str = "filter input") -> None:
    if parse_ts(data_ts) > parse_ts(row_ts):
        raise PITViolation(f"{what} dated {parse_ts(data_ts).isoformat()} is after the row at {parse_ts(row_ts).isoformat()}")


_NBA: dict = {}


def nba_table(path: Optional[str] = None) -> dict:
    p = path or os.path.join(DATA_DIR, "nba_team_percentiles.json")
    if p not in _NBA:
        with open(p) as fh:
            _NBA[p] = json.load(fh)
    return _NBA[p]


def nba_adapter(row: dict, table: Optional[dict] = None) -> Tuple[Optional[dict], Optional[str]]:
    """The 111.4 granularity-index leaves for the row's game: prior-season league percentiles of both teams."""
    from prediction_market_bot.nba_engine.filters import nba_filters
    from prediction_market_bot.pregame_shadow.nba_forecaster import parse_event_ticker

    t = table if table is not None else nba_table()
    assert_pit(t["data_through_utc"], row["ts_utc"], "NBA team percentile table")
    ev = parse_event_ticker(row.get("event_ticker", ""))
    if ev is None:
        return None, "nba_event_ticker_unparsed"
    _, _, away, home = ev
    teams = t["teams"]
    if home not in teams or away not in teams:
        return None, "nba_team_not_in_percentile_table"
    return nba_filters(teams[home], teams[away]), None


def nfl_adapter(row: dict, providers=None) -> Tuple[Optional[dict], Optional[str]]:
    """110.1 weather + matchup + market-state leaves. ``providers`` has weather(row)->(WeatherContext, issued_utc),
    terms(row)->(Terms_home, Terms_away, data_through_utc) and lines(row)->(spread, total). None -> unavailable."""
    from prediction_market_bot.nfl_engine.filters import nfl_filters
    from prediction_market_bot.nfl_engine.providers import default_nfl_providers

    providers = providers if providers is not None else default_nfl_providers()   # W113.2: snapshots + live forecast
    if providers is None:
        return None, "nfl_weather_forecast_and_matchup_book_not_wired"

    ctx, issued = providers.weather(row)
    th, ta, through = providers.terms(row)
    assert_pit(issued, row["ts_utc"], "NFL weather forecast")
    assert_pit(through, row["ts_utc"], "NFL matchup book")
    spread, total = providers.lines(row)
    return nfl_filters(ctx, th, ta, spread, total, min_lead_h=0.0), None   # the row timestamp is the PIT bound


def nhl_adapter(row: dict) -> Tuple[Optional[dict], Optional[str]]:
    """112.4's NHL filters, only if that module is merged; else the row says so."""
    try:
        mod = importlib.import_module("prediction_market_bot.nhl_engine.filters")
    except ImportError:
        return None, "filters_unavailable:nhl_engine.filters_not_merged"
    fn = getattr(mod, "nhl_filters_for_row", None)
    if fn is None:
        return None, "filters_unavailable:nhl_filters_for_row_missing"
    out = fn(row)
    return (out, None) if out else (None, "filters_unavailable:nhl_no_inputs")


class FilterSupply:
    def __init__(self, nba_table_: Optional[dict] = None, nfl_providers=None,
                 nhl: Optional[Callable[[dict], Tuple[Optional[dict], Optional[str]]]] = None):
        self.nba_table, self.nfl_providers, self.nhl = nba_table_, nfl_providers, nhl or nhl_adapter

    def for_row(self, row: dict) -> Tuple[Optional[dict], Optional[str]]:
        sport = str(row.get("sport", "")).upper()
        try:
            if sport == "NBA":
                return nba_adapter(row, self.nba_table)
            if sport == "NFL":
                return nfl_adapter(row, self.nfl_providers)
            if sport == "NHL":
                return self.nhl(row)
            return None, f"no_filter_adapter:{sport.lower() or 'unknown'}"
        except PITViolation as e:
            return None, f"pit_violation:{e}"
        except Exception as e:  # noqa: BLE001 - a filter failure never blocks a shadow row
            return None, f"filters_error:{type(e).__name__}"


_DEFAULT: Optional[FilterSupply] = None


def default_supply() -> FilterSupply:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = FilterSupply()
    return _DEFAULT

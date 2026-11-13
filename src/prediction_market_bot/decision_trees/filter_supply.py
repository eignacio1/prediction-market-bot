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
    from prediction_market_bot.archive_intake.nba_distance_filters import HIGHER_IS_BETTER, distance_filters  # lazy: package imports pandas
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
    out = nba_filters(teams[home], teams[away])
    # W114.1 (B-087): the 12 Muse-archive shot-distance entries. Their percentiles sit in the same table; only splits scored and
    # kept in filter_splits.json can move an arm, the rest are logged. A table without them (older build) just skips this.
    if all(k in teams[home] and k in teams[away] for k in HIGHER_IS_BETTER):
        out.update(distance_filters(teams[home], teams[away]))
    return out, None


def nfl_adapter(row: dict, providers=None) -> Tuple[Optional[dict], Optional[str]]:
    """110.1 weather + matchup + market-state leaves. ``providers`` has weather(row)->(WeatherContext, issued_utc),
    terms(row)->(Terms_home, Terms_away, data_through_utc) and lines(row)->(spread, total). None -> unavailable."""
    from prediction_market_bot.nfl_engine.filters import TESTED_SPLITS, nfl_filters, nfl_split_filters
    from prediction_market_bot.nfl_engine.providers import default_nfl_providers

    providers = providers if providers is not None else default_nfl_providers()   # W113.2: snapshots + live forecast
    if providers is None:
        return None, "nfl_weather_forecast_and_matchup_book_not_wired"

    ctx, issued = providers.weather(row)
    th, ta, through = providers.terms(row)
    assert_pit(issued, row["ts_utc"], "NFL weather forecast")
    assert_pit(through, row["ts_utc"], "NFL matchup book")
    spread, total = providers.lines(row)
    out = nfl_filters(ctx, th, ta, spread, total, min_lead_h=0.0)   # the row timestamp is the PIT bound
    if hasattr(providers, "splits"):   # W113.2 Part B/C: granularity-index split leaves (prior-season percentiles)
        ph, pa, pthrough = providers.splits(row)
        assert_pit(pthrough, row["ts_utc"], "NFL split percentiles")
        out.update(nfl_split_filters(ph, pa, keep=TESTED_SPLITS))
    return out, None


_NHL_ALIAS = {"LA": "LAK", "NJ": "NJD", "TB": "TBL", "SJ": "SJS"}  # Kalshi two-letter codes -> store abbreviations
_NHL_MONTHS = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
_NHL_STATE: dict = {}


def nhl_store_dir() -> str:
    import os
    return os.environ.get("NHL_EVENT_STORE") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "exp_output", "NHL_EVENTS")


def _nhl_state(store: str):
    """Point-in-time state tables from the compiled NHL event store, built once per store directory (W113.1 Part B)."""
    import glob
    import os
    import pandas as pd
    from prediction_market_bot.nhl_engine import factors_w112 as fx
    key = (os.path.abspath(store), max([os.path.getmtime(p) for p in glob.glob(store + "/*.parquet")] or [0]))
    if _NHL_STATE.get("key") == key:
        return _NHL_STATE["v"]

    def load(kind):
        ps = sorted(glob.glob(f"{store}/{kind}_202[56].parquet"))
        return pd.concat([pd.read_parquet(p) for p in ps], ignore_index=True) if ps else None
    g, ev, sh = load("games"), load("events"), load("shifts")
    if g is None or ev is None or sh is None:
        v = None
    else:
        g = g.drop_duplicates("game_id", keep="last")
        look = {(r.game_date_et, r.away, r.home): int(r.game_id) for r in g.itertuples()}
        v = {"fx": fx, "g": g.set_index("game_id"), "look": look, "sched": fx.schedule_context(g).set_index(["game_id", "team_id"]),
             "q": fx.shot_quality_rolling(ev, g), "d": fx.deployment_rolling(sh, g)}
    _NHL_STATE.clear()
    _NHL_STATE.update(key=key, v=v)
    return v


def nhl_game_id(event_ticker: str, look: dict) -> Optional[int]:
    import re
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)([A-Z]+)$", event_ticker or "")
    if not m or m.group(2) not in _NHL_MONTHS:
        return None
    d, t = f"20{m.group(1)}-{_NHL_MONTHS[m.group(2)]:02d}-{m.group(3)}", m.group(4)
    for k in range(2, len(t) - 1):
        gid = look.get((d, _NHL_ALIAS.get(t[:k], t[:k]), _NHL_ALIAS.get(t[k:], t[k:])))
        if gid:
            return gid
    return None


def nhl_filters_for_row(row: dict, store: Optional[str] = None) -> Optional[dict]:
    """The eight NHL filter leaves (nhl_engine.filters.nhl_filters) for a shadow row's game, from facts known before puck drop:
    schedule context plus as-of rolling shot quality / deployment and league percentiles at the start time (factors_w112.asof
    carries the point-in-time buffer). None when the game is not in the compiled store (the supply says why)."""
    import pandas as pd
    from prediction_market_bot.nhl_engine.filters import nhl_filters
    st = _nhl_state(store or nhl_store_dir())
    if st is None:
        return None
    gid = nhl_game_id(str(row.get("event_ticker") or ""), st["look"])
    if gid is None:
        return None
    if gid in st.setdefault("memo", {}):  # one game, one answer: facts are fixed at puck drop
        return st["memo"][gid]
    fx, r = st["fx"], st["g"].loc[gid]
    start = pd.Timestamp(r["start_time_utc"])

    def pct(state, col):
        vals = {t: fx.asof(state, int(t), start, (col,)).get(col) for t in state["team_id"].unique()}
        ser = pd.Series({t: v for t, v in vals.items() if v is not None})
        return ser.rank(pct=True, method="average").to_dict() if len(ser) >= 8 else {}
    p = {"hd_for": pct(st["q"], "hd_for"), "hd_against": pct(st["q"], "hd_against"), "top_share": pct(st["d"], "top_share")}
    sides = {}
    for side, tid in (("home", r["home_team_id"]), ("away", r["away_team_id"])):
        sd = st["sched"].loc[(gid, tid)].to_dict()
        for k in ("hd_for", "hd_against", "top_share"):
            sd[k] = p[k].get(tid)
        sides[side] = sd
    st["memo"][gid] = nhl_filters(sides["home"], sides["away"])
    return st["memo"][gid]


def nhl_adapter(row: dict) -> Tuple[Optional[dict], Optional[str]]:
    """NHL filters per row (W113.1 Part B): nhl_engine.filters.nhl_filters over the point-in-time store state."""
    try:
        out = nhl_filters_for_row(row)
    except ImportError:
        return None, "filters_unavailable:nhl_engine_not_importable"
    return (out, None) if out else (None, "filters_unavailable:nhl_game_not_in_store")


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

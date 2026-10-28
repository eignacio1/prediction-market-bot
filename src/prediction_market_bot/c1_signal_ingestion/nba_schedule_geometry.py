"""NBA factor class: travel / schedule geometry, point-in-time (W93.2, ADR-0073/0075).

Every feature here is a pre-game fact: it is computed from the published schedule (venue city + tip instant of this game
and of the team's earlier games), never from a score or a box line. A team-game's row uses only that team's EARLIER
games in the same season (``shift``-based, strictly before), so no feature can see the game it describes or a later one.

Venue geometry comes from a hand-built city table (``CITIES``: lat, lon, IANA zone, altitude in metres) keyed on the ESPN
``venue_address_city``. ESPN carries no coordinates. A city missing from the table gives NaN geometry, never a guess.

Definitions (fixed before any result):
  travel_mi     great-circle miles from the venue of the team's previous game (same season) to this game's venue
  tz_shift      UTC-offset hours at this venue minus at the previous venue, at each game's tip; + = travelled east
  rest_days     calendar days between the two games' Eastern dates, minus 1 (0 = back-to-back)
  g_last4/g_last6   games on the 4 / 6 calendar days before this game's date
  miles_last7   sum of travel legs ending on the 7 calendar days before this game's date
  road_run      consecutive away games ending with this game (0 when this game is at home)
  home_run      consecutive home games ending with this game (0 when this game is away)
  alt_m         altitude of this venue; alt_gain = max(0, alt_m - the team's home altitude) (0 for the home team)
  body_tip_hr   tip hour (0-23.99) on the clock of the team's home zone; a west-coast team in an Eastern 7pm game is 16
  late_body     1 if body_tip_hr is before 12 or at/after 22 (a start the body clock treats as off-hours)
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .nba_point_in_time import EASTERN, ESPN_TO_NBA_ABBR

# city -> (lat, lon, IANA zone, altitude m). Venue-city level: all 30 arenas 2016-2027 plus the bubble, Tampa, Austin,
# Las Vegas and the international sites ESPN lists. Altitude from the city's arena (Denver 1609, Salt Lake 1288).
CITIES = {
    "Atlanta": (33.757, -84.396, "America/New_York", 320), "Austin": (30.281, -97.733, "America/Chicago", 150),
    "Berlin": (52.521, 13.439, "Europe/Berlin", 34), "Boston": (42.366, -71.062, "America/New_York", 5),
    "Brooklyn": (40.683, -73.975, "America/New_York", 10), "Charlotte": (35.225, -80.839, "America/New_York", 220),
    "Chicago": (41.881, -87.674, "America/Chicago", 180), "Cleveland": (41.496, -81.688, "America/New_York", 200),
    "Dallas": (32.790, -96.810, "America/Chicago", 130), "Denver": (39.749, -105.008, "America/Denver", 1609),
    "Detroit": (42.341, -83.055, "America/Detroit", 183), "Houston": (29.751, -95.362, "America/Chicago", 15),
    "Indianapolis": (39.764, -86.156, "America/Indiana/Indianapolis", 220),
    "Inglewood": (33.945, -118.341, "America/Los_Angeles", 30), "Lake Buena Vista": (28.370, -81.550, "America/New_York", 30),
    "Las Vegas": (36.103, -115.178, "America/Los_Angeles", 610), "London": (51.503, -0.003, "Europe/London", 5),
    "Los Angeles": (34.043, -118.267, "America/Los_Angeles", 90), "Manchester": (53.463, -2.291, "Europe/London", 40),
    "Memphis": (35.138, -90.051, "America/Chicago", 80), "Mexico City": (19.404, -99.101, "America/Mexico_City", 2240),
    "Miami": (25.781, -80.187, "America/New_York", 3), "Milwaukee": (43.045, -87.917, "America/Chicago", 190),
    "Minneapolis": (44.979, -93.276, "America/Chicago", 255), "New Orleans": (29.949, -90.082, "America/Chicago", 3),
    "New York": (40.751, -73.994, "America/New_York", 10), "Oakland": (37.750, -122.203, "America/Los_Angeles", 5),
    "Oklahoma City": (35.463, -97.515, "America/Chicago", 365), "Orlando": (28.539, -81.384, "America/New_York", 30),
    "Paris": (48.839, 2.378, "Europe/Paris", 35), "Philadelphia": (39.901, -75.172, "America/New_York", 10),
    "Phoenix": (33.446, -112.071, "America/Phoenix", 330), "Portland": (45.532, -122.667, "America/Los_Angeles", 15),
    "Sacramento": (38.580, -121.500, "America/Los_Angeles", 10), "Salt Lake City": (40.768, -111.901, "America/Denver", 1288),
    "San Antonio": (29.427, -98.438, "America/Chicago", 200), "San Francisco": (37.768, -122.388, "America/Los_Angeles", 5),
    "Tampa": (27.943, -82.452, "America/New_York", 5), "Toronto": (43.643, -79.379, "America/Toronto", 76),
    "Washington": (38.898, -77.021, "America/New_York", 5),
}
EARTH_MI = 3958.8
LATE_BODY_BEFORE, LATE_BODY_FROM = 12.0, 22.0


def haversine_mi(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles (array-safe)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((np.radians(lon2) - np.radians(lon1)) / 2) ** 2
    return 2 * EARTH_MI * np.arcsin(np.sqrt(a))


def venue_table(schedule: pd.DataFrame, espn: pd.DataFrame) -> pd.DataFrame:
    """game_id -> venue city (ESPN), matched like ``tip_table`` on (Eastern day, home, away); unmatched/ambiguous = NaN."""
    g = schedule.drop_duplicates("game_id", keep="last").copy()
    g["game_id"] = g["game_id"].astype(str)
    e = espn.copy()
    e["tip"] = pd.to_datetime(e["date"], utc=True, errors="coerce")
    e["et_day"] = e["tip"].dt.tz_convert(EASTERN).dt.strftime("%Y-%m-%d")
    for side in ("home", "away"):
        e[f"{side}_a"] = e[f"{side}_abbreviation"].replace(ESPN_TO_NBA_ABBR)
    e = e.dropna(subset=["tip"]).drop_duplicates(["et_day", "home_a", "away_a"], keep=False)
    g["et_day"] = pd.to_datetime(g["game_date"].astype(str)).dt.strftime("%Y-%m-%d")
    m = g.merge(e[["et_day", "home_a", "away_a", "venue_address_city"]], how="left",
                left_on=["et_day", "home_team_abbreviation", "away_team_abbreviation"], right_on=["et_day", "home_a", "away_a"])
    return pd.DataFrame({"game_id": m["game_id"].to_numpy(), "city": m["venue_address_city"].to_numpy()}).set_index("game_id")


def _offset_hours(tip_utc: pd.Series, zone: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=tip_utc.index)
    for z in zone.dropna().unique():
        m = (zone == z) & tip_utc.notna()
        if m.any():
            local = tip_utc[m].dt.tz_convert(z)
            out[m] = local.map(lambda t: t.utcoffset().total_seconds() / 3600.0)
    return out


def _body_hour(tip_utc: pd.Series, zone: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=tip_utc.index)
    for z in zone.dropna().unique():
        m = (zone == z) & tip_utc.notna()
        if m.any():
            loc = tip_utc[m].dt.tz_convert(z)
            out[m] = loc.dt.hour + loc.dt.minute / 60.0
    return out


def schedule_geometry(tg: pd.DataFrame, venues: pd.DataFrame, cities: Optional[dict] = None) -> pd.DataFrame:
    """Add the geometry columns to a team-game table (``team_game_table`` output: game_id, team_id, side, season, date,
    tip_earliest). ``venues`` is ``venue_table`` output. Rows are returned sorted by (team, season, date, tip)."""
    cities = cities or CITIES
    tg = tg.sort_values(["team_id", "season", "date", "tip_latest"]).reset_index(drop=True).copy()
    tg["city"] = tg["game_id"].astype(str).map(venues["city"])
    for j, name in enumerate(("lat", "lon", "zone", "alt_m")):
        tg[name] = tg["city"].map(lambda c, j=j: cities.get(c, (np.nan,) * 4)[j] if isinstance(c, str) else np.nan)
    tg["off_h"] = _offset_hours(tg["tip_earliest"], tg["zone"])
    tg["is_home"] = (tg["side"] == "home").astype(float)
    # team home zone / altitude: per-season mode of the venues of its home games (handles Oakland->SF, Clippers' move)
    hm = tg[tg["is_home"] == 1].groupby(["team_id", "season"])["city"].agg(lambda s: s.mode().iat[0] if s.notna().any() else np.nan)
    tg["home_city"] = [hm.get((t, s), np.nan) for t, s in zip(tg["team_id"], tg["season"])]
    tg["home_zone"] = tg["home_city"].map(lambda c: cities[c][2] if c in cities else np.nan)
    tg["home_alt"] = tg["home_city"].map(lambda c: cities[c][3] if c in cities else np.nan)
    tg["body_tip_hr"] = _body_hour(tg["tip_earliest"], tg["home_zone"])
    tg["late_body"] = ((tg["body_tip_hr"] < LATE_BODY_BEFORE) | (tg["body_tip_hr"] >= LATE_BODY_FROM)).astype(float).where(tg["body_tip_hr"].notna())
    grp = tg.groupby(["team_id", "season"], sort=False)
    prev = {c: grp[c].shift(1) for c in ("lat", "lon", "off_h", "date")}
    tg["travel_mi"] = haversine_mi(prev["lat"], prev["lon"], tg["lat"], tg["lon"])
    tg["tz_shift"] = tg["off_h"] - prev["off_h"]
    tg["tz_cross"] = tg["tz_shift"].abs()
    tg["east"] = (tg["tz_shift"] > 0).astype(float).where(tg["tz_shift"].notna())
    tg["alt_gain"] = (tg["alt_m"] - tg["home_alt"]).clip(lower=0).where(tg["is_home"] == 0, 0.0)
    leg = tg["travel_mi"].fillna(0.0).to_numpy()
    g4, g6, m7, road, homer = (np.zeros(len(tg)) for _ in range(5))
    for _, idx in grp.indices.items():
        dd = tg["date"].iloc[idx].to_numpy(dtype="datetime64[D]").astype(np.int64)
        hi = np.searchsorted(dd, dd, side="left")  # first game on the same date or later = games strictly before are [:hi]
        g4[idx] = hi - np.searchsorted(dd, dd - 4, side="left")
        g6[idx] = hi - np.searchsorted(dd, dd - 6, side="left")
        cs = np.concatenate([[0.0], np.cumsum(leg[idx])])
        m7[idx] = cs[hi] - cs[np.searchsorted(dd, dd - 7, side="left")]
        h = tg["is_home"].iloc[idx].to_numpy()
        r_run = h_run = 0
        for k, v in enumerate(h):
            r_run, h_run = (0, h_run + 1) if v == 1 else (r_run + 1, 0)
            road[idx[k]], homer[idx[k]] = r_run, h_run
    tg["g_last4"], tg["g_last6"], tg["miles_last7"], tg["road_run"], tg["home_run"] = g4, g6, m7, road, homer
    tg["rest_days_g"] = (tg["date"] - prev["date"]).dt.days - 1
    return tg

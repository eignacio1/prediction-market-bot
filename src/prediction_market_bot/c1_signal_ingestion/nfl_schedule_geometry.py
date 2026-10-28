"""NFL schedule geometry (W93.4 Part B, factor N15): travel, time zones, short week, bye, neutral site, body-clock kickoff.

Point-in-time per team-game from the schedule alone (team base, venue, kickoff, rest days): nothing after kickoff is
read. Free data only. Miles are great-circle from the team's base city to the game venue city (city-level, not
stadium-level; a route taken through a previous road game is not modelled). Relocated franchises (OAK/SD/STL) use today's base
(LV/LAC/LA), so pre-move distances carry city-pair error of a few hundred miles; stated, not corrected.

When this applies: scheduling-driven fatigue and body-clock effects. When it does not: injuries, weather, anything
not in the schedule. Nothing here is wired into any model, runner, order or ledger row.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo

import pandas as pd

# team base (lat, lon, IANA tz). Relocated franchises share the new base.
_B = {
    "ARI": (33.53, -112.26, "America/Phoenix"), "ATL": (33.76, -84.40, "America/New_York"), "BAL": (39.28, -76.62, "America/New_York"),
    "BUF": (42.77, -78.79, "America/New_York"), "CAR": (35.23, -80.85, "America/New_York"), "CHI": (41.86, -87.62, "America/Chicago"),
    "CIN": (39.10, -84.52, "America/New_York"), "CLE": (41.51, -81.70, "America/New_York"), "DAL": (32.75, -97.09, "America/Chicago"),
    "DEN": (39.74, -105.02, "America/Denver"), "DET": (42.34, -83.05, "America/New_York"), "GB": (44.50, -88.06, "America/Chicago"),
    "HOU": (29.68, -95.41, "America/Chicago"), "IND": (39.76, -86.16, "America/New_York"), "JAX": (30.32, -81.64, "America/New_York"),
    "KC": (39.05, -94.48, "America/Chicago"), "LA": (33.95, -118.34, "America/Los_Angeles"), "LAC": (33.95, -118.34, "America/Los_Angeles"),
    "LV": (36.09, -115.18, "America/Los_Angeles"), "MIA": (25.96, -80.24, "America/New_York"), "MIN": (44.97, -93.26, "America/Chicago"),
    "NE": (42.09, -71.26, "America/New_York"), "NO": (29.95, -90.08, "America/Chicago"), "NYG": (40.81, -74.07, "America/New_York"),
    "NYJ": (40.81, -74.07, "America/New_York"), "PHI": (39.90, -75.17, "America/New_York"), "PIT": (40.45, -80.02, "America/New_York"),
    "SEA": (47.60, -122.33, "America/Los_Angeles"), "SF": (37.40, -121.97, "America/Los_Angeles"), "TB": (27.98, -82.50, "America/New_York"),
    "TEN": (36.17, -86.77, "America/Chicago"), "WAS": (38.91, -76.86, "America/New_York"),
}
_ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LA", "LAR": "LA", "JAC": "JAX"}

# Neutral-site / international venues by stadium name: (lat, lon, tz, international)
_N = {
    "Wembley Stadium": (51.56, -0.28, "Europe/London", True), "Tottenham Stadium": (51.60, -0.07, "Europe/London", True),
    "Tottenham Hotspur Stadium": (51.60, -0.07, "Europe/London", True), "Twickenham Stadium": (51.46, -0.34, "Europe/London", True),
    "Allianz Arena": (48.22, 11.62, "Europe/Berlin", True), "FC Bayern Munich Stadium": (48.22, 11.62, "Europe/Berlin", True),
    "Deutsche Bank Park": (50.07, 8.65, "Europe/Berlin", True), "Stade de France": (48.92, 2.36, "Europe/Paris", True),
    "Bernabeu": (40.45, -3.69, "Europe/Madrid", True), "Azteca Stadium": (19.30, -99.15, "America/Mexico_City", True),
    "Estadio Banorte": (19.30, -99.15, "America/Mexico_City", True), "Arena Corinthians": (-23.55, -46.47, "America/Sao_Paulo", True),
    "Maracana Stadium": (-22.91, -43.23, "America/Sao_Paulo", True), "Melbourne Cricket Ground": (-37.82, 144.98, "Australia/Melbourne", True),
    "Rogers Centre": (43.64, -79.39, "America/Toronto", True),
}


def _canon(team: str) -> str:
    return _ALIAS.get(team, team)


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin((radians(lon2) - radians(lon1)) / 2) ** 2
    return 3958.7613 * 2 * asin(sqrt(a))


def _utc_offset_hours(tz: str, when: datetime) -> float:
    return when.replace(tzinfo=ZoneInfo(tz)).utcoffset().total_seconds() / 3600


@dataclass(frozen=True)
class TeamGameGeometry:
    miles: float            # base city -> venue city
    tz_shift: float         # hours; + = travelled east (clock ahead of body), - = west
    short_week: bool        # <= 5 days rest (Thursday games)
    post_bye: bool          # >= 13 days rest
    neutral: bool
    international: bool
    body_clock_hour: float  # kickoff hour on the team's own base-city clock


def team_game(team: str, venue_team: str, gameday: str, gametime: str, rest_days: float | None, stadium: str | None = None,
              neutral: bool = False) -> TeamGameGeometry:
    """Geometry for ``team`` playing at ``venue_team``'s home (or at a neutral ``stadium``). ``gameday``/``gametime``
    are the nflverse US-Eastern date and clock."""
    t, v = _canon(team), _canon(venue_team)
    has_clock = bool(gametime) and str(gametime) != "None"
    ko_et = datetime.fromisoformat(f"{gameday}T{gametime if has_clock else '13:00'}").replace(tzinfo=ZoneInfo("America/New_York"))
    international = False
    if neutral and stadium in _N:
        vlat, vlon, vtz, international = _N[stadium]
    elif neutral:
        vlat, vlon, vtz = _B[v][0], _B[v][1], _B[v][2]      # unlisted US neutral venue: fall back to the nominal host
    else:
        vlat, vlon, vtz = _B[v]
    blat, blon, btz = _B[t]
    miles = 0.0 if (not neutral and t == v) else haversine_miles(blat, blon, vlat, vlon)
    naive = ko_et.replace(tzinfo=None)
    off_base = _utc_offset_hours(btz, ko_et.astimezone(ZoneInfo("UTC")).replace(tzinfo=None))
    off_venue = _utc_offset_hours(vtz, ko_et.astimezone(ZoneInfo("UTC")).replace(tzinfo=None))
    ko_utc = ko_et.astimezone(ZoneInfo("UTC"))
    body = (ko_utc.hour + ko_utc.minute / 60 + off_base) % 24 if has_clock else float("nan")   # no kickoff time before ~2000s rows
    rd = float("nan") if rest_days is None else float(rest_days)
    return TeamGameGeometry(round(miles, 1), off_venue - off_base, rd <= 5, rd >= 13, bool(neutral), international, round(body, 2) if has_clock else body)


def schedule_features(sched: pd.DataFrame) -> pd.DataFrame:
    """One row per game: home/away geometry columns (h_*, a_*) from an nflverse schedule frame."""
    rows = []
    for r in sched.itertuples():
        neutral = str(r.location) == "Neutral"
        for side, team, rest in (("h", r.home_team, r.home_rest), ("a", r.away_team, r.away_rest)):
            g = team_game(team, r.home_team, r.gameday, r.gametime, None if pd.isna(rest) else rest, getattr(r, "stadium", None), neutral)
            rows.append((r.Index, side, g))
    out = {}
    for idx, side, g in rows:
        d = out.setdefault(idx, {})
        for f in ("miles", "tz_shift", "short_week", "post_bye", "neutral", "international", "body_clock_hour"):
            d[f"{side}_{f}"] = getattr(g, f)
    return pd.DataFrame.from_dict(out, orient="index")

"""NHL point-in-time factor classes for the router (W112.4 Part A, backlog B-012, directive D-06).

Three families, each a feature known before puck drop of the game it is computed for:

* ``schedule_context(games)``  - rest / schedule density / venue / travel (NHL-6, NHL-7, NHL-8). Reads only the public schedule
  (teams, start instant, venue): no score, no state of the game itself. Applies when: any NHL game with a published start.
  Does not apply: a venue missing from ``ARENAS`` yields NaN travel (never a guess).
* ``shot_quality_rolling(events, games, window)`` - skater/shot-quality interpretation (NHL-1): per team, high-danger share of
  unblocked attempts for and against over its previous ``window`` completed games (``shift(1)``: the game itself is never in its
  own window). Applies when: the store has events for the team's earlier games.
* ``deployment_rolling(shifts, games, window)`` - line / pair deployment from shifts (NHL-3): share of a team's skater ice time
  taken by its top six skaters over the previous ``window`` games (top-heavy = depth-light).

All three use the previous-completed-games rule of ``c1_signal_ingestion.nhl_point_in_time`` (4h regular-season buffer, 9h playoffs).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

# venue name -> (lat, lon, standard-time UTC offset hours). Hand-built from public arena locations (free; GG-1011 closed for
# these venues). A venue not listed gives NaN travel.
ARENAS: dict = {
    "AT&T Stadium": (32.747, -97.093, -6), "Amerant Bank Arena": (26.158, -80.326, -5),
    "American Airlines Center": (32.790, -96.810, -6), "Ball Arena": (39.749, -105.008, -7),
    "Benchmark International Arena": (27.943, -82.452, -5), "Bridgestone Arena": (36.159, -86.779, -6),
    "Canada Life Centre": (49.893, -97.144, -6), "Canadian Tire Centre": (45.297, -75.927, -5),
    "Capital One Arena": (38.898, -77.021, -5), "Centre Bell": (45.496, -73.569, -5),
    "Climate Pledge Arena": (47.622, -122.354, -8), "Crypto.com Arena": (34.043, -118.267, -8),
    "Delta Center": (40.768, -111.901, -7), "Enterprise Center": (38.627, -90.203, -6),
    "Grand Casino Arena": (44.945, -93.101, -6), "Honda Center": (33.808, -117.877, -8),
    "KeyBank Center": (42.875, -78.876, -5), "Lenovo Center": (35.803, -78.722, -5),
    "Little Caesars Arena": (42.341, -83.055, -5), "Madison Square Garden": (40.751, -73.994, -5),
    "Nationwide Arena": (39.969, -83.006, -5), "PPG Paints Arena": (40.439, -79.989, -5),
    "PSD Bank Dome": (51.261, 6.733, 1), "Princess Auto Stadium": (49.806, -97.158, -6),
    "Prudential Center": (40.734, -74.171, -5), "Rice-Eccles Stadium": (40.760, -111.848, -7),
    "Rogers Arena": (49.278, -123.109, -8), "Rogers Place": (53.547, -113.498, -7),
    "SAP Center at San Jose": (37.333, -121.901, -8), "Scotiabank Arena": (43.643, -79.379, -5),
    "Scotiabank Saddledome": (51.037, -114.052, -7), "T-Mobile Arena": (36.103, -115.178, -8),
    "TD Garden": (42.366, -71.062, -5), "UBS Arena": (40.712, -73.726, -5), "United Center": (41.881, -87.674, -6),
    "Veikkaus Arena": (61.495, 23.775, 2), "Xfinity Mobile Arena": (39.901, -75.172, -5),
}
HIGH_DANGER_X, HIGH_DANGER_Y = 69.0, 22.0     # |x| >= 69 (within 20 ft of the goal line), |y| <= 22: the slot
UNBLOCKED = ("shot-on-goal", "goal", "missed-shot")


def haversine_km(a: tuple, b: tuple) -> float:
    (la1, lo1), (la2, lo2) = a[:2], b[:2]
    p1, p2 = math.radians(la1), math.radians(la2)
    dphi, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def _long(games: pd.DataFrame) -> pd.DataFrame:
    """One row per (game, team) with the schedule facts only."""
    g = games.drop_duplicates("game_id", keep="last").copy()
    g["start"] = pd.to_datetime(g["start_time_utc"], utc=True, errors="coerce")
    base = ["game_id", "start", "venue", "game_type", "neutral_site"]
    h = g[base + ["home_team_id", "away_team_id"]].rename(columns={"home_team_id": "team_id", "away_team_id": "opp_id"})
    h["is_home"] = True
    a = g[base + ["away_team_id", "home_team_id"]].rename(columns={"away_team_id": "team_id", "home_team_id": "opp_id"})
    a["is_home"] = False
    out = pd.concat([h, a], ignore_index=True).sort_values(["team_id", "start", "game_id"]).reset_index(drop=True)
    return out


def schedule_context(games: pd.DataFrame) -> pd.DataFrame:
    """Per (game_id, team_id): rest_days (since the team's previous scheduled game start), back_to_back, games_last_7d
    (scheduled starts in the 7 days before this start), travel_km and tz_shift_h from the team's previous venue, is_home,
    neutral_site. First game of a team in the table gets NaN rest/travel (no previous game known)."""
    t = _long(games)
    grp = t.groupby("team_id", sort=False)
    prev_start = grp["start"].shift(1)
    t["rest_days"] = (t["start"] - prev_start).dt.total_seconds() / 86400.0
    t["back_to_back"] = (t["rest_days"] < 1.3) & t["rest_days"].notna()
    cnt = []
    for _, d in t.groupby("team_id", sort=False):
        s = d["start"].dt.tz_convert(None).to_numpy()
        lo = np.searchsorted(s, s - np.timedelta64(7, "D"), side="left")
        cnt.append(pd.Series(np.arange(len(s)) - lo, index=d.index))
    t["games_last_7d"] = pd.concat(cnt).reindex(t.index)
    pv = grp["venue"].shift(1)
    km, tz = [], []
    for v0, v1 in zip(pv, t["venue"]):
        if v0 in ARENAS and v1 in ARENAS:
            km.append(haversine_km(ARENAS[v0], ARENAS[v1])); tz.append(ARENAS[v1][2] - ARENAS[v0][2])
        else:
            km.append(np.nan); tz.append(np.nan)
    t["travel_km"], t["tz_shift_h"] = km, tz
    t.loc[prev_start.isna(), ["travel_km", "tz_shift_h"]] = np.nan
    return t[["game_id", "team_id", "is_home", "neutral_site", "rest_days", "back_to_back", "games_last_7d", "travel_km", "tz_shift_h"]]


def _through_rolling(per_game: pd.DataFrame, cols: list, window: int) -> pd.DataFrame:
    """per_game: team_id, start, game_id + value columns. Mean over the team's ``window`` games ENDING WITH this one (min 5).
    This is the state AFTER the game: use it only through ``asof`` (latest row completed before the target puck drop)."""
    p = per_game.sort_values(["team_id", "start", "game_id"]).copy()
    for c in cols:
        p[c + "_prior"] = p.groupby("team_id")[c].transform(lambda s: s.rolling(window, min_periods=5).mean())
    return p


BUFFER = pd.Timedelta(hours=4)    # regular season; playoffs 9h (nhl_point_in_time.BUFFER_PLAYOFF) - pass buffer= to override


def asof(state: pd.DataFrame, team_id: int, start, cols: tuple, buffer: pd.Timedelta = BUFFER) -> dict:
    """Latest state row of ``team_id`` whose game finished (start + buffer) at or before ``start``; {} if none."""
    d = state[(state["team_id"] == team_id) & (state["start"] + buffer <= pd.Timestamp(start))]
    if d.empty:
        return {}
    r = d.sort_values(["start", "game_id"]).iloc[-1]
    return {c: (None if pd.isna(r[c]) else float(r[c])) for c in cols}


def shot_quality_rolling(events: pd.DataFrame, games: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Per (game_id, team_id, start): hd_for / hd_against = high-danger share of that team's unblocked attempts for / against over
    its ``window`` games ending with this one. Read it with ``asof`` (so a game never sees itself). NaN until 5 games."""
    e = events[events["type"].isin(UNBLOCKED) & events["x"].notna()].copy()
    e["hd"] = ((e["x"].abs() >= HIGH_DANGER_X) & (e["y"].abs() <= HIGH_DANGER_Y)).astype(float)
    gl = _long(games)[["game_id", "team_id", "opp_id", "start"]]
    f = e.groupby(["game_id", "owner_team_id"])["hd"].agg(att_for="size", hd_for_n="sum").reset_index().rename(columns={"owner_team_id": "team_id"})
    m = gl.merge(f, on=["game_id", "team_id"], how="left")
    ag = f.rename(columns={"team_id": "opp_id", "att_for": "att_ag", "hd_for_n": "hd_ag_n"})
    m = m.merge(ag, on=["game_id", "opp_id"], how="left")
    m = m[m["att_for"].notna()]                     # only games the store has events for
    m["hd_for"] = m["hd_for_n"] / m["att_for"]
    m["hd_against"] = m["hd_ag_n"] / m["att_ag"]
    r = _through_rolling(m, ["hd_for", "hd_against"], window)
    return r[["game_id", "team_id", "start", "hd_for_prior", "hd_against_prior"]].rename(columns={"hd_for_prior": "hd_for", "hd_against_prior": "hd_against"})


def deployment_rolling(shifts: pd.DataFrame, games: pd.DataFrame, window: int = 20, top: int = 6) -> pd.DataFrame:
    """Per (game_id, team_id, start): top_share = share of the team's skater shift time taken by its top ``top`` skaters, averaged
    over the ``window`` games ending with this one (top-heavy deployment). Read it with ``asof``. NaN until 5 games."""
    s = shifts.groupby(["game_id", "team_id", "player_id"])["duration_s"].sum().reset_index()
    def share(d):
        v = d["duration_s"].sort_values(ascending=False)
        return v.iloc[:top].sum() / v.sum() if v.sum() > 0 else np.nan
    sh = s.groupby(["game_id", "team_id"]).apply(share, include_groups=False).rename("top_share").reset_index()
    gl = _long(games)[["game_id", "team_id", "start"]]
    m = gl.merge(sh, on=["game_id", "team_id"], how="inner")
    r = _through_rolling(m, ["top_share"], window)
    return r[["game_id", "team_id", "start", "top_share_prior"]].rename(columns={"top_share_prior": "top_share"})

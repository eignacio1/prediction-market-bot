"""NFL unit-vs-unit matchup crosses, point-in-time (W110.1, B-069). Factor class N19-N21 in SEATS/nfl.toml.

Three crosses, each = (offence unit rate) + (opposing defence unit rate) - league, in natural units:
  pass      offence pass EPA/play        x opponent pass-defence EPA/play allowed
  rush      offence rush success rate    x opponent run-defence success rate allowed
  pressure  offence pressure-allowed     x opponent pressure-generated   (sack or QB hit per dropback)
Every rate is an empirical-Bayes shrink toward the league mean with strength k (plays), built ONLY from games strictly
before (season, week); prior seasons count with weight PRIOR_DECAY**age. A cross is converted to points by a beta fitted
outside (rate_layer.Factor protocol), never here. Pure functions over a team-game table; no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

PRIOR_DECAY = 0.5      # weight of one season back; two back = 0.25; older ignored
MAX_AGE = 2
# metric -> (numerator col, denominator col, shrink strength k in plays)
METRICS = {
    "pass": ("pass_epa", "pass_n", 150.0),
    "rush": ("rush_succ", "rush_n", 150.0),
    "pressure": ("pressured", "pass_n", 200.0),
}
PLAYS = {"pass": 36.0, "rush": 25.0, "pressure": 36.0}   # typical per-team-game volume used to scale a cross to a count


def build_team_games(plays: pd.DataFrame) -> pd.DataFrame:
    """pbp -> one OFFENSE row per (season, week, game, team). Needs: season, week, game_id, posteam, defteam, play_type,
    epa, success, sack, qb_hit, season_type. Regular season only."""
    p = plays[(plays.season_type == "REG") & plays.play_type.isin(["pass", "run"]) & plays.epa.notna() & plays.posteam.notna()].copy()
    p["is_pass"] = (p.play_type == "pass").astype(float)
    p["pass_epa"] = np.where(p.is_pass == 1, p.epa, 0.0)
    p["rush_succ"] = np.where(p.is_pass == 0, p.success.fillna(0), 0.0)
    p["pressured"] = np.where(p.is_pass == 1, ((p.sack.fillna(0) == 1) | (p.qb_hit.fillna(0) == 1)).astype(float), 0.0)
    p["rush_flag"] = 1.0 - p.is_pass
    g = p.groupby(["season", "week", "game_id", "posteam", "defteam"], as_index=False).agg(
        pass_epa=("pass_epa", "sum"), pass_n=("is_pass", "sum"), rush_succ=("rush_succ", "sum"),
        rush_n=("rush_flag", "sum"), pressured=("pressured", "sum"))
    return g.rename(columns={"posteam": "team", "defteam": "opp"})


@dataclass(frozen=True)
class Terms:
    pass_: float
    rush: float
    pressure: float


class MatchupBook:
    """PIT unit ratings + crosses from a team-game table (build_team_games output)."""

    def __init__(self, team_games: pd.DataFrame):
        self.tg = team_games.copy()
        self._cache: dict = {}

    def _weights(self, season: int, week: int) -> pd.DataFrame:
        t = self.tg
        age = season - t.season
        use = ((age == 0) & (t.week < week)) | ((age >= 1) & (age <= MAX_AGE))
        u = t[use].copy()
        u["w"] = PRIOR_DECAY ** (season - u.season)
        u.loc[u.season == season, "w"] = 1.0
        return u

    def _tables(self, season: int, week: int) -> dict:
        key = (season, week)
        if key in self._cache:
            return self._cache[key]
        u = self._weights(season, week)
        out = {}
        for m, (num, den, k) in METRICS.items():
            wn, wd = u[num] * u.w, u[den] * u.w
            lg = float(wn.sum() / wd.sum()) if wd.sum() > 0 else np.nan
            off = (u.assign(a=wn, b=wd).groupby("team")[["a", "b"]].sum())
            dfn = (u.assign(a=wn, b=wd).groupby("opp")[["a", "b"]].sum())
            sh = lambda t: ((t.a + k * lg) / (t.b + k)).to_dict()   # noqa: E731
            out[m] = dict(lg=lg, off=sh(off), dfn=sh(dfn), n_off=off.b.to_dict(), n_dfn=dfn.b.to_dict())
        self._cache[key] = out
        return out

    def rating(self, season: int, week: int, team: str, side: str, metric: str) -> Optional[float]:
        """Shrunk rate of `team`'s offence (side='off') or defence-allowed (side='dfn'); league mean if unseen."""
        t = self._tables(season, week)[metric]
        return t[side].get(team, t["lg"])

    def cross(self, season: int, week: int, off: str, dfn: str, metric: str) -> float:
        """Excess over league of the offence-unit x defence-unit cross, natural units per play."""
        t = self._tables(season, week)[metric]
        if not np.isfinite(t["lg"]):
            return 0.0
        return (t["off"].get(off, t["lg"]) - t["lg"]) + (t["dfn"].get(dfn, t["lg"]) - t["lg"])

    def terms(self, season: int, week: int, off: str, dfn: str) -> Terms:
        """Volume-scaled crosses (excess per play x typical plays) -- the regressors a fitted beta converts to points."""
        return Terms(*(PLAYS[m] * self.cross(season, week, off, dfn, m) for m in ("pass", "rush", "pressure")))

    def rank_same_week(self, season: int, week: int, team: str, side: str, metric: str, hist_seasons: range) -> dict:
        """Where `team`'s PIT rating sits vs every team's rating at the SAME week in `hist_seasons` (GRANULARITY_INDEX rank)."""
        cur = self.rating(season, week, team, side, metric)
        hist = []
        for s in hist_seasons:
            t = self._tables(s, week)[metric][side]
            hist.extend(t.values())
        hist = np.asarray(hist, float)
        return dict(value=cur, n_hist=int(len(hist)), pct=float((hist < cur).mean() + 0.5 * (hist == cur).mean()) if len(hist) else None)

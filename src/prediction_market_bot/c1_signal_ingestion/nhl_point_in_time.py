"""Point-in-time contract for the NHL event store (W83.3, ADR-0073 stage 1).

Contract: a query "as of puck drop of game G" can never return a row produced by G or by a game that could not
have finished before G starts.

* ``post_game`` rows (play-by-play, shifts, box-score player lines, rosters of a finished game) are usable for G
  only if the source game's start + a duration buffer is <= G's start.
* The NHL schedule carries the real start INSTANT (``startTimeUTC``) for every game, so unlike the NBA module there
  is no imputed bound: ``start`` is both the earliest and the latest possible start. A game missing that instant is
  a build error and refused (``PointInTime.__init__``), never guessed.
* Buffer by game type: a regular-season game (60 min + overtime + shootout + intermissions) ends well inside 4h; a
  playoff game can run multiple sudden-death overtimes (the longest ran past 7h of wall clock), so playoff games
  carry 9h. A buffer too small leaks (an unfinished game's rows look usable); too large only drops same-day games.
* ``season_static`` tables are refused outright. ``schedule`` rows are usable for other games only once complete;
  for G itself only the ``PREGAME_CONTEXT_COLS`` whitelist (teams, date, venue, start): no score, no state.
"""
from __future__ import annotations

import pandas as pd

BUFFER_REGULAR = pd.Timedelta(hours=4)
BUFFER_PLAYOFF = pd.Timedelta(hours=9)
PLAYOFF_TYPE = 3
PREGAME_CONTEXT_COLS = (
    "game_id", "season", "game_type", "game_date_et", "start_time_utc", "venue", "neutral_site",
    "home_team_id", "home", "away_team_id", "away",
)


class LeakError(AssertionError):
    """A returned row could not have been known at the query game's puck drop."""


def start_table(games: pd.DataFrame) -> pd.DataFrame:
    """game_id -> (start, end_latest, season, game_type). ``games``: the compiled ``games_<season>`` rows."""
    g = games.drop_duplicates("game_id", keep="last").copy()
    g["game_id"] = g["game_id"].astype("int64")
    g["start"] = pd.to_datetime(g["start_time_utc"], utc=True, errors="coerce")
    buf = g["game_type"].map(lambda t: BUFFER_PLAYOFF if t == PLAYOFF_TYPE else BUFFER_REGULAR)
    g["end_latest"] = g["start"] + buf
    return g[["game_id", "season", "game_type", "start", "end_latest"]].set_index("game_id")


class PointInTime:
    def __init__(self, starts: pd.DataFrame):
        self.t = starts
        bad = self.t["start"].isna()
        if bad.any():
            raise ValueError(f"{int(bad.sum())} games have no start instant, e.g. {list(self.t.index[bad][:3])}")

    def start(self, game_id: int) -> pd.Timestamp:
        return self.t.at[int(game_id), "start"]

    def completed_before(self, game_id: int) -> frozenset:
        """Game ids certainly finished at G's puck drop (G itself, anything later, and anything possibly still
        in progress are excluded)."""
        done = self.t["end_latest"] <= self.start(game_id)
        return frozenset(int(i) for i in self.t.index[done])

    def view(self, df: pd.DataFrame, kind: str, game_id: int, game_col: str = "game_id") -> pd.DataFrame:
        if kind in ("post_game", "schedule"):
            return df[df[game_col].astype("int64").isin(self.completed_before(game_id))]
        if kind == "season_static":
            raise ValueError("season_static tables are not point-in-time safe and cannot be viewed as of a game")
        raise ValueError(f"unknown kind {kind!r}")

    def pregame_context(self, games: pd.DataFrame, game_id: int) -> dict:
        row = games.loc[games["game_id"].astype("int64") == int(game_id)]
        if row.empty:
            raise KeyError(game_id)
        r = row.iloc[-1]
        return {c: r[c] for c in PREGAME_CONTEXT_COLS if c in row.columns}

    def assert_no_leak(self, result: pd.DataFrame, kind: str, game_id: int, game_col: str = "game_id") -> None:
        """Independent re-check of a returned frame; raises ``LeakError`` naming the first offending rows."""
        if result.empty:
            return
        if kind not in ("post_game", "schedule"):
            raise LeakError(f"kind {kind!r} can never be returned for a point-in-time query")
        bad = result[~result[game_col].astype("int64").isin(self.completed_before(game_id))]
        if len(bad):
            raise LeakError(f"{len(bad)} rows not knowable at puck drop of {game_id}; first: {bad.iloc[0].to_dict()}")

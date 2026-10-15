"""Point-in-time contract for the NFL event store (W73.2, ADR-0073 stage 1).

Contract: a query "as of kickoff of game G" can never return a row that was produced by G or by a game
that kicks off after G, and never returns a row whose information could not have been public at G's kickoff.
The three row kinds follow ``nfl_event_store.Source.kind``:

* ``post_game``  - rows describe a finished game (plays, participation, charting, snaps, PFR, officials).
  Usable for G only if that game's kickoff + ``COMPLETION_BUFFER`` <= G's kickoff. The buffer is
  deliberately longer than any real game, so a 1pm game is never "known" to a 4:25pm kickoff.
* ``weekly``     - injury reports and weekly rosters carry (season, week) but no publication time (GG-732).
  Usable for G if the row's (season, week) is earlier than G's, or it is the same week and G kicks off on a
  Sunday or Monday (the final report is out Friday). Thursday/Friday/Saturday games exclude week-of rows.
* ``dated``      - rows with their own timestamp ``dt`` (2025+ depth charts): usable iff dt < G's kickoff.
  Weekly-schema files (2001-2024) fall back to the weekly rule.

Schedule rows of G itself are available only through ``pregame_context`` - a whitelist that excludes
scores, closing lines (GG-733), observed weather (GG-734) and starting QBs (known late). Kickoff is the
schedule's ``gameday`` + ``gametime`` (US Eastern); a missing ``gametime`` falls back to 00:00 Eastern on
gameday and is flagged ``kickoff_imputed`` - the earliest possible, i.e. the conservative direction.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd

COMPLETION_BUFFER = pd.Timedelta(hours=4)
EASTERN = "America/New_York"
WEEK_OF_OK_WEEKDAYS = frozenset({"Sunday", "Monday"})
PREGAME_CONTEXT_COLS = (
    "game_id", "season", "week", "game_type", "gameday", "weekday", "gametime", "away_team", "home_team",
    "location", "stadium", "stadium_id", "roof", "surface", "div_game", "home_rest", "away_rest",
    "home_coach", "away_coach",
)


class LeakError(AssertionError):
    """A returned row could not have been known at the query game's kickoff."""


def kickoff_table(games: pd.DataFrame) -> pd.DataFrame:
    """game_id -> kickoff_utc (+ imputed flag, season, week, weekday). One row per game_id."""
    g = games.drop_duplicates("game_id", keep="last").copy()
    time_str = g["gametime"].where(g["gametime"].notna() & (g["gametime"].astype(str) != ""), "00:00")
    local = pd.to_datetime(g["gameday"].astype(str) + " " + time_str.astype(str), errors="coerce")
    g["kickoff_utc"] = local.dt.tz_localize(EASTERN, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    g["kickoff_imputed"] = g["gametime"].isna() | (g["gametime"].astype(str) == "")
    return g[["game_id", "season", "week", "weekday", "kickoff_utc", "kickoff_imputed"]].set_index("game_id")


class PointInTime:
    def __init__(self, games: pd.DataFrame):
        self.k = kickoff_table(games)
        bad = self.k["kickoff_utc"].isna()
        if bad.any():
            raise ValueError(f"{int(bad.sum())} games have no resolvable kickoff, e.g. {list(self.k.index[bad][:3])}")

    def kickoff(self, game_id: str) -> pd.Timestamp:
        return self.k.at[game_id, "kickoff_utc"]

    def completed_before(self, game_id: str) -> frozenset:
        """Game ids whose results were public at G's kickoff (G itself and anything later excluded)."""
        cut = self.kickoff(game_id)
        done = self.k["kickoff_utc"] + COMPLETION_BUFFER <= cut
        return frozenset(self.k.index[done])

    def _week_ok(self, df: pd.DataFrame, game_id: str) -> pd.Series:
        s, w, day = (self.k.at[game_id, c] for c in ("season", "week", "weekday"))
        season = pd.to_numeric(df["season"], errors="coerce")
        week = pd.to_numeric(df["week"], errors="coerce")
        earlier = (season < s) | ((season == s) & (week < w))
        same = (season == s) & (week == w)
        return (earlier | (same & (day in WEEK_OF_OK_WEEKDAYS))).fillna(False)

    def view(self, df: pd.DataFrame, kind: str, game_id: str, game_col: str = "game_id") -> pd.DataFrame:
        """Rows of ``df`` that were knowable at the kickoff of ``game_id``."""
        if kind == "post_game":
            return df[df[game_col].isin(self.completed_before(game_id))]
        if kind == "weekly":
            return df[self._week_ok(df, game_id)]
        if kind == "dated":
            if "dt" not in df.columns:
                return df[self._week_ok(df, game_id)]
            stamp = pd.to_datetime(df["dt"], utc=True, errors="coerce")
            return df[(stamp < self.kickoff(game_id)).fillna(False)]
        if kind == "schedule":
            return df[df[game_col].isin(self.completed_before(game_id))]
        raise ValueError(f"unknown kind {kind!r}")

    def pregame_context(self, games: pd.DataFrame, game_id: str) -> dict:
        """Whitelisted schedule facts about G itself. Referee follows the weekly rule (no assignment timestamp)."""
        row = games.loc[games["game_id"] == game_id]
        if row.empty:
            raise KeyError(game_id)
        r = row.iloc[-1]
        out = {c: r[c] for c in PREGAME_CONTEXT_COLS if c in row.columns}
        out["kickoff_utc"] = self.kickoff(game_id)
        out["kickoff_imputed"] = bool(self.k.at[game_id, "kickoff_imputed"])
        out["referee"] = r.get("referee") if self.k.at[game_id, "weekday"] in WEEK_OF_OK_WEEKDAYS else None
        return out

    def assert_no_leak(self, result: pd.DataFrame, kind: str, game_id: str, game_col: str = "game_id") -> None:
        """Independent re-check of a returned frame; raises ``LeakError`` naming the first offending rows."""
        if result.empty:
            return
        if kind in ("post_game", "schedule"):
            ok = self.completed_before(game_id)
            bad = result[~result[game_col].isin(ok)]
        elif kind == "dated" and "dt" in result.columns:
            stamp = pd.to_datetime(result["dt"], utc=True, errors="coerce")
            bad = result[~(stamp < self.kickoff(game_id)).fillna(False)]
        else:
            bad = result[~self._week_ok(result, game_id)]
        if len(bad):
            raise LeakError(f"{len(bad)} rows not knowable at kickoff of {game_id}; first: {bad.iloc[0].to_dict()}")

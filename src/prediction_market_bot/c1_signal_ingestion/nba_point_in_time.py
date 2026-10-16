"""Point-in-time contract for the NBA event store (W78.4, ADR-0073 stage 1).

Contract: a query "as of tip-off of game G" can never return a row produced by G or by a game that could not
have finished before G tips, and never a row whose information was not public at G's tip-off.

Row kinds follow ``nba_event_store.Source.kind``:

* ``post_game``     - rows describe a finished game (play-by-play, possessions, lineups, shots, box scores,
  rosters, officials). Usable for G only if the other game's *latest possible* completion
  (``tip_latest + COMPLETION_BUFFER``) is <= G's *earliest possible* tip (``tip_earliest``).
* ``schedule``      - results tables; only the ``pregame_context`` whitelist may be read for G itself.
* ``season_static`` - season-level tables with no dates (coaches): refused outright, never point-in-time.
* ``snapshot``      - dated snapshots (injuries) with their own ``as_of_date``: a row is usable only for games
  tipping after it was knowable (a date-only stamp counts from the end of that day), so it is never back-filled.

Tip bounds. The nba_stats schedule has only an Eastern calendar date; the ESPN schedule has the tip instant.
Where the two join (Eastern date + home + away) the real instant is used for both bounds. Where they do not, the
bounds are the Eastern calendar day: ``tip_earliest`` = 00:00 ET, ``tip_latest`` = 24:00 ET. That is conservative
on both sides - an unmatched game looks as early as possible when it is the *query* game and as late as possible
when it is the *candidate* - which is the opposite of the NFL module's 00:00 imputation (right for kickoffs, wrong
for the completed-game side). ``tip_imputed`` flags those games.

The buffer covers a game running long (overtime, delays); 4h is above the longest regulation+OT NBA game.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

COMPLETION_BUFFER = pd.Timedelta(hours=4)
EASTERN = "America/New_York"
# ESPN abbreviation -> nba_stats abbreviation, only where they differ (measured on the 2016-2027 schedules).
ESPN_TO_NBA_ABBR = {"NY": "NYK", "SA": "SAS", "GS": "GSW", "NO": "NOP", "UTAH": "UTA", "WSH": "WAS", "PHX": "PHX",
                    "BKN": "BKN", "CHA": "CHA", "NOH": "NOP", "NJ": "BKN", "SEA": "OKC"}
PREGAME_CONTEXT_COLS = (
    "game_id", "season", "season_type", "game_date", "home_team_id", "home_team_abbreviation",
    "away_team_id", "away_team_abbreviation", "venue_id", "venue_full_name", "neutral_site",
    "home_rest_days", "away_rest_days", "home_back_to_back", "away_back_to_back",
)


def snapshot_known_at(col: pd.Series) -> pd.Series:
    """UTC instant a snapshot row became knowable. A date-only ``as_of_date`` could have been captured any time that
    day, so it counts from the END of the day; a full timestamp is used as given."""
    txt = col.astype(str)
    stamp = pd.to_datetime(txt, utc=True, errors="coerce")
    return stamp.where(txt.str.len() > 10, stamp + pd.Timedelta(days=1))


class LeakError(AssertionError):
    """A returned row could not have been known at the query game's tip-off."""


def _et_day_bounds(day: pd.Series) -> tuple[pd.Series, pd.Series]:
    d = pd.to_datetime(day.astype(str), errors="coerce")
    start = d.dt.tz_localize(EASTERN, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    end = (d + pd.Timedelta(days=1)).dt.tz_localize(EASTERN, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    return start, end


def tip_table(schedule: pd.DataFrame, espn: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """game_id -> (tip_earliest, tip_latest, tip_imputed, season, season_type, game_date). One row per game_id.

    ``schedule``: nba_stats schedule (game_id, season, game_date, home_team_abbreviation, away_team_abbreviation).
    ``espn``: ESPN schedule (date UTC instant, home_abbreviation, away_abbreviation) or None.
    """
    g = schedule.drop_duplicates("game_id", keep="last").copy()
    g["game_id"] = g["game_id"].astype(str)
    start, end = _et_day_bounds(g["game_date"])
    g["tip_earliest"], g["tip_latest"], g["tip_imputed"] = start, end, True
    if espn is not None and len(espn):
        e = espn.copy()
        e["tip"] = pd.to_datetime(e["date"], utc=True, errors="coerce")
        e["et_day"] = e["tip"].dt.tz_convert(EASTERN).dt.strftime("%Y-%m-%d")
        for side in ("home", "away"):
            e[f"{side}_a"] = e[f"{side}_abbreviation"].replace(ESPN_TO_NBA_ABBR)
        e = e.dropna(subset=["tip"]).drop_duplicates(["et_day", "home_a", "away_a"], keep=False)  # ambiguous = unmatched
        g["et_day"] = pd.to_datetime(g["game_date"].astype(str)).dt.strftime("%Y-%m-%d")
        m = g.merge(e[["et_day", "home_a", "away_a", "tip"]], how="left",
                    left_on=["et_day", "home_team_abbreviation", "away_team_abbreviation"],
                    right_on=["et_day", "home_a", "away_a"])
        hit = m["tip"].notna().to_numpy()
        g.loc[hit, "tip_earliest"] = m.loc[hit, "tip"].to_numpy()
        g.loc[hit, "tip_latest"] = m.loc[hit, "tip"].to_numpy()
        g.loc[hit, "tip_imputed"] = False
    cols = ["game_id", "season", "season_type", "game_date", "tip_earliest", "tip_latest", "tip_imputed"]
    return g[cols].set_index("game_id")


class PointInTime:
    def __init__(self, tips: pd.DataFrame):
        self.t = tips
        bad = self.t[["tip_earliest", "tip_latest"]].isna().any(axis=1)
        if bad.any():
            raise ValueError(f"{int(bad.sum())} games have no resolvable tip bounds, e.g. {list(self.t.index[bad][:3])}")

    def tip_earliest(self, game_id: str) -> pd.Timestamp:
        return self.t.at[game_id, "tip_earliest"]

    def completed_before(self, game_id: str) -> frozenset:
        """Game ids certainly finished and public at G's earliest possible tip (G itself and anything later excluded)."""
        cut = self.tip_earliest(game_id)
        done = self.t["tip_latest"] + COMPLETION_BUFFER <= cut
        return frozenset(self.t.index[done])

    def view(self, df: pd.DataFrame, kind: str, game_id: str, game_col: str = "game_id",
             as_of_col: str = "as_of_date") -> pd.DataFrame:
        """Rows of ``df`` that were knowable at the tip-off of ``game_id``."""
        if kind == "post_game":
            return df[df[game_col].astype(str).isin(self.completed_before(game_id))]
        if kind == "snapshot":
            stamp = snapshot_known_at(df[as_of_col])
            return df[(stamp + COMPLETION_BUFFER <= self.tip_earliest(game_id)).fillna(False)]
        if kind == "schedule":
            return df[df[game_col].astype(str).isin(self.completed_before(game_id))]
        if kind == "season_static":
            raise ValueError("season_static tables are not point-in-time safe and cannot be viewed as of a game")
        raise ValueError(f"unknown kind {kind!r}")

    def pregame_context(self, schedule: pd.DataFrame, game_id: str) -> dict:
        """Whitelisted schedule facts about G itself: teams, date, tip, venue, rest. No scores, no status, no lines."""
        row = schedule.loc[schedule["game_id"].astype(str) == str(game_id)]
        if row.empty:
            raise KeyError(game_id)
        r = row.iloc[-1]
        out = {c: r[c] for c in PREGAME_CONTEXT_COLS if c in row.columns}
        out["tip_earliest"] = self.tip_earliest(game_id)
        out["tip_imputed"] = bool(self.t.at[game_id, "tip_imputed"])
        return out

    def assert_no_leak(self, result: pd.DataFrame, kind: str, game_id: str, game_col: str = "game_id",
                       as_of_col: str = "as_of_date") -> None:
        """Independent re-check of a returned frame; raises ``LeakError`` naming the first offending rows."""
        if result.empty:
            return
        if kind in ("post_game", "schedule"):
            bad = result[~result[game_col].astype(str).isin(self.completed_before(game_id))]
        elif kind == "snapshot":
            stamp = snapshot_known_at(result[as_of_col])
            bad = result[~(stamp + COMPLETION_BUFFER <= self.tip_earliest(game_id)).fillna(False)]
        else:
            raise LeakError(f"kind {kind!r} can never be returned for a point-in-time query")
        if len(bad):
            raise LeakError(f"{len(bad)} rows not knowable at tip-off of {game_id}; first: {bad.iloc[0].to_dict()}")

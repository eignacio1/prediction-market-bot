"""
C1: Team Defensive Stats Store
================================
Module:   c1_signal_ingestion.team_stats_store
Phase:    Phase 7 (Strategy B — opponent defensive rating feature, T-075)
Purpose:  Hold per-team-game statistics from TeamGameLog for use in C2
          opponent defensive feature derivation.

Key computation:
  pts_allowed per game = pts_scored - plus_minus
  (Team scored X with net margin M means opponent scored X - M)

Usage::

    store = TeamStatsStore()
    # Build from NBAIngestionClient:
    for team in client.get_all_teams():
        ok, log_df = client.fetch_team_game_log(team["id"], season="2024-25")
        if ok and not log_df.empty:
            store.add_team_log(team["abbreviation"], log_df)

    # Query in C2:
    rating = store.get_opp_def_rating("GSW", as_of_date="2025-01-15")
    # → rolling mean pts_allowed by GSW in the 10 games before 2025-01-15

Build once per experiment run; pass into FeatureStore.compute_features_bulk()
as the optional team_stats_store argument.

Temporal integrity (TI-01):
  get_opp_def_rating() uses strictly prior games (game_date < as_of_date).
  The current game's outcome is never included.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

# Default rolling window for opponent defensive rating (matches player window)
DEFAULT_WINDOW: int = 10
DEFAULT_MIN_PERIODS: int = 3


class TeamStatsStore:
    """
    Stores per-team-game statistics for opponent feature derivation in C2.

    Internally maps team_abbreviation → sorted game log DataFrame with
    a computed pts_allowed column (= pts_scored - plus_minus).

    Thread safety: not thread-safe; build once before parallel feature computation.
    """

    def __init__(self) -> None:
        self._logs: dict[str, pd.DataFrame] = {}  # UPPER abbr → sorted game log

    def add_team_log(self, team_abbr: str, game_log_df: pd.DataFrame) -> None:
        """
        Add a team's game log from NBAIngestionClient.fetch_team_game_log().

        Computes pts_allowed per game:
          pts_allowed = pts - plus_minus
          (if team scored X with net margin M, opponent scored X - M)

        Parameters
        ----------
        team_abbr:
            Three-letter team abbreviation (case-insensitive; stored as uppercase).
        game_log_df:
            DataFrame from fetch_team_game_log() containing at least
            columns: game_date, pts, plus_minus.
        """
        if game_log_df.empty:
            return

        df = game_log_df.copy()

        for col in ("pts", "plus_minus"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "pts" in df.columns and "plus_minus" in df.columns:
            df["pts_allowed"] = df["pts"] - df["plus_minus"]
        else:
            df["pts_allowed"] = np.nan

        if "game_date" in df.columns:
            df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")

        df = df.sort_values("game_date").reset_index(drop=True)
        self._logs[team_abbr.upper()] = df

    def get_opp_def_rating(
        self,
        opp_team_abbr: str,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = DEFAULT_MIN_PERIODS,
    ) -> float | None:
        """
        Return the opponent team's rolling average points allowed per game
        in the {window} games strictly before {as_of_date}.

        Temporal integrity: uses game_date < as_of_date (prior games only).

        Parameters
        ----------
        opp_team_abbr:
            Opponent team abbreviation (case-insensitive).
        as_of_date:
            Game date of the player's current game (YYYY-MM-DD string).
            Only games strictly BEFORE this date are used.
        window:
            Maximum number of prior games to include in the rolling mean.
        min_periods:
            Minimum games required to return a non-None result.

        Returns
        -------
        float | None
            Rolling mean pts_allowed. None if team not found or < min_periods games.
        """
        key = opp_team_abbr.upper() if opp_team_abbr else ""
        if not key or key not in self._logs:
            return None

        df = self._logs[key]
        prior = df[df["game_date"] < as_of_date]
        if len(prior) < min_periods:
            return None

        tail = prior.tail(window)
        vals = tail["pts_allowed"].dropna()
        if len(vals) < min_periods:
            return None

        return float(vals.mean())

    def get_opp_pts_scored(
        self,
        opp_team_abbr: str,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = DEFAULT_MIN_PERIODS,
    ) -> float | None:
        """
        Return the opponent team's rolling average points scored per game
        (offensive pace proxy) in the {window} games before {as_of_date}.

        Parameters are the same as get_opp_def_rating().
        """
        key = opp_team_abbr.upper() if opp_team_abbr else ""
        if not key or key not in self._logs:
            return None

        df = self._logs[key]
        prior = df[df["game_date"] < as_of_date]
        if len(prior) < min_periods:
            return None

        tail = prior.tail(window)
        vals = tail["pts"].dropna()
        if len(vals) < min_periods:
            return None

        return float(vals.mean())

    @property
    def teams_loaded(self) -> list[str]:
        """List of team abbreviations currently in the store."""
        return list(self._logs.keys())

    def __len__(self) -> int:
        """Number of teams loaded."""
        return len(self._logs)

    def __contains__(self, team_abbr: str) -> bool:
        return team_abbr.upper() in self._logs

    def to_cache_dict(self) -> dict[str, list[dict]]:
        """Serialize to a JSON-safe dict for file caching between PIPE-02 and PIPE-03."""
        out: dict[str, list[dict]] = {}
        for abbr, df in self._logs.items():
            keep = [c for c in ("game_date", "pts", "plus_minus", "pts_allowed") if c in df.columns]
            out[abbr] = df[keep].to_dict(orient="records")
        return out

    @classmethod
    def from_cache_dict(cls, data: dict[str, list[dict]]) -> "TeamStatsStore":
        """Deserialize from a cache dict written by to_cache_dict()."""
        store = cls()
        for abbr, records in data.items():
            if not records:
                continue
            df = pd.DataFrame(records)
            for col in ("pts", "plus_minus", "pts_allowed"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            if "game_date" in df.columns:
                df = df.sort_values("game_date").reset_index(drop=True)
            store._logs[abbr.upper()] = df
        return store

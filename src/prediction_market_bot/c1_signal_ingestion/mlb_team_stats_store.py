"""
C1: MLB Team Stats Store — opponent run-allowed rolling history.

Mirrors NBA TeamStatsStore but tracks runs_allowed (baseball defensive proxy)
instead of pts_allowed. C2 queries get_opp_runs_allowed() when computing
context features for batter game rows.

Temporal integrity (TI-01): all lookups are strictly prior to as_of_date
(game_date < as_of_date — current game's result never in its own feature vector).

Usage
-----
Populate via MLBIngestionClient.fetch_completed_games() output:

    ok, games_df = client.fetch_completed_games("2026-04-01", "2026-06-22")
    store = MLBTeamStatsStore.build_from_games(games_df)
    era = store.get_opp_runs_allowed("NYY", "2026-06-23")
"""

from __future__ import annotations

import pandas as pd

DEFAULT_WINDOW = 10
MIN_PERIODS = 3


class MLBTeamStatsStore:
    """Holds per-team game logs for MLB. Keys are uppercase team abbreviations.

    Internal schema per team: game_date (date), runs (int), runs_allowed (int).
    """

    def __init__(self) -> None:
        self._store: dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_team_log(self, team_abbr: str, game_log_df: pd.DataFrame) -> None:
        """Add or replace the game log for team_abbr.

        game_log_df must contain: game_date, runs, runs_allowed.
        If runs_allowed is absent but run_differential is present,
        runs_allowed is derived as runs − run_differential.
        Empty DataFrames are silently ignored.
        """
        if game_log_df is None or game_log_df.empty:
            return
        df = game_log_df.copy()
        key = team_abbr.upper()

        if "game_date" in df.columns:
            df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
            df = df.sort_values("game_date").reset_index(drop=True)

        if "runs_allowed" not in df.columns:
            if "runs" in df.columns and "run_differential" in df.columns:
                df["runs_allowed"] = df["runs"] - df["run_differential"]

        self._store[key] = df

    @classmethod
    def build_from_games(cls, games_df: pd.DataFrame) -> "MLBTeamStatsStore":
        """Build store from the fetch_completed_games() output DataFrame.

        games_df columns: game_date, home_team_abbr, away_team_abbr,
        home_runs, away_runs.

        Each game contributes two rows: one home-perspective and one away-perspective.
        """
        store = cls()
        if games_df is None or games_df.empty:
            return store

        team_logs: dict[str, list[dict]] = {}
        for _, row in games_df.iterrows():
            home_abbr = str(row.get("home_team_abbr", "")).upper()
            away_abbr = str(row.get("away_team_abbr", "")).upper()
            home_runs = row.get("home_runs")
            away_runs = row.get("away_runs")
            game_date = row.get("game_date")

            if home_abbr:
                team_logs.setdefault(home_abbr, []).append({
                    "game_date": game_date,
                    "runs": home_runs,
                    "runs_allowed": away_runs,
                })
            if away_abbr:
                team_logs.setdefault(away_abbr, []).append({
                    "game_date": game_date,
                    "runs": away_runs,
                    "runs_allowed": home_runs,
                })

        for abbr, records in team_logs.items():
            store.add_team_log(abbr, pd.DataFrame(records))

        return store

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_opp_runs_allowed(
        self,
        opp_team_abbr: str,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
    ) -> float | None:
        """Rolling mean of runs allowed by opp_team_abbr over last `window` games
        strictly prior to as_of_date (TI-01: game_date < as_of_date).

        Returns None if team unknown, runs_allowed column missing, or insufficient data.
        """
        key = opp_team_abbr.upper()
        if key not in self._store:
            return None
        df = self._store[key]
        if "runs_allowed" not in df.columns:
            return None
        cutoff = pd.to_datetime(as_of_date).date()
        prior = df[df["game_date"] < cutoff]
        if len(prior) < min_periods:
            return None
        recent = prior.tail(window)
        if len(recent) < min_periods:
            return None
        mean = recent["runs_allowed"].mean()
        return float(mean) if pd.notna(mean) else None

    def get_opp_runs_scored(
        self,
        opp_team_abbr: str,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
    ) -> float | None:
        """Rolling mean of runs scored by opp_team_abbr — offensive pace proxy."""
        key = opp_team_abbr.upper()
        if key not in self._store:
            return None
        df = self._store[key]
        if "runs" not in df.columns:
            return None
        cutoff = pd.to_datetime(as_of_date).date()
        prior = df[df["game_date"] < cutoff]
        if len(prior) < min_periods:
            return None
        recent = prior.tail(window)
        if len(recent) < min_periods:
            return None
        mean = recent["runs"].mean()
        return float(mean) if pd.notna(mean) else None

    # ------------------------------------------------------------------
    # Dunder / properties
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, team_abbr: object) -> bool:
        return str(team_abbr).upper() in self._store

    @property
    def teams_loaded(self) -> list[str]:
        return sorted(self._store.keys())

    # ------------------------------------------------------------------
    # Cache serialization (PIPE-02 → PIPE-03 caching pattern)
    # ------------------------------------------------------------------

    def to_cache_dict(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for team, df in self._store.items():
            records = df.copy()
            records["game_date"] = records["game_date"].astype(str)
            out[team] = records.to_dict("records")
        return out

    @classmethod
    def from_cache_dict(cls, cache: dict[str, list[dict]]) -> "MLBTeamStatsStore":
        store = cls()
        for team, records in cache.items():
            if not records:
                continue
            df = pd.DataFrame(records)
            if "game_date" in df.columns:
                df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
            store._store[team.upper()] = df
        return store

"""
C1: NFL Team Stats Store — recency-weighted offensive/defensive EPA history.

Mirrors MLBTeamStatsStore's shape (build-from-source classmethod, TI-01
temporal filter, to/from_cache_dict) but tracks off_epa / def_epa_allowed
(NFL efficiency proxies) instead of runs / runs_allowed, and uses an
exponential-decay recency-weighted mean instead of a plain rolling mean —
per GG-253's explicit "recency-weighted" requirement, deviating from MLB's
plain tail(window).mean() precedent deliberately (see DEFAULT_DECAY below).

Temporal integrity (TI-01): all lookups are strictly prior to as_of_date
(game_date < as_of_date — current game's result never in its own feature vector).

Cold start (Week 1 of a new season) — no special case, by design
--------------------------------------------------------------------
Unlike MLBTeamStatsStore, these query methods take NO season parameter.
They filter strictly on game_date < as_of_date across every season loaded
into the store, then take the most recent `window` of those. In Week 1 of
a new season there are zero current-season games satisfying that filter,
so tail(window) naturally and automatically pulls from the end of the most
recently available prior season — prior-season carryover falls out of the
temporal-ordering logic as an emergent property, with no branching code.
A team with zero games anywhere in the store (the true fallback-of-fallback,
not a realistic in-season case) returns None, exactly like MLB's contract —
substituting a league-average prior is a C2/caller decision, not C1's job.

Usage
-----
Populate via NFLIngestionClient's fetch_schedule() + fetch_team_stats_bulk():

    ok1, schedule_df = client.fetch_schedule()
    ok2, stats_df = client.fetch_team_stats_bulk([2023, 2024, 2025])
    store = NFLTeamStatsStore.build_from_team_stats(stats_df, schedule_df)
    off = store.get_off_epa("KC", "2026-09-08")
    dfa = store.get_def_epa_allowed("KC", "2026-09-08")
"""

from __future__ import annotations

import pandas as pd
from typing import Any

DEFAULT_WINDOW = 8
MIN_PERIODS = 3

# Exponential-decay half-life ≈ 4.27 games (0.85 ** 4.27 == 0.5) — a game
# 4-5 back carries half the weight of the most recent one. Chosen over
# MLB's plain rolling mean because GG-253 explicitly calls for recency
# weighting, and because NFL's 17-game season (vs. MLB's 162) makes a
# team's most recent form a much larger share of its available sample —
# an unweighted 8-game window is already ~half a season, so recency
# weighting matters more here than it would for MLB's 10-of-162 window.
DEFAULT_DECAY = 0.85


class NFLTeamStatsStore:
    """Holds per-team game logs for NFL. Keys are uppercase team abbreviations.

    Internal schema per team: game_date (date), off_epa (float),
    def_epa_allowed (float).
    """

    def __init__(self) -> None:
        self._store: dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_team_log(self, team_abbr: str, game_log_df: pd.DataFrame) -> None:
        """Add or replace the game log for team_abbr.

        game_log_df must contain: game_date, off_epa, def_epa_allowed.
        Empty DataFrames are silently ignored.
        """
        if game_log_df is None or game_log_df.empty:
            return
        df = game_log_df.copy()
        key = team_abbr.upper()

        if "game_date" in df.columns:
            df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
            df = df.sort_values("game_date").reset_index(drop=True)

        self._store[key] = df

    @classmethod
    def build_from_team_stats(
        cls,
        team_stats_df: pd.DataFrame,
        schedule_df: pd.DataFrame,
    ) -> "NFLTeamStatsStore":
        """Build store from NFLIngestionClient's fetch_team_stats_bulk() +
        fetch_schedule() outputs.

        team_stats_df columns: season, week, season_type, game_id, team,
        opponent_team, off_epa (one row per team-game).
        schedule_df columns: game_id, gameday, ... (one row per game;
        used only to attach a real calendar date to each team-game row,
        since team_stats_df carries season/week but not a date).

        def_epa_allowed for a team-game = the opponent's off_epa in that
        same game_id — the NFL analogue of MLBTeamStatsStore.build_from_games()
        deriving runs_allowed from the opposing team's runs scored.
        """
        store = cls()
        if team_stats_df is None or team_stats_df.empty:
            return store

        opp_off_epa = team_stats_df.set_index(["game_id", "team"])["off_epa"]

        date_by_game_id: dict[str, Any] = {}
        if schedule_df is not None and not schedule_df.empty and "game_id" in schedule_df.columns:
            date_by_game_id = dict(zip(schedule_df["game_id"], schedule_df["gameday"]))

        team_logs: dict[str, list[dict[str, Any]]] = {}
        for _, row in team_stats_df.iterrows():
            team = str(row["team"]).upper()
            opponent = row["opponent_team"]
            game_id = row["game_id"]
            try:
                def_epa_allowed = opp_off_epa.loc[(game_id, opponent)]
            except KeyError:
                def_epa_allowed = None

            team_logs.setdefault(team, []).append({
                "game_date": date_by_game_id.get(game_id),
                "off_epa": row["off_epa"],
                "def_epa_allowed": def_epa_allowed,
            })

        for abbr, records in team_logs.items():
            store.add_team_log(abbr, pd.DataFrame(records))

        return store

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def _get_recency_weighted(
        self,
        team_abbr: str,
        as_of_date: str,
        column: str,
        window: int,
        min_periods: int,
        decay: float,
    ) -> float | None:
        """Exponential-decay recency-weighted mean of `column` over the last
        `window` games strictly prior to as_of_date (TI-01: game_date < as_of_date).

        No season parameter: the filter operates across every season loaded
        into the store, so Week 1 of a new season automatically carries over
        from the end of the most recent prior season with no special case —
        see module docstring.

        Weight for the i-th (0-indexed, oldest-to-newest) of n non-null
        values: decay ** (n - 1 - i) — the most recent value gets weight 1,
        each one further back is discounted by another factor of `decay`.

        Returns None if team unknown, column missing, or insufficient data.
        """
        key = team_abbr.upper()
        if key not in self._store:
            return None
        df = self._store[key]
        if column not in df.columns:
            return None
        cutoff = pd.to_datetime(as_of_date).date()
        prior = df[df["game_date"] < cutoff]
        if len(prior) < min_periods:
            return None
        recent = prior.tail(window)
        vals = recent[column].dropna()
        if len(vals) < min_periods:
            return None

        n = len(vals)
        weights = pd.Series([decay ** (n - 1 - i) for i in range(n)], index=vals.index)
        weighted_sum = (vals * weights).sum()
        weight_total = weights.sum()
        if weight_total == 0:
            return None
        return float(weighted_sum / weight_total)

    def get_off_epa(
        self,
        team_abbr: str,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
        decay: float = DEFAULT_DECAY,
    ) -> float | None:
        """Recency-weighted mean offensive EPA (passing_epa + rushing_epa)
        for team_abbr over its last `window` games strictly before as_of_date."""
        return self._get_recency_weighted(
            team_abbr, as_of_date, "off_epa", window, min_periods, decay
        )

    def get_def_epa_allowed(
        self,
        team_abbr: str,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
        decay: float = DEFAULT_DECAY,
    ) -> float | None:
        """Recency-weighted mean defensive EPA allowed (opponent's off_epa
        in each game) for team_abbr over its last `window` games strictly
        before as_of_date. Higher = worse defense (more EPA given up)."""
        return self._get_recency_weighted(
            team_abbr, as_of_date, "def_epa_allowed", window, min_periods, decay
        )

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

    def to_cache_dict(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for team, df in self._store.items():
            records = df.copy()
            records["game_date"] = records["game_date"].astype(str)
            out[team] = [{str(k): v for k, v in rec.items()} for rec in records.to_dict("records")]
        return out

    @classmethod
    def from_cache_dict(cls, cache: dict[str, list[dict[str, Any]]]) -> "NFLTeamStatsStore":
        store = cls()
        for team, records in cache.items():
            if not records:
                continue
            df = pd.DataFrame(records)
            if "game_date" in df.columns:
                df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
            store._store[team.upper()] = df
        return store

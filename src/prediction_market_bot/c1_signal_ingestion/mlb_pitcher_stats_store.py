"""
C1: MLB Pitcher Stats Store — per-start rolling SP performance cache.

Holds per-game pitching logs for individual pitchers. C2 reads this store
when building the starting-pitcher feature overlay for batter game rows:

    sp_era_l5       — ERA over last 5 starts prior to game_date
    sp_k_per_9_l5   — K/9 over last 5 starts
    sp_bb_per_9_l5  — BB/9 over last 5 starts

Temporal integrity (TI-01): all queries guard with game_date < as_of_date.
Relief appearances (is_start == 0) are stored but excluded from SP queries.

Population pattern
------------------
    ok, df = client.fetch_pitcher_game_log(player_id, season)
    store.add_pitcher_log(player_id, df)
"""

from __future__ import annotations

import pandas as pd
from typing import Any

DEFAULT_WINDOW = 5
MIN_PERIODS = 2


def _era(er: float, ip: float) -> float | None:
    if ip <= 0:
        return None
    return (er / ip) * 9.0


def _k_per_9(k: float, ip: float) -> float | None:
    if ip <= 0:
        return None
    return (k / ip) * 9.0


def _bb_per_9(bb: float, ip: float) -> float | None:
    if ip <= 0:
        return None
    return (bb / ip) * 9.0


class MLBPitcherStatsStore:
    """Per-pitcher per-appearance game logs. All SP queries are TI-01 guarded."""

    def __init__(self) -> None:
        self._store: dict[int, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_pitcher_log(self, pitcher_id: int, game_log_df: pd.DataFrame) -> None:
        """Add or replace the game log for pitcher_id.

        game_log_df must contain: game_date, ip, er, k, bb, is_start.
        Empty DataFrames are silently ignored.
        """
        if game_log_df is None or game_log_df.empty:
            return
        df = game_log_df.copy()
        if "game_date" in df.columns:
            df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
            df = df.sort_values("game_date").reset_index(drop=True)
        self._store[int(pitcher_id)] = df

    # ------------------------------------------------------------------
    # Private helper
    # ------------------------------------------------------------------

    def _prior_starts(
        self, pitcher_id: int, as_of_date: str, window: int
    ) -> pd.DataFrame | None:
        """Return up to `window` starting appearances strictly before as_of_date."""
        pid = int(pitcher_id)
        if pid not in self._store:
            return None
        df = self._store[pid]
        cutoff = pd.to_datetime(as_of_date).date()
        prior = df[df["game_date"] < cutoff]
        if "is_start" in prior.columns:
            prior = prior[prior["is_start"] == 1]
        return prior.tail(window)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_era_l5(
        self,
        pitcher_id: int,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
    ) -> float | None:
        """ERA over the last `window` starts before as_of_date.

        Computed as (total ER / total IP) * 9, NOT mean of per-game ERA,
        to avoid division artifacts in short outings.
        """
        starts = self._prior_starts(pitcher_id, as_of_date, window)
        if starts is None or len(starts) < min_periods:
            return None
        return _era(float(starts["er"].sum()), float(starts["ip"].sum()))

    def get_k_per_9_l5(
        self,
        pitcher_id: int,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
    ) -> float | None:
        """K/9 over the last `window` starts before as_of_date."""
        starts = self._prior_starts(pitcher_id, as_of_date, window)
        if starts is None or len(starts) < min_periods:
            return None
        return _k_per_9(float(starts["k"].sum()), float(starts["ip"].sum()))

    def get_bb_per_9_l5(
        self,
        pitcher_id: int,
        as_of_date: str,
        window: int = DEFAULT_WINDOW,
        min_periods: int = MIN_PERIODS,
    ) -> float | None:
        """BB/9 over the last `window` starts before as_of_date."""
        starts = self._prior_starts(pitcher_id, as_of_date, window)
        if starts is None or len(starts) < min_periods:
            return None
        return _bb_per_9(float(starts["bb"].sum()), float(starts["ip"].sum()))

    # ------------------------------------------------------------------
    # Dunder / properties
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, pitcher_id: object) -> bool:
        try:
            return int(pitcher_id) in self._store
        except (TypeError, ValueError):
            return False

    @property
    def pitchers_loaded(self) -> list[int]:
        return sorted(self._store.keys())

    # ------------------------------------------------------------------
    # Cache serialization
    # ------------------------------------------------------------------

    def to_cache_dict(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for pid, df in self._store.items():
            records = df.copy()
            records["game_date"] = records["game_date"].astype(str)
            out[str(pid)] = records.to_dict("records")
        return out

    @classmethod
    def from_cache_dict(cls, cache: dict[str, list[dict[str, Any]]]) -> "MLBPitcherStatsStore":
        store = cls()
        for pid_str, records in cache.items():
            if not records:
                continue
            try:
                pid = int(pid_str)
            except (ValueError, TypeError):
                continue
            df = pd.DataFrame(records)
            if "game_date" in df.columns:
                df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
            store._store[pid] = df
        return store

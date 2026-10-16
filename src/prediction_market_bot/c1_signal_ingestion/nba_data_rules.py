"""Resolutions for the two W78.4 data findings on the NBA event store (W79.3).

1. Lineup-key repeats (~5.2% of rows). ``lineups_<season>`` is row-for-row aligned with ``pbp_<season>`` (same
   length, same game_id / action_number / period at every position, measured 2016/2019/2022/2025/2026), and the
   source assigns one ``action_number`` to paired events (a turnover and its steal; a miss and its rebound), so
   ``(game_id, action_number)`` is not a key. ``(game_id, action_number, occurrence)`` is: ``attach_order_index``
   joins it to pbp's unique ``order_index``. The repeats are not corruption and are not dropped.
2. Preseason and all-star games (5.4% = 811 of 14,979 schedule rows, 2016-2026) have no box score, officials or
   usable tip time. They are EXCLUDED, never silently used: ``eligible_games`` is the only legal game universe for
   any rolling feature or evaluation; ``game_quality`` is the audit table behind it.
"""
from __future__ import annotations

import pandas as pd

ANALYSIS_SEASON_TYPES = frozenset({"regular-season", "playoffs", "play-in", "nba-cup"})


def attach_order_index(lineups: pd.DataFrame, pbp: pd.DataFrame) -> pd.DataFrame:
    """Return lineups with pbp's ``order_index`` attached; raises if the two are not 1:1."""
    key = ["game_id", "action_number"]
    left = lineups.copy()
    right = pbp[key + ["order_index"]].copy()
    left["_occ"] = left.groupby(key).cumcount()
    right["_occ"] = right.groupby(key).cumcount()
    out = left.merge(right, on=key + ["_occ"], how="outer", indicator=True, validate="one_to_one")
    bad = int((out["_merge"] != "both").sum())
    if bad:
        raise ValueError(f"lineups and pbp are not 1:1 on (game_id, action_number, occurrence): {bad} unmatched rows")
    return out.drop(columns=["_occ", "_merge"])


def game_quality(schedule: pd.DataFrame, team_box: pd.DataFrame, officials: pd.DataFrame,
                 tips: pd.DataFrame) -> pd.DataFrame:
    """One row per scheduled game: what exists for it and whether it may be used."""
    q = schedule[["game_id", "season", "season_type"]].copy().set_index("game_id")
    q["has_box"] = q.index.isin(set(team_box["game_id"]))
    q["has_officials"] = q.index.isin(set(officials["game_id"]))
    q["tip_imputed"] = tips["tip_imputed"].reindex(q.index).fillna(True).astype(bool)
    q["eligible"] = q["season_type"].isin(ANALYSIS_SEASON_TYPES) & q["has_box"]
    return q


def eligible_games(quality: pd.DataFrame) -> set:
    return set(quality.index[quality["eligible"]])

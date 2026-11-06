"""Point-in-time pitcher and batter tables.

RULE: a row keyed (player, as_of_date) uses ONLY pitches with game_date STRICTLY BEFORE as_of_date.
Same-day games (doubleheaders) never feed each other. Built by aggregating each player's pitches to
(player, game_date) sums, cumulating, and shifting one row, so row t holds the sums of rows < t.

Applies: ranking / pricing a game from rolling skill as of the game date. Does not apply: anything that
needs the within-game state (that is the in-play layer, not this table).
Stage per ADR-0075: aggregated (pitch mix, velocity, whiff/chase, platoon split, contact/power).
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd


def _pa_rows(pa: pd.DataFrame) -> pd.DataFrame:
    d = pa.copy()
    d["woba_num"] = pd.to_numeric(d["woba_value"], errors="coerce").fillna(0.0)
    d["woba_den"] = pd.to_numeric(d["woba_denom"], errors="coerce").fillna(0.0)
    d["is_k"] = d["events"].isin(["strikeout", "strikeout_double_play"]).astype(float)
    d["is_bb"] = d["events"].isin(["walk", "intent_walk"]).astype(float)
    d["one"] = 1.0
    return d


def _cum_shift(df: pd.DataFrame, player: str, sum_cols: List[str]) -> pd.DataFrame:
    """df has one row per (player, game_date) with sum columns; return exclusive cumulative sums."""
    df = df.sort_values([player, "game_date"]).reset_index(drop=True)
    cs = df.groupby(player)[sum_cols].cumsum() - df[sum_cols]
    out = df[[player, "game_date"]].join(cs)
    return out


def pitcher_pit(p: pd.DataFrame, pa: pd.DataFrame) -> pd.DataFrame:
    """Pitcher as-of table. Columns: pitcher, game_date, counts and rates from strictly earlier dates."""
    q = p.copy()
    q["one"] = 1.0
    q["fb"] = q["is_fastball"].astype(float)
    q["fb_velo"] = np.where(q["is_fastball"], pd.to_numeric(q["release_speed"], errors="coerce"), np.nan)
    q["fb_velo_n"] = q["fb_velo"].notna().astype(float)
    q["fb_velo"] = q["fb_velo"].fillna(0.0)
    q["swing"] = q["is_swing"].astype(float)
    q["whiff"] = q["is_whiff"].astype(float)
    q["ooz"] = q["out_of_zone"].astype(float)
    q["ooz_swing"] = (q["out_of_zone"] & q["is_swing"]).astype(float)
    q["izone"] = q["in_zone"].astype(float)
    pcols = ["one", "fb", "fb_velo", "fb_velo_n", "swing", "whiff", "ooz", "ooz_swing", "izone"]
    pg = q.groupby(["pitcher", "game_date"], as_index=False)[pcols].sum()

    a = _pa_rows(pa)
    a["vsL"] = (a["stand"] == "L").astype(float)
    a["w_vsL"] = a["woba_num"] * a["vsL"]
    a["d_vsL"] = a["woba_den"] * a["vsL"]
    a["w_vsR"] = a["woba_num"] * (1 - a["vsL"])
    a["d_vsR"] = a["woba_den"] * (1 - a["vsL"])
    acols = ["one", "woba_num", "woba_den", "is_k", "is_bb", "w_vsL", "d_vsL", "w_vsR", "d_vsR"]
    ag = a.groupby(["pitcher", "game_date"], as_index=False)[acols].sum().rename(columns={"one": "bf"})
    acols = ["bf"] + acols[1:]

    # merge BEFORE cumulating: a player-date can sit in one table only (pitches thrown, no PA completed)
    m = _cum_shift(pg.merge(ag, on=["pitcher", "game_date"], how="outer").fillna(0.0), "pitcher", pcols + acols)
    out = m[["pitcher", "game_date"]].copy()
    out["n_pitches"] = m["one"]
    out["bf"] = m["bf"]
    out["fastball_share"] = m["fb"] / m["one"]
    out["fb_velo"] = m["fb_velo"] / m["fb_velo_n"]
    out["whiff_rate"] = m["whiff"] / m["swing"]
    out["chase_rate"] = m["ooz_swing"] / m["ooz"]
    out["zone_rate"] = m["izone"] / m["one"]
    out["k_rate"] = m["is_k"] / m["bf"]
    out["bb_rate"] = m["is_bb"] / m["bf"]
    out["woba_allowed"] = m["woba_num"] / m["woba_den"]
    out["woba_allowed_vsL"] = m["w_vsL"] / m["d_vsL"]
    out["woba_allowed_vsR"] = m["w_vsR"] / m["d_vsR"]
    out["woba_den"] = m["woba_den"]
    out["woba_num"] = m["woba_num"]
    return out.replace([np.inf, -np.inf], np.nan).reset_index(drop=True)


def batter_pit(p: pd.DataFrame, pa: pd.DataFrame) -> pd.DataFrame:
    """Batter as-of table: contact, power, platoon split, strictly earlier dates."""
    q = p.copy()
    q["swing"] = q["is_swing"].astype(float)
    q["whiff"] = q["is_whiff"].astype(float)
    q["ooz"] = q["out_of_zone"].astype(float)
    q["ooz_swing"] = (q["out_of_zone"] & q["is_swing"]).astype(float)
    ls = pd.to_numeric(q["launch_speed"], errors="coerce")
    q["bbe"] = ls.notna().astype(float)
    q["ls_sum"] = ls.fillna(0.0)
    q["hard"] = (ls >= 95).astype(float)
    pcols = ["swing", "whiff", "ooz", "ooz_swing", "bbe", "ls_sum", "hard"]
    pg = q.groupby(["batter", "game_date"], as_index=False)[pcols].sum()

    a = _pa_rows(pa)
    a["vsL"] = (a["p_throws"] == "L").astype(float)
    a["w_vsL"] = a["woba_num"] * a["vsL"]
    a["d_vsL"] = a["woba_den"] * a["vsL"]
    a["w_vsR"] = a["woba_num"] * (1 - a["vsL"])
    a["d_vsR"] = a["woba_den"] * (1 - a["vsL"])
    acols = ["one", "woba_num", "woba_den", "is_k", "is_bb", "w_vsL", "d_vsL", "w_vsR", "d_vsR"]
    ag = a.groupby(["batter", "game_date"], as_index=False)[acols].sum().rename(columns={"one": "pa"})
    acols = ["pa"] + acols[1:]

    m = _cum_shift(pg.merge(ag, on=["batter", "game_date"], how="outer").fillna(0.0), "batter", pcols + acols)
    out = m[["batter", "game_date"]].copy()
    out["pa"] = m["pa"]
    out["whiff_rate"] = m["whiff"] / m["swing"]
    out["chase_rate"] = m["ooz_swing"] / m["ooz"]
    out["k_rate"] = m["is_k"] / m["pa"]
    out["bb_rate"] = m["is_bb"] / m["pa"]
    out["avg_exit_velo"] = m["ls_sum"] / m["bbe"]
    out["hard_hit_rate"] = m["hard"] / m["bbe"]
    out["woba"] = m["woba_num"] / m["woba_den"]
    out["woba_vsL"] = m["w_vsL"] / m["d_vsL"]
    out["woba_vsR"] = m["w_vsR"] / m["d_vsR"]
    out["woba_den"] = m["woba_den"]
    out["woba_num"] = m["woba_num"]
    return out.replace([np.inf, -np.inf], np.nan).reset_index(drop=True)


def build_pit_tables(store, pitches: pd.DataFrame, pa: pd.DataFrame):
    """Compute both PIT tables and write them to <store>/tables/. Returns (pitcher_pit, batter_pit)."""
    from pathlib import Path
    out = Path(store) / "tables"
    out.mkdir(parents=True, exist_ok=True)
    pp, bp = pitcher_pit(pitches, pa), batter_pit(pitches, pa)
    pp.to_parquet(out / "pit_pitcher.parquet", index=False)
    bp.to_parquet(out / "pit_batter.parquet", index=False)
    return pp, bp

"""First two NBA factor classes, point-in-time (W79.3, ADR-0073/0075): pace + efficiency, and rest.

Possessions per team = FGA + 0.44*FTA - ORB + TOV; a game's possessions = mean of the two teams'. Pace is possessions
per 48 minutes (overtime-normalised from the team minutes); ortg / drtg are points per 100 possessions for / against.

As-of rule: a team's rolling value for game G uses only that team's same-season games whose
``tip_latest + COMPLETION_BUFFER <= tip_earliest(G)`` - the same predicate as ``PointInTime.completed_before``,
evaluated per team with a sorted prefix instead of a set so it is O(n log n) over 14k games.
Rest uses the schedule (public in advance): the Eastern date of the team's previous games in the same season.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .nba_point_in_time import COMPLETION_BUFFER

L10 = 10
MIN_GAMES = 10


def _minutes(col: pd.Series) -> pd.Series:
    return pd.to_numeric(col.astype(str).str.split(":").str[0], errors="coerce")


def team_game_table(schedule: pd.DataFrame, team_box: pd.DataFrame, tips: pd.DataFrame) -> pd.DataFrame:
    """One row per (game, team): pace, ortg, drtg, own/opp points, tips, Eastern date, side."""
    b = team_box.copy()
    b["game_id"] = b["game_id"].astype(str)
    b["poss"] = b["field_goals_attempted"] + 0.44 * b["free_throws_attempted"] - b["rebounds_offensive"] + b["turnovers"]
    b["mins"] = _minutes(b["minutes"])
    gp = b.groupby("game_id").agg(poss=("poss", "mean"), mins=("mins", "first"), n=("poss", "size"))
    gp = gp[gp["n"] == 2]
    b = b[b["game_id"].isin(gp.index)].copy()
    b["g_poss"] = b["game_id"].map(gp["poss"])
    b["g_mins"] = b["game_id"].map(gp["mins"])
    opp_pts = b.groupby("game_id")["points"].transform("sum") - b["points"]
    out = pd.DataFrame({
        "game_id": b["game_id"], "team_id": b["team_id"].astype(int), "side": b["side"],
        "pts": b["points"].astype(float), "opp_pts": opp_pts.astype(float),
        "pace": b["g_poss"] * 240.0 / b["g_mins"],
        "ortg": 100 * b["points"] / b["g_poss"], "drtg": 100 * opp_pts / b["g_poss"],
    })
    meta = tips[["season", "season_type", "game_date", "tip_earliest", "tip_latest", "tip_imputed"]]
    out = out.join(meta, on="game_id")
    out["date"] = pd.to_datetime(out["game_date"].astype(str))
    out["total"] = out["pts"] + out["opp_pts"]
    return out.reset_index(drop=True)


def rolling_asof(tg: pd.DataFrame, cols=("pace", "ortg", "drtg", "total")) -> pd.DataFrame:
    """Add ``<c>_ytd`` (season-to-date mean over prior completed games), ``<c>_l10`` (last 10) and ``n_prior``.

    NaN where fewer than MIN_GAMES prior completed games (l10 needs 10)."""
    tg = tg.sort_values(["team_id", "season", "tip_latest"]).reset_index(drop=True)
    res = {f"{c}_{s}": np.full(len(tg), np.nan) for c in cols for s in ("ytd", "l10")}
    nprior = np.zeros(len(tg), dtype=int)
    for _, idx in tg.groupby(["team_id", "season"]).indices.items():
        sub = tg.iloc[idx]
        comp = (sub["tip_latest"] + COMPLETION_BUFFER).to_numpy(dtype="datetime64[ns]")
        cut = sub["tip_earliest"].to_numpy(dtype="datetime64[ns]")
        k = np.searchsorted(comp, cut, side="right")  # comp is sorted: prior games form a prefix
        nprior[idx] = k
        for c in cols:
            cs = np.concatenate([[0.0], np.cumsum(sub[c].to_numpy(dtype=float))])
            with np.errstate(invalid="ignore", divide="ignore"):
                ytd = np.where(k >= MIN_GAMES, cs[k] / np.maximum(k, 1), np.nan)
                kk = np.maximum(k - L10, 0)
                l10 = np.where(k >= L10, (cs[k] - cs[kk]) / L10, np.nan)
            res[f"{c}_ytd"][idx] = ytd
            res[f"{c}_l10"][idx] = l10
    out = tg.copy()
    for name, v in res.items():
        out[name] = v
    out["n_prior"] = nprior
    return out


def rest_features(tg: pd.DataFrame) -> pd.DataFrame:
    """Add rest_days (0 = back-to-back; NaN for a season's first game), b2b, three_in_four, g_last7 per team-game."""
    tg = tg.sort_values(["team_id", "season", "date", "tip_latest"]).reset_index(drop=True)
    d = tg.groupby(["team_id", "season"])["date"]
    prev1, prev2 = d.shift(1), d.shift(2)
    tg["rest_days"] = (tg["date"] - prev1).dt.days - 1
    tg["b2b"] = (tg["rest_days"] == 0).astype(float).where(tg["rest_days"].notna())
    tg["three_in_four"] = ((tg["date"] - prev2).dt.days <= 3).astype(float).where(prev2.notna(), 0.0)
    cnt = np.zeros(len(tg))
    for _, idx in tg.groupby(["team_id", "season"]).indices.items():
        dd = tg["date"].iloc[idx].to_numpy(dtype="datetime64[D]").astype(np.int64)
        lo = np.searchsorted(dd, dd - 7, side="left")  # games on dates in [d-7, d-1]
        hi = np.searchsorted(dd, dd, side="left")
        cnt[idx] = hi - lo
    tg["g_last7"] = cnt
    return tg


def game_frame(tg: pd.DataFrame, feats: list) -> pd.DataFrame:
    """Pivot team-game rows to one row per game: ``h_<f>`` / ``a_<f>`` plus margin and total."""
    h = tg[tg["side"] == "home"].set_index("game_id")
    a = tg[tg["side"] == "away"].set_index("game_id")
    g = pd.DataFrame(index=h.index.intersection(a.index))
    for f in feats:
        g[f"h_{f}"], g[f"a_{f}"] = h[f].reindex(g.index), a[f].reindex(g.index)
    g["margin"] = h["pts"].reindex(g.index) - a["pts"].reindex(g.index)
    g["total"] = h["pts"].reindex(g.index) + a["pts"].reindex(g.index)
    g["season"] = h["season"].reindex(g.index)
    g["season_type"] = h["season_type"].reindex(g.index)
    return g

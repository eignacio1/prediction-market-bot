"""As-of team ratings with previous-season shrinkage (W93.3).

Rating for (team, game G) = (sum of the team's same-season games completed before G + K * prior) / (n + K), where
"completed before G" is the existing predicate ``tip_latest + COMPLETION_BUFFER <= tip_earliest(G)`` (nba_factors).
``prior`` is the team's previous-season full-season mean, else that season's league mean. Applies from game 1 of a season.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import COMPLETION_BUFFER

STATS = ("pace", "ortg", "drtg")


def prior_table(tg: pd.DataFrame, stats=STATS) -> pd.DataFrame:
    """(team_id, season) -> previous season's full mean of each stat; league mean of the previous season as fallback."""
    full = tg.groupby(["team_id", "season"])[list(stats)].mean()
    league = tg.groupby("season")[list(stats)].mean()
    return full, league


def add_ratings(tg: pd.DataFrame, k: float = 20.0, stats=STATS) -> pd.DataFrame:
    """Add ``<stat>_hat`` per team-game. Seasons with no previous season in ``tg`` get NaN (cannot be priced)."""
    full, league = prior_table(tg, stats)
    tg = tg.sort_values(["team_id", "season", "tip_latest"]).reset_index(drop=True)
    out = {f"{c}_hat": np.full(len(tg), np.nan) for c in stats}
    nprior = np.zeros(len(tg), dtype=int)
    seasons = set(league.index)
    for (team, season), idx in tg.groupby(["team_id", "season"]).indices.items():
        prev = season - 1
        if prev not in seasons:
            continue
        sub = tg.iloc[idx]
        comp = (sub["tip_latest"] + COMPLETION_BUFFER).to_numpy(dtype="datetime64[ns]")
        cut = sub["tip_earliest"].to_numpy(dtype="datetime64[ns]")
        order = np.argsort(comp, kind="stable")
        kk = np.searchsorted(comp[order], cut, side="right")  # prior games form a prefix of the completion order
        nprior[idx] = kk
        for c in stats:
            prior = full[c].get((team, prev), league[c].get(prev))
            vals = sub[c].to_numpy(dtype=float)[order]
            cs = np.concatenate([[0.0], np.cumsum(vals)])
            out[f"{c}_hat"][idx] = (cs[kk] + k * prior) / (kk + k)
    res = tg.copy()
    for name, v in out.items():
        res[name] = v
    res["n_prior"] = nprior
    return res


def game_inputs(tg: pd.DataFrame) -> pd.DataFrame:
    """One row per game: engine means from as-of ratings plus the realised scores (scores are labels only)."""
    h = tg[tg["side"] == "home"].set_index("game_id")
    a = tg[tg["side"] == "away"].set_index("game_id")
    g = pd.DataFrame(index=h.index.intersection(a.index))
    g["mu_poss"] = (h["pace_hat"].reindex(g.index) + a["pace_hat"].reindex(g.index)) / 2
    g["ppp_h"] = (h["ortg_hat"].reindex(g.index) + a["drtg_hat"].reindex(g.index)) / 2
    g["ppp_a"] = (a["ortg_hat"].reindex(g.index) + h["drtg_hat"].reindex(g.index)) / 2
    g["home_pts"], g["away_pts"] = h["pts"].reindex(g.index), a["pts"].reindex(g.index)
    g["season"], g["season_type"] = h["season"].reindex(g.index), h["season_type"].reindex(g.index)
    g["home_team"], g["away_team"] = h["team_id"].reindex(g.index), a["team_id"].reindex(g.index)
    g["tip_earliest"] = h["tip_earliest"].reindex(g.index)
    g["n_prior_h"], g["n_prior_a"] = h["n_prior"].reindex(g.index), a["n_prior"].reindex(g.index)
    return g.dropna(subset=["mu_poss", "ppp_h", "ppp_a"])

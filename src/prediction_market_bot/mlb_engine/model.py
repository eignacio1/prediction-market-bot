"""Minimal team-level game model from the point-in-time tables (W105.3 Part C, descriptive only).

Applies: a first-pass price for moneyline / total from starter + lineup skill as of the game date.
Does not apply: bullpen, park, weather, platoon matchup, within-game state. Those are the next factor classes.
Stage per ADR-0075: pitch-level facts aggregated (PIT tables) and applied here through a thin run model.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor

PRIOR_PA = 200.0  # shrinkage weight (plate appearances / batters faced) toward the league mean


def _shrunk(num: pd.Series, den: pd.Series, mu: float, k: float = PRIOR_PA) -> pd.Series:
    return (num.fillna(0.0) + k * mu) / (den.fillna(0.0) + k)


def design(games: pd.DataFrame, lineups: pd.DataFrame, bp: pd.DataFrame, pp: pd.DataFrame,
           mu_bat: float, mu_pit: float) -> pd.DataFrame:
    """One row per (game, batting side): shrunk lineup wOBA, opposing starter wOBA-allowed, runs scored."""
    b = bp[["batter", "game_date", "woba_num", "woba_den"]]
    lu = lineups.merge(games[["game_pk", "game_date"]], on="game_pk").merge(b, on=["batter", "game_date"], how="left")
    lu["w"] = _shrunk(lu["woba_num"], lu["woba_den"], mu_bat)
    team = lu.groupby(["game_pk", "team_side"], as_index=False).agg(lineup_woba=("w", "mean"), n_bat=("w", "size"))
    p = pp[["pitcher", "game_date", "woba_num", "woba_den"]]
    rows = []
    for side, opp_starter, runs in (("away", "home_starter", "away_runs"), ("home", "away_starter", "home_runs")):
        g = games[["game_pk", "game_date", opp_starter, runs]].rename(columns={opp_starter: "pitcher", runs: "runs"})
        g = g.merge(p, on=["pitcher", "game_date"], how="left")
        g["starter_woba_allowed"] = _shrunk(g["woba_num"], g["woba_den"], mu_pit)
        g["team_side"] = side
        rows.append(g[["game_pk", "game_date", "team_side", "starter_woba_allowed", "runs"]])
    out = pd.concat(rows).merge(team, on=["game_pk", "team_side"], how="inner")
    out["is_home"] = (out["team_side"] == "home").astype(float)
    return out[out["n_bat"] >= 9].reset_index(drop=True)


FEATURES = ["lineup_woba", "starter_woba_allowed", "is_home"]


def fit(train: pd.DataFrame, alpha: float = 1e-3) -> PoissonRegressor:
    m = PoissonRegressor(alpha=alpha, max_iter=500)
    m.fit(train[FEATURES].to_numpy(), train["runs"].to_numpy())
    return m


def _win_prob(lh: np.ndarray, la: np.ndarray, kmax: int = 25) -> np.ndarray:
    k = np.arange(kmax + 1)
    ph = poisson.pmf(k[None, :], lh[:, None])
    pa = poisson.pmf(k[None, :], la[:, None])
    cum_a = np.cumsum(pa, axis=1)
    win = (ph[:, 1:] * cum_a[:, :-1]).sum(axis=1)
    tie = (ph * pa).sum(axis=1)
    return win + 0.5 * tie  # extra innings split evenly


def predict(model: PoissonRegressor, games: pd.DataFrame, d: pd.DataFrame, line: float = 8.5) -> pd.DataFrame:
    d = d.copy()
    d["lam"] = model.predict(d[FEATURES].to_numpy())
    h = d[d.team_side == "home"].set_index("game_pk")["lam"].rename("lam_home")
    a = d[d.team_side == "away"].set_index("game_pk")["lam"].rename("lam_away")
    g = games.set_index("game_pk").join(h, how="inner").join(a, how="inner").dropna(subset=["lam_home", "lam_away"])
    g["p_home"] = _win_prob(g["lam_home"].to_numpy(), g["lam_away"].to_numpy())
    g["p_over"] = poisson.sf(np.floor(line), (g["lam_home"] + g["lam_away"]).to_numpy())  # P(total >= ceil(line))
    g["home_win"] = (g["home_runs"] > g["away_runs"]).astype(float)
    g["over"] = ((g["home_runs"] + g["away_runs"]) > line).astype(float)
    return g.reset_index()


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def boot_diff(p_model: np.ndarray, p_base: np.ndarray, y: np.ndarray, n: int = 2000, seed: int = 7) -> Tuple[float, float, float]:
    """Brier(base) - Brier(model) with a 95% game-level bootstrap interval; positive = model better."""
    rng = np.random.default_rng(seed)
    e = (p_base - y) ** 2 - (p_model - y) ** 2
    idx = rng.integers(0, len(e), size=(n, len(e)))
    bs = e[idx].mean(axis=1)
    return float(e.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

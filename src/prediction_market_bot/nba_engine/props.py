"""NBA engine player props (W109.3, B-070): player points / rebounds / assists / threes priced from the engine's draws.

One game draw = (home_pts, away_pts) from the engine (v1/v2/v3 ``simulate``). Points: the team's points in that draw are
split over the players with ``player_layer.draw_split`` (players + "rest" bucket sum exactly to the team's points).
Other stats: a team total for the stat is drawn *in the same draw*, coupled to the draw's team points by an elasticity
``beta`` (E[stat | pts] = mean * (pts / mean_pts) ** beta; threes and assists move with points, rebounds barely do) with
negative-binomial noise, then split over the players the same way, so a player's rebounds can never exceed the team's.
New module: the engine core is untouched, nothing imports this from a service. Offline / shadow use only.

When it applies: pre-game, with per-player expected stats (``mu``) from trailing box scores and the engine's team
points distribution. It does not model who plays: the caller passes the expected-minutes-weighted ``mu`` (0 for out).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from prediction_market_bot.nba_engine import player_layer as PL

STATS = ("points", "rebounds", "assists", "threes")
# Elasticity of a team's stat total to the team's points in the same game (defaults; refit with ``fit_beta``).
DEFAULT_BETA = {"points": 1.0, "rebounds": -0.25, "assists": 0.8, "threes": 1.2}
# Negative-binomial dispersion of the team stat total around its conditional mean (var = m + m^2/r).
DEFAULT_R = {"rebounds": 60.0, "assists": 90.0, "threes": 45.0}
DEFAULT_REST = {"points": 0.08, "rebounds": 0.08, "assists": 0.08, "threes": 0.08}
DEFAULT_CONC = {"points": 60.0, "rebounds": 60.0, "assists": 45.0, "threes": 25.0}


@dataclass(frozen=True)
class TeamRoster:
    """Expected per-game stat of each player (``mu[stat]`` aligned with ``players``) and the team's mean points."""
    players: tuple[str, ...]
    mu: Mapping[str, Sequence[float]]
    team_mean_pts: float


def fit_beta(team_pts: np.ndarray, team_stat: np.ndarray) -> float:
    """Slope of log(stat) on log(points) across team-games (the elasticity)."""
    x = np.log(np.maximum(np.asarray(team_pts, float), 1.0))
    y = np.log(np.maximum(np.asarray(team_stat, float), 1.0))
    return float(np.polyfit(x, y, 1)[0])


def _team_stat_total(pts: np.ndarray, mean_total: float, mean_pts: float, beta: float, r: float,
                     rng: np.random.Generator) -> np.ndarray:
    m = mean_total * (np.maximum(pts, 1) / mean_pts) ** beta
    lam = rng.gamma(r, m / r)                          # gamma-Poisson = negative binomial with mean m
    return rng.poisson(lam).astype(np.int64)


def player_draws(pts: np.ndarray, roster: TeamRoster, stat: str, rng: np.random.Generator,
                 beta: Mapping[str, float] = DEFAULT_BETA, r: Mapping[str, float] = DEFAULT_R,
                 rest: Mapping[str, float] = DEFAULT_REST, conc: Mapping[str, float] = DEFAULT_CONC):
    """(n, k+1) draws of each player's ``stat`` (last column = rest bucket) and the (n,) team total they sum to."""
    mu = np.asarray(roster.mu[stat], float)
    shares = PL.shares_from_means(mu, rest[stat])
    if stat == "points":
        total = np.asarray(pts, np.int64)
    else:
        mean_total = float(mu.sum() / (1.0 - rest[stat]))
        total = _team_stat_total(np.asarray(pts, float), mean_total, roster.team_mean_pts, beta[stat], r[stat], rng)
    return PL.draw_split(total, shares, conc[stat], rng), total


def strike_probs(draws: np.ndarray, strikes: Sequence[int]) -> dict[int, float]:
    """P(stat >= k) for one player's draws, for each strike (half-count prior; monotone non-increasing in k)."""
    return {int(k): PL.p_at_least(draws, int(k)) for k in strikes}


def price_game(home_pts: np.ndarray, away_pts: np.ndarray, home: TeamRoster, away: TeamRoster,
               strikes: Mapping[str, Sequence[int]], seed: int = 0, **kw) -> dict[str, dict[str, dict[int, float]]]:
    """{stat: {player: {strike: P(stat >= strike)}}} for both rosters from the same engine draws."""
    rng = np.random.default_rng(seed)
    out: dict[str, dict[str, dict[int, float]]] = {s: {} for s in STATS}
    for roster, pts in ((home, home_pts), (away, away_pts)):
        for stat in STATS:
            d, _ = player_draws(pts, roster, stat, rng, **kw)
            for i, name in enumerate(roster.players):
                out[stat][name] = strike_probs(d[:, i], strikes[stat])
    return out

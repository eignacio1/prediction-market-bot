"""NBA engine player layer (W96.1 Part C, B-009): player points drawn jointly with the team score.

A team's points T come from the engine's team distribution; the players' points are a Dirichlet-multinomial split of T
over the players' expected shares plus a "rest" bucket, so the players' points always add up to the team's.
New module; v1/v2/v3 are untouched. Offline/research use only: nothing imports this from a service.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.special import gammaln


def shares_from_means(mu: Sequence[float], rest_share: float) -> np.ndarray:
    """Expected share of team points per player (len k) plus the rest bucket (last entry); sums to 1."""
    mu = np.maximum(np.asarray(mu, float), 1e-6)
    return np.append((1.0 - rest_share) * mu / mu.sum(), rest_share)


def draw_split(team_pts: np.ndarray, shares: np.ndarray, conc: float, rng: np.random.Generator) -> np.ndarray:
    """(n, k+1) integer player points per draw; rows sum exactly to ``team_pts`` (n,). Smaller ``conc`` = more
    game-to-game variation in who scores."""
    n = len(team_pts)
    g = rng.gamma(np.maximum(conc * shares, 1e-9), size=(n, len(shares)))
    w = g / g.sum(axis=1, keepdims=True)
    out = np.empty((n, len(shares)), dtype=np.int64)
    for i in range(n):
        out[i] = rng.multinomial(int(team_pts[i]), w[i])
    return out


def _betabin_ll(y: np.ndarray, T: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (gammaln(T + 1) - gammaln(y + 1) - gammaln(T - y + 1) + gammaln(y + a) + gammaln(T - y + b) - gammaln(T + a + b)
            + gammaln(a + b) - gammaln(a) - gammaln(b))


def fit_concentration(y: np.ndarray, team_pts: np.ndarray, share: np.ndarray,
                      grid: Sequence[float] = tuple(np.exp(np.linspace(np.log(5.0), np.log(2000.0), 50)))) -> float:
    """Maximum-likelihood concentration from observed player points ``y`` given team points and the player's expected
    share (each player-game's marginal is beta-binomial(T, c*s, c*(1-s)))."""
    y, T, s = (np.asarray(v, float) for v in (y, team_pts, share))
    s = np.clip(s, 1e-4, 1 - 1e-4)
    best = max(grid, key=lambda c: float(_betabin_ll(y, T, c * s, c * (1 - s)).sum()))
    return float(best)


def p_at_least(player_draws: np.ndarray, k: int) -> float:
    """P(points >= k) from simulation draws, with a half-count prior so it never reaches 0 or 1."""
    return float((np.sum(player_draws >= k) + 0.5) / (len(player_draws) + 1.0))

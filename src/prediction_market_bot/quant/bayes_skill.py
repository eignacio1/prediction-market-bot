"""Bayesian skill weight (W94.Q Part C): a posterior on a model's paired Brier advantage over the market.

Advantage d = Brier(market) - Brier(model) per game (positive = the model beats the market), game-clustered.
Normal-normal conjugate: prior d ~ N(prior_mean, tau^2), likelihood mean(d) ~ N(d, se^2).

PRIOR WIDTH. tau = 0.005 Brier units (DEFAULT_TAU). A pregame model against a liquid game-winner market: the
observed advantages on our four scored frozen models sit in [-0.015, +0.0004] (W88.3, W86.1), the market Brier is ~0.19-0.24,
so tau=0.005 says "a genuine edge worth more than ~0.010 Brier (about 5% of the market's score) is a 2-sigma surprise".
Centred on 0: the market is presumed efficient until the rows say otherwise (the efficiency-gradient position in CLAUDE.md).

WEIGHT. weight = max(0, posterior_mean) / brier_market, clipped to [0, 1]: the posterior mean of the same Brier-skill
quantity the accepted gate already uses (1 - Bm/Bk = d/Bk), shrunk by the data's own noise. Why not P(d > 0): under a
null model P(d>0) is uniform on (0,1) at every n (it never settles), so a weight built on it drifts up and down with n;
the posterior mean converges to the truth, so a null model's weight goes to 0 as n grows and a real edge's rises.
P(d > 0) is reported alongside, not used.

Applies to paired per-game binary forecasts with game clusters (use games, not rows, as n). Does not apply to serially
correlated in-play rows, to n < ~30 games (the normal approximation for the mean), or to a prior that is not meant to
be centred on zero (pass prior_mean/tau explicitly for a forward update from a held-out posterior).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Mapping, Optional, Sequence

_N = NormalDist()
DEFAULT_TAU = 0.005


@dataclass(frozen=True)
class SkillPosterior:
    n: int
    mean: float          # posterior mean of the advantage
    sd: float            # posterior sd
    lo: float            # 95% credible interval
    hi: float
    p_positive: float    # P(advantage > 0)
    weight: float        # see module docstring
    prior_mean: float
    tau: float


def posterior_from_summary(mean: float, se: float, n: int, brier_market: float, tau: float = DEFAULT_TAU,
                           prior_mean: float = 0.0) -> SkillPosterior:
    """Posterior from a sample mean advantage and its (game-clustered) standard error."""
    if n <= 0 or not se > 0:
        return SkillPosterior(0, prior_mean, tau, prior_mean - 1.96 * tau, prior_mean + 1.96 * tau,
                              0.5 if prior_mean == 0 else 1 - _N.cdf((0 - prior_mean) / tau),
                              0.0, prior_mean, tau)
    prec = 1 / tau ** 2 + 1 / se ** 2
    pm = (prior_mean / tau ** 2 + mean / se ** 2) / prec
    psd = math.sqrt(1 / prec)
    z = _N.inv_cdf(0.975)
    w = min(1.0, max(0.0, pm) / brier_market) if brier_market > 0 else 0.0
    return SkillPosterior(n, pm, psd, pm - z * psd, pm + z * psd, 1 - _N.cdf((0 - pm) / psd), w, prior_mean, tau)


def posterior(adv_by_game: Mapping[str, Sequence[float]], brier_market: float, tau: float = DEFAULT_TAU,
              prior_mean: float = 0.0) -> SkillPosterior:
    """Posterior from per-row advantages grouped by game; each game is one unit (its mean), so rows in a game
    do not inflate n. The standard error is the sample sd of game means over sqrt(games)."""
    g = [sum(v) / len(v) for v in adv_by_game.values() if len(v)]
    n = len(g)
    if n < 2:
        return posterior_from_summary(0.0, 0.0, 0, brier_market, tau, prior_mean)
    m = sum(g) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in g) / (n - 1))
    return posterior_from_summary(m, sd / math.sqrt(n), n, brier_market, tau, prior_mean)


def update(prior: SkillPosterior, new_adv_by_game: Mapping[str, Sequence[float]], brier_market: float) -> SkillPosterior:
    """Forward update: yesterday's posterior becomes today's prior, new (forward) games are the likelihood.
    Applies only when the new games are disjoint from those already in `prior` (no game counted twice)."""
    p = posterior(new_adv_by_game, brier_market, tau=prior.sd, prior_mean=prior.mean)
    return SkillPosterior(prior.n + p.n, p.mean, p.sd, p.lo, p.hi, p.p_positive, p.weight, prior.prior_mean, prior.tau)


def n_for_weight(mean: float, sd_game: float, brier_market: float, threshold: float,
                 tau: float = DEFAULT_TAU) -> Optional[float]:
    """Games needed for the posterior-mean weight to reach `threshold` if the observed `mean` advantage held with
    per-game sd `sd_game`. Closed form of  mean * tau^2 / (tau^2 + sd^2/n) = threshold * brier_market.
    None when mean <= threshold * brier_market (the weight's ceiling at that mean is below the threshold: never)."""
    target = threshold * brier_market
    if mean <= target or sd_game <= 0:
        return None
    return sd_game ** 2 / (tau ** 2 * (mean / target - 1))

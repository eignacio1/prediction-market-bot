"""Always-valid evidence for "this node's net is > 0": a mixture likelihood-ratio e-process, one per tree node per arm.

At look k a node has an increment (mean ybar_k of the rows that settled since the last look, game-clustered variance
s_k^2). The e-value of the increment is the likelihood ratio against net = 0, averaged over a prior on net > 0 that was
fixed BEFORE the increment was seen (the node's pooled posterior from all earlier looks, cut at 0):

    E_k = integral_{theta>0} N(ybar_k; theta, s_k^2) / N(ybar_k; 0, s_k^2) dPi_{k-1}(theta),   E = prod_k E_k.

Under any true net <= 0, E is a non-negative supermartingale started at 1, so P(E ever >= 1/alpha) <= alpha (Ville):
the error does not grow with the number of looks, and stopping or continuing at will is allowed. The prior only changes
power, never validity -- which is where pooling and the long-history prior come in.

When it applies: increments on disjoint games (looks are cut by game start), means near normal with a usable variance
(>= min games per increment; moderated variance). When it doesn't: a prior that has seen the increment it scores, or an
increment of two or three games where the plug-in variance is itself noise -- those are carried to the next look.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from prediction_market_bot.decision_trees.evidence.model import log_norm_cdf


def log_e_increment(ybar: float, se2: float, m: float, v: float) -> float:
    """log E_k for one increment (ybar, se2) under the prior N(m, v) truncated to theta > 0."""
    p = 1.0 / v + 1.0 / se2
    mu = (m / v + ybar / se2) / p
    return (-0.5 * math.log(p * v) + 0.5 * mu * mu * p - 0.5 * m * m / v
            + log_norm_cdf(mu * math.sqrt(p)) - log_norm_cdf(m / math.sqrt(v)))


def e_path(increments: Sequence[Tuple[float, float]], priors: Sequence[Tuple[float, float]]) -> List[float]:
    """Running log E after each increment; priors[k] must not depend on increments[k:]."""
    out, tot = [], 0.0
    for (y, s2), (m, v) in zip(increments, priors):
        tot += log_e_increment(y, s2, m, v)
        out.append(tot)
    return out


def crossed(log_e_running: Sequence[float], alpha: float = 0.10) -> bool:
    """True when the e-process has ever reached 1/alpha (the claim stands once made; Ville bounds the supremum)."""
    return bool(log_e_running) and max(log_e_running) >= math.log(1.0 / alpha)

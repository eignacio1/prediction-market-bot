"""Same-game joint probabilities from ONE set of simulation draws (W110.4, B-072, ADR-0073 parlay groundwork).

A *leg* is a boolean array over the draws of a single game (draw i is one simulated game: team scores, and every
player's stat from the same draw index). Because every leg of a game reads the same draws, the joint probability of any
set of legs is just the share of draws where all are true, and a single leg's joint reproduces its marginal exactly.
Dependence is therefore whatever the engine's draws carry - it is an OUTPUT, never an input.

WHEN IT APPLIES: legs built from draws that share one index (e.g. ``nba_engine.engine_v2.simulate`` scores plus
``nba_engine.props.player_draws`` computed from those same scores). Legs from different draw sets are NOT comparable and
the functions refuse unequal lengths. WHEN IT DOES NOT: a joint is only as good as the draws' dependence; Monte Carlo
error is ~sqrt(p(1-p)/n) (``mc_se``), so tiny joints (< 5/n) are not resolved and are flagged by ``resolved``.
Prices, fees and costs are NOT here (``quant/money.py``, ``quant/costs.py``).
"""
from __future__ import annotations

import numpy as np


def leg(x, op: str, k: float) -> np.ndarray:
    """Boolean leg ``x >= k`` (op 'ge') or ``x <= k`` (op 'le') over the draws."""
    x = np.asarray(x)
    if op == "ge":
        return x >= k
    if op == "le":
        return x <= k
    raise ValueError(f"op must be 'ge' or 'le', got {op!r}")


def _stack(legs) -> np.ndarray:
    arrs = [np.asarray(l, bool) for l in legs]
    if not arrs:
        raise ValueError("need at least one leg")
    if len({a.shape for a in arrs}) != 1 or arrs[0].ndim != 1:
        raise ValueError("legs must be 1-d boolean arrays over the same draws")
    return np.vstack(arrs)


def marginal(a) -> float:
    return float(np.mean(np.asarray(a, bool)))


def joint(*legs) -> float:
    """P(all legs true) from the shared draws (works for 1, 2, 3, ... legs)."""
    return float(np.mean(_stack(legs).all(axis=0)))


def independent(*legs) -> float:
    """Product of the legs' own marginals - the naive parlay price on the same engine."""
    return float(np.prod(_stack(legs).mean(axis=1)))


def mc_se(p: float, n: int) -> float:
    return float(np.sqrt(max(p * (1.0 - p), 0.0) / n))


def resolved(p: float, n: int, min_hits: int = 5) -> bool:
    """True when at least ``min_hits`` draws (and as many misses) back the probability."""
    return p * n >= min_hits and (1.0 - p) * n >= min_hits


def lift(a, b) -> float:
    """P(A and B) / (P(A) P(B)); 1 = independent, nan if either leg never happens."""
    pa, pb = marginal(a), marginal(b)
    return float(joint(a, b) / (pa * pb)) if pa > 0 and pb > 0 else float("nan")


def phi(a, b) -> float:
    """Implied correlation of the two legs' 0/1 indicators (the phi coefficient); nan if either is constant."""
    pa, pb = marginal(a), marginal(b)
    d = np.sqrt(pa * (1 - pa) * pb * (1 - pb))
    return float((joint(a, b) - pa * pb) / d) if d > 0 else float("nan")


def frechet_bounds(*legs) -> tuple[float, float]:
    """Hard limits any joint must respect given the marginals: [max(0, sum p - (k-1)), min p]."""
    p = _stack(legs).mean(axis=1)
    return float(max(0.0, p.sum() - (len(p) - 1))), float(p.min())


def excess(a, b) -> float:
    """Dependence in probability units: P(A and B) - P(A) P(B)."""
    return joint(a, b) - independent(a, b)

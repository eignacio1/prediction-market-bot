"""Multiplicity tools: Holm, Benjamini-Hochberg, alpha spending for repeated looks.

Descriptive aids only. They never change a pre-registered rule or verdict.
"""
from __future__ import annotations

import math
import random
from typing import Sequence


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _phi_inv(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if _phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def one_sided_p(z: float) -> float:
    return 1.0 - _phi(z)


def holm(pvals: Sequence[float], alpha: float = 0.05) -> list[dict]:
    """Holm step-down. Returns per input: adjusted p (monotone, capped at 1) and reject."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[i]))
        adj[i] = run
    return [{"p": pvals[i], "p_adj": adj[i], "reject": adj[i] <= alpha} for i in range(m)]


def benjamini_hochberg(pvals: Sequence[float], q: float = 0.10) -> list[dict]:
    """BH step-up. Returns per input: adjusted p (q-value) and reject at level q."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i], reverse=True)
    adj = [0.0] * m
    run = 1.0
    for k, i in enumerate(order):
        rank = m - k
        run = min(run, pvals[i] * m / rank)
        adj[i] = min(1.0, run)
    return [{"p": pvals[i], "q": adj[i], "reject": adj[i] <= q} for i in range(m)]


def spend_obrien_fleming(t: float, alpha: float = 0.05) -> float:
    """Lan-DeMets O'Brien-Fleming-type cumulative one-sided alpha spent at information fraction t."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return alpha
    return 2.0 - 2.0 * _phi(_phi_inv(1.0 - alpha / 2.0) / math.sqrt(t))


def spend_pocock(t: float, alpha: float = 0.05) -> float:
    """Lan-DeMets Pocock-type cumulative alpha spent at information fraction t."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return alpha
    return alpha * math.log(1.0 + (math.e - 1.0) * t)


def repeated_look_false_positive(k_looks: int, z_crit: float = 1.645, reps: int = 20000,
                                 seed: int = 11) -> float:
    """Null probability that a standardized running mean exceeds z_crit at ANY of k equally
    spaced looks (Brownian-motion partial sums). One look returns ~ one_sided_p(z_crit)."""
    rng = random.Random(seed)
    hits = 0
    for _ in range(reps):
        s = 0.0
        for j in range(1, k_looks + 1):
            s += rng.gauss(0.0, 1.0)
            if s / math.sqrt(j) > z_crit:
                hits += 1
                break
    return hits / reps


def boundary_pocock_z(k_looks: int, alpha: float = 0.05, reps: int = 8000, seed: int = 5) -> float:
    """Constant z boundary keeping family-wise one-sided alpha over k equally spaced looks."""
    rng = random.Random(seed)
    maxes = []
    for _ in range(reps):
        s = 0.0
        m = -1e9
        for j in range(1, k_looks + 1):
            s += rng.gauss(0.0, 1.0)
            m = max(m, s / math.sqrt(j))
        maxes.append(m)
    maxes.sort()
    return maxes[int((1 - alpha) * (reps - 1))]

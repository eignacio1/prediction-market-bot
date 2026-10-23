"""Inference: game-clustered bootstrap, power/MDE, multiplicity, and one pooled clustered test."""
from __future__ import annotations

import math
import random
from statistics import NormalDist
from typing import Mapping, Sequence

_N = NormalDist()


def cluster_bootstrap(vals_by_cluster: Mapping[str, Sequence[float]], b: int = 2000, seed: int = 20261002,
                      alpha: float = 0.05) -> tuple[float, float, float]:
    """Mean of all row values with whole-cluster resampling -> (mean, lo, hi) percentile interval.
    Applies when rows within a cluster (a game's strikes) are dependent and clusters are independent; with < ~15
    clusters the percentile interval undercovers. Same algorithm/seed as pregame_shadow.scoring for reconciliation."""
    keys = list(vals_by_cluster)
    if not keys:
        return (float("nan"),) * 3
    allv = [v for k in keys for v in vals_by_cluster[k]]
    mean = sum(allv) / len(allv)
    rng = random.Random(seed)
    means = []
    for _ in range(b):
        s = n = 0.0
        for _ in keys:
            c = vals_by_cluster[keys[rng.randrange(len(keys))]]
            s += sum(c); n += len(c)
        means.append(s / n)
    means.sort()
    return mean, means[int(alpha / 2 * b)], means[int((1 - alpha / 2) * b) - 1]


def power_paired(effect: float, sd: float, n: int, alpha: float = 0.05) -> float:
    """Power of a one-sided z-test that a paired mean difference > 0, true mean `effect`, per-unit sd, n units.
    Applies to independent units (use games, not rows, as n) and a roughly normal mean (n >~ 30)."""
    if n <= 0 or sd <= 0:
        return float("nan")
    return 1 - _N.cdf(_N.inv_cdf(1 - alpha) - effect * math.sqrt(n) / sd)


def mde_paired(sd: float, n: int, alpha: float = 0.05, power: float = 0.8) -> float:
    """Minimum detectable true paired-mean difference at (alpha one-sided, power) for n independent units."""
    return (_N.inv_cdf(1 - alpha) + _N.inv_cdf(power)) * sd / math.sqrt(n)


def bonferroni(pvals: Sequence[float], alpha: float = 0.05) -> list[bool]:
    """Reject flags controlling family-wise error at alpha. Valid under any dependence; conservative for many tests."""
    m = len(pvals)
    return [p <= alpha / m for p in pvals]


def benjamini_hochberg(pvals: Sequence[float], q: float = 0.10) -> list[bool]:
    """BH step-up reject flags controlling FDR at q. Valid for independent or positively dependent tests
    (cells sharing games are positively dependent, so it applies; under negative dependence use BY)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    kmax = 0
    for rank, i in enumerate(order, 1):
        if pvals[i] <= q * rank / m:
            kmax = rank
    keep = set(order[:kmax])
    return [i in keep for i in range(m)]


def pooled_cluster_test(rows: Sequence[tuple[str, float]], b: int = 4000, seed: int = 20261002) -> dict:
    """One pooled test across families and bands: rows = (game_key, paired_diff). Each game's rows are averaged
    first (so a game with many strikes does not outweigh one with few), then the game means are bootstrapped.
    Returns mean, 95% interval, n_games and a one-sided bootstrap p for mean <= 0 (floor 1/(b+1)).
    Applies when the same game can appear in several cells (families/bands share game_key): clustering by game
    removes that double counting. It answers 'is there ANY pooled skill', not 'which cell'."""
    by_game: dict[str, list[float]] = {}
    for g, v in rows:
        by_game.setdefault(g, []).append(v)
    gm = {g: [sum(v) / len(v)] for g, v in by_game.items()}
    mean, lo, hi = cluster_bootstrap(gm, b, seed)
    vals = [v[0] for v in gm.values()]
    centred = [x - mean for x in vals]
    rng = random.Random(seed + 1)
    n = len(vals)
    hits = sum(1 for _ in range(b) if sum(centred[rng.randrange(n)] for _ in range(n)) / n >= mean)
    return {"mean": mean, "ci95": [lo, hi], "n_games": n, "p_one_sided": (hits + 1) / (b + 1)}

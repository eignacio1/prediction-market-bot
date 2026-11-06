"""Power and planned looks for the market-anchored blend test (W105.1 / B-051).

The question: does an engine's view move Kalshi's line usefully?  i.e. in  p = pm + w (pe - pm)  is  w > 0 ?

TEST STATISTIC (no fitting, so it can be read at planned looks).  The log-likelihood derivative at w = 0 (the market
alone) for one row is the SCORE
    s = (y - pm) (pe - pm) / (pm (1 - pm))          E[s | w] = w (pe - pm)^2 / (pm (1 - pm)) >= 0 iff w >= 0
and its information is  I = (pe - pm)^2 / (pm (1 - pm)).  A game's strikes share one outcome's cause, so a *game* is the
independent unit: S_g = mean of s over the game's rows, I_g likewise.  z = mean_g(S_g) / (sd_g(S_g) / sqrt(G)).
H0: w <= 0.  Rows with pm outside [PM_LO, PM_HI] are excluded ex ante (the score is unbounded as pm -> 0 or 1).

WHEN IT APPLIES: settled rows carrying pm and pe from one snapshot, >= ~15 games per cell, an engine not tuned on those
games.  WHEN IT DOES NOT: a market that is itself over-dispersed (a skill-free model near 0.5 then looks like w > 0 -
read a crossing as 'shrinkage or skill'), and fewer than ~15 games (the normal approximation undercovers).
SIMULATION CAVEAT: the power simulation draws ONE uniform per game and sets y = 1[U < p*] for every row, i.e. the rows
of a game are comonotone.  That is exact for a strike ladder and approximate for a moneyline's two complementary sides.

GROUP-SEQUENTIAL MACHINERY: exact (numerical-integration) boundaries and crossing probabilities for one-sided looks
with a Lan-DeMets spending function (``multiplicity.spend_obrien_fleming`` / ``spend_pocock``); efficacy stopping only
(non-binding: there is no futility boundary, so the null crossing probability is exactly the spent alpha).
Needs numpy.
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np

from prediction_market_bot.quant.multiplicity import spend_obrien_fleming, spend_pocock

PM_LO, PM_HI = 0.02, 0.98
_N = NormalDist()
Row = tuple  # (cluster, pm, pe, y)
SPENDING: dict[str, Callable] = {"obrien_fleming": spend_obrien_fleming, "pocock": spend_pocock}


# ---------------------------------------------------------------- the per-game score
def eligible(pm: float) -> bool:
    return PM_LO <= pm <= PM_HI


def game_scores(rows: Iterable[Row]) -> dict:
    """cluster -> (S_g, I_g, n_rows): game-mean score and information over rows with pm in [PM_LO, PM_HI]."""
    acc: dict = {}
    for c, pm, pe, y in rows:
        if not eligible(pm):
            continue
        v = pm * (1 - pm)
        s = (y - pm) * (pe - pm) / v
        i = (pe - pm) ** 2 / v
        a = acc.setdefault(c, [0.0, 0.0, 0])
        a[0] += s; a[1] += i; a[2] += 1
    return {c: (a[0] / a[2], a[1] / a[2], a[2]) for c, a in acc.items()}


def score_z(game_s: Sequence[float]) -> float:
    """One-sided z for H0: w <= 0 from per-game mean scores (clusters are the iid unit)."""
    n = len(game_s)
    if n < 2:
        return float("nan")
    m = sum(game_s) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in game_s) / (n - 1))
    if sd == 0:
        return 0.0 if m == 0 else math.copysign(math.inf, m)
    return m / (sd / math.sqrt(n))


def w_score_estimate(scores: Mapping) -> float | None:
    """Method-of-scoring estimate of w: sum(S_g) / sum(I_g) (not clipped).  None if there is no information."""
    si = sum(v[1] for v in scores.values())
    return None if si <= 0 else sum(v[0] for v in scores.values()) / si


def w_score_upper(scores: Mapping, b: int = 1000, seed: int = 20261106, level: float = 0.95) -> float | None:
    """One-sided upper bound for w: ``level`` quantile of the whole-game bootstrap of sum(S)/sum(I)."""
    keys = sorted(scores)
    if len(keys) < 2:
        return None
    rng = random.Random(seed)
    est = []
    for _ in range(b):
        ss = ii = 0.0
        for _ in keys:
            s, i, _n = scores[keys[rng.randrange(len(keys))]]
            ss += s; ii += i
        if ii > 0:
            est.append(ss / ii)
    est.sort()
    return est[min(len(est) - 1, int(level * len(est)))] if est else None


# ---------------------------------------------------------------- power from the observed rows
def simulate_game_scores(rows: Iterable[Row], w: float, rng: random.Random, reps: int = 1) -> list:
    """Per-game (S_g, I_g) draws in a world where the truth is the blend at weight ``w``: y = 1[U < p*], one U per game
    per replicate (rows of a game comonotone).  Returns a list of (S_g, I_g) pairs, ``reps`` per observed game."""
    by: dict = {}
    for c, pm, pe, _y in rows:
        if eligible(pm):
            by.setdefault(c, []).append((pm, pe))
    out = []
    for _ in range(reps):
        for c, lst in by.items():
            u = rng.random()
            ss = ii = 0.0
            for pm, pe in lst:
                v = pm * (1 - pm)
                ps = min(max(pm + w * (pe - pm), 1e-9), 1 - 1e-9)
                y = 1.0 if u < ps else 0.0
                ss += (y - pm) * (pe - pm) / v
                ii += (pe - pm) ** 2 / v
            out.append((ss / len(lst), ii / len(lst)))
    return out


def effect_and_sd(rows: Iterable[Row], w: float, reps: int = 200, seed: int = 20261106) -> dict:
    """mu = mean per-game score and sigma = its per-game sd in the world with weight ``w`` (pooled over games x reps)."""
    rows = list(rows)
    d = simulate_game_scores(rows, w, random.Random(seed), reps)
    if len(d) < 2:
        return {"mu": float("nan"), "sigma": float("nan"), "info": float("nan"), "n_obs_games": 0}
    s = [x[0] for x in d]
    m = sum(s) / len(s)
    sd = math.sqrt(sum((x - m) ** 2 for x in s) / (len(s) - 1))
    return {"mu": m, "sigma": sd, "info": sum(x[1] for x in d) / len(d), "n_obs_games": len({r[0] for r in rows if eligible(r[1])})}


def games_fixed_sample(mu: float, sigma: float, alpha: float = 0.05, power: float = 0.8) -> float:
    """Games for a one-sided fixed-sample z-test of mean score (effect mu, sd sigma): ((z_a + z_b) sigma / mu)^2."""
    if not (mu > 0 and sigma > 0):
        return float("inf")
    return ((_N.inv_cdf(1 - alpha) + _N.inv_cdf(power)) * sigma / mu) ** 2


def simulate_power(rows: Iterable[Row], w: float, n_games: int, alpha: float = 0.05, reps: int = 2000,
                   seed: int = 20261106) -> float:
    """Monte-Carlo power: draw n_games games with replacement from the observed ones, simulate outcomes at weight
    ``w``, test at one-sided ``alpha``.  At w = 0 this is the type-I error."""
    rows = list(rows)
    by: dict = {}
    for c, pm, pe, _y in rows:
        if eligible(pm):
            by.setdefault(c, []).append((pm, pe))
    keys = sorted(by)
    if not keys or n_games < 2:
        return float("nan")
    zc = _N.inv_cdf(1 - alpha)
    rng = random.Random(seed)
    hit = 0
    for _ in range(reps):
        sc = []
        for _ in range(n_games):
            lst = by[keys[rng.randrange(len(keys))]]
            u = rng.random()
            ss = 0.0
            for pm, pe in lst:
                ps = min(max(pm + w * (pe - pm), 1e-9), 1 - 1e-9)
                ss += ((1.0 if u < ps else 0.0) - pm) * (pe - pm) / (pm * (1 - pm))
            sc.append(ss / len(lst))
        if score_z(sc) > zc:
            hit += 1
    return hit / reps


# ---------------------------------------------------------------- exact group-sequential design
_GRID_LO, _GRID_HI, _H = -9.0, 9.0, 0.04
_X = np.arange(_GRID_LO, _GRID_HI + _H / 2, _H)
_ERF = np.frompyfunc(math.erf, 1, 1)


def _sf(z: np.ndarray) -> np.ndarray:
    """1 - Phi(z), vectorised."""
    return 0.5 * (1.0 - _ERF(z / math.sqrt(2.0)).astype(float))


def _cross_by_look(fracs: Sequence[float], bounds: Sequence[float], drift: float) -> list:
    """P(first crossing of the upper boundary at look k) for k = 1..K, for S_k = B(t_k), B a Brownian motion with
    drift ``drift`` per unit information (so E[Z_K] = drift at t = 1) and boundary  Z_k > bounds[k]."""
    out, f, t_prev = [], None, 0.0
    for k, (t, b) in enumerate(zip(fracs, bounds)):
        dt = t - t_prev
        sd = math.sqrt(dt)
        c = b * math.sqrt(t)
        if k == 0:
            out.append(float(_sf(np.array([(c - drift * dt) / sd]))[0]))
            f = np.where(_X < c, np.exp(-0.5 * ((_X - drift * dt) / sd) ** 2) / (sd * math.sqrt(2 * math.pi)), 0.0)
        else:
            out.append(float(np.sum(f * _sf((c - _X - drift * dt) / sd)) * _H))
            kern = np.exp(-0.5 * ((_X[:, None] - _X[None, :] - drift * dt) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
            f = np.where(_X < c, kern @ f * _H, 0.0)
        t_prev = t
    return out


from functools import lru_cache


def gs_boundaries(fracs: Sequence[float], alpha: float = 0.05, spending: str = "obrien_fleming") -> list:
    return list(_gs_boundaries(tuple(fracs), alpha, spending))


@lru_cache(maxsize=64)
def _gs_boundaries(fracs: tuple, alpha: float, spending: str) -> tuple:
    """Upper z boundaries so that the null crossing probability at look k equals spend(t_k) - spend(t_{k-1})."""
    sp = SPENDING[spending]
    if list(fracs) != sorted(fracs) or fracs[-1] != 1.0:
        raise ValueError("fracs must be increasing and end at 1.0")
    bounds: list = []
    spent = 0.0
    for k, t in enumerate(fracs):
        want = sp(t, alpha) - spent
        lo, hi = 0.5, 9.0
        for _ in range(34):
            mid = 0.5 * (lo + hi)
            p = _cross_by_look(fracs[:k + 1], list(bounds) + [mid], 0.0)[-1]
            if p > want:
                lo = mid
            else:
                hi = mid
        bounds.append(0.5 * (lo + hi))
        spent += want
    return tuple(bounds)


def gs_power(fracs: Sequence[float], bounds: Sequence[float], drift: float) -> float:
    """Probability of crossing at any look when E[Z at the final look] = drift."""
    return float(sum(_cross_by_look(fracs, bounds, drift)))


def gs_games_needed(mu: float, sigma: float, fracs: Sequence[float], alpha: float = 0.05, power: float = 0.8,
                    spending: str = "obrien_fleming") -> dict:
    """Games at the FINAL look so the plan crosses somewhere with probability ``power`` when the per-game mean score is
    mu (sd sigma).  Also the fixed-sample requirement and the inflation factor between them."""
    fixed = games_fixed_sample(mu, sigma, alpha, power)
    if not math.isfinite(fixed):
        return {"n_max": float("inf"), "n_fixed": fixed, "inflation": float("nan"), "bounds": []}
    bounds = gs_boundaries(fracs, alpha, spending)
    lo, hi = 0.1, 8.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if gs_power(fracs, bounds, mid) < power:
            lo = mid
        else:
            hi = mid
    theta = 0.5 * (lo + hi)
    n_max = (theta * sigma / mu) ** 2
    return {"n_max": n_max, "n_fixed": fixed, "inflation": n_max / fixed, "bounds": bounds, "theta": theta}


# ---------------------------------------------------------------- Holm across cells at a look
def holm_at_look(pvals: Sequence[float], alpha_cum: float) -> list:
    """Holm step-down at one look with the cumulative alpha spent so far (``alpha_cum``).  Valid with a spending
    function: the scaled boundary alpha_cum / m0 is itself an alpha-spending boundary for each true null."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    rej = [False] * m
    for rank, i in enumerate(order):
        if pvals[i] <= alpha_cum / (m - rank):
            rej[i] = True
        else:
            break
    return rej


def z_to_p(z: float) -> float:
    return 1.0 - _N.cdf(z)

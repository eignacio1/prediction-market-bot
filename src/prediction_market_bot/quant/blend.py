"""Market-anchored blend weight (W104.2 / B-049): how far to move off the market's own price toward a model.

    linear form:    p = pm + w * (pe - pm)
    log-odds form:  logit p = logit pm + w * (logit pe - logit pm)

``w`` is fitted by log loss on settled rows. ``w = 0`` is the market alone, ``w = 1`` is the model alone; the fit is
confined to [0, 1] (a model worth *fading* is a different question from how far to follow it). Rows are
``(cluster, pm, pe, y)``: a cluster is a game (all strikes of one game share the outcome's cause and are dependent).

WHEN IT APPLIES: settled rows carrying both prices taken at the same snapshot, and a few dozen or more independent
clusters. It does NOT apply to a model that was tuned on the same games (the weight would be in-sample), nor with
fewer than ~15 clusters (the percentile interval undercovers - the same caveat as ``inference.cluster_bootstrap``).
CAVEAT: if the market is itself over-dispersed (too confident), a skill-free model that is centred near 0.5 earns a
small positive w simply by shrinking the market toward the middle. Read a small w as 'shrinkage or skill', not skill.
The weight is DESCRIPTIVE: it is not a verdict on any frozen cell and carries no authority over sizing.

Stdlib only. Everything is built from per-cluster loss vectors over a fixed grid of w, so a bootstrap resample or a
cross-validation fold is a sum of precomputed vectors, not a re-evaluation of every row.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Iterable, Sequence

from prediction_market_bot.quant.inference import cluster_bootstrap

EPS = 1e-6
GRID = tuple(i / 100 for i in range(101))   # w = 0.00 .. 1.00
Row = tuple  # (cluster, pm, pe, y)


def _clip(p: float) -> float:
    return min(max(p, EPS), 1 - EPS)


def _logit(p: float) -> float:
    p = _clip(p)
    return math.log(p / (1 - p))


def blend_prob(pm: float, pe: float, w: float, form: str = "linear") -> float:
    """The blended probability for one row."""
    if form == "linear":
        return _clip(pm + w * (pe - pm))
    if form == "logit":
        z = _logit(pm) + w * (_logit(pe) - _logit(pm))
        return _clip(1 / (1 + math.exp(-z)))
    raise ValueError(f"unknown form {form!r}")


def _ll(p: float, y: float) -> float:
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def cluster_losses(rows: Iterable[Row], form: str = "linear", grid: Sequence[float] = GRID) -> dict:
    """cluster -> (n_rows, [sum of log loss at each w in grid])."""
    out: dict = {}
    for c, pm, pe, y in rows:
        n, v = out.get(c, (0, [0.0] * len(grid)))
        v = [a + _ll(blend_prob(pm, pe, w, form), y) for a, w in zip(v, grid)]
        out[c] = (n + 1, v)
    return out


def _argmin_w(total_n: int, total_v: Sequence[float], lam: float, grid: Sequence[float]) -> float:
    """w minimising mean log loss + lam * w^2 (ridge toward 0); ties go to the smaller w."""
    best, best_w = float("inf"), 0.0
    for v, w in zip(total_v, grid):
        obj = v / total_n + lam * w * w
        if obj < best - 1e-15:
            best, best_w = obj, w
    return best_w


def _sum(cl: dict, keys: Iterable[str], m: int) -> tuple:
    n, v = 0, [0.0] * m
    for k in keys:
        kn, kv = cl[k]
        n += kn
        v = [a + b for a, b in zip(v, kv)]
    return n, v


def fit_w(rows: Iterable[Row], form: str = "linear", lam: float = 0.0, grid: Sequence[float] = GRID) -> float:
    """Full-sample weight by log loss. ``lam`` is a ridge penalty (mean-loss units) pulling w toward 0."""
    cl = cluster_losses(rows, form, grid)
    if not cl:
        return 0.0
    n, v = _sum(cl, cl, len(grid))
    return _argmin_w(n, v, lam, grid)


def shrink_toward_zero(w: float, se: float) -> float:
    """Positive-part James-Stein style shrinkage: w * max(0, 1 - se^2 / w^2). A weight no larger than its own
    noise goes to 0; a weight many se from 0 is barely touched."""
    if w <= 0:
        return 0.0
    return w * max(0.0, 1.0 - (se * se) / (w * w))


def cv_gain(rows: Iterable[Row], form: str = "linear", k: int = 5, lam: float = 0.0, seed: int = 20261105,
            grid: Sequence[float] = GRID) -> dict:
    """Game-clustered k-fold: fit w on k-1 folds, score the held-out fold. Returns per-cluster out-of-sample log-loss
    gain over the market alone (LL_market - LL_blend, positive = blend better) as ``gain_by_cluster`` (lists of
    per-row gains, ready for ``cluster_bootstrap``), the fold weights, and their mean."""
    rows = list(rows)
    cl = cluster_losses(rows, form, grid)
    keys = sorted(cl)
    if len(keys) < 2:
        return {"gain_by_cluster": {}, "fold_w": [], "w_cv": 0.0}
    k = max(2, min(k, len(keys)))
    rng = random.Random(seed)
    order = keys[:]
    rng.shuffle(order)
    fold_of = {c: i % k for i, c in enumerate(order)}
    fold_w = []
    w_of_fold = {}
    for f in range(k):
        train = [c for c in keys if fold_of[c] != f]
        n, v = _sum(cl, train, len(grid))
        w_of_fold[f] = _argmin_w(n, v, lam, grid)
        fold_w.append(w_of_fold[f])
    gain: dict = defaultdict(list)
    for c, pm, pe, y in rows:
        w = w_of_fold[fold_of[c]]
        gain[c].append(_ll(_clip(pm), y) - _ll(blend_prob(pm, pe, w, form), y))
    return {"gain_by_cluster": dict(gain), "fold_w": fold_w, "w_cv": sum(fold_w) / len(fold_w)}


def blend_report(rows: Iterable[Row], form: str = "linear", b: int = 500, k: int = 5, lam: float = 0.0,
                 seed: int = 20261105, grid: Sequence[float] = GRID) -> dict:
    """The block's one-cell summary.

    w_hat      full-sample log-loss weight in [0, 1]
    w_boot_ci  95% percentile interval of w_hat under whole-cluster resampling
    w_shrunk   w_hat shrunk toward 0 by its bootstrap se (``shrink_toward_zero``)
    oos_gain   mean out-of-sample log-loss gain per row of the CV-fitted blend over the market alone, with a 95%
               whole-cluster interval; ``beats_market`` is True only if that interval excludes 0 from above
    The 'beats the market' call is DESCRIPTIVE (see module docstring)."""
    rows = list(rows)
    cl = cluster_losses(rows, form, grid)
    keys = sorted(cl)
    n_games, n_rows = len(keys), sum(cl[c][0] for c in keys)
    if n_games < 2:
        return {"n_rows": n_rows, "n_games": n_games, "form": form, "w_hat": None, "note": "fewer than 2 games"}
    n, v = _sum(cl, keys, len(grid))
    w_hat = _argmin_w(n, v, lam, grid)
    rng = random.Random(seed)
    ws = []
    for _ in range(b):
        picks = [keys[rng.randrange(n_games)] for _ in range(n_games)]
        bn, bv = _sum(cl, picks, len(grid))
        ws.append(_argmin_w(bn, bv, lam, grid))
    ws.sort()
    mean_w = sum(ws) / len(ws)
    se = math.sqrt(sum((x - mean_w) ** 2 for x in ws) / max(1, len(ws) - 1))
    cv = cv_gain(rows, form, k=k, lam=lam, seed=seed, grid=grid)
    g_mean, g_lo, g_hi = cluster_bootstrap(cv["gain_by_cluster"], b=b, seed=seed)
    ll_market = sum(_ll(_clip(pm), y) for _, pm, _, y in rows) / n_rows
    return {"n_rows": n_rows, "n_games": n_games, "form": form, "w_hat": w_hat,
            "w_boot_ci": (ws[int(0.025 * b)], ws[int(0.975 * b) - 1]), "w_se": se,
            "w_shrunk": shrink_toward_zero(w_hat, se), "w_cv": cv["w_cv"],
            "oos_gain": g_mean, "oos_gain_ci": (g_lo, g_hi), "ll_market": ll_market,
            "beats_market": bool(g_lo > 0), "p_w_gt0": sum(1 for x in ws if x > 0) / len(ws)}

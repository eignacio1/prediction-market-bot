"""Counterfactual placement rules on recorded orders. W105.2, B-052.

Descriptive and held-out only: nothing here places, sizes or gates an order.

Each recorded order is a dict with at least
  game    cluster id (fills in one game share an outcome path, so intervals resample games)
  price   price paid / posted for the held side, dollars
  filled  bool
  mk      post-fill markout, held-side mid minus fill price, dollars (None when unknown; only for fills)
  pnl     realised P&L per contract if filled (settle - price), dollars (None when unknown)

Tools (each with a known-answer test in tests/test_quant_placement.py):
  cluster_mean_ci       mean with a game-clustered bootstrap interval.
  bucket_markout        expected markout of a fill by price bucket (n, mean, CI).
  evaluate_rule         what a placement rule WOULD have done on the recorded orders: share of orders it
                        still posts, fill rate among those, mean markout per fill, net per ORDER POSTED.
                        A rule here is a pure filter ("do not post this order"). It never moves an order
                        to a new price, because a recorded order has no fill outcome at a price it did
                        not rest at; a rule that needs one (post at mid minus k ticks) is read from the
                        control-vs-treatment contrast in ``arm_contrast``, not simulated.
  arm_contrast          difference in fill rate and net per order between two arms that really rested at
                        different prices (e.g. control at the model mid vs treatment at the best bid).
  fit_price_threshold   change-point on price: the cut T that best splits markout into "below T" and
                        "at or above T" (least squares), with a game-clustered bootstrap interval.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

import numpy as np


def _groups(clusters: Sequence) -> list:
    idx: dict = {}
    for i, c in enumerate(clusters):
        idx.setdefault(c, []).append(i)
    return [np.array(v) for v in idx.values()]


def cluster_mean_ci(values: Sequence[float], clusters: Sequence, n_boot: int = 400, seed: int = 11,
                    level: float = 0.90) -> dict:
    """Mean of ``values`` with a percentile interval from resampling whole clusters (games)."""
    v = np.asarray(values, float)
    n = len(v)
    if n == 0:
        return {"n": 0, "mean": None, "lo": None, "hi": None, "n_clusters": 0}
    g = _groups(clusters)
    rng = np.random.default_rng(seed)
    sums = np.array([v[i].sum() for i in g])
    cnts = np.array([len(i) for i in g], float)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(g), len(g))
        boots[b] = sums[pick].sum() / cnts[pick].sum()
    a = (1 - level) / 2 * 100
    return {"n": n, "mean": float(v.mean()), "lo": float(np.percentile(boots, a)),
            "hi": float(np.percentile(boots, 100 - a)), "n_clusters": len(g)}


def bucket_markout(rows: Sequence[dict], edges: Sequence[float], n_boot: int = 400, seed: int = 11) -> list:
    """Expected markout of a FILL by price bucket [edges[i], edges[i+1]). Fills with unknown markout are skipped."""
    fl = [r for r in rows if r["filled"] and r.get("mk") is not None]
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = [r for r in fl if lo <= r["price"] < hi]
        ci = cluster_mean_ci([r["mk"] for r in sub], [r["game"] for r in sub], n_boot, seed)
        out.append({"price_lo": lo, "price_hi": hi, **ci})
    return out


def evaluate_rule(rows: Sequence[dict], allow: Callable[[dict], bool], key: str = "mk",
                  n_boot: int = 400, seed: int = 11) -> dict:
    """Apply a pure filter. ``net_per_order`` = mean over POSTED orders of (key if filled else 0), so a rule
    that skips a bad region is rewarded for the loss avoided and charged for the fills it gives up."""
    kept = [r for r in rows if allow(r)]
    n_all = len(rows)
    if not kept:
        return {"posted": 0, "share_posted": 0.0, "fill_rate": None, "per_fill": None, "net_per_order": None}
    vals = np.array([(r[key] if (r["filled"] and r.get(key) is not None) else 0.0) for r in kept])
    fills = [r for r in kept if r["filled"] and r.get(key) is not None]
    pf = cluster_mean_ci([r[key] for r in fills], [r["game"] for r in fills], n_boot, seed)
    net = cluster_mean_ci(vals, [r["game"] for r in kept], n_boot, seed)
    return {"posted": len(kept), "share_posted": len(kept) / n_all,
            "fill_rate": float(np.mean([r["filled"] for r in kept])),
            "per_fill": pf, "net_per_order": net}


def arm_contrast(rows: Sequence[dict], arm_a: str, arm_b: str, key: str = "mk",
                 n_boot: int = 400, seed: int = 11) -> dict:
    """Net-per-order and fill-rate difference (b - a) between two arms, game-clustered.
    Arms rested at different prices in reality, so this is the empirical answer to 'post lower'."""
    A = [r for r in rows if r.get("arm") == arm_a]
    B = [r for r in rows if r.get("arm") == arm_b]
    if not A or not B:
        return {"n_a": len(A), "n_b": len(B), "diff_net": None}

    def net(r):
        return r[key] if (r["filled"] and r.get(key) is not None) else 0.0

    games = sorted({r["game"] for r in rows})
    ga: dict = {}
    gb: dict = {}
    for r in A:
        ga.setdefault(r["game"], []).append(r)
    for r in B:
        gb.setdefault(r["game"], []).append(r)
    both = [g for g in games if g in ga and g in gb]
    if not both:
        return {"n_a": len(A), "n_b": len(B), "diff_net": None}
    rng = np.random.default_rng(seed)

    def stat(gs):
        a = [x for g in gs for x in ga[g]]
        b = [x for g in gs for x in gb[g]]
        return (np.mean([net(x) for x in b]) - np.mean([net(x) for x in a]),
                np.mean([x["filled"] for x in b]) - np.mean([x["filled"] for x in a]))

    point = stat(both)
    boots = np.array([stat([both[i] for i in rng.integers(0, len(both), len(both))]) for _ in range(n_boot)])
    return {"n_a": len(A), "n_b": len(B), "games_both": len(both),
            "diff_net": float(point[0]), "diff_net_ci90": [float(np.percentile(boots[:, 0], 5)), float(np.percentile(boots[:, 0], 95))],
            "diff_fill_rate": float(point[1]),
            "diff_fill_rate_ci90": [float(np.percentile(boots[:, 1], 5)), float(np.percentile(boots[:, 1], 95))]}


def _best_cut(price: np.ndarray, y: np.ndarray, grid: np.ndarray, min_side: int) -> Optional[float]:
    best, best_sse = None, np.inf
    for t in grid:
        lo, hi = y[price < t], y[price >= t]
        if len(lo) < min_side or len(hi) < min_side:
            continue
        sse = ((lo - lo.mean()) ** 2).sum() + ((hi - hi.mean()) ** 2).sum()
        if sse < best_sse:
            best, best_sse = float(t), sse
    return best


def fit_price_threshold(price: Sequence[float], markout: Sequence[float], clusters: Sequence,
                        grid: Optional[Sequence[float]] = None, min_side: int = 30, n_boot: int = 200,
                        seed: int = 11) -> dict:
    """Least-squares change-point: the price T above which markout steps to a different mean."""
    p = np.asarray(price, float)
    y = np.asarray(markout, float)
    g = np.asarray(grid if grid is not None else np.arange(0.05, 0.96, 0.01), float)
    t = _best_cut(p, y, g, min_side)
    if t is None:
        return {"threshold": None, "n": len(p)}
    groups = _groups(clusters)
    rng = np.random.default_rng(seed)
    ts = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[k] for k in rng.integers(0, len(groups), len(groups))])
        b = _best_cut(p[idx], y[idx], g, min_side)
        if b is not None:
            ts.append(b)
    lo, hi = y[p < t], y[p >= t]
    return {"threshold": t, "n": len(p), "mean_below": float(lo.mean()), "mean_at_or_above": float(hi.mean()),
            "ci90": [float(np.percentile(ts, 5)), float(np.percentile(ts, 95))] if ts else None}

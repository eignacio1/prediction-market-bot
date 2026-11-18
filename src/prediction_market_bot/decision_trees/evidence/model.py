"""Partial pooling of net-after-costs over the leaf tree: sport > family > band > price bin > move (> filter).

Model, per arm: theta_root ~ N(m0, s0^2); theta_child = theta_parent + N(0, tau_d^2) at depth d; a leaf's game-clustered
mean ybar_L ~ N(theta_L, v_L). With the variances known the posterior of every node is exact (two passes of Gaussian
message passing on the tree). tau_d^2 is estimated from the data per depth (DerSimonian-Laird moments, pooled over all
parents at that depth) with a stated floor: a thin leaf is shrunk toward its parents by how much the data says leaves
differ. v_L is cluster-robust by game, moderated toward a pooled value (few games give a noisy variance) and inflated by
a design effect because one game feeds several leaves (bands, strikes).

Why empirical Bayes and not full MCMC: the box is Python 3.9 with no sampler, the answer must be deterministic and
testable against closed forms, and it is re-run at every weekly look. Cost: uncertainty in tau is not carried, so the
posterior is somewhat too tight when a depth has few groups; the tau floor and the sequential e-process (sequential.py)
are the guards, and the held-out comparison is the check.

When it applies: per-arm net per contract with >= 2 games in most leaves and a tree whose levels are exchangeable
given the parent. When it doesn't: a level whose children are known to differ by construction (do not pool across arms;
each arm has its own tree), or payoffs so skewed that a game-clustered mean is not near normal (deep longshots, few games).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

Key = Tuple
BIG = 1e12


def norm_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def log_norm_cdf(x: float) -> float:
    if x > -35.0:
        c = norm_cdf(x)
        if c > 0.0:
            return math.log(c)
    return -0.5 * x * x - math.log(-x) - 0.5 * math.log(2.0 * math.pi)


@dataclass
class Cluster:
    """Game-clustered sufficient statistics of a set of rows: per game [sum of nets, rows]."""
    by_game: Dict[str, List[float]]

    @classmethod
    def empty(cls) -> "Cluster":
        return cls({})

    def add(self, game: str, x: float) -> None:
        g = self.by_game.setdefault(game, [0.0, 0])
        g[0] += x
        g[1] += 1

    def merge(self, other: "Cluster") -> None:
        for k, (s, n) in other.by_game.items():
            g = self.by_game.setdefault(k, [0.0, 0])
            g[0] += s
            g[1] += n

    @property
    def games(self) -> int:
        return len(self.by_game)

    @property
    def rows(self) -> int:
        return int(sum(n for _, n in self.by_game.values()))

    @property
    def mean(self) -> float:
        return sum(s for s, _ in self.by_game.values()) / self.rows

    def resid(self) -> Tuple[float, float]:
        """(R, H): R = sum_g (s_g - mean n_g)^2, H = sum_g n_g^2."""
        m = self.mean
        return (sum((s - m * n) ** 2 for s, n in self.by_game.values()), float(sum(n * n for _, n in self.by_game.values())))

    def var_cr(self) -> Optional[float]:
        """Cluster-robust variance of the row-pooled mean (None with fewer than 2 games)."""
        g = self.games
        if g < 2:
            return None
        r, _ = self.resid()
        return g / (g - 1.0) * r / self.rows ** 2

    def var_moderated(self, omega2: Optional[float], k: float = 10.0) -> Optional[float]:
        """Cluster-robust variance shrunk toward omega2 * H / N^2 with k prior degrees of freedom. omega2 is the pooled
        per-game residual variance per squared row (pooled_omega2). None when there is neither 2 games nor an omega2."""
        g, n = self.games, self.rows
        own = self.var_cr()
        if omega2 is None:
            return own
        _, h = self.resid()
        pool = omega2 * h / n ** 2
        if own is None:
            return pool
        return ((g - 1.0) * own + k * pool) / (g - 1.0 + k)


def pooled_omega2(clusters: List[Cluster]) -> Optional[float]:
    num = den = 0.0
    for c in clusters:
        g = c.games
        if g >= 2:
            r, h = c.resid()
            num += r * g / (g - 1.0)
            den += h
    return num / den if den > 0 else None


def _combine(msgs: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Precision-weighted product of Gaussian messages (mean, var). No messages -> flat."""
    p = sum(1.0 / v for _, v in msgs)
    if p <= 1.0 / BIG:
        return (0.0, BIG)
    return (sum(m / v for m, v in msgs) / p, 1.0 / p)


def _remove(post: Tuple[float, float], msg: Tuple[float, float]) -> Tuple[float, float]:
    p = 1.0 / post[1] - 1.0 / msg[1]
    if p <= 1.0 / BIG:
        return (0.0, BIG)
    return ((post[0] / post[1] - msg[0] / msg[1]) / p, 1.0 / p)


def _children(keys) -> Dict[Key, List[Key]]:
    ch = defaultdict(set)
    for k in keys:
        for d in range(len(k), 0, -1):
            ch[k[:d - 1]].add(k[:d])
    return {p: sorted(c, key=repr) for p, c in ch.items()}


def _upward(leaves: Dict[Key, Tuple[float, float]], tau2: Dict[int, float], prior_obs: Dict[Key, Tuple[float, float]],
            estimate: bool, floor: float) -> Tuple[Dict[Key, Tuple[float, float]], Dict[Key, List[Key]], Dict[int, float]]:
    ch = _children(list(leaves) + list(prior_obs))
    depth = max((len(k) for k in list(leaves) + list(prior_obs)), default=0)
    up: Dict[Key, Tuple[float, float]] = {}
    tau2 = dict(tau2)
    nodes_at = defaultdict(list)
    for k in set(ch) | set(leaves) | set(prior_obs):
        nodes_at[len(k)].append(k)
    for d in range(depth, -1, -1):
        if estimate and d + 1 <= depth:
            tau2[d + 1] = max(floor, _dl([[up[c] for c in ch.get(p, [])] for p in nodes_at[d]]))
        for k in nodes_at[d]:
            msgs = [(up[c][0], up[c][1] + tau2.get(d + 1, floor)) for c in ch.get(k, [])]
            if k in leaves:
                msgs.append(leaves[k])
            if k in prior_obs:
                msgs.append(prior_obs[k])
            up[k] = _combine(msgs)
    return up, ch, tau2


def _dl(groups: List[List[Tuple[float, float]]]) -> float:
    """DerSimonian-Laird between-child variance pooled over parent groups. 0 when no group has two children."""
    q = df = c = 0.0
    for g in groups:
        g = [(m, v) for m, v in g if v < BIG]
        if len(g) < 2:
            continue
        w = [1.0 / v for _, v in g]
        sw = sum(w)
        mu = sum(wi * m for wi, (m, _) in zip(w, g)) / sw
        q += sum(wi * (m - mu) ** 2 for wi, (m, _) in zip(w, g))
        df += len(g) - 1
        c += sw - sum(wi * wi for wi in w) / sw
    return max(0.0, (q - df) / c) if c > 0 else 0.0


@dataclass
class Posterior:
    mean: float
    var: float
    prior_mean: float  # what the rest of the tree says about this node, its own data excluded
    prior_var: float

    @property
    def sd(self) -> float:
        return math.sqrt(self.var)

    @property
    def p_pos(self) -> float:
        return norm_cdf(self.mean / math.sqrt(self.var))


@dataclass
class TreeFit:
    nodes: Dict[Key, Posterior]
    tau2: Dict[int, float]
    root_prior: Tuple[float, float]

    def predict(self, key: Key) -> Posterior:
        """Posterior for `key`; a node with no data inherits its deepest known ancestor plus the tau^2 of the levels between."""
        if key in self.nodes:
            return self.nodes[key]
        for d in range(len(key) - 1, -1, -1):
            a = self.nodes.get(key[:d])
            if a is not None:
                v = a.var + sum(self.tau2.get(j, 0.0) for j in range(d + 1, len(key) + 1))
                return Posterior(a.mean, v, a.mean, v)
        v = self.root_prior[1] + sum(self.tau2.get(j, 0.0) for j in range(1, len(key) + 1))
        return Posterior(self.root_prior[0], v, self.root_prior[0], v)


def fit_tree(leaves: Dict[Key, Tuple[float, float]], root_prior: Tuple[float, float] = (0.0, 0.01),
             tau2: Optional[Dict[int, float]] = None, tau_floor: float = 0.0,
             prior_obs: Optional[Dict[Key, Tuple[float, float]]] = None) -> TreeFit:
    """leaves: {key tuple: (game-clustered mean, its variance)}. tau2 None -> estimated per depth (>= tau_floor^2).
    prior_obs: {node key: (mean, var)} outside evidence about a node (the long-history prior), entered as one observation."""
    prior_obs = prior_obs or {}
    up, ch, t2 = _upward(leaves, tau2 or {}, prior_obs, estimate=tau2 is None, floor=tau_floor ** 2)
    nodes: Dict[Key, Posterior] = {}
    if () not in up:
        return TreeFit({(): Posterior(root_prior[0], root_prior[1], root_prior[0], root_prior[1])}, t2, root_prior)
    m, v = _combine([root_prior, up[()]])
    nodes[()] = Posterior(m, v, root_prior[0], root_prior[1])
    stack = [()]
    while stack:
        p = stack.pop()
        post = (nodes[p].mean, nodes[p].var)
        for c in ch.get(p, []):
            t = t2.get(len(c), tau_floor ** 2)
            cav = _remove(post, (up[c][0], up[c][1] + t))
            prior = (cav[0], cav[1] + t)
            m, v = _combine([prior, up[c]])
            nodes[c] = Posterior(m, v, prior[0], prior[1])
            stack.append(c)
    return TreeFit(nodes, t2, root_prior)

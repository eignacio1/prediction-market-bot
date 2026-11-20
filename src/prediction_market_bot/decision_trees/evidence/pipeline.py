"""Rows -> weekly looks -> pooled posterior + always-valid e-process -> an arm per leaf (leaf map v2).

Routing rule (two keys, both needed): a leaf takes arm a when
  (1) the pooled posterior says P(net of a in this leaf > 0) >= bar, and
  (2) the e-processes for arm a of the nodes on the leaf's path (family depth or deeper), averaged, have reached 1/alpha.
Among arms that pass, the highest posterior mean; otherwise NO_BET. Key (2) is what makes weekly looks safe: an average
of e-processes is an e-process, so for a leaf whose whole path has net <= 0 the chance it EVER gets key (2) is <= alpha,
whatever the number of looks. Key (1) keeps a leaf out when the pooled model says it differs from the nodes that earned
the claim. The guarantee is per leaf path, not across the whole tree: across-tree multiplicity is handled by the shrinkage
and checked on held-out data. There is no "thin" exclusion: a thin
leaf is shrunk toward its parents instead of being dropped.

Increment variance (null_var="binary", the default for Kalshi rows): the e-increment uses max(plug-in game-clustered
variance, the variance the rows would have if net were 0). A contract bought at all-in cost c pays 1-c or -c, so c is read
off the net itself (c = 1-x for a win, -x for a loss) and the null variance is c(1-c) per row, rows of one game taken as
fully correlated. Without this floor a short run of favourites that all won (net +0.1..+0.2 every row) has a plug-in
variance near 0 and a huge e-value: on the W110.5 corpus one MLB leaf reached log E = 32.9 on 9 games (W116.1).
A push (y = 0.5) reads as a slightly wrong c; pushes are rare and the plug-in term still applies.

When it applies: settled pre-game rows with a leaf key, a game id and a start time. When it doesn't: a level the rows do
not carry (today: the filter level -- settled rows have no filter column, so the tree stops at the move bin); nets that are
not binary contract payoffs (use null_var="none", e.g. the Gaussian synthetic tests).
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from prediction_market_bot.decision_trees.evidence import model as M
from prediction_market_bot.decision_trees.evidence import sequential as S

Key = Tuple
ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")
LOOK_ANCHOR = datetime(2026, 1, 6, 10, 0, tzinfo=timezone.utc)  # a Tuesday 10:00 UTC; looks are whole weeks from here
_TS = re.compile(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")


def parse_ts(s: str) -> datetime:
    """Tolerant UTC parse (Python 3.9 fromisoformat rejects 'Z' and odd fractions). Offsets other than UTC are not expected."""
    m = _TS.match(str(s))
    if not m:
        raise ValueError(f"bad timestamp: {s!r}")
    y, mo, d, h, mi, sec = (int(x) if x else 0 for x in m.groups())
    return datetime(y, mo, d, h, mi, sec, tzinfo=timezone.utc)


def look_index(start_time_utc: str) -> int:
    return int((parse_ts(start_time_utc) - LOOK_ANCHOR).total_seconds() // (7 * 86400))


@dataclass(frozen=True)
class Obs:
    key: Key
    game: str
    look: int
    nets: dict  # arm -> net per contract, or None when the arm takes no position on the row


@dataclass
class Config:
    bar: float = 0.90
    alpha: float = 0.10
    root_sd: float = 0.10
    tau_floor: float = 0.005
    min_inc_games: int = 5
    source_min_depth: int = 2  # (sport, family) or deeper may earn the sequential claim; sport and root may not
    var_k: float = 10.0
    deff_depth: int = 2
    arms: Sequence[str] = ARMS
    null_var: str = "binary"  # "binary": floor the increment variance at the net=0 variance of a binary contract; "none"
    prior_obs: Dict[str, Dict[Key, Tuple[float, float]]] = field(default_factory=dict)


def node_clusters(obs: Iterable[Obs], arm: str, min_depth: int = 0) -> Dict[Key, M.Cluster]:
    out: Dict[Key, M.Cluster] = {}
    for o in obs:
        x = o.nets.get(arm)
        if x is None:
            continue
        for d in range(min_depth, len(o.key) + 1):
            c = out.get(o.key[:d])
            if c is None:
                c = out[o.key[:d]] = M.Cluster.empty()
            c.add(o.game, x)
    return out


def null_row_sd(x: float) -> float:
    """sd of one binary contract's net if its true net were 0, with the all-in cost read off the realised net x."""
    c = 1.0 - x if x > 0 else -x
    c = min(0.99, max(0.01, c))
    return math.sqrt(c * (1.0 - c))


def node_null_sd(obs: Iterable[Obs], arm: str, min_depth: int = 0) -> Dict[Key, Dict[str, float]]:
    """node -> {game: sum of null_row_sd over the game's rows} (fully correlated within a game: sds add)."""
    out: Dict[Key, Dict[str, float]] = {}
    for o in obs:
        x = o.nets.get(arm)
        if x is None:
            continue
        sd = null_row_sd(x)
        for d in range(min_depth, len(o.key) + 1):
            g = out.setdefault(o.key[:d], {})
            g[o.game] = g.get(o.game, 0.0) + sd
    return out


def leaf_clusters(obs: Sequence[Obs], arm: str) -> Dict[Key, M.Cluster]:
    leaves: Dict[Key, M.Cluster] = {}
    for o in obs:
        x = o.nets.get(arm)
        if x is not None:
            leaves.setdefault(o.key, M.Cluster.empty()).add(o.game, x)
    return leaves


def leaf_inputs(obs: Sequence[Obs], arm: str, cfg: Config) -> Tuple[Dict[Key, Tuple[float, float]], Dict[Key, M.Cluster], Dict[Key, float]]:
    """-> ({leaf: (mean, variance)}, leaf clusters, design effect per family). The variance is cluster-robust by game,
    moderated toward the family's pooled value, times the family design effect (one game feeds several leaves)."""
    return leaf_inputs_from_clusters(leaf_clusters(obs, arm), cfg)


def leaf_inputs_from_clusters(leaves: Dict[Key, M.Cluster], cfg: Config) -> Tuple[Dict[Key, Tuple[float, float]], Dict[Key, M.Cluster], Dict[Key, float]]:
    fams = defaultdict(list)
    for k in leaves:
        fams[k[:cfg.deff_depth]].append(k)
    glob = M.pooled_omega2(list(leaves.values()))
    out, deffs = {}, {}
    for fam, ks in fams.items():
        om = M.pooled_omega2([leaves[k] for k in ks]) or glob
        v = {k: leaves[k].var_moderated(om, cfg.var_k) for k in ks}
        v = {k: x for k, x in v.items() if x is not None and x > 0}
        if not v:
            continue
        tot = M.Cluster.empty()
        for k in v:
            tot.merge(leaves[k])
        direct = tot.var_cr()
        indep = sum((leaves[k].rows / tot.rows) ** 2 * x for k, x in v.items())
        deff = max(1.0, direct / indep) if direct and indep > 0 else 1.0
        deffs[fam] = deff
        for k, x in v.items():
            out[k] = (leaves[k].mean, x * deff)
    return out, leaves, deffs


def fit_arm(obs: Sequence[Obs], arm: str, cfg: Config) -> M.TreeFit:
    leaves, _, _ = leaf_inputs(obs, arm, cfg)
    return M.fit_tree(leaves, root_prior=(0.0, cfg.root_sd ** 2), tau_floor=cfg.tau_floor, prior_obs=cfg.prior_obs.get(arm))


@dataclass
class Result:
    cfg: Config
    fits: Dict[str, M.TreeFit]
    log_e: Dict[str, Dict[Key, List[Tuple[int, float]]]]  # per arm, per node: (look, running log E) at each scored increment
    clusters: Dict[str, Dict[Key, M.Cluster]]
    deff: Dict[str, Dict[Key, float]]
    looks: List[int]

    def path_log_e(self, key: Key, arm: str) -> Tuple[float, Optional[Key]]:
        """(running max over looks of log mean-E over the path nodes, the node contributing most at that look).
        A path node with no scored increment yet counts as E = 1."""
        nodes = [key[:d] for d in range(self.cfg.source_min_depth, len(key) + 1)]
        if not nodes:
            return 0.0, None
        steps = sorted({lk for n in nodes for lk, _ in self.log_e[arm].get(n, [])})
        cur = {n: 0.0 for n in nodes}
        best, who = 0.0, None
        for lk in steps:
            for n in nodes:
                for l2, v in self.log_e[arm].get(n, []):
                    if l2 == lk:
                        cur[n] = v
            top = max(cur.values())
            le = top + math.log(sum(math.exp(v - top) for v in cur.values()) / len(nodes))
            if le > best:
                best, who = le, max(cur, key=cur.get)
        return best, who

    def source(self, key: Key, arm: str) -> Optional[Tuple[Key, float]]:
        le, who = self.path_log_e(key, arm)
        return (who, le) if who is not None and le >= math.log(1.0 / self.cfg.alpha) else None

    def route(self, key: Key) -> dict:
        post, src, best = {}, {}, None
        for a in self.cfg.arms:
            p = self.fits[a].predict(key)
            post[a] = [round(p.mean, 5), round(p.sd, 5), round(p.p_pos, 4)]
            s = self.source(key, a)
            if s:
                src[a] = ["|".join(str(x) for x in s[0]), round(s[1], 3)]
            if s and p.p_pos >= self.cfg.bar and p.mean > 0 and (best is None or p.mean > best[1]):
                best = (a, p.mean)
        c = self.clusters[self.cfg.arms[0]].get(key)
        return {"arm": best[0] if best else "NO_BET", "posterior": post, "source": src,
                "rows": c.rows if c else 0, "games": c.games if c else 0}

    def leaf_keys(self) -> List[Key]:
        ks = set()
        for a in self.cfg.arms:
            ks |= set(self.clusters[a])
        return sorted(ks, key=repr)


@dataclass
class State:
    """Everything a weekly look carries to the next one (W121.1). run() is one advance() over all looks; advancing look by
    look from a saved State gives the same numbers, which is what makes the always-valid guarantee hold across runs."""
    arms: Sequence[str]
    run_e: Dict[str, Dict[Key, float]]
    hist: Dict[str, Dict[Key, List[Tuple[int, float]]]]
    pend: Dict[str, Dict[Key, M.Cluster]]
    pend_prior: Dict[str, Dict[Key, Tuple[float, float]]]
    pend_null: Dict[str, Dict[Key, Dict[str, float]]]
    leaves: Dict[str, Dict[Key, M.Cluster]]  # all rows through the last look, per arm per leaf (the posterior's input)
    looks: List[int]

    @classmethod
    def new(cls, arms: Sequence[str]) -> "State":
        return cls(tuple(arms), {a: {} for a in arms}, {a: {} for a in arms}, {a: {} for a in arms}, {a: {} for a in arms},
                   {a: {} for a in arms}, {a: {} for a in arms}, [])

    def to_json(self) -> dict:
        kj = lambda k: list(k)
        cj = lambda c: c.by_game
        return {"arms": list(self.arms), "looks": self.looks,
                "run_e": {a: [[kj(k), v] for k, v in d.items()] for a, d in self.run_e.items()},
                "hist": {a: [[kj(k), [list(x) for x in h]] for k, h in d.items()] for a, d in self.hist.items()},
                "pend": {a: [[kj(k), cj(c)] for k, c in d.items()] for a, d in self.pend.items()},
                "pend_prior": {a: [[kj(k), list(v)] for k, v in d.items()] for a, d in self.pend_prior.items()},
                "pend_null": {a: [[kj(k), v] for k, v in d.items()] for a, d in self.pend_null.items()},
                "leaves": {a: [[kj(k), cj(c)] for k, c in d.items()] for a, d in self.leaves.items()}}

    @classmethod
    def from_json(cls, j: dict) -> "State":
        tk = lambda k: tuple(k)
        cl = lambda g: M.Cluster({x: [float(v[0]), int(v[1])] for x, v in g.items()})
        arms = tuple(j["arms"])
        return cls(arms,
                   {a: {tk(k): float(v) for k, v in j["run_e"][a]} for a in arms},
                   {a: {tk(k): [(int(x[0]), float(x[1])) for x in h] for k, h in j["hist"][a]} for a in arms},
                   {a: {tk(k): cl(g) for k, g in j["pend"][a]} for a in arms},
                   {a: {tk(k): (float(v[0]), float(v[1])) for k, v in j["pend_prior"][a]} for a in arms},
                   {a: {tk(k): dict(v) for k, v in j["pend_null"][a]} for a in arms},
                   {a: {tk(k): cl(g) for k, g in j["leaves"][a]} for a in arms},
                   [int(x) for x in j["looks"]])


def advance(state: State, new_obs: Iterable[Obs], cfg: Config) -> State:
    """Score the looks in new_obs (each look index must be greater than every look already in state) in order, in place."""
    by_look = defaultdict(list)
    for o in new_obs:
        by_look[o.look].append(o)
    for k in sorted(by_look):
        if state.looks and k <= state.looks[-1]:
            raise ValueError(f"look {k} is not after the last look taken ({state.looks[-1]}): a look is never re-scored")
        for a in cfg.arms:
            lv, _, _ = leaf_inputs_from_clusters(state.leaves[a], cfg)
            fit = M.fit_tree(lv, root_prior=(0.0, cfg.root_sd ** 2), tau_floor=cfg.tau_floor, prior_obs=cfg.prior_obs.get(a))
            nulls = node_null_sd(by_look[k], a, cfg.source_min_depth) if cfg.null_var == "binary" else {}
            pend, pend_prior, pend_null = state.pend[a], state.pend_prior[a], state.pend_null[a]
            for node, c in node_clusters(by_look[k], a, cfg.source_min_depth).items():
                for g, sd in nulls.get(node, {}).items():
                    pend_null.setdefault(node, {})[g] = pend_null.get(node, {}).get(g, 0.0) + sd
                if node not in pend:
                    pend[node] = M.Cluster.empty()
                    p = fit.predict(node)
                    pend_prior[node] = (p.mean, p.var)
                pend[node].merge(c)
                pc = pend[node]
                if pc.games < cfg.min_inc_games:
                    continue  # too few games for a usable variance: carried, prior stays frozen
                se2 = pc.var_cr()
                if node in pend_null:
                    se2 = max(se2 or 0.0, sum(v * v for v in pend_null[node].values()) / pc.rows ** 2)
                if not se2 or se2 <= 0:
                    continue
                m, v = pend_prior[node]
                state.run_e[a][node] = state.run_e[a].get(node, 0.0) + S.log_e_increment(pc.mean, se2, m, v)
                state.hist[a].setdefault(node, []).append((k, state.run_e[a][node]))
                del pend[node], pend_prior[node]
                pend_null.pop(node, None)
            for o in by_look[k]:  # the rows enter the posterior only after this look's increment was scored
                x = o.nets.get(a)
                if x is not None:
                    state.leaves[a].setdefault(o.key, M.Cluster.empty()).add(o.game, x)
        state.looks.append(k)
    return state


def result_of(state: State, cfg: Config) -> Result:
    fits, clusters, deff = {}, {}, {}
    for a in cfg.arms:
        leaves, cl, df = leaf_inputs_from_clusters(state.leaves[a], cfg)
        fits[a] = M.fit_tree(leaves, root_prior=(0.0, cfg.root_sd ** 2), tau_floor=cfg.tau_floor, prior_obs=cfg.prior_obs.get(a))
        clusters[a], deff[a] = cl, df
    return Result(cfg, fits, state.hist, clusters, deff, list(state.looks))


def run(obs: Sequence[Obs], cfg: Optional[Config] = None) -> Result:
    cfg = cfg or Config()
    return result_of(advance(State.new(cfg.arms), obs, cfg), cfg)

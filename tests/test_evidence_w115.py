"""W115.1 (B-094): the evidence module on known answers, a planted effect (recovered) and a planted null (not recovered)."""
import math
import random

import numpy as np

from prediction_market_bot.decision_trees.evidence import calendar as C
from prediction_market_bot.decision_trees.evidence import model as M
from prediction_market_bot.decision_trees.evidence import pipeline as P
from prediction_market_bot.decision_trees.evidence import sequential as S


def test_cluster_variance_known_answer():
    c = M.Cluster.empty()
    for g, xs in {"a": [1.0, 1.0], "b": [0.0], "c": [0.5]}.items():
        for x in xs:
            c.add(g, x)
    assert c.rows == 4 and c.games == 3 and abs(c.mean - 0.625) < 1e-12
    r = (2 - 1.25) ** 2 + (0 - 0.625) ** 2 + (0.5 - 0.625) ** 2
    assert abs(c.var_cr() - 1.5 * r / 16) < 1e-12


def test_tree_posterior_equals_joint_gaussian():
    leaves = {("a", "x"): (0.10, 0.01), ("a", "y"): (-0.02, 0.04), ("b", "z"): (0.03, 0.02)}
    f = M.fit_tree(leaves, root_prior=(0.0, 0.01), tau2={1: 0.0025, 2: 0.0009})
    order = [(), ("a",), ("b",), ("a", "x"), ("a", "y"), ("b", "z")]
    prec, h = np.zeros((6, 6)), np.zeros(6)

    def link(i, j, t):
        prec[i, i] += 1 / t; prec[j, j] += 1 / t; prec[i, j] -= 1 / t; prec[j, i] -= 1 / t

    prec[0, 0] += 1 / 0.01
    link(0, 1, 0.0025); link(0, 2, 0.0025); link(1, 3, 0.0009); link(1, 4, 0.0009); link(2, 5, 0.0009)
    for i, k in ((3, ("a", "x")), (4, ("a", "y")), (5, ("b", "z"))):
        prec[i, i] += 1 / leaves[k][1]; h[i] += leaves[k][0] / leaves[k][1]
    cov = np.linalg.inv(prec); mu = cov @ h
    for i, k in enumerate(order):
        assert abs(f.nodes[k].mean - mu[i]) < 1e-10 and abs(f.nodes[k].var - cov[i, i]) < 1e-10


def test_unseen_leaf_inherits_parent_plus_tau():
    f = M.fit_tree({("a", "x"): (0.1, 0.01)}, tau2={1: 0.004, 2: 0.001})
    p = f.predict(("a", "new"))
    assert abs(p.mean - f.nodes[("a",)].mean) < 1e-12 and abs(p.var - (f.nodes[("a",)].var + 0.001)) < 1e-12


def test_dl_tau_recovers_planted_spread():
    rng = random.Random(1)
    leaves = {}
    for p in range(40):
        for c in range(6):
            leaves[("s", p, c)] = (rng.gauss(0, 0.05) + rng.gauss(0, 0.01), 0.0001)
    f = M.fit_tree(leaves)
    assert 0.04 < math.sqrt(f.tau2[3]) < 0.06


def test_e_increment_equals_numeric_integral():
    for y, s2, m, v in [(0.05, 0.001, 0.02, 0.0004), (-0.03, 0.002, 0.0, 0.01), (0.2, 0.01, -0.05, 0.003)]:
        xs = np.linspace(0, m + 12 * math.sqrt(v) + 1, 200001)
        pri = np.exp(-(xs - m) ** 2 / (2 * v)) / math.sqrt(2 * math.pi * v) / M.norm_cdf(m / math.sqrt(v))
        f = pri * np.exp((y * xs - xs * xs / 2) / s2)
        num = math.log(float(np.sum((f[1:] + f[:-1]) / 2 * np.diff(xs))))
        assert abs(S.log_e_increment(y, s2, m, v) - num) < 1e-6


def test_e_process_error_under_null_does_not_grow_with_looks():
    rng = random.Random(7)
    hits, n = 0, 2000
    for _ in range(n):
        m, v, tot, hit = 0.02, 0.0009, 0.0, False
        for _k in range(40):  # 40 looks, true net = 0, prior updated from past looks only
            y = rng.gauss(0.0, 0.03)
            tot += S.log_e_increment(y, 0.0009, m, v)
            p = 1 / v + 1 / 0.0009
            m, v = (m / v + y / 0.0009) / p, 1 / p
            hit = hit or tot >= math.log(10)
        hits += hit
    assert hits / n <= 0.10


def _synth(effect, seed, weeks=8, games_per_week=12):
    """2 sports x 2 families x 3 bands x 4 price bins. One game feeds every band and bin of its family with a shared
    game shock (the same-game correlation the design effect exists for). `effect` = RIDE net planted in (S0, F0)."""
    rng = random.Random(seed)
    obs = []
    for w in range(weeks):
        for s in ("S0", "S1"):
            for g in range(games_per_week):
                game = f"{s}:{w}:{g}"
                for fam in ("F0", "F1"):
                    shock = rng.gauss(0, 0.25)
                    for band in ("T1", "T2", "T3"):
                        for b in range(4):
                            mu = effect if (s, fam) == ("S0", "F0") else 0.0
                            x = mu + shock + rng.gauss(0, 0.30)
                            obs.append(P.Obs((s, fam, band, b), game, w, {"RIDE": x, "FADE": -x - 0.02}))
    return obs


def test_planted_effect_recovered_and_null_families_stay_no_bet():
    res = P.run(_synth(0.15, 3), P.Config(arms=("RIDE", "FADE"), null_var="none"))
    arms = {k: res.route(k)["arm"] for k in res.leaf_keys()}
    planted = [a for k, a in arms.items() if k[:2] == ("S0", "F0")]
    rest = [a for k, a in arms.items() if k[:2] != ("S0", "F0")]
    assert sum(a == "RIDE" for a in planted) >= 10  # of 12
    assert sum(a != "NO_BET" for a in rest) <= 2  # of 36


def test_planted_null_not_recovered():
    wrong = total = 0
    for seed in range(8):
        res = P.run(_synth(0.0, 100 + seed), P.Config(arms=("RIDE", "FADE"), null_var="none"))
        ks = res.leaf_keys()
        total += len(ks)
        wrong += sum(res.route(k)["arm"] != "NO_BET" for k in ks)
    assert wrong / total <= 0.10  # the stated bound is alpha per leaf path; measured well under it


def test_prior_is_fixed_before_the_increment():
    obs = _synth(0.0, 5, weeks=1)
    res = P.run(obs, P.Config(arms=("RIDE",), null_var="none"))
    node = ("S0", "F0")
    c = P.node_clusters(obs, "RIDE", 2)[node]
    assert res.log_e["RIDE"][node] == [(0, S.log_e_increment(c.mean, c.var_cr(), 0.0, 0.01))]


def test_parse_ts_and_look_index():
    assert P.parse_ts("2026-11-10T10:00:00Z") == P.parse_ts("2026-11-10 10:00:00.123456789+00:00")
    assert P.look_index("2026-11-10T10:00:00Z") == P.look_index("2026-11-17T09:59:59Z") == P.look_index("2026-11-10T09:59:59Z") + 1


def test_calendar_known_answers():
    assert abs(C.inv_norm(0.975) - 1.959964) < 1e-5
    # a huge effect: only the thin rules bind -> 0.3 G >= 10 games -> G = 34 at 10 games a week -> week 4
    assert C.weeks_to_bh(0, 5, 1.0, 0.04, 10, m_tests=80) == 4
    assert C.weeks_to_bh(0, 5, 0.0, 0.04, 10, m_tests=80) is None
    assert C.weeks_to_cross(3.0, (0.02, 0.001), 0.05, 0.04, 10) == 0
    w1 = C.weeks_to_cross(0.0, (0.02, 0.001), 0.06, 0.2, 10)
    w2 = C.weeks_to_cross(0.0, (0.02, 0.001), 0.06, 0.2, 20)
    assert w1 and w2 and w2 < w1
    assert C.weeks_to_bar((0.05, 0.0001), 0.05, 0.2, 10) == 0 and C.weeks_to_bar((0.0, 0.01), -0.01, 0.2, 10) is None


def _binary(edge, seed, weeks=10, games_per_week=10, price=0.85):
    """Kalshi-shaped rows: each game has one favourite outcome shared by all its rows (4 bands x 3 rows); RIDE buys the
    favourite at all-in cost `price`, so net is 1 - price or -price. True win prob = price + edge (edge 0 = the null)."""
    rng = random.Random(seed)
    obs = []
    for w in range(weeks):
        for g in range(games_per_week):
            game = f"G:{w}:{g}"
            y = 1.0 if rng.random() < price + edge else 0.0
            for band in ("T1", "T2", "T3", "T4"):
                for _ in range(3):
                    x = y - price
                    obs.append(P.Obs(("S", "F", band, 4), game, w, {"RIDE": x}))
    return obs


def test_binary_null_floor_stops_the_all_favourites_won_blowup():
    # 9 games, every favourite won: plug-in variance is 0, which used to be skipped or, with one loss, tiny.
    obs = [P.Obs(("S", "F", "T1", 4), f"g{i}", 0, {"RIDE": 0.15}) for i in range(9)]
    obs.append(P.Obs(("S", "F", "T1", 4), "g9", 0, {"RIDE": -0.85}))
    obs += [P.Obs(("S", "F", "T1", 4), f"g{i}", 0, {"RIDE": 0.15}) for i in range(10, 30)]
    plug = P.run(obs, P.Config(arms=("RIDE",), null_var="none")).log_e["RIDE"][("S", "F")][-1][1]
    floor = P.run(obs, P.Config(arms=("RIDE",))).log_e["RIDE"][("S", "F")][-1][1]
    assert floor < plug and floor < math.log(10)  # 29 of 30 at a 0.85 favourite is 1.6 sd above the null, not proof


def test_binary_null_false_claims_bounded_across_looks():
    hits = 0
    n = 300
    for seed in range(n):
        res = P.run(_binary(0.0, 1000 + seed), P.Config(arms=("RIDE",)))
        hits += res.path_log_e(("S", "F", "T1", 4), "RIDE")[0] >= math.log(10)
    assert hits / n <= 0.10, hits / n


def test_binary_planted_edge_is_found():
    found = sum(P.run(_binary(0.10, 2000 + s), P.Config(arms=("RIDE",))).route(("S", "F", "T1", 4))["arm"] == "RIDE"
                for s in range(20))
    assert found >= 14, found  # favourite at 0.85 that truly wins 95%: +0.10 per contract

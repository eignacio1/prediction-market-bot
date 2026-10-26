"""W87.1 Part B: each re-pointed path is run old-vs-new on a frozen seeded snapshot and must be equal."""
from __future__ import annotations

import random

from prediction_market_bot.quant import money as Q


def _quotes(n=2000, seed=7):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        b = round(r.uniform(0.01, 0.97), 2)
        a = round(min(0.99, b + r.choice([0.01, 0.02, 0.05])), 2)
        out.append((r.random(), b, a))
    return out


def test_fees_fee_k007_bit_equal_to_core():
    from prediction_market_bot.pregame_shadow import fees
    for q in [i / 1000 for i in range(0, 1001)]:
        assert fees.fee_k007(q) == 0.07 * q * (1.0 - q) == Q.fee_k007(q)


def test_nhl_edge_net_equal_to_old_formula_on_snapshot():
    import nhl_shadow_eval as N
    for p, b, a in _quotes():
        no = 1.0 - b
        old = (p - a - 0.07 * a * (1 - a), (1 - p) - no - 0.07 * no * (1 - no))
        assert N.edge_net(p, b, a, 0.07) == old or max(abs(x - y) for x, y in zip(N.edge_net(p, b, a, 0.07), old)) < 1e-12
        assert N.edge_net(p, b, a, 0.035) == (p - a - 0.035 * a * (1 - a), (1 - p) - no - 0.035 * no * (1 - no))


def _old_cluster_bootstrap_ci(vals_by_cluster, b, seed):
    """Frozen copy of pregame_shadow.scoring.cluster_bootstrap_ci as it stood before W87.1."""
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
            s += sum(c)
            n += len(c)
        means.append(s / n)
    means.sort()
    return mean, means[int(0.025 * b)], means[int(0.975 * b) - 1]


def test_scoring_cluster_bootstrap_ci_equal_to_old_on_snapshot():
    from prediction_market_bot.pregame_shadow import scoring
    r = random.Random(7)
    groups = {f"g{i}": [r.gauss(0.01, 0.2) for _ in range(r.randint(1, 6))] for i in range(40)}
    assert scoring.cluster_bootstrap_ci(groups) == _old_cluster_bootstrap_ci(groups, scoring.BOOT_B, scoring.BOOT_SEED)
    assert scoring.cluster_bootstrap_ci(groups, b=300, seed=5) == _old_cluster_bootstrap_ci(groups, 300, 5)
    nan = scoring.cluster_bootstrap_ci({})
    assert all(x != x for x in nan)

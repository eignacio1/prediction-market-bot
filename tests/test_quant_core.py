"""Known-answer tests for the quant core (W86.1). Each uses a case where the truth is known."""
import math
import random

from prediction_market_bot import quant
from prediction_market_bot.quant import inference as inf


def test_brier_logloss_known():
    assert abs(quant.brier(0.7, 1) - 0.09) < 1e-12
    assert abs(quant.log_loss(0.5, 1) - math.log(2)) < 1e-12
    assert quant.brier_mean([0.5, 0.5], [0, 1]) == 0.25


def test_brier_diff_sign_positive_means_model_better():
    d = quant.brier_diff([0.5, 0.5], [0.9, 0.1], [1, 0])
    assert all(x > 0 for x in d)


def test_murphy_identity_exact_when_p_constant_per_bin():
    ps = [0.15] * 10 + [0.85] * 10
    ys = [1] * 2 + [0] * 8 + [1] * 8 + [0] * 2
    m = quant.murphy(ps, ys)
    assert abs(m["brier"] - m["brier_binned"]) < 1e-12
    assert abs(m["reliability"] - ((0.15 - 0.2) ** 2 + (0.85 - 0.8) ** 2) / 2) < 1e-12


def test_ece_perfectly_calibrated_is_zero_and_miscalibrated_is_known():
    assert quant.ece([0.25] * 4, [1, 0, 0, 0]) == 0.0
    assert abs(quant.ece([0.9] * 10, [1] * 5 + [0] * 5) - 0.4) < 1e-12


def test_slope_intercept_recovers_known_overconfidence():
    rng = random.Random(1)
    ps, ys = [], []
    for _ in range(20000):
        z = rng.gauss(0, 1.5)                    # true logit
        ps.append(1 / (1 + math.exp(-2 * z)))    # forecast is 2x too extreme -> true slope 0.5
        ys.append(1 if rng.random() < 1 / (1 + math.exp(-z)) else 0)
    a, b = quant.slope_intercept(ps, ys)
    assert abs(b - 0.5) < 0.05 and abs(a) < 0.05
    assert all(math.isnan(v) for v in quant.slope_intercept([0.3, 0.4], [1, 1]))


def test_cluster_bootstrap_covers_known_mean_near_nominal():
    rng = random.Random(7)
    cover, reps = 0, 200
    for r in range(reps):
        d = {f"g{i}": [rng.gauss(0.3, 1) + rng.gauss(0, 1)] * 3 for i in range(40)}   # intra-cluster dependence
        _, lo, hi = quant.cluster_bootstrap(d, b=400, seed=r)
        cover += lo <= 0.3 <= hi
    assert 0.90 <= cover / reps <= 0.99


def test_power_and_mde_are_inverse():
    mde = quant.mde_paired(sd=0.1, n=400, alpha=0.05, power=0.8)
    assert abs(quant.power_paired(mde, 0.1, 400, 0.05) - 0.8) < 1e-9
    assert abs(quant.power_paired(0.0, 0.1, 400, 0.05) - 0.05) < 1e-9


def test_bh_recovers_fdr_on_simulated_mix():
    rng = random.Random(3)
    fdps, powers = [], []
    for _ in range(300):
        null = [rng.random() for _ in range(80)]
        true = [min(1.0, rng.random() ** 8) for _ in range(20)]    # strongly skewed to 0
        rej = quant.benjamini_hochberg(null + true, q=0.10)
        r = sum(rej)
        fdps.append(sum(rej[:80]) / r if r else 0.0)
        powers.append(sum(rej[80:]) / 20)
    assert sum(fdps) / len(fdps) <= 0.10 + 0.02          # E[FDP] = pi0*q = 0.08 at most
    assert sum(powers) / len(powers) > 0.5


def test_bonferroni_stricter_than_bh():
    p = [0.001, 0.02, 0.03, 0.4]
    assert quant.bonferroni(p) == [True, False, False, False]
    assert quant.benjamini_hochberg(p, 0.10) == [True, True, True, False]


def test_pooled_test_detects_effect_and_not_null_and_averages_within_game():
    rng = random.Random(5)
    eff = [(f"g{i}", 0.05 + rng.gauss(0, 0.1)) for i in range(150) for _ in range(3)]
    nul = [(f"g{i}", rng.gauss(0, 0.1)) for i in range(150) for _ in range(3)]
    e, n = quant.pooled_cluster_test(eff), quant.pooled_cluster_test(nul)
    assert e["n_games"] == 150 and e["p_one_sided"] < 0.01 and e["ci95"][0] > 0
    assert n["p_one_sided"] > 0.05 and n["ci95"][0] < 0 < n["ci95"][1]
    big = quant.pooled_cluster_test([("a", 1.0)] * 100 + [("b", 0.0)])
    assert abs(big["mean"] - 0.5) < 1e-12              # per-game mean, not per-row


def test_net_edge_and_fill_pnl_known():
    e = quant.net_edge(0.60, yes_bid=0.50, yes_ask=0.52)
    assert e["side"] == "yes" and abs(e["yes"] - (0.60 - 0.52 - 0.07 * 0.52 * 0.48)) < 1e-12
    n = quant.net_edge(0.30, yes_bid=0.50, yes_ask=0.52)
    assert n["side"] == "no" and abs(n["no"] - (0.70 - 0.50 - 0.07 * 0.25)) < 1e-12
    assert abs(quant.fill_pnl("yes", 0.52, 1) - (1 - 0.52 - 0.07 * 0.52 * 0.48)) < 1e-12
    assert abs(quant.fill_pnl("no", 0.50, 0) - (1 - 0.5 - 0.07 * 0.25)) < 1e-12
    # model-expected edge equals realised P&L averaged over the model's own probability (known answer)
    p = 0.6
    exp = p * quant.fill_pnl("yes", 0.52, 1) + (1 - p) * quant.fill_pnl("yes", 0.52, 0)
    assert abs(exp - e["yes"]) < 1e-12

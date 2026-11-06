"""W105.2 / B-052: counterfactual placement tools. Known-answer tests on simulated books."""
import numpy as np

from prediction_market_bot.quant import placement as pl


def _book(n=6000, thresh=0.70, drop=0.04, seed=3, games=300):
    """Simulated book: fill prob 0.3 everywhere; markout ~ N(0, 0.01) below `thresh`, N(-drop, 0.01) at/above."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        p = float(rng.uniform(0.05, 0.95))
        filled = bool(rng.random() < 0.3)
        mk = float(rng.normal(-drop if p >= thresh else 0.0, 0.01)) if filled else None
        rows.append({"game": f"g{i % games}", "price": p, "filled": filled, "mk": mk, "pnl": None,
                     "arm": "control" if i % 2 == 0 else "treatment"})
    return rows


def test_planted_adverse_selection_threshold_is_recovered():
    rows = _book(thresh=0.70)
    fl = [r for r in rows if r["filled"]]
    fit = pl.fit_price_threshold([r["price"] for r in fl], [r["mk"] for r in fl], [r["game"] for r in fl])
    assert abs(fit["threshold"] - 0.70) <= 0.03
    assert fit["ci90"][0] - 0.01 <= 0.70 <= fit["ci90"][1] + 0.01          # float grid: 0.7000000000000002
    assert abs(fit["mean_at_or_above"] + 0.04) < 0.005 and abs(fit["mean_below"]) < 0.005


def test_no_planted_effect_gives_no_large_step():
    rows = _book(drop=0.0)
    fl = [r for r in rows if r["filled"]]
    fit = pl.fit_price_threshold([r["price"] for r in fl], [r["mk"] for r in fl], [r["game"] for r in fl])
    assert abs(fit["mean_at_or_above"] - fit["mean_below"]) < 0.006        # nothing to find, step ~0


def test_bucket_markout_matches_planted_means():
    b = pl.bucket_markout(_book(thresh=0.70, drop=0.04), [0.0, 0.7, 1.01])
    assert abs(b[0]["mean"]) < 0.003 and abs(b[1]["mean"] + 0.04) < 0.003
    assert b[1]["lo"] <= b[1]["mean"] <= b[1]["hi"]
    assert (b[1]["price_lo"], b[1]["price_hi"]) == (0.7, 1.01)      # edges must survive the CI merge


def test_rule_that_skips_the_bad_region_gains_what_it_avoids():
    rows = _book(thresh=0.70, drop=0.04)
    base = pl.evaluate_rule(rows, lambda r: True)
    cap = pl.evaluate_rule(rows, lambda r: r["price"] < 0.70)
    assert abs(cap["share_posted"] - 0.72) < 0.03                          # skips ~28% of orders
    assert abs(cap["fill_rate"] - 0.30) < 0.03                             # fill rate is not changed by a filter on price here
    assert cap["net_per_order"]["mean"] > base["net_per_order"]["mean"]    # loss avoided
    assert abs(cap["net_per_order"]["mean"]) < 0.002                       # all that is left is ~0 markout
    assert cap["per_fill"]["n"] < base["per_fill"]["n"]


def test_rule_in_a_clean_book_costs_fills_and_gains_nothing():
    rows = _book(drop=0.0)
    cap = pl.evaluate_rule(rows, lambda r: r["price"] < 0.70)
    base = pl.evaluate_rule(rows, lambda r: True)
    assert abs(cap["net_per_order"]["mean"] - base["net_per_order"]["mean"]) < 0.002
    assert cap["posted"] < base["posted"]


def test_empty_rule_is_reported_not_crashed():
    assert pl.evaluate_rule(_book(n=50), lambda r: False)["posted"] == 0


def test_arm_contrast_sees_a_planted_arm_difference():
    rng = np.random.default_rng(1)
    rows = []
    for g in range(200):
        for arm, fr, mk in (("control", 0.4, -0.03), ("treatment", 0.2, -0.005)):
            for _ in range(5):
                f = bool(rng.random() < fr)
                rows.append({"game": f"g{g}", "price": 0.5, "filled": f, "mk": mk if f else None, "arm": arm})
    c = pl.arm_contrast(rows, "control", "treatment")
    assert c["diff_fill_rate"] < -0.1 and c["diff_fill_rate_ci90"][1] < 0
    expected = 0.2 * -0.005 - 0.4 * -0.03                                   # +0.011 per order
    assert abs(c["diff_net"] - expected) < 0.004
    assert pl.arm_contrast(rows, "control", "nope")["diff_net"] is None


def test_cluster_ci_is_wider_when_games_share_outcomes():
    rng = np.random.default_rng(2)
    iid = rng.normal(0, 1, 600)
    shared = np.repeat(rng.normal(0, 1, 60), 10)                            # 60 games x 10 correlated orders
    cl = [i // 10 for i in range(600)]
    w_iid = pl.cluster_mean_ci(iid, cl)
    w_sh = pl.cluster_mean_ci(shared, cl)
    assert (w_sh["hi"] - w_sh["lo"]) > 1.5 * (w_iid["hi"] - w_iid["lo"])

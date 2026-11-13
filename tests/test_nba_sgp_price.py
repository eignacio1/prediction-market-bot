"""W113.3 Part C known-answer tests for same-game combo pricing."""
import numpy as np
import pytest

from prediction_market_bot.nba_engine.sgp_price import GameDraws, LegSpec, build_leg, price_combo


def _g(n=20000, seed=0):
    r = np.random.default_rng(seed)
    z = r.integers(0, 2, n)                                   # one common cause: both stats high together
    pts = 10 + 10 * z + r.integers(0, 3, n)
    thr = 1 + 2 * z + r.integers(0, 2, n)
    home = 100 + r.integers(0, 20, n)
    away = 100 + r.integers(0, 20, n)
    return GameDraws(home, away, {("home", "p", "points"): pts, ("home", "p", "threes"): thr})


def test_single_leg_marginal_and_exact_semantics():
    g = GameDraws(np.array([100, 90, 100]), np.array([99, 95, 100]), {})
    assert build_leg(g, LegSpec("ml", side="home")).tolist() == [True, False, False]   # tie is not a win
    assert build_leg(g, LegSpec("spread", 5, "away")).tolist() == [False, True, False]
    assert build_leg(g, LegSpec("total", 195)).tolist() == [True, False, True]


def test_common_cause_gives_lift_above_one_and_joint_between_bounds():
    g = _g()
    r = price_combo(g, [LegSpec("player", 18, "home", "p", "points"), LegSpec("player", 3, "home", "p", "threes")])
    assert r["lift"] > 1.3 and r["frechet_lo"] <= r["p_joint"] <= r["frechet_hi"] and r["resolved"]


def test_independent_legs_have_lift_near_one_and_three_leg_works():
    g = _g()
    r = price_combo(g, [LegSpec("ml"), LegSpec("total", 215), LegSpec("team_total", 105, "away")])
    assert abs(r["lift"] - 1.0) < 0.05 and len(r["legs"]) == 3


def test_rejects_wrong_leg_count_and_flags_unresolved():
    g = _g()
    with pytest.raises(ValueError):
        price_combo(g, [LegSpec("ml")])
    r = price_combo(g, [LegSpec("total", 10_000), LegSpec("ml")])
    assert r["p_joint"] == 0.0 and not r["resolved"]

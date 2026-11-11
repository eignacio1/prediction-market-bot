import numpy as np

from prediction_market_bot.nba_engine import cross_reference as X
from prediction_market_bot.nba_engine import engine_v2 as V

P = V.V2Params(hca=2.5, tbias=0.0, sd_margin=12.0, sd_total=18.0,
               shift_margin={"exp_missing": -1.5}, shift_total={"exp_missing": -0.8})


def test_board_is_coherent_and_matches_simulation():
    rep = X.check_board(P, 3.0, 224.0)
    assert rep.ok, rep.violations
    assert rep.max_sim_gap < 0.01


def test_incoherent_board_is_caught():
    b = X.price_board(P, 3.0, 224.0)
    b.total[215] = 0.1   # lower line priced below a higher line
    rep = X.check_board(P, 3.0, 224.0, board=b)
    assert not rep.ok and any("total" in v for v in rep.violations)


def test_team_total_identity_and_symmetry():
    # home TT mean + away TT mean = total; with m=0 both teams priced identically
    b = X.price_board(P, 0.0, 224.0)
    assert all(abs(b.tt_home[n] - b.tt_away[n]) < 1e-12 for n in b.tt_home)
    assert abs(b.ml_home - 0.5) < 1e-9


def test_fact_moves_every_market_the_right_way():
    r = X.propagate_fact(P, 112.0, 110.0, {"exp_missing": 0.0}, {"exp_missing": 3.0})
    assert r["d_margin"] < 0 and r["d_total"] < 0
    assert r["all_agree"], r["sign_agrees"]
    assert r["delta_p"]["ml"] < 0 and r["delta_p"]["total"] < 0 and r["delta_p"]["tt_home"] < 0


def test_parlay_comes_from_one_joint_draw():
    # positively-correlated legs (home wins big, home scores a lot) exceed the product of marginals
    j = X.joint_prob(P, 3.0, 224.0, [("margin_ge", 8), ("home_ge", 120)], sims=100_000)
    h, a = V.simulate(P, 3.0, 224.0, n=100_000, seed=0)
    p1, p2 = float(np.mean((h - a) >= 8)), float(np.mean(h >= 120))
    assert j > p1 * p2

"""Known-answer tests for quant/sgp.py (W110.4)."""
import numpy as np
import pytest

from prediction_market_bot.nba_engine import engine as E
from prediction_market_bot.nba_engine import props as P
from prediction_market_bot.quant import sgp as S


def test_single_leg_joint_equals_marginal():
    s = E.simulate(100.0, 115.0, 112.0, 2.0, 4.0, 8.0, n=5000, seed=1)
    a = S.leg(s.margin, "ge", 1)
    assert S.joint(a) == S.marginal(a) == E.p_moneyline_home(s)


def test_pair_marginals_recovered_from_joint_with_complement():
    s = E.simulate(100.0, 115.0, 112.0, 2.0, 4.0, 8.0, n=5000, seed=2)
    a, b = S.leg(s.margin, "ge", 1), S.leg(s.total, "ge", 225)
    assert S.joint(a, b) + S.joint(a, ~b) == pytest.approx(S.marginal(a))
    assert S.joint(a, b) + S.joint(~a, b) == pytest.approx(S.marginal(b))
    assert S.joint(a, b) == pytest.approx(E.p_joint(s, 1, 225))


def test_independent_draws_give_lift_one_and_phi_zero():
    rng = np.random.default_rng(0)
    a, b = rng.random(400_000) < 0.4, rng.random(400_000) < 0.5
    assert S.lift(a, b) == pytest.approx(1.0, abs=0.02)
    assert S.phi(a, b) == pytest.approx(0.0, abs=0.01)


def test_known_correlation_recovered():
    # bivariate normal rho=0.6 -> P(X>0,Y>0) = 1/4 + asin(rho)/(2 pi); phi of the two sign indicators = (2/pi) asin(rho)
    rng = np.random.default_rng(3)
    rho = 0.6
    z = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], size=400_000)
    a, b = z[:, 0] > 0, z[:, 1] > 0
    assert S.joint(a, b) == pytest.approx(0.25 + np.arcsin(rho) / (2 * np.pi), abs=0.004)
    assert S.phi(a, b) == pytest.approx(2 / np.pi * np.arcsin(rho), abs=0.01)


def test_frechet_bounds_and_triple():
    rng = np.random.default_rng(4)
    x = rng.standard_normal(20_000)
    a, b, c = x > 0, x > 0.3, x < 1.0
    lo, hi = S.frechet_bounds(a, b, c)
    assert lo - 1e-12 <= S.joint(a, b, c) <= hi + 1e-12
    assert S.joint(a, b, c) == pytest.approx(np.mean((x > 0.3) & (x < 1.0)))


def test_comonotone_and_countermonotone():
    x = np.arange(1000)
    assert S.phi(x >= 500, x >= 500) == pytest.approx(1.0)
    assert S.phi(x >= 500, x < 500) == pytest.approx(-1.0)


def test_unequal_lengths_refused_and_resolved_flag():
    with pytest.raises(ValueError):
        S.joint(np.ones(5, bool), np.ones(6, bool))
    assert not S.resolved(0.0005, 4000) and S.resolved(0.2, 4000)


def test_engine_player_legs_share_draws_with_team_total():
    # a player's points can never exceed the team's draw: P(player>=k AND team<k) must be exactly 0
    s = E.simulate(100.0, 115.0, 112.0, 2.0, 4.0, 8.0, n=3000, seed=5)
    roster = P.TeamRoster(("a", "b", "c"), {st: [20.0, 12.0, 8.0] for st in P.STATS}, float(s.home_pts.mean()))
    d, _ = P.player_draws(s.home_pts, roster, "points", np.random.default_rng(0))
    assert S.joint(S.leg(d[:, 0], "ge", 30), S.leg(s.home_pts, "le", 29)) == 0.0
    k0, k1 = int(np.median(d[:, 0])), int(np.median(d[:, 1]))
    # teammates compete for the same points: negative implied correlation, opposed to team total which is positive
    assert S.phi(S.leg(d[:, 0], "ge", k0), S.leg(d[:, 1], "ge", k1)) < 0
    assert S.phi(S.leg(d[:, 0], "ge", k0), S.leg(s.home_pts, "ge", int(s.home_pts.mean()))) > 0

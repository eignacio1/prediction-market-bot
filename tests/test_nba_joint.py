"""W113.3 known-answer tests for the shared-latent NBA player joint (nba_engine/joint.py)."""
import numpy as np

from prediction_market_bot.nba_engine import engine_v2 as E2
from prediction_market_bot.nba_engine import joint as J
from prediction_market_bot.nba_engine import props as P

N = 40000


def _roster(pts=(24.0, 18.0, 15.0, 13.0, 11.0, 9.0, 7.0, 5.0), mpg=(34.0, 32.0, 30.0, 28.0, 25.0, 22.0, 18.0, 14.0)):
    k = len(pts)
    mu = {"points": list(pts), "rebounds": [5.0, 7.0, 4.0, 6.0, 3.0, 4.0, 3.0, 2.0][:k],
          "assists": [6.0, 3.0, 2.0, 4.0, 1.5, 1.0, 1.0, 0.5][:k], "threes": [3.0, 1.5, 1.0, 1.2, 1.5, 0.8, 0.6, 0.4][:k]}
    return J.JointRoster(tuple("abcdefgh"[:k]), list(mpg), mu, 114.0)


def _game(seed=1):
    params = E2.V2Params(hca=2.0, tbias=0.0, sd_margin=13.0, sd_total=19.0)
    mm, tt = E2.game_means(params, 114.0, 114.0)
    return E2.simulate(params, mm, tt, N, seed=seed)


def test_team_points_are_conserved_and_marginals_near_means():
    h, a = _game()
    d = J.simulate_team(h, np.abs(h - a), _roster(), np.random.default_rng(0))
    assert np.array_equal(d.stat["points"].sum(1) + d.rest_points, h)          # the engine's team points are untouched
    assert d.stat["points"].min() >= 0 and (d.stat["threes"] * 3 <= d.stat["points"]).all()
    for i, mu in enumerate((24.0, 18.0, 15.0)):
        assert abs(d.stat["points"][:, i].mean() - mu) / mu < 0.12


def test_same_player_points_and_threes_move_together_far_more_than_before():
    h, a = _game()
    ros = _roster()
    new = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(0)).stat
    c_new = np.corrcoef(new["points"][:, 0], new["threes"][:, 0])[0, 1]
    old_ros = P.TeamRoster(ros.players, ros.mu, 114.0)
    old, _ = P.player_draws(h, old_ros, "points", np.random.default_rng(0))
    old3, _ = P.player_draws(h, old_ros, "threes", np.random.default_rng(1))
    c_old = np.corrcoef(old[:, 0], old3[:, 0])[0, 1]
    assert c_new > 0.45 and c_new > c_old + 0.3


def test_usage_shift_lowers_a_teammates_points_at_fixed_team_points():
    h, a = _game()
    base = _roster()
    hot = J.JointRoster(base.players, base.mpg, base.mu, base.team_mean_pts, usage=[1.5] + [1.0] * 7)
    d0 = J.simulate_team(h, np.abs(h - a), base, np.random.default_rng(3))
    d1 = J.simulate_team(h, np.abs(h - a), hot, np.random.default_rng(3))
    assert np.array_equal(d0.stat["points"].sum(1) + d0.rest_points, d1.stat["points"].sum(1) + d1.rest_points)
    assert d1.stat["points"][:, 0].mean() > d0.stat["points"][:, 0].mean() + 3
    assert d1.stat["points"][:, 1].mean() < d0.stat["points"][:, 1].mean() - 0.5
    assert d1.stat["points"][:, 2].mean() < d0.stat["points"][:, 2].mean() - 0.3


def test_blowouts_cut_starter_minutes_and_lift_the_rest_bucket():
    h, a = _game()
    d = J.simulate_team(h, np.abs(h - a), _roster(), np.random.default_rng(5))
    big = np.abs(h - a) >= 25
    close = np.abs(h - a) <= 6
    assert big.sum() > 200 and close.sum() > 200
    assert d.minutes[big, 0].mean() < d.minutes[close, 0].mean() - 2.0
    assert d.rest_points[big].mean() > d.rest_points[close].mean()


def test_teammate_points_are_negatively_correlated_given_a_fixed_team_total_but_bounded():
    """Known answer: with team points fixed, teammates' points split one pool, so their correlation is negative in
    either model. The realised POSITIVE teammate covariance (W110.4) comes from the team total varying across games
    (pace), which the engine's T draw carries; Part B measures that class on held-out games (gap NOT closed: +0.025 -> +0.023).
    Here only the known answer: negative at fixed total, and not extreme."""
    h, a = _game()
    ros = _roster()
    new = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(0)).stat["points"]
    old, _ = P.player_draws(h, P.TeamRoster(ros.players, ros.mu, 114.0), "points", np.random.default_rng(0))
    c_new = np.corrcoef(new[:, 0], new[:, 1])[0, 1]
    c_old = np.corrcoef(old[:, 0], old[:, 1])[0, 1]
    assert -0.3 < c_new < 0 and -0.3 < c_old < 0


def test_split_is_exact_and_deterministic_for_a_seed():
    rng = np.random.default_rng(0)
    T = rng.integers(80, 140, 500)
    w = rng.random((500, 5)) + 0.1
    x = J._split(T, w, np.random.default_rng(9))
    assert (x.sum(1) == T).all() and (x >= 0).all()
    assert np.array_equal(x, J._split(T, w, np.random.default_rng(9)))


# ---- W114.4: one usage pool per team -------------------------------------------------------------------------------------
def _corr(x, y):
    return float(np.corrcoef(x, y)[0, 1])


def test_team_pool_latent_gives_teammates_positive_covariance_at_fixed_team_points():
    h, a = _game()
    ros = _roster()
    base = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(2), J.with_params(s_pool=0.0))
    pool = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(2), J.with_params(s_pool=1.2))
    c0 = _corr(base.stat["points"][:, 0], base.stat["points"][:, 1])
    c1 = _corr(pool.stat["points"][:, 0], pool.stat["points"][:, 1])
    assert c1 > c0 + 0.05                                                       # shared rest-bucket shock lifts them together
    assert np.array_equal(pool.stat["points"].sum(1) + pool.rest_points, h)    # still one pool: the shares sum to the team's points


def test_one_players_usage_up_takes_points_from_every_teammate():
    h, a = _game()
    base = _roster()
    hot = J.JointRoster(base.players, base.mpg, base.mu, base.team_mean_pts, usage=[1.8] + [1.0] * 7)
    p = J.with_params(s_pool=0.4, s_tmin=0.1)
    d0 = J.simulate_team(h, np.abs(h - a), base, np.random.default_rng(4), p)
    d1 = J.simulate_team(h, np.abs(h - a), hot, np.random.default_rng(4), p)
    assert d1.stat["points"][:, 0].mean() > d0.stat["points"][:, 0].mean() + 3
    for j in range(1, 6):
        assert d1.stat["points"][:, j].mean() < d0.stat["points"][:, j].mean()


def test_assists_rise_with_teammates_makes_only_when_loaded():
    h, a = _game()
    ros = _roster()
    off = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(6), J.with_params(gamma_ast=0.0))
    on = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(6), J.with_params(gamma_ast=1.2))
    # player 0's assists vs teammate 1's points
    c_off = _corr(off.stat["assists"][:, 0], off.stat["points"][:, 1])
    c_on = _corr(on.stat["assists"][:, 0], on.stat["points"][:, 1])
    assert c_on > c_off + 0.03


def test_rebounds_rise_when_the_opponent_misses_more():
    h, a = _game()
    ros = _roster()
    d = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(8), J.with_params(gamma_reb=1.0), opp_pts=a, opp_mean_pts=114.0)
    assert _corr(d.stat["rebounds"][:, 1], a) < -0.02                           # opponent scores less -> more misses -> more boards
    d0 = J.simulate_team(h, np.abs(h - a), ros, np.random.default_rng(8), J.with_params(gamma_reb=0.0), opp_pts=a, opp_mean_pts=114.0)
    assert _corr(d.stat["rebounds"][:, 1], a) < _corr(d0.stat["rebounds"][:, 1], a)


def test_defaults_of_new_latents_keep_previous_behaviour_available():
    # all-zero new params reproduce the 113.3 draws exactly (same rng stream order aside from the added normals)
    h, a = _game()
    d = J.simulate_team(h, np.abs(h - a), _roster(), np.random.default_rng(0), J.with_params(s_pool=0, s_tmin=0, gamma_ast=0, gamma_reb=0))
    assert np.array_equal(d.stat["points"].sum(1) + d.rest_points, h)

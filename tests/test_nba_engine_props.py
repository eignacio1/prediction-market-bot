import numpy as np

from prediction_market_bot.nba_engine import props as P

PTS = np.random.default_rng(1).normal(114, 12, 4000).round().astype(np.int64)
# Full rotation: mu sums to ~92% of the team's mean (the rest bucket is the other ~8%).
ROSTER = P.TeamRoster(("a", "b", "c", "d", "e", "f", "g", "h"), {
    "points": [25, 20, 16, 14, 11, 9, 6, 4], "rebounds": [10, 8, 6, 5, 4, 3, 2.5, 2.5],
    "assists": [8, 5, 4, 3, 2, 1.5, 1, 0.5], "threes": [3, 2.5, 2, 1.8, 1.2, 0.8, 0.5, 0.2]}, 114.0)


def test_player_points_sum_to_team_points_each_draw():
    d, total = P.player_draws(PTS, ROSTER, "points", np.random.default_rng(2))
    assert (d.sum(axis=1) == PTS).all() and (total == PTS).all()


def test_other_stats_split_sums_to_team_total_each_draw():
    for s in ("rebounds", "assists", "threes"):
        d, total = P.player_draws(PTS, ROSTER, s, np.random.default_rng(3))
        assert (d.sum(axis=1) == total).all() and (d >= 0).all()


def test_known_answer_mean_matches_input_mu():
    d, _ = P.player_draws(PTS, ROSTER, "points", np.random.default_rng(4))
    assert abs(d[:, 0].mean() - 0.92 * 25 / 105 * PTS.mean()) < 0.7     # share = (1-rest)*mu/sum(mu) of the draw's points
    d, _ = P.player_draws(PTS, ROSTER, "rebounds", np.random.default_rng(5))
    assert abs(d[:, 0].mean() - 10) < 0.6


def test_strike_probs_monotone_and_in_unit_interval():
    d, _ = P.player_draws(PTS, ROSTER, "assists", np.random.default_rng(6))
    pr = P.strike_probs(d[:, 0], [2, 4, 6, 8, 10, 12])
    v = [pr[k] for k in sorted(pr)]
    assert all(0 < x < 1 for x in v) and all(a >= b for a, b in zip(v, v[1:]))


def test_threes_covary_positively_with_points_rebounds_not():
    r = np.random.default_rng(7)
    _, t3 = P.player_draws(PTS, ROSTER, "threes", r)
    _, tr = P.player_draws(PTS, ROSTER, "rebounds", r)
    assert np.corrcoef(PTS, t3)[0, 1] > 0.15 > np.corrcoef(PTS, tr)[0, 1]


def test_fit_beta_recovers_elasticity():
    rng = np.random.default_rng(8)
    pts = rng.normal(112, 12, 5000)
    stat = 12 * (pts / 112) ** 1.5
    assert abs(P.fit_beta(pts, stat) - 1.5) < 0.05


def test_price_game_covers_all_stats_and_players():
    out = P.price_game(PTS, PTS, ROSTER, ROSTER, {s: [1, 5] for s in P.STATS}, seed=1)
    assert set(out) == set(P.STATS) and set(out["points"]) == set(ROSTER.players)

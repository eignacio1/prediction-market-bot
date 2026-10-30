"""W97.4 Part B: the NHL goals distribution and board (known-answer, coherence, settlement)."""
import numpy as np

from prediction_market_bot.nhl_engine import goals as G


def test_poisson_known_answer_and_correlation_zero():
    s = G.simulate(3.0, 2.5, k=np.inf, n=400000, seed=1)
    assert abs(s.reg_home.mean() - 3.0) < 0.02 and abs(s.reg_away.mean() - 2.5) < 0.02
    assert abs(G.score_corr(s)) < 0.01


def test_known_correlation_recovered_by_fit_dispersion():
    # truth: shared-factor k = 20 -> Cov = lam_h*lam_a/20
    s = G.simulate(3.0, 3.0, k=20.0, n=600000, seed=2)
    k_hat = G.fit_dispersion(s.reg_home, s.reg_away, np.full(len(s.reg_home), 3.0), np.full(len(s.reg_home), 3.0))
    assert 16 < k_hat < 25
    assert G.score_corr(s) > 0.03


def test_independent_gives_inf_dispersion():
    s = G.simulate(3.0, 3.0, k=np.inf, n=400000, seed=3)
    k_hat = G.fit_dispersion(s.reg_home, s.reg_away, np.full(len(s.reg_home), 3.0), np.full(len(s.reg_home), 3.0))
    assert k_hat > 200 or np.isinf(k_hat)


def test_regulation_tie_always_broken_by_one_credited_goal():
    s = G.simulate(2.8, 2.8, k=30.0, p_home_ot=0.5, n=100000, seed=4)
    tie = s.reg_home == s.reg_away
    assert tie.any()
    assert np.all((s.home - s.away)[tie] != 0) and np.all(np.abs((s.home - s.away)[tie]) == 1)
    assert np.all((s.home + s.away)[tie] == 2 * s.reg_home[tie] + 1)
    assert np.all((s.home == s.reg_home)[~tie])


def test_moneyline_sums_to_one_and_symmetry():
    s = G.simulate(3.0, 3.0, k=30.0, n=300000, seed=5)
    p = G.p_moneyline_home(s)
    assert abs(p - 0.5) < 0.01
    assert abs(G.p_moneyline_home(s) + float(np.mean(s.away > s.home)) - 1.0) < 1e-12


def test_ladders_monotone_and_coherent():
    s = G.simulate(3.2, 2.7, k=25.0, n=200000, seed=6)
    b = G.price_board(s)
    for key in ("home_wins_by_over", "away_wins_by_over", "total_over", "home_goals_over", "away_goals_over"):
        v = [b[key][x] for x in sorted(b[key])]
        assert all(v[i] >= v[i + 1] for i in range(len(v) - 1)), key
    # ML = 1 - P(away wins by over -0.5)  and  wins-by-over-0.5 equals the moneyline (no draws survive settlement)
    assert abs(b["moneyline_home"] - float(np.mean((s.home - s.away) > 0.5))) < 1e-12
    assert b["home_wins_by_over"][0.5] + b["away_wins_by_over"][0.5] == 1.0


def test_stronger_home_prices_higher_everywhere():
    a = G.price_board(G.simulate(3.0, 3.0, k=25.0, n=100000, seed=7))
    b = G.price_board(G.simulate(3.6, 2.6, k=25.0, n=100000, seed=7))
    assert b["moneyline_home"] > a["moneyline_home"]
    assert b["home_wins_by_over"][1.5] > a["home_wins_by_over"][1.5]
    assert b["home_goals_over"][3.5] > a["home_goals_over"][3.5]

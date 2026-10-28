import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import engine as E, board as B, ratings as R


def _s(**kw):
    a = dict(mu_poss=99.0, ppp_h=115.0, ppp_a=112.0, hca=2.0, s_p=4.0, s_e=11.0, n=40000, seed=1)
    a.update(kw)
    return E.simulate(**a)


def test_ladders_monotone_and_coherent():
    b = B.price_board(_s(), range(1, 20), range(200, 250, 3), range(95, 130, 5))
    for k in ("home_margin_ge", "away_margin_ge", "total_ge", "home_pts_ge", "away_pts_ge"):
        v = list(b[k].values())
        assert all(x >= y for x, y in zip(v, v[1:])), k
    # moneyline == margin >= 1, and home + away win partition the sample (no pushes)
    assert b["moneyline_home"] == b["home_margin_ge"][1]
    assert abs(b["moneyline_home"] + b["away_margin_ge"][1] - 1.0) < 1e-12


def test_joint_bounded_by_marginals():
    s = _s()
    j = E.p_joint(s, 1, 225)
    assert j <= min(E.p_margin_ge(s, 1), E.p_total_ge(s, 225)) + 1e-12
    assert j >= E.p_margin_ge(s, 1) + E.p_total_ge(s, 225) - 1 - 1e-12


def test_known_league_means_and_correlation_recovered():
    # known generating process: shared pace noise and zero efficiency noise => rho ~ +1 on regulation; with noise, rho = f(s_p, s_e)
    s_p, s_e, mu_p, ppp = 4.0, 11.0, 99.0, 113.5
    s = E.simulate(mu_p, ppp, ppp, 0.0, s_p, s_e, n=200000, seed=7)
    # overtime adds ~0.5 pts/team on average (ties ~4%), so the mean sits slightly above the regulation mean
    assert 0.0 < s.home_pts.mean() - mu_p * ppp / 100 < 0.9
    var_pts = (ppp / mu_p * mu_p / 100 * 0 + (ppp / 100) ** 2 * s_p ** 2 + (mu_p / 100) ** 2 * s_e ** 2)
    cov = (ppp / 100) ** 2 * s_p ** 2
    # regulation rho = cov/var; the ~4.5% overtime games add a common +~12 to both sides, lifting rho by ~0.045
    assert 0.02 < E.score_corr(s) - cov / var_pts < 0.07


def test_fit_shape_recovers_known_sds():
    s_p, s_e, mu_p, ppp = 4.0, 11.0, 99.0, 113.5
    s = E.simulate(mu_p, ppp, ppp, 0.0, s_p, s_e, n=200000, seed=3)
    fp, fe = E.fit_shape(s.margin - s.margin.mean(), s.total - s.total.mean(), mu_p, 2 * mu_p * ppp / 100)
    assert abs(fe - s_e) < 0.8 and abs(fp - s_p) < 0.8


def _toy_tg():
    # two teams, two seasons, 14 games each in the later one, strictly daily
    rows = []
    for season in (2020, 2021):
        base = pd.Timestamp(f"{season}-11-01", tz="UTC")
        for g in range(14):
            tip = base + pd.Timedelta(days=g * 2)
            for team, side in ((1, "home"), (2, "away")):
                rows.append(dict(game_id=f"{season}{g:03d}", team_id=team, side=side, season=season,
                                 pts=100.0 + g, opp_pts=100.0, pace=95.0 + (season - 2020) * 10, ortg=100.0 + g, drtg=100.0,
                                 tip_earliest=tip, tip_latest=tip, season_type="regular-season"))
    return pd.DataFrame(rows)


def test_ratings_leak_free_and_shrunk():
    tg = _toy_tg()
    r = R.add_ratings(tg, k=10.0)
    # 2020 has no previous season in the table => unpriced
    assert r[r.season == 2020]["ortg_hat"].isna().all()
    r21 = r[(r.season == 2021) & (r.team_id == 1)].sort_values("tip_earliest")
    # game 0 of 2021: n_prior 0 => rating equals previous-season mean exactly
    prior_mean = tg[(tg.season == 2020) & (tg.team_id == 1)]["ortg"].mean()
    assert abs(r21.iloc[0]["ortg_hat"] - prior_mean) < 1e-9
    # changing the *current* game's own outcome must not move its rating (nothing from the game being priced)
    t2 = tg.copy()
    mask = (t2.game_id == "2021005") & (t2.team_id == 1)
    t2.loc[mask, "ortg"] = 999.0
    r2 = R.add_ratings(t2, k=10.0)
    a = r[(r.game_id == "2021005") & (r.team_id == 1)]["ortg_hat"].iloc[0]
    b = r2[(r2.game_id == "2021005") & (r2.team_id == 1)]["ortg_hat"].iloc[0]
    assert a == b
    # but the next game's rating does move (as-of includes it once completed)
    a6 = r[(r.game_id == "2021006") & (r.team_id == 1)]["ortg_hat"].iloc[0]
    b6 = r2[(r2.game_id == "2021006") & (r2.team_id == 1)]["ortg_hat"].iloc[0]
    assert b6 > a6

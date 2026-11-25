"""W126.3: known-answer tests for the MLB PA model, the game simulation and the joint board (ADR-0073).

No network, no store: every input is planted so the right answer is known in closed form."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.mlb_engine import joint_board as J
from prediction_market_bot.mlb_engine import pa_model as M
from prediction_market_bot.mlb_engine.sim import simulate
from prediction_market_bot.quant import sgp

LG = np.array([.22, .085, .14, .043, .004, .03, .478])


def _P(rates):
    return np.tile(np.asarray(rates, float), (2, 2, 9, 1))


def _hr_k(h):
    r = np.zeros(7)
    r[0], r[5] = 1 - h, h
    return _P(r)


# ------------------------------------------------------------------ stage 3: PA outcome model
def test_classify_maps_every_event_and_drops_truncated():
    e = pd.Series(["strikeout", "walk", "hit_by_pitch", "single", "double", "triple", "home_run", "field_out",
                   "grounded_into_double_play", "field_error", "sac_fly", "truncated_pa"])
    assert M.classify(e).tolist()[:-1] == [0, 1, 1, 2, 3, 4, 5, 6, 6, 6, 6]
    assert np.isnan(M.classify(e).iloc[-1])


def test_combine_is_league_at_league_and_moves_with_each_side():
    lg = np.tile(LG, (3, 1))
    big = np.array([[1000 * .22, 0, 0, 0, 0, 0, 1000 * .78]] * 3)   # a batter who strikes out far more than league
    base = M.combine(lg * 1000, lg * 1000, lg)
    assert np.allclose(base, lg, atol=1e-3) and np.allclose(base.sum(1), 1.0)
    hi_k_bat = M.combine(np.tile([400, 85, 140, 43, 4, 30, 298], (3, 1)).astype(float) * 2, lg * 1000, lg)
    assert (hi_k_bat[:, 0] > lg[:, 0]).all()
    hi_k_pit = M.combine(lg * 1000, np.tile([400, 85, 140, 43, 4, 30, 298], (3, 1)).astype(float) * 2, lg)
    assert (hi_k_pit[:, 0] > lg[:, 0]).all()
    both = M.combine(np.tile([400, 85, 140, 43, 4, 30, 298], (3, 1)).astype(float) * 2,
                     np.tile([400, 85, 140, 43, 4, 30, 298], (3, 1)).astype(float) * 2, lg)
    assert (both[:, 0] > hi_k_bat[:, 0]).all() and (both[:, 0] > hi_k_pit[:, 0]).all()   # log5: both raise it further
    assert np.allclose(M.combine(np.zeros((1, 7)), np.zeros((1, 7)), lg[:1]), lg[:1])    # no history -> league
    del big


def _planted(n_days=70, k_star=0.40, seed=3):
    """Two teams, nine batters each; batter 1 strikes out at k_star, everyone else at 0.20 (rest split evenly)."""
    rng = np.random.default_rng(seed)
    pa, games, lus = [], [], []
    pk, ab = 1000, 0
    for day in range(n_days):
        date = pd.Timestamp("2025-05-01") + pd.Timedelta(days=day)
        pk += 1
        games.append({"game_pk": pk, "game_date": date, "home_team": "H", "away_team": "A", "home_runs": 0, "away_runs": 0,
                      "n_pitches": 0, "home_starter": 200, "away_starter": 100})
        for side, base, pit, team in (("away", 10, 200, "A"), ("home", 20, 100, "H")):
            for slot in range(1, 10):
                b = base + slot
                lus.append({"game_pk": pk, "team_side": side, "slot": slot, "batter": b})
                for _ in range(4):
                    k = k_star if b == 11 else 0.20
                    probs = np.array([k, .08, .14, .04, .004, .03, 0.0]); probs[6] = 1 - probs[:6].sum()
                    c = rng.choice(7, p=probs)
                    ev = ["strikeout", "walk", "single", "double", "triple", "home_run", "field_out"][c]
                    ab += 1
                    pa.append({"game_pk": pk, "game_date": date, "at_bat_number": ab, "pitcher": pit, "batter": b,
                               "p_throws": "R", "stand": "R", "home_team": "H", "away_team": "A", "inning": 1,
                               "inning_topbot": "Top" if side == "away" else "Bot", "events": ev})
    return pd.DataFrame(pa), pd.DataFrame(games), pd.DataFrame(lus)


def test_pa_model_recovers_a_planted_strikeout_rate_and_is_point_in_time():
    pa, games, lus = _planted()
    lg = M.fit_league(M.prep(pa))
    hist = M.PAHistory(pa, games)
    last = games.iloc[[-1]]
    inp = M.game_inputs(last, lus, hist, lg)
    k_star = inp["P"][0, 0, 0, 0, 0]                    # away side, vs starter, slot 2 is batter 12; slot 1 is batter 11
    k_norm = inp["P"][0, 0, 0, 1, 0]
    assert inp["batter_id"][0, 0, 0] == 11
    assert k_star > k_norm + 0.08 and abs(k_star - 0.40) < 0.09     # shrunk but recovered, well above the 0.20 field
    assert np.allclose(inp["P"].sum(-1), 1.0)
    # point in time: rewriting every PA ON the game date (and later) cannot move that game's probabilities
    pa2 = pa.copy()
    pa2.loc[pa2.game_date >= last.game_date.iloc[0], "events"] = "home_run"
    inp2 = M.game_inputs(last, lus, M.PAHistory(pa2, games), lg)
    assert np.allclose(inp["P"], inp2["P"])


# ------------------------------------------------------------------ stage 4: game simulation known answers
def test_all_strikeouts_scores_nothing_and_every_game_ends_by_tiebreak():
    d = simulate(_hr_k(0.0), np.array([25., 25.]), 2000, 1)
    assert d["away_runs_9"].sum() == 0 and d["tie_break"].all()
    assert (d["home_runs"] != d["away_runs"]).all() and (d["home_runs"] + d["away_runs"] == 1).all()


@pytest.mark.parametrize("h", [0.06, 0.10, 0.16])
def test_planted_run_environment_is_recovered(h):
    """Every PA a HR (h) or K (1-h): runs per half-inning is geometric, so nine full innings average 27h/(1-h) runs."""
    n = 40000
    d = simulate(_hr_k(h), np.array([25., 25.]), n, 11)
    mean, truth = d["away_runs_9"].mean(), 27 * h / (1 - h)
    var = 9 * (3 * h / (1 - h) ** 2) * 1.0               # NB: variance of runs per half-inning = 3h/(1-h)^2
    assert abs(mean - truth) < 4 * np.sqrt(var / n)
    h_hat = mean / (mean + 27)                           # invert the closed form: the plant comes back out
    assert abs(h_hat - h) < 0.004


def test_extra_innings_and_walkoffs_are_consistent():
    d = simulate(_P(LG), np.array([22., 22.]), 6000, 5)
    assert d["innings"].max() <= 15
    assert (d["home_runs"] != d["away_runs"]).all()                      # no draw ends level
    reg = d["innings"] <= 9
    assert reg.mean() > 0.85                                              # most games finish in regulation
    # a home team that wins in 8.5 innings (no bottom 9th) is the only way innings==9 with home winning w/o batting; both exist
    assert (d["home_runs"][reg] != d["away_runs"][reg]).all()


def test_batter_props_use_the_same_draws_as_team_runs():
    d = simulate(_P(LG), np.array([22., 22.]), 8000, 9)
    # a team cannot score without hits or walks, and a home run team total needs hits: hits-heavy draws score more
    tot_hits = d["hits"][:, 1].sum(1)
    assert np.corrcoef(tot_hits, d["home_runs"])[0, 1] > 0.5


# ------------------------------------------------------------------ stage 5: joint board
def test_ladders_are_monotone_and_hits_ge2_below_ge1():
    d = simulate(_P(LG), np.array([22., 22.]), 6000, 4)
    b = J.price_draws(d)
    for fam in ("ge_total_{}", "home_by_ge_{}", "away_by_ge_{}", "home_runs_ge_{}", "away_runs_ge_{}"):
        ks = sorted(int(k.rsplit("_", 1)[1]) for k in b if k.startswith(fam.split("{")[0]) and k[len(fam.split("{")[0]):].isdigit())
        vals = [b[fam.format(k)] for k in ks]
        assert len(vals) >= 7 and all(x >= y for x, y in zip(vals, vals[1:])), fam
    for side in ("away", "home"):
        for slot in range(1, 10):
            assert b[f"{side}_slot{slot}_hits_ge_1"] >= b[f"{side}_slot{slot}_hits_ge_2"]
    assert abs(b["p_home_ml"] + np.mean(d["away_runs"] > d["home_runs"]) - 1.0) < 1e-12


def test_same_game_legs_correlate_in_the_right_sign():
    n = 30000
    d = simulate(_P(LG), np.array([22., 22.]), n, 21)
    hr, ar = d["home_runs"], d["away_runs"]
    ind = lambda *l: sgp.independent(*l)
    home_ml, away_total5 = hr > ar, sgp.leg(ar, "ge", 5)
    home_total5, over9 = sgp.leg(hr, "ge", 5), sgp.leg(hr + ar, "ge", 9)
    h2 = sgp.leg(d["hits"][:, 1, 2], "ge", 2)
    assert sgp.joint(home_ml, home_total5) > ind(home_ml, home_total5) + 0.02         # my team scoring helps my win
    assert sgp.joint(home_ml, away_total5) < ind(home_ml, away_total5) - 0.02         # their scoring hurts it
    assert sgp.joint(home_total5, over9) > ind(home_total5, over9) + 0.02             # team total feeds the game total
    assert sgp.joint(h2, home_total5) > ind(h2, home_total5) + 0.01                   # my batter's 2 hits go with my runs
    assert sgp.joint(h2, away_total5) <= ind(h2, away_total5) + 0.01                  # but not with their runs
    # the module's joint_leg is the same arithmetic as the legs above
    assert J.joint_leg(d, ("ml", "home"), ("team", "home", 5)) == sgp.joint(home_ml, home_total5)
    assert J.joint_leg(d, ("hits", "home:3", 2)) == float(np.mean(d["hits"][:, 1, 2] >= 2))


def test_single_leg_joint_equals_its_marginal():
    d = simulate(_P(LG), np.array([22., 22.]), 3000, 2)
    b = J.price_draws(d)
    assert J.joint_leg(d, ("total", None, 8)) == pytest.approx(b["ge_total_8"])
    assert J.joint_leg(d, ("spread", "home", 2)) == pytest.approx(b["home_by_ge_2"])

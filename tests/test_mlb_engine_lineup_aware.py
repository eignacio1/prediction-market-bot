"""W106.4 Part A: lineup-aware inputs are point-in-time (no row uses a later game) and known-answer correct."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.mlb_engine import lineup_aware as la
from prediction_market_bot.mlb_engine import store

TEAMS = ["AAA", "BBB", "CCC", "DDD"]


def _synth(days=24, seed=3):
    """Tiny season: two games a day (+ one doubleheader day), 9 innings, starter to the 5th, then relievers."""
    rng = np.random.default_rng(seed)
    rows, pk = [], 1000
    roster = {t: {"bat": [100 * (i + 1) + k for k in range(12)], "st": 5000 + 10 * i,
                  "rel": [5001 + 10 * i, 5002 + 10 * i, 5003 + 10 * i]} for i, t in enumerate(TEAMS)}
    hand = {p: ("L" if p % 3 == 0 else "R") for t in TEAMS for p in [roster[t]["st"]] + roster[t]["rel"]}
    stand = {b: ("L" if b % 4 == 0 else "R") for t in TEAMS for b in roster[t]["bat"]}
    sched = []
    for d in range(days):
        date = pd.Timestamp("2024-04-01") + pd.Timedelta(days=d)
        a, b = (TEAMS[0], TEAMS[1]) if d % 2 == 0 else (TEAMS[1], TEAMS[0])
        c, e = (TEAMS[2], TEAMS[3]) if d % 3 else (TEAMS[3], TEAMS[2])
        sched += [(date, a, b), (date, c, e)]
        if d == 10:
            sched.append((date, a, b))  # doubleheader: same teams, same date
    for date, away, home in sched:
        pk += 1
        ab, hs, as_ = 0, 0, 0
        cnt = {away: 0, home: 0}
        for inn in range(1, 10):
            for half in ("Top", "Bot"):
                bat, fld = (away, home) if half == "Top" else (home, away)
                for k in range(3):
                    ab += 1
                    pitcher = roster[fld]["st"] if inn <= 5 else roster[fld]["rel"][inn % 3]
                    batter = roster[bat]["bat"][(cnt[bat] + (pk % 3)) % 11 % 12]
                    cnt[bat] += 1
                    ev = rng.choice(["single", "strikeout", "field_out", "home_run", "walk"])
                    wv = {"single": 0.9, "strikeout": 0.0, "field_out": 0.0, "home_run": 2.0, "walk": 0.7}[ev]
                    if ev in ("single", "home_run") and rng.random() < 0.6:
                        if half == "Top":
                            as_ += 1
                        else:
                            hs += 1
                    for pn in range(1, 4):
                        last = pn == 3
                        rows.append(dict(
                            game_pk=pk, game_date=date, at_bat_number=ab, pitch_number=pn, inning=inn,
                            inning_topbot=half, pitcher=pitcher, batter=batter, p_throws=hand[pitcher],
                            stand=stand[batter], home_team=home, away_team=away,
                            events=ev if last else np.nan, woba_value=wv if last else np.nan,
                            woba_denom=1.0 if last else np.nan, bb_type=np.nan, launch_speed=np.nan,
                            launch_angle=np.nan, estimated_woba_using_speedangle=np.nan,
                            post_home_score=hs, post_away_score=as_))
    p = pd.DataFrame(rows)
    pa = store.plate_appearances(p)
    return p, pa, store.games(p), store.lineups(p)


@pytest.fixture(scope="module")
def S():
    return _synth()


MU = 0.31


def _design(p, pa, g, lu):
    return la.design_lineup(g, lu, pa, p, MU)


def _key(df):
    return df.sort_values(["game_pk", "team_side"]).reset_index(drop=True)


FEATS = ["lineup_woba_vsH", "lineup_woba", "starter_woba_allowed", "starter_woba_vs_lineup", "starter_share",
         "pen_woba_allowed", "pen_fatigue", "park_logf", "pen_p1", "pen_p3"]


def test_design_has_expected_shape(S):
    d = _design(*S)
    assert len(d) == 2 * len(S[2]) and set(d.team_side) == {"home", "away"}
    assert d[FEATS].notna().all().all()


def test_truncation_invariance_no_later_data(S):
    """Dropping every day AFTER D must not change any feature of a game on D."""
    p, pa, g, lu = S
    full = _key(_design(p, pa, g, lu))
    for cut in ("2024-04-08", "2024-04-11", "2024-04-20"):
        D = pd.Timestamp(cut)
        keep = lambda df: df[df["game_date"] <= D]
        trunc = _key(_design(keep(p), keep(pa), keep(g), lu[lu.game_pk.isin(keep(g).game_pk)]))
        f = full[full.game_pk.isin(trunc.game_pk)].reset_index(drop=True)
        assert len(trunc) == len(f) > 0
        np.testing.assert_allclose(f[FEATS].to_numpy(float), trunc[FEATS].to_numpy(float), atol=1e-12)


def test_perturbing_same_day_and_future_outcomes_changes_nothing(S):
    """Scramble outcomes (wOBA, scores) and drop half the pitches on/after D: features of games ON D are identical,
    including both games of a doubleheader (the second never sees the first)."""
    p, pa, g, lu = S
    full = _key(_design(p, pa, g, lu))
    D = pd.Timestamp("2024-04-11")  # the doubleheader day
    rng = np.random.default_rng(0)
    p2, pa2, g2 = p.copy(), pa.copy(), g.copy()
    late = pa2["game_date"] >= D
    pa2.loc[late, "woba_value"] = rng.random(late.sum()) * 2
    g2.loc[g2["game_date"] >= D, ["home_runs", "away_runs"]] = rng.integers(0, 15, (int((g2.game_date >= D).sum()), 2))
    drop = (p2["game_date"] >= D) & (rng.random(len(p2)) < 0.5)
    p2 = p2[~drop]
    pert = _key(_design(p2, pa2, g2, lu))
    on = full["game_date"] == D
    assert on.sum() >= 6  # doubleheader day has 3 games
    a = full[on].reset_index(drop=True)
    b = pert[pert.game_pk.isin(a.game_pk)].reset_index(drop=True)
    np.testing.assert_allclose(a[FEATS].to_numpy(float), b[FEATS].to_numpy(float), atol=1e-12)
    # and the perturbation is real: a LATER game's features DO move (the test can fail)
    later = full["game_date"] > D + pd.Timedelta(days=5)
    assert not np.allclose(full[later][FEATS].to_numpy(float),
                           pert[pert.game_pk.isin(full[later].game_pk)][FEATS].to_numpy(float))


def test_asof_strictly_before():
    right = pd.DataFrame({"k": [1, 1], "game_date": pd.to_datetime(["2024-05-01", "2024-05-03"]), "x": [10.0, 30.0]})
    left = pd.DataFrame({"k": [1, 1, 1], "game_date": pd.to_datetime(["2024-05-01", "2024-05-02", "2024-05-03"])})
    out = la.asof_prior(left, right, "k")
    assert np.isnan(out.x[0]) and out.x[1] == 10.0 and out.x[2] == 10.0  # same day never visible, next day is


def test_bullpen_known_answer_window():
    d = pd.Timestamp("2024-06-10")
    daily = pd.DataFrame({"team": ["X"] * 4, "game_date": [d - pd.Timedelta(days=k) for k in (1, 2, 3, 4)],
                          "pen_pitches": [10.0, 20.0, 40.0, 80.0], "pen_bf": [3.0, 4, 5, 6],
                          "pen_num": [1.0, 1, 1, 1], "pen_den": [3.0, 4, 5, 6]})
    out = la.bullpen_features(daily, pd.DataFrame({"team": ["X"], "game_date": [d]}))
    assert out.pen_p1[0] == 10.0 and out.pen_p3[0] == 70.0  # day-4 load is outside the 3-day window
    assert out.pen_bf[0] == 18.0 and out.pen_den[0] == 18.0  # all four prior days feed the cumulative quality
    same = la.bullpen_features(daily, pd.DataFrame({"team": ["X"], "game_date": [d - pd.Timedelta(days=1)]}))
    assert same.pen_p1[0] == 20.0 and same.pen_p3[0] == 140.0  # shifting the target shifts the window


def test_park_known_answer_and_shrink():
    c = pd.DataFrame({"h_g": [60.0, 0.0, 30.0], "h_runs": [600.0, 0.0, 300.0],
                      "r_g": [60.0, 40.0, 30.0], "r_runs": [300.0, 400.0, 150.0]})
    f = la.park_log_factor(c)
    assert f[0] == pytest.approx(np.log(2.0) * 60 / 120)  # 2x runs at home, half-weight after shrink
    assert f[1] == 0.0  # no home games yet -> neutral
    assert f[2] == pytest.approx(np.log(2.0) * 30 / 90)  # fewer games -> more shrink


def test_platoon_counts_known_answer():
    pa = pd.DataFrame({"batter": [1, 1, 1], "game_date": pd.to_datetime(["2024-04-01"] * 2 + ["2024-04-02"]),
                       "p_throws": ["L", "R", "L"], "stand": ["R", "L", "R"],
                       "woba_value": [2.0, 0.0, 1.0], "woba_denom": [1.0, 1.0, 1.0]})
    c = la.batter_platoon_cum(pa)
    last = c.iloc[-1]
    assert (last.n, last.n_vsL, last.n_vsR) == (3, 2, 1)
    assert (last.num_vsL, last.den_vsL, last.num_vsR) == (3.0, 2.0, 0.0)
    assert (last.Lst_vsL, last.Lst_vsR) == (0.0, 1.0)  # only the R-pitcher PA came from the left side


def test_starter_share_prior_and_learning():
    p, pa, g, lu = _synth(days=3)
    d = _design(p, pa, g, lu)
    first = d.sort_values("game_date").iloc[0]
    assert first.starter_share == pytest.approx(la.BF_START0 / la.BF_TEAM)  # no history -> the league prior

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.nfl_engine import matchup_cross as M


def _plays(rows):
    cols = ["season", "week", "game_id", "posteam", "defteam", "play_type", "epa", "success", "sack", "qb_hit", "season_type"]
    return pd.DataFrame(rows, columns=cols)


def _tg(season, week, team, opp, pass_epa, pass_n, rush_succ, rush_n, pressured):
    return dict(season=season, week=week, game_id=f"{season}_{week}_{team}_{opp}", team=team, opp=opp, pass_epa=pass_epa,
                pass_n=pass_n, rush_succ=rush_succ, rush_n=rush_n, pressured=pressured)


def test_build_counts_known_answer():
    rows = [(2023, 1, "g", "A", "B", "pass", 0.5, 1, 0, 0, "REG"), (2023, 1, "g", "A", "B", "pass", -1.0, 0, 1, 0, "REG"),
            (2023, 1, "g", "A", "B", "run", 0.1, 1, 0, 0, "REG"), (2023, 1, "g", "A", "B", "run", -0.2, 0, 0, 0, "REG"),
            (2023, 1, "g", "A", "B", "pass", 0.2, 1, 0, 1, "REG"), (2023, 1, "g", "A", "B", "punt", 0.0, 0, 0, 0, "REG"),
            (2023, 1, "p", "A", "B", "pass", 9.0, 1, 0, 0, "POST")]
    tg = M.build_team_games(_plays(rows))
    r = tg.iloc[0]
    assert len(tg) == 1 and r.team == "A" and r.opp == "B"
    assert (r.pass_n, r.rush_n, r.pressured) == (3, 2, 2)
    assert r.pass_epa == pytest.approx(-0.3) and r.rush_succ == 1


def test_point_in_time_excludes_current_and_future_weeks():
    tg = pd.DataFrame([_tg(2023, 1, "A", "B", 10.0, 10, 5, 10, 1), _tg(2023, 2, "A", "C", -99.0, 10, 0, 10, 9)])
    b = M.MatchupBook(tg)
    # week 2 sees only week 1; week 1 sees nothing (league is NaN -> cross 0)
    assert b.cross(2023, 1, "A", "B", "pass") == 0.0
    r2 = b.rating(2023, 2, "A", "off", "pass")
    assert r2 > 0                      # week-2 disaster (-99) invisible at week 2
    assert b.rating(2023, 3, "A", "off", "pass") < 0   # visible at week 3


def test_shrink_known_answer_and_symmetry():
    # one game: A offence 100 plays at +0.2 EPA; league == that single game's mean (0.2) -> rating == league, cross == 0
    tg = pd.DataFrame([_tg(2023, 1, "A", "B", 20.0, 100, 0, 1, 0)])
    b = M.MatchupBook(tg)
    assert b.cross(2023, 2, "A", "B", "pass") == pytest.approx(0.0)
    # two offences, league mean 0.1; A +0.2 on n=150 shrunk by k=150 -> 0.1 + (0.2-0.1)*0.5 = 0.15
    tg = pd.DataFrame([_tg(2023, 1, "A", "X", 30.0, 150, 0, 1, 0), _tg(2023, 1, "C", "Y", 0.0, 150, 0, 1, 0)])
    b = M.MatchupBook(tg)
    assert b.rating(2023, 2, "A", "off", "pass") == pytest.approx(0.15)
    # a strong offence meeting a defence that allows more than league -> positive cross; vs a stingy defence -> smaller
    assert b.cross(2023, 2, "A", "Y", "pass") != b.cross(2023, 2, "A", "X", "pass")


def test_prior_season_decay_weight():
    tg = pd.DataFrame([_tg(2022, 1, "A", "B", 30.0, 150, 0, 1, 0), _tg(2022, 1, "C", "D", 0.0, 150, 0, 1, 0)])
    b = M.MatchupBook(tg)
    wk1 = b.rating(2023, 1, "A", "off", "pass")      # only prior season, weight 0.5
    # weighted n = 75, league 0.1, A mean 0.2: (0.2*75... ) numerator 15 + 150*0.1 = 30 ; denom 75+150 -> 0.1333
    assert wk1 == pytest.approx((0.5 * 30 + 150 * 0.1) / (0.5 * 150 + 150))
    assert np.isnan(b.rating(2026, 1, "A", "off", "pass"))   # data 4 seasons old is ignored: nothing to rate from


def test_rank_same_week_known_answer():
    rows = []
    for s, v in ((2020, 0.0), (2021, 0.1), (2022, 0.2)):
        rows += [_tg(s, 1, "A", "B", v * 150, 150, 0, 1, 0), _tg(s, 1, "C", "D", 0.0, 150, 0, 1, 0)]
    rows += [_tg(2023, 1, "A", "B", 60.0, 150, 0, 1, 0), _tg(2023, 1, "C", "D", 0.0, 150, 0, 1, 0)]
    b = M.MatchupBook(pd.DataFrame(rows))
    r = b.rank_same_week(2023, 2, "A", "off", "pass", range(2021, 2023))
    assert r["n_hist"] > 0 and 0.0 <= r["pct"] <= 1.0
    assert r["pct"] >= 0.5      # +0.4 EPA/play offence ranks in the top half of earlier same-week ratings


def test_terms_scale_by_volume():
    tg = pd.DataFrame([_tg(2023, 1, "A", "X", 30.0, 150, 100, 150, 15), _tg(2023, 1, "C", "Y", 0.0, 150, 50, 150, 30)])
    b = M.MatchupBook(tg)
    t = b.terms(2023, 2, "A", "Y")
    assert t.pass_ == pytest.approx(M.PLAYS["pass"] * b.cross(2023, 2, "A", "Y", "pass"))
    assert t.rush == pytest.approx(M.PLAYS["rush"] * b.cross(2023, 2, "A", "Y", "rush"))

"""Point-in-time contract tests (W73.2). Synthetic frames always run; real-store tests run when the store is built.

Positive control: the leaky filters a careless query would use are shown to LEAK on the same fixture, and
``assert_no_leak`` is shown to catch them - so a passing contract test cannot be a test that detects nothing.
"""
import os
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.nfl_point_in_time import (
    LeakError, PointInTime, kickoff_table)

G = [
    # game_id, season, week, gameday, gametime, weekday
    ("2024_01_A_B", 2024, 1, "2024-09-05", "20:20", "Thursday"),
    ("2024_01_C_D", 2024, 1, "2024-09-08", "13:00", "Sunday"),
    ("2024_01_E_F", 2024, 1, "2024-09-08", "16:25", "Sunday"),
    ("2024_01_G_H", 2024, 1, "2024-09-09", "20:15", "Monday"),
    ("2024_02_A_C", 2024, 2, "2024-09-12", "20:15", "Thursday"),
    ("2024_02_B_D", 2024, 2, "2024-09-15", "13:00", "Sunday"),
    ("2024_03_A_D", 2024, 3, "2024-09-22", "13:00", "Sunday"),
    ("2024_18_X_Y", 2024, 18, "2025-01-04", "16:30", "Saturday"),
    ("2024_19_X_Z", 2024, 19, "2025-01-11", None, "Saturday"),
]


@pytest.fixture
def games():
    return pd.DataFrame(G, columns=["game_id", "season", "week", "gameday", "gametime", "weekday"]).assign(
        home_score=1, away_score=2, spread_line=-3.0, temp=70, home_qb_id="q", referee="Ref",
        home_team="H", away_team="A", location="Home", stadium="S", stadium_id="s", roof="outdoors",
        surface="grass", div_game=0, home_rest=7, away_rest=7, home_coach="c", away_coach="d", game_type="REG")


@pytest.fixture
def pit(games):
    return PointInTime(games)


def plays(games):
    # three plays in every game
    return pd.DataFrame([(g, i) for g in games.game_id for i in range(3)], columns=["game_id", "play_id"])


def test_kickoff_eastern_to_utc_and_dst(pit):
    assert pit.kickoff("2024_01_C_D") == pd.Timestamp("2024-09-08 17:00", tz="UTC")   # EDT = UTC-4
    assert pit.kickoff("2024_18_X_Y") == pd.Timestamp("2025-01-04 21:30", tz="UTC")   # EST = UTC-5


def test_missing_gametime_is_imputed_to_midnight_eastern_and_flagged(games):
    k = kickoff_table(games)
    assert bool(k.at["2024_19_X_Z", "kickoff_imputed"]) and not bool(k.at["2024_01_C_D", "kickoff_imputed"])
    assert k.at["2024_19_X_Z", "kickoff_utc"] == pd.Timestamp("2025-01-11 05:00", tz="UTC")


def test_post_game_view_excludes_g_later_games_and_same_day_earlier_game(pit, games):
    p = plays(games)
    v = pit.view(p, "post_game", "2024_01_E_F")                 # 16:25 Sunday
    assert set(v.game_id) == {"2024_01_A_B"}                    # Thursday only; 13:00 game is < 4h earlier
    assert "2024_01_E_F" not in set(v.game_id) and "2024_01_C_D" not in set(v.game_id)
    pit.assert_no_leak(v, "post_game", "2024_01_E_F")


def test_post_game_view_includes_a_game_that_finished_well_before(pit, games):
    v = pit.view(plays(games), "post_game", "2024_01_G_H")      # Monday night
    assert set(v.game_id) == {"2024_01_A_B", "2024_01_C_D", "2024_01_E_F"}


def test_first_game_of_the_data_sees_nothing(pit, games):
    assert pit.view(plays(games), "post_game", "2024_01_A_B").empty


def test_positive_control_naive_filters_leak_and_are_caught(pit, games):
    p = plays(games).merge(games[["game_id", "week", "season"]], on="game_id")
    g = "2024_01_E_F"
    naive_week = p[(p.season == 2024) & (p.week <= 1)]            # "same week or earlier" - the classic leak
    naive_ne = p[p.game_id != g]                                   # "everything but G" - leaks the future
    for leaky in (naive_week, naive_ne):
        with pytest.raises(LeakError):
            pit.assert_no_leak(leaky, "post_game", g)
    pit.assert_no_leak(pit.view(p, "post_game", g), "post_game", g)  # the contract's own view passes


def test_property_no_game_ever_sees_itself_or_a_later_kickoff(pit, games):
    for gid in games.game_id:
        seen = pit.completed_before(gid)
        assert gid not in seen
        assert all(pit.kickoff(s) < pit.kickoff(gid) for s in seen)


def test_weekly_rule_thursday_excludes_week_of_sunday_includes_it(pit):
    inj = pd.DataFrame({"season": [2024] * 3, "week": [1, 2, 3], "gsis_id": ["a", "b", "c"]})
    thu = pit.view(inj, "weekly", "2024_02_A_C")                   # Thursday week 2
    assert list(thu.week) == [1]
    sun = pit.view(inj, "weekly", "2024_02_B_D")                   # Sunday week 2
    assert list(sun.week) == [1, 2]
    pit.assert_no_leak(sun, "weekly", "2024_02_B_D")
    with pytest.raises(LeakError):
        pit.assert_no_leak(inj, "weekly", "2024_02_A_C")
    assert pit.view(inj.assign(week=float("nan")), "weekly", "2024_03_A_D").empty   # unknown week never usable


def test_weekly_rule_saturday_playoff_excludes_week_of(pit):
    inj = pd.DataFrame({"season": [2024, 2024], "week": [17, 18], "gsis_id": ["a", "b"]})
    assert list(pit.view(inj, "weekly", "2024_18_X_Y").week) == [17]


def test_dated_rule_uses_timestamp_and_falls_back_to_weekly_for_old_schema(pit):
    dc = pd.DataFrame({"dt": ["2024-09-08T16:59:59Z", "2024-09-08T17:00:00Z", "2024-09-08T17:00:01Z"]})
    v = pit.view(dc, "dated", "2024_01_C_D")                       # kickoff 17:00:00Z exactly
    assert len(v) == 1                                             # strict: the 17:00:00 snapshot is excluded
    pit.assert_no_leak(v, "dated", "2024_01_C_D")
    old = pd.DataFrame({"season": [2024, 2024], "week": [1, 2]})   # no dt column
    assert list(pit.view(old, "dated", "2024_02_B_D").week) == [1, 2]


def test_pregame_context_is_a_whitelist(pit, games):
    ctx = pit.pregame_context(games, "2024_02_B_D")
    for forbidden in ("home_score", "away_score", "spread_line", "temp", "home_qb_id"):
        assert forbidden not in ctx
    assert ctx["roof"] == "outdoors" and ctx["home_rest"] == 7 and ctx["referee"] == "Ref"
    assert pit.pregame_context(games, "2024_02_A_C")["referee"] is None   # Thursday: crew assignment untimed


def test_unresolvable_kickoff_is_refused(games):
    games.loc[0, "gameday"] = None
    with pytest.raises(ValueError):
        PointInTime(games)

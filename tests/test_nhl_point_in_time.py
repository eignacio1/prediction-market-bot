"""Point-in-time contract tests for the NHL event store (W83.3). Synthetic frames, no network.

Positive control: the leaky filters a careless query would use are shown to LEAK on the same fixture and
``assert_no_leak`` is shown to catch them, so a passing contract test cannot be a test that detects nothing.
"""
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.nhl_point_in_time import (
    BUFFER_PLAYOFF, BUFFER_REGULAR, LeakError, PointInTime, start_table)

G = [
    # game_id, game_type, start (UTC)
    (1, 2, "2025-10-21T23:00:00Z"),
    (2, 2, "2025-10-22T02:00:00Z"),    # starts 3h after game 1 -> game 1 may still be running (4h buffer)
    (3, 2, "2025-10-22T23:00:00Z"),
    (4, 3, "2026-04-20T23:00:00Z"),    # playoff game
    (5, 3, "2026-04-21T02:00:00Z"),    # 3h later: playoff buffer 9h, game 4 may still be in overtime
    (6, 3, "2026-04-21T23:00:00Z"),
]


@pytest.fixture
def games():
    return pd.DataFrame(G, columns=["game_id", "game_type", "start_time_utc"]).assign(
        season=2025, venue="X", neutral_site=False, home_team_id=1, home="AAA", away_team_id=2, away="BBB",
        game_date_et="2025-10-21", home_score=3, away_score=2, game_state="OFF")


@pytest.fixture
def pit(games):
    return PointInTime(start_table(games))


def rows(games):
    return pd.DataFrame([(g, i) for g in games.game_id for i in range(3)], columns=["game_id", "n"])


def test_game_in_progress_is_not_usable(pit, games):
    assert 1 not in pit.completed_before(2)          # 23:00Z + 4h > 02:00Z
    assert pit.completed_before(3) == frozenset({1, 2})


def test_playoff_buffer_is_longer(pit):
    assert BUFFER_PLAYOFF > BUFFER_REGULAR
    assert 4 not in pit.completed_before(5)          # 23:00Z + 9h = 08:00Z > 02:00Z: may still be in overtime
    assert pit.completed_before(6) == frozenset({1, 2, 3, 4, 5})   # 02:00Z + 9h = 11:00Z <= 23:00Z


def test_view_excludes_g_itself_and_later(pit, games):
    v = pit.view(rows(games), "post_game", 3)
    assert set(v.game_id) == {1, 2}
    pit.assert_no_leak(v, "post_game", 3)


def test_earliest_game_has_empty_history(pit, games):
    assert pit.view(rows(games), "post_game", 1).empty


def test_season_static_refused(pit, games):
    with pytest.raises(ValueError):
        pit.view(rows(games), "season_static", 3)


def test_unknown_kind_refused(pit, games):
    with pytest.raises(ValueError):
        pit.view(rows(games), "snapshot", 3)


def test_missing_start_instant_is_a_build_error(games):
    bad = games.copy()
    bad.loc[0, "start_time_utc"] = None
    with pytest.raises(ValueError):
        PointInTime(start_table(bad))


def test_pregame_context_has_no_score_or_state(pit, games):
    ctx = pit.pregame_context(games, 3)
    assert "home_score" not in ctx and "game_state" not in ctx and ctx["home"] == "AAA"


def test_positive_control_naive_filters_leak_and_are_caught(pit, games):
    r = rows(games)
    start = pit.start(3)
    naive_same_day = r[r.game_id.map(pit.t["start"]).dt.date <= start.date()]  # includes G itself
    assert 3 in set(naive_same_day.game_id)
    with pytest.raises(LeakError):
        pit.assert_no_leak(naive_same_day, "post_game", 3)
    naive_started = r[r.game_id.map(pit.t["start"]) < pit.start(2)]          # started before G=2, not yet finished
    assert 1 in set(naive_started.game_id)
    with pytest.raises(LeakError):
        pit.assert_no_leak(naive_started, "post_game", 2)


@pytest.mark.parametrize("gid", [1, 2, 3, 4, 5, 6])
def test_property_view_never_leaks(pit, games, gid):
    v = pit.view(rows(games), "post_game", gid)
    pit.assert_no_leak(v, "post_game", gid)
    for other in set(v.game_id):
        assert pit.t.at[other, "end_latest"] <= pit.start(gid)

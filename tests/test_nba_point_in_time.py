"""Point-in-time contract tests for the NBA event store (W78.4). Synthetic frames always run.

Positive control: the leaky filters a careless query would use are shown to LEAK on the same fixture, and
``assert_no_leak`` is shown to catch them - so a passing contract test cannot be a test that detects nothing.
"""
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import (
    COMPLETION_BUFFER, LeakError, PointInTime, tip_table)

S = [
    # game_id, game_date (ET), home, away
    ("G1", "2025-10-21", "BOS", "NYK"),   # tip known 23:30Z = 19:30 EDT
    ("G2", "2025-10-21", "LAL", "GSW"),   # tip known 02:00Z next day = 22:00 EDT
    ("G3", "2025-10-22", "MIA", "ORL"),   # tip known 23:00Z
    ("G4", "2025-10-22", "DEN", "UTA"),   # no ESPN row: imputed to the ET day
    ("G5", "2025-10-23", "BOS", "MIA"),   # no ESPN row: imputed
    ("G6", "2025-12-01", "NYK", "BOS"),   # known, EST
]
E = [
    ("2025-10-21T23:30Z", "BOS", "NY"),    # ESPN abbreviation NY -> NYK
    ("2025-10-22T02:00Z", "LAL", "GS"),    # 22:00 EDT on the 21st -> still the 21st ET
    ("2025-10-22T23:00Z", "MIA", "ORL"),
    ("2025-12-01T00:30Z", "NY", "BOS"),    # 19:30 EST on 11-30: a different ET day than game_date 12-01 -> unmatched
]


@pytest.fixture
def schedule():
    return pd.DataFrame(S, columns=["game_id", "game_date", "home_team_abbreviation", "away_team_abbreviation"]).assign(
        season=2026, season_type="Regular Season", home_pts=100, away_pts=99, home_wl="W")


@pytest.fixture
def espn():
    return pd.DataFrame(E, columns=["date", "home_abbreviation", "away_abbreviation"])


@pytest.fixture
def tips(schedule, espn):
    return tip_table(schedule, espn)


@pytest.fixture
def pit(tips):
    return PointInTime(tips)


def rows(schedule):
    return pd.DataFrame([(g, i) for g in schedule.game_id for i in range(3)], columns=["game_id", "order_index"])


def test_join_uses_real_tip_and_et_day_and_abbreviation_map(tips):
    assert pd.Timestamp("2025-10-21 23:30", tz="UTC") == tips.at["G1", "tip_earliest"] == tips.at["G1", "tip_latest"]
    assert not tips.at["G1", "tip_imputed"]
    assert not tips.at["G2", "tip_imputed"]                         # 02:00Z on the 22nd is the 21st in Eastern
    assert tips.at["G2", "tip_earliest"] == pd.Timestamp("2025-10-22 02:00", tz="UTC")


def test_unmatched_game_gets_conservative_eastern_day_bounds(tips):
    assert tips.at["G4", "tip_imputed"]
    assert tips.at["G4", "tip_earliest"] == pd.Timestamp("2025-10-22 04:00", tz="UTC")   # 00:00 EDT
    assert tips.at["G4", "tip_latest"] == pd.Timestamp("2025-10-23 04:00", tz="UTC")     # 24:00 EDT
    assert tips.at["G6", "tip_imputed"]                              # ET-day mismatch: refused, not guessed


def test_ambiguous_espn_match_is_not_used(schedule):
    dup = pd.DataFrame([("2025-10-21T23:30Z", "BOS", "NY"), ("2025-10-21T20:00Z", "BOS", "NY")],
                       columns=["date", "home_abbreviation", "away_abbreviation"])
    assert tip_table(schedule, dup).at["G1", "tip_imputed"]


def test_post_game_view_excludes_g_same_day_and_later(pit, schedule):
    v = pit.view(rows(schedule), "post_game", "G3")                 # tips 10-22 23:00Z
    assert set(v.game_id) == {"G1", "G2"}                           # G2 02:00Z + 4h <= 23:00Z
    assert "G3" not in set(v.game_id) and "G4" not in set(v.game_id)
    pit.assert_no_leak(v, "post_game", "G3")


def test_game_inside_the_completion_buffer_is_not_visible(pit, schedule):
    # G2 tips 02:00Z on the 22nd; G1 tips 23:30Z on the 21st, only 2.5h earlier -> within the 4h buffer
    assert COMPLETION_BUFFER == pd.Timedelta(hours=4)
    assert "G1" not in pit.completed_before("G2")


def test_imputed_candidate_is_treated_as_finishing_as_late_as_possible(pit):
    # G4 (imputed) ends no earlier than 10-23 04:00Z + 4h = 08:00Z; G5 (imputed) starts at 10-23 04:00Z -> not visible
    assert "G4" not in pit.completed_before("G5")
    # a known game on a later day sees it
    assert "G4" in pit.completed_before("G6") or pit.tip_earliest("G6") <= pd.Timestamp("2025-10-23 08:00", tz="UTC")


def test_first_game_of_the_data_sees_nothing(pit, schedule):
    assert pit.view(rows(schedule), "post_game", "G1").empty


def test_positive_control_naive_filters_leak_and_are_caught(pit, schedule):
    p = rows(schedule).merge(schedule[["game_id", "game_date"]], on="game_id")
    g = "G3"
    naive_same_day_or_earlier = p[p.game_date <= "2025-10-22"]       # "same date or earlier" - the classic leak
    naive_ne = p[p.game_id != g]                                      # "everything but G" - leaks the future
    for leaky in (naive_same_day_or_earlier, naive_ne):
        with pytest.raises(LeakError):
            pit.assert_no_leak(leaky, "post_game", g)
    pit.assert_no_leak(pit.view(p, "post_game", g), "post_game", g)   # the contract's own view passes


def test_property_no_game_ever_sees_itself_or_a_game_that_may_still_be_unfinished(pit, tips):
    for gid in tips.index:
        seen = pit.completed_before(gid)
        assert gid not in seen
        assert all(tips.at[s, "tip_latest"] + COMPLETION_BUFFER <= pit.tip_earliest(gid) for s in seen)


def test_pregame_context_is_a_whitelist(pit, schedule):
    ctx = pit.pregame_context(schedule, "G3")
    for forbidden in ("home_pts", "away_pts", "home_wl"):
        assert forbidden not in ctx
    assert ctx["home_team_abbreviation"] == "MIA" and ctx["tip_imputed"] is False


def test_season_static_tables_are_refused(pit):
    with pytest.raises(ValueError):
        pit.view(pd.DataFrame({"coach_id": [1]}), "season_static", "G3")
    with pytest.raises(LeakError):
        pit.assert_no_leak(pd.DataFrame({"coach_id": [1]}), "season_static", "G3")


def test_snapshot_never_backfills_history(pit):
    inj = pd.DataFrame({"as_of_date": ["2025-10-22T12:00:00Z"] * 2, "athlete_id": [1, 2]})
    assert pit.view(inj, "snapshot", "G1").empty                      # snapshot post-dates G1
    assert len(pit.view(inj, "snapshot", "G5")) == 2                  # G5 tips on/after the 23rd ET
    with pytest.raises(LeakError):
        pit.assert_no_leak(inj, "snapshot", "G1")


def test_unresolvable_tip_is_refused(schedule):
    t = tip_table(schedule.assign(game_date=[None] + list(schedule.game_date[1:])), None)
    with pytest.raises(ValueError):
        PointInTime(t)


def test_date_only_snapshot_counts_from_end_of_day(pit):
    inj = pd.DataFrame({"as_of_date": ["2025-10-22"], "athlete_id": [1]})   # captured sometime on the 22nd
    assert pit.view(inj, "snapshot", "G4").empty                              # G4 may tip 10-22 04:00Z: not knowable
    assert len(pit.view(inj, "snapshot", "G5")) == 1                          # G5 earliest 10-23 04:00Z >= 10-23 00:00Z + 4h
    with pytest.raises(LeakError):
        pit.assert_no_leak(inj, "snapshot", "G4")

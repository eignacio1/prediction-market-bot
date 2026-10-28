"""Known-answer tests for N15 schedule geometry (W93.4)."""
import pandas as pd
from prediction_market_bot.c1_signal_ingestion.nfl_schedule_geometry import (
    haversine_miles, team_game, schedule_features,
)


def test_haversine_known_distance():
    # Seattle -> Miami is ~2,730 statute miles by great circle
    assert abs(haversine_miles(47.60, -122.33, 25.96, -80.24) - 2730) < 40


def test_hand_checked_west_to_east_early_game():
    # SEA at NE, Sunday 13:00 ET: 1pm ET is 10am Pacific on SEA's clock; SEA crosses 3 zones east.
    g = team_game("SEA", "NE", "2025-10-05", "13:00", 7)
    assert g.tz_shift == 3 and g.body_clock_hour == 10.0
    assert 2400 < g.miles < 2500 and not g.short_week and not g.neutral
    h = team_game("NE", "NE", "2025-10-05", "13:00", 7)
    assert h.miles == 0 and h.tz_shift == 0 and h.body_clock_hour == 13.0


def test_east_coast_team_in_west_late_game_is_negative_shift():
    g = team_game("NYG", "SF", "2025-11-02", "20:20", 7)   # SNF 8:20pm ET in Santa Clara; nflverse clock is ET so NYG body clock stays 20:20
    assert g.tz_shift == -3 and abs(g.body_clock_hour - 20.33) < 0.01


def test_short_week_bye_and_international():
    assert team_game("DAL", "DET", "2025-11-27", "12:30", 4).short_week
    assert team_game("DAL", "DET", "2025-11-09", "13:00", 14).post_bye
    g = team_game("JAX", "JAX", "2025-10-05", "09:30", 7, "Wembley Stadium", neutral=True)
    assert g.international and g.neutral and g.miles > 3500 and g.tz_shift == 5


def test_relocated_franchise_alias_and_frame():
    s = pd.DataFrame([dict(home_team="OAK", away_team="SD", gameday="2018-09-09", gametime="16:25", home_rest=7, away_rest=7,
                           location="Home", stadium="Oakland Coliseum")])
    f = schedule_features(s)
    assert f.loc[0, "h_miles"] == 0 and 200 < f.loc[0, "a_miles"] < 260   # relocated franchises map to today's base (LV/LAC): documented simplification

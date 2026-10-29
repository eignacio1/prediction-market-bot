import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nba_current_season as N


def _sched(rows):
    return pd.DataFrame(rows, columns=["game_id", "season", "season_type", "game_date", "home_team_id",
                                       "home_team_abbreviation", "home_pts", "away_team_id",
                                       "away_team_abbreviation", "away_pts"])


def _box(day, abbr, score, fga=90, fta=20, oreb=10, tov=12):
    return {"game_date": day, "team_abbreviation": abbr, "team_score": score, "field_goals_attempted": fga,
            "free_throws_attempted": fta, "offensive_rebounds": oreb, "turnovers": tov, "total_turnovers": tov,
            "team_turnovers": 0}


def _pbp(gid, periods):
    return pd.DataFrame({"game_id": [gid] * periods, "period": list(range(1, periods + 1))})


def test_game_minutes_adds_overtime():
    p = pd.concat([_pbp("a", 4), _pbp("b", 6)])
    m = N.game_minutes(p)
    assert (m["a"], m["b"]) == (240.0, 290.0)


def test_build_uses_espn_abbr_map_and_keeps_matching_game():
    s = _sched([["g1", 2027, "regular-season", "2026-10-20", 1, "NYK", 110.0, 2, "BOS", 100.0]])
    b = pd.DataFrame([_box("2026-10-20", "NY", 110), _box("2026-10-20", "BOS", 100)])
    tg, tips, drops = N.build(s, b, _pbp("g1", 4))
    assert drops["games_kept"] == 1 and len(tg) == 2
    assert set(tg["side"]) == {"home", "away"} and float(tg["total"].iloc[0]) == 210.0
    # poss = 90 + 8.8 - 10 + 12 = 100.8 for both teams -> pace 100.8 at 240 team-minutes
    assert tg["pace"].iloc[0] == pytest.approx(100.8)


def test_overtime_game_pace_is_scaled_by_minutes():
    s = _sched([["g1", 2027, "regular-season", "2026-10-20", 1, "NYK", 120.0, 2, "BOS", 118.0]])
    b = pd.DataFrame([_box("2026-10-20", "NY", 120), _box("2026-10-20", "BOS", 118)])
    tg, _, _ = N.build(s, b, _pbp("g1", 5))
    assert tg["pace"].iloc[0] == pytest.approx(100.8 * 240 / 265)


def test_score_mismatch_and_missing_box_drop_whole_game():
    s = _sched([["g1", 2027, "regular-season", "2026-10-20", 1, "NYK", 110.0, 2, "BOS", 100.0],
                ["g2", 2027, "regular-season", "2026-10-21", 3, "LAL", 90.0, 4, "DEN", 95.0]])
    b = pd.DataFrame([_box("2026-10-20", "NY", 111), _box("2026-10-20", "BOS", 100)])
    pbp = pd.concat([_pbp("g1", 4), _pbp("g2", 4)])
    box, drops = N.build_team_box(s, b, pbp)
    assert box.empty and drops["score_mismatch"] == 1 and drops["no_espn_box"] == 1


def test_unplayed_and_preseason_rows_never_returned():
    s = _sched([["g1", 2027, "preseason", "2026-10-10", 1, "NYK", 110.0, 2, "BOS", 100.0],
                ["g2", 2027, "regular-season", "2026-12-08", 3, "LAL", float("nan"), 4, "DEN", float("nan")]])
    box, drops = N.build_team_box(s, pd.DataFrame([_box("2026-10-10", "NY", 110)]), _pbp("g1", 4))
    assert box.empty and drops["games_kept"] == 0

from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.c2_feature_store.nhl_features import (
    NhlFeatureStore, assert_cutoff, feature_row_sha256, RESULT_LAG)


def mk(i, day, home, away, hs, as_, hid=1, aid=2):
    t = datetime(2025, 10, day, 23, tzinfo=timezone.utc)
    return {"game_id": i, "start_time_utc": t.isoformat(), "home": home, "away": away,
            "home_score_ex_so": hs, "away_score_ex_so": as_, "home_sog": 30, "away_sog": 28,
            "home_pp_goals": 1, "away_pp_goals": 0, "home_pim": 4, "away_pim": 6,
            "home_starter_id": hid, "away_starter_id": aid, "home_goalies_used": [hid],
            "away_goalies_used": [aid], "home_goalie_sa": 28, "home_goalie_saves": 26,
            "away_goalie_sa": 30, "away_goalie_saves": 27}


def store():
    return NhlFeatureStore([mk(1, 1, "AAA", "BBB", 4, 1), mk(2, 3, "BBB", "AAA", 2, 3),
                            mk(3, 9, "AAA", "CCC", 1, 0)])


def test_future_games_excluded_from_features():
    s = store()
    as_of = datetime(2025, 10, 5, 12, tzinfo=timezone.utc)
    start = datetime(2025, 10, 6, 23, tzinfo=timezone.utc)
    f1 = s.game_features("AAA", "BBB", start, as_of)
    s2 = NhlFeatureStore([mk(1, 1, "AAA", "BBB", 4, 1), mk(2, 3, "BBB", "AAA", 2, 3),
                          mk(3, 9, "AAA", "CCC", 9, 9)])  # game 3 is after as_of: must not matter
    f2 = s2.game_features("AAA", "BBB", start, as_of)
    f1.pop("input_max_ts"); f2.pop("input_max_ts")
    assert f1 == f2


def test_game_in_progress_not_available_before_result_lag():
    s = store()
    start = datetime(2025, 10, 6, 23, tzinfo=timezone.utc)
    inside = datetime(2025, 10, 3, 23, tzinfo=timezone.utc) + RESULT_LAG - timedelta(minutes=1)
    f = s.game_features("AAA", "BBB", start, inside)
    assert f["h_n_games"] == 1.0  # only the Oct-1 game, not the one that started Oct-3 23:00


def test_input_max_ts_never_after_as_of_and_assert_raises():
    s = store()
    as_of = datetime(2025, 10, 20, tzinfo=timezone.utc)
    f = s.game_features("AAA", "CCC", as_of + timedelta(days=1), as_of)
    assert datetime.fromisoformat(f["input_max_ts"]) <= as_of
    with pytest.raises(ValueError):
        assert_cutoff(as_of + timedelta(seconds=1), as_of)


def test_rest_and_b2b():
    s = store()
    f = s.game_features("AAA", "BBB", datetime(2025, 10, 4, 1, tzinfo=timezone.utc),
                        datetime(2025, 10, 3, 23, tzinfo=timezone.utc) + RESULT_LAG)
    assert f["h_b2b"] == 1.0 and f["h_rest_days"] < 1.5


def test_missing_goalie_falls_back_to_league_prior():
    s = NhlFeatureStore([])
    f = s.game_features("AAA", "BBB", datetime(2025, 10, 6, tzinfo=timezone.utc),
                        datetime(2025, 10, 5, tzinfo=timezone.utc))
    assert f["h_goalie_known"] == 0.0 and f["h_n_games"] == 0.0 and f["input_max_ts"] is None
    assert 0.9 < f["h_goalie_svp"] < 0.91


def test_confirmed_goalie_overrides_projection_and_flagged():
    s = store()
    f = s.game_features("AAA", "BBB", datetime(2025, 10, 12, tzinfo=timezone.utc),
                        datetime(2025, 10, 11, tzinfo=timezone.utc), home_goalie=999, confirmed=True)
    assert f["starter_source"] == "confirmed" and f["home_goalie_id"] == 999
    assert f["h_goalie_known"] == 0.0  # unknown goalie -> league prior


def test_hash_is_deterministic():
    s = store()
    a = datetime(2025, 10, 5, tzinfo=timezone.utc)
    r = s.game_features("AAA", "BBB", a + timedelta(days=1), a)
    assert feature_row_sha256(r) == feature_row_sha256(dict(r))

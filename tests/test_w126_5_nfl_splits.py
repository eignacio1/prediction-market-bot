"""W126.5 -- NFL factor splits (EXP-NFLSPLITS-001): leaf rules, point-in-time guards, default-off candidate, v1 untouched."""
from datetime import date

import pytest

from prediction_market_bot.decision_trees import shadow_route as sr
from prediction_market_bot.decision_trees.filters import nfl_splits as NS
from prediction_market_bot.nfl_engine.weather_factor import WeatherContext

TK = "KXNFLTEAMTOTAL-26NOV30CARTB-TB23"


def _row(mid=0.55):
    return {"sport": "NFL", "market_type": "NFL_TEAM_TOTAL", "band": "T3", "market_ticker": TK, "event_ticker": "KXNFLTEAMTOTAL-26NOV30CARTB",
            "yes_bid": round(mid - 0.01, 2), "yes_ask": round(mid + 0.01, 2), "half_spread": 0.01, "p_yes": 0.5, "horizon_hours_to_start": 30.0}


def test_qb_and_rest_leaves():
    assert NS.qb_leaf("a", "a") == "qb_same" and NS.qb_leaf("a", "b") == "qb_new" and NS.qb_leaf(None, "b") == "unknown"
    assert NS.game_qb_leaf("qb_same", "qb_new") == "any_new" and NS.game_qb_leaf("qb_same", "unknown") == "unknown"
    assert [NS.rest_leaf(d) for d in (4, 5, 7, 9, 14, None)] == ["short", "short", "normal", "long", "long", "unknown"]
    assert NS.rest_diff_leaf(10, 6) == "home_rest_edge" and NS.rest_diff_leaf(6, 10) == "away_rest_edge" and NS.rest_diff_leaf(7, 6) == "even"


def test_referee_prior_shrinks_and_uses_given_games_only():
    assert NS.ref_prior([]) is None
    assert NS.ref_prior([10.0] * 20) == pytest.approx(5.0)
    assert NS.referee_leaf(None, (-1, 1)) == "unknown" and NS.referee_leaf(2, (-1, 1)) == "ref_high" and NS.referee_leaf(-2, (-1, 1)) == "ref_low"
    assert NS.referee_leaf(0, (-1, 1)) == "ref_mid" and NS.matchup_leaf(0.5, None) == "unknown"


def test_weather_is_forecast_only():
    with pytest.raises(NS.PITViolation):
        NS.weather_leaf(WeatherContext(source="realised", temp_f=20, wind_mph=20))
    with pytest.raises(NS.PITViolation):
        NS.weather_leaf(WeatherContext(source="forecast", temp_f=20, wind_mph=5, lead_h=None))
    assert NS.weather_leaf(None) == "unknown" and NS.weather_leaf(WeatherContext(source="none")) == "unknown"
    assert NS.weather_leaf(WeatherContext(source="forecast", roof="dome", lead_h=20)) == "dome"
    assert NS.weather_leaf(WeatherContext(source="forecast", roof="outdoors", temp_f=50, wind_mph=16, lead_h=20)) == "adverse"
    assert NS.weather_leaf(WeatherContext(source="forecast", roof="outdoors", temp_f=55, wind_mph=5, lead_h=20)) == "benign"


def test_prior_game_must_precede():
    kw = dict(game_day=date(2026, 11, 30), prev_home_game=date(2026, 11, 23), prev_away_game=date(2026, 11, 22), home_prev_qb="a", home_qb="b",
              away_prev_qb="c", away_qb="c", home_rest=7, away_rest=8, ref_prior_value=0.5, ref_cuts=(-0.2, 0.2), weather=None,
              matchup_score=None, matchup_cuts=None)
    out = NS.split_leaves(**kw)
    assert out["qb@team"] == "qb_new|qb_same" and out["qb@game"] == "any_new" and out["officials@game"] == "ref_high"
    assert out["weather@game"] == "unknown" and out["matchup@game"] == "unknown"
    with pytest.raises(NS.PITViolation):
        NS.split_leaves(**{**kw, "prev_home_game": date(2026, 11, 30)})


def test_candidate_is_off_by_default_and_tag_only(monkeypatch):
    monkeypatch.delenv("PM_NFL_SPLITS", raising=False)
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    assert "nfl_splits" not in sr.candidate_fields(_row(), "KXNFLTEAMTOTAL", 0.55, None, None, None)
    monkeypatch.setenv("PM_NFL_SPLITS", "on")
    leaves = {"qb@game": "any_new"}
    c = sr.candidate_fields(_row(), "KXNFLTEAMTOTAL", 0.55, None, None, None, leaves)
    assert c["nfl_splits"]["split_leaves"] == leaves and c["nfl_splits"]["split_applied"] is False
    assert c["nfl_splits"]["arm"] == c["router_v2"]["arm"]  # same map, same arm: the splits change nothing yet
    nba = dict(_row(), sport="NBA")
    assert "nfl_splits" not in sr.candidate_fields(nba, "KXNBATEAMTOTAL", 0.55, None, None, None, leaves)

import pytest
from prediction_market_bot.nfl_engine.filters import nfl_filters, weather_leaf, matchup_total_leaf, matchup_side_leaf, market_state_leaf
from prediction_market_bot.nfl_engine.matchup_cross import Terms
from prediction_market_bot.nfl_engine.weather_factor import WeatherContext


def fc(**k):
    return WeatherContext("forecast", k.pop("roof", "outdoors"), k.pop("temp_f", 60.0), k.pop("wind_mph", 5.0), k.pop("precip_mm", 0.0), 24.0)


def test_weather_leaves():
    assert weather_leaf(fc()) == "calm"
    assert weather_leaf(fc(wind_mph=18)) == "windy"
    assert weather_leaf(fc(temp_f=20)) == "cold"
    assert weather_leaf(fc(precip_mm=0.4)) == "wet"
    assert weather_leaf(fc(roof="dome", wind_mph=30)) == "indoor"
    assert weather_leaf(WeatherContext("none")) == "unknown"


def test_realised_weather_refused():
    with pytest.raises(ValueError):
        weather_leaf(WeatherContext("realised", "outdoors", 20, 25, 0, None))


def test_matchup_leaves():
    assert matchup_total_leaf(Terms(1.0, 0, 0), Terms(1.0, 0, 0)) == "pass_mismatch_high"
    assert matchup_total_leaf(Terms(-1.0, 0, 0), Terms(-1.0, 0, 0)) == "pass_mismatch_low"
    assert matchup_total_leaf(Terms(0.2, 0, 0), Terms(0.1, 0, 0)) == "neutral"
    assert matchup_side_leaf(Terms(2, 1, 0), Terms(0, 0, 0)) == "home_edge"
    assert matchup_side_leaf(Terms(0, 0, 0), Terms(2, 1, 0)) == "away_edge"


def test_market_state_and_bundle():
    assert market_state_leaf(-10, 50) == {"spread_bucket": "big", "total_bucket": "high"}
    assert market_state_leaf(3, 40)["spread_bucket"] == "pk"
    d = nfl_filters(fc(wind_mph=20), Terms(0, 0, 0), Terms(0, 0, 0), 4.5, 44.0)
    assert d["weather"] == "windy" and d["spread_bucket"] == "mid" and d["total_bucket"] == "mid"

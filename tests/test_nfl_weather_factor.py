import numpy as np
import pytest

from prediction_market_bot.nfl_engine import weather_factor as W


def test_realised_weather_cannot_price():
    with pytest.raises(ValueError):
        W.assert_priceable(W.WeatherContext("realised", "outdoors", 20, 25))


def test_short_lead_forecast_cannot_price_but_long_can():
    with pytest.raises(ValueError):
        W.assert_priceable(W.WeatherContext("forecast", "outdoors", 20, 25, lead_h=6))
    W.assert_priceable(W.WeatherContext("forecast", "outdoors", 20, 25, lead_h=24))


def test_indoor_zeroes_exposure_outdoor_does_not():
    out = W.exposure(W.WeatherContext("forecast", "outdoors", 30, 20, 1.5, 24))
    assert out == {"wind": 10.0, "cold": 20.0, "precip": 1.5}
    for roof in ("dome", "closed"):
        assert W.exposure(W.WeatherContext("forecast", roof, 30, 20, 1.5, 24)) == {"wind": 0.0, "cold": 0.0, "precip": 0.0}
    assert W.exposure(W.WeatherContext("forecast", "open", 30, 20, 0, 24))["wind"] == 10.0


def test_missing_and_mild_weather_is_zero():
    assert W.exposure(W.WeatherContext("none")) == {"wind": 0.0, "cold": 0.0, "precip": 0.0}
    assert W.exposure(W.WeatherContext("forecast", "outdoors", 70, 5, lead_h=24)) == {"wind": 0.0, "cold": 0.0, "precip": 0.0}
    assert W.exposure(W.WeatherContext("forecast", "outdoors", None, None, lead_h=24))["cold"] == 0.0


def test_fit_recovers_known_effects():
    rng = np.random.default_rng(1)
    n = 4000
    w, c, p = rng.uniform(0, 20, n), rng.uniform(0, 40, n), rng.uniform(0, 3, n)
    y = -0.30 * w - 0.05 * c - 1.0 * p + rng.normal(0, 3, n)
    e = W.fit_effects(w, c, p, y)
    assert e.wind == pytest.approx(-0.30, abs=0.03)
    assert e.cold == pytest.approx(-0.05, abs=0.02)
    assert e.precip == pytest.approx(-1.0, abs=0.2)


def test_shift_known_answer_and_split():
    eff = W.WeatherEffects(wind=-0.3, cold=-0.05, precip=-1.0)
    ctx = W.WeatherContext("forecast", "outdoors", 30, 20, 1.0, 24)
    assert W.total_shift(ctx, eff) == pytest.approx(-0.3 * 10 - 0.05 * 20 - 1.0)
    mh, ma = W.apply_to_means(24.0, 20.0, -4.0)
    assert (mh, ma) == (22.0, 18.0)
    assert W.apply_to_means(1.5, 1.5, -10.0) == (1.0, 1.0)


def test_total_shift_pricing_flag_guards_leak():
    ctx = W.WeatherContext("realised", "outdoors", 30, 20)
    with pytest.raises(ValueError):
        W.total_shift(ctx, W.WeatherEffects(-0.3, 0, 0))
    assert W.total_shift(ctx, W.WeatherEffects(-0.3, 0, 0), pricing=False) == pytest.approx(-3.0)

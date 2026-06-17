"""Tests for C3 probability calibration layer (ADR-0027 / GG-037)."""
import math

import pytest

from prediction_market_bot.c3_forecasting.calibration import (
    CALIBRATION_TEMPERATURE,
    DEFAULT_TEMPERATURE,
    calibrate_probability,
    get_temperature,
    temperature_scale,
)


class TestTemperatureScale:
    def test_identity_at_t_one(self):
        for p in (0.01, 0.2, 0.5, 0.73, 0.99):
            assert temperature_scale(p, 1.0) == p

    def test_half_is_fixed_point(self):
        # logit(0.5)=0; scaling by any T leaves 0.5 unchanged.
        for T in (0.5, 1.0, 2.05, 5.0):
            assert temperature_scale(0.5, T) == pytest.approx(0.5)

    def test_shrink_toward_half_when_t_gt_one(self):
        # High confidence shrinks down; low confidence rises up.
        assert temperature_scale(0.95, 3.0) < 0.95
        assert temperature_scale(0.95, 3.0) > 0.5
        assert temperature_scale(0.05, 3.0) > 0.05
        assert temperature_scale(0.05, 3.0) < 0.5

    def test_sharpen_when_t_lt_one(self):
        assert temperature_scale(0.7, 0.5) > 0.7
        assert temperature_scale(0.3, 0.5) < 0.3

    def test_monotone(self):
        prev = -1.0
        for p in [i / 100 for i in range(1, 100)]:
            cur = temperature_scale(p, 2.05)
            assert cur > prev
            prev = cur

    def test_frame_symmetry(self):
        # Calibrating YES then taking 1-... equals calibrating the NO frame.
        for p in (0.1, 0.34, 0.8, 0.97):
            yes_then_complement = 1.0 - temperature_scale(p, 2.05)
            no_frame = temperature_scale(1.0 - p, 2.05)
            assert yes_then_complement == pytest.approx(no_frame, abs=1e-12)

    def test_known_value(self):
        # p=0.9, T=2: logit=ln(9)=2.1972; /2=1.0986; sigmoid=0.75
        assert temperature_scale(0.9, 2.0) == pytest.approx(0.75, abs=1e-6)

    def test_extremes_clamped_not_nan(self):
        assert 0.0 < temperature_scale(0.0, 2.0) < 0.5
        assert 0.5 < temperature_scale(1.0, 2.0) < 1.0

    def test_invalid_temperature_raises(self):
        with pytest.raises(ValueError):
            temperature_scale(0.7, 0.0)
        with pytest.raises(ValueError):
            temperature_scale(0.7, -1.0)


class TestCalibrateProbability:
    def test_nba_uses_registered_temperature(self):
        expected = temperature_scale(0.9, CALIBRATION_TEMPERATURE["nba"])
        assert calibrate_probability(0.9, sport="nba") == pytest.approx(expected)

    def test_nba_temperature_shrinks(self):
        assert CALIBRATION_TEMPERATURE["nba"] > 1.0
        assert calibrate_probability(0.97, sport="nba") < 0.97

    def test_unknown_sport_is_identity_failsafe(self):
        # A new sport must NOT inherit another sport's shrink.
        for p in (0.1, 0.5, 0.9):
            assert calibrate_probability(p, sport="cricket") == p

    def test_mlb_identity_until_data_exists(self):
        assert CALIBRATION_TEMPERATURE["mlb"] == DEFAULT_TEMPERATURE == 1.0
        assert calibrate_probability(0.85, sport="mlb") == 0.85

    def test_get_temperature(self):
        assert get_temperature("nba") == CALIBRATION_TEMPERATURE["nba"]
        assert get_temperature("unknown") == DEFAULT_TEMPERATURE

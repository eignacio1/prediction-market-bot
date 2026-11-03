from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.nba_engine import player_availability as PA

T = datetime(2027, 1, 5, 0, 0, tzinfo=timezone.utc)


def test_conditional_shares_known_answer():
    # j=10, teammates 10 (plays surely) and 10 (out): denominator 20 -> share 0.5 * (1 - 0.1)
    assert PA.conditional_shares(10, [10, 10], [1.0, 0.0], 0.1) == pytest.approx(0.45)
    # a teammate who is a coin flip counts half
    assert PA.conditional_shares(10, [10], [0.5], 0.0) == pytest.approx(10 / 15)


def test_conditional_shares_caps_and_validates():
    assert PA.conditional_shares(10, [], [], 0.0) == PA.MAX_SHARE
    with pytest.raises(ValueError):
        PA.conditional_shares(10, [1.0], [], 0.1)


def test_fit_play_rates_shrinks_to_pooled():
    st = ["Out"] * 40 + ["Probable"] * 40
    y = [0] * 40 + [1] * 40
    r = PA.fit_play_rates(st, y, prior_n=5)
    assert r["Out"] < 0.1 and r["Probable"] > 0.9
    assert r[PA.UNLISTED] == pytest.approx(0.5, abs=0.01)
    with pytest.raises(ValueError):
        PA.fit_play_rates(["Out"], [])


def test_assert_pretip_fails_on_postgame_field():
    PA.assert_pretip([T - timedelta(hours=5), None], T, timedelta(hours=4))
    with pytest.raises(PA.LeakError):
        PA.assert_pretip([T - timedelta(hours=5), T + timedelta(minutes=1)], T, timedelta(hours=4))
    with pytest.raises(PA.LeakError):
        PA.assert_pretip([T - timedelta(hours=3)], T, timedelta(hours=4))

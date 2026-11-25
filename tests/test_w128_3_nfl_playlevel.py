"""W128.3 -- NFL play-level crosses (EXP-NFLPLAYLEVEL-001): point-in-time guard, leaf rules, default-off candidate, v1 untouched."""
from datetime import date, timedelta

import pytest

from prediction_market_bot.decision_trees import shadow_route as sr
from prediction_market_bot.decision_trees.filters import nfl_playlevel as PL

TK = "KXNFLTEAMTOTAL-26NOV30CARTB-TB23"


def _row(mid=0.55):
    return {"sport": "NFL", "market_type": "NFL_TEAM_TOTAL", "band": "T3", "market_ticker": TK, "event_ticker": "KXNFLTEAMTOTAL-26NOV30CARTB",
            "yes_bid": round(mid - 0.01, 2), "yes_ask": round(mid + 0.01, 2), "half_spread": 0.01, "p_yes": 0.5, "horizon_hours_to_start": 30.0}


def _hist(n, day0=date(2026, 9, 1), num=3.0, den=6.0):
    return [(day0 + timedelta(days=7 * i), num, den) for i in range(n)]


def test_trailing_ratio_window_and_minimum():
    day = date(2027, 2, 1)
    assert PL.trailing_ratio(_hist(PL.MIN_GAMES - 1), day) is None
    assert PL.trailing_ratio(_hist(PL.MIN_GAMES), day) == pytest.approx(0.5)
    h = [(date(2020, 1, 1) + timedelta(days=i), 0.0, 10.0) for i in range(30)] + _hist(17, num=10.0, den=10.0)
    assert PL.trailing_ratio(h, day) == pytest.approx(1.0)  # only the last 17 games count


def test_trailing_ratio_rejects_same_day_or_later_aggregate():
    day = date(2026, 12, 1)
    for bad in (day, day + timedelta(days=1)):
        with pytest.raises(PL.PITViolation):
            PL.trailing_ratio(_hist(8) + [(bad, 1.0, 1.0)], day)


def test_trailing_ratio_shrinks_toward_prior():
    day = date(2026, 12, 1)
    assert PL.trailing_ratio(_hist(6, num=6.0, den=6.0), day, prior=0.0, k=36.0) == pytest.approx(36.0 / 72.0)


def test_cross_and_game_leaves():
    cuts = (0.5, 0.4)
    assert PL.cross_leaf(0.6, 0.5, cuts) == "hi_hi" and PL.cross_leaf(0.4, 0.5, cuts) == "lo_hi" and PL.cross_leaf(0.6, 0.3, cuts) == "hi_lo"
    assert PL.cross_leaf(None, 0.5, cuts) == "unknown" and PL.cross_leaf(0.6, 0.5, None) == "unknown"
    assert PL.game_leaf_spread("hi_hi", "lo_lo") == "home_only" and PL.game_leaf_spread("lo_lo", "hi_hi") == "away_only"
    assert PL.game_leaf_spread("hi_hi", "hi_hi") == "neither_or_both" and PL.game_leaf_spread("unknown", "hi_hi") == "unknown"
    assert [PL.game_leaf_total(a, b) for a, b in (("lo_lo", "lo_hi"), ("hi_hi", "lo_lo"), ("hi_hi", "hi_hi"))] == ["none", "one", "both"]
    assert PL.game_leaf_total("unknown", "hi_hi") == "unknown"


def test_carried_flag_and_playlevel_leaves():
    assert PL.is_carried(2025, 2026) and not PL.is_carried(2026, 2026) and not PL.is_carried(None, 2026)
    cuts = {c: (0.5, 0.5) for c in PL.CROSS_NAMES}
    home = {c: (0.9, 0.9) for c in PL.CROSS_NAMES}
    away = {"x1_personnel_shell": (0.1, 0.1)}
    out = PL.playlevel_leaves(game_day=date(2026, 11, 30), home=home, away=away, cuts=cuts)
    assert out["x1_personnel_shell@home"] == "hi_hi" and out["x1_personnel_shell@away"] == "lo_lo"
    assert out["x1_personnel_shell@spread"] == "home_only" and out["x1_personnel_shell@total"] == "one"
    assert out["x2_motion_man@away"] == "unknown" and out["x2_motion_man@spread"] == "unknown"


def test_candidate_is_off_by_default_and_tag_only(monkeypatch):
    monkeypatch.delenv("PM_NFL_PLAYLEVEL", raising=False)
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    assert "nfl_playlevel" not in sr.candidate_fields(_row(), "KXNFLTEAMTOTAL", 0.55, None, None, None)
    monkeypatch.setenv("PM_NFL_PLAYLEVEL", "on")
    leaves = {"x1_personnel_shell@spread": "home_only"}
    c = sr.candidate_fields(_row(), "KXNFLTEAMTOTAL", 0.55, None, None, None, leaves)
    assert c["nfl_playlevel"]["playlevel_leaves"] == leaves and c["nfl_playlevel"]["playlevel_applied"] is False
    assert c["nfl_playlevel"]["arm"] == c["router_v2"]["arm"]  # same map, same arm: the crosses change nothing yet
    assert "nfl_playlevel" not in sr.candidate_fields(dict(_row(), sport="NBA"), "KXNBATEAMTOTAL", 0.55, None, None, None, leaves)

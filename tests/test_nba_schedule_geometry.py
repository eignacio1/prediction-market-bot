"""W93.2 travel / schedule geometry: known-answer week, definitions, as-of (no look-ahead), unknown-city handling."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nba_schedule_geometry as G


def _week():
    # Team 1 (LA-based): Mon home LA, Tue @DEN (b2b), Thu @BKN, Sat home LA. Dates are the Eastern date of the tip.
    rows = [
        ("g1", "home", "2026-11-02", "2026-11-03T03:00:00Z", "Los Angeles"),   # 7pm PST Mon
        ("g2", "away", "2026-11-03", "2026-11-04T02:00:00Z", "Denver"),        # 7pm MST Tue
        ("g3", "away", "2026-11-05", "2026-11-06T00:00:00Z", "Brooklyn"),      # 7pm EST Thu
        ("g4", "home", "2026-11-07", "2026-11-08T03:00:00Z", "Los Angeles"),   # 7pm PST Sat
    ]
    tg = pd.DataFrame(rows, columns=["game_id", "side", "date", "tip", "city"])
    tg["team_id"], tg["season"] = 1, 2027
    tg["date"] = pd.to_datetime(tg["date"])
    tg["tip_earliest"] = tg["tip_latest"] = pd.to_datetime(tg["tip"], utc=True)
    return tg.drop(columns=["tip", "city"]), pd.DataFrame({"city": [r[4] for r in rows]}, index=[r[0] for r in rows])


def test_known_answer_week():
    tg, v = _week()
    r = G.schedule_geometry(tg, v).set_index("game_id")
    assert np.isnan(r.at["g1", "travel_mi"]) and np.isnan(r.at["g1", "tz_shift"])           # season opener: no previous venue
    assert r.at["g2", "travel_mi"] == pytest.approx(830, rel=0.02)                            # LA -> Denver great circle
    assert r.at["g3", "travel_mi"] == pytest.approx(1620, rel=0.02)                           # Denver -> Brooklyn
    assert r.at["g4", "travel_mi"] == pytest.approx(2450, rel=0.02)                           # Brooklyn -> LA
    assert (r.at["g2", "tz_shift"], r.at["g3", "tz_shift"], r.at["g4", "tz_shift"]) == (1.0, 2.0, -3.0)   # DST ended 11-01
    assert r.at["g3", "east"] == 1.0 and r.at["g4", "east"] == 0.0
    assert [r.at[g, "rest_days_g"] for g in ("g2", "g3", "g4")] == [0, 1, 1]
    assert r.at["g2", "alt_gain"] == 1609 - 90 and r.at["g1", "alt_gain"] == 0 and r.at["g3", "alt_gain"] == 0
    assert [r.at[g, "road_run"] for g in ("g1", "g2", "g3", "g4")] == [0, 1, 2, 0]
    assert [r.at[g, "home_run"] for g in ("g1", "g2", "g3", "g4")] == [1, 0, 0, 1]
    assert [r.at[g, "g_last4"] for g in ("g1", "g2", "g3", "g4")] == [0, 1, 2, 2]            # g3 (Nov 5): Nov 1-4 holds g1,g2; g4 (Nov 7): Nov 3-6 holds g2,g3
    assert [r.at[g, "g_last6"] for g in ("g1", "g2", "g3", "g4")] == [0, 1, 2, 3]
    assert r.at["g4", "miles_last7"] == pytest.approx(r.at["g2", "travel_mi"] + r.at["g3", "travel_mi"])  # window Oct 31-Nov 6
    assert r.at["g3", "body_tip_hr"] == 16.0 and r.at["g3", "late_body"] == 0.0               # 7pm ET = 4pm on the LA clock


def test_late_body_clock():
    tg, v = _week()
    tg.loc[tg.game_id == "g3", "tip_earliest"] = tg.loc[tg.game_id == "g3", "tip_latest"] = pd.Timestamp("2026-11-05T17:00:00Z")  # noon ET
    r = G.schedule_geometry(tg, v).set_index("game_id")
    assert r.at["g3", "body_tip_hr"] == 9.0 and r.at["g3", "late_body"] == 1.0


def test_asof_future_changes_do_not_move_earlier_rows():
    tg, v = _week()
    base = G.schedule_geometry(tg, v).set_index("game_id")
    v2 = v.copy()
    v2.loc["g4", "city"] = "Miami"
    tg2 = tg.copy()
    tg2.loc[tg2.game_id == "g4", "date"] = pd.Timestamp("2026-11-20")
    alt = G.schedule_geometry(tg2, v2).set_index("game_id")
    cols = ["travel_mi", "tz_shift", "g_last4", "g_last6", "miles_last7", "road_run", "alt_gain", "rest_days_g"]
    pd.testing.assert_frame_equal(base.loc[["g1", "g2", "g3"], cols], alt.loc[["g1", "g2", "g3"], cols])


def test_row_order_invariant():
    tg, v = _week()
    a = G.schedule_geometry(tg, v).set_index("game_id").sort_index()
    b = G.schedule_geometry(tg.sample(frac=1, random_state=3), v).set_index("game_id").sort_index()
    pd.testing.assert_frame_equal(a, b)


def test_unknown_city_is_nan_not_guess():
    tg, v = _week()
    v.loc["g2", "city"] = "Atlantis"
    r = G.schedule_geometry(tg, v).set_index("game_id")
    assert np.isnan(r.at["g2", "travel_mi"]) and np.isnan(r.at["g3", "travel_mi"]) and np.isnan(r.at["g2", "alt_m"])
    assert r.at["g4", "travel_mi"] == pytest.approx(2450, rel=0.02)


def test_haversine_known_pairs():
    assert G.haversine_mi(40.683, -73.975, 34.043, -118.267) == pytest.approx(2450, rel=0.02)
    assert G.haversine_mi(10.0, 10.0, 10.0, 10.0) == 0.0


def test_city_table_complete_for_nba_venues():
    for c in ("Denver", "Salt Lake City", "Mexico City", "Lake Buena Vista", "Tampa", "Austin", "Las Vegas", "Toronto"):
        assert c in G.CITIES
    assert G.CITIES["Denver"][3] == 1609 and G.CITIES["Salt Lake City"][3] == 1288

import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nba_officials import SHRINK_K, official_rates


def _games(rows):
    return pd.DataFrame(rows, columns=["game_id", "date", "fouls", "fta", "pace"]).assign(
        date=lambda d: pd.to_datetime(d["date"])).set_index("game_id")


def test_known_answer_shrunk_rate():
    # official A works g1,g2 (fouls 50, 40) then g3; league prior mean before g3 = 45 (only g1,g2 played earlier)
    g = _games([("1", "2026-01-01", 50, 0, 100), ("2", "2026-01-02", 40, 0, 100), ("3", "2026-01-03", 60, 0, 100)])
    c = pd.DataFrame({"game_id": ["1", "2", "3"], "official_id": [7, 7, 7]})
    r = official_rates(c, g)
    exp = (90 + SHRINK_K * 45) / (2 + SHRINK_K) - 45
    assert abs(r.loc["3", "crew_dev_fouls"] - exp) < 1e-9
    assert r.loc["3", "crew_n"] == 2
    assert np.isnan(r.loc["1", "crew_dev_fouls"])  # no earlier games: no league mean yet


def test_own_game_never_feeds_itself():
    base = _games([("1", "2026-01-01", 50, 0, 100), ("2", "2026-01-02", 40, 0, 100), ("3", "2026-01-03", 60, 0, 100)])
    c = pd.DataFrame({"game_id": ["1", "2", "3"], "official_id": [7, 7, 7]})
    a = official_rates(c, base).loc["3"]
    changed = base.copy()
    changed.loc["3", "fouls"] = 999  # the game's own outcome must not move its own crew value
    b = official_rates(c, changed).loc["3"]
    assert a["crew_dev_fouls"] == b["crew_dev_fouls"]


def test_same_day_games_do_not_feed_each_other():
    g = _games([("1", "2026-01-01", 50, 0, 100), ("2", "2026-01-02", 10, 0, 100), ("3", "2026-01-02", 90, 0, 100)])
    c = pd.DataFrame({"game_id": ["1", "2", "3"], "official_id": [7, 7, 8]})
    r = official_rates(c, g)
    # official 8 has no history: pure league mean (50) -> deviation 0; game 2's 10 must not leak into anything on day 2
    assert abs(r.loc["3", "crew_dev_fouls"]) < 1e-9
    assert r.loc["3", "crew_n"] == 0


def test_row_order_invariance():
    g = _games([("1", "2026-01-01", 50, 0, 100), ("2", "2026-01-02", 40, 0, 100), ("3", "2026-01-03", 60, 0, 100)])
    c = pd.DataFrame({"game_id": ["1", "2", "3"], "official_id": [7, 7, 7]})
    a = official_rates(c, g).sort_index()
    b = official_rates(c.iloc[::-1], g.iloc[::-1]).sort_index()
    pd.testing.assert_frame_equal(a, b)

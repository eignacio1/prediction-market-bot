import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nba_data_rules as r


def test_attach_order_index_resolves_repeats():
    pbp = pd.DataFrame({"game_id": ["g"] * 3, "action_number": [5, 5, 6], "order_index": [10, 11, 12]})
    lin = pd.DataFrame({"game_id": ["g"] * 3, "action_number": [5, 5, 6], "home_player_1": [1, 2, 3]})
    out = r.attach_order_index(lin, pbp)
    assert out["order_index"].tolist() == [10, 11, 12] and out["order_index"].is_unique


def test_attach_order_index_refuses_non_1to1():
    pbp = pd.DataFrame({"game_id": ["g"] * 2, "action_number": [5, 6], "order_index": [1, 2]})
    lin = pd.DataFrame({"game_id": ["g"] * 3, "action_number": [5, 5, 6]})
    with pytest.raises(ValueError):
        r.attach_order_index(lin, pbp)


def test_eligibility_excludes_preseason_allstar_and_boxless():
    sch = pd.DataFrame({"game_id": ["a", "b", "c", "d"], "season": 2025,
                        "season_type": ["regular-season", "preseason", "all-star", "playoffs"]})
    box = pd.DataFrame({"game_id": ["a", "d"]})
    off = pd.DataFrame({"game_id": ["a"]})
    tips = pd.DataFrame({"tip_imputed": [False, True, True, False]}, index=["a", "b", "c", "d"])
    q = r.game_quality(sch, box, off, tips)
    assert r.eligible_games(q) == {"a", "d"}
    assert bool(q.loc["d", "has_officials"]) is False  # eligible without officials: flagged, not dropped

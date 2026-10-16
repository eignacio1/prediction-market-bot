import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nba_factors import rest_features, rolling_asof


def _tg(n=14, tip_hours=24):
    base = pd.Timestamp("2020-01-01 00:00", tz="UTC")
    rows = []
    for i in range(n):
        tip = base + pd.Timedelta(hours=tip_hours * i)
        rows.append(dict(game_id=str(i), team_id=1, season=2020, tip_earliest=tip, tip_latest=tip,
                         date=pd.Timestamp(tip.date()), pace=100.0 + i, ortg=110.0, drtg=105.0, total=200.0 + i))
    return pd.DataFrame(rows)


def test_rolling_uses_only_completed_prior_games():
    r = rolling_asof(_tg()).set_index("game_id")
    assert r.loc["9", "n_prior"] == 9 and np.isnan(r.loc["9", "pace_ytd"])      # < MIN_GAMES
    assert r.loc["10", "pace_ytd"] == np.mean(range(100, 110))                 # games 0-9 only, not game 10
    assert r.loc["10", "pace_l10"] == r.loc["10", "pace_ytd"]


def test_overlapping_game_not_counted_as_prior():
    t = _tg(12, tip_hours=3)  # games 3h apart: the 4h completion buffer means only games >=4h earlier count
    r = rolling_asof(t).set_index("game_id")
    assert r.loc["11", "n_prior"] == 11 - 1   # game 10 tipped 3h earlier, not yet certainly complete


def test_rest_days_b2b_three_in_four():
    t = _tg(5)
    r = rest_features(t).sort_values("date").reset_index(drop=True)
    assert np.isnan(r.loc[0, "rest_days"]) and r.loc[1, "rest_days"] == 0 and r.loc[1, "b2b"] == 1.0
    assert r.loc[2, "three_in_four"] == 1.0 and r.loc[1, "three_in_four"] == 0.0
    assert r.loc[4, "g_last7"] == 4

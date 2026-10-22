"""NHL store checks: synthetic frames only, no network."""
import pandas as pd

from prediction_market_bot.c1_signal_ingestion import nhl_store_checks as c


def _games(**over):
    g = pd.DataFrame([
        {"game_id": 1, "game_state": "OFF", "home_score": 3, "away_score": 2, "last_period_type": "REG",
         "has_pbp": True, "has_box": True, "has_shifts": True},
        {"game_id": 2, "game_state": "OFF", "home_score": 3, "away_score": 2, "last_period_type": "SO",
         "has_pbp": True, "has_box": True, "has_shifts": True},
    ])
    for k, v in over.items():
        g[k] = v
    return g


def _recon(goals=((3, 2), (2, 2)), sog=((30, 25), (28, 27))):
    return pd.DataFrame([{"game_id": i + 1, "season": 2020, "pbp_goals_home": gh, "pbp_goals_away": ga,
                          "pbp_sog_home": sh, "pbp_sog_away": sa, "box_home_sog": sh, "box_away_sog": sa}
                         for i, ((gh, ga), (sh, sa)) in enumerate(zip(goals, sog))])


def test_shootout_winner_gets_the_extra_goal():
    # game 2 is 2-2 in pbp (shootout excluded) but 3-2 final: home won the shootout
    assert c.reconcile(_recon(), _games())["goal_reconcile"] == 1.0


def test_goal_mismatch_is_detected_and_fails():
    rep = c.Report()
    c.check_season(2020, _games(), pd.DataFrame(), pd.DataFrame(), _recon(goals=((3, 2), (1, 2))), rep)
    assert any("goal reconcile" in f for f in rep.failures)


def test_missing_coverage_fails_with_ids():
    rep = c.Report()
    info = c.check_season(2020, _games(has_shifts=[True, False]), pd.DataFrame(), pd.DataFrame(), _recon(), rep)
    assert info["has_shifts_missing"] == [2]
    assert any("has_shifts" in f for f in rep.failures)


def test_duplicate_events_fail_and_clean_passes():
    ev = pd.DataFrame({"game_id": [1, 1], "event_id": [5, 5], "type": ["goal", "goal"], "x": [1, 1],
                       "shot_type": ["wrist"] * 2, "shooter_id": [9, 9], "home_skaters": [5, 5]})
    rep = c.Report()
    c.check_season(2020, _games(), ev, pd.DataFrame(), _recon(), rep)
    assert any("duplicate" in f for f in rep.failures)
    rep2 = c.Report()
    c.check_season(2020, _games(), ev.iloc[:1], pd.DataFrame(), _recon(), rep2)
    assert rep2.failures == []


def test_detail_shares_report_missing_fields():
    ev = pd.DataFrame({"game_id": [1, 1], "event_id": [1, 2], "type": ["shot-on-goal", "missed-shot"],
                       "x": [1.0, None], "shot_type": [None, None], "shooter_id": [7, None], "home_skaters": [5, 5]})
    d = c.detail_shares(ev)
    assert d["xy"] == 0.5 and d["shot_type"] == 0.0 and d["shooter"] == 0.5

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.nba_engine import decision_tree as D
from prediction_market_bot.nba_engine import engine_v2 as V
from prediction_market_bot.nba_engine import factors_applied as FA

FA.register()
P = V.V2Params(hca=2.5, tbias=0.0, sd_margin=12.0, sd_total=18.0,
               shift_margin={"d_miles": -1.0, "d_pam_creator": 2.0}, shift_total={"s_crew_pace": 3.0, "venue_alt": 1.0})


def test_register_adds_all_names():
    for f in FA.SPEC:
        assert f in D.FACTOR_CLASS


def test_officials_only_between_9h_and_3h():
    x = {"s_crew_pace": 1.0}
    assert "s_crew_pace" in FA.usable(x, 8.0)[0]       # T2, crew posted
    assert "s_crew_pace" in FA.usable(x, 4.0)[0]
    assert "s_crew_pace" in FA.usable(x, 1.0)[0]       # T3
    assert "s_crew_pace" in FA.usable(x, 20.0)[1]      # T1: not knowable
    assert "s_crew_pace" in FA.usable(x, 10.0)[1]      # T1 band (>=12h)? 10h is T2 but before 9h posting
    assert "s_crew_pace" not in FA.usable(x, 10.0)[0]


def test_geometry_class_is_venue_t1_only_as_in_109_1():
    use, skip = FA.usable({"d_miles": 1.0}, 24.0)
    assert "d_miles" in use
    use, skip = FA.usable({"d_miles": 1.0}, 1.0)
    assert "d_miles" in skip


def test_price_known_answer_total_shift():
    r = FA.price(P, "total", 110.0, 108.0, {"s_crew_pace": 2.0}, hours_to_tip=2.0, n=220, calibrate=False)
    assert r.t == pytest.approx(218.0 + 3.0 * 2.0)
    assert r.used == ["s_crew_pace"]
    base = FA.price(P, "total", 110.0, 108.0, {}, hours_to_tip=2.0, n=220, calibrate=False)
    assert r.raw != base.raw


def test_price_skips_unknowable():
    r = FA.price(P, "spread", 110.0, 108.0, {"d_pam_creator": 5.0}, hours_to_tip=30.0, calibrate=False)
    assert r.used == ["d_pam_creator"]
    r2 = FA.price(P, "spread", 110.0, 108.0, {"d_pam_creator": 5.0}, hours_to_tip=1.0, calibrate=False)
    assert r2.used == [] and "d_pam_creator" in r2.skipped


def test_usage_events():
    assert FA.usage_events(10, 5, 2) == pytest.approx(10 + 2.2 + 2)


def test_usage_shares_are_strictly_prior():
    rows = pd.DataFrame([
        dict(game_id="g1", team_id="A", person_id="p1", season=2025, order=1, ue=10.0),
        dict(game_id="g1", team_id="A", person_id="p2", season=2025, order=1, ue=30.0),
        dict(game_id="g2", team_id="A", person_id="p1", season=2025, order=2, ue=50.0),
        dict(game_id="g2", team_id="A", person_id="p2", season=2025, order=2, ue=0.0),
    ])
    s = FA.usage_shares_asof(rows)
    g1 = s[s.game_id == "g1"]
    assert g1["share"].isna().all()                    # no earlier game: unknown, not zero
    g2 = s[s.game_id == "g2"].set_index("person_id")["share"]
    assert g2["p1"] == pytest.approx(0.25) and g2["p2"] == pytest.approx(0.75)   # g2's own 50 is not in its own share


def test_usage_missing_and_creator_cross():
    df = pd.DataFrame([
        dict(game_id="g", team_id="A", share=0.5, p_play=0.0),    # creator out
        dict(game_id="g", team_id="A", share=0.3, p_play=1.0),
        dict(game_id="g", team_id="A", share=0.2, p_play=0.5),
    ])
    r = FA.usage_missing(df).iloc[0]
    assert r.usage_missing == pytest.approx(0.5 + 0.0 + 0.1)
    assert r.creator_out == pytest.approx(0.5)


def test_pam_point_in_time_refuses_hindsight():
    recs = [dict(id_map={"nba_person_id": 7}, recorded_at="2026-05-28", effective_from="2025-10-22",
                 archetypes=[{"id": "PRF-2", "weight": 0.8}, {"id": "PRF-3", "weight": 0.9}], modifiers=[{"id": "M-1"}, {"id": "M-4"}])]
    pam = FA.pam_player_table(recs)
    assert pam.iloc[0].creator == pytest.approx(0.8) and pam.iloc[0].n_mod == 2
    df = pd.DataFrame([dict(game_id="g", team_id="A", person_id=7, w=0.5, p_play=1.0)])
    gd = {"g": pd.Timestamp("2026-01-10")}
    assert FA.pam_flags(df, pam, gd, point_in_time=True).empty                   # record written after the game
    r = FA.pam_flags(df, pam, gd, point_in_time=False).iloc[0]                    # hindsight mode
    assert r.pam_creator == pytest.approx(0.4) and r.pam_mod == pytest.approx(1.0)
    gd2 = {"g": pd.Timestamp("2026-11-01")}
    assert not FA.pam_flags(df, pam, gd2, point_in_time=True).empty               # forward use is valid


def test_pam_not_before_effective_from():
    recs = [dict(id_map={"nba_person_id": 7}, recorded_at="2021-01-01", effective_from="2025-10-22",
                 archetypes=[{"id": "PRF-1", "weight": 1.0}], modifiers=[])]
    pam = FA.pam_player_table(recs)
    df = pd.DataFrame([dict(game_id="g", team_id="A", person_id=7, w=1.0, p_play=1.0)])
    assert FA.pam_flags(df, pam, {"g": pd.Timestamp("2025-01-01")}).empty


def test_home_away_columns():
    t = pd.DataFrame([dict(game_id="g", team_id="H", x=5.0), dict(game_id="g", team_id="A", x=2.0)])
    r = FA.home_away_columns(t, {"g": "H"}, ["x"])
    assert r.loc["g", "d_x"] == 3.0 and r.loc["g", "s_x"] == 7.0

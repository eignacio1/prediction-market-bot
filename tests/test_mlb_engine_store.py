"""MLB engine data layer: store, checks, point-in-time (W105.3). Known-answer synthetic season."""
import gzip

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.mlb_engine import checks, pit, store


def _pitch(pk, date, ab, pn, pitcher, batter, desc, ptype="FF", speed=95.0, zone=5, events=None,
           stand="R", throws="R", half="Top", inning=1, woba=None, den=None, ls=None, post=(0, 0)):
    return dict(game_pk=pk, game_date=date, at_bat_number=ab, pitch_number=pn, pitcher=pitcher, batter=batter,
                p_throws=throws, stand=stand, home_team="HOM", away_team="AWY", inning=inning,
                inning_topbot=half, outs_when_up=0, balls=0, strikes=0, on_1b=np.nan, on_2b=np.nan, on_3b=np.nan,
                pitch_type=ptype, release_speed=speed, release_spin_rate=2200.0, release_extension=6.0,
                pfx_x=0.0, pfx_z=1.0, plate_x=0.0, plate_z=2.5, zone=zone, type="S", description=desc,
                events=events, bb_type=None, launch_speed=ls, launch_angle=None, bat_speed=None,
                swing_length=None, woba_value=woba, woba_denom=den, estimated_woba_using_speedangle=None,
                delta_run_exp=0.0, home_score=0, away_score=0, post_home_score=post[0], post_away_score=post[1])


def _season():
    """Pitcher 1 faces batter 10 on 3 dates; pitcher 2 relieves. Known per-date counts."""
    rows = []
    # d1: game 100: P1 throws 3 pitches in PA1: ball(OOZ), swinging_strike, called_strike->strikeout (K)
    d1, d2, d3 = "2025-04-01", "2025-04-02", "2025-04-03"
    rows += [
        _pitch(100, d1, 1, 1, 1, 10, "ball", zone=12),
        _pitch(100, d1, 1, 2, 1, 10, "swinging_strike", zone=5),
        _pitch(100, d1, 1, 3, 1, 10, "called_strike", zone=5, events="strikeout", woba=0.0, den=1.0,
               post=(0, 0)),
        # P1 leaves mid next PA after 1 pitch (no PA completed by P1); P2 finishes it
        _pitch(100, d1, 2, 1, 1, 11, "foul", zone=11, half="Top"),
        _pitch(100, d1, 2, 2, 2, 11, "hit_into_play", zone=5, events="single", woba=0.9, den=1.0, ls=100.0,
               post=(0, 3)),
        # home half: batter 20 off pitcher 3
        _pitch(100, d1, 3, 1, 3, 20, "ball", half="Bot", post=(0, 3)),
    ]
    rows += [
        _pitch(101, d2, 1, 1, 1, 10, "swinging_strike", zone=13, events="strikeout", woba=0.0, den=1.0,
               post=(1, 0)),
    ]
    rows += [
        _pitch(102, d3, 1, 1, 1, 10, "ball", zone=5, events="walk", woba=0.7, den=1.0, post=(2, 1)),
    ]
    df = pd.DataFrame(rows)
    return store.clean_pitches(df)


def test_clean_dedupes_and_flags():
    s = _season()
    dup = pd.concat([s[store.KEY + ["pitcher", "batter", "game_date", "description", "pitch_type", "zone",
                                    "release_speed", "events", "woba_value", "woba_denom", "launch_speed",
                                    "p_throws", "stand", "home_team", "away_team", "inning", "inning_topbot",
                                    "outs_when_up", "balls", "strikes", "on_1b", "on_2b", "on_3b",
                                    "release_spin_rate", "release_extension", "pfx_x", "pfx_z", "plate_x",
                                    "plate_z", "type", "bb_type", "launch_angle", "bat_speed", "swing_length",
                                    "estimated_woba_using_speedangle", "delta_run_exp", "home_score",
                                    "away_score", "post_home_score", "post_away_score"]]] * 2)
    again = store.clean_pitches(dup)
    assert checks.duplicate_pitches(again) == 0
    assert len(again) == len(s)
    sw = s[s["description"] == "swinging_strike"]
    assert sw["is_whiff"].all() and sw["is_swing"].all()
    assert s[s["zone"] == 12]["out_of_zone"].all()


def test_read_raw_day_drops_leaky_columns(tmp_path):
    csv = ("game_pk,game_date,at_bat_number,pitch_number,pitcher,batter,pitcher_days_until_next_game,"
           "batter_days_until_next_game\n1,2025-04-01,1,1,5,6,3,2\n")
    p = tmp_path / "d.csv.gz"
    with gzip.open(p, "wb") as fh:
        fh.write(("﻿" + csv).encode("utf-8"))
    out = store.read_raw_day(p)
    for c in store.LEAKY_COLUMNS:
        assert c not in out.columns
    assert list(out.columns) == store.KEEP and len(out) == 1


def test_games_pa_lineups():
    s = _season()
    pa = store.plate_appearances(s)
    assert len(pa) == 4  # K, single, K, walk; the home-half at-bat has no event
    assert set(pa["events"]) == {"strikeout", "single", "walk"}
    g = store.games(s).set_index("game_pk")
    assert g.loc[100, "away_runs"] == 3 and g.loc[100, "home_runs"] == 0
    assert g.loc[100, "home_starter"] == 1  # P1 pitched the Top of the 1st (home team fields)
    assert g.loc[100, "away_starter"] == 3
    lu = store.lineups(s)
    top = lu[(lu.game_pk == 100) & (lu.team_side == "away")].sort_values("slot")
    assert list(top["batter"]) == [10, 11]
    assert list(top["slot"]) == [1, 2]


def test_pitcher_pit_known_answers_and_strictness():
    s = _season()
    pa = store.plate_appearances(s)
    pp = pit.pitcher_pit(s, pa).set_index(["pitcher", "game_date"])
    d1, d2, d3 = (pd.Timestamp(x) for x in ("2025-04-01", "2025-04-02", "2025-04-03"))
    # first appearance: nothing known
    assert pp.loc[(1, d1), "n_pitches"] == 0 and np.isnan(pp.loc[(1, d1), "whiff_rate"])
    # as of d2: P1 threw 4 pitches on d1 (3 + 1 before relief); swings: swinging_strike + foul = 2; whiff 1
    assert pp.loc[(1, d2), "n_pitches"] == 4
    assert pp.loc[(1, d2), "whiff_rate"] == pytest.approx(1 / 2)
    # ooz pitches: zone 12 and zone 11 = 2; ooz swings: the foul on zone 11 = 1
    assert pp.loc[(1, d2), "chase_rate"] == pytest.approx(1 / 2)
    # P1 completed one PA (the K): bf=1, k_rate=1
    assert pp.loc[(1, d2), "bf"] == 1 and pp.loc[(1, d2), "k_rate"] == 1.0
    # as of d3: + d2 (1 pitch, a whiff, a K) -> 5 pitches, bf 2
    assert pp.loc[(1, d3), "n_pitches"] == 5 and pp.loc[(1, d3), "bf"] == 2
    # reliever P2 on d1: no prior; the d1 woba is NOT in his d1 row
    assert pp.loc[(2, d1), "woba_den"] == 0


def test_batter_pit_platoon_and_power():
    s = _season()
    pa = store.plate_appearances(s)
    bp = pit.batter_pit(s, pa).set_index(["batter", "game_date"])
    d2, d3 = pd.Timestamp("2025-04-02"), pd.Timestamp("2025-04-03")
    # batter 10 on d1: one K (woba 0); as of d3: d1 K + d2 K -> woba 0/2 PA
    assert bp.loc[(10, d3), "pa"] == 2 and bp.loc[(10, d3), "woba"] == 0.0
    assert bp.loc[(10, d2), "woba_vsR"] == 0.0 and np.isnan(bp.loc[(10, d2), "woba_vsL"])
    # batter 11 hit the single at 100 mph on d1 -- appears only d1 (no later row), so nothing to leak
    assert (11, d2) not in bp.index


def test_no_future_rows_truncation_invariance():
    s = _season()
    pa = store.plate_appearances(s)
    full = pit.pitcher_pit(s, pa).sort_values(["pitcher", "game_date"]).reset_index(drop=True)
    cut = pd.Timestamp("2025-04-02")
    s2 = s[s["game_date"] <= cut]
    pa2 = pa[pa["game_date"] <= cut]
    part = pit.pitcher_pit(s2, pa2).sort_values(["pitcher", "game_date"]).reset_index(drop=True)
    f = full[full["game_date"] <= cut].reset_index(drop=True)
    pd.testing.assert_frame_equal(f, part, check_dtype=False)
    # and perturbing the future changes nothing in the past
    s3 = s.copy()
    s3.loc[s3["game_date"] > cut, "description"] = "swinging_strike"
    p3 = pit.pitcher_pit(s3, pa).sort_values(["pitcher", "game_date"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(f, p3[p3["game_date"] <= cut].reset_index(drop=True), check_dtype=False)
    # batter side too
    fb = pit.batter_pit(s, pa).sort_values(["batter", "game_date"]).reset_index(drop=True)
    pb = pit.batter_pit(s2, pa2).sort_values(["batter", "game_date"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(fb[fb["game_date"] <= cut].reset_index(drop=True), pb, check_dtype=False)


def test_same_day_doubleheader_does_not_feed_itself():
    a = _pitch(200, "2025-05-01", 1, 1, 7, 8, "swinging_strike", events="strikeout", woba=0.0, den=1.0)
    b = _pitch(201, "2025-05-01", 1, 1, 7, 8, "ball", events="walk", woba=0.7, den=1.0)
    s = store.clean_pitches(pd.DataFrame([a, b]))
    pp = pit.pitcher_pit(s, store.plate_appearances(s))
    assert len(pp) == 1 and pp.iloc[0]["n_pitches"] == 0  # both games share the date; neither sees the other


def test_box_checks_and_ids():
    s = _season()
    g = store.games(s)
    box = {"teams": {"home": {"teamStats": {"pitching": {"pitchesThrown": 1}, "batting": {"runs": 0}}},
                     "away": {"teamStats": {"pitching": {"pitchesThrown": 5}, "batting": {"runs": 3}}}}}
    out = checks.pitch_counts_vs_box(g, [100], fetcher=lambda pk: box)
    assert out.loc[0, "pitch_diff"] == 0 and bool(out.loc[0, "score_match"])
    reg = pd.DataFrame({"key_mlbam": [1, 2, 3, 10]})
    u = checks.unresolved_ids(s, reg)
    assert u["pitcher"] == 0 and u["batter"] == 2  # batters 11 and 20 not in the register

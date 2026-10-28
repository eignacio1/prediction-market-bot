from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nba_availability as A

DAY = datetime(2026, 1, 10).date()
TIP = datetime(2026, 1, 10, 0, 0, tzinfo=timezone.utc)  # 19:00 ET on 01-09; use explicit tips below


def _tip(h, m=0):  # ET wall clock on DAY -> UTC
    return A.slot_ts(DAY, f"{h:02d}:{m:02d}")


def test_slot_ts_is_et():
    assert A.slot_ts(DAY, "19:30") == datetime(2026, 1, 11, 0, 30, tzinfo=timezone.utc)


def test_leakage_post_tip_report_ignored():
    reps = {"11:30": {"a": "Out"}, "17:30": {"a": "Available"}, "19:30": {"a": "Questionable"}}
    ts, rep = A.last_report_before_tip(reps, DAY, _tip(19, 0))
    assert ts == A.slot_ts(DAY, "17:30") and rep["a"] == "Available"
    ts, rep = A.last_report_before_tip(reps, DAY, _tip(11, 0))
    assert ts is None and rep == {}


def test_lead_pushes_cutoff_back():
    reps = {"13:30": {"a": "Out"}, "17:30": {"a": "Available"}}
    ts, _ = A.last_report_before_tip(reps, DAY, _tip(19, 0), lead_min=240)
    assert ts == A.slot_ts(DAY, "13:30")


def test_report_at_tip_is_allowed_boundary():
    ts, _ = A.last_report_before_tip({"19:30": {"a": "Out"}}, DAY, _tip(19, 30))
    assert ts == _tip(19, 30)


def _slate(n=4000, seed=7):
    rng = np.random.default_rng(seed)
    planted = {"Out": 0.02, "Doubtful": 0.10, "Questionable": 0.50, "Probable": 0.90, "Available": 0.98, A.UNREPORTED: 0.97}
    sts = rng.choice(list(planted), size=n, p=[.1, .05, .2, .15, .2, .3])
    played = (rng.random(n) < np.array([planted[s] for s in sts])).astype(int)
    return pd.DataFrame({"status": sts, "played": played}), planted


def test_known_answer_play_rates_recovered():
    obs, planted = _slate()
    r = A.play_rates(obs).set_index("status")
    for s, p in planted.items():
        assert r.loc[s, "lo"] <= p <= r.loc[s, "hi"], s
    assert A.rate_map(A.play_rates(obs))["Out"] == pytest.approx(planted["Out"], abs=0.03)


def test_rate_map_falls_back_when_thin():
    obs = pd.DataFrame({"status": ["Out"] * 3 + ["Available"] * 50, "played": [0, 0, 0] + [1] * 50})
    m = A.rate_map(A.play_rates(obs), min_n=10, fallback={"Out": 0.05})
    assert m["Out"] == 0.05 and m["Available"] == 1.0


def _fixture():
    rot = pd.DataFrame({"game_id": ["g"] * 3, "team_id": [1] * 3, "person_id": [1, 2, 3], "w": [0.5, 0.3, 0.2]})
    names = pd.DataFrame({"person_id": [1, 2, 3], "norm_name": ["star one", "mid two", "bench three"]})
    gm = pd.DataFrame({"tip_earliest": [pd.Timestamp(_tip(19))], "day": [DAY]}, index=pd.Index(["g"], name="game_id"))
    return rot, names, gm


def test_status_table_matches_names_and_marks_unreported():
    rot, names, gm = _fixture()
    inj = {DAY: {"17:30": {"star one": "Out", "mid two": "Questionable"}, "21:30": {"star one": "Available"}}}
    st = A.status_table(rot, names, gm, inj).set_index("person_id")
    assert st.loc[1, "status"] == "Out" and st.loc[2, "status"] == "Questionable" and st.loc[3, "status"] == A.UNREPORTED
    assert st["has_report"].all()


def test_status_table_no_report_day():
    rot, names, gm = _fixture()
    st = A.status_table(rot, names, gm, {})
    assert (st["status"] == A.UNREPORTED).all() and not st["has_report"].any()


def test_expected_features_renormalise_and_cover():
    rot, names, gm = _fixture()
    st = A.status_table(rot, names, gm, {DAY: {"17:30": {"star one": "Out"}}})
    rat = pd.DataFrame({"game_id": ["g"] * 3, "person_id": [1, 2, 3], "rel_net": [10.0, 0.0, -5.0], "rel_ptot": 0.0, "rel_pace": 0.0})
    rates = {"Out": 0.0, A.UNREPORTED: 1.0}
    f = A.expected_lineup_features(st, rat, rates).iloc[0]
    # star out: weights renormalise over 0.3 and 0.2 -> (0*0.3 + -5*0.2)/0.5 = -2
    assert f["lineup_net_exp"] == pytest.approx(-2.0)
    assert f["exp_missing"] == pytest.approx(0.5) and f["cover"] == pytest.approx(0.5)
    # with every p = 1 the feature equals the plain rotation-weighted rating
    g = A.expected_lineup_features(st, rat, {"Out": 1.0, A.UNREPORTED: 1.0}).iloc[0]
    assert g["lineup_net_exp"] == pytest.approx(0.5 * 10 + 0.2 * -5)

"""W121.1: the weekly look carries its state forward; a planted effect earns an arm, a planted null does not; a missed
week is reported, never filled; a late row is counted, never scored into a look already taken."""
import json
import os
import random
from datetime import timedelta

import pytest

from prediction_market_bot.decision_trees.evidence import pipeline as P
from prediction_market_bot.decision_trees.evidence import weekly as W

BASE_WEEK = 10  # first look index used by the synthetic corpus


def _row(week, g, y, arm="RIDE", ticker_tag="A", cands=True):
    start = P.LOOK_ANCHOR + timedelta(weeks=week, days=1, hours=g % 5)
    ev = f"KXNBASPREAD-W{week}G{g}{ticker_tag}"
    r = {"sport": "NBA", "market_type": "NBA_SPREAD", "band": "T1", "event_ticker": ev, "market_ticker": ev + "-X",
         "run_id": "r1", "yes_bid": 0.69, "yes_ask": 0.71, "mid": 0.70, "y": float(y), "p_yes": None,
         "start_time_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "ts_utc": (start - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "router": {"arm": arm}}
    if cands:
        r["router_candidates"] = {"router_v2": {"arm": arm}}
    return r


def _corpus(weeks, p_yes, per_week=30, seed=1, skip=()):
    rng = random.Random(seed)
    return [_row(w, g, 1 if rng.random() < p_yes else 0) for w in range(BASE_WEEK, BASE_WEEK + weeks) if w not in skip
            for g in range(per_week)]


def _write(tmp, rows, name="NBA_A_T1.jsonl"):
    d = tmp / "shadow" / "settled"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return str(tmp / "shadow"), str(tmp / "nhl")


def _same(a, b, tol=1e-9):
    """Equal up to float summation order (carried look-by-look vs one pass differ at ~1e-14, nowhere else)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    return a == b


def _now(look):  # one hour after the cut that completes `look - 1`
    return P.LOOK_ANCHOR + timedelta(weeks=look, hours=1)


def test_cut_is_a_tuesday_ten_utc():
    c = W.cut_of(P.LOOK_ANCHOR + timedelta(weeks=7, days=3, hours=5))
    assert (c.weekday(), c.hour, c.minute) == (1, 10, 0) and W.cut_look(c) == 7
    assert W.cut_of(P.LOOK_ANCHOR + timedelta(weeks=7, minutes=-1)) == P.LOOK_ANCHOR + timedelta(weeks=6)


def test_state_json_round_trip_is_exact():
    cfg = P.Config()
    obs = [P.Obs(("NBA", "S", "T1", 3, "na"), f"g{i}", BASE_WEEK + i // 6, {"RIDE": 0.1 * (i % 3) - 0.05, "FADE": None,
                                                                          "MODEL_FADE": None, "MOMENTUM": None}) for i in range(60)]
    st = P.advance(P.State.new(cfg.arms), obs, cfg)
    again = P.State.from_json(json.loads(json.dumps(st.to_json())))
    assert again.to_json() == st.to_json()


def test_carried_forward_state_equals_a_single_pass(tmp_path):
    rows = _corpus(14, 0.80)
    sh, nh = _write(tmp_path, rows)
    inc, one = str(tmp_path / "inc"), str(tmp_path / "one")
    for look in (BASE_WEEK + 4, BASE_WEEK + 8, BASE_WEEK + 12, BASE_WEEK + 14):  # four weekly-ish runs, state carried
        W.run(sh, nh, inc, _now(look))
    W.run(sh, nh, one, _now(BASE_WEEK + 14))  # the same rows in one pass
    a, b = W.load_state(os.path.join(inc, "state.json")), W.load_state(os.path.join(one, "state.json"))
    assert _same(a["series"], b["series"]) and a["routes"] == b["routes"] and a["last_look"] == b["last_look"]


def test_planted_effect_earns_an_arm_in_the_expected_week(tmp_path):
    rows = _corpus(14, 0.92)  # RIDE at 0.71 pays about +0.2 per contract
    sh, nh = _write(tmp_path, rows)
    out = str(tmp_path / "o")
    first = None
    for look in range(BASE_WEEK + 1, BASE_WEEK + 15):
        rep = W.run(sh, nh, out, _now(look))
        if first is None and any(e["series"] == "NBA|v1" and e["arm"] == "RIDE" for e in rep["earned"]):
            first = look - BASE_WEEK
    assert first is not None and first <= 6, first
    final = W.load_state(os.path.join(out, "state.json"))["routes"]
    assert final["NBA|v1#NBA|NBA_SPREAD|T1|3|na"] == "RIDE" and final["NBA|router_v2#NBA|NBA_SPREAD|T1|3|na"] == "RIDE"


def test_planted_null_does_not_earn(tmp_path):
    rows = _corpus(14, 0.70, seed=4)  # win rate = price: net is minus the fee
    sh, nh = _write(tmp_path, rows)
    out = str(tmp_path / "o")
    for look in range(BASE_WEEK + 1, BASE_WEEK + 15):
        rep = W.run(sh, nh, out, _now(look))
        assert rep.get("earned", []) == []
    assert all(v == "NO_BET" for v in W.load_state(os.path.join(out, "state.json"))["routes"].values())


def test_a_missed_week_is_reported_not_filled(tmp_path):
    rows = _corpus(14, 0.80, skip=(BASE_WEEK + 6,))
    sh, nh = _write(tmp_path, rows)
    out = str(tmp_path / "o")
    W.run(sh, nh, out, _now(BASE_WEEK + 5))
    rep = W.run(sh, nh, out, _now(BASE_WEEK + 9))  # the Tuesday runs for weeks 5..8 never happened
    assert rep["catch_up"] is True
    assert rep["looks_scored"] == [BASE_WEEK + 5, BASE_WEEK + 7, BASE_WEEK + 8]
    assert rep["missed_looks"] == [BASE_WEEK + 6]  # a week with no settled rows at all: named, not invented
    assert "CATCH-UP" in W.summary(rep)


def test_a_late_row_is_counted_and_never_scored_into_a_taken_look(tmp_path):
    rows = _corpus(10, 0.80)
    sh, nh = _write(tmp_path, rows)
    out = str(tmp_path / "o")
    W.run(sh, nh, out, _now(BASE_WEEK + 6))
    before = json.dumps(W.load_state(os.path.join(out, "state.json"))["series"], sort_keys=True)
    _write(tmp_path, rows + [_row(BASE_WEEK + 2, 99, 1, ticker_tag="LATE")])  # settles after its week's look was taken
    rep = W.run(sh, nh, out, _now(BASE_WEEK + 7))
    assert rep["series"]["NBA|board"]["late_rows_not_scored"] == 1
    assert rep["series"]["NBA|v1"]["late_rows_not_scored"] == 1
    after = W.load_state(os.path.join(out, "state.json"))["series"]["NBA|board"]
    assert BASE_WEEK + 2 in after["looks"] and json.dumps(after, sort_keys=True) != before  # week 6 was added; week 2 not re-scored


def test_same_cut_twice_is_a_no_op(tmp_path):
    sh, nh = _write(tmp_path, _corpus(8, 0.8))
    out = str(tmp_path / "o")
    W.run(sh, nh, out, _now(BASE_WEEK + 6))
    s1 = open(os.path.join(out, "state.json")).read()
    rep = W.run(sh, nh, out, _now(BASE_WEEK + 6) + timedelta(days=3))
    assert rep.get("skipped") and open(os.path.join(out, "state.json")).read() == s1


def test_rows_without_candidate_blocks_feed_v1_and_board_only(tmp_path):
    rows = [_row(BASE_WEEK + w, g, g % 2, cands=False) for w in range(3) for g in range(8)]
    sh, nh = _write(tmp_path, rows)
    rep = W.run(sh, nh, str(tmp_path / "o"), _now(BASE_WEEK + 4))
    assert set(rep["series"]) == {"NBA|board", "NBA|v1"}


def test_a_state_of_another_schema_is_refused(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"schema": 99}))
    with pytest.raises(ValueError):
        W.load_state(str(p))

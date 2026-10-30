"""EXP-044c live entry (W97.1): frozen-artifact hash, pre-tip snapshot selection (leak guard), factor known answers, v2 parity."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.nba_engine import engine_v2 as V, engine_v3 as V3, live_v2 as L2, live_v3 as L3

TIP = datetime(2026, 10, 30, 23, 0, tzinfo=timezone.utc)   # 19:00 ET
ROT = [dict(norm_name="a star", w=0.6, rel_net=2.0), dict(norm_name="b role", w=0.4, rel_net=-1.0)]
RATES = {"Out": 0.0, "Questionable": 0.5, "Unreported": 0.8}


def test_frozen_artifact_hash_verifies_and_detects_tamper(tmp_path):
    art = L3.load_frozen()
    assert art["version"] == "v3" and art["factors"] and len(art["sha256"]) == 64
    bad = json.loads(L3.FROZEN.read_text())
    bad["params"]["hca"] += 0.1
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(bad, sort_keys=True, indent=1))
    with pytest.raises(ValueError):
        L3.load_frozen(f)


def test_team_factors_known_answer():
    f = L3.team_factors(ROT, {"a star": "Out", "b role": "Questionable"}, RATES, True)
    assert f["exp_missing"] == pytest.approx(0.6 * 1.0 + 0.4 * 0.5)
    assert f["lineup_net"] == pytest.approx(0.6 * 2.0 - 0.4)
    assert f["cover"] == pytest.approx(1.0)
    n = L3.team_factors(ROT, {"a star": "Out"}, RATES, False)       # no report: everyone Unreported, ignores statuses
    assert n["exp_missing"] == pytest.approx(0.2) and n["cover"] == 0.0


def test_snapshot_selection_is_pre_cutoff_and_leak_guarded():
    snaps = [dict(slot_et="2026-10-30 17:48", rows={"a": "Out"}),     # 21:48Z  <= 22:00Z cutoff
             dict(slot_et="2026-10-30 18:03", rows={"a": "Available"}),   # 22:03Z  after cutoff (post tip-60)
             dict(slot_et="2026-10-29 18:03", rows={"a": "Out"})]     # wrong ET day
    slot, rows = L3.select_snapshot(snaps, TIP)
    assert slot == "2026-10-30 17:48" and rows == {"a": "Out"}
    assert L3.select_snapshot([snaps[1]], TIP) == (None, {})
    assert L3.select_snapshot([], TIP) == (None, {})
    # every returned slot is at or before tip - 60
    assert L3._slot_utc(slot) <= TIP - timedelta(minutes=60)


def test_append_snapshot_renormalises_names_and_dedupes(tmp_path):
    st = tmp_path / "state.json"
    st.write_text(json.dumps(dict(slot_et="2026-10-30 17:48", rows={"nikola jokic": dict(name="Nikola Jokić", status="Out")})))
    out = tmp_path / "snap.jsonl"
    now = datetime(2026, 10, 30, 22, 0, tzinfo=timezone.utc)
    assert L3.append_snapshot(st, out, now) is True
    assert L3.append_snapshot(st, out, now) is False
    (row,) = L3.read_snapshots(out)
    assert row["rows"] == {"nikola jokic": "Out"}
    assert L3.append_snapshot(tmp_path / "missing.json", out, now) is False


def test_no_factors_equals_v2_pricing():
    art = L3.load_frozen()
    p, c = L3.build_model(art)
    mu_h, mu_a = 114.0, 111.0
    m3, t3 = V3.game_means(p, c, mu_h, mu_a, {})            # missing factors -> centred to 0 -> no shift
    m2, t2 = V.game_means(p, mu_h, mu_a)
    assert (m3, t3) == (m2, t2)
    parsed = dict(event_ticker="E", game_date="2026-10-30", away="OKC", home="DAL", subject="DAL", market_type="NBA_SPREAD", strike=2.5)
    assert 0.0 < L2.engine_p(p, m3, t3, parsed) < 1.0


def test_game_factors_sides_and_unknown_team():
    art = L3.load_frozen()
    tid = list(art["rotation"])[:2]
    x, cov = L3.game_factors(art, tid[0], tid[1], {}, False)
    assert x["d_exp_missing"] == pytest.approx(x["d_exp_missing"]) and set(x) == set(art["factors"])
    assert L3.game_factors(art, "0", tid[1], {}, False)[0] == {}

"""W83.2: NBA lineup-window capture -- parser parity, diff, event resolution, run() change/follow-up/rollover logic."""
import json
from datetime import datetime, timezone
from pathlib import Path

import scripts.nba_lineup_window_capture as m

FIX = Path(__file__).parent / "fixtures" / "nba_injury_report_layout_2026-10-21_0530PM.txt"
T0 = datetime(2026, 10, 21, 23, 33, tzinfo=timezone.utc)


def test_parse_fixture_parity_and_names():
    p = m.parse_report_text(FIX.read_text())
    assert p["header"] == "10/21/26 05:30 PM"
    assert len(p["rows"]) == p["n_status_tokens"] == 85
    assert "jonathan isaac" in p["rows"]  # "Isaac,Jonathan": no space after the comma


def test_diff_rows():
    a = {"x y": {"name": "X Y", "status": "Questionable"}, "z w": {"name": "Z W", "status": "Out"}}
    b = {"x y": {"name": "X Y", "status": "Out"}, "n n": {"name": "N N", "status": "Out"}}
    kinds = {(c["kind"], c["key"]) for c in m.diff_rows(a, b)}
    assert kinds == {("changed", "x y"), ("added", "n n"), ("removed", "z w")}


def test_slot_url_and_midnight():
    s = datetime(2026, 10, 21, 19, 30, tzinfo=timezone.utc)  # 15:30 ET
    assert m.slot_url(m.slot_candidates(s.replace(minute=33))[0]).endswith("2026-10-21_03_30PM.pdf")
    assert m.slot_url(m.slot_candidates(datetime(2026, 10, 22, 4, 5, tzinfo=timezone.utc))[0]).endswith("2026-10-22_12_00AM.pdf")


def _mk(player, ev="KXNBAPTS-26OCT21MINMIA"):
    return {"event_ticker": ev, "ticker": ev + "-X", "no_sub_title": player + ": 20+", "floor_strike": 19.5,
            "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.45", "last_price_dollars": "0.42", "open_interest_fp": "10"}


def _rep(slot):
    return {"slot_et": slot, "url": "u", "published_utc": "2026-10-21T23:30:04Z", "content": b""}


def test_run_change_followup_and_unresolved(tmp_path):
    rows1 = "Doe, John   Questionable   Injury/Illness -Knee\nInjury Report: 10/21/26 05:30 PM\n"
    rows2 = "Doe, John   Out   Injury/Illness -Knee\nRoe, Rick   Out   Rest\nInjury Report: 10/21/26 05:45 PM\n"
    book = [_mk("John Doe"), _mk("Sam Star")]
    m.run(tmp_path, T0, _rep("2026-10-21 17:30"), book, None, text_fn=lambda c: rows1)
    book2 = [_mk("John Doe"), _mk("Sam Star")]
    m.run(tmp_path, T0.replace(minute=48), _rep("2026-10-21 17:45"), book2, None, text_fn=lambda c: rows2)
    ev = [json.loads(l) for l in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert len(ev) == 1 and ev[0]["event_unresolved"] == 1  # Rick Roe has no market
    assert ev[0]["affected"] == {"KXNBAPTS-26OCT21MINMIA": ["John Doe"]}
    assert ev[0]["book_before"]["KXNBAPTS-26OCT21MINMIA"] and not ev[0]["book_before_stale"]
    m.run(tmp_path, T0.replace(minute=58), None, book2, None)
    assert len((tmp_path / "followups.jsonl").read_text().splitlines()) == 1
    assert len((tmp_path / "checks.jsonl").read_text().splitlines()) == 3


def test_rollover_and_same_slot_no_event(tmp_path):
    a = "Doe, John   Out   x\nInjury Report: 10/21/26 05:30 PM\n"
    b = "Zed, Al   Out   x\nInjury Report: 10/22/26 09:00 AM\n"
    m.run(tmp_path, T0, _rep("2026-10-21 17:30"), [_mk("John Doe")], None, text_fn=lambda c: a)
    m.run(tmp_path, T0, _rep("2026-10-21 17:30"), [_mk("John Doe")], None, text_fn=lambda c: a)  # same slot
    hb = m.run(tmp_path, T0, _rep("2026-10-22 09:00"), [_mk("John Doe")], None, text_fn=lambda c: b)
    assert hb.get("day_rollover") and not (tmp_path / "events.jsonl").exists()


def test_install_gate_exempts_only_exact_own_first_run_state():
    """GG-1080: the install gate refuses on RED unless every red reason is the job's own `no write found` first-run state."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import nba_lineup_window_install as ni
    own = "STALE cron|3,18,33,48 * * * *|scripts/nba_lineup_window_capture.py: no write found"
    st = {"t": "x\n"}
    rd, wr = (lambda: st["t"]), (lambda t: st.__setitem__("t", t))
    # own first-run only -> installs
    assert ni.install(lambda: {"budget": "RED", "reasons": [own]}, rd, wr) == 0 and ni.BEGIN in st["t"]
    for ev in (
        {"budget": "RED", "reasons": [own, "SILENT ARM nba_lineup_window_x: zero rows"]},                 # name-matching red of another kind
        {"budget": "RED", "reasons": ["healthcheck: 2 faults"]},
        {"budget": "RED", "reasons": []},                                                                  # RED with no reasons recorded
        {"budget": "RED", "reasons": ["STALE cron|3 * * * *|scripts/nba_lineup_window_capture.py: last write 90h ago (limit 2h)"]},
        {"budget": "RED", "reasons": ["DOWN systemd|t4-mlb: failed/failed", "STALE cron|3 * * * *|scripts/nba_lineup_window_capture.py_extra: no write found"]},
    ):
        st["t"] = "x\n"
        ni.install(lambda ev=ev: ev, rd, wr)
        assert st["t"] == "x\n", ev

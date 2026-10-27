"""W87.2 / GG-1082 / GG-441: every order-capable book feeds the gate; submit_order consults it."""
import json
import time

import pytest

from prediction_market_bot.c4_risk_engine import exposure_gate as eg
from prediction_market_bot.c5_execution import kalshi_client as kc


def _book(pnl=0.0, positions=(), initial=1000.0):
    return {"initial_bankroll_usd": initial, "total_realized_pnl": pnl,
            "open_positions": [dict(p) for p in positions]}


def _pos(t, size):
    return {"kalshi_ticker": t, "size_usd": size, "status": "OPEN"}


@pytest.fixture(autouse=True)
def _dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("PMBOT_KILL_SWITCH_DIR", str(tmp_path))
    monkeypatch.delenv(eg.MODE_ENV, raising=False)
    return tmp_path


def _client():
    c = kc.KalshiMarketClient.__new__(kc.KalshiMarketClient)
    return c


def test_record_book_merges_not_clobbers(tmp_path):
    eg.record_book("MLB_T1", _book(-10.0), logs_dir=tmp_path)
    out = eg.record_book("MLB_T4", _book(-20.0), logs_dir=tmp_path)
    assert set(out["books"]) == {"MLB_T1", "MLB_T4"}
    assert out["system"]["realized_loss_usd"] == 30.0


def test_frozen_book_reported_but_not_summed(tmp_path):
    eg.record_book("MLB_T1", _book(-10.0), logs_dir=tmp_path)
    out = eg.record_book("NBA_T1", _book(-249.0), logs_dir=tmp_path)
    assert out["books"]["NBA_T1"]["frozen"] is True
    assert out["system"]["realized_loss_usd"] == 10.0 and not out["breaches"]


def test_tripped_book_refuses_order_in_enforce(tmp_path, monkeypatch):
    monkeypatch.setenv(eg.MODE_ENV, "enforce")
    eg.record_book("MLB_T1", _book(), logs_dir=tmp_path)
    o = _client().submit_order("T", "yes", 5.0, 0.5, band="t4_mlb")  # no writer for MLB_T4
    assert not o.ok and o.status == "halted" and o.error.startswith("exposure_gate_halted:")
    eg.record_book("MLB_T4", _book(-250.0), logs_dir=tmp_path)  # breach: flag + gate both refuse
    o = _client().submit_order("T", "yes", 5.0, 0.5, band="t4_mlb")
    assert not o.ok and o.status == "halted"


def test_log_mode_records_would_halt_and_does_not_refuse(tmp_path):
    assert eg.gate_for_order("t4_mlb", tmp_path) is None  # no state at all: would halt, log only
    rec = [json.loads(l) for l in (tmp_path / eg.LOGONLY_FILE).read_text().splitlines()]
    assert rec[0]["event"] == "would_halt" and rec[0]["book"] == "MLB_T4"


def test_missing_and_corrupt_state_halt(tmp_path, monkeypatch):
    monkeypatch.setenv(eg.MODE_ENV, "enforce")
    assert eg.gate_for_order("t1_mlb", tmp_path)
    (tmp_path / eg.STATE_FILE).write_text("{not json")
    assert eg.gate_for_order("t1_mlb", tmp_path)


def test_book_with_no_writer_refused_never_waved_through(tmp_path, monkeypatch):
    monkeypatch.setenv(eg.MODE_ENV, "enforce")
    eg.record_book("MLB_T1", _book(), logs_dir=tmp_path)
    assert eg.gate_for_order("t4_mlb", tmp_path).startswith("exposure_book_no_writer:MLB_T4")
    assert eg.gate_for_order("t1_mlb", tmp_path) is None
    assert eg.gate_for_order(None, tmp_path).startswith("exposure_band_unmapped")


def test_failed_feed_refuses_that_book(tmp_path, monkeypatch):
    monkeypatch.setenv(eg.MODE_ENV, "enforce")
    eg.record_book("MLB_T1", _book(), logs_dir=tmp_path)
    eg.mark_feed_failed("MLB_T1", "boom", tmp_path)
    assert eg.gate_for_order("t1_mlb", tmp_path).startswith("exposure_book_feed_error")


def test_unknown_mode_fails_closed(monkeypatch):
    monkeypatch.setenv(eg.MODE_ENV, "bogus")
    assert eg.gate_mode() == "enforce"


def test_nfr03_halt_under_60s_across_every_book(tmp_path):
    t0 = time.monotonic()
    for b in ("MLB_T1", "MLB_T4", "SHADOW"):
        eg.record_book(b, _book(-60.0), logs_dir=tmp_path)
    assert time.monotonic() - t0 < 60


def test_system_breach_halts_and_every_book_refused(tmp_path, monkeypatch):
    monkeypatch.setenv(eg.MODE_ENV, "enforce")
    for b in ("MLB_T1", "MLB_T4"):
        eg.record_book(b, _book(-190.0), logs_dir=tmp_path)
    eg.record_book("SHADOW", _book(), logs_dir=tmp_path)
    t0 = time.monotonic()
    out = eg.record_book("MLB_T1", _book(-210.0), logs_dir=tmp_path)
    assert "MLB_T1" in out["breaches"]
    for band in ("t1_mlb", "t4_mlb", "shadow"):
        assert eg.gate_for_order(band, tmp_path)
    assert time.monotonic() - t0 < 60


def test_settled_feed_caches_and_survives_failures(tmp_path):
    calls = []

    def fn(t):
        calls.append(t)
        return {"A": "settled", "B": "active", "C": None}[t]
    s = eg.refresh_settled(["A", "B", "C"], fn, tmp_path, ttl_s=0)
    assert s == {"A"} and sorted(calls) == ["A", "B", "C"]
    assert "settled_feed_errors" in (tmp_path / eg.LOGONLY_FILE).read_text()
    assert eg.load_settled(tmp_path)[0] == {"A"}


def test_shadow_state_counts_placed_orders(tmp_path):
    p = tmp_path / "pol.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in [
        {"event": "shadow_order", "ok": True, "order_id": "1", "stake_usd": 5.0, "ticker": "X"},
        {"event": "shadow_order", "ok": False, "order_id": "", "stake_usd": 5.0, "ticker": "Y"},
        {"event": "shadow_skip"}]))
    s = eg.shadow_state(p)
    assert len(s["open_positions"]) == 1
    assert eg.book_exposure(s)["open_stake_usd"] == 5.0

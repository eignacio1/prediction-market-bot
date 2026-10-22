"""W85.3 / GG-441: exposure gate sees settled-but-unresolved stake, persists, fails closed."""
import json

from prediction_market_bot.c4_risk_engine import exposure_gate as eg
from prediction_market_bot.c5_execution import kill_switch_state as ks


def _book(pnl=0.0, positions=(), initial=1000.0):
    return {"initial_bankroll_usd": initial, "total_realized_pnl": pnl,
            "open_positions": [dict(p) for p in positions]}


def _pos(ticker, size, **kw):
    return {"kalshi_ticker": ticker, "size_usd": size, "status": "OPEN", **kw}


def test_resolution_dark_unresolved_stake_trips(tmp_path):
    # realized loss alone (10.6%) is under 20%; 17 settled-unresolved positions push worst case over
    b = _book(-106.0, [_pos(f"T{i}", 12.0) for i in range(10)])
    out = eg.update({"MLB": b}, settled_tickers=[f"T{i}" for i in range(10)], logs_dir=tmp_path)
    assert out["books"]["MLB"]["settled_unresolved_stake_usd"] == 120.0
    assert "MLB" in out["breaches"] and "SYSTEM" in out["breaches"]
    assert ks.halt_reason(logs_dir=tmp_path).startswith("kill_switch_flag:")
    assert eg.check_before_order(tmp_path).startswith("exposure_gate_breach")
    assert out["elapsed_ms"] < 60_000


def test_live_open_stake_reported_not_lost(tmp_path):
    b = _book(-50.0, [_pos("LIVE", 100.0)])
    out = eg.update({"MLB": b}, logs_dir=tmp_path)
    x = out["books"]["MLB"]
    assert x["open_stake_usd"] == 100.0 and x["total_exposure_usd"] == 150.0
    assert not out["breaches"] and eg.check_before_order(tmp_path) is None
    assert ks.halt_reason(logs_dir=tmp_path) is None


def test_system_wide_trips_when_no_single_book_does(tmp_path):
    a = _book(-150.0, initial=1000.0)       # 15%
    c = _book(-90.0, initial=1000.0)        # 9%
    out = eg.update({"A": a, "B": c}, logs_dir=tmp_path)
    assert out["system"]["worst_case_drawdown_pct"] == 0.12 and not out["breaches"]
    out = eg.update({"A": _book(-190.0), "B": _book(-190.0, initial=200.0)}, logs_dir=tmp_path)
    assert "B" in out["breaches"]


def test_restart_mid_day_reloads_breach(tmp_path):
    eg.update({"MLB": _book(-250.0)}, logs_dir=tmp_path)
    ks.global_flag_path(tmp_path).unlink()          # flag lost, e.g. manual rm or fresh volume
    assert eg.check_before_order(tmp_path).startswith("exposure_gate_breach")


def test_missing_state_fails_closed(tmp_path):
    assert eg.check_before_order(tmp_path) == "exposure_state_missing"


def test_corrupt_state_fails_closed(tmp_path):
    eg.state_path(tmp_path).write_text("{not json")
    assert eg.check_before_order(tmp_path) == "exposure_state_corrupt:parse"
    eg.state_path(tmp_path).write_text(json.dumps({"schema": 1, "books": {}}))
    assert eg.check_before_order(tmp_path).startswith("exposure_state_corrupt")
    eg.state_path(tmp_path).write_text(json.dumps([1]))
    assert eg.check_before_order(tmp_path).startswith("exposure_state_corrupt")


def test_zero_initial_bankroll_fails_closed(tmp_path):
    out = eg.update({"X": _book(0.0, initial=0.0)}, logs_dir=tmp_path)
    assert "X" in out["breaches"]

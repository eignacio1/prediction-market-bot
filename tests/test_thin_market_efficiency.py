"""W80R.2: 12_EXPLORATORY/thin_markets/efficiency.py -- quote rule, kickoff approximation, windows, custody rule,
event-cluster bootstrap, ranking. Synthetic data only."""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("thin_eff", REPO / "12_EXPLORATORY" / "thin_markets" / "efficiency.py")
ef = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ef)

UTC = timezone.utc


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _mkt(ticker, close, result="yes"):
    return {"ticker": ticker, "event_ticker": ticker.rsplit("-", 1)[0], "close_time": _iso(close), "result": result}


def _candles(start, end, step_s, bid, ask, vol):
    out, t = [], start
    while t <= end:
        out.append({"t": int(t.timestamp()), "bid": bid, "ask": ask, "vol": vol, "oi": 500.0})
        t += timedelta(seconds=step_s)
    return out


CLOSE = datetime(2025, 10, 5, 16, 45, tzinfo=UTC)            # London game: kickoff 13:30Z


def test_kickoff_and_friday_report():
    m = _mkt("KXNFLGAME-25OCT05MINCLE-MIN", CLOSE)
    assert ef.kickoff(m) == datetime(2025, 10, 5, 13, 30, tzinfo=UTC)
    assert ef.friday_report(ef.kickoff(m)) == datetime(2025, 10, 3, 20, 0, tzinfo=UTC)       # 16:00 EDT
    thu = datetime(2025, 10, 10, 0, 15, tzinfo=UTC)                                          # Thu night ET
    assert ef.friday_report(thu) is None
    assert ef.friday_report(datetime(2025, 11, 9, 18, 0, tzinfo=UTC)) == datetime(2025, 11, 7, 21, 0, tzinfo=UTC)  # EST


def test_quote_rule_prevailing_and_validity():
    cs = [{"t": 100, "bid": 0.40, "ask": 0.44, "vol": 1, "oi": 1}, {"t": 200, "bid": 0.0, "ask": 1.0, "vol": 1, "oi": 1}]
    assert abs(ef.quote_at(cs, 150)["mid"] - 0.42) < 1e-12
    assert ef.quote_at(cs, 99) is None
    assert ef.quote_at(cs, 250) is None                          # empty book is not a quote


def test_per_market_spread_volume_fill():
    m = _mkt("KXNFLTOTAL-25OCT05MINCLE-45", CLOSE)
    ko = ef.kickoff(m)
    c1 = _candles(ko - timedelta(hours=30), ko + timedelta(hours=3), 60, 0.48, 0.52, 2.0)       # 120 contracts/hr
    c60 = _candles(ko - timedelta(days=5), ko + timedelta(hours=3), 3600, 0.48, 0.52, 120.0)
    r = ef.per_market(m, c1, c60)
    assert abs(r["spread_c"] - 4.0) < 1e-9
    assert 119 <= r["vol_hr"] <= 121
    # stake $1 at mid 0.5 = 2 contracts; 10% of 120 = 12 >= 2 -> every hour fillable
    assert r["fill_share"] == 1.0
    assert r["report_move"] == 0.0 and r["late_move"] == 0.0


def test_unfillable_when_volume_thin():
    m = _mkt("KXNFLRECYDS-25OCT05MINCLE-X-60", CLOSE)
    ko = ef.kickoff(m)
    c1 = _candles(ko - timedelta(hours=30), ko, 60, 0.10, 0.20, 0.01)                         # 0.6 contracts/hr
    assert ef.per_market(m, c1, [])["fill_share"] == 0.0


def test_custody_rule():
    assert ef.analysed(_mkt("KXNFLGAME-25OCT05X-A", CLOSE))
    assert not ef.analysed(_mkt("KXNFLGAME-26SEP13X-A", datetime(2026, 9, 13, 20, 0, tzinfo=UTC)))
    assert not ef.analysed({**_mkt("KXNFLGAME-25OCT05X-A", CLOSE), "result": ""})


def test_boot_clusters_by_event_and_is_deterministic():
    rows = [{"event": f"E{i // 2}", "spread_c": float(i)} for i in range(20)]
    a, b = ef.boot(rows, "spread_c", "median", b=200), ef.boot(rows, "spread_c", "median", b=200)
    assert a == b and a["n_events"] == 10 and a["n_mkts"] == 20 and a["lo"] <= a["est"] <= a["hi"]


def test_summarize_excludes_custody_and_ranks_thinnest_first(tmp_path):
    rows = []
    for series, spread, vol in (("KXNFLGAME", 0.01, 500.0), ("KXNFLRECYDS", 0.08, 5.0)):
        for i in range(4):
            close = CLOSE + timedelta(days=7 * i)
            t = f"{series}-25OCT{5 + 7 * i:02d}AAA{i}-X"
            m = _mkt(t, close)
            ko = ef.kickoff(m)
            cs = [{"end_period_ts": c["t"], "yes_bid": {"close": f"{c['bid']:.4f}"}, "yes_ask": {"close": f"{c['ask']:.4f}"},
                   "volume": f"{c['vol']:.2f}", "open_interest": "100.00"}
                  for c in _candles(ko - timedelta(hours=30), ko, 60, 0.5 - spread / 2, 0.5 + spread / 2, vol / 60)]
            rows.append({"kind": "markets_page", "key": t, "payload": {"markets": [m]}})
            rows.append({"kind": "candles", "key": f"{t}|1|0|1", "payload": {"candlesticks": cs}})
    cust = _mkt("KXNFLGAME-26SEP13ZZZ-X", datetime(2026, 9, 13, 20, 0, tzinfo=UTC))
    rows.append({"kind": "markets_page", "key": "c", "payload": {"markets": [cust]}})
    rows.append({"kind": "candles", "key": f"{cust['ticker']}|1|0|1", "payload": {"candlesticks": [
        {"end_period_ts": 1, "yes_bid": {"close": "0.4"}, "yes_ask": {"close": "0.5"}, "volume": "1"}]}})
    p = tmp_path / "raw_2026-10-16.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    s = ef.summarize(*ef.load([str(p)]), b=50)
    assert s["KXNFLGAME"]["n_markets"] == 4 and s["KXNFLGAME"]["custody_excluded"] == 1
    assert ef.rank(s) == ["KXNFLRECYDS", "KXNFLGAME"]
    assert "KXNFLRECYDS" in ef.render(s, ef.rank(s))

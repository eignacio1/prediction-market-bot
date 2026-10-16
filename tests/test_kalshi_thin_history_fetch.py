"""W79.2: thin-market fetcher -- resume skips stored keys, sample is deterministic, 2026-season markets are custody-only."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("kalshi_thin_history_fetch", ROOT / "scripts" / "kalshi_thin_history_fetch.py")
thin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thin)


def mkt(t, close="2025-11-02T18:00:00Z", opn="2025-10-20T18:00:00Z"):
    return {"ticker": t, "close_time": close, "open_time": opn, "expiration_time": close, "result": "yes"}


def test_sample_is_deterministic_and_order_independent():
    ms = [mkt(f"KXNFLSPREAD-25NOV02-T{i}") for i in range(60)]
    a = thin.sample(ms, 10)
    b = thin.sample(list(reversed(ms)), 10)
    assert [m["ticker"] for m in a] == [m["ticker"] for m in b]
    assert len(a) == 10 and len({m["ticker"] for m in a}) == 10


def test_sample_cap_larger_than_family_returns_all():
    ms = [mkt(f"X-{i}") for i in range(5)]
    assert len(thin.sample(ms, 100)) == 5


def test_custody_only_flags_2026_season_only():
    assert not thin.custody_only(mkt("a", close="2026-02-08T23:00:00Z"))   # 2025 NFL season (Super Bowl)
    assert not thin.custody_only(mkt("b", close="2026-06-15T01:00:00Z"))   # 2025-26 NBA finals
    assert thin.custody_only(mkt("c", close="2026-09-13T20:00:00Z"))       # 2026 NFL season
    assert thin.custody_only(mkt("d", close="2026-10-20T23:00:00Z"))       # 2026-27 NBA opener


class FakeStore:
    def __init__(self, index=()):
        self.index = {k: {"h"} for k in index}
        self.written = self.skipped = 0


class FakeClient:
    def stats(self):
        return {}


def test_resume_skips_stored_candle_keys(monkeypatch):
    m = mkt("KXNFLTOTAL-25NOV02-T45", close="2025-11-02T18:00:00Z", opn="2025-10-20T18:00:00Z")
    monkeypatch.setattr(thin, "markets_of", lambda *a, **k: [m])
    close, opn = thin.bs.iso_ts(m["close_time"]), thin.bs.iso_ts(m["open_time"])
    k60 = ("candles", f"{m['ticker']}|60|{opn}|{close + 3600}")
    start1 = max(opn, close - thin.MINUTE_LOOKBACK_S)
    k1 = ("candles", f"{m['ticker']}|1|{start1}|{close + 120}")
    calls = []
    monkeypatch.setattr(thin.bs, "candles", lambda c, s, series, mk, start, end, period, cutoff: calls.append(period))
    thin.fetch(FakeClient(), FakeStore([k60]), ["KXNFLTOTAL"], cap=5)
    assert calls == [1]                                    # hourly stored -> only the 1-minute window fetched
    calls.clear()
    thin.fetch(FakeClient(), FakeStore([k60, k1]), ["KXNFLTOTAL"], cap=5)
    assert calls == []                                     # fully stored -> nothing re-fetched
    thin.fetch(FakeClient(), FakeStore(), ["KXNFLTOTAL"], cap=5)
    assert calls == [60, 1]

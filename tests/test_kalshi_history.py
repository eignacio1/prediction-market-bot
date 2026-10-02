"""D4 tests: Kalshi history reader (prevailing_quote, settlement) + builder idempotence on a synthetic raw store."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import board_survey_sports_store as bs  # noqa: E402
import kalshi_history_build as kb  # noqa: E402
from prediction_market_bot.analytics import kalshi_history as kh  # noqa: E402

T = "KXNFLTOTAL-25SEP07DALPHI-44"
CLOSE = "2025-09-08T01:00:00Z"
OPEN = "2025-09-01T00:00:00Z"
C = bs.iso_ts(CLOSE)


def _candle(t, bid, ask):
    return {"end_period_ts": t, "yes_bid": {"open": bid, "high": bid, "low": bid, "close": bid},
            "yes_ask": {"open": ask, "high": ask, "low": ask, "close": ask},
            "price": {"close": bid}, "volume": 3}


def _live_candle(t, bid, ask):  # live-endpoint key style
    return {"end_period_ts": t, "yes_bid": {"close_dollars": str(bid)}, "yes_ask": {"close_dollars": str(ask)},
            "volume_fp": "2.00"}


def _build_store(tmp_path):
    d = tmp_path / "KH"
    st = bs.Store(d / "raw", sha="testsha")
    mk = {"ticker": T, "event_ticker": "KXNFLTOTAL-25SEP07DALPHI", "open_time": OPEN, "close_time": CLOSE,
          "settlement_ts": CLOSE, "result": "yes", "expiration_value": "47"}
    st.put("markets_page", "/historical/markets|KXNFLTOTAL|", {"markets": [mk]}, "u1")
    st.put("candles", f"{T}|60|1|2", {"candlesticks": [_candle(C - 7200, 0.40, 0.44), _candle(C - 3600, 0.45, 0.49),
                                                      _live_candle(C, 0.50, 0.54)]}, "u2")
    st.put("candles", f"{T}|1|3|4", {"candlesticks": [_candle(C - 600, 0.46, 0.50), _candle(C - 540, 0.47, None)]}, "u3")
    del st
    return d


def test_build_reader_and_idempotence(tmp_path, monkeypatch):
    d = _build_store(tmp_path)
    s1 = kb.build(d)
    first = (d / "candles" / "KXNFLTOTAL.jsonl").read_bytes(), (d / "markets" / "KXNFLTOTAL.jsonl").read_bytes()
    s2 = kb.build(d)
    assert s1 == s2
    assert first == ((d / "candles" / "KXNFLTOTAL.jsonl").read_bytes(), (d / "markets" / "KXNFLTOTAL.jsonl").read_bytes())
    m = json.loads((d / "markets" / "KXNFLTOTAL.jsonl").read_text())
    assert m["provenance"]["source_url"] == "u1" and m["provenance"]["runtime_commit_sha"] == "testsha"
    assert m["season"] == "2025" and m["validation"]["ok"]
    kh._idx.clear()

    # settlement
    assert kh.settlement(T, store=d) == "yes"
    assert kh.settlement("KXNFLTOTAL-NOPE", store=d) is None

    # 1-minute first: latest candle with end_period_ts <= t
    assert kh.prevailing_quote(T, C - 600, store=d) == (0.46, 0.50, C - 600)
    assert kh.prevailing_quote(T, C - 599, store=d) == (0.46, 0.50, C - 600)
    assert kh.prevailing_quote(T, C - 540, store=d) == (0.47, None, C - 540)   # null ask preserved
    # strictly-future candles are never used
    assert kh.prevailing_quote(T, C - 601, store=d) == (0.45, 0.49, C - 3600)  # before first 1-min -> hourly fallback
    # hourly fallback, mixed schema normalized (live *_dollars keys)
    assert kh.prevailing_quote(T, C - 3601, store=d) == (0.40, 0.44, C - 7200)
    assert kh.prevailing_quote(T, C - 7200, store=d) == (0.40, 0.44, C - 7200)
    # before any candle -> None; unknown ticker -> None
    assert kh.prevailing_quote(T, C - 7201, store=d) is None
    assert kh.prevailing_quote("KXNFLTOTAL-NOPE", C, store=d) is None
    # t as ISO string / datetime
    assert kh.prevailing_quote(T, "2025-09-08T00:50:00Z", store=d) == (0.46, 0.50, C - 600)


def test_validation_flags_crossed_and_unsorted():
    v = kb.validate_candles([{"t": 2, "bid": {"close": 0.6}, "ask": {"close": 0.5}},
                             {"t": 1, "bid": {"close": 0.1}, "ask": {"close": 0.2}}])
    assert not v["ok"] and v["crossed"] == 1 and not v["sorted_unique"]
    assert kb.validate_candles([{"t": 1, "bid": {"close": 0.1}, "ask": {"close": 0.2}}])["ok"]


def test_season_of():
    assert kb.season_of("nfl", "2026-01-12T00:00:00Z") == "2025"
    assert kb.season_of("nhl", "2026-01-12T00:00:00Z") == "2025-26"
    assert kb.season_of("nhl", "2026-10-12T00:00:00Z") == "2026-27"

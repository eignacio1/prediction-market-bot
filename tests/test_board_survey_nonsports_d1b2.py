"""EXP-034 D1(b)-2 lookback logic: pull backward until a candle earlier than the first read is held, or market open."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import board_survey_nonsports_candles as bc  # noqa: E402
import board_survey_nonsports_d1b2_gate as g  # noqa: E402


def _fake(candle_ts):
    calls = []

    def fetch(s, e):
        calls.append((s, e))
        return [{"end_period_ts": t} for t in candle_ts if s <= t <= e]
    return fetch, calls


def test_stops_after_first_chunk_when_candle_found():
    fetch, calls = _fake([1_000_000 - 100])
    out = g.pull_back_to_open(fetch, 1_000_000, 1_000_600, 1)
    assert len(calls) == 1 and len(out) == 1


def test_walks_back_to_old_candle():
    old = 1_000_000 - 5 * 86400
    fetch, calls = _fake([old])
    out = g.pull_back_to_open(fetch, 1_000_000, 1_000_600, 1)
    assert any(c["end_period_ts"] == old for c in out) and len(calls) >= 3


def test_stops_at_market_open_when_no_candle_exists():
    fetch, calls = _fake([])
    out = g.pull_back_to_open(fetch, 1_000_000, 1_000_600, 1_000_000 - 3 * 86400)
    assert out == [] and calls[-1][0] == 1_000_000 - 3 * 86400


def test_sparse_ticker_old_candle_matches_prior_close():
    c = bc.parse_candle({"end_period_ts": 900, "yes_bid": {"close": "0.30"}, "yes_ask": {"close": "0.40"}})
    row = {"ticker": "X", "round": 0, "ts": "1970-01-01T00:30:00+00:00", "yes_bid": "0.30", "yes_ask": "0.40"}
    r = bc.compare(row, [c])
    assert r["kind"] == "prior" and r["pass"]

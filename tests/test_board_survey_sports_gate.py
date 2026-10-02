"""Tests for scripts/board_survey_sports_{store,gate}.py (EXP-035 / T-604, T-605). Synthetic data except the
G7 reader, which reads the real committed EXP-032 results.json. No network, no archive."""
import json
import os
import sys
from datetime import datetime, timezone

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import board_survey_sports_gate as gate  # noqa: E402
import board_survey_sports_store as bs  # noqa: E402

EXP032 = os.path.join(HERE, "..", "exp_output", "EXP-032-EXECUTION-COST-SURFACE")

HIST = {"end_period_ts": 1785625200, "open_interest": "2058.21", "volume": "0.00",
        "price": {"close": None, "high": None, "low": None, "mean": None, "open": None, "previous": "0.4700"},
        "yes_ask": {"close": "0.4700", "high": "0.4900", "low": "0.4600", "open": "0.4700"},
        "yes_bid": {"close": "0.4600", "high": "0.4600", "low": "0.4400", "open": "0.4600"}}
LIVE = {"end_period_ts": 1785625200, "open_interest_fp": "2058.21", "volume_fp": "0.00",
        "price": {"previous_dollars": "0.4700"},
        "yes_ask": {"close_dollars": "0.4700", "high_dollars": "0.4900", "low_dollars": "0.4600", "open_dollars": "0.4700"},
        "yes_bid": {"close_dollars": "0.4600", "high_dollars": "0.4600", "low_dollars": "0.4400", "open_dollars": "0.4600"}}


def candle(ts, bid, ask):
    return {"end_period_ts": ts, "yes_bid": {"close": f"{bid:.4f}", "high": f"{bid:.4f}", "low": f"{bid:.4f}", "open": f"{bid:.4f}"},
            "yes_ask": {"close": f"{ask:.4f}", "high": f"{ask:.4f}", "low": f"{ask:.4f}", "open": f"{ask:.4f}"}}


# ------------------------------------------------------------------ schemas
def test_live_and_historical_schemas_parse_identically():
    assert gate.norm_candle(HIST) == gate.norm_candle(LIVE)
    n = gate.norm_candle(LIVE)
    assert n["yes_bid"]["close"] == 0.46 and n["yes_ask"]["high"] == 0.49
    assert n["open_interest"] == 2058.21 and n["volume"] == 0.0


def test_null_price_with_populated_previous():
    n = gate.norm_candle(HIST)
    assert n["price_close"] is None and n["price_previous"] == 0.47
    assert gate.norm_candle({**LIVE, "price": {}})["price_previous"] is None      # live: price == {}


def test_q_reads_either_schema_and_missing_is_none():
    assert gate.q(HIST["yes_bid"], "close") == gate.q(LIVE["yes_bid"], "close") == 0.46
    assert gate.q({"close": None}, "close") is None and gate.q({"close": ""}, "close") is None
    assert gate.q(None, "close") is None


def test_empty_book_placeholder_bid_zero_parses_to_zero_not_none():
    n = gate.norm_candle({"end_period_ts": 1, "yes_bid": {"close_dollars": "0.0000"}, "yes_ask": {"close_dollars": "0.4800"}})
    assert n["yes_bid"]["close"] == 0.0 and n["yes_ask"]["close"] == 0.48


# ------------------------------------------------------------------ settlements
def test_scalar_settlements_excluded_from_binary_set():
    snaps = {"A": [], "B": [], "C": [], "D": []}
    settle = {"A": {"result": "yes"}, "B": {"result": "no"}, "C": {"result": "scalar"}}
    assert gate.binary_settled(snaps, settle) == ["A", "B"]          # C scalar, D unsettled


# ------------------------------------------------------------------ Part 1 matching rule on a sparse series
def test_part1_match_takes_next_change_not_prevailing_quote():
    """1-minute candles have NO row when nothing changed. Quote 0.40/0.45 prevails from ts=100 to 400; the next
    row is a different quote at ts=400. A snapshot at t=250 (true prevailing quote 0.40/0.45) is matched by
    Part 1's rule to the ts=400 candle -- a different quote by construction (H1)."""
    cs = [candle(400, 0.50, 0.55), candle(100, 0.40, 0.45)]          # deliberately unsorted
    idx, srt = gate.part1_match(cs, 250)
    assert [c["end_period_ts"] for c in srt] == [100, 400]
    assert srt[idx]["end_period_ts"] == 400 and gate.q(srt[idx]["yes_bid"], "close") == 0.50


def test_part1_match_boundary_and_none():
    cs = [candle(100, 0.4, 0.5), candle(400, 0.5, 0.6)]
    assert gate.part1_match(cs, 100)[0] == 0                         # >= is inclusive
    assert gate.part1_match(cs, 101)[0] == 1
    assert gate.part1_match(cs, 401)[0] is None                      # no later row inside window -> unmatched
    assert gate.part1_match([], 5)[0] is None


# ------------------------------------------------------------------ G7 reader against the real EXP-032 file
def test_read_ref_tau_real_exp032_results():
    ref = gate.read_ref_tau(EXP032)
    assert set(ref) == {"<0 (in-play)", "[0,1)", "[1,3)", "[3,6)", "[6,12)", "[12,24)", "[24,48)"}
    assert ref["[24,48)"] == 0.03 and ref["[12,24)"] == 0.015 and ref["[0,1)"] == 0.005


# ------------------------------------------------------------------ store
def _store(tmp_path, sha="deadbeef"):
    return bs.Store(tmp_path, now=datetime(2026, 10, 2, tzinfo=timezone.utc), sha=sha)


def test_store_idempotent_and_revision(tmp_path):
    s = _store(tmp_path)
    assert s.put("candles", "T|60|1|2", {"a": 1}, "u") == "written"
    assert s.put("candles", "T|60|1|2", {"a": 1}, "u") == "skipped"        # same hash: nothing appended
    assert s.put("candles", "T|60|1|2", {"a": 2}, "u") == "revision"       # changed content: appended, linked
    s._lock.close()
    rows = [json.loads(l) for l in open(tmp_path / "raw_2026-10-02.jsonl")]
    assert len(rows) == 2 and "revises_content_sha256" not in rows[0]
    assert rows[1]["revises_content_sha256"] == rows[0]["content_sha256"]
    assert rows[0]["payload"] == {"a": 1}                                  # old row untouched


def test_store_reopen_skips_existing_across_runs(tmp_path):
    s = _store(tmp_path); s.put("markets_page", "k", {"x": 1}, "u"); s._lock.close()
    s2 = bs.Store(tmp_path, now=datetime(2026, 10, 3, tzinfo=timezone.utc), sha="x")
    assert s2.put("markets_page", "k", {"x": 1}, "u") == "skipped"
    assert not (tmp_path / "raw_2026-10-03.jsonl").exists()
    s2._lock.close()


def test_store_keeps_scalar_settlement_verbatim(tmp_path):
    s = _store(tmp_path)
    page = {"markets": [{"ticker": "T", "result": "scalar", "settlement_value_dollars": "0.3700"}], "cursor": ""}
    s.put("markets_page", "/historical/markets|S|", page, "u"); s._lock.close()
    assert next(iter(bs.Store(tmp_path, sha="x").rows("markets_page")))["payload"] == page


def test_store_concurrent_open_fails_fast(tmp_path):
    s = _store(tmp_path)
    with pytest.raises(BlockingIOError):
        bs.Store(tmp_path, sha="x")
    s._lock.close()


def test_client_429_halves_rate_and_failed_fetch_writes_nothing(tmp_path):
    import urllib.error
    calls = []
    def opener(url):
        calls.append(url)
        if len(calls) == 1:
            raise urllib.error.HTTPError(url, 429, "slow", {}, None)
        return 200, b'{"ok": 1}'
    c = bs.Client(opener=opener, pause=0.3, sleep=lambda s: None)
    j, _ = c.get("/x")
    assert j == {"ok": 1} and c.n429 == 1 and c.pause == 0.6
    def dead(url):
        raise urllib.error.HTTPError(url, 404, "nf", {}, None)
    with pytest.raises(bs.FetchFailed):
        bs.Client(opener=dead, sleep=lambda s: None).get("/y")

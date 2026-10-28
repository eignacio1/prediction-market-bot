"""W91.1 backward_w91: known-answer tests for start-time, tier, first-candle selection and bucket logic."""
import importlib.util
import json
import os
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, "12_EXPLORATORY", "longshot_bias"))
sys.path.insert(0, os.path.join(_root, "12_EXPLORATORY"))
_p = os.path.join(_root, "12_EXPLORATORY", "ride_cells", "backward_w91.py")
_s = importlib.util.spec_from_file_location("backward_w91", _p)
B = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B)
ET = ZoneInfo("America/New_York")


def test_mlb_start_reads_hhmm_as_et():
    got = B.mlb_start("KXMLBF5TOTAL-26AUG271415BALSTL")
    assert got == datetime(2026, 8, 27, 14, 15, tzinfo=ET).timestamp()


def test_tier_boundaries():
    start = B.mlb_start("KXMLBHIT-26AUG271415BALSTL")
    for hrs, want in ((30, "T>24h"), (24, "T>24h"), (10, "T6-24h"), (3, "T2-6h"), (1, "T0-2h")):
        assert B.tier_at("KXMLBHIT", start, None, start - hrs * 3600) == want
    assert B.tier_at("KXMLBHIT", start, None, start) is None


def test_nfl_tier_is_et_calendar_day():
    _, gd = B.ticker_hhmm_et("KXNFLTOTAL-25NOV30DALKC")
    prev_noon = datetime(2025, 11, 29, 12, 0, tzinfo=ET).timestamp()
    assert B.tier_at("KXNFLTOTAL", None, gd, prev_noon) == "D1"


def test_first_two_sided_candle_per_tier():
    ev = "KXMLBF5TOTAL-26AUG271415BALSTL"
    start = B.mlb_start(ev)
    tbl = [{"t": ev + "-5", "s": "KXMLBF5TOTAL", "e": ev, "res": "yes"}]
    cs = [[int(start - 9 * 3600), None, 0.9], [int(start - 8 * 3600), 0.90, 0.92], [int(start - 7 * 3600), 0.5, 0.6]]
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "c.jsonl")
        open(f, "w").write(json.dumps({"t": ev + "-5", "c": cs}) + "\n")
        first = B.observations(tbl, [f])
    ts, mid, b, k, hs, _ = first[(ev + "-5", "T6-24h")]
    assert ts == int(start - 8 * 3600) and abs(mid - 0.91) < 1e-9 and abs(hs - 0.01) < 1e-9

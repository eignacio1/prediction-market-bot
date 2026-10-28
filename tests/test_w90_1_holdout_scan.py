"""W90.1 hold-out scan: tier boundaries, no look-ahead into the start hour, and the time split picks side on discovery only."""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "12_EXPLORATORY"))
sys.path.insert(0, os.path.join(ROOT, "12_EXPLORATORY", "longshot_bias"))
_spec = importlib.util.spec_from_file_location("holdout_scan", os.path.join(ROOT, "12_EXPLORATORY", "ride_market_scan", "holdout_scan.py"))
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)


def candle(end, bid, ask):
    return {"end_period_ts": end, "yes_bid": {"close_dollars": str(bid)}, "yes_ask": {"close_dollars": str(ask)}}


def test_tier_boundaries():
    assert H.tier_h(0) is None
    assert H.tier_h(1.99) == "T0-2h" and H.tier_h(2) == "T2-6h"
    assert H.tier_h(5.99) == "T2-6h" and H.tier_h(6) == "T6-24h"
    assert H.tier_h(24) == "T>24h"


def test_snapshots_first_two_sided_per_tier_and_no_look_ahead():
    s = 1_000_000
    cs = [candle(s - 28 * 3600, 0.40, 0.44),      # T>24h, first
          candle(s - 27 * 3600, 0.50, 0.54),      # same tier, later: ignored
          candle(s - 10 * 3600, 0.0, 0.60),       # one-sided: skipped
          candle(s - 1 * 3600, 0.60, 0.62),       # T0-2h
          candle(s + 3600, 0.99, 1.0)]            # after start: never used
    out = H.snapshots({"candles": cs, "start_ts": s})
    assert out == {"T>24h": (0.40, 0.44), "T0-2h": (0.60, 0.62)}


def test_side_net_known_answer_yes_wins_at_ask():
    rs = [{"game": "g1", "y": 1.0, "bid": 0.28, "ask": 0.30}, {"game": "g2", "y": 1.0, "bid": 0.28, "ask": 0.30}]
    m, lo, hi = H.side_net(rs, "yes")
    assert abs(m - (1.0 - 0.30 - H.C.fee_k007(0.30))) < 1e-9

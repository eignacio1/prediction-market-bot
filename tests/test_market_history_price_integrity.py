import importlib.util
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "12_EXPLORATORY/market_history/price_integrity.py"
s = importlib.util.spec_from_file_location("pi", p); pi = importlib.util.module_from_spec(s); s.loader.exec_module(pi)


def row(t, bid, ask):
    return {"event_ticker": "E", "market_ticker": f"E-{t}", "yes_bid": bid, "yes_ask": ask, "mid": (bid + ask) / 2}


def test_known_answer():
    rows = [row(6, 0.70, 0.74), row(7, 0.48, 0.52), row(8, 0.05, 0.40), row(9, 0.0, 0.03)]
    r = pi.shares(rows)
    assert r["wide_gt_10pts"]["n"] == 1      # 0.05/0.40
    assert r["one_sided_book"]["n"] == 1     # bid 0
    assert r["strike_far_from_event_line"]["n"] == 1   # line=7 (mid .5); strike 9 is 2 away
    assert r["stale_quote_age"] == "NOT MEASURABLE from rows"

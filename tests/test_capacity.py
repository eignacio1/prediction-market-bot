"""W121.3: capacity_read (box, read-only) and capacity_ceiling (offline)."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


cr, cc = _load("capacity_read"), _load("capacity_ceiling")


def _order(ts, tk, side, arm, bid_sz, ask_sz, h=3.0, entry=0.5, **kw):
    own = bid_sz if side == "yes" else ask_sz
    return {"event": "arm_order", "ok": True, "ts": ts, "ticker": tk, "side": side, "arm": arm, "sport": "NBA",
            "market_type": "SPREAD", "band": "T1", "stake_usd": 5.0, "entry_price": entry, "hours_to_start": h,
            "book_at_submit": {"yes_bid_size": bid_sz, "yes_ask_size": ask_sz, "own_touch_size": own, "spread": 0.02}, **kw}


def test_cross_is_the_opposite_touch():
    assert cr.order_sizes(_order("2026-11-10T00:00:00Z", "A", "yes", "RIDE", 100, 40))["cross"] == 40
    assert cr.order_sizes(_order("2026-11-10T00:00:00Z", "A", "no", "RIDE", 100, 40))["cross"] == 100
    assert cr.order_sizes(_order("2026-11-10T00:00:00Z", "A", "no", "RIDE", 100, 40))["own"] == 40


def test_orders_table_epoch_and_opportunities():
    rows = [_order("2026-11-10T00:00:00Z", "A", "yes", "RIDE", 100, 40),
            _order("2026-11-10T01:00:00Z", "A", "yes", "RIDE", 100, 60),   # same market-day-side: one opportunity
            _order("2026-11-11T01:00:00Z", "B", "yes", "RIDE", 100, 80),
            _order("2026-11-01T01:00:00Z", "C", "yes", "RIDE", 1, 1),      # pre-epoch: dropped
            {"event": "arm_skip", "reason": "demo_book_day_cap", "ts": "2026-11-11T02:00:00Z", "ticker": "D", "arm": "RIDE",
             "sport": "NBA", "market_type": "SPREAD", "band": "T1", "side": "yes"},
            {"event": "arm_skip", "reason": "no_bet", "ts": "2026-11-11T02:00:00Z", "ticker": "E", "arm": "RIDE",
             "sport": "NBA", "market_type": "SPREAD", "band": "T1"}]
    t = cr.orders_table(rows)
    c = t["cells"][0]
    assert c["n_orders"] == 3 and c["cross_touch_contracts"]["median"] == 60
    assert c["opportunities"] == 3 and c["days_sport_logged"] == 2 and c["opportunities_per_day"] == 1.5
    assert c["by_hours_to_start"]["2-6h"]["cross"]["n"] == 3


def test_ladder_depth_within_ticks():
    book = {"yes": [[50, 10], [49, 5]], "no": [[48, 7], [47, 3], [45, 9], [40, 100]]}
    d = cr.ladder_depth(book, "yes")  # buying YES lifts the ask = NO bids, best 48
    assert d == {"within_0": 7, "within_1": 10, "within_2": 10, "within_3": 19}
    assert cr.ladder_depth({"yes": [], "no": []}, "yes") is None


def test_ceiling_math_and_caps():
    cap = {"as_of_utc": "x", "orders": {"cells": [
        {"cell": "NBA|S|T1|FADE", "sport": "NBA", "market_type": "S", "band": "T1", "arm": "FADE", "n_orders": 50,
         "cross_touch_contracts": {"n": 50, "p25": 20, "median": 100, "p75": 200}, "entry_price": {"median": 0.5},
         "opportunities_per_day": 10.0},
        {"cell": "NBA|S|T1|MODEL_FADE", "sport": "NBA", "market_type": "S", "band": "T1", "arm": "MODEL_FADE", "n_orders": 9,
         "cross_touch_contracts": {"n": 9, "p25": 1, "median": 2, "p75": 3}, "entry_price": {"median": 0.5},
         "opportunities_per_day": 1.0}]}}
    r1k = cc.ceiling_rows(cap, 1000)[0]   # wants $10 = 20 contracts, depth 100 -> 20; 10 opps/day
    assert r1k["contracts_per_day"] == 200 and r1k["usd_per_day"] == round(200 * 0.166, 2)
    assert r1k["interval_spans_zero"] is True and r1k["usd_per_day_low"] < 0
    r100k = cc.ceiling_rows(cap, 100000)[0]  # wants 2000 contracts; depth 100; event cap $25 = 50 -> 50
    assert r100k["contracts_per_day"] == 500
    assert cc.ceiling_rows(cap, 1000)[1]["usd_per_day"] is None  # no net estimate for MODEL_FADE
    out = cc.build(cap)
    assert set(out["bankrolls"]) == {"1000", "10000", "100000"}
    assert out["bankrolls"]["1000"]["top10"][0]["cell"] == "NBA|S|T1|FADE"


def test_task_is_allowlisted():
    bt = _load("box_tasks")
    assert bt.TASKS["capacity_read"].endswith("scripts/capacity_read.py")

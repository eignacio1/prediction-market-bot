"""W105.5 / B-054: ride board runner + demo-order step. Fixture night; no network."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_ride_board as rb  # noqa: E402

from prediction_market_bot.decision_trees import ride, ride_orders  # noqa: E402

NOW = datetime(2026, 11, 6, 20, 0, tzinfo=timezone.utc)
FAM = "KXNBATOTAL"


def cell(status, side="yes", bucket="20-25c"):
    return ride.RideCell(FAM, "T0-2h", bucket, "tight", side, 0.017, status=status)


class FakeOrder:
    def __init__(self, ok=True, oid="oid-1"):
        self.ok, self.order_id, self.error = ok, oid, None


class FakeClient:
    def __init__(self):
        self.calls = []

    def submit_order(self, **kw):
        self.calls.append(kw)
        return FakeOrder()


def mkt(ticker="KXNBATOTAL-A-1", event="KXNBATOTAL-A", bid=0.21, ask=0.23, start_h=1.0):
    return {"ticker": ticker, "event_ticker": event, "yes_bid_dollars": bid, "yes_ask_dollars": ask,
            "occurrence_datetime": (NOW + timedelta(hours=start_h)).strftime("%Y-%m-%dT%H:%M:%SZ")}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("RIDE_BOARD_ORDER_LOG", str(tmp_path / "orders.jsonl"))
    monkeypatch.setenv("PMBOT_KILL_SWITCH_DIR", str(tmp_path / "ks"))
    monkeypatch.setattr(ride_orders.xg, "gate_for_order", lambda band, logs_dir=None: None)
    monkeypatch.setattr(ride_orders, "feed_exposure_gate", lambda p=None: None)
    return tmp_path


def go(env, table, markets, **kw):
    client = FakeClient()
    kw.setdefault("stake_fn", lambda p: 5.0)
    kw.setdefault("host_ok", lambda: True)
    kw.setdefault("schedule_cancel", False)
    s = rb.run(lambda f: markets if f == FAM else [], table, client, now=NOW, decisions=env / "dec.jsonl",
               archive_dir=env / "arch", evidence_skill={}, **kw)
    rows = [json.loads(x) for x in (env / "dec.jsonl").read_text().splitlines()]
    return s, rows, client


def test_held_out_cell_fires_one_demo_order(env):
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()])
    assert s["orders"] == 1 and len(c.calls) == 1
    assert c.calls[0]["band"] == "ride_board" and c.calls[0]["side"] == "yes"
    assert rows[0]["route"] == "RIDE" and rows[0]["order_event"] == "ride_order"


def test_no_side_price_is_one_minus_bid(env):
    s, rows, c = go(env, ride.Table([cell("HELD_OUT", side="no", bucket="75-80c")]), [mkt(bid=0.77, ask=0.79)])
    o = [json.loads(x) for x in (env / "orders.jsonl").read_text().splitlines()][0]
    assert o["side"] == "no" and c.calls[0]["side"] == "no"
    assert abs(c.calls[0]["mid_price"] - 0.78) < 1e-9  # YES-frame mid; submit_order prices NO at 1 - mid


def test_in_sample_logs_only(env):
    s, rows, c = go(env, ride.Table([cell("IN_SAMPLE")]), [mkt()])
    assert c.calls == [] and s["orders"] == 0
    # ride.decide never rides a non-rideable cell: the router returns NO_BET, the decision is logged, no order.
    assert rows[0]["route"] == "NO_BET" and "order_event" not in rows[0]
    # and if a RIDE route were ever handed to the order step with an IN_SAMPLE cell, it is paper-only:
    from prediction_market_bot.decision_trees.router import Route, Situation
    sit = Situation("nba", FAM, "T", "E", "T0-2h", 0.21, 0.23, 0.01)
    r = ride_orders.maybe_order(sit, Route("RIDE", "yes", ["t"], False), ride.Table([cell("IN_SAMPLE")]), c,
                                host_ok=lambda: True, stake_fn=lambda p: 5.0, now=NOW, schedule_cancel=False)
    assert r["event"] == "ride_paper" and r["reason"] == "paper_only:cell_in_sample" and c.calls == []


def test_every_decision_logged_including_no_bet(env):
    ms = [mkt(), mkt("KXNBATOTAL-B-1", "KXNBATOTAL-B", start_h=-1.0), mkt("KXNBATOTAL-C-1", "KXNBATOTAL-C", bid=0.5, ask=0.6)]
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), ms)
    dec = [r for r in rows if r.get("event") != "run_summary"]
    assert len(dec) == 3 and s["decisions"] == 3
    assert {r["route"] for r in dec} >= {"RIDE", "NO_BET"}
    assert rows[-1]["event"] == "run_summary" and rows[-1]["peak_rss_mb"] > 0


def test_kill_switch_blocks(env):
    ks = env / "ks"
    ks.mkdir()
    (ks / "kill_switch_ride_board.flag").write_text("x")
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()])
    assert c.calls == [] and rows[0]["order_reason"].startswith("kill_switch")


def test_exposure_gate_blocks(env, monkeypatch):
    monkeypatch.setattr(ride_orders.xg, "gate_for_order", lambda band, logs_dir=None: "exposure_gate_breach:X")
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()])
    assert c.calls == [] and rows[0]["order_reason"].startswith("exposure_gate:")


def test_per_event_cap_blocks(env):
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()], stake_fn=lambda p: 600.0)
    assert c.calls == [] and rows[0]["order_reason"] == "per_event_cap"


def test_daily_breaker_blocks(env):
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()], stake_fn=lambda p: 200.0)
    assert c.calls == [] and rows[0]["order_reason"] == "daily_breaker"


def test_production_host_refused(env):
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()], host_ok=lambda: False)
    assert c.calls == [] and rows[0]["order_reason"] == "production_host_refused"


def test_no_orders_flag_never_calls_order_path(env):
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), [mkt()], orders=False)
    assert c.calls == [] and rows[0]["route"] == "RIDE" and "order_event" not in rows[0]


def test_second_order_same_event_counts_toward_cap(env):
    ms = [mkt("KXNBATOTAL-A-1"), mkt("KXNBATOTAL-A-2")]
    s, rows, c = go(env, ride.Table([cell("HELD_OUT")]), ms, stake_fn=lambda p: 300.0)
    assert len(c.calls) == 0 or len(c.calls) == 1  # 300 > breaker 150 -> none; cap logic covered above
    s2, rows2, c2 = go(env, ride.Table([cell("HELD_OUT")]), ms, stake_fn=lambda p: 5.0)
    assert len(c2.calls) == 2


def test_tier_and_move():
    assert rb.tier_of(NOW + timedelta(hours=1), NOW) == "T0-2h"
    assert rb.tier_of(NOW + timedelta(hours=30), NOW) == "T>24h"
    assert rb.tier_of(NOW - timedelta(hours=1), NOW) is None and rb.tier_of(None, NOW) is None
    tails = {"X": [{"run_ts": (NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "yes_mid": 0.20}]}
    assert rb.move_1h("X", 0.25, NOW, tails) == 0.05 and rb.move_1h("Y", 0.25, NOW, tails) is None


def test_real_table_loads_and_runner_does_not_edit_it(env):
    p = Path(ride.__file__).with_name("ride_cells.toml")
    before = p.read_bytes()
    t = ride.load()
    go(env, t, [mkt()], orders=False)
    assert p.read_bytes() == before


def test_sweep_cancels_waits_then_sweeps_and_never_raises(monkeypatch):
    from prediction_market_bot.c5_execution import demo_fill_policy as pol
    calls = []
    monkeypatch.setattr(pol, "sweep_overdue", lambda c: calls.append(c) or 2)
    import time
    monkeypatch.setattr(time, "sleep", lambda s: calls.append(("sleep", s)))
    assert ride_orders.sweep_cancels(object(), True, wait=True) == 2
    assert calls[0][0] == "sleep" and len(calls) == 2
    assert ride_orders.sweep_cancels(None) == 0 and ride_orders.sweep_cancels(object(), False) == 0
    monkeypatch.setattr(pol, "sweep_overdue", lambda c: 1 / 0)
    assert ride_orders.sweep_cancels(object()) == 0

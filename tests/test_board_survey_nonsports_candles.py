import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import board_survey_nonsports_candles as bc

LIVE = {"end_period_ts": 1200, "open_interest_fp": "103.00", "volume_fp": "0.00",
        "price": {"previous_dollars": "0.0200"},
        "yes_ask": {"open_dollars": "0.0200", "high_dollars": "0.0300", "low_dollars": "0.0200", "close_dollars": "0.0300"},
        "yes_bid": {"open_dollars": "0.0100", "high_dollars": "0.0100", "low_dollars": "0.0100", "close_dollars": "0.0100"}}
HIST = {"end_period_ts": 1200, "open_interest": "103.00", "volume": "0.00",
        "price": {"close": None, "previous": "0.0200"},
        "yes_ask": {"open": "0.0200", "high": "0.0300", "low": "0.0200", "close": "0.0300"},
        "yes_bid": {"open": "0.0100", "high": "0.0100", "low": "0.0100", "close": "0.0100"}}


def cd(end, bid, ask):
    return {"end_ts": end, "bid_low": bid, "bid_high": bid, "bid_close": bid,
            "ask_low": ask, "ask_high": ask, "ask_close": ask}


def test_schemas_identical():
    assert bc.parse_candle(LIVE) == bc.parse_candle(HIST)


def test_null_price_with_previous():
    p = bc.parse_candle(HIST)
    assert p["price_close"] is None and p["price_prev"] == 0.02


def test_sparse_resolves_to_prior_close():
    cs = [cd(60, 0.10, 0.12), cd(180, 0.20, 0.22)]
    kind, c = bc.match(cs, 125.0)  # wants 180? ceil(125/60)*60=180 -> exact
    assert kind == "exact" and c["end_ts"] == 180
    kind, c = bc.match(cs, 100.0)  # wants 120, absent -> prior = 60
    assert kind == "prior" and c["end_ts"] == 60
    assert bc.match(cs, 10.0)[0] == "exact"
    assert bc.match([cd(300, .1, .2)], 10.0)[0] == "unmatched"


def row(ts, b, a):
    return {"ticker": "T", "round": 0, "ts": ts, "yes_bid": b, "yes_ask": a}


def test_compare_prior_rule_and_tolerance():
    cs = [cd(60, 0.10, 0.12)]
    r = bc.compare(row("1970-01-01T00:01:40+00:00", "0.11", "0.12"), cs)
    assert r["kind"] == "prior" and r["pass"]
    r = bc.compare(row("1970-01-01T00:01:40+00:00", "0.13", "0.12"), cs)
    assert not r["pass"] and abs(r["bid_miss"] - 0.03) < 1e-9


def test_gate_pass_and_fail():
    ok = [{"pass": True, "bid_miss": 0.0, "ask_miss": 0.0, "kind": "exact"}] * 20
    assert bc.gate(ok)["gate"] == "PASS"
    bad = ok[:-1] + [{"pass": False, "bid_miss": 0.05, "ask_miss": 0.0, "kind": "exact"}]
    assert bc.gate(bad)["gate"] == "FAIL"


def test_scalar_settlement():
    assert bc.parse_settlement({"result": "yes"}) == 1.0
    assert bc.parse_settlement({"result": "no"}) == 0.0
    assert bc.parse_settlement({"settlement_value_dollars": "1.0000"}) == 1.0
    assert bc.parse_settlement({"result": ""}) is None

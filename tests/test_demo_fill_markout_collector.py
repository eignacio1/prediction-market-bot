"""W81.1-B: the ADR-0072 (c) markout collector. Pure-function tests; no network."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import demo_fill_markout_collector as col  # noqa: E402

T0 = datetime(2026, 10, 21, 1, 0, tzinfo=timezone.utc)


def candle(t, bid, ask):
    return {"end_period_ts": int(t.timestamp()), "yes_bid": {"close_dollars": str(bid)}, "yes_ask": {"close_dollars": str(ask)}}


def test_parse_ts_accepts_five_digit_fraction_and_z():
    assert col.parse_ts("2026-10-20T11:25:03.12345Z") == datetime(2026, 10, 20, 11, 25, 3, 123450, tzinfo=timezone.utc)
    assert col.parse_ts("") is None


def test_held_side_mid_yes_and_no_and_one_sided_is_none():
    c = col.Candles([candle(T0, 0.40, 0.50)])
    assert abs(col.held_side_mid(c, T0.timestamp(), "YES") - 0.45) < 1e-9
    assert abs(col.held_side_mid(c, T0.timestamp(), "NO") - 0.55) < 1e-9
    assert col.held_side_mid(col.Candles([candle(T0, 0.0, 0.50)]), T0.timestamp(), "YES") is None  # no bid: not a quote
    assert col.held_side_mid(c, T0.timestamp() + 3600, "YES") is None  # stale


def test_markouts_for_is_mid_minus_fill_price():
    cs = col.Candles([candle(T0 + timedelta(minutes=m), 0.50, 0.60) for m in (1, 5, 30)])
    m = col.markouts_for(cs, T0, "YES", 0.52)
    assert m == {"h1": 0.03, "h5": 0.03, "h30": 0.03}


def test_group_fills_vwap_and_first_time():
    fs = [{"order_id": "a", "created_time": "2026-10-21T01:00:05Z", "side": "yes", "yes_price_dollars": "0.40", "count_fp": "1"},
          {"order_id": "a", "created_time": "2026-10-21T01:00:01Z", "side": "yes", "yes_price_dollars": "0.60", "count_fp": "3"}]
    g = col.group_fills(fs)["a"]
    assert g["side"] == "YES" and abs(g["price"] - 0.55) < 1e-9 and g["fill_ts"] == datetime(2026, 10, 21, 1, 0, 1, tzinfo=timezone.utc)


def test_collect_skips_pre_epoch_immature_done_and_failed_fetch():
    now = T0 + timedelta(hours=2)
    epoch = T0
    orders = {k: {"ticker": "KXNFLGAME-26OCT21AAABBB-AAA", "arm": "treatment", "order_ts": None} for k in "abcde"}
    fl = lambda mins: {"fill_ts": T0 + timedelta(minutes=mins), "side": "YES", "price": 0.5}  # noqa: E731
    fills = {"a": fl(-10), "b": fl(5), "c": fl(100), "d": fl(10), "e": fl(20)}  # a pre-epoch; c not matured
    cs = col.Candles([candle(T0 + timedelta(minutes=m), 0.5, 0.6) for m in range(0, 60)])
    rows = col.collect(orders, fills, epoch, now, {"d"}, lambda tk, a, b: cs, 50)
    assert [r["order_id"] for r in rows] == ["b", "e"] and rows[0]["h30"] == 0.05 and rows[0]["sport"] == "NFL"
    assert col.collect(orders, fills, epoch, now, set(), lambda *a: None, 50) == []  # transient failure: retry later
    assert len(col.collect(orders, fills, epoch, now, set(), lambda *a: cs, 1)) == 1  # cap respected

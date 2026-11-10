from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.quant import trade_path as tp

T0 = datetime(2026, 11, 5, 22, 0, tzinfo=timezone.utc)


def _planted(step_at_s=180, lo=0.50, hi=0.58, taker_hi="yes"):
    """One print every 10 s from -10 min to +30 min; price steps lo->hi at T0+step_at_s."""
    out = []
    for i in range(-60, 181):
        t = T0 + timedelta(seconds=10 * i)
        up = (t - T0).total_seconds() >= step_at_s
        out.append(tp.Trade(t, hi if up else lo, 1.0, taker_hi if up else "no"))
    return out


def test_known_step_recovered_with_its_lag():
    tr = _planted(step_at_s=180)
    p = tp.signed_path(tr, T0, +1, [-5, 1, 2, 3, 5, 10])
    assert p["ref"] == 0.50
    assert p["path"][2] == pytest.approx(0.0) and p["path"][3] == pytest.approx(0.08) and p["path"][10] == pytest.approx(0.08)
    final = tp.tail_level(tr, T0, 20, 30) - p["ref"]
    assert final == pytest.approx(0.08)
    assert tp.lag_to_fraction(tr, T0, +1, 0.5, final) == pytest.approx(3.0)
    assert tp.lag_to_fraction(tr, T0, +1, 1.0, final) == pytest.approx(3.0)


def test_negative_news_flips_sign_and_no_move_gives_none():
    tr = _planted(lo=0.60, hi=0.52)
    p = tp.signed_path(tr, T0, -1, [5])
    assert p["path"][5] == pytest.approx(0.08)                   # price fell, news was bad: signed move positive
    flat = [tp.Trade(T0 + timedelta(seconds=10 * i), 0.5, 1.0, "yes") for i in range(-60, 181)]
    assert tp.lag_to_fraction(flat, T0, +1, 0.5, 0.0) is None


def test_entry_uses_the_print_price_fee_and_side():
    tr = _planted(step_at_s=60, lo=0.50, hi=0.58, taker_hi="yes")
    e = tp.entry_net(tr, T0, +1, 2, 0.58, "KXNBAGAME-X")
    assert e["cost"] == pytest.approx(0.58) and e["gross"] == pytest.approx(0.0)       # already adjusted at minute 2
    assert e["net"] == pytest.approx(-e["fee"]) and e["fee"] > 0
    early = tp.entry_net(tr, T0, +1, 0, 0.58, "KXNBAGAME-X")                           # first YES-aggressor print is the stepped one
    assert early["cost"] == pytest.approx(0.58)
    assert tp.entry_net(tr, T0, -1, 2, 0.58, "KXNBAGAME-X") is None                    # no NO-aggressor print after the step


def test_parse_drops_block_trades_and_sorts():
    rows = [{"created_time": "2026-11-05T22:00:01.5Z", "yes_price_dollars": "0.4", "count_fp": "3", "taker_side": "no"},
            {"created_time": "2026-11-05T22:00:00.123456789Z", "yes_price_dollars": "0.5", "is_block_trade": True},
            {"created_time": "2026-11-05T21:59:59Z", "yes_price_dollars": "0.45", "taker_side": "yes"}]
    t = tp.parse_trades(rows)
    assert [x.yes for x in t] == [0.45, 0.4]


def test_fetch_paginates_until_cursor_empty():
    pages = [{"trades": [{"a": 1}], "cursor": "c1"}, {"trades": [{"a": 2}], "cursor": ""}]
    calls = []
    def g(path, params):
        calls.append(dict(params)); return pages[len(calls) - 1]
    assert tp.fetch_trades(g, "X", T0, T0 + timedelta(hours=1), pause=0) == [{"a": 1}, {"a": 2}]
    assert "cursor" not in calls[0] and calls[1]["cursor"] == "c1"

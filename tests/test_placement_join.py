"""W116.2 A2 known answers: the per-order join (one fills pull, per-ticker market cache, markouts, exact fees, epoch rule)."""
from datetime import datetime, timedelta, timezone

from prediction_market_bot.c5_execution.placement import join as pj
from prediction_market_bot.quant import money

UTC = timezone.utc
NOW = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
T0 = datetime(2026, 11, 14, 0, 0, tzinfo=UTC)  # post-epoch


class _C:
    """Candles stub: held-side mid = 0.50 + 0.01 * minutes after T0 (YES side)."""
    def quote(self, t, side):
        mid = 0.50 + 0.01 * (t - T0.timestamp()) / 60.0
        if side == "NO":
            mid = 1 - mid
        return {"bid": mid - 0.01, "ask": mid + 0.01, "two_sided": True}


def _row(oid, side="yes", ts=T0, arm="RIDE", tk="KXNBAGAME-26NOV14AB-A", price=0.5):
    return {"event": "arm_order", "ok": True, "order_id": oid, "ts": ts.strftime("%Y-%m-%dT%H:%M:%S.12345Z"), "arm": arm,
            "sport": "nba", "side": side, "ticker": tk, "entry_price": price, "placement": "rest_touch",
            "book_at_submit": {"yes_bid": 0.49, "yes_ask": 0.51}, "hours_to_start": 3.0}


def _fill(oid, n, yes_px, taker=False, at=T0):
    return {"order_id": oid, "count_fp": str(n), "yes_price_dollars": str(yes_px), "no_price_dollars": str(round(1 - yes_px, 4)),
            "is_taker": taker, "created_time": at.strftime("%Y-%m-%dT%H:%M:%S.12345Z")}


MKT = {"KXNBAGAME-26NOV14AB-A": {"result": "yes", "status": "finalized", "close_time": "2026-11-14T03:00:00Z"},
       "KXNBAGAME-26NOV14CD-C": {"result": "", "status": "open"}}


def test_join_counts_and_prices_known_answer():
    calls = []

    def market_of(tk):
        calls.append(tk)
        return MKT.get(tk)

    rows = [_row("a"), _row("b"), _row("c", side="no", price=0.48), _row("d", tk="KXNBAGAME-26NOV14CD-C"),
            _row("e", tk="KXNBAGAME-26NOV14XX-X"), _row("pre", side="no", ts=datetime(2026, 11, 1, tzinfo=UTC)),
            {"event": "arm_skip", "order_id": "z"}]
    fills = [_fill("a", 3, 0.50), _fill("a", 1, 0.54, taker=True), _fill("c", 2, 0.52), _fill("other", 9, 0.1)]
    recs = {r["order_id"]: r for r in pj.records(rows, fills, market_of, lambda tk: _C(), NOW)}
    assert set(recs) == {"a", "b", "c", "d", "e"}  # pre-epoch NO dropped, skip row ignored
    a = recs["a"]
    assert a["filled"] and a["contracts"] == 4.0 and a["fill_price"] == 0.51  # (3*.50 + 1*.54)/4
    assert a["fee_per_contract"] == round(money.fee("KXNBAGAME", 0.54, 1, "taker") / 4, 6)
    assert a["maker_share"] == 0.75 and a["won"] is True and a["outcome"] == "resolved"
    assert a["markout"]["h1"] == 0.0 and a["markout"]["h5"] == 0.04 and a["markout"]["settle"] == 0.49
    assert recs["b"]["filled"] is False and recs["b"]["won"] is True  # counterfactual for an unfilled order
    c = recs["c"]
    assert c["fill_price"] == 0.48 and c["won"] is False  # NO priced from the NO field, scored on NO
    assert c["markout"]["h1"] == round((1 - 0.51) - 0.48, 4)
    assert recs["d"]["outcome"] == "pending" and recs["e"]["outcome"] == "lookup_failed"
    assert calls.count("KXNBAGAME-26NOV14AB-A") == 3  # the caller caches; the join asks once per order
    h = pj.join_health(list(recs.values()))
    assert h == {"orders": 5, "lookups_failed": 1, "resolved": 3, "pending": 1, "void": 0, "fill_status_unknown": 0}


def test_failed_fills_pull_marks_every_order_unknown_and_recent_orders_stay_open():
    rows = [_row("a"), _row("new", ts=NOW - timedelta(seconds=30))]
    recs = pj.records(rows, None, lambda tk: MKT.get(tk), None, NOW)
    assert all(r["filled"] is None and r["outcome"] == "lookup_failed" for r in recs)
    recs = {r["order_id"]: r for r in pj.records(rows, [], lambda tk: MKT.get(tk), None, NOW)}
    assert recs["a"]["filled"] is False and recs["new"]["filled"] is None  # inside the 120 s rest window


def test_per_arm_e1_e2_e3_known_answer():
    rows = [_row("f1"), _row("f2", tk="KXNBAGAME-26NOV14CD-C"), _row("u1"), _row("u2", side="no")]
    mk = dict(MKT, **{"KXNBAGAME-26NOV14CD-C": {"result": "no", "status": "finalized"}})
    recs = pj.records(rows, [_fill("f1", 1, 0.40), _fill("f2", 1, 0.60)], lambda tk: mk.get(tk), None, NOW)
    a = pj.per_arm(recs)["RIDE|post_epoch_all_sides"]
    assert a["E1_orders"] == 4 and a["E1_fills"] == 2 and a["fill_rate"] == 0.5
    assert a["E2_per_filled_contract_before_fees"] == round(((1 - 0.40) + (0 - 0.60)) / 2, 4)  # 0.0
    assert a["E3_win_rate_fills"] == 0.5 and a["E3_win_rate_nonfills_counterfactual"] == 0.5
    assert len(pj.model_records(recs)) == 4

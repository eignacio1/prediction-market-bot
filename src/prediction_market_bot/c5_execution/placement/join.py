"""W116.2 / B-095 Part A2: the per-order settlement join for router-arm demo orders.

PURE: no I/O. The caller supplies three read results and this module joins them to one record per placed order:

  fills          the account's fill rows from ONE paginated GET /portfolio/fills (not one GET per order - the old per-order
                 GET /portfolio/orders/{id} failed on 244 of 432 orders, W115.2, because the demo API stops returning old
                 cancelled orders). An order with no fill row was not filled, once its rest window has passed.
  market_of      ticker -> {"result": "yes"|"no"|"", "status": ..., "close_time": ...} or None when the GET failed; the caller
                 caches it per ticker, so a board of 400 orders on 60 markets costs 60 GETs.
  candles_of     ticker -> Candles (1-minute held-side quotes) or None; for the markouts.

Every record says how its outcome was learned (`outcome`): "resolved", "pending" (market not settled yet), "void" (settled
with no result: nothing to learn), or "lookup_failed" (the market GET failed). Only "lookup_failed" counts against the join.

Applies when: rows are the arm-order log's ``arm_order`` rows with ok=True and an order_id, placed with the ADR-0072
rest-at-touch rule (cancelled after REST_WINDOW). The GG-1771 epoch rule is applied here and only here: pre-epoch NO-side
orders are dropped (mirror-priced); the two epochs are labelled and never pooled by any caller of ``records``.

Price and side: the side scored is the INTENDED side logged at submit (GG-1793), and the fill price is read from that side's
price field on the fill row, so a NO bought as "sell yes" is priced as NO. Fees are exact: quant.money.fee per fill row with
the fill's own maker / taker flag, summed and divided by the filled count.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from prediction_market_bot.quant import money
from prediction_market_bot.timeparse import parse_ts

EPOCH = datetime(2026, 11, 6, 1, 3, 42, tzinfo=timezone.utc)  # GG-1771 / GG-1784
PRE, POST = "pre_epoch_yes_only", "post_epoch_all_sides"
REST_WINDOW = timedelta(seconds=120)  # 60 s cancel + slack: after this an order with no fill row is unfilled
HORIZONS_MIN = (1, 5, 30)


def _f(x: Any) -> Optional[float]:
    try:
        return None if x is None or x == "" else float(x)
    except (TypeError, ValueError):
        return None


def epoch_of(ts: Optional[datetime], epoch: datetime = EPOCH) -> Optional[str]:
    return None if ts is None else (POST if ts >= epoch else PRE)


def fill_price_on(f: dict, side: str) -> Optional[float]:
    """Per-contract price of ``side`` on one fill row, dollars. Reads <side>_price_dollars, then cents, then the complement."""
    other = "no" if side == "yes" else "yes"
    p = _f(f.get(f"{side}_price_dollars"))
    if p is None and _f(f.get(f"{side}_price")) is not None:
        p = _f(f.get(f"{side}_price")) / 100.0
    if p is None:
        q = _f(f.get(f"{other}_price_dollars"))
        if q is None and _f(f.get(f"{other}_price")) is not None:
            q = _f(f.get(f"{other}_price")) / 100.0
        p = None if q is None else 1.0 - q
    return p


def fill_count(f: dict) -> float:
    return _f(f.get("count_fp")) or _f(f.get("count")) or 0.0


def fee_of_fill(f: dict, series: str, price: float, n: float) -> float:
    """The fill's own fee when the API reports one, else the exact schedule fee for its maker / taker side."""
    for k in ("fee_cost_dollars", "fee_cost"):
        v = _f(f.get(k))
        if v is not None:
            return v
    side = "taker" if f.get("is_taker") else "maker"
    try:
        return money.fee(series, min(max(price, 0.01), 0.99), max(1, int(round(n))), side)
    except Exception:  # noqa: BLE001 - an unknown series is reported as fee None by the caller
        return float("nan")


def group_by_order(fills: Iterable[dict]) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for f in fills or []:
        oid = f.get("order_id")
        if oid:
            out.setdefault(str(oid), []).append(f)
    return out


def held_mid(candles: Any, t: float, side: str) -> Optional[float]:
    if candles is None:
        return None
    q = candles.quote(t, side.upper())
    if not q or not q.get("two_sided"):
        return None
    return (q["bid"] + q["ask"]) / 2.0


def spread_at_submit(r: dict) -> Optional[float]:
    b = r.get("book_at_submit") or {}
    yb, ya = _f(b.get("yes_bid")), _f(b.get("yes_ask"))
    return None if yb is None or ya is None or ya < yb else round(ya - yb, 4)


def records(rows: Iterable[dict], fills: Optional[Iterable[dict]], market_of: Callable[[str], Optional[dict]],
            candles_of: Optional[Callable[[str], Any]] = None, now: Optional[datetime] = None,
            epoch: datetime = EPOCH) -> List[dict]:
    """One record per placed arm order (see module doc). ``fills`` None means the fills pull failed: fill status is then
    unknown and every record is outcome "lookup_failed" with filled None."""
    now = now or datetime.now(timezone.utc)
    by_oid = group_by_order(fills) if fills is not None else None
    out: List[dict] = []
    for r in rows:
        if r.get("event") != "arm_order" or not r.get("ok") or not r.get("order_id"):
            continue
        ts = parse_ts(r.get("ts"))
        ep = epoch_of(ts, epoch)
        side = r.get("side")
        if ep is None or side not in ("yes", "no") or (ep == PRE and side != "yes"):
            continue
        tk = str(r.get("ticker") or "")
        series = tk.split("-")[0]
        rec: Dict[str, Any] = {
            "order_id": r["order_id"], "arm": r.get("arm"), "sport": r.get("sport"), "leaf_id": r.get("leaf_id"),
            "epoch": ep, "ts": ts.isoformat(), "ticker": tk, "series": series, "side": side,
            "placement": r.get("placement") or "rest_touch", "price": _f(r.get("entry_price")),
            "spread": spread_at_submit(r), "depth": None, "hours": _f(r.get("hours_to_start")),
            "filled": None, "contracts": 0.0, "fill_price": None, "fee_per_contract": None, "maker_share": None,
            "won": None, "outcome": "lookup_failed", "markout": {}}
        if by_oid is None:
            out.append(rec)
            continue
        fs = by_oid.get(str(r["order_id"]), [])
        if fs:
            num = den = fee = mk = 0.0
            first = None
            for f in fs:
                p, n = fill_price_on(f, side), fill_count(f)
                if p is None or n <= 0:
                    continue
                num, den = num + p * n, den + n
                fee += fee_of_fill(f, series, p, n)
                mk += 0.0 if f.get("is_taker") else n
                t = parse_ts(f.get("created_time"))
                first = t if first is None or (t is not None and t < first) else first
            if den > 0:
                rec.update(filled=True, contracts=den, fill_price=round(num / den, 4),
                           fee_per_contract=None if fee != fee else round(fee / den, 6), maker_share=round(mk / den, 4),
                           fill_ts=first.isoformat() if first else None)
                rec["price"] = rec["fill_price"]  # the price actually paid scores the filled order
        if rec["filled"] is None:
            rec["filled"] = False if ts + REST_WINDOW <= now else None
        m = market_of(tk) if tk else None
        if m is None:
            out.append(rec)
            continue
        res = str(m.get("result") or "").lower()
        if res in ("yes", "no"):
            rec.update(won=(res == side), outcome="resolved")
        elif str(m.get("status") or "").lower() in ("finalized", "settled"):
            rec["outcome"] = "void"
        else:
            rec["outcome"] = "pending"
        if rec["filled"] and rec.get("fill_ts") and candles_of is not None:
            c = candles_of(tk)
            ft = parse_ts(rec["fill_ts"]).timestamp()
            for h in HORIZONS_MIN:
                mid = held_mid(c, ft + h * 60, side)
                rec["markout"][f"h{h}"] = None if mid is None else round(mid - rec["fill_price"], 4)
            close = parse_ts(m.get("close_time"))
            if close is not None:
                mid = held_mid(c, close.timestamp() - 60, side)
                rec["markout"]["close"] = None if mid is None else round(mid - rec["fill_price"], 4)
            if rec["won"] is not None:
                rec["markout"]["settle"] = round((1.0 if rec["won"] else 0.0) - rec["fill_price"], 4)
        out.append(rec)
    return out


def join_health(recs: List[dict]) -> dict:
    """Outcome lookups: how many records the join could not resolve because a read failed (the W115.2 244/432 measure)."""
    from collections import Counter
    c = Counter(r["outcome"] for r in recs)
    return {"orders": len(recs), "lookups_failed": c.get("lookup_failed", 0), "resolved": c.get("resolved", 0),
            "pending": c.get("pending", 0), "void": c.get("void", 0),
            "fill_status_unknown": sum(1 for r in recs if r["filled"] is None)}


def _mean(v: List[float]) -> Optional[float]:
    return round(sum(v) / len(v), 4) if v else None


def per_arm(recs: List[dict]) -> Dict[str, dict]:
    """E1 / E2 / E3 and mean markouts per (arm, epoch). E2 is per filled contract, before and after exact fees."""
    acc: Dict[str, dict] = {}
    for r in recs:
        k = f"{r['arm']}|{r['epoch']}"
        c = acc.setdefault(k, {"arm": r["arm"], "epoch": r["epoch"], "orders": 0, "fills": 0, "gross": [], "net": [],
                               "won_f": [], "won_u": [], "mk": {}})
        c["orders"] += 1
        if r["filled"]:
            c["fills"] += 1
            for h, v in r["markout"].items():
                if v is not None:
                    c["mk"].setdefault(h, []).append(v)
        if r["won"] is None or r["filled"] is None:
            continue
        w = 1.0 if r["won"] else 0.0
        if r["filled"]:
            c["won_f"].append(w)
            g = w - r["fill_price"]
            c["gross"].append(g)
            if r["fee_per_contract"] is not None:
                c["net"].append(g - r["fee_per_contract"])
        else:
            c["won_u"].append(w)
    out = {}
    for k, c in sorted(acc.items()):
        out[k] = {"arm": c["arm"], "epoch": c["epoch"], "E1_orders": c["orders"], "E1_fills": c["fills"],
                  "fill_rate": round(c["fills"] / c["orders"], 4) if c["orders"] else None,
                  "E2_per_filled_contract_before_fees": _mean(c["gross"]),
                  "E2_per_filled_contract_after_fees": _mean(c["net"]), "n_settled_fills": len(c["gross"]),
                  "E3_win_rate_fills": _mean(c["won_f"]), "E3_win_rate_nonfills_counterfactual": _mean(c["won_u"]),
                  "n_nonfills_resolved": len(c["won_u"]),
                  "markout_mean": {h: _mean(v) for h, v in sorted(c["mk"].items())},
                  "markout_n": {h: len(v) for h, v in sorted(c["mk"].items())}}
    return out


def model_records(recs: List[dict]) -> List[dict]:
    """Records in the shape placement.model expects (one epoch at a time - the caller filters)."""
    return [{"arm": r["arm"], "sport": r["sport"], "leaf_id": r["leaf_id"], "placement": r["placement"], "price": r["price"],
             "filled": bool(r["filled"]), "won": r["won"], "spread": r["spread"], "depth": r["depth"], "hours": r["hours"],
             "series": r["series"]}
            for r in recs if r["filled"] is not None and r["price"] is not None]

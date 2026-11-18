#!/usr/bin/env python3
"""READ-ONLY (W114.2 / B-090): summarise the box's logs/arm_orders/orders.jsonl.

Per arm and sport: orders (placed), would-orders (dry run), skips and skip reasons. Per arm: fills (E1), P&L per filled contract
before fees (E2), win rate on fills vs the counterfactual win rate of unfilled orders (E3). Everything is split by the GG-1771
data epoch and the two halves are never mixed: `pre_epoch_yes_only` (NO-side orders before 2026-11-06T01:03:42Z were
mirror-priced and are dropped from fills / P&L) and `post_epoch_all_sides`.

W116.2: the default fill / outcome source is the per-order JOIN (`join`: one paginated fills pull, market results cached per
ticker, markouts at 1 / 5 / 30 min and close, exact fees; placement/join.py). The old per-order path below runs only with
--legacy-lookup. Legacy: fill status comes from read-only GETs against the Kalshi DEMO API (same lookup as demo_fill_forward_report.lookup_fill, cache
held in memory only). If the host is not demo or there is no signing key, the order counts are still printed and the fill
fields say why they are missing. Writes nothing: stdout only. Python 3.9-safe (the box): timestamps parse with the tolerant
parse_ts, because 3.9 fromisoformat rejects a trailing "Z".
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
LOG = REPO / "logs" / "arm_orders" / "orders.jsonl"
EPOCH = datetime(2026, 11, 6, 1, 3, 42, tzinfo=timezone.utc)  # GG-1771 / GG-1784
PRE, POST = "pre_epoch_yes_only", "post_epoch_all_sides"


from prediction_market_bot.timeparse import parse_ts  # noqa: E402  GG-1934: one tolerant parser


def load_rows(path: Path) -> List[dict]:
    out: List[dict] = []
    try:
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                out.append(r)
    except OSError:
        pass
    return out


def epoch_of(r: dict, epoch: datetime = EPOCH) -> Optional[str]:
    ts = parse_ts(r.get("ts"))
    if ts is None:
        return None
    return POST if ts >= epoch else PRE


def counts(rows: List[dict], epoch: datetime = EPOCH) -> dict:
    """Orders / would / skips per (epoch, arm, sport) and skip reasons per (epoch, arm)."""
    ev = {"arm_order": "orders", "arm_would_order": "would", "arm_skip": "skips"}
    per: Dict[str, Counter] = {}
    reasons: Dict[str, Counter] = {}
    bad_ts = 0
    for r in rows:
        k = ev.get(r.get("event"))
        if k is None:
            continue
        ep = epoch_of(r, epoch)
        if ep is None:
            bad_ts += 1
            continue
        if k == "orders" and not r.get("ok"):
            k = "refused"  # submit returned not-ok: counted apart from placed orders
        key = f"{ep}|{r.get('arm')}|{r.get('sport')}"
        per.setdefault(key, Counter())[k] += 1
        if k == "skips":
            reasons.setdefault(f"{ep}|{r.get('arm')}", Counter())[str(r.get("reason"))] += 1
    return {"per_epoch_arm_sport": {k: dict(v) for k, v in sorted(per.items())},
            "skip_reasons_per_epoch_arm": {k: dict(v.most_common()) for k, v in sorted(reasons.items())},
            "rows_with_unparseable_ts": bad_ts}


def _mean(v: list) -> Optional[float]:
    return (sum(v) / len(v)) if v else None


def fills_report(rows: List[dict], fills_for: Optional[Callable[[str, str], dict]], epoch: datetime = EPOCH) -> dict:
    """E1 (fills), E2 (settle minus price per filled contract, before fees), E3 (win rate fills vs unfilled counterfactual), per arm and epoch.
    Pre-epoch NO-side orders are dropped (mirror-priced)."""
    acc: Dict[str, dict] = {}
    for r in rows:
        if r.get("event") != "arm_order" or not r.get("ok") or not r.get("order_id"):
            continue
        ep = epoch_of(r, epoch)
        if ep is None or (ep == PRE and r.get("side") != "yes"):
            continue
        c = acc.setdefault(f"{r.get('arm')}|{ep}", {"arm": r.get("arm"), "epoch": ep, "orders": 0, "fills": 0, "lookups_failed": 0,
                                                 "pnl": [], "won": [], "nf_won": []})
        c["orders"] += 1
        f = fills_for(r["order_id"], r.get("ticker")) if fills_for else None
        if f is None:
            continue
        if f.get("status") == "unretrievable":
            c["lookups_failed"] += 1
            continue
        if (f.get("fills") or 0) > 0:
            c["fills"] += 1
            if f.get("settled") and f.get("won") is not None:
                c["won"].append(1.0 if f["won"] else 0.0)
                price = f.get("price") if f.get("price") is not None else r.get("entry_price")
                if price is not None:
                    c["pnl"].append((1.0 - float(price)) if f["won"] else -float(price))
        elif f.get("nf_won") is not None:
            c["nf_won"].append(1.0 if f["nf_won"] else 0.0)
    out = {}
    for k, c in sorted(acc.items()):
        have = fills_for is not None
        out[k] = {"arm": c["arm"], "epoch": c["epoch"], "E1_orders": c["orders"],
                  "E1_fills": c["fills"] if have else None,
                  "fill_rate": (c["fills"] / c["orders"]) if have and c["orders"] else None,
                  "E2_pnl_per_filled_contract_before_fees": _mean(c["pnl"]), "n_settled_fills": len(c["pnl"]),
                  "E3_win_rate_fills": _mean(c["won"]), "E3_win_rate_nonfills_counterfactual": _mean(c["nf_won"]),
                  "n_nonfills_resolved": len(c["nf_won"]), "lookups_failed": c["lookups_failed"]}
    return out


def make_fills_for(rows: List[dict]):
    """(fills_for or None, note). Read-only demo GETs; in-memory cache; never writes."""
    try:
        spec = importlib.util.spec_from_file_location("demo_fill_forward_report", REPO / "scripts" / "demo_fill_forward_report.py")
        dfr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dfr)
        os.environ["BOT_ENV"] = "paper"
        from prediction_market_bot import t4_fill_status as tf
        tf._load_dotenv_if_needed(REPO / ".env")
        os.environ["BOT_ENV"] = "paper"
        from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
        from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
        client = KalshiMarketClient.from_env()
        if not demo_host_ok():
            return None, "fills skipped: host is not demo"
        if not client.has_signing_key():
            return None, "fills skipped: no signing key"
        sides = {r["order_id"]: r["side"] for r in rows if r.get("event") == "arm_order" and r.get("order_id") and r.get("side")}
        cache: dict = {}
        return (lambda oid, tk: dfr.lookup_fill(client, oid, tk, cache, sides.get(oid))), ""
    except Exception as e:  # noqa: BLE001 - the counts must still print
        return None, "fills skipped: " + type(e).__name__


def _collector():
    spec = importlib.util.spec_from_file_location("demo_fill_markout_collector", REPO / "scripts" / "demo_fill_markout_collector.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_join_inputs(rows: List[dict], client: Any, now: datetime):
    """W116.2 A2 (GG-1934 follow-on): ONE paginated fills pull, market GETs cached per ticker, 1-minute candles per ticker over
    the fill window and the minute before close. Read-only demo GETs; nothing is written. Returns (fills or None, market_of,
    candles_of, note)."""
    from datetime import timedelta
    col = _collector()
    placed = [r for r in rows if r.get("event") == "arm_order" and r.get("ok") and r.get("order_id")]
    starts = [parse_ts(r.get("ts")) for r in placed]
    starts = [t for t in starts if t]
    if not starts:
        return [], (lambda tk: None), None, "no placed orders"
    fills, ok = col.paginate_fills(client, int(min(starts).timestamp()) - 60)
    note = "ok" if ok else "fills pull failed (partial)"
    mine = {str(r["order_id"]): str(r.get("ticker") or "") for r in placed}
    fills = [f for f in fills if str(f.get("order_id")) in mine] if ok else None
    mkt: Dict[str, Optional[dict]] = {}

    def market_of(tk: str) -> Optional[dict]:
        if tk not in mkt:
            got = None
            for _ in range(2):  # one retry: a transient failure is not a lookup failure
                okm, d = client._get(f"/markets/{tk}")
                if okm and isinstance(d, dict):
                    got = d.get("market", d) or {}
                    break
            mkt[tk] = got
        return mkt[tk]

    win: Dict[str, list] = {}
    for f in fills or []:
        t = parse_ts(f.get("created_time"))
        tk = mine.get(str(f.get("order_id")))
        if t and tk:
            w = win.setdefault(tk, [t, t])
            w[0], w[1] = min(w[0], t), max(w[1], t)
    cnd: Dict[str, Any] = {}

    def candles_of(tk: str):
        if tk in cnd:
            return cnd[tk]
        rows_c: list = []
        if tk in win:
            lo, hi = win[tk]
            c = col.fetch_candles(client, tk, lo - timedelta(minutes=5), min(now, hi + timedelta(minutes=35)))
            rows_c += c.rows if c else []
            close = parse_ts((market_of(tk) or {}).get("close_time"))
            if close and close <= now:
                c2 = col.fetch_candles(client, tk, close - timedelta(minutes=10), close)
                rows_c += c2.rows if c2 else []
        seen, uniq = set(), []
        for r in rows_c:
            if r.get("end_period_ts") not in seen:
                seen.add(r.get("end_period_ts"))
                uniq.append(r)
        cnd[tk] = col.Candles(uniq) if uniq else None
        return cnd[tk]

    return fills, market_of, candles_of, note


def demo_client():
    """(client, note): the demo client with a signing key, or (None, why)."""
    try:
        os.environ["BOT_ENV"] = "paper"
        from prediction_market_bot import t4_fill_status as tf
        tf._load_dotenv_if_needed(REPO / ".env")
        os.environ["BOT_ENV"] = "paper"
        from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
        from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
        client = KalshiMarketClient.from_env()
        if not demo_host_ok():
            return None, "fills skipped: host is not demo"
        if not client.has_signing_key():
            return None, "fills skipped: no signing key"
        return client, ""
    except Exception as e:  # noqa: BLE001
        return None, "fills skipped: " + type(e).__name__


def _trim(summ: dict, min_orders: int) -> dict:
    """Leaf tables only for cells with >= min_orders placed (the box output is capped at 60 KB); the count dropped is kept."""
    keep = {c for c, v in summ["fill"].items() if v["n"] >= min_orders}
    out = {k: v for k, v in summ.items() if k not in ("fill", "selection", "options")}
    for t in ("fill", "selection", "options"):
        out[t] = {c: v for c, v in summ[t].items() if c in keep}
    out["cells_below_min_orders_dropped"] = len(summ["fill"]) - len(keep)
    return out


def joined(rows: List[dict], client: Any, now: datetime) -> dict:
    """The W116.2 per-order join, its health, per-arm E1/E2/E3 + markouts, and the placement model per epoch (never pooled)."""
    from prediction_market_bot.c5_execution.placement import join as pj, model as pm
    fills, market_of, candles_of, note = make_join_inputs(rows, client, now)
    recs = pj.records(rows, fills, market_of, candles_of, now)
    out: Dict[str, Any] = {"join_note": note, "join_health": pj.join_health(recs), "per_arm": pj.per_arm(recs),
                           "placement_model": {}}
    for ep in (PRE, POST):
        mr = pj.model_records([r for r in recs if r["epoch"] == ep])
        out["placement_model"][ep] = {"n": len(mr), "by_arm": pm.summary(mr, ("arm",)),
                                      "by_arm_sport": pm.summary(mr, ("arm", "sport")),
                                      "by_arm_leaf": _trim(pm.summary(mr, ("arm", "leaf")), 10)}
    return out


def build(rows: List[dict], fills_for, note: str, source: str, now: Optional[datetime] = None) -> dict:
    last = max((parse_ts(r.get("ts")) for r in rows if parse_ts(r.get("ts"))), default=None)
    return {"source": source, "read_utc": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rows": len(rows), "last_row_ts": last.strftime("%Y-%m-%dT%H:%M:%SZ") if last else None,
            "gg1771_epoch": EPOCH.strftime("%Y-%m-%dT%H:%M:%SZ"), "fills_note": note or "ok",
            "counts": counts(rows), "fills": fills_report(rows, fills_for)}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(LOG))
    ap.add_argument("--no-fills", action="store_true")
    ap.add_argument("--legacy-lookup", action="store_true", help="also run the old per-order GET path, for the before/after count")
    a = ap.parse_args(argv)
    rows = load_rows(Path(a.log))
    now = datetime.now(timezone.utc)
    if a.no_fills:
        rep = build(rows, None, "fills skipped: --no-fills", str(a.log), now)
    else:
        fills_for, note = make_fills_for(rows) if a.legacy_lookup else (None, "legacy per-order lookup not run")
        rep = build(rows, fills_for, note, str(a.log), now)
        client, why = demo_client()
        try:
            rep["join"] = joined(rows, client, now) if client is not None else {"join_note": why}
        except Exception as e:  # noqa: BLE001 - the counts must still print
            rep["join"] = {"join_note": "join failed: " + type(e).__name__ + ": " + str(e)[:200]}
    print(json.dumps(rep, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

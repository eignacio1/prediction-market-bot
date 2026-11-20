#!/usr/bin/env python3
"""READ-ONLY (W121.3 / B-097): fillable size per cell and arm, from depth logged at submit and the depth archive's full ladders.

Two sources, never mixed in one number:
  ORDERS  logs/arm_orders/orders.jsonl (+ .gz): every arm order logs `book_at_submit` (yes_bid, yes_ask, spread, yes_bid_size,
          yes_ask_size, own_touch_size) at decision time. Depth is MEASURED LIVE per order (CLAUDE.md: never a constant). Only the
          TOUCH size is logged, so ticks 1 / 2 / 3 behind the touch are not measurable from orders (reported as null, with the reason).
  LADDER  exp_output/DEPTH_ARCHIVE/depth_*.jsonl (capture_depth.py, full ladder retained). Series: MLB and NFL only. No NBA / NHL
          ladder is captured today (a registered gap; adding series is a new live component and is not done here).

Per (sport, market_type, band, arm): n orders, own-touch size (the queue ahead of a resting order), cross-touch size (the OPPOSITE
touch: what a taker crossing the spread meets), spread, by time to start. Opportunities / day = distinct (ticker, side, arm) per UTC
day among routed rows (orders and routed skips), post-GG-1771-epoch only. Writes nothing; stdout JSON only. Python 3.9-safe.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.io_jsonl import glob_files, iter_jsonl  # noqa: E402

EPOCH = "2026-11-06T01:03:42Z"  # GG-1771 / GG-1784: post-epoch only
ARMS = ("RIDE", "FADE", "MOMENTUM", "MODEL_FADE")
NOT_ROUTED = ("no_bet", "unrouted", "production_host_refused", "kill_switch_halted", "row_missing_fields")
BUCKETS = (("0-2h", 0.0, 2.0), ("2-6h", 2.0, 6.0), ("6-24h", 6.0, 24.0), ("24h+", 24.0, 1e9))
TICKS = (0, 1, 2, 3)  # levels at the touch (0) and up to k ticks worse; one tick = 1 cent on Kalshi


def bucket(h: Optional[float]) -> str:
    if h is None:
        return "unknown"
    for name, lo, hi in BUCKETS:
        if lo <= h < hi:
            return name
    return "unknown"


def pct(v: List[float], q: float) -> Optional[float]:
    if not v:
        return None
    s = sorted(v)
    i = (len(s) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (i - lo), 4)


def dist(v: Iterable[Optional[float]]) -> dict:
    x = [float(a) for a in v if a is not None]
    return {"n": len(x), "p25": pct(x, .25), "median": pct(x, .5), "p75": pct(x, .75)}


def _f(x: Any) -> Optional[float]:
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None


def order_sizes(r: dict) -> dict:
    """own-touch and cross-touch size (contracts) for one placed order. YES rests on the bid / crosses at the ask; NO the reverse."""
    b = r.get("book_at_submit") or {}
    bid, ask = _f(b.get("yes_bid_size")), _f(b.get("yes_ask_size"))
    own = _f(b.get("own_touch_size"))
    yes = r.get("side") == "yes"
    cross = ask if yes else bid
    spread = _f(b.get("spread"))
    return {"own": own, "cross": cross, "spread": spread}


def orders_table(rows: Iterable[dict]) -> dict:
    cells: Dict[str, dict] = {}
    opp: Dict[str, set] = defaultdict(set)
    days: Dict[str, set] = defaultdict(set)
    for r in rows:
        ev, ts = r.get("event"), str(r.get("ts") or "")
        if ts < EPOCH or r.get("arm") not in ARMS:
            continue
        sport = r.get("sport") or "?"
        key = f"{sport}|{r.get('market_type')}|{r.get('band')}|{r.get('arm')}"
        day = ts[:10]
        days[sport].add(day)
        placed = ev == "arm_order" and r.get("ok")
        routed_skip = ev == "arm_skip" and not any(str(r.get("reason", "")).startswith(x) for x in NOT_ROUTED)
        if placed or routed_skip or ev == "arm_would_order":
            opp[key].add((day, r.get("ticker"), r.get("side") or r.get("router_side") or "?"))
        if not placed:
            continue
        sz = order_sizes(r)
        c = cells.setdefault(key, {"sport": sport, "market_type": r.get("market_type"), "band": r.get("band"),
                                   "arm": r.get("arm"), "orders": 0, "own": [], "cross": [], "spread": [],
                                   "by_bucket": defaultdict(lambda: {"own": [], "cross": []}), "stake": [], "entry": []})
        c["orders"] += 1
        c["own"].append(sz["own"]); c["cross"].append(sz["cross"]); c["spread"].append(sz["spread"])
        c["stake"].append(_f(r.get("stake_usd"))); c["entry"].append(_f(r.get("entry_price")))
        bk = c["by_bucket"][bucket(_f(r.get("hours_to_start")))]
        bk["own"].append(sz["own"]); bk["cross"].append(sz["cross"])
    out = []
    for k, c in sorted(cells.items()):
        sport = c["sport"]
        nd = max(len(days[sport]), 1)
        out.append({"cell": k, "sport": sport, "market_type": c["market_type"], "band": c["band"], "arm": c["arm"],
                    "n_orders": c["orders"], "own_touch_contracts": dist(c["own"]), "cross_touch_contracts": dist(c["cross"]),
                    "spread": dist(c["spread"]), "stake_usd": dist(c["stake"]), "entry_price": dist(c["entry"]),
                    "by_hours_to_start": {b: {"own": dist(v["own"]), "cross": dist(v["cross"])}
                                          for b, v in sorted(c["by_bucket"].items())},
                    "opportunities": len(opp.get(k, ())), "days_sport_logged": nd,
                    "opportunities_per_day": round(len(opp.get(k, ())) / nd, 3)})
    cells_opp_only = sorted(k for k in opp if k not in cells)
    return {"cells": out, "cells_with_opportunities_but_no_placed_order": cells_opp_only,
            "days_by_sport": {s: {"n": len(d), "first": min(d), "last": max(d)} for s, d in days.items()}}


def ladder_depth(book: dict, side: str) -> Optional[dict]:
    """Contracts a taker could buy `side` within k ticks of the touch, from one full ladder {'yes': [[cents, size]], 'no': [...]}.
    Buying YES lifts the YES ask = 100 - NO bid; so its levels are the NO bids, best (highest) first. Buying NO uses the YES bids."""
    book_side = "no" if side == "yes" else "yes"
    lv = sorted(((int(p), int(s)) for p, s in (book.get(book_side) or []) if s), reverse=True)
    if not lv:
        return None
    best = lv[0][0]
    return {f"within_{k}": sum(s for p, s in lv if best - p <= k) for k in TICKS}


def ladder_table(files: List[str]) -> dict:
    agg: Dict[str, dict] = {}
    n_rows = 0
    for f in files:
        for r in iter_jsonl(f):
            book, series = r.get("book"), r.get("series_ticker")
            if not isinstance(book, dict) or not series:
                continue
            n_rows += 1
            ct = r.get("close_time")
            ts = r.get("retrieved_utc")
            try:
                h = (datetime.strptime(ct[:19], "%Y-%m-%dT%H:%M:%S") - datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")).total_seconds() / 3600.0
            except (TypeError, ValueError):
                h = None
            for side in ("yes", "no"):
                d = ladder_depth(book, side)
                if d is None:
                    continue
                a = agg.setdefault(f"{series}|{bucket(h)}", {"series": series, "hours_to_close_bucket": bucket(h),
                                                               **{f"within_{k}": [] for k in TICKS}})
                for k in TICKS:
                    a[f"within_{k}"].append(d[f"within_{k}"])
    rows = [{"series": a["series"], "hours_to_close_bucket": a["hours_to_close_bucket"],
             **{f"within_{k}": dist(a[f"within_{k}"]) for k in TICKS}} for _, a in sorted(agg.items())]
    return {"rows": rows, "n_ladder_rows": n_rows, "files": len(files),
            "note": "hours_to_close, NOT to start: the archive stores close_time only. Series: MLB and NFL; no NBA / NHL ladder is captured."}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orders", default=str(REPO / "logs" / "arm_orders" / "orders.jsonl"))
    ap.add_argument("--depth-glob", default=str(REPO / "exp_output" / "DEPTH_ARCHIVE" / "depth_*.jsonl"))
    a = ap.parse_args(argv)
    order_files = glob_files(a.orders) or glob_files(a.orders + ".gz")
    rows = [r for f in order_files for r in iter_jsonl(f)]
    out = {"as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "epoch": EPOCH,
           "orders_files": len(order_files), "order_rows": len(rows),
           "orders": orders_table(rows),
           "ladder": ladder_table(glob_files(a.depth_glob)),
           "limits": ["ORDERS log the touch size only; ticks 1 / 2 / 3 are measured from the ladder archive (MLB, NFL)",
                      "own_touch = queue ahead of a resting order; cross_touch = size a taker meets at the opposite touch"]}
    print(json.dumps(out, separators=(",", ":"), sort_keys=True))  # compact: box results cap at 60 KB
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

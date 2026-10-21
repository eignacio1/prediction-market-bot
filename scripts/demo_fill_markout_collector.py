#!/usr/bin/env python3
"""W81.1-B: the ADR-0072 criterion (c) collector -- held-side 1/5/30-minute markouts after each demo fill.

ADR-0072 (c) needs the 30-minute post-fill markout of treatment vs control; nothing collected it
(the report carried it as NOT_EVALUABLE). This job collects it FORWARD from the day it is installed:

  * orders (id, ticker, arm) come from logs/demo_fill_policy.jsonl (shadow_order, ok=True);
  * fill time and price come from the paginated demo GET /portfolio/fills (read-only);
  * the held-side two-sided mid at fill+1/5/30 min comes from the demo 1-minute candles
    (same quote logic as scripts/w63_3_fill_markouts.py: a side with no two-sided book is None, never 0).

Output: exp_output/FORWARD_TEST/markouts/markouts.jsonl (one row per filled order, written once its +30 min
candle exists) and EPOCH.json (collection start; only fills at/after it are eligible for (c)).
DEMO ONLY (demo_host_ok); read-only GETs; places, cancels and changes nothing. Alarm-only plumbing.
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

HORIZONS = (1, 5, 30)
BUFFER_S = 120          # wait this long after fill+30m so the closing candle exists
CANDLE_MAX_AGE_S = 180  # a quote older than this at the anchor is not a quote
LOG = REPO / "logs" / "demo_fill_policy.jsonl"
OUT_DIR = REPO / "exp_output" / "FORWARD_TEST" / "markouts"
ENV_FILE = REPO / ".env"


def parse_ts(s: Any) -> Optional[datetime]:
    """Tolerant ISO parse (Python 3.9 rejects 5-digit fractional seconds)."""
    if not s:
        return None
    s = str(s).replace("Z", "+00:00")
    s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s, count=1)
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def _f(x: Any) -> Optional[float]:
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None


def sport_of(ticker: str) -> str:
    t = ticker.split("-")[0].upper()
    for key, name in (("NFL", "NFL"), ("NHL", "NHL"), ("NBA", "NBA"), ("MLB", "MLB")):
        if key in t:
            return name
    return "OTHER"


def game_of(ticker: str) -> str:
    parts = ticker.split("-")
    return f"{sport_of(ticker)}|{parts[1] if len(parts) > 1 else ticker}"


class Candles:
    """Held-side quote from 1-minute demo candles (mirrors w63_3_fill_markouts.Candles)."""

    def __init__(self, rows: list[dict]):
        self.rows = sorted(rows or [], key=lambda r: r["end_period_ts"])
        self.t = [r["end_period_ts"] for r in self.rows]

    def quote(self, t: float, side: str, max_age: float = CANDLE_MAX_AGE_S) -> Optional[dict]:
        i = bisect.bisect_right(self.t, t) - 1
        if i < 0 or t - self.t[i] > max_age:
            return None
        r = self.rows[i]
        b = _f((r.get("yes_bid") or {}).get("close_dollars"))
        a = _f((r.get("yes_ask") or {}).get("close_dollars"))
        if b is None or a is None:
            return None
        if side == "NO":
            b, a = 1 - a, 1 - b
        return {"bid": b, "ask": a, "two_sided": b > 0 and a < 1}


def held_side_mid(c: Candles, t: float, side: str) -> Optional[float]:
    q = c.quote(t, side)
    if not q or not q["two_sided"]:
        return None
    return (q["bid"] + q["ask"]) / 2


def markouts_for(candles: Candles, fill_ts: datetime, side: str, price: float) -> dict:
    out = {}
    for h in HORIZONS:
        mid = held_side_mid(candles, fill_ts.timestamp() + h * 60, side)
        out[f"h{h}"] = None if mid is None else round(mid - price, 4)
    return out


def load_orders(path: Path) -> dict:
    """order_id -> {ticker, arm, order_ts} for ok shadow orders."""
    orders: dict = {}
    if not path.exists():
        return orders
    with open(path) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("event") == "shadow_order" and r.get("ok") and r.get("order_id"):
                orders[r["order_id"]] = {"ticker": r.get("ticker") or "", "arm": r.get("arm") or "unassigned_pre_test",
                                         "order_ts": r.get("ts")}
    return orders


def fill_side_price(f: dict) -> tuple[Optional[str], Optional[float]]:
    side = (f.get("side") or "").upper() or None
    if side == "YES":
        p = _f(f.get("yes_price_dollars"))
        p = p if p is not None else (None if _f(f.get("yes_price")) is None else _f(f.get("yes_price")) / 100)
    elif side == "NO":
        p = _f(f.get("no_price_dollars"))
        p = p if p is not None else (None if _f(f.get("no_price")) is None else _f(f.get("no_price")) / 100)
    else:
        p = None
    return side, p


def group_fills(fills: list[dict]) -> dict:
    """order_id -> {first fill ts, side, count-weighted price}."""
    by: dict = defaultdict(list)
    for f in fills:
        by[f.get("order_id")].append(f)
    out = {}
    for oid, fs in by.items():
        ts = [parse_ts(f.get("created_time")) for f in fs]
        ts = [t for t in ts if t]
        if not oid or not ts:
            continue
        num = den = 0.0
        side = None
        for f in fs:
            s, p = fill_side_price(f)
            n = _f(f.get("count_fp")) or _f(f.get("count")) or 1.0
            if s and p is not None:
                side = side or s
                num += p * n
                den += n
        if side and den:
            out[oid] = {"fill_ts": min(ts), "side": side, "price": num / den}
    return out


def read_done(path: Path) -> set:
    done = set()
    if path.exists():
        with open(path) as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["order_id"])
                except (ValueError, KeyError):
                    continue
    return done


def get_epoch(out_dir: Path, now: datetime) -> datetime:
    p = out_dir / "EPOCH.json"
    if p.exists():
        d = parse_ts(json.loads(p.read_text()).get("collection_start"))
        if d:
            return d
    from prediction_market_bot.atomic_io import atomic_write_text
    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(p, json.dumps({"collection_start": now.isoformat(),
                                      "note": "W81.1-B: ADR-0072 criterion (c) is judged only on fills at/after this instant"}, indent=1))
    return now


def paginate_fills(client: Any, min_ts: int) -> tuple[list[dict], bool]:
    items: list[dict] = []
    cursor = None
    while True:
        params: dict[str, Any] = {"limit": 1000, "min_ts": min_ts}
        if cursor:
            params["cursor"] = cursor
        ok, data = client._get("/portfolio/fills", params=params, authenticated=True)
        if not ok:
            return items, False
        batch = data.get("fills", [])
        items.extend(batch)
        cursor = data.get("cursor")
        if not cursor or not batch:
            return items, True
        time.sleep(0.15)


def fetch_candles(client: Any, ticker: str, start: datetime, end: datetime) -> Optional[Candles]:
    series = ticker.split("-")[0]
    ok, d = client._get(f"/series/{series}/markets/{ticker}/candlesticks",
                        params={"start_ts": int(start.timestamp()), "end_ts": int(end.timestamp()), "period_interval": 1},
                        authenticated=True)
    time.sleep(0.12)
    return Candles(d.get("candlesticks", [])) if ok else None


def collect(orders: dict, fills: dict, epoch: datetime, now: datetime, done: set, fetch, max_orders: int) -> list[dict]:
    """Pure core: rows for filled, eligible, matured orders. `fetch(ticker, start, end)` -> Candles|None."""
    rows = []
    cache: dict = {}
    for oid, fl in sorted(fills.items(), key=lambda kv: kv[1]["fill_ts"]):
        o = orders.get(oid)
        if not o or oid in done or fl["fill_ts"] < epoch:
            continue
        if now < fl["fill_ts"] + timedelta(minutes=max(HORIZONS), seconds=BUFFER_S):
            continue
        if len(rows) >= max_orders:
            break
        tk = o["ticker"]
        key = (tk, fl["fill_ts"].date())
        if key not in cache:
            cache[key] = fetch(tk, fl["fill_ts"] - timedelta(minutes=5), fl["fill_ts"] + timedelta(minutes=max(HORIZONS) + 5))
        c = cache[key]
        if c is None:
            continue  # transient fetch failure: retry next run
        rows.append({"order_id": oid, "arm": o["arm"], "sport": sport_of(tk), "game": game_of(tk), "ticker": tk,
                     "side": fl["side"], "fill_ts": fl["fill_ts"].isoformat(), "fill_price": round(fl["price"], 4),
                     "collected_ts": now.isoformat(), **markouts_for(c, fl["fill_ts"], fl["side"], fl["price"])})
    return rows


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log", default=str(LOG))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--env-file", default=str(ENV_FILE))
    ap.add_argument("--max-orders", type=int, default=400, help="cap per run (candle GETs are the cost)")
    args = ap.parse_args(argv)

    os.environ["BOT_ENV"] = "paper"  # demo only; .env must not flip the host
    from prediction_market_bot import t4_fill_status as tfs
    from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    tfs._load_dotenv_if_needed(Path(args.env_file))
    if not demo_host_ok():
        print("REFUSED: not the Kalshi DEMO host", file=sys.stderr)
        return 2
    client = KalshiMarketClient.from_env()
    if not client.has_signing_key():
        print("REFUSED: no signing key", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    out_dir = Path(args.out_dir)
    epoch = get_epoch(out_dir, now)
    orders = load_orders(Path(args.log))
    items, ok = paginate_fills(client, int(epoch.timestamp()))
    if not ok and not items:
        print("MARKOUT: fills fetch failed; nothing collected", file=sys.stderr)
        return 1
    mpath = out_dir / "markouts.jsonl"
    rows = collect(orders, group_fills(items), epoch, now, read_done(mpath),
                   lambda tk, a, b: fetch_candles(client, tk, a, b), args.max_orders)
    if rows:
        with open(mpath, "a") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    print(f"MARKOUT: epoch={epoch.isoformat()} orders_logged={len(orders)} fills_seen={len(items)} new_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

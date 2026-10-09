#!/usr/bin/env python3
"""W63.3 Part B step 1: read-only demo-venue GETs for order/fill detail on both books.

Writes one JSON file (default /tmp/w63_3_venue.json): all fills (GET /portfolio/fills) and one
GET /portfolio/orders/{id} for every CONFIRMED_FILLED order plus a seeded 300-order sample of the rest. Demo only (refuses BOT_ENV=live).
Run on the VPS: cd /opt/prediction-market-bot && PYTHONPATH=src:scripts python3 scripts/w63_3_fetch_orders.py
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    if os.environ.get("BOT_ENV", "").lower() == "live":
        print("refusing BOT_ENV=live"); return 2
    os.environ["BOT_ENV"] = "paper"
    from prediction_market_bot import t4_fill_status as tf
    tf._load_dotenv_if_needed(REPO / ".env")
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    client = KalshiMarketClient.from_env()
    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/w63_3_venue.json")
    fills, complete = tf._paginate(client, "/portfolio/fills", "fills")
    import random
    filled_ids, other_ids = [], []
    for book, (pf, sc) in tf.BOOKS.items():
        status = tf.load_fill_status(Path(sc))
        for p in json.load(open(pf))["closed_positions"]:
            if p.get("kalshi_order_id"):
                f = status.get(p["position_id"], {}).get("fill_class") == tf.CONFIRMED_FILLED
                (filled_ids if f else other_ids).append(p["kalshi_order_id"])
    # Every filled order (GETs run ~2s each); a seeded sample of never-filled orders to validate
    # the ledger-derived limit/submit-time used for the rest.
    random.Random(20261009).shuffle(other_ids)
    ids = filled_ids + other_ids[:300]
    orders = {}
    for i, oid in enumerate(dict.fromkeys(ids)):
        ok, data = client._get(f"/portfolio/orders/{oid}", authenticated=True)
        orders[oid] = data.get("order", data) if ok and isinstance(data, dict) else {"_error": str(data)[:200]}
        time.sleep(0.12)
        if i % 500 == 0:
            print(i, len(ids), flush=True)
    out_path.write_text(json.dumps({"fills": fills, "fills_complete": complete, "orders": orders}))
    print("fills", len(fills), "orders", len(orders), "->", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

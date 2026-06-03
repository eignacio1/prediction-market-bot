"""
One-off script: cancel all resting orders on the Kalshi DEMO account.

Run from repo root:
    BOT_ENV=paper PYTHONPATH=src python3 scripts/cancel_demo_orders.py

Requires VENUE_API_KEY and VENUE_PRIVATE_KEY_PATH in .env (NFR-05).
Only runs against demo — exits immediately if BOT_ENV != paper.
"""

import os
import sys
import time

sys.path.insert(0, "src")

# Safety guard — never run against live account
bot_env = os.environ.get("BOT_ENV", "")
if bot_env != "paper":
    print(f"ERROR: BOT_ENV={bot_env!r}. This script only runs against demo (BOT_ENV=paper).")
    sys.exit(1)

from prediction_market_bot.c5_execution.kalshi_client import (
    KalshiMarketClient,
    _auth_headers,
    _kalshi_base_url,
)
import requests

client = KalshiMarketClient.from_env()

if not client.has_signing_key():
    print("ERROR: No RSA signing key loaded. Set VENUE_PRIVATE_KEY_PATH.")
    sys.exit(1)

BASE_URL = _kalshi_base_url()
API_PATH_PREFIX = "/trade-api/v2"

session = requests.Session()
session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})


def _get(path: str, params: dict | None = None):
    url = f"{BASE_URL}{path}"
    full_path = f"{API_PATH_PREFIX}{path}"
    headers = _auth_headers(client._key_id, client._private_key, "GET", full_path)
    r = session.get(url, params=params, headers=headers, timeout=10)
    return r.status_code, r.json() if r.content else {}


def _delete(path: str):
    url = f"{BASE_URL}{path}"
    full_path = f"{API_PATH_PREFIX}{path}"
    headers = _auth_headers(client._key_id, client._private_key, "DELETE", full_path)
    r = session.delete(url, headers=headers, timeout=10)
    return r.status_code, r.json() if r.content else {}


# Fetch all resting orders (paginated)
print("Fetching resting orders...")
all_orders = []
cursor = None
while True:
    params = {"status": "resting", "limit": 100}
    if cursor:
        params["cursor"] = cursor
    status, data = _get("/portfolio/orders", params)
    if status != 200:
        print(f"ERROR fetching orders: HTTP {status} — {data}")
        sys.exit(1)
    orders = data.get("orders", [])
    all_orders.extend(orders)
    cursor = data.get("cursor")
    if not cursor or not orders:
        break

print(f"Found {len(all_orders)} resting order(s).")

if not all_orders:
    print("Nothing to cancel.")
    sys.exit(0)

# Cancel each order
canceled = 0
failed = 0
for order in all_orders:
    order_id = order.get("order_id") or order.get("id", "")
    ticker = order.get("ticker", "?")
    side = order.get("side", "?")
    contracts = order.get("remaining_count", order.get("count", "?"))
    print(f"  Canceling {order_id[:12]}... ticker={ticker} side={side} contracts={contracts}", end=" ")
    status, resp = _delete(f"/portfolio/orders/{order_id}")
    if status in (200, 204):
        print("OK")
        canceled += 1
    else:
        print(f"FAILED (HTTP {status}: {resp})")
        failed += 1
    time.sleep(0.15)  # 150ms between requests — avoid 429

print(f"\nDone. Canceled: {canceled}  Failed: {failed}")

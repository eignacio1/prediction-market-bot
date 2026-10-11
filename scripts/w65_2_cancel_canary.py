"""W65.2 canary: place ONE 1-contract DEMO limit order priced where it cannot fill, cancel it
through KalshiMarketClient.cancel_order, then GET the order to confirm it is canceled.
Demo only (refuses unless BOT_ENV=paper). Writes every call to the JSON report path given as argv[1].
Exit 0 only if the cancel was confirmed by GET."""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient, _kalshi_base_url


def main(out_path: str) -> int:
    if os.environ.get("BOT_ENV") != "paper" or "demo" not in _kalshi_base_url():
        print("REFUSED: not the demo host / BOT_ENV!=paper", file=sys.stderr)
        return 2
    c = KalshiMarketClient.from_env()
    if not c.has_signing_key():
        print("REFUSED: no signing key", file=sys.stderr)
        return 2
    log: list[dict] = []

    def rec(step: str, ok, data) -> None:
        log.append({"ts": datetime.now(timezone.utc).isoformat(), "step": step, "ok": ok, "data": data})

    ok, data = c._get("/markets", params={"status": "open", "limit": 200})
    rec("list_markets", ok, {"n": len(data.get("markets", [])) if ok else data})
    pick = None
    for m in (data.get("markets", []) if ok else []):
        t = m.get("ticker", "")
        okb, book = c.get_market_book(t)
        if okb and book["yes_bid"] >= 0.10 and book["yes_ask"] > book["yes_bid"]:
            pick = (t, book)
            break
    if not pick:
        rec("pick_market", False, "no liquid open market found")
        json.dump(log, open(out_path, "w"), indent=1)
        return 3
    ticker, book = pick
    rec("pick_market", True, {"ticker": ticker, **book})

    # YES bid at 1c: far below best bid >= 10c, cannot cross or fill. size_usd=0.01 -> 1 contract.
    order = c.submit_order(ticker=ticker, side="yes", size_usd=0.01, mid_price=0.01,
                           client_order_id=f"w65-2-canary-{uuid.uuid4().hex[:12]}")
    rec("submit_order", order.ok, {"order_id": order.order_id, "contracts": order.contracts,
                                   "yes_price_cents": order.yes_price_cents, "status": order.status,
                                   "error": order.error})
    if not order.ok:
        json.dump(log, open(out_path, "w"), indent=1)
        return 4
    okg, g1 = c._get(f"/portfolio/orders/{order.order_id}", authenticated=True)
    rec("get_before_cancel", okg, g1)
    okc, dc = c.cancel_order(order.order_id)
    rec("cancel_order", okc, dc)
    time.sleep(2)
    okg2, g2 = c._get(f"/portfolio/orders/{order.order_id}", authenticated=True)
    rec("get_after_cancel", okg2, g2)
    status = str((g2.get("order", g2) if okg2 else {}).get("status", "")).lower()
    confirmed = okc and okg2 and status in ("canceled", "cancelled")
    rec("verdict", confirmed, {"final_status": status})
    json.dump(log, open(out_path, "w"), indent=1)
    print(json.dumps(log[-1]))
    return 0 if confirmed else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

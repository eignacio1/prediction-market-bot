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

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
os.environ["BOT_ENV"] = "paper"
if os.environ.get("BOT_ENV", "").lower() == "live":
    sys.exit(2)
from prediction_market_bot import t4_fill_status as tf  # noqa: E402

tf._load_dotenv_if_needed(REPO / ".env")
os.environ["BOT_ENV"] = "paper"  # .env must not flip the host
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient, _kalshi_base_url  # noqa: E402


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

    # GG-560 root cause: the demo host lists only a SUBSET of production markets, and a ticker
    # absent from demo returns 404 not_found on order submit. Candidates MUST come from the demo
    # listing itself (authenticated=True -> demo base), never from production.
    cands: list[tuple[str, dict]] = []
    cursor = ""
    seen = 0
    for _page in range(10):
        params = {"status": "open", "limit": 1000, "mve_filter": "exclude"}
        if cursor:
            params["cursor"] = cursor
        ok, data = c._get("/markets", params=params, authenticated=True)
        if not ok:
            rec("list_markets", False, data)
            break
        mk = data.get("markets", [])
        seen += len(mk)
        for m in mk:
            if len(cands) >= 12:
                break
            try:
                bid = float(m.get("yes_bid_dollars") or 0)
                ask = float(m.get("yes_ask_dollars") or 0)
            except (TypeError, ValueError):
                continue
            # a 1c YES bid cannot fill when the best ask is >= 3c; a two-sided book is required
            if m.get("status") in ("active", "open") and ask >= 0.03 and bid > 0:
                cands.append((m["ticker"], {"yes_bid": bid, "yes_ask": ask}))
        cursor = data.get("cursor", "")
        if len(cands) >= 12 or not cursor:
            break
    rec("list_markets", True, {"seen": seen, "candidates": len(cands)})
    if not cands:
        rec("pick_market", False, "no liquid open market found")
        json.dump(log, open(out_path, "w"), indent=1)
        return 3
    # prefer MLB (the family the bot has placed demo orders on); try candidates until one accepts the order
    cands.sort(key=lambda t: not t[0].startswith("KXMLB"))
    order = None
    for ticker, book in cands:
        rec("pick_market", True, {"ticker": ticker, **book})
        # YES bid at 1c: far below best bid, cannot cross or fill. size_usd=0.01 -> 1 contract.
        order = c.submit_order(ticker=ticker, side="yes", size_usd=0.01, mid_price=0.01,
                               client_order_id=f"w65-2-canary-{uuid.uuid4().hex[:12]}")
        rec("submit_order", order.ok, {"order_id": order.order_id, "contracts": order.contracts,
                                       "yes_price_cents": order.yes_price_cents, "status": order.status,
                                       "error": order.error})
        if order.ok:
            break
    if not order or not order.ok:
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

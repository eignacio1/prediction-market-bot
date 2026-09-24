#!/usr/bin/env python3
"""Cross-check: for a sample of NOT_RETRIEVABLE rows spanning every affected
game_date, query GET /portfolio/orders?ticker=<ticker> (not by order_id) to
determine whether the market ever saw ANY order from this account at all.

This distinguishes two very different findings:
  (a) order existed once, was purged from single-order lookup by ID after
      some retention window (a "retention boundary")
  (b) no order for that ticker exists in Kalshi's history at all, under any
      order_id -- i.e. it was never actually submitted to the exchange

Read-only. Does not submit, cancel, or modify anything.
"""
import json
import sys
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, "src")
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient  # noqa: E402

PORTFOLIO = Path("exp_output/T565_calibration_benchmark/paper_portfolio_mlb_t4.LIVE.20260922.json")
RESULTS = Path("exp_output/T565_calibration_benchmark/t571_kalshi_verification_results.json")


def main():
    port = json.load(open(PORTFOLIO))
    by_pid = {p["position_id"]: p for p in port["closed_positions"]}
    res = json.load(open(RESULTS))["results"]

    nr_by_date = defaultdict(list)
    for r in res:
        if r["verdict"] == "NOT_RETRIEVABLE":
            nr_by_date[r["game_date"]].append(r)

    client = KalshiMarketClient.from_env()
    sample = []
    for date, rows in sorted(nr_by_date.items()):
        sample.extend(rows[:3])  # up to 3 per affected date

    print(f"sampling {len(sample)} NOT_RETRIEVABLE rows across {len(nr_by_date)} dates")
    out = []
    for r in sample:
        p = by_pid.get(r["position_id"])
        ticker = p.get("kalshi_ticker") if p else None
        if not ticker:
            out.append({**r, "ticker_orders_found": None, "note": "no ticker on row"})
            continue
        ok, data = client._get("/portfolio/orders", {"ticker": ticker}, authenticated=True)
        n_found = len(data.get("orders", [])) if ok and isinstance(data, dict) else None
        out.append({
            "position_id": r["position_id"],
            "game_date": r["game_date"],
            "ticker": ticker,
            "kalshi_order_id": r["kalshi_order_id"],
            "ticker_orders_found": n_found,
        })
        print(f"  {r['game_date']} {r['position_id']} ticker={ticker} orders_found={n_found}")
        time.sleep(0.15)

    n_zero = sum(1 for o in out if o.get("ticker_orders_found") == 0)
    n_nonzero = sum(1 for o in out if isinstance(o.get("ticker_orders_found"), int) and o["ticker_orders_found"] > 0)
    print(f"\nSUMMARY: {n_zero}/{len(out)} tickers have ZERO orders ever (any order_id); {n_nonzero} have >=1 order under a different id")

    with open("/tmp/t571_ticker_crosscheck_results.json", "w") as f:
        json.dump({"sample": out, "n_zero": n_zero, "n_nonzero": n_nonzero, "n_total": len(out)}, f, indent=2, default=str)


if __name__ == "__main__":
    main()

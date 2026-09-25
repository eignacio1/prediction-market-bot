#!/usr/bin/env python3
"""T-573 Deliverable 2 (+ extends Deliverable 1b to full census): for every one
of the 731 NOT_RETRIEVABLE T4M-PROJ epoch-12 clean rows, check whether an order
matching this row's EXACT ticker shows up under any alternate key form:
  - event-level: GET /portfolio/orders?event_ticker=<event>
  - account-wide date-window: GET /portfolio/orders?min_ts=<>&max_ts=<> (no ticker
    filter at all -- catches a ticker string malformed enough that no substring
    of it is a valid key)

API calls are deduplicated by event_ticker and by game_date so this scales to
the full 731 without a call-per-row blowup (~50-80 unique events/dates instead
of 731*2).

Four-bucket classification per row, reconciled to len(NOT_RETRIEVABLE rows):
  - RESOLVED_UNDER_ALTERNATE_KEY: a matching-ticker order was found under event
    or date-window query despite single-order-by-id lookup failing. If this is
    ever >0, the census must STOP per Deliverable 1b's directive.
  - NO_ORDER_FOUND_UNDER_ANY_KEY: zero matching-ticker orders under order_id,
    ticker-filter (T-571's crosscheck), event-level, AND account-wide window.
    This is the strongest evidence available that the order was never submitted.

Read-only. authenticated=True on every call (T-556).
Run ON THE VPS.
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, "src")
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient  # noqa: E402
from prediction_market_bot import logic_epoch as le  # noqa: E402


def event_ticker_from(ticker: str) -> str:
    return "-".join(ticker.split("-")[:2])


def date_window_epoch(game_date: str) -> tuple[int, int]:
    d = datetime.strptime(game_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = d - timedelta(days=1)
    hi = d + timedelta(days=2)
    return int(lo.timestamp()), int(hi.timestamp())


def main() -> None:
    portfolio_path = Path("logs/paper_portfolio_mlb_t4.json")
    verif_path = Path("/tmp/t571_kalshi_verification_results.json")
    out_path = Path("/tmp/t573_full_census_results.json")

    client = KalshiMarketClient.from_env()
    if not client.has_signing_key():
        print("ERROR: no signing key", file=sys.stderr)
        sys.exit(1)

    portfolio = json.load(open(portfolio_path))
    closed = portfolio.get("closed_positions", [])
    by_pid = {
        p["position_id"]: p for p in closed
        if p.get("band") == "T4M-PROJ" and le.is_clean_for_band(p.get("logic_epoch"), "T4M-PROJ")
    }

    verif = json.load(open(verif_path))
    nr_rows = [r for r in verif["results"] if r["verdict"] == "NOT_RETRIEVABLE"]
    print(f"census target: {len(nr_rows)} NOT_RETRIEVABLE rows")

    # attach ticker + event_ticker + date window
    enriched = []
    missing_ticker = 0
    for r in nr_rows:
        row = by_pid.get(r["position_id"], {})
        ticker = row.get("kalshi_ticker")
        if not ticker:
            missing_ticker += 1
            enriched.append({**r, "ticker": None})
            continue
        enriched.append({**r, "ticker": ticker, "event_ticker": event_ticker_from(ticker)})

    unique_events = sorted({e["event_ticker"] for e in enriched if e.get("event_ticker")})
    unique_dates = sorted({e["game_date"] for e in enriched if e.get("game_date")})
    print(f"unique event_tickers: {len(unique_events)}, unique game_dates: {len(unique_dates)}, rows missing ticker: {missing_ticker}")

    event_cache: dict[str, list[dict]] = {}
    for i, ev in enumerate(unique_events):
        ok, data = client._get("/portfolio/orders", {"event_ticker": ev}, authenticated=True)
        orders = data.get("orders", []) if ok and isinstance(data, dict) else []
        event_cache[ev] = orders
        if (i + 1) % 20 == 0:
            print(f"  event fetch {i+1}/{len(unique_events)}")
        time.sleep(0.12)

    window_cache: dict[str, list[dict]] = {}
    for i, d in enumerate(unique_dates):
        lo, hi = date_window_epoch(d)
        ok, data = client._get("/portfolio/orders", {"min_ts": lo, "max_ts": hi}, authenticated=True)
        orders = data.get("orders", []) if ok and isinstance(data, dict) else []
        window_cache[d] = orders
        print(f"  date window {d}: {len(orders)} orders account-wide ({i+1}/{len(unique_dates)})")
        time.sleep(0.12)

    results = []
    n_resolved = 0
    n_no_order_anywhere = 0
    for e in enriched:
        ticker = e.get("ticker")
        if not ticker:
            results.append({**e, "bucket": "UNREACHABLE_UNEXPLAINED", "reason": "no kalshi_ticker on ledger row -- cannot probe at all"})
            continue
        ev = e["event_ticker"]
        d = e["game_date"]
        event_match = [o for o in event_cache.get(ev, []) if o.get("ticker") == ticker]
        window_match = [o for o in window_cache.get(d, []) if o.get("ticker") == ticker]
        resolved = bool(event_match or window_match)
        if resolved:
            n_resolved += 1
            results.append({
                **e, "bucket": "RESOLVED_UNDER_ALTERNATE_KEY",
                "event_match": event_match, "window_match": window_match,
            })
        else:
            n_no_order_anywhere += 1
            results.append({
                **e, "bucket": "NO_ORDER_FOUND_UNDER_ANY_KEY",
                "event_level_orders_in_event": len(event_cache.get(ev, [])),
                "window_level_orders_in_window": len(window_cache.get(d, [])),
            })

    out = {
        "n_total_nr": len(nr_rows),
        "n_resolved_under_alternate_key": n_resolved,
        "n_no_order_found_under_any_key": n_no_order_anywhere,
        "n_missing_ticker": missing_ticker,
        "unique_events_checked": len(unique_events),
        "unique_dates_checked": len(unique_dates),
        "results": results,
    }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)

    print(f"\nFINAL: total={len(nr_rows)} resolved_under_alt_key={n_resolved} no_order_anywhere={n_no_order_anywhere} missing_ticker={missing_ticker}")
    print(f"wrote {out_path}")
    if n_resolved > 0:
        print("!" * 70)
        print(f"!!! STOP: {n_resolved} row(s) resolved under an alternate key. Report immediately.")
        print("!" * 70)


if __name__ == "__main__":
    main()

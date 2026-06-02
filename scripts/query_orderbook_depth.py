#!/usr/bin/env python3
"""
query_orderbook_depth.py — T-127 / KI-023 resolution script
=============================================================
Purpose:
    Query Kalshi orderbook depth for active KXNBAPTS markets during the
    Finals window (Jun 3–22, 2026) to resolve KI-023.

    KI-023: No estimate of KXNBAPTS market depth exists. At full operational
    scale (300+ bets/night), bot order flow may move own prices. The Finals
    window is the only active KXNBAPTS opportunity before October 2026.

What to do with the output:
    1. Record total visible depth (YES + NO combined, per contract)
    2. Record depth within $0.10 of best price (tight liquidity estimate)
    3. Compare our paper cap ($80/bet) and projected live cap ($500/bet)
       against ~5% of visible depth threshold
    4. If live cap > 5% of visible depth on a typical contract → register
       new `max_order_pct_of_depth` limit in _HARD_LIMITS via ADR before G6

Usage:
    PYTHONPATH=src python3 scripts/query_orderbook_depth.py
    PYTHONPATH=src python3 scripts/query_orderbook_depth.py --ticker KXNBAPTS-25-LBJ-22
    PYTHONPATH=src python3 scripts/query_orderbook_depth.py --all --limit 5

Governance:
    - Data from this script feeds G6 live capital ADR-0005 (DS sign-off)
    - Run during any Finals game day before Jun 22, 2026
    - If window is missed: no equivalent data until 2026-27 pre-season (October)
    - Output is logged to logs/orderbook_depth_YYYYMMDD.json for audit trail
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure src/ is on path when run with PYTHONPATH=src or from project root
project_root = Path(__file__).resolve().parents[1]
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from prediction_market_bot.c5_execution.kalshi_client import KalshiClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAPER_CAP_USD = 80.0       # current paper per-bet cap
LIVE_CAP_USD  = 500.0      # projected live per-bet cap (from risk.py _HARD_LIMITS)
DEPTH_IMPACT_THRESHOLD_PCT = 0.05  # flag if order > 5% of visible depth


# ---------------------------------------------------------------------------
# Orderbook fetching
# ---------------------------------------------------------------------------

def fetch_orderbook(client: KalshiClient, ticker: str) -> dict[str, Any] | None:
    """
    Call GET /markets/{ticker}/orderbook via KalshiClient.
    Returns raw response dict, or None on failure.

    Endpoint uses price discovery URL (always live) — unauthenticated.
    """
    try:
        data = client._get(f"/markets/{ticker}/orderbook", authenticated=False)
        return data
    except Exception as exc:
        print(f"  ERROR fetching {ticker}: {exc}")
        return None


def compute_depth_metrics(orderbook: dict[str, Any]) -> dict[str, Any]:
    """
    Compute depth metrics from raw orderbook response.

    Kalshi orderbook format:
      {
        "orderbook": {
          "yes": [[price_cents, quantity], ...],  // bids for YES
          "no":  [[price_cents, quantity], ...]   // bids for NO
        }
      }

    Prices are in cents (0-99). Quantities are in contracts ($1 face value each).
    Total dollar depth = sum(price_cents / 100 * quantity) for each level.
    """
    ob = orderbook.get("orderbook", {})
    yes_levels = ob.get("yes", [])
    no_levels  = ob.get("no",  [])

    def level_usd(levels: list) -> float:
        return sum((price / 100.0) * qty for price, qty in levels)

    def levels_within_spread(levels: list, spread_cents: int = 10) -> float:
        if not levels:
            return 0.0
        best_price = max(price for price, _ in levels)
        tight = [(p, q) for p, q in levels if p >= best_price - spread_cents]
        return sum((p / 100.0) * q for p, q in tight)

    yes_total  = level_usd(yes_levels)
    no_total   = level_usd(no_levels)
    combined   = yes_total + no_total
    yes_tight  = levels_within_spread(yes_levels)
    no_tight   = levels_within_spread(no_levels)
    tight_total = yes_tight + no_tight

    best_yes = max((p for p, _ in yes_levels), default=None) if yes_levels else None
    best_no  = max((p for p, _ in no_levels),  default=None) if no_levels  else None

    paper_pct = (PAPER_CAP_USD / combined * 100) if combined > 0 else None
    live_pct  = (LIVE_CAP_USD  / combined * 100) if combined > 0 else None

    paper_flag = paper_pct is not None and (paper_pct / 100) > DEPTH_IMPACT_THRESHOLD_PCT
    live_flag  = live_pct  is not None and (live_pct  / 100) > DEPTH_IMPACT_THRESHOLD_PCT

    return {
        "yes_depth_usd":      round(yes_total, 2),
        "no_depth_usd":       round(no_total,  2),
        "combined_depth_usd": round(combined,  2),
        "tight_depth_usd":    round(tight_total, 2),
        "best_yes_cents":     best_yes,
        "best_no_cents":      best_no,
        "yes_levels":         len(yes_levels),
        "no_levels":          len(no_levels),
        "paper_cap_pct_of_depth":   round(paper_pct, 1) if paper_pct else None,
        "live_cap_pct_of_depth":    round(live_pct,  1) if live_pct  else None,
        "paper_impact_flag":  paper_flag,
        "live_impact_flag":   live_flag,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SEPARATOR = "-" * 68

def print_market_report(ticker: str, metrics: dict[str, Any]) -> None:
    print(f"\n  {ticker}")
    print(f"    YES depth: ${metrics['yes_depth_usd']:.2f}  "
          f"({metrics['yes_levels']} levels, best {metrics['best_yes_cents']}¢)")
    print(f"    NO  depth: ${metrics['no_depth_usd']:.2f}  "
          f"({metrics['no_levels']} levels, best {metrics['best_no_cents']}¢)")
    print(f"    Combined:  ${metrics['combined_depth_usd']:.2f}  "
          f"(tight ±10¢: ${metrics['tight_depth_usd']:.2f})")
    paper_str = f"{metrics['paper_cap_pct_of_depth']:.1f}%" if metrics['paper_cap_pct_of_depth'] else "N/A"
    live_str  = f"{metrics['live_cap_pct_of_depth']:.1f}%"  if metrics['live_cap_pct_of_depth']  else "N/A"
    paper_flag = " *** IMPACT FLAG ***" if metrics['paper_impact_flag'] else ""
    live_flag  = " *** IMPACT FLAG — REGISTER ADR LIMIT ***" if metrics['live_impact_flag'] else ""
    print(f"    Paper cap (${PAPER_CAP_USD}) = {paper_str} of depth{paper_flag}")
    print(f"    Live cap  (${LIVE_CAP_USD}) = {live_str} of depth{live_flag}")


def print_aggregate_report(results: list[dict[str, Any]]) -> None:
    valid = [r for r in results if r.get("metrics")]
    if not valid:
        print("\nNo valid orderbook data collected.")
        return

    avg_combined = sum(r["metrics"]["combined_depth_usd"] for r in valid) / len(valid)
    avg_tight    = sum(r["metrics"]["tight_depth_usd"]     for r in valid) / len(valid)
    any_live_flag = any(r["metrics"]["live_impact_flag"] for r in valid)

    print(f"\n{SEPARATOR}")
    print("AGGREGATE SUMMARY")
    print(f"{SEPARATOR}")
    print(f"  Markets sampled:       {len(valid)}")
    print(f"  Avg combined depth:    ${avg_combined:.2f}")
    print(f"  Avg tight depth:       ${avg_tight:.2f}")
    print(f"  Live cap impact flag:  {'YES — register max_order_pct_of_depth ADR' if any_live_flag else 'No'}")
    print(f"\n  Paper scale (${PAPER_CAP_USD}/bet): {'FLAGGED' if any(r['metrics']['paper_impact_flag'] for r in valid) else 'OK'}")
    print(f"  Live scale  (${LIVE_CAP_USD}/bet): {'FLAGGED — must add ADR limit before G6' if any_live_flag else 'OK'}")

    if any_live_flag:
        print(f"\n  ACTION REQUIRED:")
        print(f"    Add max_order_pct_of_depth (= {int(DEPTH_IMPACT_THRESHOLD_PCT * 100)}% of visible depth)")
        print(f"    to _HARD_LIMITS in risk.py via ADR before G6 live capital authorization.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query KXNBAPTS orderbook depth — T-127 / KI-023"
    )
    parser.add_argument("--ticker", help="Query a single known ticker")
    parser.add_argument("--all", action="store_true",
                        help="Fetch all active KXNBAPTS markets and sample up to --limit")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max markets to query in --all mode (default: 5)")
    args = parser.parse_args()

    client = KalshiClient()
    results = []
    tickers_to_query: list[str] = []

    if args.ticker:
        tickers_to_query = [args.ticker]
    else:
        # Fetch active KXNBAPTS markets
        print("Fetching active KXNBAPTS markets from Kalshi...", flush=True)
        try:
            markets = client.fetch_player_points_markets()
            if not markets:
                print("No active KXNBAPTS markets found.")
                sys.exit(0)
            tickers_to_query = [m["ticker"] for m in markets[: args.limit]]
            print(f"Found {len(markets)} markets. Querying {len(tickers_to_query)}.")
        except Exception as exc:
            print(f"ERROR fetching markets: {exc}")
            sys.exit(1)

    print(f"\n{SEPARATOR}")
    print(f"KXNBAPTS ORDERBOOK DEPTH QUERY  — {datetime.now(timezone.utc).isoformat()}")
    print(f"T-127 / KI-023  |  Paper cap: ${PAPER_CAP_USD}  |  Live cap: ${LIVE_CAP_USD}")
    print(SEPARATOR)

    for ticker in tickers_to_query:
        raw = fetch_orderbook(client, ticker)
        if raw is None:
            results.append({"ticker": ticker, "metrics": None, "error": True})
            continue
        metrics = compute_depth_metrics(raw)
        print_market_report(ticker, metrics)
        results.append({"ticker": ticker, "metrics": metrics, "error": False})

    print_aggregate_report(results)

    # Write audit log
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"orderbook_depth_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    audit = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "T-127",
        "governance_gap": "KI-023",
        "paper_cap_usd": PAPER_CAP_USD,
        "live_cap_usd": LIVE_CAP_USD,
        "impact_threshold_pct": DEPTH_IMPACT_THRESHOLD_PCT,
        "results": results,
    }
    log_path.write_text(json.dumps(audit, indent=2))
    print(f"\n  Audit log: {log_path}")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    main()

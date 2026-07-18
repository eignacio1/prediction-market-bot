#!/usr/bin/env python3
"""
query_orderbook_depth_mlb.py — T-377 / GG-045 empirical depth pull
=====================================================================
Purpose:
    Query real Kalshi orderbook depth for active KXMLBHIT (MLB player hits)
    markets to empirically ground GG-045 (capital ceiling from market depth).
    The $500-$2,000/market depth figure currently cited for GG-045 is an
    UNVERIFIED ESTIMATE — this script produces a measured replacement.

    Adapted from scripts/query_orderbook_depth.py (T-127/KI-023, NBA/KXNBAPTS)
    but written as a separate MLB-scoped script rather than editing the NBA
    original, per this session's "do not touch anything NBA-tagged" scope.

Lesson carried forward from GG-041 (2026-06, NBA):
    A prior identical pull for KXNBAPTS was run pre-market, before Finals
    markets opened, and returned combined_depth_usd=0 for every market — a
    dead-end never re-run during an actual live window. Depth pulls MUST
    happen while markets are genuinely open/liquid, not pre-market or
    post-resolution, or the data is worthless zeros. This script logs
    market status/close_time alongside depth so a zero-depth read can be
    diagnosed (no market open yet vs. genuinely thin book) rather than
    silently treated as a valid data point.

Usage:
    PYTHONPATH=src python3 scripts/query_orderbook_depth_mlb.py --all --limit 30
    PYTHONPATH=src python3 scripts/query_orderbook_depth_mlb.py --ticker KXMLBHIT-...

Governance:
    - Feeds GG-045 decision-request memo (data-collection/analysis only —
      Hard Rule 3: no C4 wiring from this script's output without sign-off).
    - Output logged to logs/orderbook_depth_mlb_YYYYMMDD_HHMMSS.json for
      audit trail (T-377).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parents[1]
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from prediction_market_bot.c5_execution.kalshi_client import (
    KalshiMarketClient,
    SERIES_MLB_PLAYER_HITS,
)

LIVE_CAP_USD = 500.0  # current _HARD_LIMITS["max_single_event_exposure_usd"], risk.py
DEPTH_IMPACT_THRESHOLD_PCT = 0.05

SEPARATOR = "-" * 68


def fetch_orderbook(client: KalshiMarketClient, ticker: str) -> dict[str, Any] | None:
    try:
        ok, data = client._get(f"/markets/{ticker}/orderbook")
        return data if ok else None
    except Exception as exc:
        print(f"  ERROR fetching {ticker}: {exc}")
        return None


def compute_depth_metrics(orderbook: dict[str, Any]) -> dict[str, Any]:
    ob = orderbook.get("orderbook", {})
    yes_levels = ob.get("yes", []) or []
    no_levels = ob.get("no", []) or []

    def level_usd(levels: list) -> float:
        return sum((price / 100.0) * qty for price, qty in levels)

    yes_total = level_usd(yes_levels)
    no_total = level_usd(no_levels)
    combined = yes_total + no_total

    best_yes = max((p for p, _ in yes_levels), default=None) if yes_levels else None
    best_no = max((p for p, _ in no_levels), default=None) if no_levels else None

    live_pct = (LIVE_CAP_USD / combined * 100) if combined > 0 else None
    live_flag = live_pct is not None and (live_pct / 100) > DEPTH_IMPACT_THRESHOLD_PCT

    return {
        "yes_depth_usd": round(yes_total, 2),
        "no_depth_usd": round(no_total, 2),
        "combined_depth_usd": round(combined, 2),
        "best_yes_cents": best_yes,
        "best_no_cents": best_no,
        "yes_levels": len(yes_levels),
        "no_levels": len(no_levels),
        "live_cap_pct_of_depth": round(live_pct, 1) if live_pct else None,
        "live_impact_flag": live_flag,
    }


def print_market_report(ticker: str, status: str, close_time: str | None, metrics: dict[str, Any]) -> None:
    print(f"\n  {ticker}  [status={status}, close={close_time}]")
    print(f"    YES depth: ${metrics['yes_depth_usd']:.2f}  ({metrics['yes_levels']} levels, best {metrics['best_yes_cents']}c)")
    print(f"    NO  depth: ${metrics['no_depth_usd']:.2f}  ({metrics['no_levels']} levels, best {metrics['best_no_cents']}c)")
    print(f"    Combined:  ${metrics['combined_depth_usd']:.2f}")
    live_str = f"{metrics['live_cap_pct_of_depth']:.1f}%" if metrics["live_cap_pct_of_depth"] else "N/A"
    flag = " *** IMPACT FLAG ***" if metrics["live_impact_flag"] else ""
    print(f"    Live cap (${LIVE_CAP_USD}) = {live_str} of depth{flag}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query KXMLBHIT orderbook depth — T-377/GG-045")
    parser.add_argument("--ticker", help="Query a single known ticker")
    parser.add_argument("--all", action="store_true", help="Fetch all open KXMLBHIT markets")
    parser.add_argument("--limit", type=int, default=30, help="Max markets to query in --all mode")
    args = parser.parse_args()

    client = KalshiMarketClient.from_env()
    results: list[dict[str, Any]] = []
    tickers_to_query: list[tuple[str, str, str | None]] = []  # (ticker, status, close_time)

    if args.ticker:
        tickers_to_query = [(args.ticker, "unknown", None)]
    else:
        print("Fetching open KXMLBHIT markets from Kalshi...", flush=True)
        try:
            ok, snapshot = client.fetch_player_points_markets(
                status="open", series_ticker=SERIES_MLB_PLAYER_HITS
            )
            if not ok or not snapshot.markets:
                print("No open KXMLBHIT markets found.")
                sys.exit(0)
            for m in snapshot.markets[: args.limit]:
                status = getattr(m, "status", "unknown")
                close_time = getattr(m, "close_time", None)
                tickers_to_query.append((m.ticker, status, str(close_time) if close_time else None))
            print(f"Found {len(snapshot.markets)} open markets. Querying {len(tickers_to_query)}.")
        except Exception as exc:
            print(f"ERROR fetching markets: {exc}")
            sys.exit(1)

    print(f"\n{SEPARATOR}")
    print(f"KXMLBHIT ORDERBOOK DEPTH QUERY — {datetime.now(timezone.utc).isoformat()}")
    print(f"T-377 / GG-045  |  Live cap: ${LIVE_CAP_USD}")
    print(SEPARATOR)

    for ticker, status, close_time in tickers_to_query:
        raw = fetch_orderbook(client, ticker)
        if raw is None:
            results.append({"ticker": ticker, "status": status, "close_time": close_time, "metrics": None, "error": True})
            continue
        metrics = compute_depth_metrics(raw)
        print_market_report(ticker, status, close_time, metrics)
        results.append({
            "ticker": ticker,
            "status": status,
            "close_time": close_time,
            "metrics": metrics,
            # Raw levels preserved for top-of-book/side-split analysis —
            # combined_depth_usd alone overstates fillable size for the
            # GG-045 stake-cap question (both sides, all levels summed).
            "raw_orderbook": raw.get("orderbook"),
            "error": False,
        })

    valid = [r for r in results if r.get("metrics")]
    nonzero = [r for r in valid if r["metrics"]["combined_depth_usd"] > 0]
    print(f"\n{SEPARATOR}")
    print("AGGREGATE SUMMARY")
    print(SEPARATOR)
    print(f"  Markets sampled:        {len(valid)}")
    print(f"  Markets with nonzero depth: {len(nonzero)}")
    if nonzero:
        avg_combined = sum(r["metrics"]["combined_depth_usd"] for r in nonzero) / len(nonzero)
        print(f"  Avg combined depth (nonzero only): ${avg_combined:.2f}")
    else:
        print("  WARNING: all sampled markets returned zero depth.")
        print("  Per GG-041 precedent, this likely means markets are not yet")
        print("  genuinely open/liquid (pre-market) — re-run during a live game window.")

    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"orderbook_depth_mlb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    audit = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "T-377",
        "governance_gap": "GG-045",
        "live_cap_usd": LIVE_CAP_USD,
        "impact_threshold_pct": DEPTH_IMPACT_THRESHOLD_PCT,
        "results": results,
    }
    log_path.write_text(json.dumps(audit, indent=2))
    print(f"\n  Audit log: {log_path}")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    main()

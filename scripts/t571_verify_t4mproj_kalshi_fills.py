#!/usr/bin/env python3
"""T-571: read-only Kalshi order/fill verification for the T4M-PROJ clean cohort.

Applies GG-297's phantom-fill test (per-order GET /portfolio/orders/{order_id})
to every epoch-12 T4M-PROJ closed row in the live ledger, not just the 2026-09-22
rows GG-297 originally covered. Reports three counts, never collapsing "cannot
verify" into "verified":
  - FILLED        : Kalshi order status indicates a real fill (fill_count > 0)
  - CANCELED       : Kalshi order status is canceled/expired with zero fill
  - NOT_RETRIEVABLE: Kalshi returned 404 / an error / an unrecognized shape

Read-only. Never submits, cancels, or modifies an order. Explicitly passes
authenticated=True on every call (T-556: _get() defaults to authenticated=False,
which resolves to PRODUCTION regardless of BOT_ENV).

Run on the VPS (credentials only live there):
    cd /opt/prediction-market-bot
    PYTHONPATH=src python3 /tmp/t571_verify_t4mproj_kalshi_fills.py \
        --portfolio logs/paper_portfolio_mlb_t4.json \
        --out /tmp/t571_kalshi_verification_results.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from prediction_market_bot.c5_execution.kalshi_client import (  # noqa: E402
    KalshiMarketClient,
)
from prediction_market_bot import logic_epoch as le  # noqa: E402


def load_t4mproj_clean_closed(portfolio_path: Path) -> list[dict]:
    with open(portfolio_path) as f:
        portfolio = json.load(f)
    closed = portfolio.get("closed_positions", [])
    rows = [
        p for p in closed
        if p.get("band") == "T4M-PROJ" and le.is_clean_for_band(p.get("logic_epoch"), "T4M-PROJ")
    ]
    return rows


def check_order(client: KalshiMarketClient, order_id: str) -> dict:
    """Single-order lookup via GET /portfolio/orders/{order_id}, authenticated=True."""
    if not order_id:
        return {"verdict": "NOT_RETRIEVABLE", "reason": "no kalshi_order_id on row"}
    ok, data = client._get(f"/portfolio/orders/{order_id}", authenticated=True)
    if not ok:
        return {"verdict": "NOT_RETRIEVABLE", "reason": str(data)[:300]}
    order = data.get("order", data) if isinstance(data, dict) else None
    if not isinstance(order, dict):
        return {"verdict": "NOT_RETRIEVABLE", "reason": f"unrecognized response shape: {str(data)[:200]}"}
    status = order.get("status")
    fill_count_fp = order.get("fill_count_fp") or order.get("fill_count")
    try:
        filled = float(fill_count_fp) if fill_count_fp is not None else 0.0
    except (TypeError, ValueError):
        filled = 0.0
    if filled > 0:
        verdict = "FILLED"
    elif status in ("canceled", "cancelled", "expired"):
        verdict = "CANCELED"
    elif status in ("resting", "open"):
        verdict = "NOT_RETRIEVABLE"  # still resting at check time -- not a terminal state either way
    else:
        verdict = "NOT_RETRIEVABLE"
    return {"verdict": verdict, "status": status, "fill_count_fp": fill_count_fp}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sleep", type=float, default=0.15, help="seconds between requests (rate-limit courtesy)")
    args = ap.parse_args()

    client = KalshiMarketClient.from_env()
    if not client.has_signing_key():
        print("ERROR: No RSA signing key loaded. Set VENUE_PRIVATE_KEY_PATH.", file=sys.stderr)
        sys.exit(1)

    rows = load_t4mproj_clean_closed(args.portfolio)
    print(f"loaded {len(rows)} epoch-12 T4M-PROJ clean closed rows from {args.portfolio}")

    results = []
    counts = {"FILLED": 0, "CANCELED": 0, "NOT_RETRIEVABLE": 0}
    for i, row in enumerate(rows):
        order_id = row.get("kalshi_order_id")
        check = check_order(client, order_id)
        verdict = check["verdict"]
        counts[verdict] += 1
        results.append({
            "position_id": row.get("position_id"),
            "kalshi_order_id": order_id,
            "game_date": row.get("game_date"),
            "logic_epoch": row.get("logic_epoch"),
            "pnl_recorded": row.get("pnl"),
            "outcome_recorded": row.get("outcome"),
            **check,
        })
        if (i + 1) % 25 == 0:
            print(f"  ... {i + 1}/{len(rows)} checked ({counts})")
        time.sleep(args.sleep)

    out = {
        "n_checked": len(rows),
        "counts": counts,
        "results": results,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"wrote {args.out}")
    print(f"FINAL COUNTS: {counts}")


if __name__ == "__main__":
    main()

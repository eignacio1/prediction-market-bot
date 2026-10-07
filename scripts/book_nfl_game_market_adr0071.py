#!/usr/bin/env python3
"""GG-490 / W58.1 Part C: one-time ADR-0071 booking of the retired NFL game-market paper book.

Settles every OPEN position in a portfolio file from Kalshi's own settlement
(ADR-0071) via PaperTrader.settle_position_from_venue. Cancelled markets are
booked at Kalshi's settlement value, flagged cancelled, and excluded from G6 /
calibration by existing consumers. Positions whose market is not final (or whose
state cannot be confirmed) are LEFT OPEN and reported -- never guessed.

Default is a PLAN: Kalshi is queried, nothing is written. --apply writes to the
file named by --portfolio (point it at a COPY for a dry run). Audit events go to
--audit (default: beside the portfolio, so a copy run never touches the live log).

Usage:
    PYTHONPATH=src python3 scripts/book_nfl_game_market_adr0071.py --portfolio P [--apply] [--audit A] [--report R]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.run_resolve_mlb import (
    VENUE_CANCELLED,
    VENUE_SETTLED,
    _settlement_value,
    _venue_market_state,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--portfolio", required=True, type=Path)
    ap.add_argument("--audit", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    audit = args.audit or args.portfolio.with_suffix(".booking_audit.jsonl")
    trader = PaperTrader(args.portfolio, AuditLogger(audit, min_severity="INFO"))
    before = trader.get_state()
    open_pos = [p for p in before["open_positions"] if p.get("status") == "OPEN"]
    print(f"mode={'APPLY' if args.apply else 'PLAN'} portfolio={args.portfolio} open={len(open_pos)}")

    cache: dict[str, tuple[str, dict]] = {}
    plan, skipped = [], []
    for p in open_pos:
        t = p.get("kalshi_ticker") or ""
        if t not in cache:
            cache[t] = _venue_market_state(t)
            time.sleep(0.15)
        state, raw = cache[t]
        if state == VENUE_SETTLED:
            plan.append((p, str(raw["result"]).lower(), None))
        elif state == VENUE_CANCELLED:
            v = _settlement_value(raw)
            if v is None:
                skipped.append((p, "cancelled_no_value"))
            else:
                plan.append((p, "scalar", v))
        else:
            skipped.append((p, state))

    print(f"tickers queried={len(cache)} bookable={len(plan)} left_open={len(skipped)}")
    print("left_open reasons:", dict(Counter(r for _, r in skipped)))
    results = Counter(r for _, r, _ in plan)
    print("venue results:", dict(results))

    booked = 0
    if args.apply:
        for p, res, val in plan:
            ok, _ = trader.settle_position_from_venue(p["position_id"], res, val)
            booked += 1 if ok else 0
        print(f"booked={booked}")

    after = trader.get_state()
    report = {
        "applied": args.apply,
        "open_before": len(open_pos),
        "bookable": len(plan),
        "booked": booked,
        "left_open": [
            {"position_id": p["position_id"], "ticker": p.get("kalshi_ticker"),
             "game_date": p.get("game_date"), "reason": r} for p, r in skipped],
        "venue_results": dict(results),
        "cancelled": sum(1 for _, r, _ in plan if r == "scalar"),
        "bankroll_before": before["bankroll_usd"],
        "bankroll_after": after["bankroll_usd"],
        "realized_before": before["total_realized_pnl"],
        "realized_after": after["total_realized_pnl"],
        "closed_before": len(before["closed_positions"]),
        "closed_after": len(after["closed_positions"]),
        "open_after": len(after["open_positions"]),
    }
    print(json.dumps({k: v for k, v in report.items() if k != "left_open"}, indent=2))
    if args.report:
        args.report.write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

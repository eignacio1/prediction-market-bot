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
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.position_sweep import sweep_open_positions


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--portfolio", required=True, type=Path)
    ap.add_argument("--audit", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    audit = args.audit or args.portfolio.with_suffix(".booking_audit.jsonl")
    report = sweep_open_positions(args.portfolio, audit, apply=args.apply)
    print(f"mode={'APPLY' if args.apply else 'PLAN'} portfolio={args.portfolio} "
          f"open={report['open_before']} bookable={report['bookable']} booked={report['booked']} "
          f"not_final={len(report['not_final'])} alarms={len(report['alarms'])}")
    print(json.dumps({k: v for k, v in report.items() if k not in ("alarms", "not_final")}, indent=2))
    for a in report["alarms"]:
        print("ALARM LOOKUP_FAILED:", json.dumps(a), file=sys.stderr)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

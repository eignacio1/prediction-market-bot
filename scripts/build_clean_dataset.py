#!/usr/bin/env python
"""
build_clean_dataset.py — emit the NBA Finals paper-trading clean dataset (T-174 WS2)
====================================================================================
Reconstructs every paper bet (open + closed) from a portfolio JSON into one
auditable CSV with contamination LABELED (not dropped), plus a printed summary
splitting realized P&L into clean vs contaminated and by Finals game.

Ground truth: the position ledger (closed_positions + open_positions). Realized
P&L is derived (Σ pnl + exit_pnl), corroborated by the C6 audit log per GG-034 —
never the corrupted `total_realized_pnl` scalar.

Usage:
    python scripts/build_clean_dataset.py \
        [--portfolio logs/.vps_portfolio_cache.json] \
        [--out data/nba_finals_clean_dataset.csv]

Default input is the pulled-down live VPS book cache. Read-only on the ledger.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prediction_market_bot.analytics.clean_dataset import build_dataset, to_csv


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--portfolio", default="logs/.vps_portfolio_cache.json",
                    help="Portfolio JSON to extract (default: live VPS book cache)")
    ap.add_argument("--out", default="data/nba_finals_clean_dataset.csv",
                    help="CSV output path")
    ap.add_argument("--summary-json", default=None,
                    help="Optional path to also write the summary as JSON")
    args = ap.parse_args()

    portfolio_path = Path(args.portfolio)
    if not portfolio_path.exists():
        print(f"ERROR: portfolio not found: {portfolio_path}", file=sys.stderr)
        return 1

    rows, summary = build_dataset(portfolio_path)
    out = to_csv(rows, Path(args.out))

    print(f"Source ledger : {portfolio_path}")
    print(f"CSV written   : {out}  ({len(rows)} bets)")
    print()
    print("=== Realized P&L (closed bets only) ===")
    print(f"  total         : {summary['realized_pnl_total']:>12.4f}")
    print(f"  clean         : {summary['realized_pnl_clean']:>12.4f}")
    print(f"  contaminated  : {summary['realized_pnl_contaminated']:>12.4f}")
    print()
    print(f"=== Bet counts ===")
    print(f"  total {summary['n_bets_total']} | open {summary['n_open']} | "
          f"closed {summary['n_closed']} | clean {summary['n_clean']} | "
          f"contaminated {summary['n_contaminated']}")
    print()
    print("=== Contamination reasons (a bet may carry several) ===")
    for reason, n in summary["contamination_reasons"].items():
        print(f"  {reason:<22} {n}")
    print()
    print("=== By Finals game ===")
    print(f"  {'game':<8}{'total':>7}{'closed':>8}{'clean':>7}{'contam':>8}{'realized_pnl':>15}")
    for game, b in summary["by_finals_game"].items():
        print(f"  {game:<8}{b['n_total']:>7}{b['n_closed']:>8}{b['n_clean']:>7}"
              f"{b['n_contaminated']:>8}{b['realized_pnl']:>15.4f}")

    if args.summary_json:
        Path(args.summary_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.summary_json).write_text(json.dumps(summary, indent=2))
        print(f"\nSummary JSON  : {args.summary_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

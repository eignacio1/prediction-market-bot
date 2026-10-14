"""
Reset paper_portfolio.json to $1,000 clean state.

Usage (VPS):
    BOT_ENV=paper PYTHONPATH=src python3 \
        src/prediction_market_bot/reset_paper_portfolio.py [--confirm]

Safety: requires --confirm flag to overwrite. Prints current state first.
Decision: logged in DECISION_LOG.md 2026-06-02 (G1 portfolio tainted by GG-008).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from prediction_market_bot.atomic_io import atomic_write_json

LOG_DIR = Path("logs")
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio.json"
INITIAL_BANKROLL = 1000.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset paper_portfolio.json to $1,000")
    parser.add_argument("--confirm", action="store_true",
                        help="Required flag to perform the overwrite")
    parser.add_argument("--path", default=str(PORTFOLIO_PATH),
                        help=f"Portfolio path (default: {PORTFOLIO_PATH})")
    args = parser.parse_args()

    path = Path(args.path)

    if path.exists():
        try:
            current = json.loads(path.read_text())
            print("Current portfolio state:")
            print(f"  bankroll_usd:        {current.get('bankroll_usd', 'N/A')}")
            print(f"  initial_bankroll:    {current.get('initial_bankroll_usd', 'N/A')}")
            print(f"  total_realized_pnl:  {current.get('total_realized_pnl', 'N/A')}")
            print(f"  open_positions:      {len(current.get('open_positions', []))}")
            print(f"  closed_positions:    {len(current.get('closed_positions', []))}")
            print(f"  last_updated:        {current.get('last_updated', 'N/A')}")
        except Exception as e:
            print(f"  [WARN] Could not read current portfolio: {e}")
    else:
        print(f"No existing portfolio at {path}")

    if not args.confirm:
        print("\nDry run — pass --confirm to overwrite.")
        return

    fresh = {
        "bankroll_usd": INITIAL_BANKROLL,
        "initial_bankroll_usd": INITIAL_BANKROLL,
        "total_realized_pnl": 0.0,
        "current_daily_loss": 0.0,
        "daily_loss_date": _today(),
        "open_positions": [],
        "closed_positions": [],
        "created_at": _utc_now(),
        "last_updated": _utc_now(),
        "_reset_reason": "GG-008: G1 portfolio tainted by phantom edge (all-threshold loop misspecification). Clean slate for Path B (Poisson CDF) corrected architecture.",
        "_reset_date": "2026-06-02",
        "_reset_session": "Session 14",
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, fresh, indent=2)
    print(f"\nPortfolio reset to ${INITIAL_BANKROLL:.2f} at {path}")
    print("G6 counter reset: 0/30 resolved bets. Clean slate begins Finals G2.")


if __name__ == "__main__":
    main()

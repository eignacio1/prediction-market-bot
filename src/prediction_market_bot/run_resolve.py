"""
PIPE-03R: Paper Position Resolution
=====================================
Pipeline:     PIPE-03R (Resolution-only; companion to PIPE-03)
Phase:        Phase 6 (ENV-02 — paper trading)
Schedule:     Cron: 06:00 UTC daily (2am ET) — after all games finish
Environment:  ENV-02 — BOT_ENV=paper required

Purpose:
  PIPE-03 places bets at 22:00 UTC and 01:30 UTC. Late games (10pm+ ET)
  finish around 02:00–03:00 UTC — after both PIPE-03 runs. This script
  runs at 06:00 UTC to resolve any positions whose game results are now
  available from nba_api.

  Does NOT place new bets. Does NOT fetch live markets.
  Resolution-only: safe to run at any time without side effects.

Why separate from PIPE-03:
  Keeping resolution separate prevents late-game stats from being confused
  with the bet-placement logic and keeps the P&L audit trail clean.
  Each open position is resolved exactly once; subsequent resolution
  attempts on already-closed positions are no-ops.

How to run:
  BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

if os.environ.get("BOT_ENV", "").lower() != "paper":
    print("FATAL: PIPE-03R requires BOT_ENV=paper.", file=sys.stderr)
    sys.exit(1)

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

SESSION_ID     = f"RESOLVE-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE      = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
LOG_DIR        = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio.json"
SNAPSHOT_ID    = "SNAP-2026-05-28-002"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger  = AuditLogger(LOG_DIR / "audit.jsonl", min_severity="INFO")
    trader  = PaperTrader(PORTFOLIO_PATH, logger)

    portfolio = trader.get_state()
    n_open    = len(portfolio.get("open_positions", []))

    print(f"\n[PIPE-03R] Resolution run — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")
    print(f"Open positions: {n_open}")

    logger.info("PIPE-03R", "resolve_run_start",
                payload={"session_id": SESSION_ID, "open_positions": n_open,
                         "game_date": GAME_DATE},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    if n_open == 0:
        print("[RESOLVE] No open positions — nothing to do.")
        logger.info("PIPE-03R", "resolve_run_complete",
                    payload={"resolved": 0, "still_open": 0},
                    session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)
        return

    ok, resolved = trader.resolve_pending(session_id=SESSION_ID)

    if resolved:
        print(f"\n[RESOLVE] {len(resolved)} position(s) settled:")
        for r in resolved:
            sign  = "+" if r["pnl"] >= 0 else ""
            emoji = "WIN" if r["pnl"] > 0 else ("LOSS" if r["pnl"] < 0 else "PUSH")
            print(f"  {r['player_name']:<22} {emoji}  "
                  f"pts={r['actual_pts']:.0f} vs {r['kalshi_threshold']}+  "
                  f"P&L={sign}{r['pnl']:.2f}")
    else:
        print("[RESOLVE] No positions settled yet — game results not available.")

    still_open = len(trader.get_state().get("open_positions", []))
    summary    = trader.summary()

    print(f"\n[SUMMARY]")
    print(f"  Resolved this run:  {len(resolved) if resolved else 0}")
    print(f"  Still open:         {still_open}")
    print(f"  Bankroll:           ${summary['bankroll_usd']:.2f}")
    print(f"  Total realized P&L: ${summary['total_realized_pnl']:+.2f}")
    if summary["win_rate"] is not None:
        print(f"  Win rate:           {summary['win_rate']:.1%}  "
              f"({summary['closed_positions']} resolved bets)")
    print(f"  Drawdown:           {summary['drawdown_pct']:.1f}%")

    logger.info("PIPE-03R", "resolve_run_complete",
                payload={
                    "resolved":           len(resolved) if resolved else 0,
                    "still_open":         still_open,
                    "bankroll":           summary["bankroll_usd"],
                    "total_realized_pnl": summary["total_realized_pnl"],
                    "win_rate":           summary["win_rate"],
                },
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)


if __name__ == "__main__":
    main()

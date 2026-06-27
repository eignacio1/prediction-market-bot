"""
PIPE-05R: MLB Paper Position Resolution
=========================================
Pipeline:     PIPE-05R (Resolution-only; companion to PIPE-05)
Phase:        Phase 6 (ENV-02 — paper trading)
Schedule:     Cron: 06:30 UTC daily — after all MLB games finish
              (West Coast games end ~04:00–05:00 UTC; 90-min buffer)
Environment:  ENV-02 — BOT_ENV=paper required

Purpose:
  PIPE-05 places bets at 11:00 UTC. MLB games finish by ~04:00–05:00 UTC.
  This script runs at 06:30 UTC to resolve open MLB positions using the
  MLB Stats API (statsapi.mlb.com).

  Does NOT place new bets. Does NOT fetch live markets.
  Resolution-only: safe to run at any time without side effects.

Why separate from PIPE-05:
  Keeps resolution and bet-placement concerns clean. Each open position
  resolves exactly once (idempotent via settle_position() no-op guard).

VPS accessibility:
  MLB Stats API is accessible from DigitalOcean (157.230.91.33) for the
  current season (2026). Historical seasons ≤2025 are Fastly-CDN-blocked from
  datacenter IPs (HTTP 406). If re-running resolve for 2024/2025 data,
  run this script locally instead. See SESSION 81 DECISION_LOG.

How to run:
  BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_mlb.py

Season type handling:
  Regular season (gameType="R") is attempted first for all game dates.
  Postseason (gameType="P") is tried if Regular Season returns no result —
  mirrors NBA resolve_pending() Playoffs fallback pattern.
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import requests

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

if os.environ.get("BOT_ENV", "").lower() != "paper":
    print("FATAL: PIPE-05R requires BOT_ENV=paper.", file=sys.stderr)
    sys.exit(1)

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor

SESSION_ID     = f"RESOLVE-MLB-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE      = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
LOG_DIR        = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_mlb.json"
SNAPSHOT_ID    = "SNAP-MLB-T187E"

_MLB_BASE_URL  = "https://statsapi.mlb.com"
_RATE_LIMIT_S  = 0.6   # matches mlb_ingestion.py; stays under API rate limit
_REQUEST_TIMEOUT_S = 15


# ---------------------------------------------------------------------------
# MLB Stats API fetch
# ---------------------------------------------------------------------------

def _fetch_mlb_hits(
    player_id: int,
    game_date: str,
    game_type: str = "R",
) -> float | None:
    """Fetch actual hits for player_id on game_date from MLB Stats API.

    game_date: YYYY-MM-DD
    game_type: "R" (Regular) or "P" (Postseason)
    Returns hits as float, or None if game not found or API unreachable.
    """
    year = int(game_date[:4])
    url = f"{_MLB_BASE_URL}/api/v1/people/{player_id}/stats"
    params = {
        "stats":   "gameLog",
        "group":   "hitting",
        "season":  str(year),
        "gameType": game_type,
    }
    try:
        time.sleep(_RATE_LIMIT_S)
        resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
        stats_arr = data.get("stats", [])
        if not stats_arr:
            return None
        splits = stats_arr[0].get("splits", [])
        for split in splits:
            if split.get("date", "") == game_date:
                return float(split.get("stat", {}).get("hits", 0))
    except Exception as exc:
        print(
            f"  [MLB-API] player_id={player_id} game_date={game_date} "
            f"game_type={game_type}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
    return None


def fetch_actual_hits(player_id: int, game_date: str) -> float | None:
    """Fetch actual hits with Postseason fallback.

    Tries Regular Season first; if no result, tries Postseason.
    Mirrors NBA resolve_pending() Playoffs fallback pattern.
    """
    hits = _fetch_mlb_hits(player_id, game_date, game_type="R")
    if hits is None:
        hits = _fetch_mlb_hits(player_id, game_date, game_type="P")
    return hits


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")
    trader = PaperTrader(PORTFOLIO_PATH, logger)

    portfolio = trader.get_state()
    open_positions = portfolio.get("open_positions", [])
    n_open = len(open_positions)

    print(f"\n[PIPE-05R] MLB resolution run — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")
    print(f"Open positions: {n_open}")

    logger.info("PIPE-05R", "resolve_run_start",
                payload={"session_id": SESSION_ID, "open_positions": n_open,
                         "game_date": GAME_DATE},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    if n_open == 0:
        print("[RESOLVE] No open MLB positions — nothing to do.")
        logger.info("PIPE-05R", "resolve_run_complete",
                    payload={"resolved": 0, "still_open": 0},
                    session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)
        return

    today = date.today().isoformat()
    pending = [
        p for p in open_positions
        if p.get("game_date", today) < today
    ]

    if not pending:
        print(f"[RESOLVE] {n_open} open position(s) — all game dates are today or future. "
              f"No resolutions yet.")
        logger.info("PIPE-05R", "resolve_run_complete",
                    payload={"resolved": 0, "still_open": n_open},
                    session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)
        return

    print(f"[RESOLVE] {len(pending)} position(s) eligible (game_date < {today})...")

    resolved = []

    for pos in pending:
        player_id   = int(pos.get("player_id", 0))
        player_name = pos.get("player_name", "unknown")
        game_date   = pos.get("game_date", "")
        threshold   = int(pos.get("kalshi_threshold", 0))
        direction   = pos.get("direction", "YES")
        position_id = pos.get("position_id", "")

        actual_hits = fetch_actual_hits(player_id, game_date)

        if actual_hits is None:
            try:
                game_dt_utc = datetime.strptime(game_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                age_hours = (datetime.now(timezone.utc) - game_dt_utc).total_seconds() / 3600
            except ValueError:
                age_hours = 0.0

            if age_hours > 48:
                trader.mark_aged_open(
                    position_id=position_id,
                    reason="api_no_result_48h",
                    session_id=SESSION_ID,
                )
                print(
                    f"  [AGED] {player_name:<24} — no MLB API result after "
                    f"{age_hours:.0f}h (>48h) — tagged aged_open",
                    file=sys.stderr,
                )
            else:
                logger.warning(
                    "PIPE-05R", "player_stats_fetch_failed",
                    payload={
                        "player_id": player_id,
                        "player_name": player_name,
                        "game_date": game_date,
                        "position_id": position_id,
                        "age_hours": round(age_hours, 1),
                        "note": "MLB Stats API returned no result — position stays open",
                    },
                    session_id=SESSION_ID,
                )
                print(f"  [SKIP] {player_name:<24} — no MLB API result for {game_date} "
                      f"({age_hours:.0f}h old — within 48h grace period)")
            continue

        ok, closed_pos = trader.settle_position(
            position_id=position_id,
            actual_stat=actual_hits,
            stat_label="actual_hits",
            session_id=SESSION_ID,
        )

        if closed_pos:
            pnl     = closed_pos.get("pnl", 0.0)
            outcome = closed_pos.get("outcome", "?")
            sign    = "+" if pnl >= 0 else ""
            label   = "WIN " if outcome == "WIN" else "LOSS"
            print(f"  {player_name:<24} {label}  "
                  f"hits={actual_hits:.0f} vs H≥{threshold}  "
                  f"dir={direction}  P&L={sign}{pnl:.2f}")
            resolved.append(closed_pos)

        if not ok:
            logger.warning(
                "PIPE-05R", "settle_position_partial_failure",
                payload={"position_id": position_id, "player_name": player_name},
                session_id=SESSION_ID,
            )

    still_open = len(trader.get_state().get("open_positions", []))
    summary    = trader.summary()

    if not resolved:
        print("[RESOLVE] No positions settled yet — MLB API results not available.")
    else:
        print(f"\n[SUMMARY]")
        print(f"  Resolved this run:  {len(resolved)}")
        print(f"  Still open:         {still_open}")
        print(f"  Bankroll:           ${summary['bankroll_usd']:.2f}")
        print(f"  Total realized P&L: ${summary['total_realized_pnl']:+.2f}")
        if summary["win_rate"] is not None:
            print(f"  Win rate:           {summary['win_rate']:.1%}  "
                  f"({summary['closed_positions']} resolved bets)")
        print(f"  Realized drawdown:  {summary['realized_drawdown_pct']:.1f}%")
        print(f"  Deployed (stakes):  {summary['deployed_pct']:.1f}%")

    SystemMonitor(
        logger=logger, snapshot_id=SNAPSHOT_ID, session_id=SESSION_ID
    ).check_portfolio_pnl(
        total_realized_pnl=summary["total_realized_pnl"],
        initial_bankroll=summary["initial_bankroll_usd"],
        session_id=SESSION_ID,
    )

    logger.info("PIPE-05R", "resolve_run_complete",
                payload={
                    "resolved":           len(resolved),
                    "still_open":         still_open,
                    "bankroll":           summary["bankroll_usd"],
                    "total_realized_pnl": summary["total_realized_pnl"],
                    "win_rate":           summary["win_rate"],
                },
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)


if __name__ == "__main__":
    main()

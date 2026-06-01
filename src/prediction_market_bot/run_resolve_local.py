"""
PIPE-03R-LOCAL: Paper Position Resolution (Local Machine)
=========================================================
Pipeline:     PIPE-03R-LOCAL (companion to PIPE-03R on VPS)
Phase:        Phase 6 (ENV-02 — paper trading)
Environment:  BOT_ENV=paper required
Schedule:     Run manually after each game day, or add a local cron.

Why this exists:
  stats.nba.com returns 403 Forbidden for datacenter IPs (DigitalOcean,
  AWS, etc.). run_resolve.py on the VPS silently gets 0 resolutions every
  run. This script runs locally — where stats.nba.com is reachable — and
  syncs the resolved portfolio back to the VPS.

What it does:
  1. Pull paper_portfolio.json from VPS via SCP.
  2. Run PaperTrader.resolve_pending() locally.
  3. If any positions resolved, push the updated portfolio back to VPS.
  4. Append the local audit log entries to the VPS audit.jsonl.
  5. Print a summary.

How to run:
  BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py

Requirements:
  - SSH key at ~/.ssh/id_ed25519_droplet with access to the VPS
  - nba_api reachable from local machine (not blocked)
  - BOT_ENV=paper set
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

if os.environ.get("BOT_ENV", "").lower() != "paper":
    print("FATAL: PIPE-03R-LOCAL requires BOT_ENV=paper.", file=sys.stderr)
    sys.exit(1)

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

VPS_HOST      = "root@157.230.91.33"
VPS_KEY       = Path.home() / ".ssh" / "id_ed25519_droplet"
VPS_PORTFOLIO = "/opt/prediction-market-bot/logs/paper_portfolio.json"
VPS_AUDIT     = "/opt/prediction-market-bot/logs/audit.jsonl"

SESSION_ID  = f"RESOLVE-LOCAL-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE   = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
SNAPSHOT_ID = "SNAP-2026-05-28-002"

_SSH_OPTS = ["-i", str(VPS_KEY), "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15"]


def _scp_pull(remote: str, local: Path) -> None:
    subprocess.run(
        ["scp"] + _SSH_OPTS + [f"{VPS_HOST}:{remote}", str(local)],
        check=True, capture_output=True,
    )


def _scp_push(local: Path, remote: str) -> None:
    subprocess.run(
        ["scp"] + _SSH_OPTS + [str(local), f"{VPS_HOST}:{remote}"],
        check=True, capture_output=True,
    )


def _ssh_append(local_file: Path, remote_path: str) -> None:
    content = local_file.read_bytes()
    if not content.strip():
        return
    subprocess.run(
        ["ssh"] + _SSH_OPTS + [VPS_HOST, f"cat >> {remote_path}"],
        input=content, check=True, capture_output=True,
    )


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp(prefix="resolve_local_"))
    local_portfolio = tmpdir / "paper_portfolio.json"
    local_audit     = tmpdir / "audit_local.jsonl"

    try:
        print(f"\n[PIPE-03R-LOCAL] Resolution run — {GAME_DATE}")
        print(f"Session:  {SESSION_ID}")
        print(f"BOT_ENV:  {os.environ.get('BOT_ENV')}  |  source: local machine")

        # 1. Pull portfolio from VPS
        print("\n[PULL] Fetching portfolio from VPS...")
        try:
            _scp_pull(VPS_PORTFOLIO, local_portfolio)
            print(f"  OK — {local_portfolio.stat().st_size} bytes")
        except subprocess.CalledProcessError as e:
            print(f"  FAILED: {e.stderr.decode().strip()}", file=sys.stderr)
            sys.exit(1)

        # 2. Resolve locally
        logger = AuditLogger(local_audit, min_severity="INFO")
        trader = PaperTrader(local_portfolio, logger)

        portfolio = trader.get_state()
        n_open    = len(portfolio.get("open_positions", []))
        print(f"\n[RESOLVE] {n_open} open position(s) to attempt...")

        logger.info("PIPE-03R-LOCAL", "resolve_run_start",
                    payload={"session_id": SESSION_ID, "open_positions": n_open,
                             "game_date": GAME_DATE},
                    session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

        if n_open == 0:
            print("[RESOLVE] No open positions — nothing to do.")
            return

        ok, resolved = trader.resolve_pending(session_id=SESSION_ID)

        if resolved:
            print(f"\n  {len(resolved)} position(s) settled:")
            for r in resolved:
                sign  = "+" if r["pnl"] >= 0 else ""
                emoji = "WIN" if r["pnl"] > 0 else ("LOSS" if r["pnl"] < 0 else "PUSH")
                print(f"  {r['player_name']:<24} {emoji:<5}  "
                      f"pts={r['actual_pts']:.0f} vs {r['kalshi_threshold']}+  "
                      f"P&L={sign}{r['pnl']:.2f}")
        else:
            print("  No positions resolved — game results not yet available from nba_api.")

        summary = trader.summary()
        print(f"\n[SUMMARY]")
        print(f"  Resolved this run:  {len(resolved) if resolved else 0}")
        print(f"  Still open:         {summary['open_positions']}")
        print(f"  Bankroll:           ${summary['bankroll_usd']:.2f}")
        print(f"  Total realized P&L: ${summary['total_realized_pnl']:+.2f}")
        if summary["win_rate"] is not None:
            print(f"  Win rate:           {summary['win_rate']:.1%}  "
                  f"({summary['closed_positions']} resolved bets)")
        print(f"  Realized drawdown:  {summary['realized_drawdown_pct']:.1f}%")
        print(f"  Deployed (stakes):  {summary['deployed_pct']:.1f}%")

        logger.info("PIPE-03R-LOCAL", "resolve_run_complete",
                    payload={
                        "resolved":           len(resolved) if resolved else 0,
                        "still_open":         summary["open_positions"],
                        "bankroll":           summary["bankroll_usd"],
                        "total_realized_pnl": summary["total_realized_pnl"],
                        "win_rate":           summary["win_rate"],
                    },
                    session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

        # 3. Push updated portfolio back to VPS (only if something changed)
        if resolved:
            print(f"\n[PUSH] Uploading updated portfolio to VPS...")
            try:
                _scp_push(local_portfolio, VPS_PORTFOLIO)
                print("  OK — portfolio synced.")
            except subprocess.CalledProcessError as e:
                print(f"  FAILED: {e.stderr.decode().strip()}", file=sys.stderr)
                print("  WARNING: Portfolio updated locally but NOT synced to VPS.", file=sys.stderr)
                sys.exit(1)

            # 4. Append local audit entries to VPS audit log
            if local_audit.exists() and local_audit.stat().st_size > 0:
                try:
                    _ssh_append(local_audit, VPS_AUDIT)
                    print("  OK — audit log entries synced.")
                except subprocess.CalledProcessError as e:
                    print(f"  WARNING: Audit log sync failed: {e.stderr.decode().strip()}", file=sys.stderr)
        else:
            print("\n[PUSH] Nothing to sync — no positions resolved.")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()

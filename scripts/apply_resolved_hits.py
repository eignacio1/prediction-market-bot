#!/usr/bin/env python3
"""
T-422 out-of-band repair, apply step. Run ON THE VPS. Takes a JSON file of
already-fetched (player_id, game_date, hits) results — produced by fetching
from a network NOT subject to GG-084's datacenter-IP block (see
scripts/repair_stuck_mlb_positions.py's module docstring and
05_RESEARCH_EXPERIMENTS/ for the full diagnosis) — and calls
PaperTrader.settle_position() for each one that has a real hit count.
Makes zero outbound HTTP calls itself: purely a local JSON read + portfolio
write, so it is not subject to the IP block this repair works around.

Backs up the portfolio file before writing. Idempotent: settle_position()
is itself idempotent (no-op if the position is already closed).

Usage:
    BOT_ENV=paper PYTHONPATH=src python3 scripts/apply_resolved_hits.py \
        resolved_hits.json [--apply]
Default (no --apply) is a dry run: reports what WOULD be settled, writes
nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import prediction_market_bot.run_resolve_mlb as rrm  # noqa: E402
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

SESSION_ID = f"REPAIR-MLB-{uuid.uuid4().hex[:8].upper()}"


def _backup_portfolio(path: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.stem}.pre_repair_{ts}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_file", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    results = json.loads(args.results_file.read_text())
    resolvable = [r for r in results if r.get("hits") is not None]

    portfolio_path = rrm.PORTFOLIO_PATH
    print(f"Portfolio path: {portfolio_path}")
    print(f"Session ID:     {SESSION_ID}")
    print(f"Mode:           {'APPLY (will write)' if args.apply else 'DRY RUN (no writes)'}")
    print(f"{len(results)} position(s) in input file, {len(resolvable)} have a fetched hit count.\n")

    if args.apply and resolvable:
        backup_path = _backup_portfolio(portfolio_path)
        print(f"Backup written: {backup_path}")

    logger = AuditLogger(rrm.LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")
    trader = PaperTrader(portfolio_path, logger)

    settled = []
    for r in resolvable:
        position_id = r["position_id"]
        hits = r["hits"]
        print(f"  {r['player_name']:<20} {r['game_date']}  {position_id}  "
              f"hits={hits}  source={r['source']}")
        if args.apply:
            ok, closed_pos = trader.settle_position(
                position_id=position_id,
                actual_stat=hits,
                stat_label="actual_hits",
                session_id=SESSION_ID,
            )
            if ok and closed_pos:
                pnl = closed_pos.get("pnl", 0.0)
                outcome = closed_pos.get("outcome", "?")
                print(f"    -> settled: outcome={outcome} pnl={pnl:+.2f}")
                settled.append(closed_pos)
            else:
                print(f"    -> settle_position() returned ok={ok} (already settled or not found)")

    print(f"\n--- Summary ---")
    print(f"Resolvable (fetched hits):  {len(resolvable)}")
    print(f"Settled this run:           {len(settled)}")
    if not args.apply:
        print("\nDRY RUN — no writes made. Re-run with --apply to settle these positions.")


if __name__ == "__main__":
    main()

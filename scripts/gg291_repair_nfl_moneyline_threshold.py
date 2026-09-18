#!/usr/bin/env python3
"""
GG-291 / T-562 (2026-09-18) — backfill kalshi_threshold=0.0 on the 42
nfl_moneyline open positions in paper_portfolio_t1_nfl_game_market.json
that were written with kalshi_threshold=null before the Deliverable 2
write-path fix landed.

Root cause: run_t1_nfl_game_market.py / nfl_exp027_adapter.py never wrote
kalshi_threshold; paper_trader.py's open_position() defaulted it to None.
game_market_settlement.py's module docstring states a moneyline is a
spread at zero, so the correct backfilled value is 0.0 -- not a design
choice, a documented fact about the settlement contract.

SCOPE, deliberately narrow (Deliverable 3 instruction; do not extend):
  - open_positions ONLY, market_type == "nfl_moneyline" ONLY,
    kalshi_threshold is None ONLY.
  - Touches exactly three fields per repaired row: `kalshi_threshold`
    (set to 0.0), plus provenance `repaired_at` / `repair_ref`
    (ADR-0055 precedent format).
  - Does NOT touch closed_positions, rejected_positions, any other
    market_type, any position with a non-null threshold, or any scalar
    (bankroll_usd, total_realized_pnl, last_updated, etc -- those are
    recomputed by PaperTrader._save() on its own next write, not by
    this script).
  - If the count of matching rows is not exactly 42 at execution time,
    ABORT and report -- do not repair a different count silently
    (explicit Deliverable 3 instruction).

SAFETY (ADR-0061 / GG-228 precedent):
  - run_t1_nfl_game_market.py is a short-lived, non-systemd, manually
    invoked script (ADR-0061 table row #3) -- the GG-224 flush-revert
    hazard that applies to t4-mlb.service does NOT apply here. This
    script still takes PaperTrader's own fcntl lock (ADR-0061 sec 7,
    adopted as a complementary defensive practice regardless) and uses
    optimistic concurrency control (snapshot -> re-check immediately
    before write) plus a verified backup and an atomic write, matching
    the stronger T-502/GG-224 precedent.

Usage:
    python3 scripts/gg291_repair_nfl_moneyline_threshold.py             # dry run
    python3 scripts/gg291_repair_nfl_moneyline_threshold.py --apply     # write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX fallback
    _HAS_FCNTL = False

REPAIR_REF = "GG-291 / T-562"
TARGET_MARKET_TYPE = "nfl_moneyline"
EXPECTED_COUNT = 42


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_repairs(open_positions: list[dict]) -> list[dict]:
    """Returns repair_plan: [{position_id, ticker}] for every row matching
    market_type == nfl_moneyline AND kalshi_threshold is None."""
    plan = []
    for pos in open_positions:
        if pos.get("market_type") != TARGET_MARKET_TYPE:
            continue
        if pos.get("kalshi_threshold") is not None:
            continue
        plan.append(
            {
                "position_id": pos.get("position_id"),
                "ticker": pos.get("kalshi_ticker"),
            }
        )
    return plan


def apply_repairs(open_positions: list[dict], plan: list[dict], repaired_at: str) -> int:
    ids = {e["position_id"] for e in plan}
    applied = 0
    for pos in open_positions:
        if pos.get("position_id") not in ids:
            continue
        assert pos.get("market_type") == TARGET_MARKET_TYPE
        assert pos.get("kalshi_threshold") is None
        pos["kalshi_threshold"] = 0.0
        pos["repaired_at"] = repaired_at
        pos["repair_ref"] = REPAIR_REF
        applied += 1
    return applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument(
        "--ledger",
        default="/opt/prediction-market-bot/logs/paper_portfolio_t1_nfl_game_market.json",
        help="path to paper_portfolio_t1_nfl_game_market.json",
    )
    ap.add_argument(
        "--expected-count",
        type=int,
        default=EXPECTED_COUNT,
        help=f"abort unless exactly this many rows match (default {EXPECTED_COUNT})",
    )
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(lock_path, "w") if _HAS_FCNTL else None

    try:
        if lock_fd is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

        # --- snapshot T0 (held under lock) ---
        snapshot_bytes = ledger_path.read_bytes()
        snapshot_hash = sha256_of_bytes(snapshot_bytes)
        snapshot_lines = snapshot_bytes.count(b"\n")
        data = json.loads(snapshot_bytes)
        open_positions = data.get("open_positions", [])

        print(f"ledger: {ledger_path}")
        print(f"snapshot sha256: {snapshot_hash}")
        print(f"snapshot line count: {snapshot_lines}")
        print(f"open_positions total: {len(open_positions)}")

        plan = compute_repairs(open_positions)
        print(f"\nrepair plan: {len(plan)} row(s) match market_type={TARGET_MARKET_TYPE!r} "
              f"AND kalshi_threshold is None")
        for entry in plan:
            print(f"  - {entry['position_id']} ({entry['ticker']})")

        if len(plan) != args.expected_count:
            print(
                f"\nABORT: matched {len(plan)} row(s), expected exactly "
                f"{args.expected_count}. Per Deliverable 3 instruction: if the "
                "count is not as expected, stop and report. No write performed."
            )
            return 2

        # sanity: no other market_type / non-null-threshold row is touched
        untouched_null_others = [
            p.get("position_id")
            for p in open_positions
            if p.get("kalshi_threshold") is None and p.get("market_type") != TARGET_MARKET_TYPE
        ]
        if untouched_null_others:
            print(
                f"\nNOTE: {len(untouched_null_others)} other null-threshold row(s) exist "
                f"outside scope (market_type != {TARGET_MARKET_TYPE!r}) -- left untouched "
                f"by design: {untouched_null_others}"
            )

        if not args.apply:
            print("\nDRY RUN -- no changes written. Re-run with --apply to write.")
            return 0

        # --- verified backup, built from the EXACT T0 snapshot bytes ---
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = ledger_path.with_name(
            f"{ledger_path.stem}.pre_gg291_backfill_{ts}{ledger_path.suffix}"
        )
        backup_path.write_bytes(snapshot_bytes)

        backup_bytes = backup_path.read_bytes()
        backup_hash = sha256_of_bytes(backup_bytes)
        backup_ok = (backup_hash == snapshot_hash) and (backup_bytes == snapshot_bytes)
        print(f"\nbackup path: {backup_path}")
        print(f"backup sha256: {backup_hash} (matches original: {backup_hash == snapshot_hash})")
        if not backup_ok:
            print("BACKUP VERIFICATION FAILED -- aborting, no write to live ledger performed.")
            return 4
        print("BACKUP VERIFIED (re-read, hash + byte-for-byte match confirmed).")

        # --- apply repair to in-memory copy of the T0 snapshot ---
        repaired_at = datetime.now(timezone.utc).isoformat()
        applied = apply_repairs(open_positions, plan, repaired_at)
        print(f"\napplied {applied} repair(s) to in-memory copy")

        # --- optimistic concurrency check immediately before write ---
        live_bytes_t1 = ledger_path.read_bytes()
        if live_bytes_t1 != snapshot_bytes:
            print(
                "\nCONCURRENCY ABORT: live ledger changed since snapshot was taken. "
                "Refusing to write a repair computed against stale state. No write "
                f"performed. Backup at {backup_path} is still valid and harmless to "
                "leave in place. Re-run this script to retry against current state."
            )
            return 3

        # --- atomic write ---
        tmp_path = ledger_path.with_suffix(ledger_path.suffix + f".tmp_{ts}")
        with tmp_path.open("w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, ledger_path)
        print(f"\nwrote repaired ledger to {ledger_path} (atomic replace)")

        return 0
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()


if __name__ == "__main__":
    sys.exit(main())

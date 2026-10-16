#!/usr/bin/env python3
"""GG-271: bound the T4 MLB `rejected_positions` ring buffer and safely
migrate the live, already-unbounded `paper_portfolio_mlb_t4.json`.

Root cause: `PaperTrader.open_position()` (c5_execution/paper_trader.py)
appends every Kalshi order rejection to `rejected_positions` with no cap.
Observed 2026-09-11: 25,243 entries / 29.27MB (88.9% of the file), growing
~1,000-1,200/day and accelerating. `MAX_REJECTED_POSITIONS` (paper_trader.py)
now bounds this field to the most recent N entries on every `_save()` call,
in-process, going forward. This script performs the one-time migration of
the already-oversized live file to that bound, safely:

  1. Back up the live file (timestamped copy, never overwritten).
  2. Verify the backup loads as JSON and its `open_positions` match the
     live file's `open_positions` EXACTLY (deep-equal). Abort with no
     changes made if they differ by even one entry.
  3. Write the full pre-migration `rejected_positions` list to a durable
     sidecar JSON file — nothing is deleted, only relocated out of the
     live portfolio file (explicit GG-271 requirement: no historical
     rejection data may be discarded without first being preserved
     durably elsewhere).
  4. Load the file through `PaperTrader` (its constructor calls
     `_load_or_init`) and call `_save()` under the class's own
     `_lock`/`_file_lock()` discipline (GG-034) — this is the ONLY write
     to the live file this script performs, and it is the same lock/save
     path every other T4 writer already uses. `_save()` now enforces
     `MAX_REJECTED_POSITIONS` itself, so this call is what actually
     truncates the live file.
  5. Re-verify `open_positions` unchanged post-migration and report the
     before/after size and counts.

Does NOT restart any service. T4's own writer (`run_t4_mlb_live.py`, via
`open_position()`) and this script both go through the same `flock()`-based
`_file_lock()`, so this is safe to run while `t4-mlb` is live.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from prediction_market_bot.atomic_io import atomic_write_text  # noqa: E402  (W76.3, GG-748)
from prediction_market_bot.c5_execution.paper_trader import (  # noqa: E402
    MAX_REJECTED_POSITIONS,
    PaperTrader,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402


def _utc_stamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--portfolio",
        type=Path,
        default=REPO_ROOT / "logs" / "paper_portfolio_mlb_t4.json",
        help="Path to the live portfolio file to migrate.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Back up and verify only; do not write the bounded file.",
    )
    args = parser.parse_args()

    portfolio_path: Path = args.portfolio
    if not portfolio_path.exists():
        print(f"ABORT: {portfolio_path} does not exist.")
        return 1

    logs_dir = portfolio_path.parent
    stamp = _utc_stamp()

    # GG-271 (live-tested finding): the live T4 writer's _save() uses
    # `Path.write_text()`, which truncates-then-writes -- NOT an atomic
    # temp-file-plus-rename. A plain, lock-free read of this file (as an
    # earlier version of this script did for its backup/verify step) can
    # therefore observe a torn/empty file mid-write. This was directly
    # observed during dry-run testing against the live file: a `.stat()`
    # call immediately following a successful `.read_text()` parse reported
    # 0 bytes. Every read this script performs against the live file is
    # therefore done while holding the SAME `_file_lock()` the live writer
    # (`run_t4_mlb_live.py`, via `open_position()`/`_save()`) uses -- backup,
    # verification, sidecar preservation, and migration all happen inside
    # one lock acquisition, so no writer can interleave a torn state between
    # any of these steps.
    audit_log_path = logs_dir / "audit_mlb_t4.jsonl"
    logger = AuditLogger(log_path=audit_log_path, min_severity="INFO")
    trader = PaperTrader(portfolio_path=portfolio_path, logger=logger)

    backup_path = logs_dir / f"{portfolio_path.stem}.pre_gg271_migration.{stamp}.json.bak"
    sidecar_path = logs_dir / f"{portfolio_path.stem}.rejected_positions_history.{stamp}.json"

    with trader._lock, trader._file_lock():
        # ---- Step 1: reload the latest committed state under the lock,
        # then back it up. shutil.copy2 is now safe: no writer can be
        # mid-write while we hold this exclusive flock. ----
        trader._reload_locked()
        pre_size = portfolio_path.stat().st_size
        shutil.copy2(portfolio_path, backup_path)
        print(f"Backup written: {backup_path} ({backup_path.stat().st_size} bytes)")

        live_state = trader._state
        live_open = live_state.get("open_positions", [])

        # ---- Step 2: verify the backup loads and open_positions match
        # exactly. Both reads happened under the same lock hold, so this
        # is a same-instant comparison, not a race against a live writer. ----
        try:
            backup_state = json.loads(backup_path.read_text())
        except json.JSONDecodeError as e:
            print(f"ABORT: backup file failed to parse as JSON: {e}")
            return 1

        backup_open = backup_state.get("open_positions", [])
        if live_open != backup_open:
            print(
                "ABORT: backup open_positions does not match live open_positions "
                f"exactly (live n={len(live_open)}, backup n={len(backup_open)}). "
                "No changes made to the live file. Restore is not needed -- the "
                "live file was never touched."
            )
            return 1
        print(f"Backup verification OK: open_positions match exactly (n={len(live_open)}).")

        pre_rejected = live_state.get("rejected_positions", [])
        print(
            f"Pre-migration: file={pre_size} bytes, "
            f"open_positions={len(live_open)}, "
            f"closed_positions={len(live_state.get('closed_positions', []))}, "
            f"rejected_positions={len(pre_rejected)}"
        )

        if args.dry_run:
            print("--dry-run: stopping before sidecar write / migration.")
            return 0

        # ---- Step 3: durably preserve the FULL pre-migration
        # rejected_positions list before anything is truncated. Never
        # overwritten (timestamped). ----
        atomic_write_text(sidecar_path, json.dumps(
            {
                "source_file": str(portfolio_path),
                "migrated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "gap": "GG-271",
                "reason": (
                    "Full rejected_positions history preserved before the live "
                    "portfolio file's copy was bounded to MAX_REJECTED_POSITIONS "
                    "most-recent entries. Every entry here was already logged "
                    "individually to the C6 audit log (kalshi_order_failed) at "
                    "write time, but this sidecar preserves the FULL position "
                    "record (model_p, gross_edge, band, market_type, etc.), "
                    "which the audit log entry does not carry."
                ),
                "entry_count": len(pre_rejected),
                "rejected_positions": pre_rejected,
            },
            indent=2,
        ))
        print(f"Sidecar written: {sidecar_path} (n={len(pre_rejected)} entries preserved)")

        # ---- Step 4: migrate through PaperTrader's own lock/save
        # discipline -- still inside the same lock hold as the backup. ----
        n_before_bound = len(trader._state.get("rejected_positions", []))
        ok = trader._save()
        if not ok:
            print("ABORT: PaperTrader._save() returned False -- disk write failed. Investigate before retrying.")
            return 1

        # ---- Step 5: re-verify open_positions unchanged, report
        # before/after -- still under the lock, so this read cannot race
        # a subsequent writer either. ----
        post_raw = json.loads(portfolio_path.read_text())
        post_open = post_raw.get("open_positions", [])
        post_rejected = post_raw.get("rejected_positions", [])
        post_size = portfolio_path.stat().st_size

    if post_open != live_open:
        print(
            "ALERT: post-migration open_positions differs from pre-migration "
            "open_positions. Restore from backup immediately:\n"
            f"  cp {backup_path} {portfolio_path}"
        )
        return 1

    print(
        f"Post-migration: file={post_size} bytes, "
        f"open_positions={len(post_open)} (unchanged, verified), "
        f"rejected_positions={len(post_rejected)} "
        f"(bounded from {n_before_bound} to MAX_REJECTED_POSITIONS={MAX_REJECTED_POSITIONS})"
    )
    print(
        f"Size reduction: {pre_size} -> {post_size} bytes "
        f"({(1 - post_size / pre_size) * 100:.1f}% smaller)"
    )
    print("GG-271 migration complete. No service was restarted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

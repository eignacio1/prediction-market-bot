#!/usr/bin/env python3
"""T-321: backfill the `logic_epoch`/`approval_commit` fields onto existing
paper-trading positions.

Live writers (paper_trader.py::open_position()) now stamp logic_epoch and
approval_commit on every new position going forward (T-320). This script
derives those two fields for positions that predate that change, by mapping
each position's `entered_at` timestamp against the epoch-boundary table in
logic_epoch.py (see that module's docstring for why GG-100 is excluded and
why commit-author-timestamp is used as a deploy-timestamp proxy).

Idempotent: positions that already have a non-null `logic_epoch` are left
untouched. Writes atomically (temp file + os.replace) so a concurrently-
running cron writer never observes a partially-written portfolio file.
Mirrors scripts/backfill_band_field.py's locking/atomicity pattern exactly.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.logic_epoch import (  # noqa: E402
    approval_commit_for_epoch,
    epoch_for_timestamp,
)

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX fallback
    _HAS_FCNTL = False

_LEDGER_KEYS = ("open_positions", "closed_positions", "rejected_positions")


@contextmanager
def _file_lock(portfolio_path: Path) -> Iterator[None]:
    """Same cross-process exclusive lock convention as PaperTrader._file_lock,
    so this backfill cannot race a concurrently-running cron writer (GG-034)."""
    if not _HAS_FCNTL:  # pragma: no cover - non-POSIX fallback
        yield
        return
    lock_path = portfolio_path.with_suffix(portfolio_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = open(lock_path, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def _parse_entered_at(entered_at: str) -> datetime | None:
    """Parse paper_trader.py::_utc_now()'s "%Y-%m-%dT%H:%M:%S.%f" + "Z" format."""
    if not entered_at:
        return None
    raw = entered_at[:-1] if entered_at.endswith("Z") else entered_at
    try:
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
    return dt.replace(tzinfo=timezone.utc)


def derive_logic_epoch(entered_at: str) -> int | None:
    dt = _parse_entered_at(entered_at)
    if dt is None:
        return None
    return epoch_for_timestamp(dt)


def backfill(portfolio: dict) -> tuple[int, int, int]:
    """Mutates `portfolio` in place. Returns (tagged, already_tagged, unresolvable)."""
    tagged = already_tagged = unresolvable = 0
    for key in _LEDGER_KEYS:
        for pos in portfolio.get(key, []):
            if pos.get("logic_epoch") is not None:
                already_tagged += 1
                continue
            epoch = derive_logic_epoch(str(pos.get("entered_at", "")))
            if epoch is None:
                unresolvable += 1
                continue
            pos["logic_epoch"] = epoch
            pos["approval_commit"] = approval_commit_for_epoch(epoch)
            tagged += 1
    return tagged, already_tagged, unresolvable


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("portfolio", type=Path, help="Path to a paper_portfolio*.json file")
    ap.add_argument("--dry-run", action="store_true", help="Report counts, do not write")
    args = ap.parse_args()

    with _file_lock(args.portfolio):
        # Re-read under the lock (not before) so a concurrent cron writer's
        # appends since process start are not clobbered — same discipline as
        # PaperTrader._reload_locked (GG-034).
        data = json.loads(args.portfolio.read_text())
        tagged, already_tagged, unresolvable = backfill(data)

        print(f"{args.portfolio}: tagged={tagged} already_tagged={already_tagged} unresolvable={unresolvable}")

        if unresolvable:
            print("WARNING: positions with missing/unparseable entered_at were left without logic_epoch.",
                  file=sys.stderr)

        if args.dry_run or tagged == 0:
            return 0

        tmp_path = args.portfolio.with_suffix(args.portfolio.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, indent=2))
        os.replace(tmp_path, args.portfolio)
        print(f"wrote {args.portfolio}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

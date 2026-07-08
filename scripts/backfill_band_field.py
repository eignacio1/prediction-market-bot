#!/usr/bin/env python3
"""T-253: backfill the `band` field onto existing paper-trading positions.

Live writers (paper_trader.py + T1/T2/T4 callers) now stamp `band` on every
new position going forward. This script derives `band` for positions that
predate that change, from the `forecast_id` prefix convention already in use
(see run_*.py's forecast_id construction — these are the real observed
prefixes, not assumed ones):

    FCST-MLB-...  -> T1      (run_mlb_paper_trade.py)
    T2-MLB-...    -> T2      (run_t2_mlb_sameday.py)
    T4-MLB-...    -> T4M-PROJ (run_t4_mlb_live.py)
    FCST-...      -> T1      (run_paper_trade.py, NBA)
    T4-...        -> T4      (run_t4_live.py, NBA)

Idempotent: positions that already have a non-null `band` are left untouched.
Writes atomically (temp file + os.replace) so a concurrently-running cron
writer never observes a partially-written portfolio file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX fallback
    _HAS_FCNTL = False

_PREFIX_TO_BAND = (
    # Order matters: more specific prefixes must be checked before shorter
    # ones they contain (e.g. "FCST-MLB" before "FCST-").
    ("T4-MLB-", "T4M-PROJ"),
    ("T2-MLB-", "T2"),
    ("FCST-MLB-", "T1"),
    ("T4-", "T4"),
    ("FCST-", "T1"),
)

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


def derive_band(forecast_id: str) -> str | None:
    for prefix, band in _PREFIX_TO_BAND:
        if forecast_id.startswith(prefix):
            return band
    return None


def backfill(portfolio: dict) -> tuple[int, int, int]:
    """Mutates `portfolio` in place. Returns (tagged, already_tagged, unresolvable)."""
    tagged = already_tagged = unresolvable = 0
    for key in _LEDGER_KEYS:
        for pos in portfolio.get(key, []):
            if pos.get("band"):
                already_tagged += 1
                continue
            band = derive_band(str(pos.get("forecast_id", "")))
            if band is None:
                unresolvable += 1
                continue
            pos["band"] = band
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
            print("WARNING: positions with unresolvable forecast_id prefixes were left without a band field.",
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

#!/usr/bin/env python3
"""
T-437 Task 3 (2026-08-11) — re-derive outcome/pnl for the T4M-PROJ closed
positions in paper_portfolio_mlb_t4.json that GG-166/T-429's
correct_t4_game_dates.py flagged game_date_corrected_but_outcome_stale, using
the T-421 decoupled outcome store (logs/t4_mlb_outcome_store.jsonl) as the
authoritative source.

Authority basis (T-437 Task 1): 69/69 fresh live re-fetches, days after the
original games, matched the store and disagreed with the ledger. 0% "neither".
The store is authoritative for this population.

Classification (T-437 Task 2, reproduced here for the --apply pass):
  - store has no resolved actual_hits for this ticker -> UNRESOLVED (left
    untouched; game_date_corrected_but_outcome_stale flag stays set)
  - store.actual_hits == ledger.actual_hits -> NEITHER (wrong-date query
    coincidentally landed on the right total; outcome/pnl already correct —
    only the stale flag is cleared, with a note)
  - store.actual_hits != ledger.actual_hits -> GG166 (re-derive actual_hits,
    outcome, pnl from the store's value; original stale values preserved
    under a _pre_t437_rederivation key for audit)

Outcome/pnl formula reproduced read-only from
src/prediction_market_bot/c5_execution/paper_trader.py's settle_position()
(SCOPE FENCE forbids editing that file; this script does not import or call
it, matching correct_t4_game_dates.py's precedent of a fully standalone
one-shot remediation tool):

    yes_won = actual_stat >= threshold
    if direction == "YES":
        won = yes_won
        yes_ask = mid + vig / 2
        pnl = size * (1 - yes_ask) / yes_ask if won else -size
    else:  # NO
        won = not yes_won
        no_ask = (1 - mid) + vig / 2
        pnl = size * (1 - no_ask) / no_ask if won else -size
    pnl = round(pnl, 4)
    outcome = "WIN" if won else "LOSS"

No network calls. Reads the already-fetched, already-validated outcome store.

Usage:
    python3 scripts/t437_task3_rederive_outcomes.py --ledger <path>            # dry run
    python3 scripts/t437_task3_rederive_outcomes.py --ledger <path> --apply    # writes + backs up
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX fallback
    _HAS_FCNTL = False

_REPO_ROOT = Path(__file__).resolve().parent.parent
STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"


@contextmanager
def ledger_file_lock(ledger_path: Path) -> Iterator[None]:
    """Same advisory-flock discipline as PaperTrader._file_lock() (paper_trader.py
    line 251) — acquired here too so this standalone script cannot race a
    concurrently-running live T4 process's read-modify-save cycle."""
    if not _HAS_FCNTL:  # pragma: no cover
        yield
        return
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    fd = open(lock_path, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def load_store() -> dict:
    store = {}
    with open(STORE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            store[r["ticker"]] = r
    return store


def recompute(pos: dict, actual_hits: float) -> tuple[str, float]:
    threshold = pos["kalshi_threshold"]
    direction = pos["direction"]
    size = float(pos["size_usd"])
    mid = float(pos["mid_price_at_entry"])
    vig = float(pos["vig_at_entry"])

    yes_won = actual_hits >= threshold
    if direction == "YES":
        won = yes_won
        yes_ask = mid + vig / 2
        pnl = size * (1.0 - yes_ask) / yes_ask if won else -size
    else:
        won = not yes_won
        no_ask = (1.0 - mid) + vig / 2
        pnl = size * (1.0 - no_ask) / no_ask if won else -size

    pnl = round(pnl, 4)
    outcome = "WIN" if won else "LOSS"
    return outcome, pnl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    parser.add_argument("--ledger", required=True, help="path to paper_portfolio_mlb_t4.json")
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    store = load_store()

    lock_ctx = ledger_file_lock(ledger_path) if args.apply else _nullcontext()
    with lock_ctx:
        # Re-read under the lock (apply path) so a concurrently-running live
        # T4 process's appends made between script start and lock acquisition
        # are not clobbered by writing back a stale in-memory copy.
        with ledger_path.open() as f:
            data = json.load(f)
        closed = data.get("closed_positions", [])
        _process_and_maybe_apply(closed, store, args, ledger_path, data)
    return 0


class _nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


def _process_and_maybe_apply(closed, store, args, ledger_path, data) -> None:

    counts = {"GG166": 0, "NEITHER": 0, "UNRESOLVED": 0}
    pnl_delta_total = 0.0

    for pos in closed:
        if not pos.get("game_date_corrected_but_outcome_stale"):
            continue

        ticker = pos.get("kalshi_ticker", "")
        srec = store.get(ticker)
        ledger_hits = pos.get("actual_hits")

        if srec is None or not srec.get("resolved") or srec.get("actual_hits") is None or ledger_hits is None:
            counts["UNRESOLVED"] += 1
            continue

        store_hits = float(srec["actual_hits"])
        if store_hits == float(ledger_hits):
            counts["NEITHER"] += 1
            if args.apply:
                pos["game_date_corrected_but_outcome_stale"] = False
                pos["outcome_rederivation_ref"] = "GG-166/T-437"
                pos["outcome_rederivation_result"] = "NEITHER — store confirms ledger actual_hits unchanged"
            continue

        counts["GG166"] += 1
        new_outcome, new_pnl = recompute(pos, store_hits)
        if args.apply:
            old_pnl = pos.get("pnl", 0.0)
            pos["_pre_t437_rederivation"] = {
                "actual_hits": pos.get("actual_hits"),
                "outcome": pos.get("outcome"),
                "pnl": pos.get("pnl"),
            }
            pos["actual_hits"] = store_hits
            pos["outcome"] = new_outcome
            pos["pnl"] = new_pnl
            pos["game_date_corrected_but_outcome_stale"] = False
            pos["outcome_rederivation_ref"] = "GG-166/T-437"
            pos["outcome_rederivation_result"] = "GG166 — actual_hits/outcome/pnl re-derived from T-421 outcome store"
            pnl_delta_total += (new_pnl - old_pnl)

    print(f"GG166 (re-derived): {counts['GG166']}")
    print(f"NEITHER (flag cleared, no change): {counts['NEITHER']}")
    print(f"UNRESOLVED (untouched, flag stays): {counts['UNRESOLVED']}")
    print(f"total stale positions processed: {sum(counts.values())}")

    if not args.apply:
        # dry-run pnl delta preview (recompute without mutating)
        preview_delta = 0.0
        for pos in closed:
            if not pos.get("game_date_corrected_but_outcome_stale"):
                continue
            ticker = pos.get("kalshi_ticker", "")
            srec = store.get(ticker)
            ledger_hits = pos.get("actual_hits")
            if srec is None or not srec.get("resolved") or srec.get("actual_hits") is None or ledger_hits is None:
                continue
            store_hits = float(srec["actual_hits"])
            if store_hits == float(ledger_hits):
                continue
            _, new_pnl = recompute(pos, store_hits)
            preview_delta += (new_pnl - pos.get("pnl", 0.0))
        print(f"\nDRY RUN — no changes written. Preview net pnl delta (GG166 only): {preview_delta:+.4f}")
        print("Re-run with --apply to write (backup taken automatically).")
        return 0

    print(f"\nNet pnl delta applied (GG166 re-derivations only): {pnl_delta_total:+.4f}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = ledger_path.with_name(f"{ledger_path.stem}.pre_t437_rederivation_{ts}{ledger_path.suffix}")
    shutil.copy2(ledger_path, backup_path)
    print(f"Backed up ledger to {backup_path}")

    with ledger_path.open("w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote corrected ledger to {ledger_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

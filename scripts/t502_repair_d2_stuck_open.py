#!/usr/bin/env python3
"""
T-502 / ADR-0055 D2 (2026-08-28) — repair the 46 stuck-open T4M-PROJ
epoch-12 positions in paper_portfolio_mlb_t4.json whose `game_date` does
not match their `kalshi_ticker`-embedded date (GG-166/GG-170 lineage).

SCOPE, deliberately narrow (ADR-0055 D2 sign-off; do not extend):
  - open_positions ONLY, logic_epoch == 12 ONLY.
  - Touches exactly two/three fields per repaired row: `game_date`
    (corrected), plus provenance `repaired_at` / `repair_ref`
    (informationally also `game_date_corrected_from`, mirroring the
    GG-166/T-429 precedent script's field name for continuity).
  - Does NOT touch closed_positions, rejected_positions, logic_epoch,
    kelly_fraction, size_usd, direction, mip, vig, threshold, or any
    other field.

PRECONDITION (ADR-0055 sec 2 item 1): T-472/GG-191 landed a new
canonical, series-agnostic ticker-date parser
(market_type_registry.derive_game_date) BEFORE ADR-0055 was accepted.
The ADR explicitly forbids assuming the legacy regex
(correct_t4_game_dates.ticker_to_game_date) and the new canonical
parser agree without checking. This script checks on every one of the
targeted tickers as a hard precondition and refuses to proceed
(exit 2) on any disagreement.

CONCURRENCY: paper_portfolio_mlb_t4.json is actively written by the
live t4-mlb systemd service (new positions appended every ~45-90s).
This script uses optimistic concurrency control: it snapshots the file
once, computes the repair against that snapshot, and immediately
before writing re-reads the live file and aborts (exit 3) if it has
changed since the snapshot, rather than risk a lost-update overwrite
of concurrently-appended state. Retry externally if this happens.

Usage:
    python3 scripts/t502_repair_d2_stuck_open.py                # dry run
    python3 scripts/t502_repair_d2_stuck_open.py --apply         # write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from correct_t4_game_dates import ticker_to_game_date  # noqa: E402
from prediction_market_bot.c5_execution.market_type_registry import (  # noqa: E402
    TickerDateParseError,
    derive_game_date,
)

REPAIR_REF = "ADR-0055 D2 / T-502"
TARGET_EPOCH = 12


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as f:
        return sum(1 for _ in f)


def compute_repairs(open_positions: list[dict]) -> tuple[list[dict], list[str]]:
    """Returns (repair_plan, disagreements). Each repair_plan entry:
    {position_id, ticker, old_game_date, new_game_date}."""
    plan = []
    disagreements = []
    for pos in open_positions:
        if pos.get("logic_epoch") != TARGET_EPOCH:
            continue
        ticker = pos.get("kalshi_ticker", "")
        legacy = ticker_to_game_date(ticker)
        try:
            canonical = derive_game_date(ticker)
        except TickerDateParseError as e:
            canonical = None
            canonical_err = str(e)
        else:
            canonical_err = None

        if legacy is None and canonical is None:
            disagreements.append(
                f"{pos.get('position_id')}: BOTH parsers failed on ticker={ticker!r} "
                f"(canonical error: {canonical_err})"
            )
            continue
        if legacy != canonical:
            disagreements.append(
                f"{pos.get('position_id')}: PARSER DISAGREEMENT ticker={ticker!r} "
                f"legacy={legacy!r} canonical={canonical!r} (canonical error: {canonical_err})"
            )
            continue

        derived = legacy  # == canonical, confirmed above
        old_gd = pos.get("game_date", "")
        if derived != old_gd:
            plan.append(
                {
                    "position_id": pos.get("position_id"),
                    "ticker": ticker,
                    "old_game_date": old_gd,
                    "new_game_date": derived,
                }
            )
    return plan, disagreements


def apply_repairs(open_positions: list[dict], plan: list[dict], repaired_at: str) -> int:
    by_id = {p.get("position_id"): p for p in plan}
    applied = 0
    for pos in open_positions:
        entry = by_id.get(pos.get("position_id"))
        if entry is None:
            continue
        pos["game_date_corrected_from"] = pos.get("game_date", "")
        pos["game_date"] = entry["new_game_date"]
        pos["repaired_at"] = repaired_at
        pos["repair_ref"] = REPAIR_REF
        applied += 1
    return applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument(
        "--ledger",
        default="/opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json",
        help="path to paper_portfolio_mlb_t4.json",
    )
    args = ap.parse_args()

    ledger_path = Path(args.ledger)

    # --- snapshot T0 ---
    snapshot_bytes = ledger_path.read_bytes()
    snapshot_hash = hashlib.sha256(snapshot_bytes).hexdigest()
    snapshot_lines = snapshot_bytes.count(b"\n")
    data = json.loads(snapshot_bytes)
    open_positions = data.get("open_positions", [])
    epoch12 = [p for p in open_positions if p.get("logic_epoch") == TARGET_EPOCH]

    print(f"ledger: {ledger_path}")
    print(f"snapshot sha256: {snapshot_hash}")
    print(f"snapshot line count: {snapshot_lines}")
    print(f"open_positions total: {len(open_positions)}")
    print(f"open_positions logic_epoch=={TARGET_EPOCH}: {len(epoch12)}")

    plan, disagreements = compute_repairs(open_positions)

    print(f"\nparser cross-check: {len(epoch12)} epoch-{TARGET_EPOCH} rows checked, "
          f"{len(disagreements)} disagreement(s)/unparseable")
    if disagreements:
        print("\nDISAGREEMENTS (aborting, per ADR-0055 sec 2 item 1 -- do not assume parser equivalence):")
        for d in disagreements:
            print(f"  - {d}")
        return 2
    print("  legacy (ticker_to_game_date) and canonical (derive_game_date) AGREE on every row.")

    print(f"\nrepair plan: {len(plan)} row(s) need game_date correction")
    for entry in plan:
        print(f"  - {entry['position_id']}: {entry['old_game_date']} -> {entry['new_game_date']} "
              f"(ticker={entry['ticker']})")

    if not args.apply:
        print("\nDRY RUN -- no changes written. Re-run with --apply to write.")
        return 0

    if not plan:
        print("\nNothing to repair -- no write performed.")
        return 0

    # --- verified backup, built from the EXACT T0 snapshot bytes (no re-read gap) ---
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = ledger_path.with_name(f"{ledger_path.stem}.pre_adr0055_d2_{ts}{ledger_path.suffix}")
    backup_path.write_bytes(snapshot_bytes)

    backup_bytes = backup_path.read_bytes()
    backup_hash = hashlib.sha256(backup_bytes).hexdigest()
    backup_lines = backup_bytes.count(b"\n")
    backup_ok = (backup_hash == snapshot_hash) and (backup_lines == snapshot_lines) and (backup_bytes == snapshot_bytes)
    print(f"\nbackup path: {backup_path}")
    print(f"backup sha256: {backup_hash} (matches original: {backup_hash == snapshot_hash})")
    print(f"backup line count: {backup_lines} (matches original: {backup_lines == snapshot_lines})")
    if not backup_ok:
        print("BACKUP VERIFICATION FAILED -- aborting, no write to live ledger performed.")
        return 4
    print("BACKUP VERIFIED (re-read, hash + line count + byte-for-byte match confirmed).")

    # --- apply repair to in-memory copy of the T0 snapshot ---
    repaired_at = datetime.now(timezone.utc).isoformat()
    applied = apply_repairs(open_positions, plan, repaired_at)
    print(f"\napplied {applied} repair(s) to in-memory copy")

    # --- optimistic concurrency check immediately before write ---
    live_bytes_t1 = ledger_path.read_bytes()
    if live_bytes_t1 != snapshot_bytes:
        print(
            "\nCONCURRENCY ABORT: live ledger changed since snapshot was taken "
            "(t4-mlb service likely appended/modified positions between T0 and T1). "
            "Refusing to write a repair computed against stale state -- this would "
            "lose the concurrent update. No write performed. Backup at "
            f"{backup_path} is still valid and harmless to leave in place. Re-run this "
            "script to retry against current state."
        )
        return 3

    # --- atomic write ---
    tmp_path = ledger_path.with_suffix(ledger_path.suffix + f".tmp_{ts}")
    with tmp_path.open("w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, ledger_path)
    print(f"\nwrote repaired ledger to {ledger_path} (atomic replace)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

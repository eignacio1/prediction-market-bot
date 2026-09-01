#!/usr/bin/env python3
"""
T-503 / ADR-0055 D1+D3 (2026-08-31) -- repair the 532 logic_epoch==12
closed_positions (D1) and 76 logic_epoch==12 rejected_positions (D3) in
paper_portfolio_mlb_t4.json whose kalshi_ticker-embedded date disagrees
with stored `game_date` (GG-166/GG-170/GG-185/GG-189 lineage).

SCOPE, deliberately bundled per operator sign-off (ADR-0055 sec 9,
APPROVALS_REGISTER.md ADR-0055 row):
  - closed_positions (D1) and rejected_positions (D3), logic_epoch == 12
    ONLY, and ONLY rows where the ticker-derived date differs from the
    stored game_date.
  - D1 (closed_positions): corrects `game_date`; looks up `actual_hits`
    in the T-421 decoupled outcome store (logs/t4_mlb_outcome_store.jsonl,
    keyed on kalshi_ticker) and recomputes `outcome`/`pnl` via the
    verbatim T-437/T-477-precedent formula wherever the store's
    actual_hits disagrees with the ledger's stored actual_hits (GG166
    class) -- rows where they already agree (NEITHER class) get the
    date fix only, outcome/pnl untouched.
  - D3 (rejected_positions): corrects `game_date` ONLY -- rejected
    positions were never executed and carry no outcome/pnl/actual_hits
    fields at all (confirmed via live schema inspection, T-503).
  - Does NOT touch open_positions (0 currently -- out of scope regardless),
    logic_epoch, kelly_fraction, size_usd, direction, mip, vig, threshold,
    or any other field.
  - Does NOT touch t4_mlb_resolved_ledger.jsonl -- that file is
    regenerated separately (scripts/build_t4_resolved_ledger.py) from
    this script's corrected closed_positions, per T-503's operator
    decision to fix the root (closed_positions) rather than
    hand-duplicate the recompute logic into two files that could drift
    (the resolved ledger is a wholesale weekly-cron rebuild of
    closed_positions, deploy/cron.conf Mon 14:20 UTC -- a ledger-only
    repair would be silently reverted at the next rebuild).

PRECONDITION (ADR-0055 sec 2 item 1, reused verbatim from
scripts/t502_repair_d2_stuck_open.py): T-472/GG-191 landed a new
canonical, series-agnostic ticker-date parser
(market_type_registry.derive_game_date) BEFORE ADR-0055 was accepted.
The ADR explicitly forbids assuming the legacy regex
(correct_t4_game_dates.ticker_to_game_date) and the new canonical
parser agree without checking. This script checks on every targeted
ticker (D1 and D3 combined) as a hard precondition and refuses to
proceed (exit 2) on any disagreement.

RECOMPUTE FORMULA: verbatim from scripts/t477_dryrun_epoch12_repair.py
(itself verbatim from t437_task3_rederive_outcomes.py::recompute()),
which produced the pre-registered 532-changed/2416-unchanged result
baked into ADR-0055 Addendum A. Reused here unmodified.

CONCURRENCY: paper_portfolio_mlb_t4.json is actively written by the
live t4-mlb systemd service. This script uses optimistic concurrency
control identically to t502_repair_d2_stuck_open.py: snapshot once,
compute against the snapshot, re-read immediately before write and
abort (exit 3) if changed. GG-224: after a successful write, the
CALLER (not this script) must restart t4-mlb.service so it reloads
the corrected file from disk -- otherwise the service's own periodic
in-memory flush will silently revert this repair. See
GOVERNANCE_GAP_LOG.md GG-224.

Usage:
    python3 scripts/t503_repair_d1_d3_epoch12.py                # dry run
    python3 scripts/t503_repair_d1_d3_epoch12.py --apply         # write
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

REPAIR_REF = "ADR-0055 D1+D3 / T-503"
TARGET_EPOCH = 12
DEFAULT_STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"

EXPECTED_D1 = 532
EXPECTED_D3 = 76


def sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_store(store_path: Path) -> dict:
    store = {}
    with store_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            store[r["ticker"]] = r
    return store


def recompute(threshold, direction, size_usd, mip, vig, actual_hits):
    """Verbatim from t477_dryrun_epoch12_repair.py::recompute()."""
    size = float(size_usd)
    mid = float(mip)
    vig = float(vig)

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


def cross_check_parsers(positions: list[dict]) -> tuple[list[dict], list[str]]:
    """Returns (eligible, disagreements). `eligible` entries are dicts
    {pos, ticker, derived_date, old_game_date} for rows where both
    parsers agree AND that agreed date differs from stored game_date."""
    eligible = []
    disagreements = []
    for pos in positions:
        if pos.get("logic_epoch") != TARGET_EPOCH:
            continue
        ticker = pos.get("kalshi_ticker", "")
        legacy = ticker_to_game_date(ticker)
        try:
            canonical = derive_game_date(ticker)
            canonical_err = None
        except TickerDateParseError as e:
            canonical = None
            canonical_err = str(e)

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
            eligible.append({
                "pos": pos, "ticker": ticker,
                "derived_date": derived, "old_game_date": old_gd,
            })
    return eligible, disagreements


def compute_d1_plan(eligible: list[dict], store: dict) -> tuple[list[dict], list[str]]:
    """Returns (plan, unresolved). Each plan entry carries everything
    needed to mutate the position in place."""
    plan = []
    unresolved = []
    for e in eligible:
        pos = e["pos"]
        ticker = e["ticker"]
        srec = store.get(ticker)
        ledger_hits = pos.get("actual_hits")

        if srec is None or not srec.get("resolved") or srec.get("actual_hits") is None:
            unresolved.append(
                f"{pos.get('position_id')}: ticker={ticker!r} not resolved in outcome store "
                f"(srec={'MISSING' if srec is None else srec})"
            )
            continue

        store_hits = float(srec["actual_hits"])
        classification = "NEITHER" if store_hits == float(ledger_hits) else "GG166"
        if classification == "NEITHER":
            new_outcome = pos.get("outcome")
            new_pnl = pos.get("pnl")
        else:
            new_outcome, new_pnl = recompute(
                pos.get("kalshi_threshold"), pos.get("direction"),
                pos.get("size_usd"), pos.get("mid_price_at_entry"),
                pos.get("vig_at_entry"), store_hits,
            )

        plan.append({
            "position_id": pos.get("position_id"),
            "ticker": ticker,
            "old_game_date": e["old_game_date"],
            "new_game_date": e["derived_date"],
            "old_actual_hits": ledger_hits,
            "new_actual_hits": store_hits,
            "old_outcome": pos.get("outcome"),
            "new_outcome": new_outcome,
            "old_pnl": pos.get("pnl"),
            "new_pnl": new_pnl,
            "classification": classification,
        })
    return plan, unresolved


def compute_d3_plan(eligible: list[dict]) -> list[dict]:
    """D3: game_date correction only -- rejected positions carry no
    outcome/pnl/actual_hits fields (confirmed via live schema check)."""
    plan = []
    for e in eligible:
        pos = e["pos"]
        plan.append({
            "position_id": pos.get("position_id"),
            "ticker": e["ticker"],
            "old_game_date": e["old_game_date"],
            "new_game_date": e["derived_date"],
        })
    return plan


def apply_d1(closed_positions: list[dict], plan: list[dict], repaired_at: str) -> int:
    by_id = {p["position_id"]: p for p in plan}
    applied = 0
    for pos in closed_positions:
        entry = by_id.get(pos.get("position_id"))
        if entry is None:
            continue
        pos["game_date_corrected_from"] = pos.get("game_date", "")
        pos["game_date"] = entry["new_game_date"]
        if entry["classification"] == "GG166":
            pos["actual_hits"] = entry["new_actual_hits"]
            pos["outcome"] = entry["new_outcome"]
            pos["pnl"] = entry["new_pnl"]
            pos["outcome_rederivation_ref"] = REPAIR_REF
        pos["repaired_at"] = repaired_at
        pos["repair_ref"] = REPAIR_REF
        applied += 1
    return applied


def apply_d3(rejected_positions: list[dict], plan: list[dict], repaired_at: str) -> int:
    by_id = {p["position_id"]: p for p in plan}
    applied = 0
    for pos in rejected_positions:
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
    ap.add_argument("--store", default=str(DEFAULT_STORE), help="path to t4_mlb_outcome_store.jsonl")
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    store_path = Path(args.store)

    # --- snapshot T0 ---
    snapshot_bytes = ledger_path.read_bytes()
    snapshot_hash = sha256_of_bytes(snapshot_bytes)
    snapshot_lines = snapshot_bytes.count(b"\n")
    data = json.loads(snapshot_bytes)
    closed_positions = data.get("closed_positions", [])
    rejected_positions = data.get("rejected_positions", [])

    print(f"ledger: {ledger_path}")
    print(f"snapshot sha256: {snapshot_hash}")
    print(f"snapshot line count: {snapshot_lines}")
    print(f"closed_positions total: {len(closed_positions)}")
    print(f"rejected_positions total: {len(rejected_positions)}")

    store = load_store(store_path)
    print(f"outcome store: {store_path} ({len(store)} tickers)")

    # --- precondition: dual-parser cross-check on ALL epoch-12 rows in both arrays ---
    d1_eligible, d1_disagreements = cross_check_parsers(closed_positions)
    d3_eligible, d3_disagreements = cross_check_parsers(rejected_positions)
    all_disagreements = d1_disagreements + d3_disagreements

    print(f"\nparser cross-check (D1 closed_positions): {len(d1_eligible)} eligible, "
          f"{len(d1_disagreements)} disagreement(s)/unparseable")
    print(f"parser cross-check (D3 rejected_positions): {len(d3_eligible)} eligible, "
          f"{len(d3_disagreements)} disagreement(s)/unparseable")
    if all_disagreements:
        print("\nDISAGREEMENTS (aborting, per ADR-0055 sec 2 item 1 -- do not assume parser equivalence):")
        for d in all_disagreements:
            print(f"  - {d}")
        return 2
    print("  legacy (ticker_to_game_date) and canonical (derive_game_date) AGREE on every targeted row.")

    d1_plan, d1_unresolved = compute_d1_plan(d1_eligible, store)
    d3_plan = compute_d3_plan(d3_eligible)

    print(f"\nD1 repair plan: {len(d1_plan)} closed_positions row(s), "
          f"{len(d1_unresolved)} unresolved-in-store")
    if d1_unresolved:
        print("\nUNRESOLVED (aborting -- outcome store does not cover every D1 target ticker):")
        for u in d1_unresolved:
            print(f"  - {u}")
        return 5
    class_counts = {"GG166": 0, "NEITHER": 0}
    for e in d1_plan:
        class_counts[e["classification"]] += 1
    print(f"  classification breakdown: {class_counts}")

    print(f"\nD3 repair plan: {len(d3_plan)} rejected_positions row(s) (game_date only)")

    # --- assertions vs. ADR-0055 pre-registered counts ---
    failures = []
    if len(d1_plan) != EXPECTED_D1:
        failures.append(f"ASSERTION FAILED: expected D1={EXPECTED_D1} changed, got {len(d1_plan)}")
    if len(d3_plan) != EXPECTED_D3:
        failures.append(f"ASSERTION FAILED: expected D3={EXPECTED_D3} changed, got {len(d3_plan)}")
    if failures:
        print("\n=== PRE-WRITE ASSERTIONS: FAILED ===")
        for f_ in failures:
            print(f_)
        return 6
    print(f"\npre-write assertions vs. ADR-0055: D1=={EXPECTED_D1} OK, D3=={EXPECTED_D3} OK")

    if not args.apply:
        print("\nDRY RUN -- no changes written. Re-run with --apply to write.")
        return 0

    # --- verified backup, built from the EXACT T0 snapshot bytes (no re-read gap) ---
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = ledger_path.with_name(f"{ledger_path.stem}.pre_adr0055_d1d3_{ts}{ledger_path.suffix}")
    backup_path.write_bytes(snapshot_bytes)

    backup_bytes = backup_path.read_bytes()
    backup_hash = sha256_of_bytes(backup_bytes)
    backup_lines = backup_bytes.count(b"\n")
    backup_ok = (backup_hash == snapshot_hash) and (backup_lines == snapshot_lines) and (backup_bytes == snapshot_bytes)
    print(f"\nbackup path: {backup_path}")
    print(f"backup sha256: {backup_hash} (matches original: {backup_hash == snapshot_hash})")
    print(f"backup line count: {backup_lines} (matches original: {backup_lines == snapshot_lines})")
    if not backup_ok:
        print("BACKUP VERIFICATION FAILED -- aborting, no write to live ledger performed.")
        return 4
    print("BACKUP VERIFIED (re-read, hash + line count + byte-for-byte match confirmed).")

    # --- apply repairs to in-memory copy of the T0 snapshot ---
    repaired_at = datetime.now(timezone.utc).isoformat()
    applied_d1 = apply_d1(closed_positions, d1_plan, repaired_at)
    applied_d3 = apply_d3(rejected_positions, d3_plan, repaired_at)
    print(f"\napplied {applied_d1} D1 repair(s) + {applied_d3} D3 repair(s) to in-memory copy")

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

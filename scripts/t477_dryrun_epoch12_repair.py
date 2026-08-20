#!/usr/bin/env python3
"""
T-477 (2026-08-20) — DRY-RUN ONLY simulation of the epoch-12 ledger repair
pre-registered in ADR-0055. Reads t4_mlb_resolved_ledger.jsonl and
t4_mlb_outcome_store.jsonl, both read-only, and writes a SEPARATE output
file plus a per-row diff record. Never writes to the source ledger.

Repair rule (ADR-0055 section 2), reused not reimplemented:
  - game_date: ticker_to_game_date(), verbatim from
    scripts/correct_t4_game_dates.py (GG-166/T-429 precedent).
  - outcome/actual_hits: looked up in the T-421 decoupled outcome store
    (logs/t4_mlb_outcome_store.jsonl) keyed on kalshi_ticker.
  - outcome/pnl recompute formula: verbatim logic from
    scripts/t437_task3_rederive_outcomes.py::recompute(), adapted only for
    this ledger's field names (threshold/mip/vig/size_usd vs that script's
    kalshi_threshold/mid_price_at_entry/vig_at_entry).
  - size_usd, direction, mip, vig, threshold: unchanged.
  - Scope: logic_epoch == 12 rows whose ticker-derived date differs from
    stored game_date. All other rows pass through unchanged.

Usage:
    python3 scripts/t477_dryrun_epoch12_repair.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
OUT_LEDGER = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.REPAIRED_DRYRUN.jsonl"
OUT_DIFF = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.REPAIRED_DRYRUN.diff.jsonl"

# Verbatim from scripts/correct_t4_game_dates.py
_TICKER_DATE_RE = re.compile(r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})")
_TICKER_DATE_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}


def ticker_to_game_date(ticker: str) -> str | None:
    m = _TICKER_DATE_RE.match(ticker or "")
    if not m:
        return None
    yy, mon, dd, _hhmm = m.groups()
    month = _TICKER_DATE_MONTHS.get(mon)
    if month is None:
        return None
    return f"20{yy}-{month}-{dd}"


def recompute(threshold, direction, size_usd, mip, vig, actual_hits):
    """Verbatim logic from t437_task3_rederive_outcomes.py::recompute(),
    field names adapted to t4_mlb_resolved_ledger.jsonl's own schema."""
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


def main() -> int:
    store = load_store()

    rows = []
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    out_rows = []
    diffs = []
    n_changed = 0
    n_unchanged = 0
    n_changed_outside_epoch12 = 0
    size_usd_total_before = 0.0
    size_usd_total_after = 0.0
    class_counts = {"GG166": 0, "NEITHER": 0, "UNRESOLVED": 0, "NOT_APPLICABLE": 0}

    for pos in rows:
        size_usd_total_before += float(pos.get("size_usd", 0.0))
        ticker = pos.get("kalshi_ticker", "")
        stored_date = pos.get("game_date", "")
        epoch = pos.get("logic_epoch")
        td = ticker_to_game_date(ticker)

        is_repair_target = (epoch == 12) and (td is not None) and (td != stored_date)

        if not is_repair_target:
            out_rows.append(pos)
            size_usd_total_after += float(pos.get("size_usd", 0.0))
            n_unchanged += 1
            class_counts["NOT_APPLICABLE"] += 1
            continue

        if epoch != 12:
            n_changed_outside_epoch12 += 1  # should never happen given the guard above; tracked for the assertion anyway

        srec = store.get(ticker)
        ledger_hits = pos.get("actual_hits")

        new_pos = dict(pos)
        new_pos["game_date"] = td
        new_pos["game_date_corrected_from"] = stored_date
        new_pos["game_date_correction_ref"] = "T-477/ADR-0055-DRYRUN"

        if srec is None or not srec.get("resolved") or srec.get("actual_hits") is None:
            class_counts["UNRESOLVED"] += 1
            # Date corrected, outcome left as-is (should not occur — T-470
            # closed this gap; tracked defensively).
            out_rows.append(new_pos)
            size_usd_total_after += float(pos.get("size_usd", 0.0))
            n_changed += 1
            diffs.append({
                "position_id": pos.get("position_id"),
                "kalshi_ticker": ticker,
                "logic_epoch": epoch,
                "classification": "UNRESOLVED",
                "game_date": {"before": stored_date, "after": td},
                "actual_hits": {"before": ledger_hits, "after": ledger_hits},
                "outcome": {"before": pos.get("outcome"), "after": pos.get("outcome")},
                "pnl": {"before": pos.get("pnl"), "after": pos.get("pnl")},
            })
            continue

        store_hits = float(srec["actual_hits"])
        if store_hits == float(ledger_hits):
            class_counts["NEITHER"] += 1
            new_outcome = pos.get("outcome")
            new_pnl = pos.get("pnl")
        else:
            class_counts["GG166"] += 1
            new_outcome, new_pnl = recompute(
                pos.get("threshold"), pos.get("direction"),
                pos.get("size_usd"), pos.get("mip"), pos.get("vig"),
                store_hits,
            )

        new_pos["actual_hits"] = store_hits
        new_pos["outcome"] = new_outcome
        new_pos["pnl"] = new_pnl
        new_pos["outcome_rederivation_ref"] = "T-477/ADR-0055-DRYRUN"

        out_rows.append(new_pos)
        size_usd_total_after += float(new_pos.get("size_usd", 0.0))
        n_changed += 1

        diffs.append({
            "position_id": pos.get("position_id"),
            "kalshi_ticker": ticker,
            "logic_epoch": epoch,
            "classification": "NEITHER" if store_hits == float(ledger_hits) else "GG166",
            "game_date": {"before": stored_date, "after": td},
            "actual_hits": {"before": ledger_hits, "after": store_hits},
            "outcome": {"before": pos.get("outcome"), "after": new_outcome},
            "pnl": {"before": pos.get("pnl"), "after": new_pnl},
        })

    with open(OUT_LEDGER, "w") as f:
        for r in out_rows:
            f.write(json.dumps(r) + "\n")

    with open(OUT_DIFF, "w") as f:
        for d in diffs:
            f.write(json.dumps(d) + "\n")

    # --- Assertions (ADR-0055 STEP 2) ---
    print(f"rows changed: {n_changed}")
    print(f"rows unchanged: {n_unchanged}")
    print(f"classification breakdown: {class_counts}")
    print(f"total ledger rows in / out: {len(rows)} / {len(out_rows)}")
    print(f"size_usd total before: {size_usd_total_before:.4f}")
    print(f"size_usd total after:  {size_usd_total_after:.4f}")

    failures = []

    if n_changed != 532:
        failures.append(f"ASSERTION FAILED: expected 532 changed, got {n_changed}")
    if n_unchanged != 2416:
        failures.append(f"ASSERTION FAILED: expected 2416 unchanged, got {n_unchanged}")

    for d in diffs:
        if d["game_date"]["after"] != ticker_to_game_date(d["kalshi_ticker"]):
            failures.append(f"ASSERTION FAILED: {d['position_id']} new game_date does not match ticker-derived date")
        if d["logic_epoch"] != 12:
            failures.append(f"ASSERTION FAILED: {d['position_id']} changed outside logic_epoch 12 (epoch={d['logic_epoch']})")

    if n_changed_outside_epoch12 != 0:
        failures.append(f"ASSERTION FAILED: {n_changed_outside_epoch12} changes occurred outside logic_epoch 12")

    # Re-derive mismatch count in the repaired file, across every epoch.
    remaining_mismatches = 0
    remaining_mismatches_by_epoch = {}
    for r in out_rows:
        td2 = ticker_to_game_date(r.get("kalshi_ticker", ""))
        if td2 is not None and td2 != r.get("game_date", ""):
            remaining_mismatches += 1
            ep = r.get("logic_epoch")
            remaining_mismatches_by_epoch[ep] = remaining_mismatches_by_epoch.get(ep, 0) + 1

    print(f"remaining ticker-vs-game_date mismatches (repaired file, all epochs): {remaining_mismatches}")
    if remaining_mismatches != 0:
        failures.append(f"ASSERTION FAILED: {remaining_mismatches} mismatches remain in repaired file: {remaining_mismatches_by_epoch}")

    if abs(size_usd_total_before - size_usd_total_after) > 1e-9:
        failures.append(
            f"ASSERTION FAILED: size_usd total changed ({size_usd_total_before:.6f} -> {size_usd_total_after:.6f})"
        )

    print()
    if failures:
        print("=== ASSERTIONS: FAILED ===")
        for msg in failures:
            print(msg)
        return 1

    print("=== ASSERTIONS: ALL PASSED ===")
    print(f"  532 changed / 2416 unchanged: OK")
    print(f"  every changed row's game_date == ticker-derived date: OK")
    print(f"  zero changes outside logic_epoch 12: OK")
    print(f"  zero ticker-vs-game_date mismatches remain, all epochs: OK")
    print(f"  total size_usd unchanged: OK ({size_usd_total_before:.4f})")
    print()
    print(f"Wrote {OUT_LEDGER}")
    print(f"Wrote {OUT_DIFF}")
    print()
    print("DRY RUN ONLY. Source ledger logs/t4_mlb_resolved_ledger.jsonl was not modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

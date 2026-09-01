#!/usr/bin/env python3
"""
T-503 post-write verification: ADR-0055 STEP-2 assertions run against the
REAL pre-regen / post-regen t4_mlb_resolved_ledger.jsonl pair (not a
simulation). Read-only, both inputs local pulls of the real VPS files.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PRE = Path("logs/t4_mlb_resolved_ledger.PRE_REGEN.jsonl")
POST = Path("logs/t4_mlb_resolved_ledger.POST_REGEN.jsonl")

_TICKER_DATE_RE = re.compile(r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})")
_MONTHS = {"JAN":"01","FEB":"02","MAR":"03","APR":"04","MAY":"05","JUN":"06",
           "JUL":"07","AUG":"08","SEP":"09","OCT":"10","NOV":"11","DEC":"12"}

def ticker_to_game_date(ticker):
    m = _TICKER_DATE_RE.match(ticker or "")
    if not m:
        return None
    yy, mon, dd, _ = m.groups()
    month = _MONTHS.get(mon)
    if month is None:
        return None
    return f"20{yy}-{month}-{dd}"

def load(path):
    rows = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows[r["position_id"]] = r
    return rows

def main():
    pre = load(PRE)
    post = load(POST)

    if set(pre.keys()) != set(post.keys()):
        print("ASSERTION FAILED: position_id sets differ between pre/post (rows added/removed)")
        return 1

    changed = []
    changed_outside_epoch12 = []
    size_usd_before = 0.0
    size_usd_after = 0.0
    remaining_mismatches = []

    for pid, pr in pre.items():
        po = post[pid]
        size_usd_before += float(pr.get("size_usd", 0.0))
        size_usd_after += float(po.get("size_usd", 0.0))

        is_changed = (pr.get("game_date") != po.get("game_date")
                      or pr.get("outcome") != po.get("outcome")
                      or pr.get("pnl") != po.get("pnl")
                      or pr.get("actual_hits") != po.get("actual_hits"))
        if is_changed:
            changed.append((pid, pr, po))
            if po.get("logic_epoch") != 12:
                changed_outside_epoch12.append(pid)

        td = ticker_to_game_date(po.get("kalshi_ticker", ""))
        if td is not None and td != po.get("game_date", ""):
            remaining_mismatches.append((pid, po.get("logic_epoch")))

    print(f"rows changed (game_date/outcome/pnl/actual_hits): {len(changed)}")
    print(f"rows unchanged: {len(pre) - len(changed)}")
    print(f"total rows pre/post: {len(pre)}/{len(post)}")
    print(f"size_usd total before: {size_usd_before:.4f}")
    print(f"size_usd total after:  {size_usd_after:.4f}")

    failures = []
    # D1 expected 532 changed rows in closed_positions -> resolved ledger only
    # includes resolved WIN/LOSS rows, which is the full D1 target set (D1 is
    # closed_positions only; D3/rejected never appear in this ledger).
    if len(changed) != 532:
        failures.append(f"ASSERTION FAILED: expected 532 changed rows in resolved ledger, got {len(changed)}")

    for pid, pr, po in changed:
        expected_date = ticker_to_game_date(po.get("kalshi_ticker", ""))
        if po.get("game_date") != expected_date:
            failures.append(f"ASSERTION FAILED: {pid} new game_date != ticker-derived date")
        if po.get("logic_epoch") != 12:
            failures.append(f"ASSERTION FAILED: {pid} changed outside logic_epoch 12 (epoch={po.get('logic_epoch')})")

    if changed_outside_epoch12:
        failures.append(f"ASSERTION FAILED: changes outside logic_epoch 12: {changed_outside_epoch12}")

    if remaining_mismatches:
        by_epoch = {}
        for pid, ep in remaining_mismatches:
            by_epoch[ep] = by_epoch.get(ep, 0) + 1
        failures.append(f"ASSERTION FAILED: {len(remaining_mismatches)} ticker/game_date mismatches remain: {by_epoch}")
    else:
        print("remaining ticker-vs-game_date mismatches (post file, all epochs, all rows): 0")

    if abs(size_usd_before - size_usd_after) > 1e-9:
        failures.append(f"ASSERTION FAILED: size_usd total changed ({size_usd_before:.6f} -> {size_usd_after:.6f})")
    else:
        print(f"size_usd total invariant: OK ({size_usd_before:.4f} unchanged)")

    print()
    if failures:
        print("=== ASSERTIONS: FAILED ===")
        for f_ in failures:
            print(f_)
        return 1

    print("=== ASSERTIONS: ALL PASSED (against REAL pre/post files) ===")
    print("  532 changed / all else unchanged: OK")
    print("  every changed row's game_date == ticker-derived date: OK")
    print("  zero changes outside logic_epoch 12: OK")
    print("  zero ticker-vs-game_date mismatches remain, all epochs: OK")
    print("  total size_usd unchanged: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())

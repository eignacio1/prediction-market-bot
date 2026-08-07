#!/usr/bin/env python3
"""
GG-166/T-429 (2026-08-07) — correct the `game_date` field on T4M-PROJ
paper_portfolio_mlb_t4.json records using the ticker-embedded date, which
T-421 validated as 100% reliable across 2,021 tickers. NOT part of the
production pipeline — a one-shot, manually invoked data-remediation tool,
mirroring scripts/repair_stuck_mlb_positions.py's pattern.

Scope, deliberately narrow:

- OPEN positions: `game_date` is corrected in place. This is safe and
  complete on its own — no position has been resolved yet, so correcting
  the join key just means the *next* resolution attempt (via
  run_resolve_mlb.py, already hardened by this same task's B2 fix) uses
  the right date. No network calls are made by this script.

- CLOSED positions: `game_date` is corrected in place for bookkeeping
  accuracy, but this script deliberately does NOT attempt to re-derive
  `actual_hits` / `outcome` / `pnl` for positions that were resolved
  against the wrong day's box score. That requires live re-fetches
  against the MLB Stats API / ESPN, which T-416/T-422 (GG-084) showed
  degrades to a 100% Fastly-CDN block partway through any sequential
  batch run from the VPS's datacenter IP. Re-deriving ~1,220 closed
  positions' true outcomes safely requires the same two-phase
  fetch-off-VPS / apply-on-VPS split T-422 used for the 22-position
  T1/MAIN repair — that is out of this script's scope and is tracked
  as GG-166 follow-on work, not attempted here. Closed positions'
  `actual_hits`/`outcome`/`pnl` are therefore left untouched; only
  `game_date` is corrected, and a `game_date_corrected_but_outcome_stale`
  flag is added so any downstream consumer can tell the difference
  between "resolved against the right date" and "date fixed after the
  fact, outcome still needs re-derivation."

Usage:
    BOT_ENV=paper python3 scripts/correct_t4_game_dates.py --apply
Default (no --apply) is a dry run: reports what WOULD change, writes nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    parser.add_argument(
        "--ledger",
        default="/opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json",
        help="path to paper_portfolio_mlb_t4.json",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    with ledger_path.open() as f:
        data = json.load(f)

    open_positions = data.get("open_positions", [])
    closed_positions = data.get("closed_positions", [])

    open_fixed = 0
    open_unparseable = 0
    closed_fixed = 0
    closed_unparseable = 0

    for pos in open_positions:
        ticker = pos.get("kalshi_ticker", "")
        td = ticker_to_game_date(ticker)
        gd = pos.get("game_date", "")
        if td is None:
            open_unparseable += 1
            continue
        if td != gd:
            open_fixed += 1
            if args.apply:
                pos["game_date"] = td
                pos["game_date_corrected_from"] = gd
                pos["game_date_correction_ref"] = "GG-166/T-429"

    for pos in closed_positions:
        ticker = pos.get("kalshi_ticker", "")
        td = ticker_to_game_date(ticker)
        gd = pos.get("game_date", "")
        if td is None:
            closed_unparseable += 1
            continue
        if td != gd:
            closed_fixed += 1
            if args.apply:
                pos["game_date"] = td
                pos["game_date_corrected_from"] = gd
                pos["game_date_correction_ref"] = "GG-166/T-429"
                # Outcome was computed against the WRONG date's box score at
                # resolution time. Correcting the date here does not fix
                # actual_hits/outcome/pnl — that needs a real re-fetch. Flag it.
                pos["game_date_corrected_but_outcome_stale"] = True

    print(f"OPEN positions:   {len(open_positions)} total, {open_fixed} to fix, {open_unparseable} unparseable ticker")
    print(f"CLOSED positions: {len(closed_positions)} total, {closed_fixed} to fix, {closed_unparseable} unparseable ticker")
    print(f"  (closed fixes correct game_date only — outcome/pnl re-derivation is out of scope, see docstring)")

    if not args.apply:
        print("\nDRY RUN — no changes written. Re-run with --apply to write.")
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = ledger_path.with_name(f"{ledger_path.stem}.pre_gg166_correction_{ts}{ledger_path.suffix}")
    shutil.copy2(ledger_path, backup_path)
    print(f"\nBacked up ledger to {backup_path}")

    with ledger_path.open("w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote corrected ledger to {ledger_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

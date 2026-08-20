#!/usr/bin/env python3
"""T-470 — how many of the 532 corrupted epoch-12 positions (GG-185/GG-170)
are re-derivable from the extended t4_mlb_outcome_store.jsonl.

Read-only: does not touch the ledger or the outcome store. Recomputes the
corrupted-532 population directly from the ledger (ticker-embedded date vs.
stored game_date, same method as CLAUDE.md Q7 / the governance scan) rather
than trusting a prior count, then joins against the outcome store by ticker.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"

_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}
_TICKER_DATE_RE = re.compile(r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})")


def ticker_date(ticker: str) -> str | None:
    m = _TICKER_DATE_RE.match(ticker or "")
    if not m:
        return None
    yy, mon, dd, _hhmm = m.groups()
    month = _MONTHS.get(mon)
    return f"20{yy}-{month}-{dd}" if month else None


def main() -> None:
    rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
    epoch12 = [r for r in rows if r.get("logic_epoch") == 12]
    corrupted = [
        r for r in epoch12
        if ticker_date(r.get("kalshi_ticker", "")) not in (None, r.get("game_date"))
    ]

    store = {}
    for line in open(STORE):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        store[rec["ticker"]] = rec

    rederivable = []
    not_in_store = []
    in_store_unresolved = []

    for r in corrupted:
        t = r.get("kalshi_ticker")
        rec = store.get(t)
        if rec is None:
            not_in_store.append(r)
        elif rec.get("resolved"):
            rederivable.append((r, rec))
        else:
            in_store_unresolved.append((r, rec))

    print(f"epoch-12 n={len(epoch12)}  corrupted n={len(corrupted)}")
    print(f"RE-DERIVABLE (ticker in store, resolved=true): {len(rederivable)}")
    print(f"NOT in store at all: {len(not_in_store)}")
    print(f"in store but unresolved (all attempts failed): {len(in_store_unresolved)}")

    if in_store_unresolved:
        print("\n--- unresolved reasons (last attempt per ticker) ---")
        from collections import Counter
        reasons = Counter()
        for _, rec in in_store_unresolved:
            attempts = rec.get("attempts", [])
            if attempts:
                last = attempts[-1]
                reasons[f"{last.get('source')}: {last.get('detail')}"] += 1
            else:
                reasons["no attempts recorded"] += 1
        for reason, n in reasons.most_common(20):
            print(f"  {n:4d}  {reason}")

    if not_in_store:
        print(f"\n--- sample of {min(10, len(not_in_store))} tickers not in store at all ---")
        for r in not_in_store[:10]:
            print(f"  {r.get('kalshi_ticker')}  game_date={r.get('game_date')}  ticker_date={ticker_date(r.get('kalshi_ticker',''))}")

    out = {
        "epoch12_n": len(epoch12),
        "corrupted_n": len(corrupted),
        "rederivable_n": len(rederivable),
        "not_in_store_n": len(not_in_store),
        "unresolved_n": len(in_store_unresolved),
    }
    with open("/tmp/t470_rederivable_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nWritten: /tmp/t470_rederivable_result.json")


if __name__ == "__main__":
    main()

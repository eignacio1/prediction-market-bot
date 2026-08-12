#!/usr/bin/env python3
"""T-437 Task 2 — classify the ~1,220 game_date_corrected_but_outcome_stale
positions as GG-166 (write-time date bug fully explains the stored-outcome
discrepancy) vs GG-170 (API date-label instability on an otherwise-correct
query) vs neither (no discrepancy / coincidental agreement).

Ground truth source: the T-421 decoupled outcome store
(logs/t4_mlb_outcome_store.jsonl), independently resolved off-VPS on
2026-08-07 using the ticker-derived (correct) game_date for every position —
validated as authoritative by T-437 Task 1 (69/69 fresh live re-fetches,
days later, matched the store and disagreed with the ledger; 0% "neither").

Classification logic per stale position:
  - No store match / store unresolved  -> UNRESOLVED (needs live fetch, Task 3)
  - store.actual_hits == ledger.actual_hits (both computed with DIFFERENT
    dates, i.e. wrong-date query coincidentally agrees) -> NEITHER
    (no outcome corruption despite the date bug)
  - store.actual_hits != ledger.actual_hits -> GG166
    (the wrong game_date used at original resolution is a sufficient,
    direct explanation: the ledger queried a different game entirely, not
    a same-day API label wobble; GG-170's specific mechanism — instability
    on an otherwise-CORRECT date query — does not apply to how these
    records were originally produced, since none of them queried the
    correct date at resolution time)

Read-only. No writes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO = _REPO_ROOT / "logs" / ".vps_portfolio_cache_mlb_t4.json"
STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"


def main() -> None:
    data = json.load(open(PORTFOLIO))
    closed = data.get("closed_positions", [])
    store = {}
    with open(STORE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            store[r["ticker"]] = r

    stale = [p for p in closed if p.get("game_date_corrected_but_outcome_stale")]
    print(f"stale population: {len(stale)}")

    counts = {"GG166": 0, "NEITHER": 0, "UNRESOLVED": 0}
    by_epoch: dict = {}
    rows = []
    for p in stale:
        ticker = p.get("kalshi_ticker", "")
        srec = store.get(ticker)
        epoch = p.get("logic_epoch")
        by_epoch.setdefault(epoch, {"GG166": 0, "NEITHER": 0, "UNRESOLVED": 0})

        if srec is None or not srec.get("resolved") or srec.get("actual_hits") is None:
            tag = "UNRESOLVED"
        else:
            ledger_hits = p.get("actual_hits")
            store_hits = srec.get("actual_hits")
            if ledger_hits is None:
                tag = "UNRESOLVED"
            elif float(ledger_hits) == float(store_hits):
                tag = "NEITHER"
            else:
                tag = "GG166"

        counts[tag] += 1
        by_epoch[epoch][tag] += 1
        rows.append({
            "position_id": p.get("position_id"),
            "ticker": ticker,
            "logic_epoch": epoch,
            "game_date": p.get("game_date"),
            "game_date_corrected_from": p.get("game_date_corrected_from"),
            "ledger_hits": p.get("actual_hits"),
            "ledger_outcome": p.get("outcome"),
            "store_hits": srec.get("actual_hits") if srec else None,
            "classification": tag,
        })

    print("\n=== Classification counts (n=1220 stale population) ===")
    for k, v in counts.items():
        print(f"  {k}: {v}  ({v/len(stale):.1%})")

    print("\n=== By epoch ===")
    for e in sorted(by_epoch, key=lambda x: (x is None, x)):
        c = by_epoch[e]
        tot = sum(c.values())
        print(f"  epoch={e}: total={tot} GG166={c['GG166']} NEITHER={c['NEITHER']} UNRESOLVED={c['UNRESOLVED']}")

    out_path = _REPO_ROOT / "logs" / "t437_task2_classification.json"
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2, default=str)
    print(f"\nfull row dump written to {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""T-437 Task 1 — settle-authority check.

Build Set A: closed T4M-PROJ positions NOT in the game_date_corrected_but_
outcome_stale population (i.e. game_date already matched the ticker at
resolution time — GG-166's write-time bug does not apply) where the ledger's
actual_hits disagrees with the independently-sourced outcome store's
actual_hits (GG-170's pure signature, unconfounded by GG-166).

Sample >=50 such (player_id, game_date) pairs, re-fetch fresh from the live
MLB Stats API / ESPN fallback NOW (days after GG-170's near-real-time
instability was observed), and report the three-way split: fresh fetch
matches store / matches ledger / matches neither.

Read-only. Off-VPS network (GG-084). No writes to the ledger or portfolio.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from prediction_market_bot.run_resolve_mlb import _fetch_mlb_hits, _espn_fetch_hits  # noqa: E402
from prediction_market_bot.logic_epoch import is_clean_for_band  # noqa: E402

PORTFOLIO = _REPO_ROOT / "logs" / ".vps_portfolio_cache_mlb_t4.json"
STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
BAND = "T4M-PROJ"

_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}
_TICKER_DATE_RE = re.compile(r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})")


def ticker_game_date(ticker: str) -> str | None:
    m = _TICKER_DATE_RE.match(ticker)
    if not m:
        return None
    yy, mon, dd, _hhmm = m.groups()
    month = _MONTHS.get(mon)
    if month is None:
        return None
    return f"20{yy}-{month}-{dd}"


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


def main() -> None:
    data = json.load(open(PORTFOLIO))
    closed = data.get("closed_positions", [])
    store = load_store()

    set_a = []
    for p in closed:
        if not is_clean_for_band(p.get("logic_epoch"), BAND):
            continue  # matches GG-166 B5's own clean-cohort definition
        ticker = p.get("kalshi_ticker", "")
        gd_true = ticker_game_date(ticker)
        gd_recorded = p.get("game_date")
        if gd_true is None or gd_recorded != gd_true:
            continue  # game_date must match ticker (true post-correction for ~100% of this cohort per B5)
        if p.get("outcome") not in ("WIN", "LOSS") or p.get("actual_hits") is None:
            continue
        srec = store.get(ticker)
        if srec is None or not srec.get("resolved"):
            continue
        store_hits = srec.get("actual_hits")
        ledger_hits = p.get("actual_hits")
        if store_hits is None:
            continue
        if float(store_hits) == float(ledger_hits):
            continue  # agrees — not part of the disagreement pool
        set_a.append({
            "position_id": p.get("position_id"),
            "ticker": ticker,
            "player_id": p.get("player_id"),
            "player_name": p.get("player_name"),
            "game_date": gd_true,
            "ledger_hits": ledger_hits,
            "ledger_outcome": p.get("outcome"),
            "store_hits": store_hits,
            "store_source": srec.get("resolution_source"),
            "resolved_at": p.get("resolved_at"),
        })

    print(f"Set A (date-clean, ledger-vs-store hits disagreement) size: {len(set_a)}")

    random.seed(437)
    sample = list(set_a)  # take the full disagreement pool (n=69 at time of writing, >=50 required)
    print(f"Sampling {len(sample)} pairs for live re-fetch")

    results = []
    match_store = 0
    match_ledger = 0
    match_neither = 0
    match_both = 0  # store==ledger (shouldn't happen, sanity)
    for i, row in enumerate(sample, start=1):
        fresh = _fetch_mlb_hits(row["player_id"], row["game_date"])
        source = "MLB_R"
        if fresh is None:
            fresh = _espn_fetch_hits(row["player_name"], row["game_date"])
            source = "ESPN"
        row["fresh_hits"] = fresh
        row["fresh_source"] = source if fresh is not None else None

        ls = float(row["ledger_hits"])
        ss = float(row["store_hits"])
        fs = fresh if fresh is None else float(fresh)

        if fs is None:
            tag = "UNRESOLVED"
        elif fs == ss and fs == ls:
            tag = "BOTH"
            match_both += 1
        elif fs == ss:
            tag = "STORE"
            match_store += 1
        elif fs == ls:
            tag = "LEDGER"
            match_ledger += 1
        else:
            tag = "NEITHER"
            match_neither += 1
        row["match"] = tag
        results.append(row)
        print(f"  [{i}/{len(sample)}] {row['player_name']} {row['game_date']} "
              f"ledger={ls} store={ss} fresh={fs} -> {tag}")

    n_resolved = sum(1 for r in results if r["match"] != "UNRESOLVED")
    print("\n=== SPLIT (of resolved fresh fetches) ===")
    print(f"total sampled: {len(results)}  unresolved(fresh fetch failed): {len(results) - n_resolved}")
    print(f"matches STORE only: {match_store}")
    print(f"matches LEDGER only: {match_ledger}")
    print(f"matches BOTH (store==ledger, fresh confirms either): {match_both}")
    print(f"matches NEITHER: {match_neither}")
    if n_resolved:
        print(f"\nSTORE authority rate: {(match_store + match_both) / n_resolved:.1%}")
        print(f"LEDGER authority rate: {(match_ledger + match_both) / n_resolved:.1%}")
        print(f"NEITHER rate: {match_neither / n_resolved:.1%}")

    out_path = _REPO_ROOT / "logs" / "t437_task1_settle_check.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nfull row dump written to {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""GG-149: one-off retroactive tagging of locked-pair positions in the T4 MLB
ledger — same kalshi_ticker, opposite direction, overlapping open intervals.

A locked pair is a wash trade under Kalshi's CFTC-DCM rules: the account held
both YES and NO on one contract simultaneously with zero net edge information.
Per ADR-0050's pre-registration addendum (item h), both legs of every locked
pair are EXCLUDED from the measurement cohort, retroactively and
prospectively. This script does NOT delete or alter P&L — it stamps
`locked_pair: true` + `locked_pair_counterpart: <position_id>` onto affected
rows in a copy of the ledger; downstream analysis filters on that flag.

Usage:
    python3 scripts/tag_locked_pairs_t4_mlb.py <portfolio_json_path> [--write]

Without --write, runs in dry-run mode: prints the count of tagged tickers
and positions, does not modify the input file. Pass --write to write the
tagged output to <path>.tagged.json (never overwrites the input in place).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def _parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def find_locked_pairs(positions: list[dict]) -> dict[str, list[dict]]:
    """Group positions by ticker; within each ticker group, find pairs with
    opposite directions whose [entered_at, exited_at-or-now] intervals
    overlap. Returns {ticker: [position, ...]} for every ticker with >=1
    locked pair, listing every position involved (both legs, all pairs).
    """
    by_ticker: dict[str, list[dict]] = {}
    for p in positions:
        t = p.get("kalshi_ticker")
        if t:
            by_ticker.setdefault(t, []).append(p)

    locked: dict[str, list[dict]] = {}
    for ticker, plist in by_ticker.items():
        if len(plist) < 2:
            continue
        directions = {p.get("direction") for p in plist}
        if len(directions) < 2:
            continue  # all same direction — governed by the existing state-dedup guard, not this

        intervals = []
        for p in plist:
            try:
                start = _parse_ts(p["entered_at"])
            except Exception:
                continue
            end_raw = p.get("exited_at")
            end = _parse_ts(end_raw) if end_raw else datetime.now(timezone.utc)
            intervals.append((start, end, p))

        flagged: list[dict] = []
        for i in range(len(intervals)):
            si, ei, pi = intervals[i]
            for j in range(i + 1, len(intervals)):
                sj, ej, pj = intervals[j]
                if pi.get("direction") == pj.get("direction"):
                    continue
                if si <= ej and sj <= ei:  # overlap
                    if pi not in flagged:
                        flagged.append(pi)
                    if pj not in flagged:
                        flagged.append(pj)
                    pi["_locked_pair_counterpart"] = pj.get("position_id")
                    pj["_locked_pair_counterpart"] = pi.get("position_id")
        if flagged:
            locked[ticker] = flagged
    return locked


def tag(portfolio: dict) -> tuple[dict, int, int]:
    all_positions = list(portfolio.get("open_positions", [])) + list(portfolio.get("closed_positions", []))
    locked = find_locked_pairs(all_positions)

    tagged_ids = set()
    for ticker, plist in locked.items():
        for p in plist:
            p["locked_pair"] = True
            p["locked_pair_counterpart"] = p.pop("_locked_pair_counterpart", None)
            if p.get("position_id"):
                tagged_ids.add(p["position_id"])

    return portfolio, len(locked), len(tagged_ids)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    write = "--write" in sys.argv[2:]

    with open(path) as f:
        portfolio = json.load(f)

    portfolio, n_tickers, n_positions = tag(portfolio)

    print(f"Locked-pair tickers found: {n_tickers}")
    print(f"Locked-pair positions (both legs) tagged: {n_positions}")

    if write:
        out_path = path + ".tagged.json"
        with open(out_path, "w") as f:
            json.dump(portfolio, f, indent=2)
        print(f"Written: {out_path}")
    else:
        print("Dry run — pass --write to produce a tagged copy.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

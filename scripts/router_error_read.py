#!/usr/bin/env python3
"""READ-ONLY (W125.2 / GG-2007): why router rows reached no leaf.

Reads logs/arm_orders/orders.jsonl (plain or .gz) and groups every skip whose arm is ERROR or UNROUTED by the router's own reason
(the exception type and message logged in split_path.reason, digits collapsed so one cause is one key), sport, market_type, band
and UTC date. Post-epoch only (GG-1771, 2026-11-06T01:03:42Z) unless --all. Writes nothing: stdout JSON, bounded.
Python 3.9-safe (the box).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
LOG = REPO / "logs" / "arm_orders" / "orders.jsonl"
EPOCH = datetime(2026, 11, 6, 1, 3, 42, tzinfo=timezone.utc)
BAD_ARMS = ("ERROR", "UNROUTED")

from prediction_market_bot.timeparse import parse_ts  # noqa: E402
from prediction_market_bot import io_jsonl  # noqa: E402


def cause_key(reason: Optional[str]) -> str:
    """One cause, one key: digits and quoted ticker-like tokens collapse so a KeyError per ticker is not 1,000 keys."""
    s = str(reason or "(no reason logged)")
    s = re.sub(r"'[^']{0,80}'", "'<x>'", s)
    s = re.sub(r"\d+(\.\d+)?", "<n>", s)
    return s[:120]


def summarise(rows: List[dict], epoch: Optional[datetime] = EPOCH) -> dict:
    total = Counter()
    by_cause: Dict[str, Counter] = defaultdict(Counter)
    by_cause_sport: Dict[str, Counter] = defaultdict(Counter)
    by_cause_cell: Dict[str, Counter] = defaultdict(Counter)
    by_date: Dict[str, Counter] = defaultdict(Counter)
    examples: Dict[str, dict] = {}
    n_rows = 0
    per_day_all: Dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        if r.get("event") != "arm_skip":
            continue
        n_rows += 1
        ts = parse_ts(r.get("ts"))
        if ts is not None and (epoch is None or ts >= epoch):
            # W126.1: every skip row per sport and day, so a day with zero ERROR rows is a real zero, not a day with no rows.
            per_day_all[ts.strftime("%Y-%m-%d")][str(r.get("sport") or "?").upper()] += 1
        if r.get("arm") not in BAD_ARMS:
            continue
        if epoch is not None and (ts is None or ts < epoch):
            continue
        sp = r.get("split_path") or {}
        key = f"{r.get('arm')}|{cause_key(sp.get('reason'))}"
        sport = str(r.get("sport") or "?").upper()
        cell = f"{sport}_{r.get('market_type')}|{r.get('band')}"
        day = ts.strftime("%Y-%m-%d") if ts else "?"
        total[r["arm"]] += 1
        by_cause[key][sport] += 1
        by_cause_sport[key][sport] += 1
        by_cause_cell[key][cell] += 1
        by_date[day][key] += 1
        examples.setdefault(key, {"reason": str(sp.get("reason"))[:200], "ticker": r.get("ticker"), "ts": r.get("ts")})
    return {"skip_rows_seen": n_rows, "total_by_arm": dict(total),
            "causes": {k: {"n": sum(v.values()), "by_sport": dict(v), "by_cell": dict(by_cause_cell[k].most_common(12)),
                           "example": examples[k]} for k, v in sorted(by_cause.items(), key=lambda kv: -sum(kv[1].values()))},
            "per_day": {d: dict(c) for d, c in sorted(by_date.items())},
            "skip_rows_per_day_by_sport": {d: dict(c) for d, c in sorted(per_day_all.items())}}


def load(path: Path) -> List[dict]:
    out: List[dict] = []
    try:
        with io_jsonl.open_jsonl(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except (OSError, EOFError):
        pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include pre-epoch rows")
    ap.add_argument("--log", default=str(LOG))
    a = ap.parse_args()
    print(json.dumps(summarise(load(Path(a.log)), None if a.all else EPOCH), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

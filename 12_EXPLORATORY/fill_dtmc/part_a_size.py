"""W86.3 Part A: resting size at the top of book and within 5c, by family x time-to-start; snapshot persistence.

Source: exp_output/PRICE_ARCHIVE/depth_*.jsonl (PRODUCTION public order books, not demo books).
A taker buying YES consumes the NO-side top level, buying NO consumes the YES-side top level, so each usable row
yields two observations. Only the top level and the cumulative within-5c size are recorded, never a full ladder:
"size that moves the price 1 tier" is exact (top level); "size that moves it 2 cents" is only bracketed
[top, within_5c] and is reported as that bracket.
"""
from __future__ import annotations

import glob
import json
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402

MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
TICK = re.compile(r"-(\d\d)([A-Z]{3})(\d\d)(\d{4})?")
BUCKETS = [("started", None, 0), ("0-60m", 0, 60), ("60-180m", 60, 180), ("180-720m", 180, 720), (">720m", 720, 1e9)]


def parse_ts(s: str) -> datetime:
    """Tolerant ISO parse for py3.9 (Kalshi 5-digit fractional seconds)."""
    s = s.replace("Z", "+00:00")
    m = re.match(r"(.*?)(\.\d+)?(\+.*)?$", s)
    base, frac, tz = m.group(1), m.group(2) or "", m.group(3) or "+00:00"
    frac = (frac + "000000")[:7] if frac else ""
    return datetime.fromisoformat(base + frac + tz)


def start_utc(ticker: str) -> Optional[datetime]:
    m = TICK.search(ticker)
    if not m or not m.group(4) or m.group(2) not in MON:
        return None
    y, mo, d, hm = 2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), m.group(4)
    off = 4 if (mo, d) < (11, 1) and (mo, d) >= (3, 8) else 5  # ET->UTC; DST boundary approx, window is Aug-Oct
    try:
        return datetime(y, mo, d, int(hm[:2]), int(hm[2:]), tzinfo=timezone.utc) + timedelta(hours=off)
    except ValueError:
        return None


def game_key(ticker: str) -> str:
    parts = ticker.split("-")
    return parts[1] if len(parts) > 1 else ticker


def bucket(ttl_min: Optional[float]) -> str:
    if ttl_min is None:
        return "unknown"
    if ttl_min < 0:
        return "started"
    for name, lo, hi in BUCKETS[1:]:
        if lo <= ttl_min < hi:
            return name
    return "unknown"


def q(v: List[float], p: float) -> float:
    s = sorted(v)
    return s[min(len(s) - 1, int(p * len(s)))]


def boot_median(groups: Dict[str, List[float]], reps: int = 300, seed: int = 86):
    keys = list(groups)
    if len(keys) < 5:
        return None
    rng = random.Random(seed)
    meds = []
    for _ in range(reps):
        pool: List[float] = []
        for _k in keys:
            pool.extend(groups[keys[rng.randrange(len(keys))]])
        meds.append(q(pool, 0.5))
    meds.sort()
    return [meds[int(0.025 * reps)], meds[int(0.975 * reps)]]


def main(depth_glob: str, out_json: str) -> None:
    rows = []
    for f in sorted(glob.glob(depth_glob)):
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("usable"):
                rows.append(r)
    cells: Dict[tuple, Dict[str, list]] = defaultdict(lambda: {"top": defaultdict(list), "w5": defaultdict(list)})
    for r in rows:
        st = start_utc(r["ticker"])
        ttl = (st - parse_ts(r["run_ts"])).total_seconds() / 60 if st else None
        key = (r["family"], bucket(ttl))
        g = game_key(r["ticker"])
        for side in ("yes", "no"):
            cells[key]["top"][g].append(float(r["top_of_book_contracts"][side]))
            cells[key]["w5"][g].append(float(r["within_5c_contracts"][side]))
    out = {"n_usable_rows": len(rows), "cells": {}}
    for (fam, b), d in sorted(cells.items()):
        top = [x for v in d["top"].values() for x in v]
        w5 = [x for v in d["w5"].values() for x in v]
        out["cells"]["%s|%s" % (fam, b)] = {
            "n_obs": len(top), "n_games": len(d["top"]),
            "top_p10_p50_p90": [q(top, .1), q(top, .5), q(top, .9)],
            "top_median_ci95_game_clustered": boot_median(d["top"]),
            "within5c_p10_p50_p90": [q(w5, .1), q(w5, .5), q(w5, .9)],
            "share_top_lt_100": sum(x < 100 for x in top) / len(top),
        }
    # persistence of the top level between consecutive snapshots of one ticker
    by_t: Dict[str, list] = defaultdict(list)
    for r in rows:
        by_t[r["ticker"]].append((parse_ts(r["run_ts"]), r))
    pers: Dict[str, List[float]] = defaultdict(list)
    for tk, lst in by_t.items():
        lst.sort(key=lambda x: x[0])
        for (t0, a), (t1, b) in zip(lst, lst[1:]):
            gap = (t1 - t0).total_seconds() / 60
            gb = "<30m" if gap < 30 else "30-90m" if gap < 90 else ">90m"
            for side in ("yes", "no"):
                x0, x1 = a["top_of_book_contracts"][side], b["top_of_book_contracts"][side]
                if x0 > 0:
                    pers[gb].append(x1 / x0)
    out["persistence_top_ratio_next_over_prev"] = {
        k: {"n": len(v), "p10_p50_p90": [q(v, .1), q(v, .5), q(v, .9)], "share_ge_0.9": sum(x >= .9 for x in v) / len(v)}
        for k, v in sorted(pers.items())}
    out["note"] = ("production public books; one-tier size exact, 2c size bracketed [top, within_5c]; refill vs "
                   "consumption not separable from snapshots 20-40 min apart")
    p = safe_out(out_json)
    p.write_text(json.dumps(out, indent=1))
    print("wrote", p, "cells", len(out["cells"]), "rows", len(rows))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

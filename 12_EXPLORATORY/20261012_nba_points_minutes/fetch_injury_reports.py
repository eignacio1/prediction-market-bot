"""Fetch NBA official injury-report PDFs per game date; cache PDFs inside the fence (gitignored, never committed), write small parsed JSON.

usage: fetch_injury_reports.py <cache_dir> <out_dir> <date1> [<date2> ...]   (dates YYYY-MM-DD, ET; both dirs must lie inside 12_EXPLORATORY - writes go through _fence.safe_out)
Writes <out_dir>/inj_<date>.json = {"HH:30": {name: status}} for every hourly slot found.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _fence import safe_out  # noqa: E402
from injury_parse import parse_pdf  # noqa: E402

URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{d}_{h:02d}{ap}.pdf"
# 2-hourly grid (compute-bounded; README amended): 11:30 13:30 15:30 17:30 19:30 ET
SLOTS = [(11, "AM"), (1, "PM"), (3, "PM"), (5, "PM"), (7, "PM")]


def slot_key(h: int, ap: str) -> str:
    h24 = (h % 12) + (12 if ap == "PM" else 0)
    return f"{h24:02d}:30"


def get(d: str, h: int, ap: str, cache: str):
    p = os.path.join(cache, f"{d}_{h:02d}{ap}.pdf")
    if not os.path.exists(p):
        try:
            with urllib.request.urlopen(URL.format(d=d, h=h, ap=ap), timeout=30) as r:
                data = r.read()
        except Exception:
            return None
        safe_out(p).write_bytes(data)
    try:
        return slot_key(h, ap), parse_pdf(p)
    except Exception:
        return None


def do_date(d: str, cache: str, out: str) -> int:
    fp = os.path.join(out, f"inj_{d}.json")
    if os.path.exists(fp):
        return -1
    res = {}
    for h, ap in SLOTS:
        r = get(d, h, ap, cache)
        if r:
            res[r[0]] = r[1]
    safe_out(fp).write_text(json.dumps(res, sort_keys=True))
    return len(res)


if __name__ == "__main__":
    cache, out, *dates = sys.argv[1:]
    os.makedirs(cache, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    with ProcessPoolExecutor(8) as ex:
        for d, n in zip(dates, ex.map(do_date, dates, [cache] * len(dates), [out] * len(dates))):
            print(d, n, flush=True)

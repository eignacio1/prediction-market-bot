"""W71.3 Part A: re-fetch 2025-26 NBA injury reports across the 2025-12-22 URL rename (GG-620).
Same parser (../20261012_nba_points_minutes/injury_parse.py) and same 2-hourly ET slot grid as the W69.3 study and the live module.
usage: fetch_injury_v2.py <cache_dir> <out_dir> <date> ...   Writes <out_dir>/inj_<date>.json = {"HH:30": {name: status}}.
PDFs are cached inside the fence (gitignored); only the small parsed JSON is committed."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "20261012_nba_points_minutes"))
from _fence import safe_out  # noqa: E402
from injury_parse import parse_pdf  # noqa: E402

URL_V1 = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{d}_{h:02d}{ap}.pdf"
URL_V2 = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{d}_{h:02d}_30{ap}.pdf"
SLOTS = [(11, "AM"), (1, "PM"), (3, "PM"), (5, "PM"), (7, "PM")]


def key(h, ap):
    return f"{(h % 12) + (12 if ap == 'PM' else 0):02d}:30"


def get(d, h, ap, cache):
    p = os.path.join(cache, f"{d}_{h:02d}{ap}.pdf")
    if not os.path.exists(p):
        url = (URL_V2 if d >= "2025-12-22" else URL_V1).format(d=d, h=h, ap=ap)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
        except Exception:
            return None
        safe_out(p).write_bytes(data)
    try:
        return key(h, ap), parse_pdf(p)
    except Exception:
        return None


def do_date(args):
    d, cache, out = args
    fp = os.path.join(out, f"inj_{d}.json")
    if os.path.exists(fp):
        return d, -1
    res = {}
    for h, ap in SLOTS:
        r = get(d, h, ap, cache)
        if r:
            res[r[0]] = r[1]
    safe_out(fp).write_text(json.dumps(res, sort_keys=True))
    return d, len(res)


if __name__ == "__main__":
    cache, out, *dates = sys.argv[1:]
    os.makedirs(cache, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    with ProcessPoolExecutor(8) as ex:
        for d, n in ex.map(do_date, [(d, cache, out) for d in dates]):
            print(d, n, flush=True)

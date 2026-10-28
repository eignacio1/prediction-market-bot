"""W90.3 -- cache Kalshi's own settled `result` for the archived series. Public unauthenticated GETs only.

  python 12_EXPLORATORY/momentum_j/fetch_settle.py --out <dir> [--since-ts 1785000000]

Writes <dir>/<SERIES>.json = {ticker: {"result": "yes"|"no"}}. Read-only on Kalshi; no auth, no order path.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _fence import safe_out  # noqa: E402

BASE = "https://api.elections.kalshi.com/trade-api/v2/markets"
SERIES = ["KXMLBGAME", "KXMLBSPREAD", "KXMLBTOTAL", "KXMLBTEAMTOTAL", "KXMLBF5", "KXMLBF5TOTAL", "KXMLBF5SPREAD",
          "KXMLBF3", "KXMLBF7", "KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL"]


def fetch_series(series: str, since_ts: int) -> dict:
    out, cursor = {}, ""
    while True:
        url = f"{BASE}?series_ticker={series}&status=settled&limit=1000&min_close_ts={since_ts}" + (f"&cursor={cursor}" if cursor else "")
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    d = json.load(r)
                break
            except Exception:
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"fetch failed: {series}")
        for m in d.get("markets", []):
            if m.get("result") in ("yes", "no"):
                out[m["ticker"]] = {"result": m["result"]}
        cursor = d.get("cursor") or ""
        if not cursor or not d.get("markets"):
            return out
        time.sleep(0.15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--since-ts", type=int, default=1785000000)
    a = ap.parse_args()
    for s in SERIES:
        d = fetch_series(s, a.since_ts)
        with open(safe_out(os.path.join(a.out, f"{s}.json")), "w") as fh:
            json.dump(d, fh)
        print(s, len(d), flush=True)


if __name__ == "__main__":
    main()

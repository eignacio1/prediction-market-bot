"""W105.6 Part B: settled results for the archived sports tickers, from Kalshi's public unauthenticated GETs.

Read-only. Writes {ticker: {"result": "yes"|"no", "close_time": ...}} per series to --out (one JSON per series).
Live endpoint first (status=settled), then /historical/markets for anything the live endpoint no longer lists.
Usage: python fetch_settlements.py --series KXNHLGAME,KXNBAGAME --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _fence import safe_out  # noqa: E402

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def get(path: str, params: dict, tries: int = 4) -> dict:
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pmbot-research-readonly"})
            return json.load(urllib.request.urlopen(req, timeout=40))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + 3 * i)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1 + i)
    raise RuntimeError("fetch failed: " + url)


def pull(path: str, series: str, extra: dict) -> dict:
    out, cursor = {}, None
    while True:
        p = {"series_ticker": series, "limit": 1000, **extra}
        if cursor:
            p["cursor"] = cursor
        d = get(path, p)
        for m in d.get("markets", []):
            if m.get("result") in ("yes", "no"):
                out[m["ticker"]] = {"result": m["result"], "close_time": m.get("close_time")}
        cursor = d.get("cursor")
        if not cursor or not d.get("markets"):
            return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out_dir = safe_out(os.path.abspath(os.path.join(a.out, ".keep"))).parent  # every write goes through the fence
    for s in a.series.split(","):
        res = pull("/markets", s, {"status": "settled"})
        n_live = len(res)
        try:
            res.update({k: v for k, v in pull("/historical/markets", s, {}).items() if k not in res})
        except Exception as e:  # historical may not list a series; the live count stands
            print(s, "historical:", type(e).__name__, e)
        with open(safe_out(out_dir / (s + ".json")), "w") as fh:
            json.dump(res, fh)
        print(s, "live", n_live, "total", len(res), flush=True)


if __name__ == "__main__":
    main()

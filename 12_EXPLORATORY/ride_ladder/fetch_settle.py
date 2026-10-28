"""W91.2 Part B: settled results for every archived totals/spread/team-total event (public unauthenticated Kalshi GETs only).

Usage: python 12_EXPLORATORY/ride_ladder/fetch_settle.py <PRICE_ARCHIVE dir> out/settle_cache.json
Tries the live endpoint per event, falls back to the historical endpoint. Read-only; paced ~5 req/s.
"""
import glob
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402

SERIES = ("KXNFLTOTAL", "KXNFLSPREAD", "KXNFLTEAMTOTAL", "KXMLBTOTAL", "KXMLBSPREAD", "KXMLBTEAMTOTAL")
BASE = "https://api.elections.kalshi.com/trade-api/v2/"


def get(path):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(BASE + path, timeout=25))
        except Exception:
            time.sleep(1 + i)
    return {}


def main(archive, out):
    events = set()
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            if r["series_ticker"] in SERIES:
                events.add(r["event_ticker"])
    res, done = {}, 0
    for e in sorted(events):
        for path in ("markets?event_ticker=%s&limit=200", "historical/markets?event_ticker=%s&limit=200"):
            ms = get(path % e).get("markets", [])
            ms = [m for m in ms if m.get("result") in ("yes", "no")]
            if ms:
                for m in ms:
                    res[m["ticker"]] = {"result": m["result"], "settle_ts": m.get("settlement_ts") or m.get("expiration_time"), "close_time": m.get("close_time")}
                break
            time.sleep(0.2)
        done += 1
        if done % 200 == 0:
            print(done, len(events), len(res), flush=True)
        time.sleep(0.15)
    json.dump(res, open(safe_out(out), "w"))
    print("events", len(events), "settled tickers", len(res))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

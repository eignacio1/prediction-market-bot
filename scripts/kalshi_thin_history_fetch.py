#!/usr/bin/env python3
"""W78.2: thinner-market (NFL / NBA) Kalshi price-history inventory + backfill. Public unauthenticated GETs only.

Store: exp_output/KALSHI_HISTORY/thin/ (git-ignored raw; committed manifest = 12_EXPLORATORY/thin_markets/MANIFEST.md).
Reuses board_survey_sports_store (paced client, append-only content-hashed raw store, provenance per row).

  inventory   every NFL/NBA series -> settled markets since FROM_ISO (+ currently open), per-series counts, strikes/event.
  fetch       candles for a deterministic per-family sample (see SAMPLE_CAP) -- hourly over the life, 1-minute for the last 48h.
  summary     counts of what the raw store holds (candle sets per series), written as JSON.

Kalshi keeps NO historical order book: candles carry yes_bid/yes_ask OHLC + volume + open interest only, so quoted depth
is observable only from a live book snapshot (the `book` subcommand takes one, read-only).
No order-related endpoint is touched. Resumable: a stored (kind,key) is skipped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_store as bs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "exp_output" / "KALSHI_HISTORY" / "thin"
FROM_ISO = "2025-08-01T00:00:00Z"
CUTOFF = "2026-08-17T00:00:00Z"            # /historical/cutoff market_settled_ts read 2026-10-16
MINUTE_LOOKBACK_S = 48 * 3600
PREFIXES = ("KXNFL", "KXNBA")
SKIP_FREQ = {"annual"}                     # futures / awards / drafts: not game-level, no pre-game efficiency question
SAMPLE_CAP = 250                           # markets per series fetched with candles (deterministic hash order)


def series_list(client):
    j, _ = client.get("/series", category="Sports")
    return sorted(s["ticker"] for s in j["series"]
                  if s["ticker"].startswith(PREFIXES) and (s.get("frequency") or "") not in SKIP_FREQ)


def markets_of(client, store, series, status_paths):
    out, pages = [], 0
    for path, extra in status_paths:
        cursor = None
        while True:
            j, url = client.get(path, series_ticker=series, limit=1000, cursor=cursor, **extra)
            store.put("markets_page", f"{path}|{extra.get('status', '')}|{series}|{cursor or ''}", j, url)
            pages += 1
            out += j.get("markets") or []
            cursor = j.get("cursor") or None
            if not cursor or not j.get("markets"):
                break
    seen, ded = set(), []
    for m in out:
        if m["ticker"] not in seen:
            seen.add(m["ticker"]); ded.append(m)
    return ded


def inventory(client, store, out_json):
    floor = bs.iso_ts(FROM_ISO)
    rows = {}
    for i, s in enumerate(series_list(client)):
        try:
            settled = markets_of(client, store, s, (("/historical/markets", {}), ("/markets", {"status": "settled"})))
            opened = markets_of(client, store, s, (("/markets", {"status": "open"}),))
        except bs.FetchFailed as e:
            rows[s] = {"error": str(e)}; continue
        st = [m for m in settled if m.get("result") and bs.iso_ts(m.get("close_time") or m["expiration_time"]) >= floor]
        ev = Counter(m.get("event_ticker") for m in st)
        month = Counter((m.get("close_time") or "")[:7] for m in st)
        rows[s] = {"settled_since_floor": len(st), "open_now": len(opened), "events": len(ev),
                   "strikes_per_event_median": sorted(ev.values())[len(ev) // 2] if ev else 0,
                   "first_close": min((m["close_time"] for m in st), default=None),
                   "last_close": max((m["close_time"] for m in st), default=None), "by_month": dict(sorted(month.items()))}
        if i % 40 == 0:
            print(i, s, rows[s].get("settled_since_floor"), client.stats(), flush=True)
    Path(out_json).write_text(json.dumps(rows, indent=1, sort_keys=True))
    print("inventory done", client.stats())


def _key(t):
    return hashlib.sha256(t.encode()).hexdigest()


def fetch(client, store, wanted, cap=SAMPLE_CAP):
    cutoff, floor = bs.iso_ts(CUTOFF), bs.iso_ts(FROM_ISO)
    have = set(store.index)
    for series in wanted:
        mk = [m for m in markets_of(client, store, series, (("/historical/markets", {}), ("/markets", {"status": "settled"})))
              if m.get("result") and bs.iso_ts(m.get("close_time") or m["expiration_time"]) >= floor]
        mk.sort(key=lambda m: _key(m["ticker"]))
        pick = mk[:cap]
        print(f"{series}: settled {len(mk)} -> fetching {len(pick)}", flush=True)
        for i, m in enumerate(pick):
            close, opn = bs.iso_ts(m["close_time"]), bs.iso_ts(m["open_time"])
            for period, start in ((60, opn), (1, max(opn, close - MINUTE_LOOKBACK_S))):
                end = close + 3600 if period == 60 else close + 120
                if ("candles", f"{m['ticker']}|{period}|{start}|{end}") in have:
                    continue
                try:
                    bs.candles(client, store, series, m, start, end, period, cutoff)
                except bs.FetchFailed as e:
                    print("FAILED", m["ticker"], period, e, flush=True)
            if i % 300 == 0:
                print(series, i, client.stats(), flush=True)
    print("fetch done", client.stats(), "written", store.written, "skipped", store.skipped, flush=True)


def book(client, tickers, out_json):
    snap = {}
    for t in tickers:
        j, url = client.get(f"/markets/{t}/orderbook")
        snap[t] = {"url": url, "book": j}
    Path(out_json).write_text(json.dumps(snap, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["inventory", "fetch", "book"])
    ap.add_argument("--series", nargs="*", default=[])
    ap.add_argument("--out", default=str(STORE / "inventory.json"))
    ap.add_argument("--cap", type=int, default=SAMPLE_CAP)
    ap.add_argument("--pause", type=float, default=0.2)
    a = ap.parse_args(argv)
    client = bs.Client(pause=a.pause)
    if a.cmd == "book":
        return book(client, a.series, a.out)
    store = bs.Store(STORE)
    if a.cmd == "inventory":
        inventory(client, store, a.out)
    else:
        fetch(client, store, a.series, a.cap)


if __name__ == "__main__":
    main()

"""W109.4 (B-064) -- pre-game quotes for SETTLED prop markets from Kalshi's public batch candlesticks.

Public unauthenticated GETs only. No order, no account, no ledger. Measures the MARKET; touches no model.

* parse_ts(s)                      -- tolerant ISO parse (Z, fractional seconds of any length) -> epoch seconds.
* paged(fetch, path, params, key)  -- follow a cursor to the end. Applies to /markets and /historical/markets.
* list_settled(fetch, series)      -- live + historical settled yes/no markets, de-duplicated by ticker. Scalar / void
                                      results are dropped: they settle to a fair price, not 0/1, so no binary P&L.
* sample_events(markets, n, seed)  -- seeded sample of whole EVENTS (a game's markets stay together: clustering unit).
* fetch_candles(fetch, tickers, start, end, interval) -- batch (<=100 tickers) candles, polite pacing, 429 backoff.
* quote_at(candles, ts)            -- the carried-forward two-sided quote at ts (last candle ending <= ts).
                                      Applies because minute candles are SPARSE (a row exists only when something
                                      changed): the quote persists until the next row. Not valid before the first row.
* entry_rows(market, candles, anchor_ts, leads) -- one row per lead (seconds before anchor): bid, ask, y, ages.

`fetch` is any callable path_with_query -> dict | None, so tests run on fake data.
"""
from __future__ import annotations

import datetime
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Callable, Optional

BASE = "https://api.elections.kalshi.com/trade-api/v2"
Fetch = Callable[[str], Optional[dict]]


def parse_ts(s: str) -> int:
    """ISO-8601 'YYYY-MM-DDTHH:MM:SS[.ffffff]Z' -> epoch seconds (UTC). Fraction is dropped (Python 3.9 safe)."""
    return int(datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp())


def make_fetch(sleep: float = 0.7, tries: int = 6, timeout: int = 60) -> Fetch:
    """Polite public GET. `sleep` seconds after every call; 429 backs off 2+3a s; other HTTP errors return None."""
    def fetch(path: str) -> Optional[dict]:
        for a in range(tries):
            try:
                req = urllib.request.Request(BASE + path, headers={"User-Agent": "research-client"})
                out = json.load(urllib.request.urlopen(req, timeout=timeout))
                time.sleep(sleep)
                return out
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(2 + 3 * a)
                    continue
                return None
            except Exception:
                time.sleep(2)
        return None
    return fetch


def paged(fetch: Fetch, path: str, params: dict, key: str = "markets", max_pages: int = 400) -> list:
    out: list = []
    cursor = ""
    for _ in range(max_pages):
        q = dict(params)
        if cursor:
            q["cursor"] = cursor
        d = fetch(path + "?" + urllib.parse.urlencode(q))
        if not d:
            break
        out.extend(d.get(key) or [])
        cursor = d.get("cursor") or ""
        if not cursor:
            break
    return out


def list_settled(fetch: Fetch, series: str) -> list:
    """Settled binary yes/no markets for a series, live then historical, one row per ticker (live wins)."""
    seen: dict = {}
    for path, extra in (("/markets", {"status": "settled"}), ("/historical/markets", {})):
        for m in paged(fetch, path, dict(extra, series_ticker=series, limit=1000)):
            if m.get("result") in ("yes", "no") and m.get("close_time") and m["ticker"] not in seen:
                seen[m["ticker"]] = m
    return list(seen.values())


def sample_events(markets: list, n_events: int, seed: int = 109) -> list:
    """Seeded sample of whole events (all of an event's markets kept). Applies when the event is the clustering unit."""
    by: dict = defaultdict(list)
    for m in markets:
        by[m["event_ticker"]].append(m)
    keys = sorted(by)
    pick = random.Random(seed).sample(keys, min(n_events, len(keys)))
    return [m for k in sorted(pick) for m in by[k]]


def fetch_candles(fetch: Fetch, tickers: list, start: int, end: int, interval: int = 1) -> dict:
    """{ticker: [candle, ...]} for <=100 tickers in one call. Missing ticker -> []."""
    if len(tickers) > 100:
        raise ValueError("batch endpoint takes at most 100 tickers")
    q = urllib.parse.urlencode({"market_tickers": ",".join(tickers), "start_ts": start, "end_ts": end,
                                "period_interval": interval})
    d = fetch("/markets/candlesticks?" + q)
    out = {t: [] for t in tickers}
    for mk in (d or {}).get("markets", []):
        out[mk["market_ticker"]] = mk.get("candlesticks") or []
    return out


def fetch_candles_one(fetch: Fetch, ticker: str, start: int, end: int, interval: int = 1) -> list:
    """Per-market candles from /historical (settled markets older than the live cutoff are served only here; the
    batch endpoint returns an empty list for them). Applies to any settled ticker; one call per market."""
    q = urllib.parse.urlencode({"start_ts": start, "end_ts": end, "period_interval": interval})
    d = fetch(f"/historical/markets/{ticker}/candlesticks?{q}")
    return (d or {}).get("candlesticks") or []


def _dollars(block: dict, field: str = "close_dollars") -> Optional[float]:
    """Price from either schema: live candles use `close_dollars`, historical candles use `close`."""
    block = block or {}
    v = block.get(field, block.get("close"))
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def quote_at(candles: list, ts: int) -> Optional[dict]:
    """Two-sided quote carried forward to ts: the last candle with end_period_ts <= ts whose bid and ask are both
    present, with 0 < bid <= ask < 1 (a zero bid or a one-dollar ask is no market). Returns bid, ask, age_s (seconds
    since that candle) or None. Applies to sparse candles; None when no usable candle precedes ts."""
    best = None
    for c in candles:
        e = c["end_period_ts"]
        if e > ts:
            break
        best = c
    if best is None:
        return None
    bid, ask = _dollars(best.get("yes_bid")), _dollars(best.get("yes_ask"))
    if bid is None or ask is None or not (0.0 < bid <= ask < 1.0):
        return None
    return {"bid": bid, "ask": ask, "age_s": ts - best["end_period_ts"]}


def entry_rows(market: dict, candles: list, anchor_ts: int, leads: dict) -> list:
    """One row per (label -> lead seconds before anchor_ts) with a usable two-sided quote. y = 1 if result == 'yes'.
    Never uses a candle ending after the entry time, so the quote cannot know the result."""
    rows = []
    cs = sorted(candles, key=lambda c: c["end_period_ts"])
    for label, lead in leads.items():
        t = anchor_ts - lead
        q = quote_at(cs, t)
        if q is None:
            continue
        rows.append({"ticker": market["ticker"], "game": market["event_ticker"], "series": market["ticker"].split("-")[0],
                     "lead": label, "ts": t, "bid": q["bid"], "ask": q["ask"], "age_s": q["age_s"],
                     "y": 1.0 if market["result"] == "yes" else 0.0,
                     "vol": float(market.get("volume_fp") or 0)})
    return rows


def cache_path(root: str, series: str) -> str:
    os.makedirs(root, exist_ok=True)
    return os.path.join(root, f"{series}.candles.jsonl")


def load_cache(root: str, series: str) -> dict:
    p = cache_path(root, series)
    out: dict = {}
    if os.path.exists(p):
        for line in open(p):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            out[r["t"]] = r
    return out

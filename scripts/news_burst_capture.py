#!/usr/bin/env python3
"""W107.2 Part C: news-lag BURST capture -- top-of-book for every open NBA game-line market every INTERVAL_S seconds for
MINUTES minutes around an official injury-report publish window.

Why: the 20-minute price archive cannot see a lag shorter than ~20 minutes (12_EXPLORATORY/news_lag/RESULT.md). This
records the same prices at ~20 s so a lag of 1-20 minutes becomes measurable. Analysis use is governed by whatever
pre-registration consumes the rows, not by this script.

One run = one short process: ONE GET /markets?series_ticker=KXNBAGAME per sweep (top-of-book of every game comes back
in the listing, so no per-market order-book calls), rows streamed straight to a daily JSONL, nothing accumulated in
memory. flock => at most one burst at a time. Public unauthenticated GETs only; no order endpoint, no credentials,
no ledger or model path. Bounds: MINUTES <= 40, INTERVAL_S >= 10, MAX_DAILY_BYTES per UTC day (writes stop, nothing deleted).

Store (git-ignored): exp_output/KALSHI_HISTORY/news_burst/burst_YYYY-MM-DD.jsonl
Usage: python3 scripts/news_burst_capture.py [--minutes 30] [--interval 20] [--store DIR] [--series KXNBAGAME ...]
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_store as bs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "exp_output" / "KALSHI_HISTORY" / "news_burst"
WRITER = "news_burst_capture/1"
SERIES = ("KXNBAGAME",)
MAX_MINUTES = 40
MIN_INTERVAL_S = 10
MAX_DAILY_BYTES = 40 * 1024 * 1024
KEEP = ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "volume", "open_interest")


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sweep(client, series: str, now: float, sha: str, fh) -> int:
    """One listing call -> one compact row per open market; returns rows written."""
    n, cursor = 0, None
    while True:
        j, _ = client.get("/markets", series_ticker=series, status="open", limit=1000, cursor=cursor)
        for m in j.get("markets") or []:
            row = {"ts": _iso(now), "ticker": m["ticker"], "event": m.get("event_ticker"),
                   "close_time": m.get("close_time"), **{k: m.get(k) for k in KEEP if m.get(k) is not None},
                   "sha": sha, "writer": WRITER}
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
            n += 1
        cursor = j.get("cursor") or None
        if not cursor or not j.get("markets"):
            return n


def run(client, store: Path, minutes: float = 30, interval: float = 20, series=SERIES, sha: str | None = None,
        now_fn=time.time, sleep=time.sleep) -> dict:
    minutes = min(float(minutes), MAX_MINUTES)
    interval = max(float(interval), MIN_INTERVAL_S)
    store.mkdir(parents=True, exist_ok=True)
    lock = open(store / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("NEWS_BURST SKIP another burst holds the lock", flush=True)
        return {"skipped": True}
    sha = sha if sha is not None else bs.runtime_commit_sha()
    t_end = now_fn() + minutes * 60
    res = {"sweeps": 0, "rows": 0, "errors": 0, "capped": 0}
    while now_fn() < t_end:
        t0 = now_fn()
        day = datetime.fromtimestamp(t0, timezone.utc).strftime("%Y-%m-%d")
        path = store / f"burst_{day}.jsonl"
        if path.exists() and path.stat().st_size >= MAX_DAILY_BYTES:
            res["capped"] = 1
            print(f"NEWS_BURST CAP daily {MAX_DAILY_BYTES} bytes: stopped; nothing deleted", flush=True)
            break
        with open(path, "a") as fh:
            for s in series:
                try:
                    res["rows"] += sweep(client, s, t0, sha, fh)
                except bs.FetchFailed as e:
                    res["errors"] += 1
                    print(f"WARN sweep {s}: {e}", flush=True)
        res["sweeps"] += 1
        left = interval - (now_fn() - t0)
        if left > 0 and now_fn() + left < t_end:
            sleep(left)
        elif now_fn() + max(left, 0) >= t_end:
            break
    print("NEWS_BURST " + " ".join(f"{k}={v}" for k, v in res.items()), flush=True)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--interval", type=float, default=20)
    ap.add_argument("--store", default=str(STORE))
    ap.add_argument("--series", nargs="+", default=list(SERIES))
    a = ap.parse_args(argv)
    run(bs.Client(pause=0.3), Path(a.store), a.minutes, a.interval, tuple(a.series))
    return 0


if __name__ == "__main__":
    sys.exit(main())

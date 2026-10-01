#!/usr/bin/env python3
"""T-602: dense depth capture -- a NEW sibling writer. It does not touch, import-for-write, or re-time
scripts/archive_market_prices.py or its window; it has its own schedule and its own store.

Why: the archiver's depth sample is ~2 tickers per FAMILY per run (KXMLBF3/F5/F7 share one sample;
KXMLBF7 has 7 rows over 2 tickers). That cannot answer a capacity question. This writer samples
PER SERIES, event-balanced, full ladder retained (not just top-5c metrics), so depth-vs-stake can be
re-derived offline for any stake size.

Read-only, unauthenticated GET only: /markets (listing) and /markets/{ticker}/orderbook.
Store: <store>/depth_<UTC date>.jsonl, append-only.
Idempotency: sampling is seeded by (series, slot) and a (slot, ticker) already present is skipped, so a
re-run inside the same slot adds nothing. A failed orderbook fetch writes no row (counted, exit 2).
"""
from __future__ import annotations

import argparse
import fcntl
import glob
import hashlib
import json
import random
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase0_market_survey import FAMILY_PATTERNS, _book_metrics, _classify, _normalize_book  # noqa: E402

API = "https://api.elections.kalshi.com/trade-api/v2"
PAUSE_S = 0.30            # same floor as the archiver; T4M-PROJ shares the account read budget
MAX_RETRIES = 4
PER_SERIES = 12           # tickers per series per slot; see results summary for derivation
LIST_PAGES = 5
DEFAULT_SERIES = ["KXMLBGAME", "KXMLBSPREAD", "KXMLBTOTAL", "KXMLBTEAMTOTAL", "KXMLBHIT",
                  "KXMLBF3", "KXMLBF5", "KXMLBF7", "KXMLBF5SPREAD", "KXMLBF5TOTAL",
                  "KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL"]  # == the archive's 14
WRITER_VERSION = "capture_depth/1"


class FetchFailed(RuntimeError):
    pass


def runtime_commit_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
                                      stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain", "--",
                                         "scripts/capture_depth.py"], text=True).strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def http_get(url: str) -> dict:
    last = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pm-archive-depth/1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e
        time.sleep(PAUSE_S * (2 ** attempt))
    raise FetchFailed(f"{url}: {last}")


def slot_of(now: datetime, slot_minutes: int) -> str:
    m = (now.hour * 60 + now.minute) // slot_minutes * slot_minutes
    return now.replace(hour=m // 60, minute=m % 60, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%MZ")


def event_balanced(markets: list[dict], n: int, seed: str) -> list[dict]:
    """One market per event first (max distinct events), then fill round-robin. Seeded => repeatable."""
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16))
    by_ev: dict[str, list[dict]] = {}
    for m in sorted(markets, key=lambda x: x["ticker"]):
        by_ev.setdefault(m.get("event_ticker") or m["ticker"], []).append(m)
    evs = sorted(by_ev)
    rng.shuffle(evs)
    for e in evs:
        rng.shuffle(by_ev[e])
    out: list[dict] = []
    depth = 0
    while len(out) < n and any(len(by_ev[e]) > depth for e in evs):
        for e in evs:
            if len(by_ev[e]) > depth and len(out) < n:
                out.append(by_ev[e][depth])
        depth += 1
    return out


def list_open(series: str, get) -> tuple[list[dict], int]:
    out, cursor, calls = [], "", 0
    for _ in range(LIST_PAGES):
        q = {"series_ticker": series, "status": "open", "limit": 1000}
        if cursor:
            q["cursor"] = cursor
        j = get(f"{API}/markets?{urllib.parse.urlencode(q)}"); calls += 1
        out += [m for m in (j.get("markets") or []) if m.get("ticker")]
        cursor = j.get("cursor") or ""
        if not cursor:
            break
        time.sleep(PAUSE_S)
    return out, calls


def seen_in_slot(store: Path, slot: str) -> set[str]:
    seen: set[str] = set()
    for p in glob.glob(str(store / "depth_????-??-??.jsonl")):
        with open(p) as fh:
            for line in fh:
                if f'"slot": "{slot}"' in line:
                    seen.add(json.loads(line)["ticker"])
    return seen


def capture(store: Path, series_list: list[str], per_series: int = PER_SERIES, get=http_get,
            now: datetime | None = None, sha: str | None = None, slot_minutes: int = 60,
            sleep=time.sleep) -> dict:
    now = now or datetime.now(timezone.utc)
    sha = sha or runtime_commit_sha()
    store.mkdir(parents=True, exist_ok=True)
    lock = open(store / ".lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    slot = slot_of(now, slot_minutes)
    seen = seen_in_slot(store, slot)
    summ = {"slot": slot, "calls": 0, "written": 0, "skipped_already_in_slot": 0, "failed": [],
            "per_series": {}}
    rows: list[dict] = []
    for series in series_list:
        ps = {"open": 0, "sampled": 0, "written": 0, "distinct_events": 0}
        try:
            mk, c = list_open(series, get); summ["calls"] += c
        except FetchFailed as e:
            summ["failed"].append({"series": series, "stage": "list", "error": str(e)})
            summ["per_series"][series] = ps
            continue
        ps["open"] = len(mk)
        pick = event_balanced(mk, per_series, f"{series}|{slot}")
        ps["sampled"] = len(pick)
        evs = set()
        for m in pick:
            t = m["ticker"]
            if t in seen:
                summ["skipped_already_in_slot"] += 1
                continue
            url = f"{API}/markets/{urllib.parse.quote(t)}/orderbook"
            try:
                j = get(url); summ["calls"] += 1
            except FetchFailed as e:
                summ["failed"].append({"series": series, "ticker": t, "stage": "orderbook", "error": str(e)})
                continue
            book = _normalize_book(j or {})
            ladder = json.dumps(book, sort_keys=True, separators=(",", ":"))
            row = {
                "slot": slot, "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if get is http_get else now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ticker": t, "series_ticker": series, "family": _classify(series, FAMILY_PATTERNS, "UNCLASSIFIED"),
                "event_ticker": m.get("event_ticker"), "close_time": m.get("close_time"),
                "expected_expiration_time": m.get("expected_expiration_time"),
                "market_status": m.get("status"), "book": book,
                "book_sha256": hashlib.sha256(ladder.encode()).hexdigest(),
                **_book_metrics(book), "source_url": url, "runtime_commit_sha": sha,
                "writer": WRITER_VERSION,
            }
            rows.append(row); ps["written"] += 1; evs.add(m.get("event_ticker"))
            sleep(PAUSE_S)
        ps["distinct_events"] = len(evs)
        summ["per_series"][series] = ps
    if rows:
        out = store / f"depth_{now.strftime('%Y-%m-%d')}.jsonl"
        with open(out, "a") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        summ["store_file"] = str(out)
    summ["written"] = len(rows)
    fcntl.flock(lock, fcntl.LOCK_UN)
    return summ


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", default="exp_output/DEPTH_ARCHIVE")
    ap.add_argument("--series", nargs="+", default=DEFAULT_SERIES)
    ap.add_argument("--per-series", type=int, default=PER_SERIES)
    ap.add_argument("--slot-minutes", type=int, default=60)
    a = ap.parse_args(argv)
    s = capture(Path(a.store), a.series, a.per_series, slot_minutes=a.slot_minutes)
    print(json.dumps(s, indent=1))
    return 2 if s["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

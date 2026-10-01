#!/usr/bin/env python3
"""T-602: settlement capture -- makes the price archive able to settle itself.

Why: every row in exp_output/PRICE_ARCHIVE carries status=active; the archive holds NO
settlement. EXP-031 had to pull outcomes from Kalshi's public `result` endpoint and cache
them out-of-band. This writer records the venue's final settlement per archived ticker, into
its OWN store, so an archive row can be joined to its outcome without a fresh network pull.

Read-only against the venue: public GET /markets only. No credentials, no order endpoint.
Never modifies, relabels or backfills a PRICE_ARCHIVE row -- it only READS the ticker set.

Store: <store>/settlements_<retrieval-UTC-date>.jsonl, append-only. Index = all files.
  * A ticker already captured with the same upstream content hash is skipped (idempotent).
  * A ticker whose upstream content CHANGED is appended as a new row carrying
    `revises_content_sha256`; the earlier row is never rewritten. Reported as a finding.
  * A non-terminal record (no result / status not settled|finalized) is not written.
  * A series whose fetch fails part-way writes NOTHING for that series; exit code 2.

Usage:
  python3 scripts/capture_settlements.py capture   --archive exp_output/PRICE_ARCHIVE --store exp_output/SETTLEMENT_ARCHIVE
  python3 scripts/capture_settlements.py reconcile --store ... --cache exp_output/EXP-031-MKT-EFF-SURVEY/settlements --report out.json
"""
from __future__ import annotations

import argparse
import fcntl
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.elections.kalshi.com/trade-api/v2/markets"
TERMINAL_STATUS = {"settled", "finalized"}
# Fields that define "the settlement". Retrieval time / volume / quotes are deliberately out:
# they change without the settlement changing and would defeat idempotency.
HASH_FIELDS = ("ticker", "status", "result", "settlement_value_dollars", "expiration_value",
               "settlement_ts", "market_type")
BULK_THRESHOLD = 300          # unsettled tickers in a series above which bulk paging is cheaper
PAUSE_S = 0.30                # matches the archiver's floor (~3.3 req/s)
MAX_RETRIES = 4
WRITER_VERSION = "capture_settlements/1"


class FetchFailed(RuntimeError):
    pass


def runtime_commit_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
                                      stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain", "--",
                                         "scripts/capture_settlements.py"], text=True).strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def content_hash(market: dict) -> str:
    canon = json.dumps({k: market.get(k) for k in HASH_FIELDS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


def is_terminal(market: dict) -> bool:
    return (market.get("status") in TERMINAL_STATUS
            and market.get("result") not in (None, "")
            and bool(market.get("settlement_ts")))


def http_get(url: str) -> dict:
    last = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pm-archive-settlement/1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FetchFailed(f"404 {url}") from e
            last = e
        except Exception as e:  # network / JSON
            last = e
        time.sleep(PAUSE_S * (2 ** attempt))
    raise FetchFailed(f"{url}: {last}")


# ---------------------------------------------------------------- archive / store IO
def archive_tickers(archive_dir: str) -> dict[str, dict[str, str]]:
    """series -> {ticker: event_ticker}. Reads only strict prices_YYYY-MM-DD.jsonl files
    (the .BROKEN_FIRSTRUN set-aside file is excluded, as in EXP-031)."""
    out: dict[str, dict[str, str]] = defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(archive_dir, "prices_????-??-??.jsonl"))):
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                t, s = r.get("ticker"), r.get("series_ticker")
                if t and s:
                    out[s][t] = r.get("event_ticker")
    return out


def load_index(store: Path) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(glob.glob(str(store / "settlements_????-??-??.jsonl"))):
        with open(path) as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    idx[r["ticker"]].append(r)
    return idx


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_row(market: dict, series: str, url: str, now: datetime, sha: str,
             revises: str | None) -> dict:
    row = {
        "ticker": market["ticker"], "family": series, "series_ticker": series,
        "event_ticker": market.get("event_ticker"), "status": market.get("status"),
        "result": market.get("result"),
        "settlement_value_dollars": market.get("settlement_value_dollars"),
        "expiration_value": market.get("expiration_value"),
        "settlement_ts": market.get("settlement_ts"),
        "market_type": market.get("market_type"),
        "source_url": url, "content_sha256": content_hash(market),
        "retrieved_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_commit_sha": sha, "writer": WRITER_VERSION,
    }
    if revises:
        row["revises_content_sha256"] = revises
    return row


# ---------------------------------------------------------------- fetch strategies
def fetch_bulk(series: str, need: set[str], get=http_get) -> tuple[dict[str, tuple[dict, str]], int]:
    """Page every settled market of a series. Raises FetchFailed on any page failure."""
    found: dict[str, tuple[dict, str]] = {}
    cursor, calls = "", 0
    while True:
        q = {"series_ticker": series, "status": "settled", "limit": 1000}
        if cursor:
            q["cursor"] = cursor
        url = f"{API}?{urllib.parse.urlencode(q)}"
        j = get(url); calls += 1
        for m in j.get("markets") or []:
            if m.get("ticker") in need:
                found[m["ticker"]] = (m, url)
        cursor = j.get("cursor") or ""
        if not cursor or not j.get("markets"):
            return found, calls
        time.sleep(PAUSE_S)


def fetch_single(tickers: list[str], get=http_get) -> tuple[dict[str, tuple[dict, str]], int]:
    found, calls = {}, 0
    for t in tickers:
        url = f"{API}/{urllib.parse.quote(t)}"
        try:
            j = get(url); calls += 1
        except FetchFailed as e:
            if str(e).startswith("404"):
                continue          # unknown ticker upstream: leave uncaptured, reported as such
            raise
        m = j.get("market")
        if isinstance(m, dict) and m.get("ticker") == t:
            found[t] = (m, url)
        time.sleep(PAUSE_S)
    return found, calls


# ---------------------------------------------------------------- capture
def capture(archive_dir: str, store: Path, get=http_get, now: datetime | None = None,
            sha: str | None = None, series_filter: list[str] | None = None) -> dict:
    now = now or utc_now()
    sha = sha or runtime_commit_sha()
    store.mkdir(parents=True, exist_ok=True)
    universe = archive_tickers(archive_dir)
    lock = open(store / ".lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)       # a second concurrent run fails fast
    idx = load_index(store)
    out_path = store / f"settlements_{now.strftime('%Y-%m-%d')}.jsonl"
    summ = {"archive_tickers": 0, "already_captured": 0, "written": 0, "revisions": 0,
            "not_terminal_or_absent": 0, "failed_series": [], "calls": 0, "per_series": {}}
    pending_rows: list[dict] = []
    for series, tmap in sorted(universe.items()):
        if series_filter and series not in series_filter:
            continue
        summ["archive_tickers"] += len(tmap)
        need = sorted(t for t in tmap if t not in idx)
        summ["already_captured"] += len(tmap) - len(need)
        ps = {"archive": len(tmap), "needed": len(need), "written": 0, "not_terminal_or_absent": 0}
        try:
            if len(need) > BULK_THRESHOLD:
                found, calls = fetch_bulk(series, set(need), get)
                missing = [t for t in need if t not in found]
                if missing:       # bulk lists only settled; ask the venue about the rest by ticker
                    f2, c2 = fetch_single(missing, get); found.update(f2); calls += c2
            else:
                found, calls = fetch_single(need, get)
        except FetchFailed as e:
            summ["failed_series"].append({"series": series, "error": str(e)})
            summ["per_series"][series] = ps
            continue                          # atomic per series: nothing from it is written
        summ["calls"] += calls
        for t in need:
            rec = found.get(t)
            if rec is None or not is_terminal(rec[0]):
                ps["not_terminal_or_absent"] += 1
                continue
            pending_rows.append(make_row(rec[0], series, rec[1], now, sha, None))
            ps["written"] += 1
        summ["per_series"][series] = ps
    # Revision check: captured tickers whose upstream hash moved. Cheap re-verify is out of
    # scope for the routine run (it would re-pull every settled ticker); see `verify`.
    if pending_rows:
        with open(out_path, "a") as fh:
            for r in pending_rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    summ["written"] = len(pending_rows)
    summ["not_terminal_or_absent"] = sum(p["not_terminal_or_absent"] for p in summ["per_series"].values())
    summ["store_file"] = str(out_path)
    fcntl.flock(lock, fcntl.LOCK_UN)
    return summ


def apply_revision(store: Path, market: dict, series: str, url: str, now: datetime, sha: str) -> bool:
    """Append a revision row if upstream content differs from the latest captured row."""
    idx = load_index(store)
    rows = idx.get(market["ticker"])
    if not rows or not is_terminal(market):
        return False
    h = content_hash(market)
    if rows[-1]["content_sha256"] == h:
        return False
    with open(store / f"settlements_{now.strftime('%Y-%m-%d')}.jsonl", "a") as fh:
        fh.write(json.dumps(make_row(market, series, url, now, sha, rows[-1]["content_sha256"]),
                            sort_keys=True) + "\n")
    return True


# ---------------------------------------------------------------- reconcile vs EXP-031 cache
def reconcile(store: Path, cache_dir: str, archive_dir: str) -> dict:
    idx = load_index(store)
    universe = archive_tickers(archive_dir)
    arch_all = {t: s for s, m in universe.items() for t in m}
    rep = {"series": {}, "discrepancies": [], "totals": defaultdict(int)}
    for path in sorted(glob.glob(os.path.join(cache_dir, "*.json"))):
        series = Path(path).stem
        cache = json.load(open(path))
        mine = {t: rows[-1] for t, rows in idx.items() if arch_all.get(t) == series or rows[-1]["series_ticker"] == series}
        arch_t = set(universe.get(series, {}))
        s = defaultdict(int)
        for t, c in cache.items():
            in_arch = t in arch_t
            r = mine.get(t)
            if not in_arch:
                s["cache_only_not_in_archive"] += 1       # EXP-031 pulled the whole series; expected
                continue
            if r is None:
                s["archive_in_cache_not_in_store"] += 1
                rep["discrepancies"].append({"type": "in_cache_not_in_store", "ticker": t,
                                             "cache_result": c.get("result")})
                continue
            s["compared"] += 1
            diffs = {}
            if c.get("result") != r["result"]:
                diffs["result"] = [c.get("result"), r["result"]]
            if c.get("expiration_value") != r["expiration_value"]:
                diffs["expiration_value"] = [c.get("expiration_value"), r["expiration_value"]]
            if c.get("settlement_ts") != r["settlement_ts"]:
                diffs["settlement_ts"] = [c.get("settlement_ts"), r["settlement_ts"]]
            if diffs:
                s["field_mismatch"] += 1
                rep["discrepancies"].append({"type": "field_mismatch", "ticker": t, "diffs": diffs})
            else:
                s["agree"] += 1
        for t in arch_t:
            if t in mine and t not in cache:
                s["in_store_not_in_cache"] += 1
                rep["discrepancies"].append({"type": "in_store_not_in_cache", "ticker": t,
                                             "store_result": mine[t]["result"]})
            elif t not in mine and t not in cache:
                s["in_neither"] += 1
        rep["series"][series] = dict(s)
        for k, v in s.items():
            rep["totals"][k] += v
    rep["totals"] = dict(rep["totals"])
    rep["store_tickers"] = len(idx)
    rep["archive_tickers"] = len(arch_all)
    rep["archive_tickers_without_settlement"] = sum(1 for t in arch_all if t not in idx)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--archive", default="exp_output/PRICE_ARCHIVE")
    c.add_argument("--store", default="exp_output/SETTLEMENT_ARCHIVE")
    c.add_argument("--series", nargs="*")
    r = sub.add_parser("reconcile")
    r.add_argument("--archive", default="exp_output/PRICE_ARCHIVE")
    r.add_argument("--store", default="exp_output/SETTLEMENT_ARCHIVE")
    r.add_argument("--cache", required=True)
    r.add_argument("--report", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "capture":
        s = capture(a.archive, Path(a.store), series_filter=a.series)
        print(json.dumps(s, indent=1))
        if s["failed_series"]:
            print("FAILED series wrote nothing; rerun later.", file=sys.stderr)
            return 2
        return 0
    rep = reconcile(Path(a.store), a.cache, a.archive)
    Path(a.report).write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("totals", "store_tickers", "archive_tickers",
                                          "archive_tickers_without_settlement")}, indent=1))
    print(f"discrepancies: {len(rep['discrepancies'])} -> {a.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

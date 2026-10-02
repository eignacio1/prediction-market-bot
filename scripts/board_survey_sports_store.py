#!/usr/bin/env python3
"""EXP-035 (T-604): append-only raw-history store for the Kalshi sports board survey.

Own store, never PRICE_ARCHIVE or any existing store. Public unauthenticated GETs only; no order
endpoint, no credentials. Raw upstream JSON is kept verbatim (scalar settlements included), with
provenance on every row: source URL, retrieval UTC, upstream content hash, runtime commit sha.

Store: <store>/raw_<retrieval-UTC-date>.jsonl, append-only. Row key = (kind, key).
  * same (kind, key) with the same content hash already in ANY file: skipped (idempotent).
  * same key, different content: appended with `revises_content_sha256`; the old row is never touched.
  * a failed fetch writes nothing.
Pacing: 0.30 s between calls; every HTTP 429 doubles the pause (halves the rate) for the rest of the run.
"""
from __future__ import annotations

import fcntl
import glob
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.elections.kalshi.com/trade-api/v2"
WRITER_VERSION = "board_survey_sports_store/1"
PAUSE_S = 0.30
MAX_RETRIES = 5
STORE_DEFAULT = ROOT / "exp_output" / "BOARD_SURVEY_SPORTS"


class FetchFailed(RuntimeError):
    pass


def iso_ts(s: str) -> int:
    """ISO-8601 -> epoch seconds; tolerant of 1-9 fractional digits (py3.9 fromisoformat needs 3 or 6)."""
    s = s.replace("Z", "+00:00")
    s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s)
    return int(datetime.fromisoformat(s).timestamp())


def runtime_commit_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
                                      stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain", "--",
                                         "scripts/board_survey_sports_store.py"], text=True).strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def canon_hash(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Client:
    """Paced GET client. `opener(url)` -> (status, body_bytes) is injectable for tests."""

    def __init__(self, opener=None, pause=PAUSE_S, sleep=time.sleep):
        self.opener, self.pause, self.sleep = opener or self._urlopen, pause, sleep
        self.calls = self.bytes = self.n429 = self.errors = 0
        self.t0 = time.time()
        self._last = 0.0

    @staticmethod
    def _urlopen(url):
        req = urllib.request.Request(url, headers={"User-Agent": "pm-board-survey-sports/1"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()

    def get(self, path: str, **params) -> tuple[dict, str]:
        q = {k: v for k, v in params.items() if v is not None}
        url = f"{API}{path}" + (f"?{urllib.parse.urlencode(q)}" if q else "")
        last = None
        for attempt in range(MAX_RETRIES):
            wait = self.pause - (time.time() - self._last)
            if wait > 0:
                self.sleep(wait)
            self._last = time.time()
            try:
                status, body = self.opener(url)
                self.calls += 1; self.bytes += len(body)
                return json.loads(body), url
            except urllib.error.HTTPError as e:
                self.calls += 1
                if e.code == 429:
                    self.n429 += 1; self.pause *= 2          # halve the request rate, stays halved
                elif e.code == 404:
                    raise FetchFailed(f"404 {url}") from e
                last = e
            except Exception as e:
                self.errors += 1; last = e
            self.sleep(self.pause * (2 ** attempt))
        raise FetchFailed(f"{url}: {last}")

    def stats(self) -> dict:
        return {"calls": self.calls, "bytes": self.bytes, "n429": self.n429, "errors": self.errors,
                "final_pause_s": self.pause, "wall_s": round(time.time() - self.t0, 1)}


class Store:
    def __init__(self, path=STORE_DEFAULT, now: datetime | None = None, sha: str | None = None):
        self.path = Path(path); self.path.mkdir(parents=True, exist_ok=True)
        self.now = now or datetime.now(timezone.utc)
        self.sha = sha or runtime_commit_sha()
        self._lock = open(self.path / ".lock", "w")
        fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)      # concurrent run fails fast
        self.index: dict[tuple, set] = defaultdict(set)
        for f in sorted(glob.glob(str(self.path / "raw_????-??-??.jsonl"))):
            with open(f) as fh:
                for line in fh:
                    if line.strip():
                        r = json.loads(line); self.index[(r["kind"], r["key"])].add(r["content_sha256"])
        self.out = self.path / f"raw_{self.now.strftime('%Y-%m-%d')}.jsonl"
        self.written = self.skipped = self.revisions = 0

    def put(self, kind: str, key: str, payload, url: str) -> str:
        h = canon_hash(payload)
        have = self.index[(kind, key)]
        if h in have:
            self.skipped += 1
            return "skipped"
        row = {"kind": kind, "key": key, "payload": payload, "source_url": url, "content_sha256": h,
               "retrieved_utc": self.now.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "runtime_commit_sha": self.sha, "writer": WRITER_VERSION}
        if have:
            row["revises_content_sha256"] = sorted(have)[-1]; self.revisions += 1
        with open(self.out, "a") as fh:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
        have.add(h); self.written += 1
        return "revision" if "revises_content_sha256" in row else "written"

    def rows(self, kind: str | None = None):
        for f in sorted(glob.glob(str(self.path / "raw_????-??-??.jsonl"))):
            with open(f) as fh:
                for line in fh:
                    if line.strip():
                        r = json.loads(line)
                        if kind is None or r["kind"] == kind:
                            yield r

    def digest(self) -> str:
        h = hashlib.sha256()
        for f in sorted(glob.glob(str(self.path / "raw_????-??-??.jsonl"))):
            h.update(Path(f).read_bytes())
        return h.hexdigest()


# ---------------------------------------------------------------- endpoint helpers
def list_markets(client: Client, store: Store, series: str, cutoff_ts: str, window_start: str | None = None) -> list[dict]:
    """All settled markets of a series, historical (before cutoff) + live (after). Stores each page verbatim."""
    out = []
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None
        while True:
            j, url = client.get(path, series_ticker=series, limit=1000, cursor=cursor, **extra)
            store.put("markets_page", f"{path}|{series}|{cursor or ''}", j, url)
            out += j.get("markets") or []
            cursor = j.get("cursor") or None
            if not cursor or not j.get("markets"):
                break
    seen, dedup = set(), []
    for m in out:
        if m["ticker"] not in seen:
            seen.add(m["ticker"]); dedup.append(m)
    return dedup


def candles(client: Client, store: Store, series: str, market: dict, start_ts: int, end_ts: int, period: int, cutoff_ts: int):
    """Candles for one market; historical endpoint when it settled before the cutoff, live otherwise."""
    st = market.get("settlement_ts") or market.get("close_time")
    settled = iso_ts(st)
    if settled < cutoff_ts:
        path = f"/historical/markets/{market['ticker']}/candlesticks"
    else:
        path = f"/series/{series}/markets/{market['ticker']}/candlesticks"
    j, url = client.get(path, start_ts=start_ts, end_ts=end_ts, period_interval=period)
    store.put("candles", f"{market['ticker']}|{period}|{start_ts}|{end_ts}", j, url)
    return j.get("candlesticks") or []

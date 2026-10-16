#!/usr/bin/env python3
"""W80P.1: recurring order-book capture for the thinner NFL / NBA Kalshi families (W78.2 manifest proposal).

Why: Kalshi keeps NO historical order book. Candles carry bid/ask OHLC, volume and open interest, never depth, so
depth not captured while a market is open is lost for good (12_EXPLORATORY/thin_markets/MANIFEST.md). The thin-market
efficiency + fillability question (W79.2 / W80P.2) needs depth at decision time, so it has to be recorded forward.

What one run does (cron, every 30 min; deploy/cron.thin_capture):
  1. lists OPEN markets of each family in SERIES that close within WINDOW_S (48 h);
  2. snapshots the live order book (GET /markets/{ticker}/orderbook) of every market due:
       closing within NEAR_S (6 h)  -> every run (30 min);
       6-48 h out                   -> once every FAR_EVERY_S (3 h);
     least recently snapshotted first, then closest to close, at most MAX_BOOKS_PER_RUN per run. An unchanged book is written as a small
     "unchanged" row pointing at the last content hash (the time series stays complete, the bytes do not grow);
  3. after a captured market has closed (+ SETTLE_GRACE_S), fetches its candles once: 60-min over the life and
     1-min over the last 48 h before close, at most MAX_CANDLE_MARKETS_PER_RUN per run (the rest wait for the next run).

Bounds: Client pacing (PAUSE_S between calls, every 429 halves the rate for the rest of the run); MAX_DAILY_BYTES per
UTC day and MAX_STORE_BYTES in total (writes stop and the run says CAP; nothing is deleted); one run at a time (flock).
Resumable: state.json (atomic replace) holds per-ticker last snapshot and the candle queue; a killed run loses at most
the row it was writing. Public unauthenticated GETs only; no order endpoint, no credentials, no ledger or model path.

Store (git-ignored): exp_output/KALSHI_HISTORY/thin_capture/{books,candles}_YYYY-MM-DD.jsonl + state.json.
Every row: kind, ticker, series, retrieved_utc, source_url, content_sha256, runtime_commit_sha, writer.
Analysis use of these rows is governed by the pre-registration that consumes them (W80P.2), not by this script.

Usage:  python3 scripts/thin_market_depth_capture.py [--store DIR] [--pause S]
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_store as bs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "exp_output" / "KALSHI_HISTORY" / "thin_capture"
WRITER = "thin_market_depth_capture/1"
# The families W78.2 / W79.2 sampled (game, spread, total, team total, and the player-prop families of inventory.json).
SERIES = ("KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL", "KXNFL1HSPREAD", "KXNFL1HTOTAL",
          "KXNFLANYTD", "KXNFLFIRSTTD", "KXNFLRECYDS", "KXNFLRSHYDS", "KXNFLPASSYDS",
          "KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNBATEAMTOTAL", "KXNBAPTS", "KXNBAREB")
WINDOW_S = 48 * 3600
NEAR_S = 6 * 3600
FAR_EVERY_S = 3 * 3600 - 300          # 5 min slack so a 30-min cron does not drift past the 3 h mark
SETTLE_GRACE_S = 3 * 3600
MINUTE_LOOKBACK_S = 48 * 3600
PAUSE_S = 0.5
MAX_BOOKS_PER_RUN = 500
MAX_CANDLE_MARKETS_PER_RUN = 60
MAX_CANDLE_TRIES = 3
MAX_DAILY_BYTES = 80 * 1024 * 1024
MAX_STORE_BYTES = 4 * 1024 ** 3


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Writer:
    """Append-only per-day JSONL files with a daily and a total byte cap."""

    def __init__(self, store: Path, now: float, sha: str):
        self.store, self.now, self.sha = store, now, sha
        self.day = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
        self.capped = ""
        self.bytes_today = sum(p.stat().st_size for p in store.glob(f"*_{self.day}.jsonl"))
        self.bytes_total = sum(p.stat().st_size for p in store.glob("*.jsonl"))
        self.rows = 0

    def put(self, stream: str, row: dict) -> bool:
        row = {**row, "retrieved_utc": _iso(self.now), "runtime_commit_sha": self.sha, "writer": WRITER}
        line = json.dumps(row, separators=(",", ":")) + "\n"
        n = len(line.encode())
        if self.bytes_today + n > MAX_DAILY_BYTES:
            self.capped = f"daily cap {MAX_DAILY_BYTES} bytes"
            return False
        if self.bytes_total + n > MAX_STORE_BYTES:
            self.capped = f"store cap {MAX_STORE_BYTES} bytes"
            return False
        with open(self.store / f"{stream}_{self.day}.jsonl", "a") as fh:
            fh.write(line)
        self.bytes_today += n
        self.bytes_total += n
        self.rows += 1
        return True


def load_state(store: Path) -> dict:
    try:
        st = json.loads((store / "state.json").read_text())
    except (OSError, ValueError):
        st = {}
    st.setdefault("tickers", {})
    return st


def save_state(store: Path, st: dict) -> None:
    tmp = store / "state.json.tmp"
    tmp.write_text(json.dumps(st, sort_keys=True, separators=(",", ":")))
    os.replace(tmp, store / "state.json")


def open_markets(client: bs.Client, series: str, now: float) -> list[dict]:
    out, cursor = [], None
    while True:
        j, _ = client.get("/markets", series_ticker=series, status="open", limit=1000, cursor=cursor,
                          min_close_ts=int(now), max_close_ts=int(now + WINDOW_S))
        out += j.get("markets") or []
        cursor = j.get("cursor") or None
        if not cursor or not j.get("markets"):
            break
    # the server-side close filter is a convenience; the window is enforced here
    return [m for m in out if m.get("close_time") and 0 < bs.iso_ts(m["close_time"]) - now <= WINDOW_S]


def due(m: dict, rec: dict | None, now: float) -> bool:
    if rec is None or not rec.get("last_snap_ts"):
        return True
    if bs.iso_ts(m["close_time"]) - now <= NEAR_S:
        return True
    return now - rec["last_snap_ts"] >= FAR_EVERY_S


def snapshot_books(client, w: Writer, st: dict, now: float, series_list=SERIES) -> dict:
    c = {"listed": 0, "due": 0, "books": 0, "unchanged": 0, "errors": 0, "series_errors": 0}
    cands = []
    for s in series_list:
        try:
            ms = open_markets(client, s, now)
        except bs.FetchFailed as e:
            c["series_errors"] += 1
            print(f"WARN list {s}: {e}", flush=True)
            continue
        c["listed"] += len(ms)
        cands += [(s, m) for m in ms if due(m, st["tickers"].get(m["ticker"]), now)]
    c["due"] = len(cands)
    # least recently snapshotted first (never-seen = 0), then closest to close: under the per-run cap every due
    # market is served within a few runs instead of the closest ones starving the rest
    cands.sort(key=lambda sm: ((st["tickers"].get(sm[1]["ticker"]) or {}).get("last_snap_ts", 0),
                               bs.iso_ts(sm[1]["close_time"]), sm[1]["ticker"]))
    for s, m in cands[:MAX_BOOKS_PER_RUN]:
        t = m["ticker"]
        try:
            j, url = client.get(f"/markets/{t}/orderbook")
        except bs.FetchFailed as e:
            c["errors"] += 1
            print(f"WARN book {t}: {e}", flush=True)
            continue
        h = bs.canon_hash(j)
        rec = st["tickers"].setdefault(t, {"series": s, "n_snaps": 0})
        rec.update(close_time=m["close_time"], open_time=m.get("open_time"), event_ticker=m.get("event_ticker"))
        top = {k: m.get(k) for k in ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "volume", "volume_24h",
                                     "open_interest", "liquidity", "yes_bid_dollars", "yes_ask_dollars")
               if m.get(k) is not None}
        row = {"kind": "orderbook", "ticker": t, "series": s, "event_ticker": m.get("event_ticker"),
               "close_time": m["close_time"], "secs_to_close": int(bs.iso_ts(m["close_time"]) - now),
               "listing_top": top, "source_url": url, "content_sha256": h}
        if rec.get("last_sha") == h:
            row["unchanged_of"] = h
            kind = "unchanged"
        else:
            row["book"] = j
            kind = "books"
        if not w.put("books", row):
            break
        c[kind] += 1
        rec.update(last_snap_ts=now, last_sha=h, n_snaps=rec["n_snaps"] + 1)
    return c


def fetch_candles(client, w: Writer, st: dict, now: float) -> dict:
    c = {"candle_markets": 0, "candle_errors": 0, "dropped": 0}
    ready = sorted((t for t, r in st["tickers"].items() if r.get("close_time")
                    and now - bs.iso_ts(r["close_time"]) >= SETTLE_GRACE_S),
                   key=lambda t: (st["tickers"][t]["close_time"], t))
    for t in ready[:MAX_CANDLE_MARKETS_PER_RUN]:
        r = st["tickers"][t]
        close = bs.iso_ts(r["close_time"])
        opn = bs.iso_ts(r["open_time"]) if r.get("open_time") else close - 14 * 86400
        ok = True
        for period, start, end in ((60, opn, close + 3600), (1, max(opn, close - MINUTE_LOOKBACK_S), close + 120)):
            j = url = None
            for path in (f"/series/{r['series']}/markets/{t}/candlesticks", f"/historical/markets/{t}/candlesticks"):
                try:
                    j, url = client.get(path, start_ts=start, end_ts=end, period_interval=period)
                    break
                except bs.FetchFailed:
                    continue
            if j is None:
                ok = False
                break
            if not w.put("candles", {"kind": "candles", "ticker": t, "series": r["series"], "period": period,
                                     "start_ts": start, "end_ts": end, "payload": j, "source_url": url,
                                     "content_sha256": bs.canon_hash(j)}):
                return c
        if ok:
            c["candle_markets"] += 1
            del st["tickers"][t]
        else:
            c["candle_errors"] += 1
            r["candle_tries"] = r.get("candle_tries", 0) + 1
            if r["candle_tries"] >= MAX_CANDLE_TRIES:
                c["dropped"] += 1
                print(f"WARN candles {t}: gave up after {MAX_CANDLE_TRIES} runs", flush=True)
                del st["tickers"][t]
    return c


def run(client, store: Path, now: float | None = None, sha: str | None = None, series_list=SERIES) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    lock = open(store / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("THIN_CAPTURE SKIP another run holds the lock", flush=True)
        return {"skipped": True}
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    st = load_state(store)
    w = Writer(store, now, sha if sha is not None else bs.runtime_commit_sha())
    res = {"ts": _iso(now)}
    if w.bytes_total >= MAX_STORE_BYTES:
        w.capped = f"store cap {MAX_STORE_BYTES} bytes"
    else:
        res.update(snapshot_books(client, w, st, now, series_list))
        if not w.capped:
            res.update(fetch_candles(client, w, st, now))
    save_state(store, st)
    res.update(rows=w.rows, bytes_today=w.bytes_today, tracked=len(st["tickers"]), cap=w.capped or "none",
               **{f"http_{k}": v for k, v in client.stats().items() if k in ("calls", "n429", "errors")})
    print("THIN_CAPTURE " + " ".join(f"{k}={v}" for k, v in res.items()), flush=True)
    if w.capped:
        print(f"THIN_CAPTURE CAP {w.capped}: writes stopped for this run; nothing deleted", flush=True)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default=str(STORE))
    ap.add_argument("--pause", type=float, default=PAUSE_S)
    a = ap.parse_args(argv)
    run(bs.Client(pause=a.pause), Path(a.store))
    return 0


if __name__ == "__main__":
    sys.exit(main())

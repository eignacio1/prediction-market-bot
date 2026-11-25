#!/usr/bin/env python3
"""W124.4 dense capture: props from first listing, 5-min game snapshots near start, Kalshi trade prints forward.

Three modes, each a NEW cron line (no existing archive line is edited):

  props   NBA/NFL/NHL prop series, every open market dated today (ET), at the existing 20-min cadence. Run in hours the
          existing lines do not cover, so a prop is seen from its first listing (W123 H1 had no fit window).
  games   ML / spread / total / team total, only markets whose estimated start is within the next 3 h (5-min cadence;
          W123 H4 saw 19-30 min spacing).
  prints  Kalshi public trade prints (global /markets/trades feed), written forward (W123 H3 had prints only from 11-10).
          W127.4 cut: only the families H3 named (PRINT_SERIES) and only prints inside a market's 3 h pre-start window.

Output: exp_output/PRICE_ARCHIVE_DENSE/<mode>/<UTC date>.jsonl.gz and exp_output/TRADE_PRINTS/<UTC date>.jsonl.gz.
Rows are appended as gzip members (readable by gzip.open / io_jsonl.open_jsonl). Every row carries event timestamps
(run_ts, plus occurrence_datetime / close_time / open_time for snapshots, created_time for prints).

KNOWN LIMIT: Kalshi's occurrence_datetime is the expected-expiration (about game END), not the start. Start is
estimated as occurrence_datetime minus a nominal per-sport duration (NBA 2.5 h, NHL 2.5 h, NFL 3.25 h). The raw
occurrence_datetime is stored on every row so a reader can re-derive any window. The estimate is +/- ~30 min.

Public, unauthenticated endpoints only. $0. No orders. --dry-run writes nothing and reports bytes/day and requests/min.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

BASE = "https://api.elections.kalshi.com/trade-api/v2"
ET = ZoneInfo("America/New_York")
PAUSE_S = 0.15                  # ~6.7 req/s ceiling inside one process; the gate budgets the real figure
MAX_PAGES = 40
MAX_PRINT_PAGES = 400           # global feed is ~280 trades/s; 5 min is ~85 pages of 1000
PRINT_OVERLAP_S = 60            # re-read this much so a late print is not missed; trade_id dedupe removes repeats
DEDUPE_KEEP = 200_000

PROP_SERIES = {
    "NBA": ["KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT", "KXNBASTL", "KXNBAPRA", "KXNBA2D", "KXNBA3D"],
    "NHL": ["KXNHLGOAL", "KXNHLAST"],
    "NFL": ["KXNFLPASSYDS", "KXNFLRSHYDS", "KXNFLRECYDS", "KXNFLREC", "KXNFLTD", "KXNFLPASSTDS", "KXNFLPASSATT",
            "KXNFLPASSCOMP", "KXNFLRSHATT", "KXNFLRRYDS"],
}
GAME_SERIES = {
    "NBA": ["KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNBATEAMTOTAL"],
    "NHL": ["KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL", "KXNHLTEAMTOTAL"],
    "NFL": ["KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL"],
}
NOMINAL_DURATION_H = {"NBA": 2.5, "NHL": 2.5, "NFL": 3.25}
GAME_WINDOW_BEFORE_H = 3.0
GAME_WINDOW_AFTER_H = 0.25
# W127.4: prints were 91% of the W126.1 gate's 159.2 MB/day. Kept: the families the H3 RESULT names -- NBA player props and
# team totals (its "next test the data can support now"), NBA and NFL game moneylines (the news-latency base and NFL inactives).
# Dropped: NFL props, NHL everything, spreads, totals. H3 NHL goalie closed in W118.3.
PRINT_SERIES = frozenset(PROP_SERIES["NBA"] + ["KXNBAGAME", "KXNBATEAMTOTAL", "KXNFLGAME"])
PRINT_WINDOW_BEFORE_H = GAME_WINDOW_BEFORE_H            # same 3 h pre-start window as the 5-min game snapshots
PRINT_WINDOW_AFTER_H = GAME_WINDOW_AFTER_H
START_MAP_HORIZON_H = 4.5       # the start map holds markets starting within this many hours (window opens 3 h before start)
START_MAP_STALE_S = 1200        # relist at most every 20 min; a market listed after that and starting inside 4.5 h waits for the next relist

FIELDS = ("ticker", "event_ticker", "status", "yes_bid_dollars", "yes_ask_dollars", "no_bid_dollars", "no_ask_dollars",
          "last_price_dollars", "previous_price_dollars", "volume_fp", "volume_24h_fp", "open_interest_fp",
          "liquidity_dollars", "open_time", "close_time", "expiration_time", "occurrence_datetime")
_MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
_DATE_TOKEN = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")

Fetch = Callable[[str, dict], dict]


# ---------------------------------------------------------------- helpers
def ticker_date(ticker: str):
    """Date encoded in a Kalshi sports ticker (e.g. KXNBAPTS-26NOV28...), or None."""
    m = _DATE_TOKEN.search(ticker or "")
    if not m or m.group(2) not in _MON:
        return None
    try:
        return datetime(2000 + int(m.group(1)), _MON[m.group(2)], int(m.group(3))).date()
    except ValueError:
        return None


def sport_of(series_or_ticker: str) -> str | None:
    for sp in ("NBA", "NFL", "NHL"):
        if series_or_ticker.startswith("KX" + sp):
            return sp
    return None


def parse_ts(s: Any):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def est_start(market: dict, sport: str):
    occ = parse_ts(market.get("occurrence_datetime") or market.get("expected_expiration_time"))
    return occ - timedelta(hours=NOMINAL_DURATION_H[sport]) if occ else None


def in_game_window(market: dict, sport: str, now: datetime) -> bool:
    st = est_start(market, sport)
    return bool(st) and st - timedelta(hours=GAME_WINDOW_BEFORE_H) <= now <= st + timedelta(hours=GAME_WINDOW_AFTER_H)


def snapshot(market: dict, series: str, run_ts: str) -> dict:
    row = {"run_ts": run_ts, "series_ticker": series}
    row.update({k: market[k] for k in FIELDS if k in market})
    return row


class Http:
    """Counted, paced, retrying GET against the public API."""

    def __init__(self, pause: float = PAUSE_S):
        self.pause, self.requests, self.started = pause, 0, time.time()

    def __call__(self, path: str, params: dict) -> dict:
        url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
        for attempt in range(4):
            self.requests += 1
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pm-dense-capture"}),
                                            timeout=30) as r:
                    data = json.load(r)
                time.sleep(self.pause)
                return data
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                if isinstance(e, urllib.error.HTTPError) and e.code not in (429, 500, 502, 503, 504):
                    raise
                time.sleep(self.pause * (2 ** attempt) + (2 if getattr(e, "code", 0) == 429 else 0))
        raise RuntimeError(f"GET {path} failed after retries")


def fetch_series(fetch: Fetch, series: str) -> list[dict]:
    out, cursor = [], None
    for _ in range(MAX_PAGES):
        params = {"series_ticker": series, "status": "open", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        d = fetch("/markets", params)
        page = [m for m in d.get("markets") or [] if isinstance(m, dict)]
        out += page
        cursor = d.get("cursor") or None
        if not cursor or not page:
            break
    return out


class Sink:
    """Appends gzip members to <dir>/<UTC date>.jsonl.gz; in dry-run counts the compressed bytes instead."""

    def __init__(self, directory: Path, now: datetime, dry_run: bool):
        self.path = directory / f"{now:%Y-%m-%d}.jsonl.gz"
        self.dry_run, self.rows, self.bytes = dry_run, 0, 0

    def write(self, rows: Iterable[dict]) -> None:
        rows = list(rows)
        if not rows:
            return
        blob = gzip.compress(("\n".join(json.dumps(r, separators=(",", ":"), sort_keys=True) for r in rows) + "\n").encode())
        self.rows += len(rows)
        self.bytes += len(blob)
        if not self.dry_run:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "ab") as f:
                f.write(blob)


# ---------------------------------------------------------------- modes
def run_props(fetch: Fetch, now: datetime, out: Path, dry_run: bool) -> dict:
    run_ts, today = now.strftime("%Y-%m-%dT%H:%M:%SZ"), now.astimezone(ET).date()
    sink, seen = Sink(out / "PRICE_ARCHIVE_DENSE" / "props", now, dry_run), 0
    for sport, series_list in PROP_SERIES.items():
        for series in series_list:
            ms = fetch_series(fetch, series)
            seen += len(ms)
            sink.write(snapshot(m, series, run_ts) for m in ms if ticker_date(m.get("ticker", "")) == today)
    return {"mode": "props", "markets_seen": seen, "rows": sink.rows, "gz_bytes": sink.bytes}


def run_games(fetch: Fetch, now: datetime, out: Path, dry_run: bool) -> dict:
    run_ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    sink, seen = Sink(out / "PRICE_ARCHIVE_DENSE" / "games", now, dry_run), 0
    for sport, series_list in GAME_SERIES.items():
        for series in series_list:
            ms = fetch_series(fetch, series)
            seen += len(ms)
            sink.write(snapshot(m, series, run_ts) for m in ms if in_game_window(m, sport, now))
    return {"mode": "games", "markets_seen": seen, "rows": sink.rows, "gz_bytes": sink.bytes}


def _load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def series_of(ticker: str) -> str:
    return (ticker or "").split("-", 1)[0]


def build_start_map(fetch: Fetch, now: datetime) -> dict:
    """ticker -> estimated start (epoch s) for open markets in PRINT_SERIES that start within START_MAP_HORIZON_H."""
    lo = now - timedelta(hours=PRINT_WINDOW_AFTER_H + 0.25)
    hi = now + timedelta(hours=START_MAP_HORIZON_H)
    out: dict = {}
    for series in sorted(PRINT_SERIES):
        sport = sport_of(series)
        for m in fetch_series(fetch, series):
            st = est_start(m, sport)
            if st and lo <= st <= hi and m.get("ticker"):
                out[m["ticker"]] = int(st.timestamp())
    return out


def print_in_window(start_epoch: int | None, created_epoch: int) -> bool:
    return start_epoch is not None and (start_epoch - PRINT_WINDOW_BEFORE_H * 3600 <= created_epoch
                                        <= start_epoch + PRINT_WINDOW_AFTER_H * 3600)


def run_prints(fetch: Fetch, now: datetime, out: Path, dry_run: bool) -> dict:
    state_path = out / "TRADE_PRINTS" / "_state.json"
    state = _load_state(state_path)
    last_ts = int(state.get("last_ts") or (now.timestamp() - 300))
    min_ts = last_ts - PRINT_OVERLAP_S
    seen_ids = set(state.get("ids") or [])
    starts, starts_ts = state.get("starts"), float(state.get("starts_ts") or 0)
    if not isinstance(starts, dict) or now.timestamp() - starts_ts > START_MAP_STALE_S:
        starts, starts_ts = build_start_map(fetch, now), now.timestamp()
    sink, cursor, pages, scanned, kept, max_ts = Sink(out / "TRADE_PRINTS", now, dry_run), None, 0, 0, [], last_ts
    while pages < MAX_PRINT_PAGES:
        params = {"min_ts": min_ts, "max_ts": int(now.timestamp()), "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        d = fetch("/markets/trades", params)
        pages += 1
        trades = [t for t in d.get("trades") or [] if isinstance(t, dict)]
        scanned += len(trades)
        for t in trades:
            ct = parse_ts(t.get("created_time"))
            if ct:
                max_ts = max(max_ts, int(ct.timestamp()))
            tk = t.get("ticker", "")
            if (ct and series_of(tk) in PRINT_SERIES and print_in_window(starts.get(tk), int(ct.timestamp()))
                    and t.get("trade_id") not in seen_ids):
                seen_ids.add(t.get("trade_id"))
                kept.append({"captured_ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), **t})
        cursor = d.get("cursor") or None
        if not cursor or not trades:
            break
    sink.write(kept)
    if not dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"last_ts": max_ts, "ids": sorted(i for i in seen_ids if i)[-DEDUPE_KEEP:],
                                          "starts": starts, "starts_ts": starts_ts}))
    return {"mode": "prints", "pages": pages, "trades_scanned": scanned, "rows": sink.rows, "gz_bytes": sink.bytes,
            "start_map": len(starts), "truncated": bool(pages >= MAX_PRINT_PAGES and cursor)}


MODES = {"props": run_props, "games": run_games, "prints": run_prints}

# Cadence each mode runs at per day on the box (calls/day) -- used to extrapolate a dry run. Keep in step with
# deploy/cron.archive_dense; tests/test_w124_4_dense_capture.py asserts it.
RUNS_PER_DAY = {"props": 33, "games": 288, "prints": 288}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=sorted(MODES), required=True)
    ap.add_argument("--out", default="exp_output")
    ap.add_argument("--dry-run", action="store_true", help="write nothing; print requests and gz bytes for this one run")
    ap.add_argument("--now", help="override UTC now (tests / replays), ISO-8601")
    args = ap.parse_args(argv)
    now = parse_ts(args.now) or datetime.now(timezone.utc)
    http = Http()
    t0 = time.time()
    try:
        res = MODES[args.mode](http, now, Path(args.out), args.dry_run)
    except Exception as e:  # noqa: BLE001 -- a cron run must report, not crash silently
        print(json.dumps({"mode": args.mode, "error": f"{type(e).__name__}: {e}", "requests": http.requests}))
        return 1
    secs = max(time.time() - t0, 1e-6)
    res.update({"requests": http.requests, "seconds": round(secs, 1), "dry_run": args.dry_run, "run_ts": now.isoformat()})
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())

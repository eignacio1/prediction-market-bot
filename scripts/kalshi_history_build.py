#!/usr/bin/env python3
"""Wave 47 / 47.1 D4: validated Kalshi history store (NFL 2025/2026-to-date, NHL 2025-26/2026-27-to-date).

Store: exp_output/KALSHI_HISTORY/ (one documented path; reader = prediction_market_bot.analytics.kalshi_history)
  raw/raw_<UTC-date>.jsonl   verbatim upstream pages/candle payloads (board_survey_sports_store.Store: append-only,
                             idempotent on content hash, provenance per row). Public unauthenticated GETs only.
  markets/<SERIES>.jsonl     one row per settled market: ticker, series, sport, season, times, result, expiration_value,
                             validation flags, provenance (source_url, retrieved_utc, content_sha256, commit sha).
  candles/<SERIES>.jsonl     one row per (ticker, period): normalized candles + validation + provenance of the raw row.
  VALIDATION.json, MANIFEST.json

`fetch` is rate-limited (default 1.5 req/s; every 429 halves it). `build` is a pure function of raw/ -> re-running it
rewrites byte-identical output. Prevailing-quote rule (documented in the reader): close of the latest candle with
end_period_ts <= t, 1-minute first, hourly fallback. Gate 2 (EXP-035) established equivalence for KXMLBTOTAL only; the
per-row `validation` block is what each other series carries.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_store as bs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "exp_output" / "KALSHI_HISTORY"
SERIES = {
    "nfl": ["KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL"],
    "nhl": ["KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL", "KXNHLTEAMTOTAL"],
}
FROM_ISO = "2025-08-01T00:00:00Z"        # NFL 2025 season / NHL 2025-26 preseason onward; to-date = settled at run time
MINUTE_LOOKBACK_S = 48 * 3600            # 1-minute candles: last 48h before close (<= 2880 candles, under the 5000 cap)
REQ_PER_S = 1.5
CUTOFF = "2026-08-03T00:00:00Z"          # /historical/cutoff market_settled_ts at build time
SCHEMA = "kalshi_history/1"


def sport_of(series: str) -> str:
    return "nfl" if series.startswith("KXNFL") else "nhl"


def season_of(sport: str, close_iso: str) -> str:
    y, m = int(close_iso[:4]), int(close_iso[5:7])
    if sport == "nfl":                    # Sep-Feb = season starting that Sep (Jan/Feb belong to the prior year)
        s = y if m >= 7 else y - 1
        return f"{s}"
    s = y if m >= 7 else y - 1            # NHL: Oct-Jun
    return f"{s}-{str(s + 1)[2:]}"


# ------------------------------------------------------------------ fetch
def fetch(series_list, store_dir, pause):
    client = bs.Client(pause=pause)
    store = bs.Store(Path(store_dir) / "raw")
    cutoff = bs.iso_ts(CUTOFF)
    floor = bs.iso_ts(FROM_ISO)
    have = {(r["kind"], r["key"]) for r in store.rows()}
    for series in series_list:
        mk = [m for m in bs.list_markets(client, store, series, CUTOFF)
              if m.get("result")]
        mk = [m for m in mk if bs.iso_ts(m.get("close_time") or m.get("expiration_time")) >= floor]
        print(f"{series}: settled markets since {FROM_ISO}: {len(mk)}", flush=True)
        for i, m in enumerate(mk):
            close = bs.iso_ts(m["close_time"]); opn = bs.iso_ts(m["open_time"])
            for period, start in ((60, opn), (1, max(opn, close - MINUTE_LOOKBACK_S))):
                end = close + 3600 if period == 60 else close + 120
                k = f"{m['ticker']}|{period}|{start}|{end}"
                if ("candles", k) in have:
                    continue
                try:
                    bs.candles(client, store, series, m, start, end, period, cutoff)
                except bs.FetchFailed as e:
                    print("FAILED", m["ticker"], period, e, flush=True)
            if i % 200 == 0:
                print(series, i, client.stats(), flush=True)
    print("done", client.stats(), "written", store.written, "skipped", store.skipped, flush=True)


# ------------------------------------------------------------------ build
def _num(v):
    return None if v in (None, "") else float(v)


def norm_candle(c: dict) -> dict:
    def side(name):
        s = c.get(name) or {}
        return {f: _num(s.get(f, s.get(f + "_dollars"))) for f in ("open", "high", "low", "close")}
    p = c.get("price") or {}
    return {"t": c["end_period_ts"], "bid": side("yes_bid"), "ask": side("yes_ask"),
            "last": _num(p.get("close", p.get("close_dollars"))),
            "vol": _num(c.get("volume", c.get("volume_fp")))}


def validate_candles(cs: list) -> dict:
    ts = [c["t"] for c in cs]
    bad_range = crossed = null_q = 0
    for c in cs:
        b, a = c["bid"]["close"], c["ask"]["close"]
        if b is None or a is None:
            null_q += 1
            continue
        if not (0 <= b <= 1 and 0 <= a <= 1):
            bad_range += 1
        if b > a + 1e-9:
            crossed += 1
    return {"n": len(cs), "sorted_unique": ts == sorted(set(ts)), "null_quote": null_q,
            "out_of_range": bad_range, "crossed": crossed,
            "ok": ts == sorted(set(ts)) and bad_range == 0 and crossed == 0}


def validate_market(m: dict) -> dict:
    flags = {"result_binary": m.get("result") in ("yes", "no"),
             "has_times": all(m.get(k) for k in ("open_time", "close_time")),
             "has_settlement_ts": bool(m.get("settlement_ts") or m.get("close_time")),
             "ordered_times": bool(m.get("open_time") and m.get("close_time") and m["open_time"] <= m["close_time"])}
    flags["ok"] = all(flags.values())
    return flags


def build(store_dir):
    store_dir = Path(store_dir)
    raw = bs.Store(store_dir / "raw")
    mk_rows, cs_rows = {}, {}
    for r in raw.rows():
        if r["kind"] == "markets_page":
            for m in r["payload"].get("markets") or []:
                mk_rows[m["ticker"]] = (m, r)       # later row (revision) wins; raw keeps both
        elif r["kind"] == "candles":
            ticker, period, start, end = r["key"].split("|")
            cs_rows[(ticker, int(period))] = (r, int(start), int(end))
    floor = bs.iso_ts(FROM_ISO)
    out_m, out_c = {}, {}
    vm, vc = Counter(), Counter()
    for t in sorted(mk_rows):
        m, r = mk_rows[t]
        series = t.split("-")[0]
        if series not in sum(SERIES.values(), []) or bs.iso_ts(m["close_time"]) < floor:
            continue
        sp = sport_of(series)
        val = validate_market(m)
        vm[(series, "ok" if val["ok"] else "flagged")] += 1
        out_m.setdefault(series, []).append({
            "schema": SCHEMA, "ticker": t, "series": series, "sport": sp, "season": season_of(sp, m["close_time"]),
            "event_ticker": m.get("event_ticker"), "open_time": m.get("open_time"), "close_time": m.get("close_time"),
            "occurrence_datetime": m.get("occurrence_datetime"), "settlement_ts": m.get("settlement_ts"),
            "result": m.get("result"), "expiration_value": m.get("expiration_value"),
            "floor_strike": m.get("floor_strike"), "validation": val,
            "provenance": {"source_url": r["source_url"], "retrieved_utc": r["retrieved_utc"],
                           "content_sha256": r["content_sha256"], "runtime_commit_sha": r["runtime_commit_sha"]}})
    for (t, period), (r, start, end) in sorted(cs_rows.items()):
        series = t.split("-")[0]
        if t not in mk_rows or series not in out_m:
            continue
        cs = sorted((norm_candle(c) for c in (r["payload"].get("candlesticks") or [])), key=lambda c: c["t"])
        val = validate_candles(cs)
        vc[(series, period, "ok" if val["ok"] else "flagged")] += 1
        out_c.setdefault(series, []).append({
            "schema": SCHEMA, "ticker": t, "series": series, "period_min": period, "start_ts": start, "end_ts": end,
            "candles": cs, "validation": val,
            "provenance": {"source_url": r["source_url"], "retrieved_utc": r["retrieved_utc"],
                           "content_sha256": r["content_sha256"], "runtime_commit_sha": r["runtime_commit_sha"]}})
    for sub, data in (("markets", out_m), ("candles", out_c)):
        (store_dir / sub).mkdir(exist_ok=True)
        for series, rows in data.items():
            with open(store_dir / sub / f"{series}.jsonl", "w") as fh:
                for row in rows:
                    fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    summary = {"schema": SCHEMA, "from": FROM_ISO, "raw_digest_sha256": raw.digest(),
               "markets": {f"{s}|{k}": n for (s, k), n in sorted(vm.items())},
               "candle_sets": {f"{s}|{p}m|{k}": n for (s, p, k), n in sorted(vc.items())},
               "market_rows": {s: len(v) for s, v in out_m.items()},
               "candle_rows": {s: len(v) for s, v in out_c.items()},
               "markets_without_hourly_candles": sorted(t for s in out_m for t in (x["ticker"] for x in out_m[s])
                                                         if (t, 60) not in cs_rows)[:50]}
    (store_dir / "VALIDATION.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "build"])
    ap.add_argument("--sport", choices=["nfl", "nhl", "all"], default="all")
    ap.add_argument("--store", default=str(STORE))
    ap.add_argument("--rate", type=float, default=REQ_PER_S)
    a = ap.parse_args(argv)
    sl = sum(SERIES.values(), []) if a.sport == "all" else SERIES[a.sport]
    if a.cmd == "fetch":
        fetch(sl, a.store, 1.0 / a.rate)
    else:
        print(json.dumps(build(a.store), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

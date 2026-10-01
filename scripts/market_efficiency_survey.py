#!/usr/bin/env python3
"""EXP-031 / T-599 -- cross-family market-efficiency survey of the Kalshi price archive.

Measures the MARKET, never our model. Read-only on exp_output/PRICE_ARCHIVE/. Fits,
tunes and trades nothing. Subcommands are added in the order the pre-registration
(05_RESEARCH_EXPERIMENTS/EXP-031_PREREG.md) allows them to be used:

  inventory   D1 -- per-family structural inventory (no outcomes, no ranking)

The archive is a live-quote archiver: every row is status "active" and no row carries a
settlement, so outcomes must come from an independent source (see later subcommands).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone

DEFAULT_ARCHIVE = "exp_output/PRICE_ARCHIVE"


def iter_price_rows(archive_dir: str):
    """Yield (filename, row) for every price row; raises on an unparseable line."""
    for path in sorted(glob.glob(os.path.join(archive_dir, "prices_*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                yield os.path.basename(path), json.loads(line)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def inventory(archive_dir: str) -> dict:
    fam = defaultdict(lambda: {
        "rows": 0, "tickers": set(), "events": set(), "days": set(),
        "snap_by_ticker_day": defaultdict(set), "fields_present": defaultdict(int),
        "null_mid": 0, "last_price_pos": 0, "volume_pos": 0, "oi_pos": 0,
        "bid_ask_both": 0, "ticks": defaultdict(int), "closed_tickers": set(),
        "close_times": [], "run_ts_max": "", "run_ts_min": "~",
    })
    archive_end = ""
    files = set()
    for fn, r in iter_price_rows(archive_dir):
        files.add(fn)
        a = fam[r["series_ticker"]]
        a["rows"] += 1
        a["tickers"].add(r["ticker"]); a["events"].add(r["event_ticker"])
        day = r["run_ts"][:10]
        a["days"].add(day)
        a["snap_by_ticker_day"][(r["ticker"], day)].add(r["run_ts"])
        for k, v in r.items():
            if v is not None and v != "":
                a["fields_present"][k] += 1
        if r.get("yes_mid") is None:
            a["null_mid"] += 1
        if (_f(r["last_price"]) or 0) > 0: a["last_price_pos"] += 1
        if (_f(r["volume"]) or 0) > 0: a["volume_pos"] += 1
        if (_f(r["open_interest"]) or 0) > 0: a["oi_pos"] += 1
        yb, ya = _f(r["yes_bid"]), _f(r["yes_ask"])
        if yb and ya: a["bid_ask_both"] += 1
        for q in (yb, ya):
            if q is not None:
                a["ticks"][round(q * 100 % 1, 6) == 0.0] += 1
        a["run_ts_max"] = max(a["run_ts_max"], r["run_ts"])
        a["run_ts_min"] = min(a["run_ts_min"], r["run_ts"])
        archive_end = max(archive_end, r["run_ts"])
        a["close_times"].append((r["ticker"], r.get("expiration_time") or r.get("close_time")))
    out = {"archive_end": archive_end, "n_price_files": len(files), "families": {}}
    for s, a in sorted(fam.items()):
        per = [len(v) for v in a["snap_by_ticker_day"].values()]
        exp_by_t = {}
        for t, e in a["close_times"]:
            exp_by_t[t] = e
        closed = sum(1 for e in exp_by_t.values() if e and e <= archive_end)
        out["families"][s] = {
            "rows": a["rows"], "distinct_tickers": len(a["tickers"]),
            "distinct_events": len(a["events"]), "distinct_days": len(a["days"]),
            "first_ts": a["run_ts_min"], "last_ts": a["run_ts_max"],
            "snapshots_per_ticker_day_mean": round(st.mean(per), 2),
            "snapshots_per_ticker_day_median": st.median(per),
            "snapshots_per_ticker_day_max": max(per),
            "fields_present_pct": {k: round(100 * v / a["rows"], 1) for k, v in sorted(a["fields_present"].items())},
            "null_yes_mid_pct": round(100 * a["null_mid"] / a["rows"], 2),
            "last_price_positive_pct": round(100 * a["last_price_pos"] / a["rows"], 2),
            "volume_positive_pct": round(100 * a["volume_pos"] / a["rows"], 2),
            "open_interest_positive_pct": round(100 * a["oi_pos"] / a["rows"], 2),
            "two_sided_quote_pct": round(100 * a["bid_ask_both"] / a["rows"], 2),
            "tickers_past_expiration_at_archive_end": closed,
        }
    return out


def depth_inventory(archive_dir: str) -> dict:
    d = defaultdict(lambda: {"rows": 0, "tickers": set(), "days": set(), "usable": 0})
    for path in sorted(glob.glob(os.path.join(archive_dir, "depth_*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                r = json.loads(line)
                a = d[r["series_ticker"]]
                a["rows"] += 1; a["tickers"].add(r["ticker"]); a["days"].add(r["run_ts"][:10])
                a["usable"] += 1 if r.get("usable") else 0
    return {s: {"rows": a["rows"], "distinct_tickers": len(a["tickers"]),
                "distinct_days": len(a["days"]), "usable_pct": round(100 * a["usable"] / a["rows"], 1)}
            for s, a in sorted(d.items())}


API = "https://api.elections.kalshi.com/trade-api/v2/markets"


def fetch_settlements(series: str, out_path: str, sleep_s: float = 0.15) -> int:
    """Public, read-only GET of Kalshi's own settled-market records for one series.

    Stores ticker -> {result, expiration_value, close_time, settlement_ts}. No order
    endpoint is touched; no credentials are used.
    """
    import time
    import urllib.request
    res, cursor = {}, ""
    while True:
        url = f"{API}?series_ticker={series}&status=settled&limit=1000" + (f"&cursor={cursor}" if cursor else "")
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    j = json.load(r)
                break
            except Exception:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"fetch failed for {series}")
        for m in j["markets"]:
            res[m["ticker"]] = {"result": m.get("result"), "expiration_value": m.get("expiration_value"),
                                "close_time": m.get("close_time"), "settlement_ts": m.get("settlement_ts"),
                                "event_ticker": m.get("event_ticker")}
        cursor = j.get("cursor") or ""
        if not cursor or not j["markets"]:
            break
        time.sleep(sleep_s)
    with open(out_path, "w") as fh:
        json.dump(res, fh)
    return len(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory"); p.add_argument("--archive", default=DEFAULT_ARCHIVE)
    p.add_argument("--out", required=True)
    q = sub.add_parser("fetch-settlements"); q.add_argument("--series", required=True); q.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.cmd == "fetch-settlements":
        print(args.series, fetch_settlements(args.series, args.out))
    if args.cmd == "inventory":
        res = inventory(args.archive)
        res["depth"] = depth_inventory(args.archive)
        res["generated_at"] = datetime.now(timezone.utc).isoformat()
        with open(args.out, "w") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

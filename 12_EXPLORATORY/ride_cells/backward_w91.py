"""W91.1 (EXP-042) backward / overlap test of the 11 W89.2 ride cells, hourly-candle method.

  backward_w91.py table  --raw <raw_*.jsonl> --out <dir>            # compact market table + GG-1253 start-time check
  backward_w91.py fetch  SERIES --table <t> --out <dir> --window overlap|backward --cap-min N
  backward_w91.py score  --table <t> --candles <dir> --archive <PRICE_ARCHIVE> --out <dir>

When it applies: one observation per (ticker, tier) = first two-sided hourly candle (close bid/ask) whose end is in the tier;
MLB start = ticker date+HHMM read as ET (validated against rules_primary by `table`, GG-1253); NFL tiers by ET day.
Read-only; public unauthenticated Kalshi market-data GETs only; outputs only under 12_EXPLORATORY/.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias"))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))

from _fence import safe_out  # noqa: E402

ET = ZoneInfo("America/New_York")
SERIES = ["KXMLBF5TOTAL", "KXMLBF5", "KXMLBTOTAL", "KXMLBTEAMTOTAL", "KXMLBSPREAD", "KXMLBF7", "KXNFLTOTAL", "KXMLBHIT"]
OVERLAP_START = "2026-08-01T00:00:00Z"
BACK_END = OVERLAP_START
BACK_START = {"KXMLBHIT": "2026-03-26", "KXMLBF5TOTAL": "2026-03-26", "KXMLBF5": "2026-03-26", "KXMLBTEAMTOTAL": "2026-04-01",
              "KXMLBSPREAD": "2025-10-01", "KXMLBTOTAL": "2025-10-01", "KXMLBF7": "2026-07-01", "KXNFLTOTAL": "2025-08-21"}
TIGHT = 0.01
CELLS = [  # id, series, tier, bucket label, book, side
    (1, "KXMLBHIT", "T0-2h", "20-25c", "all", "yes"), (2, "KXMLBHIT", "T0-2h", "20-25c", "tight", "yes"),
    (3, "KXMLBF5TOTAL", "T6-24h", "90-95c", "all", "yes"), (4, "KXMLBF5TOTAL", "T6-24h", "90-95c", "wide", "yes"),
    (5, "KXMLBF5TOTAL", "T2-6h", "90-95c", "tight", "yes"), (6, "KXNFLTOTAL", "D1", "5-10c", "all", "no"),
    (7, "KXMLBSPREAD", "T>24h", "20-25c", "tight", "no"), (8, "KXMLBTEAMTOTAL", "T6-24h", "15-20c", "tight", "no"),
    (9, "KXMLBF5", "T2-6h", "10-15c", "all", "no"), (10, "KXMLBTOTAL", "T0-2h", "85-90c", "wide", "yes"),
    (11, "KXMLBF7", "T0-2h", "40-45c", "wide", "yes")]
_TK = re.compile(r"-(\d\d)([A-Z]{3})(\d\d)(\d{4})?")
_MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def parse_ts(s: str) -> float:
    s = re.sub(r"Z$", "+00:00", s)
    s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s)
    return datetime.fromisoformat(s).timestamp()


def ticker_hhmm_et(event_ticker: str):
    """(epoch of ticker date+HHMM read as ET or None, ET game date) -- the GG-1253 assumption under test."""
    m = _TK.search(event_ticker)
    if not m:
        return None, None
    yy, mon, dd, hhmm = m.groups()
    y, mo, d = 2000 + int(yy), _MON[mon], int(dd)
    if hhmm:
        dt = datetime(y, mo, d, int(hhmm[:2]), int(hhmm[2:]), tzinfo=ET)
        return dt.timestamp(), dt.date()
    return None, datetime(y, mo, d).date()


def mlb_start(event_ticker: str) -> float:
    """First pitch = ticker date+HHMM read as ET (GG-1253: validated 99.6%+ against rules_primary; occurrence_datetime-3h
    fails for F5/F7 so it is NOT used)."""
    return ticker_hhmm_et(event_ticker)[0]


def tier_at(series: str, start, gdate, end_ts: float):
    """Tier of a candle ending at end_ts, or None if at/after start."""
    if start is not None:
        h = (start - end_ts) / 3600.0
        if h <= 0:
            return None
        return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"
    days = (gdate - datetime.fromtimestamp(end_ts, ET).date()).days
    return None if days < 0 else "D0" if days == 0 else "D1" if days == 1 else "D2+"


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def cmd_table(a):
    seen, n = {}, 0
    with open(a.raw) as fh:
        for line in fh:
            if '"markets_page"' not in line[:30]:
                continue
            r = json.loads(line)
            ser = r["key"].split("|")[1]
            if ser not in SERIES:
                continue
            for m in r["payload"].get("markets") or []:
                tk = m["ticker"]
                if tk in seen:
                    continue
                seen[tk] = {"t": tk, "s": ser, "e": m["event_ticker"], "res": m.get("result"), "occ": m.get("occurrence_datetime"),
                            "close": m.get("close_time"), "settle": m.get("settlement_ts") or m.get("close_time"),
                            "rules": (m.get("rules_primary") or "")[:400]}
    os.makedirs(a.out, exist_ok=True)
    # GG-1253: ticker HHMM read as ET vs occurrence_datetime-3h and the rules text clock
    chk = defaultdict(lambda: {"n": 0, "ok_occ": 0, "ok_rules": 0, "rules_unparsed": 0})
    rx = re.compile(r"at (\d{1,2}):(\d\d) ([AP])M (E[DS]T)")
    for m in seen.values():
        if not m["s"].startswith("KXMLB") or not m["occ"]:
            continue
        t_et, _ = ticker_hhmm_et(m["e"])
        if t_et is None:
            continue
        c = chk[m["s"]]
        c["n"] += 1
        c["ok_occ"] += abs((parse_ts(m["occ"]) - 3 * 3600) - t_et) <= 60
        g = rx.search(m["rules"])
        if not g:
            c["rules_unparsed"] += 1
            continue
        hh = int(g.group(1)) % 12 + (12 if g.group(3) == "P" else 0)
        c["ok_rules"] += (hh, int(g.group(2))) == (datetime.fromtimestamp(t_et, ET).hour, datetime.fromtimestamp(t_et, ET).minute)
    with open(safe_out(os.path.join(a.out, "markets.jsonl")), "w") as fo:
        for m in seen.values():
            fo.write(json.dumps(m) + "\n")
    with open(safe_out(os.path.join(a.out, "gg1253_check.json")), "w") as fj:
        json.dump(chk, fj, indent=1)
    print(len(seen), "markets;", json.dumps(chk))


def in_window(m, window):
    st = m["settle"]
    if window == "overlap":
        return st >= OVERLAP_START
    return st < BACK_END and m["e"] and (m["close"] or "")[:10] >= BACK_START[m["s"]]


def cmd_fetch(a):
    from board_survey_sports_store import Client, FetchFailed, iso_ts
    cutoff = iso_ts("2026-08-28T00:00:00Z")
    cl = Client(pause=a.pause)
    mk = [json.loads(x) for x in open(a.table)]
    mk = [m for m in mk if m["s"] == a.series and m["res"] in ("yes", "no") and in_window(m, a.window)]
    mk.sort(key=lambda m: m["close"], reverse=True)  # newest first
    path = os.path.join(a.out, f"candles_{a.series}_{a.window}.jsonl")
    done = set()
    if os.path.exists(path):
        done = {json.loads(x)["t"] for x in open(path)}
    t0 = time.time()
    with open(safe_out(path), "a") as fo:
        for m in mk:
            if m["t"] in done:
                continue
            if time.time() - t0 > a.cap_min * 60:
                break
            if m["s"].startswith("KXMLB"):
                start = mlb_start(m["e"])
                lo, hi = int(start - 48 * 3600), int(start)
            else:
                _, gd = ticker_hhmm_et(m["e"])
                k = datetime(gd.year, gd.month, gd.day, tzinfo=ET).timestamp()
                lo, hi = int(k - 3 * 86400), int(k + 86400)
            ep = "/historical/markets/%s/candlesticks" % m["t"] if iso_ts(m["settle"]) < cutoff else \
                "/series/%s/markets/%s/candlesticks" % (m["s"], m["t"])
            try:
                j, _ = cl.get(ep, start_ts=lo, end_ts=hi, period_interval=60)
            except FetchFailed:
                fo.write(json.dumps({"t": m["t"], "err": 1}) + "\n")
                continue
            cs = []
            for c in j.get("candlesticks") or []:
                yb, ya = c.get("yes_bid") or {}, c.get("yes_ask") or {}
                b = fnum(yb.get("close_dollars", yb.get("close")))  # live endpoint: close_dollars; tolerate legacy "close"
                k2 = fnum(ya.get("close_dollars", ya.get("close")))
                cs.append([c["end_period_ts"], b, k2])
            fo.write(json.dumps({"t": m["t"], "c": cs}) + "\n")
            fo.flush()
    print(a.series, a.window, "listed", len(mk), "calls", cl.calls, cl.stats())


def observations(table, candle_files):
    """First two-sided hourly candle per (ticker, tier) -> rows keyed by (series, tier)."""
    meta = {m["t"]: m for m in table}
    first, listed = {}, defaultdict(int)
    for f in candle_files:
        for line in open(f):
            r = json.loads(line)
            m = meta.get(r["t"])
            if m is None or "c" not in r:
                continue
            if m["s"].startswith("KXMLB"):
                start, gd = mlb_start(m["e"]), None
            else:
                start, (_, gd) = None, ticker_hhmm_et(m["e"])
            for end_ts, b, k in sorted(r["c"]):
                if not b or not k or k < b:
                    continue
                t = tier_at(m["s"], start, gd, end_ts)
                if t is None:
                    continue
                key = (m["t"], t)
                if key not in first:
                    first[key] = (end_ts, (b + k) / 2.0, b, k, (k - b) / 2.0, m)
    return first


def cell_rows(first):
    import calib as C
    rows = defaultdict(list)
    for (tk, t), (ts, mid, b, k, hs, m) in first.items():
        row = {"game": m["e"], "p": mid, "y": 1 if m["res"] == "yes" else 0, "bid": b, "ask": k, "ts": ts}
        book = "tight" if hs <= TIGHT else "wide"
        lab = C.bucket_label(C.bucket(mid))
        for bk in (book, "all"):
            rows[(m["s"], t, lab, bk)].append(row)
    return rows


def cmd_score(a):
    import calib as C
    table = [json.loads(x) for x in open(a.table)]
    out = {}
    for window in ("overlap", "backward"):
        files = sorted(glob.glob(os.path.join(a.candles, f"candles_*_{window}.jsonl")))
        first = observations(table, files)
        rows = cell_rows(first)
        cells, cov = {}, {}
        for cid, ser, t, lab, bk, side in CELLS:
            rs = rows.get((ser, t, lab, bk), [])
            if not rs:
                cells[cid] = {"n": 0, "games": 0, "status": "UNTESTED", "p_value": None}
                continue
            c = C.cell_test(rs)
            c["fixed_side"] = side
            c["fixed_side_net"] = None
            vals = defaultdict(list)
            for r in rs:
                vals[r["game"]].append(C.side_pnl(side, r["y"], r["bid"], r["ask"]))
            mean, lo, hi = C.cluster_bootstrap(vals, b=1000, seed=C.SEED)
            c.update(net_mean=mean, net_lo=lo, net_hi=hi)
            c["status"] = "UNTESTED" if c["games"] < 30 else "SCORED"
            if c["games"] < 30:
                c["p_value"] = None
            cells[cid] = c
        scored = {k: v for k, v in cells.items() if v["status"] == "SCORED" and v.get("p_value") is not None}
        bh = C.bh_flags(scored) if scored else {"tested": 0, "flagged": 0, "q": C.BH_Q}
        for k, v in cells.items():
            if v["status"] == "SCORED":
                held = bool(v.get("bh")) and v["net_lo"] > 0 and (v["gap"] > 0) == (v["fixed_side"] == "yes")
                v["status"] = "HELD_OUT" if held else "FAILED"
        out[window] = {"cells": cells, "bh": bh, "obs": len(first)}
    with open(safe_out(os.path.join(a.out, "score_raw.json")), "w") as fj:
        json.dump(out, fj, indent=1, default=str)
    print(json.dumps({w: {k: (v["status"], v["games"], v.get("net_mean")) for k, v in d["cells"].items()} for w, d in out.items()}, default=str))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("table"); t.add_argument("--raw", required=True); t.add_argument("--out", required=True)
    f = sub.add_parser("fetch"); f.add_argument("series"); f.add_argument("--table", required=True); f.add_argument("--out", required=True)
    f.add_argument("--window", choices=["overlap", "backward"], required=True); f.add_argument("--cap-min", type=float, default=30)
    f.add_argument("--pause", type=float, default=0.30)
    s = sub.add_parser("score"); s.add_argument("--table", required=True); s.add_argument("--candles", required=True)
    s.add_argument("--archive", default=None); s.add_argument("--out", required=True)
    a = ap.parse_args()
    {"table": cmd_table, "fetch": cmd_fetch, "score": cmd_score}[a.cmd](a)


if __name__ == "__main__":
    main()

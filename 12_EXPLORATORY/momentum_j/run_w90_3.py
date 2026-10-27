"""W90.3 runner: Part A (follow, net) and Part B (transition cuts, hold-out). Read-only on local data.

  python 12_EXPLORATORY/momentum_j/run_w90_3.py --archive <PRICE_ARCHIVE> --settle <settle dir> \
      --w897 <.../KALSHI_HISTORY/w89_7> --out momentum_j/out   (relative to 12_EXPLORATORY/)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core as K  # noqa: E402
from _fence import safe_out  # noqa: E402

ET = ZoneInfo("America/New_York")
_TK = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})(\d{4})?")
_MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
TIGHT = 0.01
SPORT = {"KXMLB": "mlb", "KXNFL": "nfl", "KXNBA": "nba", "KXNHL": "nhl"}


def parse_ts(s: str) -> float:
    s = re.sub(r"Z$", "+00:00", s)
    m = re.match(r"(.*?)(\.\d+)?(\+.*)?$", s)
    frac = ((m.group(2) or "") + "000000")[:7] if m.group(2) else ""
    return datetime.fromisoformat(m.group(1) + frac + (m.group(3) or "+00:00")).timestamp()


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mlb_start(ev: str):
    m = _TK.search(ev)
    if not m or not m.group(4):
        return None
    yy, mon, dd, hhmm = m.groups()
    return datetime(2000 + int(yy), _MON[mon], int(dd), int(hhmm[:2]), int(hhmm[2:]), tzinfo=ET).timestamp()


def nfl_starts(w897: str) -> dict:
    """event-suffix (date+teams, shared across NFL series) -> ESPN start epoch."""
    out = {}
    p = os.path.join(w897, "nfl", "events.jsonl")
    for line in open(p):
        r = json.loads(line)
        if r.get("join") == "matched" and r.get("start_utc"):
            suf = r["event_ticker"].split("-", 1)[1]
            out[suf] = datetime.fromisoformat(re.sub(r"Z$", "+00:00", r["start_utc"])).timestamp()
    return out


def load_archive(archive: str, nfl_start: dict):
    """-> {ticker: (sport, series, event, start, [(ts,bid,ask)])} for MLB + NFL (pre-start, two-sided only)."""
    ser = defaultdict(list)
    meta = {}
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                st = r.get("series_ticker", "")
                if st == "KXMLBHIT" or st[:5] not in ("KXMLB", "KXNFL"):
                    continue
                b, a = fnum(r.get("yes_bid")), fnum(r.get("yes_ask"))
                if not b or not a or a < b or a >= 1.0:
                    continue
                ev, tk = r["event_ticker"], r["ticker"]
                if tk not in meta:
                    start = mlb_start(ev) if st.startswith("KXMLB") else nfl_start.get(ev.split("-", 1)[1])
                    meta[tk] = (SPORT[st[:5]], st, ev, start)
                if meta[tk][3] is None:
                    continue
                ser[tk].append((parse_ts(r["run_ts"]), b, a))
    return {tk: (*meta[tk], sorted(set(p))) for tk, p in ser.items() if meta[tk][3] is not None}


def load_candles(w897: str, sports=("nba", "nhl", "nfl")):
    out = {}
    for sp in sports:
        for f in glob.glob(os.path.join(w897, sp, "candles", "KX*GAME.jsonl")):
            for line in open(f):
                r = json.loads(line)
                pts = []
                for c in r["candles"]:
                    b, a = fnum((c.get("yes_bid") or {}).get("close_dollars")), fnum((c.get("yes_ask") or {}).get("close_dollars"))
                    if b and a and a >= b and a < 1.0:
                        pts.append((float(c["end_period_ts"]), b, a))
                if len(pts) >= 4:
                    out[r["ticker"]] = (sp, r["series"], r["event_ticker"], float(r["start_ts"]), sorted(pts),
                                        1.0 if r.get("result") == "yes" else 0.0 if r.get("result") == "no" else None)
    return out


def load_settle(d: str) -> dict:
    res = {}
    for f in glob.glob(os.path.join(d, "*.json")):
        for t, v in json.load(open(f)).items():
            if v.get("result") in ("yes", "no"):
                res[t] = 1.0 if v["result"] == "yes" else 0.0
    return res


def build_rows(archive_data: dict, candle_data: dict, settle: dict) -> list:
    rows = []
    seen_nfl = set()
    for tk, (sp, ser, ev, start, pts) in archive_data.items():
        seen_nfl.add(tk)
        y = settle.get(tk)
        for s in K.find_signals(pts, start):
            rows.append(_row(s, sp, ser, ev, start, y, "archive20m"))
    for tk, (sp, ser, ev, start, pts, y0) in candle_data.items():
        if tk in seen_nfl:
            continue
        y = settle.get(tk, y0)
        for s in K.find_signals(pts, start, lb=(3000.0, 4200.0), step_max=4200.0, hold_tol=1800.0):
            rows.append(_row(s, sp, ser, ev, start, y, "candle1h"))
    return rows


def _row(s, sp, ser, ev, start, y, src):
    r = K.realize(s, y)
    return {"sport": sp, "fam": ser, "game": ev, "ts": s["ts"], "size": s["size"], "move": s["move"], "dir": s["dir"],
            "tta": K.tta_tier(s["tta_h"]), "tta_h": s["tta_h"], "book": "tight" if s["hs"] <= TIGHT else "wide",
            "news": K.news_flag(sp, start, s["look_ts"], s["ts"]), "src": src, "res": r}


def flat(rows, hold):
    out = []
    for r in rows:
        x = r["res"].get(hold)
        if x:
            out.append({**r, "gross": x["gross"], "follow": x["follow"], "fade": x["fade"]})
    return out


def grid(rows, dims):
    """cells for each (dims..., hold). dims = list of row-keys."""
    cells = {}
    for hold in K.HOLDS:
        fr = flat(rows, hold)
        groups = defaultdict(list)
        for r in fr:
            groups[tuple(r[d] for d in dims) + (hold,)].append(r)
        for k, g in groups.items():
            cells[k] = {"follow": K.cell_stats(g, "follow"), "fade": K.cell_stats(g, "fade")}
    return cells


def part_b(rows, cut_date):
    """Interpretable cuts: sport x tta x size-class x news, fit on the earlier half by date, scored on the later half.
    A cell is routed FOLLOW if the train follow-net interval excludes 0 above, FADE if the train fade-net does; the
    hold-out reports the same rule's net with game-clustered interval. 3h hold."""
    fr = flat(rows, "3h")
    for r in fr:
        r["szc"] = "big" if r["move"] >= 0.05 else "small"
    train = [r for r in fr if r["ts"] < cut_date]
    test = [r for r in fr if r["ts"] >= cut_date]
    out = []
    keyf = lambda r: (r["sport"], r["tta"], r["szc"], r["news"])  # noqa: E731
    tg, eg = defaultdict(list), defaultdict(list)
    for r in train:
        tg[keyf(r)].append(r)
    for r in test:
        eg[keyf(r)].append(r)
    for k, g in tg.items():
        ft, fd = K.cell_stats(g, "follow"), K.cell_stats(g, "fade")
        if not ft["testable"] and not fd["testable"]:
            continue
        route = "FOLLOW" if ft["lo"] > 0 else "FADE" if fd["lo"] > 0 else None
        te = eg.get(k, [])
        if not te:
            out.append({"cell": k, "route": route, "train": ft if route != "FADE" else fd, "test": None})
            continue
        tf = K.cell_stats(te, "follow")
        td = K.cell_stats(te, "fade")
        out.append({"cell": k, "route": route, "train_follow": ft, "train_fade": fd, "test_follow": tf, "test_fade": td})
    return out, len(train), len(test)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", required=True)
    ap.add_argument("--w897", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    settle = load_settle(a.settle)
    nstart = nfl_starts(a.w897)
    arch = load_archive(a.archive, nstart)
    cand = load_candles(a.w897)
    rows = build_rows(arch, cand, settle)
    print("tickers archive", len(arch), "candle", len(cand), "signals", len(rows))
    res = {}
    for name, dims in (("main", ["sport", "fam", "size"]), ("tta", ["sport", "tta"]), ("book", ["sport", "book"]),
                       ("news", ["sport", "news"]), ("src", ["sport", "src"]), ("dir", ["sport", "dir"])):
        res[name] = grid(rows, dims)
    allc = {}
    for name, g in res.items():
        for k, v in g.items():
            allc[(name,) + k + ("follow",)] = v["follow"]
            allc[(name,) + k + ("fade",)] = v["fade"]
    mult = K.bh(allc)
    dates = sorted(r["ts"] for r in rows)
    cut = dates[len(dates) // 2]
    pb, ntr, nte = part_b(rows, cut)
    ser = lambda c: {"|".join(map(str, k)): v for k, v in c.items()}  # noqa: E731
    with open(safe_out(os.path.join(a.out, "summary.json")), "w") as f:
        json.dump({"mult": mult, "cut_ts": cut, "n_train": ntr, "n_test": nte, "signals": len(rows),
                   "cells": ser(allc), "partB": [{**p, "cell": "|".join(p["cell"])} for p in pb]}, f, default=str)
    print("BH", mult, "cut", datetime.fromtimestamp(cut).isoformat(), "train", ntr, "test", nte)


if __name__ == "__main__":
    main()

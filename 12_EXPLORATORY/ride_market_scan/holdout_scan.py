"""W90.1 Part A: 89.2's calibration method (longshot_bias/calib.py, unchanged) on the W89.7 settled history with TRUE start
times, with a TIME SPLIT: cells are chosen on the earlier half of games and tested on the later half.

  python 12_EXPLORATORY/ride_market_scan/holdout_scan.py --root exp_output/KALSHI_HISTORY/w89_7 --out ride_market_scan/out   (relative paths resolve inside 12_EXPLORATORY/)

Unit: the first two-sided hourly-candle snapshot (candle close bid/ask) of each (ticker, time tier), tier = hours before the
ESPN-joined start. Discovery: per (sport, family) the games are split at the median start; cell_test + BH (q=0.10) over every
testable discovery cell; a CANDIDATE is BH-flagged with net lower bound > 0 on its own side. Hold-out: the same cell, the side
FIXED from discovery, net-of-k007 at the quote with a game-clustered interval; HELD OUT iff the hold-out lower bound > 0.
When it applies: a cell needs >= MIN_EVENTS games on each side of the split; otherwise it is reported untestable.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias"))
import calib as C  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402

TIGHT = 0.01


def tier_h(h: float):
    if h <= 0:
        return None
    return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"


def f(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def snapshots(rec: dict):
    """First two-sided candle per tier before start. Candle end_period_ts is the CLOSE of the hour, so a candle is usable
    only if its end is <= start (no look at the start hour or later)."""
    seen = {}
    for c in sorted(rec["candles"], key=lambda c: c["end_period_ts"]):
        if c["end_period_ts"] > rec["start_ts"]:
            continue
        bid = f((c.get("yes_bid") or {}).get("close_dollars"))
        ask = f((c.get("yes_ask") or {}).get("close_dollars"))
        if not bid or not ask or ask < bid or ask >= 1.0:
            continue
        t = tier_h((rec["start_ts"] - c["end_period_ts"]) / 3600.0)
        if t and t not in seen:
            seen[t] = (bid, ask)
    return seen


def load(root: str):
    rows = []  # (sport, family, tier, row)
    for sport in ("nba", "nhl", "nfl"):
        for path in sorted(glob.glob(os.path.join(root, sport, "candles", "*.jsonl"))):
            fam = os.path.basename(path)[:-6]
            for line in open(path):
                rec = json.loads(line)
                if rec.get("result") not in ("yes", "no") or not rec["candles"]:
                    continue
                y = 1.0 if rec["result"] == "yes" else 0.0
                for t, (bid, ask) in snapshots(rec).items():
                    rows.append((sport, fam, t, {"game": rec["event_ticker"], "p": (bid + ask) / 2, "y": y, "bid": bid,
                                                 "ask": ask, "ts": rec["start_ts"], "hs": (ask - bid) / 2}))
    return rows


def side_net(rs, side):
    vals = defaultdict(list)
    for r in rs:
        vals[r["game"]].append(C.side_pnl(side, r["y"], r["bid"], r["ask"]))
    return cluster_bootstrap(vals, b=1000, seed=C.SEED)


def run(rows):
    groups = defaultdict(list)
    for sport, fam, t, r in rows:
        groups[(sport, fam)].append((t, r))
    disc_cells, hold_rows, splits = {}, {}, {}
    for key, items in groups.items():
        starts = sorted({r["ts"] for _, r in items})
        cut = starts[len(starts) // 2]
        splits[key] = cut
        d, h = defaultdict(list), defaultdict(list)
        for t, r in items:
            for book in ("all", "tight" if r["hs"] <= TIGHT else "wide"):
                (d if r["ts"] < cut else h)[(t, C.bucket(r["p"]), book)].append(r)
        for ck, rs in d.items():
            disc_cells[key + ck] = C.cell_test(rs)
        for ck, rs in h.items():
            hold_rows[key + ck] = rs
    fam_bh = C.bh_flags(disc_cells)
    out = []
    for k, c in disc_cells.items():
        if not (c["bh"] and c["net_lo"] > 0):
            continue
        hr = hold_rows.get(k, [])
        hg = len({r["game"] for r in hr})
        rec = {"sport": k[0], "family": k[1], "tier": k[2], "bucket": C.bucket_label(k[3]), "book": k[4], "side": c["side"],
               "disc_n": c["n"], "disc_games": c["games"], "disc_net": c["net_mean"], "disc_lo": c["net_lo"],
               "hold_n": len(hr), "hold_games": hg, "hold_net": None, "hold_lo": None, "hold_hi": None, "held_out": False}
        if hg >= 15:
            m, lo, hi = side_net(hr, c["side"])
            rec.update(hold_net=m, hold_lo=lo, hold_hi=hi, held_out=bool(lo > 0))
        out.append(rec)
    return disc_cells, out, fam_bh, splits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    od = safe_out(os.path.join(a.out, "holdout_summary.json")).parent
    rows = load(a.root)
    cells, cand, bh, splits = run(rows)
    summary = {"snapshot_rows": len(rows), "discovery_cells": len(cells), "bh": bh, "candidates": len(cand),
               "held_out": sum(r["held_out"] for r in cand),
               "split_start_epoch": {f"{k[0]}/{k[1]}": v for k, v in splits.items()}}
    json.dump(summary, open(safe_out(os.path.join(od, "holdout_summary.json")), "w"), indent=1)
    cols = ["sport", "family", "tier", "bucket", "book", "side", "disc_n", "disc_games", "disc_net", "disc_lo", "hold_n",
            "hold_games", "hold_net", "hold_lo", "hold_hi", "held_out"]
    with open(safe_out(os.path.join(od, "holdout_cells.csv")), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in sorted(cand, key=lambda r: (r["sport"], r["family"], r["tier"], r["bucket"], r["book"])):
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

"""W89.2 runner. Part A: calibration of Kalshi sports prices by family x time-to-start x price bucket x book class.
Part B: reversion after large pre-game one-step moves. Read-only on the local price archive and cached settlements.

  python 12_EXPLORATORY/longshot_bias/run_w89_2.py --archive <PRICE_ARCHIVE dir> --settle <settle dir> --out <dir inside 12_EXPLORATORY/, e.g. 12_EXPLORATORY/longshot_bias/out>
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import calib as C  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.money import fee_k007  # noqa: E402

TIGHT = 0.01  # half_spread <= 1c = deep/tight book class (archive records spread, not size)


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def scan(archive: str):
    """First two-sided pre-start snapshot per (ticker, tier); and per-ticker pre-start mid series for Part B."""
    first, series, meta = {}, defaultdict(list), {}
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                bid, ask = fnum(r.get("yes_bid")), fnum(r.get("yes_ask"))
                if not bid or not ask or ask < bid:
                    continue
                ev = r["event_ticker"]
                ts = C.parse_ts(r["run_ts"])
                t = C.tier(ev, ts)
                if t is None:
                    continue
                tk = r["ticker"]
                mid, hs = (bid + ask) / 2.0, (ask - bid) / 2.0
                key = (tk, t)
                if key not in first:
                    first[key] = (ts, mid, bid, ask, hs)
                    meta[tk] = (r["series_ticker"], ev)
                # Part B only where the strictly pre-game window is known: MLB hours, NFL D1/D2+
                if t != "D0":
                    series[tk].append((ts, mid, hs))
    return first, series, meta


def part_a(first, meta, settle):
    rows = defaultdict(list)
    skipped = 0
    for (tk, t), (ts, mid, bid, ask, hs) in first.items():
        y = settle.get(tk)
        if y is None:
            skipped += 1
            continue
        fam, ev = meta[tk]
        book = "tight" if hs <= TIGHT else "wide"
        row = {"game": ev, "p": mid, "y": y, "bid": bid, "ask": ask, "ts": ts}
        rows[(fam, t, C.bucket(mid), book)].append(row)
        rows[(fam, t, C.bucket(mid), "all")].append(row)
    cells = {}
    for k, rs in rows.items():
        c = C.cell_test(rs)
        c["split_sign_same"] = None
        ts_sorted = sorted(r["ts"] for r in rs)
        mid_ts = ts_sorted[len(ts_sorted) // 2]
        h1 = [r for r in rs if r["ts"] <= mid_ts]
        h2 = [r for r in rs if r["ts"] > mid_ts]
        if h1 and h2:
            g1 = sum(r["y"] - r["p"] for r in h1) / len(h1)
            g2 = sum(r["y"] - r["p"] for r in h2) / len(h2)
            c["split_sign_same"] = (g1 > 0) == (g2 > 0) and (g1 > 0) == (c["gap"] > 0)
        cells[k] = c
    return cells, skipped


def part_b(series, meta, settle):
    moves = defaultdict(list)
    for tk, pts in series.items():
        pts.sort()
        fam, ev = meta[tk]
        i = 1
        while i < len(pts):
            d = pts[i][1] - pts[i - 1][1]
            if abs(d) >= C.MOVE_MIN and pts[i][0] - pts[i - 1][0] <= 3600:
                for lag, lab in ((3, "1h"), (9, "3h")):
                    j = i + lag
                    if j < len(pts) and pts[j][0] - pts[i][0] <= lag * 1500:
                        sgn = 1.0 if d > 0 else -1.0
                        cost = pts[i][2] + pts[j][2] + fee_k007(pts[i][1]) + fee_k007(pts[j][1])
                        moves[(fam, lab, "up" if d > 0 else "down")].append(
                            {"game": ev, "rev": -sgn * (pts[j][1] - pts[i][1]), "cost": cost})
                i += 9  # one move per 3h window per ticker to limit overlap
            else:
                i += 1
    cells = {k: C.reversion_cell(v) for k, v in moves.items()}
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out_dir = safe_out(os.path.join(a.out, "summary.json")).parent  # fence: writes stay inside 12_EXPLORATORY/
    settle = C.load_settlements(a.settle)
    first, series, meta = scan(a.archive)
    cellsA, skipped = part_a(first, meta, settle)
    famA = C.bh_flags(cellsA)
    cellsB = part_b(series, meta, settle)
    famB = C.bh_flags(cellsB)
    summary = {"settled_tickers": len(settle), "ticker_tiers": len(first), "unsettled_skipped": skipped,
               "partA_bh": famA, "partB_bh": famB,
               "partA_bonferroni": sum(1 for c in cellsA.values() if c["p_value"] is not None and c["p_value"] < 0.05 / max(famA["tested"], 1))}
    json.dump(summary, open(safe_out(os.path.join(out_dir, "summary.json")), "w"), indent=1)
    with open(safe_out(os.path.join(out_dir, "partA_cells.csv")), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "tier", "bucket", "book", "n", "games", "pbar", "f", "gap", "z", "p", "bh", "side",
                    "net_mean", "net_lo", "net_hi", "split_same", "testable"])
        for (fam, t, b, book), c in sorted(cellsA.items()):
            w.writerow([fam, t, C.bucket_label(b), book, c["n"], c["games"], round(c["pbar"], 4), round(c["f"], 4),
                        round(c["gap"], 4), c["z"], c["p_value"], c["bh"], c["side"], round(c["net_mean"], 4),
                        round(c["net_lo"], 4), round(c["net_hi"], 4), c["split_sign_same"], c["testable"]])
    with open(safe_out(os.path.join(out_dir, "partB_cells.csv")), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "horizon", "direction", "n", "games", "gross", "net", "net_lo", "net_hi", "p", "bh", "testable"])
        for (fam, lab, d), c in sorted(cellsB.items()):
            w.writerow([fam, lab, d, c["n"], c["games"], round(c["gross"], 4), round(c["net"], 4), round(c["net_lo"], 4),
                        round(c["net_hi"], 4), c["p_value"], c.get("bh"), c["testable"]])
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

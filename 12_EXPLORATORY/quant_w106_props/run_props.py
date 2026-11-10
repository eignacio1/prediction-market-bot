"""W106.3 B-058 -- EXPLORATORY, never a verdict. Held-out net-of-cost calibration of Kalshi prop (KXMLBHIT) vs
game-line families from the PUBLIC price archive and public settled results. Reads no shadow/ledger/log files."""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias"))
sys.path.insert(0, os.path.dirname(HERE))
import calib as C  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402
from prediction_market_bot.quant.multiplicity import holm  # noqa: E402
from prediction_market_bot.quant.props_calib import holdout_cell, net_pnl_side, time_split  # noqa: E402

PROPS = {"KXMLBHIT"}
LINES = {"KXMLBTOTAL", "KXMLBSPREAD", "KXMLBGAME", "KXMLBTEAMTOTAL", "KXMLBF5TOTAL"}
BANDS = [(0, .10, "<10c"), (.10, .30, "10-30c"), (.30, .70, "30-70c"), (.70, .90, "70-90c"), (.90, 1.01, ">90c")]


def band(p):
    return next(l for lo, hi, l in BANDS if lo <= p < hi)


def liq(hs):  # archive records spread, not size; depth-file tiers are per family (see Part A table)
    return "deep" if hs <= 0.01 else "mid" if hs <= 0.025 else "thin"


def load_settle(dirs):
    s = {}
    for d in dirs:
        for f in glob.glob(os.path.join(d, "*.json")):
            for k, v in json.load(open(f)).items():
                s[k] = 1.0 if v["result"] == "yes" else 0.0
    return s


def scan(archive, fams):
    first = {}
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("series_ticker") not in fams:
                continue
            try:
                bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
            except (TypeError, ValueError, KeyError):
                continue
            if not bid or not ask or ask < bid:
                continue
            ts = C.parse_ts(r["run_ts"])
            t = C.tier(r["event_ticker"], ts)
            if t is None:
                continue
            key = (r["ticker"], t)
            if key not in first:
                first[key] = (ts, bid, ask, r["series_ticker"], r["event_ticker"])
    return first


def rows_from(first, settle):
    out = []
    for (tk, t), (ts, bid, ask, fam, ev) in first.items():
        y = settle.get(tk)
        if y is None:
            continue
        mid = (bid + ask) / 2
        out.append({"game": ev, "ts": ts, "y": y, "bid": bid, "ask": ask, "p": mid, "fam": fam, "tier": t,
                    "band": band(mid), "liq": liq((ask - bid) / 2), "cls": "prop" if fam in PROPS else "line"})
    return out


def cells(rows, keyf, minn=200):
    g = defaultdict(list)
    for r in rows:
        g[keyf(r)].append(r)
    res = {}
    for k, rs in g.items():
        if len(rs) < minn:
            continue
        fit, hold = time_split(rs)
        c = holdout_cell(fit, hold)
        c["n"] = len(rs)
        res[k] = c
    ks = [k for k, c in res.items() if c["p_pos"] is not None]
    if ks:
        for k, h in zip(ks, holm([res[k]["p_pos"] for k in ks])):
            res[k]["p_holm"] = h["p_adj"]
            res[k]["holm_reject"] = h["reject"]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", nargs="+", required=True)
    ap.add_argument("--out", default="quant_w106_props/results.json")
    a = ap.parse_args()
    settle = load_settle(a.settle)
    rows = rows_from(scan(a.archive, PROPS | LINES), settle)
    out = {"n_rows": len(rows), "settled_tickers": len(settle)}
    out["family_band_liq"] = {"|".join(k): v for k, v in cells(rows, lambda r: (r["fam"], r["band"], r["liq"])).items()}
    out["family_band_tier"] = {"|".join(k): v for k, v in cells(rows, lambda r: (r["fam"], r["band"], r["tier"])).items()}
    # props vs lines, same nights: restrict to game dates present in both classes
    def d(r):
        return r["game"].split("-")[1][:7]
    nights = {d(r) for r in rows if r["cls"] == "prop"} & {d(r) for r in rows if r["cls"] == "line"}
    same = [r for r in rows if d(r) in nights]
    out["nights_shared"] = len(nights)
    cmp = {}
    for cls in ("prop", "line"):
        rs = [r for r in same if r["cls"] == cls]
        fit, hold = time_split(rs)
        gaps = defaultdict(list)
        for r in rs:
            gaps[r["game"]].append(r["y"] - r["p"])
        m, lo, hi = cluster_bootstrap(gaps, b=1000)
        cmp[cls] = {"n": len(rs), "gap_mean": m, "gap_lo": lo, "gap_hi": hi, **holdout_cell(fit, hold)}
        # longshot shape: gap on <10c and >90c vs middle
        for b in ("<10c", "30-70c", ">90c"):
            g = defaultdict(list)
            for r in rs:
                if r["band"] == b:
                    g[r["game"]].append(r["y"] - r["p"])
            cmp[cls]["gap_" + b] = cluster_bootstrap(g, b=1000) if g else None
    out["props_vs_lines"] = cmp
    p = safe_out(a.out)
    p.write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    print(json.dumps({k: v for k, v in out.items() if k in ("n_rows", "settled_tickers", "nights_shared")}))


if __name__ == "__main__":
    main()

"""W94.Q Part A: re-score the reported net figures of 89.2 (11 cells), 90.3 (headline grid) and 91.2 (ladder) with the
exact per-series taker fee (`quant.money.fee_rate`, phase prelive: every archived snapshot is pre-start) instead of
`fee_k007`. Measure-only: no existing function, pre-registration or ride_cells.toml status is touched.

  python 12_EXPLORATORY/quant_w94/exact_fee_recompute.py --archive <PRICE_ARCHIVE> --settle <settle dir> \
      --until 2026-10-27 --out 12_EXPLORATORY/quant_w94/out

Fee unit: per contract, unrounded (`fee_rate`). `fee()` rounds an ORDER up to a centicent; per contract that rounding is
not a property of the trade, so it is excluded here (it adds < 0.5 centicent per order, split over its contracts).
Applies to: any taker leg priced off a pre-start quote. Does not apply to maker fills or to in-play legs (phase live).
NFL/NBA/NHL game series have multiplier 1 in the table, so exact == k007 there by construction (asserted in the tests);
only the MLB series move. The `--until` cap reproduces each wave's own data window; the archive has grown since.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
for sub in ("", "longshot_bias", "momentum_j", "ride_ladder"):
    sys.path.insert(0, os.path.join(EXP, sub))
sys.path.insert(0, os.path.join(EXP, "..", "src"))
from prediction_market_bot.quant.inference import cluster_bootstrap, pooled_cluster_test  # noqa: E402
from prediction_market_bot.quant.money import fee_k007, fee_rate  # noqa: E402

PHASE = "prelive"


def series_of(ticker: str) -> str:
    return ticker.split("-", 1)[0]


def fee_x(series: str, q: float) -> float:
    return fee_rate(series, q, "taker", PHASE)


def leg_net(side: str, y: float, bid: float, ask: float, fee) -> float:
    """Hold-to-settle net of one taker leg: YES at the ask, NO at 1 - bid. `fee(q)` is the per-contract fee."""
    if side == "yes":
        return y - ask - fee(ask)
    q = 1.0 - bid
    return (1.0 - y) - q - fee(q)


def cell_net(rows: list, side: str, fee_for) -> dict:
    """Game-clustered mean net and 95% interval (same bootstrap, seed and replicates as calib.cell_test)."""
    import calib as C
    vals = defaultdict(list)
    for r in rows:
        vals[r["game"]].append(leg_net(side, r["y"], r["bid"], r["ask"], lambda q, r=r: fee_for(r, q)))
    m, lo, hi = cluster_bootstrap(vals, b=1000, seed=C.SEED)
    return {"net": m, "lo": lo, "hi": hi}


def status_change(old_lo: float, new_lo: float) -> str:
    return ("none (lo>0 both)" if old_lo > 0 and new_lo > 0 else
            "LOST (lo>0 -> lo<=0)" if old_lo > 0 else
            "GAINED (lo<=0 -> lo>0)" if new_lo > 0 else "none (lo<=0 both)")


# The archive subset (prices_*.jsonl dated <= --until) is built by the caller, outside 12_EXPLORATORY:
#   mkdir D; for f in PRICE_ARCHIVE/prices_*.jsonl; do [ "$(basename $f | cut -c8-17)" \< "2026-10-28" ] && ln -s "$f" D/; done
# This script only reads it and writes to stdout (the results file is that stdout, saved by the caller).


# ------------------------------------------------------------------------------------------------ 89.2
CELLS_89 = [  # (family, tier, bucket label, book) -- the 11 CALIBRATION cells of ride_cells.toml, with the toml's reported net
    ("KXMLBHIT", "T0-2h", "20-25c", "all", 1892, 0.027, 0.0065),
    ("KXMLBHIT", "T0-2h", "20-25c", "tight", 1151, 0.044, 0.017),
    ("KXMLBF5TOTAL", "T6-24h", "90-95c", "all", 143, 0.038, 0.022),
    ("KXMLBF5TOTAL", "T6-24h", "90-95c", "wide", 111, 0.033, 0.011),
    ("KXMLBF5TOTAL", "T2-6h", "90-95c", "tight", 85, 0.043, 0.017),
    ("KXNFLTOTAL", "D1", "5-10c", "all", 154, 0.038, 0.0065),
    ("KXMLBSPREAD", "T>24h", "20-25c", "tight", 186, 0.052, 0.0026),
    ("KXMLBTEAMTOTAL", "T6-24h", "15-20c", "tight", 49, 0.095, 0.0085),
    ("KXMLBF5", "T2-6h", "10-15c", "all", 44, 0.078, 0.0087),
    ("KXMLBTOTAL", "T0-2h", "85-90c", "wide", 52, 0.089, 0.047),
    ("KXMLBF7", "T0-2h", "40-45c", "wide", 121, 0.065, 0.0006),
]


def run_89(archive_subset: str, settle_dir: str) -> list:
    import calib as C
    import run_w89_2 as R
    settle = C.load_settlements(settle_dir)
    first, _series, meta = R.scan(archive_subset)
    want = {(f, t, b, k) for f, t, b, k, *_ in CELLS_89}
    rows = defaultdict(list)
    for (tk, t), (ts, mid, bid, ask, hs) in first.items():
        y = settle.get(tk)
        if y is None:
            continue
        fam, ev = meta[tk]
        lab = C.bucket_label(C.bucket(mid))
        book = "tight" if hs <= R.TIGHT else "wide"
        row = {"game": ev, "p": mid, "y": y, "bid": bid, "ask": ask, "ts": ts, "fam": fam}
        for bk in (book, "all"):
            if (fam, t, lab, bk) in want:
                rows[(fam, t, lab, bk)].append(row)
    out = []
    for fam, t, lab, bk, n0, m0, lo0 in CELLS_89:
        rs = rows.get((fam, t, lab, bk), [])
        if not rs:
            out.append({"cell": (fam, t, lab, bk), "rep_n": n0, "rep_net": m0, "rep_lo": lo0, "n": 0})
            continue
        c = C.cell_test(rs)  # k007, unchanged code path
        ex = cell_net(rs, c["side"], lambda r, q: fee_x(r["fam"], q))
        out.append({"cell": (fam, t, lab, bk), "rep_n": n0, "rep_net": m0, "rep_lo": lo0, "n": c["n"], "games": c["games"],
                    "side": c["side"], "old": {"net": c["net_mean"], "lo": c["net_lo"], "hi": c["net_hi"]}, "exact": ex,
                    "change": status_change(c["net_lo"], ex["lo"])})
    return out


# ------------------------------------------------------------------------------------------------ 90.3
def side_leg_x(series: str, side: str, entry: tuple, exit_, y) -> float:
    """core.side_leg_pnl with the exact per-series fee on both legs."""
    eb, ea = entry
    f = lambda q: fee_x(series, q)  # noqa: E731
    if side == "yes":
        q = ea
        if exit_ is None:
            return y - q - f(q)
        v = exit_[0]
    else:
        q = 1.0 - eb
        if exit_ is None:
            return (1.0 - y) - q - f(q)
        v = 1.0 - exit_[1]
    return v - q - f(q) - f(v)


def realize_x(sig: dict, y, series: str) -> dict:
    import core as K
    f_side, a_side = ("yes", "no") if sig["dir"] > 0 else ("no", "yes")
    res = {}
    for hold in K.HOLDS:
        if hold == "settle":
            if y is None:
                continue
            ex, gross = None, (y - sig["entry_mid"]) * sig["dir"]
        else:
            if hold not in sig["ex"]:
                continue
            ex, gross = sig["ex"][hold][:2], sig["ex"][hold][2]
        res[hold] = {"gross": gross, "follow": side_leg_x(series, f_side, sig["entry"], ex, y),
                     "fade": side_leg_x(series, a_side, sig["entry"], ex, y)}
    return res


def run_90(archive_subset: str, settle_dir: str) -> dict:
    import core as K
    import run_w90_3 as R
    settle = R.load_settle(settle_dir)
    arch = R.load_archive(archive_subset, {})  # NFL needs the 89.7 events file (not local): NFL rows are M=1, unchanged
    old_rows, new_rows = [], []
    for tk, (sp, ser, ev, start, pts) in arch.items():
        y = settle.get(tk)
        for s in K.find_signals(pts, start):
            ro = R._row(s, sp, ser, ev, start, y, "archive20m")
            old_rows.append(ro)
            new_rows.append({**ro, "res": realize_x(s, y, ser)})
    out = {"signals": len(old_rows), "pooled": {}, "grid": {}}
    for hold in K.HOLDS:
        for tag, rows in (("old", old_rows), ("exact", new_rows)):
            fr = R.flat(rows, hold)
            out["pooled"][(hold, tag)] = {k: K.cell_stats(fr, k) for k in ("follow", "fade")} if fr else None
            for r in fr:
                pass
            if tag == "old":
                continue
        # main grid (sport, fam, size) per hold, follow + fade, old vs exact
        for tag, rows in (("old", old_rows), ("exact", new_rows)):
            g = defaultdict(list)
            for r in R.flat(rows, hold):
                g[(r["sport"], r["fam"], r["size"])].append(r)
            for k, rs in g.items():
                out["grid"].setdefault((k, hold), {})[tag] = {s: K.cell_stats(rs, s) for s in ("follow", "fade")}
    return out


# ------------------------------------------------------------------------------------------------ 91.2
def trigger_f(rec: dict, fee_for):
    L, b, a = rec["L"], rec["bid"], rec["ask"]
    f = lambda q: fee_for(rec["series"], q)  # noqa: E731
    ey = L - a - f(a)
    q = 1.0 - b
    en = (1.0 - L) - q - f(q)
    e, side = (ey, "yes") if ey >= en else (en, "no")
    return (side, e) if e > 0 else None


def ladder_rows(recs: list, settle: dict, fee_for) -> list:
    import calib
    import ladder_ride as LR
    rows = []
    for r in recs:
        tg = trigger_f(r, fee_for)
        if tg is None or r["ticker"] not in settle:
            continue
        side, e = tg
        y = settle[r["ticker"]]
        rows.append({"series": r["series"], "game": r["game"], "tier": r["tier"], "gap": LR.gapbin(e), "net_edge": e,
                     "book": "tight" if (r["ask"] - r["bid"]) / 2 <= 0.01 else "wide", "side": side,
                     "pnl": leg_net(side, y, r["bid"], r["ask"], lambda q, s=r["series"]: fee_for(s, q)),
                     "date": str(calib.game_start(r["game"])[1])})
    return rows


def run_91(archive_subset: str, settle_dir: str) -> dict:
    import calib
    import ladder_ride as LR
    settle = calib.load_settlements(settle_dir)
    recs, _idx = LR.build_records(LR.load(archive_subset))
    old = ladder_rows(recs, settle, lambda s, q: fee_k007(q))
    new = ladder_rows(recs, settle, fee_x)
    split = sorted({r["date"] for r in old})[len(old and {r["date"] for r in old}) // 2] if old else ""  # the OLD run's split date, fixed

    def stat(rs):
        if not rs:
            return None
        t = pooled_cluster_test([(r["game"], r["pnl"]) for r in rs], b=1500)
        return {"n": len(rs), "games": t["n_games"], "net": t["mean"], "lo": t["ci95"][0], "hi": t["ci95"][1]}

    out = {"triggers_old": len(old), "triggers_exact": len(new), "split": split, "whole": {}, "cells": {}}
    for tag, rows in (("old", old), ("exact", new)):
        out["whole"][tag] = {"all": stat(rows), "second_half": stat([r for r in rows if r["date"] >= split])}
        for gap in ("net2-5c", "net5c+"):
            rs = [r for r in rows if r["series"] == "KXMLBTOTAL" and r["tier"] == "T0-2h" and r["gap"] == gap
                  and r["book"] == "tight" and r["date"] >= split]
            out["cells"].setdefault(gap, {})[tag] = stat(rs)
    return out


# ------------------------------------------------------------------------------------------------ report
def f4(x):
    return "—" if x is None else f"{x:+.4f}"


def render(r89, r90, r91, until, notes) -> str:
    L = ["# W94.Q — exact-fee recompute (Part A)", "",
         f"Generated by `12_EXPLORATORY/quant_w94/exact_fee_recompute.py` (archive window ≤ {until}). Fee = `quant.money.fee_rate`, taker, "
         "prelive, per contract, unrounded; the old figure is the same code path with `fee_k007`. Interval = game-clustered 95%.", ""]
    L += ["## 89.2 — the 11 CALIBRATION cells", "",
          "| Cell | reported n / net / lo | re-run n | k007 net [lo, hi] | exact net [lo, hi] | status |", "|---|---|---|---|---|---|"]
    for c in r89:
        if not c.get("n"):
            L.append(f"| {' '.join(c['cell'])} | {c['rep_n']} / {c['rep_net']} / {c['rep_lo']} | 0 | — | — | NOT REPRODUCED |")
            continue
        L.append(f"| {' '.join(c['cell'])} {c['side']} | {c['rep_n']} / {c['rep_net']} / {c['rep_lo']} | {c['n']} | "
                 f"{f4(c['old']['net'])} [{f4(c['old']['lo'])}, {f4(c['old']['hi'])}] | "
                 f"{f4(c['exact']['net'])} [{f4(c['exact']['lo'])}, {f4(c['exact']['hi'])}] | {c['change']} |")
    L += ["", "## 90.3 — Part A follow/fade, MLB archive rows (NFL/NBA/NHL: multiplier 1, unchanged)", "",
          "| Hold | n | k007 follow net [lo, hi] | exact follow net [lo, hi] | k007 fade | exact fade |", "|---|---|---|---|---|---|"]
    for hold in ("1h", "3h", "settle"):
        o, e = r90["pooled"].get((hold, "old")), r90["pooled"].get((hold, "exact"))
        if not o:
            continue
        L.append(f"| {hold} | {o['follow']['n']} | {f4(o['follow']['net'])} [{f4(o['follow']['lo'])}, {f4(o['follow']['hi'])}] | "
                 f"{f4(e['follow']['net'])} [{f4(e['follow']['lo'])}, {f4(e['follow']['hi'])}] | {f4(o['fade']['net'])} | {f4(e['fade']['net'])} |")
    pos = defaultdict(lambda: [0, 0, 0])
    for (k, hold), v in r90["grid"].items():
        for side in ("follow", "fade"):
            if v.get("exact") and v["exact"][side]["testable"]:
                pos[(hold, side)][0] += 1
                pos[(hold, side)][1] += int(v["old"][side]["lo"] > 0)
                pos[(hold, side)][2] += int(v["exact"][side]["lo"] > 0)
    L += ["", "Main grid (sport × family × size), testable cells with net_lo > 0:", "", "| Hold | side | testable | k007 | exact |", "|---|---|---|---|---|"]
    for (hold, side), (t, a, b) in sorted(pos.items()):
        L.append(f"| {hold} | {side} | {t} | {a} | {b} |")
    L += ["", "## 91.2 — ladder ride (trigger recomputed under the exact fee; the two HELD_OUT cells fixed, no re-selection)", "",
          f"Triggers: k007 {r91['triggers_old']} → exact {r91['triggers_exact']}. Split date held at the k007 run's ({r91['split']}).", "",
          "| Sample | k007 n / net [lo, hi] | exact n / net [lo, hi] | status |", "|---|---|---|---|"]

    def cs(s):
        return "—" if not s else f"{s['n']} / {f4(s['net'])} [{f4(s['lo'])}, {f4(s['hi'])}]"
    for name, o, e in (("whole sample", r91["whole"]["old"]["all"], r91["whole"]["exact"]["all"]),
                       ("second half (all cells)", r91["whole"]["old"]["second_half"], r91["whole"]["exact"]["second_half"]),
                       ("HELD_OUT KXMLBTOTAL T0-2h net2-5c tight", r91["cells"]["net2-5c"]["old"], r91["cells"]["net2-5c"]["exact"]),
                       ("HELD_OUT KXMLBTOTAL T0-2h net5c+ tight", r91["cells"]["net5c+"]["old"], r91["cells"]["net5c+"]["exact"])):
        L.append(f"| {name} | {cs(o)} | {cs(e)} | {status_change(o['lo'], e['lo']) if o and e else '—'} |")
    L += ["", "## Notes", ""] + [f"- {n}" for n in notes] + ["", "END OF GENERATED RESULTS."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True, help="prebuilt subset directory of prices_*.jsonl")
    ap.add_argument("--settle", required=True)
    ap.add_argument("--until", default="2026-10-27")
    a = ap.parse_args()
    sub = a.archive
    import sys
    import time
    t0 = time.time()
    r89 = run_89(sub, a.settle); print(f"[89 done {time.time()-t0:.0f}s]", file=sys.stderr, flush=True)
    r90 = run_90(sub, a.settle); print(f"[90 done {time.time()-t0:.0f}s]", file=sys.stderr, flush=True)
    r91 = run_91(sub, a.settle); print(f"[91 done {time.time()-t0:.0f}s]", file=sys.stderr, flush=True)
    notes = ["Re-run n differs from the reported n where the archive/settlement window differs from the wave's; the status column compares "
             "k007 vs exact on the SAME re-run rows, so the comparison is like for like even when the re-run does not reproduce the report.",
             "NFL (and NBA/NHL game series) have multiplier 1: exact == k007 (test_w94_q_exact_fee). Only MLB rows move.",
             "90.3 NFL rows and the 89.7 NBA/NHL candles need the 89.7 events/candles files, which are not local; unchanged by construction."]
    md = render(r89, r90, r91, a.until, notes)
    print(md)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""EXP-035 Part 1 correctness gate (D1b). Implements PART 1 of
`05_RESEARCH_EXPERIMENTS/EXP035_BOARD_SURVEY_SPORTS_PREREGISTRATION_2026-10-02.md` as frozen.

  fetch    : back-capture KXMLBTEAMTOTAL markets + hourly candles + quote-level 1-minute windows into the store
  evaluate : read the store only; compute G1..G7; write gate_result.json

Archive and EXP-031/032 outputs are read-only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_store as bs  # noqa: E402
from market_efficiency_survey import calib_gap  # noqa: E402
from execution_cost_surface import parse_ticker_start, tau_bucket  # noqa: E402

SERIES = "KXMLBTEAMTOTAL"
WINDOW_START = "2026-08-01T23:01:11Z"
CUTOFF = "2026-08-03T00:00:00Z"
SAMPLE_SEED, SAMPLE_N = 20261002, 400
REF = {"B": 0.02572, "H": 0.04, "null": 0.00975, "E": -0.02403}


def ts(s: str) -> int:
    return bs.iso_ts(s)


def q(side: dict, field: str):
    """Quote value from either schema (historical: close; live: close_dollars)."""
    v = side.get(field, side.get(field + "_dollars")) if side else None
    return None if v in (None, "") else float(v)


def archive_snaps(archive: str) -> dict:
    """ticker -> [(run_ts, bid, ask)] usable two-sided rows, sorted."""
    out: dict = {}
    for p in sorted(glob.glob(os.path.join(archive, "prices_????-??-??.jsonl"))):
        for line in open(p):
            if SERIES not in line:
                continue
            r = json.loads(line)
            if r.get("series_ticker") != SERIES:
                continue
            b, a = float(r["yes_bid"] or 0), float(r["yes_ask"] or 0)
            if b > 0 and a > 0:
                out.setdefault(r["ticker"], []).append((r["run_ts"], b, a))
    for v in out.values():
        v.sort()
    return out


ALSO_SKIP = os.environ.get("ALSO_SKIP")
SUB = tuple(map(int, os.environ["SUB"].split("/"))) if os.environ.get("SUB") else None


def done_keys(store_dir: str) -> set:
    """(kind,key) already stored in a closed store dir (read-only; no lock)."""
    out = set()
    for f in glob.glob(os.path.join(store_dir, "raw_????-??-??.jsonl")):
        for line in open(f):
            r = json.loads(line)
            out.add((r["kind"], r["key"].split("|")[0] + "|" + (r["key"].split("|")[1] if "|" in r["key"] else "")))
    return out


def fetch(archive: str, store_dir: str, exp031: str, shard=None, skip_dir=None):
    if shard:
        store_dir = os.path.join(store_dir, f"shard_{shard[0]}" + (f"_{SUB[0]}" if SUB else ""))
        os.makedirs(store_dir, exist_ok=True)
    client, store = bs.Client(), bs.Store(store_dir)
    snaps = archive_snaps(archive)
    mk = bs.list_markets(client, store, SERIES, CUTOFF)
    by_t = {m["ticker"]: m for m in mk}
    w0 = ts(WINDOW_START)
    todo = sorted(t for t in snaps if t in by_t)
    if skip_dir:
        dk = done_keys(skip_dir)
        todo_h = [t for t in todo if ("candles", t + "|60") not in dk]
    else:
        todo_h = todo
    if shard:
        todo_h = todo_h[shard[0]::shard[1]]
    if ALSO_SKIP:  # resume of a partially-done shard: applied AFTER slicing so assignments don't shift
        dk2 = done_keys(ALSO_SKIP)
        todo_h = [t for t in todo_h if ("candles", t + "|60") not in dk2]
    if SUB:
        todo_h = todo_h[SUB[0]::SUB[1]]
    print(f"universe markets={len(mk)} archive tickers={len(snaps)} on both={len(todo)}", flush=True)
    for i, t in enumerate(todo_h):
        m = by_t[t]
        bs.candles(client, store, SERIES, m, max(ts(m["open_time"]), w0), ts(m["close_time"]) + 3600, 60, ts(CUTOFF))
        if i % 500 == 0:
            print(i, client.stats(), flush=True)
    rng = np.random.default_rng(SAMPLE_SEED)
    pick = sorted(rng.choice(sorted(todo), size=min(SAMPLE_N, len(todo)), replace=False))
    pick = pick[shard[0]::shard[1]] if shard else pick
    if SUB:
        pick = pick[SUB[0]::SUB[1]]
    for t in pick:
        s = snaps[t]; n = len(s)
        for pos in (0, 0.25, 0.5, 0.75, 1.0):
            run = s[min(n - 1, int(round(pos * (n - 1))))][0]
            tt = ts(run)
            bs.candles(client, store, SERIES, by_t[t], tt - 120, tt + 120, 1, ts(CUTOFF))
    print("done", client.stats(), "store written", store.written, "skipped", store.skipped, flush=True)
    json.dump({**client.stats(), "written": store.written, "skipped": store.skipped, "universe": len(mk),
               "both": len(todo)}, open(os.path.join(store_dir, "fetch_stats.json"), "w"))


def evaluate(archive: str, store_dir: str, exp031: str, exp032: str, out: str):
    dirs = [store_dir] + sorted(glob.glob(os.path.join(store_dir, "shard_*")))
    stores = [bs.Store(d) for d in dirs]
    snaps = archive_snaps(archive)
    settle = {}
    for f in glob.glob(os.path.join(exp031, "settlements", "*.json")):
        settle.update(json.load(open(f)))
    s_tickers = [t for t in snaps if t in settle and settle[t].get("result") in ("yes", "no")]
    hourly, minute, markets = {}, {}, set()
    for r in (r for s_ in stores for r in s_.rows()):
        if r["kind"] == "markets_page":
            markets.update(m["ticker"] for m in r["payload"].get("markets") or [])
        elif r["kind"] == "candles":
            t, per, st_, en_ = r["key"].split("|")
            cs = r["payload"].get("candlesticks") or []
            (hourly if per == "60" else minute.setdefault(t, {}))[(t if per == "60" else (int(st_), int(en_)))] = cs
    hr = {t: cs for t, cs in hourly.items()}
    # G1
    cov = sum(t in markets for t in s_tickers) / len(s_tickers)
    def usable(c):
        b, a = q(c.get("yes_bid"), "close"), q(c.get("yes_ask"), "close")
        return (b or 0) > 0 and (a or 0) > 0
    both = [t for t in snaps if t in hr]
    cov2 = sum(any(usable(c) for c in hr[t]) for t in both) / len(both)
    G1 = {"ticker_coverage": cov, "usable_candle_coverage": cov2, "passed": bool(cov >= .98 and cov2 >= .98)}
    # G2/G3
    n = ok2 = ok3 = 0
    for t, wins in minute.items():
        for (st_, en_), cs in wins.items():
            tt = (st_ + en_) // 2
            run = next(r for r in snaps[t] if abs(ts(r[0]) - tt) <= 1)
            cs = sorted(cs, key=lambda c: c["end_period_ts"])
            idx = next((i for i, c in enumerate(cs) if c["end_period_ts"] >= tt), None)
            if idx is None:
                n += 1; continue
            c = cs[idx]; nb = cs[max(0, idx - 1): idx + 2]
            n += 1
            cb, ca = q(c.get("yes_bid"), "close"), q(c.get("yes_ask"), "close")
            if cb is not None and ca is not None and abs(run[1] - cb) <= .01 + 1e-9 and abs(run[2] - ca) <= .01 + 1e-9:
                ok2 += 1
            lo_b = min(q(x["yes_bid"], "low") for x in nb if q(x.get("yes_bid"), "low") is not None) if nb else None
            hi_b = max(q(x["yes_bid"], "high") for x in nb if q(x.get("yes_bid"), "high") is not None) if nb else None
            lo_a = min(q(x["yes_ask"], "low") for x in nb if q(x.get("yes_ask"), "low") is not None) if nb else None
            hi_a = max(q(x["yes_ask"], "high") for x in nb if q(x.get("yes_ask"), "high") is not None) if nb else None
            if None not in (lo_b, hi_b, lo_a, hi_a) and lo_b - 1e-9 <= run[1] <= hi_b + 1e-9 and lo_a - 1e-9 <= run[2] <= hi_a + 1e-9:
                ok3 += 1
    G2 = {"n": n, "share": ok2 / n if n else None, "passed": bool(n and ok2 / n >= .80)}
    G3 = {"n": n, "share": ok3 / n if n else None, "passed": bool(n and ok3 / n >= .95)}
    # G4-G6: candle first-seen, earliest usable candle with end_period_ts >= window start
    w0 = ts(WINDOW_START); p, y, h = [], [], []
    for t in s_tickers:
        cs = sorted(hr.get(t, []), key=lambda c: c["end_period_ts"])
        c = next((c for c in cs if c["end_period_ts"] >= w0 and usable(c)), None)
        if c:
            b, a = q(c["yes_bid"], "close"), q(c["yes_ask"], "close")
            p.append((a + b) / 2); h.append((a - b) / 2); y.append(1.0 if settle[t]["result"] == "yes" else 0.0)
    B = calib_gap(np.array(p), np.array(y))[0]; H = float(np.median(h)); E = B - REF["null"] - H
    G4 = {"B_candle": B, "B_ref": REF["B"], "n": len(p), "passed": bool(abs(B - REF["B"]) <= .003)}
    G5 = {"H_candle": H, "H_ref": REF["H"], "passed": bool(abs(H - REF["H"]) <= .005)}
    G6 = {"E_candle": E, "E_ref": REF["E"], "passed": bool(np.sign(E) == np.sign(REF["E"]))}
    # G7: EXP-032 measured tau buckets, start clock from ticker
    ref_tau = json.load(open(os.path.join(exp032, "results.json")))["families"][SERIES]["surface"]["tau"]
    import pandas as pd
    rows = []
    for t in snaps:
        st_t = parse_ticker_start(t)[0]
        if st_t is None:
            continue
        for c in hr.get(t, []):
            if usable(c):
                b, a = q(c["yes_bid"], "close"), q(c["yes_ask"], "close")
                rows.append(((st_t.timestamp() - c["end_period_ts"]) / 3600.0, (a - b) / 2))
    df = pd.DataFrame(rows, columns=["tau", "hs"]); df["tb"] = tau_bucket(df["tau"])
    g7 = {}
    for lab, cell in ref_tau.items():
        if cell.get("measured"):
            sub = df[df["tb"].astype(str) == lab]["hs"]
            g7[lab] = {"ref": cell["hs_med"], "candle": float(sub.median()) if len(sub) else None, "n": int(len(sub))}
            g7[lab]["ok"] = bool(len(sub) and abs(g7[lab]["candle"] - cell["hs_med"]) <= .005)
    G7 = {"buckets": g7, "passed": bool(g7 and all(v["ok"] for v in g7.values()))}
    res = {"G1": G1, "G2": G2, "G3": G3, "G4": G4, "G5": G5, "G6": G6, "G7": G7}
    res["ALL_PASSED"] = bool(all(v["passed"] for v in res.values() if isinstance(v, dict)))
    json.dump(res, open(out, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["fetch", "evaluate"])
    ap.add_argument("--archive", required=True); ap.add_argument("--store", default=str(bs.STORE_DEFAULT))
    ap.add_argument("--exp031", default="exp_output/EXP-031-MKT-EFF-SURVEY")
    ap.add_argument("--exp032", default="exp_output/EXP-032-EXECUTION-COST-SURFACE")
    ap.add_argument("--shard", default=None); ap.add_argument("--skip-dir", default=None)
    ap.add_argument("--out", default="exp_output/EXP-035-BOARD-SURVEY-SPORTS/gate_result.json")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fetch(a.archive, a.store, a.exp031, tuple(map(int, a.shard.split("/"))) if a.shard else None, a.skip_dir) if a.cmd == "fetch" else evaluate(a.archive, a.store, a.exp031, a.exp032, a.out)

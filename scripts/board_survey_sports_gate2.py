#!/usr/bin/env python3
"""EXP-035 Gate 2 (T-605) -- implements 05_RESEARCH_EXPERIMENTS/EXP035_GATE2_PREREGISTRATION_2026-10-02.md exactly.
A NEW test; Part 1's verdict is untouched. Changes from Part 1: (1) prevailing-quote matching (close of the latest candle at
or before t; 1-minute over [t-3600, t+120], hourly fallback), (2) B/H at the archive's own first-seen t0 on the subset that
has a prevailing hourly candle, referenced to the archive on that same subset. Thresholds identical to Part 1.
Usage: fetch|evaluate --series S --archive A --store DIR [--seed N] [--hourly-from DIR ...] [--markets-from DIR]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_gate as g  # noqa: E402
import board_survey_sports_store as bs  # noqa: E402
from market_efficiency_survey import calib_gap  # noqa: E402
from execution_cost_surface import parse_ticker_start, tau_bucket  # noqa: E402

NULL_REF = {"KXMLBTOTAL": 0.01038, "KXMLBTEAMTOTAL": 0.00975}   # EXP-031 family null (B - H - E of the published row)
LOOKBACK, LOOKAHEAD = 3600, 120
POSITIONS = (0, 0.25, 0.5, 0.75, 1.0)


def usable(c):
    b, a = g.q(c.get("yes_bid"), "close"), g.q(c.get("yes_ask"), "close")
    return (b or 0) > 0 and (a or 0) > 0


def prevailing(minute_cs: list, hourly_cs: list, tt: int):
    """Close of the latest candle at or before tt: 1-minute first, else hourly. Returns (candle, source, sorted_minute, idx)."""
    ms = sorted(minute_cs, key=lambda c: c["end_period_ts"])
    idx = max((i for i, c in enumerate(ms) if c["end_period_ts"] <= tt), default=None)
    if idx is not None:
        return ms[idx], "minute", ms, idx
    hs = [c for c in hourly_cs if c["end_period_ts"] <= tt]
    if hs:
        return max(hs, key=lambda c: c["end_period_ts"]), "hourly", [], None
    return None, "unmatched", ms, None


def g3_contains(run, nb):
    def rng(side, f):
        v = [g.q(x.get(side), f) for x in nb]
        v = [z for z in v if z is not None]
        return v
    lb, hb, la, ha = rng("yes_bid", "low"), rng("yes_bid", "high"), rng("yes_ask", "low"), rng("yes_ask", "high")
    if not (lb and hb and la and ha):
        return False
    return min(lb) - 1e-9 <= run[1] <= max(hb) + 1e-9 and min(la) - 1e-9 <= run[2] <= max(ha) + 1e-9


def agrees(run, c):
    cb, ca = g.q(c.get("yes_bid"), "close"), g.q(c.get("yes_ask"), "close")
    return cb is not None and ca is not None and abs(run[1] - cb) <= .01 + 1e-9 and abs(run[2] - ca) <= .01 + 1e-9


def existing(store) -> set:
    return {(r["kind"], r["key"]) for r in store.rows()}


def fetch(a):
    g.SERIES = a.series
    client, store = bs.Client(), bs.Store(a.store)
    snaps = g.archive_snaps(a.archive)
    if a.markets_from:
        mk = [m for d in a.markets_from for r in bs.Store(d).rows("markets_page") for m in (r["payload"].get("markets") or [])]
    else:
        mk = bs.list_markets(client, store, a.series, g.CUTOFF)
    by_t = {m["ticker"]: m for m in mk}
    have = existing(store)
    w0 = g.ts(g.WINDOW_START)
    todo = sorted(t for t in snaps if t in by_t)
    print(f"series={a.series} markets={len(mk)} archive tickers={len(snaps)} on both={len(todo)}", flush=True)
    if not a.hourly_from:
        for i, t in enumerate(todo):
            m = by_t[t]; s, e = max(g.ts(m["open_time"]), w0), g.ts(m["close_time"]) + 3600
            if ("candles", f"{t}|60|{s}|{e}") not in have:
                bs.candles(client, store, a.series, m, s, e, 60, g.ts(g.CUTOFF))
            if i % 500 == 0:
                print("hourly", i, client.stats(), flush=True)
    rng = np.random.default_rng(a.seed)
    pick = sorted(rng.choice(todo, size=min(g.SAMPLE_N, len(todo)), replace=False))
    json.dump(list(map(str, pick)), open(os.path.join(a.store, "sample_tickers.json"), "w"))
    for j, t in enumerate(pick):
        s_ = snaps[t]; n = len(s_)
        for pos in POSITIONS:
            tt = g.ts(s_[min(n - 1, int(round(pos * (n - 1))))][0])
            k = f"{t}|1|{tt - LOOKBACK}|{tt + LOOKAHEAD}"
            if ("candles", k) not in have:
                bs.candles(client, store, a.series, by_t[t], tt - LOOKBACK, tt + LOOKAHEAD, 1, g.ts(g.CUTOFF))
        if j % 50 == 0:
            print("minute", j, client.stats(), flush=True)
    print("done", client.stats(), "written", store.written, "skipped", store.skipped, flush=True)
    json.dump({**client.stats(), "written": store.written, "skipped": store.skipped}, open(os.path.join(a.store, "fetch_stats.json"), "w"))


def evaluate(a):
    g.SERIES = a.series
    snaps = g.archive_snaps(a.archive)
    settle = {}
    for f in glob.glob(os.path.join(a.exp031, "settlements", "*.json")):
        settle.update(json.load(open(f)))
    s_tickers = g.binary_settled(snaps, settle)
    dirs = [a.store] + list(a.hourly_from or [])
    hourly, minute, markets = {}, {}, set()
    for d in dirs:
        for sd in [d] + sorted(glob.glob(os.path.join(d, "shard_*"))):
            for r in bs.Store(sd).rows():
                if r["kind"] == "markets_page":
                    markets.update(m["ticker"] for m in r["payload"].get("markets") or [])
                elif r["kind"] == "candles":
                    t, per, s0, e0 = r["key"].split("|")
                    cs = r["payload"].get("candlesticks") or []
                    if per == "60":
                        hourly[t] = cs
                    elif int(e0) - int(s0) == LOOKBACK + LOOKAHEAD:
                        minute.setdefault(t, {})[int(e0) - LOOKAHEAD] = cs
    for d in (a.markets_from or []):
        for r in bs.Store(d).rows("markets_page"):
            markets.update(m["ticker"] for m in r["payload"].get("markets") or [])
    # G1
    cov = sum(t in markets for t in s_tickers) / len(s_tickers)
    both = [t for t in snaps if t in hourly]
    cov2 = sum(any(usable(c) for c in hourly[t]) for t in both) / len(both)
    G1 = {"ticker_coverage": cov, "usable_candle_coverage": cov2, "passed": bool(cov >= .98 and cov2 >= .98)}
    # G2/G3
    n = ok2 = ok3 = 0; src = {"minute": 0, "hourly": 0, "unmatched": 0}
    for t, wins in minute.items():
        for tt, cs in wins.items():
            run = next(r for r in snaps[t] if abs(g.ts(r[0]) - tt) <= 1)
            c, how, ms, idx = prevailing(cs, hourly.get(t, []), tt)
            n += 1; src[how] += 1
            if c is None:
                continue
            ok2 += agrees(run, c)
            nb = ms[max(0, idx - 1): idx + 2] if how == "minute" else [c]
            ok3 += g3_contains(run, nb)
    G2 = {"n": n, "share": ok2 / n if n else None, "passed": bool(n and ok2 / n >= .80), "source_counts": src}
    G3 = {"n": n, "share": ok3 / n if n else None, "passed": bool(n and ok3 / n >= .95)}
    # G4-G6 at archive first-seen t0, subset with prevailing usable hourly; reference = archive on same subset
    pc, pa, yc, hc, ha_, excluded = [], [], [], [], [], 0
    for t in s_tickers:
        r0 = snaps[t][0]; t0 = g.ts(r0[0])
        hs = sorted((c for c in hourly.get(t, []) if c["end_period_ts"] <= t0), key=lambda c: c["end_period_ts"])
        c = hs[-1] if hs else None
        if c is None or not usable(c):
            excluded += 1; continue
        b, a_ = g.q(c["yes_bid"], "close"), g.q(c["yes_ask"], "close")
        pc.append((a_ + b) / 2); hc.append((a_ - b) / 2)
        pa.append((r0[1] + r0[2]) / 2); ha_.append((r0[2] - r0[1]) / 2)
        yc.append(1.0 if settle[t]["result"] == "yes" else 0.0)
    null = NULL_REF[a.series]; y = np.array(yc)
    Bc, Hc = calib_gap(np.array(pc), y)[0], float(np.median(hc))
    Br, Hr = calib_gap(np.array(pa), y)[0], float(np.median(ha_))
    Ec, Er = Bc - null - Hc, Br - null - Hr
    G4 = {"B_candle": Bc, "B_ref_archive_same_subset": Br, "n": len(pc), "excluded_no_prevailing_hourly": excluded,
          "passed": bool(abs(Bc - Br) <= .003)}
    G5 = {"H_candle": Hc, "H_ref_archive_same_subset": Hr, "passed": bool(abs(Hc - Hr) <= .005)}
    G6 = {"E_candle": Ec, "E_ref_archive_same_subset": Er, "null": null, "passed": bool(np.sign(Ec) == np.sign(Er))}
    # G7 identical construction to Part 1
    import pandas as pd
    ref_tau = json.load(open(os.path.join(a.exp032, "results.json")))["families"][a.series]["surface"]["tau"]
    rows = []
    for t in snaps:
        st_t = parse_ticker_start(t)[0]
        if st_t is None:
            continue
        for c in hourly.get(t, []):
            if usable(c):
                b, a_ = g.q(c["yes_bid"], "close"), g.q(c["yes_ask"], "close")
                rows.append(((st_t.timestamp() - c["end_period_ts"]) / 3600.0, (a_ - b) / 2))
    df = pd.DataFrame(rows, columns=["tau", "hs"]); df["tb"] = tau_bucket(df["tau"])
    g7 = {}
    for lab, cell in ref_tau.items():
        if cell.get("measured"):
            sub = df[df["tb"].astype(str) == lab]["hs"]
            g7[lab] = {"ref": cell["hs_med"], "candle": float(sub.median()) if len(sub) else None, "n": int(len(sub))}
            g7[lab]["ok"] = bool(len(sub) and abs(g7[lab]["candle"] - cell["hs_med"]) <= .005)
    G7 = {"buckets": g7, "passed": bool(g7 and all(v["ok"] for v in g7.values()))}
    res = {"series": a.series, "G1": G1, "G2": G2, "G3": G3, "G4": G4, "G5": G5, "G6": G6, "G7": G7}
    res["ALL_PASSED"] = bool(all(v["passed"] for v in res.values() if isinstance(v, dict)))
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["fetch", "evaluate"])
    ap.add_argument("--series", required=True); ap.add_argument("--archive", required=True); ap.add_argument("--store", required=True)
    ap.add_argument("--seed", type=int, default=35035)
    ap.add_argument("--hourly-from", nargs="*"); ap.add_argument("--markets-from", nargs="*")
    ap.add_argument("--exp031", default="exp_output/EXP-031-MKT-EFF-SURVEY")
    ap.add_argument("--exp032", default="exp_output/EXP-032-EXECUTION-COST-SURFACE")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    a.out = a.out or f"exp_output/EXP-035-BOARD-SURVEY-SPORTS/gate2_{a.series}.json"
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    os.makedirs(a.store, exist_ok=True)
    fetch(a) if a.cmd == "fetch" else evaluate(a)

#!/usr/bin/env python3
"""W99.2 Part C: READ-ONLY. Prints one row per settled NFL game-total game (first row per market, per band) as TSV:
game_key, band, strike, p_yes, mid, y, p_clim, kickoff, plus roof/temp/wind/week from the public nflverse schedule
when it can be fetched (blank otherwise). Never scores, never writes, never touches a ledger or a model.
Descriptive input for results_W99_2.md only (the verdict was already released in W98.2)."""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = ["band", "game_key", "market_ticker", "strike", "p_yes", "mid", "yes_ask", "y", "p_clim", "start_time_utc",
        "week", "roof", "temp", "wind"]


def load_rows(d: str, bands=("T1_MULTI_DAY", "T2_SAME_DAY", "T3_PREGAME")):
    out = []
    for path in sorted(glob.glob(os.path.join(d, "NFL_NFL_GAME_TOTAL_*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("y") is None or not r.get("game_key"):
                    continue
                if r.get("excluded_from_judged_n") or r.get("season_phase") == "preseason":
                    continue
                out.append(r)
    seen, firsts = set(), []
    for r in sorted(out, key=lambda r: r["ts_utc"]):
        k = (r["market_ticker"], r["band"])
        if k not in seen:
            seen.add(k)
            firsts.append(r)
    return firsts


BINS = (("lo", None, 38.5), ("m1", 38.5, 44.5), ("m2", 44.5, 50.5), ("hi", 50.5, None))


def _strike(r):
    import re
    m = re.search(r"-(\d+(?:\.\d+)?)$", r["market_ticker"])
    return float(m.group(1)) if m else None


def median_total(pairs):
    """Linear-interpolated strike where P(over) crosses 0.5, from [(strike, p)]; None when the ladder never crosses."""
    pts = sorted(pairs)
    for (k0, p0), (k1, p1) in zip(pts, pts[1:]):
        if p0 >= 0.5 > p1 and p0 != p1:
            return round(k0 + (k1 - k0) * (p0 - 0.5) / (p0 - p1), 2)
    return None


def aggregate(rows):
    """W100.2 Part B: one compact row per (game, band): rung count, summed Brier model/market on the market mid,
    mean(p_yes - mid), interpolated median totals (model, market), and the same sums in four strike bins.
    Descriptive only; the verdict was released in W98.2."""
    g = {}
    for r in rows:
        k, mid = _strike(r), r.get("mid")
        if k is None or mid is None:
            continue
        a = g.setdefault((r["game_key"], r["band"]), {"w": r.get("week"), "roof": r.get("roof"), "t": r.get("temp"),
                                                      "wd": r.get("wind"), "pm": [], "mm": [], "bm": [], "bk": [], "d": [],
                                                      "bin": {b[0]: [0, 0.0, 0.0] for b in BINS}})
        y, p = float(r["y"]), float(r["p_yes"])
        bm, bk = (p - y) ** 2, (float(mid) - y) ** 2
        a["pm"].append((k, p)); a["mm"].append((k, float(mid))); a["bm"].append(bm); a["bk"].append(bk); a["d"].append(p - float(mid))
        for name, lo, hi in BINS:
            if (lo is None or k > lo) and (hi is None or k <= hi):
                b = a["bin"][name]; b[0] += 1; b[1] += bm; b[2] += bk
    out = []
    for (gk, band), a in sorted(g.items()):
        n = len(a["bm"])
        out.append({"g": gk, "band": band, "n": n, "w": a["w"], "roof": a["roof"], "t": a["t"], "wd": a["wd"],
                    "bm": round(sum(a["bm"]), 4), "bk": round(sum(a["bk"]), 4), "dp": round(sum(a["d"]) / n, 4),
                    "mt": median_total(a["pm"]), "kt": median_total(a["mm"]),
                    "bins": {k: [v[0], round(v[1], 4), round(v[2], 4)] for k, v in a["bin"].items()}})
    return out


def schedule_lookup():
    try:
        import pandas as pd
        df = pd.read_csv("https://github.com/nflverse/nfldata/raw/master/data/games.csv")
    except Exception as e:  # network or pandas missing: stay descriptive, leave blanks
        print(f"# schedule unavailable: {e}", file=sys.stderr)
        return {}
    d = {}
    for r in df.itertuples():
        d[(str(r.gameday), r.away_team, r.home_team)] = (r.week, r.roof, r.temp, r.wind)
    return d


def lookup_weather(sched, game_key, blank=None):
    """(week, roof, temp, wind). game_key dates can be UTC, so a late kickoff sits one day after the schedule's gameday:
    try the key's date, then the day before (the W99.2 week-8 blanks)."""
    from datetime import date as _d, timedelta
    try:
        date, rest = game_key.split(":")
        away, home = rest.split("@")
        for dd in (date, (_d.fromisoformat(date) - timedelta(days=1)).isoformat()):
            if (dd, away, home) in sched:
                return sched[(dd, away, home)]
    except ValueError:
        pass
    return (blank, blank, blank, blank)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agg", action="store_true", help="per (game, band) aggregates as compact JSON lines (fits the 60KB cap)")
    ap.add_argument("--dir", default=os.path.join(REPO, "exp_output", "PREGAME_SHADOW", "settled"))
    a = ap.parse_args(argv)
    sched = schedule_lookup()
    rows = load_rows(a.dir)
    if a.agg:
        for r in rows:
            r["week"], r["roof"], r["temp"], r["wind"] = lookup_weather(sched, r["game_key"])
        for o in aggregate(rows):
            print(json.dumps(o, separators=(",", ":")))
        return 0
    print("\t".join(COLS))
    for r in rows:
        wk = lookup_weather(sched, r["game_key"], blank="")
        strike = r["market_ticker"].rsplit("-", 1)[-1]
        vals = [r["band"], r["game_key"], r["market_ticker"], strike, r["p_yes"], r.get("mid"), r.get("yes_ask"),
                r["y"], r.get("p_clim"), r.get("start_time_utc"), *wk]
        print("\t".join("" if v is None else str(v) for v in vals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

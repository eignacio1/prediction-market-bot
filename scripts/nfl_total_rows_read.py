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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(REPO, "exp_output", "PREGAME_SHADOW", "settled"))
    a = ap.parse_args(argv)
    sched = schedule_lookup()
    print("\t".join(COLS))
    for r in load_rows(a.dir):
        try:
            date, rest = r["game_key"].split(":")
            away, home = rest.split("@")
            wk = sched.get((date, away, home)) or ("", "", "", "")
        except ValueError:
            wk = ("", "", "", "")
        strike = r["market_ticker"].rsplit("-", 1)[-1]
        vals = [r["band"], r["game_key"], r["market_ticker"], strike, r["p_yes"], r.get("mid"), r.get("yes_ask"),
                r["y"], r.get("p_clim"), r.get("start_time_utc"), *wk]
        print("\t".join("" if v is None else str(v) for v in vals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

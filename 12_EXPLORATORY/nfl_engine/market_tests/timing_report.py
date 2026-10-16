"""EXPLORATORY -- W77.2b: the Friday-report window, from the HOURLY KXNFLGAME candles (period_min=60), which span market
open (~2 weeks pre-game) -> close, unlike the 1-min set (48h before settlement only, so REPORT n was 0 in W77.2).
Same estimator as timing.py (slope of dMid per F8 margin point, game-bootstrap CI). Windows (ET): REPORT = Fri 12:00 ->
Sat 12:00 (final report lands Fri ~16:00); PRE = Thu 12:00 -> Fri 12:00 (placebo before the report);
POST = Sat 12:00 -> Sun 09:00 (placebo after). Hourly resolution: a mid is the last hourly candle close <= t (tol 2h).
Usage: python3 timing_report.py <terms.json> <schedule.parquet> <team_stats.parquet> <candles.jsonl> <out>"""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta
import numpy as np, pandas as pd
import timing as T
from timing import W, ET, safe_out, slope


def main(terms, sched_p, stats_p, candles, out):
    sched, stats = pd.read_parquet(sched_p), pd.read_parquet(stats_p)
    df = W.build(sched, sched, stats); g25 = df[df.season == 2025]
    t = pd.read_json(terms).set_index("game_id"); teams = set(df.home) | set(df.away)
    rows, nsets, ngames = [], 0, 0
    for l in open(candles):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26JAN' not in l:
            continue
        r = json.loads(l)
        if r.get("period_min") != 60 or not r.get("candles"):
            continue
        nsets += 1
        s_ = W.split_ticker(r["ticker"], teams)
        if not s_ or s_[2] != s_[1]:
            continue
        g = g25[(g25.home == s_[1]) & (g25.away == s_[0])]
        if len(g) != 1:
            continue
        g = g.iloc[0]; ngames += 1
        ko_dt = datetime(*map(int, g.gameday.split("-")), *map(int, g.gametime.split(":")[:2]), tzinfo=ET)
        if ko_dt.weekday() != 6 or g.game_id not in t.index:
            continue
        f8h, f8a = t.loc[g.game_id, "f8_h"], t.loc[g.game_id, "f8_a"]
        if pd.isna(f8h) or pd.isna(f8a):
            continue
        cs = r["candles"]
        at = lambda days, hr: T.mid_at(cs, datetime(ko_dt.year, ko_dt.month, ko_dt.day, hr, tzinfo=ET).timestamp()
                                       - days * 86400, tol=7200)
        rows.append(dict(d8=float(f8h - f8a), thu=at(3, 12), fri=at(2, 12), sat=at(1, 12), sun=at(0, 9)))
    d = pd.DataFrame(rows)
    res = {"hourly_candle_sets": nsets, "home_side_games_linked": ngames, "sunday_f8_games": int(len(d))}
    for name, a, b in (("PRE_placebo", "thu", "fri"), ("REPORT", "fri", "sat"), ("POST_placebo", "sat", "sun")):
        m = d.dropna(subset=[a, b])
        res[name] = slope(m.d8.to_numpy(), (m[b] - m[a]).to_numpy()) if len(m) >= 20 else {"n": int(len(m)), "note": "too few"}
    res["d8_sd"] = float(d.d8.std()) if len(d) else None
    safe_out(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])

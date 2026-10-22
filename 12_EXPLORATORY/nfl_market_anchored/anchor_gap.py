"""EXPLORATORY -- W85.1 Part A.1: how far is a T1/T2/T3-horizon Kalshi KXNFLGAME home mid from the nflverse close?
Candles: 1-minute sets for the 2025 season to 2026-01 (no 2026 candles exist; spreads/totals/team totals were never fetched).
Horizons (kickoff-relative, ET kickoff from the schedule): T1 = ko-36h, T2 = ko-24h, T3 = ko-6h, CLOSE = ko-30min.
For each horizon: gap = mid - de-vigged nflverse close (home win prob); Brier of mid vs outcome; slope of the ko-30min move on F8 d8.
Usage: anchor_gap.py terms.json schedules.parquet candles.jsonl out_json"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from _fence import safe_out  # noqa: E402
from anchored_price import ml_prob  # noqa: E402
ET = ZoneInfo("America/New_York"); H = {"T1": 36, "T2": 24, "T3": 6, "CLOSE": 0.5}


def mid_at(cs, t, tol=3600):
    c = [x for x in cs if x["t"] <= t and x["ask"]["close"] is not None and x["bid"]["close"] is not None]
    if not c or t - c[-1]["t"] > tol: return None
    return (c[-1]["ask"]["close"] + c[-1]["bid"]["close"]) / 2


def main(terms_p, sched_p, candles_p, out):
    s = pd.read_parquet(sched_p); s = s[(s.season == 2025)].copy()
    s["p0"] = ml_prob(s.home_moneyline.to_numpy(float), s.away_moneyline.to_numpy(float))
    t = pd.DataFrame(json.load(open(terms_p))).set_index("game_id")
    key = {(r.gameday.replace("-", "")[2:], r.away_team + r.home_team): r for r in s.itertuples()}
    mon = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
    rows, sets = [], 0
    for l in open(candles_p):
        r = json.loads(l)
        if r.get("period_min") != 1 or not r.get("candles") or not r["ticker"].startswith("KXNFLGAME-"): continue
        sets += 1; _, ev, side = r["ticker"].split("-"); yy, mm, dd, code = ev[:2], ev[2:5], ev[5:7], ev[7:]
        g = key.get((f"{yy}{mon[mm]:02d}{dd}", code))
        if g is None or side != g.home_team: continue   # one home-side ticker per game
        ko = datetime(*map(int, g.gameday.split("-")), *map(int, g.gametime.split(":")[:2]), tzinfo=ET).timestamp()
        row = dict(game_id=g.game_id, p0=g.p0, y=float(g.home_score > g.away_score), d8=np.nan)
        if g.game_id in t.index and pd.notna(t.loc[g.game_id, "f8_h"]) and pd.notna(t.loc[g.game_id, "f8_a"]):
            row["d8"] = float(t.loc[g.game_id, "f8_h"] - t.loc[g.game_id, "f8_a"])
        for k, h in H.items(): row[k] = mid_at(r["candles"], ko - h * 3600)
        rows.append(row)
    d = pd.DataFrame(rows); res = {"candle_sets_1min": sets, "home_side_games_linked": int(len(d))}
    rng = np.random.default_rng(20261022)
    for k in H:
        m = d.dropna(subset=[k]); gap = (m[k] - m.p0).to_numpy(); n = len(m)
        bs = [rng.integers(0, n, n) for _ in range(2000)]
        bb = [(((m[k].to_numpy() - m.y.to_numpy()) ** 2)[i].mean() - ((m.p0.to_numpy() - m.y.to_numpy()) ** 2)[i].mean()) for i in bs]
        res[k] = dict(n=n, gap_mean=float(gap.mean()), gap_sd=float(gap.std()), gap_abs_mean=float(np.abs(gap).mean()),
                      brier_mid=float(((m[k] - m.y) ** 2).mean()), brier_close=float(((m.p0 - m.y) ** 2).mean()),
                      dBrier_mid_minus_close=float(np.mean(bb)), dB_lo=float(np.quantile(bb, .025)), dB_hi=float(np.quantile(bb, .975)))
    m = d.dropna(subset=["T1", "CLOSE", "d8"])
    if len(m) >= 20:   # does the T1 -> close drift load on the F8 term (the information an adjustment is trying to add)?
        x = m.d8.to_numpy(); y = (m.CLOSE - m.T1).to_numpy(); X = np.c_[np.ones(len(x)), x]; b = np.linalg.lstsq(X, y, rcond=None)[0][1]
        bs = [np.linalg.lstsq(X[i], y[i], rcond=None)[0][1] for i in (rng.integers(0, len(x), len(x)) for _ in range(2000))]
        res["T1_to_close_slope_on_d8"] = dict(n=int(len(x)), slope=float(b), lo=float(np.quantile(bs, .025)), hi=float(np.quantile(bs, .975)))
    safe_out(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])

"""EXPLORATORY -- W77.2 Part B.3: does the Kalshi KXNFLGAME home-ML mid move in the F8 term's direction after the
information becomes public? Sunday games only (F8 populated), 2025 games with 1-min candles (no 2026 candles exist
in the archive). Windows (ET): REPORT = Fri 12:00 -> Sat 12:00 (final injury report lands Fri ~16:00);
INACTIVES = ko-150min -> ko-30min; PLACEBO = Sat 12:00 -> ko-150min (no scheduled release).
Slope = dMid(prob) per F8 margin point (d8 = f8_h - f8_a), game-bootstrap CI. Plan: market_tests/PLAN.md."""
from __future__ import annotations
import importlib.util, json, sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
NE = HERE.parent
sys.path.insert(0, str(NE)); sys.path.insert(0, str(NE.parent)); sys.path.insert(0, str(NE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
sp = importlib.util.spec_from_file_location("study_stage3", NE / "study_stage3.py")
S3 = importlib.util.module_from_spec(sp); sys.modules["study_stage3"] = S3; sp.loader.exec_module(S3)
W = S3.W
ET = ZoneInfo("America/New_York")


def mid_at(cs, t, tol=3600):
    c = [x for x in cs if x["t"] <= t and x["ask"]["close"] is not None and x["bid"]["close"] is not None]
    if not c or t - c[-1]["t"] > tol:
        return None
    return (c[-1]["ask"]["close"] + c[-1]["bid"]["close"]) / 2


def slope(d8, dm, B=2000, seed=20261014):
    X = np.column_stack([np.ones(len(d8)), d8]); b = np.linalg.lstsq(X, dm, rcond=None)[0][1]
    rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        i = rng.integers(0, len(d8), len(d8)); bs.append(np.linalg.lstsq(X[i], dm[i], rcond=None)[0][1])
    return dict(n=int(len(d8)), slope=float(b), lo=float(np.quantile(bs, .025)), hi=float(np.quantile(bs, .975)))


def main(terms, sched_p, stats_p, candles, out):
    sched, stats = pd.read_parquet(sched_p), pd.read_parquet(stats_p)
    df = W.build(sched, sched, stats); g25 = df[df.season == 2025]
    t = pd.read_json(terms).set_index("game_id")
    teams = set(df.home) | set(df.away)
    rows, nsets, ngames = [], 0, 0
    for l in open(candles):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26JAN' not in l:
            continue
        r = json.loads(l)
        if r.get("period_min") != 1 or not r.get("candles"):
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
        ko = ko_dt.timestamp(); cs = r["candles"]
        noon = lambda days: (datetime(ko_dt.year, ko_dt.month, ko_dt.day, 12, tzinfo=ET) - timedelta(days=days)).timestamp()
        pts = dict(fri=mid_at(cs, noon(2)), sat=mid_at(cs, noon(1)), i0=mid_at(cs, ko - 9000), i1=mid_at(cs, ko - 1800))
        rows.append(dict(d8=float(f8h - f8a), **pts))
    d = pd.DataFrame(rows)
    res = {"candle_sets_2025_26jan": nsets, "home_side_games_linked": ngames, "sunday_f8_games_with_candles": int(len(d))}
    for name, a, b in (("REPORT", "fri", "sat"), ("INACTIVES", "i0", "i1"), ("PLACEBO", "sat", "i0")):
        m = d.dropna(subset=[a, b])
        res[name] = slope(m.d8.to_numpy(), (m[b] - m[a]).to_numpy()) if len(m) >= 20 else {"n": int(len(m)), "note": "too few"}
    res["d8_sd"] = float(d.d8.std()) if len(d) else None
    safe_out(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])

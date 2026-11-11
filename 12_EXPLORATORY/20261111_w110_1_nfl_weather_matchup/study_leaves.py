"""EXPLORATORY (W110.1 Part C, per operator addendum 2026-11-10 21:35 PT): factors as SPLITS in the multi-arm tree.
Per leaf (filter condition x market state): net units per bet after costs (the book's own price) for each arm at the CLOSING line.
Arms scored: spread FAV (ride the market's side) / DOG (fade it); total OVER / UNDER; NO BET = 0 by construction.
MOMENTUM is NOT scorable: nflverse schedules carry one closing line, no opening line or move. Stated, not faked.
Filters = src/.../nfl_engine/filters.py, thresholds fixed a priori (nothing fitted => every season 2013-2025 is held out).
Weather = forecast only (temp 2021-25, wind 2024-25, precip fetched 2021-25); other games -> 'unknown' leaf.
Usage: python3 study_leaves.py <games.csv> <pbp_dir>"""
from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nfl_engine import filters as F  # noqa: E402
import study as S  # noqa: E402

B = 2000
MIN_N = 40


def payoff(odds, won):
    odds = -110.0 if not np.isfinite(odds) else odds
    w = 100.0 / abs(odds) if odds < 0 else odds / 100.0
    return np.where(won == 1, w, np.where(won == 0, -1.0, 0.0))


def ci(x, seed=7):
    rng = np.random.default_rng(seed); i = rng.integers(0, len(x), (B, len(x))); m = x[i].mean(1)
    return float(x.mean()), float(np.quantile(m, .025)), float(np.quantile(m, .975))


def main():
    g, book = S.load(sys.argv[1], sys.argv[2]); fc, pr = S.forecasts()
    g = g[g.season >= 2013].reset_index(drop=True)
    rows = []
    for r in g.itertuples():
        th = book.terms(r.season, r.week, r.home_team, r.away_team); ta = book.terms(r.season, r.week, r.away_team, r.home_team)
        ctx = S.ctx_fc(r, fc, pr)
        if ctx.source == "forecast" and ctx.wind_mph is not None and np.isnan(ctx.wind_mph):
            ctx = S.WF.WeatherContext("forecast", ctx.roof, ctx.temp_f, None, ctx.precip_mm, ctx.lead_h)
        f = F.nfl_filters(ctx, th, ta, r.spread_line, r.total_line)
        home_fav = r.spread_line > 0
        fav_m = r.result if home_fav else -r.result; L = abs(r.spread_line)
        fo = r.home_spread_odds if home_fav else r.away_spread_odds; do = r.away_spread_odds if home_fav else r.home_spread_odds
        sw = 1 if fav_m > L else (0 if fav_m < L else -1); dw = 0 if sw == 1 else (1 if sw == 0 else -1)
        ow = 1 if r.total > r.total_line else (0 if r.total < r.total_line else -1); uw = 0 if ow == 1 else (1 if ow == 0 else -1)
        rows.append(dict(game=r.game_id, season=r.season, **f, FAV=float(payoff(fo, np.array(sw))), DOG=float(payoff(do, np.array(dw))),
                         OVER=float(payoff(r.over_odds, np.array(ow))), UNDER=float(payoff(r.under_odds, np.array(uw)))))
    d = pd.DataFrame(rows); out = {"n_games": len(d), "leaves": [], "note": {}}
    splits = [("weather", ["FAV", "DOG", "OVER", "UNDER"], None), ("matchup_total", ["OVER", "UNDER"], None), ("matchup_side", ["FAV", "DOG"], None),
              ("weather", ["OVER", "UNDER"], "total_bucket"), ("matchup_total", ["OVER", "UNDER"], "total_bucket"), ("matchup_side", ["FAV", "DOG"], "spread_bucket")]
    allleaf = [("ALL", "all", None, a) for a in ("FAV", "DOG", "OVER", "UNDER")]
    for filt, arms, ms in splits:
        keys = [filt] + ([ms] if ms else [])
        for lv, sub in d.groupby(keys):
            lv = lv if isinstance(lv, tuple) else (lv,)
            for arm in arms:
                x = sub[arm].to_numpy()
                if len(x) < MIN_N: continue
                m, lo, hi = ci(x)
                out["leaves"].append(dict(filter=filt, market_state=ms, leaf="|".join(lv), arm=arm, n=int(len(x)), net=m, lo=lo, hi=hi,
                                          earns=("YES" if lo > 0 else "loses" if hi < 0 else "no"),
                                          held_out_halves=[float(sub[sub.season % 2 == k][arm].mean()) for k in (0, 1)]))
    for a in ("FAV", "DOG", "OVER", "UNDER"):
        m, lo, hi = ci(d[a].to_numpy()); out["note"][f"baseline_{a}"] = dict(net=m, lo=lo, hi=hi, n=len(d))
    L = out["leaves"]; out["note"]["leaves_scored"] = len(L); out["note"]["leaves_earning"] = sum(l["earns"] == "YES" for l in L)
    out["note"]["expected_by_chance_at_2.5pct"] = round(0.025 * len(L), 1)
    safe_out(HERE / "results_leaves.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out["note"], indent=1))
    for l in sorted(L, key=lambda l: -l["lo"])[:12]:
        print(l["filter"], l["market_state"], l["leaf"], l["arm"], l["n"], round(l["net"], 4), round(l["lo"], 4), round(l["hi"], 4), l["earns"])


if __name__ == "__main__":
    main()

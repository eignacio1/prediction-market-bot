"""EXPLORATORY -- NFL engine scaffold vs frozen-recipe Gaussians (W73.3 Part B). Not a verdict. Plan: PLAN.md (frozen before fitting).

Reads public nflverse copies + archived 2025 KXNFLGAME candles. Pre-2026 only. Writes only via safe_out().
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "20261009_nfl_qb_challenger"))
sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
import engine as E  # noqa: E402
import importlib.util  # noqa: E402
_sp = importlib.util.spec_from_file_location("w641_study", HERE.parent / "20261009_nfl_qb_challenger" / "study.py")
W = importlib.util.module_from_spec(_sp)  # W64.1 study: build, ridge, pred, platt, phi, split_ticker, cols
_sp.loader.exec_module(W)
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import FEATURE_NAMES  # noqa: E402

B, SEED = 2000, 20261014
NSIM = 40_000
OFFS = np.array([-7, -3, 0, 3, 7], float)
FAMS = ["ml", "spread", "total", "team_total"]
KEY = [2.5, 3.5, 6.5, 7.5]
OTHER = [1.5, 4.5, 5.5, 9.5, 10.5]
R_GRID = [round(0.3 + 0.1 * i, 1) for i in range(8)]
SN_GRID = [0.5 * i for i in range(7)]
ARMS = {"A": "frozen", "B": "full"}
_delta_cache = {}


def delta_for(r, sn):
    if (r, sn) not in _delta_cache:
        _delta_cache[(r, sn)] = E.ot_delta(n=60_000, r=r, s_n=sn)
    return _delta_cache[(r, sn)]


def boot(d, level=0.95):
    rng = np.random.default_rng(SEED)
    n = len(d)
    m = d[rng.integers(0, n, (B, n))].mean(1)
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    return dict(mean=float(d.mean()), lo=float(np.percentile(m, lo)), hi=float(np.percentile(m, hi)))


def fit_shape(lg_t, sd_m, sd_t):
    best = None
    for r in R_GRID:
        for sn in SN_GRID:
            s = E.simulate(lg_t / 2, lg_t / 2, 20_000, 12345, r, sn, delta=delta_for(r, sn))
            e = (s.margin.std() - sd_m) ** 2 + (s.total.std() - sd_t) ** 2
            if best is None or e < best[0]:
                best = (e, r, sn)
    return best[1], best[2]


def logit_fit(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    x = np.log(p / (1 - p))
    a, b = 1.0, 0.0
    for _ in range(30):
        q = 1 / (1 + np.exp(-(a * x + b)))
        w = q * (1 - q)
        X = np.column_stack([x, np.ones_like(x)])
        g = X.T @ (y - q)
        H = X.T @ (X * w[:, None]) + 1e-9 * np.eye(2)
        s = np.linalg.solve(H, g)
        a, b = a + s[0], b + s[1]
    return float(a), float(b)


def reliab(p, y):
    bins = np.minimum((p * 10).astype(int), 9)
    return [dict(bin=i, n=int((bins == i).sum()), p=float(p[bins == i].mean()), y=float(y[bins == i].mean()))
            for i in range(10) if (bins == i).any()]


def bvn_upper(mx, sx, my, sy, rho, a, b, z):
    """P(X>a, Y>b) for bivariate normal using fixed standard draws z (n,2)."""
    x = mx + sx * z[:, 0]
    y = my + sy * (rho * z[:, 0] + math.sqrt(1 - rho**2) * z[:, 1])
    return float(((x > a) & (y > b)).mean())


def main():
    ap = argparse.ArgumentParser()
    for k in ("schedule", "schedule-ext", "team-stats", "candles", "markets"):
        ap.add_argument(f"--{k}", required=True)
    a = ap.parse_args()
    sched, ext, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.schedule_ext), pd.read_parquet(a.team_stats)
    df = W.build(sched, ext, stats)
    tot = sched.set_index("game_id").apply(lambda r: r.home_score + r.away_score, axis=1)
    df["total"] = df.game_id.map(tot).astype(float)
    print("rows", len(df), file=sys.stderr)
    zj = np.random.default_rng(99).standard_normal((NSIM, 2))
    recs, shapes, cons = [], [], dict(sum_identity_viol=0, ladder_monotone_viol=0, games=0)
    for T in W.TESTS:
        tr, ca, te = df[df.season <= T - 2], df[df.season == T - 1], df[df.season == T]
        for arm, key in ARMS.items():
            c = W.cols(key)
            Xtr, Xca, Xte = (d[c].to_numpy(float) for d in (tr, ca, te))
            mm = W.ridge(Xtr, tr.margin.to_numpy(float), 100.0)
            mt = W.ridge(Xtr, tr.total.to_numpy(float), 100.0)
            rc = W.pred(mm, Xca)
            sm = float(np.std(ca.margin.to_numpy(float) - rc, ddof=1))
            st = float(np.std(ca.total.to_numpy(float) - W.pred(mt, Xca), ddof=1))
            rho = float(np.corrcoef(ca.margin.to_numpy(float) - rc, ca.total.to_numpy(float) - W.pred(mt, Xca))[0, 1])
            nt = (ca.margin != 0).to_numpy()
            pa, pb = W.platt(rc[nt] / sm, ca.y.to_numpy()[nt])
            mu_m = pa * W.pred(mm, Xte) + pb * sm
            mu_t = W.pred(mt, Xte)
            r, sn = fit_shape(float(ca.total.mean()), sm, st)
            d = delta_for(r, sn)
            shapes.append(dict(season=T, arm=arm, r=r, s_n=sn, delta=d, sigma_margin=sm, sigma_total=st, rho=rho, platt_a=pa, platt_b=pb))
            for i, g in enumerate(te.itertuples()):
                mh, ma_ = (mu_t[i] + mu_m[i]) / 2, (mu_t[i] - mu_m[i]) / 2
                s = E.simulate(mh, ma_, NSIM, zlib.crc32(g.game_id.encode()), r, sn, delta=d,
                               provenance=dict(game_id=g.game_id, arm=arm))
                cons["games"] += 1
                cons["sum_identity_viol"] += int((s.total != s.home_pts + s.away_pts).any())
                cm, ct = math.floor(mu_m[i]) + 0.5, math.floor(mu_t[i]) + 0.5
                ch, ca2 = math.floor(mh) + 0.5, math.floor(ma_) + 0.5
                am, at_, ah, aw = g.margin, g.total, None, None
                hs = (at_ + am) / 2
                as_ = (at_ - am) / 2
                row = dict(season=T, arm=arm, game_id=g.game_id)
                # moneyline
                row["ml"] = ([E.p_moneyline_home(s)], [W.phi(mu_m[i] / sm)], [g.y])
                ks = cm + OFFS
                pe = [E.p_spread_home_covers(s, k) for k in ks]
                cons["ladder_monotone_viol"] += int(any(x < y_ - 1e-12 for x, y_ in zip(pe, pe[1:])))
                row["spread"] = (pe, [1 - W.phi((k - mu_m[i]) / sm) for k in ks], [float(am > k) for k in ks])
                ks = ct + OFFS
                row["total"] = ([E.p_total_over(s, k) for k in ks], [1 - W.phi((k - mu_t[i]) / st) for k in ks],
                                [float(at_ > k) for k in ks])
                # team totals: home and away ladders pooled
                vh = (st**2 + sm**2 + 2 * rho * st * sm) / 4
                va = (st**2 + sm**2 - 2 * rho * st * sm) / 4
                khs, kas = ch + OFFS, ca2 + OFFS
                row["team_total"] = ([E.p_team_total_over(s, True, k) for k in khs] + [E.p_team_total_over(s, False, k) for k in kas],
                                     [1 - W.phi((k - mh) / math.sqrt(vh)) for k in khs] + [1 - W.phi((k - ma_) / math.sqrt(va)) for k in kas],
                                     [float(hs > k) for k in khs] + [float(as_ > k) for k in kas])
                kk = [x for v in KEY for x in (v, -v)]
                oo = [x for v in OTHER for x in (v, -v)]
                row["key"] = ([E.p_spread_home_covers(s, k) for k in kk], [1 - W.phi((k - mu_m[i]) / sm) for k in kk], [float(am > k) for k in kk])
                row["oth"] = ([E.p_spread_home_covers(s, k) for k in oo], [1 - W.phi((k - mu_m[i]) / sm) for k in oo], [float(am > k) for k in oo])
                je = E.p_joint(s, lambda x: x.margin > cm, lambda x: x.total > ct)
                jg = bvn_upper(mu_m[i], sm, mu_t[i], st, rho, cm, ct, zj)
                row["joint"] = ([je], [jg], [float((am > cm) and (at_ > ct))])
                row["pwin_vs_cover0"] = (E.p_moneyline_home(s), E.p_spread_home_covers(s, -0.5), float((s.margin == 0).mean()))
                row["ot_rate"] = float(s.went_ot.mean())
                row["tie_rate"] = float((s.margin == 0).mean())
                recs.append(row)
            print("done", T, arm, file=sys.stderr)

    res = {"n_games": int(len(recs) // 2), "nsim": NSIM, "shapes": shapes, "consistency": cons, "families": {}}
    fam_keys = FAMS + ["key", "oth", "joint"]
    for arm in ARMS:
        R = [r for r in recs if r["arm"] == arm]
        seas = np.array([r["season"] for r in R])
        out = {}
        for f in fam_keys:
            pe = [np.array(r[f][0]) for r in R]
            pg = [np.array(r[f][1]) for r in R]
            yy = [np.array(r[f][2]) for r in R]
            be = np.array([((a_ - y_) ** 2).mean() for a_, y_ in zip(pe, yy)])
            bg = np.array([((a_ - y_) ** 2).mean() for a_, y_ in zip(pg, yy)])
            d = be - bg
            PE, PG, Y = np.concatenate(pe), np.concatenate(pg), np.concatenate(yy)
            ce, cg = np.clip(PE, 1e-6, 1 - 1e-6), np.clip(PG, 1e-6, 1 - 1e-6)
            o = dict(brier_engine=float(be.mean()), brier_gauss=float(bg.mean()), delta=boot(d),
                     per_season={str(T): float(d[seas == T].mean()) for T in W.TESTS},
                     logloss_engine=float(-(Y * np.log(ce) + (1 - Y) * np.log(1 - ce)).mean()),
                     logloss_gauss=float(-(Y * np.log(cg) + (1 - Y) * np.log(1 - cg)).mean()),
                     calib_slope_intercept_engine=logit_fit(PE, Y), calib_slope_intercept_gauss=logit_fit(PG, Y),
                     reliability_engine=reliab(PE, Y), reliability_gauss=reliab(PG, Y))
            if f in FAMS:
                hi = o["delta"]["hi"]
                o["decision"] = "BEATS" if hi < 0 else ("MATCHES" if hi < 0.001 else "NO")
            out[f] = o
        pw = np.array([r["pwin_vs_cover0"] for r in R])
        out["consistency"] = dict(**{
            "max_abs_ml_minus_cover_adj": float(np.abs(pw[:, 0] - (pw[:, 1] - 0.5 * pw[:, 2])).max()),
            "mean_ot_rate": float(np.mean([r["ot_rate"] for r in R])), "mean_tie_rate": float(np.mean([r["tie_rate"] for r in R]))})
        res["families"][arm] = out

    # ---- 2025 market-mid subset (ML) ----
    et = ZoneInfo("America/New_York")
    teams = set(df.home) | set(df.away)
    sets = {}
    for l in open(a.candles):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26JAN' not in l and '"KXNFLGAME-26FEB' not in l:
            continue
        r = json.loads(l)
        if r.get("period_min") == 1 and r.get("candles"):
            sets[r["ticker"]] = r["candles"]
    mres = {}
    for l in open(a.markets):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26' not in l:
            continue
        r = json.loads(l)
        mres[r["ticker"]] = r.get("result")
    pml = {(r["arm"], r["game_id"]): r["ml"] for r in recs if r["season"] == 2025}
    g25 = df[df.season == 2025]
    mk = []
    for tk, cs in sets.items():
        sp = W.split_ticker(tk, teams)
        if not sp:
            continue
        away, home, side = sp
        if side != home:
            continue
        g = g25[(g25.home == home) & (g25.away == away)]
        if len(g) != 1:
            continue
        g = g.iloc[0]
        ko = datetime(*map(int, g.gameday.split("-")), *map(int, g.gametime.split(":")[:2]), tzinfo=et).timestamp()
        cand = [c for c in cs if c["t"] <= ko - 1800 and c["ask"]["close"] is not None and c["bid"]["close"] is not None]
        if not cand or mres.get(tk) not in ("yes", "no"):
            continue
        c = cand[-1]
        if ko - 1800 - c["t"] > 3600:
            continue
        mk.append(dict(gA=pml[("A", g.game_id)][1][0], eA=pml[("A", g.game_id)][0][0], gB=pml[("B", g.game_id)][1][0],
                       eB=pml[("B", g.game_id)][0][0], mid=(c["ask"]["close"] + c["bid"]["close"]) / 2,
                       y=1.0 if mres[tk] == "yes" else 0.0))
    m = pd.DataFrame(mk)
    ms = {"n": int(len(m))}
    if len(m) >= 10:
        for k in ("gA", "eA", "gB", "eB", "mid"):
            ms[f"brier_{k}"] = float(((m[k] - m.y) ** 2).mean())
        for k in ("gA", "eA", "gB", "eB"):
            ms[f"{k}_minus_mid"] = boot((((m[k] - m.y) ** 2) - ((m.mid - m.y) ** 2)).to_numpy())
    res["market_subset_2025_ml"] = ms
    res["frozen_2025_ml_brier_A_gauss"] = float(np.mean([((r["ml"][1][0] - r["ml"][2][0]) ** 2) for r in recs
                                                         if r["arm"] == "A" and r["season"] == 2025]))
    p = safe_out(HERE / "results.json")
    p.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "shapes"}, indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()

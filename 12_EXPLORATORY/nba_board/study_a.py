"""W93.3 Part A: rolling-origin held-out score of the NBA board engine vs a same-means Gaussian (PLAN.md s4).

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_board/study_a.py <NBA_EVENTS raw dir> <out json>
Reads only completed regular-season games; ratings are as-of (no game sees itself). Writes only the given json.
"""
from __future__ import annotations

import glob
import json
import sys
from statistics import NormalDist

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 2)[0])
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_factors as F, nba_point_in_time as P
from prediction_market_bot.nba_engine import engine as E, ratings as R
from prediction_market_bot.quant.inference import cluster_bootstrap

ND = NormalDist()
N_SIM = 4000
OFFS = (-6, -3, 0, 3, 6)
KS = (10.0, 20.0, 40.0)


def load(raw):
    rd = lambda n: pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/{n}/*.parquet"))], ignore_index=True)
    sch, esp, tb = rd("schedule"), rd("espn_schedule"), rd("team_box")
    return F.team_game_table(sch, tb, P.tip_table(sch, esp))


def reg_means(g):
    mu_h = g["mu_poss"] * g["ppp_h"] / 100.0
    mu_a = g["mu_poss"] * g["ppp_a"] / 100.0
    return mu_h, mu_a


def calibrate(g_cal):
    """hca, level bias, (s_p, s_e) from a calibration season's out-of-sample residuals."""
    mu_h, mu_a = reg_means(g_cal)
    rm = (g_cal["home_pts"] - g_cal["away_pts"]) - (mu_h - mu_a)
    rt = (g_cal["home_pts"] + g_cal["away_pts"]) - (mu_h + mu_a)
    hca = float(rm.mean())
    s_p, s_e = E.fit_shape(rm.to_numpy(), rt.to_numpy(), float(g_cal["mu_poss"].mean()), float((mu_h + mu_a).mean()))
    return dict(hca=hca, tbias=float(rt.mean()), s_p=s_p, s_e=s_e, sd_margin=float(rm.std()), sd_total=float(rt.std()),
                rho_emp=float(np.corrcoef(g_cal["home_pts"] - mu_h, g_cal["away_pts"] - mu_a)[0, 1]))


def sim_game(row, cal, seed):
    # level bias is the part of the mean the ratings miss (overtime, league drift); spread across both teams' ppp
    adj = cal["tbias"] / 2.0 / (row["mu_poss"] / 100.0)
    return E.simulate(row["mu_poss"], row["ppp_h"] + adj, row["ppp_a"] + adj, cal["hca"], cal["s_p"], cal["s_e"], N_SIM, seed)


def gauss_surv(mu, sd, n):
    return 1.0 - ND.cdf((n - 0.5 - mu) / sd)


def score_season(g, cal):
    """Per game: for each family and strike, (engine p, gaussian p, outcome)."""
    rows = []
    for i, (gid, r) in enumerate(g.iterrows()):
        s = sim_game(r, cal, 1000 + i % 5000)
        mh, ma, mm, mt = s.home_pts.mean(), s.away_pts.mean(), s.margin.mean(), s.total.mean()
        sds = dict(margin=cal["sd_margin"], total=cal["sd_total"])
        hp, ap, mg, tt = r["home_pts"], r["away_pts"], r["home_pts"] - r["away_pts"], r["home_pts"] + r["away_pts"]
        fam = []
        fam.append(("ml", 1, E.p_margin_ge(s, 1), gauss_surv(mm, sds["margin"], 1), float(mg >= 1)))
        c = int(np.floor(mm)) + 1
        for o in OFFS:
            fam.append(("spread", c + o, E.p_margin_ge(s, c + o), gauss_surv(mm, sds["margin"], c + o), float(mg >= c + o)))
        c = int(np.floor(mt)) + 1
        for o in OFFS:
            fam.append(("total", c + o, E.p_total_ge(s, c + o), gauss_surv(mt, sds["total"], c + o), float(tt >= c + o)))
        for side, m, pts in (("home", mh, hp), ("away", ma, ap)):
            sd_t = float(np.sqrt(np.var(s.home_pts if side == "home" else s.away_pts)))  # gaussian uses cal-implied team sd
            c = int(np.floor(m)) + 1
            for o in OFFS:
                fam.append(("team_total", c + o, E.p_team_total_ge(s, side, c + o), gauss_surv(m, cal["sd_team"], c + o),
                            float(pts >= c + o)))
        for f, n, pe, pg, y in fam:
            rows.append((str(gid), r["season"], f, n, pe, pg, y))
    return pd.DataFrame(rows, columns=["game_id", "season", "family", "strike", "p_engine", "p_gauss", "y"])


def calib_slope(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    x = np.log(p / (1 - p))
    X = np.column_stack([np.ones_like(x), x])
    # logistic fit by Newton
    b = np.array([0.0, 1.0])
    for _ in range(30):
        mu = 1 / (1 + np.exp(-X @ b))
        W = mu * (1 - mu)
        H = X.T @ (X * W[:, None]) + 1e-9 * np.eye(2)
        b = b + np.linalg.solve(H, X.T @ (y - mu))
    return float(b[1]), float(b[0])


def main(raw, out):
    tg = load(raw)
    tg = tg[tg["season_type"] == "regular-season"]
    results, shape_log = [], {}
    for T in range(2021, 2027):
        best = None
        for k in KS:  # K picked on calibration season T-1 only: ratings built from <= T-1 data, scored on T-1
            g = R.game_inputs(R.add_ratings(tg[tg.season <= T - 1], k=k))
            g = g[g.season == T - 1]
            if len(g) < 500:
                continue
            mu_h, mu_a = reg_means(g)
            mse = float(np.mean(((g["home_pts"] - g["away_pts"]) - (mu_h - mu_a)) ** 2) + np.mean(((g["home_pts"] + g["away_pts"]) - (mu_h + mu_a)) ** 2))
            if best is None or mse < best[1]:
                best = (k, mse, g)
        k, _, gcal = best
        cal = calibrate(gcal)
        mu_h, mu_a = reg_means(gcal)
        cal["sd_team"] = float(np.std(np.concatenate([(gcal["home_pts"] - mu_h).to_numpy(), (gcal["away_pts"] - mu_a).to_numpy()])))
        gall = R.game_inputs(R.add_ratings(tg[tg.season <= T], k=k))
        gt = gall[gall.season == T]
        sc = score_season(gt, cal)
        # sim-vs-target check on the engine's own shape
        sm = sim_game(gt.iloc[0], cal, 7)
        cal["sim_sd_margin"] = float(np.std(sm.margin)); cal["sim_sd_total"] = float(np.std(sm.total)); cal["sim_rho"] = E.score_corr(sm)
        cal["K"] = k; cal["n_test_games"] = int(len(gt)); cal["test_rho_emp"] = None
        mh_t, ma_t = reg_means(gt)
        cal["test_rho_emp"] = float(np.corrcoef(gt["home_pts"] - mh_t, gt["away_pts"] - ma_t)[0, 1])
        shape_log[T] = cal
        results.append(sc)
        print(T, "K", k, "n", len(gt), {a: round(b, 3) for a, b in cal.items() if isinstance(b, float)}, flush=True)
    sc = pd.concat(results, ignore_index=True)
    sc["be"], sc["bg"] = (sc.p_engine - sc.y) ** 2, (sc.p_gauss - sc.y) ** 2
    summary = {}
    for fam, d in list(sc.groupby("family")) + [("ALL", sc)]:
        diffs = {gid: list((x.be - x.bg).to_numpy()) for gid, x in d.groupby("game_id")}
        m, lo, hi = cluster_bootstrap(diffs, b=2000, seed=20261028)
        sl, ic = calib_slope(d.p_engine.to_numpy(), d.y.to_numpy())
        sg, ig = calib_slope(d.p_gauss.to_numpy(), d.y.to_numpy())
        verdict = "BEATS" if hi < 0 else ("MATCHES" if hi < 0.0010 else "NO")
        summary[fam] = dict(n_games=int(d.game_id.nunique()), n_rows=int(len(d)), brier_engine=float(d.be.mean()), brier_gauss=float(d.bg.mean()),
                            delta=m, lo=lo, hi=hi, verdict=verdict, slope_engine=sl, icpt_engine=ic, slope_gauss=sg, icpt_gauss=ig)
        print(fam, {a: (round(b, 5) if isinstance(b, float) else b) for a, b in summary[fam].items()}, flush=True)
    per_season = {int(s): float((x.be - x.bg).mean()) for s, x in sc.groupby("season")}
    safe_out(out).write_text(json.dumps(dict(summary=summary, per_season_delta=per_season, shape=shape_log), indent=1, default=float))
    sc.to_csv(safe_out(out[: -len(".json")] + "_rows.csv.gz"), index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""W94.1 Part C: NBA engine v2 vs v1 vs same-means Gaussian, rolling-origin held-out 2021-2026 (paired, game-clustered).

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_engine_live/study_v2.py <NBA_EVENTS raw dir> <out json, inside 12_EXPLORATORY/>
Protocol = W93.3 study_a (K picked on season T-1; v1 shape fit on T-1) so v1/Gaussian rows are the pinned ones. v2 parameters
(hca, level, residual SDs -> rho, factor shifts) are fit on seasons T-3..T-1; its Platt step is fit on those seasons' own
predictions; season T is never seen. Writes only the given json and a rows csv.gz beside it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_board"))
sys.path.insert(0, str(HERE.parent))
import study_a as SA  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_factors import game_frame  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_schedule_geometry import schedule_geometry, venue_table  # noqa: E402
from prediction_market_bot.nba_engine import engine_v2 as V, ratings as R  # noqa: E402

OFFS = SA.OFFS
FACTORS = {  # name -> (target, game-level column)
    "venue_alt": ("total", "venue_alt"), "s_miles": ("total", "s_miles"), "s_g_last4": ("total", "s_g_last4"),
    "alt_gain_a": ("margin", "alt_gain_a"), "d_miles": ("margin", "d_miles"), "d_g_last4": ("margin", "d_g_last4"),
}


def geometry_games(raw):
    import glob
    rd = lambda n: pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/{n}/*.parquet"))], ignore_index=True)
    sch, esp = rd("schedule"), rd("espn_schedule")
    tg = SA.load(raw)
    tg = tg[tg["season_type"] == "regular-season"]
    sch["game_id"] = sch["game_id"].astype(str)
    geo = schedule_geometry(tg[["game_id", "team_id", "side", "season", "date", "tip_earliest", "tip_latest"]], venue_table(sch, esp))
    cols = ["travel_mi", "alt_m", "alt_gain", "g_last4"]
    tg = tg.merge(geo[["game_id", "team_id"] + cols], on=["game_id", "team_id"], how="left")
    g = game_frame(tg, cols)
    out = pd.DataFrame(index=g.index.astype(str))
    out["venue_alt"] = g["h_alt_m"].to_numpy() / 1000
    out["s_miles"] = (g["h_travel_mi"] + g["a_travel_mi"]).to_numpy() / 1000
    out["s_g_last4"] = (g["h_g_last4"] + g["a_g_last4"]).to_numpy()
    out["alt_gain_a"] = g["a_alt_gain"].to_numpy() / 1000
    out["d_miles"] = (g["h_travel_mi"] - g["a_travel_mi"]).to_numpy() / 1000
    out["d_g_last4"] = (g["h_g_last4"] - g["a_g_last4"]).to_numpy()
    return tg, out


def v2_rows(p, g, X, keep=None):
    """Closed-form v2 rows at strikes around the game's own v2 mean; side is kept for team totals."""
    rows = []
    for gid, r in g.iterrows():
        x = {f: float(X.loc[str(gid), c]) if str(gid) in X.index and np.isfinite(X.loc[str(gid), c]) else 0.0 for f, (_, c) in FACTORS.items()}
        mu_h = r["mu_poss"] * r["ppp_h"] / 100.0
        mu_a = r["mu_poss"] * r["ppp_a"] / 100.0
        m, t = V.game_means(p, mu_h, mu_a, x)
        mg, tt = r["home_pts"] - r["away_pts"], r["home_pts"] + r["away_pts"]
        rows.append((str(gid), "ml", "", 1, m, t, float(mg >= 1)))
        for o in OFFS:
            c = int(np.floor(m)) + 1
            rows.append((str(gid), "spread", "", c + o, m, t, float(mg >= c + o)))
            c = int(np.floor(t)) + 1
            rows.append((str(gid), "total", "", c + o, m, t, float(tt >= c + o)))
        for side, mean, pts in (("home", (t + m) / 2, r["home_pts"]), ("away", (t - m) / 2, r["away_pts"])):
            c = int(np.floor(mean)) + 1
            for o in OFFS:
                rows.append((str(gid), "team_total", side, c + o, m if side == "home" else -m, t, float(pts >= c + o)))
    d = pd.DataFrame(rows, columns=["game_id", "family", "side", "strike", "m", "t", "y"])
    return d


def raw_p(p, d):
    return np.array([V.raw_prob(p, f, m, t, n) for f, m, t, n in zip(d.family, d.m, d.t, d.strike)])


def train_variant(gtr, Xtr, mf, tf):
    mu_h = (gtr["mu_poss"] * gtr["ppp_h"] / 100.0).to_numpy()
    mu_a = (gtr["mu_poss"] * gtr["ppp_a"] / 100.0).to_numpy()
    fx = {f: Xtr.reindex(gtr.index.astype(str))[c].fillna(0.0).to_numpy() for f, (_, c) in FACTORS.items()}
    p = V.fit_params(mu_h, mu_a, gtr["home_pts"], gtr["away_pts"], fx, mf, tf)
    d = v2_rows(p, gtr, Xtr)
    d["raw"] = raw_p(p, d)
    platt = {f: V.fit_platt(x.raw.to_numpy(), x.y.to_numpy()) for f, x in d.groupby("family")}
    return V.with_platt(p, platt)


def boot(d, ca, cb, b=2000, seed=20261029):
    """Game-clustered bootstrap of the mean paired row difference (resample games, keep each game's rows together)."""
    diff = (d[ca] - d[cb]).groupby(d["game_id"]).agg(["sum", "count"]).to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diff), size=(b, len(diff)))
    est = diff[idx, 0].sum(1) / diff[idx, 1].sum(1)
    return float(diff[:, 0].sum() / diff[:, 1].sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def main(raw, out):
    tg, X = geometry_games(raw)
    variants = {"v2_core": ([], []), "v2_alt": ([], ["venue_alt"]), "v2_travel": (["d_miles", "alt_gain_a", "d_g_last4"], ["s_miles", "s_g_last4"]),
                "v2_all": (["d_miles", "alt_gain_a", "d_g_last4"], ["venue_alt", "s_miles", "s_g_last4"])}
    allrows, shapes = [], {}
    for T in range(2021, 2027):
        best = None
        for k in SA.KS:
            g = R.game_inputs(R.add_ratings(tg[tg.season <= T - 1], k=k))
            g = g[g.season == T - 1]
            mu_h, mu_a = SA.reg_means(g)
            mse = float(np.mean(((g["home_pts"] - g["away_pts"]) - (mu_h - mu_a)) ** 2) + np.mean(((g["home_pts"] + g["away_pts"]) - (mu_h + mu_a)) ** 2))
            if best is None or mse < best[1]:
                best = (k, mse, g)
        k, _, gcal = best
        cal = SA.calibrate(gcal)
        mu_h, mu_a = SA.reg_means(gcal)
        cal["sd_team"] = float(np.std(np.concatenate([(gcal["home_pts"] - mu_h).to_numpy(), (gcal["away_pts"] - mu_a).to_numpy()])))
        gall = R.game_inputs(R.add_ratings(tg[tg.season <= T], k=k))
        gt, gtr = gall[gall.season == T], gall[gall.season.between(T - 3, T - 1)]
        v1 = SA.score_season(gt, cal)
        v1["side"] = ""
        tt = v1.family == "team_total"
        v1.loc[tt, "side"] = np.where(v1[tt].groupby(["game_id", "family"]).cumcount() < len(OFFS), "home", "away")
        shapes[T] = dict(K=k, n_test=int(len(gt)), n_train=int(len(gtr)), v1_rho_sim=cal.get("rho_emp"))
        for name, (mf, tf) in variants.items():
            p = train_variant(gtr, X, mf, tf)
            shapes[T][name] = dict(rho=p.rho, sd_margin=p.sd_margin, sd_total=p.sd_total, hca=p.hca, tbias=p.tbias,
                                   shift_margin=p.shift_margin, shift_total=p.shift_total, platt=p.platt)
            # score v2 at v1's own strikes so every row is paired
            keyed = v1.merge(v2_rows(p, gt, X)[["game_id", "family", "side", "m", "t"]].drop_duplicates(["game_id", "family", "side"]),
                             on=["game_id", "family", "side"], how="left")
            raw = np.array([V.raw_prob(p, f, m if f != "team_total" else m, t, n) for f, m, t, n in zip(keyed.family, keyed.m, keyed.t, keyed.strike)])
            v1[name + "_raw"] = raw
            v1[name] = [V.calibrated(p, f, r) for f, r in zip(keyed.family, raw)]
        allrows.append(v1)
        print(T, "K", k, {n: round(shapes[T][n]["rho"], 3) for n in variants}, flush=True)
    sc = pd.concat(allrows, ignore_index=True)
    sc.to_csv(safe_out(HERE / (out[: -len(".json")] + "_rows.csv.gz")), index=False)
    br = lambda c: (sc[c] - sc.y) ** 2
    cols = ["p_engine", "p_gauss"] + list(variants) + [v + "_raw" for v in variants]
    for c in cols:
        sc["b_" + c] = br(c)
    pairs = [("v2_core", "p_engine"), ("v2_core", "p_gauss"), ("v2_alt", "v2_core"), ("v2_travel", "v2_core"), ("v2_all", "v2_core"),
             ("v2_all", "p_engine"), ("v2_core_raw", "p_engine")]
    summary = {}
    for fam, d in list(sc.groupby("family")) + [("ALL", sc)]:
        summary[fam] = {"n_games": int(d.game_id.nunique()), **{c: float(d["b_" + c].mean()) for c in cols}}
        for a, b in pairs:
            m, lo, hi = boot(d, "b_" + a, "b_" + b)
            summary[fam][f"{a}_minus_{b}"] = dict(delta=m, lo=lo, hi=hi)
        for c in ("p_engine", "v2_core_raw", "v2_core"):
            sl, ic = SA.calib_slope(d[c].to_numpy(), d.y.to_numpy())
            summary[fam][f"slope_{c}"] = sl
        print(fam, json.dumps(summary[fam], default=float)[:1500], flush=True)
    safe_out(HERE / out).write_text(json.dumps(dict(summary=summary, shapes=shapes), indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

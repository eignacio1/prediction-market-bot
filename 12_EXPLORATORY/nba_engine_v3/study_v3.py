"""W96.1 Part B: NBA engine v3 factors (pre-tip availability, lineups) vs v2 core, rolling-origin held-out 2025-2026, paired, game-clustered.

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_engine_v3/study_v3.py <NBA_EVENTS raw dir> <out json, inside 12_EXPLORATORY/>
Needs v3_factors.parquet (factors_frame.py). Protocol = W94.1 study_v2 (K on season T-1; v2 params on T-3..T-1; Platt on training
predictions; season T never seen) but restricted to games with a factor row (injury reports exist from 2022-23 only), so TEST = 2025, 2026
and TRAIN = the in-coverage seasons among T-3..T-1 (2023-24 for T=2025; 2023-25 for T=2026). v2_core is refit on the SAME training
games, so every contrast is v3-variant minus v2 on identical data. Rows are scored at v1's own strikes (as in W94.1).
Multiplicity: 3 variants x 4 families + ALL, reported as-is; a factor is carried only where its CI excludes 0 in the helpful direction.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_board"))
sys.path.insert(0, str(HERE.parent / "nba_engine_live"))
sys.path.insert(0, str(HERE.parent))
import study_a as SA  # noqa: E402
import study_v2 as S2  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import engine_v2 as V, engine_v3 as V3, ratings as R  # noqa: E402

OFFS = SA.OFFS
TESTS = (2025, 2026)
VARIANTS = {"v2_core": [], "v3_avail": ["d_exp_missing", "s_exp_missing"], "v3_lineup": ["d_lineup_net", "s_lineup_net"],
            "v3_all": ["d_exp_missing", "s_exp_missing", "d_lineup_net", "s_lineup_net"]}
COLS = sorted({c for v in VARIANTS.values() for c in v})


def rows_for(p, centers, g, F):
    rows = []
    for gid, r in g.iterrows():
        x = {c: float(F.at[str(gid), c]) for c in COLS if str(gid) in F.index}
        mu_h, mu_a = r["mu_poss"] * r["ppp_h"] / 100.0, r["mu_poss"] * r["ppp_a"] / 100.0
        m, t = V3.game_means(p, centers, mu_h, mu_a, x)
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
    return pd.DataFrame(rows, columns=["game_id", "family", "side", "strike", "m", "t", "y"])


def train_variant(gtr, F, names):
    idx = gtr.index.astype(str)
    cols = {c: F.reindex(idx)[c].to_numpy() for c in COLS}
    mu_h, mu_a = (gtr["mu_poss"] * gtr["ppp_h"] / 100.0).to_numpy(), (gtr["mu_poss"] * gtr["ppp_a"] / 100.0).to_numpy()
    p, centers = V3.fit(mu_h, mu_a, gtr["home_pts"], gtr["away_pts"], cols, names)
    d = rows_for(p, centers, gtr, F)
    d["raw"] = S2.raw_p(p, d)
    platt = {f: V.fit_platt(x.raw.to_numpy(), x.y.to_numpy()) for f, x in d.groupby("family")}
    return V.with_platt(p, platt), centers


def main(raw, out):
    F = pd.read_parquet(HERE / "v3_factors.parquet")
    F = F[F.season >= 2023]
    F = F.dropna(subset=COLS)
    tg = SA.load(raw)
    tg = tg[tg["season_type"] == "regular-season"]
    allrows, shapes = [], {}
    for T in TESTS:
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
        gall = gall[gall.index.astype(str).isin(F.index)]
        gt, gtr = gall[gall.season == T], gall[gall.season.between(T - 3, T - 1)]
        v1 = SA.score_season(gt, cal)
        v1["side"] = ""
        tt = v1.family == "team_total"
        v1.loc[tt, "side"] = np.where(v1[tt].groupby(["game_id", "family"]).cumcount() < len(OFFS), "home", "away")
        shapes[T] = dict(K=k, n_test=int(len(gt)), n_train=int(len(gtr)))
        for name, names in VARIANTS.items():
            p, c = train_variant(gtr, F, names)
            shapes[T][name] = dict(rho=p.rho, sd_margin=p.sd_margin, sd_total=p.sd_total, hca=p.hca, tbias=p.tbias,
                                   shift_margin=p.shift_margin, shift_total=p.shift_total, centers=c.mean)
            keyed = v1.merge(rows_for(p, c, gt, F)[["game_id", "family", "side", "m", "t"]].drop_duplicates(["game_id", "family", "side"]),
                             on=["game_id", "family", "side"], how="left")
            raw_ = np.array([V.raw_prob(p, f, m, t, n) for f, m, t, n in zip(keyed.family, keyed.m, keyed.t, keyed.strike)])
            v1[name] = [V.calibrated(p, f, r) for f, r in zip(keyed.family, raw_)]
        v1["season"] = T
        allrows.append(v1)
        print(T, shapes[T]["n_train"], shapes[T]["n_test"], flush=True)
    sc = pd.concat(allrows, ignore_index=True)
    sc = sc[sc.v2_core.notna()]
    sc.to_csv(safe_out(HERE / (out[: -len(".json")] + "_rows.csv.gz")), index=False)
    cols = ["p_engine"] + list(VARIANTS)
    for c in cols:
        sc["b_" + c] = (sc[c] - sc.y) ** 2
    pairs = [(v, "v2_core") for v in VARIANTS if v != "v2_core"]
    summary = {}
    for scope, sub in (("pooled", sc), *[(str(T), sc[sc.season == T]) for T in TESTS]):
        summary[scope] = {}
        for fam, d in list(sub.groupby("family")) + [("ALL", sub)]:
            summary[scope][fam] = {"n_games": int(d.game_id.nunique()), **{c: float(d["b_" + c].mean()) for c in cols}}
            for a, b in pairs:
                m, lo, hi = S2.boot(d, "b_" + a, "b_" + b)
                summary[scope][fam][f"{a}_minus_{b}"] = dict(delta=m, lo=lo, hi=hi)
        print(scope, {f: {k: round(v["delta"], 5) for k, v in s.items() if isinstance(v, dict)} for f, s in summary[scope].items()}, flush=True)
    safe_out(HERE.parent / out).write_text(json.dumps(dict(summary=summary, shapes=shapes), indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

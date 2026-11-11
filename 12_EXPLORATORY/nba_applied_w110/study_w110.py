"""W110.2 Part C: each applied factor group vs v2_core on identical games, rolling-origin held-out 2025 and 2026 (=2025-26), paired, game-clustered.

Protocol = W96.1 study_v3 (K on season T-1; params on T-3..T-1 within factor coverage; Platt on training predictions; season T never seen),
rows at v1's strikes. Complete-case on geometry + officials + usage columns so every variant scores the SAME games; PAM (hindsight) NaN = 0
(no PAM player in the rotation). Outputs per family: Brier, paired delta vs v2_core with game-cluster bootstrap CI, n.
Usage: study_w110.py <NBA_EVENTS raw dir> <out json, inside 12_EXPLORATORY/>
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
sys.path.insert(0, str(HERE.parent / "nba_engine_v3"))
sys.path.insert(0, str(HERE.parent))
import study_a as SA  # noqa: E402
import study_v2 as S2  # noqa: E402
import study_v3 as SV  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import engine_v2 as V, ratings as R  # noqa: E402
from prediction_market_bot.nba_engine import factors_applied as FA  # noqa: E402

FA.register()
G = list(FA.GROUPS["geometry"]); O = list(FA.GROUPS["officials"]); U = list(FA.GROUPS["usage"]); P = list(FA.GROUPS["pam"])
BASE = ["d_exp_missing", "s_exp_missing", "d_lineup_net", "s_lineup_net"]
VARIANTS = {"v2_core": [], "v3_base": BASE, "geometry": G, "officials_UB": O, "usage": U, "pam_HINDSIGHT": P,
            "new_pit": G + U, "new_all": G + O + U + P}
SV.COLS = sorted({c for v in VARIANTS.values() for c in v})
SV.VARIANTS = VARIANTS
TESTS = (2025, 2026)


def load_frame():
    F = pd.read_parquet(HERE.parent / "nba_engine_v3" / "v3_factors.parquet")
    N = pd.read_parquet(HERE / "w110_factors.parquet").drop(columns="season")
    F = F.join(N, how="inner")
    F = F[F.season >= 2023]
    F[P] = F[P].fillna(0.0)
    return F.dropna(subset=BASE + G + O + U)


def main(raw, out):
    F = load_frame()
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
        v1.loc[tt, "side"] = np.where(v1[tt].groupby(["game_id", "family"]).cumcount() < len(SA.OFFS), "home", "away")
        shapes[T] = dict(K=k, n_test=int(len(gt)), n_train=int(len(gtr)))
        for name, names in VARIANTS.items():
            p, c = SV.train_variant(gtr, F, names)
            shapes[T][name] = dict(sd_margin=p.sd_margin, sd_total=p.sd_total, hca=p.hca, shift_margin=p.shift_margin, shift_total=p.shift_total)
            keyed = v1.merge(SV.rows_for(p, c, gt, F)[["game_id", "family", "side", "m", "t"]].drop_duplicates(["game_id", "family", "side"]),
                             on=["game_id", "family", "side"], how="left")
            raw_ = np.array([V.raw_prob(p, f, m, t, n) for f, m, t, n in zip(keyed.family, keyed.m, keyed.t, keyed.strike)])
            v1[name] = [V.calibrated(p, f, r) for f, r in zip(keyed.family, raw_)]
        v1["season"] = T
        allrows.append(v1)
        print(T, shapes[T]["n_train"], shapes[T]["n_test"], flush=True)
    sc = pd.concat(allrows, ignore_index=True)
    sc = sc[sc.v2_core.notna()]
    sc.to_csv(safe_out(HERE / (out.split("/")[-1][: -len(".json")] + "_rows.csv.gz")), index=False)
    cols = ["p_engine"] + list(VARIANTS)
    for c in cols:
        sc["b_" + c] = (sc[c] - sc.y) ** 2
    pairs = [(v, "v2_core") for v in VARIANTS if v != "v2_core"]
    summary = {}
    for scope, sub in (("pooled", sc), *[(str(T), sc[sc.season == T]) for T in TESTS]):
        summary[scope] = {}
        for fam, d in list(sub.groupby("family")) + [("ALL", sub)]:
            summary[scope][fam] = {"n_games": int(d.game_id.nunique()), "n_rows": int(len(d)), **{c: float(d["b_" + c].mean()) for c in cols}}
            for a, b in pairs:
                m, lo, hi = S2.boot(d, "b_" + a, "b_" + b)
                summary[scope][fam][f"{a}_minus_{b}"] = dict(delta=m, lo=lo, hi=hi)
        print(scope, {f: {k: round(v["delta"], 5) for k, v in s.items() if isinstance(v, dict)} for f, s in summary[scope].items()}, flush=True)
    safe_out(HERE.parent / out).write_text(json.dumps(dict(summary=summary, shapes=shapes), indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

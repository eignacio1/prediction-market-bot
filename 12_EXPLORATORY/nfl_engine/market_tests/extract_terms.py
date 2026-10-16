"""EXPLORATORY -- W77.2 Part A.2 step 1: per-game engine v0 means + factor terms (points), rolling origin identical to study_stage3.
Point-in-time only; closing lines are attached afterwards and are NEVER inputs. Plan: market_tests/PLAN.md."""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
NE = HERE.parent
sys.path.insert(0, str(NE)); sys.path.insert(0, str(NE.parent)); sys.path.insert(0, str(NE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
sp = importlib.util.spec_from_file_location("study_stage3", NE / "study_stage3.py")
S3 = importlib.util.module_from_spec(sp); sys.modules["study_stage3"] = S3; sp.loader.exec_module(S3)
S2, S, W, F, A, ROOT, TESTS = S3.S2, S3.S, S3.W, S3.F, S3.A, S3.ROOT, S3.TESTS


def main(sched_path, stats_path, out):
    sched, stats = pd.read_parquet(sched_path), pd.read_parquet(stats_path)
    df = W.build(sched, sched, stats)
    df["total"] = df.game_id.map(sched.set_index("game_id").apply(lambda r: r.home_score + r.away_score, axis=1)).astype(float)
    plays = F.build_play_table(ROOT, list(range(2018, 2026)))
    plays["off"], plays["dfn"] = plays.off.map(W.norm), plays.dfn.map(W.norm)
    fC = S2.CoverageXPersonnel(plays, "prior")
    df["th_C"] = [fC.points(pd.Timestamp(r.gameday, tz="UTC"), r.home, r.away) for r in df.itertuples()]
    df["ta_C"] = [fC.points(pd.Timestamp(r.gameday, tz="UTC"), r.away, r.home) for r in df.itertuples()]
    flags, tg, _ = A.build_flags(ROOT, sched, list(range(2018, 2026)), W.norm)
    games = df[["game_id", "gameday", "home", "away"]]
    df["hs"], df["as"] = (df.total + df.margin) / 2, (df.total - df.margin) / 2
    rows = []
    for T in TESTS:
        tr, ca, te = df[df.season <= T - 2], df[df.season == T - 1], df[df.season == T]
        c = W.cols("full")
        mm = W.ridge(tr[c].to_numpy(float), tr.margin.to_numpy(float), 100.0)
        mt = W.ridge(tr[c].to_numpy(float), tr.total.to_numpy(float), 100.0)
        Xca, Xte = ca[c].to_numpy(float), te[c].to_numpy(float)
        rc = W.pred(mm, Xca)
        sm = float(np.std(ca.margin.to_numpy(float) - rc, ddof=1))
        nt = (ca.margin != 0).to_numpy()
        pa, pb = W.platt(rc[nt] / sm, ca.y.to_numpy()[nt])
        mu_m, mu_t = pa * W.pred(mm, Xte) + pb * sm, W.pred(mt, Xte)
        fit = df[(df.season >= 2019) & (df.season <= T - 1)]
        pm, pt = W.pred(mm, fit[c].to_numpy(float)), W.pred(mt, fit[c].to_numpy(float))
        rh, ra = fit.hs.to_numpy() - (pt + pm) / 2, fit["as"].to_numpy() - (pt - pm) / 2
        x = np.concatenate([fit.th_C.astype(float).fillna(0).to_numpy(), fit.ta_C.astype(float).fillna(0).to_numpy()])
        betC = float((x @ np.concatenate([rh, ra])) / (x @ x))
        rates = A.absence_rates(flags, T - 1); lost = A.lost_table(flags, tg, rates); sm_ = A.side_matrix(lost, tg)
        resid = pd.concat([pd.DataFrame(dict(game_id=fit.game_id, team=fit.home, r=rh)), pd.DataFrame(dict(game_id=fit.game_id, team=fit.away, r=ra))])
        M = sm_.merge(resid, on=["game_id", "team"], how="inner").dropna(subset=list(A.UNITS))
        coef, center = A.fit_coefs(M[list(A.UNITS)], M.r.to_numpy(float))
        f8 = A.AvailabilityFactor(lost, games, coef, center)
        for i, g in enumerate(te.itertuples()):
            asof = pd.Timestamp(g.gameday, tz="UTC")
            h8, a8 = f8.points(asof, g.home, g.away), f8.points(asof, g.away, g.home)
            rows.append(dict(season=T, game_id=g.game_id, margin=float(g.margin), total=float(g.total), y=float(g.y),
                             mu_m=float(mu_m[i]), mu_t=float(mu_t[i]),
                             c_h=np.nan if pd.isna(g.th_C) else betC * g.th_C, c_a=np.nan if pd.isna(g.ta_C) else betC * g.ta_C,
                             f8_h=np.nan if h8 is None else h8, f8_a=np.nan if a8 is None else a8))
        print("done", T, file=sys.stderr)
    out_df = pd.DataFrame(rows)
    safe_out(out).write_text(out_df.to_json(orient="records"))
    print(len(out_df))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

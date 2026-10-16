"""EXPLORATORY -- W76.2 Part B: F8 unit availability applied through the rate layer. Plan: PLAN.md addendum 2026-10-15 (W76.2),
frozen before this fit. Arms: B = engine v0 arm B; C = B + F5/F6; E = B + F8; F = C + F8. Not a verdict, no live model touched."""
from __future__ import annotations

import argparse, importlib.util, json, math, sys, zlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
import engine as E  # noqa: E402
import factors as F  # noqa: E402
import rate_layer as RL  # noqa: E402
import availability as A  # noqa: E402


def _load(name, fn):
    sp = importlib.util.spec_from_file_location(name, HERE / fn)
    m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m); return m


S2 = _load("study_stage2", "study_stage2.py")
S, W = S2.S, S2.W
ROOT = HERE.parent.parent
TESTS = S2.TESTS
ARMS = ("B", "C", "E", "F")


def main():
    ap = argparse.ArgumentParser()
    for k in ("schedule", "team-stats", "candles", "markets"):
        ap.add_argument(f"--{k}", required=True)
    a = ap.parse_args()
    sched, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.team_stats)
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
    recs, betas, term_sd = [], [], []
    for T in TESTS:
        tr, ca, te = df[df.season <= T - 2], df[df.season == T - 1], df[df.season == T]
        c = W.cols("full")
        mm = W.ridge(tr[c].to_numpy(float), tr.margin.to_numpy(float), 100.0)
        mt = W.ridge(tr[c].to_numpy(float), tr.total.to_numpy(float), 100.0)
        Xca, Xte = ca[c].to_numpy(float), te[c].to_numpy(float)
        rc = W.pred(mm, Xca)
        sm = float(np.std(ca.margin.to_numpy(float) - rc, ddof=1))
        st = float(np.std(ca.total.to_numpy(float) - W.pred(mt, Xca), ddof=1))
        nt = (ca.margin != 0).to_numpy()
        pa, pb = W.platt(rc[nt] / sm, ca.y.to_numpy()[nt])
        mu_m, mu_t = pa * W.pred(mm, Xte) + pb * sm, W.pred(mt, Xte)
        r, sn = S.fit_shape(float(ca.total.mean()), sm, st)
        d0 = S.delta_for(r, sn)
        fit = df[(df.season >= 2019) & (df.season <= T - 1)]
        pm, pt = W.pred(mm, fit[c].to_numpy(float)), W.pred(mt, fit[c].to_numpy(float))
        rh, ra = fit.hs.to_numpy() - (pt + pm) / 2, fit["as"].to_numpy() - (pt - pm) / 2
        # F5/F6 beta exactly as stage 2
        x = np.concatenate([fit.th_C.astype(float).fillna(0).to_numpy(), fit.ta_C.astype(float).fillna(0).to_numpy()])
        betC = float((x @ np.concatenate([rh, ra])) / (x @ x))
        # F8: absence rates and unit coefficients on seasons <= T-1 only
        rates = A.absence_rates(flags, T - 1)
        lost = A.lost_table(flags, tg, rates)
        sm_ = A.side_matrix(lost, tg)
        resid = pd.concat([pd.DataFrame(dict(game_id=fit.game_id, team=fit.home, r=rh)), pd.DataFrame(dict(game_id=fit.game_id, team=fit.away, r=ra))])
        M = sm_.merge(resid, on=["game_id", "team"], how="inner").dropna(subset=list(A.UNITS))
        coef, center = A.fit_coefs(M[list(A.UNITS)], M.r.to_numpy(float))
        f8 = A.AvailabilityFactor(lost, games, coef, center)
        th8, ta8 = [], []
        for g in te.itertuples():
            asof = pd.Timestamp(g.gameday, tz="UTC")
            th8.append(f8.points(asof, g.home, g.away)); ta8.append(f8.points(asof, g.away, g.home))
        th8, ta8 = np.array([np.nan if v is None else v for v in th8]), np.array([np.nan if v is None else v for v in ta8])
        betas.append(dict(season=T, beta_C=betC, coef_F8=coef, center_F8=center, rates=rates, f8_fit_sides=int(len(M)),
                          f8_populated=float(np.mean(~np.isnan(th8)))))
        term_sd.append(dict(season=T, sd_F8=float(np.nanstd(np.concatenate([th8, ta8])))))
        for i, g in enumerate(te.itertuples()):
            mh0, ma0 = (mu_t[i] + mu_m[i]) / 2, (mu_t[i] - mu_m[i]) / 2
            cm, ct = math.floor(mu_m[i]) + 0.5, math.floor(mu_t[i]) + 0.5
            ch, ca2 = math.floor(mh0) + 0.5, math.floor(ma0) + 0.5
            cH = 0.0 if pd.isna(g.th_C) else betC * g.th_C
            cA = 0.0 if pd.isna(g.ta_C) else betC * g.ta_C
            e8h = 0.0 if np.isnan(th8[i]) else th8[i]
            e8a = 0.0 if np.isnan(ta8[i]) else ta8[i]
            shifts = {"B": (0.0, 0.0), "C": (cH, cA), "E": (e8h, e8a), "F": (cH + e8h, cA + e8a)}
            row = dict(season=T, game_id=g.game_id)
            for arm in ARMS:
                mh, ma_ = mh0 + shifts[arm][0], ma0 + shifts[arm][1]
                s = E.simulate(mh, ma_, S.NSIM, zlib.crc32(g.game_id.encode()), r, sn, delta=d0, provenance=dict(game_id=g.game_id, arm=arm))
                am, at_ = g.margin, g.total
                hs_, as__ = (at_ + am) / 2, (at_ - am) / 2
                row[arm] = dict(
                    ml=([E.p_moneyline_home(s)], [g.y]),
                    spread=([E.p_spread_home_covers(s, k) for k in cm + S.OFFS], [float(am > k) for k in cm + S.OFFS]),
                    total=([E.p_total_over(s, k) for k in ct + S.OFFS], [float(at_ > k) for k in ct + S.OFFS]),
                    team_total=([E.p_team_total_over(s, True, k) for k in ch + S.OFFS] + [E.p_team_total_over(s, False, k) for k in ca2 + S.OFFS],
                                [float(hs_ > k) for k in ch + S.OFFS] + [float(as__ > k) for k in ca2 + S.OFFS]),
                    mu=(mh, ma_))
            row["f8_used"] = bool(not np.isnan(th8[i]))
            recs.append(row)
        print("done", T, file=sys.stderr)
    res = {"n_games": len(recs), "tests": TESTS, "betas": betas, "term_sd": term_sd, "families": {},
           "f8_populated_overall": float(np.mean([r["f8_used"] for r in recs]))}
    seas = np.array([r["season"] for r in recs])
    for lab, arm, base in (("E_vs_B", "E", "B"), ("F_vs_C", "F", "C"), ("C_vs_B", "C", "B")):
        out = {}
        for f in S.FAMS:
            def br(a_):
                return np.array([((np.array(r[a_][f][0]) - np.array(r[a_][f][1])) ** 2).mean() for r in recs])
            bB, bX = br(base), br(arm)
            dd = bX - bB
            PB = np.concatenate([r[base][f][0] for r in recs]); PX = np.concatenate([r[arm][f][0] for r in recs]); Y = np.concatenate([r[base][f][1] for r in recs])
            o = dict(brier_base=float(bB.mean()), brier_arm=float(bX.mean()), delta=S.boot(dd),
                     per_season={str(T): float(dd[seas == T].mean()) for T in TESTS},
                     calib_base=S.logit_fit(PB, Y), calib_arm=S.logit_fit(PX, Y))
            hi = o["delta"]["hi"]
            o["decision"] = "BEATS" if hi < 0 else ("MATCHES" if hi < 0.001 else "NO")
            out[f] = o
        res["families"][lab] = out
    for arm in ("C", "E", "F"):
        d = np.array([[r[arm]["mu"][0] - r["B"]["mu"][0], r[arm]["mu"][1] - r["B"]["mu"][1]] for r in recs])
        res[f"mean_abs_mu_shift_{arm}"], res[f"max_abs_mu_shift_{arm}"] = float(np.abs(d).mean()), float(np.abs(d).max())
    # ---- 2025 KXNFLGAME ML market subset (reported, never judged) ----
    et = ZoneInfo("America/New_York")
    teams = set(df.home) | set(df.away)
    sets, mres = {}, {}
    for l in open(a.candles):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26JAN' not in l and '"KXNFLGAME-26FEB' not in l:
            continue
        r_ = json.loads(l)
        if r_.get("period_min") == 1 and r_.get("candles"):
            sets[r_["ticker"]] = r_["candles"]
    for l in open(a.markets):
        if '"KXNFLGAME-25' in l or '"KXNFLGAME-26' in l:
            r_ = json.loads(l); mres[r_["ticker"]] = r_.get("result")
    pmap = {r["game_id"]: {arm: r[arm]["ml"][0][0] for arm in ARMS} for r in recs if r["season"] == 2025}
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
        cand = [c_ for c_ in cs if c_["t"] <= ko - 1800 and c_["ask"]["close"] is not None and c_["bid"]["close"] is not None]
        if not cand or mres.get(tk) not in ("yes", "no"):
            continue
        c_ = cand[-1]
        if ko - 1800 - c_["t"] > 3600:
            continue
        mk.append(dict(**pmap[g.game_id], mid=(c_["ask"]["close"] + c_["bid"]["close"]) / 2, y=1.0 if mres[tk] == "yes" else 0.0))
    m = pd.DataFrame(mk)
    ms = {"n": int(len(m))}
    if len(m) >= 10:
        for k in (*ARMS, "mid"):
            ms[f"brier_{k}"] = float(((m[k] - m.y) ** 2).mean())
        ms["E_minus_B"] = S.boot((((m.E - m.y) ** 2) - ((m.B - m.y) ** 2)).to_numpy())
        ms["F_minus_C"] = S.boot((((m.F - m.y) ** 2) - ((m.C - m.y) ** 2)).to_numpy())
        ms["E_minus_mid"] = S.boot((((m.E - m.y) ** 2) - ((m.mid - m.y) ** 2)).to_numpy())
    res["market_subset_2025_ml"] = ms
    safe_out(HERE / "results_stage3.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float)[:9000])


if __name__ == "__main__":
    main()

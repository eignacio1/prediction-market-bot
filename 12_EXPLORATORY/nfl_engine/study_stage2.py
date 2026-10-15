"""EXPLORATORY -- W75.2 Part B: F5/F6 coverage-x-personnel term applied through the rate layer. Plan: PLAN.md addendum 2026-10-15
(frozen before this fit). Arm B = engine v0 arm B; C = B + term (prior-season tendencies); D = B + term (in-season PIT). Not a verdict."""
from __future__ import annotations

import argparse
import importlib.util
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
sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
import engine as E  # noqa: E402
import factors as F  # noqa: E402
import rate_layer as RL  # noqa: E402

_sp = importlib.util.spec_from_file_location("v0study", HERE / "study.py")
S = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(S)
W = S.W
ROOT = HERE.parent.parent
TESTS = list(range(2020, 2026))
PLAYS_PER_TEAM_GAME = 62.0
OFF_PERS = F.FactorSpec("pers_usage", ("pers",), "off", ("shell", "pers"))


class CoverageXPersonnel:
    """Factor: points for an offense from the defense's shell mix (given personnel) vs league, at league cell payoffs."""
    name = "F5F6_coverage_x_personnel"

    def __init__(self, plays: pd.DataFrame, mode: str):
        self.plays, self.mode, self._cache = plays, mode, {}   # mode: 'prior' (seasons <= T-1) | 'inseason' (PIT, weekly)

    def _key(self, as_of: pd.Timestamp):
        season = as_of.year if as_of.month >= 3 else as_of.year - 1
        return (season, as_of.normalize()) if self.mode == "inseason" else (season, None)

    def _tables(self, as_of):
        key = self._key(as_of)
        if key in self._cache:
            return self._cache[key]
        season = key[0]
        far = pd.Timestamp("2100-01-01", tz="UTC")
        if self.mode == "prior":
            g = F.factor_values(self.plays, far, F.COVERAGE_X_PERSONNEL_NOMOTION, prior_seasons_only=season - 1)
            w = F.factor_values(self.plays, far, OFF_PERS, prior_seasons_only=season - 1)
        else:
            g = F.factor_values(self.plays, as_of, F.COVERAGE_X_PERSONNEL_NOMOTION)
            w = F.factor_values(self.plays, as_of, OFF_PERS)
        g = g.assign(c=g.share_shrunk / g.groupby(["dfn", "pers"]).share_shrunk.transform("sum"),
                     l=g.l_share / g.groupby(["dfn", "pers"]).l_share.transform("sum"))
        cond = {(d, p, s): c - l for d, p, s, c, l in zip(g.dfn, g.pers, g.shell, g.c, g.l)}
        pay = {(s, p): e for s, p, e in zip(g.shell, g.pers, g.l_epa)}
        wt = {(o, p): x for o, p, x in zip(w.off, w.pers, w.share_shrunk)}
        t = (cond, pay, wt, set(g.dfn), set(w.off))
        self._cache[key] = t
        return t

    def points(self, as_of, offense, defense):
        cond, pay, wt, dset, oset = self._tables(as_of)
        if defense not in dset or offense not in oset:
            return None
        tot = 0.0
        for (o, p), wo in ((k, v) for k, v in wt.items() if k[0] == offense):
            tot += wo * sum(cond.get((defense, p, s), 0.0) * pay[(s, p)] for (s, pp) in pay if pp == p)
        return PLAYS_PER_TEAM_GAME * tot


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
    fC, fD = CoverageXPersonnel(plays, "prior"), CoverageXPersonnel(plays, "inseason")
    # week-start as_of for the in-season arm: earliest gameday of (season, week) at 00:00 UTC
    wk0 = df.groupby(["season", "week"]).gameday.min().to_dict()
    for nm, f in (("C", fC), ("D", fD)):
        th, ta = [], []
        for r in df.itertuples():
            asof = pd.Timestamp(wk0[(r.season, r.week)], tz="UTC") if nm == "D" else pd.Timestamp(r.gameday, tz="UTC")
            th.append(f.points(asof, r.home, r.away))
            ta.append(f.points(asof, r.away, r.home))
        df[f"th_{nm}"], df[f"ta_{nm}"] = th, ta
        print("terms", nm, "populated", float(np.mean([x is not None for x in th])), file=sys.stderr)
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
        # beta: pooled through-origin OLS of team-points residual on term, seasons 2019..T-1
        fit = df[(df.season >= 2019) & (df.season <= T - 1)]
        pm = W.pred(mm, fit[c].to_numpy(float))
        pt = W.pred(mt, fit[c].to_numpy(float))
        rh, ra = fit.hs.to_numpy() - (pt + pm) / 2, fit["as"].to_numpy() - (pt - pm) / 2
        bet = {}
        for nm in ("C", "D"):
            x = np.concatenate([fit[f"th_{nm}"].astype(float).fillna(0).to_numpy(), fit[f"ta_{nm}"].astype(float).fillna(0).to_numpy()])
            y = np.concatenate([rh, ra])
            bet[nm] = float((x @ y) / (x @ x))
        betas.append(dict(season=T, **bet, fit_games=int(len(fit))))
        tc = np.concatenate([te.th_C.astype(float).fillna(0), te.ta_C.astype(float).fillna(0)])
        term_sd.append(dict(season=T, term_sd_C=float(tc.std()), term_sd_D=float(np.concatenate([te.th_D.astype(float).fillna(0), te.ta_D.astype(float).fillna(0)]).std())))
        for i, g in enumerate(te.itertuples()):
            mh0, ma0 = (mu_t[i] + mu_m[i]) / 2, (mu_t[i] - mu_m[i]) / 2
            cm, ct = math.floor(mu_m[i]) + 0.5, math.floor(mu_t[i]) + 0.5
            ch, ca2 = math.floor(mh0) + 0.5, math.floor(ma0) + 0.5
            row = dict(season=T, game_id=g.game_id)
            for arm in ("B", "C", "D"):
                if arm == "B":
                    mh, ma_ = mh0, ma0
                else:
                    gi = RL.GameInputs(pd.Timestamp(g.gameday, tz="UTC"), g.home, g.away, mh0, ma0)
                    thv, tav = getattr(g, f"th_{arm}"), getattr(g, f"ta_{arm}")
                    mh = mh0 + bet[arm] * (0.0 if pd.isna(thv) else thv)
                    ma_ = ma0 + bet[arm] * (0.0 if pd.isna(tav) else tav)
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
            recs.append(row)
        print("done", T, file=sys.stderr)
    res = {"n_games": len(recs), "tests": TESTS, "betas": betas, "term_sd": term_sd, "families": {}}
    seas = np.array([r["season"] for r in recs])
    for arm in ("C", "D"):
        out = {}
        for f in S.FAMS:
            def br(a_):
                return np.array([((np.array(r[a_][f][0]) - np.array(r[a_][f][1])) ** 2).mean() for r in recs])
            bB, bX = br("B"), br(arm)
            dd = bX - bB
            PB = np.concatenate([r["B"][f][0] for r in recs]); PX = np.concatenate([r[arm][f][0] for r in recs]); Y = np.concatenate([r["B"][f][1] for r in recs])
            o = dict(brier_B=float(bB.mean()), brier_arm=float(bX.mean()), delta=S.boot(dd),
                     per_season={str(T): float(dd[seas == T].mean()) for T in TESTS},
                     calib_B=S.logit_fit(PB, Y), calib_arm=S.logit_fit(PX, Y),
                     reliability_B=S.reliab(PB, Y), reliability_arm=S.reliab(PX, Y))
            hi = o["delta"]["hi"]
            o["decision"] = "BEATS" if hi < 0 else ("MATCHES" if hi < 0.001 else "NO")
            out[f] = o
        res["families"][arm] = out
    dmu = np.array([[r["C"]["mu"][0] - r["B"]["mu"][0], r["C"]["mu"][1] - r["B"]["mu"][1]] for r in recs])
    res["mean_abs_mu_shift_C_points"] = float(np.abs(dmu).mean())
    res["max_abs_mu_shift_C_points"] = float(np.abs(dmu).max())
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
            r_ = json.loads(l)
            mres[r_["ticker"]] = r_.get("result")
    pm = {r["game_id"]: {arm: r[arm]["ml"][0][0] for arm in ("B", "C", "D")} for r in recs if r["season"] == 2025}
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
        mk.append(dict(**pm[g.game_id], mid=(c_["ask"]["close"] + c_["bid"]["close"]) / 2, y=1.0 if mres[tk] == "yes" else 0.0))
    m = pd.DataFrame(mk)
    ms = {"n": int(len(m))}
    if len(m) >= 10:
        for k in ("B", "C", "D", "mid"):
            ms[f"brier_{k}"] = float(((m[k] - m.y) ** 2).mean())
        for k in ("B", "C"):
            ms[f"{k}_minus_mid"] = S.boot((((m[k] - m.y) ** 2) - ((m.mid - m.y) ** 2)).to_numpy())
        ms["C_minus_B"] = S.boot((((m.C - m.y) ** 2) - ((m.B - m.y) ** 2)).to_numpy())
    res["market_subset_2025_ml"] = ms
    p = safe_out(HERE / "results_stage2.json")
    p.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items()}, indent=1, default=float)[:7000])


if __name__ == "__main__":
    main()

"""W96.1 Part C (B-009): engine-priced player points vs the existing points arm (EXP-039 spec, ctrl_refit), held-out, paired.

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_engine_v3/study_partc.py <ESPN raw dir> <NBA_EVENTS raw dir> <out json, inside 12_EXPLORATORY/>
Folds = W69.3's: A train 2023 / calibrate 2024 / test 2025; B train 2023-24 / calibrate 2025 / test 2026.
Arms (all scored at strikes 10/15/20/25 on player-games where the player played, as EXP-039 does):
  base      ridge mean -> negative binomial -> Platt  (the existing arm's spec, refit on the fold)
  engine    team points ~ engine v2 team mean (+ sd_team), split over players by Dirichlet-multinomial, shares from the
            same ridge means, rest bucket, concentration by ML on the calibration season; Platt on the calibration season
  engine_pt  LEAK-FREE variant of engine: share = ridge mean / (mean team sum of ridge means over the team's previous 10 games in the
            frame, / (1 - rest)); no teammate enters, so who else played this game is never used (the other arms' shares are
            normalised over the players who played, which is post-game information the base arm does not have)
  sumonly   same split, team mean = sum of ridge means / (1 - rest share): isolates what the ENGINE's team total adds
Join ESPN game -> NBA game on (ET date, home pts, away pts). Per-team marginal of the team score is used (the opponent's score
does not enter one player's points). Who played is known only after the game: base and engine both condition on it identically.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(EXP / "nba_board"))
sys.path.insert(0, str(EXP / "20261012_nba_points_minutes"))
sys.path.insert(0, str(EXP))
sys.path.insert(0, str(EXP.parent / "scripts"))
import features as F  # noqa: E402
import study_a as SA  # noqa: E402
from _fence import safe_out  # noqa: E402
from train_nba_player_points import STRIKES, nb_loglik, platt, ridge  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N, nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date  # noqa: E402
from prediction_market_bot.nba_engine import engine_v2 as V, player_layer as PL, ratings as R  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_model import logit, nb_sf  # noqa: E402

FOLDS = {2025: ((2023,), 2024), 2026: ((2023, 2024), 2025)}
NSIM, B, SEED = 2000, 20000, 20261030
INJ = str(EXP / "20261012_nba_points_minutes" / "inj")


def engine_means(tg, T):
    """Per NBA game_id in seasons T-1 and T: (home mean pts, away mean pts, sd_team) from the v2 core (K on T-1, params on T-3..T-1)."""
    best = None
    for k in SA.KS:
        g = R.game_inputs(R.add_ratings(tg[tg.season <= T - 1], k=k))
        g = g[g.season == T - 1]
        mu_h, mu_a = SA.reg_means(g)
        mse = float(np.mean(((g["home_pts"] - g["away_pts"]) - (mu_h - mu_a)) ** 2) + np.mean(((g["home_pts"] + g["away_pts"]) - (mu_h + mu_a)) ** 2))
        if best is None or mse < best[1]:
            best = (k, mse)
    gall = R.game_inputs(R.add_ratings(tg[tg.season <= T], k=best[0]))
    gtr = gall[gall.season.between(T - 3, T - 1)]
    mh, ma = SA.reg_means(gtr)
    p = V.fit_params(mh, ma, gtr["home_pts"], gtr["away_pts"])
    out = {}
    for gid, r in gall[gall.season.isin([T - 1, T])].iterrows():
        m, t = V.game_means(p, r["mu_poss"] * r["ppp_h"] / 100.0, r["mu_poss"] * r["ppp_a"] / 100.0)
        out[str(gid)] = ((t + m) / 2.0, (t - m) / 2.0)
    return out, p.sd_team, best[0]


def boot(d, gid, rng):
    ug, inv = np.unique(gid, return_inverse=True)
    S, N = np.bincount(inv, weights=d), np.bincount(inv).astype(float)
    G = len(ug)
    bs = np.empty(B)
    for i in range(0, B, 500):
        idx = rng.integers(0, G, size=(min(500, B - i), G))
        bs[i:i + len(idx)] = S[idx].sum(1) / N[idx].sum(1)
    return {"delta": float(d.mean()), "ci95": [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))], "n": int(len(d)), "n_games": int(G)}


def main(espn_raw, nba_raw, out):
    espn_raw, nba_raw = Path(espn_raw), Path(nba_raw)
    rows = F.build_frame(espn_raw, INJ)
    meta, gscore = {}, {}
    for s in (2023, 2024, 2025, 2026):
        gm = N.load_season(s, espn_raw)["games"]
        for gid, rec in P.load_players(s, espn_raw)["games"].items():
            if gid not in gm:
                continue
            gscore[gid] = (str(et_date(_dt(rec["start_time_utc"]))), gm[gid]["home_score"], gm[gid]["away_score"])
            for r in rec["rows"]:
                meta[(gid, r["player_id"])] = (r["team"], r["home"])
    tg = SA.load(str(nba_raw))
    tg = tg[tg["season_type"] == "regular-season"]
    sch = pd.concat([pd.read_parquet(f) for f in sorted((nba_raw / "schedule").glob("*.parquet"))], ignore_index=True)
    sch = sch[sch.season_type == "regular-season"].drop_duplicates("game_id")
    key2nba = {(str(r.game_date)[:10], int(r.home_pts), int(r.away_pts)): str(r.game_id) for r in sch.itertuples() if r.home_pts == r.home_pts}
    rows = [r for r in rows if r["game_id"] in gscore]
    for r in rows:
        r["team"], r["home"] = meta[(r["game_id"], r["player_id"])]
    allr, shapes = [], {}
    for T, (tr, ca) in FOLDS.items():
        eng, sd_team, K = engine_means(tg, T)
        R_ = lambda ss: [r for r in rows if r["season"] in ss]  # noqa: E731
        trr, car, ter = R_(tr), R_((ca,)), R_((T,))
        X = lambda rs: np.array([[r[k] for k in F.FEATURE_NAMES] for r in rs], float)  # noqa: E731
        y = lambda rs: np.array([r["points"] for r in rs], float)  # noqa: E731
        b0, w, mu, sd = ridge(X(trr), y(trr))
        mean = lambda rs: np.maximum(b0 + ((X(rs) - mu) / sd) @ w, 0.5)  # noqa: E731
        for rs in (trr, car, ter):
            for r, m in zip(rs, mean(rs)):
                r["mu"] = float(m)
        sums, order = {}, {}
        for r in trr + car + ter:
            sums[(r["game_id"], r["team"])] = sums.get((r["game_id"], r["team"]), 0.0) + r["mu"]
        hist = {}
        for (gid, tm), v in sorted(sums.items(), key=lambda kv: (gscore[kv[0][0]][0], kv[0][0])):
            hist.setdefault(tm, []).append((gid, v))
        Dprev = {}
        for tm, lst in hist.items():
            for i, (gid, _) in enumerate(lst):
                if i >= 10:
                    Dprev[(gid, tm)] = float(np.mean([x[1] for x in lst[i - 10:i]]))
        # base arm (same as EXP-039 spec)
        mc, yc = np.array([r["mu"] for r in car]), y(car)
        grid = np.exp(np.linspace(np.log(0.5), np.log(200), 60))
        r_hat = float(grid[int(np.argmax([nb_loglik(yc, mc, r) for r in grid]))])
        xs, ys = [], []
        for k in STRIKES:
            xs += [logit(nb_sf(k, m, r_hat)) for m in mc]
            ys += [1.0 if p >= k else 0.0 for p in yc]
        a_b, b_b = platt(np.array(xs), np.array(ys))
        # team-game structure
        def team_games(rs):
            d = {}
            for r in rs:
                d.setdefault((r["game_id"], r["team"]), []).append(r)
            return d
        def team_pts(gid, home):
            sc = gscore[gid]
            return sc[1] if home else sc[2]
        tgtr = team_games(trr)
        rest = float(np.mean([1 - sum(x["points"] for x in v) / team_pts(g, v[0]["home"]) for (g, _), v in tgtr.items()]))
        def raw_probs(rs, arm, conc, rng):
            """Per player-game raw P(points >= k) for k in STRIKES from NSIM joint draws."""
            res = {}
            for (gid, tm), v in team_games(rs).items():
                home = v[0]["home"]
                mus = [x["mu"] for x in v]
                if arm == "engine_pt":
                    nid = key2nba.get((gscore[gid][0], int(gscore[gid][1]), int(gscore[gid][2])))
                    if nid is None or nid not in eng or (gid, tm) not in Dprev:
                        continue
                    Tpts = np.maximum(np.rint(eng[nid][0 if home else 1] + sd_team * rng.standard_normal(NSIM)), 40).astype(int)
                    for x in v:
                        sj = min(x["mu"] * (1 - rest) / Dprev[(gid, tm)], 0.95)
                        pts = rng.binomial(Tpts, rng.beta(conc * sj, conc * (1 - sj), NSIM))
                        res[(gid, x["player_id"])] = [PL.p_at_least(pts, k) for k in STRIKES]
                    continue
                if arm == "engine":
                    nid = key2nba.get((gscore[gid][0], int(gscore[gid][1]), int(gscore[gid][2])))
                    if nid is None or nid not in eng:
                        continue
                    tmean = eng[nid][0 if home else 1]
                else:
                    tmean = sum(mus) / (1 - rest)
                Tpts = np.maximum(np.rint(tmean + sd_team * rng.standard_normal(NSIM)), 40).astype(int)
                d = PL.draw_split(Tpts, PL.shares_from_means(mus, rest), conc, rng)
                for j, x in enumerate(v):
                    res[(gid, x["player_id"])] = [PL.p_at_least(d[:, j], k) for k in STRIKES]
            return res
        rng = np.random.default_rng(SEED + T)
        preds = {}
        for arm in ("engine", "sumonly", "engine_pt"):
            # concentration by ML on the calibration season (team pts = actual: marginal of the split given T)
            ccal = [(r["points"], team_pts(r["game_id"], r["home"]), r["mu"], r["game_id"], r["team"]) for r in car]
            tot = {}
            for r in car:
                tot[(r["game_id"], r["team"])] = tot.get((r["game_id"], r["team"]), 0.0) + r["mu"]
            if arm == "engine_pt":
                ok = [i for i, c in enumerate(ccal) if (c[3], c[4]) in Dprev]
                sh = np.array([min(ccal[i][2] * (1 - rest) / Dprev[(ccal[i][3], ccal[i][4])], 0.95) for i in ok])
                conc = PL.fit_concentration(np.array([ccal[i][0] for i in ok]), np.array([ccal[i][1] for i in ok]), sh)
            else:
                sh = np.array([(1 - rest) * c[2] / tot[(c[3], c[4])] for c in ccal])
                conc = PL.fit_concentration(np.array([c[0] for c in ccal]), np.array([c[1] for c in ccal]), sh)
            pc = raw_probs(car, arm, conc, rng)
            kc = [(r["game_id"], r["player_id"]) for r in car if (r["game_id"], r["player_id"]) in pc]
            xs = np.array([logit(pc[q][i]) for q in kc for i in range(len(STRIKES))])
            ys = np.array([1.0 if r["points"] >= k else 0.0 for r in car if (r["game_id"], r["player_id"]) in pc for k in STRIKES])
            a_e, b_e = platt(xs, ys)
            pt = raw_probs(ter, arm, conc, rng)
            preds[arm] = (pt, a_e, b_e, conc)
        n_eng = len(preds["engine"][0])
        shapes[T] = dict(K=K, sd_team=sd_team, rest_share=rest, n_test_rows=len(ter), n_engine_rows=n_eng, r_hat=r_hat,
                         conc={a: preds[a][3] for a in preds}, n_engine_pt_rows=len(preds["engine_pt"][0]), platt_engine=preds["engine"][1:3])
        mt = np.array([r["mu"] for r in ter])
        for r, m in zip(ter, mt):
            q = (r["game_id"], r["player_id"])
            if q not in preds["engine"][0] or q not in preds["engine_pt"][0]:
                continue
            for i, k in enumerate(STRIKES):
                yy = 1.0 if r["points"] >= k else 0.0
                pb = 1 / (1 + np.exp(-(a_b * logit(nb_sf(k, m, r_hat)) + b_b)))
                pe = 1 / (1 + np.exp(-(preds["engine"][1] * logit(preds["engine"][0][q][i]) + preds["engine"][2])))
                ps = 1 / (1 + np.exp(-(preds["sumonly"][1] * logit(preds["sumonly"][0][q][i]) + preds["sumonly"][2])))
                pp = 1 / (1 + np.exp(-(preds["engine_pt"][1] * logit(preds["engine_pt"][0][q][i]) + preds["engine_pt"][2])))
                allr.append((T, r["game_id"], k, int(r["pts10"] >= 15), yy, pb, pe, ps, pp))
        print(T, shapes[T], flush=True)
    d = pd.DataFrame(allr, columns=["season", "game_id", "k", "star", "y", "pb", "pe", "ps", "pp"])
    for c in ("pb", "pe", "ps", "pp"):
        d["b_" + c] = (d[c] - d.y) ** 2
    d.to_csv(safe_out(HERE / (out[: -len(".json")] + "_rows.csv.gz")), index=False)
    rng = np.random.default_rng(SEED)
    res = {}
    contrasts = {"engine_minus_base": ("b_pe", "b_pb"), "sumonly_minus_base": ("b_ps", "b_pb"), "engine_minus_sumonly": ("b_pe", "b_ps"),
                 "engine_pt_minus_base": ("b_pp", "b_pb"), "engine_pt_minus_sumonly": ("b_pp", "b_ps")}
    for scope, sub in (("pooled", d), ("2025", d[d.season == 2025]), ("2026", d[d.season == 2026])):
        for sname, s in (("all", sub), ("star", sub[sub.star == 1])):
            for kk in ("ALL", *STRIKES):
                z = s if kk == "ALL" else s[s.k == kk]
                e = {"brier": {c: float(z["b_" + c].mean()) for c in ("pb", "pe", "ps", "pp")}}
                for name, (a, b) in contrasts.items():
                    e[name] = boot((z[a] - z[b]).to_numpy(), z.game_id.to_numpy(), rng)
                res[f"{scope}|{sname}|{kk}"] = e
    safe_out(HERE.parent / out).write_text(json.dumps(dict(results=res, shapes=shapes), indent=1, default=float))
    for kname, e in res.items():
        if kname.startswith("pooled"):
            print(kname, {n: (round(e[n]["delta"], 5), [round(x, 5) for x in e[n]["ci95"]]) for n in contrasts}, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

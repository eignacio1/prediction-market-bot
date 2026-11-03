"""W97.1 Part C (B-009): player points priced from the engine with NO post-game information anywhere, held-out, paired.

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_engine_v3/study_partc_w97.py <ESPN raw dir> <NBA_EVENTS raw dir> <out json, inside 12_EXPLORATORY/>
Same folds, scoring universe (player-games where the player played, as EXP-039 scores), strikes 10/15/20/25, engine team mean and
Platt calibration as W96.1's study_partc.py (imported, not edited). Arms:
  base        the existing points arm's spec (ridge mean -> negative binomial -> Platt), refit on the fold
  engine_pt   W96.1's leak-free arm: share = ridge mean / (mean team sum of ridge means over the team's previous 10 games)
  engine_set  NEW: share = mu_j / (mu_j + sum_i p_i mu_i) over the PRE-TIP candidate set (players whose latest prior appearance was for
              the team within 21 days), p_i = P(plays | injury status in the last report published >= 4h before tip), fit on training seasons
Who played comes only from the injury report and rotation as known before tip. The scored player must have played (the scoring universe,
identical for every arm); his own presence is not used in any other player's share.
Leakage test (hard assertion, runs before the study): for sampled team-games, the candidate set, each candidate's features and the report
slot used are rebuilt from data TRUNCATED to before the game's cutoff and must be identical; every report slot passes assert_pretip.
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study_partc as SP  # noqa: E402  (also puts the helper dirs on sys.path)
import features as F  # noqa: E402
from _fence import safe_out  # noqa: E402
from train_nba_player_points import STRIKES, nb_loglik, platt, ridge  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N, nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_player_features import FEATURE_NAMES, PlayerFeatureBuilder  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date, et_midnight_utc  # noqa: E402
from prediction_market_bot.nba_engine import player_availability as PA, player_layer as PL  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_model import logit, nb_sf  # noqa: E402

NSIM, B, SEED = SP.NSIM, SP.B, SP.SEED
SEASONS = (2023, 2024, 2025, 2026)


def load_all(espn_raw: Path):
    games, stores = [], []
    for s in SEASONS:
        games += list(N.load_season(s, espn_raw)["games"].values())
        stores.append(P.load_players(s, espn_raw))
    return games, stores


def slot_stamp(inj: dict, start):
    """UTC time of the report slot F.snapshot would use for this game (None if no report)."""
    day = inj.get(str(et_date(start)))
    if not day:
        return None
    base, best = et_midnight_utc(et_date(start)), None
    for slot in sorted(day):
        hh, mm = slot.split(":")
        t = base + timedelta(hours=int(hh), minutes=int(mm))
        if t <= start - F.LEAD:
            best = t
    return best


def pretip(fb, inj, gmap_rec, gid, team, opp, home, season):
    """Candidates for (game, team) from data before the game's cutoff: [(pid, name, features, status)]; also the report slot stamp."""
    start = _dt(gmap_rec["start_time_utc"])
    cutoff = min(start, et_midnight_utc(et_date(start)))
    snap = F.snapshot(inj, start)
    stamp = slot_stamp(inj, start)
    PA.assert_pretip([stamp, cutoff], start, timedelta(0) if stamp is None else F.LEAD) if stamp else PA.assert_pretip([cutoff], start, timedelta(0))
    out = []
    for pid, nm in F._team_candidates(fb, team, cutoff).items():
        if F._recent(fb, pid, team, cutoff) is None:
            continue
        r = fb.row(pid, team, opp, home, season, start, start)
        if r is None:
            continue
        st = PA.NO_REPORT if snap is None else (F.status_of(snap, nm) or PA.UNLISTED)
        out.append((pid, nm, dict(r["features"]), st))
    return out, stamp


def leakage_test(games, stores, fb_full, inj, n_sample=6):
    """Rebuild from truncated data; the pre-tip inputs must be identical to the full build's."""
    rng = np.random.default_rng(SEED)
    recs = [(gid, rec) for st in stores for gid, rec in st["games"].items() if rec["start_time_utc"][:4] == "2026" or rec["start_time_utc"][:4] == "2027"]
    gmap = {g["game_id"]: g for g in games}
    recs = [(gid, rec) for gid, rec in recs if gid in gmap and gmap[gid]["season_type"] == 2]
    pick = [recs[i] for i in rng.choice(len(recs), size=min(n_sample, len(recs)), replace=False)]
    for gid, rec in pick:
        g, start = gmap[gid], _dt(rec["start_time_utc"])
        cutoff = min(start, et_midnight_utc(et_date(start)))
        keep = {k for st in stores for k, v in st["games"].items() if _dt(v["start_time_utc"]) < cutoff}
        t_games = [x for x in games if x["game_id"] in keep]
        t_stores = [{**st, "games": {k: v for k, v in st["games"].items() if k in keep}} for st in stores]
        fb_t = PlayerFeatureBuilder(t_games, t_stores)
        for team, home in ((g["home"], True), (g["away"], False)):
            opp = g["away"] if home else g["home"]
            a, sa = pretip(fb_full, inj, rec, gid, team, opp, home, g["season"])
            b, sb = pretip(fb_t, inj, rec, gid, team, opp, home, g["season"])
            assert sa == sb and [(x[0], x[3]) for x in a] == [(x[0], x[3]) for x in b], "candidate set/status differs when rebuilt pre-tip: LEAK"
            for x, y in zip(a, b):
                assert all(abs(x[2][k] - y[2][k]) < 1e-9 for k in FEATURE_NAMES), "feature differs when rebuilt pre-tip: LEAK"
    return len(pick)


def main(espn_raw, nba_raw, out):
    espn_raw, nba_raw = Path(espn_raw), Path(nba_raw)
    games, stores = load_all(espn_raw)
    fb = PlayerFeatureBuilder(games, stores)
    gmap = {g["game_id"]: g for g in games}
    inj = F.load_inj(SP.INJ)
    n_leak = leakage_test(games, stores, fb, inj)
    print("leakage test passed on", n_leak, "games", flush=True)
    rows = F.build_frame(espn_raw, SP.INJ)
    rec_of = {gid: rec for st in stores for gid, rec in st["games"].items()}
    meta, gscore = {}, {}
    for s in SEASONS:
        gm = N.load_season(s, espn_raw)["games"]
        for gid, rec in P.load_players(s, espn_raw)["games"].items():
            if gid not in gm:
                continue
            gscore[gid] = (str(et_date(_dt(rec["start_time_utc"]))), gm[gid]["home_score"], gm[gid]["away_score"])
            for r in rec["rows"]:
                meta[(gid, r["player_id"])] = (r["team"], r["home"])
    tg = SP.SA.load(str(nba_raw))
    tg = tg[tg["season_type"] == "regular-season"]
    sch = pd.concat([pd.read_parquet(f) for f in sorted((nba_raw / "schedule").glob("*.parquet"))], ignore_index=True)
    sch = sch[sch.season_type == "regular-season"].drop_duplicates("game_id")
    key2nba = {(str(r.game_date)[:10], int(r.home_pts), int(r.away_pts)): str(r.game_id) for r in sch.itertuples() if r.home_pts == r.home_pts}
    rows = [r for r in rows if r["game_id"] in gscore]
    for r in rows:
        r["team"], r["home"] = meta[(r["game_id"], r["player_id"])]
    cand_cache = {}

    def cands(gid, team, home):
        k = (gid, team)
        if k not in cand_cache:
            g = gmap[gid]
            opp = g["away"] if home else g["home"]
            cand_cache[k] = pretip(fb, inj, rec_of[gid], gid, team, opp, home, g["season"])[0]
        return cand_cache[k]

    allr, shapes = [], {}
    for T, (tr, ca) in SP.FOLDS.items():
        eng, sd_team, K = SP.engine_means(tg, T)
        R_ = lambda ss: [r for r in rows if r["season"] in ss]  # noqa: E731
        trr, car, ter = R_(tr), R_((ca,)), R_((T,))
        X = lambda rs: np.array([[r[k] for k in FEATURE_NAMES] for r in rs], float)  # noqa: E731
        y = lambda rs: np.array([r["points"] for r in rs], float)  # noqa: E731
        b0, w, mu, sd = ridge(X(trr), y(trr))
        mean_x = lambda M: np.maximum(b0 + ((M - mu) / sd) @ w, 0.5)  # noqa: E731
        for rs in (trr, car, ter):
            for r, m in zip(rs, mean_x(X(rs))):
                r["mu"] = float(m)
        # play rates: training seasons, candidates' status vs whether they appeared (label only, never an input to a prediction)
        sts, pl = [], []
        seen_tg = {(r["game_id"], r["team"], r["home"]) for r in trr}
        for gid, team, home in seen_tg:
            appeared = {x["player_id"] for x in rec_of[gid]["rows"] if not x["dnp"] and x["team"] == team}
            for pid, nm, f, st in cands(gid, team, home):
                sts.append(st)
                pl.append(1 if pid in appeared else 0)
        rates = PA.fit_play_rates(sts, pl)
        # candidate means, ridge from the same features
        for r in car + ter:
            cands(r["game_id"], r["team"], r["home"])  # populate pre-tip candidates for calibration and test games
        cmu = {}
        for (gid, team), lst in list(cand_cache.items()):
            if gscore.get(gid) is None:
                continue
            for pid, nm, f, st in lst:
                cmu[(gid, team, pid)] = float(mean_x(np.array([[f[k] for k in FEATURE_NAMES]], float))[0])
        sums, hist = {}, {}
        for r in trr + car + ter:
            sums[(r["game_id"], r["team"])] = sums.get((r["game_id"], r["team"]), 0.0) + r["mu"]
        for (gid, tm), v in sorted(sums.items(), key=lambda kv: (gscore[kv[0][0]][0], kv[0][0])):
            hist.setdefault(tm, []).append((gid, v))
        Dprev = {(gid, tm): float(np.mean([x[1] for x in lst[i - 10:i]])) for tm, lst in hist.items() for i, (gid, _) in enumerate(lst) if i >= 10}
        mc, yc = np.array([r["mu"] for r in car]), y(car)
        grid = np.exp(np.linspace(np.log(0.5), np.log(200), 60))
        r_hat = float(grid[int(np.argmax([nb_loglik(yc, mc, r) for r in grid]))])
        xs, ys = [], []
        for k in STRIKES:
            xs += [logit(nb_sf(k, m, r_hat)) for m in mc]
            ys += [1.0 if p >= k else 0.0 for p in yc]
        a_b, b_b = platt(np.array(xs), np.array(ys))

        def team_games(rs):
            d = {}
            for r in rs:
                d.setdefault((r["game_id"], r["team"]), []).append(r)
            return d

        def team_pts(gid, home):
            return gscore[gid][1] if home else gscore[gid][2]
        rest = float(np.mean([1 - sum(x["points"] for x in v) / team_pts(g, v[0]["home"]) for (g, _), v in team_games(trr).items()]))

        def share(arm, x, gid, tm):
            if arm == "engine_pt":
                if (gid, tm) not in Dprev:
                    return None
                return min(x["mu"] * (1 - rest) / Dprev[(gid, tm)], 0.95)
            oth = [(cmu[(gid, tm, pid)], rates.get(st, rates[PA.UNLISTED])) for pid, nm, f, st in cands(gid, tm, x["home"]) if pid != x["player_id"] and (gid, tm, pid) in cmu]
            return PA.conditional_shares(x["mu"], [o[0] for o in oth], [o[1] for o in oth], rest)

        def raw_probs(rs, arm, conc, rng):
            res = {}
            for (gid, tm), v in team_games(rs).items():
                nid = key2nba.get((gscore[gid][0], int(gscore[gid][1]), int(gscore[gid][2])))
                if nid is None or nid not in eng:
                    continue
                home = v[0]["home"]
                Tpts = np.maximum(np.rint(eng[nid][0 if home else 1] + sd_team * rng.standard_normal(NSIM)), 40).astype(int)
                for x in v:
                    sj = share(arm, x, gid, tm)
                    if sj is None:
                        continue
                    pts = rng.binomial(Tpts, rng.beta(conc * sj, conc * (1 - sj), NSIM))
                    res[(gid, x["player_id"])] = [PL.p_at_least(pts, k) for k in STRIKES]
            return res
        rng = np.random.default_rng(SEED + T)
        preds = {}
        for arm in ("engine_pt", "engine_set"):
            ok = [(r, share(arm, r, r["game_id"], r["team"])) for r in car]
            ok = [(r, s) for r, s in ok if s is not None]
            conc = PL.fit_concentration(np.array([r["points"] for r, _ in ok]), np.array([team_pts(r["game_id"], r["home"]) for r, _ in ok]), np.array([s for _, s in ok]))
            pc = raw_probs(car, arm, conc, rng)
            kc = [r for r in car if (r["game_id"], r["player_id"]) in pc]
            a_e, b_e = platt(np.array([logit(pc[(r["game_id"], r["player_id"])][i]) for r in kc for i in range(len(STRIKES))]),
                             np.array([1.0 if r["points"] >= k else 0.0 for r in kc for k in STRIKES]))
            preds[arm] = (raw_probs(ter, arm, conc, rng), a_e, b_e, conc)
        shapes[T] = dict(K=K, sd_team=sd_team, rest_share=rest, n_test_rows=len(ter), n_rows={a: len(preds[a][0]) for a in preds},
                         conc={a: preds[a][3] for a in preds}, play_rates={k: round(v, 3) for k, v in rates.items()}, r_hat=r_hat)
        for r in ter:
            q = (r["game_id"], r["player_id"])
            if q not in preds["engine_pt"][0] or q not in preds["engine_set"][0]:
                continue
            for i, k in enumerate(STRIKES):
                sg = lambda a, z: 1 / (1 + np.exp(-(preds[a][1] * logit(preds[a][0][q][i]) + preds[a][2])))  # noqa: E731
                pb = 1 / (1 + np.exp(-(a_b * logit(nb_sf(k, r["mu"], r_hat)) + b_b)))
                allr.append((T, r["game_id"], k, int(r["pts10"] >= 15), 1.0 if r["points"] >= k else 0.0, pb, sg("engine_pt", 0), sg("engine_set", 0)))
        print(T, shapes[T], flush=True)
    d = pd.DataFrame(allr, columns=["season", "game_id", "k", "star", "y", "pb", "pp", "ps"])
    for c in ("pb", "pp", "ps"):
        d["b_" + c] = (d[c] - d.y) ** 2
    d.to_csv(safe_out(HERE.parent / (out[: -len(".json")] + "_rows.csv.gz")), index=False)
    rng = np.random.default_rng(SEED)
    contrasts = {"set_minus_base": ("b_ps", "b_pb"), "set_minus_pt": ("b_ps", "b_pp"), "pt_minus_base": ("b_pp", "b_pb")}
    res = {}
    for scope, sub in (("pooled", d), ("2025", d[d.season == 2025]), ("2026", d[d.season == 2026])):
        for sname, s in (("all", sub), ("star", sub[sub.star == 1])):
            for kk in ("ALL", *STRIKES):
                z = s if kk == "ALL" else s[s.k == kk]
                e = {"brier": {c: float(z["b_" + c].mean()) for c in ("pb", "pp", "ps")}}
                for name, (a, b) in contrasts.items():
                    e[name] = SP.boot((z[a] - z[b]).to_numpy(), z.game_id.to_numpy(), rng)
                res[f"{scope}|{sname}|{kk}"] = e
    safe_out(HERE.parent / out).write_text(json.dumps(dict(results=res, shapes=shapes, leakage_test_games=n_leak), indent=1, default=float))
    for kname, e in res.items():
        if kname.startswith("pooled|all"):
            print(kname, {n: (round(e[n]["delta"], 5), [round(x, 5) for x in e[n]["ci95"]]) for n in contrasts}, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

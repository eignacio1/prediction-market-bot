"""W126.2 EXP-047-C2, exactly as PREREG_C2.md. Usage: run_c2.py fit|judge <NBA_EVENTS root> <out dir inside 12_EXPLORATORY/nba_props_role>
fit   : fit season 2022-23 only (game dates 2022-08-01..2023-07-31) -> FIT_C2.json (lambdas, frozen into the forecaster before judge).
judge : judged season 2023-24 (2023-08-01..2024-07-31) -> RESULT_C2.json. Refuses to run unless FIT_C2.json equals the forecaster's LAMBDA."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_retro as R  # noqa: E402  (same loader, ladder, bootstrap, BH as C1)
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_availability as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.nba_engine import props as P  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_c1_forecaster as C1  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F  # noqa: E402

W = R.W
WINDOWS = {"fit": ("2022-08-01", "2023-07-31"), "judge": ("2023-08-01", "2024-07-31")}
COL = {"points": "points", "rebounds": "rebounds_total", "assists": "assists", "threes": "three_pointers_made"}
BOOT = R.BOOT


def att_rows(pb_s, reg):
    """{(team, name): [(date, 3PA)]} for one season, same players/dates as build_season."""
    out = {}
    for gid, g in pb_s.groupby("game_id"):
        d = str(reg.loc[gid, "game_date"])[:10]
        for row in g[g.m > 0].itertuples():
            out.setdefault((row.team_tricode, row.name), []).append((d, float(row.three_pointers_attempted)))
    return out


def season_inputs(reg, pb, lo, hi):
    gids = [g for g in reg.index if lo <= str(reg.loc[g, "game_date"])[:10] <= hi]
    pb_s = pb[pb.game_id.isin(gids)]
    games, pl = R.build_season(reg, pb_s)
    return pb_s, games, pl, att_rows(pb_s, reg)


def team_games(games, tips, inj, fc0, nodata):
    """Yield (gid, g, team, ros, onames) for each team-game with a usable pre-tip report and >= 5 rotation players."""
    for gid in sorted(games, key=lambda g: games[g]["date"]):
        g = games[gid]
        tip = tips.loc[gid, "tip_earliest"]
        day = tip.tz_convert(A.ET).date()
        ts, rep = A.last_report_before_tip(inj.get(day, {}), day, tip.to_pydatetime(), R.LEAD_MIN)
        nodata["games"] += 1
        if ts is None:
            nodata["no_report"] += 1
            continue
        outs = {n for n, st in rep.items() if st == "Out"}
        for team in (g["home"], g["away"]):
            ros = fc0.roster(team, g["date"])
            if len(ros) >= 5:
                yield gid, g, team, ros, {norm_name(n) for _, n, _ in ros} & outs


def fit(root, out):
    reg, tips, pb = R.load(root)
    inj = W.load_inj()
    pb_s, games, pl, att = season_inputs(reg, pb, *WINDOWS["fit"])
    fc0 = F.NBAEngineProps(games, pl, {})
    actual = {(g, n): r for g, gg in pb_s[pb_s.m > 0].groupby("game_id") for n, r in
              zip(gg["name"], gg[["points", "rebounds_total", "assists", "three_pointers_made", "three_pointers_attempted"]].to_dict("records"))}
    nodata = dict(no_report=0, games=0)
    rec = {s: [] for s in ("rebounds", "assists", "threes")}      # threes = 3PA basis here
    for gid, g, team, ros, onames in team_games(games, tips, inj, fc0, nodata):
        prior = {"rebounds": [r[2]["rebounds"] for r in ros], "assists": [r[2]["assists"] for r in ros]}
        pa = [fc_att(att, team, n, g["date"]) for _, n, _ in ros]
        prior["threes"] = pa
        for s in rec:
            col = {"rebounds": "rebounds_total", "assists": "assists", "threes": "three_pointers_attempted"}[s]
            w_act = a_tot = vac = 0.0
            ok = True
            for i, (_, n, _) in enumerate(ros):
                w = prior[s][i]
                if w is None:
                    ok = False
                    break
                if norm_name(n) in onames:
                    vac += w
                else:
                    r = actual.get((gid, n))
                    if r is not None:
                        w_act += w
                        a_tot += r[col]
            if ok:
                rec[s].append((gid, a_tot - w_act, vac, bool(onames)))
    res = {"window": WINDOWS["fit"], "nodata": nodata, "stats": {}}
    rng = np.random.default_rng(126002)
    for s, rows in rec.items():
        df = pd.DataFrame(rows, columns=["gid", "e", "vac", "has_out"])
        b0 = float(df[~df.has_out].e.mean())
        v = df[df.has_out & (df.vac > 0)].copy()
        v["ec"] = v.e - b0
        lam_raw = float((v.ec * v.vac).sum() / (v.vac ** 2).sum())
        gs = v.groupby("gid").apply(lambda x: pd.Series({"a": (x.ec * x.vac).sum(), "b": (x.vac ** 2).sum()}), include_groups=False)
        idx = rng.integers(0, len(gs), size=(BOOT, len(gs)))
        m = gs.a.to_numpy()[idx].sum(1) / gs.b.to_numpy()[idx].sum(1)
        res["stats"][s] = dict(b0=b0, n_baseline=int((~df.has_out).sum()), n_v_games=int(len(v)), lam_raw=lam_raw,
                               lam=round(min(max(lam_raw, 0.0), 1.0), 2), ci95=[float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))])
    safe_out(out / "FIT_C2.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps(res, indent=1))


def fc_att(att, team, name, before):
    v = [a for d, a in att.get((team, name), ()) if d < before]
    return float(np.mean(v)) if v else None


def judge(root, out):
    fit_j = json.loads((HERE / "FIT_C2.json").read_text())
    lam = {"rebounds": fit_j["stats"]["rebounds"]["lam"], "assists": fit_j["stats"]["assists"]["lam"], "threes": fit_j["stats"]["threes"]["lam"]}
    assert lam == C2.LAMBDA, f"frozen lambdas {C2.LAMBDA} != FIT_C2.json {lam}: freeze before judging"
    reg, tips, pb = R.load(root)
    inj = W.load_inj()
    pb_s, games, pl, att = season_inputs(reg, pb, *WINDOWS["judge"])
    fc0 = F.NBAEngineProps(games, pl, {})
    fc1 = C1.NBAEnginePropsC1(games, pl, {}, lambda p, t: ())
    fc2 = C2.NBAEnginePropsC2(games, pl, {}, lambda p, t: (), att)
    actual = {(g, n): r for g, gg in pb_s[pb_s.m > 0].groupby("game_id") for n, r in
              zip(gg["name"], gg[["points", "rebounds_total", "assists", "three_pointers_made"]].to_dict("records"))}
    nodata = dict(no_report=0, games=0, dnp_excluded=0)
    rows = []
    for gid, g, team, ros, onames in team_games(games, tips, inj, fc0, nodata):
        if not onames:
            continue
        p = dict(game_date=g["date"], home=g["home"], away=g["away"], team=team)
        mu_pts = np.array([r[2]["points"] for r in ros])
        V = float(sum(r[2]["points"] for r in ros if norm_name(r[1]) in onames) / mu_pts.sum())
        for stat in P.STATS:
            d0 = R.draws_for(fc0, {**p, "stat": stat}, ros, stat, ())
            fc1._out = frozenset(onames)
            d1 = R.draws_for(fc1, {**p, "stat": stat}, ros, stat, onames)
            fc2._out = frozenset(onames)
            d2 = R.draws_for(fc2, {**p, "stat": stat}, ros, stat, onames)
            for i, (_, n, _) in enumerate(ros):
                if norm_name(n) in onames:
                    continue
                a = actual.get((gid, n))
                if a is None:
                    nodata["dnp_excluded"] += 1
                    continue
                y = a[COL[stat]]
                for k in R.LADDER[stat]:
                    q = [min(max(P.strike_probs(d[:, i], [k])[k], 1e-4), 1 - 1e-4) for d in (d0, d1, d2)]
                    rows.append((gid, g["date"], team, n, stat, k, int(y >= k), q[0], q[1], q[2], V))
    df = pd.DataFrame(rows, columns=["game_id", "date", "team", "player", "stat", "k", "y", "p0", "p1", "p2", "V"])
    ll = lambda p, y: -(y * np.log(p) + (1 - y) * np.log(1 - p))
    df["d"] = ll(df.p2, df.y) - ll(df.p0, df.y)          # C2 - EXP-047 (verdict)
    df["dc"] = ll(df.p2, df.y) - ll(df.p1, df.y)         # C2 - C1 (secondary)
    df["b0"], df["b2"] = (df.p0 - df.y) ** 2, (df.p2 - df.y) ** 2
    rng = np.random.default_rng(126002)
    res = {"lambda": lam, "window": WINDOWS["judge"], "judged_rows": int(len(df)), "judged_games": int(df.game_id.nunique()),
           "nodata": nodata, "stats": {}, "buckets": {}}
    pv = {}
    for stat in P.STATS:
        x = df[df.stat == stat]
        if x.empty:
            continue
        gs = x.groupby("game_id").agg(s=("d", "sum"), c=("d", "size"))
        mean, ci, m = R.boot(gs.s.to_numpy(), gs.c.to_numpy(), rng)
        gc = x.groupby("game_id").agg(s=("dc", "sum"), c=("dc", "size"))
        cm, cci, _ = R.boot(gc.s.to_numpy(), gc.c.to_numpy(), rng)
        p2 = max(2 * min((m <= 0).mean(), (m >= 0).mean()), 1.0 / (BOOT + 1))
        pv[stat] = p2
        res["stats"][stat] = dict(n_rows=int(len(x)), n_games=int(len(gs)), ll_diff=mean, ci95=ci, p=p2,
                                  verdict="improves" if ci[1] < 0 else ("worse" if ci[0] > 0 else "indeterminate"),
                                  vs_c1_ll_diff=cm, vs_c1_ci95=cci, brier_diff=float((x.b2 - x.b0).mean()),
                                  ll_base=float(ll(x.p0, x.y).mean()), ll_c2=float(ll(x.p2, x.y).mean()))
        for lo, hi, lab in R.BUCKETS:
            xb = x[(x.V >= lo) & (x.V < hi)]
            if len(xb) >= 50:
                gb = xb.groupby("game_id").agg(s=("d", "sum"), c=("d", "size"))
                bm, bci, _ = R.boot(gb.s.to_numpy(), gb.c.to_numpy(), rng)
                res["buckets"][f"{stat}|{lab}"] = dict(n_rows=int(len(xb)), n_games=int(len(gb)), ll_diff=bm, ci95=bci)
    order = sorted(pv, key=pv.get)
    mk, passed = len(order), set()
    for r_, st in enumerate(order, 1):
        if pv[st] <= 0.10 * r_ / mk:
            passed = set(order[:r_])
    for st in res["stats"]:
        res["stats"][st]["bh_significant"] = st in passed
    imp = [s for s, v in res["stats"].items() if v["verdict"] == "improves" and v["bh_significant"]]
    wor = [s for s, v in res["stats"].items() if v["verdict"] == "worse"]
    res["verdict"] = "SUPPORTED" if imp and not wor else ("REFUTED" if wor and not imp else "INDETERMINATE")
    safe_out(out / "RESULT_C2.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps(res["stats"], indent=1), res["verdict"])


if __name__ == "__main__":
    mode, root, out = sys.argv[1], Path(sys.argv[2]), safe_out(HERE / sys.argv[3])
    (fit if mode == "fit" else judge)(root, out)

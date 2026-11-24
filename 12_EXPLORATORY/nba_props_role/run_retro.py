"""W125.4 Part C: EXP-047-C1 retrospective, exactly as 12_EXPLORATORY/nba_props_role/PREREG.md (frozen at 437975c).
Usage: run_retro.py <NBA_EVENTS root> <out dir inside 12_EXPLORATORY/nba_props_role>"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_availability"))
sys.path.insert(0, str(HERE.parent))
import run_w93_1 as W  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_availability as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402
from prediction_market_bot.nba_engine import props as P  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_c1_forecaster as C1  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F  # noqa: E402

LADDER = {"points": (10, 15, 20, 25, 30), "rebounds": (4, 6, 8, 10, 12), "assists": (2, 4, 6, 8, 10), "threes": (1, 2, 3, 4)}
JUDGE_FROM = "2024-10-01"
BUCKETS = ((0.0, 0.10, "V<0.10"), (0.10, 0.25, "0.10-0.25"), (0.25, 9.0, "V>=0.25"))
BOOT, LEAD_MIN = 10000, 240.0


def mins(v):
    if isinstance(v, str) and ":" in v:
        a, b = v.split(":")[:2]
        return float(a) + float(b) / 60
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def season_of(d: str) -> int:
    return int(d[:4]) if int(d[5:7]) >= 8 else int(d[:4]) - 1


def load(root: Path):
    rd = W.rd
    sch, espn, pb = rd(root, "schedule"), rd(root, "espn_schedule"), rd(root, "player_box")
    sch["game_id"] = sch["game_id"].astype(str)
    tips = tip_table(sch, espn)
    reg = sch[sch.season_type == "regular-season"].drop_duplicates("game_id").set_index("game_id")
    pb = pb.assign(game_id=pb.game_id.astype(str))
    pb = pb[pb.game_id.isin(reg.index)].copy()
    pb["m"] = pb["minutes"].map(mins)
    pb["name"] = (pb.first_name.fillna("") + " " + pb.family_name.fillna("")).str.strip()
    return reg, tips, pb


def build_season(reg, pb_s):
    games, pl = {}, {}
    for gid, g in pb_s.groupby("game_id"):
        r = reg.loc[gid]
        d = str(r["game_date"])[:10]
        side = {s: gg for s, gg in g.groupby("side")}
        if "home" not in side or "away" not in side:
            continue
        home, away = side["home"].team_tricode.iloc[0], side["away"].team_tricode.iloc[0]
        games[gid] = dict(date=d, home=home, away=away, pts={home: float(r["home_pts"]), away: float(r["away_pts"])}, teams={})
        for code, gg in ((home, side["home"]), (away, side["away"])):
            for row in gg[gg.m > 0].itertuples():
                pl.setdefault((code, row.name), []).append((d, dict(
                    min=row.m, points=float(row.points), rebounds=float(row.rebounds_total), assists=float(row.assists),
                    threes=float(row.three_pointers_made))))
    return games, pl


def draws_for(fc, p, ros, stat, out):
    """Same path as NBAEngineProps.forecast: shared engine draws, sha-keyed seed, EXP-047 constants."""
    import hashlib
    h, a = fc._game_draws(p)
    pts = h if p["team"] == p["home"] else a
    fc._out = frozenset(out) if hasattr(fc, "_out") else None
    R = P.TeamRoster(tuple(n for _, n, _ in ros), fc._mu(ros, p), float(pts.mean()))
    key = (p["game_date"], p["home"], p["away"], p["team"], p["stat"])
    seed = int(hashlib.sha256("|".join(key).encode()).hexdigest()[:8], 16) % 99991
    kw = {"rest": {**P.DEFAULT_REST, "points": F.POINTS_REST}} if stat == "points" else {}
    return P.player_draws(pts, R, stat, np.random.default_rng(seed), **kw)[0]


def boot(dsum, dcnt, rng):
    g = len(dsum)
    idx = rng.integers(0, g, size=(BOOT, g))
    m = dsum[idx].sum(1) / dcnt[idx].sum(1)
    return float(dsum.sum() / dcnt.sum()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], m


def main(root, out):
    root, out = Path(root), safe_out(HERE / out)
    reg, tips, pb = load(root)
    inj = W.load_inj()
    rows, diag, nodata = [], [], dict(no_report=0, games=0, dnp_excluded=0, name_unmatched=0)
    for s in sorted({season_of(str(d)[:10]) for d in reg.game_date}):
        if s < 2022:
            continue
        gids = [g for g in reg.index if season_of(str(reg.loc[g, "game_date"])[:10]) == s]
        pb_s = pb[pb.game_id.isin(gids)]
        games, pl = build_season(reg, pb_s)
        fc0 = F.NBAEngineProps(games, pl, {})
        fc1 = C1.NBAEnginePropsC1(games, pl, {}, lambda p, t: ())
        actual = {(g, n): r for g, gg in pb_s[pb_s.m > 0].groupby("game_id") for n, r in
                  zip(gg["name"], gg[["points", "rebounds_total", "assists", "three_pointers_made"]].to_dict("records"))}
        for gid in sorted(games, key=lambda g: games[g]["date"]):
            g = games[gid]
            tip = tips.loc[gid, "tip_earliest"]
            day = tip.tz_convert(A.ET).date()
            ts, rep = A.last_report_before_tip(inj.get(day, {}), day, tip.to_pydatetime(), LEAD_MIN)
            nodata["games"] += 1
            if ts is None:
                nodata["no_report"] += 1
                continue
            outs = {n for n, st in rep.items() if st == "Out"}
            for team in (g["home"], g["away"]):
                p = dict(game_date=g["date"], home=g["home"], away=g["away"], team=team)
                ros = fc0.roster(team, g["date"])
                if len(ros) < 5:
                    continue
                onames = {norm_name(n) for _, n, _ in ros} & outs
                # diagnostics (all seasons): did a listed-Out rotation player play?
                for _, n, _ in ros:
                    if norm_name(n) in outs:
                        diag.append(dict(season=s, played=int((gid, n) in actual)))
                if not onames:
                    continue
                mu_pts = np.array([r[2]["points"] for r in ros])
                V = float(sum(r[2]["points"] for r in ros if norm_name(r[1]) in onames) / mu_pts.sum())
                for stat in P.STATS:
                    d0 = draws_for(fc0, {**p, "stat": stat}, ros, stat, ())
                    fc1._out = frozenset(onames)
                    d1 = draws_for(fc1, {**p, "stat": stat}, ros, stat, onames)
                    for i, (_, n, _) in enumerate(ros):
                        if norm_name(n) in onames:
                            continue
                        a = actual.get((gid, n))
                        if a is None:
                            nodata["dnp_excluded"] += 1
                            continue
                        y = a[{"points": "points", "rebounds": "rebounds_total", "assists": "assists", "threes": "three_pointers_made"}[stat]]
                        for k in LADDER[stat]:
                            q0 = min(max(P.strike_probs(d0[:, i], [k])[k], 1e-4), 1 - 1e-4)
                            q1 = min(max(P.strike_probs(d1[:, i], [k])[k], 1e-4), 1 - 1e-4)
                            rows.append((s, gid, g["date"], team, n, stat, k, int(y >= k), q0, q1, V))
        print("season", s, "rows", len(rows), flush=True)
    df = pd.DataFrame(rows, columns=["season", "game_id", "date", "team", "player", "stat", "k", "y", "p0", "p1", "V"])
    ll = lambda p, y: -(y * np.log(p) + (1 - y) * np.log(1 - p))
    df["d"] = ll(df.p1, df.y) - ll(df.p0, df.y)
    df["b0"], df["b1"] = (df.p0 - df.y) ** 2, (df.p1 - df.y) ** 2
    jd = df[df.date >= JUDGE_FROM]
    rng = np.random.default_rng(125004)
    res = {"judged_rows": int(len(jd)), "judged_games": int(jd.game_id.nunique()), "nodata": nodata, "stats": {}, "buckets": {}}
    pv = {}
    for stat in P.STATS:
        x = jd[jd.stat == stat]
        if x.empty:
            continue
        gs = x.groupby("game_id").agg(s=("d", "sum"), c=("d", "size"))
        mean, ci, m = boot(gs.s.to_numpy(), gs.c.to_numpy(), rng)
        p2 = max(2 * min((m <= 0).mean(), (m >= 0).mean()), 1.0 / (BOOT + 1))
        pv[stat] = p2
        verdict = "improves" if ci[1] < 0 else ("worse" if ci[0] > 0 else "indeterminate")
        res["stats"][stat] = dict(n_rows=int(len(x)), n_games=int(len(gs)), ll_diff=mean, ci95=ci, p=p2, verdict=verdict,
                                  brier_diff=float((x.b1 - x.b0).mean()), ll_base=float(ll(x.p0, x.y).mean()), ll_c1=float(ll(x.p1, x.y).mean()))
        for lo, hi, lab in BUCKETS:
            xb = x[(x.V >= lo) & (x.V < hi)]
            if len(xb) >= 50:
                gb = xb.groupby("game_id").agg(s=("d", "sum"), c=("d", "size"))
                bm, bci, _ = boot(gb.s.to_numpy(), gb.c.to_numpy(), rng)
                res["buckets"][f"{stat}|{lab}"] = dict(n_rows=int(len(xb)), n_games=int(len(gb)), ll_diff=bm, ci95=bci)
    order = sorted(pv, key=pv.get)                       # Benjamini-Hochberg q = 0.10
    mk, passed = len(order), set()
    for r_, st in enumerate(order, 1):
        if pv[st] <= 0.10 * r_ / mk:
            passed = set(order[:r_])
    for st in res["stats"]:
        res["stats"][st]["bh_significant"] = st in passed
    imp = [s for s, v in res["stats"].items() if v["verdict"] == "improves" and v["bh_significant"]]
    wor = [s for s, v in res["stats"].items() if v["verdict"] == "worse"]
    res["verdict"] = "SUPPORTED" if imp and not wor else ("REFUTED" if wor and not imp else "INDETERMINATE")
    dg = pd.DataFrame(diag)
    res["out_reliability"] = {int(s): dict(n=int(len(g)), p_played=float(g.played.mean())) for s, g in dg.groupby("season")} if len(dg) else {}
    safe_out(out / "RESULT.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps(res["stats"], indent=1), res["verdict"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

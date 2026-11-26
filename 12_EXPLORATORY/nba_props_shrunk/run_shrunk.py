"""W129.2 EXP-047-S judged read, exactly as PREREG.md. Usage: run_shrunk.py --final <NBA_EVENTS root>
Judged: 2025-26 regular season. Control NBAEnginePropsC2 as logged; challenger NBAEnginePropsShrunk. One run; --final required."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_props_role"))
sys.path.insert(0, str(HERE.parent))
import run_retro as R  # noqa: E402
import run_c2 as RC  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.nba_engine import props as P  # noqa: E402
from prediction_market_bot.nba_engine import shrunk_means as S  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_shrunk_forecaster as SF  # noqa: E402
from prediction_market_bot.quant.inference import mde_paired  # noqa: E402

W = R.W
JUDGE = ("2025-08-01", "2026-07-31")
PREV = ("2024-08-01", "2025-07-31")
B, SEED, Q = 2000, 20261121, 0.10
COL = RC.COL
STRATA = ((4, 10, "4-10"), (11, 30, "11-30"), (31, 10 ** 6, "31+"))
ARMS = ("c2", "shrunk", "rate_only", "minutes_only")


def prev_table(pb_prev) -> dict:
    t: dict = {}
    for r in pb_prev[pb_prev.m > 0].itertuples():
        a = t.setdefault(norm_name(r.name), dict(min=0.0, games=0.0, points=0.0, rebounds=0.0, assists=0.0, threes=0.0))
        a["min"] += r.m; a["games"] += 1.0; a["points"] += r.points; a["rebounds"] += r.rebounds_total
        a["assists"] += r.assists; a["threes"] += r.three_pointers_made
    return t


def ll(p, y):
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(df, col, rng):
    gs = df.groupby("game_id").agg(s=(col, "sum"), c=(col, "size"))
    s, c = gs.s.to_numpy(), gs.c.to_numpy()
    idx = rng.integers(0, len(gs), size=(B, len(gs)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return dict(d=float(s.sum() / c.sum()), ci90=[float(np.percentile(m, 5)), float(np.percentile(m, 95))],
                p_le0=float(max((m <= 0).mean(), 1.0 / (B + 1))), n_rows=int(c.sum()), n_games=int(len(gs))), m


def main(root: Path) -> None:
    sha = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(HERE / "PREREG.md")], capture_output=True, text=True, cwd=HERE).stdout.strip()
    reg, tips, pb = R.load(root)
    inj = W.load_inj()
    prev = prev_table(pb[pb.game_id.isin([g for g in reg.index if PREV[0] <= str(reg.loc[g, "game_date"])[:10] <= PREV[1]])])
    league = S.league_band_rates(prev)
    pb_s, games, pl, att = RC.season_inputs(reg, pb, *JUDGE)
    fc0 = F.NBAEngineProps(games, pl, {})
    kw = dict(prev=prev, league=league)
    fcs = {"c2": C2.NBAEnginePropsC2(games, pl, {}, lambda p, t: (), att),
           "shrunk": SF.NBAEnginePropsShrunk(games, pl, {}, lambda p, t: (), att, **kw),
           "rate_only": SF.NBAEnginePropsShrunk(games, pl, {}, lambda p, t: (), att, k_min=0.0, **kw),
           "minutes_only": SF.NBAEnginePropsShrunk(games, pl, {}, lambda p, t: (), att, k={s: 0.0 for s in S.STATS}, **kw)}
    actual = {(g, n): r for g, gg in pb_s[pb_s.m > 0].groupby("game_id") for n, r in
              zip(gg["name"], gg[["points", "rebounds_total", "assists", "three_pointers_made"]].to_dict("records"))}
    nodata = dict(no_report=0, games=0, dnp_excluded=0, players_without_prev=0)
    rows = []
    for gid, g, team, ros, onames in RC.team_games(games, tips, inj, fc0, nodata):
        p = dict(game_date=g["date"], home=g["home"], away=g["away"], team=team)
        for stat in P.STATS:
            d = {}
            for a, fc in fcs.items():
                fc._out = frozenset(onames)
                d[a] = R.draws_for(fc, {**p, "stat": stat}, ros, stat, onames)
            for i, (_, n, _) in enumerate(ros):
                if norm_name(n) in onames:
                    continue
                act = actual.get((gid, n))
                if act is None:
                    nodata["dnp_excluded"] += 1
                    continue
                nprior = sum(1 for dd, _ in pl.get((team, n), ()) if dd < g["date"])
                y = act[COL[stat]]
                for k in R.LADDER[stat]:
                    q = {a: min(max(P.strike_probs(d[a][:, i], [k])[k], 1e-4), 1 - 1e-4) for a in ARMS}
                    rows.append((gid, g["date"], team, n, stat, k, int(y >= k), nprior, int(bool(onames)), *[q[a] for a in ARMS]))
    df = pd.DataFrame(rows, columns=["game_id", "date", "team", "player", "stat", "k", "y", "n", "has_out", *["p_" + a for a in ARMS]])
    df["d"] = ll(df.p_c2, df.y) - ll(df.p_shrunk, df.y)
    df["d_rate"] = ll(df.p_c2, df.y) - ll(df.p_rate_only, df.y)
    df["d_min"] = ll(df.p_c2, df.y) - ll(df.p_minutes_only, df.y)
    rng = np.random.default_rng(SEED)
    pooled, _ = boot(df, "d", rng)
    res = dict(prereg_sha=sha, judged=JUDGE, previous_season=PREV, nodata=nodata, judged_games=pooled["n_games"], pooled=pooled, stats={},
               strata={}, out_slice={}, decomposition={}, constants=dict(k=S.K, k_min=S.K_MIN), c2_lambda=C2.LAMBDA)
    pv = {}
    for st in P.STATS:
        x = df[df.stat == st]
        r, _ = boot(x, "d", rng)
        r["brier_diff"] = float(((x.p_c2 - x.y) ** 2 - (x.p_shrunk - x.y) ** 2).mean())
        r["ll_c2"], r["ll_shrunk"] = float(ll(x.p_c2, x.y).mean()), float(ll(x.p_shrunk, x.y).mean())
        res["stats"][st], pv[st] = r, r["p_le0"]
    order = sorted(pv, key=pv.get)
    passed = set()
    for rk, st in enumerate(order, 1):
        if pv[st] <= Q * rk / len(order):
            passed = set(order[:rk])
    for st in res["stats"]:
        res["stats"][st]["bh_q10"] = st in passed
    for lo, hi, lab in STRATA:
        x = df[(df.n >= lo) & (df.n <= hi)]
        if len(x):
            res["strata"][lab] = boot(x, "d", rng)[0]
    for lab, flag in (("with_out", 1), ("no_out", 0)):
        x = df[df.has_out == flag]
        if len(x):
            res["out_slice"][lab] = boot(x, "d", rng)[0]
    for lab, col in (("rate_only", "d_rate"), ("minutes_only", "d_min")):
        res["decomposition"][lab] = boot(df, col, rng)[0]
    pos = sum(1 for s in res["stats"].values() if s["d"] > 0)
    lo, hi = pooled["ci90"]
    res["n_stats_positive"] = pos
    res["verdict"] = ("SUPPORTED" if lo > 0 and pos >= 3 else "NOT SUPPORTED" if pooled["d"] <= 0 or pos < 3 else "UNDERPOWERED")
    sd = float(df.groupby("game_id").d.mean().std())
    res["power"] = dict(game_sd_of_mean_d=sd, mde_80=float(mde_paired(sd, pooled["n_games"])))
    out = safe_out(HERE / "results.json")
    out.write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps({k: res[k] for k in ("verdict", "pooled", "n_stats_positive", "power")}, indent=1))


if __name__ == "__main__":
    if "--final" not in sys.argv:
        raise SystemExit("judged read refused without --final (PREREG §6: the run happens once)")
    main(Path([a for a in sys.argv[1:] if a != "--final"][0]))

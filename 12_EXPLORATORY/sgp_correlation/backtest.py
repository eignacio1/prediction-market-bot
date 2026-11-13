"""W110.4 Part B: is the engine's same-game joint calibrated? Walk-forward, settled NBA regular-season games.

Inputs (public sportsdataverse files, scratch dir): player_boxscores_<season>.parquet, nba_schedule_<season>.parquet.
Engine: engine_v2 with FIXED league constants (same as W109.3, fitted on no tested game), team ratings from games dated
strictly before the game; player means from the player's prior games only; 4,000 draws per game; props by nba_engine/props.py.
Legs are defined from the engine's own draws (lines = the draw median, so no outcome data picks a line). A game is scored only
when both teams have >= 10 prior games. Players who did not play are dropped (the market would void the leg).
Usage: PYTHONPATH=src python3 backtest.py <data_dir> <season> <out_prefix> [old|joint] [params_json] [max_games] [skip_games]
W113.3: ``joint`` swaps the props layer for nba_engine/joint.py (shared latent); team scores, lines' selection, legs and pair
definitions are identical, so before -> after is the same games, same pairs, same seeds. Game-level rows go to <prefix>_games.csv.
"""
import collections, itertools, json, sys
import numpy as np, pandas as pd
from prediction_market_bot.nba_engine import engine_v2 as E2
from prediction_market_bot.nba_engine import props as P
from prediction_market_bot.nba_engine import joint as J
from prediction_market_bot.quant import sgp as S
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402

LEAGUE, N, MIN_PRIOR_TEAM = 114.0, 4000, 10
COMBO3 = []   # (game, type, p_joint, p_indep, y) 3-leg rows, filled by run()
PARAMS = E2.V2Params(hca=2.0, tbias=0.0, sd_margin=13.0, sd_total=19.0)
STAT_COL = {"points": "points", "rebounds": "rebounds_total", "assists": "assists", "threes": "three_pointers_made"}
TOP_LEGS, ROSTER_N = 3, 8


def mins(s):
    try:
        m, sec = str(s).split(":"); return float(m) + float(sec) / 60.0
    except Exception:
        return 0.0


def load(data_dir, season):
    sch = pd.read_parquet(f"{data_dir}/nba_schedule_{season}.parquet")
    sch = sch[sch.season_type == "regular-season"].copy()
    pb = pd.read_parquet(f"{data_dir}/player_boxscores_{season}.parquet")
    pb = pb[pb.game_id.isin(sch.game_id)].copy()
    pb["min"] = pb.minutes.map(mins)
    pb = pb[pb["min"] > 0]
    return sch.sort_values(["game_date", "game_id"]).reset_index(drop=True), pb


def run(data_dir, season, engine="old", jp=None, max_games=None, skip_games=0, n_draws=N):
    sch, pb = load(data_dir, season)
    box = {g: d for g, d in pb.groupby("game_id")}
    hist = collections.defaultdict(list)          # team -> [(date, pts_for, pts_against)]
    phist = collections.defaultdict(list)         # (team, pid) -> [(date, row-dict)]
    rows, grows, ngames, seen_games = [], [], 0, 0
    jp = jp or J.JointParams()
    for _, g in sch.iterrows():
        gid, date, H, A = g.game_id, g.game_date, g.home_team_abbreviation, g.away_team_abbreviation
        d = box.get(gid)
        if d is None or pd.isna(g.home_pts):
            continue
        scorable = len(hist[H]) >= MIN_PRIOR_TEAM and len(hist[A]) >= MIN_PRIOR_TEAM
        if scorable:
            seen_games += 1
        if scorable and seen_games > skip_games and (max_games is None or ngames < max_games):
            sh = lambda v: (sum(v) + 8 * LEAGUE) / (len(v) + 8)
            fH, aH = sh([x[1] for x in hist[H]]), sh([x[2] for x in hist[H]])
            fA, aA = sh([x[1] for x in hist[A]]), sh([x[2] for x in hist[A]])
            mu_h, mu_a = (fH + aA) / 2, (fA + aH) / 2
            mm, tt = E2.game_means(PARAMS, mu_h, mu_a)
            h, a = E2.simulate(PARAMS, mm, tt, n_draws, seed=int(gid) % 100003)
            marg, tot = h - a, h + a
            r_h, r_a = float(g.home_pts), float(g.away_pts)
            grows.append((gid, date, float(np.mean(marg >= 1)), int(r_h - r_a >= 1), float(np.mean(marg >= int(round(np.median(marg))))),
                          int(r_h - r_a >= int(round(np.median(marg)))), float(np.mean(tot >= int(round(np.median(tot))))),
                          int(r_h + r_a >= int(round(np.median(tot))))))
            legs = []   # (name, side, pid, stat, draw_bool, real_bool)
            m50, t50 = int(round(np.median(marg))), int(round(np.median(tot)))
            legs += [("ML", "H", None, None, marg >= 1, r_h - r_a >= 1),
                     ("WIN", "A", None, None, marg <= -1, r_a - r_h >= 1),
                     ("SPR", "H", None, None, marg >= m50, r_h - r_a >= m50),
                     ("TOT", None, None, None, tot >= t50, r_h + r_a >= t50),
                     ("TT", "H", None, None, h >= int(round(np.median(h))), r_h >= int(round(np.median(h)))),
                     ("TT", "A", None, None, a >= int(round(np.median(a))), r_a >= int(round(np.median(a))))]
            for side, team, pts in (("H", H, h), ("A", A, a)):
                ros = []
                for (tm, pid), hh in phist.items():
                    if tm == team and len(hh) >= 4 and np.mean([x["min"] for _, x in hh]) >= 10:
                        ros.append((np.mean([x["min"] for _, x in hh]), pid, {s: float(np.mean([x[STAT_COL[s]] for _, x in hh])) for s in P.STATS}))
                ros.sort(reverse=True); ros = ros[:ROSTER_N]
                if len(ros) < TOP_LEGS:
                    continue
                R = P.TeamRoster(tuple(str(p) for _, p, _ in ros), {s: [m[s] for _, _, m in ros] for s in P.STATS}, float(pts.mean()))
                rng = np.random.default_rng(int(gid) % 99991 + (7 if side == "A" else 0))
                played = d[d.team_tricode == team].set_index("person_id")
                if engine == "joint":
                    RJ = J.JointRoster(R.players, [m for m, _, _ in ros], R.mu, float(pts.mean()))
                    jd = J.simulate_team(pts, np.abs(marg), RJ, rng, jp)
                for stat in P.STATS:
                    dd = jd.stat[stat] if engine == "joint" else P.player_draws(pts, R, stat, rng)[0]
                    for i in range(TOP_LEGS):
                        pid = ros[i][1]
                        if pid not in played.index:
                            continue
                        line = max(1, int(np.median(dd[:, i])))
                        pm = float(np.mean(dd[:, i] >= line))
                        if not 0.15 <= pm <= 0.85:
                            continue
                        legs.append((stat, side, pid, stat, dd[:, i] >= line, float(played.loc[pid, STAT_COL[stat]]) >= line))
            for side_ in ("H", "A"):                      # W113.3 Part C: 3-leg same-game combos on one player
                own_win = legs[0] if side_ == "H" else legs[1]
                for pid_ in {l[2] for l in legs if l[2] is not None and l[1] == side_}:
                    by = {l[3]: l for l in legs if l[2] == pid_}
                    for nm3, parts in (("WIN + PTS + 3PM (same player)", [own_win, by.get("points"), by.get("threes")]),
                                       ("TOT + PTS + 3PM (same player)", [legs[3], by.get("points"), by.get("threes")]),
                                       ("PTS + REB + AST (same player)", [by.get("points"), by.get("rebounds"), by.get("assists")])):
                        if any(p_ is None for p_ in parts):
                            continue
                        allh = np.logical_and.reduce([p_[4] for p_ in parts])
                        pm_ = [(np.sum(p_[4]) + 0.5) / (n_draws + 1.0) for p_ in parts]
                        COMBO3.append((gid, nm3, (np.sum(allh) + 0.5) / (n_draws + 1.0), float(np.prod(pm_)), int(all(p_[5] for p_ in parts))))
            def kind(l): return l[0]
            def pairs():
                P_ = [l for l in legs if l[3] is not None]
                for l in legs:
                    if l[0] == "TOT":
                        yield "TOT x PTS", l, [x for x in P_ if x[3] == "points"]
                        yield "TOT x 3PM", l, [x for x in P_ if x[3] == "threes"]
                for ml, t, nm in ((legs[0], legs[4], "ML x TT"),):
                    yield nm, ml, [t]
                yield "ML x TOT", legs[0], [legs[3]]
                yield "SPR x TOT", legs[2], [legs[3]]
                for x in P_:
                    own_win = legs[0] if x[1] == "H" else legs[1]
                    own_tt = legs[4] if x[1] == "H" else legs[5]
                    if x[3] == "points":
                        yield "WIN x PTS", own_win, [x]
                        yield "TT x PTS (own)", own_tt, [x]
                    if x[3] == "rebounds":
                        yield "WIN x REB", own_win, [x]
                for x, y in itertools.combinations(P_, 2):
                    key = (x[3], y[3])
                    same_p, same_team = x[2] == y[2], x[1] == y[1]
                    if same_p and set(key) == {"points", "rebounds"}: yield "PTS x REB (same player)", x, [y]
                    elif same_p and set(key) == {"points", "threes"}: yield "PTS x 3PM (same player)", x, [y]
                    elif same_p and set(key) == {"points", "assists"}: yield "PTS x AST (same player)", x, [y]
                    elif not same_p and key == ("points", "points"): yield ("PTS x PTS (teammates)" if same_team else "PTS x PTS (opponents)"), x, [y]
                    elif not same_p and same_team and set(key) == {"points", "assists"}: yield "PTS x AST (teammates)", x, [y]
                    elif not same_p and same_team and key == ("rebounds", "rebounds"): yield "REB x REB (teammates)", x, [y]
            seen = set()
            for nm, x, ys in pairs():
                for y in ys:
                    if x is y:
                        continue
                    k = (nm, id(x), id(y))
                    if k in seen:
                        continue
                    seen.add(k)
                    pj = (np.sum(x[4] & y[4]) + 0.5) / (n_draws + 1.0)
                    pa, pb = (np.sum(x[4]) + 0.5) / (n_draws + 1.0), (np.sum(y[4]) + 0.5) / (n_draws + 1.0)
                    rows.append((gid, date, nm, float(pj), float(pa * pb), float(pa), float(pb), int(x[5]), int(y[5])))
            ngames += 1
        for side, tm, f, ag in (("H", H, g.home_pts, g.away_pts), ("A", A, g.away_pts, g.home_pts)):
            hist[tm].append((date, float(f), float(ag)))
        for _, r in d.iterrows():
            phist[(r.team_tricode, r.person_id)].append((date, r))
    games = pd.DataFrame(grows, columns=["game", "date", "p_ml", "y_ml", "p_spr", "y_spr", "p_tot", "y_tot"])
    return pd.DataFrame(rows, columns=["game", "date", "type", "p_joint", "p_indep", "p_a", "p_b", "y_a", "y_b"]), ngames, games


if __name__ == "__main__":
    data_dir, season, prefix = sys.argv[1:4]
    engine = sys.argv[4] if len(sys.argv) > 4 else "old"
    jp = J.JointParams(**json.loads(sys.argv[5])) if len(sys.argv) > 5 and sys.argv[5] != "-" else None
    mg = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != "-" else None
    sk = int(sys.argv[7]) if len(sys.argv) > 7 else 0
    df, ng, games = run(data_dir, int(season), engine, jp, mg, sk)
    df["y"] = df.y_a * df.y_b
    df.to_csv(safe_out(prefix + "_rows.csv.gz"), index=False)
    games.to_csv(safe_out(prefix + "_games.csv"), index=False)
    pd.DataFrame(COMBO3, columns=["game", "type", "p_joint", "p_indep", "y"]).to_csv(safe_out(prefix + "_combo3.csv.gz"), index=False)
    print(ng, "games scored;", len(df), "pairs")

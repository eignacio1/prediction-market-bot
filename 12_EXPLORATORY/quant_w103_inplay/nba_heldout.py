"""W103.3 Part A: NBA diffusion held-out test. Run: /usr/bin/python3 nba_heldout.py <pbp_dir> <out_json>

Train 2023-2025 (season label = ending year; 2025 = 2024-25), test 2026 (2025-26 regular season, game_id '002...').
No historical pre-game lines exist, so the pre-game margin M is a walk-forward Elo-style team rating (home edge
fitted on training seasons only, ratings updated only AFTER each game). This is a proxy for the line, stated in RESULT.md.
"""
import json
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/12_EXPLORATORY", 1)[0] + "/src")
from prediction_market_bot.quant import inplay_nba as q  # noqa: E402

pbp_dir, out = sys.argv[1], sys.argv[2]
rows = []
for yr in (2023, 2024, 2025, 2026):
    d = pd.read_parquet(f"{pbp_dir}/pbp_{yr}.parquet", columns=["game_id", "period", "seconds_remaining", "event_type",
                                                                  "score_home", "score_away", "location", "team_tricode"])
    d = d[d.game_id.str.startswith("002")]
    home = d[d.location == "h"].groupby("game_id").team_tricode.agg(lambda s: s.mode().iat[0])
    away = d[d.location == "v"].groupby("game_id").team_tricode.agg(lambda s: s.mode().iat[0])
    p = d[(d.event_type == "period") & (d.seconds_remaining == 0)].copy()
    p["sh"] = pd.to_numeric(p.score_home, errors="coerce")
    p["sa"] = pd.to_numeric(p.score_away, errors="coerce")
    for gid, g in p.groupby("game_id"):
        g = g.sort_values("period")
        by = {int(r.period): (r.sh, r.sa) for r in g.itertuples()}
        if not all(k in by for k in (1, 2, 3, 4)) or gid not in home.index or gid not in away.index:
            continue
        last = by[max(by)]
        if np.isnan(last[0]) or np.isnan(last[1]) or last[0] == last[1]:
            continue
        reg = by[4]
        rows.append(dict(season=yr, game_id=gid, home=home[gid], away=away[gid],
                         q1=by[1][0] - by[1][1], q2=by[2][0] - by[2][1], q3=by[3][0] - by[3][1],
                         reg=reg[0] - reg[1], tot_q1=by[1][0] + by[1][1], tot_q2=by[2][0] + by[2][1],
                         tot_q3=by[3][0] + by[3][1], tot_reg=reg[0] + reg[1], home_won=int(last[0] > last[1])))
g = pd.DataFrame(rows).sort_values(["season", "game_id"]).reset_index(drop=True)

# walk-forward rating -> pregame margin M. Elo-ish: rating in points, K by hand-fixed 0.04 (not tuned on test).
HFA, K = None, 0.04
train = g[g.season < 2026]
HFA = float(train.reg.mean())  # home edge from training seasons only
rat = defaultdict(float)
pre = []
for r in g.itertuples():
    m = rat[r.home] - rat[r.away] + HFA
    pre.append(m)
    err = r.reg - m
    rat[r.home] += K * err
    rat[r.away] -= K * err
    # regress toward 0 slightly each game is skipped on purpose: season-start carryover is crude, stated.
g["M"] = pre

CK = {"Q1": (1, 36.0), "Q2": (2, 24.0), "Q3": (3, 12.0)}
tr = g[g.season < 2026]
# variance per minute from training checkpoints (margin)
fm, tau, mm = [], [], []
for col, (_, t) in CK.items():
    fm += list(tr.reg - tr[col.lower()]); tau += [t] * len(tr); mm += list(tr.M)
s2 = q.estimate_sigma2(fm, tau, mm)
te = g[g.season == 2026]
res = {"n_train_games": int(len(tr)), "n_test_games": int(len(te)), "sigma2_per_min": s2, "sigma_per_sqrt_min": s2 ** .5,
       "HFA": HFA, "test_M_mean": float(te.M.mean()), "checkpoints": {}}
base_p = np.array([q.p_home_win(0.0, 48.0, m, s2) for m in te.M])
res["pregame_only_brier"] = q.brier(base_p, te.home_won)
for name, (_, t) in CK.items():
    p = np.array([q.p_home_win(x, t, m, s2) for x, m in zip(te[name.lower()], te.M)])
    y = te.home_won.values
    sq = (p - y) ** 2
    mean, lo, hi = q.bootstrap_ci(sq)
    naive = ((np.where(te[name.lower()] > 0, 1.0, 0.0) * 0.8 + 0.1) - y) ** 2  # crude leader-wins reference
    res["checkpoints"][name] = dict(minutes_left=t, n=int(len(te)), brier=mean, brier_ci95=[lo, hi],
                                    naive_leader_brier=float(naive.mean()),
                                    bins=[list(b) for b in q.calibration_bins(p, y)],
                                    mean_p=float(p.mean()), home_win_rate=float(y.mean()))
# cover probability at checkpoint vs half-point spread at M rounded to .5 (margin > -spread line)
cov = {}
for name, (_, t) in CK.items():
    line = np.round(te.M.values * 2) / 2
    line = np.where(line == np.round(line), line + 0.5, line)  # force half-point strikes
    p = np.array([q.p_margin_gt(x, t, m, s2, ln) for x, m, ln in zip(te[name.lower()], te.M, line)])
    y = (te.reg.values > line).astype(float)
    mean, lo, hi = q.bootstrap_ci((p - y) ** 2)
    cov[name] = dict(n=int(len(te)), brier=mean, brier_ci95=[lo, hi], mean_p=float(p.mean()), rate=float(y.mean()))
res["cover_vs_pregame_line"] = cov
json.dump(res, open(out, "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != "checkpoints"}, indent=1, default=float))
for k, v in res["checkpoints"].items():
    print(k, {a: v[a] for a in ("n", "brier", "brier_ci95", "naive_leader_brier", "mean_p", "home_win_rate")})
    for b in v["bins"]:
        print("   ", b)

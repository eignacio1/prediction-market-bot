"""W99.1 Part A: NFL crew prior -> total / team totals, rolling-origin held-out, paired, game-clustered.
Usage: python run_w99_1_nfl.py <games.csv> <archive_dir>   (archive is read only)"""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "12_EXPLORATORY")
from _fence import safe_out
from prediction_market_bot.nfl_engine.board_v2 import build_library, price_board
from prediction_market_bot.nfl_engine.crew import load_crew_table, attach_feature, fit_beta

g = pd.read_csv(sys.argv[1]); tab = load_crew_table(sys.argv[2])
g = g[(g.game_type == "REG") & g.home_score.notna() & g.spread_line.notna() & g.total_line.notna()].copy()
out = {"archive_rows": int(len(tab)), "seasons": {}}
res = {}
for col in ("pen", "yds"):
    d = attach_feature(g, tab, col)
    d["resid"] = d.home_score + d.away_score - d.total_line
    feat = "crew_" + col
    rows = []
    for S in range(2019, 2026):
        tr = d[(d.season < S) & (d.season >= 2017)]
        beta = fit_beta(tr[feat].to_numpy(), tr.resid.to_numpy())
        te = d[d.season == S]
        lib = build_library(g, before_season=S)
        for r in te.itertuples():
            x = getattr(r, feat); sh = beta * x
            b0 = price_board(lib, r.spread_line, r.total_line); b1 = price_board(lib, r.spread_line, r.total_line + sh)
            T = r.home_score + r.away_score; c = int(round(r.total_line))
            bs = []
            for k in range(-10, 11, 2):
                y = float(T >= c + k); bs.append(((b0.p_total_ge(c + k) - y) ** 2, (b1.p_total_ge(c + k) - y) ** 2))
            tt = []
            for home, pts in ((True, r.home_score), (False, r.away_score)):
                ctr = int(round(r.total_line / 2 + (-r.spread_line / 2 if not home else r.spread_line / 2)))
                for k in range(-6, 7, 3):
                    y = float(pts >= ctr + k); tt.append(((b0.p_team_ge(home, ctr + k) - y) ** 2, (b1.p_team_ge(home, ctr + k) - y) ** 2))
            rows.append(dict(season=S, gid=r.game_id, x=x, sh=sh, resid=r.resid,
                             tot_d=np.mean([a - b for a, b in bs]), tm_d=np.mean([a - b for a, b in tt]), covered=getattr(r, "referee") is not None))
    R = pd.DataFrame(rows); rng = np.random.default_rng(7)
    def boot(v):
        v = v.to_numpy(); m = v.mean(); bb = [rng.choice(v, len(v)).mean() for _ in range(2000)]
        return dict(mean=float(m), lo=float(np.percentile(bb, 2.5)), hi=float(np.percentile(bb, 97.5)), n=int(len(v)))
    res[col] = dict(total=boot(R.tot_d), team_total=boot(R.tm_d), corr_x_resid=float(np.corrcoef(R.x, R.resid)[0, 1]),
                    beta_last=float(beta), nonzero_feature_share=float((R.x != 0).mean()),
                    by_season={int(s): dict(total=float(q.tot_d.mean()), n=int(len(q)), corr=float(np.corrcoef(q.x, q.resid)[0, 1])) for s, q in R.groupby("season")})
    print(col, json.dumps(res[col], indent=1)[:900])
out["held_out"] = res
json.dump(out, open(safe_out("archive_officials/w99_1_nfl_heldout.json"), "w"), indent=1)

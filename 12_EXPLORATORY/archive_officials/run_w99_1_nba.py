"""W99.1 Part B: NBA referee archive priors -> total / team totals through engine v2. Upper bound (crew is post-game, GG-1390).
Baseline mu = OLS on the W93.2 frame fit on 2017-2024; engine v2 factor shift fit on the ONE season with a prior (2025);
test 2026 (2025-26). Brier on total and team-total ladders, paired, game-clustered bootstrap.
Usage: run_w99_1_nba.py <NBA root with raw/> <archive_dir>"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "12_EXPLORATORY"); sys.path.insert(0, "12_EXPLORATORY/nba_geometry")
import run_w93_2 as A
from _fence import safe_out
from prediction_market_bot.nba_engine.crew_archive import load_ref_table, crew_features, norm_name
from prediction_market_bot.nba_engine.engine_v2 import fit_params
import prediction_market_bot.nba_engine.engine_v2 as E
from statistics import NormalDist
N = NormalDist()

root = Path(sys.argv[1]); tab = load_ref_table(sys.argv[2])
g, tg = A.build_frame(root)
off = A.rd(root, "officials"); off["game_id"] = off.game_id.astype(str)
off["ref"] = (off.first_name.fillna("") + " " + off.last_name.fillna("")).map(norm_name)
gs = g.set_index("game_id").season.to_dict()
off = off[off.game_id.isin(gs)]
cf = crew_features(tab, off[["game_id", "ref"]], gs)
g = g.merge(cf, left_on="game_id", right_index=True, how="left")
out = {"archive_rows": int(len(tab)), "archive_refs": int(tab.ref.nunique()), "frame_games": int(len(g))}
for s in (2025, 2026):
    q = g[g.season == s]; out[f"matched_share_{s}"] = float(q.crew_matched.mean()) if len(q) else None
bt = ["base_total", "pace_mean", "eff_mean", "pace_dev_mean", "b2b_sum", "prior_total_mean", "prior_pace_mean"]
d = g.dropna(subset=bt + ["crew_pf", "crew_fta", "crew_pts", "base_margin", "net_dev_diff", "rest_diff", "b2b_diff", "prior_margin"]).copy()
pts = tg.pivot_table(index="game_id", columns="side", values="pts", aggfunc="first")
d = d.merge(pts[["home", "away"]].set_axis(["hp", "ap"], axis=1), left_on="game_id", right_index=True)
d["T"], d["M"] = d.hp + d.ap, d.hp - d.ap
bm = ["base_margin", "net_dev_diff", "rest_diff", "b2b_diff", "prior_margin"]
tr = d[d.season.isin(list(A.TRAIN))]
bT, bM = A.ols(tr[bt], tr["T"]), A.ols(tr[bm], tr["M"])
d["muT"], d["muM"] = A.pred(bT, d[bt]), A.pred(bM, d[bm])
d["mu_h"], d["mu_a"] = (d.muT + d.muM) / 2, (d.muT - d.muM) / 2
fit, te = d[d.season == 2025], d[d.season == 2026]
out["n_fit_2025"], out["n_test_2026"] = int(len(fit)), int(len(te))
out["corr_resid_2025"] = {c: float(np.corrcoef(fit[c], fit["T"] - fit.muT)[0, 1]) for c in ("crew_pf", "crew_fta", "crew_pts")}
out["corr_resid_2026"] = {c: float(np.corrcoef(te[c], te["T"] - te.muT)[0, 1]) for c in ("crew_pf", "crew_fta", "crew_pts")}
rng = np.random.default_rng(99)

def brier_rows(P, frame, shift_mode):
    rows = []
    for r in frame.itertuples():
        x = {f: getattr(r, f) for f in P.shift_total} if shift_mode == "fit" else {}
        m, t = E.game_means(P, r.mu_h, r.mu_a, x)
        if shift_mode == "unit":
            t = t + r.crew_pts
        c = int(round(t)); bs = []
        for k in range(-12, 13, 4):
            y = float(r.T >= c + k); bs.append((E.raw_prob(P, "total", m, t, c + k) - y) ** 2)
        ch = int(round((t + m) / 2)); tt = []
        for k in range(-8, 9, 4):
            y = float(r.hp >= ch + k); tt.append((E.raw_prob(P, "team_total", m, t, ch + k) - y) ** 2)
        rows.append((np.mean(bs), np.mean(tt)))
    return np.array(rows)

def boot(v):
    bb = [rng.choice(v, len(v)).mean() for _ in range(2000)]
    return dict(mean=float(v.mean()), lo=float(np.percentile(bb, 2.5)), hi=float(np.percentile(bb, 97.5)), n=int(len(v)))

P0 = fit_params(fit.mu_h.to_numpy(), fit.mu_a.to_numpy(), fit.hp.to_numpy(), fit.ap.to_numpy())
base = brier_rows(P0, te, "none")
out["brier_base_total"], out["brier_base_team_total"] = float(base[:, 0].mean()), float(base[:, 1].mean())
out["tests"] = {}
for name, facs in {"pts (crew total-points deviation)": ["crew_pts"], "pf": ["crew_pf"], "fta": ["crew_fta"], "pf+fta+pts": ["crew_pf", "crew_fta", "crew_pts"]}.items():
    P1 = fit_params(fit.mu_h.to_numpy(), fit.mu_a.to_numpy(), fit.hp.to_numpy(), fit.ap.to_numpy(),
                    factors={f: fit[f].to_numpy() for f in facs}, total_factors=facs)
    w = brier_rows(P1, te, "fit")
    out["tests"][name] = dict(shift=P1.shift_total, total_gain=boot(base[:, 0] - w[:, 0]), team_total_gain=boot(base[:, 1] - w[:, 1]))
u = brier_rows(P0, te, "unit")
out["tests"]["unit slope on crew_pts (no fit)"] = dict(total_gain=boot(base[:, 0] - u[:, 0]), team_total_gain=boot(base[:, 1] - u[:, 1]))
json.dump(out, open(safe_out("archive_officials/w99_1_nba_heldout.json"), "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:3500])

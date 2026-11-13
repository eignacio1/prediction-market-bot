"""W113.3 Part A: fit nba_engine/joint.py latent scales on the 2024-25 season (NOT the 2025-26 games Part B tests on).
Random search; loss = weighted squared dependence-covariance gap (realised - engine, against realised marginals) over the
pair classes W110.4 found wrong. Usage: PYTHONPATH=src python3 fit_joint.py <data_dir> <n_iter> <n_games> <out_json>"""
import json, sys, os, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prediction_market_bot.nba_engine import joint as J
import backtest as B
from _fence import safe_out

SPACE = dict(blow_thresh=(4, 14), blow_k=(0.0, 0.6), s_min=(0.05, 0.35), s_use=(0.05, 0.6), s_three=(0.0, 0.8),
             s_ast=(0.0, 0.6), s_reb=(0.0, 0.6), beta_reb=(-0.8, 0.2), beta_ast=(0.0, 1.5))


def gaps(df):
    df = df.copy(); df["yab"] = df.y_a * df.y_b; df["pab"] = df.p_a * df.p_b
    g = df.groupby("type").agg(n=("yab", "size"), yab=("yab", "mean"), ya=("y_a", "mean"), yb=("y_b", "mean"),
                               pj=("p_joint", "mean"), pa=("p_a", "mean"), pb=("p_b", "mean"))
    # means of products differ from products of means; use the per-pair form of dependence.py (mean of pab)
    g["pab"] = df.groupby("type").pab.mean()
    g["cov_real"] = g.yab - g.ya * g.yb
    g["cov_eng"] = g.pj - g.pab
    g["gap"] = g.cov_real - g.cov_eng
    return g


def loss(g):
    sel = g[(g.n >= 100)]
    return float((sel.gap ** 2 * np.sqrt(sel.n)).sum() / np.sqrt(sel.n).sum())


if __name__ == "__main__":
    data, n_iter, n_games, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    rng = np.random.default_rng(113)
    best, best_l, log = J.JointParams(), None, []
    def evaluate(p):
        df, ng, _ = B.run(data, 2025, "joint", p, n_games, 60, 1500)
        return loss(gaps(df)), gaps(df)
    old_df, _, _ = B.run(data, 2025, "old", None, n_games, 60, 1500)
    l_old = loss(gaps(old_df)); print("old", l_old, flush=True)
    best_l, g = evaluate(best); print("defaults", best_l, flush=True)
    for it in range(n_iter):
        cand = {k: (float(rng.uniform(*v)) if rng.random() < 0.5 or it < n_iter // 3 else
                    float(np.clip(getattr(best, k) + rng.normal(0, (v[1] - v[0]) * 0.1), *v))) for k, v in SPACE.items()}
        if it >= n_iter // 3:
            cand = {k: float(np.clip(getattr(best, k) + rng.normal(0, (SPACE[k][1] - SPACE[k][0]) * 0.1), *SPACE[k])) for k in SPACE}
        p = J.with_params(**cand); l, _ = evaluate(p)
        log.append((l, cand))
        if l < best_l:
            best, best_l = p, l; print(it, "best", l, flush=True)
    res = dict(loss_old=l_old, loss_best=best_l, params={k: getattr(best, k) for k in vars(best) if not k.startswith("_")},
               fit_season="2024-25", fit_games=n_games, skip_first=60, n_draws=1500, n_iter=n_iter)
    json.dump(res, open(safe_out(out), "w"), indent=1)
    print(json.dumps(res, indent=1))

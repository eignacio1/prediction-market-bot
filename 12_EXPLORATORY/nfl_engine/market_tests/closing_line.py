"""EXPLORATORY -- W77.2 Part A.2: how much of each factor term does the closing line price? Plan: PLAN.md (frozen). Close is the target, never an input."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from _fence import safe_out  # noqa: E402


def ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X]); b = np.linalg.lstsq(X1, y, rcond=None)[0]
    return b, 1 - ((y - X1 @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def boot(X, y, B=2000, seed=20261014):
    rng = np.random.default_rng(seed); n = len(y); bs = []
    for _ in range(B):
        i = rng.integers(0, n, n); bs.append(ols(X[i], y[i])[0])
    bs = np.array(bs); b, r2 = ols(X, y)
    return dict(n=int(n), r2=float(r2), coef=[float(v) for v in b[1:]], lo=[float(v) for v in np.percentile(bs, 2.5, axis=0)[1:]],
                hi=[float(v) for v in np.percentile(bs, 97.5, axis=0)[1:]], intercept=float(b[0]))


def devig(h, a):
    ph, pa = 100 / (h + 100) if h > 0 else -h / (-h + 100), 100 / (a + 100) if a > 0 else -a / (-a + 100)
    return ph / (ph + pa)


def main(terms, sched, out):
    t = pd.read_json(terms)
    s = pd.read_parquet(sched)[["game_id", "spread_line", "total_line", "home_moneyline", "away_moneyline"]]
    d = t.merge(s, on="game_id", how="left").dropna(subset=["spread_line", "total_line"]).copy()
    d["p_close"] = [devig(h, a) for h, a in zip(d.home_moneyline, d.away_moneyline)]
    d["has8"] = d.f8_h.notna() & d.f8_a.notna()
    for c in ("c_h", "c_a", "f8_h", "f8_a"):
        d[c + "0"] = d[c].fillna(0.0)
    d["dC"], d["sC"] = d.c_h0 - d.c_a0, d.c_h0 + d.c_a0
    d["d8"], d["s8"] = d.f8_h0 - d.f8_a0, d.f8_h0 + d.f8_a0
    res = {"n_games": int(len(d)), "sanity_corr_spread_line_vs_margin": float(np.corrcoef(d.spread_line, d.margin)[0, 1]),
           "term_sd": {k: float(d[k].std()) for k in ("dC", "sC", "d8", "s8")}, "f8_populated": float(d.has8.mean()), "fits": {}}
    names = ["engine_v0", "F5F6", "F8"]
    for lab, sub in (("all", d), ("f8_populated", d[d.has8])):
        f = {}
        f["spread"] = boot(sub[["mu_m", "dC", "d8"]].to_numpy(), sub.spread_line.to_numpy())
        f["total"] = boot(sub[["mu_t", "sC", "s8"]].to_numpy(), sub.total_line.to_numpy())
        pm = sub.p_close.clip(0.01, 0.99); lg = np.log(pm / (1 - pm)).to_numpy()
        f["moneyline_logit"] = boot(sub[["mu_m", "dC", "d8"]].to_numpy(), lg)
        # engine-only R2 of close, and outcome R2 for reference
        f["spread_engine_only_r2"] = ols(sub[["mu_m"]].to_numpy(), sub.spread_line.to_numpy())[1]
        f["total_engine_only_r2"] = ols(sub[["mu_t"]].to_numpy(), sub.total_line.to_numpy())[1]
        f["coef_names"] = names
        res["fits"][lab] = f
    safe_out(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

"""W110.4 Part B (b): dependence-only check. Excess co-occurrence measured against the REALISED marginal rates, so the
engine's marginal bias (it under-prices over-the-median legs, W109.3) cannot masquerade as a dependence error.
cov_real = mean(ya*yb) - mean(ya)*mean(yb); cov_eng = mean(p_joint) - mean(p_a)*mean(p_b); game-clustered bootstrap CI."""
import json, sys
import numpy as np, pandas as pd
import os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402
rng, B = np.random.default_rng(111), 1000

def main(path, prefix):
    df = pd.read_csv(path); out = []
    df["yab"] = df.y_a * df.y_b; df["pab"] = df.p_a * df.p_b; df["one"] = 1.0
    cols = ["yab", "y_a", "y_b", "p_joint", "p_a", "p_b", "pab", "one"]
    def f(t):  # t = column sums
        n = t[7]; return (t[0]/n - t[1]/n*t[2]/n, t[3]/n - t[4]/n*t[5]/n)
    for t, d in df.groupby("type"):
        g = d.groupby("game")[cols].sum().values
        cr, ce = f(g.sum(0)); bs = []
        for _ in range(B):
            r, e = f(g[rng.integers(0, len(g), len(g))].sum(0)); bs.append((r, e, r - e))
        bs = np.array(bs); lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        out.append(dict(type=t, n_pairs=len(d), n_games=len(g), cov_real=cr, cov_real_lo=lo[0], cov_real_hi=hi[0],
                        cov_engine=ce, cov_engine_lo=lo[1], cov_engine_hi=hi[1], gap=cr - ce, gap_lo=lo[2], gap_hi=hi[2],
                        ya=d.y_a.mean(), yb=d.y_b.mean(), pa=d.p_a.mean(), pb=d.p_b.mean()))
    out.sort(key=lambda r: -r["n_pairs"])
    pd.DataFrame(out).to_csv(safe_out(prefix + "_dependence.csv"), index=False, float_format="%.5f")
    for r in out:
        print(f"{r['type']:26s} n={r['n_pairs']:6d} cov_real={r['cov_real']:+.4f}[{r['cov_real_lo']:+.4f},{r['cov_real_hi']:+.4f}] "
              f"cov_eng={r['cov_engine']:+.4f}[{r['cov_engine_lo']:+.4f},{r['cov_engine_hi']:+.4f}] gap={r['gap']:+.4f}[{r['gap_lo']:+.4f},{r['gap_hi']:+.4f}]")

if __name__ == "__main__":
    main(*sys.argv[1:3])

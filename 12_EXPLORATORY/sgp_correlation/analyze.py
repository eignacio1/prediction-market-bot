"""W110.4 Part B analysis: engine joint vs independent product, by leg-pair type, game-clustered bootstrap.
Usage: python3 analyze.py <rows.csv.gz> <out_prefix>"""
import json, sys
import numpy as np, pandas as pd
import os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402

B, rng = 1000, np.random.default_rng(110)

def ll(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); return -(y * np.log(p) + (1 - y) * np.log(1 - p))

def boot(df, fn):
    g = {k: v for k, v in df.groupby("game")}
    keys = list(g); out = []
    # per-game sufficient stats make the bootstrap cheap
    s = np.array([fn(g[k]) for k in keys])      # (games, 2): sum, count
    for _ in range(B):
        i = rng.integers(0, len(keys), len(keys)); t = s[i].sum(0); out.append(t[0] / t[1])
    return np.percentile(out, [2.5, 97.5])

def stat(df, f):
    return lambda d: np.array([f(d).sum(), len(d)])


def main(path, prefix):
    df = pd.read_csv(path)
    out = []
    for t, d in df.groupby("type"):
        y, pj, pi = d.y.values, d.p_joint.values, d.p_indep.values
        d = d.assign(dll=ll(pi, y) - ll(pj, y), dbs=(pi - y) ** 2 - (pj - y) ** 2,
                     real_ex=y - d.p_a * d.p_b, eng_ex=pj - d.p_a * d.p_b)
        row = dict(type=t, n_pairs=len(d), n_games=d.game.nunique(), realised=y.mean(), engine_joint=pj.mean(), indep=pi.mean())
        for k in ("dll", "dbs", "real_ex", "eng_ex"):
            row[k] = d[k].mean(); lo, hi = boot(d, stat(d, lambda x, k=k: x[k])); row[k + "_lo"], row[k + "_hi"] = lo, hi
        # calibration slope of excess: regress realised excess on engine excess
        row["excess_ratio"] = row["real_ex"] / row["eng_ex"] if abs(row["eng_ex"]) > 1e-9 else None
        bins = pd.qcut(d.p_joint, 5, duplicates="drop")
        row["bins"] = [dict(pred=float(g.p_joint.mean()), real=float(g.y.mean()), n=int(len(g))) for _, g in d.groupby(bins, observed=True)]
        out.append(row)
    out.sort(key=lambda r: -r["n_pairs"])
    json.dump(out, open(safe_out(prefix + "_RESULT.json"), "w"), indent=1)
    pd.DataFrame([{k: v for k, v in r.items() if k != "bins"} for r in out]).to_csv(safe_out(prefix + "_by_type.csv"), index=False, float_format="%.5f")
    for r in out:
        print(f"{r['type']:26s} pairs={r['n_pairs']:6d} g={r['n_games']:4d} real={r['realised']:.3f} eng={r['engine_joint']:.3f} ind={r['indep']:.3f} "
              f"dLL={r['dll']:+.4f}[{r['dll_lo']:+.4f},{r['dll_hi']:+.4f}] dBS={r['dbs']:+.4f}[{r['dbs_lo']:+.4f},{r['dbs_hi']:+.4f}] "
              f"excess real={r['real_ex']:+.4f}[{r['real_ex_lo']:+.4f},{r['real_ex_hi']:+.4f}] eng={r['eng_ex']:+.4f}")

if __name__ == "__main__":
    main(*sys.argv[1:3])

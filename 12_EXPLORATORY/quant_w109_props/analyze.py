"""W109.3 Part B analysis: Brier engine vs market mid by family, game-clustered bootstrap (2000 draws), subsets."""
import json, sys, collections
import numpy as np
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402
d = json.load(open(sys.argv[1])); rows = d["rows"]
rng = np.random.default_rng(109)
def stats(rs):
    y = np.array([r["y"] for r in rs], float); p = np.array([r["p"] for r in rs]); m = np.array([r["mid"] for r in rs])
    ev = np.array([r["ev"] for r in rs]); u = np.unique(ev); idx = {e: np.where(ev == e)[0] for e in u}
    dif = (p - y) ** 2 - (m - y) ** 2
    bs = []
    for _ in range(2000):
        s = np.concatenate([idx[e] for e in rng.choice(u, len(u))]); bs.append(dif[s].mean())
    return dict(n=len(rs), games=len(u), yes_rate=float(y.mean()), mean_engine=float(p.mean()), mean_market=float(m.mean()),
                brier_engine=float(((p - y) ** 2).mean()), brier_market=float(((m - y) ** 2).mean()), diff=float(dif.mean()),
                diff_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
out = {"skipped": d["skipped"]}
subsets = {"all": lambda r: True, "spread<=0.10": lambda r: r["spread"] <= 0.10,
           "mid_0.10_0.90": lambda r: 0.10 <= r["mid"] <= 0.90, "mid_0.10_0.90_spread<=0.10": lambda r: 0.10 <= r["mid"] <= 0.90 and r["spread"] <= 0.10}
for sn, f in subsets.items():
    out[sn] = {fam: stats([r for r in rows if r["fam"] == fam and f(r)]) for fam in ("points", "rebounds", "assists", "threes") if any(r["fam"] == fam and f(r) for r in rows)}
json.dump(out, open(safe_out(sys.argv[2]), "w"), indent=1)
for sn in subsets:
    print(sn)
    for fam, s in out[sn].items():
        print("  %-9s n=%5d g=%3d yes=%.3f eng=%.3f mkt=%.3f BS_eng=%.4f BS_mkt=%.4f diff=%+.4f [%+.4f,%+.4f]" % (fam, s["n"], s["games"], s["yes_rate"], s["mean_engine"], s["mean_market"], s["brier_engine"], s["brier_market"], s["diff"], *s["diff_ci95"]))

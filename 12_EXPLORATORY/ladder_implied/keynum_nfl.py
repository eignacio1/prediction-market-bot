"""W86.2 Part A: NFL margin key-number check (3 and 7) on the T1 market spread ladder.

Two reads: (1) non-parametric - implied pmf at |m|=k from adjacent strikes, S(k-.5)-S(k+.5), against
the normal fit; (2) parametric - pooled mass multipliers (w3,w7) chosen on a grid to minimise total SSE.
usage: python keynum_nfl.py <shadow_dir>
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import ladder as L  # noqa: E402
from _fence import safe_out  # noqa: E402

RNG = np.random.default_rng(87)
GRID = [1.0, 1.4, 1.8, 2.2, 2.6, 3.0]


def last_run_ladders(shadow_dir, band="T1"):
    g = defaultdict(lambda: defaultdict(list))
    for line in open(Path(shadow_dir) / f"NFL_NFL_SPREAD_{band}.jsonl"):
        r = json.loads(line)
        g[r["event_ticker"]][r["run_id"]].append({"ticker": r["market_ticker"], "bid": r["yes_bid"], "ask": r["yes_ask"]})
    return {ev: runs[max(runs)] for ev, runs in g.items()}


def main(shadow_dir):
    lad = last_run_ladders(shadow_dir)
    pts = {ev: L.survival_points(rows, "margin") for ev, rows in lad.items()}
    # (1) non-parametric pmf ratio at |m| in {3,7} and control {2,4,5,6}
    ratios = defaultdict(list)
    for ev, p in pts.items():
        f = L.fit_normal(p)
        if not f:
            continue
        d = dict(p)
        for k in (2, 3, 4, 5, 6, 7, 8, 10, 14):
            for sgn in (1, -1):
                lo_x, hi_x = (k - 0.5, k + 0.5) if sgn == 1 else (-k - 0.5, -k + 0.5)
                if lo_x in d and hi_x in d:
                    emp = d[lo_x] - d[hi_x]
                    nrm = float(L.surv_normal(lo_x, f["mu"], f["sigma"]) - L.surv_normal(hi_x, f["mu"], f["sigma"]))
                    if nrm > 0.005:
                        ratios[k].append((ev, emp / nrm))
    np_res = {}
    for k, v in sorted(ratios.items()):
        byev = defaultdict(list)
        for ev, r in v:
            byev[ev].append(r)
        x = np.array([np.mean(a) for a in byev.values()])
        idx = RNG.integers(0, len(x), (3000, len(x)))
        bs = np.mean(x[idx], axis=1)
        np_res[k] = {"n_games": len(x), "mean_ratio": float(x.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
    # (2) pooled parametric grid
    base = {ev: L.fit_keynum(p, 1.0, 1.0) for ev, p in pts.items()}
    best = None; table = {}
    for w3 in GRID:
        for w7 in GRID:
            tot = 0.0; n = 0
            for ev, p in pts.items():
                f = L.fit_keynum(p, w3, w7)
                if f:
                    tot += f["sse"]; n += 1
            table[f"{w3},{w7}"] = tot
            if best is None or tot < best[0]:
                best = (tot, w3, w7, n)
    sse0 = table["1.0,1.0"]
    sig = []
    for ev, p in pts.items():
        f = L.fit_keynum(p, best[1], best[2])
        if f:
            sig.append(f["sigma"])
    out = {"n_games": len(pts), "pmf_ratio_vs_normal": np_res, "best_w3_w7": [best[1], best[2]],
           "sse_normal_only": sse0, "sse_best": best[0], "sse_reduction": 1 - best[0] / sse0,
           "sigma_keynum_median": float(np.median(sig)),
           "sigma_normal_median": float(np.median([L.fit_normal(p)["sigma"] for p in pts.values() if L.fit_normal(p)]))}
    json.dump(out, open(safe_out(HERE / "out" / "keynum_nfl.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])

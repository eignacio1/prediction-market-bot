"""W86.2 Part A summary: per sport/kind/band implied-width distribution, T1->T3 change, decomposition.

Bootstrap intervals resample GAMES (events), not snapshots (snapshots of one game are not independent).
usage: python summarize_a.py   (reads out/part_a_snapshots.json)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402
from part_a import FIXED  # noqa: E402

RNG = np.random.default_rng(86)
B = 4000


def boot(vals, stat=np.mean):
    v = np.asarray(vals, float)
    idx = RNG.integers(0, len(v), (B, len(v)))
    d = np.array([stat(v[i]) for i in idx])
    return float(stat(v)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def per_event(rows, key):
    g = defaultdict(list)
    for r in rows:
        if r.get(key) is not None:
            g[r["event"]].append(r[key])
    return {e: float(np.median(v)) for e, v in g.items()}


def main():
    snaps = json.load(open(HERE / "out" / "part_a_snapshots.json"))
    grp = defaultdict(list)
    for r in snaps:
        grp[(r["sport"], r["kind"], r["band"])].append(r)
    out = {"width": {}, "paired_T1_T3": {}, "between_game_sd": {}, "decomp": {}}
    for (sp, kind, band), rows in sorted(grp.items()):
        sk = per_event(rows, "sig_k"); sm = per_event(rows, "sig_m"); mk = per_event(rows, "mu_k")
        v = list(sk.values())
        med = boot(v, np.median)
        fixed = FIXED.get((sp, kind))
        out["width"][f"{sp}|{kind}|{band}"] = {
            "n_games": len(v), "sigma_market_median": med, "sigma_market_p10_p90": [float(np.percentile(v, 10)), float(np.percentile(v, 90))],
            "sigma_model_median": float(np.median(list(sm.values()))) if sm else None, "fixed_quoted": fixed,
            "mean_rmse_fit": float(np.mean([r["rmse_k"] for r in rows])),
            "ladder_points_median": float(np.median([r["n_k"] for r in rows]))}
        if band == "T1":
            out["between_game_sd"][f"{sp}|{kind}"] = {"sd_sigma_market": boot(v, np.std), "cv": float(np.std(v) / np.mean(v)),
                                                    "sd_mu_market": float(np.std(list(mk.values())))}
    for (sp, kind) in sorted({(a, b) for a, b, _ in grp}):
        a = per_event(grp[(sp, kind, "T1")], "sig_k"); c = per_event(grp[(sp, kind, "T3")], "sig_k")
        both = sorted(set(a) & set(c))
        if len(both) >= 5:
            d = [c[e] - a[e] for e in both]
            out["paired_T1_T3"][f"{sp}|{kind}"] = {"n_games": len(both), "mean_change_sigma_T3_minus_T1": boot(d)}
    for (sp, kind, band), rows in sorted(grp.items()):
        rr = [r for r in rows if r.get("dec_n")]
        if not rr:
            continue
        ev = defaultdict(list)
        for r in rr:
            ev[r["event"]].append(r)

        def agg(k):
            return [float(np.mean([x[k] for x in v])) for v in ev.values()]
        ac, aw, ar, ad = agg("abs_center"), agg("abs_width"), agg("abs_resid"), agg("abs_delta")
        ne = [sum(x["n_edge_rows"] for x in v) for v in ev.values()]
        ns = [sum(x["edge_rows_surviving_if_market_width"] for x in v) for v in ev.values()]
        se = [sum(x["sum_edge"] for x in v) for v in ev.values()]
        sw = [sum(x["sum_edge_from_width"] for x in v) for v in ev.values()]
        out["decomp"][f"{sp}|{kind}|{band}"] = {
            "n_games": len(ev), "mean_abs_delta": boot(ad), "mean_abs_center": boot(ac), "mean_abs_width": boot(aw), "mean_abs_resid": boot(ar),
            "width_share_of_center_plus_width": float(np.sum(aw) / (np.sum(aw) + np.sum(ac))) if (np.sum(aw) + np.sum(ac)) > 0 else None,
            "edge_rows": int(sum(ne)), "edge_rows_surviving_with_market_width": int(sum(ns)),
            "sum_edge": float(sum(se)), "sum_edge_removed_by_market_width": float(sum(sw))}
    p = safe_out(HERE / "out" / "part_a_summary.json")
    json.dump(out, open(p, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

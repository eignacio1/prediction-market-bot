#!/usr/bin/env python3
"""W124.1: one measured result per variance tool on OUR archive-derived rows (descriptive; no outcomes, no held-out third touched).

Rows come from build_dataset.py: per ticker, E = 15:00Z snapshot on game date - 1 (entry), R = 15:00Z snapshot on the game date
(reference line, NOT the true close: the archive has no start time), P0 = game date - 2. Side = the favourite at E (mid >= 0.5 -> YES).
CLV is on the order's own side via quant.variance.clv; entry is the E mid (gross); round cost = half-spread + Kalshi fee 0.07 p(1-p).
Data epoch: the archive is quote data, not fills, so the NO-side mirror-pricing epoch (2026-11-06T01:03:42Z) does not touch it.
usage: measure_variance_tools.py --data ds.jsonl.gz --out 12_EXPLORATORY/edge_location/power_ledger/variance_measurements.json
"""
import argparse, gzip, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import variance as V  # noqa: E402


def load(path):
    out = []
    for l in gzip.open(path, "rt"):
        r = json.loads(l)
        e, rf = r["e"], r.get("r")
        if rf is None:
            continue
        side = "yes" if e["mid"] >= 0.5 else "no"
        p = e["mid"] if side == "yes" else 1 - e["mid"]          # entry price on own side (gross, at mid)
        cost = (e["ask"] - e["bid"]) / 2 + 0.07 * p * (1 - p)    # half-spread + fee, per contract
        row = {"series": r["series"], "gk": "%s|%s" % (r["gd"], r["game"]), "gd": r["gd"], "side": side,
               "clv": V.clv(p, rf["mid"], side), "cost": cost, "p": p}
        if "p0" in r:
            mv = e["mid"] - r["p0"]["mid"]
            row["move"] = mv if side == "yes" else -mv          # pre-entry move in the order's own direction
        out.append(row)
    return out


def family(s):
    for k in ("GAME", "SPREAD", "TEAMTOTAL", "TOTAL"):
        if s.endswith(k):
            return k
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = load(a.data)
    res = {"rows": len(rows), "games": len({r["gk"] for r in rows}),
           "dates": [min(r["gd"] for r in rows), max(r["gd"] for r in rows)],
           "caveat": "R is the game-morning 15:00Z line, not the close; CLV here is descriptive, pre-H-MEAS-1."}
    y = [r["clv"] for r in rows]; g = [r["gk"] for r in rows]
    res["clv"] = {"gross": V.clustered_mean(y, g), "cost_mean": sum(r["cost"] for r in rows) / len(rows),
                  "net": V.clustered_mean([r["clv"] - r["cost"] for r in rows], g)}
    d = V.design_effect(y, g)
    sd = (sum((v - res["clv"]["gross"]["mean"]) ** 2 for v in y) / (len(y) - 1)) ** 0.5
    res["design_effect"] = {**d, "clv_sd": sd,
                            "mde_now": V.mde_clustered(sd, d["n_games"], d["rows_per_game"], d["icc"]),
                            "games_for_mde_equal_cost": V.games_needed(sd, d["rows_per_game"], d["icc"], res["clv"]["cost_mean"])}
    # control variate: pre-entry move, fit on the earliest 2/3 of game dates, judged on the rest
    cv = [r for r in rows if "move" in r]
    dates = sorted({r["gd"] for r in cv}); cut = dates[int(len(dates) * 2 / 3) - 1]
    fit = [r["gd"] <= cut for r in cv]
    res["control_variate"] = {"fit_through": cut, **V.control_variate(
        [r["clv"] for r in cv], [r["move"] for r in cv], [r["gk"] for r in cv], fit)}
    # paired: on the same game, mean CLV of the GAME ticker vs mean CLV of SPREAD tickers
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["gk"]][family(r["series"])].append(r["clv"])
    pr = [(k, sum(f["GAME"]) / len(f["GAME"]), sum(f["SPREAD"]) / len(f["SPREAD"])) for k, f in by.items() if "GAME" in f and "SPREAD" in f]
    res["paired_game_vs_spread"] = V.paired_within_cluster(pr) if len(pr) > 2 else {"n_games": len(pr)}
    # partial pooling over series
    cells = {}
    for s in sorted({r["series"] for r in rows}):
        sub = [r for r in rows if r["series"] == s]
        if len({r["gk"] for r in sub}) >= 5:
            c = V.clustered_mean([r["clv"] for r in sub], [r["gk"] for r in sub])
            cells[s] = (c["mean"], c["se"])
    res["partial_pool_by_series"] = V.partial_pool(cells) if len(cells) >= 2 else {}
    # per-family design effect + sd (feeds the ledger)
    res["by_family"] = {}
    for f in sorted({family(r["series"]) for r in rows}):
        sub = [r for r in rows if family(r["series"]) == f]
        ys = [r["clv"] for r in sub]; gs = [r["gk"] for r in sub]
        dd = V.design_effect(ys, gs); m = sum(ys) / len(ys)
        res["by_family"][f] = {**dd, "clv_mean": m, "clv_sd": (sum((v - m) ** 2 for v in ys) / (len(ys) - 1)) ** 0.5,
                               "cost_mean": sum(r["cost"] for r in sub) / len(sub)}
    p = safe_out(a.out)
    p.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: res[k] for k in ("rows", "games", "clv", "design_effect")}, indent=1, default=float))
    print("CV VR", res["control_variate"]["variance_reduction"], "theta", res["control_variate"]["theta"], "n_judged", res["control_variate"]["n_judged"])
    print("PAIRED", {k: v for k, v in res["paired_game_vs_spread"].items()})
    pp = res["partial_pool_by_series"]; print("POOL tau", pp.get("tau"), "mu", pp.get("mu"), [(c["cell"], round(c["raw"], 4), round(c["shrunk"], 4)) for c in pp.get("cells", [])])


if __name__ == "__main__":
    main()

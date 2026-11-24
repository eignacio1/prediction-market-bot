"""W125.3 Part C: pot-of-gold branches scored PER LEAF on 2026-27 forward shadow rows, partial pooling, net after costs, FLB bucket as a split.

  python 12_EXPLORATORY/pot_of_gold/score_w125.py --archive <PRICE_ARCHIVE> --settle <dir> --out 12_EXPLORATORY/pot_of_gold/out/w125

Leaf = (sport, family, tier, FLB bucket of the mid, side). FLB buckets are the H-EDGE-5 set [.02,.10) [.10,.25) [.25,.50) [.50,.75) [.75,.90) [.90,.98].
Rows = first two-sided pre-start snapshot per (ticker, tier) at or after 2026-11-05 (measure.scan, unchanged), settled, entry at the quote,
exact taker fee (longshot_bias.net_per_contract). Per leaf: n, games, game-clustered CR1 mean and 90% interval (variance.clustered_mean).
Partial pooling (variance.partial_pool) across the leaves of one (family, side, favourite|longshot half): the shrunk mean and interval are the
leaf's score. Judged n is the 11-05 rule (>= 150 contracts, >= 30 games, minority >= 5); below it the leaf is IN_SAMPLE and its score is shown
as unjudged. EARNED = judged n AND shrunk 90% lower bound > 0 AND Benjamini-Hochberg q 0.10 across judged leaves. Nothing here changes a leaf map.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias"))
sys.path.insert(0, os.path.join(REPO, "src"))
import calib as C  # noqa: E402
import measure as M  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import longshot_bias as L  # noqa: E402
from prediction_market_bot.quant import variance as V  # noqa: E402
from prediction_market_bot.quant import multiplicity as MU  # noqa: E402

FORWARD_FROM = C.parse_ts("2026-11-05T00:00:00Z")
JUDGED_N, JUDGED_GAMES, JUDGED_MINORITY = 150, 30, 5
EDGES = [(0.02, 0.10), (0.10, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 0.90), (0.90, 0.98001)]


def flb_bucket(p):
    for lo, hi in EDGES:
        if lo <= p < hi:
            return "[%.2f,%.2f)" % (lo, min(hi, 0.98))
    return None


def forward_rows(archive, settle):
    rows = []
    for s in M.scan(archive):
        y = settle.get(s["ticker"])
        b = flb_bucket(s["p"])
        if y is None or s["ts"] < FORWARD_FROM or b is None:
            continue
        s.update(y=y, flb=b, sport=M.sport_of(s["series"]))
        rows.append(s)
    return rows


def leaves(rows):
    g = defaultdict(list)
    for r in rows:
        for side in ("yes", "no"):
            g[(r["sport"], r["series"], r["tier"], r["flb"], side)].append(r)
    out = []
    for k, rs in sorted(g.items()):
        nets = [L.net_per_contract(r["series"], k[4], r["y"], r["bid"], r["ask"]) for r in rs]
        cm = V.clustered_mean(nets, [r["game"] for r in rs], level=0.90)
        wins = sum(1 for x in nets if x > 0)
        minority = min(wins, len(nets) - wins)
        pbar = sum(r["p"] for r in rs) / len(rs)
        out.append({"sport": k[0], "family": k[1], "tier": k[2], "flb": k[3], "side": k[4],
                    "half": "fav" if pbar >= 0.5 else "long", "n": len(nets), "games": cm["n_clusters"],
                    "minority": minority, "mean": cm["mean"], "se": cm["se"], "pbar": pbar,
                    "gap": sum(r["y"] for r in rs) / len(rs) - pbar,
                    "judged": len(nets) >= JUDGED_N and cm["n_clusters"] >= JUDGED_GAMES and minority >= JUDGED_MINORITY})
    return out


def pool(lv):
    groups = defaultdict(list)
    for i, r in enumerate(lv):
        if r["games"] >= 5 and r["se"] == r["se"] and r["se"] > 0:
            groups[(r["family"], r["side"], r["half"])].append(i)
    for key, idx in groups.items():
        if len(idx) < 2:
            continue
        res = V.partial_pool({i: (lv[i]["mean"], lv[i]["se"]) for i in idx}, level=0.90)
        for c in res["cells"]:
            r = lv[c["cell"]]
            r.update(shrunk=c["shrunk"], post_se=c["post_se"], s_lo=c["lo"], s_hi=c["hi"], B=c["B"], tau=res["tau"], pool_k=len(idx))
    return groups


def verdicts(lv):
    jd = [r for r in lv if r["judged"] and "s_lo" in r]
    ps = [MU.one_sided_p(r["shrunk"] / r["post_se"]) if r["post_se"] > 0 else 1.0 for r in jd]
    rej = MU.benjamini_hochberg(ps, q=0.10) if jd else []
    flag = {id(r): bool(x["reject"]) for r, x in zip(jd, rej)}
    for r in lv:
        if not r["judged"]:
            r["verdict"] = "IN_SAMPLE"
        elif "s_lo" not in r:
            r["verdict"] = "IN_SAMPLE (no pool)"
        elif flag.get(id(r)) and r["s_lo"] > 0:
            r["verdict"] = "EARNED"
        elif r["shrunk"] <= 0:
            r["verdict"] = "ROUTED AWAY (hypothesis closed, EXP-POT-W125, parked for R&D)"
        else:
            r["verdict"] = "IN_SAMPLE (CONTINUE)"
    return len(jd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    settle = C.load_settlements(a.settle)
    rows = forward_rows(a.archive, settle)
    lv = leaves(rows)
    groups = pool(lv)
    n_j = verdicts(lv)
    tally = defaultdict(int)
    for r in lv:
        tally[r["verdict"].split(" (")[0]] += 1
    fam = defaultdict(lambda: [0, 0])
    for r in rows:
        fam[r["series"]][0] += 1
    summary = {"forward_rows": len(rows), "leaves": len(lv), "judged_leaves": n_j, "pools": len(groups),
               "verdicts": dict(tally), "rows_by_family": {k: v[0] for k, v in sorted(fam.items())}}
    with open(safe_out(os.path.join(out, "leaves_w125.json")), "w") as fh:
        json.dump({"summary": summary, "leaves": lv}, fh, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

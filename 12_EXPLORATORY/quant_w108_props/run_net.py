"""W109.4 Parts A+B -- coverage and held-out net-of-cost cells for NBA/NFL/NHL props from cached pre-game candles.
usage: run_net.py CACHE_DIR OUT_JSON.  Entry = last two-sided quote at LEAD hours BEFORE close_time (close is the end of
the game or earlier, so close-5h is before tip-off for NBA/NHL/NFL; tip-off itself is not in the API)."""
import glob, json, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from prediction_market_bot.quant import props_candles as P  # noqa: E402
sys.path.insert(0, os.path.dirname(HERE))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.props_calib import time_split, MIN_GAMES  # noqa: E402
from prediction_market_bot.quant.money import fee_rate  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402
from prediction_market_bot.quant.multiplicity import holm, benjamini_hochberg, one_sided_p  # noqa: E402
import math
from statistics import NormalDist

LEADS = {"C-5h": 5 * 3600, "C-8h": 8 * 3600, "C-12h": 12 * 3600}
MAXAGE = 6 * 3600
SPORT = {"KXNBA": "NBA", "KXNFL": "NFL", "KXNHL": "NHL"}


def net(side, y, bid, ask, series):
    q = ask if side == "yes" else 1 - bid
    won = y if side == "yes" else 1 - y
    return won - q - fee_rate(series, q)


def band(mid):
    return "<10" if mid < .10 else "10-30" if mid < .30 else "30-70" if mid < .70 else "70-90" if mid < .90 else ">90"


def load(root):
    rows, cov = [], defaultdict(lambda: defaultdict(int))
    dates = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(root, "*.jsonl"))):
        for l in open(f):
            r = json.loads(l)
            s = r["t"].split("-")[0]
            cov[s]["markets"] += 1
            if not r["c"]:
                continue
            cov[s]["with_candles"] += 1
            dates[s].append(r["close"][:10])
            m = {"ticker": r["t"], "event_ticker": r["ev"], "result": r["res"], "volume_fp": r["vol"]}
            cs = sorted(r["c"], key=lambda c: c["end_period_ts"])
            ct = P.parse_ts(r["close"])
            for x in P.entry_rows(m, cs, ct, LEADS):
                if x["age_s"] <= MAXAGE:
                    rows.append(x); cov[s]["q_" + x["lead"]] += 1
    return rows, cov, dates


def cell(rows):
    fit, hold = time_split(rows)
    if not fit or not hold:
        return None
    ser = rows[0]["series"]
    mean = lambda rs, sd: sum(net(sd, r["y"], r["bid"], r["ask"], ser) for r in rs) / len(rs)
    side = "yes" if mean(fit, "yes") >= mean(fit, "no") else "no"
    g = defaultdict(list)
    for r in hold:
        g[r["game"]].append(net(side, r["y"], r["bid"], r["ask"], ser))
    m, lo, hi = cluster_bootstrap(g, b=1000, seed=20261110)
    n = len(hold)
    p = None
    if len(g) >= MIN_GAMES:
        s2 = sum((sum(v) - len(v) * m) ** 2 for v in g.values())
        se = math.sqrt(s2) / n
        if se > 0:
            p = 1 - NormalDist().cdf(m / se)
    return {"side": side, "n_fit": len(fit), "n_hold": n, "games_hold": len(g), "fit_net": mean(fit, side), "net": m, "lo": lo, "hi": hi, "p": p}


def main():
    rows, cov, dates = load(sys.argv[1])
    out = {"coverage": {s: dict(v, first=min(dates[s]) if dates[s] else None, last=max(dates[s]) if dates[s] else None) for s, v in cov.items()}}
    cells = []
    for r in rows:
        r["sport"] = SPORT[r["series"][:5]]; r["fam"] = r["series"]
        r["band"] = band((r["bid"] + r["ask"]) / 2); r["liq"] = "tight" if r["ask"] - r["bid"] <= .02 else "wide"
    keys = [("fam", "lead"), ("fam", "lead", "band"), ("fam", "lead", "band", "liq"), ("sport", "lead", "band")]
    for ks in keys:
        grp = defaultdict(list)
        for r in rows:
            grp[tuple(r[k] for k in ks)].append(r)
        for k, rs in grp.items():
            if len({r["game"] for r in rs}) < 10:
                continue
            c = cell(rs)
            if c:
                c.update(level="x".join(ks), key=list(k)); cells.append(c)
    # costs per family (pooled, tail-aware): mean half-spread, mean fee, total round-trip-free entry cost
    cost = {}
    for fam in sorted({r["fam"] for r in rows}):
        for lead in LEADS:
            rs = [r for r in rows if r["fam"] == fam and r["lead"] == lead]
            if len(rs) < 20:
                continue
            hs = sum((r["ask"] - r["bid"]) / 2 for r in rs) / len(rs)
            fe = sum(fee_rate(fam, r["ask"]) for r in rs) / len(rs)
            cost[f"{fam}|{lead}"] = {"n": len(rs), "games": len({r["game"] for r in rs}), "half_spread": hs, "fee": fe, "entry_cost": hs + fe}
    tested = [c for c in cells if c["p"] is not None]
    for fn, name in ((holm, "holm"), (benjamini_hochberg, "bh")):
        res = fn([c["p"] for c in tested])
        for c, rr in zip(tested, res):
            c[name] = rr["reject"] and c["net"] > 0
            c[name + "_adj"] = rr.get("p_adj", rr.get("q"))
    out.update(cells=cells, cost=cost, n_rows=len(rows), n_tested=len(tested),
               holm_wins=[c for c in tested if c.get("holm")], bh_wins=[c for c in tested if c.get("bh")])
    json.dump(out, open(safe_out(sys.argv[2]), "w"), indent=1)
    print("rows", len(rows), "cells", len(cells), "tested", len(tested), "holm", len(out["holm_wins"]), "bh", len(out["bh_wins"]))

main()

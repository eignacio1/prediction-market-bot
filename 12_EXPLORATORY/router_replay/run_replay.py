"""W90.2 replay: route every first two-sided pre-start snapshot per (ticker, tier) of the local price archive through
decision_trees.router and report traffic per tree plus DESCRIPTIVE settlement-minus-price on each tree's routed side
(mid entry, no fee), game-clustered 95% interval. Measures nothing about edge: the ride table is the 11 W89.2 survivor cells
drawn from this same archive, so the RIDE rows are IN-SAMPLE and are not evidence; a time-split view is added.
FADE needs a model_p, which the archive does not carry (shadow ledgers live on the box), so FADE traffic is reported
twice: 0 by evidence (W88.3 skill ~0 everywhere) and, as a stress, with a synthetic model_p to show the gate holds.

  python 12_EXPLORATORY/router_replay/run_replay.py --archive <PRICE_ARCHIVE> --settle <dir> --out router_replay/out   (relative to 12_EXPLORATORY/ by the write fence)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias"))
sys.path.insert(0, os.path.dirname(HERE))
import calib as C  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.decision_trees.router import (  # noqa: E402
    Evidence, RideCell, Situation, Skill, route)
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402

# W89.2 survivors (results_W89.md): family, tier, bucket, book, side, net 95% lower bound per contract.
SURVIVORS = [
    ("KXMLBHIT", "T0-2h", "20-25c", "all", "yes", 0.0065), ("KXMLBHIT", "T0-2h", "20-25c", "tight", "yes", 0.017),
    ("KXMLBF5TOTAL", "T6-24h", "90-95c", "all", "yes", 0.022), ("KXMLBF5TOTAL", "T6-24h", "90-95c", "wide", "yes", 0.011),
    ("KXMLBF5TOTAL", "T2-6h", "90-95c", "tight", "yes", 0.017), ("KXNFLTOTAL", "D1", "5-10c", "all", "no", 0.0065),
    ("KXMLBSPREAD", "T>24h", "20-25c", "tight", "no", 0.0026), ("KXMLBTEAMTOTAL", "T6-24h", "15-20c", "tight", "no", 0.0085),
    ("KXMLBF5", "T2-6h", "10-15c", "all", "no", 0.0087), ("KXMLBTOTAL", "T0-2h", "85-90c", "wide", "yes", 0.047),
    ("KXMLBF7", "T0-2h", "40-45c", "wide", "yes", 0.0006),
]
# W88.3 paired Brier (market - model); weight = clip(1 - Bm/Bk, 0, 1). NFL has no interval (W87.3).
SKILL = {"mlb": Skill(0.0018, -0.0030, 2037), "nhl": Skill(0.0, -0.00005, 1305), "nba": Skill(0.0, -0.0089, 1228),
         "nfl": Skill(0.0, None, 271)}


class Table:
    def __init__(self):
        self.c = {(f, t, b, k): RideCell(f, t, b, k, s, lo) for f, t, b, k, s, lo in SURVIVORS}

    def lookup(self, f, t, b, k):
        return self.c.get((f, t, b, k))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def situations(archive):
    seen, out = set(), []
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                fam = r.get("series_ticker", "")
                bid, ask = fnum(r.get("yes_bid")), fnum(r.get("yes_ask"))
                if not bid or not ask or ask < bid:
                    continue
                ts = C.parse_ts(r["run_ts"])
                t = C.tier(r["event_ticker"], ts)
                if t is None:
                    continue
                key = (r["ticker"], t)
                if key in seen:
                    continue
                seen.add(key)
                sport = "nfl" if fam.startswith("KXNFL") else "mlb"
                out.append((ts, r["event_ticker"], Situation(sport, fam, r["ticker"], r["event_ticker"], t, bid, ask,
                                                              (ask - bid) / 2.0)))
    out.sort(key=lambda x: x[0])
    return out


def summarize(rows):
    """rows: (event, y_side - price_side). Returns n, games, mean, lo, hi."""
    g = defaultdict(list)
    for ev, v in rows:
        g[ev].append(v)
    m, lo, hi = cluster_bootstrap(g, b=1000, seed=20261027)
    return {"n": len(rows), "games": len(g), "mean": m, "lo": lo, "hi": hi}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    settle = C.load_settlements(a.settle)
    sits = situations(a.archive)
    ev = Evidence(skill={(s, f): k for s, k in SKILL.items() for f in ("*",)}, ride=Table())
    # per-family skill lookup: apply the sport-level record to every family of that sport
    fams = {s.family for _, _, s in sits}
    ev.skill = {(sp, f): SKILL[sp] for f in fams for sp in SKILL}
    counts, reasons = Counter(), Counter()
    per = defaultdict(list)  # tree -> [(ts, event, value)]
    fade_stress = Counter()
    for ts, evt, s in sits:
        r = route(s, ev)
        counts[r.tree] += 1
        reasons[(r.tree, r.reasons[0])] += 1
        # stress: a confident synthetic model_p must still not reach FADE (no measured skill)
        if route(Situation(**{**s.__dict__, "model_p": 0.99 if s.mid < 0.5 else 0.01}), ev).tree == "FADE":
            fade_stress["FADE"] += 1
        y = settle.get(s.ticker)
        if r.tree == "RIDE" and y is not None:
            if r.side == "yes":
                v = y - s.mid
            else:
                v = (1 - y) - (1 - s.mid)
            per["RIDE"].append((ts, evt, v))
    n = len(sits)
    res = {"situations": n, "counts": dict(counts), "share": {k: v / n for k, v in counts.items()},
           "top_reasons": [[list(k), v] for k, v in reasons.most_common(12)], "fade_stress_traffic": dict(fade_stress),
           "no_skill_tree_traffic": [t for t in counts if t == "FADE" and counts[t] > 0]}
    rows = per["RIDE"]
    res["ride_settled"] = summarize([(e, v) for _, e, v in rows]) if rows else None
    if rows:
        h = len(rows) // 2
        res["ride_time_split"] = {"first_half": summarize([(e, v) for _, e, v in rows[:h]]),
                                  "second_half": summarize([(e, v) for _, e, v in rows[h:]])}
        by_fam = defaultdict(list)
        for (_, e, v), (_, _, s) in zip(rows, [x for x in sits if route(x[2], ev).tree == "RIDE" and x[2].ticker in settle]):
            by_fam[s.family].append((e, v))
        res["ride_by_family"] = {k: summarize(v) for k, v in by_fam.items()}
    json.dump(res, open(safe_out(os.path.join(a.out, "replay.json")), "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()

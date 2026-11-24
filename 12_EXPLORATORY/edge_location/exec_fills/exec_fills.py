#!/usr/bin/env python3
"""H-EXEC-4 (W124.3): net-of-fee settled value of filled arm orders, with control variate, pairing and partial pooling.

Input: recs.jsonl from placement/join.records (one record per placed order). Stdlib only (Python 3.9 on the box).
Applies when: the unit of independence is the game and each fill record carries the fee actually charged.
Does not apply: unsettled / void orders (counted, never imputed). Pre-registered in PREREG.md before any post-cut fill was read.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402

CUT = "2026-11-20T20:00:00+00:00"
BUCKETS = [(0, 2, "0-2h"), (2, 6, "2-6h"), (6, 24, "6-24h"), (24, 1e9, "24h+")]
SEED = 20261123


def bucket(h: Optional[float]) -> Optional[str]:
    if h is None:
        return None
    for lo, hi, name in BUCKETS:
        if lo <= h < hi:
            return name
    return None


def net_of(rec: dict) -> Optional[float]:
    """Settled net per contract after the fee charged; None when not filled, not resolved or fee unknown."""
    if not rec.get("filled") or rec.get("won") is None or rec.get("fill_price") is None or rec.get("fee_per_contract") is None:
        return None
    return (1.0 if rec["won"] else 0.0) - rec["fill_price"] - rec["fee_per_contract"]


def game_of(rec: dict) -> str:
    return rec["ticker"].rsplit("-", 1)[0]


def cell_of(rec: dict) -> Tuple[str, str, str]:
    return (str(rec.get("arm")), str(rec.get("series")), str(bucket(rec.get("hours"))))


def split_by_cut(recs: Sequence[dict], cut: str = CUT) -> Tuple[List[dict], List[dict]]:
    """(pre-cut descriptive, forward judged) by first fill time; records with no fill time are in neither."""
    pre, fwd = [], []
    for r in recs:
        t = r.get("fill_ts")
        if not t:
            continue
        (fwd if t > cut else pre).append(r)
    return pre, fwd


def isotonic(xs: Sequence[float], ys: Sequence[float]) -> List[Tuple[float, float]]:
    """Pool-adjacent-violators fit -> sorted [(x, fitted)] knots (fit on pre-cut data only)."""
    pts = sorted(zip(xs, ys))
    blocks = [[y, 1, x, x] for x, y in pts]
    out: List[list] = []
    for b in blocks:
        out.append(b)
        while len(out) > 1 and out[-2][0] / out[-2][1] > out[-1][0] / out[-1][1]:
            b2 = out.pop(); b1 = out.pop()
            out.append([b1[0] + b2[0], b1[1] + b2[1], b1[2], b2[3]])
    return [((b[2] + b[3]) / 2, b[0] / b[1]) for b in out]


def apply_iso(knots: Sequence[Tuple[float, float]], x: float) -> float:
    if x <= knots[0][0]:
        return knots[0][1]
    for (x0, y0), (x1, y1) in zip(knots, knots[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0) if x1 > x0 else y1
    return knots[-1][1]


def cv_adjust(y: Sequence[float], c: Sequence[float], games: Sequence[str]) -> dict:
    """Regress y on c (slope b, game-clustered by construction of the bootstrap that follows); return adjusted y and the
    variance reduction 1 - var(adj)/var(y). Adjusted mean equals the raw mean (c is centred)."""
    n = len(y)
    my, mc = sum(y) / n, sum(c) / n
    vc = sum((ci - mc) ** 2 for ci in c)
    b = 0.0 if vc == 0 else sum((ci - mc) * (yi - my) for ci, yi in zip(c, y)) / vc
    adj = [yi - b * (ci - mc) for yi, ci in zip(y, c)]
    vy = sum((yi - my) ** 2 for yi in y) / n
    va = sum((a - sum(adj) / n) ** 2 for a in adj) / n
    return {"b": b, "adj": adj, "var_reduction": 0.0 if vy == 0 else 1 - va / vy}


def paired_arm_diff(recs: Sequence[dict], a: str, b: str) -> Dict[str, float]:
    """Per game with both arms filled: mean net of arm a minus mean net of arm b."""
    by: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for r in recs:
        v = net_of(r)
        if v is not None and r.get("arm") in (a, b):
            by[game_of(r)][r["arm"]].append(v)
    return {g: sum(d[a]) / len(d[a]) - sum(d[b]) / len(d[b]) for g, d in by.items() if d[a] and d[b]}


def eb_pool(means: Sequence[float], ses: Sequence[float]) -> dict:
    """Normal-normal empirical Bayes (DerSimonian-Laird tau^2). Returns pooled mean, tau2 and shrunk means."""
    w = [1 / s ** 2 for s in ses]
    mu0 = sum(wi * m for wi, m in zip(w, means)) / sum(w)
    q = sum(wi * (m - mu0) ** 2 for wi, m in zip(w, means))
    k = len(means)
    c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    wr = [1 / (s ** 2 + tau2) for s in ses]
    mu = sum(wi * m for wi, m in zip(wr, means)) / sum(wr)
    shrunk = [mu + (tau2 / (tau2 + s ** 2)) * (m - mu) for m, s in zip(means, ses)]
    return {"mu": mu, "tau2": tau2, "shrunk": shrunk}


def cell_table(recs: Sequence[dict], min_fills: int = 10, min_games: int = 5, level: float = 0.10) -> List[dict]:
    by: Dict[tuple, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for r in recs:
        v = net_of(r)
        if v is not None:
            by[cell_of(r)][game_of(r)].append(v)
    out = []
    for key, g in sorted(by.items()):
        n = sum(len(v) for v in g.values())
        m, lo, hi = cluster_bootstrap(g, 2000, SEED, level)
        out.append({"arm": key[0], "series": key[1], "bucket": key[2], "fills": n, "games": len(g),
                    "net": m, "lo": lo, "hi": hi, "judgeable": n >= min_fills and len(g) >= min_games})
    return out


def classify(lo: float, hi: float) -> str:
    return "SUPPORTED" if lo > 0 else "NOT SUPPORTED" if hi < 0 else "COLLECTING"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("recs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    recs = [json.loads(l) for l in open(a.recs) if l.strip()]
    pre, fwd = split_by_cut(recs)
    res = {"cut": CUT, "descriptive_pre_cut": cell_table(pre), "forward": cell_table(fwd), "n_pre": len(pre), "n_fwd": len(fwd)}
    with open(safe_out(a.out), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps({"n_pre": len(pre), "n_fwd": len(fwd)}))


if __name__ == "__main__":
    main()

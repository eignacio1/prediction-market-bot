"""EXPLORATORY -- W77.2 Part A.1: power of the outcome test (stage 3) per family. Plan: market_tests/PLAN.md.
(1) MDE at 80% power from each stage-3 paired-dBrier CI: MDE = 2.8 * SE, SE = (hi-lo)/3.92 (BEATS needs hi<0).
(2) Injection: outcomes redrawn as if a term were FULLY real (true mean = arm mean), paired dBrier bootstrapped,
    P(BEATS) = share of repeats with CI hi < 0. Normal-margin/total approximation; sigma from the data."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from math import erf, sqrt
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from _fence import safe_out  # noqa: E402
SEED, B_IN, REPS = 20261014, 300, 500
Phi = np.vectorize(lambda z: 0.5 * (1 + erf(z / sqrt(2))))


def boot_hi(d, rng):
    idx = rng.integers(0, len(d), (B_IN, len(d)))
    return float(np.quantile(d[idx].mean(1), 0.975))


def inject(mu_b, shift, sig, line, rng):
    """P(BEATS) for arm (mu_b+shift) vs base (mu_b) when truth mean = arm mean. Binary outcome vs `line`."""
    hits, deltas = 0, []
    for _ in range(REPS):
        y = (mu_b + shift + rng.normal(0, sig, len(mu_b)) > line).astype(float)
        pb, pa = Phi((mu_b - line) / sig), Phi((mu_b + shift - line) / sig)
        d = (pa - y) ** 2 - (pb - y) ** 2
        deltas.append(d.mean()); hits += boot_hi(d, rng) < 0
    return dict(p_beats=hits / REPS, mean_dbrier=float(np.mean(deltas)))


def main(terms, sched, stage3, out):
    rng = np.random.default_rng(SEED)
    t = pd.read_json(terms); s = pd.read_parquet(sched)[["game_id", "spread_line", "total_line"]]
    t = t.merge(s, on="game_id")
    r3 = json.load(open(stage3))
    res = {"mde": {}, "inject": {}}
    for lab, fams in r3["families"].items():
        for f, o in fams.items():
            se = (o["delta"]["hi"] - o["delta"]["lo"]) / 3.92
            res["mde"][f"{lab}/{f}"] = dict(se=se, mde80=2.8 * se, observed=o["delta"]["mean"], decision=o["decision"])
    sm, st = float((t.margin - t.mu_m).std()), float((t.total - t.mu_t).std())
    res["sigma"] = dict(margin=sm, total=st)
    z = lambda c: t[c].fillna(0).to_numpy()
    d8, s8 = z("f8_h") - z("f8_a"), z("f8_h") + z("f8_a")
    dC, sC = z("c_h") - z("c_a"), z("c_h") + z("c_a")
    mm, mt = t.mu_m.to_numpy(), t.mu_t.to_numpy()
    kS, kT = t.spread_line.to_numpy(), t.total_line.to_numpy()
    for term, dsh, ssh in (("F8", d8, s8), ("F5F6", dC, sC)):
        res["inject"][term] = dict(
            ml=inject(mm, dsh, sm, 0.0, rng),
            spread=inject(mm, dsh, sm, kS, rng),     # P(margin > spread_line): cover-style threshold at the close
            total=inject(mt, ssh, st, kT, rng))
    safe_out(out).write_text(json.dumps(res, indent=1))
    for k, v in res["inject"].items(): print(k, {a: (round(b["p_beats"], 3), round(b["mean_dbrier"], 5)) for a, b in v.items()})
    for k, v in res["mde"].items(): print(k, round(v["mde80"], 5), round(v["observed"], 5), v["decision"])


if __name__ == "__main__":
    main(*sys.argv[1:5])

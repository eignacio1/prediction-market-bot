#!/usr/bin/env python3
"""T-573 Deliverable 3: selection-bias test, 34 confirmed-FILLED vs 731 NOT_RETRIEVABLE.

PRE-REGISTERED OBSERVABLES (fixed by the task instruction itself, before any test
statistic was computed -- not derived from inspecting results):
  1. mid_price_at_entry      (entry price stratum)
  2. game_date                (categorical -- distributional comparison)
  3. kalshi_ticker             (categorical -- distinct-ness / team-clustering, descriptive)
  4. kalshi_threshold          (categorical -- 1/2/3+ hits)
  5. gross_edge                (gross_edge at entry)
  6. h_so_far_at_entry          (proxy for "inning" -- no explicit inning field on this
                                 schema; h_so_far_at_entry and ab_remaining_at_entry are
                                 the stored in-game-state fields)
  7. ab_remaining_at_entry
  8. size_usd                  (order size)

Continuous observables (1,5,6,7,8): two-sided Mann-Whitney U test, normal
approximation with tie correction (no scipy on VPS -- implemented by hand below,
standard formula, e.g. Lehmann 1975 / Wikipedia "Mann-Whitney U test" ->
"Normal approximation and tie correction").
Categorical observables (2,3,4): descriptive distribution only (chi-square across
sparse per-date/per-ticker cells is underpowered and not attempted; reported as
proportions).

Multiple-comparison handling: 5 continuous tests -> Bonferroni alpha = 0.05/5 = 0.01.
Stated BEFORE results below, applied mechanically after.

Run on VPS. Read-only (loads portfolio + T-571 verification JSON only).
"""
import json
import math
import sys
sys.path.insert(0, "src")
from prediction_market_bot import logic_epoch as le  # noqa: E402

CONTINUOUS_OBSERVABLES = [
    "mid_price_at_entry",
    "gross_edge",
    "h_so_far_at_entry",
    "ab_remaining_at_entry",
    "size_usd",
]
ALPHA_BONFERRONI = 0.05 / len(CONTINUOUS_OBSERVABLES)


def mann_whitney_u(x, y):
    """Two-sided MWU, normal approximation with tie correction. Returns (U, z, p)."""
    n1, n2 = len(x), len(y)
    combined = [(v, 0) for v in x] + [(v, 1) for v in y]
    combined.sort(key=lambda t: t[0])
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    r1 = sum(r for r, (v, g) in zip(ranks, combined) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    n = n1 + n2
    tie_groups = []
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        tie_groups.append(j - i)
        i = j
    tie_correction = sum(t**3 - t for t in tie_groups)
    mu = n1 * n2 / 2.0
    sigma2 = (n1 * n2 / 12.0) * ((n + 1) - tie_correction / (n * (n - 1))) if n > 1 else 0
    sigma = math.sqrt(sigma2) if sigma2 > 0 else 1e-9
    z = (u1 - mu) / sigma
    p = 2 * (1 - _norm_cdf(abs(z)))
    return u1, z, p


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def main():
    portfolio = json.load(open("logs/paper_portfolio_mlb_t4.json"))
    closed = portfolio.get("closed_positions", [])
    by_pid = {
        p["position_id"]: p for p in closed
        if p.get("band") == "T4M-PROJ" and le.is_clean_for_band(p.get("logic_epoch"), "T4M-PROJ")
    }
    verif = json.load(open("/tmp/t571_kalshi_verification_results.json"))
    results = verif["results"]
    filled = [r for r in results if r["verdict"] == "FILLED"]
    nr = [r for r in results if r["verdict"] == "NOT_RETRIEVABLE"]

    print(f"n_filled={len(filled)} n_not_retrievable={len(nr)}")
    print(f"Bonferroni alpha per test = {ALPHA_BONFERRONI:.5f} (5 continuous tests)\n")

    print("=== CONTINUOUS OBSERVABLES: Mann-Whitney U, FILLED vs NOT_RETRIEVABLE ===")
    for field in CONTINUOUS_OBSERVABLES:
        xs = [by_pid[r["position_id"]][field] for r in filled if r["position_id"] in by_pid and by_pid[r["position_id"]].get(field) is not None]
        ys = [by_pid[r["position_id"]][field] for r in nr if r["position_id"] in by_pid and by_pid[r["position_id"]].get(field) is not None]
        if not xs or not ys:
            print(f"  {field}: insufficient data (n_filled={len(xs)}, n_nr={len(ys)})")
            continue
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        u, z, p = mann_whitney_u(xs, ys)
        sig = "SIGNIFICANT (survives Bonferroni)" if p < ALPHA_BONFERRONI else "not significant"
        print(f"  {field:28s} mean_FILLED={mean_x:10.4f} mean_NR={mean_y:10.4f} n_f={len(xs):3d} n_nr={len(ys):4d} U={u:9.1f} z={z:7.3f} p={p:.5f}  {sig}")

    print("\n=== CATEGORICAL OBSERVABLES: descriptive distribution ===")
    for field in ["kalshi_threshold", "game_date"]:
        from collections import Counter
        f_dist = Counter(by_pid[r["position_id"]].get(field) for r in filled if r["position_id"] in by_pid)
        nr_dist = Counter(by_pid[r["position_id"]].get(field) for r in nr if r["position_id"] in by_pid)
        f_total = sum(f_dist.values())
        nr_total = sum(nr_dist.values())
        print(f"  {field}:")
        keys = sorted(set(f_dist) | set(nr_dist), key=lambda k: (k is None, k))
        for k in keys:
            fp = f_dist.get(k, 0) / f_total if f_total else 0
            nrp = nr_dist.get(k, 0) / nr_total if nr_total else 0
            print(f"    {str(k):14s} FILLED: {f_dist.get(k,0):3d} ({fp*100:5.1f}%)   NR: {nr_dist.get(k,0):4d} ({nrp*100:5.1f}%)")

    # ticker/event clustering -- do FILLED rows cluster in a narrow set of games/events?
    f_dates = set(by_pid[r["position_id"]].get("game_date") for r in filled if r["position_id"] in by_pid)
    nr_dates = set(by_pid[r["position_id"]].get("game_date") for r in nr if r["position_id"] in by_pid)
    print(f"\n  distinct game_dates: FILLED spans {len(f_dates)} dates {sorted(f_dates)}")
    print(f"  distinct game_dates: NOT_RETRIEVABLE spans {len(nr_dates)} dates {sorted(nr_dates)}")
    print(f"  FILLED dates NOT covered by NR: {f_dates - nr_dates}")
    print(f"  NR dates NOT covered by FILLED: {nr_dates - f_dates}")


if __name__ == "__main__":
    main()

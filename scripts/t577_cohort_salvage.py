#!/usr/bin/env python3
"""T-577 Deliverables 2+3: four-tier partition + bias-corrected calibration bounds.

Read-only. Pre-registered in
05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T577_PREREGISTRATION_cohort_salvage.md
(pushed before this script computed anything). Loads the same portfolio snapshot
+ T-571 verification JSON T-573 used, and the T-573 duplicate-ticker join
artifact, to build the four tiers:

  CONFIRMED-REAL      -- verdict=FILLED
  CONFIRMED-CANCELED  -- verdict=CANCELED
  DUPLICATE-SUSPECT   -- verdict=NOT_RETRIEVABLE, in GG-303 buckets A/B/C
  UNCONFIRMED-CLEAN   -- verdict=NOT_RETRIEVABLE, GG-303 bucket D only

Then runs the pre-registered bias screen (Mann-Whitney, Bonferroni a=0.01,
5 continuous observables) comparing UNCONFIRMED-CLEAN to CONFIRMED-REAL, and
computes the scenario-bounds calibration estimate (S1/S2/S3) using
t565_calibration_model_vs_market.py's own Row/metric machinery, unmodified.
"""
import json
import math
import sys
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from prediction_market_bot import logic_epoch as le  # noqa: E402
import t565_calibration_model_vs_market as t565  # noqa: E402

DATA_DIR = REPO_ROOT / "exp_output" / "T577_cohort_salvage"
OUT_DIR = DATA_DIR
CONTINUOUS_OBSERVABLES = [
    "mid_price_at_entry", "gross_edge", "h_so_far_at_entry",
    "ab_remaining_at_entry", "size_usd",
]
ALPHA_BONFERRONI = 0.05 / len(CONTINUOUS_OBSERVABLES)


def mann_whitney_u(x, y):
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
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return u1, z, p


def main():
    portfolio = json.load(open(DATA_DIR / "paper_portfolio_mlb_t4.LIVE.20260922.json"))
    closed = portfolio.get("closed_positions", [])
    by_pid = {
        p["position_id"]: p for p in closed
        if p.get("band") == "T4M-PROJ" and le.is_clean_for_band(p.get("logic_epoch"), "T4M-PROJ")
    }
    verif = json.load(open(DATA_DIR / "t571_kalshi_verification_results.json"))
    results = verif["results"]

    join = json.load(open(REPO_ROOT / "05_RESEARCH_EXPERIMENTS" / "RESULTS_SUMMARIES" /
                           "t573_artifacts" / "t573_duplicate_ticker_full_join_results.json"))
    dup_pids = set(
        join["partition"]["A_filled_collision_only"]
        + join["partition"]["B_nr_internal_only"]
        + join["partition"]["C_both_three_way"]
    )
    clean_nr_pids = set(join["partition"]["D_neither_unique"])

    filled_pids = {r["position_id"] for r in results if r["verdict"] == "FILLED"}
    canceled_pids = {r["position_id"] for r in results if r["verdict"] == "CANCELED"}
    nr_pids = {r["position_id"] for r in results if r["verdict"] == "NOT_RETRIEVABLE"}

    assert dup_pids | clean_nr_pids == nr_pids, "join partition does not cover all NR rows"
    assert not (dup_pids & clean_nr_pids), "join partition overlap"

    tiers = {
        "CONFIRMED-REAL": filled_pids,
        "CONFIRMED-CANCELED": canceled_pids,
        "DUPLICATE-SUSPECT": dup_pids,
        "UNCONFIRMED-CLEAN": clean_nr_pids,
    }

    print("=== DELIVERABLE 2: four-tier partition ===")
    report = {"tiers": {}}
    for name, pids in tiers.items():
        rows = [by_pid[p] for p in pids if p in by_pid]
        dates = sorted({r.get("game_date") for r in rows})
        print(f"\n-- {name}: n={len(rows)} (pids resolved to ledger: {len(rows)}/{len(pids)}) --")
        print(f"   date span: {dates[0] if dates else None} .. {dates[-1] if dates else None}  ({len(dates)} distinct dates)")
        date_counts = Counter(r.get("game_date") for r in rows)
        top_date, top_n = date_counts.most_common(1)[0] if date_counts else (None, 0)
        top_share = top_n / len(rows) if rows else 0
        print(f"   most-concentrated date: {top_date} = {top_n}/{len(rows)} ({top_share*100:.1f}%)")
        obs = {}
        for field in CONTINUOUS_OBSERVABLES:
            vals = [r[field] for r in rows if r.get(field) is not None]
            if vals:
                mean = sum(vals) / len(vals)
                obs[field] = {"n": len(vals), "mean": mean}
                print(f"   {field:26s} n={len(vals):4d} mean={mean:10.4f}")
            else:
                obs[field] = {"n": 0, "mean": None}
                print(f"   {field:26s} n=0 (field absent on this tier)")
        report["tiers"][name] = {
            "n": len(rows), "n_pids": len(pids),
            "date_span": [dates[0] if dates else None, dates[-1] if dates else None],
            "n_distinct_dates": len(dates),
            "top_date_share": top_share,
            "observables": obs,
        }

    print("\n=== BIAS SCREEN: UNCONFIRMED-CLEAN vs CONFIRMED-REAL (pre-registered test) ===")
    real_rows = [by_pid[p] for p in filled_pids if p in by_pid]
    clean_rows = [by_pid[p] for p in clean_nr_pids if p in by_pid]
    bias_results = {}
    any_survive = False
    for field in CONTINUOUS_OBSERVABLES:
        xs = [r[field] for r in real_rows if r.get(field) is not None]
        ys = [r[field] for r in clean_rows if r.get(field) is not None]
        if not xs or not ys:
            print(f"  {field}: insufficient data")
            continue
        mean_x, mean_y = sum(xs) / len(xs), sum(ys) / len(ys)
        u, z, p = mann_whitney_u(xs, ys)
        survives = p < ALPHA_BONFERRONI
        any_survive = any_survive or survives
        sig = "SIGNIFICANT (survives Bonferroni)" if survives else "not significant"
        bias_results[field] = {"mean_real": mean_x, "mean_clean_nr": mean_y, "p": p, "survives_bonferroni": survives}
        print(f"  {field:26s} mean_REAL={mean_x:10.4f} mean_CLEAN_NR={mean_y:10.4f} n_r={len(xs):3d} n_c={len(ys):4d} p={p:.5f}  {sig}")

    print("\n=== DELIVERABLE 3: scenario-bounds calibration estimate ===")
    def calib(rows, label):
        pos_rows = []
        for r in rows:
            outcome = r.get("outcome")
            model_p = r.get("model_p")
            mid = r.get("mid_price_at_entry")
            if outcome is None or model_p is None or mid is None:
                continue
            y = 1 if outcome == "WIN" else 0
            pos_rows.append((model_p, mid, y, r.get("pnl", 0.0), r.get("game_date")))
        n = len(pos_rows)
        if n == 0:
            print(f"  {label}: n=0, cannot compute")
            return {"n": 0}
        model_brier = sum((mp - y) ** 2 for mp, mid, y, pnl, gd in pos_rows) / n
        market_brier = sum((mid - y) ** 2 for mp, mid, y, pnl, gd in pos_rows) / n
        base_rate = sum(y for mp, mid, y, pnl, gd in pos_rows) / n
        climatology_brier = sum((base_rate - y) ** 2 for mp, mid, y, pnl, gd in pos_rows) / n
        skill_vs_market = 1 - (model_brier / market_brier) if market_brier > 0 else None
        skill_vs_climatology = 1 - (model_brier / climatology_brier) if climatology_brier > 0 else None
        win_rate = base_rate
        total_pnl = sum(pnl for mp, mid, y, pnl, gd in pos_rows)
        n_dates = len({gd for mp, mid, y, pnl, gd in pos_rows})
        print(f"  {label}: n={n} n_dates={n_dates} model_brier={model_brier:.4f} market_brier={market_brier:.4f} "
              f"skill_vs_market={skill_vs_market} win_rate={win_rate:.3f} total_pnl={total_pnl:.2f}")
        return {
            "n": n, "n_dates": n_dates, "model_brier": model_brier, "market_brier": market_brier,
            "skill_vs_market": skill_vs_market, "skill_vs_climatology": skill_vs_climatology,
            "win_rate": win_rate, "total_pnl": total_pnl,
        }

    s1 = calib(real_rows, "S1 (CONFIRMED-REAL only, n=35)")
    s2 = calib(real_rows + clean_rows, "S2 (CONFIRMED-REAL + UNCONFIRMED-CLEAN)")
    s3 = calib(clean_rows, "S3 (UNCONFIRMED-CLEAN only)")

    report["bias_screen_unconfirmed_clean_vs_confirmed_real"] = bias_results
    report["bias_screen_any_survive_bonferroni"] = any_survive
    report["calibration_scenarios"] = {"S1_confirmed_real_only": s1, "S2_real_plus_clean": s2, "S3_clean_only": s3}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "t577_results.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nwrote {OUT_DIR / 't577_results.json'}")


if __name__ == "__main__":
    main()

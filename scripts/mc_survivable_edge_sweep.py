#!/usr/bin/env python3
"""
Survivable-Edge Frontier Sweep  (2026-07-23, Window B / GG ruin-geometry finding)
==================================================================================

WHY THIS EXISTS
---------------
`mc_empirical_bootstrap.py` (2026-07-22) established that both books, at their
*current* real cohort edge/variance/cadence/kill-switch geometry, are at or
near certain to trip the permanent 20% drawdown kill within a year -- and,
critically, that the MAIN book hits ~100% 1yr kill even at *zero* edge, purely
from variance x cadence (the "ruin geometry" finding, Window B1's governance
gap). That report answers "what happens at the observed cohorts." It does not
answer the follow-on question this script answers: **holding real variance
shape and real cadence fixed, how much edge would be needed to survive, and
how much room is there in Kelly-fraction / drawdown-switch-width / cadence
before a genuine positive edge gets killed by variance anyway?**

METHOD
------
Reuses `mc_empirical_bootstrap.load_book_fracs` / `cohort_fracs` to pull the
real per-bet fractional-bankroll-impact pool from each book's live ledger
cache (the "full" cohort -- largest n, most stable variance estimate; MAIN
std_frac and T4 std_frac are within ~15% of the strict-e8 cohort's own std,
so this is not a sensitive choice). From that pool we take ONLY the empirical
*shape* of per-bet log-return variance (`sig_g_base = std(log1p(frac))`) --
the mean is discarded and replaced by a swept `target_edge` so this becomes a
genuine what-if tool, not a re-statement of the (currently ~zero/negative)
observed edge.

Three levers, each a multiplier/override on the real per-book baseline:
  * `kelly_mult`   -- scales both mean and stdev of per-bet log-return
                      (bigger stake -> proportionally bigger P&L swing at a
                      fixed per-unit-stake edge; a stake-scaling model, not a
                      probability-edge model).
  * `cadence_mult` -- scales real observed bets/calendar-day.
  * `kill_dd`      -- permanent peak-drawdown kill threshold (replaces the
                      real risk.py 0.20 for the sweep only).
  * `daily_breaker`-- intraday breaker (replaces the real ADR-0012 0.15).

Same day-by-day compounding + kill mechanics as `mc_empirical_bootstrap.py`
(15% intraday breaker applied in log-space, 20%-from-peak permanent kill
evaluated at day-close), just parameterized. This script does NOT modify or
depend on any live risk.py constant -- it is a pure forward-looking research
sweep, output is advisory (feeds a future ADR per Window B3), not self-executing.

Part A -- bisection: minimum `target_edge` (holding kelly_mult=1, cadence_mult=1,
  kill_dd=0.20, daily_breaker=0.15 -- i.e. the REAL current risk config) such
  that 1yr P(kill) <= TARGET_PKILL (0.10).
Part B -- grid: for a handful of illustrative `target_edge` scenarios, the
  max kelly_mult / max cadence_mult / min kill_dd (each swept alone, others
  held at real current values) that holds 1yr P(kill) <= TARGET_PKILL.

Usage:
  PYTHONPATH=src python3 scripts/mc_survivable_edge_sweep.py --out logs/mc_survivable_edge_sweep.json
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

from mc_empirical_bootstrap import (
    MAIN_CACHE, T4_CACHE, load_book_fracs, cohort_fracs,
    START_BANKROLL, HORIZONS, KILL_DD, DAILY_BREAKER, SEED,
)

ROOT = Path(__file__).resolve().parent.parent
TARGET_PKILL = 0.10
HORIZON_1YR = 365

GRID_KELLY = [0.10, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00, 3.00]
GRID_CADENCE = [0.10, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00]
GRID_DD = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

# Illustrative what-if edge scenarios (decimal, per-bet log-return mean).
# 0.0 = breakeven; others span from the report's own near-zero "full history"
# cohort reads up through a clearly-positive hypothetical. NOT empirical
# claims -- labeled per-book below against each book's own real full-history
# edge for context.
EDGE_SCENARIOS = [0.0, 0.0002, 0.0005, 0.0010, 0.0020]


def day_params(sig_g_base, lambda_cal, target_edge, kelly_mult, cadence_mult):
    mu_g = kelly_mult * target_edge
    sig_g = kelly_mult * sig_g_base
    D = max(1, round(lambda_cal * cadence_mult))
    day_mu = D * mu_g
    day_sig = math.sqrt(D) * sig_g
    return day_mu, day_sig


def simulate_1yr_pkill(day_mu, day_sig, n_sims, rng, kill_dd, daily_breaker,
                        horizon=HORIZON_1YR):
    log_floor = math.log(1.0 - daily_breaker)
    B = np.full(n_sims, START_BANKROLL, dtype=np.float64)
    peak = B.copy()
    alive = np.ones(n_sims, dtype=bool)
    ever_killed = np.zeros(n_sims, dtype=bool)
    for _day in range(1, horizon + 1):
        day_log = rng.normal(day_mu, day_sig, size=n_sims)
        np.maximum(day_log, log_floor, out=day_log)
        mult = np.exp(day_log)
        mult[~alive] = 1.0
        B *= mult
        peak = np.maximum(peak, B)
        breach = alive & (B <= peak * (1.0 - kill_dd))
        if breach.any():
            ever_killed |= breach
            alive &= ~breach
    return float(np.mean(ever_killed))


def bisect_min_edge(sig_g_base, lambda_cal, rng, n_sims, kill_dd, daily_breaker,
                     lo=-0.0005, hi=0.02, iters=16):
    """Min target_edge s.t. 1yr P(kill) <= TARGET_PKILL, real cadence/kelly=1x."""
    def pkill_at(edge):
        mu, sig = day_params(sig_g_base, lambda_cal, edge, 1.0, 1.0)
        return simulate_1yr_pkill(mu, sig, n_sims, rng, kill_dd, daily_breaker)

    p_hi = pkill_at(hi)
    if p_hi > TARGET_PKILL:
        return None, p_hi  # even the upper bound can't survive -- report as such
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        p = pkill_at(mid)
        if p <= TARGET_PKILL:
            hi = mid
        else:
            lo = mid
    return hi, pkill_at(hi)


def sweep_lever(sig_g_base, lambda_cal, rng, n_sims, target_edge, lever, grid):
    """Return list of (grid_value, p_kill_1yr) holding others at real/current."""
    out = []
    for v in grid:
        if lever == "kelly":
            mu, sig = day_params(sig_g_base, lambda_cal, target_edge, v, 1.0)
            p = simulate_1yr_pkill(mu, sig, n_sims, rng, KILL_DD, DAILY_BREAKER)
        elif lever == "cadence":
            mu, sig = day_params(sig_g_base, lambda_cal, target_edge, 1.0, v)
            p = simulate_1yr_pkill(mu, sig, n_sims, rng, KILL_DD, DAILY_BREAKER)
        elif lever == "dd":
            mu, sig = day_params(sig_g_base, lambda_cal, target_edge, 1.0, 1.0)
            p = simulate_1yr_pkill(mu, sig, n_sims, rng, v, DAILY_BREAKER)
        else:
            raise ValueError(lever)
        out.append((v, p))
    return out


def frontier_from_sweep(points, higher_is_riskier):
    """Max (or min, if not higher_is_riskier) grid value with p<=TARGET_PKILL."""
    passing = [v for v, p in points if p <= TARGET_PKILL]
    if not passing:
        return None
    return max(passing) if higher_is_riskier else min(passing)


def main():
    t0 = time.time()
    books = {
        "MAIN (T1/T2/T3)": (MAIN_CACHE, "main"),
        "T4 (T4M-PROJ)": (T4_CACHE, "t4"),
    }
    rng = np.random.default_rng(SEED)
    results = {"meta": {
        "target_pkill_1yr": TARGET_PKILL, "seed": SEED,
        "start_bankroll": START_BANKROLL,
        "real_kill_dd": KILL_DD, "real_daily_breaker": DAILY_BREAKER,
        "edge_scenarios": EDGE_SCENARIOS,
        "grid_kelly_mult": GRID_KELLY, "grid_cadence_mult": GRID_CADENCE,
        "grid_kill_dd": GRID_DD,
    }, "books": {}}

    for bname, (path, _tag) in books.items():
        book = load_book_fracs(path)
        fracs, sel = cohort_fracs(book["closed"], "full")
        g = np.log1p(np.asarray(fracs, dtype=np.float64))
        sig_g_base = float(np.std(g))
        real_mean_frac = float(np.mean(fracs))
        lambda_cal = book["lambda_cal"]

        print(f"\n{'='*70}\nBOOK: {bname}  cadence={lambda_cal:.2f}/day  "
              f"real_full_hist_mean_frac={real_mean_frac*100:+.4f}%/bet  "
              f"sig_g_base={sig_g_base*100:.4f}%")

        # --- Part A: bisection at REAL current config (kelly=1x, cadence=1x,
        #     kill_dd=0.20, daily_breaker=0.15) ---
        min_edge, p_at_min = bisect_min_edge(
            sig_g_base, lambda_cal, rng, n_sims=30000,
            kill_dd=KILL_DD, daily_breaker=DAILY_BREAKER)
        print(f"  [Part A] min per-bet edge for 1yr P(kill)<=10% "
              f"(real cadence/Kelly/DD): "
              f"{'NONE FOUND up to +2.0%/bet' if min_edge is None else f'{min_edge*100:+.4f}%/bet (verified p={p_at_min:.3f})'}")

        # --- Part B: per-lever grid, per edge scenario ---
        part_b = {}
        for edge in EDGE_SCENARIOS:
            kelly_pts = sweep_lever(sig_g_base, lambda_cal, rng, 8000, edge, "kelly", GRID_KELLY)
            cadence_pts = sweep_lever(sig_g_base, lambda_cal, rng, 8000, edge, "cadence", GRID_CADENCE)
            dd_pts = sweep_lever(sig_g_base, lambda_cal, rng, 8000, edge, "dd", GRID_DD)
            max_kelly = frontier_from_sweep(kelly_pts, higher_is_riskier=True)
            max_cadence = frontier_from_sweep(cadence_pts, higher_is_riskier=True)
            min_dd = frontier_from_sweep(dd_pts, higher_is_riskier=False)
            part_b[f"{edge:.4f}"] = {
                "target_edge_pct_per_bet": edge * 100,
                "kelly_mult_sweep": kelly_pts,
                "cadence_mult_sweep": cadence_pts,
                "kill_dd_sweep": dd_pts,
                "max_kelly_mult_surviving": max_kelly,
                "max_cadence_mult_surviving": max_cadence,
                "min_kill_dd_surviving": min_dd,
            }
            print(f"  [Part B] edge={edge*100:+.3f}%/bet -> "
                  f"max_kelly_mult={max_kelly}  max_cadence_mult={max_cadence}  "
                  f"min_kill_dd={min_dd}")

        results["books"][bname] = {
            "cadence_per_day": lambda_cal,
            "n_closed_full": book["n_closed"],
            "real_full_hist_mean_frac_pct": real_mean_frac * 100,
            "sig_g_base_pct": sig_g_base * 100,
            "part_a_min_edge_pct_per_bet": None if min_edge is None else min_edge * 100,
            "part_a_pkill_at_min_edge": p_at_min,
            "part_b": part_b,
        }

    outp = ROOT / "logs" / "mc_survivable_edge_sweep.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(outp, "w"), indent=2)
    print(f"\nWrote {outp}  ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

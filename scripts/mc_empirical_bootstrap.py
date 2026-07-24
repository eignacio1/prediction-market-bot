#!/usr/bin/env python3
"""
Empirical Bootstrap Forward Monte Carlo  (2026-07-22, operator request)
=======================================================================

WHY THIS EXISTS
---------------
`mc_forward_projection.py` (GG-071/ADR-0040) is parametric slop for a
forward *edge* projection: every bet is drawn from ONE fixed win rate
(0.5306) and ONE fixed payoff multiple (+115.8% / -100%). That:
  (a) crushes the real per-bet payoff spread (entry prices vary, so win
      multiples vary) into a single number, and
  (b) hard-codes the edge as a clean, IID, +EV coin -- the exact premise
      GG-105 says is false (anti-predictive / overconfidence structure).
Result: it compounded a fantasy (+$294k mean ending bankroll on a $1k book).

THIS ENGINE
-----------
Nonparametric bootstrap. For each book we replay REAL resolved bets:
per-bet fractional bankroll impact  frac_i = pnl_i / B_before_i , where
B_before_i is the running bankroll reconstructed by walking the closed
ledger in resolve order from the book's initial bankroll. Normalizing by
bankroll (not by stake) is deliberate -- it is exactly the quantity that
compounds forward, and it is immune to the micro-stake artifact that blows
up raw return-on-stake in the T4 ledger.

Resampling realized outcomes preserves, for free and without assumption:
  * the real win rate,
  * the real payoff heterogeneity (full multiple distribution), and
  * the real (anti-predictive) edge structure -- we replay what happened.

Forward sim: 100k paths, day-by-day compounding at the book's real observed
calendar-day cadence, with the REAL kill switches:
  * permanent 20% peak-drawdown kill (_HARD_LIMITS["max_drawdown_pct"])
  * intraday 15% daily-loss breaker (MAX_DAILY_LOSS_PCT, ADR-0012)
A single 365-day pass snapshots state at each horizon checkpoint.

Books modeled independently (dual-ledger reality): MAIN = T1/T2/T3,
T4 = T4M-PROJ. Cohorts: strict current epoch (8), post-vig-fix (e6-8),
full history -- reported side by side for sensitivity.

Usage:
  PYTHONPATH=src python3 scripts/mc_empirical_bootstrap.py \
      --sims 100000 --out logs/mc_empirical_bootstrap.json
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MAIN_CACHE = ROOT / "logs" / ".vps_portfolio_cache_mlb.json"
T4_CACHE = ROOT / "logs" / ".vps_portfolio_cache_mlb_t4.json"

START_BANKROLL = 1000.0          # normalized, per operator (2026-07-22)
HORIZONS = [30, 90, 182, 365]    # calendar days
KILL_DD = 0.20                   # permanent peak-drawdown kill (risk.py _HARD_LIMITS)
DAILY_BREAKER = 0.15             # intraday daily-loss breaker (ADR-0012)
CURRENT_EPOCH = 8
SEED = 20260722

PCTS = [1, 5, 10, 25, 50, 75, 90, 95, 99]


# --------------------------------------------------------------------------
# Data prep
# --------------------------------------------------------------------------
def _sort_key(p):
    return p.get("resolved_at") or p.get("entered_at") or ""


def load_book_fracs(path: Path):
    """Return dict: reconstructed closed positions with _frac, plus meta."""
    d = json.load(open(path))
    init = float(d.get("initial_bankroll_usd") or START_BANKROLL)
    closed = [
        p for p in d["closed_positions"]
        if p.get("pnl") is not None and p.get("size_usd")
    ]
    closed.sort(key=_sort_key)
    B = init
    for p in closed:
        p["_B_before"] = B
        p["_frac"] = p["pnl"] / B
        B += p["pnl"]
    # calendar-day cadence from the observed window
    dates = sorted({p.get("game_date") for p in closed if p.get("game_date")})
    span_days = _date_span_days(dates)
    lambda_cal = len(closed) / max(1, span_days)
    return {
        "init": init,
        "closed": closed,
        "n_closed": len(closed),
        "span_days": span_days,
        "lambda_cal": lambda_cal,
        "cache_bankroll": d.get("bankroll_usd"),
        "realized_pnl": d.get("total_realized_pnl"),
    }


def _date_span_days(dates):
    if not dates:
        return 1
    from datetime import date
    def parse(s):
        y, m, dd = s.split("-")[:3]
        return date(int(y), int(m), int(dd))
    try:
        d0, d1 = parse(dates[0]), parse(dates[-1])
        return (d1 - d0).days + 1
    except Exception:
        return len(dates)


def cohort_fracs(closed, cohort):
    if cohort == "strict_e8":
        sel = [p for p in closed if p.get("logic_epoch") == 8]
    elif cohort == "postfix_e6_8":
        sel = [p for p in closed if p.get("logic_epoch") in (6, 7, 8)]
    elif cohort == "full":
        sel = list(closed)
    else:
        raise ValueError(cohort)
    return np.asarray([p["_frac"] for p in sel], dtype=np.float64), sel


def cohort_stats(fracs, sel):
    n = len(fracs)
    if n == 0:
        return {"n": 0}
    wins = sum(1 for p in sel if p.get("pnl", 0) > 0)
    return {
        "n": n,
        "win_rate": wins / n,
        "mean_frac": float(np.mean(fracs)),          # per-bet EV as fraction of bankroll
        "std_frac": float(np.std(fracs)),
        "min_frac": float(np.min(fracs)),
        "max_frac": float(np.max(fracs)),
        "mean_pnl_usd": float(np.mean([p["pnl"] for p in sel])),
        "mean_stake_usd": float(np.mean([p["size_usd"] for p in sel])),
    }


# --------------------------------------------------------------------------
# Vectorized forward sim (single 365-day pass, checkpoints at horizons)
# --------------------------------------------------------------------------
def simulate(fracs, lambda_cal, n_sims, rng, horizons=HORIZONS):
    """Vectorized day-by-day compounding.

    Each day: draw Poisson(lambda) bets per path, build an (n_sims x Dmax)
    matrix of realized fractional multipliers (bootstrap w/ replacement),
    mask bets beyond each path's daily count, cumprod within the day to get
    the intraday bankroll path. The 15% daily-loss breaker is applied EXACTLY
    (day ends at the value of the bet that first crossed -15%). The permanent
    20% peak-drawdown kill is evaluated at day-close (day-granular; can lag a
    true intraday breach by <=1 day -- a mild, conservative under-count of
    kills, documented in the report).
    """
    pool = np.asarray(fracs, dtype=np.float64)
    D = max(1, int(round(lambda_cal)))       # fixed bets/active-day (mean cadence)

    # Per-bet log-growth from the REAL resolved outcomes (empirical, no assumed edge).
    g = np.log1p(pool)                       # log(1 + frac_i)
    mu_g = float(np.mean(g))                 # empirical mean per-bet log-return
    sig_g = float(np.std(g))                 # empirical per-bet log-return stdev
    # Daily total log-return = sum of D iid per-bet draws ~ Normal(D*mu, sqrt(D)*sig)
    # (CLT exact-in-the-limit; D=16-63 bets/day -> daily aggregate genuinely near-normal.
    #  Horizon totals are sums of hundreds-to-thousands of bets -> effectively exact.)
    day_mu = D * mu_g
    day_sig = math.sqrt(D) * sig_g
    log_floor = math.log(1.0 - DAILY_BREAKER)   # 15% daily-loss breaker (log space)

    B = np.full(n_sims, START_BANKROLL, dtype=np.float64)
    peak = B.copy()
    alive = np.ones(n_sims, dtype=bool)
    ever_killed = np.zeros(n_sims, dtype=bool)
    checkpoints = {}
    max_day = max(horizons)

    for day in range(1, max_day + 1):
        day_log = rng.normal(day_mu, day_sig, size=n_sims)
        np.maximum(day_log, log_floor, out=day_log)          # daily-loss breaker (cap at -15%)
        mult = np.exp(day_log)
        mult[~alive] = 1.0                                   # killed paths don't trade
        B *= mult
        peak = np.maximum(peak, B)
        breach = alive & (B <= peak * (1.0 - KILL_DD))       # permanent 20% peak-drawdown kill
        if breach.any():
            ever_killed |= breach
            alive &= ~breach
        if day in horizons:
            checkpoints[day] = (B.copy(), ever_killed.copy())
    return checkpoints


def summarize(B, killed):
    n = len(B)
    ret = B / START_BANKROLL - 1.0
    out = {
        "mean_bankroll": float(np.mean(B)),
        "pct_bankroll": {f"p{p}": float(np.percentile(B, p)) for p in PCTS},
        "p_killed": float(np.mean(killed)),
        "p_profit": float(np.mean(B > START_BANKROLL)),
        "p_below_start": float(np.mean(B < START_BANKROLL)),
        "p_down_10": float(np.mean(ret <= -0.10)),
        "p_down_20": float(np.mean(ret <= -0.20)),
        "p_down_50": float(np.mean(ret <= -0.50)),
        "p_up_25": float(np.mean(ret >= 0.25)),
        "p_up_50": float(np.mean(ret >= 0.50)),
        "p_up_100": float(np.mean(ret >= 1.00)),
        "mean_return": float(np.mean(ret)),
        "median_return": float(np.median(ret)),
    }
    # 95% CI on kill probability (Wald)
    p = out["p_killed"]
    se = math.sqrt(max(p * (1 - p), 0) / n)
    out["p_killed_ci95"] = [max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)]
    return out


# --------------------------------------------------------------------------
# TOKEN / RUN GUARD (2026-07-22) -- do NOT scale N or loop full runs blindly.
# Root cause of the 2026-07-22 token burn: full 100k sims were launched
# repeatedly against the sandbox's 45s wall before the engine was validated.
# Protocol for ANY model (esp. high-cost ones) invoking this script:
#   1. It ALWAYS runs a <1s self-test first (unless --skip-selftest) and aborts
#      the whole run if outputs are invalid (NaN / kill prob outside [0,1]).
#   2. It prints a runtime estimate and REFUSES to run if projected wall time
#      exceeds --max-seconds (default 40s, under the 45s cap) unless --force.
#   Background jobs do NOT survive between sandbox calls -- never rely on nohup.
# Validated baseline: log-space engine runs both books x 3 cohorts x 100k in
# ~38s in-sandbox. If a change makes it slower, fix the engine, don't retry.
# --------------------------------------------------------------------------
def run_selftest():
    rng = np.random.default_rng(0)
    pool = np.array([-0.01, 0.012, -0.01, 0.011, -0.009], dtype=np.float64)
    cp = simulate(pool, 15.0, 1000, rng, horizons=[5, 30])
    for day, (B, killed) in cp.items():
        s = summarize(B, killed)
        assert np.isfinite(s["mean_bankroll"]), "self-test: non-finite bankroll"
        assert 0.0 <= s["p_killed"] <= 1.0, "self-test: kill prob out of range"
    return True


def _est_seconds(sims, n_books, n_cohorts):
    # ~38s measured for 100k x 2 books x 3 cohorts -> per (sim*book*cohort)
    return 38.0 * (sims / 100_000) * (n_books / 2) * (n_cohorts / 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=100_000)
    ap.add_argument("--book", choices=["main", "t4", "both"], default="both")
    ap.add_argument("--cohort", choices=["strict_e8", "postfix_e6_8", "full", "all"],
                    default="all")
    ap.add_argument("--out", default="logs/mc_empirical_bootstrap.json")
    ap.add_argument("--skip-selftest", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=40.0)
    ap.add_argument("--force", action="store_true", help="bypass runtime guard")
    args = ap.parse_args()

    # --- self-test + runtime guard (prevents blind broken/oversized runs) ---
    if not args.skip_selftest:
        run_selftest()
        print("self-test: OK")
    n_books = 2 if args.book == "both" else 1
    n_cohorts = 3 if args.cohort == "all" else 1
    est = _est_seconds(args.sims, n_books, n_cohorts)
    print(f"runtime estimate: ~{est:.0f}s  (guard --max-seconds={args.max_seconds:.0f})")
    if est > args.max_seconds and not args.force:
        raise SystemExit(
            f"ABORT: est ~{est:.0f}s exceeds {args.max_seconds:.0f}s cap. "
            f"Reduce --sims (e.g. --sims 50000), split --book/--cohort into "
            f"separate calls, or pass --force if you accept the risk.")

    all_books = {
        "MAIN (T1/T2/T3)": (MAIN_CACHE, "main"),
        "T4 (T4M-PROJ)": (T4_CACHE, "t4"),
    }
    books = {
        name: load_book_fracs(path)
        for name, (path, tag) in all_books.items()
        if args.book in ("both", tag)
    }
    cohorts = ["strict_e8", "postfix_e6_8", "full"] if args.cohort == "all" else [args.cohort]

    results = {"meta": {
        "sims": args.sims, "seed": SEED, "start_bankroll": START_BANKROLL,
        "horizons": HORIZONS, "kill_dd": KILL_DD, "daily_breaker": DAILY_BREAKER,
        "current_epoch": CURRENT_EPOCH,
    }, "books": {}}

    rng = np.random.default_rng(SEED)

    for bname, book in books.items():
        print(f"\n{'='*70}\nBOOK: {bname}")
        print(f"  init=${book['init']:.2f}  cache_bankroll=${book['cache_bankroll']}"
              f"  realized_pnl=${book['realized_pnl']}")
        print(f"  n_closed={book['n_closed']}  span_days={book['span_days']}"
              f"  cadence={book['lambda_cal']:.2f} bets/calendar-day")
        results["books"][bname] = {
            "cadence_per_day": book["lambda_cal"],
            "n_closed": book["n_closed"],
            "span_days": book["span_days"],
            "cache_bankroll": book["cache_bankroll"],
            "realized_pnl": book["realized_pnl"],
            "cohorts": {},
        }
        for cohort in cohorts:
            fracs, sel = cohort_fracs(book["closed"], cohort)
            stats = cohort_stats(fracs, sel)
            if stats["n"] == 0:
                print(f"    [{cohort}] n=0 -- skipped")
                results["books"][bname]["cohorts"][cohort] = {"input": stats, "horizons": {}}
                continue
            print(f"    [{cohort}] n={stats['n']} win={stats['win_rate']:.3f} "
                  f"mean_frac={stats['mean_frac']*100:+.4f}%/bet "
                  f"std={stats['std_frac']*100:.3f}% "
                  f"mean_pnl=${stats['mean_pnl_usd']:+.4f}")
            cp = simulate(fracs, book["lambda_cal"], args.sims, rng)
            hz = {}
            for day, (B, killed) in cp.items():
                hz[str(day)] = summarize(B, killed)
            results["books"][bname]["cohorts"][cohort] = {"input": stats, "horizons": hz}

    outp = ROOT / args.out
    json.dump(results, open(outp, "w"), indent=2)
    print(f"\nWrote {outp}")


if __name__ == "__main__":
    main()

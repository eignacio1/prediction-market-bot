"""
EXP-014: Line Shopping EV Simulation — Cross-Venue Vig Savings Analysis
========================================================================
Experiment ID:   EXP-014
Phase:           Phase 7 (T-077 infrastructure — Polymarket routing)
Status:          OFFLINE RUNNER — 2026-05-29

Purpose:
    Quantify the expected EV improvement from routing a fraction of bets to
    a cheaper venue (Polymarket) relative to the EXP-010 Kalshi-only baseline.
    Also estimates complement-lock frequency given realistic mid-price divergence.

Fully offline — no API key required.  Parametrises vig savings scenarios
using EXP-010 as the anchor (EV +$0.0958/bet, 871 bets, vig=0.030).

How to run:
    PYTHONPATH=src python3 src/prediction_market_bot/run_exp014.py

Security (NFR-05):
    No API keys. BOT_C4_ACTIVE must NOT be set.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from typing import Any

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

EXP_ID     = "EXP-014"
SESSION_ID = f"EXP-014-{uuid.uuid4().hex[:8].upper()}"
OUTPUT_DIR = Path("exp_output/EXP-014")

# Anchor metrics from EXP-010
EXP010_EV_PER_BET  = 0.095792
EXP010_N_BETS      = 871
EXP010_VIG_KALSHI  = 0.030
EXP010_WIN_RATE    = 0.6108
EXP010_BETS_YES    = 252
EXP010_BETS_NO     = 619

# Scenario grids
VIG_SAVINGS_SCENARIOS      = [0.005, 0.010, 0.015]
ROUTING_FRACTION_SCENARIOS = [0.25, 0.50, 0.75, 1.00]

# Lock frequency simulation
LOCK_DIV_STD        = 0.015   # mid-price divergence std between venues (conservative)
LOCK_MIN_NET_PROFIT = 0.001   # min net profit to count as a lock (matches ComplementLockScanner)
LOCK_MID_LOW        = 0.30    # lower bound for realistic market range
LOCK_MID_HIGH       = 0.70    # upper bound


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def simulate_vig_savings(
    ev_baseline: float,
    vig_baseline: float,
    vig_savings: float,
    routing_fraction: float,
    n_bets: int,
    win_rate: float,
    bets_yes: int,
    bets_no: int,
) -> dict[str, Any]:
    """
    Compute EV improvement from routing a fraction of bets to a cheaper venue.

    The cheaper venue saves `vig_savings` in total vig (absolute).  Because the
    spread is symmetric, half of that savings improves the execution price on
    each routed bet.

    Parameters
    ----------
    ev_baseline:       EV per bet at Kalshi-only (EXP-010 anchor).
    vig_baseline:      Kalshi vig (absolute, e.g. 0.030).
    vig_savings:       Absolute vig reduction on the cheaper venue (e.g. 0.010).
    routing_fraction:  Fraction of bets routed to the cheaper venue [0, 1].
    n_bets:            Total bets per season.
    win_rate:          Historical win rate (used for context; not in EV formula).
    bets_yes / bets_no: Directional bet counts (context only).
    """
    half_spread_savings = vig_savings / 2.0
    ev_delta_per_bet    = half_spread_savings * routing_fraction
    ev_per_bet_improved = ev_baseline + ev_delta_per_bet
    annual_dollar_improvement = ev_delta_per_bet * n_bets
    pct_improvement = (ev_delta_per_bet / ev_baseline * 100) if ev_baseline > 0 else 0.0

    return {
        "vig_savings": vig_savings,
        "routing_fraction": routing_fraction,
        "ev_per_bet_baseline": round(ev_baseline, 6),
        "ev_per_bet_improved": round(ev_per_bet_improved, 6),
        "ev_delta_per_bet": round(ev_delta_per_bet, 6),
        "annual_dollar_improvement": round(annual_dollar_improvement, 4),
        "pct_improvement": round(pct_improvement, 2),
    }


def estimate_lock_frequency(
    vig_kalshi: float,
    vig_polymarket: float,
    n_simulations: int = 50_000,
    seed: int = 42,
) -> dict[str, Any]:
    """
    Monte Carlo estimate of complement-lock frequency given spread distributions.

    Models each market as having a random base mid-price with a small divergence
    between Kalshi and Polymarket (information lag, liquidity differences).
    A lock exists when buying one side on Kalshi and the other on Polymarket
    costs less than $1.00 net (i.e., net profit > LOCK_MIN_NET_PROFIT).

    Parameters
    ----------
    vig_kalshi / vig_polymarket: absolute vigs for each venue.
    n_simulations:               number of random markets to simulate.
    seed:                        RNG seed for reproducibility.
    """
    rng = np.random.default_rng(seed)
    base_mid  = rng.uniform(LOCK_MID_LOW, LOCK_MID_HIGH, n_simulations)
    divergence = rng.normal(0, LOCK_DIV_STD, n_simulations)

    kalshi_mid = np.clip(base_mid, 0.01, 0.99)
    poly_mid   = np.clip(base_mid + divergence, 0.01, 0.99)

    # Lock A: buy YES on Kalshi + NO on Polymarket
    cost_yn  = (kalshi_mid + vig_kalshi / 2) + ((1 - poly_mid) + vig_polymarket / 2)
    # Lock B: buy NO on Kalshi + YES on Polymarket
    cost_ny  = ((1 - kalshi_mid) + vig_kalshi / 2) + (poly_mid + vig_polymarket / 2)

    profit_yn = 1.0 - cost_yn
    profit_ny = 1.0 - cost_ny

    locks     = (profit_yn > LOCK_MIN_NET_PROFIT) | (profit_ny > LOCK_MIN_NET_PROFIT)
    n_locks   = int(locks.sum())
    lock_freq = n_locks / n_simulations

    net_profits = np.maximum(profit_yn, 0.0) + np.maximum(profit_ny, 0.0)
    avg_net_profit = float(net_profits[locks].mean()) if n_locks > 0 else 0.0

    estimated_locks_per_season = lock_freq * EXP010_N_BETS

    return {
        "vig_kalshi":                  vig_kalshi,
        "vig_polymarket":              vig_polymarket,
        "lock_frequency":              round(lock_freq, 6),
        "avg_net_profit":              round(avg_net_profit, 6),
        "estimated_locks_per_season":  round(estimated_locks_per_season, 2),
    }


def run_sensitivity_grid(
    ev_baseline: float,
    n_bets: int,
    vig_baseline: float,
    win_rate: float,
    bets_yes: int,
    bets_no: int,
    vig_savings_scenarios: list[float],
    routing_fraction_scenarios: list[float],
) -> pd.DataFrame:
    """Full cross-product sensitivity grid; returns one row per (vig_savings, routing_fraction)."""
    rows = []
    for vs in vig_savings_scenarios:
        for rf in routing_fraction_scenarios:
            row = simulate_vig_savings(
                ev_baseline, vig_baseline, vs, rf, n_bets, win_rate, bets_yes, bets_no
            )
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE set.", file=sys.stderr); sys.exit(1)

    print(f"\n{'='*60}")
    print(f"EXP-014: Line Shopping EV Simulation")
    print(f"Session:  {SESSION_ID}")
    print(f"Anchor:   EXP-010 | EV {EXP010_EV_PER_BET:+.4f}/bet | vig={EXP010_VIG_KALSHI} | {EXP010_N_BETS} bets")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 1. Sensitivity grid
    # ------------------------------------------------------------------
    grid = run_sensitivity_grid(
        EXP010_EV_PER_BET, EXP010_N_BETS, EXP010_VIG_KALSHI,
        EXP010_WIN_RATE, EXP010_BETS_YES, EXP010_BETS_NO,
        VIG_SAVINGS_SCENARIOS, ROUTING_FRACTION_SCENARIOS,
    )

    print("EV SENSITIVITY GRID (per-bet EV improvement via line shopping)")
    print(f"{'Vig Savings':>12}  {'Routing %':>10}  {'EV/bet':>10}  {'Δ EV/bet':>10}  "
          f"{'Annual $ (×$1 bet)':>20}  {'% Improvement':>14}")
    print("-" * 82)
    for _, r in grid.iterrows():
        print(f"  {r['vig_savings']:.3f}         {r['routing_fraction']:.0%}        "
              f"{r['ev_per_bet_improved']:+.5f}   {r['ev_delta_per_bet']:+.6f}   "
              f"  {r['annual_dollar_improvement']:+8.4f}              {r['pct_improvement']:+.2f}%")

    best = grid.loc[grid["ev_per_bet_improved"].idxmax()]
    print(f"\n  Best case: vig_savings={best['vig_savings']:.3f} + routing={best['routing_fraction']:.0%} → "
          f"EV {best['ev_per_bet_improved']:+.5f} (+{best['pct_improvement']:.1f}%)")

    # ------------------------------------------------------------------
    # 2. Lock frequency analysis
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("COMPLEMENT LOCK FREQUENCY (cross-venue lock detection)")
    print(f"{'='*60}")
    print(f"{'Vig Kalshi':>12}  {'Vig Poly':>10}  {'Lock Freq':>10}  {'Avg Profit':>12}  {'Locks/Season':>14}")
    print("-" * 64)

    lock_results = []
    for vs in VIG_SAVINGS_SCENARIOS:
        vig_poly = EXP010_VIG_KALSHI - vs
        result = estimate_lock_frequency(EXP010_VIG_KALSHI, vig_poly)
        lock_results.append(result)
        print(f"  {result['vig_kalshi']:.3f}          {result['vig_polymarket']:.3f}     "
              f"  {result['lock_frequency']:.4f}      {result['avg_net_profit']:+.5f}      "
              f"  {result['estimated_locks_per_season']:.1f}")

    # ------------------------------------------------------------------
    # 3. Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("EXP-014 SUMMARY")
    print(f"{'='*60}")
    print(f"  Baseline EV/bet:  {EXP010_EV_PER_BET:+.4f}  (EXP-010, vig={EXP010_VIG_KALSHI})")
    print(f"  Best-case gain:   +{best['pct_improvement']:.1f}% EV improvement "
          f"({best['vig_savings']:.0f}pp vig savings, {best['routing_fraction']:.0%} routing)")
    print(f"  Lock baseline:    ~{lock_results[0]['estimated_locks_per_season']:.1f} locks/season "
          f"at vig_savings={VIG_SAVINGS_SCENARIOS[0]:.3f}")
    print(f"  Conclusion:       Line shopping adds marginal EV improvement; locks are rare "
          f"but detection infrastructure is ready (T-080).")

    # ------------------------------------------------------------------
    # 4. Save
    # ------------------------------------------------------------------
    out = {
        "exp_id": EXP_ID,
        "session_id": SESSION_ID,
        "run_at": _utc_now(),
        "anchor": {
            "source": "EXP-010",
            "ev_per_bet": EXP010_EV_PER_BET,
            "n_bets": EXP010_N_BETS,
            "vig_kalshi": EXP010_VIG_KALSHI,
            "win_rate": EXP010_WIN_RATE,
        },
        "sensitivity_grid": grid.to_dict(orient="records"),
        "lock_frequency_analysis": lock_results,
        "best_case": {
            "vig_savings": float(best["vig_savings"]),
            "routing_fraction": float(best["routing_fraction"]),
            "ev_per_bet_improved": float(best["ev_per_bet_improved"]),
            "pct_improvement": float(best["pct_improvement"]),
        },
    }
    out_path = OUTPUT_DIR / "EXP-014_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()

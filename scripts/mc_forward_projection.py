#!/usr/bin/env python3
"""
Prediction Market Bot — Forward-Time Compounding Monte Carlo (GG-071 / T-223)

Recreates the forward-time (calendar-day, compounding) ruin-risk simulation
first run in SESSION 113 (2026-07-02) and registered as GG-071. Unlike
run_monte_carlo.py (which answers "given the open book today, what's the P&L
distribution"), this script asks "if this edge and cadence persist, what does
the bankroll path look like a year out, and how often does it permanently
trip the 20% max-drawdown kill switch."

Mechanic modeled: proportional/Kelly-style stake sizing (risk.py
_compute_kelly_size) compounds a *fraction* of current bankroll each bet,
capped in absolute dollars at _HARD_LIMITS["max_single_event_exposure_usd"]
(=$500). The average observed T1 MLB stake fraction is ~1.153% of bankroll
per bet (GG-071) — this holds constant in percentage terms as bankroll grows
until 0.01153 * bankroll > $500, i.e. bankroll > ~$43,373, at which point the
absolute cap engages and further compounding slows.

Usage:
  PYTHONPATH=src python3 scripts/mc_forward_projection.py
  PYTHONPATH=src python3 scripts/mc_forward_projection.py --stake-frac 0.008
  PYTHONPATH=src python3 scripts/mc_forward_projection.py --cap 250
  PYTHONPATH=src python3 scripts/mc_forward_projection.py --sensitivity
  PYTHONPATH=src python3 scripts/mc_forward_projection.py --out logs/mc_forward.txt

Exit codes: 0 = success
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# GG-071 cited parameters — matched to real T1 MLB observed statistics
# (SESSION 113, 2026-07-02) and risk.py production constants.
# ---------------------------------------------------------------------------
WIN_RATE = 0.5306              # real T1 MLB win rate at time of GG-071 study
WIN_MULT = 1.158                # +115.8% avg payout multiple on a WIN
LOSS_MULT = 1.0                 # -100% of stake on a LOSS (binary Kalshi contract)
STAKE_FRAC = 0.01153             # avg observed stake as fraction of bankroll (proportional/Kelly)
CAP_USD = 500.0                  # _HARD_LIMITS["max_single_event_exposure_usd"] (risk.py)
BETS_PER_DAY = 26                # real T1 MLB cadence, active days
KILL_SWITCH_DD = 0.20            # _HARD_LIMITS["max_drawdown_pct"] (risk.py) — permanent kill switch
STARTING_BANKROLL = 1000.0       # matches DEFAULT_BANKROLL (run_monte_carlo.py) / initial_bankroll_usd

HORIZONS_DAYS = [30, 182, 365]   # 1mo / 6mo / 1yr, per GG-071
N_SIMS = 10_000
SEED = 42


@dataclass
class SimParams:
    win_rate: float = WIN_RATE
    win_mult: float = WIN_MULT
    loss_mult: float = LOSS_MULT
    stake_frac: float = STAKE_FRAC
    cap_usd: float = CAP_USD
    bets_per_day: int = BETS_PER_DAY
    kill_switch_dd: float = KILL_SWITCH_DD
    starting_bankroll: float = STARTING_BANKROLL


def simulate_paths(
    params: SimParams,
    n_days: int,
    n_sims: int = N_SIMS,
    seed: int = SEED,
) -> dict:
    """Vectorized forward-time compounding simulation.

    Returns dict with per-sim: killed (bool), kill_day (int or n_days+1 if
    never killed), ending_bankroll (float, frozen at kill_day if killed).
    """
    rng = np.random.default_rng(seed)

    bankroll = np.full(n_sims, params.starting_bankroll, dtype=np.float64)
    peak = bankroll.copy()
    killed = np.zeros(n_sims, dtype=bool)
    kill_day = np.full(n_sims, n_days + 1, dtype=np.int64)

    for day in range(1, n_days + 1):
        active = ~killed
        if not active.any():
            break
        for _ in range(params.bets_per_day):
            active = ~killed
            if not active.any():
                break
            stake = np.minimum(params.stake_frac * bankroll, params.cap_usd)
            stake = np.where(active, stake, 0.0)
            wins = rng.random(n_sims) < params.win_rate
            delta = np.where(wins, stake * params.win_mult, -stake * params.loss_mult)
            bankroll = np.where(active, bankroll + delta, bankroll)
            peak = np.maximum(peak, bankroll)
            dd = np.where(peak > 0, (peak - bankroll) / peak, 0.0)
            newly_killed = active & (dd >= params.kill_switch_dd) & (~killed)
            kill_day[newly_killed] = day
            killed = killed | newly_killed

    return {
        "killed": killed,
        "kill_day": kill_day,
        "ending_bankroll": bankroll,
    }


def kill_prob_at_horizons(params: SimParams, horizons: list, n_sims: int = N_SIMS, seed: int = SEED) -> dict:
    """Run one simulation to max(horizons) days, report cumulative P(kill switch tripped by day H)
    for each horizon (a path killed at day 10 counts as killed at every later horizon too)."""
    max_days = max(horizons)
    result = simulate_paths(params, max_days, n_sims=n_sims, seed=seed)
    kill_day = result["kill_day"]
    probs = {}
    for h in horizons:
        probs[h] = float(np.mean(kill_day <= h)) * 100.0
    return probs, result


def build_report(params: SimParams, horizons: list, n_sims: int, label: Optional[str] = None) -> str:
    probs, result = kill_prob_at_horizons(params, horizons, n_sims=n_sims)
    ending = result["ending_bankroll"]
    killed = result["killed"]

    sep = "=" * 68
    lines = [
        sep,
        "  GG-071/T-223 Forward-Time Compounding Monte Carlo",
        "  MODE: proportional/Kelly-style stake sizing, calendar-day compounding",
        f"  N={n_sims:,} paths  |  bets/day={params.bets_per_day}  |  "
        f"win_rate={params.win_rate:.4f}",
    ]
    if label:
        lines.append(f"  Label: {label}")
    lines.append(sep)

    lines += [
        "",
        "PARAMETERS",
        f"  Starting bankroll   : ${params.starting_bankroll:,.2f}",
        f"  Stake fraction      : {params.stake_frac*100:.3f}% of current bankroll",
        f"  Absolute cap        : ${params.cap_usd:,.2f}/bet",
        f"  Cap-engagement pt   : ~${params.cap_usd/params.stake_frac:,.0f} bankroll",
        f"  Win multiple        : +{params.win_mult*100:.1f}% of stake (profit)",
        f"  Loss multiple       : -{params.loss_mult*100:.1f}% of stake",
        f"  Kill switch (perm.) : {params.kill_switch_dd*100:.0f}% realized drawdown from peak",
        "",
        "KILL-SWITCH BREACH PROBABILITY (cumulative, by horizon)",
    ]
    for h in horizons:
        label_h = {30: "1mo", 182: "6mo", 365: "1yr"}.get(h, f"{h}d")
        lines.append(f"  P(kill switch by day {h:>3} / {label_h:<4}) : {probs[h]:>6.2f}%")

    lines += [
        "",
        "ENDING BANKROLL (all paths, including killed — frozen at kill day)",
        f"  Mean   : ${np.mean(ending):>10,.2f}",
        f"  Median : ${np.median(ending):>10,.2f}",
        f"  p5     : ${np.percentile(ending, 5):>10,.2f}",
        f"  p95    : ${np.percentile(ending, 95):>10,.2f}",
        f"  Survived (never killed by day {max(horizons)}): {float(np.mean(~killed))*100:.1f}%",
    ]

    lines += [
        "",
        "GOVERNANCE",
        "  GG-071 (OPEN): a real, positive T1 MLB edge does not suppress ruin",
        "  risk under proportional-stake compounding — it amplifies both tails.",
        "  T-223: this script formally reviews candidate remediations. See",
        "  ADR-0040 (draft) for the recommendation. Requires operator/DS",
        "  sign-off before any risk.py parameter is changed (Hard Rule 3).",
        sep,
    ]

    return "\n".join(lines)


def sensitivity_report(n_sims: int = N_SIMS) -> str:
    """Compare baseline against three candidate remediation directions from T-223:
      (a) cadence-aware Kelly de-rating (reduce stake_frac by a de-rate factor)
      (b) formal max-P(kill-switch) target (search stake_frac to hit a target)
      (c) lowering the $500/bet hard cap
    """
    base = SimParams()
    lines = [
        "=" * 78,
        "  GG-071/T-223 Sensitivity Analysis — Candidate Remediation Directions",
        "=" * 78,
        "",
        f"  BASELINE  (stake_frac={base.stake_frac*100:.3f}%, cap=${base.cap_usd:.0f})",
    ]
    probs, _ = kill_prob_at_horizons(base, HORIZONS_DAYS, n_sims=n_sims)
    lines.append(
        "    P(kill switch): "
        + "  ".join(f"{h}d={probs[h]:.2f}%" for h in HORIZONS_DAYS)
    )
    lines.append("")

    # (a) cadence-aware Kelly de-rating
    lines.append("  (a) CADENCE-AWARE KELLY DE-RATING (divide stake_frac by de-rate factor)")
    for derate in [1.0, 1.5, 2.0, 3.0, 4.0, 5.0]:
        p = SimParams(stake_frac=base.stake_frac / derate)
        probs, _ = kill_prob_at_horizons(p, HORIZONS_DAYS, n_sims=n_sims)
        lines.append(
            f"    de-rate={derate:>4.1f}x  (stake_frac={p.stake_frac*100:.3f}%)  "
            + "  ".join(f"{h}d={probs[h]:>6.2f}%" for h in HORIZONS_DAYS)
        )
    lines.append("")

    # (b) formal max-P(kill-switch) target — search stake_frac for target 1yr P(kill) <= 5%
    lines.append("  (b) FORMAL MAX-P(KILL-SWITCH) TARGET — search stake_frac for P(kill, 1yr) <= target")
    for target in [10.0, 5.0, 2.0]:
        lo, hi = 0.0005, base.stake_frac
        for _ in range(18):
            mid = (lo + hi) / 2.0
            p = SimParams(stake_frac=mid)
            probs, _ = kill_prob_at_horizons(p, [365], n_sims=max(2000, n_sims // 4))
            if probs[365] > target:
                hi = mid
            else:
                lo = mid
        p = SimParams(stake_frac=lo)
        probs, _ = kill_prob_at_horizons(p, HORIZONS_DAYS, n_sims=n_sims)
        lines.append(
            f"    target<={target:>4.1f}%  ->  stake_frac={p.stake_frac*100:.3f}%  "
            + "  ".join(f"{h}d={probs[h]:>6.2f}%" for h in HORIZONS_DAYS)
        )
    lines.append("")

    # (c) lowering the $500/bet hard cap
    lines.append("  (c) LOWERING THE $500/BET HARD CAP (stake_frac unchanged)")
    for cap in [500.0, 250.0, 100.0, 50.0]:
        p = SimParams(cap_usd=cap)
        probs, _ = kill_prob_at_horizons(p, HORIZONS_DAYS, n_sims=n_sims)
        lines.append(
            f"    cap=${cap:>6.0f}  (engages at ~${cap/base.stake_frac:>9,.0f} bankroll)  "
            + "  ".join(f"{h}d={probs[h]:>6.2f}%" for h in HORIZONS_DAYS)
        )
    lines.append("")
    lines.append("  NOTE: (c) has ~zero effect on the 30-day horizon (the cap has not yet")
    lines.append("  engaged for almost any path at that point) but a real, growing effect at")
    lines.append("  6mo/1yr as some paths compound past the (lower) engagement bankroll and")
    lines.append("  get their growth-driven stake size clipped before a later reversal wipes")
    lines.append("  them out. (a)/(b) act on every bet from day 1 regardless of bankroll")
    lines.append("  level and are far more efficient per unit of expected-growth sacrificed —")
    lines.append("  they are the only directions that reduce NEAR-TERM (30d) ruin risk at all.")
    lines.append("=" * 78)

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="GG-071/T-223 Forward-Time Compounding Monte Carlo")
    parser.add_argument("--stake-frac", type=float, default=STAKE_FRAC, dest="stake_frac",
                         help=f"Stake fraction of bankroll per bet (default {STAKE_FRAC})")
    parser.add_argument("--cap", type=float, default=CAP_USD,
                         help=f"Absolute $ cap per bet (default {CAP_USD})")
    parser.add_argument("--win-rate", type=float, default=WIN_RATE, dest="win_rate",
                         help=f"Win probability (default {WIN_RATE})")
    parser.add_argument("--bets-per-day", type=int, default=BETS_PER_DAY, dest="bets_per_day",
                         help=f"Bets per active day (default {BETS_PER_DAY})")
    parser.add_argument("--bankroll", type=float, default=STARTING_BANKROLL,
                         help=f"Starting bankroll (default {STARTING_BANKROLL})")
    parser.add_argument("--n-sims", type=int, default=N_SIMS, dest="n_sims",
                         help=f"Number of simulated paths (default {N_SIMS})")
    parser.add_argument("--sensitivity", action="store_true",
                         help="Run T-223 sensitivity analysis across remediation directions instead of a single report")
    parser.add_argument("--label", help="Label for comparison runs")
    parser.add_argument("--out", help="Save report to file (also prints to stdout)")
    args = parser.parse_args()

    if args.sensitivity:
        report = sensitivity_report(n_sims=args.n_sims)
    else:
        params = SimParams(
            win_rate=args.win_rate,
            stake_frac=args.stake_frac,
            cap_usd=args.cap,
            bets_per_day=args.bets_per_day,
            starting_bankroll=args.bankroll,
        )
        report = build_report(params, HORIZONS_DAYS, n_sims=args.n_sims, label=args.label)

    print(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report)
        print(f"[Saved to {out_path}]", file=sys.stderr)


if __name__ == "__main__":
    main()

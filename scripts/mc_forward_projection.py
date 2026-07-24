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
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_band_monitor import (  # noqa: E402
    BOOK_BANDS,
    DEFAULT_PORTFOLIO,
    DEFAULT_T4_LEDGER,
    load_pool_by_band,
    load_t4_ledger,
    filter_clean,
)
from run_power_calc import (  # noqa: E402
    observed_cadence_per_week,
    MATURE_CADENCE_SPAN_DAYS,
)

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

# ---------------------------------------------------------------------------
# T-342 — T4M-PROJ frozen "operational" citation (flat-stake regime).
#
# T4M-PROJ's live decision path (run_t4_mlb_live.py KELLY_T4=0.10) is
# formula-proportional, not architecturally flat — but its typical computed
# edge is tiny and stable enough that, over the observed window, per-bet
# dollar stakes cluster tightly rather than visibly compounding with
# bankroll growth the way T1's do (T-342 task framing: "~$0.47 flat"). This
# is an empirical regime property, not a code-level guarantee, and should be
# re-examined if edge size or bankroll growth materially shift.
#
# Frozen 2026-07-11 (T-342), from clean_n=338 (CURRENT_LOGIC_EPOCH-only)
# records in the freshly-rebuilt logs/t4_mlb_resolved_ledger.jsonl (see
# DECISION_LOG.md 2026-07-11 T-341 entry for the rebuild). Mirrors how
# WIN_RATE/WIN_MULT/etc. above were frozen from a point-in-time GG-071 read
# of the T1 ledger (SESSION 113, 2026-07-02) — same convention, new band.
#
# CAVEAT: cadence measured over only ~5.0 days of resolved history, below
# the 14-day maturity floor (run_power_calc.MATURE_CADENCE_SPAN_DAYS) — this
# bets_per_day figure is provisional and should be re-derived (or re-run via
# --from-ledger T4M-PROJ, which always uses the LIVE ledger for floor/ceiling)
# once more days accrue.
# ---------------------------------------------------------------------------
T4M_PROJ_WIN_RATE = 0.650887573964497
T4M_PROJ_WIN_MULT = 1.7010275566641562
T4M_PROJ_LOSS_MULT = 1.0
T4M_PROJ_STAKE_USD = 0.5662869822485207
T4M_PROJ_BETS_PER_DAY = 68


@dataclass
class SimParams:
    win_rate: float = WIN_RATE
    win_mult: float = WIN_MULT
    loss_mult: float = LOSS_MULT
    stake_frac: float = STAKE_FRAC
    stake_usd: float = 0.0           # T-342: used only when stake_mode == "flat"
    stake_mode: str = "proportional"  # T-342: "proportional" (stake_frac*bankroll) or "flat" (fixed stake_usd, does not compound)
    cap_usd: float = CAP_USD
    bets_per_day: int = BETS_PER_DAY
    kill_switch_dd: float = KILL_SWITCH_DD
    starting_bankroll: float = STARTING_BANKROLL

    def __post_init__(self):
        if self.stake_mode not in ("proportional", "flat"):
            raise ValueError(f"stake_mode must be 'proportional' or 'flat', got {self.stake_mode!r}")


def t4m_proj_operational_params(cap_usd: float = CAP_USD, kill_switch_dd: float = KILL_SWITCH_DD,
                                 starting_bankroll: float = STARTING_BANKROLL) -> "SimParams":
    """T-342: T4M-PROJ's frozen operational scenario (flat-stake regime) —
    the analogue of SimParams() (T1's frozen GG-071 defaults) for the new band."""
    return SimParams(
        win_rate=T4M_PROJ_WIN_RATE, win_mult=T4M_PROJ_WIN_MULT, loss_mult=T4M_PROJ_LOSS_MULT,
        stake_mode="flat", stake_usd=T4M_PROJ_STAKE_USD, cap_usd=cap_usd,
        bets_per_day=T4M_PROJ_BETS_PER_DAY, kill_switch_dd=kill_switch_dd,
        starting_bankroll=starting_bankroll,
    )


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
            if params.stake_mode == "flat":
                stake = np.minimum(np.full(n_sims, params.stake_usd, dtype=np.float64), params.cap_usd)
            else:
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
    ]
    if params.stake_mode == "flat":
        lines.append(f"  Stake               : ${params.stake_usd:,.4f}/bet flat (T-342 — does not scale with bankroll)")
    else:
        lines.append(f"  Stake fraction      : {params.stake_frac*100:.3f}% of current bankroll")
        lines.append(f"  Cap-engagement pt   : ~${params.cap_usd/params.stake_frac:,.0f} bankroll" if params.stake_frac > 0 else "  Cap-engagement pt   : n/a (stake_frac=0)")
    lines += [
        f"  Absolute cap        : ${params.cap_usd:,.2f}/bet",
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


# ---------------------------------------------------------------------------
# T-330 — ledger-driven parameter derivation (--from-ledger)
# T-331 — bootstrap confidence on the derived edge input (--bootstrap)
# ---------------------------------------------------------------------------
LEDGER_BANDS = tuple(BOOK_BANDS) + ("T4M-PROJ",)


def load_clean_band_records(
    band: str,
    portfolio_path: Path = DEFAULT_PORTFOLIO,
    t4_ledger_path: Path = DEFAULT_T4_LEDGER,
) -> list:
    """Load resolved records for `band`, filtered to clean_n (per-band clean-epoch
    floor, per logic_epoch.py / GG-124 — see run_band_monitor.filter_clean)."""
    if band in BOOK_BANDS:
        by_band = load_pool_by_band(portfolio_path)
        recs = by_band.get(band, [])
    elif band == "T4M-PROJ":
        recs = load_t4_ledger(t4_ledger_path)
    else:
        raise ValueError(f"Unknown band {band!r}; expected one of {LEDGER_BANDS}")
    return filter_clean(recs, band)


@dataclass
class LedgerStats:
    band: str
    clean_n: int
    win_rate: float
    win_mult: float
    loss_mult: float
    stake_frac: float
    stake_usd_flat: float  # T-342: mean $ stake, bankroll-independent (for stake_mode="flat")
    starting_bankroll: float
    bets_per_day: int
    cadence_bets_per_week: Optional[float]
    cadence_span_days: Optional[float]
    cadence_immature: bool


def derive_ledger_stats(band: str, recs: list, starting_bankroll: float) -> LedgerStats:
    """Derive win_rate/win_mult/loss_mult/stake_frac/cadence directly from a
    clean_n record set (already filtered by load_clean_band_records / filter_clean).

    win_mult/loss_mult are computed per-record as pnl/size_usd (WIN) and
    abs(pnl)/size_usd (LOSS), then averaged — this mirrors the module's own
    hardcoded WIN_MULT/LOSS_MULT constants but reads them from the live ledger
    instead of a frozen GG-071-era snapshot.
    """
    n = len(recs)
    if n == 0:
        raise ValueError(f"Band {band!r} has clean_n=0 — no CURRENT_LOGIC_EPOCH records to derive MC parameters from.")

    wins = [r for r in recs if r.get("_win") == 1 and float(r.get("_size", 0.0) or 0.0) > 0]
    losses = [r for r in recs if r.get("_win") == 0 and float(r.get("_size", 0.0) or 0.0) > 0]
    sized = [r for r in recs if float(r.get("_size", 0.0) or 0.0) > 0]
    if not wins:
        raise ValueError(f"Band {band!r} clean_n={n} has zero WIN records with size_usd>0 — cannot derive win_mult.")
    if not losses:
        raise ValueError(f"Band {band!r} clean_n={n} has zero LOSS records with size_usd>0 — cannot derive loss_mult.")

    win_rate = len(wins) / n
    win_mult = statistics.mean(float(r["_pnl"]) / float(r["_size"]) for r in wins)
    loss_mult = statistics.mean(abs(float(r["_pnl"])) / float(r["_size"]) for r in losses)
    stake_usd_flat = statistics.mean(float(r["_size"]) for r in sized)
    stake_frac = stake_usd_flat / starting_bankroll

    cadence_per_week, span_days = observed_cadence_per_week(recs)
    cadence_immature = span_days is not None and span_days < MATURE_CADENCE_SPAN_DAYS
    bets_per_day = max(1, round(cadence_per_week / 7.0)) if cadence_per_week else BETS_PER_DAY

    return LedgerStats(
        band=band,
        clean_n=n,
        win_rate=win_rate,
        win_mult=win_mult,
        loss_mult=loss_mult,
        stake_frac=stake_frac,
        stake_usd_flat=stake_usd_flat,
        starting_bankroll=starting_bankroll,
        bets_per_day=bets_per_day,
        cadence_bets_per_week=cadence_per_week,
        cadence_span_days=span_days,
        cadence_immature=cadence_immature,
    )


def build_ledger_scenarios(stats: LedgerStats, cap_usd: float = CAP_USD,
                            kill_switch_dd: float = KILL_SWITCH_DD,
                            stake_mode: str = "proportional",
                            operational: Optional[SimParams] = None) -> dict:
    """{floor, operational, ceiling} per T-330 spec (T-342 extends with stake_mode):
      floor       = zero-edge breakeven win_rate, with the REAL observed
                    payout/stake/cadence mechanics from the clean_n ledger
                    ("if the edge turned out to be illusory, what's the ruin
                    risk under today's actual sizing behavior?").
      operational = frozen module defaults, NOT re-derived from the ledger —
                    the existing regression anchor. Defaults to SimParams()
                    (T1/GG-071 proportional-compounding defaults, unchanged —
                    see TestGG071Reproduction in
                    tests/test_mc_forward_projection.py) unless a band-
                    specific `operational` SimParams is supplied (T-342: see
                    t4m_proj_operational_params() for T4M-PROJ's analogue).
      ceiling     = fully observed win_rate/win_mult/loss_mult/stake
                    (proportional stake_frac or flat stake_usd, per
                    stake_mode)/cadence, all pulled from the clean_n ledger.

    stake_mode: "proportional" (default, unchanged behavior — stake scales
    with current bankroll, T1-style compounding) or "flat" (T-342 — fixed
    dollar stake_usd per bet, does not scale with bankroll; models T4M-PROJ's
    observed near-constant per-bet dollar sizing).
    """
    if stake_mode not in ("proportional", "flat"):
        raise ValueError(f"stake_mode must be 'proportional' or 'flat', got {stake_mode!r}")

    p0 = stats.loss_mult / (stats.win_mult + stats.loss_mult)  # zero-edge breakeven win rate
    if stake_mode == "flat":
        floor = SimParams(
            win_rate=p0, win_mult=stats.win_mult, loss_mult=stats.loss_mult,
            stake_mode="flat", stake_usd=stats.stake_usd_flat, cap_usd=cap_usd,
            bets_per_day=stats.bets_per_day, kill_switch_dd=kill_switch_dd,
            starting_bankroll=stats.starting_bankroll,
        )
        ceiling = SimParams(
            win_rate=stats.win_rate, win_mult=stats.win_mult, loss_mult=stats.loss_mult,
            stake_mode="flat", stake_usd=stats.stake_usd_flat, cap_usd=cap_usd,
            bets_per_day=stats.bets_per_day, kill_switch_dd=kill_switch_dd,
            starting_bankroll=stats.starting_bankroll,
        )
    else:
        floor = SimParams(
            win_rate=p0, win_mult=stats.win_mult, loss_mult=stats.loss_mult,
            stake_frac=stats.stake_frac, cap_usd=cap_usd, bets_per_day=stats.bets_per_day,
            kill_switch_dd=kill_switch_dd, starting_bankroll=stats.starting_bankroll,
        )
        ceiling = SimParams(
            win_rate=stats.win_rate, win_mult=stats.win_mult, loss_mult=stats.loss_mult,
            stake_frac=stats.stake_frac, cap_usd=cap_usd, bets_per_day=stats.bets_per_day,
            kill_switch_dd=kill_switch_dd, starting_bankroll=stats.starting_bankroll,
        )
    operational_params = operational if operational is not None else SimParams()
    return {"floor": floor, "operational": operational_params, "ceiling": ceiling}


def bootstrap_kill_ci(
    band: str,
    recs: list,
    scenario_name: str,
    starting_bankroll: float,
    cap_usd: float,
    kill_switch_dd: float,
    horizons: list,
    n_boot: int = 200,
    boot_sims: int = 1000,
    seed: int = SEED,
    stake_mode: str = "proportional",
) -> dict:
    """Bootstrap-resample (with replacement) the clean_n record set n_boot times;
    for each resample, re-derive win_rate/win_mult/loss_mult/stake_frac/cadence
    and run a reduced-n_sims MC. Returns, per horizon, a percentile band
    (5th/median/95th = ~90% CI) on P(kill switch) reflecting sample uncertainty
    in the edge input (T-331). scenario_name in {"floor", "ceiling"} — for
    "floor" the win_rate is recomputed as that resample's own zero-edge
    breakeven point (not resampled directly), since floor asks "given this
    resample's real payout structure, what if the edge were illusory."

    stake_mode (T-342): "proportional" (default, unchanged) or "flat" — must
    match the stake_mode used for the point-estimate scenario being CI'd.
    """
    if stake_mode not in ("proportional", "flat"):
        raise ValueError(f"stake_mode must be 'proportional' or 'flat', got {stake_mode!r}")
    if scenario_name not in ("floor", "ceiling"):
        raise ValueError('scenario_name must be "floor" or "ceiling"')

    rng = np.random.default_rng(seed)
    n = len(recs)
    per_horizon = {h: [] for h in horizons}
    skipped = 0

    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample = [recs[i] for i in idx]
        try:
            s = derive_ledger_stats(band, sample, starting_bankroll)
        except ValueError:
            skipped += 1
            continue

        win_rate = (s.loss_mult / (s.win_mult + s.loss_mult)) if scenario_name == "floor" else s.win_rate
        if stake_mode == "flat":
            params = SimParams(
                win_rate=win_rate, win_mult=s.win_mult, loss_mult=s.loss_mult,
                stake_mode="flat", stake_usd=s.stake_usd_flat, cap_usd=cap_usd,
                bets_per_day=s.bets_per_day, kill_switch_dd=kill_switch_dd,
                starting_bankroll=starting_bankroll,
            )
        else:
            params = SimParams(
                win_rate=win_rate, win_mult=s.win_mult, loss_mult=s.loss_mult,
                stake_frac=s.stake_frac, cap_usd=cap_usd, bets_per_day=s.bets_per_day,
                kill_switch_dd=kill_switch_dd, starting_bankroll=starting_bankroll,
            )
        probs, _ = kill_prob_at_horizons(params, horizons, n_sims=boot_sims, seed=seed + b + 1)
        for h in horizons:
            per_horizon[h].append(probs[h])

    result = {}
    for h in horizons:
        vals = per_horizon[h]
        if not vals:
            result[h] = None
            continue
        arr = np.array(vals)
        result[h] = {
            "point": float(np.median(arr)),
            "lo": float(np.percentile(arr, 5)),
            "hi": float(np.percentile(arr, 95)),
            "n_boot_valid": len(vals),
            "n_boot_skipped": skipped,
        }
    return result


def build_ledger_report(
    band: str,
    stats: LedgerStats,
    scenarios: dict,
    horizons: list,
    n_sims: int,
    boot_ci: Optional[dict] = None,
) -> str:
    sep = "=" * 78
    lines = [
        sep,
        f"  T-330/T-331 Ledger-Driven Forward MC — band={band}",
        sep,
        "",
        "DERIVED FROM CLEAN_N LEDGER (CURRENT_LOGIC_EPOCH only — GG-077/GG-087)",
        f"  clean_n              : {stats.clean_n}",
        f"  observed win_rate    : {stats.win_rate:.4f}",
        f"  observed win_mult    : {stats.win_mult:.4f}",
        f"  observed loss_mult   : {stats.loss_mult:.4f}",
    ]
    stake_mode = scenarios["floor"].stake_mode
    if stake_mode == "flat":
        lines.append(f"  observed stake ($)   : ${stats.stake_usd_flat:,.4f}/bet flat (T-342 — does not scale with bankroll)")
    else:
        lines.append(f"  observed stake_frac  : {stats.stake_frac*100:.4f}% of ${stats.starting_bankroll:,.2f} bankroll")
    if stats.cadence_bets_per_week is not None:
        lines.append(f"  observed cadence     : {stats.cadence_bets_per_week:.1f} bets/wk -> {stats.bets_per_day} bets/day")
    else:
        lines.append(f"  observed cadence     : unmeasurable (<2 timestamped bets) -> falling back to bets_per_day={stats.bets_per_day}")
    if stats.cadence_immature:
        lines.append(
            f"  CAVEAT: cadence measured over only {stats.cadence_span_days:.1f} days "
            f"(< {MATURE_CADENCE_SPAN_DAYS:.0f}-day maturity floor) — provisional, re-derive as more days accrue."
        )
    if band == "T4M-PROJ":
        lines += [
            "",
            "  GG-105 CAVEAT (T-342): T4M-PROJ's own computed edge is ANTI_PREDICTIVE against",
            "  realized win rate on clean data (clean_n=338, Fisher p=0.0563) — this is a live,",
            "  unresolved finding, not historical. The ruin-risk figures below (including any",
            "  flat-vs-proportional sizing comparison) describe the SIZING MECHANIC's structural",
            "  behavior only. They do NOT certify that T4M-PROJ's edge is real. Read this report",
            "  together with GG-105, never in isolation.",
        ]
    if band == "T4M-PROJ" and stake_mode == "flat":
        lines += [
            "",
            "  GG-078 CAVEAT (T-350): T4M-PROJ's live code is Kelly-PROPORTIONAL (KELLY_T4=0.10),",
            "  the same sizing family as T1 — not a hardcoded flat-dollar path. The flat-stake",
            "  numbers below are an OBSERVED EMPIRICAL REGIME (tight, stable tiny edge -> stakes",
            "  clustering near a near-constant dollar amount over a short window), not a code",
            "  guarantee that will hold as bankroll moves. GG-078 already found that Kelly-",
            "  proportional sizing at T4's real high cadence produces a FAST, front-loaded kill",
            "  dynamic (~15-day decision horizon at breakeven, via the separate mc_t4_leg.py",
            "  analysis) — structurally different from the gradual, full-year risk accumulation",
            "  shown below. Do not read the 182d/365d figures in this flat-mode report as",
            "  evidence that T4M-PROJ is safe out to a year under its real sizing mechanic; they",
            "  describe only the flat-stake hypothetical. If observed stakes begin to visibly",
            "  compound with bankroll, GG-078's fast-decision dynamic is the operative risk model,",
            "  not this one.",
        ]
    lines += ["", "KILL-SWITCH BREACH PROBABILITY BY SCENARIO", ""]

    op_desc = (
        "frozen T-342 T4M-PROJ operational defaults, flat-stake regime (regression anchor, unchanged)"
        if scenarios["operational"].stake_mode == "flat"
        else "frozen ADR-0040/GG-071 module defaults (regression anchor, unchanged)"
    )
    desc = {
        "floor": "zero-edge breakeven win_rate; real observed payout/stake/cadence mechanics",
        "operational": op_desc,
        "ceiling": "fully observed win_rate/payout/stake/cadence from the clean_n ledger",
    }
    for name in ("floor", "operational", "ceiling"):
        params = scenarios[name]
        probs, _ = kill_prob_at_horizons(params, horizons, n_sims=n_sims)
        stake_desc = (
            f"stake=${params.stake_usd:,.4f}/bet flat" if params.stake_mode == "flat"
            else f"stake_frac={params.stake_frac*100:.3f}%"
        )
        lines.append(
            f"  [{name.upper()}] win_rate={params.win_rate:.4f}  {stake_desc}  "
            f"bets/day={params.bets_per_day}  bankroll=${params.starting_bankroll:,.2f}"
        )
        lines.append(f"    {desc[name]}")
        for h in horizons:
            label_h = {30: "1mo", 182: "6mo", 365: "1yr"}.get(h, f"{h}d")
            row = f"    P(kill by day {h:>3} / {label_h:<4}) : {probs[h]:>6.2f}%"
            if boot_ci and name in boot_ci and boot_ci[name] and boot_ci[name].get(h):
                ci = boot_ci[name][h]
                row += f"   [90% CI: {ci['lo']:.2f}% - {ci['hi']:.2f}%]  (n_boot={ci['n_boot_valid']})"
            lines.append(row)
        lines.append("")

    lines.append(
        "  NOTE: bootstrap CI (T-331), where shown, is computed only for FLOOR/CEILING —"
    )
    lines.append(
        "  OPERATIONAL stays a frozen point estimate (it is the existing GG-071 regression anchor)."
    )
    lines.append(sep)
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
    parser.add_argument("--from-ledger", dest="from_ledger", choices=list(LEDGER_BANDS), default=None,
                         help="T-330: derive win_rate/win_mult/loss_mult/stake_frac/cadence from the "
                              "clean_n (CURRENT_LOGIC_EPOCH) ledger for this band instead of hardcoded "
                              "module constants; emits floor/operational/ceiling scenarios.")
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO,
                         help="T1/T2/T3 band-tagged portfolio JSON (only used with --from-ledger)")
    parser.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER, dest="t4_ledger",
                         help="T4M-PROJ resolved ledger JSONL (only used with --from-ledger)")
    parser.add_argument("--bootstrap", action="store_true",
                         help="T-331: bootstrap-resample the clean_n ledger to report P(kill) as a "
                              "90%% CI band (floor/ceiling only), not a single point estimate. "
                              "Only valid with --from-ledger.")
    parser.add_argument("--n-boot", type=int, default=30, dest="n_boot",
                         help="Number of bootstrap resamples (default 30 — kept low because per-sim "
                              "cost is dominated by days*bets_per_day iterations, not n_sims; "
                              "high-cadence bands like T4M-PROJ (~68 bets/day) cost ~1s/resample. "
                              "Only used with --bootstrap.")
    parser.add_argument("--boot-sims", type=int, default=500, dest="boot_sims",
                         help="MC paths per bootstrap resample (default 500, only used with --bootstrap)")
    parser.add_argument("--stake-mode", dest="stake_mode", choices=["auto", "proportional", "flat"],
                         default="auto",
                         help="T-342: 'auto' (default) picks 'flat' for T4M-PROJ and 'proportional' for "
                              "T1/T2/T3, matching each band's real sizing mechanic; override explicitly "
                              "with 'proportional' or 'flat'. Only used with --from-ledger.")
    args = parser.parse_args()

    if args.from_ledger:
        try:
            recs = load_clean_band_records(args.from_ledger, args.portfolio, args.t4_ledger)
            stats = derive_ledger_stats(args.from_ledger, recs, starting_bankroll=args.bankroll)
        except ValueError as e:
            print(f"[--from-ledger error] {e}", file=sys.stderr)
            raise SystemExit(1)

        if args.stake_mode == "auto":
            stake_mode = "flat" if args.from_ledger == "T4M-PROJ" else "proportional"
        else:
            stake_mode = args.stake_mode

        operational = (
            t4m_proj_operational_params(cap_usd=args.cap, starting_bankroll=args.bankroll)
            if (args.from_ledger == "T4M-PROJ" and stake_mode == "flat")
            else None
        )
        scenarios = build_ledger_scenarios(stats, cap_usd=args.cap, stake_mode=stake_mode, operational=operational)

        boot_ci = None
        if args.bootstrap:
            boot_ci = {}
            for name in ("floor", "ceiling"):
                boot_ci[name] = bootstrap_kill_ci(
                    args.from_ledger, recs, name,
                    starting_bankroll=args.bankroll, cap_usd=args.cap,
                    kill_switch_dd=KILL_SWITCH_DD, horizons=HORIZONS_DAYS,
                    n_boot=args.n_boot, boot_sims=args.boot_sims,
                    stake_mode=stake_mode,
                )

        report = build_ledger_report(args.from_ledger, stats, scenarios, HORIZONS_DAYS, args.n_sims, boot_ci=boot_ci)
    elif args.sensitivity:
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

#!/usr/bin/env python3
"""
T-323 — Sample-Adequacy / Power Calculation (Workstream B2)
GG-004 | Companion to run_band_monitor.py (T-255/T-322)

WHY THIS EXISTS
----------------
G6's "n>=150 single-sport / n>=500 Tier-2" thresholds (ADR-0024) are fixed
heuristics, not derived from this system's actual observed bet-level variance.
This script converts that heuristic into a real, per-band target: given the
CURRENT_LOGIC_EPOCH clean_n cohort's observed mean per-bet P&L (mu) and sample
standard deviation (sigma), compute n* = the clean-bet count needed to
distinguish `edge > 0` from `edge = 0` at a given significance level (alpha,
one-sided — the test is directional: "is mean P&L per bet positive?") and
power (1 - beta). This is a standard one-sample mean power calculation:

    n* = ((z_alpha + z_beta) * sigma / mu) ** 2

If the observed mu <= 0, no finite n* exists to *confirm* a positive edge from
this exact sample's effect size — the script reports that explicitly rather
than emitting a misleading number (dividing by a non-positive mu would either
error or produce a meaningless negative/undefined n*).

ETA is derived from the SAME clean cohort's own observed cadence (bets per
week between its earliest and latest resolved_at/entered_at), not an assumed
constant — cadence varies enormously by band (T4M-PROJ fires far more often
than T1).

Composition: reuses run_band_monitor.py's loaders (load_pool_by_band,
load_t4_ledger, filter_clean, BOOK_BANDS, MIN_N) so this script cannot drift
from what T-322 already validated as the clean_n definition.

Run:
  python3 scripts/run_power_calc.py
  python3 scripts/run_power_calc.py --alpha 0.05 --power 0.95
  python3 scripts/run_power_calc.py --portfolio logs/.vps_portfolio_cache_mlb.json \\
      --t4-ledger logs/t4_mlb_resolved_ledger.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_band_monitor import (   # noqa: E402
    MIN_N,
    BOOK_BANDS,
    DEFAULT_PORTFOLIO,
    DEFAULT_T4_LEDGER,
    load_pool_by_band,
    load_t4_ledger,
    filter_clean,
)

OUT_DIR = Path("exp_output/T323-POWER-CALC")


# ── inverse normal CDF (Acklam's rational approximation, |err| < 1.15e-9) ───────

def _inv_norm_cdf(p: float) -> float:
    if not (0.0 < p < 1.0):
        raise ValueError(f"p must be in (0,1), got {p}")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def z_for(alpha_or_beta: float) -> float:
    """z such that P(Z > z) = alpha_or_beta, i.e. the upper-tail critical value
    for a one-sided test at that significance/power complement."""
    return _inv_norm_cdf(1.0 - alpha_or_beta)


# ── cadence ──────────────────────────────────────────────────────────────────────

def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    s = raw[:-1] if raw.endswith("Z") else raw
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


MATURE_CADENCE_SPAN_DAYS = 14.0  # below this, ETA is an extrapolation from an
# immature window, not a settled cadence — same caution as GG-080's "n=2
# game-days, not a stable long-run estimate" precedent. CURRENT_LOGIC_EPOCH
# (T-320/T-321) only started ~2026-07-06/07, so early clean_n cohorts are
# necessarily short-span; flag rather than silently presenting as steady-state.


def observed_cadence_per_week(recs: list[dict]) -> tuple[float | None, float | None]:
    """Bets/week over the clean cohort's own observed span (resolved_at,
    falling back to entered_at/game_date), plus the raw span in days.
    Returns (None, None) if span is too short (<1 day) or fewer than 2
    timestamps resolve — cadence is not yet measurable."""
    ts = []
    for r in recs:
        dt = _parse_ts(r.get("resolved_at")) or _parse_ts(r.get("entered_at")) \
             or _parse_ts(r.get("game_date"))
        if dt is not None:
            ts.append(dt)
    if len(ts) < 2:
        return None, None
    span_days = (max(ts) - min(ts)).total_seconds() / 86400.0
    if span_days < 1.0:
        return None, span_days
    return len(recs) / (span_days / 7.0), span_days


# ── per-band power calc ──────────────────────────────────────────────────────────

def analyze_band_power(band: str, recs: list[dict], alpha: float, power: float) -> dict:
    clean_recs = filter_clean(recs)
    raw_n = len(recs)
    clean_n = len(clean_recs)

    if clean_n < 2:
        return {
            "band": band, "raw_n": raw_n, "clean_n": clean_n,
            "status": "INSUFFICIENT_DATA",
            "reason": f"clean_n={clean_n} < 2 — cannot estimate a sample variance.",
        }

    pnl = [float(r["_pnl"]) for r in clean_recs]
    mu = statistics.mean(pnl)
    sigma = statistics.stdev(pnl)  # sample stdev, ddof=1

    cadence, span_days = observed_cadence_per_week(clean_recs)
    cadence_immature = span_days is not None and span_days < MATURE_CADENCE_SPAN_DAYS

    if mu <= 0:
        return {
            "band": band, "raw_n": raw_n, "clean_n": clean_n,
            "status": "NO_POSITIVE_EFFECT",
            "mean_pnl_per_bet": mu, "stdev_pnl_per_bet": sigma,
            "cadence_bets_per_week": cadence,
            "cadence_span_days": span_days, "cadence_immature": cadence_immature,
            "reason": f"observed mean P&L/bet={mu:+.4f} <= 0 — no finite n* exists "
                      f"to confirm a positive edge from this sample's own effect size. "
                      f"The current point estimate does not support a target sample size; "
                      f"it would need to turn positive first.",
        }

    z_a = z_for(alpha)
    z_b = z_for(1.0 - power)  # power = 1 - beta -> beta = 1 - power
    n_star = ((z_a + z_b) * sigma / mu) ** 2
    n_star_ceil = math.ceil(n_star)
    gap = max(0, n_star_ceil - clean_n)
    eta_weeks = (gap / cadence) if (cadence and cadence > 0) else None

    return {
        "band": band, "raw_n": raw_n, "clean_n": clean_n,
        "status": "COMPUTED",
        "mean_pnl_per_bet": mu, "stdev_pnl_per_bet": sigma,
        "alpha": alpha, "power": power,
        "z_alpha": z_a, "z_beta": z_b,
        "n_star": n_star_ceil,
        "gap_to_n_star": gap,
        "cadence_bets_per_week": cadence,
        "cadence_span_days": span_days,
        "cadence_immature": cadence_immature,
        "eta_weeks": eta_weeks,
        "met": gap == 0,
    }


def run_all_bands(portfolio_path: Path, t4_ledger_path: Path,
                   alpha: float, power: float) -> dict[str, dict]:
    results: dict[str, dict] = {}
    by_band = load_pool_by_band(portfolio_path)
    for band in BOOK_BANDS:
        results[band] = analyze_band_power(band, by_band.get(band, []), alpha, power)
    t4_recs = load_t4_ledger(t4_ledger_path)
    results["T4M-PROJ"] = analyze_band_power("T4M-PROJ", t4_recs, alpha, power)
    return results


# ── reporting ────────────────────────────────────────────────────────────────────

def _fmt_band(r: dict) -> str:
    band = r["band"]
    if r["status"] == "INSUFFICIENT_DATA":
        return f"[{band}] clean_n={r['clean_n']} (raw_n={r['raw_n']}) — {r['reason']}"
    if r["status"] == "NO_POSITIVE_EFFECT":
        cad = f"{r['cadence_bets_per_week']:.1f}/wk" if r["cadence_bets_per_week"] else "unknown"
        return (f"[{band}] clean_n={r['clean_n']} (raw_n={r['raw_n']})  "
                f"mean_pnl/bet=${r['mean_pnl_per_bet']:+.4f}  cadence={cad}\n"
                f"    {r['reason']}")
    eta = f"{r['eta_weeks']:.1f} weeks" if r["eta_weeks"] is not None else "cadence unknown"
    cad = f"{r['cadence_bets_per_week']:.1f}/wk" if r["cadence_bets_per_week"] else "unknown"
    status = "TARGET MET" if r["met"] else f"needs {r['gap_to_n_star']} more clean bets"
    caveat = ""
    if r.get("cadence_immature"):
        caveat = (f"\n    CAVEAT: cadence measured over only {r['cadence_span_days']:.1f} days "
                  f"(clean epoch is new) — this is an early-window extrapolation, not a "
                  f"settled cadence. Treat ETA as provisional; re-derive as more days accrue.")
    return (f"[{band}] {band} needs ~n*={r['n_star']} clean bets to distinguish "
            f"edge>0 from edge=0 at alpha={r['alpha']}, power={r['power']}; "
            f"currently at clean_n={r['clean_n']} (raw_n={r['raw_n']}). "
            f"{status}. Cadence={cad}. ETA at current cadence = {eta}.\n"
            f"    (mean_pnl/bet=${r['mean_pnl_per_bet']:+.4f}, "
            f"stdev_pnl/bet=${r['stdev_pnl_per_bet']:.4f}){caveat}")


def _print_report(results: dict[str, dict], alpha: float, power: float) -> None:
    print("=" * 96)
    print(f"T-323 SAMPLE-ADEQUACY / POWER CALCULATION  (GG-004, alpha={alpha}, power={power})")
    print("=" * 96)
    for band, r in results.items():
        print()
        print(_fmt_band(r))
    print("\n" + "=" * 96)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="T-323 sample-adequacy / power calculation (GG-004)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    p.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER)
    p.add_argument("--alpha", type=float, default=0.05,
                    help="One-sided significance level (default 0.05)")
    p.add_argument("--power", type=float, default=0.95,
                    help="Target power, 1-beta (default 0.95)")
    p.add_argument("--out", type=Path, default=OUT_DIR)
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    results = run_all_bands(args.portfolio, args.t4_ledger, args.alpha, args.power)

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "power_calc_results.json"
    out_json.write_text(json.dumps(results, indent=2))

    _print_report(results, args.alpha, args.power)
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

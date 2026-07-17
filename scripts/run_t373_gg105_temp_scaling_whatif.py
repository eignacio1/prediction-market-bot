#!/usr/bin/env python3
"""
T-373 — GG-105 retrospective temperature-scaling what-if (offline analysis only)

WHY THIS EXISTS
----------------
GG-105: T4M-PROJ's own computed edge is anti-predictive (win rate declines
monotonically as edge rises). GG105_FULL_HISTORY.md has already ruled out
game-state noise, sizing artifacts, the edge-formula/vig-omission bug, and a
formal H1xH4 interaction model. The standing hypothesis is H1: unshrunk
ba_l10 treated as a noiseless per-AB Bernoulli rate -> overconfident model_p
at the extremes. T-341/T-344 already measured this indirectly via a
calibration-slope CI (b=0.600, CI excludes 1.0, "overconfident") but no prior
session has actually applied a retrospective temperature-scaling transform
(the exact remediation NBA used in ADR-0027, T=2.05) to see whether it
flattens the GG-105 tercile monotonicity. This script does exactly that, and
only that: read-only, offline, no live formula touched (Hard Rule 3).

DATA COHORT CAVEAT (read before trusting the numbers below)
--------------------------------------------------------------
As of this run, CURRENT_LOGIC_EPOCH=6 (GG-123, landed 2026-07-16T00:13:46Z),
but every resolved row currently in logs/t4_mlb_resolved_ledger.jsonl has
logic_epoch <= 3 (max epoch present: 3; distribution at run time: epoch1=122,
epoch2=122, epoch3=666, epoch4/5/6=0). Three epoch boundaries (GG-113, GG-119,
GG-123) landed within a ~24h window (2026-07-15 to 2026-07-16) and no bet
opened after the newest of those has had time to resolve yet. This means
scripts/run_band_monitor.py's official clean_n filter (== CURRENT_LOGIC_EPOCH)
currently returns clean_n=0 / UNDERPOWERED for T4M-PROJ -- a real, freshly
discovered monitoring-coverage gap (T4M-PROJ is flying blind on its own
band-monitor verdict until epoch-6 bets accumulate), logged separately in
DECISION_LOG.md. It is NOT evidence GG-105 resolved itself.

For this diagnostic, we deliberately relax to logic_epoch == 3 (the most
recent *fully resolved* epoch bucket, n=666, superset of the n=412 cohort
T-341/T-344 already analyzed and reported ANTI-PREDICTIVE + overconfident on).
This is defensible specifically for THIS metric because:
  1. GG-113/GG-119/GG-123 all fixed a VIG SIGN/MAGNITUDE bug in the *live
     approval-gate* formula (run_t4_mlb_live.py / run_mlb_paper_trade.py /
     run_t2_mlb_sameday.py) -- they never touched model_p itself, and they
     never touched compute_fee_net_edge() (run_exp017_mlb.py), which is what
     this script (like run_band_monitor.py) uses to recompute edge fresh,
     direction-symmetric, from raw model_p/mip -- defense in depth, per that
     module's own docstring. The live-approval-gate bug epoch boundary is
     therefore not a contamination vector for a model_p-vs-outcome reliability
     question, only for which bets got approved/how they were sized.
  2. Epoch 3 is itself already the GG-087/GG-077 POST-fix cohort (those two
     *did* touch structural direction/sign correctness) -- so epoch==3 is not
     "unclean" data, it is the same-quality cohort the standing b=0.600 CI
     figure was already computed from, just with more resolutions accrued.
This script prints both the epoch==3 cohort and an epoch>=1 (all resolved,
n=910) robustness check so the reader can see whether conclusions are
sensitive to the choice.

METHOD
------
For T in a sweep including NBA's ADR-0027 T=2.05: model_p_scaled =
sigmoid(logit(model_p) / T). Recompute fee_net_edge from model_p_scaled via
the same e17.compute_fee_net_edge() used live, rebuild MLBPosition tuples,
and rerun e17.edge_monotonicity() (identical Fisher/tercile methodology GG-105
was originally diagnosed with) plus c17c.calib_fit_ci()/reliability() on the
scaled probabilities. If T~2 flattens the tercile monotonicity and pulls
calib slope b toward 1.0, that is strong incremental mechanism-match evidence
for H1 on top of the existing shrinkage dose-response finding. If it does
NOT, that is equally informative -- it would argue temperature scaling alone
(a simple, global, one-parameter fix) is insufficient and the more granular
per-feature shrinkage APR-0025 already proposes is doing necessary additional
work, not just a redundant alternative fix.

This script performs NO write to any live file, portfolio, or ledger. It only
reads logs/t4_mlb_resolved_ledger.jsonl (already-pulled local cache) and
prints a report.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17                 # noqa: E402
import run_exp017c_calibration_mlb as c17c   # noqa: E402
import run_band_monitor as bm                # noqa: E402

LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
T_SWEEP = [1.00, 1.25, 1.50, 1.75, 2.00, 2.05, 2.25, 2.50, 3.00]
BINS = 5
BOOT = 2000
SEED = 17
ALPHA = 0.10


def scale_records(recs: list[dict], T: float) -> list[dict]:
    """Return new record dicts with _model_p replaced by the temperature-scaled
    value and _fne (fee_net_edge) recomputed from the scaled probability via
    the SAME e17.compute_fee_net_edge() used for the live edge_monotonicity
    check. Original recs are not mutated."""
    out = []
    for r in recs:
        p_scaled = c17c.sigmoid(c17c.logit(r["_model_p"]) / T)
        rr = dict(r)
        rr["_model_p"] = p_scaled
        rr["_fne"] = e17.compute_fee_net_edge(r["_dir"], p_scaled, r["_mip"])
        out.append(rr)
    return out


def report_for_cohort(label: str, recs: list[dict]) -> None:
    print("=" * 100)
    print(f"COHORT: {label}  (n={len(recs)})")
    print("=" * 100)
    if len(recs) < 30:
        print("  n < 30 -- skipping (GG-098 discipline, would be an underpowered read).")
        return

    header = (f"{'T':>5} | {'fisher_p':>9} | {'verdict':>16} | "
              f"{'tercile1_wr':>11} {'tercile2_wr':>11} {'tercile3_wr':>11} | "
              f"{'calib_b':>8} {'b_excl_1':>9} | {'ECE':>7}")
    print(header)
    print("-" * len(header))

    import random
    for T in T_SWEEP:
        scaled = scale_records(recs, T)
        positions = bm.to_mlb_positions(scaled)
        mono = e17.edge_monotonicity(positions, alpha=ALPHA)
        terciles = mono.get("terciles", [])
        wrs = [f"{t['winrate']:.3f}" for t in terciles] if len(terciles) == 3 else ["n/a"] * 3
        rng = random.Random(SEED)
        fit = c17c.calib_fit_ci(scaled, BOOT, rng)
        ece_val = c17c.ece(scaled, BINS)
        marker = "  <-- T=1 (raw, no scaling)" if T == 1.0 else (
            "  <-- NBA ADR-0027 T" if T == 2.05 else "")
        print(f"{T:>5.2f} | {mono.get('fisher_pvalue', float('nan')):>9.4f} | "
              f"{mono.get('verdict', '?'):>16} | "
              f"{wrs[0]:>11} {wrs[1]:>11} {wrs[2]:>11} | "
              f"{fit['slope_b']:>8.3f} {str(fit['b_excludes_1']):>9} | "
              f"{ece_val:>7.4f}{marker}")

    print()
    print(f"  Reliability curve at T=1.00 (raw) vs T=2.05 (NBA-analog), {BINS} bins:")
    for T in (1.00, 2.05):
        scaled = scale_records(recs, T)
        rows = c17c.reliability(scaled, BINS)
        print(f"    T={T:.2f}:")
        for row in rows:
            if row.get("n", 0) == 0:
                print(f"      {row['bin']}: n=0")
                continue
            print(f"      {row['bin']}: n={row['n']:>4}  mean_forecast={row['mean_forecast']:.3f}  "
                  f"empirical_rate={row['empirical_rate']:.3f}  gap={row['gap']:+.3f}")
    print()


def main() -> int:
    all_recs = bm.load_t4_ledger(LEDGER)
    if not all_recs:
        print(f"ERROR: no records loaded from {LEDGER} -- run "
              f"scripts/build_t4_resolved_ledger.py --pull first.", file=sys.stderr)
        return 1

    epoch3 = [r for r in all_recs if r.get("logic_epoch") == 3]
    report_for_cohort("logic_epoch == 3 (most recent fully-resolved epoch, primary)", epoch3)
    report_for_cohort("logic_epoch >= 1 (all resolved, robustness check)", all_recs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

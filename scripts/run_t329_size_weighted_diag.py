#!/usr/bin/env python3
"""
T-329 — GG-105 diagnostic 1: size-weighted re-run of the T4M-PROJ edge-tercile
inversion found by T-324 (T324_T1_VS_T4_DIVERGENCE_MEMO.md).

WHY THIS EXISTS
---------------
GG-105 found that T4M-PROJ's clean_n cohort (n=271, CURRENT_LOGIC_EPOCH=3) shows
a statistically significant, tercile-monotonic ANTI-PREDICTIVE relationship
between computed edge and win rate (74.4% -> 64.4% -> 58.2% across three ~90-count
edge-magnitude terciles, unweighted). T-324's memo explicitly ruled out sizing as
the *source* of that win/loss pattern (Fisher/tercile tests are unweighted counts
by construction) but flagged it as a *compounding risk*: ADR-0010/ADR-0039 Kelly
sizing scales stake with computed edge magnitude, so if the largest-edge tercile
is also getting the largest stakes, the anti-predictive relationship could be
doing more P&L damage than the barely-positive unweighted aggregate (+$0.047/bet)
suggests -- or could already be net-negative on a stake-weighted basis.

This script answers exactly that, and only that. It does not re-litigate the
Fisher/tercile finding itself (T-324 already established it is not a thin-cell
artifact) and does not attempt the game-state segmentation (T-324 recommendation
#3 in GG-105) -- that is a separate, larger diagnostic deferred by this session's
own priority call (see DECISION_LOG.md entry alongside this script's introduction).

METHOD
------
Reuses run_band_monitor.py's T4M-PROJ loader (load_t4_ledger) and clean_n filter
(filter_clean) verbatim -- same defense-in-depth as T-324: edge is read from
`_fne`, which load_t4_ledger() recomputes via the audited
run_exp017_mlb.compute_fee_net_edge() helper, never trusted from a stored field.
Records are sorted by `_fne` ascending and split into 3 terciles matching T-324's
90/90/91 split exactly (same n, same sort key, same direction). Each tercile is
then scored two ways:
  (1) unweighted win_rate / total_pnl -- reproduces T-324's table, as a
      correctness check that this script is looking at the same cohort.
  (2) ab_harness.metrics() applied per-tercile -- adds pnl_per_dollar (sum(pnl)
      / sum(size), i.e. Sigma-pnl-staked return) and avg/total stake per tercile.
If avg_stake rises with tercile *and* pnl_per_dollar falls (or goes negative) in
the same direction as win_rate, sizing is amplifying the inversion's P&L impact,
confirming GG-105's compounding-risk flag. If pnl_per_dollar does not track
win_rate's decline, sizing is closer to sizing-neutral here despite the rank
inversion.

Run:
  python3 scripts/run_t329_size_weighted_diag.py
  python3 scripts/run_t329_size_weighted_diag.py --t4-ledger logs/t4_mlb_resolved_ledger.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_band_monitor as bm    # noqa: E402  load_t4_ledger, filter_clean
import ab_harness as abh         # noqa: E402  metrics() -- pnl_per_dollar

DEFAULT_T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
OUT_DIR = Path("exp_output/T329-SIZE-WEIGHTED-DIAG")


def build_terciles(recs: list[dict]) -> list[list[dict]]:
    """Sort by _fne ascending, split into 3 as-equal-as-possible contiguous
    bins -- same construction T-324 used (smallest-edge bin first)."""
    ordered = sorted(recs, key=lambda r: r["_fne"])
    n = len(ordered)
    base, rem = divmod(n, 3)
    sizes = [base + (1 if i < rem else 0) for i in range(3)]
    terciles, i = [], 0
    for s in sizes:
        terciles.append(ordered[i:i + s])
        i += s
    return terciles


def analyze(recs: list[dict]) -> dict:
    terciles = build_terciles(recs)
    rows = []
    for idx, t in enumerate(terciles, start=1):
        n = len(t)
        edge_mean = sum(r["_fne"] for r in t) / n if n else float("nan")
        win_rate_unweighted = sum(r["_win"] for r in t) / n if n else float("nan")
        total_pnl_unweighted = sum(r["_pnl"] for r in t)
        m = abh.metrics(t)
        avg_stake = sum(r["_size"] for r in t) / n if n else float("nan")
        total_staked = sum(r["_size"] for r in t)
        rows.append({
            "tercile": idx,
            "n": n,
            "edge_mean": edge_mean,
            "win_rate": win_rate_unweighted,
            "total_pnl_unweighted": total_pnl_unweighted,
            "avg_stake_usd": avg_stake,
            "total_staked_usd": total_staked,
            "pnl_per_dollar_staked": m["pnl_per_dollar"],
            "ev_per_bet_usd": m["ev_per_bet_usd"],
        })

    overall = abh.metrics(recs)
    overall_unweighted_ev = sum(r["_pnl"] for r in recs) / len(recs) if recs else 0.0

    stake_rises_with_tercile = (
        rows[2]["avg_stake_usd"] > rows[1]["avg_stake_usd"] > rows[0]["avg_stake_usd"]
    ) if len(rows) == 3 else False
    return_falls_with_tercile = (
        rows[2]["pnl_per_dollar_staked"] < rows[1]["pnl_per_dollar_staked"] < rows[0]["pnl_per_dollar_staked"]
    ) if len(rows) == 3 else False
    sizing_amplifies = stake_rises_with_tercile and return_falls_with_tercile

    return {
        "n": len(recs),
        "terciles": rows,
        "overall_pnl_per_dollar_staked": overall["pnl_per_dollar"],
        "overall_ev_per_bet_usd": overall_unweighted_ev,
        "overall_total_staked_usd": sum(r["_size"] for r in recs),
        "overall_total_pnl_usd": sum(r["_pnl"] for r in recs),
        "stake_rises_with_tercile": stake_rises_with_tercile,
        "return_falls_with_tercile": return_falls_with_tercile,
        "sizing_amplifies_inversion": sizing_amplifies,
    }


def _print_report(result: dict) -> None:
    print("=" * 100)
    print("T-329 — GG-105 DIAGNOSTIC 1: SIZE-WEIGHTED TERCILE RE-RUN (T4M-PROJ, clean_n)")
    print("=" * 100)
    print(f"\nn={result['n']}")
    print(f"{'Tercile':<8}{'n':<6}{'edge_mean':<12}{'win_rate':<11}"
          f"{'avg_stake':<12}{'total_staked':<15}{'$/staked':<11}{'ev/bet':<10}")
    for r in result["terciles"]:
        print(f"{r['tercile']:<8}{r['n']:<6}{r['edge_mean']:<12.4f}{r['win_rate']:<11.3f}"
              f"${r['avg_stake_usd']:<11.2f}${r['total_staked_usd']:<14.2f}"
              f"{r['pnl_per_dollar_staked'] * 100:<10.2f}%${r['ev_per_bet_usd']:<9.4f}")
    print(f"\nOverall: $/staked={result['overall_pnl_per_dollar_staked'] * 100:+.2f}%  "
          f"EV/bet=${result['overall_ev_per_bet_usd']:+.4f}  "
          f"total_staked=${result['overall_total_staked_usd']:.2f}  "
          f"total_pnl=${result['overall_total_pnl_usd']:+.2f}")
    print(f"\nStake rises monotonically with tercile (edge magnitude): "
          f"{result['stake_rises_with_tercile']}")
    print(f"$/staked return falls monotonically with tercile: "
          f"{result['return_falls_with_tercile']}")
    print(f"\n{'*** SIZING AMPLIFIES THE INVERSION ***' if result['sizing_amplifies_inversion'] else 'Sizing does NOT amplify the inversion by the monotonic-both-ways test.'}")
    print("=" * 100)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER)
    p.add_argument("--out", type=Path, default=OUT_DIR)
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    recs = bm.filter_clean(bm.load_t4_ledger(args.t4_ledger), "T4M-PROJ")
    if len(recs) < 3:
        print(f"Only {len(recs)} clean T4M-PROJ records found at {args.t4_ledger} "
              f"-- need at least 3 for a tercile split. Nothing to analyze.")
        return 1

    result = analyze(recs)
    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "size_weighted_diag_results.json"
    out_json.write_text(json.dumps(result, indent=2))
    _print_report(result)
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

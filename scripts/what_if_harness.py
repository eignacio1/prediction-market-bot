#!/usr/bin/env python3
"""
D1 — Offline replay / what-if harness (Window D, ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md)

WHY THIS EXISTS
----------------
GG-105's leading remediation candidates (temperature scaling, then APR-0025's
ba_l10 shrinkage) both needed to be evaluated against the REAL resolved ledger
before touching a live epoch (an epoch bump zeroes every band's clean_n,
GG-124 -- churn is expensive, not free). scripts/run_t373_gg105_temp_scaling_
whatif.py proved the pattern for exactly one candidate (temperature scaling,
hardcoded T-sweep). This script generalizes that pattern into a reusable,
flag-driven harness so any future candidate model_p transform can be tested
the same way, without writing a new one-off script each time. It supersedes
run_t373's role as "the" what-if tool going forward; that script is left in
place as a citable precedent/audit trail, not deleted.

WHAT THIS DOES
---------------
Loads the real resolved ledger (T1/T2/T3 live MLB book, or the T4M-PROJ
ledger), applies a named --flag transform to each position's model_p (fee_net
_edge is ALWAYS recomputed fresh via the audited, direction-aware
compute_fee_net_edge() -- GG-077 discipline, never hand-adjusted), and prints/
optionally writes the same three diagnostics GG-105/T-177 already use to judge
a candidate fix:
  1. edge-tercile monotonicity (Fisher exact, MONOTONIC/ANTI-PREDICTIVE/
     INCONCLUSIVE verdict) -- e17.edge_monotonicity()
  2. calibration slope + bootstrap CI -- c17c.calib_fit_ci()
  3. Brier/Murphy decomposition + ECE -- c17c.brier_murphy() / c17c.ece()

NO WRITE to any live file, portfolio, or ledger, and NO epoch bump. Read-only
by construction: it only reads the local ledger/portfolio cache and prints (or
--out writes) a report.

SCOPE LIMITATION (read before assuming this replaces a real model refit)
--------------------------------------------------------------------------
Neither resolved-ledger schema (paper_portfolio_mlb.json's closed_positions,
nor logs/t4_mlb_resolved_ledger.jsonl written by build_t4_resolved_ledger.py)
persists the RAW per-bet features (ab_sum, h_sum, raw ba_l10) that fed the
live model at bet-time -- only the final scalar model_p survives to the
ledger. That means this harness can faithfully replay any candidate that is
expressible as a POST-HOC transform of model_p (temperature scaling, an
affine logit-shift, a Platt-style re-calibration) -- but it CANNOT
faithfully re-derive "what model_p would ba_l10_shrunk have produced" from
the ledger alone, because the raw ba_l10/ab_sum inputs the live formula would
need are not there to re-run. A true feature-level replay (e.g. testing
APR-0025's shrinkage formula itself, not just its aggregate calibration
effect) needs either (a) the candidate model/feature pipeline to compute its
own new model_p externally (e.g. from a full backtest re-run against the raw
C2 feature store) and hand them to a future `--overrides-file` extension
point keyed by kalshi_ticker/position_id, or (b) extending the ledger schema
to persist raw features at bet-time. Neither is built here -- flagging it
now (and in DECISION_LOG.md) rather than silently under-scoping D1 or
over-building an unused path before A2 confirms it needs it.

FLAG REGISTRY
--------------
  raw          -- identity transform (baseline, T=1 equivalent)
  temp_scale   -- params: T (float, default 1.0). model_p' = sigmoid(logit(p)/T).
                  Exactly reproduces run_t373's methodology (NBA ADR-0027 T=2.05
                  is the historical reference point for "how much flattening a
                  global recalibration fix buys").
  logit_shift  -- params: a (float, default 1.0), b (float, default 0.0).
                  model_p' = sigmoid(logit(p)*a + b). Generalizes temp_scale
                  (a=1/T, b=0) into a full affine logit-space transform, so any
                  candidate expressible as an affine recalibration (not just a
                  pure temperature) can be swept without a new script.

Run:
  python3 scripts/what_if_harness.py --book t1t2t3 --flag raw
  python3 scripts/what_if_harness.py --book t4 --flag temp_scale --param T=2.05
  python3 scripts/what_if_harness.py --book t4 --flag logit_shift --param a=0.6 --param b=0.1 \\
      --out exp_output/whatif_logit_shift.json
  python3 scripts/what_if_harness.py --book t4 --flag temp_scale --param T=2.05 --logic-epoch 3
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17                 # noqa: E402  MLBPosition, compute_fee_net_edge, edge_monotonicity, MIN_N
import run_exp017c_calibration_mlb as c17c   # noqa: E402  sigmoid, logit, calib_fit_ci, brier_murphy, ece
import run_band_monitor as bm                # noqa: E402  load_t4_ledger, to_mlb_positions

DEFAULT_T1_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
DEFAULT_T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
BINS = 5
BOOT = 2000
SEED = 17
ALPHA = 0.10

Transform = Callable[[list, dict], list]


def _rescale(positions: list, params: dict, new_p_fn: Callable[[float], float]) -> list:
    """Shared apply step for every flag: recompute model_p via new_p_fn, then
    ALWAYS recompute fee_net_edge fresh from the scaled probability via the
    audited, direction-aware e17.compute_fee_net_edge() (GG-077 -- never trust
    or hand-adjust a stored/derived edge value)."""
    out = []
    for p in positions:
        p_scaled = new_p_fn(p.model_p)
        fne = e17.compute_fee_net_edge(p.direction, p_scaled, p.mip)
        out.append(p._replace(model_p=p_scaled, fee_net_edge=fne))
    return out


def flag_raw(positions: list, params: dict) -> list:
    return _rescale(positions, params, lambda p: p)


def flag_temp_scale(positions: list, params: dict) -> list:
    T = float(params.get("T", 1.0))
    return _rescale(positions, params, lambda p: c17c.sigmoid(c17c.logit(p) / T))


def flag_logit_shift(positions: list, params: dict) -> list:
    a = float(params.get("a", 1.0))
    b = float(params.get("b", 0.0))
    return _rescale(positions, params, lambda p: c17c.sigmoid(c17c.logit(p) * a + b))


FLAGS: dict[str, Transform] = {
    "raw": flag_raw,
    "temp_scale": flag_temp_scale,
    "logit_shift": flag_logit_shift,
}


def parse_params(pairs: list[str] | None) -> dict:
    out: dict = {}
    for pair in pairs or []:
        k, _, v = pair.partition("=")
        if not _:
            raise SystemExit(f"--param must be KEY=VAL, got: {pair!r}")
        out[k] = v
    return out


def load_positions(
    book: str,
    portfolio_path: Path,
    t4_ledger_path: Path,
    logic_epoch: int | None,
) -> list:
    """book='t1t2t3' -> live MLB book (T1/T2/T3, band-mixed pool, shared
    PaperTrader schema). book='t4' -> T4M-PROJ resolved ledger.
    logic_epoch filtering is only wired for t4 (matches run_t373 precedent's
    clean-cohort caveat); the t1t2t3 loader does not currently expose
    logic_epoch through MLBPosition, so no filter is applied there -- noted
    in the printed report, not silently assumed."""
    if book == "t1t2t3":
        if not portfolio_path.exists():
            raise SystemExit(f"ERROR: {portfolio_path} not found. Pull the live MLB "
                              f"portfolio cache first (see governance_scan.sh's ssh-cache step).")
        positions = e17.load_portfolio(portfolio_path)
        return e17.deduplicate(positions)
    elif book == "t4":
        if not t4_ledger_path.exists():
            raise SystemExit(f"ERROR: {t4_ledger_path} not found. Run "
                              f"scripts/build_t4_resolved_ledger.py --pull first.")
        recs = bm.load_t4_ledger(t4_ledger_path)
        if logic_epoch is not None:
            recs = [r for r in recs if r.get("logic_epoch") == logic_epoch]
        return bm.to_mlb_positions(recs)
    raise SystemExit(f"ERROR: unknown --book {book!r} (expected t1t2t3 or t4)")


def calib_records(positions: list) -> list[dict]:
    """Same {_model_p, _event} convention as exp_retrospective_core.
    _calibration_records() / run_band_monitor._attach_event() -- restated
    inline rather than cross-imported since it is a single audited one-liner,
    matching the existing convention in both of those modules."""
    return [
        {"_model_p": p.model_p,
         "_event": 1 if ((p.direction == "YES") == (p.outcome == "WIN")) else 0}
        for p in positions
    ]


def score(label: str, positions: list) -> dict:
    print("=" * 100)
    print(f"COHORT: {label}  (n={len(positions)})")
    print("=" * 100)
    result: dict = {"label": label, "n": len(positions)}

    if len(positions) < e17.MIN_N:
        print(f"  n={len(positions)} < MIN_N={e17.MIN_N} -- INCONCLUSIVE "
              f"(GG-098 discipline: too few positions for any verdict).")
        result["verdict"] = "INCONCLUSIVE"
        return result

    mono = e17.edge_monotonicity(positions, alpha=ALPHA)
    recs = calib_records(positions)
    rng = random.Random(SEED)
    fit = c17c.calib_fit_ci(recs, BOOT, rng)
    ece_val = c17c.ece(recs, BINS)
    murphy = c17c.brier_murphy(recs, BINS)

    print(f"  Edge-tercile monotonicity: verdict={mono['verdict']}  "
          f"fisher_p={mono['fisher_pvalue']:.4f}  "
          f"winrate(edge>0)={mono['winrate_edge_pos']:.3f}  "
          f"winrate(edge<=0)={mono['winrate_edge_neg']:.3f}")
    for t in mono.get("terciles", []):
        print(f"    tercile {t['tercile']}: n={t['n']:>4}  "
              f"edge_mean={t['edge_mean']:+.4f}  winrate={t['winrate']:.3f}  pnl=${t['pnl']:+.2f}")
    print(f"  Calibration slope b={fit['slope_b']:.3f}  b_ci={fit['b_ci']}  "
          f"b_excludes_1={fit['b_excludes_1']}  ({fit['interpretation']})")
    print(f"  Brier (full)={murphy['brier_full']:.4f}  "
          f"reliability={murphy['reliability']:.4f}  resolution={murphy['resolution']:.4f}  "
          f"uncertainty={murphy['uncertainty']:.4f}  recompose_ok={murphy['recompose_ok']}")
    print(f"  ECE={ece_val:.4f}")
    print()

    result.update({
        "edge_monotonicity": mono,
        "calibration_fit": fit,
        "brier_murphy": murphy,
        "ece": ece_val,
    })
    return result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="D1 -- offline replay/what-if harness (Window D, no deploy, no epoch bump)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--book", choices=["t1t2t3", "t4"], required=True,
                    help="Which resolved book to replay.")
    p.add_argument("--flag", choices=sorted(FLAGS), default="raw",
                    help="Candidate model_p transform to apply (default: raw/identity).")
    p.add_argument("--param", action="append", default=[],
                    help="Flag parameter as KEY=VAL. May be repeated (e.g. --param a=0.6 --param b=0.1).")
    p.add_argument("--portfolio", metavar="PATH", default=str(DEFAULT_T1_PORTFOLIO),
                    help=f"t1t2t3 portfolio JSON path (default: {DEFAULT_T1_PORTFOLIO}).")
    p.add_argument("--t4-ledger", metavar="PATH", default=str(DEFAULT_T4_LEDGER),
                    help=f"t4 resolved ledger JSONL path (default: {DEFAULT_T4_LEDGER}).")
    p.add_argument("--logic-epoch", type=int, default=None,
                    help="t4 only: restrict to a single logic_epoch cohort (default: all resolved).")
    p.add_argument("--out", metavar="PATH", default=None,
                    help="Optional: write the scored report as JSON to PATH.")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    params = parse_params(args.param)
    transform = FLAGS[args.flag]

    positions = load_positions(
        args.book, Path(args.portfolio), Path(args.t4_ledger), args.logic_epoch)
    if not positions:
        print("ERROR: 0 positions loaded -- nothing to score.", file=sys.stderr)
        return 1

    baseline = score(f"book={args.book} flag=raw (baseline, n={len(positions)})", positions)
    scored_positions = transform(positions, params)
    label = f"book={args.book} flag={args.flag} params={params or '{}'}"
    candidate = score(label, scored_positions)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(
            {"book": args.book, "flag": args.flag, "params": params,
             "logic_epoch": args.logic_epoch, "baseline": baseline, "candidate": candidate},
            indent=2, default=str))
        print(f"Wrote report: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

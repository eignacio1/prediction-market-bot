#!/usr/bin/env python3
"""
EXP-T4-01 MLB — Commercial Validation: T4M-PROJ Live Model Edge vs Kalshi KXMLBHIT Prices
ADR-0024 | GG-004 | GG-046 | T-375

WHY THIS EXISTS
----------------
GG-046 ("T4 Commercial Validation Gate") found T4M-PROJ's resolved-position
count had crossed the legacy ADR-0024 Tier 2 single-sport floor (raw_n=910,
2026-07-15 VPS pull) with no experiment ever run to check what that data
actually says about T4's live-market edge — EXP-017 answers this question for
T1 (pregame calibration edge), but no analogous script existed for T4
(live market-latency edge, see CLAUDE.md's Alpha Taxonomy — these are
independent theses and require independent proofs). GG-046's own Resolution
field specifies building "EXP-T4-01, analogous to EXP-017: compare T4
model_p against live Kalshi market price at the moment each evaluation
fired; compute net_edge over resolved bets; apply ADR-0024 Tier 1/2
thresholds independently." This script is that experiment.

This is a thin wrapper: all accounting (fee-net edge, EV, win rate, ADR-0024
tier check, edge-monotonicity/anti-predictive guard, calibration diagnostics)
is scripts/exp_retrospective_core.py — the exact same code EXP-017 (T1) runs,
because T4M-PROJ's paper_portfolio_mlb_t4.json closed_positions carry the
same schema (model_p, mid_price_at_entry, vig_at_entry, direction, outcome,
pnl, kalshi_ticker, kalshi_threshold, game_date, player_name) as T1's
portfolio — C5/PaperTrader writes both. Only the default portfolio path,
output dir, and report title differ from EXP-017.

DO NOT conflate this verdict with EXP-017's. T1 and T4M-PROJ are independent
alpha theses (CLAUDE.md Alpha Taxonomy) sharing only the accounting
methodology, not the underlying signal — a positive verdict here says
nothing about T1, and vice versa. Do not conflate T4M-PROJ (this script) with
T4M-ARITH/T4M-FLOW (ADR-0039 sub-bands, still BLOCKED pending their own
EXP-ARITH-MLB-01/EXP-FLOW-MLB-01) — those are architecturally separate
modules (GG-061) and this script does not cover them.

Data requirements:
  logs/paper_portfolio_mlb_t4.json
  Position records must carry: model_p, threshold, mid_price_at_entry, direction, outcome
  Optional but preferred: fee_net_edge (recomputed regardless, see core module note), pnl

Run:
  python3 scripts/run_exp_t4_01_mlb.py
  python3 scripts/run_exp_t4_01_mlb.py --portfolio logs/paper_portfolio_mlb_t4.json
  python3 scripts/run_exp_t4_01_mlb.py --csv path/to/backtest.csv
  python3 scripts/run_exp_t4_01_mlb.py --ci

Exit codes (--ci mode only):
  0  Positive or INCONCLUSIVE — no alarm
  2  CONFIRMED_NEGATIVE (Tier 2) — halt + DS review
  3  DIAGNOSTIC_SPRINT (Tier 1, EV < -$0.03) — DS review required
  4  Insufficient data (n < MIN_N)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp_retrospective_core import (  # noqa: E402
    MIN_N,
    V_CONF_NEG,
    V_DIAG,
    analyse,
    load_csv,
    load_portfolio,
    print_report,
)

SPORT             = "mlb"
BAND              = "T4M-PROJ"
DEFAULT_PORTFOLIO = Path("logs/paper_portfolio_mlb_t4.json")
OUT_DIR           = Path("exp_output/EXP-T4-01-MLB")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="EXP-T4-01 MLB — Commercial validation of T4M-PROJ vs Kalshi KXMLBHIT (ADR-0024 / GG-004 / GG-046)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--portfolio", metavar="PATH",
        default=str(DEFAULT_PORTFOLIO),
        help=f"T4M-PROJ paper portfolio JSON (default: {DEFAULT_PORTFOLIO})",
    )
    p.add_argument(
        "--csv", metavar="PATH",
        help="Read from a resolved-bet CSV instead of portfolio JSON (batch backtest mode)",
    )
    p.add_argument(
        "--nba-n", type=int, default=0, metavar="N",
        help="Number of unique resolved NBA unique markets (enables multi-sport Tier 2 check)",
    )
    p.add_argument(
        "--alpha", type=float, default=0.10,
        help="Fisher p-value threshold for edge monotonicity verdict (default 0.10)",
    )
    p.add_argument(
        "--ci", action="store_true",
        help="CI mode: exit 2 on CONFIRMED_NEGATIVE, exit 3 on DIAGNOSTIC_SPRINT, exit 4 insufficient",
    )
    p.add_argument(
        "--include-duplicates", action="store_true",
        help="Include duplicate_of-annotated positions (excluded by default)",
    )
    p.add_argument(
        "--no-save", action="store_true",
        help="Do not save results JSON to exp_output/",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    exc_dup = not args.include_duplicates

    if args.csv:
        path = Path(args.csv)
        if not path.exists():
            print(f"ERROR: CSV not found: {path}", file=sys.stderr)
            return 1
        positions = load_csv(path, exclude_duplicates=exc_dup)
        label = f"CSV {path.name}"
    else:
        path = Path(args.portfolio)
        if not path.exists():
            print(f"ERROR: portfolio not found: {path}", file=sys.stderr)
            print("  T4M-PROJ paper trading has not yet generated positions.", file=sys.stderr)
            print(f"  Expected path: {path}", file=sys.stderr)
            return 1
        positions = load_portfolio(path, exclude_duplicates=exc_dup)
        label = f"portfolio {path.name}"

    result = analyse(
        positions,
        alpha=args.alpha,
        nba_n=args.nba_n,
        label=label,
        sport=SPORT,
        adr="ADR-0024",
        gg="GG-004",
    )
    result["band"] = BAND
    print_report(
        result,
        title="EXP-T4-01 MLB — Commercial Validation of T4M-PROJ vs Kalshi KXMLBHIT Prices",
        subtitle="ADR-0024 | GG-004 | GG-046 | T-375",
    )

    if not args.no_save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / "EXP-T4-01-MLB_results.json"
        with open(out_path, "w") as fh:
            json.dump(result, fh, indent=2)
        print(f"Results saved: {out_path}")

    if args.ci:
        verdict = result["verdict"]
        if verdict == V_CONF_NEG:
            return 2
        if verdict == V_DIAG:
            return 3
        if result["n_unique_markets"] < MIN_N:
            return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

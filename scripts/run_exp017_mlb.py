#!/usr/bin/env python3
"""
EXP-017 MLB — Commercial Validation: MLB Model Edge vs Kalshi KXMLBHIT Prices
ADR-0024 | GG-004 | OQ-023 | T-184

Answers the commercial question: does the MLB LR+Platt model (train_mlb_model.py)
generate positive fee-net EV against actual Kalshi KXMLBHIT market prices?

GG-004 (OPEN) resolution path:
  This script accumulates evidence from MLB paper trading positions.
  GG-004 closes CONFIRMED_POSITIVE once Tier 2 criteria are met.
  Until then GG-004 remains OPEN — no claim of positive alpha is valid.

ADR-0024 tier checks:
  Tier 1 (n >= 150 unique markets):
    EV/bet < -$0.03  ->  DIAGNOSTIC_SPRINT  (model class review per ADR-0004)
    EV/bet >=  0     ->  continue toward Tier 2
  Tier 2 (n >= 500 unique MLB markets, OR --nba-n >=150 alongside n >=150 MLB):
    EV > 0, p < 0.05  ->  CONFIRMED_POSITIVE  — GG-004 closeable
    EV < -$0.03        ->  CONFIRMED_NEGATIVE  — halt + ADR-0004 review

Edge monotonicity check (T-177 / GG-037 guard):
  MONOTONIC       ->  edge>0 bets win MORE often (signal predictive)
  ANTI-PREDICTIVE ->  edge>0 bets win LESS often (NBA Finals pattern; escalate to DS)
  INCONCLUSIVE    ->  no statistically significant pattern

MLB-specific threshold breakdown:
  Separate EV and win-rate rows for k in {1, 2, 3} (hits thresholds).
  k=1 (1+ hits) has highest hit rate; k=3 (3+ hits) is rarest — different dynamics.

Data requirements:
  logs/paper_portfolio_mlb.json
  Position records must carry: model_p, threshold, mid_price_at_entry, direction, outcome
  Optional but preferred: fee_net_edge (pre-computed by C4 risk engine), pnl

Run:
  python3 scripts/run_exp017_mlb.py
  python3 scripts/run_exp017_mlb.py --portfolio logs/paper_portfolio_mlb.json
  python3 scripts/run_exp017_mlb.py --csv path/to/backtest.csv
  python3 scripts/run_exp017_mlb.py --nba-n 200   # multi-sport Tier 2 check
  python3 scripts/run_exp017_mlb.py --ci           # CI mode

Exit codes (--ci mode only):
  0  Positive or INCONCLUSIVE — no alarm
  2  CONFIRMED_NEGATIVE (Tier 2) — halt + DS review
  3  DIAGNOSTIC_SPRINT (Tier 1, EV < -$0.03) — DS review required
  4  Insufficient data (n < MIN_N)

IMPLEMENTATION NOTE (T-375, GG-060 Phase 4): the accounting core (loaders,
fee/edge math, ADR-0024 tier logic, edge monotonicity, calibration, report
printer) moved to scripts/exp_retrospective_core.py so EXP-T4-01
(run_exp_t4_01_mlb.py) can reuse it without forking this file. This script is
now a thin CLI wrapper: MLB-specific defaults (portfolio path, output dir,
report title) plus argument parsing only. Behavioral equivalence with the
pre-refactor version was verified by diffing full report output against a
real VPS T1 portfolio pull (n=261) before and after the split — see
DECISION_LOG.md T-375 Phase 4 entry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp_retrospective_core import (  # noqa: E402
    ADR_0024_TIER1_N,
    ADR_0024_TIER1_DIAG_EV,
    ADR_0024_TIER2_N_SINGLE,
    ADR_0024_TIER2_N_MULTI,
    ADR_0024_P_THRESHOLD,
    KALSHI_FEE_RATE,
    MIN_N,
    V_CONF_POS,
    V_DIR_POS,
    V_CONF_NEG,
    V_DIR_NEG,
    V_DIAG,
    V_INC,
    E_ANTI,
    E_MONO,
    E_INC,
    kalshi_fee,
    compute_fee_net_edge,
    compute_pnl_unit,
    MLBPosition,
    load_portfolio,
    load_csv,
    deduplicate,
    ev_stats,
    threshold_breakdown,
    adr0024_tier,
    ev_verdict,
    _fisher_pvalue,
    _tercile_table,
    edge_monotonicity,
    analyse,
    print_report,
)

# Pre-refactor (T-375, GG-060 Phase 4) callers/tests import these two loaders
# under their original private names — keep the alias rather than churn every
# call site, since the underlying behavior (not the name) is what moved.
_load_portfolio = load_portfolio
_load_csv = load_csv

SPORT             = "mlb"
DEFAULT_PORTFOLIO = Path("logs/paper_portfolio_mlb.json")
OUT_DIR           = Path("exp_output/EXP-017-MLB")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="EXP-017 MLB — Commercial validation vs Kalshi KXMLBHIT (ADR-0024 / GG-004)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--portfolio", metavar="PATH",
        default=str(DEFAULT_PORTFOLIO),
        help=f"MLB paper portfolio JSON (default: {DEFAULT_PORTFOLIO})",
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
            print("  MLB paper trading has not yet generated positions.", file=sys.stderr)
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
    print_report(
        result,
        title="EXP-017 MLB — Commercial Validation vs Kalshi KXMLBHIT Prices",
        subtitle="ADR-0024 | GG-004 | T-184",
    )

    if not args.no_save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / "EXP-017-MLB_results.json"
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

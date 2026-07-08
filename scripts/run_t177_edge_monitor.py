#!/usr/bin/env python3
"""T-177 Edge Inversion Monitor

GG-037 / GG-004 ongoing diagnostic. Reads closed positions from the live paper
portfolio (default) or a resolved-bet CSV and answers: is the model's fee_net_edge
signal monotonically predictive of outcomes, or anti-predictive?

After calibration (ADR-0027, T=2.05), the NBA Finals dataset (n=144 clean bets)
showed edge>0 winrate=0.356 vs edge<=0 winrate=0.747 — the signal is inverted.
This script is the recurring monitor that catches whether this persists as MLB and
regular-season data accumulate, or whether it was a Finals-specific artifact.

T-177 Resolution path:
  (a) This script provides the ongoing anti-predictive guard signal.
  (b) EXP-017 at scale (MLB season, n>=150) is the structural resolution gate.

If ANTI-PREDICTIVE fires at p<0.10 on a structurally adequate sample (ADR-0024),
T-177 requires a DS-directed model architecture review per ADR-0004 trigger.

T-256 (2026-07-07): default was `logs/paper_portfolio.json` — the dark/frozen NBA
book (GG-070 dual-ledger split) — so every unparameterized run silently monitored
a dead ledger instead of the ACTIVE MLB one. Default is now `--sport mlb`, which
resolves to the same VPS-synced cache path (`logs/.vps_portfolio_cache_<sport>.json`)
the CLAUDE.md session-start governance hook uses, so this script and the hook can
never disagree about which file is "the live book."

Band-awareness caveat (GG-099): `PaperTrader.open_position()` does not persist a
`band` field on closed positions (T2/T3 MLB construct one internally but it is
dropped before the record is written), and T4M-PROJ is tracked in a wholly separate
store (`t4_position_trajectories.jsonl`, pool_isolated) with no resolved-outcome
join as of this fix. So the MLB book this script reads is band-BLIND — it mixes
whatever of T1/T2/T3 has resolved into one undifferentiated stream, and it does
NOT include T4M-PROJ at all. This script does not claim otherwise (see the
band-mix note printed with every report). True per-band splitting (a real `band`
field on the position record, plus T4M-PROJ's resolved join) is T-255's scope,
which depends on T-253/T-254 — do not treat this script's verdict as scoped to
any single band until T-255 lands.

Usage:
    # Read the live ACTIVE-pool portfolio (default: MLB, VPS-synced cache):
    python scripts/run_t177_edge_monitor.py

    # Read the dark/frozen NBA book explicitly (historical, not live risk):
    python scripts/run_t177_edge_monitor.py --sport nba

    # Read historical CSV (nba_finals format):
    python scripts/run_t177_edge_monitor.py --csv data/nba_finals_clean_dataset.csv

    # Rolling window analysis (last N bets only):
    python scripts/run_t177_edge_monitor.py --window 50

    # CI mode: exits non-zero if ANTI-PREDICTIVE at p<ALPHA
    python scripts/run_t177_edge_monitor.py --ci --alpha 0.10

Exit codes (--ci mode only):
    0  MONOTONIC or INCONCLUSIVE — no alarm
    2  ANTI-PREDICTIVE (p < alpha)
    3  Insufficient data (n < MIN_N)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import NamedTuple, Optional

# --- constants ---

MIN_N = 20          # minimum resolved bets for any verdict (below this: INCONCLUSIVE)
DEFAULT_ALPHA = 0.10  # Fisher's p-value threshold for ANTI-PREDICTIVE / MONOTONIC verdict
DEFAULT_SPORT = "mlb"  # GG-070: MLB is the ACTIVE pool; NBA is dark/frozen
# GG-070 dual-ledger split: each sport is a separate, isolated bankroll pool.
# These are the same VPS-synced cache paths CLAUDE.md's session-start governance
# hook reads (.claude/hooks/governance_scan.sh) — keep in sync with that script.
SPORT_PORTFOLIO = {
    "mlb": Path("logs/.vps_portfolio_cache_mlb.json"),
    "nba": Path("logs/.vps_portfolio_cache_nba.json"),
}
VERDICT_ANTI = "ANTI-PREDICTIVE"
VERDICT_MONO = "MONOTONIC"
VERDICT_INC  = "INCONCLUSIVE"

# --- scipy import ---

try:
    from scipy.stats import fisher_exact
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Position(NamedTuple):
    fee_net_edge: float
    win: int            # 1=WIN, 0=LOSS
    game_date: str
    direction: str
    pnl: float


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_portfolio(
    path: Path,
    exclude_duplicates: bool = True,
    exclude_fee_contaminated: bool = True,
) -> list[Position]:
    with open(path) as fh:
        data = json.load(fh)
    positions: list[Position] = []
    for p in data.get("closed_positions", []):
        if exclude_duplicates and p.get("duplicate_of"):
            continue
        if exclude_fee_contaminated and p.get("fee_contaminated"):
            continue
        outcome = p.get("outcome", "")
        if outcome not in ("WIN", "LOSS"):
            continue
        edge = p.get("fee_net_edge")
        if edge is None:
            continue
        try:
            edge = float(edge)
        except (TypeError, ValueError):
            continue
        positions.append(Position(
            fee_net_edge=edge,
            win=1 if outcome == "WIN" else 0,
            game_date=str(p.get("game_date", "")),
            direction=str(p.get("direction", "")),
            pnl=float(p.get("pnl", 0.0) or 0.0),
        ))
    return positions


def _load_csv(
    path: Path,
    exclude_duplicates: bool = True,
    exclude_fee_contaminated: bool = True,
) -> list[Position]:
    positions: list[Position] = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            if exclude_duplicates and row.get("duplicate_of", "").strip():
                continue
            contamination = row.get("contamination", "").strip()
            is_clean = row.get("is_clean", "True").strip().lower()
            if exclude_fee_contaminated and (contamination == "fee_contaminated" or is_clean == "false"):
                continue
            outcome = row.get("outcome", "").strip().upper()
            if outcome not in ("WIN", "LOSS"):
                continue
            try:
                edge = float(row["fee_net_edge"])
            except (KeyError, ValueError, TypeError):
                continue
            positions.append(Position(
                fee_net_edge=edge,
                win=1 if outcome == "WIN" else 0,
                game_date=str(row.get("game_date", "")),
                direction=str(row.get("direction", "")),
                pnl=float(row.get("realized_pnl", 0.0) or 0.0),
            ))
    return positions


# ---------------------------------------------------------------------------
# Statistical test
# ---------------------------------------------------------------------------

def _fisher_pvalue(
    pos_pos: list[Position],  # edge > 0
    neg_pos: list[Position],  # edge <= 0
) -> tuple[float, float]:
    """
    Fisher's exact test: edge>0 group vs edge<=0 group, WIN/LOSS counts.
    Returns (odds_ratio, two_tailed_p_value).
    """
    a = sum(p.win for p in pos_pos)         # edge>0, WIN
    b = len(pos_pos) - a                    # edge>0, LOSS
    c = sum(p.win for p in neg_pos)         # edge<=0, WIN
    d = len(neg_pos) - c                    # edge<=0, LOSS
    if not _HAS_SCIPY:
        # Manual approximation via hypergeometric — just chi-squared
        n = a + b + c + d
        if n == 0:
            return (1.0, 1.0)
        r1, r2 = a + b, c + d
        c1, c2 = a + c, b + d
        e_a = r1 * c1 / n
        e_b = r1 * c2 / n
        e_c = r2 * c1 / n
        e_d = r2 * c2 / n
        chi2 = sum(
            (o - e) ** 2 / e if e > 0 else 0.0
            for o, e in [(a, e_a), (b, e_b), (c, e_c), (d, e_d)]
        )
        # chi2 with df=1; approximate p using regularized incomplete gamma
        # Use simple bound: p < 0.10 iff chi2 > 2.71; p < 0.05 iff chi2 > 3.84
        # Return approximate p (good enough for threshold check)
        if chi2 > 10.83:
            approx_p = 0.001
        elif chi2 > 6.63:
            approx_p = 0.01
        elif chi2 > 3.84:
            approx_p = 0.05
        elif chi2 > 2.71:
            approx_p = 0.10
        else:
            approx_p = 0.20
        or_ = (a * d) / (b * c) if b > 0 and c > 0 else float("inf")
        return (or_, approx_p)
    table = [[a, b], [c, d]]
    or_, pval = fisher_exact(table, alternative="two-sided")
    return (float(or_), float(pval))


# ---------------------------------------------------------------------------
# Tercile table
# ---------------------------------------------------------------------------

def _tercile_table(positions: list[Position]) -> list[dict]:
    if not positions:
        return []
    sorted_pos = sorted(positions, key=lambda p: p.fee_net_edge)
    n = len(sorted_pos)
    chunks = [sorted_pos[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    if len(sorted_pos) % 3 != 0:
        chunks[2] = sorted_pos[2 * n // 3:]
    rows = []
    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        rows.append({
            "tercile": i + 1,
            "n": len(chunk),
            "edge_min": chunk[0].fee_net_edge,
            "edge_max": chunk[-1].fee_net_edge,
            "edge_mean": sum(p.fee_net_edge for p in chunk) / len(chunk),
            "winrate": sum(p.win for p in chunk) / len(chunk),
            "pnl": sum(p.pnl for p in chunk),
        })
    return rows


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyse(
    positions: list[Position],
    alpha: float = DEFAULT_ALPHA,
    window: Optional[int] = None,
    label: str = "",
) -> dict:
    if window is not None and window > 0:
        positions = positions[-window:]
    n = len(positions)
    if n < MIN_N:
        return {
            "label": label, "n": n, "verdict": VERDICT_INC,
            "reason": f"n={n} < MIN_N={MIN_N}",
        }
    n_win = sum(p.win for p in positions)
    mean_edge = sum(p.fee_net_edge for p in positions) / n
    n_pos_edge = sum(1 for p in positions if p.fee_net_edge > 0)

    pos_group = [p for p in positions if p.fee_net_edge > 0]
    neg_group = [p for p in positions if p.fee_net_edge <= 0]

    wr_pos = sum(p.win for p in pos_group) / len(pos_group) if pos_group else float("nan")
    wr_neg = sum(p.win for p in neg_group) / len(neg_group) if neg_group else float("nan")

    or_, pval = _fisher_pvalue(pos_group, neg_group) if (pos_group and neg_group) else (1.0, 1.0)

    terciles = _tercile_table(positions)

    if pval < alpha and wr_pos < wr_neg:
        verdict = VERDICT_ANTI
    elif pval < alpha and wr_pos > wr_neg:
        verdict = VERDICT_MONO
    else:
        verdict = VERDICT_INC

    return {
        "label": label,
        "n": n,
        "n_win": n_win,
        "overall_winrate": n_win / n,
        "mean_edge": mean_edge,
        "n_pos_edge": n_pos_edge,
        "pct_pos_edge": n_pos_edge / n,
        "winrate_edge_pos": wr_pos,
        "winrate_edge_neg": wr_neg,
        "fisher_odds_ratio": or_,
        "fisher_pvalue": pval,
        "alpha": alpha,
        "terciles": terciles,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_report(result: dict) -> None:
    label = result.get("label", "")
    header = f"=== T-177 Edge Monitor{' — ' + label if label else ''} ==="
    print(header)
    n = result["n"]
    if result["verdict"] == VERDICT_INC and "reason" in result:
        print(f"  INCONCLUSIVE — {result['reason']}")
        return
    print(f"  n={n}  wins={result['n_win']}  overall_winrate={result['overall_winrate']:.3f}")
    print(f"  mean_fee_net_edge={result['mean_edge']:+.4f}  "
          f"edge>0: {result['n_pos_edge']}/{n} ({result['pct_pos_edge']:.1%})")
    print()
    print(f"  edge>0  winrate={result['winrate_edge_pos']:.3f}  "
          f"(n={result['n_pos_edge']})")
    print(f"  edge<=0 winrate={result['winrate_edge_neg']:.3f}  "
          f"(n={result['n'] - result['n_pos_edge']})")
    print(f"  Fisher exact: OR={result['fisher_odds_ratio']:.3f}  "
          f"p={result['fisher_pvalue']:.4f}  (alpha={result['alpha']})")
    sci_note = "" if _HAS_SCIPY else " [approx — install scipy for exact test]"
    print(f"  {sci_note}")
    print()
    print(f"  -- Edge terciles (low→high fee_net_edge) --")
    for t in result["terciles"]:
        print(f"    T{t['tercile']}: edge[{t['edge_min']:+.4f},{t['edge_max']:+.4f}]  "
              f"n={t['n']:3d}  winrate={t['winrate']:.3f}  P&L={t['pnl']:+.2f}")
    print()
    verdict = result["verdict"]
    if verdict == VERDICT_ANTI:
        print(f"  *** {verdict} (p={result['fisher_pvalue']:.4f} < {result['alpha']}) ***")
        print("  Edge>0 bets win LESS often than edge<=0 bets.")
        print("  GG-037 alpha half confirmed on this dataset. T-177 is active.")
        print("  If this persists at ADR-0024 adequate sample (n>=150, >=15 opponents),")
        print("  escalate to DS for model architecture review (ADR-0004 trigger).")
    elif verdict == VERDICT_MONO:
        print(f"  {verdict} (p={result['fisher_pvalue']:.4f} < {result['alpha']})")
        print("  Edge>0 bets win MORE often than edge<=0 bets. Signal is working as intended.")
    else:
        print(f"  {verdict} (p={result['fisher_pvalue']:.4f} >= {result['alpha']})")
        print("  No statistically significant edge-winrate relationship detected.")
        if n < 100:
            print(f"  Sample ({n}) may be too small for reliable verdict — continue accumulating.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="T-177 edge inversion monitor (GG-037/GG-004 diagnostic)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--csv",
        metavar="PATH",
        help="Read from a resolved-bet CSV instead of the live portfolio.",
    )
    p.add_argument(
        "--sport",
        choices=sorted(SPORT_PORTFOLIO),
        default=DEFAULT_SPORT,
        help=f"Which sport's ledger to monitor (default: {DEFAULT_SPORT} — the "
             f"ACTIVE pool; GG-070 dual-ledger split). Ignored if --portfolio is given.",
    )
    p.add_argument(
        "--portfolio",
        metavar="PATH",
        default=None,
        help="Live portfolio JSON path. Overrides --sport if given "
             f"(default resolves from --sport: {SPORT_PORTFOLIO[DEFAULT_SPORT]}).",
    )
    p.add_argument(
        "--window",
        type=int,
        default=None,
        metavar="N",
        help="Analyse only the last N positions (chronological order).",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Fisher's p-value threshold for ANTI-PREDICTIVE verdict (default {DEFAULT_ALPHA}).",
    )
    p.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 2 if ANTI-PREDICTIVE, exit 3 if insufficient data.",
    )
    p.add_argument(
        "--include-duplicates",
        action="store_true",
        help="Include duplicate_of-annotated positions (excluded by default).",
    )
    p.add_argument(
        "--include-fee-contaminated",
        action="store_true",
        help="Include fee_contaminated positions (excluded by default).",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    exc_dup = not args.include_duplicates
    exc_fee = not args.include_fee_contaminated

    if args.csv:
        path = Path(args.csv)
        if not path.exists():
            print(f"ERROR: CSV not found: {path}", file=sys.stderr)
            return 1
        positions = _load_csv(path, exclude_duplicates=exc_dup,
                              exclude_fee_contaminated=exc_fee)
        label = f"CSV {path.name}"
    else:
        path = Path(args.portfolio) if args.portfolio else SPORT_PORTFOLIO[args.sport]
        if not path.exists():
            print(f"ERROR: portfolio not found: {path}", file=sys.stderr)
            if not args.portfolio:
                print(
                    f"  (no --portfolio given; resolved from --sport={args.sport}. "
                    "Cache is VPS-synced — run the session-start governance hook, "
                    "or `ssh prediction-market-vps 'cat "
                    f"/opt/prediction-market-bot/logs/paper_portfolio"
                    f"{'_mlb' if args.sport == 'mlb' else ''}.json' > {path}` to refresh it.)",
                    file=sys.stderr,
                )
            return 1
        positions = _load_portfolio(path, exclude_duplicates=exc_dup,
                                    exclude_fee_contaminated=exc_fee)
        sport_tag = "ACTIVE" if args.sport == "mlb" else "DARK/FROZEN — historical, not live risk"
        label = f"{args.sport.upper()} ({sport_tag}) — {path.name}"

    result = analyse(positions, alpha=args.alpha, window=args.window, label=label)
    _print_report(result)
    if not args.csv:
        print(
            "  NOTE (GG-099): this book is band-BLIND — PaperTrader does not persist a "
            "band field, so any resolved T1/T2/T3 MLB positions are mixed together "
            "undifferentiated, and T4M-PROJ (separate store, no resolved-outcome join "
            "yet) is NOT included. Do not read this verdict as scoped to one band "
            "until T-255 lands per-band splitting."
        )

    if args.ci:
        if result["verdict"] == VERDICT_ANTI:
            return 2
        if result.get("n", 0) < MIN_N:
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

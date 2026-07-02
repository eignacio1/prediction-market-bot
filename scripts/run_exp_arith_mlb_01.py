#!/usr/bin/env python3
"""
EXP-ARITH-MLB-01 — T4M-ARITH Near-Certainty Boundary Calibration (Backtest Runner)
ADR-0039 | GG-067 | T-219

Answers the question the experiment design doc (05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/
EXP-ARITH-MLB-01_t4m-arith-near-certainty-boundary-calibration.md) poses: does a dedicated
near-certainty Binomial band (batter is _ARITH_ENTRY_WINDOW hits away from their market
threshold, with p_arith clearing _ARITH_CONFIDENCE_GATE) produce calibrated probabilities
that beat market price, and are the current provisional constants (entry_window=1,
confidence_gate=0.80) the right choice?

Data source (GG-067, fixed SESSION 110):
  logs/t4_mlb_cycle_log.jsonl — raw per-cycle context written unconditionally by
  run_t4_mlb_live.py::_run_cycle() for every cycle reaching the p_t4/gross_edge
  computation, independent of dry_run/fired status. This file did not exist before
  SESSION 110; real games since deploy are the only rows that can appear in it.

T4MlbArithEvaluator (t4_mlb_execution_engine.py) reuses the exact same frozen
p_hits_gte_threshold/_compute_ab_remaining Binomial math as T4M-PROJ (ADR-0023,
ADR-0004) — so a cycle log record's `p_t4` field IS `p_arith` for that record's
h_so_far/threshold/ba_l10/ab_remaining. No separate probability recomputation is
needed here; only the entry-window and confidence-gate FILTERS are the object under
test, exactly as the design doc's Approach section states.

Grid: entry_window in {0, 1, 2}, confidence_gate in {0.70, 0.75, 0.80, 0.85, 0.90, 0.95}.
Outcomes are resolved against the real MLB Stats API (run_resolve_mlb.fetch_actual_hits),
so this script requires BOT_ENV=paper (same gate run_resolve_mlb.py itself enforces).

Run:
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_exp_arith_mlb_01.py
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_exp_arith_mlb_01.py --cycle-log logs/t4_mlb_cycle_log.jsonl
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_exp_arith_mlb_01.py --ci

Exit codes (--ci mode only, applied to the headline cell: entry_window=1, confidence_gate=0.80):
  0  Positive or INCONCLUSIVE — no alarm
  2  CONFIRMED_NEGATIVE (Tier 2) — halt + DS review
  3  DIAGNOSTIC_SPRINT (Tier 1, EV < -$0.03) — DS review required
  4  Insufficient data (n < MIN_N) — expected until enough post-deploy games accumulate
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, NamedTuple, Optional

os.environ.setdefault("BOT_ENV", "paper")

_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT / "src"))

# ── Constants ──────────────────────────────────────────────────────────────────

_ARITH_ENTRY_WINDOW_DEFAULT   = 1      # t4_mlb_execution_engine.py::_ARITH_ENTRY_WINDOW
_ARITH_CONFIDENCE_GATE_DEFAULT = 0.80  # t4_mlb_execution_engine.py::_ARITH_CONFIDENCE_GATE
_MIN_EDGE                      = 0.04  # t4_mlb_execution_engine.py::_MIN_EDGE

ENTRY_WINDOW_GRID     = (0, 1, 2)
CONFIDENCE_GATE_GRID  = (0.70, 0.75, 0.80, 0.85, 0.90, 0.95)

ADR_0024_TIER1_N          = 150
ADR_0024_TIER1_DIAG_EV    = -0.03
ADR_0024_TIER2_N_SINGLE   = 500
ADR_0024_P_THRESHOLD      = 0.05
MIN_N                      = 20     # minimum resolved bets for any verdict
DEFAULT_CYCLE_LOG          = Path("logs/t4_mlb_cycle_log.jsonl")
OUT_DIR                    = Path("exp_output/EXP-ARITH-MLB-01")

V_CONF_POS   = "CONFIRMED_POSITIVE"
V_DIR_POS    = "DIRECTIONAL_POSITIVE"
V_CONF_NEG   = "CONFIRMED_NEGATIVE"
V_DIR_NEG    = "DIRECTIONAL_NEGATIVE"
V_DIAG       = "DIAGNOSTIC_SPRINT"
V_INC        = "INCONCLUSIVE"

E_ANTI = "ANTI-PREDICTIVE"
E_MONO = "MONOTONIC"
E_INC  = "INCONCLUSIVE"

try:
    from scipy.stats import fisher_exact
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False


# ── Data model ─────────────────────────────────────────────────────────────────

class ArithCycle(NamedTuple):
    ticker:       str
    player_id:    int
    player_name:  str
    game_date:    str
    threshold:    int
    h_so_far:     int
    p_t4:         float   # == p_arith for this h_so_far/threshold/ba_l10/ab_remaining
    mip:          float
    vig:          float
    gross_edge:   float
    ts:           str


class ResolvedBet(NamedTuple):
    ticker:      str
    direction:   str    # "YES" or "NO"
    mip:         float
    vig:         float
    model_p:     float
    gross_edge:  float
    outcome:     str    # "WIN" or "LOSS"
    pnl:         float
    game_date:   str
    threshold:   int
    player_name: str


# ── Loading ────────────────────────────────────────────────────────────────────

def load_cycle_log(path: Path) -> list[ArithCycle]:
    """Parse the GG-067 raw per-cycle JSONL. Malformed lines are skipped."""
    cycles: list[ArithCycle] = []
    if not path.exists():
        return cycles
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                cycles.append(ArithCycle(
                    ticker=str(rec["ticker"]),
                    player_id=int(rec["player_id"]),
                    player_name=str(rec.get("player_name", "")),
                    game_date=str(rec["game_date"]),
                    threshold=int(rec["threshold"]),
                    h_so_far=int(rec["h_so_far"]),
                    p_t4=float(rec["p_t4"]),
                    mip=float(rec["mip"]),
                    vig=float(rec["vig"]),
                    gross_edge=float(rec["gross_edge"]),
                    ts=str(rec.get("ts", "")),
                ))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
    return cycles


# ── Qualification / dedup ──────────────────────────────────────────────────────

def h_needed(cycle: ArithCycle) -> int:
    return cycle.threshold - cycle.h_so_far


def qualifies(cycle: ArithCycle, entry_window: int, confidence_gate: float) -> bool:
    hn = h_needed(cycle)
    if not (0 < hn <= entry_window):
        return False
    if cycle.p_t4 < confidence_gate:
        return False
    if abs(cycle.gross_edge) < _MIN_EDGE:
        return False
    return True


def direction_of(cycle: ArithCycle) -> str:
    return "YES" if cycle.p_t4 > 0.5 else "NO"


def dedupe_earliest(cycles: list[ArithCycle]) -> list[ArithCycle]:
    """One cycle per unique ticker — earliest ts wins (mirrors EXP-017 dedup)."""
    ordered = sorted(cycles, key=lambda c: c.ts)
    seen: set[str] = set()
    unique: list[ArithCycle] = []
    for c in ordered:
        if c.ticker not in seen:
            seen.add(c.ticker)
            unique.append(c)
    return unique


# ── Resolution (real MLB Stats API, cached) ─────────────────────────────────────

def build_resolution_cache(
    cycles: list[ArithCycle],
    resolver: Callable[[int, str], Optional[float]],
) -> dict[tuple[int, str], Optional[float]]:
    """Resolve actual hits for every unique (player_id, game_date) pair once."""
    pairs = {(c.player_id, c.game_date) for c in cycles}
    cache: dict[tuple[int, str], Optional[float]] = {}
    for player_id, game_date in pairs:
        cache[(player_id, game_date)] = resolver(player_id, game_date)
    return cache


def kalshi_fee(mip: float) -> float:
    return 0.07 * mip * (1.0 - mip)


def compute_pnl_unit(direction: str, mip: float, vig: float, won: bool) -> float:
    """Realized P&L per unit bet (consistent with EXP-017/EXP-018 methodology)."""
    half_vig = vig / 2.0
    if direction == "YES":
        price_paid = mip + half_vig
        return (1.0 - price_paid) if won else -price_paid
    else:
        price_paid = (1.0 - mip) + half_vig
        return (1.0 - price_paid) if won else -price_paid


def resolve_bets(
    cycles: list[ArithCycle],
    hits_cache: dict[tuple[int, str], Optional[float]],
) -> list[ResolvedBet]:
    """Join qualifying, deduped cycles to real outcomes. Unresolved (None) rows dropped."""
    resolved: list[ResolvedBet] = []
    for c in cycles:
        actual_hits = hits_cache.get((c.player_id, c.game_date))
        if actual_hits is None:
            continue
        direction = direction_of(c)
        if direction == "YES":
            won = actual_hits >= c.threshold
        else:
            won = actual_hits < c.threshold
        outcome = "WIN" if won else "LOSS"
        pnl = compute_pnl_unit(direction, c.mip, c.vig, won)
        resolved.append(ResolvedBet(
            ticker=c.ticker,
            direction=direction,
            mip=c.mip,
            vig=c.vig,
            model_p=c.p_t4,
            gross_edge=c.gross_edge,
            outcome=outcome,
            pnl=pnl,
            game_date=c.game_date,
            threshold=c.threshold,
            player_name=c.player_name,
        ))
    return resolved


# ── EV / tier / monotonicity (self-contained, mirrors run_exp017_mlb.py) ────────

def ev_stats(bets: list[ResolvedBet]) -> dict:
    if not bets:
        return {"n": 0, "ev_per_bet": 0.0, "win_rate": 0.0, "total_pnl": 0.0}
    n = len(bets)
    wins = sum(1 for b in bets if b.outcome == "WIN")
    total_pnl = sum(b.pnl for b in bets)
    return {"n": n, "ev_per_bet": total_pnl / n, "win_rate": wins / n, "total_pnl": total_pnl}


def adr0024_tier(n: int, ev_per_bet: float) -> dict:
    at_tier1 = n >= ADR_0024_TIER1_N
    at_tier2 = n >= ADR_0024_TIER2_N_SINGLE
    diagnostic_sprint = at_tier1 and (ev_per_bet < ADR_0024_TIER1_DIAG_EV)
    return {"at_tier1": at_tier1, "at_tier2": at_tier2, "diagnostic_sprint": diagnostic_sprint}


def ev_verdict(n: int, ev_per_bet: float, tier: dict, fisher_pvalue: float) -> str:
    if n < MIN_N:
        return V_INC
    if tier["diagnostic_sprint"]:
        return V_DIAG
    if tier["at_tier2"]:
        if ev_per_bet > 0 and fisher_pvalue < ADR_0024_P_THRESHOLD:
            return V_CONF_POS
        if ev_per_bet < ADR_0024_TIER1_DIAG_EV:
            return V_CONF_NEG
        if ev_per_bet > 0:
            return V_DIR_POS
        return V_INC
    if ev_per_bet > 0:
        return V_DIR_POS
    if ev_per_bet < 0:
        return V_DIR_NEG
    return V_INC


def _fisher_pvalue(pos_group: list[ResolvedBet], neg_group: list[ResolvedBet]) -> tuple[float, float]:
    a = sum(1 for b in pos_group if b.outcome == "WIN")
    b_ = len(pos_group) - a
    c = sum(1 for b in neg_group if b.outcome == "WIN")
    d = len(neg_group) - c
    if _HAS_SCIPY:
        or_, pval = fisher_exact([[a, b_], [c, d]], alternative="two-sided")
        return (float(or_), float(pval))
    n = a + b_ + c + d
    if n == 0:
        return (1.0, 1.0)
    r1, r2 = a + b_, c + d
    c1, c2 = a + c, b_ + d
    e_a = r1 * c1 / n
    e_b = r1 * c2 / n
    e_c = r2 * c1 / n
    e_d = r2 * c2 / n
    chi2 = sum((o - e) ** 2 / e if e > 0 else 0.0
               for o, e in [(a, e_a), (b_, e_b), (c, e_c), (d, e_d)])
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
    or_ = (a * d) / (b_ * c) if (b_ > 0 and c > 0) else float("inf")
    return (or_, approx_p)


def edge_monotonicity(bets: list[ResolvedBet], alpha: float = 0.10) -> dict:
    """T-177 / GG-037 guard: does gross_edge predict outcomes for this cell?"""
    n = len(bets)
    if n < MIN_N:
        return {"verdict": E_INC, "reason": f"n={n} < MIN_N={MIN_N}"}
    pos_group = [b for b in bets if b.gross_edge > 0]
    neg_group = [b for b in bets if b.gross_edge <= 0]
    wr_pos = sum(1 for b in pos_group if b.outcome == "WIN") / len(pos_group) if pos_group else float("nan")
    wr_neg = sum(1 for b in neg_group if b.outcome == "WIN") / len(neg_group) if neg_group else float("nan")
    if pos_group and neg_group:
        or_, pval = _fisher_pvalue(pos_group, neg_group)
    else:
        or_, pval = 1.0, 1.0
    if pval < alpha and wr_pos > wr_neg:
        verdict = E_MONO
    elif pval < alpha and wr_pos < wr_neg:
        verdict = E_ANTI
    else:
        verdict = E_INC
    return {
        "verdict": verdict, "n": n,
        "n_pos_edge": len(pos_group), "n_neg_edge": len(neg_group),
        "winrate_edge_pos": wr_pos, "winrate_edge_neg": wr_neg,
        "fisher_odds_ratio": or_, "fisher_pvalue": pval, "alpha": alpha,
    }


# ── Grid sweep ─────────────────────────────────────────────────────────────────

def evaluate_cell(
    all_cycles: list[ArithCycle],
    entry_window: int,
    confidence_gate: float,
    hits_cache: dict[tuple[int, str], Optional[float]],
    alpha: float = 0.10,
) -> dict:
    qualifying = [c for c in all_cycles if qualifies(c, entry_window, confidence_gate)]
    deduped = dedupe_earliest(qualifying)
    bets = resolve_bets(deduped, hits_cache)
    stats = ev_stats(bets)
    mono = edge_monotonicity(bets, alpha=alpha)
    tier = adr0024_tier(stats["n"], stats["ev_per_bet"])
    verdict = ev_verdict(stats["n"], stats["ev_per_bet"], tier, mono.get("fisher_pvalue", 1.0))
    return {
        "entry_window": entry_window,
        "confidence_gate": confidence_gate,
        "n_qualifying_cycles": len(qualifying),
        "n_unique_tickers": len(deduped),
        "n_resolved": stats["n"],
        "ev_per_bet": stats["ev_per_bet"],
        "win_rate": stats["win_rate"],
        "total_pnl": stats["total_pnl"],
        "tier": tier,
        "verdict": verdict,
        "edge_monotonicity": mono,
    }


def run_grid_sweep(
    all_cycles: list[ArithCycle],
    hits_cache: dict[tuple[int, str], Optional[float]],
    entry_windows: tuple[int, ...] = ENTRY_WINDOW_GRID,
    confidence_gates: tuple[float, ...] = CONFIDENCE_GATE_GRID,
    alpha: float = 0.10,
) -> list[dict]:
    return [
        evaluate_cell(all_cycles, ew, cg, hits_cache, alpha=alpha)
        for ew in entry_windows
        for cg in confidence_gates
    ]


# ── Reporting ──────────────────────────────────────────────────────────────────

def _print_report(grid: list[dict], headline: dict, n_raw_cycles: int) -> None:
    sep = "=" * 72
    print(sep)
    print("EXP-ARITH-MLB-01 — T4M-ARITH Near-Certainty Boundary Calibration")
    print("ADR-0039 | GG-067 | T-219")
    print(sep)
    print(f"  Raw cycle-log rows: {n_raw_cycles}")
    print()
    print("── Headline cell (current live constants: entry_window=1, "
          "confidence_gate=0.80) ──")
    print(f"  Qualifying cycles: {headline['n_qualifying_cycles']}   "
          f"Unique tickers: {headline['n_unique_tickers']}   "
          f"Resolved: {headline['n_resolved']}")
    print(f"  EV/bet: ${headline['ev_per_bet']:+.4f}   win_rate: {headline['win_rate']:.3f}   "
          f"total_pnl: ${headline['total_pnl']:+.2f}")
    print(f"  Verdict: {headline['verdict']}")
    mono = headline["edge_monotonicity"]
    if "reason" in mono:
        print(f"  Edge monotonicity: {mono['verdict']} — {mono['reason']}")
    else:
        print(f"  Edge monotonicity: {mono['verdict']}  "
              f"(edge>0 wr={mono['winrate_edge_pos']:.3f} n={mono['n_pos_edge']}, "
              f"edge<=0 wr={mono['winrate_edge_neg']:.3f} n={mono['n_neg_edge']}, "
              f"p={mono['fisher_pvalue']:.4f})")
    print()
    print("── Full grid (entry_window x confidence_gate) ──────────────────────")
    print(f"  {'ew':>3} {'gate':>5} {'qual':>6} {'uniq':>6} {'res':>5} "
          f"{'ev/bet':>9} {'winrate':>8} {'verdict':>22}")
    for cell in sorted(grid, key=lambda c: (-c["n_resolved"], -c["ev_per_bet"])):
        print(f"  {cell['entry_window']:>3} {cell['confidence_gate']:>5.2f} "
              f"{cell['n_qualifying_cycles']:>6} {cell['n_unique_tickers']:>6} "
              f"{cell['n_resolved']:>5} {cell['ev_per_bet']:>+9.4f} "
              f"{cell['win_rate']:>8.3f} {cell['verdict']:>22}")
    print()
    print("── Verdict ───────────────────────────────────────────────────────")
    if headline["n_resolved"] < MIN_N:
        print(f"  Insufficient data ({headline['n_resolved']} resolved bets, "
              f"need >= {MIN_N}). T4M-ARITH remains status=BLOCKED.")
        print("  This is expected until enough post-deploy games accumulate "
              "in the GG-067 cycle log.")
    else:
        print(f"  {headline['verdict']}")
    print(sep)


# ── CLI ────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="EXP-ARITH-MLB-01 — T4M-ARITH backtest runner (ADR-0039 / GG-067 / T-219)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--cycle-log", metavar="PATH", default=str(DEFAULT_CYCLE_LOG),
        help=f"GG-067 raw per-cycle JSONL (default: {DEFAULT_CYCLE_LOG})",
    )
    p.add_argument("--alpha", type=float, default=0.10,
                    help="Fisher p-value threshold for edge monotonicity verdict (default 0.10)")
    p.add_argument("--ci", action="store_true",
                    help="CI mode: exit 2 CONFIRMED_NEGATIVE, exit 3 DIAGNOSTIC_SPRINT, exit 4 insufficient")
    p.add_argument("--no-save", action="store_true",
                    help="Do not save results JSON to exp_output/")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    cycle_log_path = Path(args.cycle_log)

    all_cycles = load_cycle_log(cycle_log_path)
    n_raw = len(all_cycles)

    if not all_cycles:
        print(f"No cycle-log data found at {cycle_log_path}.", file=sys.stderr)
        print("T4M-ARITH remains status=BLOCKED — this is expected until enough "
              "post-deploy MLB games accumulate cycle-log rows (GG-067, SESSION 110).",
              file=sys.stderr)
        if not args.no_save:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_path = OUT_DIR / "EXP-ARITH-MLB-01_results.json"
            with open(out_path, "w") as fh:
                json.dump({"n_raw_cycles": 0, "verdict": V_INC,
                           "reason": "no cycle-log data yet"}, fh, indent=2)
            print(f"Results saved: {out_path}")
        return 4 if args.ci else 0

    from prediction_market_bot.run_resolve_mlb import fetch_actual_hits

    hits_cache = build_resolution_cache(all_cycles, fetch_actual_hits)

    grid = run_grid_sweep(all_cycles, hits_cache, alpha=args.alpha)
    headline = evaluate_cell(
        all_cycles, _ARITH_ENTRY_WINDOW_DEFAULT, _ARITH_CONFIDENCE_GATE_DEFAULT,
        hits_cache, alpha=args.alpha,
    )

    _print_report(grid, headline, n_raw)

    if not args.no_save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / "EXP-ARITH-MLB-01_results.json"
        with open(out_path, "w") as fh:
            json.dump({"n_raw_cycles": n_raw, "headline": headline, "grid": grid}, fh, indent=2)
        print(f"Results saved: {out_path}")

    if args.ci:
        verdict = headline["verdict"]
        if verdict == V_CONF_NEG:
            return 2
        if verdict == V_DIAG:
            return 3
        if headline["n_resolved"] < MIN_N:
            return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

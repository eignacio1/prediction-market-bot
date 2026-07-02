#!/usr/bin/env python3
"""
EXP-FLOW-MLB-01 — T4M-FLOW/FLOW-BLOWOUT Multiplier Calibration (Backtest Runner)
ADR-0039 | GG-067 | F-FLOW-01

Answers the question the experiment design doc (05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/
EXP-FLOW-MLB-01_t4m-flow-blowout-multiplier-calibration.md) poses: does a sustained
run-differential blowout (|score_diff| >= _BLOWOUT_RUN_THRESHOLD for >= _BLOWOUT_SUSTAIN_INNINGS
innings) systematically shift a batter's true hit probability by an amount the market fails to
price in, and are the current provisional constants (run_threshold=6, sustain_innings=2,
trailing_mult=1.15, leading_mult=0.80) the right choice?

Governance note — read before running this script for real:
T4M-FLOW is registered status="BLOCKED" in T4_MLB_SUBBAND_REGISTRY, gated on this exact
experiment ID. Building and running this backtest runner does NOT authorize live/paper firing
of T4M-FLOW — that requires this experiment's own Phase 8 Activation Gate + APR, per the design
doc's explicit governance note. This script produces the data this session's Follow-Up queue
calls for; it does not itself constitute experiment sign-off.

Two inputs this runner joins that EXP-ARITH-MLB-01's runner did not need:
  1. logs/t4_mlb_cycle_log.jsonl (GG-067) — same raw per-cycle source, now also reading
     ba_l10/ab_so_far/inning/batting_slot (T4M-PROJ inputs already captured per row).
  2. scripts/reconstruct_mlb_score_diff.py (F-FLOW-01) — retrospective score_diff/
     is_batting_team_leading per (game_date, teams, inning, half), reconstructed from resolved
     ESPN boxscores. Joined to each cycle via its ticker (encodes away/home team codes) + inning.

p_flow is NOT the cycle log's logged p_t4 (unlike ARITH, where p_t4 IS p_arith by construction)
— T4M-FLOW recomputes the Binomial update with an adjusted ba_l10 (ba_l10 * trailing/leading
multiplier), so this runner recomputes p_flow itself via the same frozen
p_hits_gte_threshold/_compute_ab_remaining primitives T4MlbFlowEvaluator uses, rather than
trusting a logged field.

Blowout state (has |score_diff| been >= run_threshold for >= sustain_innings, per game) is a
stateful scan over time-ordered cycles per synthetic game key (away_abbr, home_abbr, game_date)
— ticker alone does not carry an ESPN/MLB game_id, so the ticker's own embedded team codes plus
game_date serve as the join key, mirroring T4MlbFlowEvaluator's per-game_id dict exactly.

Grid (per design doc's Approach step 2): run_threshold in {4,5,6,7,8} runs, sustain_innings in
{1,2,3} innings, holding the trailing/leading multipliers at their current provisional values
(1.15 / 0.80) — multiplier-value refitting from observed hit-rate ratios is a further step not
implemented in this v1 runner. Design doc's step 1 (effect existence/direction, independent of
market price) is reported separately as a diagnostic: trailing vs. leading empirical win_rate
and mean ba_l10 for the headline cell's resolved bets, before the tier/monotonicity verdict.

Run:
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_exp_flow_mlb_01.py
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_exp_flow_mlb_01.py --cycle-log logs/t4_mlb_cycle_log.jsonl
  BOT_ENV=paper PYTHONPATH=src python3 scripts/run_exp_flow_mlb_01.py --ci

Exit codes (--ci mode only, applied to the headline cell: run_threshold=6, sustain_innings=2):
  0  Positive or INCONCLUSIVE — no alarm
  2  CONFIRMED_NEGATIVE (Tier 2) — halt + DS review
  3  DIAGNOSTIC_SPRINT (Tier 1, EV < -$0.03) — DS review required
  4  Insufficient data (n < MIN_N) — expected until enough sustained-blowout innings accumulate
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import NamedTuple, Optional

os.environ.setdefault("BOT_ENV", "paper")

_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT / "src"))
if str(_SRC_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT / "scripts"))

from reconstruct_mlb_score_diff import load_score_diff_lookup, parse_mlb_ticker, score_diff_for_cycle
from run_exp_arith_mlb_01 import (  # generic EV/tier/monotonicity/resolution machinery — not ARITH-specific
    ADR_0024_P_THRESHOLD,
    ADR_0024_TIER1_DIAG_EV,
    ADR_0024_TIER1_N,
    ADR_0024_TIER2_N_SINGLE,
    MIN_N,
    ResolvedBet,
    V_CONF_NEG,
    V_DIAG,
    V_INC,
    adr0024_tier,
    build_resolution_cache,
    compute_pnl_unit,
    edge_monotonicity,
    ev_stats,
    ev_verdict,
)

# ── Constants (mirror t4_mlb_execution_engine.py exactly) ─────────────────────

_BLOWOUT_RUN_THRESHOLD_DEFAULT: int = 6
_BLOWOUT_SUSTAIN_INNINGS_DEFAULT: int = 2
_BLOWOUT_TRAILING_MULT: float = 1.15
_BLOWOUT_LEADING_MULT: float = 0.80
_MIN_EDGE: float = 0.04  # t4_mlb_execution_engine.py::_MIN_EDGE

RUN_THRESHOLD_GRID = (4, 5, 6, 7, 8)
SUSTAIN_INNINGS_GRID = (1, 2, 3)

DEFAULT_CYCLE_LOG = Path("logs/t4_mlb_cycle_log.jsonl")
OUT_DIR = Path("exp_output/EXP-FLOW-MLB-01")


# ── Data model ─────────────────────────────────────────────────────────────────

class FlowCycle(NamedTuple):
    ticker: str
    player_id: int
    player_name: str
    game_date: str
    threshold: int
    h_so_far: int
    ab_so_far: int
    inning: int
    batting_slot: int
    ba_l10: float
    mip: float
    vig: float
    ts: str


# ── Loading ────────────────────────────────────────────────────────────────────

def load_cycle_log(path: Path) -> list[FlowCycle]:
    """Parse the GG-067 raw per-cycle JSONL. Malformed lines are skipped."""
    cycles: list[FlowCycle] = []
    if not path.exists():
        return cycles
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                cycles.append(FlowCycle(
                    ticker=str(rec["ticker"]),
                    player_id=int(rec["player_id"]),
                    player_name=str(rec.get("player_name", "")),
                    game_date=str(rec["game_date"]),
                    threshold=int(rec["threshold"]),
                    h_so_far=int(rec["h_so_far"]),
                    ab_so_far=int(rec["ab_so_far"]),
                    inning=int(rec["inning"]),
                    batting_slot=int(rec["batting_slot"]),
                    ba_l10=float(rec["ba_l10"]),
                    mip=float(rec["mip"]),
                    vig=float(rec["vig"]),
                    ts=str(rec.get("ts", "")),
                ))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
    return cycles


def build_score_diff_lookups(
    cycles: list[FlowCycle],
) -> dict[str, dict[tuple[str, str, int, str], dict]]:
    """One score_diff lookup per unique game_date present in the cycle log.

    Reconstruction is retrospective (resolved ESPN boxscores) — game_dates for
    games still in progress will simply yield an empty lookup (no FINAL games
    to reconstruct yet) and those cycles are dropped by join_score_diff below.
    """
    lookups: dict[str, dict[tuple[str, str, int, str], dict]] = {}
    for game_date in {c.game_date for c in cycles}:
        lookups[game_date] = load_score_diff_lookup(game_date)
    return lookups


def join_score_diff(
    cycle: FlowCycle,
    lookups: dict[str, dict[tuple[str, str, int, str], dict]],
) -> Optional[tuple[float, bool]]:
    """Return (score_diff, is_batting_team_leading) for one cycle, or None if
    unresolvable (game not yet FINAL, ticker unparseable, or inning beyond
    the reconstructed table)."""
    lookup = lookups.get(cycle.game_date)
    if not lookup:
        return None
    row = score_diff_for_cycle(cycle.ticker, cycle.inning, lookup)
    if row is None:
        return None
    return float(row["score_diff"]), bool(row["is_batting_team_leading"])


# ── Blowout state machine + p_flow recomputation ────────────────────────────────

class FlowBet(NamedTuple):
    ticker: str
    player_id: int
    player_name: str
    game_date: str
    threshold: int
    h_so_far: int
    ba_l10: float
    ba_adjusted: float
    mip: float
    vig: float
    p_flow: float
    gross_edge: float
    player_trailing: bool
    ts: str


def compute_flow_bets(
    cycles: list[FlowCycle],
    lookups: dict[str, dict[tuple[str, str, int, str], dict]],
    run_threshold: int,
    sustain_innings: int,
    trailing_mult: float = _BLOWOUT_TRAILING_MULT,
    leading_mult: float = _BLOWOUT_LEADING_MULT,
) -> list[FlowBet]:
    """Stateful scan mirroring T4MlbFlowEvaluator.evaluate() exactly, applied
    offline across a synthetic per-game_id grouping (away_abbr, home_abbr,
    game_date), since cycle-log rows carry no ESPN/MLB game_id directly."""
    from prediction_market_bot.run_t4_mlb_live import _compute_ab_remaining, p_hits_gte_threshold

    # Group by synthetic game_id, then process each game's cycles chronologically.
    games: dict[tuple[str, str, str], list[FlowCycle]] = {}
    for c in cycles:
        parsed = parse_mlb_ticker(c.ticker)
        if parsed is None:
            continue
        away_abbr, home_abbr, _player_team = parsed
        games.setdefault((away_abbr, home_abbr, c.game_date), []).append(c)

    bets: list[FlowBet] = []
    for _game_key, game_cycles in games.items():
        game_cycles.sort(key=lambda c: c.ts)
        blowout_start_inning: Optional[int] = None
        for c in game_cycles:
            joined = join_score_diff(c, lookups)
            if joined is None:
                continue
            score_diff, is_batting_team_leading = joined

            in_blowout = abs(score_diff) >= run_threshold
            if in_blowout:
                if blowout_start_inning is None:
                    blowout_start_inning = c.inning
            else:
                blowout_start_inning = None

            if not in_blowout or blowout_start_inning is None:
                continue
            if (c.inning - blowout_start_inning) < sustain_innings:
                continue

            player_trailing = not is_batting_team_leading
            mult = trailing_mult if player_trailing else leading_mult
            ba_adjusted = min(1.0, c.ba_l10 * mult)

            ab_remaining = _compute_ab_remaining(c.ab_so_far, c.inning, c.batting_slot)
            if ab_remaining <= 0:
                continue

            p_flow = p_hits_gte_threshold(c.h_so_far, c.threshold, ba_adjusted, ab_remaining)
            edge = p_flow - c.mip - c.vig
            if abs(edge) < _MIN_EDGE:
                continue

            bets.append(FlowBet(
                ticker=c.ticker,
                player_id=c.player_id,
                player_name=c.player_name,
                game_date=c.game_date,
                threshold=c.threshold,
                h_so_far=c.h_so_far,
                ba_l10=c.ba_l10,
                ba_adjusted=ba_adjusted,
                mip=c.mip,
                vig=c.vig,
                p_flow=p_flow,
                gross_edge=edge,
                player_trailing=player_trailing,
                ts=c.ts,
            ))
    return bets


def dedupe_earliest_flow(bets: list[FlowBet]) -> list[FlowBet]:
    """One bet per unique ticker — earliest ts wins (mirrors EXP-017/ARITH dedup)."""
    ordered = sorted(bets, key=lambda b: b.ts)
    seen: set[str] = set()
    unique: list[FlowBet] = []
    for b in ordered:
        if b.ticker not in seen:
            seen.add(b.ticker)
            unique.append(b)
    return unique


def resolve_flow_bets(
    bets: list[FlowBet],
    hits_cache: dict[tuple[int, str], Optional[float]],
) -> list[ResolvedBet]:
    """Join deduped flow bets to real outcomes. Unresolved (None) rows dropped."""
    resolved: list[ResolvedBet] = []
    for b in bets:
        actual_hits = hits_cache.get((b.player_id, b.game_date))
        if actual_hits is None:
            continue
        direction = "YES" if b.p_flow > 0.5 else "NO"
        won = actual_hits >= b.threshold if direction == "YES" else actual_hits < b.threshold
        outcome = "WIN" if won else "LOSS"
        pnl = compute_pnl_unit(direction, b.mip, b.vig, won)
        resolved.append(ResolvedBet(
            ticker=b.ticker,
            direction=direction,
            mip=b.mip,
            vig=b.vig,
            model_p=b.p_flow,
            gross_edge=b.gross_edge,
            outcome=outcome,
            pnl=pnl,
            game_date=b.game_date,
            threshold=b.threshold,
            player_name=b.player_name,
        ))
    return resolved


# ── Grid sweep ─────────────────────────────────────────────────────────────────

def evaluate_cell(
    all_cycles: list[FlowCycle],
    lookups: dict[str, dict[tuple[str, str, int, str], dict]],
    run_threshold: int,
    sustain_innings: int,
    hits_cache: dict[tuple[int, str], Optional[float]],
    alpha: float = 0.10,
) -> dict:
    flow_bets = compute_flow_bets(all_cycles, lookups, run_threshold, sustain_innings)
    deduped = dedupe_earliest_flow(flow_bets)
    bets = resolve_flow_bets(deduped, hits_cache)
    stats = ev_stats(bets)
    mono = edge_monotonicity(bets, alpha=alpha)
    tier = adr0024_tier(stats["n"], stats["ev_per_bet"])
    verdict = ev_verdict(stats["n"], stats["ev_per_bet"], tier, mono.get("fisher_pvalue", 1.0))

    trailing = [b for b in deduped if b.player_trailing]
    leading = [b for b in deduped if not b.player_trailing]

    return {
        "run_threshold": run_threshold,
        "sustain_innings": sustain_innings,
        "n_qualifying_cycles": len(flow_bets),
        "n_unique_tickers": len(deduped),
        "n_trailing": len(trailing),
        "n_leading": len(leading),
        "n_resolved": stats["n"],
        "ev_per_bet": stats["ev_per_bet"],
        "win_rate": stats["win_rate"],
        "total_pnl": stats["total_pnl"],
        "tier": tier,
        "verdict": verdict,
        "edge_monotonicity": mono,
    }


def effect_existence_diagnostic(
    all_cycles: list[FlowCycle],
    lookups: dict[str, dict[tuple[str, str, int, str], dict]],
    run_threshold: int,
    sustain_innings: int,
    hits_cache: dict[tuple[int, str], Optional[float]],
) -> dict:
    """Design doc's step 1: does a real, directionally-consistent shift exist
    at all for trailing vs. leading batters during a sustained blowout,
    before any multiplier value is trusted? Uses the same per-game resolved
    hit total as the P&L path (no per-plate-appearance outcome is available
    from the cycle log), split by trailing/leading, comparing mean ba_l10
    (the pre-adjustment baseline) against the empirical win_rate actually
    realized once the game resolved.
    """
    flow_bets = compute_flow_bets(all_cycles, lookups, run_threshold, sustain_innings)
    deduped = dedupe_earliest_flow(flow_bets)
    resolved = resolve_flow_bets(deduped, hits_cache)
    by_ticker = {b.ticker: b for b in deduped}

    def _group_stats(trailing: bool) -> dict:
        group = [r for r in resolved if by_ticker[r.ticker].player_trailing == trailing]
        if not group:
            return {"n": 0, "mean_ba_l10": float("nan"), "win_rate": float("nan")}
        n = len(group)
        mean_ba = sum(by_ticker[r.ticker].ba_l10 for r in group) / n
        wins = sum(1 for r in group if r.outcome == "WIN")
        return {"n": n, "mean_ba_l10": mean_ba, "win_rate": wins / n}

    return {"trailing": _group_stats(True), "leading": _group_stats(False)}


def run_grid_sweep(
    all_cycles: list[FlowCycle],
    lookups: dict[str, dict[tuple[str, str, int, str], dict]],
    hits_cache: dict[tuple[int, str], Optional[float]],
    run_thresholds: tuple[int, ...] = RUN_THRESHOLD_GRID,
    sustain_innings_grid: tuple[int, ...] = SUSTAIN_INNINGS_GRID,
    alpha: float = 0.10,
) -> list[dict]:
    return [
        evaluate_cell(all_cycles, lookups, rt, si, hits_cache, alpha=alpha)
        for rt in run_thresholds
        for si in sustain_innings_grid
    ]


# ── Reporting ──────────────────────────────────────────────────────────────────

def _print_report(
    grid: list[dict], headline: dict, effect: dict, n_raw_cycles: int
) -> None:
    sep = "=" * 72
    print(sep)
    print("EXP-FLOW-MLB-01 — T4M-FLOW/FLOW-BLOWOUT Multiplier Calibration")
    print("ADR-0039 | GG-067 | F-FLOW-01")
    print(sep)
    print(f"  Raw cycle-log rows: {n_raw_cycles}")
    print()
    print("── Step 1: effect existence/direction (headline cell: "
          "run_threshold=6, sustain_innings=2) ──")
    for label, key in (("Trailing batters", "trailing"), ("Leading batters", "leading")):
        g = effect[key]
        if g["n"] == 0:
            print(f"  {label}: n=0 (no resolved bets in this group yet)")
        else:
            print(f"  {label}: n={g['n']}  mean_ba_l10={g['mean_ba_l10']:.3f}  "
                  f"realized_win_rate={g['win_rate']:.3f}")
    print("  (Trailing predicted to outperform its own ba_l10 baseline; leading "
          "predicted to underperform. This is a directional sanity check, not "
          "a substitute for the tier/monotonicity verdict below.)")
    print()
    print("── Headline cell (current live constants: run_threshold=6, "
          "sustain_innings=2) ──")
    print(f"  Qualifying cycles: {headline['n_qualifying_cycles']}   "
          f"Unique tickers: {headline['n_unique_tickers']}   "
          f"Resolved: {headline['n_resolved']}   "
          f"(trailing={headline['n_trailing']}, leading={headline['n_leading']})")
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
    print("── Full grid (run_threshold x sustain_innings, multipliers fixed at "
          "1.15/0.80) ──")
    print(f"  {'rt':>3} {'si':>3} {'qual':>6} {'uniq':>6} {'res':>5} "
          f"{'ev/bet':>9} {'winrate':>8} {'verdict':>22}")
    for cell in sorted(grid, key=lambda c: (-c["n_resolved"], -c["ev_per_bet"])):
        print(f"  {cell['run_threshold']:>3} {cell['sustain_innings']:>3} "
              f"{cell['n_qualifying_cycles']:>6} {cell['n_unique_tickers']:>6} "
              f"{cell['n_resolved']:>5} {cell['ev_per_bet']:>+9.4f} "
              f"{cell['win_rate']:>8.3f} {cell['verdict']:>22}")
    print()
    print("── Verdict ───────────────────────────────────────────────────────")
    if headline["n_resolved"] < MIN_N:
        print(f"  Insufficient data ({headline['n_resolved']} resolved bets, "
              f"need >= {MIN_N}). T4M-FLOW remains status=BLOCKED.")
        print("  This is expected until enough sustained-blowout innings "
              "accumulate across resolved MLB games in the GG-067 cycle log.")
    else:
        print(f"  {headline['verdict']}")
    print(sep)


# ── CLI ────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="EXP-FLOW-MLB-01 — T4M-FLOW backtest runner (ADR-0039 / GG-067 / F-FLOW-01)",
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
        print("T4M-FLOW remains status=BLOCKED — this is expected until enough "
              "post-deploy MLB games accumulate cycle-log rows (GG-067, SESSION 110).",
              file=sys.stderr)
        if not args.no_save:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_path = OUT_DIR / "EXP-FLOW-MLB-01_results.json"
            with open(out_path, "w") as fh:
                json.dump({"n_raw_cycles": 0, "verdict": V_INC,
                           "reason": "no cycle-log data yet"}, fh, indent=2)
            print(f"Results saved: {out_path}")
        return 4 if args.ci else 0

    lookups = build_score_diff_lookups(all_cycles)

    from prediction_market_bot.run_resolve_mlb import fetch_actual_hits

    hits_cache = build_resolution_cache(all_cycles, fetch_actual_hits)

    grid = run_grid_sweep(all_cycles, lookups, hits_cache, alpha=args.alpha)
    headline = evaluate_cell(
        all_cycles, lookups, _BLOWOUT_RUN_THRESHOLD_DEFAULT, _BLOWOUT_SUSTAIN_INNINGS_DEFAULT,
        hits_cache, alpha=args.alpha,
    )
    effect = effect_existence_diagnostic(
        all_cycles, lookups, _BLOWOUT_RUN_THRESHOLD_DEFAULT, _BLOWOUT_SUSTAIN_INNINGS_DEFAULT,
        hits_cache,
    )

    _print_report(grid, headline, effect, n_raw)

    if not args.no_save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / "EXP-FLOW-MLB-01_results.json"
        with open(out_path, "w") as fh:
            json.dump(
                {"n_raw_cycles": n_raw, "headline": headline, "effect_existence": effect, "grid": grid},
                fh, indent=2,
            )
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

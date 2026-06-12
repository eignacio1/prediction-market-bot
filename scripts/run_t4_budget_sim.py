#!/usr/bin/env python3
"""
T4 Band Budget Simulation — ADR-0013 Verification
===================================================
Simulates T4 band budget depletion over a game to verify ADR-0013 architecture.

Two modes:

  Parametric (pre-G1, default):
    Generates synthetic T4 fires using pregame context + configurable assumptions.
    Use to verify budget math and explore T4_BAND_WEIGHT scenarios BEFORE G1.

  Empirical (post-G1, --from-log):
    Replays actual PAPER_T4_VIRTUAL log from G1+ to calibrate T4_BAND_WEIGHT
    and T4_EXPECTED_TOTAL_EDGE with real data.

Output answers:
  - At T4_BAND_WEIGHT=X, how many bets fire before budget exhaustion?
  - What cycle does budget exhaust?
  - What T4_BAND_WEIGHT is needed for the budget to last the whole game?
  - What is T4_EXPECTED_TOTAL_EDGE from real data (post-G1)?

Usage:
    # Pre-G1 parametric (verify architecture now):
    PYTHONPATH=src python3 scripts/run_t4_budget_sim.py

    # Compare band weight scenarios:
    PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --band-weight 0.05 --label "conservative"
    PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --band-weight 0.20 --label "aggressive"

    # Post-G1 empirical calibration:
    PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl

    # Empirical with explicit bankroll:
    PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl --bankroll 618.03

Exit codes: 0 = success, 1 = missing input
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants — mirror run_t4_live.py ADR-0023 values exactly
# ---------------------------------------------------------------------------
DEFAULT_BAND_WEIGHT = 0.27       # T4_BAND_WEIGHT (ADR-0023, G4-calibrated)
DEFAULT_KELLY_T4 = 0.20          # KELLY_T4 from game_state_model.py (ADR-0010)
DEFAULT_MIN_EDGE = 0.02          # MIN_EDGE_TO_APPROVE from risk.py
DEFAULT_BANKROLL = 1000.0
MIN_BET_PAPER = 1.0              # MIN_BET_T4_PAPER
MAX_EXPOSURE = 500.0             # _HARD_LIMITS max_single_event_exposure_usd

# Parametric game model — placeholders until G1 calibration
GAME_CYCLES = 200                # ~200 × 45s = ~150 min game
FIRE_RATE_PER_PLAYER_CYCLE = 0.15  # P(T4 signal fires for a player in a given cycle)
EDGE_MEAN = 0.05                 # avg T4 edge (from T1 distribution as proxy)
EDGE_STD = 0.02                  # edge std dev
N_SIMS = 1_000                   # parametric simulations
SEED = 42

VPS_LOGS = Path("/opt/prediction-market-bot/logs")
LOCAL_LOGS = Path(__file__).resolve().parent.parent / "logs"


def _logs_dir() -> Path:
    if VPS_LOGS.exists():
        return VPS_LOGS
    LOCAL_LOGS.mkdir(exist_ok=True)
    return LOCAL_LOGS


def _find_pregame(date_str: Optional[str]) -> Optional[Path]:
    logs = _logs_dir()
    if date_str:
        p = logs / f"pregame_{date_str}.json"
        return p if p.exists() else None
    candidates = sorted(logs.glob("pregame_*.json"), reverse=True)
    return candidates[0] if candidates else None


def _read_bankroll(bankroll_override: Optional[float]) -> float:
    if bankroll_override is not None:
        return bankroll_override
    pf = _logs_dir() / "paper_portfolio.json"
    if pf.exists():
        try:
            d = json.loads(pf.read_text())
            return float(d.get("bankroll_usd", DEFAULT_BANKROLL))
        except Exception:
            pass
    return DEFAULT_BANKROLL


def _compute_band_budget(bankroll: float, band_weight: float) -> float:
    # ADR-0023: T4 budget = bankroll × weight, single path. T4 pool is isolated
    # capital — no RESERVE_MANDATE deduction (that gate applies to T1 batches).
    return bankroll * band_weight


# ---------------------------------------------------------------------------
# Parametric simulation (pre-G1 mode)
# ---------------------------------------------------------------------------

def _parametric_sim(
    n_players: int,
    band_budget: float,
    kelly_t4: float,
    min_edge: float,
    n_sims: int,
    seed: int,
) -> dict:
    """
    Simulate T4 budget depletion over a game parametrically.
    Returns summary statistics across n_sims Monte Carlo runs.
    """
    import random
    rng = random.Random(seed)

    bets_at_exhaustion_list = []
    cycle_at_exhaustion_list = []
    total_deployed_list = []
    total_bets_list = []

    for _ in range(n_sims):
        deployed = 0.0
        total_bets = 0
        exhaustion_cycle = None
        exhaustion_bets = None

        for cycle in range(GAME_CYCLES):
            for _ in range(n_players):
                if rng.random() > FIRE_RATE_PER_PLAYER_CYCLE:
                    continue

                edge = max(min_edge + 0.001, rng.gauss(EDGE_MEAN, EDGE_STD))
                bet = min(edge * kelly_t4 * band_budget, MAX_EXPOSURE)
                bet = max(bet, MIN_BET_PAPER)

                if deployed + bet > band_budget:
                    if exhaustion_cycle is None:
                        exhaustion_cycle = cycle
                        exhaustion_bets = total_bets
                    continue  # budget exhausted

                deployed += bet
                total_bets += 1

        total_deployed_list.append(deployed)
        total_bets_list.append(total_bets)
        if exhaustion_cycle is not None:
            bets_at_exhaustion_list.append(exhaustion_bets)
            cycle_at_exhaustion_list.append(exhaustion_cycle)

    n_exhausted = len(bets_at_exhaustion_list)
    pct_exhausted = n_exhausted / n_sims * 100

    return {
        "n_sims": n_sims,
        "n_exhausted": n_exhausted,
        "pct_exhausted": pct_exhausted,
        "avg_total_bets": sum(total_bets_list) / n_sims,
        "avg_deployed": sum(total_deployed_list) / n_sims,
        "avg_cycle_at_exhaustion": (
            sum(cycle_at_exhaustion_list) / n_exhausted if n_exhausted else None
        ),
        "avg_bets_at_exhaustion": (
            sum(bets_at_exhaustion_list) / n_exhausted if n_exhausted else None
        ),
        "total_bets_list": total_bets_list,
        "total_deployed_list": total_deployed_list,
        "cycle_at_exhaustion_list": cycle_at_exhaustion_list,
    }


# ---------------------------------------------------------------------------
# Empirical calibration (post-G1 mode)
# ---------------------------------------------------------------------------

def _parse_audit_log(log_path: Path) -> list[dict]:
    """
    Parse audit_t4.jsonl for VIRTUAL fire events.
    Returns list of {edge, approved_size, cycle_id} dicts.
    """
    fires = []
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = record.get("payload", {})
                # Look for T4 virtual fire events in audit log
                event_type = record.get("event_type", "")
                if "approved" in event_type.lower() or "virtual" in str(payload).lower():
                    edge = payload.get("edge")
                    size = payload.get("approved_size")
                    if edge is not None and size is not None:
                        fires.append({
                            "edge": float(edge),
                            "approved_size": float(size),
                            "cycle_id": payload.get("forecast_id", ""),
                        })
    except FileNotFoundError:
        pass
    return fires


def _parse_t4_log(log_path: Path) -> list[dict]:
    """
    Parse t4_live.log for 'T4 VIRTUAL' lines.
    Format: 'T4 VIRTUAL <ticker>  <dir>  $<size>  p=<p>  mip=<mip>  edge=<edge>  budget_track=$<used>/<budget>  cycle=<id>'
    """
    fires = []
    try:
        with open(log_path) as f:
            for line in f:
                if "T4 VIRTUAL" not in line:
                    continue
                parts = line.split()
                edge = None
                size = None
                for i, p in enumerate(parts):
                    if p.startswith("edge="):
                        try:
                            edge = float(p.split("=")[1])
                        except ValueError:
                            pass
                    if p.startswith("$") and i > 0 and parts[i-1] in ("YES", "NO", "YES ", "NO "):
                        try:
                            size = float(p.lstrip("$"))
                        except ValueError:
                            pass
                if edge is not None and size is not None:
                    fires.append({"edge": edge, "approved_size": size})
    except FileNotFoundError:
        pass
    return fires


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def _band_weight_needed(total_deployed: float, bankroll: float) -> float:
    """Back-calculate T4_BAND_WEIGHT needed to cover total_deployed exactly."""
    # ADR-0023: weight applies to full bankroll (no RESERVE_MANDATE deduction).
    if bankroll <= 0:
        return 0.0
    return total_deployed / bankroll


def _percentile(data: list, pct: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = max(0, min(len(sorted_data) - 1, int(math.ceil(pct / 100 * len(sorted_data))) - 1))
    return sorted_data[idx]


def build_parametric_report(
    pregame_path: Optional[Path],
    bankroll: float,
    band_weight: float,
    kelly: float,
    label: Optional[str],
) -> str:
    n_players = 25  # default
    if pregame_path:
        try:
            data = json.loads(pregame_path.read_text())
            forecasts = data.get("forecasts", [])
            player_ids = {f.get("player_id") for f in forecasts if f.get("player_id")}
            n_players = max(len(player_ids), 1)
        except Exception:
            pass

    band_budget = _compute_band_budget(bankroll, band_weight)
    stats = _parametric_sim(n_players, band_budget, kelly, DEFAULT_MIN_EDGE, N_SIMS, SEED)

    sep = "=" * 68
    lines = []
    label_str = f"  Label: {label}" if label else ""

    lines += [
        sep,
        "  T4 BAND BUDGET SIMULATION — ADR-0023 Verification (Parametric)",
        f"  Bankroll=${bankroll:.2f}  |  T4_BAND_WEIGHT={band_weight}  |  KELLY_T4={kelly}",
        f"  band_budget=${band_budget:.2f} (bankroll × weight; ADR-0023 single path)",
        f"  N_SIMS={N_SIMS:,}  |  GAME_CYCLES={GAME_CYCLES}  |  N_PLAYERS={n_players}",
        f"  FIRE_RATE={FIRE_RATE_PER_PLAYER_CYCLE}  |  EDGE_MEAN={EDGE_MEAN}  |  EDGE_STD={EDGE_STD}",
    ]
    if label_str:
        lines.append(label_str)
    lines += [
        "  [Parametric mode — replace with --from-log after G1 for calibration]",
        sep,
        "",
        "BUDGET BEHAVIOUR",
        f"  Band budget          : ${band_budget:.2f}",
        f"  Avg bets per game    : {stats['avg_total_bets']:.1f}",
        f"  Avg capital deployed : ${stats['avg_deployed']:.2f}  ({stats['avg_deployed']/band_budget*100:.1f}% of budget)",
        f"  Simulations exhausted: {stats['n_exhausted']:,} / {N_SIMS:,}  ({stats['pct_exhausted']:.1f}%)",
    ]

    if stats["avg_cycle_at_exhaustion"] is not None:
        pct_game = stats["avg_cycle_at_exhaustion"] / GAME_CYCLES * 100
        lines += [
            f"  Avg cycle at exhaust.: {stats['avg_cycle_at_exhaustion']:.0f} / {GAME_CYCLES}"
            f"  ({pct_game:.0f}% into game)",
            f"  Avg bets at exhaust. : {stats['avg_bets_at_exhaustion']:.0f}",
        ]
    else:
        lines.append("  Budget never exhausted in parametric model (budget weight may be large)")

    # Percentile distribution
    bets_p = stats["total_bets_list"]
    dep_p = stats["total_deployed_list"]
    lines += [
        "",
        "DEPLOYED CAPITAL DISTRIBUTION",
        f"  p5   : ${_percentile(dep_p, 5):.2f}",
        f"  p25  : ${_percentile(dep_p, 25):.2f}",
        f"  p50  : ${_percentile(dep_p, 50):.2f}",
        f"  p75  : ${_percentile(dep_p, 75):.2f}",
        f"  p95  : ${_percentile(dep_p, 95):.2f}",
        "",
        "BETS FIRED DISTRIBUTION",
        f"  p5   : {_percentile(bets_p, 5):.0f} bets",
        f"  p50  : {_percentile(bets_p, 50):.0f} bets",
        f"  p95  : {_percentile(bets_p, 95):.0f} bets",
    ]

    # Band weight sensitivity
    lines += [
        "",
        "BAND WEIGHT SENSITIVITY (at this bankroll)",
        f"  {'Weight':>8}  {'Band Budget':>12}  {'Avg Bet (edge=0.05)':>20}  {'~Bets Before Exhaust':>22}",
        "  " + "-" * 68,
    ]
    for w in [0.05, 0.10, 0.15, 0.20, 0.30]:
        bb = _compute_band_budget(bankroll, w)
        avg_bet = max(DEFAULT_MIN_EDGE * kelly * bb, MIN_BET_PAPER)
        est_bets = bb / avg_bet if avg_bet > 0 else 0
        lines.append(
            f"  {w:>8.2f}  ${bb:>10.2f}  {'$' + f'{avg_bet:.2f}':>20}  {est_bets:>20.0f}"
        )

    lines += [
        "",
        "CALIBRATION GUIDANCE",
        "  After G1 PAPER_T4_VIRTUAL run:",
        "  1. Run: PYTHONPATH=src python3 scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl",
        "  2. Note 'Total would-be deployed' from empirical section",
        "  3. Set T4_BAND_WEIGHT = total_deployed / (bankroll × 0.60) to cover 100% of G1 fires",
        "     Or: set to cover 50% of G1 fires as conservative starting point",
        "  4. Replace T4_BAND_WEIGHT stub in run_t4_live.py; log derivation in DECISION_LOG",
        "  5. Operator signs ADR-0013 calibration block before T4 ACTIVE",
        "",
        "GOVERNANCE",
        "  T4_BAND_WEIGHT=0.10 is a STUB. Do not set PAPER_T4_VIRTUAL=false until calibrated.",
        "  T4 ACTIVE gates: ADR-0013 calibrated + EXP-018 + DS-02 ADR (ADR-0011 successor).",
        sep,
        f"  Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"  Parameters : band_weight={band_weight}  kelly_t4={kelly}  bankroll=${bankroll:.2f}",
        sep,
    ]

    return "\n".join(lines)


def build_empirical_report(
    log_path: Path,
    bankroll: float,
    band_weight: float,
    kelly: float,
    label: Optional[str],
) -> str:
    """Replay actual PAPER_T4_VIRTUAL fires to calibrate ADR-0013 constants."""
    # Try audit_t4.jsonl first, then t4_live.log
    if log_path.suffix == ".jsonl":
        fires = _parse_audit_log(log_path)
    else:
        fires = _parse_t4_log(log_path)

    if not fires:
        return (
            f"No T4 VIRTUAL fires found in {log_path}.\n"
            "Ensure the file is the audit_t4.jsonl or t4_live.log from a PAPER_T4_VIRTUAL=true run."
        )

    band_budget = _compute_band_budget(bankroll, band_weight)
    total_edge = sum(f["edge"] for f in fires)
    total_deployed = sum(f["approved_size"] for f in fires)
    n_fires = len(fires)
    avg_edge = total_edge / n_fires if n_fires else 0
    avg_size = total_deployed / n_fires if n_fires else 0

    # Calibrated band weight
    calibrated_weight_100pct = _band_weight_needed(total_deployed, bankroll)
    calibrated_weight_50pct = calibrated_weight_100pct * 0.5  # conservative start

    sep = "=" * 68
    lines = []
    label_str = f"  Label: {label}" if label else ""

    lines += [
        sep,
        "  T4 BAND BUDGET SIMULATION — ADR-0013 Calibration (Empirical)",
        f"  Source: {log_path.name}",
        f"  Bankroll=${bankroll:.2f}  |  T4_BAND_WEIGHT={band_weight} (current stub)",
        f"  band_budget=${band_budget:.2f}",
    ]
    if label_str:
        lines.append(label_str)
    lines += [
        sep,
        "",
        "EMPIRICAL T4 FIRE DATA",
        f"  Total VIRTUAL fires  : {n_fires}",
        f"  Total edge (sum)     : {total_edge:.4f}  ← this is T4_EXPECTED_TOTAL_EDGE",
        f"  Total would-be deploy: ${total_deployed:.2f}  (if PAPER_T4_VIRTUAL=false)",
        f"  Avg edge per fire    : {avg_edge:.4f}",
        f"  Avg bet per fire     : ${avg_size:.2f}",
        "",
        "CALIBRATION — T4_BAND_WEIGHT",
        f"  Current stub          : {band_weight}  (band_budget=${band_budget:.2f})",
        f"  Weight to cover 100%  : {calibrated_weight_100pct:.4f}  "
        f"(budget=${_compute_band_budget(bankroll, calibrated_weight_100pct):.2f})",
        f"  Weight to cover 50%   : {calibrated_weight_50pct:.4f}  "
        f"(budget=${_compute_band_budget(bankroll, calibrated_weight_50pct):.2f})  ← recommended start",
        "",
        "CALIBRATION — T4_EXPECTED_TOTAL_EDGE",
        f"  Calibrated value      : {total_edge:.4f}",
        f"  Current stub          : 5.0",
        f"  → Replace stub in run_t4_live.py: T4_EXPECTED_TOTAL_EDGE = {total_edge:.2f}",
        "",
        "BUDGET SIMULATION (with current stub values)",
        f"  Would-be deployment vs band_budget: ${total_deployed:.2f} vs ${band_budget:.2f}",
    ]

    if total_deployed > band_budget:
        bets_before_exhaust = 0
        running = 0.0
        for f in fires:
            if running + f["approved_size"] > band_budget:
                break
            running += f["approved_size"]
            bets_before_exhaust += 1
        pct_bets = bets_before_exhaust / n_fires * 100
        lines += [
            f"  Budget OVER by        : ${total_deployed - band_budget:.2f}",
            f"  Bets before exhaust   : {bets_before_exhaust} / {n_fires}  ({pct_bets:.0f}%)",
            f"  ⚠ Current T4_BAND_WEIGHT={band_weight} insufficient for full game deployment.",
            f"  Consider: T4_BAND_WEIGHT = {calibrated_weight_50pct:.3f} (50% coverage)",
        ]
    else:
        headroom = band_budget - total_deployed
        lines += [
            f"  Budget headroom       : ${headroom:.2f}  ({headroom/band_budget*100:.0f}% unused)",
            f"  ✓ T4_BAND_WEIGHT={band_weight} covers all G1 fires with ${headroom:.2f} headroom.",
        ]

    lines += [
        "",
        "NEXT STEPS",
        f"  1. Replace T4_BAND_WEIGHT stub: T4_BAND_WEIGHT = {calibrated_weight_50pct:.3f}",
        f"     (or {calibrated_weight_100pct:.3f} for 100% coverage — operator decision)",
        f"  2. Replace T4_EXPECTED_TOTAL_EDGE stub: T4_EXPECTED_TOTAL_EDGE = {total_edge:.2f}",
        "  3. Log derivation in DECISION_LOG with this report as evidence.",
        "  4. Operator signs ADR-0013 calibration block.",
        "  5. Repeat after each Finals game to refine estimates.",
        "",
        "GOVERNANCE",
        "  Do not set PAPER_T4_VIRTUAL=false until stubs are replaced and ADR-0013 signed.",
        sep,
        f"  Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"  Source     : {log_path}",
        f"  Parameters : band_weight={band_weight}  kelly_t4={kelly}  bankroll=${bankroll:.2f}",
        sep,
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="T4 Band Budget Simulation — ADR-0013 verification and calibration"
    )
    parser.add_argument("--from-log", metavar="PATH",
                        help="Path to audit_t4.jsonl or t4_live.log for empirical calibration (post-G1)")
    parser.add_argument("--date", help="Pregame date YYYYMMDD for parametric mode (default: auto)")
    parser.add_argument("--bankroll", type=float, default=None,
                        help="Override bankroll (default: read from paper_portfolio.json)")
    parser.add_argument("--band-weight", type=float, default=DEFAULT_BAND_WEIGHT,
                        help=f"T4_BAND_WEIGHT to simulate (default: {DEFAULT_BAND_WEIGHT})")
    parser.add_argument("--kelly", type=float, default=DEFAULT_KELLY_T4,
                        help=f"KELLY_T4 fraction (default: {DEFAULT_KELLY_T4})")
    parser.add_argument("--label", help="Label for comparison runs")
    parser.add_argument("--out", help="Write output to file (also prints to stdout)")

    args = parser.parse_args()

    bankroll = _read_bankroll(args.bankroll)

    if args.from_log:
        log_path = Path(args.from_log)
        if not log_path.exists():
            # Try relative to logs dir
            log_path = _logs_dir() / args.from_log
        if not log_path.exists():
            print(f"ERROR: Log file not found: {args.from_log}", file=sys.stderr)
            sys.exit(1)
        report = build_empirical_report(log_path, bankroll, args.band_weight, args.kelly, args.label)
    else:
        pregame_path = _find_pregame(args.date)
        if pregame_path is None:
            print(
                "WARNING: No pregame file found — using default player count (25).",
                file=sys.stderr,
            )
        report = build_parametric_report(pregame_path, bankroll, args.band_weight, args.kelly, args.label)

    print(report)

    if args.out:
        Path(args.out).write_text(report)
        print(f"\n[Output saved to {args.out}]")


if __name__ == "__main__":
    main()

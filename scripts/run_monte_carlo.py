#!/usr/bin/env python3
"""
Prediction Market Bot — Monte Carlo Pre-Game Assessment

MANDATORY TRIGGER: Run this after any ADR acceptance, parameter change,
or model update that affects C3/C4 behaviour. See MONTE_CARLO_PROTOCOL.md.

Reads the latest pregame_YYYYMMDD.json from PIPE-02.
Mirrors PIPE-03 Path B sizing exactly so output predicts actual bets.

Usage:
    # Auto-discover latest pregame (standard use):
    PYTHONPATH=src python3 scripts/run_monte_carlo.py

    # Specific game date:
    PYTHONPATH=src python3 scripts/run_monte_carlo.py --date 20260603

    # Before/after strategy comparison — run twice, compare outputs:
    PYTHONPATH=src python3 scripts/run_monte_carlo.py --label "before-ADR-0013" --out logs/mc_before.txt
    PYTHONPATH=src python3 scripts/run_monte_carlo.py --kelly 0.12 --label "after-ADR-0013" --out logs/mc_after.txt

    # Override any C4 parameter to test impact:
    PYTHONPATH=src python3 scripts/run_monte_carlo.py --kelly 0.15 --min-edge 0.03

Exit codes: 0 = success, 1 = no pregame file, 2 = no actionable bets
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from scipy.stats import poisson

# ---------------------------------------------------------------------------
# Default constants — mirror PIPE-03 / C4 hard limits exactly
# Changes here require an ADR; use CLI overrides to test without committing.
# ---------------------------------------------------------------------------
DEFAULT_T1_KELLY = 0.10          # ADR-0010
DEFAULT_MIN_EDGE = 0.02          # EDGE_YES / EDGE_NO in run_paper_trade.py
DEFAULT_MAX_EXPOSURE = 500.0     # _HARD_LIMITS["max_single_event_exposure_usd"]
DEFAULT_MIN_BET = 10.0           # risk.py MIN_BET_USD
DEFAULT_BANKROLL = 1000.0
MAX_DAILY_LOSS_PCT = 0.15        # ADR-0012
RESERVE_MANDATE_PCT = 0.40       # advisory at paper; blocking at live capital
N_SIMS = 10_000
SEED = 42

VPS_LOGS = Path("/opt/prediction-market-bot/logs")
LOCAL_LOGS = Path(__file__).resolve().parent.parent / "logs"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
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


def _read_bankroll() -> float:
    pf = _logs_dir() / "paper_portfolio.json"
    if not pf.exists():
        return DEFAULT_BANKROLL
    try:
        d = json.loads(pf.read_text())
        return float(d.get("bankroll_usd", DEFAULT_BANKROLL))
    except Exception:
        return DEFAULT_BANKROLL


def _load_markets(pregame_path: Path) -> Tuple[List[dict], dict]:
    data = json.loads(pregame_path.read_text())
    markets = [
        {
            "player": f["player_name"],
            "lam": float(f["pts_l10_mean"]),
            "threshold": int(f["kalshi_threshold"]),
            "mid": float(f["mid_price"]),
            "vig": float(f["vig"]),
        }
        for f in data.get("forecasts", [])
    ]
    return markets, data


# ---------------------------------------------------------------------------
# Bet computation (mirrors run_paper_trade.py Path B + risk.py Kelly)
# ---------------------------------------------------------------------------
def _poisson_sf(t: int, lam: float) -> float:
    return float(poisson.sf(t - 1, lam))


def compute_bets(
    markets: List[dict],
    bankroll: float,
    kelly: float = DEFAULT_T1_KELLY,
    min_edge: float = DEFAULT_MIN_EDGE,
    max_exposure: float = DEFAULT_MAX_EXPOSURE,
    min_bet: float = DEFAULT_MIN_BET,
) -> Tuple[List[dict], List[dict]]:
    """
    Compute approved bets AND rejected markets (with rejection reason).
    Returns (approved_bets, rejected_list).
    Sequential bankroll reduction matches run_paper_trade.py behaviour.
    """
    approved = []
    rejected = []
    current_bankroll = bankroll

    for m in markets:
        lam = m["lam"]
        threshold = int(m["threshold"])
        mid = float(m["mid"])
        vig = float(m["vig"])

        half = vig / 2.0
        p_model = _poisson_sf(threshold, lam)
        edge = p_model - mid - half

        if edge > min_edge:
            direction = "YES"
        elif edge < -min_edge:
            direction = "NO"
        else:
            rejected.append({**m, "p_model": p_model, "edge": edge, "reason": "PASS (insufficient edge)"})
            continue

        if direction == "YES":
            p_eff, mip_eff = p_model, mid
        else:
            p_eff, mip_eff = 1.0 - p_model, 1.0 - mid

        b = (1.0 - mip_eff) / mip_eff
        q = 1.0 - p_eff
        f_star = (p_eff * b - q) / b

        if f_star <= 0.0:
            rejected.append({**m, "p_model": p_model, "edge": edge, "reason": "kelly_zero (no edge on direction)"})
            continue

        stake = min(f_star * kelly * current_bankroll, max_exposure)

        if stake < min_bet:
            rejected.append({**m, "p_model": p_model, "edge": edge, "reason": f"min_bet_floor (${stake:.2f} < ${min_bet})"})
            continue

        approved.append({
            **m,
            "direction": direction,
            "p_model": p_model,
            "p_eff": p_eff,
            "mip_eff": mip_eff,
            "edge": edge,
            "f_star": f_star,
            "stake": stake,
            "win_odds": (1.0 - mip_eff) / mip_eff,
        })
        current_bankroll -= stake

    return approved, rejected


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def simulate(bets: List[dict], n_sims: int = N_SIMS) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (pnl_array, per_bet_win_matrix).
    pnl_array shape: (n_sims,)
    per_bet_win_matrix shape: (n_sims, n_bets) — True where bet won
    """
    if not bets:
        return np.zeros(n_sims), np.zeros((n_sims, 0), dtype=bool)

    rng = np.random.default_rng(SEED)
    players = list({b["player"] for b in bets})
    lambda_map = {b["player"]: b["lam"] for b in bets}
    scores = {p: rng.poisson(lambda_map[p], size=n_sims) for p in players}

    pnl = np.zeros(n_sims)
    win_matrix = np.zeros((n_sims, len(bets)), dtype=bool)

    for i, b in enumerate(bets):
        s = scores[b["player"]]
        wins = s >= b["threshold"] if b["direction"] == "YES" else s < b["threshold"]
        win_matrix[:, i] = wins
        pnl += np.where(wins, b["stake"] * b["win_odds"], -b["stake"])

    return pnl, win_matrix


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------
def build_report(
    pregame_path: Path,
    bankroll: float,
    kelly: float,
    min_edge: float,
    max_exposure: float,
    label: Optional[str],
) -> str:
    markets, meta = _load_markets(pregame_path)
    bets, rejected = compute_bets(markets, bankroll, kelly, min_edge, max_exposure)
    pnl, win_matrix = simulate(bets)

    n_markets = len(markets)
    n_bets = len(bets)
    n_yes = sum(1 for b in bets if b["direction"] == "YES")
    n_no = n_bets - n_yes
    n_rejected = len(rejected)
    total_stake = sum(b["stake"] for b in bets)
    deployment_pct = total_stake / bankroll * 100 if bankroll else 0
    max_daily_loss = bankroll * MAX_DAILY_LOSS_PCT

    total_ev = sum(
        b["stake"] * (b["p_eff"] * b["win_odds"] - (1.0 - b["p_eff"]))
        for b in bets
    )

    sep = "=" * 68
    lines: List[str] = []

    label_str = f"  Label: {label}" if label else ""

    lines += [
        sep,
        "  PIPE-03 Monte Carlo Pre-Game Assessment",
        f"  game_date={meta.get('game_date','?')}  |  pregame_run={meta.get('run_at','?')}",
        f"  Bankroll=${bankroll:.2f}  |  T1_KELLY={kelly}  |  MIN_EDGE={min_edge}  |  N={N_SIMS:,}",
    ]
    if label_str:
        lines.append(label_str)
    lines.append(sep)

    # ------------------------------------------------------------------
    # 1. Bot Statistics
    # ------------------------------------------------------------------
    lines += ["", "BOT STATISTICS"]
    lines += [
        f"  Markets evaluated  : {n_markets}",
        f"  Bets PLACED        : {n_bets}  ({n_yes} YES  |  {n_no} NO)",
        f"  Bets REJECTED/PASS : {n_rejected}",
    ]

    if bets:
        # Analytical win/loss projections per bet
        exp_wins_per_bet = [b["p_eff"] for b in bets]
        exp_wins_total = sum(exp_wins_per_bet)
        exp_losses_total = n_bets - exp_wins_total

        # MC win/loss counts
        wins_per_sim = win_matrix.sum(axis=1)    # shape (n_sims,)
        mean_wins = float(np.mean(wins_per_sim))
        mean_losses = n_bets - mean_wins

        lines += [
            f"  Bets exp. to WIN   : {exp_wins_total:.1f} / {n_bets}  ({exp_wins_total/n_bets*100:.0f}%)",
            f"  Bets exp. to LOSE  : {exp_losses_total:.1f} / {n_bets}  ({exp_losses_total/n_bets*100:.0f}%)",
            f"  MC avg bets won    : {mean_wins:.1f}  |  lost: {mean_losses:.1f}",
        ]

        lines += [
            f"",
            f"  Total staked       : ${total_stake:.2f}  ({deployment_pct:.1f}% of bankroll)",
            f"  Reserve (T4/T5)    : ${bankroll - total_stake:.2f}  ({100-deployment_pct:.1f}%)",
        ]
        if deployment_pct > 60.0:
            lines.append(
                f"  ⚠ RESERVE MANDATE : {deployment_pct:.1f}% > 60% target. "
                f"T4/T5 capital=${bankroll - total_stake:.2f}. Batch enforcement deferred."
            )

        # Per-player breakdown
        lines += ["", "  Per-player breakdown:"]
        lines.append(f"  {'Player':<22} {'Bets':>5}  {'Stake':>8}  {'Exp.Win%':>9}  {'YES/NO'}")
        lines.append("  " + "-" * 62)
        player_names = sorted({b["player"] for b in bets})
        for pname in player_names:
            pb = [b for b in bets if b["player"] == pname]
            p_stake = sum(b["stake"] for b in pb)
            p_yes = sum(1 for b in pb if b["direction"] == "YES")
            p_no  = sum(1 for b in pb if b["direction"] == "NO")
            p_win_pct = sum(b["p_eff"] for b in pb) / len(pb) * 100
            lines.append(
                f"  {pname:<22} {len(pb):>5}  ${p_stake:>7.2f}  {p_win_pct:>8.0f}%  {p_yes}Y/{p_no}N"
            )

        # Bet-level detail
        lines += ["", "  Bet-level detail:"]
        lines.append(f"  {'Player':<22} {'D':<4} {'Thr':>4}  {'p_mdl':>6}  {'mid':>6}  {'edge':>7}  {'f*':>6}  {'Stake':>7}  {'WinRate':>8}")
        lines.append("  " + "-" * 82)
        for pname in player_names:
            for b in [x for x in bets if x["player"] == pname]:
                lines.append(
                    f"  {b['player']:<22} {b['direction']:<4} {b['threshold']:>4}"
                    f"  {b['p_model']:.4f}  {b['mid']:.4f}  {b['edge']:>+.4f}"
                    f"  {b['f_star']:.4f}  ${b['stake']:>6.2f}  {b['p_eff']*100:>7.1f}%"
                )

        # Rejected summary
        if rejected:
            lines += ["", "  Rejected / PASS:"]
            for r in rejected:
                lines.append(f"    {r['player']:<22} thr={r['threshold']:>3}  edge={r['edge']:>+.4f}  → {r['reason']}")

    # ------------------------------------------------------------------
    # 2. Expected Value
    # ------------------------------------------------------------------
    lines += [
        "",
        "EXPECTED VALUE",
        f"  Analytical EV      : ${total_ev:>+.2f}",
    ]
    if total_stake:
        lines.append(f"  ROI on deployed    : {total_ev / total_stake * 100:>+.2f}%")
    lines.append(f"  ROI on bankroll    : {total_ev / bankroll * 100:>+.2f}%")
    if n_bets:
        lines.append(f"  Avg EV per bet     : ${total_ev / n_bets:>+.2f}")

    # ------------------------------------------------------------------
    # 3. Monte Carlo P/L Distribution
    # ------------------------------------------------------------------
    if n_bets:
        pcts = [1, 5, 25, 50, 75, 95, 99]
        pct_vals = np.percentile(pnl, pcts)
        prob_profit = float(np.mean(pnl > 0)) * 100
        prob_breakeven = float(np.mean(pnl == 0)) * 100
        prob_loss = float(np.mean(pnl < 0)) * 100
        prob_ks = float(np.mean(pnl <= -max_daily_loss)) * 100

        lines += [
            "",
            "MONTE CARLO P/L DISTRIBUTION",
            f"  Mean P/L           : ${np.mean(pnl):>+.2f}",
            f"  Std deviation      : ${np.std(pnl):>.2f}",
            f"  P(profit)          : {prob_profit:.1f}%",
            f"  P(loss)            : {prob_loss:.1f}%",
            f"  Kill switch risk   : {prob_ks:.2f}%  (loss ≥ ${max_daily_loss:.0f}; ADR-0012)",
            "",
        ]
        for p, v in zip(pcts, pct_vals):
            lines.append(f"  p{p:>2}  ${v:>+8.2f}")
        lines += [
            "",
            f"  Worst case (ever)  : ${np.min(pnl):>+.2f}",
            f"  Best case (all-win): ${np.max(pnl):>+.2f}",
            f"  Ending bankroll",
            f"    p5   : ${bankroll + np.percentile(pnl, 5):.2f}",
            f"    p50  : ${bankroll + np.median(pnl):.2f}",
            f"    p95  : ${bankroll + np.percentile(pnl, 95):.2f}",
        ]
    else:
        lines.append("\n  No approved bets — simulation not run.")

    # ------------------------------------------------------------------
    # 4. Governance
    # ------------------------------------------------------------------
    lines += [
        "",
        "GOVERNANCE",
        "  GG-004: EV compares Poisson model vs market mid — NOT adversarial.",
        "  EXP-017 Part B (≥66 resolved bets) is the binding commercial test.",
        "  Player scores modeled as independent Poisson draws. True P/L variance",
        "  is HIGHER due to intra-game pace correlation. P5/P95 are conservative.",
        sep,
        f"  Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"  Source     : {pregame_path.name}",
        f"  Parameters : kelly={kelly}  min_edge={min_edge}  max_exposure={max_exposure}",
        sep,
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="PIPE-03 Monte Carlo Pre-Game Assessment (see MONTE_CARLO_PROTOCOL.md)"
    )
    parser.add_argument("--date", help="Game date YYYYMMDD (default: auto-discover latest)")
    parser.add_argument("--pregame", help="Explicit path to pregame JSON")
    parser.add_argument("--out", help="Save report to file (also prints to stdout)")
    parser.add_argument("--label", help="Label for before/after comparison runs")
    parser.add_argument("--kelly", type=float, default=DEFAULT_T1_KELLY,
                        help=f"Kelly fraction override (default {DEFAULT_T1_KELLY}; ADR-0010)")
    parser.add_argument("--min-edge", type=float, default=DEFAULT_MIN_EDGE, dest="min_edge",
                        help=f"Min edge override (default {DEFAULT_MIN_EDGE})")
    parser.add_argument("--max-exposure", type=float, default=DEFAULT_MAX_EXPOSURE, dest="max_exposure",
                        help=f"Max single-bet exposure $ override (default {DEFAULT_MAX_EXPOSURE})")
    args = parser.parse_args()

    # Resolve pregame file
    if args.pregame:
        pregame_path = Path(args.pregame)
        if not pregame_path.exists():
            print(f"ERROR: pregame file not found: {args.pregame}", file=sys.stderr)
            sys.exit(1)
    else:
        pregame_path = _find_pregame(args.date)
        if pregame_path is None:
            hint = args.date or "latest"
            print(f"ERROR: no pregame JSON found ({hint}). Run PIPE-02 first.", file=sys.stderr)
            sys.exit(1)

    bankroll = _read_bankroll()
    report = build_report(
        pregame_path, bankroll,
        kelly=args.kelly,
        min_edge=args.min_edge,
        max_exposure=args.max_exposure,
        label=args.label,
    )

    print(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report)
        print(f"[Saved to {out_path}]", file=sys.stderr)

    # Exit 2 if no bets placed
    markets, _ = _load_markets(pregame_path)
    bets, _ = compute_bets(markets, bankroll, args.kelly, args.min_edge, args.max_exposure)
    if not bets:
        sys.exit(2)


if __name__ == "__main__":
    main()

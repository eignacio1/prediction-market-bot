#!/usr/bin/env python3
"""
Prediction Market Bot — Monte Carlo Risk Assessment

Two modes:
  portfolio (default): simulate actual committed positions from paper_portfolio.json
  preview (--preview): pre-deployment preview from latest pregame JSON

Usage:
  # Actual portfolio risk (default):
  PYTHONPATH=src python3 scripts/run_monte_carlo.py

  # Filters (portfolio mode):
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --exclude-failed
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --yes-only
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --no-only
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --haircut 15

  # Pre-deployment preview (pregame JSON):
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --preview
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --preview --date 20260613
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --preview --kelly 0.20 --label "before-ADR-XXXX"
  PYTHONPATH=src python3 scripts/run_monte_carlo.py --preview --out logs/mc_preview.txt

Exit codes: 0 = success, 1 = no data, 2 = no actionable bets
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from scipy.stats import poisson

# ---------------------------------------------------------------------------
# Constants — match production values in risk.py / run_paper_trade.py
# ---------------------------------------------------------------------------
DEFAULT_T1_KELLY = 0.25          # DEFAULT_KELLY_FRACTION in risk.py (ADR-0020)
DEFAULT_MIN_EDGE = 0.04          # MIN_EDGE_TO_APPROVE in risk.py (ADR-0020)
DEFAULT_MAX_EXPOSURE = 500.0     # _HARD_LIMITS["max_single_event_exposure_usd"]
DEFAULT_MIN_BET = float(os.environ.get("MIN_BET_T1_PAPER", "1.0"))
DEFAULT_BANKROLL = 1000.0
MAX_DAILY_LOSS_PCT = 0.15        # ADR-0012
N_SIMS = 10_000
SEED = 42

VPS_LOGS = Path("/opt/prediction-market-bot/logs")
LOCAL_LOGS = Path(__file__).resolve().parent.parent / "logs"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _logs_dir() -> Path:
    if VPS_LOGS.exists():
        return VPS_LOGS
    LOCAL_LOGS.mkdir(exist_ok=True)
    return LOCAL_LOGS


def _read_bankroll() -> float:
    pf = _logs_dir() / "paper_portfolio.json"
    if not pf.exists():
        return DEFAULT_BANKROLL
    try:
        d = json.loads(pf.read_text())
        return float(d.get("bankroll_usd", DEFAULT_BANKROLL))
    except Exception:
        return DEFAULT_BANKROLL


# ---------------------------------------------------------------------------
# Portfolio mode — load from paper_portfolio.json
# ---------------------------------------------------------------------------
def _load_portfolio(
    exclude_failed: bool = False,
    direction_filter: Optional[str] = None,
) -> Tuple[List[dict], dict]:
    pf = _logs_dir() / "paper_portfolio.json"
    if not pf.exists():
        return [], {}
    data = json.loads(pf.read_text())
    positions = [p for p in data.get("open_positions", []) if p.get("status") == "OPEN"]

    if exclude_failed:
        positions = [p for p in positions
                     if not str(p.get("kalshi_order_status", "")).startswith("failed:")]
    if direction_filter:
        positions = [p for p in positions if p.get("direction") == direction_filter]

    return positions, data


def _build_portfolio_bets(positions: List[dict], haircut_pct: float = 0.0) -> List[dict]:
    bets = []
    for p in positions:
        direction = p["direction"]
        model_p = float(p["model_p"])
        mid = float(p["mid_price_at_entry"])
        size = float(p["size_usd"])
        if haircut_pct > 0.0:
            size *= 1.0 - haircut_pct / 100.0

        if direction == "YES":
            p_win = model_p
            win_odds = (1.0 - mid) / mid
        else:
            p_win = 1.0 - model_p
            win_odds = mid / (1.0 - mid)

        bets.append({
            "player": p.get("player_name", "unknown"),
            "ticker": p["kalshi_ticker"],
            "threshold": p.get("kalshi_threshold", 0),
            "direction": direction,
            "model_p": model_p,
            "mid": mid,
            "p_win": p_win,
            "win_odds": win_odds,
            "stake": size,
            "kalshi_order_status": p.get("kalshi_order_status", "unknown"),
        })
    return bets


def simulate_portfolio(
    bets: List[dict],
    n_sims: int = N_SIMS,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate P&L from committed positions using per-position Bernoulli draws.
    Returns (pnl_array, win_matrix)."""
    if not bets:
        return np.zeros(n_sims), np.zeros((n_sims, 0), dtype=bool)

    rng = np.random.default_rng(SEED)
    pnl = np.zeros(n_sims)
    win_matrix = np.zeros((n_sims, len(bets)), dtype=bool)

    for i, b in enumerate(bets):
        wins = rng.random(n_sims) < b["p_win"]
        win_matrix[:, i] = wins
        pnl += np.where(wins, b["stake"] * b["win_odds"], -b["stake"])

    return pnl, win_matrix


def build_portfolio_report(
    bankroll: float,
    exclude_failed: bool,
    direction_filter: Optional[str],
    haircut_pct: float,
    label: Optional[str],
    positions: List[dict],
    portfolio_meta: dict,
) -> str:
    bets = _build_portfolio_bets(positions, haircut_pct=haircut_pct)
    pnl, win_matrix = simulate_portfolio(bets)

    n_bets = len(bets)
    n_yes = sum(1 for b in bets if b["direction"] == "YES")
    n_no = n_bets - n_yes
    total_stake = sum(b["stake"] for b in bets)
    deployment_pct = total_stake / bankroll * 100 if bankroll else 0
    max_daily_loss = bankroll * MAX_DAILY_LOSS_PCT
    total_ev = sum(
        b["stake"] * (b["p_win"] * b["win_odds"] - (1.0 - b["p_win"]))
        for b in bets
    )

    all_open = [p for p in portfolio_meta.get("open_positions", []) if p.get("status") == "OPEN"]
    n_total_open = len(all_open)
    n_failed = sum(1 for p in all_open
                   if str(p.get("kalshi_order_status", "")).startswith("failed:"))
    realized_pnl = portfolio_meta.get("realized_pnl_usd", 0.0)

    filter_parts = []
    if exclude_failed:
        filter_parts.append("exclude-failed")
    if direction_filter:
        filter_parts.append(direction_filter + "-only")
    if haircut_pct > 0:
        filter_parts.append(f"haircut={haircut_pct:.0f}%")
    filter_str = "  Filters   : " + ", ".join(filter_parts) if filter_parts else "  Filters   : none"

    sep = "=" * 68
    lines = [
        sep,
        "  PIPE-03 Monte Carlo Portfolio Risk Assessment",
        "  MODE: actual committed positions (paper_portfolio.json)",
        f"  Bankroll=${bankroll:.2f}  |  Realized P&L=${realized_pnl:+.2f}  |  N={N_SIMS:,}",
        f"  Positions: {n_total_open} total open  |  {n_failed} failed-Kalshi  |  simulating {n_bets}",
        filter_str,
    ]
    if label:
        lines.append(f"  Label     : {label}")
    lines.append(sep)

    lines += ["", "BOT STATISTICS"]
    lines += [f"  Positions simulated: {n_bets}  ({n_yes} YES  |  {n_no} NO)"]

    if bets:
        exp_wins = sum(b["p_win"] for b in bets)
        exp_losses = n_bets - exp_wins
        wins_per_sim = win_matrix.sum(axis=1)
        mean_wins = float(np.mean(wins_per_sim))

        lines += [
            f"  Exp. bets to WIN   : {exp_wins:.1f} / {n_bets}  ({exp_wins/n_bets*100:.0f}%)",
            f"  Exp. bets to LOSE  : {exp_losses:.1f} / {n_bets}  ({exp_losses/n_bets*100:.0f}%)",
            f"  MC avg bets won    : {mean_wins:.1f}  |  lost: {n_bets - mean_wins:.1f}",
            "",
            f"  Total staked       : ${total_stake:.2f}  ({deployment_pct:.1f}% of bankroll)",
            f"  Reserve remaining  : ${bankroll - total_stake:.2f}  ({100 - deployment_pct:.1f}%)",
        ]
        if deployment_pct > 60.0:
            lines.append(f"  ! RESERVE MANDATE : {deployment_pct:.1f}% > 60% target.")

        lines += ["", "  Per-player breakdown:"]
        lines.append(f"  {'Player':<22} {'Bets':>5}  {'Stake':>8}  {'Exp.Win%':>9}  {'YES/NO'}")
        lines.append("  " + "-" * 62)
        player_names = sorted({b["player"] for b in bets})
        for pname in player_names:
            pb = [b for b in bets if b["player"] == pname]
            p_stake = sum(b["stake"] for b in pb)
            p_yes = sum(1 for b in pb if b["direction"] == "YES")
            p_no = sum(1 for b in pb if b["direction"] == "NO")
            p_win_pct = sum(b["p_win"] for b in pb) / len(pb) * 100
            lines.append(
                f"  {pname:<22} {len(pb):>5}  ${p_stake:>7.2f}  {p_win_pct:>8.0f}%  {p_yes}Y/{p_no}N"
            )

        lines += ["", "  Bet-level detail:"]
        lines.append(
            f"  {'Player':<22} {'D':<4} {'Thr':>4}  {'p_mdl':>6}  {'mid':>6}"
            f"  {'p_win':>6}  {'Stake':>7}  {'Kalshi':>10}"
        )
        lines.append("  " + "-" * 84)
        for pname in player_names:
            for b in [x for x in bets if x["player"] == pname]:
                ks = b["kalshi_order_status"]
                ks_tag = "OK" if ks == "resting" else ("FAIL" if ks.startswith("failed:") else ks[:10])
                lines.append(
                    f"  {b['player']:<22} {b['direction']:<4} {b['threshold']:>4}"
                    f"  {b['model_p']:.4f}  {b['mid']:.4f}"
                    f"  {b['p_win']:.4f}  ${b['stake']:>6.2f}  {ks_tag:>10}"
                )

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

    if n_bets:
        pcts = [1, 5, 25, 50, 75, 95, 99]
        pct_vals = np.percentile(pnl, pcts)
        prob_profit = float(np.mean(pnl > 0)) * 100
        prob_loss = float(np.mean(pnl < 0)) * 100
        prob_ks = float(np.mean(pnl <= -max_daily_loss)) * 100

        lines += [
            "",
            "MONTE CARLO P/L DISTRIBUTION",
            f"  Mean P/L           : ${np.mean(pnl):>+.2f}",
            f"  Std deviation      : ${np.std(pnl):>.2f}",
            f"  P(profit)          : {prob_profit:.1f}%",
            f"  P(loss)            : {prob_loss:.1f}%",
            f"  Kill switch risk   : {prob_ks:.2f}%  (loss >= ${max_daily_loss:.0f}; ADR-0012)",
            "",
        ]
        for p, v in zip(pcts, pct_vals):
            lines.append(f"  p{p:>2}  ${v:>+8.2f}")
        lines += [
            "",
            f"  Worst case         : ${np.min(pnl):>+.2f}",
            f"  Best case          : ${np.max(pnl):>+.2f}",
            f"  Ending bankroll",
            f"    p5   : ${bankroll + np.percentile(pnl, 5):.2f}",
            f"    p50  : ${bankroll + np.median(pnl):.2f}",
            f"    p95  : ${bankroll + np.percentile(pnl, 95):.2f}",
        ]
    else:
        lines.append("\n  No positions — simulation not run.")

    lines += [
        "",
        "GOVERNANCE",
        "  Simulated as independent Bernoulli draws using model_p per position.",
        "  Multiple thresholds on same player are correlated in reality —",
        "  actual variance is higher than reported. P5/P95 are optimistic on downside.",
        "  GG-028 (T-166): failed Kalshi positions included in idempotency guard.",
        "  Use --exclude-failed to simulate Kalshi-confirmed positions only.",
        "  GG-004: EV compares model vs market mid — NOT adversarial validation.",
        "  EXP-017 is the binding commercial test.",
        sep,
        f"  Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"  Source     : paper_portfolio.json",
        sep,
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Preview mode — load from pregame JSON (pre-deployment simulation)
# ---------------------------------------------------------------------------
def _find_pregame(date_str: Optional[str]) -> Optional[Path]:
    logs = _logs_dir()
    if date_str:
        p = logs / f"pregame_{date_str}.json"
        return p if p.exists() else None
    candidates = sorted(logs.glob("pregame_*.json"), reverse=True)
    return candidates[0] if candidates else None


def _load_markets(pregame_path: Path) -> Tuple[List[dict], dict]:
    data = json.loads(pregame_path.read_text())
    markets = []
    for f in data.get("forecasts", []):
        adj_lam = f.get("opp_adj_lambda")
        sim_lam = float(adj_lam) if adj_lam is not None else float(f["pts_l10_mean"])
        p_precomp = float(f["p_estimate"]) if f.get("p_estimate") is not None else None
        net_edge_precomp = float(f["edge"]) if f.get("edge") is not None else None
        markets.append({
            "player": f["player_name"],
            "lam": float(f["pts_l10_mean"]),
            "sim_lam": sim_lam,
            "threshold": int(f["kalshi_threshold"]),
            "mid": float(f["mid_price"]),
            "vig": float(f["vig"]),
            "p_precomp": p_precomp,
            "net_edge_precomp": net_edge_precomp,
        })
    return markets, data


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
    approved = []
    rejected = []
    current_bankroll = bankroll

    for m in markets:
        lam = m["lam"]
        threshold = int(m["threshold"])
        mid = float(m["mid"])
        vig = float(m["vig"])

        if m.get("p_precomp") is not None:
            p_model = m["p_precomp"]
        else:
            p_model = _poisson_sf(threshold, lam)

        if m.get("net_edge_precomp") is not None:
            edge = m["net_edge_precomp"]
        else:
            half = vig / 2.0
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
            rejected.append({**m, "p_model": p_model, "edge": edge, "reason": "kelly_zero"})
            continue

        stake = min(f_star * kelly * current_bankroll, max_exposure)

        if stake < min_bet:
            rejected.append({**m, "p_model": p_model, "edge": edge,
                              "reason": f"min_bet_floor (${stake:.2f} < ${min_bet})"})
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


def simulate_preview(bets: List[dict], n_sims: int = N_SIMS) -> Tuple[np.ndarray, np.ndarray]:
    """Poisson-based simulation for preview mode (score draws → threshold comparison)."""
    if not bets:
        return np.zeros(n_sims), np.zeros((n_sims, 0), dtype=bool)

    rng = np.random.default_rng(SEED)
    players = list({b["player"] for b in bets})
    lambda_map = {b["player"]: b.get("sim_lam", b["lam"]) for b in bets}
    scores = {p: rng.poisson(lambda_map[p], size=n_sims) for p in players}

    pnl = np.zeros(n_sims)
    win_matrix = np.zeros((n_sims, len(bets)), dtype=bool)

    for i, b in enumerate(bets):
        s = scores[b["player"]]
        wins = s >= b["threshold"] if b["direction"] == "YES" else s < b["threshold"]
        win_matrix[:, i] = wins
        pnl += np.where(wins, b["stake"] * b["win_odds"], -b["stake"])

    return pnl, win_matrix


def build_preview_report(
    pregame_path: Path,
    bankroll: float,
    kelly: float,
    min_edge: float,
    max_exposure: float,
    label: Optional[str],
    min_bet: float = DEFAULT_MIN_BET,
) -> str:
    markets, meta = _load_markets(pregame_path)
    bets, rejected = compute_bets(markets, bankroll, kelly, min_edge, max_exposure, min_bet)
    pnl, win_matrix = simulate_preview(bets)

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
    lines = []

    adj_lam_applied = any(m.get("net_edge_precomp") is not None for m in markets)

    lines += [
        sep,
        "  PIPE-03 Monte Carlo Pre-Game Assessment",
        "  MODE: preview (pregame JSON — hypothetical pre-deployment)",
        f"  game_date={meta.get('game_date','?')}  |  pregame_run={meta.get('run_at','?')}",
        f"  Bankroll=${bankroll:.2f}  |  T1_KELLY={kelly}  |  MIN_EDGE={min_edge}  |  N={N_SIMS:,}",
        f"  adj_lam: {'APPLIED' if adj_lam_applied else 'NOT in pregame — raw pts_l10_mean'}",
        f"  T3 signals: NEUTRAL (pre-game; PIPE-06 not yet run)",
        f"  Exit mechanics: T4 only (EXIT_MECHANICS_ACTIVE=True); not modeled in T1 MC",
    ]
    if label:
        lines.append(f"  Label: {label}")
    lines.append(sep)

    lines += ["", "BOT STATISTICS"]
    lines += [
        f"  Markets evaluated  : {n_markets}",
        f"  Bets PLACED        : {n_bets}  ({n_yes} YES  |  {n_no} NO)",
        f"  Bets REJECTED/PASS : {n_rejected}",
    ]

    if bets:
        exp_wins_total = sum(b["p_eff"] for b in bets)
        exp_losses_total = n_bets - exp_wins_total
        wins_per_sim = win_matrix.sum(axis=1)
        mean_wins = float(np.mean(wins_per_sim))

        lines += [
            f"  Bets exp. to WIN   : {exp_wins_total:.1f} / {n_bets}  ({exp_wins_total/n_bets*100:.0f}%)",
            f"  Bets exp. to LOSE  : {exp_losses_total:.1f} / {n_bets}  ({exp_losses_total/n_bets*100:.0f}%)",
            f"  MC avg bets won    : {mean_wins:.1f}  |  lost: {n_bets - mean_wins:.1f}",
            "",
            f"  Total staked       : ${total_stake:.2f}  ({deployment_pct:.1f}% of bankroll)",
            f"  Reserve (T4/T5)    : ${bankroll - total_stake:.2f}  ({100-deployment_pct:.1f}%)",
        ]
        if deployment_pct > 60.0:
            lines.append(f"  ! RESERVE MANDATE : {deployment_pct:.1f}% > 60% target.")

        lines += ["", "  Per-player breakdown:"]
        lines.append(f"  {'Player':<22} {'Bets':>5}  {'Stake':>8}  {'Exp.Win%':>9}  {'YES/NO'}")
        lines.append("  " + "-" * 62)
        player_names = sorted({b["player"] for b in bets})
        for pname in player_names:
            pb = [b for b in bets if b["player"] == pname]
            p_stake = sum(b["stake"] for b in pb)
            p_yes = sum(1 for b in pb if b["direction"] == "YES")
            p_no = sum(1 for b in pb if b["direction"] == "NO")
            p_win_pct = sum(b["p_eff"] for b in pb) / len(pb) * 100
            lines.append(
                f"  {pname:<22} {len(pb):>5}  ${p_stake:>7.2f}  {p_win_pct:>8.0f}%  {p_yes}Y/{p_no}N"
            )

        lines += ["", "  Bet-level detail:"]
        lines.append(
            f"  {'Player':<22} {'D':<4} {'Thr':>4}  {'p_mdl':>6}  {'mid':>6}  {'edge':>7}"
            f"  {'f*':>6}  {'Stake':>7}  {'WinRate':>8}"
        )
        lines.append("  " + "-" * 86)
        for pname in player_names:
            for b in [x for x in bets if x["player"] == pname]:
                lines.append(
                    f"  {b['player']:<22} {b['direction']:<4} {b['threshold']:>4}"
                    f"  {b['p_model']:.4f}  {b['mid']:.4f}  {b['edge']:>+.4f}"
                    f"  {b['f_star']:.4f}  ${b['stake']:>6.2f}  {b['p_eff']*100:>7.1f}%"
                )

        if rejected:
            lines += ["", "  Rejected / PASS:"]
            for r in rejected:
                lines.append(f"    {r['player']:<22} thr={r['threshold']:>3}  edge={r['edge']:>+.4f}  -> {r['reason']}")

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

    if n_bets:
        pcts = [1, 5, 25, 50, 75, 95, 99]
        pct_vals = np.percentile(pnl, pcts)
        prob_profit = float(np.mean(pnl > 0)) * 100
        prob_loss = float(np.mean(pnl < 0)) * 100
        prob_ks = float(np.mean(pnl <= -max_daily_loss)) * 100

        lines += [
            "",
            "MONTE CARLO P/L DISTRIBUTION",
            f"  Mean P/L           : ${np.mean(pnl):>+.2f}",
            f"  Std deviation      : ${np.std(pnl):>.2f}",
            f"  P(profit)          : {prob_profit:.1f}%",
            f"  P(loss)            : {prob_loss:.1f}%",
            f"  Kill switch risk   : {prob_ks:.2f}%  (loss >= ${max_daily_loss:.0f}; ADR-0012)",
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

    lines += [
        "",
        "GOVERNANCE",
        "  GG-004: EV compares Poisson model vs market mid — NOT adversarial.",
        "  EXP-017 is the binding commercial test.",
        "  Player scores modeled as independent Poisson draws. True P/L variance",
        "  is HIGHER due to intra-game pace correlation. P5/P95 are conservative.",
        sep,
        f"  Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"  Source     : {pregame_path.name}",
        f"  Parameters : kelly={kelly}  min_edge={min_edge}  max_exposure={max_exposure}  min_bet={min_bet}",
        sep,
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="PIPE-03 Monte Carlo Risk Assessment"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Preview mode: simulate from latest pregame JSON instead of actual portfolio"
    )
    # Portfolio mode filters
    parser.add_argument(
        "--exclude-failed", action="store_true", dest="exclude_failed",
        help="[portfolio] Exclude positions where Kalshi order failed (simulate confirmed fills only)"
    )
    parser.add_argument(
        "--yes-only", action="store_true", dest="yes_only",
        help="[portfolio] Simulate YES positions only (EXP-018 YES-drag diagnostic)"
    )
    parser.add_argument(
        "--no-only", action="store_true", dest="no_only",
        help="[portfolio] Simulate NO positions only"
    )
    parser.add_argument(
        "--haircut", type=float, default=0.0,
        help="[portfolio] Reduce all stakes by PCT%% before simulation (T-153 integration; e.g. --haircut 15)"
    )
    # Preview mode options
    parser.add_argument("--date", help="[preview] Game date YYYYMMDD (default: auto-discover latest)")
    parser.add_argument("--pregame", help="[preview] Explicit path to pregame JSON")
    parser.add_argument("--kelly", type=float, default=DEFAULT_T1_KELLY,
                        help=f"[preview] Kelly fraction override (default {DEFAULT_T1_KELLY})")
    parser.add_argument("--min-edge", type=float, default=DEFAULT_MIN_EDGE, dest="min_edge",
                        help=f"[preview] Min edge override (default {DEFAULT_MIN_EDGE})")
    parser.add_argument("--max-exposure", type=float, default=DEFAULT_MAX_EXPOSURE, dest="max_exposure",
                        help=f"[preview] Max single-bet exposure $ override (default {DEFAULT_MAX_EXPOSURE})")
    parser.add_argument("--min-bet", type=float, default=DEFAULT_MIN_BET, dest="min_bet",
                        help=f"[preview] Min bet $ floor override (default {DEFAULT_MIN_BET})")
    # Shared
    parser.add_argument("--out", help="Save report to file (also prints to stdout)")
    parser.add_argument("--label", help="Label for comparison runs")
    args = parser.parse_args()

    if args.yes_only and args.no_only:
        print("ERROR: --yes-only and --no-only are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    bankroll = _read_bankroll()

    if args.preview:
        # Preview mode
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

        report = build_preview_report(
            pregame_path, bankroll,
            kelly=args.kelly,
            min_edge=args.min_edge,
            max_exposure=args.max_exposure,
            label=args.label,
            min_bet=args.min_bet,
        )
        no_bets_check = compute_bets(
            _load_markets(pregame_path)[0], bankroll,
            args.kelly, args.min_edge, args.max_exposure, args.min_bet,
        )[0]
        has_bets = len(no_bets_check) > 0

    else:
        # Portfolio mode (default)
        direction_filter = "YES" if args.yes_only else ("NO" if args.no_only else None)
        positions, portfolio_meta = _load_portfolio(
            exclude_failed=args.exclude_failed,
            direction_filter=direction_filter,
        )
        if not portfolio_meta:
            print("ERROR: paper_portfolio.json not found. Run PIPE-03 first.", file=sys.stderr)
            sys.exit(1)

        report = build_portfolio_report(
            bankroll=bankroll,
            exclude_failed=args.exclude_failed,
            direction_filter=direction_filter,
            haircut_pct=args.haircut,
            label=args.label,
            positions=positions,
            portfolio_meta=portfolio_meta,
        )
        has_bets = len(positions) > 0

    print(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report)
        print(f"[Saved to {out_path}]", file=sys.stderr)

    if not has_bets:
        sys.exit(2)


if __name__ == "__main__":
    main()

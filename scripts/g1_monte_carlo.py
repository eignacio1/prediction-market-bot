#!/usr/bin/env python3
"""
G1 Monte Carlo Simulation — NBA Finals G1: NYK vs SAS, Jun 3 2026

Estimates P/L distribution, activity statistics, and strategic insights
for PIPE-03 T1 paper bets under Path B Poisson CDF sizing (T-129 / GG-008).

Data source: pregame_20260602.json (VPS PIPE-02, run 21:30 UTC Jun 2)
Model: p_threshold = P(score >= t) = Poisson.SF(t-1, pts_l10_mean)
Sizing: fractional Kelly with T1_KELLY=0.10, bankroll updated sequentially
Risk: ADR-0012 MAX_DAILY_LOSS_PCT=0.15 ($150 kill switch on $1,000 paper)

Usage:
    PYTHONPATH=src python3 scripts/g1_monte_carlo.py

Requirements: scipy (already in project venv)
"""

import sys
import numpy as np
from scipy.stats import poisson, norm
from dataclasses import dataclass, field
from typing import List

# ---------------------------------------------------------------------------
# Constants (mirror PIPE-03 / C4 hard limits)
# ---------------------------------------------------------------------------
N_SIMS = 10_000
SEED = 42
T1_KELLY = 0.10
MIN_EDGE = 0.02
MIN_BET_USD = 10.0
MAX_EXPOSURE_USD = 500.0
INITIAL_BANKROLL = 1000.0
MAX_DAILY_LOSS_USD = 150.0  # ADR-0012: 15% of $1,000
RESERVE_MANDATE_PCT = 0.40   # advisory at paper scale

# ---------------------------------------------------------------------------
# Market data — pregame_20260602.json (VPS PIPE-02, 2026-06-02T21:30Z)
# Columns: player, pts_l10_mean (lambda), threshold, mid_price, vig
# ---------------------------------------------------------------------------
RAW_MARKETS = [
    ("De'Aaron Fox",        15.0,  10, 0.840, 0.060),
    ("De'Aaron Fox",        15.0,  15, 0.575, 0.010),
    ("De'Aaron Fox",        15.0,  20, 0.275, 0.010),
    ("De'Aaron Fox",        15.0,  25, 0.105, 0.010),
    ("Devin Vassell",       13.6,  10, 0.765, 0.010),
    ("Devin Vassell",       13.6,  15, 0.415, 0.010),
    ("Devin Vassell",       13.6,  20, 0.175, 0.010),
    ("Devin Vassell",       13.6,  25, 0.065, 0.010),
    ("Jalen Brunson",       24.4,  20, 0.780, 0.020),
    ("Jalen Brunson",       24.4,  25, 0.545, 0.010),
    ("Jalen Brunson",       24.4,  30, 0.285, 0.010),
    ("Jalen Brunson",       24.4,  35, 0.125, 0.010),
    ("Josh Hart",           12.6,  10, 0.665, 0.010),
    ("Josh Hart",           12.6,  15, 0.300, 0.020),
    ("Josh Hart",           12.6,  20, 0.100, 0.020),
    ("Karl-Anthony Towns",  20.2,  10, 0.875, 0.070),
    ("Karl-Anthony Towns",  20.2,  15, 0.645, 0.010),
    ("Karl-Anthony Towns",  20.2,  20, 0.350, 0.020),
    ("Karl-Anthony Towns",  20.2,  25, 0.135, 0.030),
    ("Mikal Bridges",       13.8,  10, 0.790, 0.040),
    ("Mikal Bridges",       13.8,  15, 0.495, 0.010),
    ("Mikal Bridges",       13.8,  20, 0.205, 0.010),
    ("Mikal Bridges",       13.8,  25, 0.065, 0.010),
    ("OG Anunoby",          17.2,  10, 0.850, 0.020),
    ("OG Anunoby",          17.2,  15, 0.570, 0.020),
    ("OG Anunoby",          17.2,  20, 0.280, 0.040),
    ("OG Anunoby",          17.2,  25, 0.125, 0.010),
    ("Stephon Castle",      19.2,  15, 0.655, 0.010),
    ("Stephon Castle",      19.2,  20, 0.325, 0.010),
    ("Stephon Castle",      19.2,  25, 0.135, 0.010),
    ("Stephon Castle",      19.2,  30, 0.055, 0.010),
    ("Victor Wembanyama",   25.8,  25, 0.635, 0.010),
    ("Victor Wembanyama",   25.8,  30, 0.395, 0.010),
    ("Victor Wembanyama",   25.8,  35, 0.185, 0.010),
    ("Victor Wembanyama",   25.8,  40, 0.095, 0.010),
]


# ---------------------------------------------------------------------------
# Bet computation (mirrors run_paper_trade.py + risk.py _compute_kelly_size)
# ---------------------------------------------------------------------------
@dataclass
class Bet:
    player: str
    lam: float          # pts_l10_mean (Poisson lambda)
    threshold: int
    direction: str      # YES or NO
    p_model: float      # P(score >= threshold) under Poisson(lam)
    p_eff: float        # effective model prob for the bet side
    mip_eff: float      # effective market implied prob for the bet side
    mid: float
    vig: float
    edge: float         # signed YES edge
    f_star: float       # full Kelly fraction
    stake: float        # approved stake ($)
    win_odds: float     # net profit per $1 staked if win


def _poisson_sf(t: int, lam: float) -> float:
    """P(X >= t) under Poisson(lam). Matches _poisson_cdf in game_state_model.py."""
    return float(poisson.sf(t - 1, lam))


def compute_bets(bankroll: float = INITIAL_BANKROLL) -> List[Bet]:
    """
    Replicate PIPE-03 T1 Path B bet selection + Kelly sizing.
    Sequential bankroll update matches engine re-instantiation in run_paper_trade.py.
    """
    bets = []
    current_bankroll = bankroll

    for player, lam, threshold, mid, vig in RAW_MARKETS:
        half = vig / 2.0
        p_model = _poisson_sf(threshold, lam)
        edge = p_model - mid - half

        if edge > MIN_EDGE:
            direction = "YES"
        elif edge < -MIN_EDGE:
            direction = "NO"
        else:
            continue  # PASS — mirrors EDGE_YES/EDGE_NO thresholds in run_paper_trade.py

        if direction == "YES":
            p_eff, mip_eff = p_model, mid
        else:
            p_eff, mip_eff = 1.0 - p_model, 1.0 - mid

        b = (1.0 - mip_eff) / mip_eff
        q = 1.0 - p_eff
        f_star = (p_eff * b - q) / b
        if f_star <= 0.0:
            continue

        stake = min(f_star * T1_KELLY * current_bankroll, MAX_EXPOSURE_USD)
        if stake < MIN_BET_USD:
            continue

        win_odds = (1.0 - mip_eff) / mip_eff

        bets.append(Bet(
            player=player, lam=lam, threshold=threshold, direction=direction,
            p_model=p_model, p_eff=p_eff, mip_eff=mip_eff,
            mid=mid, vig=vig, edge=edge, f_star=f_star, stake=stake,
            win_odds=win_odds,
        ))
        current_bankroll -= stake  # sequential bankroll reduction

    return bets


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def simulate(bets: List[Bet], n_sims: int = N_SIMS, seed: int = SEED) -> np.ndarray:
    """
    Monte Carlo: sample Poisson scores for each player, resolve bets.
    Returns array of per-simulation P/L in dollars.

    Bets are assumed to be independent draws from Poisson(lam).
    Note: intra-game pace correlation is ignored; see INSIGHTS section.
    """
    rng = np.random.default_rng(seed)

    # Build per-player lambda map; sample player scores once per sim
    players = list({b.player for b in bets})
    lambda_map = {b.player: b.lam for b in bets}

    # Shape: (n_sims, n_players)
    scores = {
        player: rng.poisson(lambda_map[player], size=n_sims)
        for player in players
    }

    pnl = np.zeros(n_sims)
    for bet in bets:
        player_scores = scores[bet.player]
        if bet.direction == "YES":
            wins = player_scores >= bet.threshold
        else:
            wins = player_scores < bet.threshold

        pnl += np.where(wins, bet.stake * bet.win_odds, -bet.stake)

    return pnl


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def print_section(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print('=' * 65)


def print_bet_table(bets: List[Bet]) -> None:
    header = f"{'Player':<22} {'Dir':<4} {'Thr':>4} {'p_mdl':>6} {'mid':>6} {'edge':>7} {'f*':>6} {'Stake':>7}"
    print(header)
    print('-' * len(header))
    for b in bets:
        print(
            f"{b.player:<22} {b.direction:<4} {b.threshold:>4}  "
            f"{b.p_model:.4f} {b.mid:.4f} {b.edge:+.4f} {b.f_star:.4f} ${b.stake:>6.2f}"
        )


def main() -> None:
    print("G1 Monte Carlo Simulation — NYK vs SAS, Jun 3 2026")
    print(f"Model: Poisson CDF Path B (T-129 / GG-008)  |  T1_KELLY={T1_KELLY}  |  N={N_SIMS:,}")
    print(f"Bankroll: ${INITIAL_BANKROLL:.2f}  |  Kill switch: ${MAX_DAILY_LOSS_USD:.2f} loss")

    # -----------------------------------------------------------------------
    # 1. Activity Statistics
    # -----------------------------------------------------------------------
    bets = compute_bets()
    print_section("1. ACTIVITY STATISTICS")

    n_markets = len(RAW_MARKETS)
    n_bets = len(bets)
    n_yes = sum(1 for b in bets if b.direction == "YES")
    n_no  = sum(1 for b in bets if b.direction == "NO")
    total_stake = sum(b.stake for b in bets)
    deployment_pct = total_stake / INITIAL_BANKROLL * 100

    print(f"Markets evaluated   : {n_markets}")
    print(f"Bets approved       : {n_bets}  ({n_yes} YES, {n_no} NO)")
    print(f"PASS / rejected     : {n_markets - n_bets}")
    print(f"Total staked        : ${total_stake:.2f}")
    print(f"Deployment %        : {deployment_pct:.1f}% of $1,000 bankroll")
    print(f"Reserve remaining   : ${INITIAL_BANKROLL - total_stake:.2f}  "
          f"({100 - deployment_pct:.1f}%)")

    print(f"\nPer-player breakdown:")
    players = sorted({b.player for b in bets})
    for player in players:
        player_bets = [b for b in bets if b.player == player]
        player_stake = sum(b.stake for b in player_bets)
        print(f"  {player:<22}  {len(player_bets)} bets  ${player_stake:.2f}")

    print(f"\nAll approved bets:")
    print_bet_table(bets)

    # -----------------------------------------------------------------------
    # 2. Expected Value (regression / analytical)
    # -----------------------------------------------------------------------
    print_section("2. EXPECTED VALUE (ANALYTICAL)")

    ev_list = []
    for b in bets:
        ev = b.stake * (b.p_eff * b.win_odds - (1.0 - b.p_eff))
        ev_list.append((b.player, b.threshold, b.direction, b.stake, b.edge, ev))

    total_ev = sum(e[-1] for e in ev_list)
    print(f"{'Player':<22} {'D':<4} {'Thr':>4}  {'Stake':>7}  {'Edge':>7}  {'EV':>8}")
    print('-' * 62)
    for player, thr, direction, stake, edge, ev in ev_list:
        print(f"{player:<22} {direction:<4} {thr:>4}  ${stake:>6.2f}  {edge:>+.4f}  ${ev:>+7.3f}")
    print('-' * 62)
    print(f"{'TOTAL EV':<44}  ${total_ev:>+7.3f}")
    print(f"\nExpected ROI on deployed capital: {total_ev / total_stake * 100:+.2f}%")
    print(f"Expected ROI on total bankroll:   {total_ev / INITIAL_BANKROLL * 100:+.2f}%")

    # -----------------------------------------------------------------------
    # 3. Monte Carlo P/L Distribution
    # -----------------------------------------------------------------------
    print_section("3. MONTE CARLO P/L DISTRIBUTION (N=10,000)")

    pnl = simulate(bets)

    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct_vals = np.percentile(pnl, percentiles)

    print(f"Mean P/L            : ${np.mean(pnl):>+.2f}")
    print(f"Std deviation       : ${np.std(pnl):>.2f}")
    print()
    print("Percentile distribution:")
    for p, v in zip(percentiles, pct_vals):
        bar = '#' * int(max(0, v + total_stake) / (total_stake * 2) * 40)
        print(f"  p{p:>2}  ${v:>+8.2f}")

    print()
    prob_profit = np.mean(pnl > 0) * 100
    prob_loss   = np.mean(pnl < 0) * 100
    prob_breakeven = np.mean(pnl == 0) * 100
    print(f"P(profit)     : {prob_profit:.1f}%")
    print(f"P(loss)       : {prob_loss:.1f}%")
    print(f"Expected value: ${np.mean(pnl):+.2f}  (MC verify; analytical above)")

    # Kill switch risk
    print()
    kill_switch_pnl = -MAX_DAILY_LOSS_USD
    prob_ks = np.mean(pnl <= kill_switch_pnl) * 100
    print(f"Kill switch threshold  : -${MAX_DAILY_LOSS_USD:.2f}")
    print(f"P(kill switch fires)   : {prob_ks:.1f}%  (loss >= ${MAX_DAILY_LOSS_USD:.2f})")
    print(f"Worst 1% outcome       : ${np.percentile(pnl, 1):+.2f}")
    print(f"Worst single outcome   : ${np.min(pnl):+.2f}")
    print(f"Best single outcome    : ${np.max(pnl):+.2f}")

    # Ending bankroll distribution
    ending_br = INITIAL_BANKROLL + pnl
    print()
    print("Ending bankroll distribution:")
    print(f"  Mean  : ${np.mean(ending_br):.2f}")
    print(f"  p5    : ${np.percentile(ending_br, 5):.2f}")
    print(f"  p25   : ${np.percentile(ending_br, 25):.2f}")
    print(f"  p50   : ${np.percentile(ending_br, 50):.2f}")
    print(f"  p75   : ${np.percentile(ending_br, 75):.2f}")
    print(f"  p95   : ${np.percentile(ending_br, 95):.2f}")

    # -----------------------------------------------------------------------
    # 4. Insights
    # -----------------------------------------------------------------------
    print_section("4. INSIGHTS")

    # Edge concentration
    edges = [(b.edge, b.player, b.threshold, b.direction, b.stake) for b in bets]
    edges.sort(key=lambda x: abs(x[0]), reverse=True)

    print("Top 5 highest-edge bets (Path B Poisson model):")
    for i, (edge, player, thr, direction, stake) in enumerate(edges[:5]):
        print(f"  {i+1}. {player} {direction} {thr}+  edge={edge:+.4f}  stake=${stake:.2f}")

    # Vig analysis
    yes_bets = [b for b in bets if b.direction == "YES"]
    no_bets  = [b for b in bets if b.direction == "NO"]
    avg_vig = np.mean([b.vig for b in bets])
    print(f"\nVig analysis:")
    print(f"  Avg vig across approved bets : {avg_vig:.4f}")
    print(f"  Total vig drag (half-spread) : ${sum(b.vig/2 * b.stake for b in bets):.2f}")

    # Kelly concentration
    max_stake_bet = max(bets, key=lambda b: b.stake)
    print(f"\nLargest single bet:")
    print(f"  {max_stake_bet.player} {max_stake_bet.direction} {max_stake_bet.threshold}+  "
          f"stake=${max_stake_bet.stake:.2f}  f*={max_stake_bet.f_star:.4f}  "
          f"= {max_stake_bet.stake/INITIAL_BANKROLL*100:.1f}% of bankroll")

    # Path B vs LR alignment warning
    print(f"\nPath B vs LR divergence:")
    print(f"  Path B uses Poisson CDF per threshold — p_model varies significantly")
    print(f"  across thresholds (unlike LR which gave same p_est for all thresholds)")
    print(f"  of a given player). Key divergences:")
    for player, lam, threshold, mid, vig in RAW_MARKETS:
        p_poisson = _poisson_sf(threshold, lam)
        half = vig / 2.0
        edge_poisson = p_poisson - mid - half
        # LR p_est is same for all thresholds: from pregame data
    # Show players where Poisson flips direction vs LR
    lr_p_map = {  # from pregame_20260602.json p_estimate field
        "De'Aaron Fox": 0.5667,
        "Devin Vassell": 0.4963,
        "Jalen Brunson": 0.5103,
        "Josh Hart": 0.5068,
        "Karl-Anthony Towns": 0.4710,
        "Mikal Bridges": 0.4888,
        "OG Anunoby": 0.4821,
        "Stephon Castle": 0.5002,
        "Victor Wembanyama": 0.4629,
    }
    flips = []
    for player, lam, threshold, mid, vig in RAW_MARKETS:
        half = vig / 2.0
        p_poisson = _poisson_sf(threshold, lam)
        p_lr = lr_p_map.get(player, 0.5)
        edge_poisson = p_poisson - mid - half
        edge_lr = p_lr - mid - half
        dir_poisson = "YES" if edge_poisson > MIN_EDGE else ("NO" if edge_poisson < -MIN_EDGE else "PASS")
        dir_lr = "YES" if edge_lr > MIN_EDGE else ("NO" if edge_lr < -MIN_EDGE else "PASS")
        if dir_poisson != dir_lr:
            flips.append(f"    {player} thr={threshold}: LR→{dir_lr} | Poisson→{dir_poisson} "
                         f"(p_lr={p_lr:.3f} p_poi={p_poisson:.3f})")
    if flips:
        for f in flips:
            print(f)
    else:
        print("    No direction flips between LR and Poisson models for G1 markets.")

    # Reserve mandate warning
    print()
    print("Reserve mandate (IMPORTANT — batch deployment):")
    reserve_remaining = INITIAL_BANKROLL - total_stake
    reserve_pct = reserve_remaining / INITIAL_BANKROLL * 100
    print(f"  RESERVE_MANDATE_PCT=0.40 targets ≤60% deployment per batch.")
    print(f"  Actual T1 batch deployment: {deployment_pct:.1f}% (${total_stake:.2f})")
    print(f"  Remaining for T4/T5:        {reserve_pct:.1f}% (${reserve_remaining:.2f})")
    if deployment_pct > 60.0:
        print(f"  ⚠ EXCEEDS 60% target. T4/T5 capital is constrained.")
        print(f"    Batch-level enforcement deferred per SESSION 15 — ADR-0011.")
        print(f"    Per-bet advisory only fires when single bet > 60% of current bankroll.")
        print(f"    No single T1 bet triggered it. Batch aggregation is the gap.")

    # Correlation warning
    print()
    print("Correlation note (key limitation):")
    print("  Bets are modeled as independent Poisson draws. In practice, game")
    print("  pace affects all players simultaneously (positive correlation for")
    print("  same-team bets like NYK: Brunson/Hart/Bridges/Anunoby/Towns, or")
    print("  SAS: Fox/Vassell/Wembanyama/Castle). High-pace games help ALL")
    print("  YES bets and hurt ALL NO bets. True P/L variance is likely HIGHER")
    print("  than reported above. Treat P5/P95 as conservative bounds.")

    # GG-004 warning
    print()
    print("GG-004 reminder:")
    print("  All EV figures above compare model vs Poisson(pts_l10_mean) — not")
    print("  vs actual Kalshi market prices in an adversarial sense. EXP-017")
    print("  Part B (n=2 directional positive, floor ≥66) is the binding test.")
    print("  Do not claim commercial viability from this simulation alone.")

    # -----------------------------------------------------------------------
    # 5. Summary
    # -----------------------------------------------------------------------
    print_section("SUMMARY")
    print(f"  Bets to be placed    : {n_bets} across {len(players)} players")
    print(f"  Total stake          : ${total_stake:.2f}  ({deployment_pct:.1f}% deployed)")
    print(f"  Expected P/L         : ${total_ev:+.2f}  (analytical)")
    print(f"  MC mean P/L          : ${np.mean(pnl):+.2f}")
    print(f"  Win probability      : {prob_profit:.1f}%")
    print(f"  Kill switch risk     : {prob_ks:.1f}%")
    print(f"  Best case (p99)      : ${np.percentile(pnl, 99):+.2f}")
    print(f"  Worst case (p1)      : ${np.percentile(pnl, 1):+.2f}")
    print()
    print(f"  Source: pregame_20260602.json | Run: 2026-06-02T21:30Z")
    print(f"  Simulation seed: {SEED} | Path B Poisson CDF (ADR-0010/T-129)")


if __name__ == "__main__":
    main()

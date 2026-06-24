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
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import NamedTuple, Optional

# ── Constants ──────────────────────────────────────────────────────────────────

ADR_0024_TIER1_N          = 150    # ADR-0024: Tier 1 minimum sample
ADR_0024_TIER1_DIAG_EV    = -0.03  # Tier 1 diagnostic sprint threshold (EV/bet < -$0.03)
ADR_0024_TIER2_N_SINGLE   = 500    # Tier 2 single-sport floor
ADR_0024_TIER2_N_MULTI    = 150    # Tier 2 multi-sport floor (per sport, requires --nba-n)
ADR_0024_P_THRESHOLD      = 0.05   # significance level for CONFIRMED_* verdicts
KALSHI_FEE_RATE           = 0.07   # taker fee: 0.07 × mip × (1 - mip)
MIN_N                     = 20     # minimum positions for any verdict
SPORT                     = "mlb"
DEFAULT_PORTFOLIO         = Path("logs/paper_portfolio_mlb.json")
OUT_DIR                   = Path("exp_output/EXP-017-MLB")

# EV verdict strings
V_CONF_POS   = "CONFIRMED_POSITIVE"
V_DIR_POS    = "DIRECTIONAL_POSITIVE"
V_CONF_NEG   = "CONFIRMED_NEGATIVE"
V_DIR_NEG    = "DIRECTIONAL_NEGATIVE"
V_DIAG       = "DIAGNOSTIC_SPRINT"
V_INC        = "INCONCLUSIVE"

# Edge monotonicity verdict strings
E_ANTI = "ANTI-PREDICTIVE"
E_MONO = "MONOTONIC"
E_INC  = "INCONCLUSIVE"

# ── scipy optional ─────────────────────────────────────────────────────────────

try:
    from scipy.stats import fisher_exact
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False


# ── Data model ─────────────────────────────────────────────────────────────────

class MLBPosition(NamedTuple):
    kalshi_ticker:  str
    direction:      str    # "YES" or "NO"
    mip:            float  # mid_price_at_entry
    vig:            float  # vig_at_entry
    model_p:        float  # LR+Platt probability for YES
    fee_net_edge:   float  # signed edge minus Kalshi fee
    outcome:        str    # "WIN" or "LOSS"
    pnl:            float  # realized P&L in USD (from position)
    game_date:      str
    threshold:      int    # 1, 2, or 3
    player_name:    str


# ── Fee and edge helpers ────────────────────────────────────────────────────────

def kalshi_fee(mip: float) -> float:
    """Kalshi taker fee per dollar of YES contract: 0.07 × mip × (1 − mip)."""
    return KALSHI_FEE_RATE * mip * (1.0 - mip)


def compute_fee_net_edge(direction: str, model_p: float, mip: float) -> float:
    """
    Fee-net edge: model advantage over market price minus Kalshi taker fee.
    YES: model thinks p_yes = model_p; market charges mip.  edge = model_p − mip − fee
    NO:  model thinks p_yes < mip; bets NO.                 edge = mip − model_p − fee
    """
    fee = kalshi_fee(mip)
    if direction == "YES":
        return model_p - mip - fee
    else:
        return mip - model_p - fee


def compute_pnl_unit(direction: str, mip: float, vig: float, won: bool) -> float:
    """Realized P&L per unit bet (consistent with EXP-018 methodology)."""
    half_vig = vig / 2.0
    if direction == "YES":
        price_paid = mip + half_vig
        return (1.0 - price_paid) if won else -price_paid
    else:
        price_paid = (1.0 - mip) + half_vig
        return (1.0 - price_paid) if won else -price_paid


# ── Loaders ────────────────────────────────────────────────────────────────────

def _load_portfolio(
    path: Path,
    exclude_duplicates: bool = True,
) -> list[MLBPosition]:
    """Load closed MLB positions from a paper portfolio JSON."""
    with open(path) as fh:
        data = json.load(fh)
    positions: list[MLBPosition] = []
    for p in data.get("closed_positions", []):
        if exclude_duplicates and p.get("duplicate_of"):
            continue
        outcome = p.get("outcome", "")
        if outcome not in ("WIN", "LOSS"):
            continue
        raw_model_p = p.get("model_p")
        if raw_model_p is None:
            continue
        try:
            model_p = float(raw_model_p)
            mip     = float(p["mid_price_at_entry"])
            vig     = float(p.get("vig_at_entry", 0.0))
        except (KeyError, TypeError, ValueError):
            continue
        direction = str(p.get("direction", "YES"))
        raw_edge = p.get("fee_net_edge")
        if raw_edge is not None:
            try:
                fee_net_edge = float(raw_edge)
            except (TypeError, ValueError):
                fee_net_edge = compute_fee_net_edge(direction, model_p, mip)
        else:
            fee_net_edge = compute_fee_net_edge(direction, model_p, mip)
        pnl = float(p.get("pnl", 0.0) or 0.0)
        try:
            threshold = int(p.get("threshold", 0))
        except (TypeError, ValueError):
            threshold = 0
        positions.append(MLBPosition(
            kalshi_ticker=str(p.get("kalshi_ticker", "")),
            direction=direction,
            mip=mip,
            vig=vig,
            model_p=model_p,
            fee_net_edge=fee_net_edge,
            outcome=outcome,
            pnl=pnl,
            game_date=str(p.get("game_date", "")),
            threshold=threshold,
            player_name=str(p.get("player_name", "")),
        ))
    return positions


def _load_csv(
    path: Path,
    exclude_duplicates: bool = True,
) -> list[MLBPosition]:
    """Load positions from a resolved-bet CSV (batch backtest mode)."""
    positions: list[MLBPosition] = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            if exclude_duplicates and row.get("duplicate_of", "").strip():
                continue
            outcome = row.get("outcome", "").strip().upper()
            if outcome not in ("WIN", "LOSS"):
                continue
            raw_model_p = row.get("model_p", "").strip()
            if not raw_model_p:
                continue
            try:
                model_p = float(raw_model_p)
                mip     = float(row["mid_price_at_entry"])
                vig     = float(row.get("vig_at_entry") or 0.0)
            except (KeyError, TypeError, ValueError):
                continue
            direction = str(row.get("direction", "YES")).strip()
            raw_edge = row.get("fee_net_edge", "").strip()
            if raw_edge:
                try:
                    fee_net_edge = float(raw_edge)
                except ValueError:
                    fee_net_edge = compute_fee_net_edge(direction, model_p, mip)
            else:
                fee_net_edge = compute_fee_net_edge(direction, model_p, mip)
            try:
                pnl = float(row.get("pnl") or 0.0)
            except (TypeError, ValueError):
                pnl = 0.0
            try:
                threshold = int(row.get("threshold") or 0)
            except (TypeError, ValueError):
                threshold = 0
            positions.append(MLBPosition(
                kalshi_ticker=str(row.get("kalshi_ticker", "")),
                direction=direction,
                mip=mip,
                vig=vig,
                model_p=model_p,
                fee_net_edge=fee_net_edge,
                outcome=outcome,
                pnl=pnl,
                game_date=str(row.get("game_date", "")),
                threshold=threshold,
                player_name=str(row.get("player_name", "")),
            ))
    return positions


# ── Deduplication ──────────────────────────────────────────────────────────────

def deduplicate(positions: list[MLBPosition]) -> list[MLBPosition]:
    """Return one position per unique kalshi_ticker (earliest entry wins)."""
    seen: set[str] = set()
    unique: list[MLBPosition] = []
    for p in positions:
        if p.kalshi_ticker not in seen:
            seen.add(p.kalshi_ticker)
            unique.append(p)
    return unique


# ── EV computation ─────────────────────────────────────────────────────────────

def ev_stats(positions: list[MLBPosition]) -> dict:
    """Compute EV/bet and win-rate from realized P&L."""
    if not positions:
        return {"n": 0, "ev_per_bet": 0.0, "win_rate": 0.0, "total_pnl": 0.0}
    n = len(positions)
    wins = sum(1 for p in positions if p.outcome == "WIN")
    total_pnl = sum(p.pnl for p in positions)
    return {
        "n": n,
        "ev_per_bet": total_pnl / n,
        "win_rate": wins / n,
        "total_pnl": total_pnl,
    }


# ── Threshold breakdown ────────────────────────────────────────────────────────

def threshold_breakdown(positions: list[MLBPosition]) -> list[dict]:
    """EV and win-rate broken down by KXMLBHIT threshold (k=1,2,3)."""
    buckets: dict[int, list[MLBPosition]] = {}
    for p in positions:
        buckets.setdefault(p.threshold, []).append(p)
    rows = []
    for k in sorted(buckets):
        stats = ev_stats(buckets[k])
        rows.append({"threshold": k, **stats})
    return rows


# ── ADR-0024 tier check ────────────────────────────────────────────────────────

def adr0024_tier(n_mlb: int, ev_per_bet: float, nba_n: int = 0) -> dict:
    """
    Returns ADR-0024 tier status and action flag.

    nba_n: number of unique resolved NBA markets (for multi-sport Tier 2).
           Pass 0 if NBA data is not available / not yet adequate.
    """
    at_tier1 = n_mlb >= ADR_0024_TIER1_N
    at_tier2_single = n_mlb >= ADR_0024_TIER2_N_SINGLE
    at_tier2_multi  = (n_mlb >= ADR_0024_TIER2_N_MULTI and nba_n >= ADR_0024_TIER2_N_MULTI)
    at_tier2 = at_tier2_single or at_tier2_multi

    diagnostic_sprint = at_tier1 and (ev_per_bet < ADR_0024_TIER1_DIAG_EV)

    return {
        "at_tier1": at_tier1,
        "at_tier2": at_tier2,
        "at_tier2_single": at_tier2_single,
        "at_tier2_multi": at_tier2_multi,
        "diagnostic_sprint": diagnostic_sprint,
        "nba_n": nba_n,
    }


# ── EV verdict ─────────────────────────────────────────────────────────────────

def ev_verdict(
    n_unique: int,
    ev_per_bet: float,
    tier: dict,
    fisher_pvalue: float,
) -> str:
    """Map (n, EV, tier, p-value) to an EV verdict string."""
    if n_unique < MIN_N:
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
    # Below Tier 2
    if ev_per_bet > 0:
        return V_DIR_POS
    if ev_per_bet < 0:
        return V_DIR_NEG
    return V_INC


# ── Fisher's exact / chi-squared ───────────────────────────────────────────────

def _fisher_pvalue(
    pos_group: list[MLBPosition],
    neg_group: list[MLBPosition],
) -> tuple[float, float]:
    """Fisher's exact (or chi-squared approximation) for edge>0 vs edge<=0."""
    a = sum(1 for p in pos_group if p.outcome == "WIN")
    b = len(pos_group) - a
    c = sum(1 for p in neg_group if p.outcome == "WIN")
    d = len(neg_group) - c
    if _HAS_SCIPY:
        or_, pval = fisher_exact([[a, b], [c, d]], alternative="two-sided")
        return (float(or_), float(pval))
    # chi-squared approximation (scipy unavailable)
    n = a + b + c + d
    if n == 0:
        return (1.0, 1.0)
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    e_a = r1 * c1 / n if n > 0 else 0
    e_b = r1 * c2 / n if n > 0 else 0
    e_c = r2 * c1 / n if n > 0 else 0
    e_d = r2 * c2 / n if n > 0 else 0
    chi2 = sum(
        (o - e) ** 2 / e if e > 0 else 0.0
        for o, e in [(a, e_a), (b, e_b), (c, e_c), (d, e_d)]
    )
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
    or_ = (a * d) / (b * c) if (b > 0 and c > 0) else float("inf")
    return (or_, approx_p)


# ── Edge monotonicity analysis ─────────────────────────────────────────────────

def _tercile_table(positions: list[MLBPosition]) -> list[dict]:
    if not positions:
        return []
    sorted_pos = sorted(positions, key=lambda p: p.fee_net_edge)
    n = len(sorted_pos)
    chunks = [sorted_pos[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    if n % 3 != 0:
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
            "winrate": sum(1 for p in chunk if p.outcome == "WIN") / len(chunk),
            "pnl": sum(p.pnl for p in chunk),
        })
    return rows


def edge_monotonicity(
    positions: list[MLBPosition],
    alpha: float = 0.10,
) -> dict:
    """T-177 / GG-037 guard: does fee_net_edge predict outcomes?"""
    n = len(positions)
    if n < MIN_N:
        return {"verdict": E_INC, "reason": f"n={n} < MIN_N={MIN_N}"}
    pos_group = [p for p in positions if p.fee_net_edge > 0]
    neg_group = [p for p in positions if p.fee_net_edge <= 0]
    wr_pos = sum(1 for p in pos_group if p.outcome == "WIN") / len(pos_group) if pos_group else float("nan")
    wr_neg = sum(1 for p in neg_group if p.outcome == "WIN") / len(neg_group) if neg_group else float("nan")
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
        "verdict": verdict,
        "n": n,
        "n_pos_edge": len(pos_group),
        "n_neg_edge": len(neg_group),
        "winrate_edge_pos": wr_pos,
        "winrate_edge_neg": wr_neg,
        "fisher_odds_ratio": or_,
        "fisher_pvalue": pval,
        "alpha": alpha,
        "terciles": _tercile_table(positions),
    }


# ── Main analysis ──────────────────────────────────────────────────────────────

def analyse(
    positions: list[MLBPosition],
    alpha: float = 0.10,
    nba_n: int = 0,
    label: str = "",
) -> dict:
    """Full EXP-017 MLB analysis. Returns a result dict."""
    unique = deduplicate(positions)
    n_unique = len(unique)
    stats = ev_stats(unique)

    mono = edge_monotonicity(unique, alpha=alpha)
    fisher_pvalue = mono.get("fisher_pvalue", 1.0)

    tier = adr0024_tier(n_unique, stats["ev_per_bet"], nba_n=nba_n)
    verdict = ev_verdict(n_unique, stats["ev_per_bet"], tier, fisher_pvalue)

    by_direction: dict[str, list[MLBPosition]] = {"YES": [], "NO": []}
    for p in unique:
        by_direction.get(p.direction, by_direction["YES"]).append(p)
    ev_yes = ev_stats(by_direction["YES"])
    ev_no  = ev_stats(by_direction["NO"])

    thr_rows = threshold_breakdown(unique)

    return {
        "label": label,
        "sport": SPORT,
        "n_total_positions": len(positions),
        "n_unique_markets": n_unique,
        "at_tier1": tier["at_tier1"],
        "at_tier2": tier["at_tier2"],
        "tier_detail": tier,
        "ev_per_bet": stats["ev_per_bet"],
        "win_rate": stats["win_rate"],
        "total_pnl": stats["total_pnl"],
        "ev_yes": ev_yes,
        "ev_no": ev_no,
        "threshold_breakdown": thr_rows,
        "edge_monotonicity": mono,
        "verdict": verdict,
        "adr": "ADR-0024",
        "gg": "GG-004",
    }


# ── Reporting ──────────────────────────────────────────────────────────────────

def _print_report(result: dict) -> None:
    sep = "=" * 68
    print(sep)
    print("EXP-017 MLB — Commercial Validation vs Kalshi KXMLBHIT Prices")
    print("ADR-0024 | GG-004 | T-184")
    print(sep)
    if result.get("label"):
        print(f"  Source:   {result['label']}")
    n_unique = result["n_unique_markets"]
    ev = result["ev_per_bet"]
    wr = result["win_rate"]
    print(f"  Unique markets: {n_unique}   "
          f"(total positions: {result['n_total_positions']})")
    print(f"  EV/bet: ${ev:+.4f}   win_rate: {wr:.3f}")
    print(f"  Total P&L: ${result['total_pnl']:+.2f}")
    print()
    # ADR-0024 tier
    t1 = result["at_tier1"]
    t2 = result["at_tier2"]
    print("── ADR-0024 Tier Status ─────────────────────────────────────")
    print(f"  Tier 1 (n >= {ADR_0024_TIER1_N}):  {'REACHED' if t1 else f'NOT YET ({n_unique}/{ADR_0024_TIER1_N})'}")
    td = result["tier_detail"]
    if t1:
        print(f"  Tier 1 diagnostic: EV < -$0.03?  {td['diagnostic_sprint']}")
    print(f"  Tier 2 single (n>={ADR_0024_TIER2_N_SINGLE}): {'YES' if td['at_tier2_single'] else f'NOT YET ({n_unique}/{ADR_0024_TIER2_N_SINGLE})'}")
    nba_n_str = td["nba_n"]
    print(f"  Tier 2 multi  (MLB n>={ADR_0024_TIER2_N_MULTI} AND NBA n>={ADR_0024_TIER2_N_MULTI}): "
          f"{'YES' if td['at_tier2_multi'] else 'NOT YET (NBA n=' + str(nba_n_str) + ')'}")
    print()
    # Direction split
    ey = result["ev_yes"]
    en = result["ev_no"]
    print("── Direction Split ──────────────────────────────────────────")
    print(f"  YES: EV=${ey['ev_per_bet']:+.4f}/bet  win={ey['win_rate']:.3f}  n={ey['n']}")
    print(f"  NO:  EV=${en['ev_per_bet']:+.4f}/bet  win={en['win_rate']:.3f}  n={en['n']}")
    print()
    # Threshold breakdown
    if result["threshold_breakdown"]:
        print("── Threshold Breakdown (k=1: 1+hits, k=2: 2+hits, k=3: 3+hits) ─")
        for row in result["threshold_breakdown"]:
            k = row["threshold"]
            label = f"k={k}" if k in (1, 2, 3) else f"k={k}(?)"
            print(f"  {label}: EV=${row['ev_per_bet']:+.4f}/bet  "
                  f"win={row['win_rate']:.3f}  n={row['n']}  P&L=${row['total_pnl']:+.2f}")
        print()
    # Edge monotonicity
    mono = result["edge_monotonicity"]
    print("── Edge Monotonicity (T-177 / GG-037 guard) ────────────────")
    if "reason" in mono:
        print(f"  {mono['verdict']} — {mono['reason']}")
    else:
        print(f"  edge>0  winrate={mono['winrate_edge_pos']:.3f}  (n={mono['n_pos_edge']})")
        print(f"  edge<=0 winrate={mono['winrate_edge_neg']:.3f}  (n={mono['n_neg_edge']})")
        print(f"  Fisher: OR={mono['fisher_odds_ratio']:.3f}  p={mono['fisher_pvalue']:.4f}  "
              f"(alpha={mono['alpha']})")
        if mono["terciles"]:
            print("  Terciles (low→high fee_net_edge):")
            for t in mono["terciles"]:
                print(f"    T{t['tercile']}: edge[{t['edge_min']:+.4f},{t['edge_max']:+.4f}]"
                      f"  n={t['n']:3d}  winrate={t['winrate']:.3f}  P&L=${t['pnl']:+.2f}")
        print(f"  Monotonicity: {mono['verdict']}")
    print()
    # Final verdict
    print("── Verdict ──────────────────────────────────────────────────")
    verdict = result["verdict"]
    print(f"  {verdict}")
    if verdict == V_CONF_POS:
        print("  GG-004 CLOSEABLE: positive EV at adequate sample (p < 0.05).")
        print("  Recommend DS sign-off on G6 EXP-017 gate.")
    elif verdict == V_DIR_POS:
        print("  Directional signal is positive but below Tier 2 floor.")
        print(f"  Continue accumulating toward n={ADR_0024_TIER2_N_SINGLE} (single-sport Tier 2).")
    elif verdict == V_CONF_NEG:
        print("  CONFIRMED_NEGATIVE at adequate sample.")
        print("  ADR-0024: halt paper trading + initiate ADR-0004 model class review.")
    elif verdict == V_DIAG:
        print(f"  Tier 1 diagnostic sprint required: EV=${ev:+.4f} < -$0.03 at n>={ADR_0024_TIER1_N}.")
        print("  Escalate to DS per ADR-0024 before continuing paper trading.")
    elif verdict == V_DIR_NEG:
        print("  Directional signal is negative; below Tier 1 floor — continue accumulating.")
    else:
        print(f"  Inconclusive ({n_unique} positions). Continue accumulating data.")
    print(sep)


# ── CLI ────────────────────────────────────────────────────────────────────────

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
        positions = _load_csv(path, exclude_duplicates=exc_dup)
        label = f"CSV {path.name}"
    else:
        path = Path(args.portfolio)
        if not path.exists():
            print(f"ERROR: portfolio not found: {path}", file=sys.stderr)
            print("  MLB paper trading has not yet generated positions.", file=sys.stderr)
            print(f"  Expected path: {path}", file=sys.stderr)
            return 1
        positions = _load_portfolio(path, exclude_duplicates=exc_dup)
        label = f"portfolio {path.name}"

    result = analyse(
        positions,
        alpha=args.alpha,
        nba_n=args.nba_n,
        label=label,
    )
    _print_report(result)

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

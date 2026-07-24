#!/usr/bin/env python3
"""
GG-060 Phase 4 / T-375 — shared EXP-017-style retrospective accounting core.

WHY THIS EXISTS
----------------
GG-046's own resolution spec (GOVERNANCE_GAP_LOG.md) calls for "EXP-T4-01,
analogous to EXP-017: compare model_p against live Kalshi market price at the
moment each evaluation fired; compute net_edge over resolved bets; apply
ADR-0024 Tier 1/2 thresholds independently" — but as of this session no
EXP-T4-01 script exists (confirmed via grep across scripts/). Meanwhile
run_exp017_mlb.py's accounting logic (fee-net edge, EV, win rate, ADR-0024
tier check, edge-monotonicity/anti-predictive guard, calibration diagnostics)
is entirely band-agnostic — nothing in it is actually specific to T1 MLB
beyond the sport label and the default portfolio path. It reads whatever
paper-portfolio JSON it's given, keyed on the same closed_positions schema
every MLB band's PaperTrader/C5 writes (model_p, mid_price_at_entry,
vig_at_entry, direction, outcome, pnl, kalshi_ticker, kalshi_threshold,
game_date, player_name).

This module is that logic, extracted so EXP-017 (T1) and EXP-T4-01 (T4M-PROJ)
share one implementation instead of forking it — the exact "future EXP
re-runs don't require bespoke one-off scripts" gap GG-059's Resolution item 5
/ T-213 called out. run_exp017_mlb.py was refactored to import from here with
zero behavioral change (validated by diffing full report output against a
real VPS portfolio pull, before vs. after the refactor — see DECISION_LOG.md
T-375 Phase 4 entry). run_exp_t4_01_mlb.py is the new EXP-T4-01 script built
directly on this core.

Do not add sport-specific branching here. If a future band's resolved-position
schema diverges (a new field name, a new outcome vocabulary), that is a signal
the band needs its own loader function passed in, not an if/else grown inside
this module.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path
from typing import NamedTuple, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.analytics.calibration_diagnostics import (  # noqa: E402
    reliability,
    brier_murphy,
    ece,
    calib_fit_ci,
)

# ── Constants (ADR-0024) ────────────────────────────────────────────────────

ADR_0024_TIER1_N          = 150    # ADR-0024: Tier 1 minimum sample
ADR_0024_TIER1_DIAG_EV    = -0.03  # Tier 1 diagnostic sprint threshold (EV/bet < -$0.03)
ADR_0024_TIER2_N_SINGLE   = 500    # Tier 2 single-sport floor
ADR_0024_TIER2_N_MULTI    = 150    # Tier 2 multi-sport floor (per sport, requires --nba-n)
ADR_0024_P_THRESHOLD      = 0.05   # significance level for CONFIRMED_* verdicts
KALSHI_FEE_RATE           = 0.07   # taker fee: 0.07 x mip x (1 - mip)
MIN_N                     = 20     # minimum positions for any verdict
CALIB_MIN_N               = 20     # minimum positions to attempt calibration diagnostics
CALIB_BINS                = 5      # reliability/ECE bin count (matches EXP-017C default)
CALIB_BOOT                = 2000   # bootstrap draws for IRLS (a,b) CI
CALIB_SEED                = 17     # deterministic bootstrap seed (matches EXP-017C convention)

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

try:
    from scipy.stats import fisher_exact
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False


# ── Data model ─────────────────────────────────────────────────────────────

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
    # Added 2026-07-24 (A2/D1, GG-105) -- needed for (a) logic_epoch cohort
    # filtering on the t1t2t3 book (previously only wired for t4, see
    # what_if_harness.py) and (b) the --overrides-file join key
    # (player_id, game_date) for scoring an externally-computed candidate
    # model_p against the real ledger. Defaulted so every existing keyword
    # construction call site (run_band_monitor.py, run_t333_*.py) stays
    # valid unchanged.
    player_id:      int | None = None
    position_id:    str | None = None
    logic_epoch:    int | None = None


# ── Fee and edge helpers ────────────────────────────────────────────────────

def kalshi_fee(mip: float) -> float:
    """Kalshi taker fee per dollar of YES contract: 0.07 x mip x (1 - mip)."""
    return KALSHI_FEE_RATE * mip * (1.0 - mip)


def compute_fee_net_edge(direction: str, model_p: float, mip: float) -> float:
    """
    Fee-net edge: model advantage over market price minus Kalshi taker fee.
    YES: model thinks p_yes = model_p; market charges mip.  edge = model_p - mip - fee
    NO:  model thinks p_yes < mip; bets NO.                 edge = mip - model_p - fee
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


# ── Loaders ────────────────────────────────────────────────────────────────

def load_portfolio(
    path: Path,
    exclude_duplicates: bool = True,
) -> list[MLBPosition]:
    """Load closed positions from a paper portfolio JSON (any MLB band —
    schema is shared across T1/T2/T4M-PROJ PaperTrader/C5 writers)."""
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
        # NOTE (2026-07-03, T-184 real-data validation, GG-077): the stored
        # "fee_net_edge" field is NOT trusted here even when present.
        # paper_trader.py (open_position(), c5_execution) always computes
        # and stores this field in the YES-frame (gross_edge - fee) and
        # never flips sign for NO-direction bets — unlike its sibling
        # "fee_contaminated" field, which the same function DOES flip via
        # _directional_gross. Confirmed empirically: all 47 real NO-direction
        # MLB T1 positions (of 49) carry a negative stored fee_net_edge even
        # though many are profitable, correctly-signaled bets. Trusting the
        # stored value here silently breaks the edge-monotonicity /
        # anti-predictive guard (the GG-037/T-177 check class) for any
        # portfolio that is majority-NO, which real MLB data is. Always
        # recompute via the direction-aware, already-tested
        # compute_fee_net_edge() instead.
        fee_net_edge = compute_fee_net_edge(direction, model_p, mip)
        pnl = float(p.get("pnl", 0.0) or 0.0)
        try:
            # PIPE-05 (run_mlb_paper_trade.py) emits "kalshi_threshold" on real
            # positions; "threshold" is kept as a fallback for other producers.
            threshold = int(p.get("kalshi_threshold", p.get("threshold", 0)))
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
            player_id=p.get("player_id"),
            position_id=p.get("position_id"),
            logic_epoch=p.get("logic_epoch"),
        ))
    return positions


def load_csv(
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
                player_id=(int(row["player_id"]) if row.get("player_id") not in (None, "") else None),
                position_id=(row.get("position_id") or None),
                logic_epoch=(int(row["logic_epoch"]) if row.get("logic_epoch") not in (None, "") else None),
            ))
    return positions


# ── Deduplication ──────────────────────────────────────────────────────────

def deduplicate(positions: list[MLBPosition]) -> list[MLBPosition]:
    """Return one position per unique kalshi_ticker (earliest entry wins)."""
    seen: set[str] = set()
    unique: list[MLBPosition] = []
    for p in positions:
        if p.kalshi_ticker not in seen:
            seen.add(p.kalshi_ticker)
            unique.append(p)
    return unique


# ── EV computation ─────────────────────────────────────────────────────────

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


# ── Threshold breakdown ─────────────────────────────────────────────────────

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


# ── Calibration diagnostics (T-280/B4) ──────────────────────────────────────

def _calibration_records(positions: list[MLBPosition]) -> list[dict]:
    """Build the dict-record shape calibration_diagnostics.py expects:
    _model_p (forecast) and _event (0/1, reconstructed outcome). Convention
    matches run_exp017c_calibration_mlb.py exactly (verified 0/151 mismatch
    vs actual_hits there): event = 1 iff the bet direction and outcome agree
    on the underlying "player reached threshold" fact.
    """
    return [
        {"_model_p": p.model_p,
         "_event": 1 if ((p.direction == "YES") == (p.outcome == "WIN")) else 0}
        for p in positions
    ]


def calibration_report(
    positions: list[MLBPosition],
    bins: int = CALIB_BINS,
    boot: int = CALIB_BOOT,
    seed: int = CALIB_SEED,
) -> Optional[dict]:
    """Reliability/Murphy/ECE/logistic-fit diagnostics on the same deduped
    universe. Returns None below CALIB_MIN_N (bootstrap CI and per-bin
    reliability are not meaningful at very small n)."""
    if len(positions) < CALIB_MIN_N:
        return None
    recs = _calibration_records(positions)
    rng = random.Random(seed)
    bm = brier_murphy(recs, bins)
    return {
        "n": len(recs),
        "bins": bins,
        "reliability": reliability(recs, bins),
        "brier_murphy": bm,
        "ece": ece(recs, bins),
        "calibration_fit": calib_fit_ci(recs, boot, rng),
        "recompose_ok": bm["recompose_ok"],
    }


# ── ADR-0024 tier check ──────────────────────────────────────────────────────

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


# ── EV verdict ────────────────────────────────────────────────────────────────

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


# ── Fisher's exact / chi-squared ─────────────────────────────────────────────

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


# ── Edge monotonicity analysis ───────────────────────────────────────────────

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


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(
    positions: list[MLBPosition],
    alpha: float = 0.10,
    nba_n: int = 0,
    label: str = "",
    sport: str = "mlb",
    adr: str = "ADR-0024",
    gg: str = "GG-004",
) -> dict:
    """Full EXP-017-style analysis, reusable across any MLB band's resolved
    positions. `sport`/`adr`/`gg` are tags carried through into the result
    dict for report headers and JSON output — they do not change the math."""
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
    calibration = calibration_report(unique)

    return {
        "label": label,
        "sport": sport,
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
        "calibration": calibration,
        "verdict": verdict,
        "adr": adr,
        "gg": gg,
    }


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_report(
    result: dict,
    title: str = "EXP-017 MLB — Commercial Validation vs Kalshi KXMLBHIT Prices",
    subtitle: str = "ADR-0024 | GG-004 | T-184",
) -> None:
    sep = "=" * 68
    print(sep)
    print(title)
    print(subtitle)
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
    print("── ADR-0024 Tier Status ─────────────────────────────────────")
    print(f"  Tier 1 (n >= {ADR_0024_TIER1_N}):  {'REACHED' if t1 else f'NOT YET ({n_unique}/{ADR_0024_TIER1_N})'}")
    td = result["tier_detail"]
    if t1:
        print(f"  Tier 1 diagnostic: EV < -$0.03?  {td['diagnostic_sprint']}")
    print(f"  Tier 2 single (n>={ADR_0024_TIER2_N_SINGLE}): {'YES' if td['at_tier2_single'] else f'NOT YET ({n_unique}/{ADR_0024_TIER2_N_SINGLE})'}")
    nba_n_str = td["nba_n"]
    sport_label = result.get("sport", "sport").upper()
    print(f"  Tier 2 multi  ({sport_label} n>={ADR_0024_TIER2_N_MULTI} AND NBA n>={ADR_0024_TIER2_N_MULTI}): "
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
            lbl = f"k={k}" if k in (1, 2, 3) else f"k={k}(?)"
            print(f"  {lbl}: EV=${row['ev_per_bet']:+.4f}/bet  "
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
    # Calibration diagnostics (T-280/B4)
    calib = result.get("calibration")
    print("── Calibration Diagnostics (reliability / Murphy / ECE) ────────")
    if calib is None:
        print(f"  Skipped — n={n_unique} < CALIB_MIN_N={CALIB_MIN_N}")
    else:
        bm = calib["brier_murphy"]
        print(f"  n={calib['n']}  bins={calib['bins']}")
        print(f"  Brier: full={bm['brier_full']:.4f}  binned={bm['brier_binned']:.4f}  "
              f"(binning_gap={bm['binning_gap_(full-binned)']:+.4f})")
        print(f"  Murphy: REL={bm['reliability']:.4f}  RES={bm['resolution']:.4f}  "
              f"UNC={bm['uncertainty']:.4f}  "
              f"REL-RES+UNC={bm['decomposition_(rel-res+unc)']:.4f}  "
              f"recompose_ok={bm['recompose_ok']}")
        print(f"  ECE: {calib['ece']:.4f}")
        fit = calib["calibration_fit"]
        print(f"  Logistic fit: a={fit['intercept_a']:+.3f}  b={fit['slope_b']:.3f}  "
              f"b_CI={[round(x, 3) for x in fit['b_ci']]}  -> {fit['interpretation']} "
              f"(b excludes 1: {fit['b_excludes_1']})")
        for row in calib["reliability"]:
            if row["n"] == 0:
                continue
            print(f"    {row['bin']:<14} n={row['n']:<3} forecast={row['mean_forecast']:.3f} "
                  f"empirical={row['empirical_rate']:.3f}  gap={row['gap']:+.3f}")
    print()
    # Final verdict
    print("── Verdict ──────────────────────────────────────────────────")
    verdict = result["verdict"]
    print(f"  {verdict}")
    if verdict == V_CONF_POS:
        print(f"  {result['gg']} CLOSEABLE: positive EV at adequate sample (p < 0.05).")
        print("  Recommend DS sign-off on G6 EXP gate.")
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

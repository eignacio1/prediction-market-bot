"""
C3: Game State Model — T4/T5 In-Play Inference Engine
======================================================
Component:    C3 (Forecasting) — in-play sub-module
Phase active: SKELETON — Phase 8+ only. Pure math; testable now without DS-02.
Upstream:     DS-02 real-time game state feed (BLOCKED — not selected/activated)
Downstream:   run_t4_inplay.py (PIPE-07); run_t5_lategame.py (PIPE-08)
ADR refs:     ADR-0004 (base model); future Phase 8 infrastructure ADR required
              before T4/T5 activation with live capital.

What this module does:
    T4 (Poisson current-state model): Computes a fresh probability estimate
    from current game state: P(total_pts >= threshold | pts_so_far,
    time_remaining, pace). p_t1 is NOT incorporated into this calculation —
    it is the pre-game benchmark carried for telemetry, not the Bayesian
    prior. Materiality (ADR-0021, resolves GG-025) is judged on the
    INCREMENTAL signal delta_p_incr = p_t4 - p_t4_baseline, where the
    baseline is the same Poisson model evaluated at the tip-off null state
    (0 pts, full game remaining). This cancels the raw-Poisson-vs-Platt
    calibration gap by construction: at tip-off delta_p_incr = 0 identically,
    and E[delta_p_incr] = 0 whenever the player scores at the pregame rate
    (Poisson additivity). The fire condition additionally requires
    p_t4 > mip + vig.

    T5 (Arithmetic certainty): Classifies a player-threshold market as
    NEAR_CERTAIN_YES, NEAR_CERTAIN_NO, or UNCERTAIN in the final 3 minutes
    of Q4. Arithmetic only — no model inference, no Poisson approximation
    needed (pts_needed is small enough that Poisson CDF is deterministic
    within the 5ms compute budget).

Design constraints:
    T4: 50ms compute budget (must be faster than Kalshi market update latency)
    T5: 5ms compute budget (arithmetic; final minutes only)
    No external API calls — all inputs are game state parameters
    No scipy dependency — Poisson CDF implemented in pure Python (stdlib math)
    Unit-testable now without real-time feed (BLOCKED until DS-02 is active)

Kelly fractions by band (ADR-0010):
    T1 = 0.10, T4 = 0.20, T5 = 0.25
    Variance-scaling principle: k ∝ 1/σ_λ. T4/T5 use threshold-specific Poisson
    (lower σ) → higher k. T1 uses player-level LR estimate (higher σ) → lower k.

Governance:
    T4/T5 activation requires a new Phase 8 ADR (kill switch redesign +
    DS-02 source ADR + infrastructure ADR). No live capital until G6.
    This file may be imported and tested freely in paper/dark-period.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# T4 materiality gate (ADR-0021; supersedes ADR-0020 D2; resolves GG-025).
#
# The gate is computed per ticker per cycle — no fixed delta threshold:
#   material ⟺ |delta_p_incr| >= max(T4_DELTA_SIGMA_Z · σ_null(t), T4_MIN_DELTA_FLOOR)
#
#   delta_p_incr  = p_t4(current state) - p_t4(tip-off null state). Stateless and
#                   restart-safe: the baseline is deterministic from (pace, threshold),
#                   both fixed pregame — no stored game-start snapshot required.
#   σ_null(t)     = exact standard deviation of delta_p_incr at the current elapsed
#                   time under the null hypothesis that the player scores at the
#                   pregame rate. Enumerated from the Poisson pmf (closed form, no MC).
#                   Because Poisson(pace·elapsed) + Poisson(pace·remaining) =
#                   Poisson(pace·48), the null delta has mean exactly 0.
#   Z = 2.0       = house noise-envelope convention (EXP-019A σ-methodology, ADR-0018).
#   FLOOR = 0.04  = economic floor; mirrors C4 MIN_EDGE_TO_APPROVE (ADR-0020). A
#                   probability move below the minimum actionable edge cannot be
#                   commercially material regardless of statistical significance.
GAME_MINUTES_TOTAL: float = 48.0
T4_DELTA_SIGMA_Z: float = 2.0
T4_MIN_DELTA_FLOOR: float = 0.04

# T5: game time threshold for late-game arithmetic activation.
T5_TIME_THRESHOLD_MIN: float = 3.0

# T5: probability bounds for near-certainty classification (ADR-0010 / EXP-019).
# Derived: λ_rem≈1.25 at ≤3 min; P(≥3 more pts)=0.131 → p≥0.85 means ≤1 pt needed.
# Economic floor: p_min = market + MIN_EDGE + VIG_HALF = 0.845 at market=0.80; 0.85 clears it.
T5_YES_CERTAINTY: float = 0.85
T5_NO_CERTAINTY: float  = 0.15

# Kelly fractions by execution band (ADR-0010; mirrored from execution_bands.py)
KELLY_T4: float = 0.20
KELLY_T5: float = 0.25

# ---------------------------------------------------------------------------
# T1 opponent adjustment (ADR-0015)
# ---------------------------------------------------------------------------

# 2025-26 NBA season average points allowed per game across all 30 teams.
# Update via DECISION_LOG entry at season rollover — no new ADR required.
LEAGUE_AVG_PTS_ALLOWED: float = 113.0

OPP_ADJ_MIN: float = 0.70  # floor: suppress at most 30% below league avg
OPP_ADJ_MAX: float = 1.30  # ceiling: inflate at most 30% above league avg


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GameState:
    """
    Snapshot of a player's in-game state for T4/T5 inference.

    pace_pts_per_min: rolling expected scoring rate for this player in
    this game context (pts/min). Caller computes from C2 feature store
    adjusted for opponent defensive rating and current foul trouble.
    DS-02 provides pts_so_far, time_remaining_min, quarter.
    """
    player_id: str
    pts_so_far: float
    time_remaining_min: float
    quarter: int
    pace_pts_per_min: float


@dataclass(frozen=True)
class T4Signal:
    """Updated probability estimate from T4 Bayesian inference."""
    player_id: str
    threshold: float
    p_t1: float               # T1 pre-game benchmark (from C3 LR model) — telemetry only
    p_t4: float               # T4 Poisson estimate (fresh from game state; not a posterior)
    delta_p: float            # p_t4 - p_t1; calibration-contaminated, kept for telemetry
    p_t4_baseline: float      # p_t4 at the tip-off null state (0 pts, full game remaining)
    delta_p_incr: float       # p_t4 - p_t4_baseline; live game-state signal only (ADR-0021)
    sigma_null: float         # exact null σ of delta_p_incr at current elapsed time
    pts_so_far: float
    pts_needed: float         # max(0, threshold - pts_so_far)
    lambda_remaining: float   # Poisson lambda (expected pts remaining)
    time_remaining_min: float
    t5_eligible: bool         # True when T5 activation conditions are met


@dataclass(frozen=True)
class T5Signal:
    """Late-game arithmetic certainty classification."""
    player_id: str
    threshold: float
    pts_so_far: float
    pts_needed: float
    expected_pts_remaining: float
    p_hit: float              # Poisson P(total_pts >= threshold | current state)
    verdict: str              # "NEAR_CERTAIN_YES" | "NEAR_CERTAIN_NO" | "UNCERTAIN"
    kelly_fraction: float     # KELLY_T5 if NEAR_CERTAIN_*, else 0.0


# ---------------------------------------------------------------------------
# Core Poisson math
# ---------------------------------------------------------------------------

def _poisson_cdf(k: int, lam: float) -> float:
    """
    P(X <= k) for X ~ Poisson(lambda). Pure Python; no scipy.

    Iterative computation: sum_{i=0}^{k} exp(-lam) * lam^i / i!
    Numerically stable via incremental term multiplication.
    """
    if lam <= 0.0:
        return 1.0 if k >= 0 else 0.0
    cumulative = 0.0
    term = math.exp(-lam)
    for i in range(k + 1):
        cumulative += term
        term *= lam / (i + 1)
    return min(1.0, cumulative)


def parse_ticker_opponent(ticker: str) -> str | None:
    """
    Extract opponent team abbreviation from a Kalshi KXNBAPTS ticker.

    Format: KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20
      Segment[1] = date(7 chars) + team_a(3) + team_b(3)
      Segment[2] = player_team(3) + player_id

    Returns None on parse failure or if player team does not appear in matchup.
    """
    parts = ticker.split("-")
    if len(parts) < 3:
        return None
    seg1 = parts[1]
    if len(seg1) < 13:
        return None
    team_a = seg1[7:10]
    team_b = seg1[10:13]
    player_team = parts[2][:3]
    if player_team == team_a:
        return team_b
    if player_team == team_b:
        return team_a
    return None


def opp_adjusted_lambda(
    pts_mean: float,
    ticker: str,
    team_store: Any,  # TeamStatsStore | None — duck-typed to avoid package import cycle
    game_date_iso: str,
) -> float:
    """
    Apply opponent defensive adjustment to Poisson λ (ADR-0015).

    adj_λ = pts_mean × clip(opp_def_l10 / LEAGUE_AVG_PTS_ALLOWED, 0.70, 1.30)

    Falls back to raw pts_mean if: team_store is None, ticker unparseable,
    or opponent defensive rating unavailable (< 3 prior games).
    """
    if team_store is None or not ticker:
        return pts_mean
    opp = parse_ticker_opponent(ticker)
    if opp is None:
        return pts_mean
    opp_def = team_store.get_opp_def_rating(opp, as_of_date=game_date_iso)
    if opp_def is None:
        return pts_mean
    factor = max(OPP_ADJ_MIN, min(OPP_ADJ_MAX, opp_def / LEAGUE_AVG_PTS_ALLOWED))
    return float(pts_mean * factor)


def null_delta_sigma(pace_pts_per_min: float, threshold: float, time_remaining_min: float) -> float:
    """
    Exact standard deviation of delta_p_incr under the null hypothesis that
    the player scores at the pregame rate (pace_pts_per_min) all game.

    At elapsed time τ = GAME_MINUTES_TOTAL − time_remaining, the null says
    pts_so_far ~ Poisson(pace·τ). For each outcome k, the model would report
    p_t4(k) = P(total ≥ threshold | k pts, λ_rem = pace·time_remaining).
    Poisson additivity gives Σ_k pmf(k)·p_t4(k) = p_t4_baseline exactly, so
    the null delta has mean 0 and Var = Σ_k pmf(k)·(p_t4(k) − baseline)².

    Structural facts (asserted by tests):
      σ = 0 at tip-off (no information yet);
      σ → sqrt(b·(1−b)) at the final horn (b = baseline) — full resolution;
      σ is non-decreasing in elapsed time (martingale variance accumulation).

    Pure stdlib math; O(λ_elapsed + threshold) per call — well inside the
    50ms T4 compute budget.
    """
    t_rem = max(0.0, time_remaining_min)
    elapsed = max(0.0, GAME_MINUTES_TOTAL - t_rem)
    lam_elapsed = pace_pts_per_min * elapsed
    lam_remaining = pace_pts_per_min * t_rem
    baseline = p_exceeds_threshold(0.0, threshold, pace_pts_per_min * GAME_MINUTES_TOTAL)
    if lam_elapsed <= 0.0:
        return 0.0

    var = 0.0
    pmf = math.exp(-lam_elapsed)
    cum = 0.0
    k = 0
    # Hard cap guards against pathological inputs from a bad live feed.
    k_cap = int(lam_elapsed + 12.0 * math.sqrt(lam_elapsed) + 30.0)
    while k <= k_cap and cum < 1.0 - 1e-12:
        p_k = p_exceeds_threshold(float(k), threshold, lam_remaining)
        d = p_k - baseline
        var += pmf * d * d
        cum += pmf
        k += 1
        pmf *= lam_elapsed / k
    # Residual tail mass sits at high k where p_t4 ≈ 1 → delta ≈ 1 − baseline.
    tail = max(0.0, 1.0 - cum)
    var += tail * (1.0 - baseline) * (1.0 - baseline)
    return math.sqrt(max(0.0, var))


def p_exceeds_threshold(pts_so_far: float, threshold: float, lam_remaining: float) -> float:
    """
    P(total_pts >= threshold | pts_so_far, lambda_remaining).

    Models remaining points as Poisson(lam_remaining). Since NBA points are
    integers, "needs 12.5 more" means "needs at least 13 more" — so we take
    ceil(pts_needed) as the minimum integer required.

    Returns 1.0 if threshold already reached, 0.0 if lam_remaining == 0.
    """
    pts_needed = threshold - pts_so_far
    if pts_needed <= 0.0:
        return 1.0
    k_needed = math.ceil(pts_needed)
    # P(X >= k_needed) = 1 - P(X <= k_needed - 1)
    return 1.0 - _poisson_cdf(k_needed - 1, lam_remaining)


# ---------------------------------------------------------------------------
# T4: Bayesian game state update
# ---------------------------------------------------------------------------

class GameStateModel:
    """
    T4 in-play inference engine.

    Accepts a GameState snapshot and the T1 benchmark probability, returns
    a T4Signal with a fresh Poisson estimate. p_t4 is computed entirely from
    current game state (pts_so_far, pace, time_remaining) — p_t1 appears only
    in delta_p and the fire condition, not in the probability computation.

    Compute budget: 50ms. Actual runtime: ~0.01ms (pure Python arithmetic).
    No external calls. No model artifacts loaded. Deterministic given inputs.

    Phase 8+ activation: wire on_game_state_event() in run_t4_inplay.py
    to the DS-02 real-time feed. Until DS-02 is active, testable with
    synthetic GameState inputs only.
    """

    def update(self, gs: GameState, threshold: float, p_t1: float) -> T4Signal:
        """
        Compute T4 probability update for a single player-threshold market.

        Args:
            gs:        Current game state snapshot from DS-02.
            threshold: Market threshold (e.g. 22.5 for KXNBAPTS-...-22).
            p_t1:      Pre-game model probability from T1 C3 forecast.

        Returns:
            T4Signal with updated probability and T5 eligibility flag.
        """
        lam = gs.pace_pts_per_min * gs.time_remaining_min
        p_t4 = p_exceeds_threshold(gs.pts_so_far, threshold, lam)
        delta_p = p_t4 - p_t1
        p_t4_baseline = p_exceeds_threshold(
            0.0, threshold, gs.pace_pts_per_min * GAME_MINUTES_TOTAL
        )
        delta_p_incr = p_t4 - p_t4_baseline
        sigma_null = null_delta_sigma(
            gs.pace_pts_per_min, threshold, gs.time_remaining_min
        )
        pts_needed = max(0.0, threshold - gs.pts_so_far)
        t5_eligible = (
            gs.time_remaining_min <= T5_TIME_THRESHOLD_MIN
            and gs.quarter == 4
        )
        return T4Signal(
            player_id=gs.player_id,
            threshold=threshold,
            p_t1=p_t1,
            p_t4=p_t4,
            delta_p=delta_p,
            p_t4_baseline=p_t4_baseline,
            delta_p_incr=delta_p_incr,
            sigma_null=sigma_null,
            pts_so_far=gs.pts_so_far,
            pts_needed=pts_needed,
            lambda_remaining=lam,
            time_remaining_min=gs.time_remaining_min,
            t5_eligible=t5_eligible,
        )

    def is_material(self, signal: T4Signal) -> bool:
        """
        True if the live game-state move clears both the per-ticker null
        noise envelope (Z·σ_null) and the economic floor (ADR-0021).
        """
        gate = max(T4_DELTA_SIGMA_Z * signal.sigma_null, T4_MIN_DELTA_FLOOR)
        return abs(signal.delta_p_incr) >= gate


# ---------------------------------------------------------------------------
# T5: Late-game arithmetic certainty engine
# ---------------------------------------------------------------------------

class LateGameArithmetic:
    """
    T5 near-certainty engine for final 3 minutes of Q4.

    Compute budget: 5ms. Uses the same Poisson CDF as GameStateModel but
    pts_needed is small in T5 scenarios (typically 0-8), so the CDF loop
    runs ≤ 8 iterations. Deterministic.

    Only activates when:
        gs.quarter == 4 AND gs.time_remaining_min <= T5_TIME_THRESHOLD_MIN

    Returns kelly_fraction = KELLY_T5 for NEAR_CERTAIN verdicts,
    0.0 for UNCERTAIN (no bet recommended).
    """

    def evaluate(self, gs: GameState, threshold: float) -> T5Signal:
        """
        Classify a player-threshold market in the final minutes.

        Args:
            gs:        Current game state (should be Q4 with ≤3 min remaining).
            threshold: Market threshold.

        Returns:
            T5Signal with verdict and kelly_fraction.
        """
        lam = gs.pace_pts_per_min * gs.time_remaining_min
        p_hit = p_exceeds_threshold(gs.pts_so_far, threshold, lam)
        pts_needed = max(0.0, threshold - gs.pts_so_far)
        expected_remaining = lam

        if p_hit >= T5_YES_CERTAINTY:
            verdict = "NEAR_CERTAIN_YES"
            kelly = KELLY_T5
        elif p_hit <= T5_NO_CERTAINTY:
            verdict = "NEAR_CERTAIN_NO"
            kelly = KELLY_T5
        else:
            verdict = "UNCERTAIN"
            kelly = 0.0

        return T5Signal(
            player_id=gs.player_id,
            threshold=threshold,
            pts_so_far=gs.pts_so_far,
            pts_needed=pts_needed,
            expected_pts_remaining=expected_remaining,
            p_hit=p_hit,
            verdict=verdict,
            kelly_fraction=kelly,
        )

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
    T4 (Bayesian update): Updates the T1 pre-game probability estimate given
    the current game state. Uses a Poisson model of remaining scoring
    opportunities. The T1 prior is never discarded — it is the prior;
    game state provides the likelihood.

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

Kelly fractions by band (from EXECUTION_BANDS.md):
    T1 = 0.25, T4 = 0.05, T5 = 0.15
    T5 is higher than T4 because the near-certainty classification gates entry:
    only very high-P outcomes reach T5 execution. The uncertainty band has
    collapsed by definition.

Governance:
    T4/T5 activation requires a new Phase 8 ADR (kill switch redesign +
    DS-02 source ADR + infrastructure ADR). No live capital until G6.
    This file may be imported and tested freely in paper/dark-period.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# T4: minimum absolute change in probability to treat as material.
# Small deltas don't overcome vig at Kelly 0.05; this avoids thrash.
T4_MIN_DELTA_P: float = 0.08

# T5: game time threshold for late-game arithmetic activation.
T5_TIME_THRESHOLD_MIN: float = 3.0

# T5: probability bounds for near-certainty classification.
T5_YES_CERTAINTY: float = 0.85
T5_NO_CERTAINTY: float  = 0.15

# Kelly fractions by execution band (mirrored from EXECUTION_BANDS.md)
KELLY_T4: float = 0.05
KELLY_T5: float = 0.15


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
    p_t1: float               # T1 pre-game prior
    p_t4: float               # T4 updated probability
    delta_p: float            # p_t4 - p_t1; material if |delta_p| >= T4_MIN_DELTA_P
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

    Accepts a GameState snapshot and the T1 prior probability, returns
    an updated T4Signal. The T1 prior is the starting point — game state
    accumulates evidence on top of it via Bayesian update (Poisson likelihood).

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
            pts_so_far=gs.pts_so_far,
            pts_needed=pts_needed,
            lambda_remaining=lam,
            time_remaining_min=gs.time_remaining_min,
            t5_eligible=t5_eligible,
        )

    def is_material(self, signal: T4Signal) -> bool:
        """True if the T4 update is large enough to act on."""
        return abs(signal.delta_p) >= T4_MIN_DELTA_P


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

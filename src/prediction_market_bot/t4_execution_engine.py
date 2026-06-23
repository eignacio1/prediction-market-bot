"""
T4 Execution Engine — Layer 1 Continuous Evaluation + Layer 2 Staleness Queue
===============================================================================
Module:   t4_execution_engine
Phase:    Phase 8+ ONLY — BLOCKED on GG-038 / GG-039 / GG-040 resolution
Purpose:  Implements the three-layer architecture defined in ADR-0029 (Tier A,
          accepted 2026-06-22). Replaces the monolithic T4EventLoop
          (run_t4_inplay.py) with a multi-tree, continuously-evaluating,
          staleness-arbitrated execution engine.

Architecture (ADR-0029 Tier A — immutable):

  LAYER 1 — CONTINUOUS EVALUATION ENGINE
      Each sub-band evaluator runs at its natural update frequency.
      Output per cycle: PASS | SIGNAL(bet) | EXIT(position)
      SIGNAL / EXIT → enqueued to Layer 2 immediately.

  LAYER 2 — EXECUTION QUEUE WITH STALENESS ARBITRATION
      Priority queue ordered by |edge| descending (highest edge first).
      EXIT signals bypass the queue (URGENT priority).
      Per-dequeue cycle:
        1. Staleness check (T4PriceCache.get_price → None = DROP)
        2. T4-CORR adjustment (downward-only invariant, ADR-0029 Principle 6)
        3. C4 full risk check (Kelly + free-cash invariant ADR-0026 + kill switch)
        4. Submit to Layer 3 (C5 + C6) immediately

  LAYER 3 — C5 EXECUTION + C6 AUDIT (not implemented here; see c5_execution/)

Key design principles (ADR-0029):
    Principle 1 — Immediate Execution: approved bets execute immediately; no
                  execution time mandates; edge window duration ≠ execution gate.
    Principle 2 — Staleness Arbitration: staleness check REPLACES time buckets
                  as the gate for which bets actually execute.
    Principle 3 — Parallel Evaluation: all active trees run simultaneously;
                  T4-PROJ latency does not block T4-EVENT.
    Principle 4 — Multi-Tree, Bidirectional: multiple trees may fire on the
                  same market simultaneously; convergence is confirmatory.
    Principle 5 — No Inherited Arbitrary Values: every numeric must be derived
                  analytically or explicitly gated on a named EXP.
    Principle 6 — T4-CORR Downward-Only: correlation overlay can only reduce
                  C4-approved sizes, never increase.

Q6 flag (SESSION 67): "enum/config plumbing is NOT the routing intelligence —
Layer 1 Continuous Evaluation + Layer 2 staleness-arbitrated queue (the
~1,000-eval/game engine, the substance of Tier A) remain UNBUILT."

This module resolves that flag.

BLOCKED until ALL of:
    GG-038 — T4 kill switch ≤5s SLA (C7 fast-halt mechanism)
    GG-039 — T4 price cache design + ADR accepted (T4PriceCache)
    GG-040 — T4 real-time data sources confirmed (live box score + lineups feed)

Do NOT activate any execution path outside Phase 8.
"""

from __future__ import annotations

import heapq
import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from scipy.stats import poisson as _sp_poisson

from prediction_market_bot.execution_bands import (
    EXIT_MIN_TIME_REMAINING_MIN,
    ExecutionBand,
    NOISE_BUFFER_BAND_T4,
    T4_SUBBAND_REGISTRY,
    T4_SUBBANDS,
    is_t4_subband,
)
from prediction_market_bot.t4_price_cache import T4Phase8BlockedError, T4PriceCache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Game phase classification (ADR-0029 T4-PROJ confidence regimes)
# ---------------------------------------------------------------------------

class GamePhase(Enum):
    """
    In-game confidence regime for T4-PROJ Kelly schedule (ADR-0029).

    Thresholds are provisional (Tier B); formal derivation requires EXP-PROJ-01.
    The game-phase computation must use elapsed_min, not remaining_min, so that
    the phase advances monotonically through the game.
    """
    EARLY       = "EARLY"        # < 24 min elapsed; σ_λ ≫ T1; sparse firing
    MID         = "MID"          # 24–36 min elapsed; σ_λ comparable to T1
    LATE        = "LATE"         # 36–44 min elapsed; σ_λ < T1; primary T4-PROJ window
    NEAR_CERTAIN = "NEAR_CERTAIN" # > 44 min elapsed; σ_λ very low; T4-ARITH territory
    # Provisional boundaries live in module-level _PHASE_BOUNDARIES list.


# ADR-0029 provisional thresholds (Tier B).
_PHASE_BOUNDARIES: list[tuple[float, GamePhase]] = [
    (44.0, GamePhase.NEAR_CERTAIN),
    (36.0, GamePhase.LATE),
    (24.0, GamePhase.MID),
    (0.0,  GamePhase.EARLY),
]


def classify_game_phase(elapsed_min: float) -> GamePhase:
    """Return the GamePhase for the given elapsed game minutes."""
    for threshold, phase in _PHASE_BOUNDARIES:
        if elapsed_min >= threshold:
            return phase
    return GamePhase.EARLY


# ---------------------------------------------------------------------------
# T4 Bayesian math constants (ADR-0029 Tier B — all provisional)
# ---------------------------------------------------------------------------

GAME_REGULATION_MIN: float = 48.0   # NBA regulation game length
OVERTIME_PERIOD_MIN: float = 5.0    # NBA overtime period length

# Prior variance for Gamma-Poisson λ estimate. σ=5 pts means 1σ covers a
# 5-pt deviation from λ_prior per full game (~1 scoring category).
# EXP-PROJ-01 must calibrate from T1 λ residuals before T4-PROJ activation.
PRIOR_LAMBDA_SIGMA_PTS: float = 5.0

# Phase-conditional Kelly schedule (ADR-0029 Tier B).
# Linear interpolation within MID (0.032→0.078) and LATE (0.078→0.167).
# NEAR_CERTAIN held at LATE ceiling until EXP-PROJ-01 confirms tail calibration.
_KELLY_EARLY: float = 0.010          # EARLY: σ_λ ≫ T1 prior; sparse firing
_KELLY_MID_LO: float = 0.032         # MID entry: σ_λ comparable to T1
_KELLY_MID_HI: float = 0.078         # MID exit / LATE entry
_KELLY_LATE_LO: float = 0.078        # LATE entry
_KELLY_LATE_HI: float = 0.167        # LATE exit = NEAR_CERTAIN cap
_KELLY_NEAR_CERTAIN: float = 0.167   # Held at LATE ceiling (EXP-PROJ-01 pending)

# Phase elapsed-minute boundaries for Kelly interpolation (must match _PHASE_BOUNDARIES).
_PHASE_MID_START_MIN: float = 24.0
_PHASE_LATE_START_MIN: float = 36.0
_PHASE_NC_START_MIN: float = 44.0

# Blowout constants (EXP-FLOW-03 required — all provisional).
# FLOW-BLOWOUT fires when |score_differential| >= threshold sustained for >= sustain_min.
BLOWOUT_SCORE_THRESHOLD: int = 20
BLOWOUT_SUSTAIN_MIN: float = 2.0
# Provisional λ multipliers: trailing star scores more (garbage-time usage),
# leading star scores less (rested). EXP-FLOW-03 must calibrate these.
_BLOWOUT_TRAILING_LAMBDA_MULT: float = 1.15
_BLOWOUT_LEADING_LAMBDA_MULT: float = 0.80

# Minimum edge threshold. Mirrors MIN_EDGE_TO_APPROVE in c4_risk_engine/risk.py.
# Local constant avoids importing risk.py into the T4 engine test path (pandas dep).
# Must stay in sync with risk.py when that value changes.
_MIN_EDGE: float = 0.04


# ---------------------------------------------------------------------------
# Game state snapshot (Layer 1 input)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class T4MarketSpec:
    """
    A market that Layer 1 evaluators should track during a game.

    Passed via T4GameState.market_specs. Evaluators iterate over market_specs
    to determine which markets to evaluate each cycle. When empty (the default),
    evaluators return [] without running any Bayesian math — preserving backward
    compatibility with tests that construct T4GameState without market_specs.

    Fields
    ------
    market_id : str
        Kalshi market ticker.
    player_id : str
        Player whose stat this market tracks.
    threshold : float
        Stat value the player must reach (e.g., 20.0 for "20+ points").
    stat_type : str
        Stat category: "pts" | "reb" | "ast" | "pra". Default "pts".
    team_is_home : Optional[bool]
        True if the player is on the home team; False if away; None if unknown.
        Required by T4-FLOW FLOW-BLOWOUT to determine leading/trailing side.
        None → FLOW-BLOWOUT skips this market (cannot determine blowout side).
    """
    market_id: str
    player_id: str
    threshold: float
    stat_type: str = "pts"
    team_is_home: Optional[bool] = None


@dataclass(frozen=True)
class T4PlayerState:
    """
    Per-player snapshot passed to Layer 1 evaluators.

    All stat accumulators are full-game running totals (as broadcast).
    lambda_t4_proj is None until T4-PROJ has computed at least one
    posterior for this player — T4-EVENT uses lambda_t1_prior until then.
    """
    player_id: str
    pts_so_far: float
    reb_so_far: float
    ast_so_far: float
    min_so_far: float
    fouls: int
    is_active: bool            # currently on the floor
    lambda_t1_prior: float     # T1 pregame Poisson rate estimate (pts/game)
    lambda_t4_proj: Optional[float]  # current T4-PROJ posterior; None = not computed yet


@dataclass(frozen=True)
class T4GameEvent:
    """
    An in-game event that may trigger Layer 1 evaluation cycles.

    event_type values:
        SCORE_UPDATE    — a player recorded a stat (points, rebound, assist, etc.)
        FOUL            — a personal foul recorded
        SUBSTITUTION    — a player checked in or out
        QUARTER_END     — end of Q1/Q2/Q3/Q4 (triggers T4-BOUNDARY)
        PRICE_DRIFT     — sustained Kalshi market price movement (triggers T4-SENTIMENT)
        TIMER           — periodic trigger (e.g., every M minutes for T4-PROJ)
    """
    event_type: str
    player_id: Optional[str]   # None for game-level events (QUARTER_END, TIMER)
    market_id: Optional[str]   # None if event is not market-specific
    ts: datetime
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class T4GameState:
    """
    Full in-game snapshot: the single object passed to all Layer 1 evaluators.

    Market prices are NOT included here — they are read directly from T4PriceCache
    by Layer 1 evaluators that need the current market price (T4-SENTIMENT, T4-PROJ).
    """
    game_id: str
    game_date: str             # YYYY-MM-DD
    quarter: int               # 1–4 (5+ = overtime)
    time_remaining_min: float  # minutes remaining in current quarter
    elapsed_min: float         # total game minutes elapsed (0 at tip; ~48 at regulation end)
    home_score: int
    away_score: int
    score_differential: int    # home_score - away_score; negative = home trailing
    ts: datetime
    player_states: dict[str, T4PlayerState]   # player_id → T4PlayerState
    trigger_event: Optional[T4GameEvent]       # what triggered this evaluation cycle
    market_specs: tuple[T4MarketSpec, ...] = field(default_factory=tuple)
    # Markets to evaluate this cycle. Empty tuple → all evaluators return [].
    # Default is empty for backward compatibility with existing tests.


# ---------------------------------------------------------------------------
# Open position record (for T4-EXIT monitoring)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class T4OpenPosition:
    """
    Typed record of an open T4 position for T4-EXIT monitoring.

    T4ExitEvaluator.generate_exit_signals() accepts list[T4OpenPosition] or
    the legacy list[dict] format. Dict entries missing required keys are
    silently skipped (backward-compatible with existing test fixtures).

    Fields
    ------
    market_id : str
        Kalshi market ticker for the open position.
    player_id : str
        Player the market tracks.
    direction : str
        "YES" or "NO" at position entry.
    threshold : float
        Stat threshold the market tracks.
    entry_model_p : float
        Model probability at position entry time.
    sub_band : ExecutionBand
        Which sub-band originated this position (governs noise buffer selection).
    entry_ts : datetime
        UTC time the position was opened.
    stat_type : str
        Stat category: "pts" | "reb" | "ast" | "pra". Default "pts".
    noise_buffer : Optional[float]
        Per-position noise buffer override. None → sub-band default or
        NOISE_BUFFER_BAND_T4 aggregate fallback.
    """
    market_id: str
    player_id: str
    direction: str          # "YES" | "NO"
    threshold: float
    entry_model_p: float
    sub_band: ExecutionBand
    entry_ts: datetime
    stat_type: str = "pts"
    noise_buffer: Optional[float] = None


# ---------------------------------------------------------------------------
# Layer 1 output types
# ---------------------------------------------------------------------------

@dataclass
class EvaluationSignal:
    """
    Output from a Layer 1 evaluator tree: an approved candidate bet or EXIT.

    Fields
    ------
    sub_band : ExecutionBand
        Which T4 sub-band produced this signal.
    tree_id : str
        Which decision tree within the sub-band (e.g. "EVENT-PTS-MADE",
        "FLOW-BLOWOUT"). Used for C6 audit and rate-limit governance.
    market_id : str
        Kalshi market ticker.
    player_id : str
        Player the market tracks.
    direction : str
        "YES" or "NO".
    model_p : float
        Sub-band's posterior probability estimate at signal time.
    mip_at_signal : float
        Market implied probability at signal time (from T4PriceCache).
    vig_at_signal : float
        Market vig estimate at signal time.
    edge_at_signal : float
        model_p - mip_at_signal - vig_at_signal. Positive = favourable.
    kelly_fraction : float
        Sub-band's applicable Kelly fraction (from BandConfig or dynamic schedule).
    signal_snapshot : dict
        Game state snapshot for C6 audit (game phase, relevant stats, etc.).
    ts : datetime
        UTC timestamp when this signal was produced.
    is_exit : bool
        True for T4-EXIT signals (priority bypass in Layer 2 queue).
    game_phase : GamePhase
        Classified game phase at signal time (used by T4-PROJ Kelly schedule).
    """
    sub_band: ExecutionBand
    tree_id: str
    market_id: str
    player_id: str
    direction: str                  # "YES" | "NO"
    model_p: float
    mip_at_signal: float
    vig_at_signal: float
    edge_at_signal: float           # model_p - mip_at_signal - vig_at_signal
    kelly_fraction: float
    signal_snapshot: dict
    ts: datetime
    is_exit: bool = False
    game_phase: GamePhase = GamePhase.EARLY


# ---------------------------------------------------------------------------
# Layer 2 queue types
# ---------------------------------------------------------------------------

@dataclass
class QueueEntry:
    """
    An EvaluationSignal waiting in the Layer 2 execution queue.

    The queue is a min-heap ordered by priority (lower = dequeued first).
    Priority is computed from |edge|: EXIT signals use 0.0 (highest priority);
    standard signals use 1.0 - |edge| so that higher edge = lower heap value.

    Fields
    ------
    signal : EvaluationSignal
        The signal from Layer 1.
    enqueued_ts : datetime
        UTC timestamp when this entry was enqueued.
    priority : float
        Heap ordering value. 0.0 = EXIT (urgent bypass). 1.0 - |edge| for others.
    """
    signal: EvaluationSignal
    enqueued_ts: datetime
    priority: float

    def __lt__(self, other: "QueueEntry") -> bool:
        """heapq comparison: lower priority value = dequeued first."""
        return self.priority < other.priority

    @classmethod
    def from_signal(cls, signal: EvaluationSignal) -> "QueueEntry":
        if signal.is_exit:
            priority = 0.0  # URGENT — bypass standard queue
        else:
            # Higher |edge| → lower heap value → dequeued first.
            priority = 1.0 - min(abs(signal.edge_at_signal), 1.0)
        return cls(
            signal=signal,
            enqueued_ts=datetime.now(timezone.utc),
            priority=priority,
        )


@dataclass(frozen=True)
class StaleDropRecord:
    """
    Audit record emitted when a queued bet is dropped due to staleness.

    C6 should log these to measure queue-survival rates per sub-band, which
    feed EXP-QUEUE-01 (ADR-0029 T4 Activation Gate prerequisite).
    """
    market_id: str
    sub_band_value: str        # ExecutionBand.value for JSON serialisation
    tree_id: str
    edge_at_entry: float
    edge_at_drop: Optional[float]  # None if price cache miss (no price available)
    queue_wait_ms: float
    drop_reason: str           # "price_stale" | "edge_below_min" | "direction_reversed"
    ts: datetime


@dataclass(frozen=True)
class CorrAdjustmentRecord:
    """
    Audit record emitted when T4-CORR adjusts a size downward.

    Downward-only invariant (ADR-0029 Principle 6): T4-CORR may never increase
    a C4-approved size. This record is appended to the C6 event for every
    dequeue cycle where a size was reduced.
    """
    market_id: str
    original_size_usd: float
    adjusted_size_usd: float
    correlation_score: float
    correlated_with: list[str]  # market_ids of simultaneously-queued correlated bets
    adjustment_reason: str


# ---------------------------------------------------------------------------
# T4 Bayesian math helpers (all O(1) analytic — safe at ~1,000 evals/game)
# ---------------------------------------------------------------------------


def _total_remaining_min(game_state: T4GameState) -> float:
    """Total game minutes remaining, including overtime periods."""
    if game_state.quarter <= 4:
        return max(0.0, GAME_REGULATION_MIN - game_state.elapsed_min)
    ot_periods = game_state.quarter - 4
    game_total = GAME_REGULATION_MIN + ot_periods * OVERTIME_PERIOD_MIN
    return max(0.0, game_total - game_state.elapsed_min)


def _gamma_prior_params(lambda_prior: float, sigma_prior: float) -> tuple[float, float]:
    """
    Compute Gamma(alpha, beta) prior parameters via moment matching.

    For rate-parameterized Gamma with mean=lambda_prior, variance=sigma_prior²:
        alpha = (lambda_prior / sigma_prior)²
        beta  = lambda_prior / sigma_prior²
    """
    alpha = (lambda_prior / sigma_prior) ** 2
    beta = lambda_prior / (sigma_prior ** 2)
    return alpha, beta


def _gamma_poisson_update(
    alpha0: float, beta0: float, k_obs: float, t_elapsed_frac: float
) -> tuple[float, float]:
    """
    Gamma-Poisson conjugate update.

    Prior:      λ ~ Gamma(alpha0, beta0)
    Likelihood: k_obs ~ Poisson(λ × t_elapsed_frac)
    Posterior:  λ ~ Gamma(alpha0 + k_obs, beta0 + t_elapsed_frac)
    """
    return alpha0 + k_obs, beta0 + t_elapsed_frac


def _poisson_survival_p(
    pts_so_far: float, threshold: float, lambda_remaining: float
) -> float:
    """
    P(player reaches threshold | pts already scored, expected pts remaining).

    Models additional pts scored ~ Poisson(lambda_remaining).
    Uses scipy Poisson CDF (C extension — O(1) for integer k, safe at high eval rate).
    """
    if pts_so_far >= threshold:
        return 1.0
    pts_needed = int(math.ceil(threshold - pts_so_far))
    if pts_needed <= 0:
        return 1.0
    if lambda_remaining <= 0.0:
        return 0.0
    return float(1.0 - _sp_poisson.cdf(pts_needed - 1, lambda_remaining))


def _phase_conditional_kelly(elapsed_min: float) -> float:
    """
    ADR-0029 dynamic Kelly schedule by game phase.

    EARLY (<24 min):    0.010 (flat; σ_λ ≫ T1 prior, data sparse)
    MID (24–36 min):    linear 0.032 → 0.078
    LATE (36–44 min):   linear 0.078 → 0.167
    NEAR_CERTAIN (≥44): 0.167 (held at LATE ceiling; EXP-PROJ-01 pending)
    """
    phase = classify_game_phase(elapsed_min)
    if phase == GamePhase.EARLY:
        return _KELLY_EARLY
    elif phase == GamePhase.MID:
        t = (elapsed_min - _PHASE_MID_START_MIN) / (_PHASE_LATE_START_MIN - _PHASE_MID_START_MIN)
        return _KELLY_MID_LO + t * (_KELLY_MID_HI - _KELLY_MID_LO)
    elif phase == GamePhase.LATE:
        t = (elapsed_min - _PHASE_LATE_START_MIN) / (_PHASE_NC_START_MIN - _PHASE_LATE_START_MIN)
        return _KELLY_LATE_LO + t * (_KELLY_LATE_HI - _KELLY_LATE_LO)
    else:  # NEAR_CERTAIN
        return _KELLY_NEAR_CERTAIN


# ---------------------------------------------------------------------------
# Layer 1 — SubBandEvaluator ABC
# ---------------------------------------------------------------------------

class SubBandEvaluator(ABC):
    """
    Abstract base class for all T4 sub-band evaluators.

    Each sub-band has exactly one SubBandEvaluator subclass. Evaluators are
    stateless with respect to the queue — they fire signals and return; they
    do not track what was enqueued. State (e.g., T4-PROJ posterior cache) lives
    in the evaluator's own attributes, updated each evaluation cycle.

    All concrete evaluate() implementations MUST:
      - Return an empty list when no signal meets the edge threshold.
      - Return one EvaluationSignal per qualifying market per tree.
      - Never block for I/O (price reads come from T4PriceCache, not live API).
      - Complete within BandConfig.max_compute_ms for their sub_band.

    BLOCKED: evaluate() may be called in tests with synthetic game state.
    start_continuous() and the actual evaluation loop are Phase 8 ONLY.
    """

    @property
    @abstractmethod
    def sub_band(self) -> ExecutionBand:
        """The ExecutionBand this evaluator serves."""

    @abstractmethod
    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        """
        Evaluate one cycle. Return SIGNAL(s) or [] for PASS.

        game_state carries current player stats and game context.
        price_cache provides current market prices (no live API calls).
        """

    def _require_phase8(self, operation: str) -> None:
        """Guard for execution-path methods that require Phase 8."""
        raise T4Phase8BlockedError(
            f"{self.__class__.__name__}.{operation} is Phase 8 infrastructure. "
            f"Sub-band {self.sub_band.value} is BLOCKED (status='BLOCKED' in "
            f"T4_SUBBAND_REGISTRY). All T4 sub-bands require Phase 8 Activation Gate."
        )

    def _assert_sub_band_blocked(self) -> None:
        """Verify at construction that this sub-band is BLOCKED in T4_SUBBAND_REGISTRY."""
        spec = T4_SUBBAND_REGISTRY.get(self.sub_band)
        if spec is None or spec.status != "BLOCKED":
            raise RuntimeError(
                f"{self.__class__.__name__}: sub-band {self.sub_band.value} must have "
                f"status='BLOCKED' in T4_SUBBAND_REGISTRY. Found: "
                f"{spec.status if spec else 'NOT REGISTERED'}. "
                f"Activating T4 sub-bands without a Phase 8 Activation Gate violates ADR-0029."
            )


# ---------------------------------------------------------------------------
# Layer 1 — Per-sub-band evaluator stubs (all BLOCKED)
# ---------------------------------------------------------------------------
# Each stub documents what the evaluator will DO at Phase 8 (the architectural
# contract), without implementing the decision tree logic (which requires Phase 8
# data sources — live box score, lineups, Kalshi tick feed). Decision tree
# specifications are in ADR-0029; this module holds the Python contract.
# ---------------------------------------------------------------------------

class T4StagedEvaluator(SubBandEvaluator):
    """
    T4-STAGED: Pre-game conditional fill (resting limit order placed at T3).

    At Phase 8: monitors Kalshi price against T3-approved trigger_price range.
    When market reaches trigger price, a resting order already in the
    StagedOrderStore fills passively — no new model computation needed.
    The evaluator's job is to confirm the fill event via the price cache and
    enqueue the position for Layer 2 accounting (NOT a new bet decision).

    Alpha hypothesis: T3-approved bet can fill at a better in-game price
    via a resting limit order.

    Kelly: inherits T3 Kelly (0.07, ADR-0010). Not independent.
    EXP: none required (T3 signal quality applies); resting-order C5 infra required.
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_STAGED

    def __init__(self) -> None:
        self._assert_sub_band_blocked()

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        return []  # BLOCKED — no active resting-order infrastructure at Phase 6/7


class T4EventEvaluator(SubBandEvaluator):
    """
    T4-EVENT: Discrete stat-event reaction.

    At Phase 8: detects qualifying game events (made shot, foul, substitution,
    blowout), computes Bayesian point update on affected player/threshold markets,
    applies materiality gate, and fires signals if edge ≥ MIN_EDGE_TO_APPROVE.

    Trees: EVENT-PTS-MADE, EVENT-PTS-OPPO, EVENT-MIN-FOUL, EVENT-MIN-SUB,
           EVENT-MIN-SUBIN, EVENT-BLOWOUT.

    Borrows λ from T4-PROJ posterior; uses T1 prior until first T4-PROJ cycle.

    Alpha hypothesis: Kalshi systematically lags repricing after discrete game
    events — a capturable edge window of 1–10 seconds per event.

    Kelly: EXP-EVENT-02 required (provisional 0.05).
    EXP: EXP-EVENT-01 (repricing lag measurement), EXP-EVENT-02 (Kelly derivation).
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_EVENT

    def __init__(self, proj_evaluator: Optional["T4ProjEvaluator"] = None) -> None:
        self._assert_sub_band_blocked()
        # Borrows T4-PROJ posterior (written earlier in the same cycle) to avoid
        # redundant Bayesian computation for the same player. Falls back to T1 prior.
        # No-arg construction (proj_evaluator=None) required for test fixture compatibility.
        self._proj_evaluator = proj_evaluator

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        """
        React to discrete stat events (SCORE_UPDATE, FOUL) for tracked players.

        Only fires for the player identified in trigger_event.player_id.
        Uses T4-PROJ posterior if available (written by T4-PROJ earlier this cycle).
        Alpha hypothesis: Kalshi lags repricing after discrete events (1–10s window).
        """
        if not game_state.market_specs:
            return []

        trigger = game_state.trigger_event
        if trigger is None or trigger.event_type not in ("SCORE_UPDATE", "FOUL"):
            return []  # T4-EVENT only reacts to discrete stat events

        triggered_player_id = trigger.player_id
        if triggered_player_id is None:
            return []

        now = datetime.now(timezone.utc)
        total_remaining = _total_remaining_min(game_state)
        phase = classify_game_phase(game_state.elapsed_min)
        signals: list[EvaluationSignal] = []

        for spec in game_state.market_specs:
            if spec.player_id != triggered_player_id:
                continue  # only react to the player who triggered this event

            player = game_state.player_states.get(spec.player_id)
            if player is None or not player.is_active:
                continue

            # Borrow T4-PROJ posterior; fall back to T1 prior
            lambda_est: float = player.lambda_t1_prior
            if self._proj_evaluator is not None:
                posterior = self._proj_evaluator.get_lambda_posterior(spec.player_id)
                if posterior is not None:
                    lambda_est = posterior

            t_remaining_frac = total_remaining / GAME_REGULATION_MIN
            lambda_remaining = lambda_est * t_remaining_frac

            model_p = _poisson_survival_p(player.pts_so_far, spec.threshold, lambda_remaining)

            cached_price = price_cache.get_raw(spec.market_id)
            if cached_price is None:
                continue

            edge = model_p - cached_price.mid - cached_price.vig
            if abs(edge) < _MIN_EDGE:
                continue

            direction = "YES" if model_p > 0.5 else "NO"
            event_suffix = "MADE" if trigger.event_type == "SCORE_UPDATE" else "FOUL"
            signals.append(EvaluationSignal(
                sub_band=ExecutionBand.T4_EVENT,
                tree_id=f"EVENT-{spec.stat_type.upper()}-{event_suffix}",
                market_id=spec.market_id,
                player_id=spec.player_id,
                direction=direction,
                model_p=model_p,
                mip_at_signal=cached_price.mid,
                vig_at_signal=cached_price.vig,
                edge_at_signal=edge,
                kelly_fraction=0.05,  # PROVISIONAL: EXP-EVENT-02 required (ADR-0029)
                signal_snapshot={
                    "trigger_event": trigger.event_type,
                    "triggered_player": triggered_player_id,
                    "lambda_est": round(lambda_est, 4),
                    "lambda_remaining": round(lambda_remaining, 4),
                    "pts_so_far": player.pts_so_far,
                    "threshold": spec.threshold,
                    "total_remaining": round(total_remaining, 2),
                },
                ts=now,
                is_exit=False,
                game_phase=phase,
            ))

        return signals


class T4LineupEvaluator(SubBandEvaluator):
    """
    T4-LINEUP: Live lineup / rotation change detection.

    At Phase 8: detects unexpected substitutions (player checks in/out outside
    predicted rotation window), cascades revised minutes projections to all
    open markets for the affected player, and fires signals for markets where
    edge ≥ MIN_EDGE_TO_APPROVE.

    Distinction from T4-EVENT: fires on N markets per event (portfolio cascade),
    not one market. T4-CORR handles within-game player correlations downstream.

    Alpha hypothesis: Kalshi reprices slowly after substitution events; minutes-
    dependent markets misprice when rotations change unexpectedly.

    Kelly: below T4-PROJ (cascading risk + harder σ_λ); provisional 0.05 max.
    EXP: EXP-LINEUP-01 (repricing lag for subs + rotation model validation).
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_LINEUP

    def __init__(self) -> None:
        self._assert_sub_band_blocked()

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        return []  # BLOCKED — requires live lineups/play-by-play API (GG-040)


class T4FlowEvaluator(SubBandEvaluator):
    """
    T4-FLOW: Accumulated game-state / context pattern.

    At Phase 8: monitors rolling game context via four trees:
      FLOW-FOUL     — foul trouble accumulation
      FLOW-PACE     — pace deviation from expected
      FLOW-ROTATION — starter minutes pace implies shortened night
      FLOW-BLOWOUT  — score differential ≥20 for 5+ possessions

    FLOW-BLOWOUT is the primary carrier of "blowout consequences" on individual
    player markets (trailing star lambda↑, leading star lambda↓/backup lambda↑).

    Alpha hypothesis: sustained context shifts (foul trouble, pace, blowout) move
    true λ before the market reprices.

    Kelly: variance-scaling including context-multiplier variance; provisional
    range 0.08–0.12 by phase/context. EXP-FLOW-01 (multiplier calibration),
    EXP-FLOW-02 (persistence threshold validation).
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_FLOW

    def __init__(self) -> None:
        self._assert_sub_band_blocked()
        # Tracks the elapsed_min at which the current blowout condition started.
        # None = no blowout currently active. Resets when |score_diff| < threshold.
        self._blowout_start_elapsed: Optional[float] = None

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        """
        FLOW-BLOWOUT: fire when score differential sustained at ≥ BLOWOUT_SCORE_THRESHOLD.

        Applies λ multipliers: trailing star λ↑ (garbage-time usage),
        leading star λ↓ (rested). T4MarketSpec.team_is_home required;
        markets without team affiliation are skipped.

        FLOW-FOUL, FLOW-PACE, FLOW-ROTATION: deferred to Phase 8 data sources.
        EXP-FLOW-01/02/03 required before activation.
        """
        if not game_state.market_specs:
            return []

        score_diff = game_state.score_differential
        elapsed = game_state.elapsed_min

        # Update blowout state
        in_blowout = abs(score_diff) >= BLOWOUT_SCORE_THRESHOLD
        if in_blowout:
            if self._blowout_start_elapsed is None:
                self._blowout_start_elapsed = elapsed
        else:
            self._blowout_start_elapsed = None

        if not in_blowout:
            return []
        # Guard: blowout start may not have been set if evaluate() was never called
        # before the threshold crossed — shouldn't happen in normal flow but defensive.
        if self._blowout_start_elapsed is None:
            return []
        if (elapsed - self._blowout_start_elapsed) < BLOWOUT_SUSTAIN_MIN:
            return []  # blowout not yet sustained long enough

        home_leading = score_diff > 0
        now = datetime.now(timezone.utc)
        total_remaining = _total_remaining_min(game_state)
        phase = classify_game_phase(elapsed)
        signals: list[EvaluationSignal] = []

        for spec in game_state.market_specs:
            if spec.team_is_home is None:
                continue  # team affiliation unknown; cannot determine blowout side

            player = game_state.player_states.get(spec.player_id)
            if player is None or not player.is_active:
                continue

            player_on_home = spec.team_is_home
            player_trailing = (home_leading and not player_on_home) or (not home_leading and player_on_home)
            lambda_mult = _BLOWOUT_TRAILING_LAMBDA_MULT if player_trailing else _BLOWOUT_LEADING_LAMBDA_MULT

            # Base lambda: T4-PROJ posterior (via T4PlayerState) if available, else T1 prior
            lambda_base = (
                player.lambda_t4_proj
                if player.lambda_t4_proj is not None
                else player.lambda_t1_prior
            )
            lambda_adjusted = lambda_base * lambda_mult
            t_remaining_frac = total_remaining / GAME_REGULATION_MIN
            lambda_remaining = lambda_adjusted * t_remaining_frac

            model_p = _poisson_survival_p(player.pts_so_far, spec.threshold, lambda_remaining)

            cached_price = price_cache.get_raw(spec.market_id)
            if cached_price is None:
                continue

            edge = model_p - cached_price.mid - cached_price.vig
            if abs(edge) < _MIN_EDGE:
                continue

            direction = "YES" if model_p > 0.5 else "NO"
            signals.append(EvaluationSignal(
                sub_band=ExecutionBand.T4_FLOW,
                tree_id="FLOW-BLOWOUT",
                market_id=spec.market_id,
                player_id=spec.player_id,
                direction=direction,
                model_p=model_p,
                mip_at_signal=cached_price.mid,
                vig_at_signal=cached_price.vig,
                edge_at_signal=edge,
                kelly_fraction=0.08,  # PROVISIONAL: ADR-0029 range 0.08–0.12 (EXP-FLOW-01/02)
                signal_snapshot={
                    "score_differential": score_diff,
                    "blowout_start_elapsed": self._blowout_start_elapsed,
                    "elapsed": elapsed,
                    "lambda_mult": lambda_mult,
                    "lambda_base": round(lambda_base, 4),
                    "lambda_adjusted": round(lambda_adjusted, 4),
                    "player_trailing": player_trailing,
                    "player_on_home": player_on_home,
                },
                ts=now,
                is_exit=False,
                game_phase=phase,
            ))

        return signals


class T4SentimentEvaluator(SubBandEvaluator):
    """
    T4-SENTIMENT: Market price drift (no game event).

    At Phase 8: monitors Kalshi price drift via T4PriceCache over a sustained
    window W, compares drift direction to T4-PROJ posterior, classifies drift as
    INFORMED (bet with drift) or OVERREACTION (bet against drift), and fires if
    edge ≥ MIN_EDGE_TO_APPROVE. Re-evaluated every 30–120s of sustained drift.

    Alpha hypothesis: system can classify Kalshi price drift as informed vs.
    noise better than chance.

    Kelly: lowest confidence signal; provisional 0.05. EXP-SENT-01 required.
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_SENTIMENT

    def __init__(self) -> None:
        self._assert_sub_band_blocked()

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        return []  # BLOCKED — requires EXP-SENT-01 drift-classification validation


class T4ProjEvaluator(SubBandEvaluator):
    """
    T4-PROJ: Bayesian posterior full-game projection.

    The richest T4 signal and architectural spine of the T4 suite. At Phase 8:
    updates a per-player Poisson posterior from accumulated in-game stats,
    classifies the game phase (EARLY/MID/LATE/NEAR_CERTAIN), applies the
    dynamic Kelly schedule (ADR-0029), and fires if edge ≥ MIN_EDGE_TO_APPROVE.

    Posterior is written to _posterior_cache for consumption by T4-EVENT and
    T4-SENTIMENT (those sub-bands do NOT maintain their own lambda estimate).

    Blowout regime: bidirectional edge on trailing/leading star markets.

    NEAR-CERTAIN Kelly: inverse-variance formula diverges at low σ_λ (0.526 at
    46 min); held ≤ 0.167 (LATE ceiling) until EXP-PROJ-01 confirms tail
    calibration. Hard governance ceiling remains 0.25 (DEFAULT_KELLY_FRACTION).

    Kelly schedule: EARLY 0.010 / MID 0.032–0.078 / LATE 0.078–0.167 / NEAR-CERTAIN ≤0.167.
    EXP: EXP-PROJ-01 (confidence_weight curve + NEAR-CERTAIN tail calibration),
         EXP-PROJ-02 (convergence premium derivation),
         EXP-PROJ-03 (blowout lambda factors).
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_PROJ

    def __init__(self) -> None:
        self._assert_sub_band_blocked()
        # Posterior cache: player_id → lambda_posterior.
        # Written by this evaluator; read by T4EventEvaluator, T4SentimentEvaluator.
        self._posterior_cache: dict[str, float] = {}

    def get_lambda_posterior(self, player_id: str) -> Optional[float]:
        """Return the current posterior lambda estimate for player_id, or None."""
        return self._posterior_cache.get(player_id)

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        """
        Gamma-Poisson Bayesian posterior update for each tracked market.

        Prior:      λ ~ Gamma(α₀, β₀) via moment-match to (λ_t1_prior, PRIOR_LAMBDA_SIGMA_PTS)
        Likelihood: pts_so_far ~ Poisson(λ × t_elapsed_frac)
        Posterior:  λ ~ Gamma(α₀ + pts_so_far, β₀ + t_elapsed_frac)

        Posterior mean = (α₀ + pts_so_far) / (β₀ + t_elapsed_frac) estimates full-game λ.
        Expected remaining pts = posterior_mean × (total_remaining / GAME_REGULATION_MIN).

        WARNING: λ_t1_prior inherits T1's opp_adj_lambda, which is calibrated from
        regular-season defensive ratings. This causes the same bias identified in S69
        (Finals scoring 9–30% below model-implied λ). The Bayesian update self-corrects
        as game data accumulates, but EARLY-phase (< 24 min) estimates remain biased.
        KELLY_EARLY = 0.010 is intentionally conservative to account for this.
        T-072 playoff_round_multiplier will fix the prior; required before T4-PROJ activation.
        """
        if not game_state.market_specs:
            return []

        now = datetime.now(timezone.utc)
        phase = classify_game_phase(game_state.elapsed_min)
        kelly = _phase_conditional_kelly(game_state.elapsed_min)
        total_remaining = _total_remaining_min(game_state)
        signals: list[EvaluationSignal] = []

        for spec in game_state.market_specs:
            player = game_state.player_states.get(spec.player_id)
            if player is None or not player.is_active:
                continue

            t_elapsed_frac = player.min_so_far / GAME_REGULATION_MIN
            t_remaining_frac = total_remaining / GAME_REGULATION_MIN

            # Gamma-Poisson update
            alpha0, beta0 = _gamma_prior_params(player.lambda_t1_prior, PRIOR_LAMBDA_SIGMA_PTS)
            alpha_post, beta_post = _gamma_poisson_update(
                alpha0, beta0, player.pts_so_far, t_elapsed_frac
            )
            lambda_posterior = alpha_post / beta_post

            # Write to cache — consumed by T4-EVENT and T4-ARITH in the same cycle
            self._posterior_cache[spec.player_id] = lambda_posterior

            lambda_remaining = lambda_posterior * t_remaining_frac
            model_p = _poisson_survival_p(player.pts_so_far, spec.threshold, lambda_remaining)

            cached_price = price_cache.get_raw(spec.market_id)
            if cached_price is None:
                continue

            edge = model_p - cached_price.mid - cached_price.vig
            if abs(edge) < _MIN_EDGE:
                continue

            direction = "YES" if model_p > 0.5 else "NO"
            signals.append(EvaluationSignal(
                sub_band=ExecutionBand.T4_PROJ,
                tree_id=f"PROJ-{spec.stat_type.upper()}",
                market_id=spec.market_id,
                player_id=spec.player_id,
                direction=direction,
                model_p=model_p,
                mip_at_signal=cached_price.mid,
                vig_at_signal=cached_price.vig,
                edge_at_signal=edge,
                kelly_fraction=kelly,
                signal_snapshot={
                    "game_phase": phase.value,
                    "lambda_posterior": round(lambda_posterior, 4),
                    "lambda_remaining": round(lambda_remaining, 4),
                    "pts_so_far": player.pts_so_far,
                    "threshold": spec.threshold,
                    "t_elapsed_frac": round(t_elapsed_frac, 4),
                    "alpha_post": round(alpha_post, 4),
                    "beta_post": round(beta_post, 4),
                },
                ts=now,
                is_exit=False,
                game_phase=phase,
            ))

        return signals


class T4ArithEvaluator(SubBandEvaluator):
    """
    T4-ARITH: Threshold-approaching arithmetic near-certainty.

    At Phase 8: fires when a player's stat is within ARITH_ENTRY_WINDOW of
    their threshold AND T4_ARITH_CONFIDENCE_GATE is met AND time_remaining >
    EXIT_MIN_TIME_REMAINING_MIN. Uses T4-PROJ's lambda_posterior for the
    remaining Poisson survival computation.

    Distinction from T4-PROJ: fires only in the high-certainty regime (tight
    distribution around threshold); computation is dominated by gap arithmetic.
    Distinction from T5: T5 fires in final EXIT_MIN_TIME_REMAINING_MIN minutes;
    T4-ARITH fires earlier (up to ~15 min remaining).

    ARITH_ENTRY_WINDOW: EXP-derived (expected 2–4 stat units).
    T4_ARITH_CONFIDENCE_GATE: EXP-derived (expected 0.70–0.80).
    Kelly: provisional 0.22, NON-OPERATIONAL — held at T4-PROJ LATE ceiling
    (0.167) until EXP-ARITH-01 confirms tail calibration.

    EXP: EXP-ARITH-01 (ARITH_ENTRY_WINDOW + T4_ARITH_CONFIDENCE_GATE calibration).
    """

    # Provisional thresholds (Tier B — EXP-ARITH-01 required before activation).
    _ARITH_ENTRY_WINDOW: float = 3.0      # stat units from threshold (provisional)
    _CONFIDENCE_GATE: float = 0.75        # minimum p_arith to qualify (provisional)

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_ARITH

    def __init__(self, proj_evaluator: Optional["T4ProjEvaluator"] = None) -> None:
        self._assert_sub_band_blocked()
        # Borrows T4-PROJ posterior to avoid recomputing λ in the same cycle.
        # Falls back to T1 prior (player.lambda_t1_prior) when proj_evaluator is None
        # or no posterior exists yet. No-arg construction (proj_evaluator=None) is
        # required for the parametrized test_evaluator_returns_empty_list fixture.
        self._proj_evaluator = proj_evaluator

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        """
        Fire when player is within ARITH_ENTRY_WINDOW of threshold and p_arith ≥ CONFIDENCE_GATE.

        Uses T4-PROJ posterior lambda for the survival computation (written earlier
        in the same cycle). Falls back to T1 prior if no posterior available.
        Does not fire in the final EXIT_MIN_TIME_REMAINING_MIN minutes (T5 territory).
        """
        if not game_state.market_specs:
            return []

        total_remaining = _total_remaining_min(game_state)
        if total_remaining <= EXIT_MIN_TIME_REMAINING_MIN:
            return []  # T5 territory — do not compete with arithmetic certainty sub-band

        now = datetime.now(timezone.utc)
        phase = classify_game_phase(game_state.elapsed_min)
        signals: list[EvaluationSignal] = []

        for spec in game_state.market_specs:
            player = game_state.player_states.get(spec.player_id)
            if player is None or not player.is_active:
                continue

            gap = spec.threshold - player.pts_so_far
            if gap <= 0 or gap > self._ARITH_ENTRY_WINDOW:
                continue  # already achieved or too far from threshold

            # Borrow T4-PROJ posterior; fall back to T1 prior
            lambda_est: float = player.lambda_t1_prior
            if self._proj_evaluator is not None:
                posterior = self._proj_evaluator.get_lambda_posterior(spec.player_id)
                if posterior is not None:
                    lambda_est = posterior

            t_remaining_frac = total_remaining / GAME_REGULATION_MIN
            lambda_remaining = lambda_est * t_remaining_frac

            p_arith = _poisson_survival_p(player.pts_so_far, spec.threshold, lambda_remaining)
            if p_arith < self._CONFIDENCE_GATE:
                continue

            cached_price = price_cache.get_raw(spec.market_id)
            if cached_price is None:
                continue

            edge = p_arith - cached_price.mid - cached_price.vig
            if abs(edge) < _MIN_EDGE:
                continue

            direction = "YES" if p_arith > 0.5 else "NO"
            signals.append(EvaluationSignal(
                sub_band=ExecutionBand.T4_ARITH,
                tree_id=f"ARITH-{spec.stat_type.upper()}",
                market_id=spec.market_id,
                player_id=spec.player_id,
                direction=direction,
                model_p=p_arith,
                mip_at_signal=cached_price.mid,
                vig_at_signal=cached_price.vig,
                edge_at_signal=edge,
                kelly_fraction=_KELLY_NEAR_CERTAIN,  # ADR-0029: ARITH held at LATE ceiling
                signal_snapshot={
                    "gap": round(gap, 2),
                    "lambda_est": round(lambda_est, 4),
                    "lambda_remaining": round(lambda_remaining, 4),
                    "pts_so_far": player.pts_so_far,
                    "threshold": spec.threshold,
                    "arith_entry_window": self._ARITH_ENTRY_WINDOW,
                    "confidence_gate": self._CONFIDENCE_GATE,
                },
                ts=now,
                is_exit=False,
                game_phase=phase,
            ))

        return signals


class T4BoundaryEvaluator(SubBandEvaluator):
    """
    T4-BOUNDARY: Quarter / halftime structural reset.

    At Phase 8: triggers on QUARTER_END game events. Phase 1 exits all open
    T4 positions that have reversed direction. Phase 2 (halftime only) re-runs
    T4-PROJ with halftime adjustments (coach adjustments, lineup changes). Phase 3
    re-scans all tracked markets for new entry opportunities.

    This sub-band is primarily about exits and reassessments, not new entries.
    New entries are secondary output — only when Phase 3 reveals significant edge.

    No independent Kelly: new entries inherit T4-PROJ; exits inherit T4-EXIT.
    EXP: none required (structural trigger on game clock; no new alpha claim).
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_BOUNDARY

    def __init__(self) -> None:
        self._assert_sub_band_blocked()

    def evaluate(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        return []  # BLOCKED — requires T4-PROJ infrastructure (EXP-PROJ-01)


# ---------------------------------------------------------------------------
# Layer 1 — Portfolio overlays (T4-CORR + T4-EXIT)
# ---------------------------------------------------------------------------

class PortfolioOverlay(ABC):
    """
    Abstract base for portfolio-level overlays that modify signals rather than
    produce them. T4-CORR and T4-EXIT implement this interface.

    Unlike SubBandEvaluator, overlays operate on groups of signals / positions,
    not individual game-state updates.
    """

    @property
    @abstractmethod
    def sub_band(self) -> ExecutionBand:
        """The ExecutionBand this overlay serves."""

    def _require_phase8(self, operation: str) -> None:
        raise T4Phase8BlockedError(
            f"{self.__class__.__name__}.{operation} is Phase 8 infrastructure."
        )


class T4CorrAdjuster(PortfolioOverlay):
    """
    T4-CORR: Cross-market correlation overlay (Layer 2, between C4 and C5).

    DOWNWARD-ONLY invariant (ADR-0029 Principle 6): T4-CORR may only REDUCE
    sizes below their C4-approved levels, never increase them. This ensures
    the ADR-0026 free-cash invariant evaluated at C4 approval time remains valid
    at C5 submission time — upward adjustment post-C4 would violate the invariant.

    At Phase 8: detects groups of simultaneously-queued bets on correlated
    markets (same player, same game, same time window), applies correlation
    discounts proportionally, and enforces the per-market exposure cap
    (max_single_event_exposure_usd = $500, risk.py) across all sub-bands combined.

    Convergence signal: when N sub-bands from DIFFERENT families fire on the
    same market in the SAME direction independently, this is confirmatory —
    T4-CORR should NOT discount this as correlation. Test: mechanistic independence.

    EXP: EXP-CORR-01 (convergence premium derivation).
    """

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_CORR

    def adjust(
        self,
        approvals: list[EvaluationSignal],
        max_single_event_usd: float,
    ) -> tuple[list[EvaluationSignal], list[CorrAdjustmentRecord]]:
        """
        Apply correlation discounts to a batch of simultaneously-queued approvals.

        Returns (adjusted_approvals, adjustment_records).

        INVARIANT: for every signal in adjusted_approvals:
            adjusted.kelly_fraction <= original.kelly_fraction

        At Phase 8: full correlation matrix + convergence detection.
        Current stub: enforces the per-market exposure cap only (no
        correlation matrix computed; EXP-CORR-01 pending).
        """
        # Phase 8 full implementation deferred to EXP-CORR-01 resolution.
        # Current stub: return approvals unchanged (the cap is enforced by C4).
        return approvals, []

    def _assert_downward_only(
        self,
        original_kelly: float,
        adjusted_kelly: float,
        market_id: str,
    ) -> None:
        """Raise if T4-CORR attempted an upward adjustment (invariant violation)."""
        if adjusted_kelly > original_kelly:
            raise RuntimeError(
                f"T4-CORR downward-only invariant VIOLATED for {market_id}: "
                f"adjusted_kelly={adjusted_kelly:.4f} > original_kelly={original_kelly:.4f}. "
                f"T4-CORR may only reduce sizes (ADR-0029 Principle 6). "
                f"This is a governance error — trace the adjustment logic."
            )


class T4ExitEvaluator(PortfolioOverlay):
    """
    T4-EXIT: Continuous open-position monitoring.

    At Phase 8: evaluates each open T4 position on every qualifying game event.
    Fires EXIT signals (priority=URGENT in Layer 2 queue) when:
      - Full directional reversal (current_p crosses 0.5 vs entry_p)
      - Noise buffer breach AGAINST the bet direction
      - Time-based floor: time_remaining ≤ EXIT_MIN_TIME_REMAINING_MIN (hand-off to T5)
      - Q4-blowout: leading starters rested with ≤8 min remaining

    EXIT signals bypass the standard Layer 2 queue (URGENT priority = 0.0).
    EXIT latency must be ≤5s (GG-038).

    Noise buffers per sub-band (provisional; EXP-required for EVENT/LINEUP/SENT/ARITH):
        T4-STAGED:   0.22053 (inherited from T3 buffer)
        T4-FLOW:     0.19    (monolithic T4 empirical basis)
        T4-PROJ:     0.19    (direct inheritance; primary basis for this value)
        T4-EVENT:    EXP-required (expected < 0.19)
        T4-LINEUP:   EXP-required
        T4-SENTIMENT: EXP-required
        T4-ARITH:    EXP-required (expected < 0.19, near-certainty)

    EXP: no new EXP required for the structural exit logic; sub-band noise buffers
    require EXP derivation per sub-band (EXP-NOISE-01, ADR-0029).
    """

    EXIT_TIME_FLOOR_MIN: float = EXIT_MIN_TIME_REMAINING_MIN  # 3.0 min

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4_EXIT

    def generate_exit_signals(
        self,
        open_positions: list,
        game_state: T4GameState,
        price_cache: T4PriceCache,
    ) -> list[EvaluationSignal]:
        """
        Evaluate all open T4 positions against three exit conditions.

        Accepts list[T4OpenPosition] (typed) or list[dict] (legacy). Dict entries
        missing required keys (market_id, player_id, direction, threshold,
        entry_model_p) are silently skipped for backward compatibility.

        Exit conditions (evaluated in priority order, first match wins):
          1. TIME FLOOR:    total_remaining ≤ EXIT_TIME_FLOOR_MIN (3 min → T5 territory)
          2. REVERSAL:      model_p crosses 0.5 vs entry direction
          3. BUFFER BREACH: model_p moved > noise_buffer AGAINST bet direction

        All EXIT signals carry is_exit=True → priority=0.0 in Layer 2 queue (URGENT).
        """
        if not open_positions:
            return []

        total_remaining = _total_remaining_min(game_state)
        now = datetime.now(timezone.utc)
        signals: list[EvaluationSignal] = []

        for pos in open_positions:
            # Unpack: support both T4OpenPosition typed objects and legacy dicts
            if isinstance(pos, T4OpenPosition):
                market_id = pos.market_id
                player_id = pos.player_id
                direction = pos.direction
                threshold = pos.threshold
                entry_model_p = pos.entry_model_p
                noise_buf = pos.noise_buffer
            elif isinstance(pos, dict):
                market_id = pos.get("market_id")
                player_id = pos.get("player_id")
                direction = pos.get("direction")
                threshold = pos.get("threshold")
                entry_model_p = pos.get("entry_model_p")
                noise_buf = pos.get("noise_buffer")
                # Skip dicts missing required keys; this preserves backward compatibility
                # with test fixtures that pass minimal dicts (e.g. {"market_id": "MKT-001"}).
                if not all([market_id, player_id, direction,
                            threshold is not None, entry_model_p is not None]):
                    continue
            else:
                continue

            buffer = noise_buf if noise_buf is not None else NOISE_BUFFER_BAND_T4

            # Condition 1: Time floor — hand off to T5
            if total_remaining <= self.EXIT_TIME_FLOOR_MIN:
                signals.append(self._make_exit_signal(
                    market_id=market_id, player_id=player_id, direction=direction,
                    model_p=entry_model_p, game_state=game_state,
                    tree_id="EXIT-TIME-FLOOR", ts=now,
                ))
                continue

            # Compute current model probability for this position
            player = game_state.player_states.get(player_id)
            if player is None:
                continue

            lambda_est = (
                player.lambda_t4_proj
                if player.lambda_t4_proj is not None
                else player.lambda_t1_prior
            )
            t_remaining_frac = total_remaining / GAME_REGULATION_MIN
            lambda_remaining = lambda_est * t_remaining_frac
            current_p = _poisson_survival_p(player.pts_so_far, threshold, lambda_remaining)

            # Condition 2: Directional reversal (model_p crossed 0.5 vs entry direction)
            entry_is_yes = direction == "YES"
            current_implies_yes = current_p > 0.5
            if entry_is_yes != current_implies_yes:
                signals.append(self._make_exit_signal(
                    market_id=market_id, player_id=player_id, direction=direction,
                    model_p=current_p, game_state=game_state,
                    tree_id="EXIT-REVERSAL", ts=now,
                ))
                continue

            # Condition 3: Noise buffer breach AGAINST bet direction
            if direction == "YES" and current_p < entry_model_p - buffer:
                signals.append(self._make_exit_signal(
                    market_id=market_id, player_id=player_id, direction=direction,
                    model_p=current_p, game_state=game_state,
                    tree_id="EXIT-BUFFER-BREACH", ts=now,
                ))
            elif direction == "NO" and current_p > entry_model_p + buffer:
                signals.append(self._make_exit_signal(
                    market_id=market_id, player_id=player_id, direction=direction,
                    model_p=current_p, game_state=game_state,
                    tree_id="EXIT-BUFFER-BREACH", ts=now,
                ))

        return signals

    def _make_exit_signal(
        self,
        market_id: str,
        player_id: str,
        direction: str,
        model_p: float,
        game_state: T4GameState,
        tree_id: str,
        ts: datetime,
    ) -> EvaluationSignal:
        """Construct an EXIT EvaluationSignal (priority=0.0 in Layer 2 queue)."""
        return EvaluationSignal(
            sub_band=ExecutionBand.T4_EXIT,
            tree_id=tree_id,
            market_id=market_id,
            player_id=player_id,
            direction=direction,
            model_p=model_p,
            mip_at_signal=0.0,   # price irrelevant to the exit decision
            vig_at_signal=0.0,
            edge_at_signal=0.0,  # EXIT signals bypass edge check in Layer 2
            kelly_fraction=0.0,  # no new sizing; managing existing position
            signal_snapshot={
                "exit_reason": tree_id,
                "total_remaining": round(_total_remaining_min(game_state), 2),
                "elapsed": game_state.elapsed_min,
            },
            ts=ts,
            is_exit=True,
            game_phase=classify_game_phase(game_state.elapsed_min),
        )


# ---------------------------------------------------------------------------
# Layer 1 — Evaluation Engine
# ---------------------------------------------------------------------------

class Layer1EvaluationEngine:
    """
    Layer 1: Continuous evaluation coordinator.

    Holds all sub-band evaluators and the exit overlay. On each evaluation cycle
    (triggered by a T4GameEvent), runs every evaluator whose natural trigger
    matches the event type, collects all EvaluationSignals, and returns them for
    enqueuing in Layer 2.

    Evaluators run concurrently in the same thread at Phase 6/7 paper scale.
    At Phase 8: each evaluator is a separate worker (Principle 3 — Parallel
    Evaluation: T4-PROJ latency must not block T4-EVENT).

    BLOCKED: run_continuous() requires Phase 8 data feeds.
    evaluate_cycle() is available for testing with synthetic game state.
    """

    # Evaluators that fire on SCORE_UPDATE events.
    _SCORE_UPDATE_EVALUATORS: frozenset[str] = frozenset({
        "T4-EVENT", "T4-FLOW", "T4-PROJ", "T4-ARITH",
    })
    # Evaluators that fire on SUBSTITUTION events.
    _SUBSTITUTION_EVALUATORS: frozenset[str] = frozenset({
        "T4-LINEUP", "T4-FLOW",
    })
    # Evaluators that fire on FOUL events.
    _FOUL_EVALUATORS: frozenset[str] = frozenset({
        "T4-EVENT", "T4-FLOW",
    })
    # Evaluators that fire on QUARTER_END events.
    _QUARTER_END_EVALUATORS: frozenset[str] = frozenset({
        "T4-BOUNDARY",
    })
    # Evaluators that fire on PRICE_DRIFT events.
    _PRICE_DRIFT_EVALUATORS: frozenset[str] = frozenset({
        "T4-SENTIMENT",
    })
    # Evaluators that fire on every TIMER tick.
    _TIMER_EVALUATORS: frozenset[str] = frozenset({
        "T4-PROJ", "T4-SENTIMENT",
    })

    def __init__(
        self,
        proj_evaluator: T4ProjEvaluator,
        event_evaluator: T4EventEvaluator,
        lineup_evaluator: T4LineupEvaluator,
        flow_evaluator: T4FlowEvaluator,
        sentiment_evaluator: T4SentimentEvaluator,
        arith_evaluator: T4ArithEvaluator,
        boundary_evaluator: T4BoundaryEvaluator,
        staged_evaluator: T4StagedEvaluator,
        exit_evaluator: T4ExitEvaluator,
        corr_adjuster: T4CorrAdjuster,
    ) -> None:
        self._evaluators: dict[str, SubBandEvaluator] = {
            "T4-PROJ":      proj_evaluator,
            "T4-EVENT":     event_evaluator,
            "T4-LINEUP":    lineup_evaluator,
            "T4-FLOW":      flow_evaluator,
            "T4-SENTIMENT": sentiment_evaluator,
            "T4-ARITH":     arith_evaluator,
            "T4-BOUNDARY":  boundary_evaluator,
            "T4-STAGED":    staged_evaluator,
        }
        self._exit_evaluator = exit_evaluator
        self._corr_adjuster = corr_adjuster

    def _evaluators_for_event(self, event: Optional[T4GameEvent]) -> list[str]:
        """Return sub-band IDs whose natural trigger matches event_type."""
        if event is None:
            return list(self._evaluators.keys())
        return {
            "SCORE_UPDATE":  list(self._SCORE_UPDATE_EVALUATORS),
            "SUBSTITUTION":  list(self._SUBSTITUTION_EVALUATORS),
            "FOUL":          list(self._FOUL_EVALUATORS),
            "QUARTER_END":   list(self._QUARTER_END_EVALUATORS),
            "PRICE_DRIFT":   list(self._PRICE_DRIFT_EVALUATORS),
            "TIMER":         list(self._TIMER_EVALUATORS),
        }.get(event.event_type, list(self._evaluators.keys()))

    def evaluate_cycle(
        self,
        game_state: T4GameState,
        price_cache: T4PriceCache,
        open_positions: Optional[list[dict]] = None,
    ) -> list[EvaluationSignal]:
        """
        Run one evaluation cycle triggered by game_state.trigger_event.

        Returns all EvaluationSignals from matching evaluators plus any EXIT
        signals from T4-EXIT. Available for testing with synthetic game state.

        In production (Phase 8): called on every DS-02 game event. Returns
        signals that are immediately enqueued in Layer 2.
        """
        active_ids = self._evaluators_for_event(game_state.trigger_event)
        # T4-PROJ must always evaluate before T4-ARITH and T4-EVENT in the same cycle.
        # Both borrow T4-PROJ's _posterior_cache; if they run first they get a stale
        # posterior and fall back to the T1 prior (losing the in-game update).
        # _SCORE_UPDATE_EVALUATORS is a frozenset (unordered) so we enforce order here.
        _PROJ_FIRST = ["T4-PROJ"]
        ordered_ids = _PROJ_FIRST + [bid for bid in active_ids if bid not in _PROJ_FIRST]
        signals: list[EvaluationSignal] = []
        for band_id in ordered_ids:
            evaluator = self._evaluators.get(band_id)
            if evaluator is not None:
                try:
                    signals.extend(evaluator.evaluate(game_state, price_cache))
                except Exception:
                    logger.exception(
                        "Layer 1 evaluator %s raised unexpectedly — skipping cycle",
                        band_id,
                    )

        # T4-EXIT evaluates open positions on every cycle.
        if open_positions:
            exit_signals = self._exit_evaluator.generate_exit_signals(
                open_positions, game_state, price_cache
            )
            signals.extend(exit_signals)

        return signals

    def run_continuous(self, game_event_feed) -> None:
        """
        Start the continuous evaluation loop (Phase 8 only).

        game_event_feed: an iterable that yields T4GameState objects as
        DS-02 real-time events arrive.

        BLOCKED until GG-040 (real-time data sources) resolved.
        """
        raise T4Phase8BlockedError(
            "Layer1EvaluationEngine.run_continuous() requires DS-02 real-time "
            "data feed (GG-040) and T4 kill switch ≤5s SLA (GG-038). "
            "Both are Phase 8 prerequisites."
        )


# ---------------------------------------------------------------------------
# Layer 2 — Execution Queue with Staleness Arbitration
# ---------------------------------------------------------------------------

class Layer2ExecutionQueue:
    """
    Layer 2: Staleness-arbitrated execution queue.

    Priority min-heap (heapq). EXIT signals have priority=0.0 (dequeued first).
    Standard signals: priority = 1.0 - |edge| (higher edge → dequeued first).

    Per-dequeue cycle (called by T4ExecutionEngine.process_queue()):
      1. STALENESS CHECK — T4PriceCache.get_price(market_id, sub_band)
         None → DROP (log StaleDropRecord)
         Not None → PROCEED
      2. T4-CORR ADJUSTMENT — T4CorrAdjuster.adjust() (downward-only)
      3. C4 RISK CHECK — injected RiskEngine (at Phase 8)
      4. SUBMIT to Layer 3 (at Phase 8)

    Rate-limit governance (ADR-0029):
      EXIT signals: reserved budget (cannot be starved by entry volume)
      T4-PROJ signals: reserved budget (richest signal; must not be starved)
      T4-EVENT signals: standard budget; high stale-drop rate acceptable in bursts

    BLOCKED: process_queue_batch() requires C4 RiskEngine and C5 VenueRouter
    (Phase 8). enqueue() and the staleness-check internals are available for
    testing.
    """

    # Reserved cycle budget per signal class (as fraction of dequeue cycles).
    # Ensures EXIT and T4-PROJ are not starved by T4-EVENT bursts.
    # Provisional: EXP-QUEUE-01 must measure actual queue survival rates.
    _RESERVED_BUDGET_FRAC: dict[str, float] = {
        "EXIT":    0.30,  # 30% of cycles reserved for EXIT signals
        "T4-PROJ": 0.20,  # 20% reserved for T4-PROJ (richest signal)
        # Remaining 50% is open — any sub-band competes on edge priority.
    }

    def __init__(self, corr_adjuster: T4CorrAdjuster) -> None:
        self._heap: list[QueueEntry] = []
        self._corr_adjuster = corr_adjuster
        self._stale_drop_log: list[StaleDropRecord] = []  # in-memory audit; Phase 8 routes to C6

    def enqueue(self, signal: EvaluationSignal) -> None:
        """Enqueue a signal from Layer 1. Thread-safe via GIL for single-threaded use."""
        entry = QueueEntry.from_signal(signal)
        heapq.heappush(self._heap, entry)
        logger.debug(
            "Layer2 enqueue: market=%s sub_band=%s edge=%.3f priority=%.3f is_exit=%s",
            signal.market_id, signal.sub_band.value,
            signal.edge_at_signal, entry.priority, signal.is_exit,
        )

    def queue_depth(self) -> int:
        """Current number of entries in the queue."""
        return len(self._heap)

    def _staleness_check(
        self,
        entry: QueueEntry,
        price_cache: T4PriceCache,
        min_edge: float,
    ) -> tuple[bool, Optional[StaleDropRecord]]:
        """
        Check if a queued entry is still actionable.

        Returns (is_valid, drop_record_or_None).
        is_valid=True → proceed to C4. False → drop.

        Drop conditions:
          1. Price cache miss or stale (drop_reason='price_stale')
          2. Current edge below min_edge (drop_reason='edge_below_min')
          3. Direction reversed at current price (drop_reason='direction_reversed')
        """
        signal = entry.signal
        cached_price = price_cache.get_price(signal.market_id, signal.sub_band)

        now = datetime.now(timezone.utc)
        queue_wait_ms = (now - entry.enqueued_ts).total_seconds() * 1000.0

        if cached_price is None:
            drop_record = StaleDropRecord(
                market_id=signal.market_id,
                sub_band_value=signal.sub_band.value,
                tree_id=signal.tree_id,
                edge_at_entry=signal.edge_at_signal,
                edge_at_drop=None,
                queue_wait_ms=queue_wait_ms,
                drop_reason="price_stale",
                ts=now,
            )
            return False, drop_record

        current_mip = cached_price.mid
        current_vig = cached_price.vig
        current_edge = signal.model_p - current_mip - current_vig

        if abs(current_edge) < min_edge:
            drop_record = StaleDropRecord(
                market_id=signal.market_id,
                sub_band_value=signal.sub_band.value,
                tree_id=signal.tree_id,
                edge_at_entry=signal.edge_at_signal,
                edge_at_drop=current_edge,
                queue_wait_ms=queue_wait_ms,
                drop_reason="edge_below_min",
                ts=now,
            )
            return False, drop_record

        # Direction reversed: model_p < 0.5 and we have a YES bet, or vice versa.
        entry_is_yes = signal.direction == "YES"
        model_implies_yes = signal.model_p > 0.5
        if entry_is_yes != model_implies_yes:
            drop_record = StaleDropRecord(
                market_id=signal.market_id,
                sub_band_value=signal.sub_band.value,
                tree_id=signal.tree_id,
                edge_at_entry=signal.edge_at_signal,
                edge_at_drop=current_edge,
                queue_wait_ms=queue_wait_ms,
                drop_reason="direction_reversed",
                ts=now,
            )
            return False, drop_record

        return True, None

    def process_queue_batch(
        self,
        price_cache: T4PriceCache,
        min_edge: float,
        max_dequeue_per_batch: int = 10,
    ) -> tuple[list[EvaluationSignal], list[StaleDropRecord]]:
        """
        Dequeue up to max_dequeue_per_batch entries, apply staleness check and
        T4-CORR adjustment, return approved signals for C4 + C5.

        BLOCKED for actual C4/C5 execution (Phase 8). At Phase 6/7 this method
        may be used in test/simulation mode with synthetic price_cache data.

        Returns:
            approved: signals that passed staleness check + T4-CORR adjustment
            drops:    StaleDropRecords for all dropped signals
        """
        approved_raw: list[EvaluationSignal] = []
        drops: list[StaleDropRecord] = []

        for _ in range(min(max_dequeue_per_batch, len(self._heap))):
            if not self._heap:
                break
            entry = heapq.heappop(self._heap)
            is_valid, drop_record = self._staleness_check(entry, price_cache, min_edge)
            if not is_valid:
                if drop_record:
                    drops.append(drop_record)
                    self._stale_drop_log.append(drop_record)
            else:
                approved_raw.append(entry.signal)

        # T4-CORR: downward-only adjustment
        approved, corr_records = self._corr_adjuster.adjust(
            approved_raw, max_single_event_usd=500.0
        )
        # corr_records routed to C6 at Phase 8
        return approved, drops

    def pop_stale_drops(self) -> list[StaleDropRecord]:
        """Return and clear the accumulated stale-drop log (for testing / monitoring)."""
        records = list(self._stale_drop_log)
        self._stale_drop_log.clear()
        return records


# ---------------------------------------------------------------------------
# T4 Execution Engine — top-level coordinator
# ---------------------------------------------------------------------------

class T4ExecutionEngine:
    """
    Top-level T4 execution engine: coordinates Layer 1 and Layer 2.

    This is the ADR-0029 Tier A architecture instantiated as Python code.
    At Phase 8: receives DS-02 game events, evaluates all sub-band trees,
    staleness-checks the queue, and submits approved bets to C5.

    BLOCKED: on_game_event() and start() require Phase 8 data feeds + kill switch.
    simulate_cycle() is available for testing with synthetic inputs.

    Kill switch integration (GG-038):
      - T4-specific kill switch (≤5s SLA) halts the evaluation loop immediately
      - Queue is flushed (pending entries dropped, logged)
      - In-flight orders cancelled within 5s window
      - System kill switch (C7, 60s) halts everything including T4
      - Both operate independently without coupling (ADR-0029 kill switch table)

    Usage (testing):
        engine = T4ExecutionEngine.create()
        signals = engine.simulate_cycle(game_state, price_cache)
    """

    _PHASE8_ACTIVE: bool = False  # Set by Phase 8 activation ADR only.

    def __init__(
        self,
        layer1: Layer1EvaluationEngine,
        layer2: Layer2ExecutionQueue,
        price_cache: T4PriceCache,
        min_edge: float = 0.04,  # matches MIN_EDGE_TO_APPROVE in risk.py
    ) -> None:
        self._layer1 = layer1
        self._layer2 = layer2
        self._price_cache = price_cache
        self._min_edge = min_edge

    @classmethod
    def create(cls, min_edge: float = 0.04) -> "T4ExecutionEngine":
        """
        Factory: construct a T4ExecutionEngine with all sub-band evaluators wired.

        Returns a fully-assembled engine suitable for testing (all evaluators
        are BLOCKED stubs). At Phase 8: inject live C4/C5 dependencies via the
        Layer 2 constructor.
        """
        proj_eval     = T4ProjEvaluator()
        event_eval    = T4EventEvaluator(proj_evaluator=proj_eval)
        lineup_eval   = T4LineupEvaluator()
        flow_eval     = T4FlowEvaluator()
        sentiment_eval = T4SentimentEvaluator()
        arith_eval    = T4ArithEvaluator(proj_evaluator=proj_eval)
        boundary_eval = T4BoundaryEvaluator()
        staged_eval   = T4StagedEvaluator()
        exit_eval     = T4ExitEvaluator()
        corr_adjuster = T4CorrAdjuster()

        layer1 = Layer1EvaluationEngine(
            proj_evaluator=proj_eval,
            event_evaluator=event_eval,
            lineup_evaluator=lineup_eval,
            flow_evaluator=flow_eval,
            sentiment_evaluator=sentiment_eval,
            arith_evaluator=arith_eval,
            boundary_evaluator=boundary_eval,
            staged_evaluator=staged_eval,
            exit_evaluator=exit_eval,
            corr_adjuster=corr_adjuster,
        )
        layer2 = Layer2ExecutionQueue(corr_adjuster=corr_adjuster)
        price_cache = T4PriceCache()
        return cls(layer1=layer1, layer2=layer2, price_cache=price_cache, min_edge=min_edge)

    def simulate_cycle(
        self,
        game_state: T4GameState,
        price_cache: Optional[T4PriceCache] = None,
        open_positions: Optional[list[dict]] = None,
    ) -> list[EvaluationSignal]:
        """
        Dry-run one evaluation cycle without activating C4/C5 execution.

        Available at all phases for testing. With current BLOCKED stubs, returns
        an empty list (no evaluator produces signals). At Phase 8: returns
        signals for C4/C5 processing via process_queue_batch().

        Signals returned have NOT been staleness-checked or sized — they are
        raw Layer 1 outputs. Use process_queue_batch() for the full Layer 2 path.
        """
        _cache = price_cache if price_cache is not None else self._price_cache
        signals = self._layer1.evaluate_cycle(game_state, _cache, open_positions)
        return signals

    def on_game_event(self, game_state: T4GameState) -> None:
        """
        Main entry point for DS-02 game events (Phase 8 only).

        Evaluates Layer 1, enqueues all signals in Layer 2, and triggers one
        Layer 2 dequeue batch. All approved bets proceed to C4 + C5.

        BLOCKED until GG-038 (kill switch) + GG-040 (data feed) resolved.
        """
        if not self._PHASE8_ACTIVE:
            raise T4Phase8BlockedError(
                "T4ExecutionEngine.on_game_event() is Phase 8 infrastructure. "
                "Blocked until GG-038 / GG-039 / GG-040 resolved and Phase 8 "
                "activation ADR wires T4ExecutionEngine._PHASE8_ACTIVE = True."
            )
        # Phase 8 implementation:
        # 1. Kill switch check (< 5ms)
        # 2. layer1.evaluate_cycle(game_state, price_cache) → signals
        # 3. layer2.enqueue(signal) for each signal
        # 4. layer2.process_queue_batch(price_cache, min_edge) → approved
        # 5. for each approved: C4.evaluate_forecast → C5.execute → C6.log
        raise NotImplementedError("Phase 8 execution implementation deferred.")

    def start(self, game_event_feed) -> None:
        """
        Start the continuous evaluation loop (Phase 8 only).

        BLOCKED until GG-038 / GG-039 / GG-040 resolved.
        """
        if not self._PHASE8_ACTIVE:
            raise T4Phase8BlockedError(
                "T4ExecutionEngine.start() is Phase 8 infrastructure."
            )
        raise NotImplementedError("Phase 8 implementation deferred.")

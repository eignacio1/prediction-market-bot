"""
T4M-ARITH / T4M-FLOW — MLB-native T4 sub-band evaluators (ADR-0039, T-219)
============================================================================
Scope: SESSION 109/T-219, sign-off "T-4 PROJ / T-4 ARITH / T-4 FLOW + T-4
BLOWOUT can be proceed with." Only T4M-ARITH and T4M-FLOW live here.
T4M-PROJ is NOT a new build — it is the existing flat Binomial model in
run_t4_mlb_live.py, relabeled (see that module's docstring and
execution_bands.py::T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_PROJ]).

Governance (mirrors ADR-0029/t4_execution_engine.py exactly — same two-tier
gate, not a new mechanism):
  - T4_MLB_SUBBAND_REGISTRY[sub_band].status must be "BLOCKED" for both
    evaluators here, checked at construction time by _assert_sub_band_blocked().
  - This governs construction/testing only. evaluate() may run real math
    against synthetic T4MlbGameContext in tests. There is no live wiring:
    no Layer 1/2 queue engine, no ESPN score-diff extraction, no C4/C5
    hookup. Standing this up is separate, EXP-gated, Phase 8 follow-up
    work (EXP-ARITH-MLB-01, EXP-FLOW-MLB-01).
  - Reuses run_t4_mlb_live.py's Binomial math (p_hits_gte_threshold,
    _compute_ab_remaining) rather than reimplementing it — same prior,
    same AB-remaining estimator T4M-PROJ already uses in production.

Deliberately excluded from this module (not authorized this session):
T4M-BOUNDARY and the rest of ADR-0039's Tier B roster (T4M-EVENT,
T4M-LINEUP, T4M-PITCHER, T4M-STAGED, T4M-CORR, T4M-EXIT).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from prediction_market_bot.execution_bands import (
    ExecutionBand,
    T4_MLB_SUBBAND_REGISTRY,
)
from prediction_market_bot.run_t4_mlb_live import (
    _compute_ab_remaining,
    p_hits_gte_threshold,
)
from prediction_market_bot.t4_execution_engine import EvaluationSignal
from prediction_market_bot.t4_price_cache import CachedPrice, T4Phase8BlockedError

# ---------------------------------------------------------------------------
# Provisional, EXP-gated constants (Tier B — no MLB-specific derivation exists
# yet for any of these; do not treat as calibrated). See T4_MLB_SUBBAND_REGISTRY
# for the exp_gate that must clear before either evaluator leaves BLOCKED.
# ---------------------------------------------------------------------------

# T4M-ARITH: near-certain band between the flat model's hard boundaries
# (h_so_far >= threshold -> p=1.0; h_needed > ab_remaining -> p=0.0).
_ARITH_ENTRY_WINDOW: int = 1        # hits needed, in AB units (EXP-ARITH-MLB-01)
_ARITH_CONFIDENCE_GATE: float = 0.80  # minimum p_arith to qualify (EXP-ARITH-MLB-01)

# T4M-FLOW / FLOW-BLOWOUT: sustained run-differential context multiplier.
# Borrows NBA T4-FLOW's order of magnitude (BLOWOUT_SCORE_THRESHOLD=20 pts of
# ~100 pt game -> ~6 runs of a ~9 run MLB game; BLOWOUT_SUSTAIN_MIN=2.0 min ->
# 2 full innings). No MLB-specific precedent exists (EXP-FLOW-MLB-01).
_BLOWOUT_RUN_THRESHOLD: int = 6
_BLOWOUT_SUSTAIN_INNINGS: int = 2
_BLOWOUT_TRAILING_MULT: float = 1.15   # trailing-team batter: garbage-time AB uplift
_BLOWOUT_LEADING_MULT: float = 0.80    # leading-team batter: early-pull discount

# Minimum |edge| to fire, shared by both evaluators. Borrowed from NBA's
# T4 _MIN_EDGE (0.04) — no MLB-specific derivation exists yet.
_MIN_EDGE: float = 0.04


@dataclass
class T4MlbGameContext:
    """Synthetic/live per-market snapshot consumed by the MLB T4 sub-band evaluators.

    Field names mirror MLBLiveBatterState / run_t4_mlb_live.py's per-cycle context
    dict for consistency. score_diff and is_batting_team_leading are new — FLOW's
    inputs. Live ESPN score-diff extraction is not wired as of T-219; population of
    those two fields is Phase-8-adjacent follow-up work.
    """

    player_id: str
    game_id: str
    h_so_far: int
    ab_so_far: int
    inning: int
    batting_slot: int
    ba_l10: float
    threshold: int
    ticker: str
    score_diff: float = 0.0
    is_batting_team_leading: bool = False


class T4MlbSubBandEvaluator(ABC):
    """Abstract base for MLB-native T4 sub-band evaluators.

    Structural mirror of t4_execution_engine.SubBandEvaluator, checked against
    T4_MLB_SUBBAND_REGISTRY (the MLB-only registry) instead of NBA's
    T4_SUBBAND_REGISTRY. See execution_bands.py's governance note on why these
    registries are kept separate rather than merged.
    """

    @property
    @abstractmethod
    def sub_band(self) -> ExecutionBand:
        """The ExecutionBand this evaluator serves."""

    @abstractmethod
    def evaluate(
        self,
        ctx: T4MlbGameContext,
        price: Optional[CachedPrice],
    ) -> list[EvaluationSignal]:
        """Evaluate one market/cycle. Return SIGNAL(s) or [] for PASS."""

    def _require_phase8(self, operation: str) -> None:
        raise T4Phase8BlockedError(
            f"{self.__class__.__name__}.{operation} is Phase 8 infrastructure. "
            f"Sub-band {self.sub_band.value} is BLOCKED (status='BLOCKED' in "
            f"T4_MLB_SUBBAND_REGISTRY). All net-new MLB T4 sub-bands require a "
            f"Phase 8 Activation Gate (ADR-0039)."
        )

    def _assert_sub_band_blocked(self) -> None:
        """Verify at construction that this sub-band is BLOCKED in T4_MLB_SUBBAND_REGISTRY."""
        spec = T4_MLB_SUBBAND_REGISTRY.get(self.sub_band)
        if spec is None or spec.status != "BLOCKED":
            raise RuntimeError(
                f"{self.__class__.__name__}: sub-band {self.sub_band.value} must have "
                f"status='BLOCKED' in T4_MLB_SUBBAND_REGISTRY. Found: "
                f"{spec.status if spec else 'NOT REGISTERED'}. "
                f"Activating MLB T4 sub-bands without a Phase 8 Activation Gate violates ADR-0039."
            )


class T4MlbArithEvaluator(T4MlbSubBandEvaluator):
    """
    T4M-ARITH: threshold-approaching Binomial near-certainty.

    Fires when a batter is within _ARITH_ENTRY_WINDOW hits of their market
    threshold AND the resulting p_arith clears _CONFIDENCE_GATE. Distinct from
    the flat model's hard boundaries (h_so_far >= threshold -> p=1.0;
    h_needed > ab_remaining -> p=0.0) — this is the near-certain band *between*
    those boundaries, where Binomial variance has contracted enough that a
    dedicated (provisionally higher) Kelly fraction might be justified.

    kelly_fraction is pinned to T4_MLB_SUBBAND_REGISTRY[T4M_ARITH].provisional_kelly
    (held at T4M-PROJ's existing ceiling) until EXP-ARITH-MLB-01 clears.
    """

    _ARITH_ENTRY_WINDOW = _ARITH_ENTRY_WINDOW
    _CONFIDENCE_GATE = _ARITH_CONFIDENCE_GATE

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4M_ARITH

    def __init__(self) -> None:
        self._assert_sub_band_blocked()

    def evaluate(
        self,
        ctx: T4MlbGameContext,
        price: Optional[CachedPrice],
    ) -> list[EvaluationSignal]:
        h_needed = ctx.threshold - ctx.h_so_far
        if not (0 < h_needed <= self._ARITH_ENTRY_WINDOW):
            return []  # already achieved (h_needed<=0, that's the flat model's job) or too far out

        ab_remaining = _compute_ab_remaining(ctx.ab_so_far, ctx.inning, ctx.batting_slot)
        if ab_remaining <= 0:
            return []

        p_arith = p_hits_gte_threshold(ctx.h_so_far, ctx.threshold, ctx.ba_l10, ab_remaining)
        if p_arith < self._CONFIDENCE_GATE:
            return []

        if price is None:
            return []

        edge = p_arith - price.mid - price.vig
        if abs(edge) < _MIN_EDGE:
            return []

        kelly = T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_ARITH].provisional_kelly
        direction = "YES" if p_arith > 0.5 else "NO"

        return [EvaluationSignal(
            sub_band=ExecutionBand.T4M_ARITH,
            tree_id="ARITH-NEAR-CERTAIN",
            market_id=ctx.ticker,
            player_id=ctx.player_id,
            direction=direction,
            model_p=p_arith,
            mip_at_signal=price.mid,
            vig_at_signal=price.vig,
            edge_at_signal=edge,
            kelly_fraction=kelly,
            signal_snapshot={
                "h_so_far": ctx.h_so_far,
                "threshold": ctx.threshold,
                "h_needed": h_needed,
                "ab_remaining": ab_remaining,
                "ba_l10": ctx.ba_l10,
                "entry_window": self._ARITH_ENTRY_WINDOW,
                "confidence_gate": self._CONFIDENCE_GATE,
            },
            ts=datetime.now(timezone.utc),
            is_exit=False,
        )]


class T4MlbFlowEvaluator(T4MlbSubBandEvaluator):
    """
    T4M-FLOW: accumulated game-state pattern — FLOW-BLOWOUT tree only.

    Fires when a run-differential blowout (|score_diff| >= _BLOWOUT_RUN_THRESHOLD)
    has been sustained for >= _BLOWOUT_SUSTAIN_INNINGS innings. Applies an
    asymmetric multiplier to the batter's effective ba_l10 before the Binomial
    update: trailing-team batters get an uplift (garbage-time at-bats against
    tiring/mop-up relief), leading-team batters get a discount (pulled early /
    facing fresh relief). Both multipliers are provisional and non-operational
    pending EXP-FLOW-MLB-01.

    Blowout state is tracked per game_id (dict, not a single Optional[int]) since
    this evaluator has no Layer 1/2 engine wrapping it per-game — a single
    instance may see interleaved cycles from multiple live games.
    """

    _BLOWOUT_RUN_THRESHOLD = _BLOWOUT_RUN_THRESHOLD
    _BLOWOUT_SUSTAIN_INNINGS = _BLOWOUT_SUSTAIN_INNINGS
    _BLOWOUT_TRAILING_MULT = _BLOWOUT_TRAILING_MULT
    _BLOWOUT_LEADING_MULT = _BLOWOUT_LEADING_MULT

    @property
    def sub_band(self) -> ExecutionBand:
        return ExecutionBand.T4M_FLOW

    def __init__(self) -> None:
        self._assert_sub_band_blocked()
        # game_id -> inning the current blowout condition started. Absent = no
        # blowout currently active for that game. Cleared when the gap closes.
        self._blowout_start_inning: dict[str, int] = {}

    def evaluate(
        self,
        ctx: T4MlbGameContext,
        price: Optional[CachedPrice],
    ) -> list[EvaluationSignal]:
        in_blowout = abs(ctx.score_diff) >= self._BLOWOUT_RUN_THRESHOLD
        if in_blowout:
            self._blowout_start_inning.setdefault(ctx.game_id, ctx.inning)
        else:
            self._blowout_start_inning.pop(ctx.game_id, None)

        if not in_blowout:
            return []

        start_inning = self._blowout_start_inning.get(ctx.game_id)
        if start_inning is None:
            return []  # defensive; should not happen given the setdefault above
        if (ctx.inning - start_inning) < self._BLOWOUT_SUSTAIN_INNINGS:
            return []  # blowout not yet sustained long enough

        player_trailing = not ctx.is_batting_team_leading
        mult = self._BLOWOUT_TRAILING_MULT if player_trailing else self._BLOWOUT_LEADING_MULT
        ba_adjusted = min(1.0, ctx.ba_l10 * mult)

        ab_remaining = _compute_ab_remaining(ctx.ab_so_far, ctx.inning, ctx.batting_slot)
        if ab_remaining <= 0:
            return []

        p_flow = p_hits_gte_threshold(ctx.h_so_far, ctx.threshold, ba_adjusted, ab_remaining)

        if price is None:
            return []

        edge = p_flow - price.mid - price.vig
        if abs(edge) < _MIN_EDGE:
            return []

        kelly = T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_FLOW].provisional_kelly
        direction = "YES" if p_flow > 0.5 else "NO"

        return [EvaluationSignal(
            sub_band=ExecutionBand.T4M_FLOW,
            tree_id="FLOW-BLOWOUT",
            market_id=ctx.ticker,
            player_id=ctx.player_id,
            direction=direction,
            model_p=p_flow,
            mip_at_signal=price.mid,
            vig_at_signal=price.vig,
            edge_at_signal=edge,
            kelly_fraction=kelly,
            signal_snapshot={
                "score_diff": ctx.score_diff,
                "blowout_start_inning": start_inning,
                "inning": ctx.inning,
                "mult": mult,
                "ba_l10": ctx.ba_l10,
                "ba_adjusted": round(ba_adjusted, 4),
                "player_trailing": player_trailing,
                "is_batting_team_leading": ctx.is_batting_team_leading,
            },
            ts=datetime.now(timezone.utc),
            is_exit=False,
        )]

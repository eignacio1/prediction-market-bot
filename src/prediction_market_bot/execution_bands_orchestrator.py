"""
Execution Bands Orchestrator — Multi-Band Decision Engine
==========================================================
Module:   execution_bands_orchestrator
Phase:    Phase 7 (multi-band active — T1 live; T2/T3 activating)
Purpose:  Apply the P6 multi-band interaction rules to produce a single
          authoritative BandDecision for each player/market from potentially
          concurrent T1, T2, and T3 signals.

Multi-band interaction rules (STRATEGY_OVERVIEW.md P6):
  Priority:  T3 (most recent) > T2 > T1
  Sizing:    Most conservative (lowest) kelly_fraction among active bands
  Decision matrix:
    T3 CONFIRM  + T1/T2 actionable  →  PROCEED at T3 sizing
    T3 FADE     + T1/T2 actionable  →  HOLD; wait for next T3 scan
    T3 NEUTRAL  + T1/T2 actionable  →  PROCEED at T2/T1 sizing
    T3 absent, T2 present           →  PROCEED at T2 sizing
    T3 absent, T2 absent            →  PROCEED at T1 sizing
    T1 direction == PASS            →  PASS regardless of T2/T3

Governance:
  BandDecision.action == PROCEED feeds C4 RiskEngine but does NOT place orders.
  C4 still applies phase gate (BOT_C4_ACTIVE), hard limits, and Kelly cap.
  This module is the signal aggregator, not the execution engine.

References:
  STRATEGY_OVERVIEW.md Section 5 — Execution Band Framework, P6
  EXECUTION_BANDS.md — Band definitions and Kelly fractions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from prediction_market_bot.execution_bands import ExecutionBand, get_band_config


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BandSignal:
    """
    A forecast signal from a single execution band for one player/market.

    Produced by pipeline runners (PIPE-02 T1, PIPE-05 T2, PIPE-06 T3)
    and consumed by MultiBandOrchestrator.decide() to produce BandDecision.

    Fields
    ------
    band : ExecutionBand
        Which band produced this signal.
    player_name : str
        Player display name as returned by the venue adapter.
    ticker : str
        Venue market ticker (e.g. KXNBAPTS-26MAY28OKCSAS-OKCSGA-25).
    direction : str
        'YES', 'NO', or 'PASS' (no actionable edge at this band).
    edge : float
        Edge estimate: p̂ - mid_price (or adjusted for T3 momentum multiplier).
    p_estimate : float
        Calibrated probability estimate from C3 (0.0–1.0).
    kelly_fraction : float
        Band-specific Kelly fraction from BandConfig.
    momentum_signal : str
        T3 only — 'CONFIRM', 'FADE', or 'NEUTRAL'.
        Defaults to 'NEUTRAL' for T1/T2 (field unused at those bands).
    """
    band: ExecutionBand
    player_name: str
    ticker: str
    direction: str
    edge: float
    p_estimate: float
    kelly_fraction: float
    momentum_signal: str = "NEUTRAL"

    @property
    def is_actionable(self) -> bool:
        """True when this band has a non-PASS direction with positive edge."""
        return self.direction != "PASS" and self.edge > 0


@dataclass(frozen=True)
class BandDecision:
    """
    Authoritative trading decision for one player/market after applying
    multi-band interaction rules.

    Consumed by C4 RiskEngine for phase gate, Kelly sizing, and hard limits.

    Fields
    ------
    player_name : str
        Player display name.
    ticker : str
        Venue market ticker.
    action : str
        'PROCEED' — submit to C4 for risk evaluation and potential execution.
        'HOLD'    — T3 FADE; wait for next PIPE-06 scan cycle (15-min window).
        'PASS'    — No edge or T1 direction=PASS; skip this market.
    direction : str
        'YES', 'NO', or 'PASS'. Set to 'PASS' when action == 'PASS'.
    final_band : ExecutionBand
        The band whose signal governs this decision (highest-priority active).
    final_kelly : float
        Kelly fraction to apply — most conservative among all active bands.
    final_edge : float
        Edge estimate from the governing band.
    rationale : str
        Human-readable explanation of which rules fired and why.
    """
    player_name: str
    ticker: str
    action: str
    direction: str
    final_band: ExecutionBand
    final_kelly: float
    final_edge: float
    rationale: str

    @property
    def should_proceed(self) -> bool:
        """True when action == 'PROCEED' — signal is ready for C4 risk check."""
        return self.action == "PROCEED"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class MultiBandOrchestrator:
    """
    Applies P6 multi-band interaction rules to produce a single BandDecision.

    T3 has highest priority (most recent information). Kelly fraction defaults
    to the most conservative across all active bands — shorter horizon = less
    model confidence = smaller position, except T5 (arithmetic near-certainty).

    Usage::

        orch = MultiBandOrchestrator()

        # Single-market decision:
        decision = orch.decide(t1_signal, t2_signal=t2, t3_signal=t3)
        if decision.should_proceed:
            risk_engine.evaluate(decision)

        # Full game-day batch:
        decisions = orch.batch_decide(t1_list, t2_list, t3_list)
    """

    def decide(
        self,
        t1: BandSignal,
        t2: Optional[BandSignal] = None,
        t3: Optional[BandSignal] = None,
    ) -> BandDecision:
        """
        Apply P6 rules and return the authoritative BandDecision.

        Parameters
        ----------
        t1 : BandSignal
            T1 signal (required — PIPE-02 always runs first; T1 is the
            mandatory foundation for all downstream bands).
        t2 : BandSignal, optional
            T2 signal from PIPE-05 same-day injury overlay.
        t3 : BandSignal, optional
            T3 signal from PIPE-06 pre-tip momentum scan.
        """
        # T1 is the gating condition — no edge means no bet regardless of T2/T3
        if not t1.is_actionable:
            return BandDecision(
                player_name=t1.player_name,
                ticker=t1.ticker,
                action="PASS",
                direction="PASS",
                final_band=ExecutionBand.T1_MULTI_DAY,
                final_kelly=t1.kelly_fraction,
                final_edge=t1.edge,
                rationale="T1: no actionable edge (direction=PASS or edge≤0)",
            )

        # T3 present — apply momentum rules (highest priority)
        if t3 is not None:
            return self._apply_t3_rules(t1, t2, t3)

        # T2 present and actionable — use T2 sizing with T1 direction
        if t2 is not None and t2.is_actionable:
            kelly = min(t1.kelly_fraction, t2.kelly_fraction)
            return BandDecision(
                player_name=t1.player_name,
                ticker=t1.ticker,
                action="PROCEED",
                direction=t1.direction,
                final_band=ExecutionBand.T2_SAME_DAY,
                final_kelly=kelly,
                final_edge=t2.edge,
                rationale=(
                    f"T2 injury overlay active; direction={t1.direction}; "
                    f"kelly=min({t1.kelly_fraction},{t2.kelly_fraction})={kelly}"
                ),
            )

        # T1 only
        return BandDecision(
            player_name=t1.player_name,
            ticker=t1.ticker,
            action="PROCEED",
            direction=t1.direction,
            final_band=ExecutionBand.T1_MULTI_DAY,
            final_kelly=t1.kelly_fraction,
            final_edge=t1.edge,
            rationale=(
                f"T1 only; direction={t1.direction}; kelly={t1.kelly_fraction}"
            ),
        )

    def batch_decide(
        self,
        t1_signals: list[BandSignal],
        t2_signals: Optional[list[BandSignal]] = None,
        t3_signals: Optional[list[BandSignal]] = None,
    ) -> list[BandDecision]:
        """
        Apply multi-band rules across all players for a full game day.

        Matches T2/T3 signals to T1 signals by ticker. Players in T1 but
        absent from T2/T3 fall back to T1-only decisions (graceful degradation).
        Players in T3 but absent from T1 are silently skipped — T1 is mandatory.

        Parameters
        ----------
        t1_signals : list[BandSignal]
            All T1 signals from today's PIPE-02 run.
        t2_signals : list[BandSignal], optional
            All T2 signals from today's PIPE-05 run (same-day injury overlay).
        t3_signals : list[BandSignal], optional
            Most recent T3 signals from PIPE-06 (last 15-min scan cycle).
        """
        t2_idx: dict[str, BandSignal] = (
            {s.ticker: s for s in t2_signals} if t2_signals else {}
        )
        t3_idx: dict[str, BandSignal] = (
            {s.ticker: s for s in t3_signals} if t3_signals else {}
        )

        return [
            self.decide(t1, t2=t2_idx.get(t1.ticker), t3=t3_idx.get(t1.ticker))
            for t1 in t1_signals
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply_t3_rules(
        self,
        t1: BandSignal,
        t2: Optional[BandSignal],
        t3: BandSignal,
    ) -> BandDecision:
        """Apply P6 rules when a T3 momentum signal is present."""
        player  = t1.player_name
        ticker  = t1.ticker
        signal  = t3.momentum_signal
        direction = t1.direction  # T1 determines direction; T3 adjusts confidence

        # Collect all active band fractions for conservative kelly selection
        active_fractions = [t1.kelly_fraction, t3.kelly_fraction]
        if t2 is not None and t2.is_actionable:
            active_fractions.append(t2.kelly_fraction)
        min_kelly = min(active_fractions)

        # Determine which base band governs edge and sizing when T3 is NEUTRAL
        base_is_t2 = t2 is not None and t2.is_actionable
        base_band  = ExecutionBand.T2_SAME_DAY if base_is_t2 else ExecutionBand.T1_MULTI_DAY
        base_edge  = t2.edge if base_is_t2 else t1.edge
        base_kelly = t2.kelly_fraction if base_is_t2 else t1.kelly_fraction

        if signal == "CONFIRM":
            return BandDecision(
                player_name=player,
                ticker=ticker,
                action="PROCEED",
                direction=direction,
                final_band=ExecutionBand.T3_PRE_TIP,
                final_kelly=min_kelly,
                final_edge=t3.edge,
                rationale=(
                    f"T3 CONFIRM: price drifted with model; "
                    f"kelly={min_kelly}; edge={t3.edge:.4f}"
                ),
            )

        if signal == "FADE":
            return BandDecision(
                player_name=player,
                ticker=ticker,
                action="HOLD",
                direction=direction,
                final_band=ExecutionBand.T3_PRE_TIP,
                final_kelly=min_kelly,
                final_edge=t3.edge,
                rationale=(
                    "T3 FADE: price drifted against model; "
                    "hold — wait for next 15-min scan"
                ),
            )

        # NEUTRAL — T3 present but no momentum; proceed at base band sizing
        neutral_kelly = min(base_kelly, t3.kelly_fraction)
        return BandDecision(
            player_name=player,
            ticker=ticker,
            action="PROCEED",
            direction=direction,
            final_band=base_band,
            final_kelly=neutral_kelly,
            final_edge=base_edge,
            rationale=(
                f"T3 NEUTRAL: no price momentum; proceed at {base_band.value} sizing; "
                f"kelly={neutral_kelly}"
            ),
        )

"""
C7: Semantic Contracts — Layer 3 Behavioral Coherence
=====================================================
Component:    C7 (Monitoring — Layer 3 extension)
Phase active: ACTIVE from Phase 6+ (MLB paper trading live)
Status:       CANONICAL (2026-06-29)

Root cause (GG-049):
  T1 MLB ran 0 bets for 2+ game days without detection. Cause: a naming
  convention mismatch in the ESPN boxscore parser silently prevented all
  player-to-market matching. No architecture was wrong. No hard limit was
  breached. No C7 threshold fired. The system was structurally sound and
  operationally dark. The semantic layer — the explicit assertion that
  "if games were fetched, some players must match" — did not exist.

  This module is not a defensive coding patch. It is a governance tier that
  formally states each pipeline's behavioral intent, then verifies it at
  runtime. Violations emit to C6 and surface in C7's health snapshot.

Governance framework (three layers):
  Layer 1 — Architecture integrity:
    Verified at gate review (G0–G9). Checks whether components were built
    as designed. Does not run at runtime.

  Layer 2 — Operational health (C7 existing monitor.py):
    Verified per monitoring cycle. Checks Brier/ECE drift and P&L. Runs
    on resolved forecasts. Cannot detect a dark pipeline.

  Layer 3 — Semantic behavioral coherence (this module):
    Verified per pipeline stage, per band, per evaluation. Asks: "Is what
    is currently happening coherent with what this band is supposed to do?"
    Runs pre-evaluation and at pipeline boundaries. Catches dark pipelines
    and contaminated evaluations before they become governance gaps.

Contract taxonomy:
  PIPELINE_FLOOR   C1→C2 boundary: data retrieved → some players matched
  EVALUATION_GATE  T4 pre-evaluation: data window coherent before firing
  BAND_INVARIANT   Per-band structural property, every evaluation
  CROSS_BAND       System-level coherence across bands

Per-band contract intent (each band carries a distinct semantic commitment):

  T1 (night-before baseline, ACTIVE):
    Intent: historical rolling model emits calibrated probabilities for real
    markets. Expected behavior: players with pregame context produce forecasts
    in the Platt-calibrated range. Failure mode: silent zero (GG-049 pattern).
    Contracts: pipeline_floor (players matched), p_estimate in calibrated
    range, ba_l10 in plausible range (MLB), min_games_for_features ≥ 5.

  T2 (same-day injury overlay, SKELETON):
    Intent: T1 forecasts adjusted by injury information. If injury data is
    absent, T2 must not claim to be applying an overlay — it must pass through
    T1 probabilities unchanged and log the absence explicitly.
    Contracts: injury_source_acknowledged (if no data, flag it, don't silently
    default), threshold unchanged from T1 (T2 modifies p_estimate only).

  T3 (pre-tip momentum, SKELETON):
    Intent: short-horizon momentum scan; only fires near game start.
    Contracts: game_start_proximity (T3 output must be time-gated; firing
    when game_starts_in_min > 120 indicates stale or incorrect trigger).

  T4 (in-play, ACTIVE for MLB / dark for NBA off-season):
    Intent: ~1,000 evaluations per game, dynamically routed by model
    computation. Each evaluation must see a coherent data window: market
    exists, price is fresh, player is in the live game, game is in progress.
    Failure mode: contamination (evaluation fires on stale/ghost data).
    Contracts: ContaminationGuard per evaluation (see below).

  T4 sub-band contracts (ADR-0029 Tier B — provisional boundaries):

    T4-EVENT:  stat event is discrete and attributable to a live player.
      - event_type in recognized set
      - player_id present in live boxscore
      - stat delta is physically realizable (no negative stats, no >40 pts)

    T4-PROJ:   Bayesian posterior for full-game projection.
      - lambda_prior derived from historical data (not fallback 20.0 default)
      - elapsed_min < GAME_REGULATION_MIN (game has not ended)
      - model_p not at boundary (0.0 or 1.0 = arithmetic certainty, route
        to T4-ARITH instead)

    T4-ARITH:  threshold-approaching arithmetic near-certainty.
      - game is late (elapsed_min ≥ 36 min, GAME_REGULATION_MIN=48)
      - h_needed ≤ 2 or pts_needed ≤ 5 (actually near-certain)
      - ab_remaining > 0 (game ongoing; if 0, route to T4-EXIT)

    T4-FLOW:   accumulated game-state / context pattern.
      - score_differential in [-60, 60] (outside = ESPN parser artifact)
      - game in progress (not final, not pre-game)
      - sustained_blowout only fired if score sustained for ≥ BLOWOUT_SUSTAIN_MIN

    T4-EXIT:   active position management.
      - position being exited exists in T4PositionRegistry
      - no ghost exits (log WARNING, do not halt)

    T4-CORR:   cross-market correlation overlay.
      - adjusted_size ≤ original_size (downward-only, ADR-0029 Principle 6)
      - no T4-CORR signal increases a size (KILL_SWITCH on violation)

    T4-LINEUP: live lineup change.
      - player_count_change ≤ 2 per cycle (> 2 = likely data artifact)
      - lineup_change_ts is within last 60 seconds (not stale)

    T4-BOUNDARY: quarter/halftime structural reset.
      - fires only within 2 minutes of quarter/half boundary
      - quarter in [1, 2, 3, 4] or overtime (not 0 = pre-game state)

Audit events emitted (new event types — extend C6 taxonomy):
  semantic_floor_violation    CRITICAL  pipeline halted; matched_players=0 given games_fetched>0
  contamination_halt          WARNING   single T4 evaluation skipped; data window incoherent
  semantic_contract_breach    WARNING   band invariant violated; evaluation continues with flag
  semantic_contract_ok        DEBUG     clean check (sampled — not emitted every cycle)
  semantic_health_snapshot    INFO      periodic summary of contract health (per session)

Integration points (caller responsibilities):

  1. SemanticFloorGuard.assert_floor() — call after C1 data load, before C2 features.
     Import: from prediction_market_bot.c7_monitoring.semantic_contracts import SemanticFloorGuard
     Call:   SemanticFloorGuard.assert_floor(pipeline_id, games_fetched, matched_players,
                                              sport, audit, session_id, snapshot_id)
     Effect: raises SemanticFloorViolation if matched_players == 0 and games_fetched > 0.
             Caller catches the exception and halts the pipeline.

  2. ContaminationGuard.is_clean() — call inside T4 evaluation loop, BEFORE evaluate_forecast().
     Import: from prediction_market_bot.c7_monitoring.semantic_contracts import ContaminationGuard
     Call:   guard = ContaminationGuard(ticker, player_id, market, player_state, cycle_id,
                                        audit, session_id, snapshot_id, game_state_ts)
             if not guard.is_clean(): continue
     Effect: emits contamination_halt to C6, returns False. Caller skips the evaluation.

  3. SemanticContractMonitor — integrate into C7 SystemMonitor.check_and_alert().
     Add to SystemMonitor.__init__: self._semantic = SemanticContractMonitor(self._logger, ...)
     Add to check_and_alert(): semantic_snap = self._semantic.check_band_invariants(context)
     Add to get_health_snapshot(): include semantic_snap in returned dict.

ADR refs:   ADR-0029 (T4 sub-band architecture), ADR-0023 (T4 pool isolation)
            GG-049 (T1 MLB silent zero — root cause documentation)
Policy refs: CLAUDE.md (hard rule 9: ~1,000 evaluations/game throughput design)
             MONITORING_DRIFT_PLAN.md (Layer 2 baseline), OBSERVABILITY.md
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy — pipeline halting violations
# ---------------------------------------------------------------------------


class SemanticContractError(Exception):
    """Base for all semantic contract violations."""


class SemanticFloorViolation(SemanticContractError):
    """
    C1→C2 pipeline floor violated: data was retrieved but nothing matched.

    Raised when games_fetched > 0 AND matched_players == 0.

    This is the formal representation of the GG-049 failure mode: the pipeline
    did not fail (no exception, no HTTP error, no missing file), but its output
    was semantically empty — a dark pipeline indistinguishable from a working
    one with no active games.

    Callers must catch this exception and halt the pipeline. Do not re-raise
    as a generic exception; the specific type matters for C7 monitoring.

    Attributes
    ----------
    pipeline_id:    e.g. "PIPE-05", "PIPE-02"
    sport:          e.g. "MLB", "NBA"
    games_fetched:  number of games returned by the C1 data source
    matched_players: number of players successfully matched to markets
    diagnosis:      human-readable explanation of the mismatch
    """

    def __init__(
        self,
        pipeline_id: str,
        sport: str,
        games_fetched: int,
        matched_players: int,
        diagnosis: str = "",
    ) -> None:
        self.pipeline_id = pipeline_id
        self.sport = sport
        self.games_fetched = games_fetched
        self.matched_players = matched_players
        self.diagnosis = diagnosis
        super().__init__(
            f"SemanticFloorViolation: {pipeline_id} {sport} — "
            f"games_fetched={games_fetched} but matched_players={matched_players}. "
            f"{diagnosis}"
        )


class T4CorrDownwardViolation(SemanticContractError):
    """
    T4-CORR downward-only invariant breached (ADR-0029 Principle 6).

    The correlation overlay increased a position size. This is structurally
    impossible per the ADR — T4-CORR can only reduce sizes, never increase.
    A violation here means the overlay is applying in the wrong direction,
    which could compound risk rather than hedge it. KILL_SWITCH warranted.
    """

    def __init__(
        self,
        market_id: str,
        original_size: float,
        adjusted_size: float,
    ) -> None:
        self.market_id = market_id
        self.original_size = original_size
        self.adjusted_size = adjusted_size
        super().__init__(
            f"T4CorrDownwardViolation: T4-CORR overlay INCREASED size on {market_id}: "
            f"original={original_size:.4f} adjusted={adjusted_size:.4f} "
            f"(ADR-0029 Principle 6 — downward-only)"
        )


# ---------------------------------------------------------------------------
# Contract result types
# ---------------------------------------------------------------------------


class ContractType(Enum):
    PIPELINE_FLOOR = "PIPELINE_FLOOR"
    EVALUATION_GATE = "EVALUATION_GATE"
    BAND_INVARIANT = "BAND_INVARIANT"
    CORR_DOWNWARD = "CORR_DOWNWARD"


@dataclass
class ContractViolation:
    """
    A recorded contract violation — does not necessarily halt execution.

    CRITICAL violations (SemanticFloorViolation, T4CorrDownwardViolation)
    raise exceptions. WARNING violations (ContaminationGuard, band invariants)
    create ContractViolation records and emit to C6 but allow execution to
    continue with a skip or a flag.
    """
    contract_type: ContractType
    band: str
    pipeline_id: str
    violation_id: str
    violation_reason: str
    payload: dict[str, Any]
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SemanticHealthState:
    """
    Current semantic contract health snapshot.

    Consumed by C7 get_health_snapshot() and surfaced on the C8 dashboard.
    Separate from DriftSnapshot (which tracks forecast accuracy) — semantic
    health is about pipeline coherence, not model calibration.
    """
    n_floor_violations_session: int = 0
    n_contamination_halts_session: int = 0
    n_band_invariant_breaches_session: int = 0
    n_corr_downward_violations_session: int = 0
    last_floor_violation_ts: Optional[str] = None
    last_contamination_halt_ts: Optional[str] = None
    last_breach_band: Optional[str] = None
    is_semantically_dark: bool = False   # True if floor violation seen this session
    session_id: Optional[str] = None
    computed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# SemanticFloorGuard — C1→C2 boundary
# ---------------------------------------------------------------------------


class SemanticFloorGuard:
    """
    Static guard: asserts that data retrieved from C1 successfully mapped
    to model-ready players in C2.

    The invariant: if games_fetched > 0, then matched_players > 0.

    If this fails, the pipeline is semantically dark — it completed without
    error but produced no usable output. This is structurally worse than a
    hard failure because it is invisible to Layer 1 and Layer 2 monitoring.

    Usage (in pipeline entrypoint, after data load and before evaluation)::

        from prediction_market_bot.c7_monitoring.semantic_contracts import (
            SemanticFloorGuard, SemanticFloorViolation,
        )

        try:
            SemanticFloorGuard.assert_floor(
                pipeline_id="PIPE-05",
                games_fetched=len(games),
                matched_players=len(players_in_markets),
                sport="MLB",
                audit=audit,
                session_id=session_id,
                snapshot_id=SNAPSHOT_ID,
            )
        except SemanticFloorViolation as exc:
            logger.critical("Pipeline floor violated — halting: %s", exc)
            audit.log(component="PIPE-05", event_type="pipeline_floor_halt",
                      payload={"reason": str(exc)}, severity="CRITICAL",
                      session_id=session_id, snapshot_id=SNAPSHOT_ID)
            return   # or sys.exit(1) for cron entry points

    Note: assert_floor does NOT call audit.log() — the caller must log the
    exception for full context (pipeline_id, session_id, etc). The guard
    focuses purely on the semantic check. This separation is deliberate: the
    guard has no knowledge of C6 configuration, so all C6 writes flow through
    the component that owns the C6 instance.
    """

    @staticmethod
    def assert_floor(
        pipeline_id: str,
        games_fetched: int,
        matched_players: int,
        sport: str,
        min_match_rate: float = 0.0,
    ) -> None:
        """
        Assert that data retrieval produced usable matches.

        Parameters
        ----------
        pipeline_id:
            e.g. "PIPE-05", "PIPE-02". Used in exception and audit payload.
        games_fetched:
            Number of games returned by the C1 data source (ESPN, StatsAPI, etc.)
        matched_players:
            Number of players successfully matched to live Kalshi markets.
        sport:
            "MLB" or "NBA". Used in exception message.
        min_match_rate:
            Optional minimum expected match rate. If > 0, raises when
            matched_players / games_fetched < min_match_rate. Useful if you
            have a stable historical baseline (e.g. "at least 3 players per
            game should match"). Default 0.0 = only check the total floor.

        Raises
        ------
        SemanticFloorViolation
            If games_fetched > 0 and matched_players == 0.
            If min_match_rate > 0 and match rate falls below threshold.
        """
        if games_fetched <= 0:
            # No games today is not a floor violation — it is expected.
            # The pipeline should idle; this guard has nothing to assert.
            return

        if matched_players == 0:
            # Games were fetched but not a single player matched to a market.
            # This is the GG-049 pattern: data retrieval succeeded, matching failed.
            # Root causes: naming convention mismatch, wrong market series ticker,
            # market closed before pipeline ran, pregame file stale/absent.
            raise SemanticFloorViolation(
                pipeline_id=pipeline_id,
                sport=sport,
                games_fetched=games_fetched,
                matched_players=matched_players,
                diagnosis=(
                    "Zero players matched despite active games. "
                    "Likely causes: naming convention mismatch (player name vs "
                    "Kalshi displayName normalization), wrong market series ticker, "
                    "all markets settled before pipeline ran, or pregame context file "
                    "missing/stale (check PIPE-06pre ran before T4)."
                ),
            )

        if min_match_rate > 0.0:
            actual_rate = matched_players / games_fetched
            if actual_rate < min_match_rate:
                raise SemanticFloorViolation(
                    pipeline_id=pipeline_id,
                    sport=sport,
                    games_fetched=games_fetched,
                    matched_players=matched_players,
                    diagnosis=(
                        f"Match rate {actual_rate:.2%} < expected floor {min_match_rate:.2%}. "
                        f"{games_fetched} games, {matched_players} matched. "
                        "Partial match failure: some players are present but a significant "
                        "fraction are missing. Check normalization consistency."
                    ),
                )

    @staticmethod
    def check_calibration_range(
        p_estimate: float,
        pipeline_id: str,
        player_id: Any,
        band: str = "T1",
        p_min: float = 0.05,
        p_max: float = 0.95,
    ) -> Optional[ContractViolation]:
        """
        Assert that a Platt-calibrated probability is in a plausible range.

        Probabilities at the boundary (0.0 or 1.0) from a logistic regression
        model indicate arithmetic certainty — which LR+Platt scaling should
        not produce on real market distributions. Values outside [0.05, 0.95]
        indicate either model collapse or data entry errors.

        Returns None if clean, ContractViolation if out of range (not raised —
        callers decide whether to skip, log, or halt).

        The typical T1 Platt output range for NBA/MLB props is [0.20, 0.80].
        The [0.05, 0.95] bounds here are deliberately liberal — they flag
        genuine outliers without rejecting real tail bets.
        """
        if p_min <= p_estimate <= p_max:
            return None

        return ContractViolation(
            contract_type=ContractType.BAND_INVARIANT,
            band=band,
            pipeline_id=pipeline_id,
            violation_id=f"CALIB-{uuid.uuid4().hex[:8].upper()}",
            violation_reason="p_estimate_out_of_calibrated_range",
            payload={
                "p_estimate": p_estimate,
                "p_min": p_min,
                "p_max": p_max,
                "player_id": player_id,
                "note": (
                    "LR+Platt calibration should not produce extreme probabilities "
                    "on real market distributions. Check feature pipeline integrity."
                ),
            },
        )

    @staticmethod
    def check_mlb_ba_range(
        ba_l10: float,
        player_id: Any,
        pipeline_id: str,
        ba_min: float = 0.05,
        ba_max: float = 0.60,
    ) -> Optional[ContractViolation]:
        """
        Assert that a batting average (last 10 games) is in a plausible range.

        ba_l10 is used as the Binomial success probability in T4 MLB evaluation.
        Values of 0.0 are default/missing data — the Binomial will return 0
        probability of any hits, making the player invisible to the model.
        Values > 0.60 are historically impossible for a 10-game sample at MLB level.

        Returns None if clean, ContractViolation if out of range.
        """
        if ba_min <= ba_l10 <= ba_max:
            return None

        return ContractViolation(
            contract_type=ContractType.BAND_INVARIANT,
            band="T1",
            pipeline_id=pipeline_id,
            violation_id=f"BA-{uuid.uuid4().hex[:8].upper()}",
            violation_reason="ba_l10_out_of_plausible_range",
            payload={
                "ba_l10": ba_l10,
                "ba_min": ba_min,
                "ba_max": ba_max,
                "player_id": player_id,
                "note": (
                    "ba_l10=0.0 means the player has 0 hits in their last 10 games, "
                    "or this is a default/missing-data fallback. Either way the "
                    "Binomial model returns p≈0 and the player generates no edge. "
                    "ba_l10>0.60 is historically impossible for a 10-game MLB sample."
                ),
            },
        )


# ---------------------------------------------------------------------------
# ContaminationGuard — T4 pre-evaluation gate
# ---------------------------------------------------------------------------


class ContaminationGuard:
    """
    T4 evaluation pre-fire gate. Verifies data window coherence before
    evaluate_forecast() is called.

    The contamination failure mode: a T4 evaluation fires on data that is
    structurally valid (no exception, no None) but semantically wrong —
    a price snapshot from a market that has since closed, a player who left
    the game, or game state data from a previous cycle that was not refreshed.

    This guard runs before every evaluation in the T4 loop. It is designed
    to be O(1) with no I/O — it checks already-loaded data, does not fetch
    anything new.

    A ContaminationGuard instance is not reused across evaluations. Create
    one per evaluation context.

    Usage (in T4 evaluation loop, before evaluate_forecast())::

        guard = ContaminationGuard(
            ticker=ticker,
            player_id=player_id,
            has_live_quotes=pm.has_live_quotes,
            mip=pm.mid_price,
            player_in_live_game=player_id in active_player_ids,
            game_in_progress=game_status == "STATUS_IN_PROGRESS",
            cycle_id=cycle_id,
            audit=audit,
            session_id=session_id,
            snapshot_id=SNAPSHOT_ID,
        )
        if not guard.is_clean():
            continue   # contamination_halt logged by guard

    Note: audit is optional (None = test mode). The guard still returns False
    and logs via Python logging if audit is None — the guard does not fail
    silently even in test mode.
    """

    def __init__(
        self,
        ticker: str,
        player_id: Any,
        has_live_quotes: bool,
        mip: float,
        player_in_live_game: bool,
        game_in_progress: bool,
        cycle_id: str,
        audit: Any,               # AuditLogger instance or None
        session_id: Optional[str],
        snapshot_id: str,
        # Optional T4-PROJ specific checks
        elapsed_min: Optional[float] = None,
        game_regulation_min: float = 48.0,   # GAME_REGULATION_MIN from t4_execution_engine
        # Optional T4-ARITH specific checks
        h_needed: Optional[int] = None,
        ab_remaining: Optional[int] = None,
        # Optional T4-CORR specific check
        original_size: Optional[float] = None,
        adjusted_size: Optional[float] = None,
    ) -> None:
        self._ticker = ticker
        self._player_id = player_id
        self._has_live_quotes = has_live_quotes
        self._mip = mip
        self._player_in_live_game = player_in_live_game
        self._game_in_progress = game_in_progress
        self._cycle_id = cycle_id
        self._audit = audit
        self._session_id = session_id
        self._snapshot_id = snapshot_id
        self._elapsed_min = elapsed_min
        self._game_regulation_min = game_regulation_min
        self._h_needed = h_needed
        self._ab_remaining = ab_remaining
        self._original_size = original_size
        self._adjusted_size = adjusted_size

    def is_clean(self) -> bool:
        """
        Run all contamination checks. Returns True if clean, False if
        contaminated (CONTAMINATION_HALT emitted to C6).

        Checks (in order — stops at first failure):
          1. Market has live quotes (not closed/settled)
          2. MIP is in valid probability range (0, 1) exclusive
          3. Player is in the live game boxscore
          4. Game is in progress (not final, not pre-game)
          5. If elapsed_min provided: game has not exceeded regulation
          6. If h_needed + ab_remaining provided: T4-ARITH coherence
          7. If original_size + adjusted_size provided: T4-CORR downward invariant

        Returns False immediately on the first violation. Does not accumulate
        multiple violations per call — the first contamination source is
        sufficient reason to skip.
        """
        reason = self._check()
        if reason is None:
            return True

        # Emit to C6
        payload = {
            "contamination_reason": reason,
            "ticker": self._ticker,
            "player_id": self._player_id,
            "cycle_id": self._cycle_id,
            "has_live_quotes": self._has_live_quotes,
            "mip": self._mip,
            "player_in_live_game": self._player_in_live_game,
            "game_in_progress": self._game_in_progress,
        }
        if self._elapsed_min is not None:
            payload["elapsed_min"] = self._elapsed_min
            payload["game_regulation_min"] = self._game_regulation_min
        if self._h_needed is not None:
            payload["h_needed"] = self._h_needed
            payload["ab_remaining"] = self._ab_remaining

        if self._audit is not None:
            try:
                ok = self._audit.log(
                    component="C7-SEMANTIC",
                    event_type="contamination_halt",
                    payload=payload,
                    severity="WARNING",
                    session_id=self._session_id,
                    snapshot_id=self._snapshot_id,
                )
                if not ok:
                    logger.error(
                        "ContaminationGuard: C6 write failure on contamination_halt"
                        " — ticker=%s cycle=%s",
                        self._ticker, self._cycle_id,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "ContaminationGuard: audit.log() raised for ticker=%s: %s",
                    self._ticker, exc,
                )
        else:
            logger.warning(
                "CONTAMINATION_HALT (test mode — no C6): ticker=%s reason=%s cycle=%s",
                self._ticker, reason, self._cycle_id,
            )

        return False

    def _check(self) -> Optional[str]:
        """
        Internal: return violation reason string if contaminated, None if clean.
        """
        # Check 1 — market must have live quotes (not closed/settled/halted)
        if not self._has_live_quotes:
            return "market_no_live_quotes"

        # Check 2 — MIP must be in valid probability range (strictly open interval)
        if not (0.0 < self._mip < 1.0):
            return f"mip_out_of_range:{self._mip}"

        # Check 3 — player must be in the live boxscore for this game
        # (not a player from a different game, not a player who DNP'd)
        if not self._player_in_live_game:
            return "player_not_in_live_boxscore"

        # Check 4 — game must be in progress
        # (market can stay open briefly after game ends; check game state too)
        if not self._game_in_progress:
            return "game_not_in_progress"

        # Check 5 — T4-PROJ coherence: game must not have exceeded regulation
        # (post-regulation evaluations route to T4-ARITH or T5, not T4-PROJ)
        if self._elapsed_min is not None:
            if self._elapsed_min >= self._game_regulation_min:
                return f"elapsed_min_exceeds_regulation:{self._elapsed_min:.1f}"

        # Check 6 — T4-ARITH coherence: h_needed must be achievable
        # (if ab_remaining == 0, the bet is impossible and T4-ARITH should
        # have already returned 0.0; this is a guard against float rounding)
        if self._h_needed is not None and self._ab_remaining is not None:
            if self._ab_remaining <= 0:
                return f"ab_remaining_exhausted:h_needed={self._h_needed}"
            if self._h_needed > self._ab_remaining:
                return (
                    f"h_needed_exceeds_ab_remaining:"
                    f"h_needed={self._h_needed},ab_remaining={self._ab_remaining}"
                )

        # Check 7 — T4-CORR downward-only invariant (ADR-0029 Principle 6)
        # This check is only relevant when the correlation overlay is applied.
        # If adjusted_size > original_size, this is a hard architectural violation.
        if self._original_size is not None and self._adjusted_size is not None:
            if self._adjusted_size > self._original_size + 1e-9:
                # Do not just return False — raise the hard exception.
                # T4-CORR increasing a size is a structural error, not contamination.
                raise T4CorrDownwardViolation(
                    market_id=self._ticker,
                    original_size=self._original_size,
                    adjusted_size=self._adjusted_size,
                )

        return None


# ---------------------------------------------------------------------------
# BandInvariantChecker — per-band structural checks
# ---------------------------------------------------------------------------


class BandInvariantChecker:
    """
    Per-band structural invariants — checks that fire once per evaluation,
    not just at the pipeline boundary.

    These are the "is the math doing what it's supposed to do?" checks.
    They do not halt evaluation (unlike SemanticFloorViolation). They emit
    WARNING to C6 and update the SemanticHealthState for the C8 dashboard.

    Intended to be called from the evaluation loop after inputs are assembled
    but before evaluate_forecast() runs.
    """

    # T1 MLB: plausible hit threshold range (Kalshi MLB player hits markets)
    T1_MLB_THRESHOLD_MIN = 1
    T1_MLB_THRESHOLD_MAX = 3   # >3 hits in a game is rare; higher = suspect data

    # T4-FLOW: plausible score differential (outside = ESPN parser artifact)
    T4_FLOW_SCORE_DIFF_MAX = 60  # NBA; extreme blowout is ~50 pts

    # T4-LINEUP: max players changing per cycle (> 2 = data artifact)
    T4_LINEUP_MAX_CHANGES_PER_CYCLE = 2

    # T4-PROJ: lambda_prior fallback default (from t4_execution_engine.py)
    # If a player's lambda_t1_prior == this fallback, their T4-PROJ signal
    # is not empirically grounded — it is the module default.
    T4_PROJ_LAMBDA_DEFAULT = 20.0

    @classmethod
    def check_t1_mlb_threshold(
        cls,
        threshold: int,
        ticker: str,
        pipeline_id: str,
    ) -> Optional[ContractViolation]:
        """
        T1 MLB: threshold must be in [1, 3].

        A threshold of 0 is always True (100% probability) and should be
        filtered before forecast generation. A threshold of 4+ hits in a
        single game is an uncommon market that may indicate a parsing error
        (e.g., a season total parsed as a single-game threshold).
        """
        if cls.T1_MLB_THRESHOLD_MIN <= threshold <= cls.T1_MLB_THRESHOLD_MAX:
            return None
        return ContractViolation(
            contract_type=ContractType.BAND_INVARIANT,
            band="T1",
            pipeline_id=pipeline_id,
            violation_id=f"THR-{uuid.uuid4().hex[:8].upper()}",
            violation_reason="t1_mlb_threshold_out_of_range",
            payload={
                "threshold": threshold,
                "ticker": ticker,
                "threshold_min": cls.T1_MLB_THRESHOLD_MIN,
                "threshold_max": cls.T1_MLB_THRESHOLD_MAX,
                "note": (
                    "threshold=0 → p=1.0 trivially; threshold≥4 → very rare market "
                    "or parsing error (season total vs single-game threshold)."
                ),
            },
        )

    @classmethod
    def check_t4_proj_lambda(
        cls,
        lambda_prior: float,
        player_id: Any,
        band: str = "T4-PROJ",
    ) -> Optional[ContractViolation]:
        """
        T4-PROJ: lambda_prior should not be the module default (20.0).

        If lambda_t1_prior == T4_PROJ_LAMBDA_DEFAULT for a player, their
        Bayesian posterior is anchored on an arbitrary fallback, not on
        historical data. The signal is not empirically grounded.

        This is not a hard violation (the math still runs) but it is a
        data-quality flag that should appear in the health snapshot.
        """
        if abs(lambda_prior - cls.T4_PROJ_LAMBDA_DEFAULT) > 0.01:
            return None
        return ContractViolation(
            contract_type=ContractType.BAND_INVARIANT,
            band=band,
            pipeline_id="PIPE-07",
            violation_id=f"LMBD-{uuid.uuid4().hex[:8].upper()}",
            violation_reason="t4_proj_lambda_prior_is_fallback",
            payload={
                "lambda_prior": lambda_prior,
                "player_id": player_id,
                "default_value": cls.T4_PROJ_LAMBDA_DEFAULT,
                "note": (
                    "lambda_t1_prior == 20.0 (module fallback). Player's pregame "
                    "context was not loaded from C1/C2. Bayesian posterior is "
                    "anchored on an arbitrary default, not historical data. "
                    "Pregame context required for T4-PROJ signal integrity."
                ),
            },
        )

    @classmethod
    def check_t4_flow_score_diff(
        cls,
        score_differential: int,
        game_id: str,
    ) -> Optional[ContractViolation]:
        """
        T4-FLOW: score differential must be in plausible range.

        An NBA blowout record is ~73 points. Values outside [-60, 60] are
        almost certainly ESPN parser artifacts (int conversion of a None,
        or a score from a different sport parsed into the NBA scoreboard).
        """
        if abs(score_differential) <= cls.T4_FLOW_SCORE_DIFF_MAX:
            return None
        return ContractViolation(
            contract_type=ContractType.BAND_INVARIANT,
            band="T4-FLOW",
            pipeline_id="PIPE-07",
            violation_id=f"SCRDIFF-{uuid.uuid4().hex[:8].upper()}",
            violation_reason="t4_flow_score_differential_out_of_range",
            payload={
                "score_differential": score_differential,
                "game_id": game_id,
                "max_plausible": cls.T4_FLOW_SCORE_DIFF_MAX,
                "note": (
                    "Score differential exceeds historical NBA record (≈73 pts). "
                    "Likely ESPN parser artifact (None→0 conversion, or cross-sport "
                    "data contamination). Do not fire FLOW bets on this game state."
                ),
            },
        )


# ---------------------------------------------------------------------------
# SemanticContractMonitor — C7 integration class
# ---------------------------------------------------------------------------


class SemanticContractMonitor:
    """
    C7-facing integration: maintains session-level semantic health state and
    provides the check_band_invariants() interface called from SystemMonitor.

    Thread-safe via threading.Lock.

    Lifecycle:
      Constructed once per session alongside C7 SystemMonitor.
      Callers (PIPE scripts, T4 evaluation loops) call record_violation()
      each time a ContractViolation or SemanticFloorViolation occurs.
      SystemMonitor.check_and_alert() calls get_health_state() to include
      semantic health in the C8 dashboard snapshot.

    Callers do NOT call check_band_invariants() themselves — they record
    violations as they encounter them, and the monitor accumulates.

    Note: SemanticFloorViolation raises an exception (the pipeline catches it
    and calls record_floor_violation() before halting). ContaminationGuard
    auto-logs to C6 and returns False — callers record via
    record_contamination_halt() for session-level tracking.
    """

    def __init__(
        self,
        logger: Any,               # AuditLogger
        session_id: Optional[str],
        snapshot_id: str,
    ) -> None:
        self._logger = logger
        self._session_id = session_id
        self._snapshot_id = snapshot_id
        self._lock = threading.Lock()
        self._state = SemanticHealthState(
            session_id=session_id,
            computed_at=_utc_now_iso(),
        )

    # ------------------------------------------------------------------
    # Violation recording (called by callers, not internally)
    # ------------------------------------------------------------------

    def record_floor_violation(
        self,
        exc: SemanticFloorViolation,
    ) -> None:
        """
        Record a SemanticFloorViolation after it has been caught by the pipeline.

        The pipeline is responsible for halting itself (raise/return after catching).
        This method updates the session state so the C8 dashboard reflects
        that a floor violation occurred this session.

        Also emits semantic_floor_violation to C6 at CRITICAL severity.
        """
        ts = _utc_now_iso()
        with self._lock:
            self._state.n_floor_violations_session += 1
            self._state.last_floor_violation_ts = ts
            self._state.is_semantically_dark = True

        ok = self._logger.log(
            component="C7-SEMANTIC",
            event_type="semantic_floor_violation",
            payload={
                "pipeline_id": exc.pipeline_id,
                "sport": exc.sport,
                "games_fetched": exc.games_fetched,
                "matched_players": exc.matched_players,
                "diagnosis": exc.diagnosis,
                "session_floor_violations": self._state.n_floor_violations_session,
                "action_required": (
                    "Pipeline is semantically dark. Halt immediately. "
                    "Check: (1) naming normalization between ESPN and pregame context, "
                    "(2) market series ticker correctness, "
                    "(3) pregame context file freshness (PIPE-06pre ran today?), "
                    "(4) all markets settled before pipeline reached them."
                ),
            },
            severity="CRITICAL",
            session_id=self._session_id,
            snapshot_id=self._snapshot_id,
        )
        if not ok:
            logger.error(
                "SemanticContractMonitor: C6 write failure on semantic_floor_violation"
            )

    def record_contamination_halt(self, ticker: str, reason: str) -> None:
        """
        Record a contamination halt for session-level tracking.

        Called by the T4 evaluation loop after ContaminationGuard.is_clean()
        returns False. The ContaminationGuard itself already logs to C6 —
        this method only updates the session counter.
        """
        ts = _utc_now_iso()
        with self._lock:
            self._state.n_contamination_halts_session += 1
            self._state.last_contamination_halt_ts = ts

    def record_band_invariant_breach(
        self,
        violation: ContractViolation,
    ) -> None:
        """
        Record a band invariant breach and emit to C6.

        Called when BandInvariantChecker returns a non-None ContractViolation.
        The evaluation continues (invariant breaches do not halt), but the
        violation is recorded and emitted for monitoring.
        """
        with self._lock:
            self._state.n_band_invariant_breaches_session += 1
            self._state.last_breach_band = violation.band

        ok = self._logger.log(
            component="C7-SEMANTIC",
            event_type="semantic_contract_breach",
            payload={
                "contract_type": violation.contract_type.value,
                "band": violation.band,
                "pipeline_id": violation.pipeline_id,
                "violation_id": violation.violation_id,
                "violation_reason": violation.violation_reason,
                **violation.payload,
            },
            severity="WARNING",
            session_id=self._session_id,
            snapshot_id=self._snapshot_id,
        )
        if not ok:
            logger.error(
                "SemanticContractMonitor: C6 write failure on semantic_contract_breach "
                "violation_id=%s", violation.violation_id,
            )

    def record_corr_downward_violation(
        self,
        exc: T4CorrDownwardViolation,
    ) -> None:
        """
        Record a T4-CORR downward invariant breach (ADR-0029 Principle 6).

        This is a structural error — the correlation overlay increased a size.
        Emits CRITICAL to C6. Caller must trigger kill switch.
        """
        with self._lock:
            self._state.n_corr_downward_violations_session += 1

        ok = self._logger.log(
            component="C7-SEMANTIC",
            event_type="semantic_corr_downward_violation",
            payload={
                "market_id": exc.market_id,
                "original_size": exc.original_size,
                "adjusted_size": exc.adjusted_size,
                "delta": exc.adjusted_size - exc.original_size,
                "adr_ref": "ADR-0029 Principle 6 — T4-CORR downward-only invariant",
                "action_required": (
                    "T4-CORR increased a position size. This is structurally "
                    "impossible per ADR-0029. Trigger kill switch immediately. "
                    "Do not allow further T4-CORR bets until root cause is resolved."
                ),
            },
            severity="CRITICAL",
            session_id=self._session_id,
            snapshot_id=self._snapshot_id,
        )
        if not ok:
            logger.error(
                "SemanticContractMonitor: C6 write failure on CORR downward violation"
            )

    # ------------------------------------------------------------------
    # Health state (read by C7 get_health_snapshot)
    # ------------------------------------------------------------------

    def get_health_state(self) -> SemanticHealthState:
        """
        Return a snapshot of current semantic health state.

        Called by C7 SystemMonitor.get_health_snapshot() to include semantic
        health in the C8 dashboard feed.

        Thread-safe: returns a copy so the caller can read without holding the lock.
        """
        with self._lock:
            ts = _utc_now_iso()
            return SemanticHealthState(
                n_floor_violations_session=self._state.n_floor_violations_session,
                n_contamination_halts_session=self._state.n_contamination_halts_session,
                n_band_invariant_breaches_session=self._state.n_band_invariant_breaches_session,
                n_corr_downward_violations_session=self._state.n_corr_downward_violations_session,
                last_floor_violation_ts=self._state.last_floor_violation_ts,
                last_contamination_halt_ts=self._state.last_contamination_halt_ts,
                last_breach_band=self._state.last_breach_band,
                is_semantically_dark=self._state.is_semantically_dark,
                session_id=self._session_id,
                computed_at=ts,
            )

    def emit_health_snapshot(self, session_id: Optional[str] = None) -> None:
        """
        Emit a semantic_health_snapshot event to C6.

        Called periodically (e.g., once per 10 evaluation cycles) to provide
        a running session summary. The C8 dashboard can poll this for trend data.
        """
        state = self.get_health_state()
        self._logger.log(
            component="C7-SEMANTIC",
            event_type="semantic_health_snapshot",
            payload={
                "n_floor_violations": state.n_floor_violations_session,
                "n_contamination_halts": state.n_contamination_halts_session,
                "n_band_invariant_breaches": state.n_band_invariant_breaches_session,
                "n_corr_downward_violations": state.n_corr_downward_violations_session,
                "is_semantically_dark": state.is_semantically_dark,
                "last_floor_violation_ts": state.last_floor_violation_ts,
                "last_contamination_halt_ts": state.last_contamination_halt_ts,
                "last_breach_band": state.last_breach_band,
            },
            severity="INFO",
            session_id=session_id or self._session_id,
            snapshot_id=self._snapshot_id,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

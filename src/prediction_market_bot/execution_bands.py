"""
Execution Band Framework
========================
Module:   execution_bands
Phase:    Phase 7+ (design skeleton active Phase 6 idle period)
Purpose:  Define time-horizon execution bands and their model/execution
          requirements. Each band maps to a pipeline, a model complexity tier,
          a Kelly fraction, and an execution SLA.

Inspired by HFT time-horizon principle:
  - Ultra-low latency (T4/T5): execution quality IS the edge; minimal model
  - Longer horizon (T1/T2/T3): model complexity scales with available compute time

Band summary (ADR-0010 Kelly fractions):
  T1 — Multi-day:    Full LR+Platt (78 feat); PIPE-02; Kelly 0.10
  T2 — Same-day:     Injury overlay on T1; PIPE-05; Kelly 0.13
  T3 — Pre-tip:      Momentum signal only; PIPE-06; Kelly 0.07
  T4 — In-play:      Poisson game-state; PIPE-07 (real-time infra required); Kelly 0.20
  T5 — Late-game:    Arithmetic certainty; PIPE-08 (real-time infra required); Kelly 0.25

Governance:
  T1/T2/T3 are buildable on current cron infrastructure.
  T4/T5 require full real-time C5 rebuild (Phase 8+).
  Kelly fractions follow variance-scaling (ADR-0010): higher fraction at lower
  λ-estimation uncertainty. T4/T5 are threshold-specific (lower σ) → higher k.
  T1 uses player-level LR estimate (higher σ) → lower k. Reserve mandate: ≥40%
  bankroll uncommitted after T1 batch (warning-only at paper scale).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


# ---------------------------------------------------------------------------
# Band enum
# ---------------------------------------------------------------------------


class ExecutionBand(Enum):
    """
    Time-horizon execution bands.

    Each band determines which model runs, what execution quality is required,
    and what Kelly fraction applies. Do not change band semantics without
    updating EXECUTION_BANDS.md and BandConfig below.
    """
    T1_MULTI_DAY = "T1"    # Full ML pipeline — current PIPE-02; Strategy A primary
    T2_SAME_DAY  = "T2"    # Injury/lineup overlay on T1 — PIPE-05; Strategy B
    T3_PRE_TIP   = "T3"    # Momentum signal scan — PIPE-06; Strategy J simplified
    T4_IN_PLAY   = "T4"    # AGGREGATE PARENT — in-play budget/risk unit (ADR-0013 T4_BAND_WEIGHT=0.27);
                           #   sub-bands below route beneath it (ADR-0029). PIPE-07; requires real-time.
    T5_LATE_GAME = "T5"    # Arithmetic certainty (pts needed/time) — PIPE-08; requires real-time

    # --- T4 sub-bands (ADR-0029, ACCEPTED Tier A; sub-band ROSTER is Tier B / PROVISIONAL) ---
    # These are in-game routing destinations beneath the T4_IN_PLAY aggregate. ADR-0029's
    # two-tier acceptance model: the existence of a sub-band layer (the "machine") is Tier A
    # (frozen); WHICH sub-bands exist, and every numeric attached to them, is Tier B —
    # revisable via DECISION_LOG (NOT a superseding ADR) until each sub-band clears its own
    # Phase 8 Activation Gate. ALL are BLOCKED (requires_realtime=True, Phase 8). T4-MICRO is
    # NOT here — it was carved out to ADR-0030 as a no-`model_p` execution-quality strategy class.
    T4_STAGED    = "T4-STAGED"     # Pre-game conditional fill (resting order placed at T3)
    T4_EVENT     = "T4-EVENT"      # Discrete stat-event reaction (multi-tree by event type)
    T4_LINEUP    = "T4-LINEUP"     # Live lineup / rotation change (portfolio cascade)
    T4_FLOW      = "T4-FLOW"       # Accumulated game-state / context pattern (incl. blowout)
    T4_SENTIMENT = "T4-SENTIMENT"  # Market price drift (informed vs noise classification)
    T4_PROJ      = "T4-PROJ"       # Bayesian posterior full-game projection (richest signal)
    T4_ARITH     = "T4-ARITH"      # Threshold-approaching arithmetic near-certainty (pre-T5)
    T4_BOUNDARY  = "T4-BOUNDARY"   # Quarter/halftime structural reset (structural overlay)
    T4_CORR      = "T4-CORR"       # Cross-market correlation overlay (downward-only, portfolio)
    T4_EXIT      = "T4-EXIT"       # Active position management / exit signals (portfolio)

    # --- MLB-native T4 sub-bands (ADR-0039, DS sign-off SESSION 108/T-219) ---
    # NOT part of the NBA T4_SUBBAND_REGISTRY/T4_SUBBANDS roster above — MLB gets its own
    # parallel registry (T4_MLB_SUBBAND_REGISTRY) because T4M-PROJ is a documented exception
    # to the "all T4 sub-bands are BLOCKED" invariant: it is a RELABELING of the flat model
    # already live in run_t4_mlb_live.py (ADR-0023), not a net-new Phase-8-gated build.
    # T4M-ARITH and T4M-FLOW ARE net-new and ARE BLOCKED, following the NBA pattern exactly.
    # Only these three are authorized (T-219) — T4M-BOUNDARY and the rest of ADR-0039's
    # Tier B roster are scoped but NOT built.
    T4M_PROJ  = "T4M-PROJ"    # ACTIVE — flat Binomial model, already running (run_t4_mlb_live.py)
    T4M_ARITH = "T4M-ARITH"   # BLOCKED — near-certain band between p_t4's 0.0/1.0 hard boundaries
    T4M_FLOW  = "T4M-FLOW"    # BLOCKED — accumulated game-state pattern, incl. FLOW-BLOWOUT tree

    # --- NFL/NHL-native T4 sub-bands (ADR-0062, T-522) ---
    # 17.1 registry+band scaffolding ONLY (no behavior change). ADR-0062 §4/§6 disagreed on
    # whether BOUNDARY is authorization-eligible at this step; resolved conservative (GG-246):
    # ARITH and FLOW only, mirroring MLB's own never-built T4M-BOUNDARY. EVENT is excluded
    # pending C1 ingestion verification (ADR-0062 §7). Four-letter sport-code convention
    # (T4NFL-/T4NHL-, NOT the superseded T4N-, per GG-233/ADR-0062 §0). FLOW-BLOWOUT is a mode
    # within FLOW here too — no separate enum member, mirroring MLB's T4M_FLOW exactly.
    T4NFL_ARITH = "T4NFL-ARITH"   # BLOCKED — near-certain band, threshold-approaching (pre-boundary)
    T4NFL_FLOW  = "T4NFL-FLOW"    # BLOCKED — accumulated game-state pattern, incl. blowout mode
    T4NHL_ARITH = "T4NHL-ARITH"   # BLOCKED — near-certain band, threshold-approaching (pre-boundary)
    T4NHL_FLOW  = "T4NHL-FLOW"    # BLOCKED — accumulated game-state pattern, incl. blowout mode


# ---------------------------------------------------------------------------
# Band configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BandConfig:
    """
    Configuration for a single execution band.

    Attributes
    ----------
    band:
        The ExecutionBand this config applies to.
    model_class:
        Model type used at this horizon.
    max_compute_ms:
        Hard ceiling on model inference wall time (milliseconds).
        Enforced to prevent slow models from eating the edge window.
    execution_sla_s:
        Maximum acceptable order placement latency (seconds).
        At T4/T5 this is in single-digit seconds; at T1 it's irrelevant.
    kelly_fraction:
        Fractional Kelly multiplier. Decreases at shorter horizons
        (lower model confidence due to simplified signal).
        T5 exception: near-certainty warrants higher fraction.
    pipeline_id:
        Associated pipeline identifier (matches PIPELINES_JOBS.md).
    cron_schedule:
        Crontab expression for scheduled bands. None for event-driven bands.
    requires_realtime:
        True if this band requires sub-second event-driven infrastructure.
        T4/T5 are Phase 8+ — do not activate without full C5 rebuild.
    phase_active:
        Earliest phase at which this band can be activated.
    """
    band: ExecutionBand
    model_class: str
    max_compute_ms: int
    execution_sla_s: int
    kelly_fraction: float
    pipeline_id: str
    cron_schedule: Optional[str]
    requires_realtime: bool
    phase_active: str


# Band configurations — single source of truth for all timing and sizing parameters
BAND_CONFIGS: dict[ExecutionBand, BandConfig] = {
    ExecutionBand.T1_MULTI_DAY: BandConfig(
        band=ExecutionBand.T1_MULTI_DAY,
        model_class="full_lr_platt",         # LR+Platt, 78 features, qualitative enrichment
        max_compute_ms=30_000,               # 30s — full pipeline; batched; irrelevant to edge
        execution_sla_s=3600,                # 1 hour — execution timing immaterial at this horizon
        kelly_fraction=0.0,                   # ADR-0048 (2026-07-29, supersedes ADR-0040's 0.061): GG-135 found MAIN's real variance alone (independent of edge sign) produces ~100%/yr kill-switch trip probability at any positive Kelly; zeroed pending edge-conditional reactivation (ADR-0048 lookup table). DS sign-off: operator 2026-07-29. Evaluations continue to log for research; only sizing is zero.
        pipeline_id="PIPE-02",
        cron_schedule="30 21 * * *",         # 21:30 UTC daily (pre-game)
        requires_realtime=False,
        phase_active="Phase 6",
    ),
    ExecutionBand.T2_SAME_DAY: BandConfig(
        band=ExecutionBand.T2_SAME_DAY,
        model_class="injury_overlay",        # T1 output + injury/lineup adjustment (T-075)
        max_compute_ms=5_000,                # 5s — fast overlay on cached T1 output
        execution_sla_s=1800,                # 30 min — still relaxed; 4-8h before tip
        kelly_fraction=0.0,                  # ADR-0048 (2026-07-29, supersedes ADR-0010's 0.13): GG-135 ruin geometry applies to any positive Kelly on this book; zeroed pending edge-conditional reactivation. DS sign-off: operator 2026-07-29. Evaluations continue to log for research; only sizing is zero.
        pipeline_id="PIPE-05",
        cron_schedule="0 17 * * *",          # 17:00 UTC (12pm ET — afternoon of game day)
        requires_realtime=False,
        phase_active="Phase 7",              # Requires injury data source (T-075)
    ),
    ExecutionBand.T3_PRE_TIP: BandConfig(
        band=ExecutionBand.T3_PRE_TIP,
        model_class="momentum_signal",       # Price drift vs T1 forecast; no historical data
        max_compute_ms=500,                  # 500ms — reads cached T1 + live price only
        execution_sla_s=300,                 # 5 min — window closes at tip-off
        kelly_fraction=0.0,                  # ADR-0048 (2026-07-29, supersedes ADR-0010's 0.07): GG-135 ruin geometry applies to any positive Kelly on this book; zeroed pending edge-conditional reactivation. DS sign-off: operator 2026-07-29. Evaluations continue to log for research; only sizing is zero.
        pipeline_id="PIPE-06",
        # Extended to 03:00 UTC to cover late 10pm ET tip-offs (02:00 UTC).
        # Two entries needed because cron hour ranges cannot wrap midnight in one expr.
        # VPS cron.conf should use: */15 20-23 * * * and */15 0-3 * * *
        cron_schedule="*/15 20-23,0-3 * * *",
        requires_realtime=False,
        phase_active="Phase 7",
    ),
    ExecutionBand.T4_IN_PLAY: BandConfig(
        band=ExecutionBand.T4_IN_PLAY,
        model_class="bayesian_game_state",   # Bayesian update: current score + time remaining
        max_compute_ms=50,                   # 50ms — must be faster than market update latency
        execution_sla_s=5,                   # 5s — in-play window is seconds
        kelly_fraction=0.20,                 # ADR-0010: σ_λ≈0.5 in Q3/Q4 firing window; Q4 only (Phase 8 ACTIVE requires EXP-018)
        pipeline_id="PIPE-07",
        cron_schedule=None,                  # Event-driven — not cron-based
        requires_realtime=True,              # BLOCKED: requires real-time C5 rebuild (Phase 8+)
        phase_active="Phase 8",
    ),
    ExecutionBand.T5_LATE_GAME: BandConfig(
        band=ExecutionBand.T5_LATE_GAME,
        model_class="arithmetic_certainty",  # pts_needed / pace / time_remaining
        max_compute_ms=5,                    # 5ms — pure arithmetic; no model
        execution_sla_s=1,                   # 1s — final minutes; sub-second preferred
        kelly_fraction=0.25,                 # ADR-0010: arithmetic certainty gate p≥0.85; quarter-Kelly on f*
        pipeline_id="PIPE-08",
        cron_schedule=None,                  # Event-driven
        requires_realtime=True,              # BLOCKED: Phase 8+
        phase_active="Phase 8",
    ),

    # -----------------------------------------------------------------------
    # T4 sub-band configs (ADR-0029) — Tier B PROVISIONAL. ALL BLOCKED Phase 8.
    # -----------------------------------------------------------------------
    # kelly_fraction values here are the ADR-0029 PROVISIONAL placeholders (Tier B):
    # they are non-operational until each sub-band's named EXP completes (Principle 5),
    # and several are deliberately held below their formula output pending tail-calibration
    # (T4-PROJ NEAR-CERTAIN, T4-ARITH). The authoritative Tier B governance metadata
    # (exposure caps, EXP gates, alpha hypotheses, BLOCKED status) lives in
    # T4_SUBBAND_REGISTRY below — BandConfig only carries timing/sizing for uniformity.
    # execution_sla_s is nominal (immediate-execution principle: no time mandate; the
    # Layer-2 staleness check is the only execution gate). Sub-bands share PIPE-07.
    ExecutionBand.T4_STAGED: BandConfig(
        band=ExecutionBand.T4_STAGED,
        model_class="t3_resting_order",      # T3 decision; resting limit order fills in T4 time
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.07,                 # ADR-0029: inherits T3 Kelly (signal is a T3 decision)
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_EVENT: BandConfig(
        band=ExecutionBand.T4_EVENT,
        model_class="event_conditional_update",
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.05,                 # PROVISIONAL: EXP-EVENT-02 required; repricing-lag hypothesis unconfirmed
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_LINEUP: BandConfig(
        band=ExecutionBand.T4_LINEUP,
        model_class="t4proj_rotation",       # T4-PROJ posterior + rotation model (EXP-required)
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.05,                 # PROVISIONAL max (ADR-0029): EXP-LINEUP-01 required; below T4-PROJ
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_FLOW: BandConfig(
        band=ExecutionBand.T4_FLOW,
        model_class="context_multiplier",
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.08,                 # PROVISIONAL: ADR-0029 range 0.08–0.12 by phase/context; EXP-FLOW-01/02
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_SENTIMENT: BandConfig(
        band=ExecutionBand.T4_SENTIMENT,
        model_class="drift_classifier",      # informed vs noise drift classification
        max_compute_ms=50,
        execution_sla_s=120,                 # NOMINAL: re-eval every 30–120s of sustained drift (EXP-SENT-01)
        kelly_fraction=0.05,                 # PROVISIONAL: EXP-SENT-01 required; lowest-confidence signal
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_PROJ: BandConfig(
        band=ExecutionBand.T4_PROJ,
        model_class="bayesian_posterior",    # Full Poisson survival, game-state-updated lambda (richest signal)
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.167,                # PROVISIONAL LATE-regime ceiling. Dynamic schedule (ADR-0029):
                                             #   EARLY 0.010 / MID 0.032–0.078 / LATE 0.078–0.167.
                                             #   NEAR-CERTAIN held ≤0.167 (formula diverges; 0.25 is a HARD
                                             #   ceiling, NOT derived) until EXP-PROJ-01 confirms tail calibration.
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_ARITH: BandConfig(
        band=ExecutionBand.T4_ARITH,
        model_class="arithmetic_survival",   # near-certainty pre-T5; re-derive from arithmetic model, not 1/σ_λ
        max_compute_ms=10,
        execution_sla_s=5,
        kelly_fraction=0.167,                # PROVISIONAL & NON-OPERATIONAL. ADR-0029 placeholder is 0.22 but it
                                             #   is HELD at the T4-PROJ LATE ceiling (0.167) here until EXP-ARITH-01
                                             #   confirms p_arith tail reliability. Do NOT raise without EXP.
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_BOUNDARY: BandConfig(
        band=ExecutionBand.T4_BOUNDARY,
        model_class="structural_reset",      # quarter/halftime re-evaluation; no independent Kelly
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.167,                # Inherits T4-PROJ (new entries) / T4-EXIT (exits); no independent size
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_CORR: BandConfig(
        band=ExecutionBand.T4_CORR,
        model_class="correlation_overlay",   # downward-only invariant; convergence premium for independent signals
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.0,                  # Overlay — modifies other sub-bands' sizing; no own position
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),
    ExecutionBand.T4_EXIT: BandConfig(
        band=ExecutionBand.T4_EXIT,
        model_class="exit_management",       # continuous position monitoring; priority/bypass queue
        max_compute_ms=50,
        execution_sla_s=5,                   # ≤5s priority (same as T4 kill-switch requirement, GG-038)
        kelly_fraction=0.0,                  # Manages existing positions; no new sizing
        pipeline_id="PIPE-07",
        cron_schedule=None,
        requires_realtime=True,
        phase_active="Phase 8",
    ),

    # -----------------------------------------------------------------------
    # MLB-native T4 sub-band configs (ADR-0039, T-219). See T4_MLB_SUBBAND_REGISTRY
    # below for Tier B governance metadata (status, exp_gate, alpha_hypothesis).
    # -----------------------------------------------------------------------
    ExecutionBand.T4M_PROJ: BandConfig(
        band=ExecutionBand.T4M_PROJ,
        model_class="binomial_flat",         # p_hits_gte_threshold — run_t4_mlb_live.py
        max_compute_ms=50,
        execution_sla_s=45,                  # matches the existing 45s poll cycle (POLL_INTERVAL_S)
        kelly_fraction=0.0,                  # ADR-0048 (2026-07-29, supersedes ADR-0023's KELLY_T4=0.10): zeroed pending GG-105 anti-predictive-edge remediation and GG-142 abs()-gate fix; ADR-0048 lookup table gates reactivation on validated per-bet edge. DS sign-off: operator 2026-07-29. Evaluations continue to log for research; only sizing is zero.
        pipeline_id="PIPE-07-MLB",
        cron_schedule=None,                  # Event-driven within the 45s poll loop
        requires_realtime=False,             # Already running on cron/poll infra, not real-time infra
        phase_active="Phase 6",              # Live today — not gated behind Phase 8
    ),
    ExecutionBand.T4M_ARITH: BandConfig(
        band=ExecutionBand.T4M_ARITH,
        model_class="binomial_near_certain",  # near-certain band within p_hits_gte_threshold's boundaries
        max_compute_ms=10,
        execution_sla_s=45,
        kelly_fraction=0.10,                  # PROVISIONAL & NON-OPERATIONAL: held at T4M-PROJ's ceiling
                                               #   (KELLY_T4) until EXP-ARITH-MLB-01. Do NOT raise without EXP.
        pipeline_id="PIPE-07-MLB",
        cron_schedule=None,
        requires_realtime=True,               # BLOCKED: Phase 8 (net-new sub-band, ADR-0039)
        phase_active="Phase 8",
    ),
    ExecutionBand.T4M_FLOW: BandConfig(
        band=ExecutionBand.T4M_FLOW,
        model_class="context_multiplier_mlb",  # score-differential blowout multiplier on p_t4
        max_compute_ms=50,
        execution_sla_s=45,
        kelly_fraction=0.08,                   # PROVISIONAL: borrows NBA T4-FLOW's starting order of
                                                #   magnitude (no MLB precedent exists). EXP-FLOW-MLB-01.
        pipeline_id="PIPE-07-MLB",
        cron_schedule=None,
        requires_realtime=True,                # BLOCKED: Phase 8 (net-new sub-band, ADR-0039)
        phase_active="Phase 8",
    ),

    # -----------------------------------------------------------------------
    # NFL/NHL-native T4 sub-band configs (ADR-0062, T-522). See
    # T4_NFL_SUBBAND_REGISTRY / T4_NHL_SUBBAND_REGISTRY below for Tier B governance
    # metadata (status, exp_gate, alpha_hypothesis). 17.1 scaffolding: NOT_IMPLEMENTED,
    # kelly_fraction=0.0, nothing wired.
    # -----------------------------------------------------------------------
    ExecutionBand.T4NFL_ARITH: BandConfig(
        band=ExecutionBand.T4NFL_ARITH,
        model_class="arithmetic_survival_nfl",  # near-certain band, mirrors MLB's binomial_near_certain shape
        max_compute_ms=10,
        execution_sla_s=5,
        kelly_fraction=0.0,                     # Scaffolding only — no model, no EXP, no sizing.
        pipeline_id="PIPE-07-NFL",
        cron_schedule=None,
        requires_realtime=True,                 # BLOCKED: Phase 8 (net-new sub-band, ADR-0062)
        phase_active="Phase 8",
    ),
    ExecutionBand.T4NFL_FLOW: BandConfig(
        band=ExecutionBand.T4NFL_FLOW,
        model_class="context_multiplier_nfl",   # score-differential / blowout multiplier, mirrors MLB
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.0,                     # Scaffolding only — no model, no EXP, no sizing.
        pipeline_id="PIPE-07-NFL",
        cron_schedule=None,
        requires_realtime=True,                 # BLOCKED: Phase 8 (net-new sub-band, ADR-0062)
        phase_active="Phase 8",
    ),
    ExecutionBand.T4NHL_ARITH: BandConfig(
        band=ExecutionBand.T4NHL_ARITH,
        model_class="arithmetic_survival_nhl",
        max_compute_ms=10,
        execution_sla_s=5,
        kelly_fraction=0.0,                     # Scaffolding only — no model, no EXP, no sizing.
        pipeline_id="PIPE-07-NHL",
        cron_schedule=None,
        requires_realtime=True,                 # BLOCKED: Phase 8 (net-new sub-band, ADR-0062)
        phase_active="Phase 8",
    ),
    ExecutionBand.T4NHL_FLOW: BandConfig(
        band=ExecutionBand.T4NHL_FLOW,
        model_class="context_multiplier_nhl",
        max_compute_ms=50,
        execution_sla_s=5,
        kelly_fraction=0.0,                     # Scaffolding only — no model, no EXP, no sizing.
        pipeline_id="PIPE-07-NHL",
        cron_schedule=None,
        requires_realtime=True,                 # BLOCKED: Phase 8 (net-new sub-band, ADR-0062)
        phase_active="Phase 8",
    ),
}


# T4 sub-band roster (ADR-0029 Tier B — PROVISIONAL; revisable via DECISION_LOG).
# Order follows the ADR taxonomy. T4-MICRO is intentionally absent (ADR-0030 carve-out).
T4_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4_STAGED,
    ExecutionBand.T4_EVENT,
    ExecutionBand.T4_LINEUP,
    ExecutionBand.T4_FLOW,
    ExecutionBand.T4_SENTIMENT,
    ExecutionBand.T4_PROJ,
    ExecutionBand.T4_ARITH,
    ExecutionBand.T4_BOUNDARY,
    ExecutionBand.T4_CORR,
    ExecutionBand.T4_EXIT,
)


def is_t4_subband(band: ExecutionBand) -> bool:
    """True if `band` is one of the ADR-0029 T4 sub-bands (not the T4_IN_PLAY aggregate)."""
    return band in T4_SUBBANDS


def t4_parent(band: ExecutionBand) -> ExecutionBand:
    """
    Return the aggregate parent band for a T4 sub-band.

    T4 sub-bands roll up to ExecutionBand.T4_IN_PLAY for budget (ADR-0013 T4_BAND_WEIGHT)
    and aggregate risk accounting. Non-sub-band bands return themselves.
    """
    return ExecutionBand.T4_IN_PLAY if is_t4_subband(band) else band


def get_band_config(band: ExecutionBand) -> BandConfig:
    """Return the BandConfig for a given ExecutionBand."""
    return BAND_CONFIGS[band]


def get_active_bands(include_realtime: bool = False) -> list[BandConfig]:
    """
    Return all bands that can run on current cron infrastructure.

    Parameters
    ----------
    include_realtime:
        If False (default), excludes T4/T5 which require real-time infra rebuild.
    """
    return [
        cfg for cfg in BAND_CONFIGS.values()
        if include_realtime or not cfg.requires_realtime
    ]


# ---------------------------------------------------------------------------
# Band exit noise buffers — ADR-0018 + ADR-0019 (T4 amended T-152/ADR-0019-A01)
# ---------------------------------------------------------------------------
# Derived analytically in EXP-019A: NOISE_BUFFER_BAND = max(2×σ_p, EXIT_NET_COST_BAND)
# where σ_p = |dP/dλ| × σ_λ evaluated at the band's representative firing window.
# EXP-019B/C empirical (G4, n=1199 T4 positions / n=5192 spread obs):
#   observed mean buffer=0.182, p50=0.187; EXP-019C p90 spread=0.170.
#   within_20pct=False — analytic 0.139 deviates >20% from empirical 0.182.
#   T4 value raised per T-152 update gate; see DECISION_LOG ADR-0019-A01.

NOISE_BUFFER_BAND_T1: float = 0.22053   # EXP-019A analytic; σ_λ_ingame=1.45 (Q2 midpoint, 24min elapsed)
NOISE_BUFFER_BAND_T2: float = 0.22053   # same σ_λ basis as T1
NOISE_BUFFER_BAND_T3: float = 0.22053   # same σ_λ basis as T1
NOISE_BUFFER_BAND_T4: float = 0.19      # EXP-019B/C empirical (G4): obs mean=0.182, p50=0.187; ADR-0019-A01
NOISE_BUFFER_BAND_T5: float = 0.13328   # EXP-019A analytic; near-deterministic (final 3 min)

# --- Per-sub-band noise buffers (ADR-0029) — Tier B PROVISIONAL ---
# NOISE_BUFFER_BAND_T4 (0.19) REMAINS the aggregate default and the live-exit basis in
# run_t4_live.py — it is NOT split away. Sub-bands inherit it unless ADR-0029 specifies
# otherwise. EXP-019D must re-derive these per sub-band (max(2·σ_p_at_firing, EXIT_NET_COST).
# `None` = EXP-required, no provisional value; callers must fall back to NOISE_BUFFER_BAND_T4.
NOISE_BUFFER_T4_STAGED: float = NOISE_BUFFER_BAND_T3      # 0.22053 — sized/approved at T3; T3 buffer governs
NOISE_BUFFER_T4_FLOW: float = NOISE_BUFFER_BAND_T4        # 0.19 — monolithic-T4 empirical basis is closest match
NOISE_BUFFER_T4_PROJ: float = NOISE_BUFFER_BAND_T4        # 0.19 — direct inheritance; primary intended basis
NOISE_BUFFER_T4_EVENT: Optional[float] = None            # EXP-EVENT required; expected tighter (< 0.19, short window)
NOISE_BUFFER_T4_LINEUP: Optional[float] = None           # EXP-LINEUP required; expected moderate (portfolio-level)
NOISE_BUFFER_T4_SENTIMENT: Optional[float] = None        # EXP-SENT required
NOISE_BUFFER_T4_ARITH: Optional[float] = None            # EXP-ARITH required; expected < 0.19 (near-certainty)

# Exit guard: no exits in the final N minutes — T5 arithmetic certainty logic takes over.
EXIT_MIN_TIME_REMAINING_MIN: float = 3.0

# ADR-0019 Tier 2 activation gate.
# SESSION 43 DS override: set True for G4/G5 paper trading. Rationale: EXP-019B
# analytic validated (79.9% correct exits, 0 false exits); empirical data (T-152)
# can only be collected by running exits; T4 pool is isolated (no real capital risk).
# GG-017 Tier 2 gate remains OPEN until T-152/T-153 complete.
EXIT_MECHANICS_ACTIVE: bool = True


# ---------------------------------------------------------------------------
# T4 sub-band governance registry — ADR-0029 Tier B (PROVISIONAL)
# ---------------------------------------------------------------------------
#
# GOVERNANCE: This registry is the code-level encoding of ADR-0029's two-tier
# acceptance model. The EXISTENCE of a sub-band layer beneath T4_IN_PLAY is Tier A
# (frozen on DS sign-off, 2026-06-22 S67). Everything in THIS registry — the roster,
# every Kelly fraction, exposure cap, noise buffer, and alpha hypothesis — is Tier B:
# PROVISIONAL and revisable via a DECISION_LOG entry (NOT a superseding ADR) until each
# sub-band clears its own Phase 8 Activation Gate, at which point its then-current values
# are frozen by an activation ADR (APR-XXXX).
#
# HARD INVARIANTS (do not weaken without a superseding ADR):
#   - Every sub-band is status="BLOCKED" until its Phase 8 Activation Gate clears.
#   - No sub-band may deploy capital while any exp_gate EXP is unmet (Principle 5).
#   - max_concurrent_exposure_pct_t4 caps are % of the T4 AGGREGATE budget (T4_BAND_WEIGHT
#     × bankroll, ADR-0013), not of total equity; the ADR-0026 60%-equity invariant and
#     the T4 aggregate cap both still bind on top of these.
# T4-MICRO is absent by design (carved out to ADR-0030 — no `model_p`).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class T4SubBandSpec:
    """
    Tier B (provisional) governance spec for a single T4 sub-band (ADR-0029).

    Separate from BandConfig: BandConfig carries timing/sizing for uniformity with
    T1–T5; this carries the provisional governance metadata that ADR-0029 explicitly
    leaves un-frozen. `status` must remain "BLOCKED" until the sub-band's Phase 8
    Activation Gate clears.

    Fields
    ------
    band : ExecutionBand
        The sub-band enum member.
    information_class : str
        What information the sub-band acts on (the ADR's organizing principle).
    provisional_kelly : float | None
        ADR-0029 placeholder Kelly. PROVISIONAL — non-operational until exp_gate clears.
        None for pure overlays (T4-CORR) / position-managers (T4-EXIT) with no own size.
    kelly_basis : str
        Derivation status / EXP gate / hold note for the Kelly value.
    noise_buffer : float | None
        Provisional exit noise buffer. None = EXP-required (fall back to NOISE_BUFFER_BAND_T4).
    max_concurrent_exposure_pct_t4 : float | None
        Max concurrent exposure as a fraction of the T4 aggregate budget. None = overlay /
        inherits parent (no independent cap).
    exp_gate : tuple[str, ...]
        Named EXPs that must complete before this sub-band can leave BLOCKED.
    alpha_hypothesis : str
        The falsifiable edge claim this sub-band rests on (Tier B — may be disproven).
    status : str
        "BLOCKED" until Phase 8 Activation Gate. Never "ACTIVE" without an activation ADR.
    notes : str
        Cross-references, dependencies, structural role.
    """
    band: ExecutionBand
    information_class: str
    provisional_kelly: Optional[float]
    kelly_basis: str
    noise_buffer: Optional[float]
    max_concurrent_exposure_pct_t4: Optional[float]
    exp_gate: tuple[str, ...]
    alpha_hypothesis: str
    status: str = "BLOCKED"
    notes: str = ""


T4_SUBBAND_REGISTRY: dict[ExecutionBand, T4SubBandSpec] = {
    ExecutionBand.T4_STAGED: T4SubBandSpec(
        band=ExecutionBand.T4_STAGED,
        information_class="Pre-game T3 decision → resting limit order that fills in T4 time",
        provisional_kelly=0.07,
        kelly_basis="Inherits T3 Kelly (ADR-0010); tracks T3 if T3 Kelly changes. Not independent.",
        noise_buffer=NOISE_BUFFER_T4_STAGED,
        max_concurrent_exposure_pct_t4=0.30,
        exp_gate=(),  # T3-derived; no T4 EXP — but infra (resting-order C5) still required
        alpha_hypothesis="A T3-approved bet can be filled at a better in-game price via a resting order.",
        notes="Fills charged to T4 budget (execute in T4 time/capital), not T3. Zero live T4 API calls.",
    ),
    ExecutionBand.T4_EVENT: T4SubBandSpec(
        band=ExecutionBand.T4_EVENT,
        information_class="Discrete stat event (made shot, foul, sub) → event-conditional posterior",
        provisional_kelly=0.05,
        kelly_basis="PROVISIONAL. ADR-0010 variance-scaling at event-time σ_λ; per-tree. EXP-EVENT-02 required.",
        noise_buffer=NOISE_BUFFER_T4_EVENT,
        max_concurrent_exposure_pct_t4=0.20,
        exp_gate=("EXP-EVENT-01", "EXP-EVENT-02"),
        alpha_hypothesis="Kalshi systematically lags repricing after discrete game events (a capturable edge window).",
        notes="Borrows λ from T4-PROJ posterior; uses T1 prior until first T4-PROJ posterior exists.",
    ),
    ExecutionBand.T4_LINEUP: T4SubBandSpec(
        band=ExecutionBand.T4_LINEUP,
        information_class="Live lineup / rotation change → revised minutes projection",
        provisional_kelly=0.05,
        kelly_basis="PROVISIONAL maximum (ADR-0029): below T4-PROJ (cascading risk, harder σ_λ). EXP-LINEUP-01.",
        noise_buffer=NOISE_BUFFER_T4_LINEUP,
        max_concurrent_exposure_pct_t4=0.15,
        exp_gate=("EXP-LINEUP-01",),
        alpha_hypothesis="Kalshi reprices slowly after substitution events; minutes-dependent markets misprice.",
        notes="Per-event exposure cap (≤15% T4 budget per lineup event); T4-CORR discounts correlated players.",
    ),
    ExecutionBand.T4_FLOW: T4SubBandSpec(
        band=ExecutionBand.T4_FLOW,
        information_class="Accumulated game-state / context pattern (foul trouble, pace, blowout)",
        provisional_kelly=0.08,
        kelly_basis="PROVISIONAL 0.08–0.12 by phase/context. Variance-scaling incl. context-multiplier variance. EXP-FLOW-01/02.",
        noise_buffer=NOISE_BUFFER_T4_FLOW,
        max_concurrent_exposure_pct_t4=0.40,
        exp_gate=("EXP-FLOW-01", "EXP-FLOW-02"),
        alpha_hypothesis="Sustained context shifts (e.g. blowout, foul trouble) move true λ before the market reprices.",
        notes="Primary carrier of blowout-consequence betting on individual player markets (FLOW-BLOWOUT tree).",
    ),
    ExecutionBand.T4_SENTIMENT: T4SubBandSpec(
        band=ExecutionBand.T4_SENTIMENT,
        information_class="Market price drift (no game event) → informed-vs-noise classification",
        provisional_kelly=0.05,
        kelly_basis="PROVISIONAL. Lowest-confidence signal (depends on drift classification). EXP-SENT-01.",
        noise_buffer=NOISE_BUFFER_T4_SENTIMENT,
        max_concurrent_exposure_pct_t4=0.15,
        exp_gate=("EXP-SENT-01",),
        alpha_hypothesis="The system can classify price drift as informed vs noise better than chance.",
        notes="Re-evaluated every 30–120s of sustained drift via the Layer-2 price cache.",
    ),
    ExecutionBand.T4_PROJ: T4SubBandSpec(
        band=ExecutionBand.T4_PROJ,
        information_class="Accumulated in-game stats → full Poisson survival posterior on T1 prior (richest signal)",
        provisional_kelly=0.167,
        kelly_basis=(
            "DYNAMIC by game phase (ADR-0029): EARLY 0.010 / MID 0.032–0.078 / LATE 0.078–0.167. "
            "NEAR-CERTAIN held ≤0.167 — inverse-variance formula diverges (k=0.526 @46min); 0.25 is a "
            "HARD GOVERNANCE CEILING, not a derived value. Re-derive from arithmetic-survival model; "
            "EXP-PROJ-01 must confirm post-calibration tail reliability before any NEAR-CERTAIN size > MID/LATE."
        ),
        noise_buffer=NOISE_BUFFER_T4_PROJ,
        max_concurrent_exposure_pct_t4=0.60,
        exp_gate=("EXP-PROJ-01",),
        alpha_hypothesis="In-game stats let the posterior beat the market's implied λ in Q3/Q4 (approaching T1 evidence quality).",
        notes="Supersedes monolithic T4 Kelly=0.20 (ADR-0010). Primary T4 capital home. Model documented overconfident in tails.",
    ),
    ExecutionBand.T4_ARITH: T4SubBandSpec(
        band=ExecutionBand.T4_ARITH,
        information_class="Threshold-approaching arithmetic near-certainty (pts needed vs time/pace), pre-T5",
        provisional_kelly=0.167,
        kelly_basis=(
            "ADR-0029 placeholder is 0.22 but HELD NON-OPERATIONAL at the T4-PROJ LATE ceiling (0.167) "
            "until EXP-ARITH-01 confirms p_arith tail reliability — same near-certain regime where the "
            "model is documented overconfident. Must NOT be read as an approved size."
        ),
        noise_buffer=NOISE_BUFFER_T4_ARITH,
        max_concurrent_exposure_pct_t4=0.30,
        exp_gate=("EXP-ARITH-01",),
        alpha_hypothesis="When a stat is within a few units of threshold with ample time, survival is near-certain and mispriced.",
        notes="Routing gated by T4_ARITH_CONFIDENCE_GATE (EXP: ~0.70–0.80) and ARITH_ENTRY_WINDOW (EXP: ~2–4 units).",
    ),
    ExecutionBand.T4_BOUNDARY: T4SubBandSpec(
        band=ExecutionBand.T4_BOUNDARY,
        information_class="Quarter / halftime structural reset → re-evaluate all open positions + new entries",
        provisional_kelly=None,
        kelly_basis="No independent Kelly. New entries inherit T4-PROJ; exits inherit T4-EXIT.",
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,  # inherits T4-PROJ cap; not independent capital
        exp_gate=(),
        alpha_hypothesis="Structural breaks (quarter/half) are systematic re-pricing moments worth a forced re-evaluation.",
        notes="Structural overlay, not an independent capital sub-band.",
    ),
    ExecutionBand.T4_CORR: T4SubBandSpec(
        band=ExecutionBand.T4_CORR,
        information_class="Cross-market correlation across simultaneously-firing sub-bands (portfolio overlay)",
        provisional_kelly=None,
        kelly_basis="Overlay — modifies other sub-bands' sizing. Downward-only invariant; convergence premium for "
                    "N mechanistically-independent same-direction signals (EXP-derived ~0.10–0.25 per signal).",
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,  # overlay; no own position
        exp_gate=("EXP-CORR-01",),
        alpha_hypothesis="Independent signals converging on the same direction are confirmatory, not redundant; "
                         "correlated exposure must be discounted downward only.",
        notes="DOWNWARD-ONLY invariant: T4-CORR may only reduce, never increase, aggregate correlated exposure.",
    ),
    ExecutionBand.T4_EXIT: T4SubBandSpec(
        band=ExecutionBand.T4_EXIT,
        information_class="Continuous monitoring of open T4 positions → priority EXIT signals",
        provisional_kelly=None,
        kelly_basis="Manages existing positions; no new sizing.",
        noise_buffer=None,  # uses each position's own sub-band buffer
        max_concurrent_exposure_pct_t4=None,
        exp_gate=(),
        alpha_hypothesis="Edge decays intra-game; active exit on edge reversal / noise-buffer breach beats hold-to-resolution.",
        notes="EXIT signals bypass the standard queue (≤5s, GG-038). Uses each position's sub-band noise buffer.",
    ),
}


def get_t4_subband_spec(band: ExecutionBand) -> T4SubBandSpec:
    """Return the Tier B governance spec for a T4 sub-band. Raises KeyError otherwise."""
    return T4_SUBBAND_REGISTRY[band]


def validate_t4_subbands() -> list[str]:
    """
    Structural validation of the T4 sub-band registry. Returns violation messages.

    Enforces ADR-0029 Tier B invariants:
      - registry roster matches the T4_SUBBANDS tuple exactly,
      - every sub-band has a BandConfig and is BLOCKED + requires_realtime (Phase 8),
      - no sub-band is ACTIVE (would require an activation ADR not yet written).
    Empty list = clean.
    """
    violations: list[str] = []
    if set(T4_SUBBAND_REGISTRY) != set(T4_SUBBANDS):
        violations.append(
            "T4_SUBBAND_REGISTRY roster does not match T4_SUBBANDS tuple "
            f"(registry-only={set(T4_SUBBAND_REGISTRY) - set(T4_SUBBANDS)}, "
            f"tuple-only={set(T4_SUBBANDS) - set(T4_SUBBAND_REGISTRY)})."
        )
    for band, spec in T4_SUBBAND_REGISTRY.items():
        if spec.status != "BLOCKED":
            violations.append(
                f"{band.value}: status={spec.status!r}; T4 sub-bands must be BLOCKED until a "
                f"Phase 8 Activation Gate / activation ADR clears them (ADR-0029 Tier B)."
            )
        cfg = BAND_CONFIGS.get(band)
        if cfg is None:
            violations.append(f"{band.value}: missing BandConfig entry.")
        elif not cfg.requires_realtime:
            violations.append(
                f"{band.value}: BandConfig.requires_realtime=False; all T4 sub-bands are Phase 8+."
            )
    return violations


# ---------------------------------------------------------------------------
# MLB-native T4 sub-band governance registry — ADR-0039 (T-219)
# ---------------------------------------------------------------------------
#
# GOVERNANCE: Deliberately SEPARATE from T4_SUBBAND_REGISTRY/T4_SUBBANDS above, not merged
# into them. NBA's validate_t4_subbands() hard-asserts every registry entry is status=
# "BLOCKED" (ADR-0029 Tier B invariant). T4M-PROJ genuinely is NOT blocked — it is the
# existing flat model in run_t4_mlb_live.py, already live and trading paper capital under
# ADR-0023. Registering it "BLOCKED" here would be false; adding it to the NBA registry
# would either violate that registry's own invariant or require weakening it (a superseding
# ADR this session does not have). So MLB gets its own registry with its own validator that
# encodes the T4M-PROJ exception explicitly, rather than silently bending NBA's Tier A rule.
#
# T4M-ARITH and T4M-FLOW ARE net-new and DO follow the standard BLOCKED pattern — same
# _assert_sub_band_blocked() guard, same Phase 8 Activation Gate + EXP + APR requirement
# as every NBA sub-band, per ADR-0039's DS Sign-Off (code authorization != capital
# authorization).
#
# Only T4M-PROJ, T4M-ARITH, and T4M-FLOW exist here. The rest of ADR-0039's Tier B roster
# (T4M-BOUNDARY, T4M-EVENT, T4M-LINEUP, T4M-PITCHER, T4M-STAGED, T4M-CORR, T4M-EXIT) is
# scoped in the ADR but explicitly NOT authorized for code — do not add entries for them
# without a new sign-off.
# ---------------------------------------------------------------------------

T4_MLB_SUBBAND_REGISTRY: dict[ExecutionBand, T4SubBandSpec] = {
    ExecutionBand.T4M_PROJ: T4SubBandSpec(
        band=ExecutionBand.T4M_PROJ,
        information_class="Live Binomial survival posterior on pregame ba_l10 prior (flat model)",
        provisional_kelly=0.10,
        kelly_basis=(
            "Inherits KELLY_T4 from run_t4_mlb_live.py. NOT a Tier B placeholder — already "
            "approved and operating under ADR-0023 paper trading. This registry entry is a "
            "relabeling/traceability addition (ADR-0039, T-219); it changes no live behavior."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,  # governed by T4_BAND_WEIGHT budget check in run_t4_mlb_live.py
        exp_gate=(),  # already live; no activation gate pending
        alpha_hypothesis=(
            "Market is slow to reprice live MLB batter-hit props after each at-bat; the "
            "Binomial-updated posterior beats the current MIP + vig."
        ),
        status="ACTIVE",  # Documented, deliberate exception — see module governance note above.
        notes=(
            "Implemented in run_t4_mlb_live.py::p_hits_gte_threshold / _run_cycle. "
            "No new work required to stand this sub-band up (ADR-0039 Tier B roster)."
        ),
    ),
    ExecutionBand.T4M_ARITH: T4SubBandSpec(
        band=ExecutionBand.T4M_ARITH,
        information_class="Threshold-approaching Binomial near-certainty (h needed vs ab_remaining), pre-boundary",
        provisional_kelly=0.10,
        kelly_basis=(
            "PROVISIONAL & NON-OPERATIONAL. Held at T4M-PROJ's existing ceiling (KELLY_T4=0.10) "
            "until EXP-ARITH-MLB-01 confirms p_arith tail reliability. Do NOT raise without EXP."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=0.30,
        exp_gate=("EXP-ARITH-MLB-01",),
        alpha_hypothesis=(
            "The existing flat model already has degenerate hard boundaries "
            "(h_so_far >= threshold -> p_t4=1.0; h_needed > ab_remaining -> p_t4=0.0). This "
            "sub-band formalizes the near-certain band between those boundaries, where Binomial "
            "variance has contracted enough that a distinct (likely higher) Kelly fraction is "
            "justified."
        ),
        status="BLOCKED",
        notes=(
            "Reuses p_hits_gte_threshold/_binomial_pmf/_compute_ab_remaining from "
            "run_t4_mlb_live.py (t4_mlb_execution_engine.T4MlbArithEvaluator). Routing gated by "
            "an ARITH entry window + confidence gate, both EXP-required."
        ),
    ),
    ExecutionBand.T4M_FLOW: T4SubBandSpec(
        band=ExecutionBand.T4M_FLOW,
        information_class="Accumulated game-state / context pattern (blowout) on MLB batter markets",
        provisional_kelly=0.08,
        kelly_basis=(
            "PROVISIONAL: borrows NBA T4-FLOW's starting order of magnitude — no MLB-specific "
            "precedent exists. EXP-FLOW-MLB-01 required before this value is operative."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=0.40,
        exp_gate=("EXP-FLOW-MLB-01",),
        alpha_hypothesis=(
            "Sustained run-differential blowouts shift true batter outcome probability "
            "(garbage-time at-bats vs. tiring relief, or leading-team batters pulled early) "
            "before the market reprices."
        ),
        status="BLOCKED",
        notes=(
            "FLOW-BLOWOUT tree (t4_mlb_execution_engine.T4MlbFlowEvaluator). Requires score_diff "
            "as an evaluator input; live ESPN score extraction is NOT wired as part of T-219 — "
            "the evaluator is dependency-injection-testable only until that follow-up lands."
        ),
    ),
}


T4_MLB_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4M_PROJ,
    ExecutionBand.T4M_ARITH,
    ExecutionBand.T4M_FLOW,
)


def get_t4_mlb_subband_spec(band: ExecutionBand) -> T4SubBandSpec:
    """Return the Tier B governance spec for an MLB T4 sub-band. Raises KeyError otherwise."""
    return T4_MLB_SUBBAND_REGISTRY[band]


def validate_t4_mlb_subbands() -> list[str]:
    """
    Structural validation of the MLB T4 sub-band registry. Returns violation messages.

    Unlike validate_t4_subbands() (NBA), this does NOT require every entry to be BLOCKED:
    T4M-PROJ is a documented ACTIVE exception (relabeling of the already-live flat model).
    T4M-ARITH and T4M-FLOW must be BLOCKED, same invariant as every NBA sub-band. Drift in
    either direction — T4M-PROJ ever going non-ACTIVE, or ARITH/FLOW ever going non-BLOCKED
    without an activation ADR — is flagged. Empty list = clean.
    """
    violations: list[str] = []
    if set(T4_MLB_SUBBAND_REGISTRY) != set(T4_MLB_SUBBANDS):
        violations.append(
            "T4_MLB_SUBBAND_REGISTRY roster does not match T4_MLB_SUBBANDS tuple "
            f"(registry-only={set(T4_MLB_SUBBAND_REGISTRY) - set(T4_MLB_SUBBANDS)}, "
            f"tuple-only={set(T4_MLB_SUBBANDS) - set(T4_MLB_SUBBAND_REGISTRY)})."
        )
    for band, spec in T4_MLB_SUBBAND_REGISTRY.items():
        expected_status = "ACTIVE" if band is ExecutionBand.T4M_PROJ else "BLOCKED"
        if spec.status != expected_status:
            violations.append(
                f"{band.value}: status={spec.status!r}, expected {expected_status!r}. "
                f"T4M-PROJ is the sole documented ACTIVE exception (ADR-0039); all other MLB "
                f"T4 sub-bands must stay BLOCKED until their own Phase 8 Activation Gate clears."
            )
        cfg = BAND_CONFIGS.get(band)
        if cfg is None:
            violations.append(f"{band.value}: missing BandConfig entry.")
    return violations


# ---------------------------------------------------------------------------
# NFL-native T4 sub-band governance registry — ADR-0062 (T-522)
# ---------------------------------------------------------------------------
#
# GOVERNANCE: Deliberately SEPARATE from T4_SUBBAND_REGISTRY (NBA) and
# T4_MLB_SUBBAND_REGISTRY (MLB), mirroring MLB's own separation rationale. Unlike MLB,
# NFL has no live model and no ACTIVE exception at this step — every entry is BLOCKED,
# same invariant as NBA's registry, using MLB's structure as a superset template so a
# future ACTIVE promotion (if one ever occurs) needs no structural rework.
#
# 17.1 scaffolding only (T-522, no behavior change): ONLY T4NFL-ARITH and T4NFL-FLOW
# exist here. BOUNDARY is scoped in ADR-0062 §4 but explicitly NOT authorized for code —
# §4 calls it "propose, scoped only, not authorized to build" and this session applied the
# conservative reading over §6's cell-count projection (GG-246). EVENT is excluded pending
# C1 ingestion verification (ADR-0062 §7). Do not add entries for BOUNDARY/EVENT without a
# new sign-off.
# ---------------------------------------------------------------------------

T4_NFL_SUBBAND_REGISTRY: dict[ExecutionBand, T4SubBandSpec] = {
    ExecutionBand.T4NFL_ARITH: T4SubBandSpec(
        band=ExecutionBand.T4NFL_ARITH,
        information_class="Threshold-approaching arithmetic near-certainty (yards/points needed vs. clock/downs), pre-boundary",
        provisional_kelly=0.0,
        kelly_basis=(
            "NO VALUE — 17.1 scaffolding only (T-522). No NFL-specific model, EXP, or precedent "
            "exists yet. Held at 0.0 pending EXP-ARITH-NFL-01; do NOT set nonzero without an EXP."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,
        exp_gate=("EXP-ARITH-NFL-01",),
        alpha_hypothesis=(
            "When a stat is within a few units of a threshold with limited clock/downs remaining, "
            "survival is near-certain and the market is slow to reprice."
        ),
        status="BLOCKED",
        notes=(
            "Registry + band scaffolding only (T-522, ADR-0062). No evaluator exists. Nothing wired, "
            "nothing promoted."
        ),
    ),
    ExecutionBand.T4NFL_FLOW: T4SubBandSpec(
        band=ExecutionBand.T4NFL_FLOW,
        information_class="Accumulated game-state / context pattern (incl. blowout) on NFL markets",
        provisional_kelly=0.0,
        kelly_basis=(
            "NO VALUE — 17.1 scaffolding only (T-522). No NFL-specific model, EXP, or precedent "
            "exists yet. Held at 0.0 pending EXP-FLOW-NFL-01; do NOT set nonzero without an EXP."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,
        exp_gate=("EXP-FLOW-NFL-01",),
        alpha_hypothesis=(
            "Sustained game-state shifts (e.g. blowout) move true outcome probability before the "
            "market reprices."
        ),
        status="BLOCKED",
        notes=(
            "Blowout is a MODE within this band, not a separate ExecutionBand member (mirrors "
            "MLB's T4M_FLOW; GG-246 applied the same conservative test to ADR-0062 §7's open "
            "T4NFL-FLOW-BLOWOUT question). Registry + band scaffolding only. No evaluator exists."
        ),
    ),
}


T4_NFL_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4NFL_ARITH,
    ExecutionBand.T4NFL_FLOW,
)


def get_t4_nfl_subband_spec(band: ExecutionBand) -> T4SubBandSpec:
    """Return the Tier B governance spec for an NFL T4 sub-band. Raises KeyError otherwise."""
    return T4_NFL_SUBBAND_REGISTRY[band]


def validate_t4_nfl_subbands() -> list[str]:
    """
    Structural validation of the NFL T4 sub-band registry. Returns violation messages.

    Unlike validate_t4_mlb_subbands(), there is no ACTIVE exception here — every entry
    must be BLOCKED (no NFL model exists yet). Empty list = clean.
    """
    violations: list[str] = []
    if set(T4_NFL_SUBBAND_REGISTRY) != set(T4_NFL_SUBBANDS):
        violations.append(
            "T4_NFL_SUBBAND_REGISTRY roster does not match T4_NFL_SUBBANDS tuple "
            f"(registry-only={set(T4_NFL_SUBBAND_REGISTRY) - set(T4_NFL_SUBBANDS)}, "
            f"tuple-only={set(T4_NFL_SUBBANDS) - set(T4_NFL_SUBBAND_REGISTRY)})."
        )
    for band, spec in T4_NFL_SUBBAND_REGISTRY.items():
        if spec.status != "BLOCKED":
            violations.append(
                f"{band.value}: status={spec.status!r}, expected 'BLOCKED'. No NFL T4 sub-band "
                f"may be ACTIVE without an activation ADR."
            )
        cfg = BAND_CONFIGS.get(band)
        if cfg is None:
            violations.append(f"{band.value}: missing BandConfig entry.")
    return violations


# ---------------------------------------------------------------------------
# NHL-native T4 sub-band governance registry — ADR-0062 (T-522)
# ---------------------------------------------------------------------------
#
# GOVERNANCE: Same rationale as T4_NFL_SUBBAND_REGISTRY above — separate parallel
# registry, no ACTIVE exception, ARITH/FLOW only (BOUNDARY/EVENT excluded, GG-246).
# ---------------------------------------------------------------------------

T4_NHL_SUBBAND_REGISTRY: dict[ExecutionBand, T4SubBandSpec] = {
    ExecutionBand.T4NHL_ARITH: T4SubBandSpec(
        band=ExecutionBand.T4NHL_ARITH,
        information_class="Threshold-approaching arithmetic near-certainty (goals needed vs. clock), pre-boundary",
        provisional_kelly=0.0,
        kelly_basis=(
            "NO VALUE — 17.1 scaffolding only (T-522). No NHL-specific model, EXP, or precedent "
            "exists yet. Held at 0.0 pending EXP-ARITH-NHL-01; do NOT set nonzero without an EXP."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,
        exp_gate=("EXP-ARITH-NHL-01",),
        alpha_hypothesis=(
            "When a stat is within a few units of a threshold with limited clock remaining, "
            "survival is near-certain and the market is slow to reprice."
        ),
        status="BLOCKED",
        notes=(
            "Registry + band scaffolding only (T-522, ADR-0062). No evaluator exists. Nothing wired, "
            "nothing promoted."
        ),
    ),
    ExecutionBand.T4NHL_FLOW: T4SubBandSpec(
        band=ExecutionBand.T4NHL_FLOW,
        information_class="Accumulated game-state / context pattern (incl. blowout) on NHL markets",
        provisional_kelly=0.0,
        kelly_basis=(
            "NO VALUE — 17.1 scaffolding only (T-522). No NHL-specific model, EXP, or precedent "
            "exists yet. Held at 0.0 pending EXP-FLOW-NHL-01; do NOT set nonzero without an EXP."
        ),
        noise_buffer=None,
        max_concurrent_exposure_pct_t4=None,
        exp_gate=("EXP-FLOW-NHL-01",),
        alpha_hypothesis=(
            "Sustained game-state shifts (e.g. blowout) move true outcome probability before the "
            "market reprices."
        ),
        status="BLOCKED",
        notes=(
            "Blowout is a MODE within this band, not a separate ExecutionBand member (mirrors "
            "MLB's T4M_FLOW; GG-246 applied the same conservative test). Registry + band "
            "scaffolding only. No evaluator exists."
        ),
    ),
}


T4_NHL_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4NHL_ARITH,
    ExecutionBand.T4NHL_FLOW,
)


def get_t4_nhl_subband_spec(band: ExecutionBand) -> T4SubBandSpec:
    """Return the Tier B governance spec for an NHL T4 sub-band. Raises KeyError otherwise."""
    return T4_NHL_SUBBAND_REGISTRY[band]


def validate_t4_nhl_subbands() -> list[str]:
    """
    Structural validation of the NHL T4 sub-band registry. Returns violation messages.

    Unlike validate_t4_mlb_subbands(), there is no ACTIVE exception here — every entry
    must be BLOCKED (no NHL model exists yet). Empty list = clean.
    """
    violations: list[str] = []
    if set(T4_NHL_SUBBAND_REGISTRY) != set(T4_NHL_SUBBANDS):
        violations.append(
            "T4_NHL_SUBBAND_REGISTRY roster does not match T4_NHL_SUBBANDS tuple "
            f"(registry-only={set(T4_NHL_SUBBAND_REGISTRY) - set(T4_NHL_SUBBANDS)}, "
            f"tuple-only={set(T4_NHL_SUBBANDS) - set(T4_NHL_SUBBAND_REGISTRY)})."
        )
    for band, spec in T4_NHL_SUBBAND_REGISTRY.items():
        if spec.status != "BLOCKED":
            violations.append(
                f"{band.value}: status={spec.status!r}, expected 'BLOCKED'. No NHL T4 sub-band "
                f"may be ACTIVE without an activation ADR."
            )
        cfg = BAND_CONFIGS.get(band)
        if cfg is None:
            violations.append(f"{band.value}: missing BandConfig entry.")
    return violations


# ---------------------------------------------------------------------------
# Strategy band specification — mandatory structural interface for all strategies
# ---------------------------------------------------------------------------
#
# GOVERNANCE: Every strategy (A–K) must have a StrategyBandSpec registered in
# BAND_REGISTRY. Strategies not registered cannot be activated. band_status must
# be truthful — ACTIVE requires EXP/ADR evidence. Promotion from SKELETON → ACTIVE
# requires a DECISION_LOG entry + DS sign-off.
#
# See: 02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md for full protocol.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrategyBandSpec:
    """
    Structural band assignment declaration for a single quantitative strategy.

    Every strategy (A–K) must have a StrategyBandSpec registered in BAND_REGISTRY
    before it can be activated. This is the code-level enforcement of the band
    assignment protocol defined in BAND_ASSIGNMENT_FRAMEWORK.md.

    Fields
    ------
    strategy_id : str
        Single letter (A–K).
    strategy_name : str
        Human-readable name.
    signal_type : str
        "model_edge" | "arb_lock" | "arb_spread" | "arb_route" |
        "momentum" | "execution_scalp" | "sizing" | "risk_envelope"
    native_bands : tuple[ExecutionBand, ...]
        All bands where this strategy has any involvement.
    detection_band : ExecutionBand | None
        Band where expensive signal computation occurs. None for sizing/envelope.
    execution_band : ExecutionBand | None
        Band governing final execution timing (fastest achievable). None for sizing/envelope.
    band_status : str
        "ACTIVE"   — validated by EXP/ADR; may execute paper/live bets.
        "SKELETON" — code exists; signals are logged but NOT executed.
        "BLOCKED"  — awaiting gate (ADR, approval, infrastructure, data source).
    evidence_basis : str
        EXP/ADR/APR reference for ACTIVE; blocking reason for SKELETON/BLOCKED.
    activation_gate : str
        The gate or condition required for promotion to ACTIVE.
    fallback_chain : str
        Defined degradation path when execution band fails (e.g., "T3→T1→PASS").
        Fallback must always be more conservative, never more aggressive.
    compute_budget_ms : int
        Expected compute time at detection_band. Must fit BandConfig.max_compute_ms.
    phase_active : str
        Earliest phase at which this strategy can be activated.
    notes : str
        Governance notes (blockers, cross-strategy dependencies, edge cases).
    """
    strategy_id: str
    strategy_name: str
    signal_type: str
    native_bands: tuple[ExecutionBand, ...]
    detection_band: Optional[ExecutionBand]
    execution_band: Optional[ExecutionBand]
    band_status: str          # "ACTIVE" | "SKELETON" | "BLOCKED"
    evidence_basis: str
    activation_gate: str
    fallback_chain: str
    compute_budget_ms: int
    phase_active: str
    notes: str


# ---------------------------------------------------------------------------
# Venue band constraints — per-venue, per-band feasibility ("technical braces")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VenueBandConstraint:
    """
    Per-venue feasibility constraint for a single execution band.

    Defines whether a venue can achieve a band's SLA given its API latency
    and operational capabilities. Used by BandRegistry.validate_venues() and
    by arb routing to select the fastest achievable venue per band.

    Fields
    ------
    venue_id : str
        Venue identifier (matches VENUE_REGISTRY.md, e.g. "V-001").
    venue_name : str
        Human-readable venue name.
    band : ExecutionBand
        Which band this constraint applies to.
    api_latency_ms_p90 : int
        P90 (90th-percentile) round-trip API latency estimate. P90 not mean —
        SLA compliance requires worst-case planning.
    max_api_calls_per_decision : int
        Hard limit on API calls allowed per decision at this band.
        T3=1 (latency consumes most of the 500ms budget).
        T4=0 (all data pre-staged at T3; zero live calls permitted).
    supports_simultaneous_legs : bool
        True if the venue API can submit both legs of a complement lock in
        a single atomic request. False = sequential (fill-risk between legs).
    rate_limit_per_min : int
        Venue API rate limit (calls/min). Shared across all strategies — contention
        occurs when multiple strategies scan simultaneously.
    min_market_depth_usd : float
        Minimum acceptable market depth to proceed at this band. Below this
        threshold, skip the market — thin depth compresses realized edge.
    phase_availability : str
        Phase at which this venue/band combination becomes available.
    constraint_notes : str
        Human-readable notes for borderline or blocked combinations.
    """
    venue_id: str
    venue_name: str
    band: ExecutionBand
    api_latency_ms_p90: int
    max_api_calls_per_decision: int
    supports_simultaneous_legs: bool
    rate_limit_per_min: int
    min_market_depth_usd: float
    phase_availability: str
    constraint_notes: str

    @property
    def sla_headroom_ms(self) -> int:
        """Remaining SLA after subtracting P90 API latency. Negative = band not achievable."""
        band_sla_ms = BAND_CONFIGS[self.band].execution_sla_s * 1000
        return band_sla_ms - self.api_latency_ms_p90

    @property
    def is_feasible(self) -> bool:
        """True when API latency leaves non-negative headroom within the band SLA."""
        return self.sla_headroom_ms > 0


# ---------------------------------------------------------------------------
# Band Registry — centralized map of all strategy band assignments
# ---------------------------------------------------------------------------

_VALID_EVIDENCE_PREFIXES = ("EXP-", "ADR-", "APR-")
_VALID_STATUSES = frozenset({"ACTIVE", "SKELETON", "BLOCKED"})


class BandRegistry:
    """
    Centralized registry of all strategy StrategyBandSpecs.

    Single source of truth for strategy-to-band assignments. Validated at
    bot startup via validate(). All 11 strategies (A–K) plus sizing (G) and
    risk envelope (H) must be registered.

    Usage::

        spec = BAND_REGISTRY.get("A")
        if spec.band_status != "ACTIVE":
            raise RuntimeError("Strategy A not active")

        violations = BAND_REGISTRY.validate()
        if violations:
            raise RuntimeError("\\n".join(violations))
    """

    def __init__(self) -> None:
        self._specs: dict[str, StrategyBandSpec] = {}

    def register(self, spec: StrategyBandSpec) -> None:
        """Register a StrategyBandSpec. Overwrites existing entry for strategy_id."""
        if spec.band_status not in _VALID_STATUSES:
            raise ValueError(
                f"Strategy {spec.strategy_id}: invalid band_status '{spec.band_status}'. "
                f"Must be one of {_VALID_STATUSES}."
            )
        self._specs[spec.strategy_id] = spec

    def get(self, strategy_id: str) -> StrategyBandSpec:
        """Return the StrategyBandSpec for a strategy. Raises KeyError if not registered."""
        if strategy_id not in self._specs:
            raise KeyError(
                f"Strategy '{strategy_id}' not found in BandRegistry. "
                f"Every strategy must be registered before activation."
            )
        return self._specs[strategy_id]

    def all_specs(self) -> list[StrategyBandSpec]:
        """Return all registered specs."""
        return list(self._specs.values())

    def active_specs(self) -> list[StrategyBandSpec]:
        """Return only ACTIVE strategies (may execute paper/live bets)."""
        return [s for s in self._specs.values() if s.band_status == "ACTIVE"]

    def skeleton_specs(self) -> list[StrategyBandSpec]:
        """Return SKELETON strategies (signals logged; bets not executed)."""
        return [s for s in self._specs.values() if s.band_status == "SKELETON"]

    def validate(self) -> list[str]:
        """
        Structural validation. Returns list of violation messages.

        Called at bot startup — empty list means clean state.
        Violations must be resolved before live capital deployment.

        Checks:
        - ACTIVE strategies must reference a valid evidence artifact
        - ACTIVE strategies must not require real-time infra (Phase 8+)
        - All registered bands must exist in BAND_CONFIGS
        """
        violations: list[str] = []
        for spec in self._specs.values():
            if spec.band_status == "ACTIVE":
                has_evidence = any(
                    prefix in spec.evidence_basis
                    for prefix in _VALID_EVIDENCE_PREFIXES
                )
                if not has_evidence:
                    violations.append(
                        f"Strategy {spec.strategy_id} is ACTIVE but evidence_basis "
                        f"'{spec.evidence_basis}' does not reference an EXP/ADR/APR. "
                        f"ACTIVE status requires a validated artifact."
                    )
                if spec.execution_band is not None:
                    band_cfg = BAND_CONFIGS.get(spec.execution_band)
                    if band_cfg and band_cfg.requires_realtime:
                        violations.append(
                            f"Strategy {spec.strategy_id} has execution_band="
                            f"{spec.execution_band.value} which requires_realtime=True "
                            f"(Phase 8+). Cannot be ACTIVE before Phase 8 infrastructure."
                        )
            for band in spec.native_bands:
                if band not in BAND_CONFIGS:
                    violations.append(
                        f"Strategy {spec.strategy_id} references unknown band {band}."
                    )
        return violations


# ---------------------------------------------------------------------------
# Canonical strategy band registry — all 11 strategies (A–K) + G (sizing) + H (risk)
# ---------------------------------------------------------------------------

BAND_REGISTRY = BandRegistry()

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="A",
    strategy_name="ML+EV Forecast (Primary)",
    signal_type="model_edge",
    native_bands=(ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T3_PRE_TIP,
    band_status="ACTIVE",
    evidence_basis="EXP-010 (871 bets; +$0.0958/bet; T1 validated; LR+Platt ECE 0.0342)",
    activation_gate="G6 (ADR-0005) for live capital; paper currently active",
    fallback_chain="T3→T2→T1→PASS",
    compute_budget_ms=30_000,
    phase_active="Phase 6",
    notes="T2/T3 are SKELETON overlays on T1-derived signals. T1 is the primary revenue band. T3 execution requires single-API-call only (Kalshi latency constraint).",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="B",
    strategy_name="Data Aggregation Enhancement",
    signal_type="model_edge",
    native_bands=(ExecutionBand.T1_MULTI_DAY,),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T1_MULTI_DAY,
    band_status="SKELETON",
    evidence_basis="HYP-005 falsified at N<800; requires N>2000 statistical power (EXP pending)",
    activation_gate="Dedicated EXP validating B/D feature combinations at N>2000",
    fallback_chain="T1→PASS",
    compute_budget_ms=30_000,
    phase_active="Phase 7",
    notes="Continuous improvement booster to Strategy A. Second Phase 7 priority (after E). Pipeline runs; outputs logged but not used for sizing.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="C",
    strategy_name="Complement Lock Arbitrage",
    signal_type="arb_lock",
    native_bands=(ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP, ExecutionBand.T4_IN_PLAY),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T3_PRE_TIP,
    band_status="BLOCKED",
    evidence_basis="BLOCKED: APR-0010 pending DS decision; arb/ folder is reference-only (RO-001)",
    activation_gate="APR-0010 (DS sign-off) + write-capable C5 key (ACC-0002 upgrade) + T-077",
    fallback_chain="T3_fail→REQUEUE(next T3 scan 15min); T4_fail→T3_execute; no T1 fallback for lock",
    compute_budget_ms=50_000,
    phase_active="Phase 7",
    notes="No T1 fallback — complement lock windows do not persist at T1 pricing. T4 requires pre-staged order pairs. Kalshi simultaneous_legs=False means sequential fill risk.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="D",
    strategy_name="Statistical Arbitrage (OU Mean Reversion)",
    signal_type="arb_spread",
    native_bands=(ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T2_SAME_DAY,
    band_status="BLOCKED",
    evidence_basis="BLOCKED: DS-02 price history required (>=2 seasons per pair); new ADR required",
    activation_gate="DS-02 upgrade + new strategy ADR + cross-venue activation post-T-077",
    fallback_chain="T2_fail→T1_cached_OU_estimate→PASS",
    compute_budget_ms=30_000,
    phase_active="Phase 8",
    notes="T4/T5 explicitly excluded (DECISION_LOG 2026-05-29). OU reversion horizon is hours; in-play window is seconds. Binary settlement creates OU edge cases not present in equity stat arb.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="E",
    strategy_name="Line Shopping (Best Price Routing)",
    signal_type="arb_route",
    native_bands=(ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP, ExecutionBand.T4_IN_PLAY),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T3_PRE_TIP,
    band_status="SKELETON",
    evidence_basis="EXP-014 (T1 routing: +7.8% max EV vs. single-venue); T3/T4 routing unvalidated",
    activation_gate="T-077 Polymarket API provisioning (KYC) + VenueRouter multi-venue expansion",
    fallback_chain="T3_live_route_fail→T1_cached_routing_table; T4_fail→T3_live_route",
    compute_budget_ms=5_000,
    phase_active="Phase 7",
    notes="First Phase 7 build priority (EXP-014 confirmed +7.8%). DFS bookmaker-fixed venues use edge=p_hat-0.50 not p_hat-mid_price. T4 routing uses pre-cached routing_table[market_id].",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="F",
    strategy_name="Correlated Parlays",
    signal_type="model_edge_joint",
    native_bands=(ExecutionBand.T1_MULTI_DAY,),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T1_MULTI_DAY,
    band_status="BLOCKED",
    evidence_basis="BLOCKED: joint probability distribution model required; no ADR exists",
    activation_gate="New ADR for joint distribution model + EXP validating joint P(X,Y) vs independent P(X)*P(Y)",
    fallback_chain="T1→PASS",
    compute_budget_ms=30_000,
    phase_active="Phase 7",
    notes="Requires joint P(X,Y) model — probabilities are not additively separable. Block until new ADR defines the joint model class.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="G",
    strategy_name="Kelly Criterion Sizing",
    signal_type="sizing",
    native_bands=(ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP, ExecutionBand.T4_IN_PLAY, ExecutionBand.T5_LATE_GAME),
    detection_band=None,
    execution_band=None,
    band_status="ACTIVE",
    evidence_basis="ADR-0004 (LR+Platt ECE 0.0342) + EXP-010 (calibration confirmed at quarter-Kelly)",
    activation_gate="G6 (ADR-0005) for live capital; paper active",
    fallback_chain="N/A — envelope applied at whichever band fires the underlying signal",
    compute_budget_ms=1,
    phase_active="Phase 6",
    notes="Sizing component only — not an independent signal strategy. Fractions by band: T1=0.25, T2=0.20, T3=0.10, T4=0.05, T5=0.15. Hard limits from ADR-0004 apply at all bands.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="H",
    strategy_name="Risk Constraints Envelope",
    signal_type="risk_envelope",
    native_bands=(ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP, ExecutionBand.T4_IN_PLAY, ExecutionBand.T5_LATE_GAME),
    detection_band=None,
    execution_band=None,
    band_status="ACTIVE",
    evidence_basis="ADR-0004 + APR-0013 ($500/bet cap; $1000/day limit; 20% drawdown kill switch tested)",
    activation_gate="Active at all phases — non-negotiable governance component",
    fallback_chain="N/A — hard limits override all bands; no fallback bypasses H",
    compute_budget_ms=1,
    phase_active="Phase 6",
    notes="Kill switch must halt all components within 60s (NFR-03). Hard limits must be revised via ADR at G6 when live bankroll is set. Kill switch 60s SLA is 12x too slow for T4/T5 (requires <5s).",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="I",
    strategy_name="Poisson / Negative Binomial Model",
    signal_type="model_edge",
    native_bands=(ExecutionBand.T1_MULTI_DAY,),
    detection_band=ExecutionBand.T1_MULTI_DAY,
    execution_band=ExecutionBand.T1_MULTI_DAY,
    band_status="SKELETON",
    evidence_basis="EXP-013 incomplete; ScoringDistributionModel blocked by LL-009 pilot-first rule",
    activation_gate="Pilot EXP confirming Poisson/NB Brier improvement over LR baseline before model build",
    fallback_chain="T1→PASS",
    compute_budget_ms=30_000,
    phase_active="Phase 7",
    notes="Third Phase 7 priority (after E, B). LL-009 rule: run pilot EXP before building ScoringDistributionModel. EXP-013 is the pilot and must complete first.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="J",
    strategy_name="Momentum Signal (Pre-Tip)",
    signal_type="momentum",
    native_bands=(ExecutionBand.T3_PRE_TIP,),
    detection_band=ExecutionBand.T3_PRE_TIP,
    execution_band=ExecutionBand.T3_PRE_TIP,
    band_status="BLOCKED",
    evidence_basis="BLOCKED: DS-02 intraday price series required for backtesting CONFIRM/FADE signal",
    activation_gate="DS-02 upgrade + EXP confirming CONFIRM/FADE win rate improvement vs T1-only",
    fallback_chain="T3_fail→T1 (momentum absent; T1 decision used without overlay)",
    compute_budget_ms=500,
    phase_active="Phase 7",
    notes="Currently embedded as sub-component of Strategy A T3 overlay (PIPE-06). Separation into standalone Strategy J pending DS-02 and dedicated validation EXP.",
))

BAND_REGISTRY.register(StrategyBandSpec(
    strategy_id="K",
    strategy_name="In-Play Scalping",
    signal_type="execution_scalp",
    native_bands=(ExecutionBand.T4_IN_PLAY, ExecutionBand.T5_LATE_GAME),
    detection_band=ExecutionBand.T4_IN_PLAY,
    execution_band=ExecutionBand.T4_IN_PLAY,
    band_status="BLOCKED",
    evidence_basis="BLOCKED: Phase 8+ — real-time C5 rebuild required; no live game data feed",
    activation_gate="Phase 8 + real-time infra ADR + DS-02 websocket upgrade + kill switch SLA <5s",
    fallback_chain="T4_fail→PASS (no T3 fallback — scalp opportunity is strictly time-bounded)",
    compute_budget_ms=50,
    phase_active="Phase 8",
    notes="Kill switch 60s SLA is 12x too slow for T4/T5 (requires <5s). Cannot activate until NFR-03 SLA is revised via ADR and tested. No fallback — scalp window is seconds. "
          "ADR-0029: T4 is now sub-banded — the strategy↔sub-band mapping is Tier B (provisional, pending). "
          "OPEN governance question: K's 'execution_scalp' identity overlaps the T4-MICRO carve-out (ADR-0030, "
          "no `model_p`); whether K is re-homed to ADR-0030 or re-scoped onto model_p sub-bands is a separate "
          "strategy-level decision. Held at the T4_IN_PLAY aggregate here pending that ruling.",
))


# ---------------------------------------------------------------------------
# Venue band constraints — canonical per-venue feasibility registry
# ---------------------------------------------------------------------------
#
# GOVERNANCE: Add a VenueBandConstraint entry for every new venue activation.
# Update api_latency_ms_p90 with empirical measurements — placeholder values
# (999) indicate TBD. T3 single-call constraint on Kalshi is ENFORCED by design,
# not just documented.
# ---------------------------------------------------------------------------

VENUE_BAND_CONSTRAINTS: list[VenueBandConstraint] = [
    # ------------------------------------------------------------------
    # V-001 Kalshi (primary venue; Phase 6 active)
    # ------------------------------------------------------------------
    VenueBandConstraint(
        venue_id="V-001", venue_name="Kalshi",
        band=ExecutionBand.T1_MULTI_DAY,
        api_latency_ms_p90=500,
        max_api_calls_per_decision=50,
        supports_simultaneous_legs=False,
        rate_limit_per_min=60,
        min_market_depth_usd=100.0,
        phase_availability="current",
        constraint_notes="T1 batch scan. Rate limit shared across all strategies — contention if A+C scan simultaneously.",
    ),
    VenueBandConstraint(
        venue_id="V-001", venue_name="Kalshi",
        band=ExecutionBand.T2_SAME_DAY,
        api_latency_ms_p90=500,
        max_api_calls_per_decision=5,
        supports_simultaneous_legs=False,
        rate_limit_per_min=60,
        min_market_depth_usd=75.0,
        phase_availability="Phase 7",
        constraint_notes="T2 refresh of top-N candidates from T1 scan only. No full re-scan at T2.",
    ),
    VenueBandConstraint(
        venue_id="V-001", venue_name="Kalshi",
        band=ExecutionBand.T3_PRE_TIP,
        api_latency_ms_p90=350,
        max_api_calls_per_decision=1,
        supports_simultaneous_legs=False,
        rate_limit_per_min=60,
        min_market_depth_usd=50.0,
        phase_availability="current",
        constraint_notes="CRITICAL: Single API call enforced. 350ms P90 latency leaves ~150ms compute margin within 500ms SLA. Any second live call violates SLA. Measure empirically and update P90.",
    ),
    VenueBandConstraint(
        venue_id="V-001", venue_name="Kalshi",
        band=ExecutionBand.T4_IN_PLAY,
        api_latency_ms_p90=350,
        max_api_calls_per_decision=0,
        supports_simultaneous_legs=False,
        rate_limit_per_min=60,
        min_market_depth_usd=25.0,
        phase_availability="Phase 8",
        constraint_notes="BLOCKED: T4 50ms SLA is impossible with 350ms P90 latency. All orders must be pre-staged at T3. Zero live API calls permitted at T4. "
                         "ADR-0029: all T4 sub-bands INHERIT this aggregate constraint (zero live execution API calls; the Layer-2 read-only price cache, GG-039, "
                         "supplies staleness-check prices off a separate polling loop). Per-sub-band VenueBandConstraint rows are Tier B and added only if a sub-band "
                         "ever needs to diverge from this aggregate (none currently do).",
    ),
    VenueBandConstraint(
        venue_id="V-001", venue_name="Kalshi",
        band=ExecutionBand.T5_LATE_GAME,
        api_latency_ms_p90=350,
        max_api_calls_per_decision=0,
        supports_simultaneous_legs=False,
        rate_limit_per_min=60,
        min_market_depth_usd=10.0,
        phase_availability="Phase 8",
        constraint_notes="BLOCKED: Same as T4. Pre-staged orders only. Phase 8+.",
    ),

    # ------------------------------------------------------------------
    # V-002 Polymarket — TBD pending T-077 KYC/provisioning
    # ------------------------------------------------------------------
    VenueBandConstraint(
        venue_id="V-002", venue_name="Polymarket",
        band=ExecutionBand.T1_MULTI_DAY,
        api_latency_ms_p90=999,
        max_api_calls_per_decision=50,
        supports_simultaneous_legs=False,
        rate_limit_per_min=60,
        min_market_depth_usd=100.0,
        phase_availability="Phase 7",
        constraint_notes="TBD: All values are placeholders. Measure empirically after T-077 API provisioning. api_latency_ms_p90=999 indicates unset.",
    ),
]

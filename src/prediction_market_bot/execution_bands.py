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

Band summary:
  T1 — Multi-day:    Full LR+Platt (78 feat); PIPE-02; Kelly 0.25
  T2 — Same-day:     Injury overlay on T1; PIPE-05; Kelly 0.20
  T3 — Pre-tip:      Momentum signal only; PIPE-06; Kelly 0.10
  T4 — In-play:      Bayesian game-state; PIPE-07 (real-time infra required)
  T5 — Late-game:    Arithmetic certainty; PIPE-08 (real-time infra required)

Governance:
  T1/T2/T3 are buildable on current cron infrastructure.
  T4/T5 require full real-time C5 rebuild (Phase 8+).
  Kelly fractions decrease at shorter horizons (lower model confidence).
  T5 is an exception — arithmetic certainty warrants higher sizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
    T4_IN_PLAY   = "T4"    # Bayesian game-state update — PIPE-07; requires real-time
    T5_LATE_GAME = "T5"    # Arithmetic certainty (pts needed/time) — PIPE-08; requires real-time


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
        kelly_fraction=0.25,                 # Quarter-Kelly (ADR-0004)
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
        kelly_fraction=0.20,                 # Slightly reduced (injury data adds uncertainty)
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
        kelly_fraction=0.10,                 # Half of T1 (signal is thinner; confirmation only)
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
        kelly_fraction=0.05,                 # Minimal (no historical calibration on live model)
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
        kelly_fraction=0.15,                 # Higher than T4 — near-certainty warrants more
        pipeline_id="PIPE-08",
        cron_schedule=None,                  # Event-driven
        requires_realtime=True,              # BLOCKED: Phase 8+
        phase_active="Phase 8",
    ),
}


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

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
        kelly_fraction=0.10,                 # ADR-0010: σ_λ=2.055 (pts_l10_mean); 2× operational premium over derived 0.049
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
        kelly_fraction=0.13,                 # ADR-0010: tentative; injury overlay uncertainty; 2× premium over derived 0.061
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
        kelly_fraction=0.07,                 # ADR-0010: tentative; momentum confirmation only; 2× premium over derived 0.032
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


# ---------------------------------------------------------------------------
# Band exit noise buffers — ADR-0018 + ADR-0019
# ---------------------------------------------------------------------------
# Derived analytically in EXP-019A: NOISE_BUFFER_BAND = max(2×σ_p, EXIT_NET_COST_BAND)
# where σ_p = |dP/dλ| × σ_λ evaluated at the band's representative firing window.
# EXP-019B analytic confirms FULL_EXIT (Kelly fraction → 0 at exit boundary).
# Empirical validation pending EXP-019B/C (≥3 game nights trajectory + spread data, G4+).
# Before activation: run EXP-019B empirical; if observed buffer deviates >20% from these
# analytic values, update via ADR amendment (T-152). See ADR-0019 for full gate structure.

NOISE_BUFFER_BAND_T1: float = 0.22053   # EXP-019A analytic; σ_λ_ingame=1.45 (Q2 midpoint, 24min elapsed)
NOISE_BUFFER_BAND_T2: float = 0.22053   # same σ_λ basis as T1
NOISE_BUFFER_BAND_T3: float = 0.22053   # same σ_λ basis as T1
NOISE_BUFFER_BAND_T4: float = 0.13905   # EXP-019A analytic; σ_λ=0.5 (Q3/Q4 firing window)
NOISE_BUFFER_BAND_T5: float = 0.13328   # EXP-019A analytic; near-deterministic (final 3 min)

# Exit guard: no exits in the final N minutes — T5 arithmetic certainty logic takes over.
EXIT_MIN_TIME_REMAINING_MIN: float = 3.0

# ADR-0019 Tier 2 activation gate.
# SESSION 43 DS override: set True for G4/G5 paper trading. Rationale: EXP-019B
# analytic validated (79.9% correct exits, 0 false exits); empirical data (T-152)
# can only be collected by running exits; T4 pool is isolated (no real capital risk).
# GG-017 Tier 2 gate remains OPEN until T-152/T-153 complete.
EXIT_MECHANICS_ACTIVE: bool = True


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
    notes="Kill switch 60s SLA is 12x too slow for T4/T5 (requires <5s). Cannot activate until NFR-03 SLA is revised via ADR and tested. No fallback — scalp window is seconds.",
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
        constraint_notes="BLOCKED: T4 50ms SLA is impossible with 350ms P90 latency. All orders must be pre-staged at T3. Zero live API calls permitted at T4.",
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

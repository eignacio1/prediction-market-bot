"""Tests for execution_bands.py — ExecutionBand enum and BandConfig."""
import pytest
from prediction_market_bot.execution_bands import (
    BandConfig,
    ExecutionBand,
    BAND_CONFIGS,
    get_band_config,
    get_active_bands,
)


class TestExecutionBandEnum:
    def test_base_aggregate_bands_defined(self):
        # Five aggregate time-horizon bands (ADR-0010). T4_IN_PLAY is now the
        # aggregate parent over the ADR-0029 T4 sub-bands.
        values = {b.value for b in ExecutionBand}
        assert {"T1", "T2", "T3", "T4", "T5"} <= values

    def test_t4_subbands_defined(self):
        # ADR-0029 (Tier A accepted; roster Tier B/provisional): 10 T4 sub-bands
        # beneath the T4_IN_PLAY aggregate. T4-MICRO was carved out to ADR-0030.
        from prediction_market_bot.execution_bands import T4_SUBBANDS
        assert len(T4_SUBBANDS) == 10
        assert {b.value for b in T4_SUBBANDS} == {
            "T4-STAGED", "T4-EVENT", "T4-LINEUP", "T4-FLOW", "T4-SENTIMENT",
            "T4-PROJ", "T4-ARITH", "T4-BOUNDARY", "T4-CORR", "T4-EXIT",
        }
        # T4-MICRO is intentionally absent (no model_p; ADR-0030 carve-out).
        assert "T4-MICRO" not in {b.value for b in ExecutionBand}
        # 5 aggregate bands + 10 NBA T4 sub-bands + 3 MLB-native T4 sub-bands
        # (T4M-PROJ/T4M-ARITH/T4M-FLOW, ADR-0039/T-219) = 18.
        assert len(list(ExecutionBand)) == 18

    def test_band_string_values(self):
        assert ExecutionBand.T1_MULTI_DAY.value == "T1"
        assert ExecutionBand.T5_LATE_GAME.value  == "T5"


class TestBandConfigs:
    def test_all_bands_have_config(self):
        for band in ExecutionBand:
            assert band in BAND_CONFIGS, f"Missing config for {band}"

    def test_get_band_config_returns_correct_type(self):
        cfg = get_band_config(ExecutionBand.T1_MULTI_DAY)
        assert isinstance(cfg, BandConfig)

    def test_t1_kelly_fraction(self):
        # ADR-0048 (2026-07-29, supersedes ADR-0040's 0.061): zeroed per GG-135
        # ruin-risk finding (MAIN's real variance alone produces ~100%/yr
        # kill-switch trip probability at any positive Kelly).
        assert get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction == 0.0

    def test_t2_kelly_zeroed_same_as_t1(self):
        # ADR-0048 (2026-07-29): the old T2 > T1 signal-layer ordering no longer
        # applies — GG-135's ruin geometry zeroed both bands identically,
        # pending edge-conditional reactivation.
        t1 = get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction
        t2 = get_band_config(ExecutionBand.T2_SAME_DAY).kelly_fraction
        assert t1 == t2 == 0.0

    def test_t3_kelly_zeroed_same_as_t2(self):
        # ADR-0048 (2026-07-29): the old T3 < T2 ordering no longer applies —
        # both zeroed identically pending edge-conditional reactivation.
        t2 = get_band_config(ExecutionBand.T2_SAME_DAY).kelly_fraction
        t3 = get_band_config(ExecutionBand.T3_PRE_TIP).kelly_fraction
        assert t2 == t3 == 0.0

    def test_t4_kelly_greater_than_t3(self):
        # ADR-0010: T4 > T3 — threshold-specific Poisson; Q4 σ_λ ≈ 0.5 (0.20 > 0.07)
        t3 = get_band_config(ExecutionBand.T3_PRE_TIP).kelly_fraction
        t4 = get_band_config(ExecutionBand.T4_IN_PLAY).kelly_fraction
        assert t4 > t3

    def test_t5_kelly_higher_than_t4(self):
        # T5 = arithmetic near-certainty → higher fraction than T4
        t4 = get_band_config(ExecutionBand.T4_IN_PLAY).kelly_fraction
        t5 = get_band_config(ExecutionBand.T5_LATE_GAME).kelly_fraction
        assert t5 > t4

    def test_compute_ms_increases_with_longer_horizon(self):
        t1 = get_band_config(ExecutionBand.T1_MULTI_DAY).max_compute_ms
        t3 = get_band_config(ExecutionBand.T3_PRE_TIP).max_compute_ms
        t5 = get_band_config(ExecutionBand.T5_LATE_GAME).max_compute_ms
        assert t1 > t3 > t5

    def test_t1_t2_t3_do_not_require_realtime(self):
        for band in [ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP]:
            assert not get_band_config(band).requires_realtime

    def test_t4_t5_require_realtime(self):
        for band in [ExecutionBand.T4_IN_PLAY, ExecutionBand.T5_LATE_GAME]:
            assert get_band_config(band).requires_realtime

    def test_t1_t2_t3_have_cron_schedule(self):
        for band in [ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP]:
            assert get_band_config(band).cron_schedule is not None

    def test_t4_t5_have_no_cron(self):
        for band in [ExecutionBand.T4_IN_PLAY, ExecutionBand.T5_LATE_GAME]:
            assert get_band_config(band).cron_schedule is None

    def test_pipeline_ids_assigned(self):
        expected = {
            ExecutionBand.T1_MULTI_DAY: "PIPE-02",
            ExecutionBand.T2_SAME_DAY:  "PIPE-05",
            ExecutionBand.T3_PRE_TIP:   "PIPE-06",
            ExecutionBand.T4_IN_PLAY:   "PIPE-07",
            ExecutionBand.T5_LATE_GAME: "PIPE-08",
        }
        for band, pipe in expected.items():
            assert get_band_config(band).pipeline_id == pipe


class TestGetActiveBands:
    def test_excludes_realtime_by_default(self):
        active = get_active_bands()
        for cfg in active:
            assert not cfg.requires_realtime

    def test_includes_t1_t2_t3_by_default(self):
        active_bands = {cfg.band for cfg in get_active_bands()}
        assert ExecutionBand.T1_MULTI_DAY in active_bands
        assert ExecutionBand.T2_SAME_DAY  in active_bands
        assert ExecutionBand.T3_PRE_TIP   in active_bands

    def test_excludes_t4_t5_by_default(self):
        active_bands = {cfg.band for cfg in get_active_bands()}
        assert ExecutionBand.T4_IN_PLAY   not in active_bands
        assert ExecutionBand.T5_LATE_GAME not in active_bands

    def test_excludes_t4_subbands_by_default(self):
        # All ADR-0029 T4 sub-bands are requires_realtime=True (Phase 8) → excluded by default.
        from prediction_market_bot.execution_bands import T4_SUBBANDS
        active_bands = {cfg.band for cfg in get_active_bands()}
        for sub in T4_SUBBANDS:
            assert sub not in active_bands

    def test_include_realtime_returns_all_bands(self):
        # 5 aggregate (T1–T5) + 10 NBA T4 sub-bands (ADR-0029) + 3 MLB-native T4
        # sub-bands (T4M-PROJ/T4M-ARITH/T4M-FLOW, ADR-0039/T-219) = 18.
        all_bands = get_active_bands(include_realtime=True)
        assert len(all_bands) == 18


class TestT4SubBandRegistry:
    """ADR-0029 Tier B governance invariants — the scaffold must keep these true."""

    def test_validate_clean(self):
        from prediction_market_bot.execution_bands import validate_t4_subbands
        assert validate_t4_subbands() == []

    def test_registry_matches_roster(self):
        from prediction_market_bot.execution_bands import (
            T4_SUBBANDS, T4_SUBBAND_REGISTRY,
        )
        assert set(T4_SUBBAND_REGISTRY) == set(T4_SUBBANDS)

    def test_all_subbands_blocked(self):
        # No T4 sub-band may be ACTIVE without an activation ADR (ADR-0029 Tier B; rule 2).
        from prediction_market_bot.execution_bands import T4_SUBBAND_REGISTRY
        for band, spec in T4_SUBBAND_REGISTRY.items():
            assert spec.status == "BLOCKED", f"{band.value} must be BLOCKED"

    def test_all_subbands_phase8_realtime(self):
        from prediction_market_bot.execution_bands import (
            T4_SUBBANDS, get_band_config,
        )
        for sub in T4_SUBBANDS:
            cfg = get_band_config(sub)
            assert cfg.requires_realtime is True
            assert cfg.phase_active == "Phase 8"

    def test_parent_rollup_to_aggregate(self):
        from prediction_market_bot.execution_bands import (
            T4_SUBBANDS, t4_parent, is_t4_subband,
        )
        for sub in T4_SUBBANDS:
            assert is_t4_subband(sub) is True
            assert t4_parent(sub) is ExecutionBand.T4_IN_PLAY
        # Aggregate + non-T4 bands are not sub-bands and map to themselves.
        assert is_t4_subband(ExecutionBand.T4_IN_PLAY) is False
        assert t4_parent(ExecutionBand.T1_MULTI_DAY) is ExecutionBand.T1_MULTI_DAY

    def test_proj_near_certain_kelly_held_below_ceiling(self):
        # T4-PROJ provisional Kelly must not exceed the LATE-regime hold (0.167) and must
        # stay strictly below the NBA T4-PROJ hard ceiling (0.25, a literal set by ADR-0029 —
        # independent of T1 MLB's kelly_fraction (ADR-0040) and of risk.py's
        # DEFAULT_KELLY_FRACTION; do not conflate the three),
        # per the ADR-0029 tail-calibration constraint (EXP-PROJ-01 pending).
        from prediction_market_bot.execution_bands import T4_SUBBAND_REGISTRY
        proj = T4_SUBBAND_REGISTRY[ExecutionBand.T4_PROJ]
        arith = T4_SUBBAND_REGISTRY[ExecutionBand.T4_ARITH]
        assert proj.provisional_kelly <= 0.167
        assert arith.provisional_kelly <= 0.167  # 0.22 placeholder held non-operational
        assert proj.provisional_kelly < 0.25
        assert proj.exp_gate == ("EXP-PROJ-01",)

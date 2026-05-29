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
    def test_all_five_bands_defined(self):
        values = {b.value for b in ExecutionBand}
        assert values == {"T1", "T2", "T3", "T4", "T5"}

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
        assert get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction == 0.25

    def test_t2_kelly_less_than_t1(self):
        t1 = get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction
        t2 = get_band_config(ExecutionBand.T2_SAME_DAY).kelly_fraction
        assert t2 < t1

    def test_t3_kelly_less_than_t2(self):
        t2 = get_band_config(ExecutionBand.T2_SAME_DAY).kelly_fraction
        t3 = get_band_config(ExecutionBand.T3_PRE_TIP).kelly_fraction
        assert t3 < t2

    def test_t4_kelly_less_than_t3(self):
        t3 = get_band_config(ExecutionBand.T3_PRE_TIP).kelly_fraction
        t4 = get_band_config(ExecutionBand.T4_IN_PLAY).kelly_fraction
        assert t4 < t3

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

    def test_include_realtime_returns_all_five(self):
        all_bands = get_active_bands(include_realtime=True)
        assert len(all_bands) == 5

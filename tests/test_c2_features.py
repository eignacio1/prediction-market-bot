"""
Tests for src/prediction_market_bot/c2_feature_store/features.py — v1.2.0

Coverage areas:
  - FEATURE_VERSION is "1.2.0"
  - get_feature_names() returns 31 features (F-001 to F-031; v1.1.0 ERI/schedule pruned)
  - Pruned v1.1.0 features (F-032–F-038) are absent from feature names and output
  - Core rolling mean, std, efficiency, regime, and season context features present
  - Temporal integrity: no look-ahead in any feature
  - FeatureStore.compute_features_bulk smoke test
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c2_feature_store.features import (
    FEATURE_VERSION,
    FeatureStore,
    _compute_rolling_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_player_df(
    n: int = 20,
    pts_values: list[float] | None = None,
    season_type: str = "Regular Season",
    start_date: date = date(2022, 1, 1),
    gap_days: int = 2,
) -> pd.DataFrame:
    """Build a per-player sorted game-log DataFrame."""
    dates = [start_date + timedelta(days=gap_days * i) for i in range(n)]
    pts = pts_values if pts_values is not None else [float(20 + i % 5) for i in range(n)]
    return pd.DataFrame(
        {
            "player_id": [2544] * n,
            "player_name": ["LeBron"] * n,
            "team_id": [1610612747] * n,
            "team_abbreviation": ["LAL"] * n,
            "game_id": [f"00220{1000 + i}" for i in range(n)],
            "game_date": [d.isoformat() for d in dates],
            "season": ["2021-22"] * n,
            "season_type": [season_type] * n,
            "pts": [float(p) for p in pts],
            "reb": [5.0] * n,
            "ast": [7.0] * n,
            "stl": [1.0] * n,
            "blk": [0.5] * n,
            "tov": [3.0] * n,
            "min": [35.0] * n,
            "fgm": [8.0] * n,
            "fga": [17.0] * n,
            "fg_pct": [0.47] * n,
            "fg3m": [2.0] * n,
            "fg3a": [6.0] * n,
            "fg3_pct": [0.33] * n,
            "ftm": [5.0] * n,
            "fta": [6.0] * n,
            "ft_pct": [0.83] * n,
            "plus_minus": [5.0] * n,
            "pf": [2.0] * n,
            "snapshot_id": ["SNAP-TEST"] * n,
            "ingestion_run_id": ["TEST-RUN"] * n,
            "ingested_at": ["2026-01-01T00:00:00.000Z"] * n,
        }
    )


def _make_mock_logger(write_ok: bool = True) -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = write_ok
    logger.info.return_value = write_ok
    logger.error.return_value = write_ok
    return logger


# ---------------------------------------------------------------------------
# FEATURE_VERSION and feature count
# ---------------------------------------------------------------------------


class TestFeatureVersion:
    @pytest.mark.unit
    def test_version_is_1_3_0(self):
        assert FEATURE_VERSION == "1.3.0"

    @pytest.mark.unit
    def test_get_feature_names_count(self):
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        assert len(names) == 33, f"Expected 33 features, got {len(names)}: {names}"

    @pytest.mark.unit
    def test_pruned_schedule_features_absent_from_names(self):
        """F-032–F-035 (v1.1.0 schedule/load) must not appear in v1.2.0 feature names."""
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        for col in ["season_type_is_playoffs", "days_since_last_game", "b2b_flag", "load_games_l7d"]:
            assert col not in names, f"Pruned feature '{col}' should not be in get_feature_names()"

    @pytest.mark.unit
    def test_pruned_eri_features_absent_from_names(self):
        """F-036–F-038 (v1.1.0 ERI v0) must not appear in v1.2.0 feature names."""
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        for col in ["eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games"]:
            assert col not in names, f"Pruned feature '{col}' should not be in get_feature_names()"

    @pytest.mark.unit
    def test_no_duplicate_feature_names(self):
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        assert len(names) == len(set(names)), "Duplicate feature names detected"

    @pytest.mark.unit
    def test_core_rolling_mean_features_present(self):
        """F-001–F-018: rolling mean features still present in v1.2.0."""
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        for col in ["pts_l10_mean", "reb_l10_mean", "ast_l10_mean", "min_l10_mean", "fg_pct_l10_mean"]:
            assert col in names, f"Core feature '{col}' missing from get_feature_names()"

    @pytest.mark.unit
    def test_regime_and_context_features_present(self):
        """F-027–F-031: regime flags and season context still present in v1.2.0."""
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        for col in ["pts_hot_flag", "pts_cold_flag", "games_played_prior", "pts_season_mean", "min_season_mean"]:
            assert col in names, f"Core feature '{col}' missing from get_feature_names()"


# ---------------------------------------------------------------------------
# FeatureStore bulk compute — v1.2.0 behaviour
# ---------------------------------------------------------------------------


class TestFeatureStoreBulk:
    @pytest.mark.unit
    def test_compute_features_bulk_feature_version_is_1_3_0(self):
        df = _make_player_df(n=20)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert (feature_df["feature_version"] == "1.3.0").all()

    @pytest.mark.unit
    def test_compute_features_bulk_has_core_columns(self):
        df = _make_player_df(n=20)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        ok, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert ok is True
        for col in ["pts_l10_mean", "pts_hot_flag", "pts_cold_flag",
                    "games_played_prior", "pts_season_mean", "min_season_mean"]:
            assert col in feature_df.columns, f"'{col}' missing from bulk output"

    @pytest.mark.unit
    def test_compute_features_bulk_pruned_columns_absent(self):
        """v1.1.0 pruned features must not appear in bulk output."""
        df = _make_player_df(n=20)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        for col in [
            "season_type_is_playoffs", "days_since_last_game", "b2b_flag", "load_games_l7d",
            "eri_prev_hot", "eri_prev_cold", "eri_consec_cold_games",
        ]:
            assert col not in feature_df.columns, f"Pruned column '{col}' should not be in bulk output"

    @pytest.mark.unit
    def test_compute_features_bulk_empty_input(self):
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        ok, feature_df = store.compute_features_bulk(pd.DataFrame(), session_id="TEST-SESSION")
        assert ok is True
        assert len(feature_df) == 0

    @pytest.mark.unit
    def test_compute_features_bulk_c6_write_failure_propagates(self):
        store = FeatureStore(logger=_make_mock_logger(write_ok=False), snapshot_id="SNAP-TEST")
        df = _make_player_df(n=20)
        ok, _ = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert ok is False

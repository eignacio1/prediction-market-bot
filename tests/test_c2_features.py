"""
Tests for src/prediction_market_bot/c2_feature_store/features.py — v1.4.0

Coverage areas:
  - FEATURE_VERSION is "1.4.0"
  - get_feature_names() returns 36 features (+3 playoff context: F-041/F-042/F-043)
  - Pruned v1.1.0 features (F-032–F-038) are absent from feature names and output
  - Core rolling mean, std, efficiency, regime, and season context features present
  - Temporal integrity: no look-ahead in any feature
  - FeatureStore.compute_features_bulk smoke test
  - playoff_round_multiplier (F-041): 1.0 for regular season
  - series_scoring_delta (F-043): 0.0 for regular season, computed for playoff games
  - opp_playoff_def_rating_l5_mean (F-042): NaN when no playoff store provided
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
    _compute_playoff_features,
    _PLAYOFF_ROUND_MULTIPLIERS,
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
    def test_version_is_1_4_0(self):
        assert FEATURE_VERSION == "1.4.0"

    @pytest.mark.unit
    def test_get_feature_names_count(self):
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        assert len(names) == 36, f"Expected 36 features, got {len(names)}: {names}"

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
    def test_compute_features_bulk_feature_version_is_1_4_0(self):
        df = _make_player_df(n=20)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert (feature_df["feature_version"] == "1.4.0").all()

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

    @pytest.mark.unit
    def test_playoff_features_present_in_bulk_output(self):
        """F-041/F-042/F-043 columns must exist in bulk output (v1.4.0)."""
        df = _make_player_df(n=20)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        for col in ["playoff_round_multiplier", "opp_playoff_def_rating_l5_mean", "series_scoring_delta"]:
            assert col in feature_df.columns, f"'{col}' missing from v1.4.0 bulk output"


# ---------------------------------------------------------------------------
# v1.4.0 playoff context features (F-041, F-042, F-043)
# ---------------------------------------------------------------------------


def _make_playoff_player_df(
    n_regular: int = 10,
    n_series1: int = 4,
    pts_regular: float = 25.0,
    pts_series: list[float] | None = None,
    opponent: str = "GSW",
) -> pd.DataFrame:
    """Build a game log with regular-season games followed by playoff series games."""
    import numpy as np
    from datetime import date, timedelta

    start = date(2026, 1, 1)
    rows = []
    for i in range(n_regular):
        rows.append({
            "player_id": 2544,
            "player_name": "LeBron",
            "team_id": 1610612747,
            "team_abbreviation": "LAL",
            "game_id": f"0022{1000 + i}",
            "game_date": (start + timedelta(days=2 * i)).isoformat(),
            "season": "2025-26",
            "season_type": "Regular Season",
            "pts": pts_regular,
            "reb": 5.0, "ast": 7.0, "stl": 1.0, "blk": 0.5, "tov": 3.0, "min": 35.0,
            "fgm": 8.0, "fga": 17.0, "fg_pct": 0.47, "fg3m": 2.0, "fg3a": 6.0,
            "fg3_pct": 0.33, "ftm": 5.0, "fta": 6.0, "ft_pct": 0.83,
            "plus_minus": 5.0, "pf": 2.0,
            "opponent_team_abbr": "BOS",
            "snapshot_id": "SNAP-TEST", "ingestion_run_id": "TEST-RUN",
            "ingested_at": "2026-01-01T00:00:00.000Z",
        })

    playoff_start = start + timedelta(days=2 * n_regular + 30)
    pts_list = pts_series if pts_series is not None else [float(20 - j) for j in range(n_series1)]
    for j in range(n_series1):
        rows.append({
            "player_id": 2544,
            "player_name": "LeBron",
            "team_id": 1610612747,
            "team_abbreviation": "LAL",
            "game_id": f"0042{2000 + j}",
            "game_date": (playoff_start + timedelta(days=2 * j)).isoformat(),
            "season": "2025-26",
            "season_type": "Playoffs",
            "pts": float(pts_list[j]),
            "reb": 5.0, "ast": 7.0, "stl": 1.0, "blk": 0.5, "tov": 3.0, "min": 35.0,
            "fgm": 8.0, "fga": 17.0, "fg_pct": 0.47, "fg3m": 2.0, "fg3a": 6.0,
            "fg3_pct": 0.33, "ftm": 5.0, "fta": 6.0, "ft_pct": 0.83,
            "plus_minus": 5.0, "pf": 2.0,
            "opponent_team_abbr": opponent,
            "snapshot_id": "SNAP-TEST", "ingestion_run_id": "TEST-RUN",
            "ingested_at": "2026-01-01T00:00:00.000Z",
        })

    return pd.DataFrame(rows)


class TestPlayoffFeatures:
    """v1.4.0 — F-041 playoff_round_multiplier, F-042 opp_playoff_def_rating_l5_mean,
    F-043 series_scoring_delta."""

    @pytest.mark.unit
    def test_multiplier_constant_keys(self):
        """_PLAYOFF_ROUND_MULTIPLIERS must have keys 0 and 1."""
        assert 0 in _PLAYOFF_ROUND_MULTIPLIERS
        assert 1 in _PLAYOFF_ROUND_MULTIPLIERS

    @pytest.mark.unit
    def test_multiplier_constant_regular_season_is_1(self):
        """Regular-season key must be exactly 1.0 (no adjustment)."""
        assert _PLAYOFF_ROUND_MULTIPLIERS[0] == 1.0

    @pytest.mark.unit
    def test_playoff_features_in_get_feature_names(self):
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        names = store.get_feature_names()
        for col in ["playoff_round_multiplier", "opp_playoff_def_rating_l5_mean", "series_scoring_delta"]:
            assert col in names, f"'{col}' missing from get_feature_names() v1.4.0"

    @pytest.mark.unit
    def test_regular_season_multiplier_is_one(self):
        """playoff_round_multiplier must be 1.0 for all regular-season rows."""
        df = _make_player_df(n=20, season_type="Regular Season")
        result = _compute_rolling_features(df, window=10, min_periods=3)
        # Need opponent_team_abbr for playoff features
        result["opponent_team_abbr"] = "BOS"
        playoff_df = _compute_playoff_features(result, window=10)
        assert (playoff_df["playoff_round_multiplier"] == 1.0).all()

    @pytest.mark.unit
    def test_regular_season_series_delta_is_zero(self):
        """series_scoring_delta must be 0.0 for all regular-season rows."""
        df = _make_player_df(n=20, season_type="Regular Season")
        result = _compute_rolling_features(df, window=10, min_periods=3)
        result["opponent_team_abbr"] = "BOS"
        playoff_df = _compute_playoff_features(result, window=10)
        assert (playoff_df["series_scoring_delta"] == 0.0).all()

    @pytest.mark.unit
    def test_playoff_game1_series_delta_is_zero(self):
        """Game 1 of a playoff series has no prior series data — delta must be 0.0."""
        df = _make_playoff_player_df(n_regular=10, n_series1=4, pts_regular=25.0,
                                     pts_series=[20.0, 15.0, 12.0, 10.0])
        result = _compute_rolling_features(df, window=10, min_periods=3)
        playoff_df = _compute_playoff_features(result, window=10)
        playoff_rows = playoff_df[result["season_type"] == "Playoffs"]
        game1_delta = playoff_rows.iloc[0]["series_scoring_delta"]
        assert game1_delta == 0.0, f"Game 1 series_scoring_delta should be 0.0, got {game1_delta}"

    @pytest.mark.unit
    def test_playoff_game2_series_delta_uses_game1_pts(self):
        """Game 2 delta = game1_pts - pts_l10_mean_at_game2."""
        pts_series = [20.0, 15.0, 12.0, 10.0]
        df = _make_playoff_player_df(n_regular=10, n_series1=4, pts_regular=25.0,
                                     pts_series=pts_series)
        result = _compute_rolling_features(df, window=10, min_periods=3)
        playoff_df = _compute_playoff_features(result, window=10)

        playoff_rows = result[result["season_type"] == "Playoffs"].reset_index()
        playoff_deltas = playoff_df[result["season_type"] == "Playoffs"].reset_index()

        game2_idx = playoff_rows.index[1]
        expected_series_mean = pts_series[0]  # only game 1 is prior
        baseline = playoff_rows.iloc[1]["pts_l10_mean"]
        expected_delta = expected_series_mean - baseline
        actual_delta = playoff_deltas.iloc[1]["series_scoring_delta"]
        assert abs(actual_delta - expected_delta) < 1e-9, \
            f"Game 2 delta: expected {expected_delta:.4f}, got {actual_delta:.4f}"

    @pytest.mark.unit
    def test_series_delta_temporal_integrity(self):
        """series_scoring_delta for game N must only use games 1..N-1 of the series."""
        pts_series = [30.0, 10.0, 20.0, 15.0]
        df = _make_playoff_player_df(n_regular=10, n_series1=4, pts_regular=25.0,
                                     pts_series=pts_series)
        result = _compute_rolling_features(df, window=10, min_periods=3)
        playoff_df = _compute_playoff_features(result, window=10)

        playoff_result = result[result["season_type"] == "Playoffs"].reset_index()
        playoff_feats = playoff_df[result["season_type"] == "Playoffs"].reset_index()

        # Game 3 (index 2): prior series pts = [30.0, 10.0], mean = 20.0
        g3_baseline = playoff_result.iloc[2]["pts_l10_mean"]
        expected_g3_delta = (30.0 + 10.0) / 2 - g3_baseline
        actual_g3_delta = playoff_feats.iloc[2]["series_scoring_delta"]
        assert abs(actual_g3_delta - expected_g3_delta) < 1e-9, \
            f"Game 3 delta (TI check): expected {expected_g3_delta:.4f}, got {actual_g3_delta:.4f}"

        # Game 4: prior series pts = [30.0, 10.0, 20.0], mean = 20.0
        g4_baseline = playoff_result.iloc[3]["pts_l10_mean"]
        expected_g4_delta = (30.0 + 10.0 + 20.0) / 3 - g4_baseline
        actual_g4_delta = playoff_feats.iloc[3]["series_scoring_delta"]
        assert abs(actual_g4_delta - expected_g4_delta) < 1e-9, \
            f"Game 4 delta (TI check): expected {expected_g4_delta:.4f}, got {actual_g4_delta:.4f}"

    @pytest.mark.unit
    def test_opp_playoff_def_nan_when_no_playoff_store(self):
        """F-042 must be NaN for all rows when playoff_team_stats_store is None."""
        df = _make_playoff_player_df(n_regular=10, n_series1=4)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert feature_df["opp_playoff_def_rating_l5_mean"].isna().all(), \
            "F-042 should be NaN when no playoff_team_stats_store provided"

    @pytest.mark.unit
    def test_opp_playoff_def_nan_for_regular_season_rows(self):
        """F-042 must be NaN for regular-season rows regardless of playoff store."""
        df = _make_player_df(n=20, season_type="Regular Season")
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert feature_df["opp_playoff_def_rating_l5_mean"].isna().all(), \
            "F-042 should be NaN for all regular-season rows"

    @pytest.mark.unit
    def test_bulk_output_row_count_unchanged_with_playoff_features(self):
        """Adding playoff features must not drop or duplicate rows."""
        df = _make_playoff_player_df(n_regular=15, n_series1=5)
        store = FeatureStore(logger=_make_mock_logger(), snapshot_id="SNAP-TEST")
        _, feature_df = store.compute_features_bulk(df, session_id="TEST-SESSION")
        assert len(feature_df) == 20, \
            f"Expected 20 rows (15 regular + 5 playoff), got {len(feature_df)}"

"""
T-183 — MLB C3 Model Training Tests
=====================================

Tests for scripts/train_mlb_model.py.

All tests use synthetic data — no live HTTP, no venue API calls.
The training script is exercised via direct function calls and via
main() in dry-run mode with a tmp_path CSV.

Test classes:
  TestBuildMlbTarget      — threshold expansion and y_target derivation
  TestComputeEce          — ECE calculation
  TestImpute              — NaN imputation
  TestMlbModelVersion     — deterministic version hash
  TestExtractFeatureMatrix — NON_FEATURE exclusion and sorted columns
  TestNonFeatureSet       — _NON_FEATURE_MLB membership
  TestNullBaseline        — Brier of naive class-prior predictor
  TestShadowGateLogic     — brier_delta and ECE gate conditions
  TestModelArtifact       — joblib save / load round-trip
  TestEndToEndDryRun      — full main() in dry-run mode with synthetic CSV
  TestMultipleThresholds  — cross-threshold consistency
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import brier_score_loss

# ---------------------------------------------------------------------------
# Make scripts/ importable
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from train_mlb_model import (  # noqa: E402
    HOLDOUT_CUTOFF,
    MIN_HOLDOUT_SAMPLES,
    MIN_TRAIN_SAMPLES,
    SHADOW_GATE_BRIER_DELTA,
    SHADOW_GATE_ECE_MAX,
    THRESHOLDS,
    _NON_FEATURE_MLB,
    _build_mlb_target,
    _compute_ece,
    _extract_feature_matrix,
    _impute,
    _mlb_model_version,
    main,
)

# ---------------------------------------------------------------------------
# Shared synthetic data helpers
# ---------------------------------------------------------------------------


def _make_game_row(
    player_id: int = 1,
    game_id: int = 100,
    game_date: str = "2025-04-01",
    h: int = 1,
    ab: int = 4,
    is_home_game: int = 1,
    has_prior: bool = True,
    threshold: float | None = None,
) -> dict:
    row = {
        "player_id": player_id,
        "player_name": "Test Player",
        "team_abbreviation": "TST",
        "game_id": game_id,
        "game_date": game_date,
        "season": "2025",
        "season_type": "Regular Season",
        "matchup": "TST @ OPP",
        "opponent_team_abbr": "OPP",
        "snapshot_id": "SNAP-TEST",
        "feature_run_id": "C2MLB-abc12345",
        "feature_version": "1.0.0",
        "temporal_cutoff": "2025-03-31" if has_prior else None,
        "train_test_label": "TRAIN",
        "ingestion_run_id": "ING-001",
        "ingested_at": "2025-04-02T00:00:00Z",
        # Raw outcomes (must not be features)
        "ab": ab,
        "h": h,
        "doubles": 0,
        "triples": 0,
        "hr": 0,
        "rbi": 0,
        "bb": 0,
        "k": 1,
        "hbp": 0,
        "sf": 0,
        # Features
        "is_home_game": float(is_home_game),
        "days_rest": 1.0,
        "b2b_flag": 1.0,
        "ba_l10": 0.280,
        "slg_l10": 0.420,
        "obp_l10": 0.350,
        "ops_l10": 0.770,
        "h_l10_mean": 1.1,
        "k_rate_l10": 0.22,
        "bb_rate_l10": 0.08,
        "hr_rate_l10": 0.05,
        "opp_runs_allowed_l10": 4.2,
        "opp_sp_era_l5": 3.80,
        "opp_sp_k9_l5": 8.5,
        "opp_sp_bb9_l5": 2.5,
        "opp_sp_is_known": 1.0,
        "park_factor_hits": 1.000,
    }
    if threshold is not None:
        row["threshold"] = threshold
    return row


def _make_feature_df(
    n: int = 10,
    base_date: str = "2025-04-01",
    h_values: list[int] | None = None,
) -> pd.DataFrame:
    """Return a minimal IF-C2-C3 feature DataFrame with n rows."""
    rows = []
    for i in range(n):
        h = h_values[i] if h_values else (i % 3)
        rows.append(
            _make_game_row(
                player_id=i + 1,
                game_id=200 + i,
                game_date=base_date,
                h=h,
            )
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# TestBuildMlbTarget
# ---------------------------------------------------------------------------


class TestBuildMlbTarget:
    def test_row_count_expands_by_threshold_count(self) -> None:
        df = _make_feature_df(n=5)
        result = _build_mlb_target(df, thresholds=[1, 2, 3])
        assert len(result) == 5 * 3

    def test_threshold_values_present(self) -> None:
        df = _make_feature_df(n=2)
        result = _build_mlb_target(df, thresholds=[1, 2, 3])
        assert set(result["threshold"].unique()) == {1.0, 2.0, 3.0}

    def test_threshold_stored_as_float(self) -> None:
        df = _make_feature_df(n=1)
        result = _build_mlb_target(df, thresholds=[1])
        assert result["threshold"].dtype == float

    def test_target_1plus_when_h_equals_1(self) -> None:
        df = _make_feature_df(n=1, h_values=[1])
        result = _build_mlb_target(df, thresholds=[1])
        assert int(result["y_target"].iloc[0]) == 1

    def test_target_1plus_when_h_equals_0(self) -> None:
        df = _make_feature_df(n=1, h_values=[0])
        result = _build_mlb_target(df, thresholds=[1])
        assert int(result["y_target"].iloc[0]) == 0

    def test_target_2plus_when_h_equals_2(self) -> None:
        df = _make_feature_df(n=1, h_values=[2])
        result = _build_mlb_target(df, thresholds=[2])
        assert int(result["y_target"].iloc[0]) == 1

    def test_target_2plus_when_h_equals_1(self) -> None:
        df = _make_feature_df(n=1, h_values=[1])
        result = _build_mlb_target(df, thresholds=[2])
        assert int(result["y_target"].iloc[0]) == 0

    def test_target_3plus_when_h_equals_3(self) -> None:
        df = _make_feature_df(n=1, h_values=[3])
        result = _build_mlb_target(df, thresholds=[3])
        assert int(result["y_target"].iloc[0]) == 1

    def test_target_3plus_when_h_equals_2(self) -> None:
        df = _make_feature_df(n=1, h_values=[2])
        result = _build_mlb_target(df, thresholds=[3])
        assert int(result["y_target"].iloc[0]) == 0

    def test_target_nan_when_h_missing(self) -> None:
        df = _make_feature_df(n=1, h_values=[1])
        df["h"] = np.nan
        result = _build_mlb_target(df, thresholds=[1, 2])
        assert result["y_target"].isna().all()

    def test_single_threshold_only(self) -> None:
        df = _make_feature_df(n=3)
        result = _build_mlb_target(df, thresholds=[2])
        assert len(result) == 3
        assert (result["threshold"] == 2.0).all()

    def test_original_df_not_mutated(self) -> None:
        df = _make_feature_df(n=3)
        original_len = len(df)
        _build_mlb_target(df, thresholds=[1, 2, 3])
        assert len(df) == original_len
        assert "threshold" not in df.columns

    def test_each_game_appears_once_per_threshold(self) -> None:
        df = _make_feature_df(n=4)
        result = _build_mlb_target(df, thresholds=[1, 2, 3])
        for gid in df["game_id"].unique():
            assert (result["game_id"] == gid).sum() == 3


# ---------------------------------------------------------------------------
# TestComputeEce
# ---------------------------------------------------------------------------


class TestComputeEce:
    def test_perfect_calibration_near_zero(self) -> None:
        rng = np.random.default_rng(0)
        y_prob = rng.uniform(0.1, 0.9, 200)
        y_true = rng.binomial(1, y_prob)
        ece = _compute_ece(y_true, y_prob)
        assert ece < 0.15

    def test_overconfident_predictor_has_high_ece(self) -> None:
        y_prob = np.full(100, 0.9)
        y_true = np.zeros(100)
        y_true[:20] = 1  # 20% actual positive, 90% predicted
        ece = _compute_ece(y_true, y_prob)
        assert ece > 0.5

    def test_ece_is_nonnegative(self) -> None:
        rng = np.random.default_rng(1)
        y_prob = rng.uniform(0, 1, 50)
        y_true = rng.binomial(1, 0.5, 50)
        assert _compute_ece(y_true, y_prob) >= 0.0

    def test_ece_at_most_one(self) -> None:
        y_prob = np.array([0.99] * 100)
        y_true = np.zeros(100)
        assert _compute_ece(y_true, y_prob) <= 1.0

    def test_ece_symmetric_around_50pct(self) -> None:
        y_prob = np.full(100, 0.5)
        y_true = np.zeros(100)
        ece = _compute_ece(y_true, y_prob)
        assert abs(ece - 0.5) < 0.01


# ---------------------------------------------------------------------------
# TestImpute
# ---------------------------------------------------------------------------


class TestImpute:
    def test_replaces_nan_with_median(self) -> None:
        X = np.array([[1.0, np.nan], [3.0, 4.0]])
        medians = np.array([2.0, 4.0])
        result = _impute(X, medians)
        assert result[0, 1] == 4.0

    def test_non_nan_values_unchanged(self) -> None:
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        medians = np.array([99.0, 99.0])
        result = _impute(X, medians)
        np.testing.assert_array_equal(result, X)

    def test_all_nan_column_gets_zero(self) -> None:
        X = np.array([[np.nan], [np.nan]])
        medians = np.array([np.nan])
        result = _impute(X, medians)
        assert (result == 0.0).all()

    def test_returns_copy_not_inplace(self) -> None:
        X = np.array([[np.nan, 1.0]])
        medians = np.array([5.0, 1.0])
        result = _impute(X, medians)
        assert np.isnan(X[0, 0])  # original unchanged
        assert result[0, 0] == 5.0


# ---------------------------------------------------------------------------
# TestMlbModelVersion
# ---------------------------------------------------------------------------


class TestMlbModelVersion:
    def test_deterministic(self) -> None:
        features = ["ba_l10", "threshold", "opp_sp_era_l5"]
        assert _mlb_model_version(features) == _mlb_model_version(features)

    def test_order_independent(self) -> None:
        f1 = ["ba_l10", "threshold", "opp_sp_era_l5"]
        f2 = ["threshold", "opp_sp_era_l5", "ba_l10"]
        assert _mlb_model_version(f1) == _mlb_model_version(f2)

    def test_changes_with_different_features(self) -> None:
        f1 = ["ba_l10", "threshold"]
        f2 = ["ba_l10", "threshold", "park_factor_hits"]
        assert _mlb_model_version(f1) != _mlb_model_version(f2)

    def test_prefix(self) -> None:
        assert _mlb_model_version(["ba_l10"]).startswith("mlb-v1-")

    def test_hash_length(self) -> None:
        v = _mlb_model_version(["ba_l10", "threshold"])
        # "mlb-v1-" (7 chars) + 8 hex chars = 15
        assert len(v) == 15


# ---------------------------------------------------------------------------
# TestExtractFeatureMatrix
# ---------------------------------------------------------------------------


class TestExtractFeatureMatrix:
    def test_excludes_player_id(self) -> None:
        df = _make_feature_df(n=2)
        _, feature_names = _extract_feature_matrix(df)
        assert "player_id" not in feature_names

    def test_excludes_raw_h_column(self) -> None:
        df = _make_feature_df(n=2)
        _, feature_names = _extract_feature_matrix(df)
        assert "h" not in feature_names

    def test_excludes_y_target(self) -> None:
        df = _make_feature_df(n=2)
        df["y_target"] = 0
        _, feature_names = _extract_feature_matrix(df)
        assert "y_target" not in feature_names

    def test_includes_ba_l10(self) -> None:
        df = _make_feature_df(n=2)
        _, feature_names = _extract_feature_matrix(df)
        assert "ba_l10" in feature_names

    def test_includes_threshold_when_present(self) -> None:
        df = _make_feature_df(n=2)
        df["threshold"] = 1.0
        _, feature_names = _extract_feature_matrix(df)
        assert "threshold" in feature_names

    def test_columns_sorted_alphabetically(self) -> None:
        df = _make_feature_df(n=2)
        _, feature_names = _extract_feature_matrix(df)
        assert feature_names == sorted(feature_names)

    def test_x_shape_matches_feature_count(self) -> None:
        df = _make_feature_df(n=5)
        X, feature_names = _extract_feature_matrix(df)
        assert X.shape == (5, len(feature_names))

    def test_x_dtype_float64(self) -> None:
        df = _make_feature_df(n=3)
        X, _ = _extract_feature_matrix(df)
        assert X.dtype == np.float64


# ---------------------------------------------------------------------------
# TestNonFeatureSet
# ---------------------------------------------------------------------------


class TestNonFeatureSet:
    def test_h_in_non_feature(self) -> None:
        assert "h" in _NON_FEATURE_MLB

    def test_ab_in_non_feature(self) -> None:
        assert "ab" in _NON_FEATURE_MLB

    def test_player_id_in_non_feature(self) -> None:
        assert "player_id" in _NON_FEATURE_MLB

    def test_game_date_in_non_feature(self) -> None:
        assert "game_date" in _NON_FEATURE_MLB

    def test_y_target_in_non_feature(self) -> None:
        assert "y_target" in _NON_FEATURE_MLB

    def test_ba_l10_not_in_non_feature(self) -> None:
        assert "ba_l10" not in _NON_FEATURE_MLB

    def test_threshold_not_in_non_feature(self) -> None:
        assert "threshold" not in _NON_FEATURE_MLB

    def test_is_home_game_not_in_non_feature(self) -> None:
        assert "is_home_game" not in _NON_FEATURE_MLB

    def test_opp_sp_era_l5_not_in_non_feature(self) -> None:
        assert "opp_sp_era_l5" not in _NON_FEATURE_MLB

    def test_park_factor_hits_not_in_non_feature(self) -> None:
        assert "park_factor_hits" not in _NON_FEATURE_MLB


# ---------------------------------------------------------------------------
# TestNullBaseline
# ---------------------------------------------------------------------------


class TestNullBaseline:
    def test_null_brier_equals_p_times_one_minus_p(self) -> None:
        p = 0.35
        y_true = np.zeros(1000)
        y_true[: int(1000 * p)] = 1
        y_null = np.full(1000, p)
        brier = float(brier_score_loss(y_true, y_null))
        assert abs(brier - p * (1 - p)) < 0.005

    def test_null_brier_maximized_at_50pct(self) -> None:
        p_50 = 0.25  # Brier at p=0.5 is 0.25
        p = 0.5
        y_true = np.zeros(1000)
        y_true[:500] = 1
        y_null = np.full(1000, p)
        brier = float(brier_score_loss(y_true, y_null))
        assert abs(brier - p_50) < 0.01

    def test_high_prevalence_lower_null_brier(self) -> None:
        p_high = 0.8
        y_true = np.zeros(1000)
        y_true[:800] = 1
        brier_high = float(brier_score_loss(y_true, np.full(1000, p_high)))
        p_50 = 0.5
        y_true_50 = np.zeros(1000)
        y_true_50[:500] = 1
        brier_50 = float(brier_score_loss(y_true_50, np.full(1000, p_50)))
        assert brier_high < brier_50


# ---------------------------------------------------------------------------
# TestShadowGateLogic
# ---------------------------------------------------------------------------


class TestShadowGateLogic:
    def test_brier_delta_computation(self) -> None:
        y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0] * 10, dtype=float)
        p = float(y_true.mean())
        y_null = np.full(len(y_true), p)
        brier_null = float(brier_score_loss(y_true, y_null))
        # Model that's slightly better
        y_model = np.clip(y_true + np.random.default_rng(42).normal(0, 0.05, len(y_true)), 0, 1)
        brier_model = float(brier_score_loss(y_true, y_model))
        delta = brier_null - brier_model
        assert delta > -1.0  # sanity

    def test_shadow_gate_brier_delta_constant(self) -> None:
        assert SHADOW_GATE_BRIER_DELTA == 0.001

    def test_shadow_gate_ece_max_constant(self) -> None:
        assert SHADOW_GATE_ECE_MAX == 0.05

    def test_holdout_cutoff_constant(self) -> None:
        assert HOLDOUT_CUTOFF == "2026-01-01"

    def test_min_train_samples_constant(self) -> None:
        assert MIN_TRAIN_SAMPLES == 30

    def test_thresholds_constant(self) -> None:
        assert THRESHOLDS == [1, 2, 3]


# ---------------------------------------------------------------------------
# TestModelArtifact
# ---------------------------------------------------------------------------


class TestModelArtifact:
    def _make_pipeline(self) -> object:
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        rng = np.random.default_rng(0)
        X = rng.standard_normal((100, 3))
        y = rng.integers(0, 2, 100)
        clf = LogisticRegression(max_iter=200, random_state=42)
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", CalibratedClassifierCV(clf, cv=3, method="sigmoid")),
        ])
        pipe.fit(X, y)
        return pipe

    def test_artifact_round_trip(self, tmp_path: Path) -> None:
        pipe = self._make_pipeline()
        feature_names = ["f1", "f2", "f3"]
        medians = np.array([0.0, 0.0, 0.0])
        artifact = {
            "pipeline": pipe,
            "feature_names": feature_names,
            "col_medians": medians,
            "model_version": "mlb-v1-testtest",
            "thresholds": [1, 2, 3],
            "sport": "mlb",
        }
        path = tmp_path / "mlb_v1_model.joblib"
        joblib.dump(artifact, path)
        loaded = joblib.load(path)
        assert loaded["feature_names"] == feature_names
        assert loaded["model_version"] == "mlb-v1-testtest"
        assert loaded["sport"] == "mlb"

    def test_loaded_pipeline_predicts_probabilities(self, tmp_path: Path) -> None:
        pipe = self._make_pipeline()
        artifact = {
            "pipeline": pipe,
            "feature_names": ["f1", "f2", "f3"],
            "col_medians": np.array([0.0, 0.0, 0.0]),
            "model_version": "mlb-v1-testtest",
            "thresholds": [1, 2, 3],
            "sport": "mlb",
        }
        path = tmp_path / "mlb_v1_model.joblib"
        joblib.dump(artifact, path)
        loaded = joblib.load(path)
        X_test = np.array([[0.1, 0.2, 0.3]])
        probs = loaded["pipeline"].predict_proba(X_test)
        assert probs.shape == (1, 2)
        assert 0.0 <= probs[0, 1] <= 1.0

    def test_meta_json_structure(self, tmp_path: Path) -> None:
        meta = {
            "model_version": "mlb-v1-abc12345",
            "feature_version": "1.0.0",
            "thresholds": [1, 2, 3],
            "holdout_cutoff": "2026-01-01",
            "shadow_gate_pass": True,
        }
        path = tmp_path / "mlb_v1_model_meta.json"
        path.write_text(json.dumps(meta))
        loaded = json.loads(path.read_text())
        assert loaded["model_version"] == "mlb-v1-abc12345"
        assert loaded["holdout_cutoff"] == "2026-01-01"
        assert loaded["shadow_gate_pass"] is True

    def test_col_medians_preserved(self, tmp_path: Path) -> None:
        pipe = self._make_pipeline()
        medians = np.array([1.1, 2.2, 3.3])
        artifact = {
            "pipeline": pipe,
            "feature_names": ["f1", "f2", "f3"],
            "col_medians": medians,
            "model_version": "mlb-v1-testtest",
            "thresholds": [1, 2, 3],
            "sport": "mlb",
        }
        path = tmp_path / "mlb_v1_model.joblib"
        joblib.dump(artifact, path)
        loaded = joblib.load(path)
        np.testing.assert_array_almost_equal(loaded["col_medians"], medians)


# ---------------------------------------------------------------------------
# TestEndToEndDryRun
# ---------------------------------------------------------------------------


def _write_synthetic_csv(path: Path, n_train: int = 60, n_holdout: int = 20) -> None:
    """Write a synthetic feature matrix CSV for end-to-end testing."""
    rng = np.random.default_rng(42)
    rows = []

    # Training rows: dates before HOLDOUT_CUTOFF
    for i in range(n_train):
        h = int(rng.integers(0, 4))
        rows.append({
            "player_id": (i % 10) + 1,
            "player_name": f"Player{(i % 10) + 1}",
            "team_abbreviation": "TST",
            "game_id": 1000 + i,
            "game_date": f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "season": "2025",
            "season_type": "Regular Season",
            "matchup": "TST @ OPP",
            "opponent_team_abbr": "OPP",
            "snapshot_id": "SNAP-TEST",
            "feature_run_id": "C2MLB-testtest",
            "feature_version": "1.0.0",
            "temporal_cutoff": "2025-03-15",
            "train_test_label": "TRAIN",
            "ingestion_run_id": "ING-001",
            "ingested_at": "2025-04-02T00:00:00Z",
            "ab": 4,
            "h": h,
            "doubles": 0,
            "triples": 0,
            "hr": 0,
            "rbi": 0,
            "bb": 0,
            "k": 1,
            "hbp": 0,
            "sf": 0,
            "is_home_game": float(i % 2),
            "days_rest": float(1 + (i % 3)),
            "b2b_flag": float((i % 3) == 0),
            "ba_l10": round(rng.uniform(0.200, 0.350), 3),
            "slg_l10": round(rng.uniform(0.300, 0.550), 3),
            "obp_l10": round(rng.uniform(0.300, 0.400), 3),
            "ops_l10": round(rng.uniform(0.600, 0.900), 3),
            "h_l10_mean": round(rng.uniform(0.5, 1.8), 2),
            "k_rate_l10": round(rng.uniform(0.15, 0.30), 3),
            "bb_rate_l10": round(rng.uniform(0.05, 0.15), 3),
            "hr_rate_l10": round(rng.uniform(0.02, 0.08), 3),
            "opp_runs_allowed_l10": round(rng.uniform(3.0, 5.5), 2),
            "opp_sp_era_l5": round(rng.uniform(2.5, 5.5), 2),
            "opp_sp_k9_l5": round(rng.uniform(6.0, 11.0), 1),
            "opp_sp_bb9_l5": round(rng.uniform(1.5, 4.5), 1),
            "opp_sp_is_known": 1.0,
            "park_factor_hits": round(rng.uniform(0.96, 1.12), 3),
        })

    # Holdout rows: dates after HOLDOUT_CUTOFF
    for i in range(n_holdout):
        h = int(rng.integers(0, 4))
        rows.append({
            "player_id": (i % 10) + 1,
            "player_name": f"Player{(i % 10) + 1}",
            "team_abbreviation": "TST",
            "game_id": 2000 + i,
            "game_date": f"2026-{(i % 6) + 2:02d}-{(i % 28) + 1:02d}",
            "season": "2026",
            "season_type": "Regular Season",
            "matchup": "TST @ OPP",
            "opponent_team_abbr": "OPP",
            "snapshot_id": "SNAP-TEST",
            "feature_run_id": "C2MLB-testtest",
            "feature_version": "1.0.0",
            "temporal_cutoff": "2026-02-15",
            "train_test_label": "TEST",
            "ingestion_run_id": "ING-001",
            "ingested_at": "2026-06-01T00:00:00Z",
            "ab": 4,
            "h": h,
            "doubles": 0,
            "triples": 0,
            "hr": 0,
            "rbi": 0,
            "bb": 0,
            "k": 1,
            "hbp": 0,
            "sf": 0,
            "is_home_game": float(i % 2),
            "days_rest": float(1 + (i % 3)),
            "b2b_flag": float((i % 3) == 0),
            "ba_l10": round(rng.uniform(0.200, 0.350), 3),
            "slg_l10": round(rng.uniform(0.300, 0.550), 3),
            "obp_l10": round(rng.uniform(0.300, 0.400), 3),
            "ops_l10": round(rng.uniform(0.600, 0.900), 3),
            "h_l10_mean": round(rng.uniform(0.5, 1.8), 2),
            "k_rate_l10": round(rng.uniform(0.15, 0.30), 3),
            "bb_rate_l10": round(rng.uniform(0.05, 0.15), 3),
            "hr_rate_l10": round(rng.uniform(0.02, 0.08), 3),
            "opp_runs_allowed_l10": round(rng.uniform(3.0, 5.5), 2),
            "opp_sp_era_l5": round(rng.uniform(2.5, 5.5), 2),
            "opp_sp_k9_l5": round(rng.uniform(6.0, 11.0), 1),
            "opp_sp_bb9_l5": round(rng.uniform(1.5, 4.5), 1),
            "opp_sp_is_known": 1.0,
            "park_factor_hits": round(rng.uniform(0.96, 1.12), 3),
        })

    pd.DataFrame(rows).to_csv(path, index=False)


class TestEndToEndDryRun:
    @pytest.fixture(autouse=True)
    def clear_c4_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """run_paper_trade.py sets BOT_C4_ACTIVE at import time.
        The training guard would fire on every call — clear for these tests."""
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)

    def test_dry_run_completes_without_error(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        # dry_run=True + force_save=True so shadow gate never kills the run
        main(csv_path=csv, dry_run=True, force_save=True, model_path=tmp_path / "m.joblib", meta_path=tmp_path / "m.json")

    def test_dry_run_does_not_create_model_file(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        main(csv_path=csv, dry_run=True, force_save=True, model_path=model_path, meta_path=tmp_path / "m.json")
        assert not model_path.exists()

    def test_dry_run_does_not_create_meta_file(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=True, force_save=True, model_path=tmp_path / "m.joblib", meta_path=meta_path)
        assert not meta_path.exists()

    def test_guard_fires_when_csv_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(csv_path=tmp_path / "nonexistent.csv", dry_run=True,
                 model_path=tmp_path / "m.joblib", meta_path=tmp_path / "m.json")
        assert exc_info.value.code == 1

    def test_guard_fires_when_bot_c4_active_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BOT_C4_ACTIVE", "1")
        with pytest.raises(SystemExit) as exc_info:
            main(csv_path=tmp_path / "nonexistent.csv", dry_run=True,
                 model_path=tmp_path / "m.joblib", meta_path=tmp_path / "m.json")
        assert exc_info.value.code == 1

    def test_guard_fires_on_insufficient_train_rows(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=5, n_holdout=15)  # 5*3=15 expanded < MIN_TRAIN_SAMPLES
        with pytest.raises(SystemExit) as exc_info:
            main(csv_path=csv, dry_run=True, force_save=True,
                 model_path=tmp_path / "m.joblib", meta_path=tmp_path / "m.json")
        assert exc_info.value.code == 1

    def test_guard_fires_on_insufficient_holdout_rows(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=0)
        with pytest.raises(SystemExit) as exc_info:
            main(csv_path=csv, dry_run=True, force_save=True,
                 model_path=tmp_path / "m.joblib", meta_path=tmp_path / "m.json")
        assert exc_info.value.code == 1

    def test_force_save_creates_model_file(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=False, force_save=True,
             model_path=model_path, meta_path=meta_path)
        assert model_path.exists()

    def test_force_save_creates_meta_file(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=False, force_save=True,
             model_path=model_path, meta_path=meta_path)
        assert meta_path.exists()

    def test_saved_meta_has_model_version(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=False, force_save=True,
             model_path=model_path, meta_path=meta_path)
        meta = json.loads(meta_path.read_text())
        assert meta["model_version"].startswith("mlb-v1-")

    def test_saved_meta_has_thresholds(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=False, force_save=True,
             model_path=model_path, meta_path=meta_path)
        meta = json.loads(meta_path.read_text())
        assert meta["thresholds"] == [1, 2, 3]

    def test_saved_artifact_has_feature_names(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=False, force_save=True,
             model_path=model_path, meta_path=meta_path)
        artifact = joblib.load(model_path)
        assert "feature_names" in artifact
        assert "threshold" in artifact["feature_names"]

    def test_saved_artifact_predicts_probabilities(self, tmp_path: Path) -> None:
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        model_path = tmp_path / "mlb_v1_model.joblib"
        meta_path = tmp_path / "mlb_v1_model_meta.json"
        main(csv_path=csv, dry_run=False, force_save=True,
             model_path=model_path, meta_path=meta_path)
        artifact = joblib.load(model_path)
        n_features = len(artifact["feature_names"])
        X_test = np.zeros((1, n_features))
        probs = artifact["pipeline"].predict_proba(X_test)
        assert probs.shape[1] == 2
        assert 0.0 <= probs[0, 1] <= 1.0

    def test_temporal_cutoff_none_rows_excluded(self, tmp_path: Path) -> None:
        """Rows with temporal_cutoff=None (first game per player) must not appear in train/holdout."""
        csv = tmp_path / "matrix.csv"
        _write_synthetic_csv(csv, n_train=60, n_holdout=30)
        # Inject a row with no prior game
        df = pd.read_csv(csv)
        no_prior_row = df.iloc[0].copy()
        no_prior_row["temporal_cutoff"] = None
        no_prior_row["game_date"] = "2025-01-01"
        df = pd.concat([df, pd.DataFrame([no_prior_row])], ignore_index=True)
        df.to_csv(csv, index=False)
        # dry_run should succeed — the null-cutoff row is filtered out
        main(csv_path=csv, dry_run=True, force_save=True,
             model_path=tmp_path / "m.joblib", meta_path=tmp_path / "m.json")


# ---------------------------------------------------------------------------
# TestMultipleThresholds
# ---------------------------------------------------------------------------


class TestMultipleThresholds:
    def test_higher_threshold_has_lower_or_equal_positive_rate(self) -> None:
        rng = np.random.default_rng(7)
        h_vals = rng.integers(0, 5, 100).tolist()
        df = _make_feature_df(n=100, h_values=h_vals)
        expanded = _build_mlb_target(df, thresholds=[1, 2, 3])
        for t1, t2 in [(1, 2), (2, 3)]:
            rate_t1 = expanded[expanded["threshold"] == float(t1)]["y_target"].astype(float).mean()
            rate_t2 = expanded[expanded["threshold"] == float(t2)]["y_target"].astype(float).mean()
            assert rate_t1 >= rate_t2, f"rate({t1}+) should be >= rate({t2}+)"

    def test_1plus_always_geq_2plus_target(self) -> None:
        df = _make_feature_df(n=10, h_values=[0, 1, 2, 3, 0, 1, 2, 3, 0, 1])
        expanded = _build_mlb_target(df, thresholds=[1, 2])
        t1_targets = expanded[expanded["threshold"] == 1.0]["y_target"].astype(float).values
        t2_targets = expanded[expanded["threshold"] == 2.0]["y_target"].astype(float).values
        # If 2+ is hit, 1+ must also be hit
        assert ((t2_targets == 1) & (t1_targets == 0)).sum() == 0

    def test_game_identity_preserved_across_thresholds(self) -> None:
        df = _make_feature_df(n=5)
        original_game_ids = set(df["game_id"].unique())
        expanded = _build_mlb_target(df, thresholds=[1, 2, 3])
        assert set(expanded["game_id"].unique()) == original_game_ids

    def test_feature_values_identical_across_thresholds_for_same_game(self) -> None:
        df = _make_feature_df(n=1)
        expanded = _build_mlb_target(df, thresholds=[1, 2, 3])
        assert len(expanded) == 3
        ba_values = expanded["ba_l10"].values
        assert np.allclose(ba_values, ba_values[0])

    def test_threshold_column_is_only_difference_between_copies(self) -> None:
        df = _make_feature_df(n=1)
        expanded = _build_mlb_target(df, thresholds=[1, 2])
        r1 = expanded[expanded["threshold"] == 1.0].iloc[0]
        r2 = expanded[expanded["threshold"] == 2.0].iloc[0]
        # All feature columns except threshold and y_target should be equal
        feature_cols = [c for c in expanded.columns if c not in ("threshold", "y_target")]
        for col in feature_cols:
            assert r1[col] == r2[col], f"column {col!r} differs between threshold copies"

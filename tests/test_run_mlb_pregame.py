"""
Tests for run_mlb_pregame.py (T-190 Step 1).

Scope:
  - _safe_int: pure function, numeric coercion and None handling
  - _build_mlb_feature_vector: column ordering, imputation, SP override injection
  - _NON_FEATURE_MLB / _MODEL_THRESHOLDS / _SP_OVERRIDE_FIELDS: constants match training
  - main() wrong sport guard: exits 1 if artifact.sport != mlb
  - main() no markets: writes empty pregame JSON, exits 0
  - main() happy path: writes pregame_mlb_YYYYMMDD.json with forecast records

Excluded (require real API/network):
  - Live Kalshi market fetch
  - Live MLB Stats API calls (SP overlay)
  - Real model inference (tested in test_train_mlb_model.py / T-183)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT  = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


# ---------------------------------------------------------------------------
# Module import helper
# ---------------------------------------------------------------------------


def _import_runner():
    sys.modules.pop("prediction_market_bot.run_mlb_pregame", None)
    import prediction_market_bot.run_mlb_pregame as runner
    return runner


# ---------------------------------------------------------------------------
# _safe_int
# ---------------------------------------------------------------------------


class TestSafeInt:
    def test_none_returns_none(self):
        fn = _import_runner()._safe_int
        assert fn(None) is None

    def test_nan_returns_none(self):
        fn = _import_runner()._safe_int
        assert fn(float("nan")) is None

    def test_valid_int_string(self):
        fn = _import_runner()._safe_int
        assert fn("660670") == 660670

    def test_valid_float_truncates(self):
        fn = _import_runner()._safe_int
        assert fn(123.9) == 123

    def test_non_numeric_returns_none(self):
        fn = _import_runner()._safe_int
        assert fn("abc") is None

    def test_zero(self):
        fn = _import_runner()._safe_int
        assert fn(0) == 0


# ---------------------------------------------------------------------------
# _build_mlb_feature_vector
# ---------------------------------------------------------------------------


def _make_row() -> pd.Series:
    return pd.Series({
        "player_id": 660670,
        "ba_l10": 0.280,
        "slg_l10": 0.450,
        "obp_l10": 0.380,
        "ops_l10": 0.830,
        "h_l10_mean": 1.0,
        "k_rate_l10": 0.22,
        "bb_rate_l10": 0.15,
        "hr_rate_l10": 0.03,
        "days_rest": 1,
        "b2b_flag": 0,
        "is_home_game": 1,
        "opp_sp_era_l5": 4.0,
        "opp_sp_k9_l5": 8.0,
        "opp_sp_bb9_l5": 3.0,
        "opp_sp_is_known": 1,
        "opp_runs_allowed_l10": 4.5,
        "park_factor_hits": 1.0,
    })


class TestBuildMLBFeatureVector:
    def test_known_value_preserved(self):
        fn = _import_runner()._build_mlb_feature_vector
        row = _make_row()
        X = fn(row, feature_names=["ba_l10", "days_rest"], col_medians=np.array([0.25, 1.0]))
        assert X.shape == (1, 2)
        assert X[0, 0] == pytest.approx(0.280)
        assert X[0, 1] == pytest.approx(1.0)

    def test_nan_imputed_with_median(self):
        fn = _import_runner()._build_mlb_feature_vector
        row = pd.Series({"col": np.nan})
        X = fn(row, feature_names=["col"], col_medians=np.array([0.300]))
        assert X[0, 0] == pytest.approx(0.300)

    def test_missing_column_treated_as_nan(self):
        fn = _import_runner()._build_mlb_feature_vector
        row = pd.Series({"ba_l10": 0.280})
        X = fn(row, feature_names=["ba_l10", "ops_l10"], col_medians=np.array([0.25, 0.75]))
        assert X[0, 0] == pytest.approx(0.280)
        assert X[0, 1] == pytest.approx(0.75)

    def test_output_shape(self):
        fn = _import_runner()._build_mlb_feature_vector
        n = 15
        X = fn(_make_row(), feature_names=[f"f{i}" for i in range(n)],
               col_medians=np.zeros(n))
        assert X.shape == (1, n)

    def test_sp_override_replaces_stale_row_value(self):
        fn = _import_runner()._build_mlb_feature_vector
        row = pd.Series({"opp_sp_era_l5": 5.0, "days_rest": 1})
        override = {"opp_sp_era_l5": 2.5, "opp_sp_k9_l5": 10.0,
                    "opp_sp_bb9_l5": 2.0, "opp_sp_is_known": 1.0}
        X = fn(row, feature_names=["opp_sp_era_l5", "days_rest"],
               col_medians=np.array([4.0, 1.0]), sp_override=override)
        assert X[0, 0] == pytest.approx(2.5)

    def test_no_sp_override_uses_row_value(self):
        fn = _import_runner()._build_mlb_feature_vector
        row = pd.Series({"opp_sp_era_l5": 5.0})
        X = fn(row, feature_names=["opp_sp_era_l5"], col_medians=np.array([4.0]),
               sp_override=None)
        assert X[0, 0] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestModelThresholds:
    def test_thresholds_are_1_and_2(self):
        runner = _import_runner()
        assert runner._MODEL_THRESHOLDS == frozenset({1, 2})

    def test_threshold_3_excluded(self):
        runner = _import_runner()
        assert 3 not in runner._MODEL_THRESHOLDS


class TestNonFeatureMLB:
    def test_player_id_excluded(self):
        assert "player_id" in _import_runner()._NON_FEATURE_MLB

    def test_h_excluded(self):
        assert "h" in _import_runner()._NON_FEATURE_MLB

    def test_y_target_excluded(self):
        assert "y_target" in _import_runner()._NON_FEATURE_MLB

    def test_threshold_excluded(self):
        assert "threshold" in _import_runner()._NON_FEATURE_MLB


class TestSpOverrideFields:
    def test_contains_expected_keys(self):
        runner = _import_runner()
        assert runner._SP_OVERRIDE_FIELDS == frozenset({
            "opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_sp_is_known"
        })


# ---------------------------------------------------------------------------
# Helpers for main() smoke tests
# ---------------------------------------------------------------------------


def _make_artifact() -> dict:
    pipe = MagicMock()
    pipe.predict_proba.return_value = np.array([[0.3, 0.55]])
    return {
        "pipelines": {1: pipe, 2: pipe},
        "feature_names": ["ba_l10", "days_rest"],
        "col_medians": np.array([0.25, 1.0]),
        "model_version": "mlb_v1_test",
        "thresholds": [1, 2],
        "sport": "mlb",
    }


def _make_feature_csv(tmp_path: Path) -> Path:
    from datetime import date, timedelta
    recent = (date.today() - timedelta(days=1)).isoformat()
    csv = tmp_path / "mlb_feature_matrix.csv"
    header = (
        "player_id,player_name,team_id,team_abbreviation,game_id,game_date,"
        "season,season_type,matchup,is_home_game,opponent_team_abbr,ab,h,"
        "doubles,triples,hr,rbi,bb,k,hbp,sf,snapshot_id,ingestion_run_id,"
        "ingested_at,temporal_cutoff,ba_l10,slg_l10,obp_l10,ops_l10,"
        "h_l10_mean,k_rate_l10,bb_rate_l10,hr_rate_l10,days_rest,b2b_flag,"
        "opp_runs_allowed_l10,opp_sp_era_l5,opp_sp_k9_l5,opp_sp_bb9_l5,"
        "opp_sp_is_known,park_factor_hits,feature_run_id,feature_version,"
        "train_test_label"
    )
    row = (
        f"660670,Juan Soto,147,NYY,717465,{recent},2024,Regular Season,"
        "NYY vs BOS,1,BOS,4,1,0,0,0,1,1,1,0,0,SNAP,IRD-001,"
        f"{recent}T12:00:00Z,{recent},0.280,0.450,0.380,0.830,"
        "1.0,0.22,0.15,0.03,1,0,"
        "4.5,4.0,8.0,3.0,"
        "1,1.0,FRD-001,1.0.0,"
        "train"
    )
    csv.write_text(f"{header}\n{row}\n")
    return csv


def _make_mock_market(ticker: str, player_name: str, threshold: int) -> MagicMock:
    m = MagicMock()
    m.ticker = ticker
    m.player_name = player_name
    m.threshold = threshold
    m.status = "active"
    m.has_live_quotes = True
    m.mid_price = 0.35
    m.vig = 0.08
    m.half_spread = 0.04
    return m


# ---------------------------------------------------------------------------
# main() — wrong sport guard
# ---------------------------------------------------------------------------


class TestMainWrongSportGuard:
    def test_exits_1_on_wrong_sport(self, tmp_path):
        runner = _import_runner()
        wrong_artifact = {**_make_artifact(), "sport": "nba"}
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", tmp_path / "pregame_mlb_20260624.json"),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient"),
        ):
            mock_jl.load.return_value = wrong_artifact
            with pytest.raises(SystemExit) as exc_info:
                runner.main()
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# main() — no markets → empty report, exit 0
# ---------------------------------------------------------------------------


class TestMainNoMarkets:
    def test_writes_empty_report_and_exits_0(self, tmp_path):
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mock_snap = MagicMock()
        mock_snap.markets = []

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client

            with pytest.raises(SystemExit) as exc_info:
                runner.main()

        assert exc_info.value.code == 0
        assert output_path.exists()
        report = json.loads(output_path.read_text())
        assert report["markets_fetched"] == 0
        assert report["forecasts"] == []
        assert report["sport"] == "mlb"


# ---------------------------------------------------------------------------
# main() — happy path smoke test
# ---------------------------------------------------------------------------


class TestMainHappyPath:
    def test_writes_pregame_json_with_forecast(self, tmp_path):
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mkt_h1 = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-1", "Juan Soto", threshold=1)
        mkt_h2 = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-2", "Juan Soto", threshold=2)

        mock_snap = MagicMock()
        mock_snap.markets = [mkt_h1, mkt_h2]

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client
            runner.main()

        assert output_path.exists()
        report = json.loads(output_path.read_text())
        assert report["sport"] == "mlb"
        assert report["players_matched"] == 1
        assert report["markets_logged"] == 2
        assert len(report["forecasts"]) == 2

        fc = report["forecasts"][0]
        assert fc["player_name"] == "Juan Soto"
        assert fc["player_id"] == 660670
        assert "p_estimate" in fc
        assert "kalshi_ticker" in fc
        assert "kalshi_threshold" in fc
        assert "edge" in fc
        assert "direction" in fc
        assert fc["direction"] in {"YES", "NO", "PASS"}

    def test_player_not_in_feature_csv_is_skipped(self, tmp_path):
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)  # only has Juan Soto
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mkt_unknown = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAXYZ99-1", "Unknown Player", threshold=1)

        mock_snap = MagicMock()
        mock_snap.markets = [mkt_unknown]

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client
            runner.main()

        report = json.loads(output_path.read_text())
        assert report["players_matched"] == 0
        assert report["markets_logged"] == 0
        assert report["forecasts"] == []

    def test_threshold_3_is_excluded(self, tmp_path):
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mkt_h3 = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-3", "Juan Soto", threshold=3)

        mock_snap = MagicMock()
        mock_snap.markets = [mkt_h3]

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client
            runner.main()

        report = json.loads(output_path.read_text())
        # h≥3 market for known player: matched but no forecast because t=3 excluded
        assert report["markets_logged"] == 0

    def test_forecast_keys_present(self, tmp_path):
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mkt = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-1", "Juan Soto", threshold=1)
        mock_snap = MagicMock()
        mock_snap.markets = [mkt]

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client
            runner.main()

        fc = json.loads(output_path.read_text())["forecasts"][0]
        required_keys = {
            "player_name", "player_id", "kalshi_ticker", "kalshi_threshold",
            "p_estimate", "mid_price", "edge", "direction", "model_version",
        }
        assert required_keys.issubset(fc.keys()), (
            f"Missing keys: {required_keys - fc.keys()}"
        )

    def test_ba_l10_shrunk_none_when_column_absent(self, tmp_path):
        # GG-105/APR-0025/ADR-0047: the fixture CSV predates ba_l10_shrunk.
        # This mirrors any pre-fix feature matrix still on disk post-deploy.
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")
        feature_csv = _make_feature_csv(tmp_path)
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mkt = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-1", "Juan Soto", threshold=1)
        mock_snap = MagicMock()
        mock_snap.markets = [mkt]

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client
            runner.main()

        fc = json.loads(output_path.read_text())["forecasts"][0]
        assert "ba_l10_shrunk" in fc
        assert fc["ba_l10_shrunk"] is None
        assert fc["ba_l10"] == pytest.approx(0.280, rel=1e-3)

    def test_ba_l10_shrunk_surfaced_when_column_present(self, tmp_path):
        # GG-105/APR-0025/ADR-0047: once the feature matrix carries
        # ba_l10_shrunk (post v1.1.0), it must surface into the forecast dict
        # for audit/backtest comparison (T1 does not consume it for gating).
        runner = _import_runner()
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"fake")

        from datetime import date, timedelta
        recent = (date.today() - timedelta(days=1)).isoformat()
        feature_csv = tmp_path / "mlb_feature_matrix.csv"
        header = (
            "player_id,player_name,team_id,team_abbreviation,game_id,game_date,"
            "season,season_type,matchup,is_home_game,opponent_team_abbr,ab,h,"
            "doubles,triples,hr,rbi,bb,k,hbp,sf,snapshot_id,ingestion_run_id,"
            "ingested_at,temporal_cutoff,ba_l10,ba_l10_shrunk,slg_l10,obp_l10,ops_l10,"
            "h_l10_mean,k_rate_l10,bb_rate_l10,hr_rate_l10,days_rest,b2b_flag,"
            "opp_runs_allowed_l10,opp_sp_era_l5,opp_sp_k9_l5,opp_sp_bb9_l5,"
            "opp_sp_is_known,park_factor_hits,feature_run_id,feature_version,"
            "train_test_label"
        )
        row = (
            f"660670,Juan Soto,147,NYY,717465,{recent},2024,Regular Season,"
            "NYY vs BOS,1,BOS,4,1,0,0,0,1,1,1,0,0,SNAP,IRD-001,"
            f"{recent}T12:00:00Z,{recent},0.280,0.2650,0.450,0.380,0.830,"
            "1.0,0.22,0.15,0.03,1,0,"
            "4.5,4.0,8.0,3.0,"
            "1,1.0,FRD-001,1.1.0,"
            "train"
        )
        feature_csv.write_text(f"{header}\n{row}\n")
        output_path = tmp_path / "pregame_mlb_20260624.json"

        mkt = _make_mock_market(
            "KXMLBHIT-26JUN241607NYYNYY-NYYAAJUDG7-1", "Juan Soto", threshold=1)
        mock_snap = MagicMock()
        mock_snap.markets = [mkt]

        mock_client = MagicMock()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        mock_client.fetch_player_points_markets.return_value = (True, mock_snap)

        with (
            patch.object(runner, "MODEL_PATH", model_path),
            patch.object(runner, "FEATURE_CSV", feature_csv),
            patch.object(runner, "LOG_DIR", tmp_path),
            patch.object(runner, "OUTPUT_PATH", output_path),
            patch("prediction_market_bot.run_mlb_pregame.joblib") as mock_jl,
            patch("prediction_market_bot.run_mlb_pregame.KalshiMarketClient") as MockClient,
            patch("prediction_market_bot.run_mlb_pregame.MLBIngestionClient"),
            patch("prediction_market_bot.run_mlb_pregame._build_live_sp_override",
                  return_value={}),
        ):
            mock_jl.load.return_value = _make_artifact()
            MockClient.from_env.return_value = mock_client
            runner.main()

        fc = json.loads(output_path.read_text())["forecasts"][0]
        assert fc["ba_l10_shrunk"] == pytest.approx(0.2650, rel=1e-3)
        assert fc["ba_l10"] == pytest.approx(0.280, rel=1e-3)

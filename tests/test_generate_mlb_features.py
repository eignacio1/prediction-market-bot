"""
Tests for scripts/generate_mlb_features.py (T-187A).

Scope:
  - Helper functions (season date range, cache paths)
  - _fetch_position_players (mocked HTTP)
  - main() in dry-run mode with fully mocked C1/C2 layer
  - BOT_C4_ACTIVE guard
  - Cache hit path

We do NOT test the real MLB Stats API endpoints here — that is left to
manual integration runs (T-187B requires a real CSV). Tests must pass
offline with no network access.
"""

from __future__ import annotations

import json
import os
import sys
import types
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Make sure the script is importable
_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import generate_mlb_features as gmf


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all file I/O to tmp_path so tests don't pollute repo."""
    cache_dir = tmp_path / "cache"
    output_csv = tmp_path / "mlb_feature_matrix.csv"
    log_path = tmp_path / "generate_features.jsonl"

    monkeypatch.setattr(gmf, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(gmf, "OUTPUT_CSV", output_csv)
    monkeypatch.setattr(gmf, "LOG_PATH", log_path)

    cache_dir.mkdir(parents=True, exist_ok=True)

    return {"cache_dir": cache_dir, "output_csv": output_csv, "log_path": log_path, "tmp": tmp_path}


@pytest.fixture()
def sample_batter_df() -> pd.DataFrame:
    return pd.DataFrame({
        "player_id": [660670, 660670, 660670],
        "player_name": ["Juan Soto"] * 3,
        "team_id": [147, 147, 147],
        "team_abbreviation": ["NYY"] * 3,
        "game_id": [717465, 717466, 717467],
        "game_date": ["2024-04-01", "2024-04-02", "2024-04-03"],
        "season": ["2024"] * 3,
        "season_type": ["Regular Season"] * 3,
        "matchup": ["NYY vs BOS"] * 3,
        "opponent_team_abbr": ["BOS"] * 3,
        "is_home_game": [1, 0, 1],
        "ab": [4, 3, 4],
        "h": [1, 2, 0],
        "doubles": [0, 1, 0],
        "triples": [0, 0, 0],
        "hr": [0, 0, 0],
        "rbi": [1, 2, 0],
        "bb": [1, 0, 1],
        "k": [1, 1, 2],
        "hbp": [0, 0, 0],
        "sf": [0, 0, 0],
        "snapshot_id": ["SNAP"] * 3,
        "ingestion_run_id": ["IRD-001"] * 3,
        "ingested_at": ["2024-04-01T12:00:00Z", "2024-04-02T12:00:00Z", "2024-04-03T12:00:00Z"],
    })


@pytest.fixture()
def sample_feature_df() -> pd.DataFrame:
    return pd.DataFrame({
        "player_id": [660670] * 3,
        "player_name": ["Juan Soto"] * 3,
        "game_date": ["2024-04-01", "2024-04-02", "2024-04-03"],
        "season": ["2024"] * 3,
        "season_type": ["Regular Season"] * 3,
        "ba_l10": [0.280, 0.281, 0.282],
        "slg_l10": [0.450, 0.452, 0.448],
        "obp_l10": [0.380, 0.382, 0.384],
        "ops_l10": [0.830, 0.833, 0.832],
        "h_l10_mean": [1.0, 1.1, 1.05],
        "k_rate_l10": [0.22, 0.23, 0.22],
        "bb_rate_l10": [0.15, 0.14, 0.15],
        "hr_rate_l10": [0.03, 0.03, 0.02],
        "days_rest": [1, 1, 1],
        "b2b_flag": [0, 0, 0],
        "is_home_game": [1, 0, 1],
        "opp_sp_era_l5": [4.0, 3.5, 4.2],
        "opp_sp_k9_l5": [8.0, 9.0, 7.5],
        "opp_sp_bb9_l5": [3.0, 2.5, 3.2],
        "opp_sp_is_known": [1, 1, 1],
        "opp_runs_allowed_l10": [4.5, 4.8, 4.2],
        "park_factor_hits": [1.0, 0.95, 1.0],
        "y_target": [1, 1, 0],
        "h": [1, 2, 0],
        "train_test_label": [None, None, None],
        "temporal_cutoff": [None, None, None],
        "feature_run_id": ["FRD-001"] * 3,
        "feature_version": ["1.0.0"] * 3,
    })


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestSeasonDateRange:
    def test_2024_range(self):
        start, end = gmf._season_date_range(2024)
        assert start == "2024-03-20"
        assert end == "2024-10-01"

    def test_2025_range(self):
        start, end = gmf._season_date_range(2025)
        assert start == "2025-03-20"
        assert end == "2025-10-01"

    def test_2026_starts_march(self):
        start, end = gmf._season_date_range(2026)
        assert start == "2026-03-26"
        # end = today — just check it's a valid date string
        date.fromisoformat(end)

    def test_2026_end_is_today_or_earlier(self):
        _, end = gmf._season_date_range(2026)
        assert end <= date.today().isoformat()


class TestCachePaths:
    def test_players_cache_path_contains_season(self):
        p = gmf._players_cache_path(2025)
        assert "2025" in str(p)
        assert p.suffix == ".json"

    def test_batter_cache_path_parquet(self):
        p = gmf._batter_cache_path(2024)
        assert p.suffix == ".parquet"

    def test_pitcher_cache_path_parquet(self):
        p = gmf._pitcher_cache_path(2024)
        assert p.suffix == ".parquet"
        assert "pitcher" in str(p)

    def test_games_cache_path_parquet(self):
        p = gmf._games_cache_path(2024)
        assert p.suffix == ".parquet"

    def test_starters_cache_path_json(self):
        p = gmf._starters_cache_path(2024)
        assert p.suffix == ".json"


class TestUtcNow:
    def test_format_is_iso_with_z(self):
        ts = gmf._utc_now()
        assert ts.endswith("Z")
        # Should parse as ISO-like without error
        assert len(ts) >= 20


# ---------------------------------------------------------------------------
# _fetch_position_players (mocked HTTP)
# ---------------------------------------------------------------------------


class TestFetchPositionPlayers:
    def _make_resp(self, people: list[dict]) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"people": people}
        resp.raise_for_status.return_value = None
        return resp

    def test_filters_pitchers(self):
        people = [
            {"id": 1, "fullName": "Aaron Judge", "primaryPosition": {"type": "Outfielder", "abbreviation": "CF"}},
            {"id": 2, "fullName": "Gerrit Cole", "primaryPosition": {"type": "Pitcher", "abbreviation": "P"}},
            {"id": 3, "fullName": "Ohtani", "primaryPosition": {"type": "Pitcher", "abbreviation": "TWP"}},
        ]
        with patch("generate_mlb_features.requests") as mock_req:
            mock_req.get.return_value = self._make_resp(people)
            result = gmf._fetch_position_players(2025)
        ids = [p["player_id"] for p in result]
        assert 1 in ids   # position player
        assert 2 not in ids  # pitcher excluded

    def test_returns_player_id_and_name(self):
        people = [
            {"id": 99, "fullName": "Test Player", "primaryPosition": {"type": "FirstBaseman", "abbreviation": "1B"}},
        ]
        with patch("generate_mlb_features.requests") as mock_req:
            mock_req.get.return_value = self._make_resp(people)
            result = gmf._fetch_position_players(2025)
        assert len(result) == 1
        assert result[0]["player_id"] == 99
        assert result[0]["full_name"] == "Test Player"

    def test_http_error_returns_empty(self):
        with patch("generate_mlb_features.requests") as mock_req:
            mock_req.get.side_effect = Exception("connection refused")
            result = gmf._fetch_position_players(2025)
        assert result == []

    def test_skips_missing_id(self):
        people = [
            {"fullName": "No ID Player", "primaryPosition": {"type": "Outfielder", "abbreviation": "LF"}},
        ]
        with patch("generate_mlb_features.requests") as mock_req:
            mock_req.get.return_value = self._make_resp(people)
            result = gmf._fetch_position_players(2025)
        assert result == []


# ---------------------------------------------------------------------------
# Cache hit/miss tests
# ---------------------------------------------------------------------------


class TestCacheHitMiss:
    def test_players_cache_hit_skips_api(self, tmp_dirs):
        cache = tmp_dirs["cache_dir"] / "players_2024.json"
        expected = [{"player_id": 123, "full_name": "Cached Player"}]
        cache.write_text(json.dumps(expected))

        with patch("generate_mlb_features._fetch_position_players") as mock_fetch:
            result = gmf._load_or_fetch_players(2024)

        mock_fetch.assert_not_called()
        assert result == expected

    def test_players_cache_miss_calls_api(self, tmp_dirs):
        players = [{"player_id": 456, "full_name": "Fresh Player"}]
        with patch("generate_mlb_features._fetch_position_players", return_value=players):
            result = gmf._load_or_fetch_players(2024)

        assert result == players
        cache = tmp_dirs["cache_dir"] / "players_2024.json"
        assert cache.exists()

    def test_batter_cache_hit_skips_client(self, tmp_dirs, sample_batter_df):
        pytest.importorskip("pyarrow", reason="pyarrow required for parquet cache tests")
        cache = tmp_dirs["cache_dir"] / "batter_logs_2024.parquet"
        sample_batter_df.to_parquet(cache, index=False)

        mock_client = MagicMock()
        result = gmf._load_or_fetch_batter_logs(2024, [], mock_client, "SID-001")

        mock_client.fetch_batter_game_logs_bulk.assert_not_called()
        assert len(result) == len(sample_batter_df)

    def test_starters_cache_hit(self, tmp_dirs):
        starters = {"717465": {"home_sp_id": 100, "away_sp_id": 200}}
        cache = tmp_dirs["cache_dir"] / "starters_2024.json"
        cache.write_text(json.dumps(starters))

        mock_client = MagicMock()
        result = gmf._load_or_fetch_starters(2024, ["2024-04-01"], mock_client, "SID-001")

        mock_client.fetch_game_starters.assert_not_called()
        assert 717465 in result  # keys are converted to int


# ---------------------------------------------------------------------------
# BOT_C4_ACTIVE guard
# ---------------------------------------------------------------------------


class TestBotC4ActiveGuard:
    def test_exits_when_c4_active(self, monkeypatch, tmp_dirs):
        monkeypatch.setenv("BOT_C4_ACTIVE", "true")
        with pytest.raises(SystemExit) as exc_info:
            gmf.main(seasons=[2024], dry_run=True)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# main() dry-run integration
# ---------------------------------------------------------------------------


class TestMainDryRun:
    """Run main() with fully mocked C1/C2 layer — no network, no file writes."""

    def _make_mock_client(self, batter_df, games_df, starters_dict=None, pitcher_df=None):
        client = MagicMock()
        client.fetch_batter_game_logs_bulk.return_value = (True, batter_df)
        client.fetch_completed_games.return_value = (True, games_df)
        client.fetch_game_starters.return_value = (True, starters_dict or {})
        client.fetch_pitcher_game_logs_bulk.return_value = (True, pitcher_df if pitcher_df is not None else pd.DataFrame())
        return client

    def test_dry_run_no_output_csv(
        self,
        tmp_dirs,
        sample_batter_df,
        sample_feature_df,
        monkeypatch,
    ):
        """Dry run must not write the output CSV."""
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)

        games_df = pd.DataFrame({
            "game_id": [1], "game_date": ["2024-04-01"],
            "home_team_id": [147], "home_team_abbr": ["NYY"],
            "away_team_id": [111], "away_team_abbr": ["BOS"],
            "home_runs": [5], "away_runs": [3],
        })

        mock_client = self._make_mock_client(sample_batter_df, games_df)
        mock_feature_store = MagicMock()
        mock_feature_store.compute_features_bulk.return_value = (True, sample_feature_df)
        mock_feature_store.assign_train_test_labels.return_value = (True, sample_feature_df)

        with (
            patch("generate_mlb_features.MLBIngestionClient", return_value=mock_client),
            patch("generate_mlb_features.MLBFeatureStore", return_value=mock_feature_store),
            patch("generate_mlb_features._load_or_fetch_players", return_value=[
                {"player_id": 660670, "full_name": "Juan Soto"}
            ]),
            patch("generate_mlb_features._load_or_fetch_batter_logs", return_value=sample_batter_df),
            patch("generate_mlb_features._load_or_fetch_completed_games", return_value=games_df),
            patch("generate_mlb_features._load_or_fetch_starters", return_value={}),
            patch("generate_mlb_features._load_or_fetch_pitcher_logs", return_value=pd.DataFrame()),
        ):
            gmf.main(seasons=[2024], dry_run=True)

        assert not tmp_dirs["output_csv"].exists()

    def test_normal_run_writes_csv(
        self,
        tmp_dirs,
        sample_batter_df,
        sample_feature_df,
        monkeypatch,
    ):
        """Non-dry-run must write the CSV."""
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)

        games_df = pd.DataFrame({
            "game_id": [1], "game_date": ["2024-04-01"],
            "home_team_id": [147], "home_team_abbr": ["NYY"],
            "away_team_id": [111], "away_team_abbr": ["BOS"],
            "home_runs": [5], "away_runs": [3],
        })

        with (
            patch("generate_mlb_features.MLBIngestionClient"),
            patch("generate_mlb_features.MLBFeatureStore"),
            patch("generate_mlb_features._load_or_fetch_players", return_value=[
                {"player_id": 660670, "full_name": "Juan Soto"}
            ]),
            patch("generate_mlb_features._load_or_fetch_batter_logs", return_value=sample_batter_df),
            patch("generate_mlb_features._load_or_fetch_completed_games", return_value=games_df),
            patch("generate_mlb_features._load_or_fetch_starters", return_value={}),
            patch("generate_mlb_features._load_or_fetch_pitcher_logs", return_value=pd.DataFrame()),
            patch("generate_mlb_features.MLBPitcherStatsStore"),
            patch("generate_mlb_features.MLBTeamStatsStore") as MockTSS,
            patch("generate_mlb_features.MLBFeatureStore") as MockFS,
        ):
            mock_fs_instance = MagicMock()
            mock_fs_instance.compute_features_bulk.return_value = (True, sample_feature_df)
            mock_fs_instance.assign_train_test_labels.return_value = (True, sample_feature_df)
            MockFS.return_value = mock_fs_instance

            mock_tss = MagicMock()
            mock_tss.__len__ = MagicMock(return_value=2)
            MockTSS.build_from_games.return_value = mock_tss

            gmf.main(seasons=[2024], dry_run=False)

        assert tmp_dirs["output_csv"].exists()

    def test_no_data_exits_nonzero(self, tmp_dirs, monkeypatch):
        """If no seasons produce data, main() must sys.exit(1)."""
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)

        with (
            patch("generate_mlb_features.MLBIngestionClient"),
            patch("generate_mlb_features.MLBFeatureStore"),
            patch("generate_mlb_features._load_or_fetch_players", return_value=[]),
        ):
            with pytest.raises(SystemExit) as exc_info:
                gmf.main(seasons=[2024], dry_run=True)
        assert exc_info.value.code == 1

    def test_multiple_seasons_combined(self, tmp_dirs, sample_batter_df, sample_feature_df, monkeypatch):
        """Multiple seasons should concatenate into a single CSV."""
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)

        # Return the same small feature_df for each season
        with (
            patch("generate_mlb_features.MLBIngestionClient"),
            patch("generate_mlb_features._load_or_fetch_players", return_value=[
                {"player_id": 660670, "full_name": "Juan Soto"}
            ]),
            patch("generate_mlb_features._load_or_fetch_batter_logs", return_value=sample_batter_df),
            patch("generate_mlb_features._load_or_fetch_completed_games", return_value=pd.DataFrame()),
            patch("generate_mlb_features._load_or_fetch_starters", return_value={}),
            patch("generate_mlb_features._load_or_fetch_pitcher_logs", return_value=pd.DataFrame()),
            patch("generate_mlb_features.MLBPitcherStatsStore"),
            patch("generate_mlb_features.MLBTeamStatsStore"),
            patch("generate_mlb_features.MLBFeatureStore") as MockFS,
        ):
            mock_fs_instance = MagicMock()
            # Return a 3-row df per season call
            mock_fs_instance.compute_features_bulk.return_value = (True, sample_feature_df)
            mock_fs_instance.assign_train_test_labels.return_value = (True, sample_feature_df)
            MockFS.return_value = mock_fs_instance

            gmf.main(seasons=[2024, 2025], dry_run=False)

        df = pd.read_csv(tmp_dirs["output_csv"])
        # 3 rows × 2 seasons = 6 rows
        assert len(df) == 6


_GOLDEN_DEFAULT_SHA = "7ea0e37659be4d12b862c2b79a7040cf2da210b9b8a11009f397a207612bfcfa"


class TestPostseasonOptIn:
    """D6(b): postseason is additive; the default regular-season path is unchanged."""

    def _run(self, tmp_dirs, sample_batter_df, sample_feature_df, include):
        games_df = pd.DataFrame({
            "game_id": [1], "game_date": ["2024-04-01"],
            "home_team_id": [147], "home_team_abbr": ["NYY"],
            "away_team_id": [111], "away_team_abbr": ["BOS"],
            "home_runs": [5], "away_runs": [3],
        })
        post_b = sample_batter_df.copy()
        post_b["game_id"] = post_b["game_id"] + 900000
        post_b["season_type"] = "Postseason"
        fs = MagicMock()
        fs.compute_features_bulk.return_value = (True, sample_feature_df)
        fs.assign_train_test_labels.return_value = (True, sample_feature_df)
        post_loader = MagicMock(return_value=post_b)
        post_games = MagicMock(return_value=pd.DataFrame())
        with (
            patch("generate_mlb_features.MLBIngestionClient", return_value=MagicMock()),
            patch("generate_mlb_features.MLBFeatureStore", return_value=fs),
            patch("generate_mlb_features._load_or_fetch_players",
                  return_value=[{"player_id": 660670, "full_name": "Juan Soto"}]),
            patch("generate_mlb_features._load_or_fetch_batter_logs", return_value=sample_batter_df),
            patch("generate_mlb_features._load_or_fetch_batter_logs_post", post_loader),
            patch("generate_mlb_features._load_or_fetch_completed_games", return_value=games_df),
            patch("generate_mlb_features._load_or_fetch_completed_games_post", post_games),
            patch("generate_mlb_features._load_or_fetch_starters", return_value={}),
            patch("generate_mlb_features._load_or_fetch_pitcher_logs", return_value=pd.DataFrame()),
        ):
            gmf.main(seasons=[2024], dry_run=False, include_postseason=include)
        return fs, post_loader, post_games

    def test_default_output_unchanged(self, tmp_dirs, sample_batter_df, sample_feature_df, monkeypatch):
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)
        fs, post_loader, post_games = self._run(tmp_dirs, sample_batter_df, sample_feature_df, False)
        post_loader.assert_not_called()
        post_games.assert_not_called()
        sent = fs.compute_features_bulk.call_args.args[0] if fs.compute_features_bulk.call_args.args \
            else next(iter(fs.compute_features_bulk.call_args.kwargs.values()))
        pd.testing.assert_frame_equal(sent, sample_batter_df)
        # Golden digest captured from the PRE-change script (git stash of the edits) for these inputs
        # - the regular-season default path is byte-for-byte unchanged.
        import hashlib
        out = tmp_dirs["output_csv"].read_bytes()
        again = self._golden_bytes(tmp_dirs, sample_batter_df, sample_feature_df)
        assert out == again
        assert hashlib.sha256(out).hexdigest() == _GOLDEN_DEFAULT_SHA

    def _golden_bytes(self, tmp_dirs, sample_batter_df, sample_feature_df):
        self._run(tmp_dirs, sample_batter_df, sample_feature_df, False)
        return tmp_dirs["output_csv"].read_bytes()

    def test_flag_appends_postseason_rows(self, tmp_dirs, sample_batter_df, sample_feature_df, monkeypatch):
        monkeypatch.delenv("BOT_C4_ACTIVE", raising=False)
        fs, post_loader, _ = self._run(tmp_dirs, sample_batter_df, sample_feature_df, True)
        post_loader.assert_called_once()
        sent = fs.compute_features_bulk.call_args.args[0] if fs.compute_features_bulk.call_args.args \
            else next(iter(fs.compute_features_bulk.call_args.kwargs.values()))
        assert len(sent) == 2 * len(sample_batter_df)
        assert set(sent["season_type"]) >= {"Postseason"}

    def test_postseason_range_and_cache_paths_separate(self):
        assert gmf._batter_post_cache_path(2025) != gmf._batter_cache_path(2025)
        assert gmf._games_post_cache_path(2025) != gmf._games_cache_path(2025)
        assert gmf._postseason_date_range(2025) == ("2025-09-25", "2025-11-15")

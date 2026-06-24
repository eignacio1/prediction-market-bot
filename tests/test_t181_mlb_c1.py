"""Tests for T-181: MLB C1 ingestion module.

Coverage:
  - MLBIngestionClient: init, batter game log, pitcher game log, bulk variants,
    game starters, completed games
  - MLBTeamStatsStore: init, add, temporal integrity, rolling stats, cache
  - MLBPitcherStatsStore: init, add, ERA/K9/BB9 rolling queries, temporal integrity,
    relief filtering, cache

All tests are pure unit tests — no live HTTP calls. requests.get is mocked
throughout via the _patch_requests fixture.
"""
from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (
    MLBIngestionClient,
    _MLB_BATTER_COLUMNS,
    _MLB_PITCHER_COLUMNS,
    _FALLBACK_TEAM_ABBR,
)
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import MLBTeamStatsStore
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import MLBPitcherStatsStore


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_TEST_TEAM_MAP = {147: "NYY", 116: "DET", 113: "CIN", 135: "SD", 143: "PHI", 144: "ATL"}


def _make_logger() -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = True
    return logger


def _make_client(team_map=None) -> tuple[MLBIngestionClient, MagicMock]:
    """Return (client, logger) with a known team map so init skips live HTTP."""
    logger = _make_logger()
    client = MLBIngestionClient(
        logger=logger,
        snapshot_id="TEST-SNAP-001",
        _team_abbr_map=team_map or _TEST_TEAM_MAP,
    )
    return client, logger


def _mock_resp(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


def _batter_api_response(
    player_id: int = 592518,
    player_name: str = "Manny Machado",
    team_id: int = 135,
    opp_id: int = 144,
    is_home: bool = True,
    n_games: int = 3,
) -> dict:
    splits = []
    for i in range(n_games):
        splits.append({
            "season": "2026",
            "date": f"2026-04-{10 + i:02d}",
            "gameType": "R",
            "isHome": is_home,
            "player": {"id": player_id, "fullName": player_name},
            "team": {"id": team_id, "name": "San Diego Padres"},
            "opponent": {"id": opp_id, "name": "Atlanta Braves"},
            "game": {"gamePk": 800000 + i},
            "stat": {
                "atBats": 4,
                "hits": 2,
                "doubles": 0,
                "triples": 0,
                "homeRuns": 1,
                "rbi": 2,
                "baseOnBalls": 1,
                "strikeOuts": 1,
                "hitByPitch": 0,
                "sacFlies": 0,
            },
        })
    return {"stats": [{"splits": splits}]}


def _pitcher_api_response(
    player_id: int = 621244,
    player_name: str = "Corbin Burnes",
    n_starts: int = 3,
    n_relief: int = 1,
) -> dict:
    splits = []
    for i in range(n_starts):
        splits.append({
            "season": "2026",
            "date": f"2026-04-{7 * (i + 1):02d}",
            "gameType": "R",
            "isHome": True,
            "player": {"id": player_id, "fullName": player_name},
            "team": {"id": 113, "name": "Cincinnati Reds"},
            "opponent": {"id": 116, "name": "Detroit Tigers"},
            "game": {"gamePk": 900000 + i},
            "stat": {
                "inningsPitched": "6.0",
                "hits": 5,
                "earnedRuns": 2,
                "baseOnBalls": 2,
                "strikeOuts": 8,
                "homeRuns": 1,
                "gamesStarted": 1,
                "gamesPitched": 1,
            },
        })
    for j in range(n_relief):
        splits.append({
            "season": "2026",
            "date": f"2026-05-{5 + j:02d}",
            "gameType": "R",
            "isHome": False,
            "player": {"id": player_id, "fullName": player_name},
            "team": {"id": 113, "name": "Cincinnati Reds"},
            "opponent": {"id": 144, "name": "Atlanta Braves"},
            "game": {"gamePk": 950000 + j},
            "stat": {
                "inningsPitched": "1.2",
                "hits": 1,
                "earnedRuns": 0,
                "baseOnBalls": 0,
                "strikeOuts": 2,
                "homeRuns": 0,
                "gamesStarted": 0,
                "gamesPitched": 1,
            },
        })
    return {"stats": [{"splits": splits}]}


def _starters_api_response() -> dict:
    return {
        "dates": [{
            "date": "2026-06-23",
            "games": [{
                "gamePk": 12345,
                "teams": {
                    "home": {
                        "team": {"id": 113},
                        "probablePitcher": {"id": 686730, "fullName": "Carson Spiers"},
                    },
                    "away": {
                        "team": {"id": 116},
                        "probablePitcher": {"id": 543135, "fullName": "Nathan Eovaldi"},
                    },
                },
                "venue": {"id": 2602, "name": "Great American Ball Park"},
            }]
        }]
    }


def _completed_games_response() -> dict:
    return {
        "dates": [{
            "date": "2026-06-20",
            "games": [
                {
                    "gamePk": 77001,
                    "status": {"abstractGameState": "Final"},
                    "teams": {
                        "home": {"team": {"id": 147}, "score": 5},
                        "away": {"team": {"id": 116}, "score": 3},
                    },
                },
                {
                    "gamePk": 77002,
                    "status": {"abstractGameState": "Live"},  # not Final — must be excluded
                    "teams": {
                        "home": {"team": {"id": 113}, "score": None},
                        "away": {"team": {"id": 135}, "score": None},
                    },
                },
            ]
        }]
    }


# ---------------------------------------------------------------------------
# MLBIngestionClient — init
# ---------------------------------------------------------------------------

class TestMLBIngestionClientInit:
    def test_uses_provided_team_map(self):
        client, _ = _make_client()
        assert client._team_abbr_map[147] == "NYY"

    def test_team_abbr_lookup_known(self):
        client, _ = _make_client()
        assert client._team_abbr(147) == "NYY"

    def test_team_abbr_lookup_fallback(self):
        client, _ = _make_client()
        assert client._team_abbr(9999) == "T9999"

    def test_snapshot_id_stored(self):
        client, _ = _make_client()
        assert client._snapshot_id == "TEST-SNAP-001"

    def test_build_team_abbr_map_live_fallback(self):
        """If requests.get raises, _build_team_abbr_map falls back to _FALLBACK_TEAM_ABBR."""
        logger = _make_logger()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mock_get:
            mock_get.side_effect = Exception("network error")
            client = MLBIngestionClient(logger=logger, snapshot_id="SNAP-TEST")
        assert client._team_abbr_map == _FALLBACK_TEAM_ABBR

    def test_build_team_abbr_map_live_success(self):
        """Live team map is used when the /teams endpoint succeeds."""
        logger = _make_logger()
        mock_resp = _mock_resp({"teams": [{"id": 999, "abbreviation": "TST"}]})
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mock_get:
            mock_get.return_value = mock_resp
            client = MLBIngestionClient(logger=logger, snapshot_id="SNAP-TEST")
        assert client._team_abbr_map == {999: "TST"}


# ---------------------------------------------------------------------------
# MLBIngestionClient — fetch_batter_game_log
# ---------------------------------------------------------------------------

class TestFetchBatterGameLog:
    def test_returns_true_and_nonempty_df_on_success(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(n_games=5))
            ok, df = client.fetch_batter_game_log(592518, 2026)
        assert ok is True
        assert not df.empty
        assert len(df) == 5

    def test_output_columns_match_contract(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response())
            _, df = client.fetch_batter_game_log(592518, 2026)
        assert list(df.columns) == _MLB_BATTER_COLUMNS

    def test_stat_values_mapped_correctly(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(n_games=1))
            _, df = client.fetch_batter_game_log(592518, 2026)
        row = df.iloc[0]
        assert row["ab"] == 4
        assert row["h"] == 2
        assert row["hr"] == 1
        assert row["rbi"] == 2
        assert row["bb"] == 1
        assert row["k"] == 1

    def test_is_home_game_flag(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(is_home=True, n_games=1))
            _, df_home = client.fetch_batter_game_log(1, 2026)
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(is_home=False, n_games=1))
            _, df_away = client.fetch_batter_game_log(1, 2026)
        assert df_home.iloc[0]["is_home_game"] == 1
        assert df_away.iloc[0]["is_home_game"] == 0

    def test_matchup_format_home(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(
                team_id=135, opp_id=144, is_home=True, n_games=1
            ))
            _, df = client.fetch_batter_game_log(1, 2026)
        assert df.iloc[0]["matchup"] == "SD vs. ATL"

    def test_matchup_format_away(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(
                team_id=135, opp_id=144, is_home=False, n_games=1
            ))
            _, df = client.fetch_batter_game_log(1, 2026)
        assert df.iloc[0]["matchup"] == "SD @ ATL"

    def test_game_date_is_date_type(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(n_games=1))
            _, df = client.fetch_batter_game_log(1, 2026)
        assert isinstance(df.iloc[0]["game_date"], date)

    def test_returns_true_empty_df_on_no_splits(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp({"stats": [{"splits": []}]})
            ok, df = client.fetch_batter_game_log(1, 2026)
        assert ok is True
        assert df.empty
        assert list(df.columns) == _MLB_BATTER_COLUMNS

    def test_returns_false_empty_df_on_http_error(self):
        client, _ = _make_client()
        import requests as req_mod
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.time.sleep"):
                mg.side_effect = req_mod.ConnectionError("network down")
                ok, df = client.fetch_batter_game_log(1, 2026)
        assert ok is False
        assert df.empty

    def test_snapshot_id_in_output(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(n_games=1))
            _, df = client.fetch_batter_game_log(1, 2026)
        assert df.iloc[0]["snapshot_id"] == "TEST-SNAP-001"

    def test_season_type_regular(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(n_games=1))
            _, df = client.fetch_batter_game_log(1, 2026)
        assert df.iloc[0]["season_type"] == "Regular Season"

    def test_logger_called_on_success(self):
        client, logger = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_batter_api_response(n_games=2))
            client.fetch_batter_game_log(1, 2026, session_id="S-TEST")
        event_types = [c.args[1] for c in logger.log.call_args_list]
        assert "batter_game_log_fetch_start" in event_types
        assert "batter_game_log_fetch_complete" in event_types

    def test_logger_called_on_error(self):
        client, logger = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            import requests as req_mod
            http_err = req_mod.HTTPError(response=MagicMock(status_code=500))
            mg.side_effect = http_err
            client.fetch_batter_game_log(1, 2026)
        event_types = [c.args[1] for c in logger.log.call_args_list]
        assert "batter_game_log_fetch_error" in event_types


# ---------------------------------------------------------------------------
# MLBIngestionClient — fetch_pitcher_game_log
# ---------------------------------------------------------------------------

class TestFetchPitcherGameLog:
    def test_returns_true_and_nonempty_df(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_pitcher_api_response(n_starts=3, n_relief=0))
            ok, df = client.fetch_pitcher_game_log(621244, 2026)
        assert ok is True
        assert len(df) == 3

    def test_output_columns_match_contract(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_pitcher_api_response(n_starts=1, n_relief=0))
            _, df = client.fetch_pitcher_game_log(1, 2026)
        assert list(df.columns) == _MLB_PITCHER_COLUMNS

    def test_is_start_flag_starter(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_pitcher_api_response(n_starts=1, n_relief=0))
            _, df = client.fetch_pitcher_game_log(1, 2026)
        assert df.iloc[0]["is_start"] == 1

    def test_is_start_flag_relief(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_pitcher_api_response(n_starts=0, n_relief=1))
            _, df = client.fetch_pitcher_game_log(1, 2026)
        assert df.iloc[0]["is_start"] == 0

    def test_stat_values_mapped(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_pitcher_api_response(n_starts=1, n_relief=0))
            _, df = client.fetch_pitcher_game_log(1, 2026)
        row = df.iloc[0]
        assert row["ip"] == 6.0
        assert row["er"] == 2
        assert row["k"] == 8
        assert row["bb"] == 2
        assert row["h_allowed"] == 5
        assert row["hr_allowed"] == 1

    def test_mixed_starts_and_relief_in_one_log(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_pitcher_api_response(n_starts=2, n_relief=1))
            ok, df = client.fetch_pitcher_game_log(1, 2026)
        assert ok is True
        assert len(df) == 3
        assert df["is_start"].sum() == 2

    def test_returns_false_on_http_failure(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            import requests as req_mod
            mg.side_effect = req_mod.ConnectionError("down")
            ok, df = client.fetch_pitcher_game_log(1, 2026)
        assert ok is False
        assert df.empty

    def test_returns_true_empty_on_no_splits(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp({"stats": [{"splits": []}]})
            ok, df = client.fetch_pitcher_game_log(1, 2026)
        assert ok is True
        assert df.empty


# ---------------------------------------------------------------------------
# MLBIngestionClient — bulk variants
# ---------------------------------------------------------------------------

class TestFetchBulk:
    def test_batter_bulk_concatenates(self):
        client, _ = _make_client()
        resp = _mock_resp(_batter_api_response(n_games=2))
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = resp
            ok, df = client.fetch_batter_game_logs_bulk([101, 102], 2026)
        assert ok is True
        assert len(df) == 4  # 2 players × 2 games

    def test_batter_bulk_partial_failure_returns_false(self):
        client, _ = _make_client()
        import requests as req_mod

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail ALL retries for player 1 (MAX_RETRIES=3 → calls 1-3 fail)
            if call_count <= 3:
                raise req_mod.ConnectionError("fail")
            return _mock_resp(_batter_api_response(n_games=1))

        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.time.sleep"):
                mg.side_effect = side_effect
                ok, df = client.fetch_batter_game_logs_bulk([101, 102], 2026)
        assert ok is False
        assert len(df) == 1  # second player's data still returned

    def test_pitcher_bulk_concatenates(self):
        client, _ = _make_client()
        resp = _mock_resp(_pitcher_api_response(n_starts=1, n_relief=0))
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = resp
            ok, df = client.fetch_pitcher_game_logs_bulk([201, 202, 203], 2026)
        assert ok is True
        assert len(df) == 3  # 3 pitchers × 1 game each

    def test_batter_bulk_empty_player_list(self):
        client, _ = _make_client()
        ok, df = client.fetch_batter_game_logs_bulk([], 2026)
        assert ok is True
        assert df.empty


# ---------------------------------------------------------------------------
# MLBIngestionClient — fetch_game_starters
# ---------------------------------------------------------------------------

class TestFetchGameStarters:
    def test_returns_true_and_dict_on_success(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_starters_api_response())
            ok, starters = client.fetch_game_starters("2026-06-23")
        assert ok is True
        assert 12345 in starters

    def test_starter_sp_fields_present(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_starters_api_response())
            _, starters = client.fetch_game_starters("2026-06-23")
        entry = starters[12345]
        assert entry["home_sp_id"] == 686730
        assert entry["home_sp_name"] == "Carson Spiers"
        assert entry["away_sp_id"] == 543135
        assert entry["venue_id"] == 2602

    def test_home_away_team_abbr_populated(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_starters_api_response())
            _, starters = client.fetch_game_starters("2026-06-23")
        entry = starters[12345]
        assert entry["home_team_abbr"] == "CIN"
        assert entry["away_team_abbr"] == "DET"

    def test_returns_false_on_http_error(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            import requests as req_mod
            mg.side_effect = req_mod.ConnectionError("down")
            ok, starters = client.fetch_game_starters("2026-06-23")
        assert ok is False
        assert starters == {}

    def test_returns_empty_dict_on_no_games(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp({"dates": []})
            ok, starters = client.fetch_game_starters("2026-01-01")
        assert ok is True
        assert starters == {}

    def test_logger_called_on_success(self):
        client, logger = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_starters_api_response())
            client.fetch_game_starters("2026-06-23")
        event_types = [c.args[1] for c in logger.log.call_args_list]
        assert "game_starters_fetch_start" in event_types
        assert "game_starters_fetch_complete" in event_types

    def test_game_pk_is_int_key(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_starters_api_response())
            _, starters = client.fetch_game_starters("2026-06-23")
        assert all(isinstance(k, int) for k in starters)


# ---------------------------------------------------------------------------
# MLBIngestionClient — fetch_completed_games
# ---------------------------------------------------------------------------

class TestFetchCompletedGames:
    def test_returns_true_and_df_on_success(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_completed_games_response())
            ok, df = client.fetch_completed_games("2026-06-20", "2026-06-20")
        assert ok is True
        assert len(df) == 1  # only the "Final" game

    def test_excludes_non_final_games(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_completed_games_response())
            _, df = client.fetch_completed_games("2026-06-20", "2026-06-20")
        assert 77002 not in df["game_id"].values

    def test_scores_correct(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_completed_games_response())
            _, df = client.fetch_completed_games("2026-06-20", "2026-06-20")
        row = df[df["game_id"] == 77001].iloc[0]
        assert row["home_runs"] == 5
        assert row["away_runs"] == 3

    def test_team_abbr_populated(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(_completed_games_response())
            _, df = client.fetch_completed_games("2026-06-20", "2026-06-20")
        row = df.iloc[0]
        assert row["home_team_abbr"] == "NYY"
        assert row["away_team_abbr"] == "DET"

    def test_returns_false_on_http_error(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.mlb_ingestion.requests.get") as mg:
            import requests as req_mod
            mg.side_effect = req_mod.ConnectionError("down")
            ok, df = client.fetch_completed_games("2026-06-20", "2026-06-20")
        assert ok is False


# ---------------------------------------------------------------------------
# MLBTeamStatsStore — init and add
# ---------------------------------------------------------------------------

def _make_team_log(runs: list, runs_allowed: list, dates: list) -> pd.DataFrame:
    return pd.DataFrame({"game_date": dates, "runs": runs, "runs_allowed": runs_allowed})


class TestMLBTeamStatsStoreInit:
    def test_empty_on_init(self):
        store = MLBTeamStatsStore()
        assert len(store) == 0
        assert store.teams_loaded == []

    def test_add_increments_length(self):
        store = MLBTeamStatsStore()
        store.add_team_log("NYY", _make_team_log([5], [3], ["2026-06-01"]))
        assert len(store) == 1

    def test_contains_after_add(self):
        store = MLBTeamStatsStore()
        store.add_team_log("NYY", _make_team_log([5], [3], ["2026-06-01"]))
        assert "NYY" in store
        assert "nyy" in store  # case-insensitive

    def test_empty_df_ignored(self):
        store = MLBTeamStatsStore()
        store.add_team_log("NYY", pd.DataFrame())
        assert len(store) == 0

    def test_runs_allowed_derived_from_run_differential(self):
        store = MLBTeamStatsStore()
        df = pd.DataFrame({"game_date": ["2026-06-01"], "runs": [5], "run_differential": [2]})
        store.add_team_log("NYY", df)
        result = store.get_opp_runs_allowed("NYY", "2026-06-02", min_periods=1)
        assert result == pytest.approx(3.0)  # runs(5) - differential(2) = 3

    def test_teams_loaded_sorted(self):
        store = MLBTeamStatsStore()
        store.add_team_log("SD", _make_team_log([3], [5], ["2026-06-01"]))
        store.add_team_log("ATL", _make_team_log([4], [2], ["2026-06-01"]))
        assert store.teams_loaded == ["ATL", "SD"]


# ---------------------------------------------------------------------------
# MLBTeamStatsStore — get_opp_runs_allowed (temporal integrity)
# ---------------------------------------------------------------------------

class TestGetOppRunsAllowed:
    def _store_with_data(self) -> MLBTeamStatsStore:
        store = MLBTeamStatsStore()
        runs    = [5, 3, 4, 6, 2, 5, 7, 3, 4, 6, 5]
        allowed = [3, 4, 2, 5, 6, 3, 2, 5, 4, 3, 2]
        dates = [
            "2026-04-01", "2026-04-03", "2026-04-05",
            "2026-04-07", "2026-04-09", "2026-04-11",
            "2026-04-13", "2026-04-15", "2026-04-17",
            "2026-04-19", "2026-04-21",
        ]
        store.add_team_log("NYY", _make_team_log(runs, allowed, dates))
        return store

    def test_returns_float_with_enough_data(self):
        store = self._store_with_data()
        result = store.get_opp_runs_allowed("NYY", "2026-04-22")
        assert isinstance(result, float)

    def test_excludes_current_date(self):
        store = self._store_with_data()
        r_before = store.get_opp_runs_allowed("NYY", "2026-04-21")  # excludes Apr 21
        r_after  = store.get_opp_runs_allowed("NYY", "2026-04-22")  # includes Apr 21
        assert r_before != r_after

    def test_returns_none_unknown_team(self):
        store = self._store_with_data()
        assert store.get_opp_runs_allowed("FAKE", "2026-04-22") is None

    def test_returns_none_insufficient_data(self):
        store = MLBTeamStatsStore()
        store.add_team_log("SD", _make_team_log([3, 4], [2, 3], ["2026-04-01", "2026-04-03"]))
        assert store.get_opp_runs_allowed("SD", "2026-04-04", min_periods=3) is None

    def test_case_insensitive_lookup(self):
        store = self._store_with_data()
        r_upper = store.get_opp_runs_allowed("NYY", "2026-04-22")
        r_lower = store.get_opp_runs_allowed("nyy", "2026-04-22")
        assert r_upper == pytest.approx(r_lower)

    def test_returns_none_no_prior_games(self):
        store = self._store_with_data()
        assert store.get_opp_runs_allowed("NYY", "2026-03-01") is None

    def test_respects_window_size(self):
        store = self._store_with_data()
        r5  = store.get_opp_runs_allowed("NYY", "2026-04-22", window=5)
        r10 = store.get_opp_runs_allowed("NYY", "2026-04-22", window=10)
        assert r5 != r10


# ---------------------------------------------------------------------------
# MLBTeamStatsStore — build_from_games
# ---------------------------------------------------------------------------

class TestBuildFromGames:
    def test_both_teams_populated(self):
        games_df = pd.DataFrame([{
            "game_date": "2026-06-20",
            "home_team_abbr": "NYY", "away_team_abbr": "DET",
            "home_team_id": 147, "away_team_id": 116,
            "home_runs": 5, "away_runs": 3,
        }])
        store = MLBTeamStatsStore.build_from_games(games_df)
        assert "NYY" in store
        assert "DET" in store

    def test_runs_allowed_correct_for_home(self):
        games_df = pd.DataFrame([{
            "game_date": "2026-06-20",
            "home_team_abbr": "NYY", "away_team_abbr": "DET",
            "home_team_id": 147, "away_team_id": 116,
            "home_runs": 5, "away_runs": 3,
        }])
        store = MLBTeamStatsStore.build_from_games(games_df)
        # NYY home → runs=5, runs_allowed=3 (away scored 3)
        result = store.get_opp_runs_allowed("NYY", "2026-06-21", min_periods=1)
        assert result == pytest.approx(3.0)

    def test_runs_allowed_correct_for_away(self):
        games_df = pd.DataFrame([{
            "game_date": "2026-06-20",
            "home_team_abbr": "NYY", "away_team_abbr": "DET",
            "home_team_id": 147, "away_team_id": 116,
            "home_runs": 5, "away_runs": 3,
        }])
        store = MLBTeamStatsStore.build_from_games(games_df)
        # DET away → runs=3, runs_allowed=5 (home scored 5)
        result = store.get_opp_runs_allowed("DET", "2026-06-21", min_periods=1)
        assert result == pytest.approx(5.0)

    def test_empty_games_df_returns_empty_store(self):
        store = MLBTeamStatsStore.build_from_games(pd.DataFrame())
        assert len(store) == 0


# ---------------------------------------------------------------------------
# MLBTeamStatsStore — cache serialization
# ---------------------------------------------------------------------------

class TestMLBTeamStatsCacheSerialization:
    def test_round_trip_preserves_teams(self):
        store = MLBTeamStatsStore()
        store.add_team_log("NYY", _make_team_log([5, 3], [3, 4], ["2026-06-01", "2026-06-03"]))
        store.add_team_log("SD",  _make_team_log([4, 2], [2, 5], ["2026-06-02", "2026-06-04"]))
        restored = MLBTeamStatsStore.from_cache_dict(store.to_cache_dict())
        assert set(restored.teams_loaded) == {"NYY", "SD"}

    def test_round_trip_preserves_ratings(self):
        store = MLBTeamStatsStore()
        store.add_team_log("NYY", _make_team_log([5, 3, 4], [3, 4, 2], [
            "2026-06-01", "2026-06-03", "2026-06-05"
        ]))
        cache = store.to_cache_dict()
        restored = MLBTeamStatsStore.from_cache_dict(cache)
        original = store.get_opp_runs_allowed("NYY", "2026-06-06", min_periods=3)
        restored_val = restored.get_opp_runs_allowed("NYY", "2026-06-06", min_periods=3)
        assert restored_val == pytest.approx(original)

    def test_empty_records_skipped(self):
        cache = {"NYY": [], "SD": [{"game_date": "2026-06-01", "runs": 5, "runs_allowed": 3}]}
        restored = MLBTeamStatsStore.from_cache_dict(cache)
        assert "NYY" not in restored
        assert "SD" in restored


# ---------------------------------------------------------------------------
# MLBPitcherStatsStore — init and add
# ---------------------------------------------------------------------------

def _make_pitcher_log(ip, er, k, bb, dates, is_start=None):
    n = len(dates)
    if is_start is None:
        is_start = [1] * n
    return pd.DataFrame({
        "game_date": dates,
        "ip": ip,
        "er": er,
        "k": k,
        "bb": bb,
        "is_start": is_start,
    })


class TestMLBPitcherStatsStoreInit:
    def test_empty_on_init(self):
        store = MLBPitcherStatsStore()
        assert len(store) == 0
        assert store.pitchers_loaded == []

    def test_add_increments_length(self):
        store = MLBPitcherStatsStore()
        store.add_pitcher_log(1, _make_pitcher_log([6.0], [2], [8], [2], ["2026-04-07"]))
        assert len(store) == 1

    def test_contains_after_add(self):
        store = MLBPitcherStatsStore()
        store.add_pitcher_log(1234, _make_pitcher_log([6.0], [2], [8], [2], ["2026-04-07"]))
        assert 1234 in store

    def test_empty_df_ignored(self):
        store = MLBPitcherStatsStore()
        store.add_pitcher_log(1, pd.DataFrame())
        assert len(store) == 0


# ---------------------------------------------------------------------------
# MLBPitcherStatsStore — ERA/K9/BB9
# ---------------------------------------------------------------------------

class TestMLBPitcherRollingStats:
    def _store_with_5_starts(self) -> MLBPitcherStatsStore:
        store = MLBPitcherStatsStore()
        # IP sums to 31.0, ER=8, K=39, BB=9 — clean integer totals
        store.add_pitcher_log(1, _make_pitcher_log(
            ip=[6.0, 7.0, 6.0, 6.0, 6.0],
            er=[2,   1,   3,   0,   2],
            k= [8,   10,  5,   9,   7],
            bb=[2,   1,   3,   1,   2],
            dates=["2026-04-07", "2026-04-13", "2026-04-19",
                   "2026-04-25", "2026-05-01"],
        ))
        return store

    def test_era_l5_returns_float(self):
        store = self._store_with_5_starts()
        result = store.get_era_l5(1, "2026-05-07")
        assert isinstance(result, float)

    def test_era_l5_correct_value(self):
        # ER=8, IP=31.0 → ERA = (8/31)*9 ≈ 2.323
        store = self._store_with_5_starts()
        result = store.get_era_l5(1, "2026-05-07")
        assert result == pytest.approx(8 / 31.0 * 9, rel=1e-3)

    def test_k_per_9_correct_value(self):
        # K=39, IP=31.0 → K/9 = (39/31)*9 ≈ 11.32
        store = self._store_with_5_starts()
        result = store.get_k_per_9_l5(1, "2026-05-07")
        assert result == pytest.approx(39 / 31.0 * 9, rel=1e-3)

    def test_bb_per_9_correct_value(self):
        # BB=9, IP=31.0 → BB/9 = (9/31)*9 ≈ 2.613
        store = self._store_with_5_starts()
        result = store.get_bb_per_9_l5(1, "2026-05-07")
        assert result == pytest.approx(9 / 31.0 * 9, rel=1e-3)

    def test_temporal_guard_excludes_current_date(self):
        store = self._store_with_5_starts()
        era_before = store.get_era_l5(1, "2026-05-01")  # excludes May 1 start
        era_after  = store.get_era_l5(1, "2026-05-02")  # includes May 1 start
        assert era_before != era_after

    def test_returns_none_unknown_pitcher(self):
        store = self._store_with_5_starts()
        assert store.get_era_l5(9999, "2026-05-07") is None

    def test_returns_none_insufficient_data(self):
        store = MLBPitcherStatsStore()
        store.add_pitcher_log(1, _make_pitcher_log(
            [6.0], [2], [8], [2], ["2026-04-07"]
        ))
        assert store.get_era_l5(1, "2026-04-08", min_periods=2) is None

    def test_relief_appearances_excluded_from_sp_queries(self):
        store = MLBPitcherStatsStore()
        log = _make_pitcher_log(
            ip=[6.0, 6.0, 6.0, 1.0, 1.0],
            er=[2,   2,   2,   3,   3],   # relief ERs are much worse
            k= [8,   8,   8,   1,   1],
            bb=[2,   2,   2,   2,   2],
            dates=["2026-04-07", "2026-04-13", "2026-04-19", "2026-04-22", "2026-04-24"],
            is_start=[1, 1, 1, 0, 0],
        )
        store.add_pitcher_log(1, log)
        # ERA should only count 3 starts (IP=18, ER=6) → ERA = 3.0
        result = store.get_era_l5(1, "2026-05-01")
        assert result == pytest.approx(3.0, rel=1e-3)

    def test_window_respects_most_recent(self):
        store = MLBPitcherStatsStore()
        # 6 starts, window=5 should exclude earliest
        log = _make_pitcher_log(
            ip=[6.0, 6.0, 6.0, 6.0, 6.0, 6.0],
            er=[0,   5,   5,   5,   5,   5],  # first start is the outlier
            k= [8,   8,   8,   8,   8,   8],
            bb=[2,   2,   2,   2,   2,   2],
            dates=["2026-04-01", "2026-04-07", "2026-04-13",
                   "2026-04-19", "2026-04-25", "2026-05-01"],
        )
        store.add_pitcher_log(1, log)
        era_w5 = store.get_era_l5(1, "2026-05-07", window=5)
        era_w6 = store.get_era_l5(1, "2026-05-07", window=6)
        assert era_w5 != era_w6
        # last 5 of 6 starts: ER=[5,5,5,5,5]=25, IP=[6,6,6,6,6]=30 → ERA=(25/30)*9=7.5
        assert era_w5 == pytest.approx((25 / 30.0) * 9, rel=1e-3)


# ---------------------------------------------------------------------------
# MLBPitcherStatsStore — cache serialization
# ---------------------------------------------------------------------------

class TestMLBPitcherCacheSerialization:
    def test_round_trip_preserves_pitchers(self):
        store = MLBPitcherStatsStore()
        store.add_pitcher_log(111, _make_pitcher_log([6.0, 7.0], [2, 1], [8, 10], [2, 1],
                                                     ["2026-04-07", "2026-04-13"]))
        store.add_pitcher_log(222, _make_pitcher_log([5.0], [3], [5], [3], ["2026-04-08"]))
        restored = MLBPitcherStatsStore.from_cache_dict(store.to_cache_dict())
        assert set(restored.pitchers_loaded) == {111, 222}

    def test_round_trip_preserves_era(self):
        store = MLBPitcherStatsStore()
        store.add_pitcher_log(1, _make_pitcher_log([6.0, 7.0, 5.0], [2, 1, 3], [8, 10, 5], [2, 1, 3],
                                                   ["2026-04-07", "2026-04-13", "2026-04-19"]))
        restored = MLBPitcherStatsStore.from_cache_dict(store.to_cache_dict())
        original_era = store.get_era_l5(1, "2026-04-20", min_periods=3)
        restored_era = restored.get_era_l5(1, "2026-04-20", min_periods=3)
        assert restored_era == pytest.approx(original_era)

    def test_empty_records_skipped(self):
        cache = {"111": [], "222": [{"game_date": "2026-04-07", "ip": 6.0, "er": 2, "k": 8, "bb": 2, "is_start": 1}]}
        restored = MLBPitcherStatsStore.from_cache_dict(cache)
        assert 111 not in restored
        assert 222 in restored

    def test_invalid_pitcher_id_key_skipped(self):
        cache = {"not-an-int": [{"game_date": "2026-04-07", "ip": 6.0, "er": 2, "k": 8, "bb": 2}]}
        restored = MLBPitcherStatsStore.from_cache_dict(cache)
        assert len(restored) == 0

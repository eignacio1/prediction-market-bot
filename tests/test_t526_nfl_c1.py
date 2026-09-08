"""Tests for T-526/GG-253: NFL C1 ingestion module.

Coverage:
  - NFLIngestionClient: fetch_schedule, fetch_team_stats (incl. the
    documented 404/cold-start case), fetch_team_stats_bulk
  - NFLTeamStatsStore: init, add, build_from_team_stats, temporal integrity,
    recency-weighted rolling stats, cold-start carryover (Week 1 of a new
    season pulls from the prior season via the temporal filter alone, with
    no season-aware branch), fallback-of-fallback (zero games anywhere),
    cache round-trip

All tests are pure unit tests — no live HTTP calls. requests.get is mocked
throughout.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import (
    NFLIngestionClient,
    _NFL_SCHEDULE_COLUMNS,
    _NFL_TEAM_STATS_COLUMNS,
)
from prediction_market_bot.c1_signal_ingestion.nfl_team_stats_store import NFLTeamStatsStore


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_logger() -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = True
    return logger


def _make_client() -> tuple[NFLIngestionClient, MagicMock]:
    logger = _make_logger()
    client = NFLIngestionClient(logger=logger, snapshot_id="TEST-SNAP-001")
    return client, logger


def _mock_resp(status_code: int, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if status_code == 200:
        resp.raise_for_status.return_value = None
    else:
        import requests as req_mod
        err = req_mod.HTTPError(response=resp)
        resp.raise_for_status.side_effect = err
    return resp


def _schedule_csv(rows: list[dict]) -> str:
    df = pd.DataFrame(rows, columns=_NFL_SCHEDULE_COLUMNS)
    return df.to_csv(index=False)


def _team_stats_csv(rows: list[dict]) -> str:
    cols = ["season", "week", "season_type", "game_id", "team", "opponent_team",
            "passing_epa", "rushing_epa"]
    df = pd.DataFrame(rows, columns=cols)
    return df.to_csv(index=False)


def _sample_schedule_rows() -> list[dict]:
    return [
        {
            "game_id": "2025_01_ARI_NO", "season": 2025, "game_type": "REG",
            "week": 1, "gameday": "2025-09-07", "home_team": "NO",
            "away_team": "ARI", "home_score": 20.0, "away_score": 17.0,
            "home_rest": 7, "away_rest": 7,
        },
        {
            "game_id": "2026_01_KC_LAC", "season": 2026, "game_type": "REG",
            "week": 1, "gameday": "2026-09-10", "home_team": "LAC",
            "away_team": "KC", "home_score": None, "away_score": None,
            "home_rest": 10, "away_rest": 9,
        },
    ]


def _sample_team_stats_rows() -> list[dict]:
    return [
        {"season": 2025, "week": 1, "season_type": "REG", "game_id": "2025_01_ARI_NO",
         "team": "ARI", "opponent_team": "NO", "passing_epa": 1.52, "rushing_epa": 1.16},
        {"season": 2025, "week": 1, "season_type": "REG", "game_id": "2025_01_ARI_NO",
         "team": "NO", "opponent_team": "ARI", "passing_epa": -0.40, "rushing_epa": -0.10},
    ]


# ---------------------------------------------------------------------------
# NFLIngestionClient — fetch_schedule
# ---------------------------------------------------------------------------

class TestFetchSchedule:
    def test_returns_true_and_df_on_success(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _schedule_csv(_sample_schedule_rows()))
            ok, df = client.fetch_schedule()
        assert ok is True
        assert len(df) == 2

    def test_output_columns_match_contract(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _schedule_csv(_sample_schedule_rows()))
            _, df = client.fetch_schedule()
        assert list(df.columns) == _NFL_SCHEDULE_COLUMNS

    def test_unplayed_game_has_null_scores_but_real_rest(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _schedule_csv(_sample_schedule_rows()))
            _, df = client.fetch_schedule()
        row = df[df["game_id"] == "2026_01_KC_LAC"].iloc[0]
        assert pd.isna(row["home_score"])
        assert pd.isna(row["away_score"])
        assert row["home_rest"] == 10
        assert row["away_rest"] == 9

    def test_season_filter(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _schedule_csv(_sample_schedule_rows()))
            _, df = client.fetch_schedule(seasons=[2025])
        assert len(df) == 1
        assert df.iloc[0]["season"] == 2025

    def test_returns_false_on_http_error(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.time.sleep"):
                mg.return_value = _mock_resp(500)
                ok, df = client.fetch_schedule()
        assert ok is False
        assert df.empty

    def test_returns_false_on_network_error(self):
        client, _ = _make_client()
        import requests as req_mod
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.time.sleep"):
                mg.side_effect = req_mod.ConnectionError("network down")
                ok, df = client.fetch_schedule()
        assert ok is False

    def test_logger_called_on_success(self):
        client, logger = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _schedule_csv(_sample_schedule_rows()))
            client.fetch_schedule()
        event_types = [c.args[1] for c in logger.log.call_args_list]
        assert "schedule_fetch_start" in event_types
        assert "schedule_fetch_complete" in event_types


# ---------------------------------------------------------------------------
# NFLIngestionClient — fetch_team_stats (incl. cold-start / 404 handling)
# ---------------------------------------------------------------------------

class TestFetchTeamStats:
    def test_returns_true_and_df_on_success(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _team_stats_csv(_sample_team_stats_rows()))
            ok, df = client.fetch_team_stats(2025)
        assert ok is True
        assert len(df) == 2

    def test_output_columns_match_contract(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _team_stats_csv(_sample_team_stats_rows()))
            _, df = client.fetch_team_stats(2025)
        assert list(df.columns) == _NFL_TEAM_STATS_COLUMNS

    def test_off_epa_computed_as_sum(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _team_stats_csv(_sample_team_stats_rows()))
            _, df = client.fetch_team_stats(2025)
        row = df[df["team"] == "ARI"].iloc[0]
        assert row["off_epa"] == pytest.approx(1.52 + 1.16)

    def test_cold_start_404_returns_ok_true_empty_df(self):
        """GG-253 required cold-start test: a season whose file doesn't
        exist yet (not started) is an expected condition, not a failure."""
        client, logger = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(404)
            ok, df = client.fetch_team_stats(2099)
        assert ok is True
        assert df.empty
        assert list(df.columns) == _NFL_TEAM_STATS_COLUMNS
        event_types = [c.args[1] for c in logger.log.call_args_list]
        assert "team_stats_not_yet_available" in event_types
        # must be logged as WARNING, not ERROR — this is expected, not a failure
        warn_calls = [c for c in logger.log.call_args_list if c.args[1] == "team_stats_not_yet_available"]
        assert warn_calls[0].kwargs["severity"] == "WARNING"

    def test_404_does_not_retry(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(404)
            client.fetch_team_stats(2099)
        assert mg.call_count == 1

    def test_returns_false_on_500(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.time.sleep"):
                mg.return_value = _mock_resp(500)
                ok, df = client.fetch_team_stats(2025)
        assert ok is False

    def test_500_retries_up_to_max(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.time.sleep"):
                mg.return_value = _mock_resp(500)
                client.fetch_team_stats(2025)
        assert mg.call_count == 3  # MAX_RETRIES


class TestFetchTeamStatsBulk:
    def test_concatenates_multiple_seasons(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.return_value = _mock_resp(200, _team_stats_csv(_sample_team_stats_rows()))
            ok, df = client.fetch_team_stats_bulk([2024, 2025])
        assert ok is True
        assert len(df) == 4  # 2 seasons × 2 rows each

    def test_one_season_404_folds_in_as_empty_not_failure(self):
        """A 404 for one season among several must not flip the bulk
        result to False — it's the documented cold-start case."""
        client, _ = _make_client()
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_resp(200, _team_stats_csv(_sample_team_stats_rows()))
            return _mock_resp(404)

        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            mg.side_effect = side_effect
            ok, df = client.fetch_team_stats_bulk([2025, 2026])
        assert ok is True
        assert len(df) == 2  # only 2025's rows

    def test_real_failure_among_seasons_returns_false(self):
        client, _ = _make_client()
        with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get") as mg:
            with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.time.sleep"):
                mg.return_value = _mock_resp(500)
                ok, df = client.fetch_team_stats_bulk([2025])
        assert ok is False


# ---------------------------------------------------------------------------
# NFLTeamStatsStore — init and add
# ---------------------------------------------------------------------------

def _make_team_log(off_epa: list, def_epa_allowed: list, dates: list) -> pd.DataFrame:
    return pd.DataFrame({
        "game_date": dates, "off_epa": off_epa, "def_epa_allowed": def_epa_allowed,
    })


class TestNFLTeamStatsStoreInit:
    def test_empty_on_init(self):
        store = NFLTeamStatsStore()
        assert len(store) == 0
        assert store.teams_loaded == []

    def test_add_increments_length(self):
        store = NFLTeamStatsStore()
        store.add_team_log("KC", _make_team_log([2.5], [0.5], ["2026-09-10"]))
        assert len(store) == 1

    def test_contains_case_insensitive(self):
        store = NFLTeamStatsStore()
        store.add_team_log("KC", _make_team_log([2.5], [0.5], ["2026-09-10"]))
        assert "KC" in store
        assert "kc" in store

    def test_empty_df_ignored(self):
        store = NFLTeamStatsStore()
        store.add_team_log("KC", pd.DataFrame())
        assert len(store) == 0

    def test_teams_loaded_sorted(self):
        store = NFLTeamStatsStore()
        store.add_team_log("NO", _make_team_log([1.0], [0.5], ["2026-09-10"]))
        store.add_team_log("ARI", _make_team_log([1.5], [0.2], ["2026-09-10"]))
        assert store.teams_loaded == ["ARI", "NO"]


# ---------------------------------------------------------------------------
# NFLTeamStatsStore — build_from_team_stats
# ---------------------------------------------------------------------------

class TestBuildFromTeamStats:
    def _team_stats_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"season": 2025, "week": 1, "season_type": "REG", "game_id": "2025_01_ARI_NO",
             "team": "ARI", "opponent_team": "NO", "off_epa": 2.68},
            {"season": 2025, "week": 1, "season_type": "REG", "game_id": "2025_01_ARI_NO",
             "team": "NO", "opponent_team": "ARI", "off_epa": -0.50},
        ])

    def _schedule_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"game_id": "2025_01_ARI_NO", "gameday": "2025-09-07"},
        ])

    def test_both_teams_populated(self):
        store = NFLTeamStatsStore.build_from_team_stats(self._team_stats_df(), self._schedule_df())
        assert "ARI" in store
        assert "NO" in store

    def test_def_epa_allowed_is_opponent_off_epa(self):
        store = NFLTeamStatsStore.build_from_team_stats(self._team_stats_df(), self._schedule_df())
        ari_def = store.get_def_epa_allowed("ARI", "2025-09-08", min_periods=1)
        assert ari_def == pytest.approx(-0.50)
        no_def = store.get_def_epa_allowed("NO", "2025-09-08", min_periods=1)
        assert no_def == pytest.approx(2.68)

    def test_game_date_attached_from_schedule(self):
        store = NFLTeamStatsStore.build_from_team_stats(self._team_stats_df(), self._schedule_df())
        off = store.get_off_epa("ARI", "2025-09-08", min_periods=1)
        assert off == pytest.approx(2.68)
        # date filter excludes same-day
        off_excluded = store.get_off_epa("ARI", "2025-09-07", min_periods=1)
        assert off_excluded is None

    def test_empty_team_stats_returns_empty_store(self):
        store = NFLTeamStatsStore.build_from_team_stats(pd.DataFrame(), pd.DataFrame())
        assert len(store) == 0


# ---------------------------------------------------------------------------
# NFLTeamStatsStore — recency-weighted queries (temporal integrity)
# ---------------------------------------------------------------------------

class TestRecencyWeightedQueries:
    def _store_with_data(self) -> NFLTeamStatsStore:
        store = NFLTeamStatsStore()
        off = [1.0, -0.5, 2.0, 0.5, -1.0, 1.5, 0.8, 2.2]
        dfa = [0.5, 1.0, -0.5, 0.2, 1.5, -0.3, 0.9, -0.2]
        dates = [
            "2025-09-07", "2025-09-14", "2025-09-21", "2025-09-28",
            "2025-10-05", "2025-10-12", "2025-10-19", "2025-10-26",
        ]
        store.add_team_log("KC", _make_team_log(off, dfa, dates))
        return store

    def test_returns_float_with_enough_data(self):
        store = self._store_with_data()
        result = store.get_off_epa("KC", "2025-11-02")
        assert isinstance(result, float)

    def test_excludes_current_date(self):
        store = self._store_with_data()
        before = store.get_off_epa("KC", "2025-10-26")  # excludes Oct 26
        after = store.get_off_epa("KC", "2025-11-02")   # includes Oct 26
        assert before != after

    def test_returns_none_unknown_team(self):
        store = self._store_with_data()
        assert store.get_off_epa("FAKE", "2025-11-02") is None

    def test_returns_none_insufficient_data(self):
        store = NFLTeamStatsStore()
        store.add_team_log("SD", _make_team_log([1.0, 0.5], [0.2, 0.3], ["2025-09-07", "2025-09-14"]))
        assert store.get_off_epa("SD", "2025-09-21", min_periods=3) is None

    def test_case_insensitive_lookup(self):
        store = self._store_with_data()
        upper = store.get_off_epa("KC", "2025-11-02")
        lower = store.get_off_epa("kc", "2025-11-02")
        assert upper == pytest.approx(lower)

    def test_recency_weighting_differs_from_plain_mean(self):
        """The most recent game should pull the weighted mean toward it
        more than a plain unweighted mean would."""
        store = self._store_with_data()
        weighted = store.get_off_epa("KC", "2025-11-02", window=8, decay=0.85)
        plain_mean = pd.Series([1.0, -0.5, 2.0, 0.5, -1.0, 1.5, 0.8, 2.2]).mean()
        # last value (2.2) is well above the plain mean, so weighting toward
        # recency should push the result closer to 2.2 than the plain mean is
        assert abs(weighted - 2.2) < abs(plain_mean - 2.2)

    def test_decay_of_one_equals_plain_mean(self):
        """decay=1.0 (no discount) should reduce to an unweighted mean."""
        store = self._store_with_data()
        result = store.get_off_epa("KC", "2025-11-02", window=8, decay=1.0)
        plain_mean = pd.Series([1.0, -0.5, 2.0, 0.5, -1.0, 1.5, 0.8, 2.2]).mean()
        assert result == pytest.approx(plain_mean)

    def test_respects_window_size(self):
        store = self._store_with_data()
        r4 = store.get_off_epa("KC", "2025-11-02", window=4)
        r8 = store.get_off_epa("KC", "2025-11-02", window=8)
        assert r4 != r8

    def test_def_epa_allowed_independent_of_off_epa(self):
        store = self._store_with_data()
        off = store.get_off_epa("KC", "2025-11-02")
        dfa = store.get_def_epa_allowed("KC", "2025-11-02")
        assert off != dfa


# ---------------------------------------------------------------------------
# NFLTeamStatsStore — cold start (GG-253 required test, not an accident)
# ---------------------------------------------------------------------------

class TestColdStartCarryover:
    """Week 1 of a new season: zero current-season games exist before
    as_of_date. Per the module's design, get_off_epa/get_def_epa_allowed
    take no season parameter — the temporal filter alone (game_date <
    as_of_date, tail(window)) should transparently fall back to the end
    of the most recent prior season with no special-cased branch."""

    def _store_spanning_two_seasons(self) -> NFLTeamStatsStore:
        store = NFLTeamStatsStore()
        # 2025 season: weeks 1-8 (ending 2025-10-26)
        off_2025 = [1.0, -0.5, 2.0, 0.5, -1.0, 1.5, 0.8, 2.2]
        dfa_2025 = [0.5, 1.0, -0.5, 0.2, 1.5, -0.3, 0.9, -0.2]
        dates_2025 = [
            "2025-09-07", "2025-09-14", "2025-09-21", "2025-09-28",
            "2025-10-05", "2025-10-12", "2025-10-19", "2025-10-26",
        ]
        store.add_team_log("KC", _make_team_log(off_2025, dfa_2025, dates_2025))
        return store

    def test_week1_new_season_pulls_prior_season_data(self):
        """as_of_date is 2026 Week 1 (2026-09-10); the store has ONLY 2025
        games. Because there is no season parameter, the temporal filter
        (game_date < 2026-09-10) still includes all 8 prior-season games,
        and tail(window) draws from the end of the 2025 season."""
        store = self._store_spanning_two_seasons()
        result = store.get_off_epa("KC", "2026-09-10")
        assert result is not None
        assert isinstance(result, float)

    def test_week1_carryover_uses_most_recent_prior_season_games(self):
        """The carried-over value should reflect the last (most recent)
        games of 2025, not an average diluted by the whole season equally —
        i.e. recency weighting is still applied across the season boundary."""
        store = self._store_spanning_two_seasons()
        carried_over = store.get_off_epa("KC", "2026-09-10", window=8, decay=0.85)
        plain_mean_2025 = pd.Series([1.0, -0.5, 2.0, 0.5, -1.0, 1.5, 0.8, 2.2]).mean()
        # last 2025 game (2.2) should still pull the weighted carryover value
        # toward it, exactly as within-season recency weighting does
        assert abs(carried_over - 2.2) < abs(plain_mean_2025 - 2.2)

    def test_no_season_parameter_exists_on_query_methods(self):
        """Structural assertion of the design decision itself: these methods
        must not accept a season kwarg — the carryover is emergent from the
        temporal filter, not a branch keyed on season."""
        import inspect
        sig_off = inspect.signature(NFLTeamStatsStore.get_off_epa)
        sig_def = inspect.signature(NFLTeamStatsStore.get_def_epa_allowed)
        assert "season" not in sig_off.parameters
        assert "season" not in sig_def.parameters

    def test_fallback_of_fallback_zero_games_anywhere_returns_none(self):
        """A team with zero games in the ENTIRE dataset (true
        fallback-of-fallback) must return None, not crash or silently
        substitute a league average — that substitution is a C2/caller
        decision, not C1's."""
        store = self._store_spanning_two_seasons()
        result = store.get_off_epa("EXPANSION_TEAM_NEVER_PLAYED", "2026-09-10")
        assert result is None


# ---------------------------------------------------------------------------
# NFLTeamStatsStore — cache serialization
# ---------------------------------------------------------------------------

class TestNFLTeamStatsCacheSerialization:
    def test_round_trip_preserves_teams(self):
        store = NFLTeamStatsStore()
        store.add_team_log("KC", _make_team_log([1.0, 2.0], [0.5, 0.3], ["2026-09-10", "2026-09-17"]))
        store.add_team_log("NO", _make_team_log([0.5, -0.2], [1.0, 0.8], ["2026-09-11", "2026-09-18"]))
        restored = NFLTeamStatsStore.from_cache_dict(store.to_cache_dict())
        assert set(restored.teams_loaded) == {"KC", "NO"}

    def test_round_trip_preserves_values(self):
        store = NFLTeamStatsStore()
        store.add_team_log("KC", _make_team_log(
            [1.0, 2.0, 0.5], [0.5, 0.3, 0.2],
            ["2026-09-10", "2026-09-17", "2026-09-24"],
        ))
        restored = NFLTeamStatsStore.from_cache_dict(store.to_cache_dict())
        original = store.get_off_epa("KC", "2026-10-01", min_periods=3)
        restored_val = restored.get_off_epa("KC", "2026-10-01", min_periods=3)
        assert restored_val == pytest.approx(original)

    def test_empty_records_skipped(self):
        cache = {
            "KC": [],
            "NO": [{"game_date": "2026-09-10", "off_epa": 1.0, "def_epa_allowed": 0.5}],
        }
        restored = NFLTeamStatsStore.from_cache_dict(cache)
        assert "KC" not in restored
        assert "NO" in restored

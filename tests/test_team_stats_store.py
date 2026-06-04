"""Tests for c1_signal_ingestion/team_stats_store.py — TeamStatsStore."""
import pytest
import pandas as pd
import numpy as np

from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_team_log(
    pts: list[float],
    plus_minus: list[float],
    dates: list[str],
) -> pd.DataFrame:
    return pd.DataFrame({
        "game_date": dates,
        "pts": pts,
        "plus_minus": plus_minus,
    })


# ---------------------------------------------------------------------------
# Construction and add_team_log
# ---------------------------------------------------------------------------

class TestTeamStatsStoreInit:
    def test_empty_on_init(self):
        store = TeamStatsStore()
        assert len(store) == 0
        assert store.teams_loaded == []

    def test_add_team_increments_length(self):
        store = TeamStatsStore()
        store.add_team_log("GSW", _make_team_log([110], [5], ["2025-01-10"]))
        assert len(store) == 1

    def test_contains_after_add(self):
        store = TeamStatsStore()
        store.add_team_log("GSW", _make_team_log([110], [5], ["2025-01-10"]))
        assert "GSW" in store
        assert "gsw" in store  # case-insensitive

    def test_empty_df_ignored(self):
        store = TeamStatsStore()
        store.add_team_log("GSW", pd.DataFrame())
        assert len(store) == 0

    def test_pts_allowed_computed(self):
        # pts=110, plus_minus=+10 → pts_allowed = 110 - 10 = 100
        store = TeamStatsStore()
        store.add_team_log("OKC", _make_team_log([110], [10], ["2025-01-10"]))
        rating = store.get_opp_def_rating("OKC", "2025-01-11", min_periods=1)
        assert rating == pytest.approx(100.0)

    def test_pts_allowed_when_loss(self):
        # pts=95, plus_minus=-8 → pts_allowed = 95 - (-8) = 103
        store = TeamStatsStore()
        store.add_team_log("LAL", _make_team_log([95], [-8], ["2025-01-10"]))
        rating = store.get_opp_def_rating("LAL", "2025-01-11", min_periods=1)
        assert rating == pytest.approx(103.0)


# ---------------------------------------------------------------------------
# get_opp_def_rating — temporal integrity
# ---------------------------------------------------------------------------

class TestGetOppDefRating:
    def _store_with_data(self):
        store = TeamStatsStore()
        pts       = [110, 105, 98,  115, 108, 102, 112, 100, 107, 95,  120]
        plus_minus= [  5,  -3, 12,    8,   2, -10,   6, -15,   9,  3,   14]
        dates = [
            "2025-01-01", "2025-01-03", "2025-01-05",
            "2025-01-07", "2025-01-09", "2025-01-11",
            "2025-01-13", "2025-01-15", "2025-01-17",
            "2025-01-19", "2025-01-21",
        ]
        store.add_team_log("GSW", _make_team_log(pts, plus_minus, dates))
        return store

    def test_returns_float_with_enough_data(self):
        store = self._store_with_data()
        result = store.get_opp_def_rating("GSW", "2025-01-22")
        assert isinstance(result, float)

    def test_excludes_current_game_date(self):
        # Games strictly before 2025-01-22; last game on 2025-01-21 included
        store = self._store_with_data()
        r_before = store.get_opp_def_rating("GSW", "2025-01-21")  # excludes Jan 21
        r_after  = store.get_opp_def_rating("GSW", "2025-01-22")  # includes Jan 21
        assert r_before != r_after

    def test_returns_none_for_unknown_team(self):
        store = self._store_with_data()
        assert store.get_opp_def_rating("FAKE", "2025-01-22") is None

    def test_returns_none_when_insufficient_data(self):
        store = TeamStatsStore()
        store.add_team_log("MIA", _make_team_log([105, 98], [3, -5], ["2025-01-01", "2025-01-03"]))
        assert store.get_opp_def_rating("MIA", "2025-01-04", min_periods=3) is None

    def test_respects_window_size(self):
        store = self._store_with_data()
        # Window=3 vs window=10 should give different results
        r3  = store.get_opp_def_rating("GSW", "2025-01-22", window=3)
        r10 = store.get_opp_def_rating("GSW", "2025-01-22", window=10)
        assert r3 != r10

    def test_case_insensitive(self):
        store = self._store_with_data()
        r_upper = store.get_opp_def_rating("GSW", "2025-01-22")
        r_lower = store.get_opp_def_rating("gsw", "2025-01-22")
        assert r_upper == pytest.approx(r_lower)

    def test_returns_none_when_no_prior_games(self):
        store = self._store_with_data()
        # Date before all data
        assert store.get_opp_def_rating("GSW", "2024-12-31") is None


# ---------------------------------------------------------------------------
# get_opp_pts_scored
# ---------------------------------------------------------------------------

class TestGetOppPtsScored:
    def test_returns_float(self):
        store = TeamStatsStore()
        store.add_team_log("BOS", _make_team_log([115, 110, 120], [5, -3, 8],
                                                  ["2025-01-01", "2025-01-03", "2025-01-05"]))
        result = store.get_opp_pts_scored("BOS", "2025-01-06", min_periods=3)
        assert result == pytest.approx(115.0)

    def test_returns_none_for_unknown_team(self):
        store = TeamStatsStore()
        assert store.get_opp_pts_scored("FAKE", "2025-01-06") is None


# ---------------------------------------------------------------------------
# TeamStatsStore cache serialization (ADR-0015)
# ---------------------------------------------------------------------------

class TestCacheSerialization:
    def test_round_trip_preserves_teams(self):
        store = TeamStatsStore()
        store.add_team_log("NYK", _make_team_log([110, 105, 115], [5, -3, 8],
                                                   ["2026-01-01", "2026-01-03", "2026-01-05"]))
        store.add_team_log("SAS", _make_team_log([108, 112, 102], [2, -1, 6],
                                                   ["2026-01-02", "2026-01-04", "2026-01-06"]))
        cache = store.to_cache_dict()
        restored = TeamStatsStore.from_cache_dict(cache)
        assert set(restored.teams_loaded) == {"NYK", "SAS"}

    def test_round_trip_preserves_ratings(self):
        store = TeamStatsStore()
        store.add_team_log("GSW", _make_team_log([115, 110, 120], [5, -3, 8],
                                                   ["2026-01-01", "2026-01-03", "2026-01-05"]))
        cache = store.to_cache_dict()
        restored = TeamStatsStore.from_cache_dict(cache)
        original_rating = store.get_opp_def_rating("GSW", "2026-01-06", min_periods=3)
        restored_rating = restored.get_opp_def_rating("GSW", "2026-01-06", min_periods=3)
        assert restored_rating == pytest.approx(original_rating)

    def test_empty_store_round_trips(self):
        store = TeamStatsStore()
        cache = store.to_cache_dict()
        restored = TeamStatsStore.from_cache_dict(cache)
        assert len(restored) == 0

    def test_from_cache_dict_empty_records_skipped(self):
        cache = {"NYK": [], "SAS": [{"game_date": "2026-01-01", "pts": 110, "plus_minus": 5, "pts_allowed": 105}]}
        restored = TeamStatsStore.from_cache_dict(cache)
        assert "NYK" not in restored
        assert "SAS" in restored

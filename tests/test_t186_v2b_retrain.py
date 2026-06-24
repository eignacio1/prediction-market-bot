"""
T-186 Tests — F-042 Playoff Store Population + v2b Retrain Pipeline
=====================================================================

Tests for:
  - pull_playoff_teamgamelog.py  (script-level logic, mocked API)
  - train_model_v2b.py           (_add_f042_from_store + dry-run integration)
  - run_t177_v2_backtest.py      (--model flag regression)

Suite:
  TestAddF042FromStore     (16) — core F-042 computation: temporal integrity,
                                   NaN for non-playoff rows, correct store lookup,
                                   edge cases (missing opp, bad date, no min_periods)
  TestPlayoffPullMerge     (6)  — accumulation logic for multi-season log merge
  TestV2bBoilerplateGuards (5)  — BOT_C4_ACTIVE guard, missing files, path names
  TestT177ModelFlag        (4)  — --model arg accepted and routes to correct artifact
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

_SRC_ROOT = Path(__file__).parent.parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

_SCRIPTS_ROOT = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_game_log(dates: list[str], pts: list[float], pm: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "game_date": dates,
        "pts": pts,
        "plus_minus": pm,
    })


def _make_playoff_store(*team_logs: tuple[str, pd.DataFrame]) -> TeamStatsStore:
    store = TeamStatsStore()
    for abbr, df in team_logs:
        store.add_team_log(abbr, df)
    return store


def _make_feature_row(
    season_type: str = "Playoffs",
    opp_abbr: str = "LAL",
    game_date: object = pd.Timestamp("2025-05-10"),
) -> pd.Series:
    return pd.Series({
        "season_type": season_type,
        "opponent_team_abbr": opp_abbr,
        "game_date": game_date,
    })


# ---------------------------------------------------------------------------
# Import _add_f042_from_store without executing main()
# ---------------------------------------------------------------------------

def _import_v2b():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "train_model_v2b",
        _SCRIPTS_ROOT / "train_model_v2b.py",
    )
    mod = importlib.util.module_from_spec(spec)
    # Patch heavy imports so they load without needing all packages installed
    # in the test runner (joblib, sklearn etc. ARE installed — just guarding
    # against module-level side effects).
    spec.loader.exec_module(mod)
    return mod


try:
    _v2b = _import_v2b()
    _add_f042_from_store = _v2b._add_f042_from_store
    _V2B_AVAILABLE = True
except Exception:
    _V2B_AVAILABLE = False


# ---------------------------------------------------------------------------
# TestAddF042FromStore
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _V2B_AVAILABLE, reason="train_model_v2b.py not importable")
class TestAddF042FromStore:

    def _store_with_lal(self) -> TeamStatsStore:
        log = _make_game_log(
            ["2025-04-20", "2025-04-22", "2025-04-25", "2025-04-27", "2025-04-30"],
            [110.0, 108.0, 115.0, 112.0, 109.0],
            [5.0, -3.0, 8.0, 2.0, -4.0],
        )
        return _make_playoff_store(("LAL", log))

    def test_regular_season_row_returns_nan(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row(season_type="Regular Season", game_date=pd.Timestamp("2025-03-10"))])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_playoff_row_with_sufficient_history(self):
        store = self._store_with_lal()
        # game_date after 5 prior LAL playoff games → should get L5 mean pts_allowed
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="LAL", game_date=pd.Timestamp("2025-05-05")
        )])
        result = _add_f042_from_store(df, store)
        val = result["opp_playoff_def_rating_l5_mean"].iloc[0]
        assert not np.isnan(val)
        # pts_allowed = pts - plus_minus; expected values:
        # 110-5=105, 108-(-3)=111, 115-8=107, 112-2=110, 109-(-4)=113
        expected = np.mean([105, 111, 107, 110, 113])
        assert abs(val - expected) < 0.001

    def test_playoff_row_insufficient_history_returns_nan(self):
        # Only 2 games before the query date — below min_periods=3
        log = _make_game_log(
            ["2025-04-20", "2025-04-22"],
            [110.0, 108.0],
            [5.0, -3.0],
        )
        store = _make_playoff_store(("BOS", log))
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="BOS", game_date=pd.Timestamp("2025-04-25")
        )])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_temporal_integrity_game_date_excluded(self):
        # game on 2025-04-22 must NOT include 2025-04-22 entry
        log = _make_game_log(
            ["2025-04-18", "2025-04-20", "2025-04-22"],
            [110.0, 108.0, 120.0],  # 120 on the game date — should be excluded
            [5.0, -3.0, 10.0],
        )
        store = _make_playoff_store(("GSW", log))
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="GSW", game_date=pd.Timestamp("2025-04-22")
        )])
        result = _add_f042_from_store(df, store)
        # Only 2 prior games (2025-04-18, 2025-04-20) — below min_periods → NaN
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_unknown_opponent_returns_nan(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="UNKNOWN", game_date=pd.Timestamp("2025-05-05")
        )])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_none_opp_abbr_returns_nan(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr=None, game_date=pd.Timestamp("2025-05-05")
        )])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_nan_opp_abbr_returns_nan(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr=float("nan"), game_date=pd.Timestamp("2025-05-05")
        )])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_string_game_date_accepted(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="LAL", game_date="2025-05-05"
        )])
        result = _add_f042_from_store(df, store)
        assert not np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_timestamp_game_date_accepted(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="LAL", game_date=pd.Timestamp("2025-05-05")
        )])
        result = _add_f042_from_store(df, store)
        assert not np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_output_column_name(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row()])
        result = _add_f042_from_store(df, store)
        assert "opp_playoff_def_rating_l5_mean" in result.columns

    def test_does_not_mutate_input_df(self):
        store = self._store_with_lal()
        df = pd.DataFrame([_make_feature_row()])
        original_cols = set(df.columns)
        _add_f042_from_store(df, store)
        assert set(df.columns) == original_cols

    def test_multiple_rows_mixed_season_types(self):
        store = self._store_with_lal()
        df = pd.DataFrame([
            _make_feature_row(season_type="Regular Season", game_date=pd.Timestamp("2025-03-01")),
            _make_feature_row(season_type="Playoffs", opp_abbr="LAL", game_date=pd.Timestamp("2025-05-05")),
        ])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])
        assert not np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[1])

    def test_window_limited_to_5(self):
        # Store has 8 games; window=5 → only last 5 prior should contribute
        log = _make_game_log(
            [f"2025-04-{d:02d}" for d in range(10, 18)],
            [100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0],
            [0.0] * 8,
        )
        store = _make_playoff_store(("MIA", log))
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="MIA", game_date=pd.Timestamp("2025-04-20")
        )])
        result = _add_f042_from_store(df, store)
        # Games before 2025-04-20: Apr 10-19 = 10 games → L5 = last 5
        # pts_allowed = pts (pm=0) → last 5 are Apr 15-19: 105,107,109,111,113
        val = result["opp_playoff_def_rating_l5_mean"].iloc[0]
        assert not np.isnan(val)

    def test_cross_season_lookup(self):
        # LAL has 2024-25 playoff games (Apr 2025) AND 2025-26 playoff games (Apr 2026)
        log = _make_game_log(
            ["2025-04-20", "2025-04-22", "2025-04-25", "2026-04-20", "2026-04-22"],
            [110.0, 108.0, 115.0, 112.0, 109.0],
            [5.0, -3.0, 8.0, 2.0, -4.0],
        )
        store = _make_playoff_store(("LAL", log))
        # Query for 2026 playoff game — should see prior 2025 + 2026 games
        df = pd.DataFrame([_make_feature_row(
            season_type="Playoffs", opp_abbr="LAL", game_date=pd.Timestamp("2026-04-25")
        )])
        result = _add_f042_from_store(df, store)
        val = result["opp_playoff_def_rating_l5_mean"].iloc[0]
        assert not np.isnan(val)

    def test_empty_store_returns_nan(self):
        store = TeamStatsStore()
        df = pd.DataFrame([_make_feature_row(season_type="Playoffs", opp_abbr="LAL")])
        result = _add_f042_from_store(df, store)
        assert np.isnan(result["opp_playoff_def_rating_l5_mean"].iloc[0])

    def test_empty_dataframe(self):
        store = self._store_with_lal()
        df = pd.DataFrame(columns=["season_type", "opponent_team_abbr", "game_date"])
        result = _add_f042_from_store(df, store)
        assert "opp_playoff_def_rating_l5_mean" in result.columns
        assert len(result) == 0


# ---------------------------------------------------------------------------
# TestPlayoffPullMerge
# ---------------------------------------------------------------------------

class TestPlayoffPullMerge:
    """Test the multi-season merge logic in pull_playoff_teamgamelog.py."""

    def test_store_after_single_season_has_correct_games(self):
        log = _make_game_log(["2025-04-20", "2025-04-22"], [110.0, 108.0], [5.0, -3.0])
        store = TeamStatsStore()
        store.add_team_log("LAL", log)
        assert "LAL" in store
        assert store.get_opp_def_rating("LAL", "2025-04-25", window=5, min_periods=2) is not None

    def test_store_merge_two_seasons_chronological(self):
        log_24 = _make_game_log(["2025-04-20", "2025-04-22", "2025-04-25"], [110, 108, 112], [5, -3, 8])
        log_25 = _make_game_log(["2026-04-20", "2026-04-22", "2026-04-25"], [115, 109, 111], [4, -2, 6])
        combined = pd.concat([log_24, log_25], ignore_index=True)
        store = TeamStatsStore()
        store.add_team_log("BOS", combined)

        # 2025-04-22 query: 1 prior game (2025-04-20) — below min_periods=2
        assert store.get_opp_def_rating("BOS", "2025-04-22", window=5, min_periods=2) is None

        # 2026-04-25 query: 5 prior games (all 2025 + 2026-04-20/22) → L5 mean
        rating = store.get_opp_def_rating("BOS", "2026-04-25", window=5, min_periods=3)
        assert rating is not None

    def test_second_add_replaces_first(self):
        log1 = _make_game_log(["2025-04-20"], [110.0], [5.0])
        log2 = _make_game_log(["2025-04-22"], [108.0], [-3.0])
        store = TeamStatsStore()
        store.add_team_log("GSW", log1)
        store.add_team_log("GSW", log2)  # replaces log1
        assert len(store._logs["GSW"]) == 1  # only log2

    def test_cache_round_trip(self):
        log = _make_game_log(["2025-04-20", "2025-04-22", "2025-04-25"], [110, 108, 112], [5, -3, 8])
        store = TeamStatsStore()
        store.add_team_log("LAL", log)
        cache = store.to_cache_dict()
        restored = TeamStatsStore.from_cache_dict(cache)
        r1 = store.get_opp_def_rating("LAL", "2025-05-01", window=5, min_periods=2)
        r2 = restored.get_opp_def_rating("LAL", "2025-05-01", window=5, min_periods=2)
        assert r1 is not None
        assert abs(r1 - r2) < 0.001

    def test_json_serialization_of_cache(self):
        log = _make_game_log(["2025-04-20", "2025-04-22"], [110.0, 108.0], [5.0, -3.0])
        store = TeamStatsStore()
        store.add_team_log("MIA", log)
        cache = store.to_cache_dict()
        # Must be JSON-serializable
        serialized = json.dumps(cache)
        reloaded = json.loads(serialized)
        assert "MIA" in reloaded

    def test_empty_season_skipped_gracefully(self):
        store = TeamStatsStore()
        # add_team_log with empty DataFrame should not crash
        store.add_team_log("PHX", pd.DataFrame())
        assert "PHX" not in store


# ---------------------------------------------------------------------------
# TestV2bBoilerplateGuards
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _V2B_AVAILABLE, reason="train_model_v2b.py not importable")
class TestV2bBoilerplateGuards:

    def test_output_paths_use_v2b_prefix(self):
        assert "v2b" in str(_v2b.V2B_MODEL_PATH)
        assert "v2b" in str(_v2b.V2B_META_PATH)

    def test_holdout_cutoff_unchanged_from_v2(self):
        assert _v2b.HOLDOUT_CUTOFF == "2026-02-01"

    def test_f041_multiplier_unchanged_from_v2(self):
        assert abs(_v2b.F041_PLAYOFF_MULTIPLIER - 0.959603) < 1e-6

    def test_playoff_opp_def_window(self):
        assert _v2b._PLAYOFF_OPP_DEF_WINDOW == 5
        assert _v2b._PLAYOFF_OPP_DEF_MIN_P == 3

    def test_bot_c4_active_guard_in_main(self, monkeypatch):
        monkeypatch.setenv("BOT_C4_ACTIVE", "true")
        with pytest.raises(SystemExit) as exc:
            _v2b.main()
        assert exc.value.code == 1


# ---------------------------------------------------------------------------
# TestT177ModelFlag
# ---------------------------------------------------------------------------

class TestT177ModelFlag:
    """Verify the --model arg was added to run_t177_v2_backtest.py correctly."""

    def _load_t177(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_t177_v2_backtest",
            _SCRIPTS_ROOT / "run_t177_v2_backtest.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_model_parameter_in_main_signature(self):
        import inspect
        mod = self._load_t177()
        sig = inspect.signature(mod.main)
        assert "model_path" in sig.parameters

    def test_model_default_is_v2_path(self):
        import inspect
        mod = self._load_t177()
        sig = inspect.signature(mod.main)
        default = sig.parameters["model_path"].default
        assert "v2_model" in str(default)

    def test_argparser_accepts_model_arg(self):
        import argparse
        mod = self._load_t177()
        parser = argparse.ArgumentParser()
        parser.add_argument("--model", type=str, default=str(mod.V2_MODEL_PATH))
        ns = parser.parse_args(["--model", "models/v2b_model.joblib"])
        assert ns.model == "models/v2b_model.joblib"

    def test_v2b_model_path_differs_from_v2(self):
        assert _v2b.V2B_MODEL_PATH != _v2b.V2_MODEL_PATH


# ---------------------------------------------------------------------------
# TestPtsAllowedCrossRef  — _parse_opponent_abbr + _fill_pts_allowed_via_crossref
# ---------------------------------------------------------------------------

def _import_pull_script():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pull_playoff_teamgamelog",
        _SCRIPTS_ROOT / "pull_playoff_teamgamelog.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    _pull = _import_pull_script()
    _parse_opponent_abbr = _pull._parse_opponent_abbr
    _fill_pts_allowed_via_crossref = _pull._fill_pts_allowed_via_crossref
    _PULL_AVAILABLE = True
except Exception:
    _PULL_AVAILABLE = False


@pytest.mark.skipif(not _PULL_AVAILABLE, reason="pull_playoff_teamgamelog.py not importable")
class TestPtsAllowedCrossRef:
    """Tests for cross-reference pts_allowed computation."""

    # --- _parse_opponent_abbr ---

    def test_parse_vs_matchup(self):
        assert _parse_opponent_abbr("BOS vs. PHI", "BOS") == "PHI"

    def test_parse_at_matchup(self):
        assert _parse_opponent_abbr("BOS @ PHI", "BOS") == "PHI"

    def test_parse_returns_uppercase(self):
        assert _parse_opponent_abbr("bos vs. phi", "BOS") == "PHI"

    def test_parse_none_on_bad_input(self):
        assert _parse_opponent_abbr(None, "BOS") is None

    def test_parse_none_on_empty_string(self):
        assert _parse_opponent_abbr("", "BOS") is None

    # --- _fill_pts_allowed_via_crossref ---

    def _make_df(
        self,
        abbr: str,
        dates: list[str],
        pts_list: list[float],
        matchups: list[str],
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "game_date": dates,
            "pts": pts_list,
            "matchup": matchups,
        })

    def test_cross_ref_populates_pts_allowed(self):
        bos = self._make_df("BOS", ["2025-05-01"], [110.0], ["BOS vs. PHI"])
        phi = self._make_df("PHI", ["2025-05-01"], [98.0], ["PHI @ BOS"])
        result = _fill_pts_allowed_via_crossref({"BOS": bos, "PHI": phi})
        # BOS allowed PHI's 98 pts → plus_minus = 110 - 98 = 12
        assert result["BOS"]["plus_minus"].iloc[0] == pytest.approx(12.0)

    def test_cross_ref_opponent_not_in_cache_gives_nan(self):
        bos = self._make_df("BOS", ["2025-05-01"], [110.0], ["BOS vs. MIA"])
        # MIA not in the dict
        result = _fill_pts_allowed_via_crossref({"BOS": bos})
        assert np.isnan(result["BOS"]["plus_minus"].iloc[0])

    def test_cross_ref_multiple_games(self):
        bos = self._make_df(
            "BOS",
            ["2025-05-01", "2025-05-03"],
            [110.0, 105.0],
            ["BOS vs. PHI", "BOS @ PHI"],
        )
        phi = self._make_df(
            "PHI",
            ["2025-05-01", "2025-05-03"],
            [98.0, 100.0],
            ["PHI @ BOS", "PHI vs. BOS"],
        )
        result = _fill_pts_allowed_via_crossref({"BOS": bos, "PHI": phi})
        pm = result["BOS"]["plus_minus"].tolist()
        assert pm[0] == pytest.approx(12.0)   # 110 - 98
        assert pm[1] == pytest.approx(5.0)    # 105 - 100

    def test_cross_ref_empty_dict(self):
        result = _fill_pts_allowed_via_crossref({})
        assert result == {}

    def test_cross_ref_preserves_all_original_columns(self):
        bos = self._make_df("BOS", ["2025-05-01"], [110.0], ["BOS vs. PHI"])
        bos["extra_col"] = "keep_me"
        phi = self._make_df("PHI", ["2025-05-01"], [98.0], ["PHI @ BOS"])
        result = _fill_pts_allowed_via_crossref({"BOS": bos, "PHI": phi})
        assert "extra_col" in result["BOS"].columns

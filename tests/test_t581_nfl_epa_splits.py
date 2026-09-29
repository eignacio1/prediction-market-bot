"""T-581: opt-in EPA-split retention + accessors. Incumbent path must be unchanged."""
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import (
    NFLIngestionClient, _NFL_TEAM_STATS_COLUMNS, _NFL_TEAM_STATS_SPLIT_COLUMNS)
from prediction_market_bot.c1_signal_ingestion.nfl_team_stats_store import NFLTeamStatsStore


def _stats(with_splits: bool) -> pd.DataFrame:
    rows = []
    # 4 games each for A and B (A home always); A: pass 2/rush 1, B: pass -1/rush 0.5
    for wk in range(1, 5):
        gid = f"2025_{wk:02d}_B_A"
        for team, opp, p, r in (("A", "B", 2.0, 1.0), ("B", "A", -1.0, 0.5)):
            row = {"season": 2025, "week": wk, "season_type": "REG", "game_id": gid,
                   "team": team, "opponent_team": opp, "off_epa": p + r}
            if with_splits:
                row.update(passing_epa=p, rushing_epa=r)
            rows.append(row)
    return pd.DataFrame(rows)


def _sched() -> pd.DataFrame:
    return pd.DataFrame({"game_id": [f"2025_{w:02d}_B_A" for w in range(1, 5)],
                         "gameday": [f"2025-09-{7 * w:02d}" for w in range(1, 5)]})


def test_split_columns_extend_not_replace():
    assert _NFL_TEAM_STATS_SPLIT_COLUMNS[:len(_NFL_TEAM_STATS_COLUMNS)] == _NFL_TEAM_STATS_COLUMNS
    assert _NFL_TEAM_STATS_SPLIT_COLUMNS[-2:] == ["passing_epa", "rushing_epa"]


def test_default_store_has_no_splits_and_aggregates_unchanged():
    base = NFLTeamStatsStore.build_from_team_stats(_stats(False), _sched())
    split = NFLTeamStatsStore.build_from_team_stats(_stats(True), _sched())
    d = "2025-12-01"
    assert base.get_off_epa("A", d) == split.get_off_epa("A", d)
    assert base.get_def_epa_allowed("A", d) == split.get_def_epa_allowed("A", d)
    assert base.get_pass_epa("A", d) is None  # no splits retained -> None, not an error


def test_split_accessors_values_and_defense_is_opponent_offense():
    s = NFLTeamStatsStore.build_from_team_stats(_stats(True), _sched())
    d = "2025-12-01"
    assert s.get_pass_epa("A", d) == pytest.approx(2.0)
    assert s.get_rush_epa("A", d) == pytest.approx(1.0)
    assert s.get_def_pass_epa_allowed("A", d) == pytest.approx(-1.0)  # B's passing vs A
    assert s.get_def_rush_epa_allowed("A", d) == pytest.approx(0.5)
    # exact decomposition of the aggregate
    assert s.get_off_epa("A", d) == pytest.approx(s.get_pass_epa("A", d) + s.get_rush_epa("A", d))


def test_ti01_no_lookahead_on_splits():
    s = NFLTeamStatsStore.build_from_team_stats(_stats(True), _sched())
    # as_of the day of game 4 must exclude game 4 (strict <): only 3 prior games -> still >= MIN_PERIODS
    assert s.get_pass_epa("A", "2025-09-28") is not None
    # as_of before game 3 leaves 2 games < MIN_PERIODS(3) -> None
    assert s.get_pass_epa("A", "2025-09-21") is None


def test_normalizer_include_splits_flag():
    c = NFLIngestionClient.__new__(NFLIngestionClient)
    raw = pd.DataFrame({"season": [2025], "week": [1], "season_type": ["REG"], "game_id": ["2025_01_B_A"], "team": ["A"],
                        "opponent_team": ["B"], "passing_epa": [2.0], "rushing_epa": [1.0],
                        "receiving_epa": [0.0]})
    default = c._normalize_team_stats_df(raw)
    split = c._normalize_team_stats_df(raw, include_splits=True)
    assert list(default.columns) == _NFL_TEAM_STATS_COLUMNS
    assert list(split.columns) == _NFL_TEAM_STATS_SPLIT_COLUMNS

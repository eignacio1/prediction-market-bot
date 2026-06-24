"""Tests for T-182: MLB C2 feature store.

Coverage:
  - _ip_to_decimal: baseball innings notation conversion (C1 fix)
  - _compute_rolling_batter_features: all rolling stats, TI-01, NaN for <3 games
  - MLBFeatureStore.compute_features_bulk:
      - single player, multiple players
      - SP overlay: known SP, unknown SP (None), insufficient SP history
      - park factor: known venue, unknown venue
      - opp_runs_allowed_l10: known team, unknown team
      - empty input
      - audit log events
  - MLBFeatureStore.assign_train_test_labels: chronological split, NaT exclusion
  - _PARK_FACTOR_HITS: Coors Field outlier, neutral default
  - Temporal integrity (TI-01): current game excluded from own features

No live HTTP calls. All dependencies are in-memory.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import _ip_to_decimal
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import MLBPitcherStatsStore
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import MLBTeamStatsStore
from prediction_market_bot.c2_feature_store.mlb_features import (
    MLB_FEATURE_VERSION,
    _PARK_FACTOR_HITS,
    MLBFeatureStore,
    _compute_rolling_batter_features,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_logger() -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = True
    return logger


def _make_store(snapshot_id: str = "SNAP-T182") -> tuple[MLBFeatureStore, MagicMock]:
    logger = _make_logger()
    store = MLBFeatureStore(logger=logger, snapshot_id=snapshot_id)
    return store, logger


def _batter_row(
    player_id: int = 1,
    player_name: str = "Test Player",
    game_id: int = 100,
    game_date: str = "2026-05-01",
    ab: int = 4,
    h: int = 1,
    doubles: int = 0,
    triples: int = 0,
    hr: int = 0,
    rbi: int = 0,
    bb: int = 0,
    k: int = 1,
    hbp: int = 0,
    sf: int = 0,
    is_home_game: int = 1,
    opponent_team_abbr: str = "NYY",
    team_abbreviation: str = "BOS",
    matchup: str = "BOS vs. NYY",
    season: str = "2026",
    season_type: str = "Regular Season",
    snapshot_id: str = "SNAP-T182",
) -> dict:
    return dict(
        player_id=player_id,
        player_name=player_name,
        team_id=111,
        team_abbreviation=team_abbreviation,
        game_id=game_id,
        game_date=game_date,
        season=season,
        season_type=season_type,
        matchup=matchup,
        is_home_game=is_home_game,
        opponent_team_abbr=opponent_team_abbr,
        ab=ab,
        h=h,
        doubles=doubles,
        triples=triples,
        hr=hr,
        rbi=rbi,
        bb=bb,
        k=k,
        hbp=hbp,
        sf=sf,
        snapshot_id=snapshot_id,
        ingestion_run_id="RUN-001",
        ingested_at="2026-05-01T00:00:00Z",
    )


def _n_game_log(
    n: int,
    player_id: int = 1,
    ab_per_game: int = 4,
    h_per_game: int = 1,
    doubles_per_game: int = 0,
    triples_per_game: int = 0,
    hr_per_game: int = 0,
    bb_per_game: int = 0,
    k_per_game: int = 1,
    hbp_per_game: int = 0,
    sf_per_game: int = 0,
    opponent_team_abbr: str = "NYY",
    is_home_game: int = 1,
    game_id_start: int = 100,
) -> pd.DataFrame:
    """Build an n-game batter log starting 2026-04-01."""
    rows = []
    for i in range(n):
        game_date = (date(2026, 4, 1) + timedelta(days=i)).isoformat()
        rows.append(_batter_row(
            player_id=player_id,
            game_id=game_id_start + i,
            game_date=game_date,
            ab=ab_per_game,
            h=h_per_game,
            doubles=doubles_per_game,
            triples=triples_per_game,
            hr=hr_per_game,
            bb=bb_per_game,
            k=k_per_game,
            hbp=hbp_per_game,
            sf=sf_per_game,
            opponent_team_abbr=opponent_team_abbr,
            is_home_game=is_home_game,
        ))
    return pd.DataFrame(rows)


def _empty_starters() -> dict:
    return {}


def _make_starters(game_ids: list[int], home_sp_id: int = 555, away_sp_id: int = 666, venue_name: str = "Fenway Park") -> dict:
    return {
        gid: {
            "home_sp_id": home_sp_id,
            "away_sp_id": away_sp_id,
            "venue_name": venue_name,
            "home_team_id": 111,
            "home_team_abbr": "BOS",
            "away_team_id": 147,
            "away_team_abbr": "NYY",
        }
        for gid in game_ids
    }


def _make_pitcher_store_with_sp(sp_id: int, n_starts: int = 5, era_per_start: float = 3.0) -> MLBPitcherStatsStore:
    """Pitcher store with n_starts for sp_id, each with 6 IP and computed ER for given ERA."""
    store = MLBPitcherStatsStore()
    ip_per_start = 6.0
    er_per_start = era_per_start * ip_per_start / 9.0
    rows = []
    for i in range(n_starts):
        rows.append({
            "game_date": (date(2026, 3, 1) + timedelta(days=i * 5)).isoformat(),
            "ip": ip_per_start,
            "er": er_per_start,
            "k": 7,
            "bb": 2,
            "is_start": 1,
        })
    store.add_pitcher_log(sp_id, pd.DataFrame(rows))
    return store


def _make_team_store(team_abbr: str = "NYY", n_games: int = 10, runs_allowed: float = 4.0) -> MLBTeamStatsStore:
    ts = MLBTeamStatsStore()
    rows = []
    for i in range(n_games):
        rows.append({
            "game_date": (date(2026, 3, 15) + timedelta(days=i)).isoformat(),
            "runs": 4,
            "runs_allowed": runs_allowed,
        })
    ts.add_team_log(team_abbr, pd.DataFrame(rows))
    return ts


# ===========================================================================
# C1 IP decimal conversion fix
# ===========================================================================


class TestIpToDecimal:
    def test_whole_innings(self):
        assert _ip_to_decimal("6.0") == pytest.approx(6.0)

    def test_one_out(self):
        assert _ip_to_decimal("5.1") == pytest.approx(5 + 1 / 3)

    def test_two_outs(self):
        assert _ip_to_decimal("5.2") == pytest.approx(5 + 2 / 3)

    def test_zero_innings(self):
        assert _ip_to_decimal("0.0") == pytest.approx(0.0)

    def test_zero_point_one(self):
        assert _ip_to_decimal("0.1") == pytest.approx(1 / 3)

    def test_zero_point_two(self):
        assert _ip_to_decimal("0.2") == pytest.approx(2 / 3)

    def test_integer_string(self):
        assert _ip_to_decimal("7") == pytest.approx(7.0)

    def test_float_input(self):
        assert _ip_to_decimal(6.0) == pytest.approx(6.0)

    def test_bad_input_returns_zero(self):
        assert _ip_to_decimal("not-a-number") == pytest.approx(0.0)

    def test_none_input_returns_zero(self):
        assert _ip_to_decimal(None) == pytest.approx(0.0)

    def test_one_inning_two_outs(self):
        assert _ip_to_decimal("1.2") == pytest.approx(1 + 2 / 3)


# ===========================================================================
# Park factor table
# ===========================================================================


class TestParkFactorTable:
    def test_coors_field_highest(self):
        assert _PARK_FACTOR_HITS["Coors Field"] > 1.10

    def test_oracle_park_pitcher_friendly(self):
        assert _PARK_FACTOR_HITS["Oracle Park"] < 1.0

    def test_all_values_in_reasonable_range(self):
        for venue, pf in _PARK_FACTOR_HITS.items():
            assert 0.90 <= pf <= 1.20, f"{venue}: {pf} outside expected range"

    def test_unknown_venue_not_in_table(self):
        assert "Nonexistent Stadium" not in _PARK_FACTOR_HITS


# ===========================================================================
# Rolling batter feature computation
# ===========================================================================


class TestComputeRollingBatterFeatures:
    def test_first_game_has_nan_features(self):
        df = _n_game_log(1)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        assert result["ba_l10"].isna().all()
        assert result["slg_l10"].isna().all()
        assert result["ops_l10"].isna().all()

    def test_fewer_than_min_periods_has_nan(self):
        df = _n_game_log(2)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        # Only 2 prior games available for game 2 → NaN for both (game 1 has 0 prior)
        assert result["ba_l10"].isna().all()

    def test_ba_correct_after_min_periods(self):
        # 4 AB, 2 H per game → BA should be 0.500
        df = _n_game_log(5, ab_per_game=4, h_per_game=2)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        ba_non_nan = result["ba_l10"].dropna()
        assert len(ba_non_nan) >= 2
        assert ba_non_nan.iloc[0] == pytest.approx(0.500, rel=1e-3)

    def test_ba_zero_ab_is_nan(self):
        # 0 AB → BA should be NaN (safe_div returns NaN on zero denominator)
        df = _n_game_log(5, ab_per_game=0, h_per_game=0)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        assert result["ba_l10"].isna().all()

    def test_slg_with_extra_bases(self):
        # 4 AB, 1 H, 1 double, 1 triple, 1 HR = 1+1+2+3=7 total bases in 4 AB = 0.625 + base H
        # Actually: h=4 (includes doubles, triples, HR) isn't how baseball works.
        # Let's use clean: 4 AB, 1 single (h=1, doubles=0, triples=0, hr=0) → SLG = 0.250
        df = _n_game_log(5, ab_per_game=4, h_per_game=1, doubles_per_game=0, triples_per_game=0, hr_per_game=0)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        slg_non_nan = result["slg_l10"].dropna()
        # 1 single = 1 total base / 4 AB = 0.250
        assert slg_non_nan.iloc[0] == pytest.approx(0.250, rel=1e-3)

    def test_slg_hr_counts_three_extra_bases(self):
        # 4 AB, 1 HR (h=1, hr=1) → total bases = h + 0 + 0 + 3*hr = 1 + 3 = 4? No.
        # Actually: h includes the HR (a HR is a hit). h=1 (the HR itself).
        # tb = h + doubles + 2*triples + 3*hr = 1 + 0 + 0 + 3 = 4. SLG = 4/4 = 1.000
        df = _n_game_log(5, ab_per_game=4, h_per_game=1, doubles_per_game=0, triples_per_game=0, hr_per_game=1)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        slg_non_nan = result["slg_l10"].dropna()
        # 1 HR = 4 total bases (h=1, hr=1 → tb = 1 + 3*1 = 4) / 4 AB = 1.000
        assert slg_non_nan.iloc[0] == pytest.approx(1.000, rel=1e-3)

    def test_obp_includes_walks(self):
        # 3 AB, 1 H, 1 BB, 0 HBP, 0 SF → OBP = (1+1+0)/(3+1+0+0) = 2/4 = 0.500
        df = _n_game_log(5, ab_per_game=3, h_per_game=1, bb_per_game=1)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        obp_non_nan = result["obp_l10"].dropna()
        assert obp_non_nan.iloc[0] == pytest.approx(0.500, rel=1e-3)

    def test_ops_equals_obp_plus_slg(self):
        df = _n_game_log(6, ab_per_game=4, h_per_game=1, bb_per_game=1)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        valid = result.dropna(subset=["ops_l10", "obp_l10", "slg_l10"])
        for _, row in valid.iterrows():
            assert row["ops_l10"] == pytest.approx(row["obp_l10"] + row["slg_l10"], rel=1e-6)

    def test_h_l10_mean(self):
        # h=2 per game for 5 games → after 3 prior, h_l10_mean = 2
        df = _n_game_log(5, ab_per_game=4, h_per_game=2)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        h_mean_non_nan = result["h_l10_mean"].dropna()
        # h_l10_mean = sum(h over window) / window
        # After 3 prior games: sum = 6, window=10, mean = 0.6 (not per-game avg but sum/window)
        assert h_mean_non_nan.iloc[0] == pytest.approx(3 * 2 / 10, rel=1e-3)

    def test_k_rate_l10(self):
        # 4 AB, 2 K → K rate = 0.500
        df = _n_game_log(5, ab_per_game=4, k_per_game=2)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        k_rate_non_nan = result["k_rate_l10"].dropna()
        assert k_rate_non_nan.iloc[0] == pytest.approx(0.500, rel=1e-3)

    def test_bb_rate_l10(self):
        # 4 AB, 1 BB → BB rate = 0.250
        df = _n_game_log(5, ab_per_game=4, bb_per_game=1)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        bb_rate_non_nan = result["bb_rate_l10"].dropna()
        assert bb_rate_non_nan.iloc[0] == pytest.approx(0.250, rel=1e-3)

    def test_hr_rate_l10(self):
        # 4 AB, 1 HR → HR rate = 0.250
        df = _n_game_log(5, ab_per_game=4, hr_per_game=1)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        hr_rate_non_nan = result["hr_rate_l10"].dropna()
        assert hr_rate_non_nan.iloc[0] == pytest.approx(0.250, rel=1e-3)

    def test_ti01_current_game_excluded(self):
        # Row N should NOT include its own stats. If game N has h=10, BA should not reflect that.
        rows = [_batter_row(game_id=100+i, game_date=(date(2026, 4, 1)+timedelta(days=i)).isoformat(), h=1, ab=4) for i in range(4)]
        # Add a 5th game with h=10 (outlier)
        rows.append(_batter_row(game_id=104, game_date="2026-04-05", h=10, ab=4))
        df = pd.DataFrame(rows)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        last_row = result.iloc[-1]
        # BA for game 5 should be based on prior 4 games (h=1 each), NOT the h=10 in game 5
        assert last_row["ba_l10"] == pytest.approx(0.250, rel=1e-3)  # 4*1/4*4 = 4/16 = 0.25

    def test_days_rest_correct(self):
        # Games on consecutive days → days_rest = 1
        df = _n_game_log(5)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        # First game: days_rest = NaN
        assert pd.isna(result.iloc[0]["days_rest"])
        # Subsequent games (consecutive days): days_rest = 1
        for i in range(1, 5):
            assert result.iloc[i]["days_rest"] == pytest.approx(1.0)

    def test_b2b_flag_set_for_consecutive_days(self):
        df = _n_game_log(5)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        # Games 2-5 are back-to-back (1-day rest)
        for i in range(1, 5):
            assert result.iloc[i]["b2b_flag"] == 1.0

    def test_b2b_flag_not_set_with_rest(self):
        # Insert 2-day gaps between games
        rows = []
        for i in range(5):
            gd = (date(2026, 4, 1) + timedelta(days=i * 2)).isoformat()  # every other day
            rows.append(_batter_row(game_id=100+i, game_date=gd))
        df = pd.DataFrame(rows)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        # All games have 2-day rest → b2b_flag = 0
        for i in range(1, 5):
            assert result.iloc[i]["b2b_flag"] == 0.0

    def test_temporal_cutoff_is_prior_game_date(self):
        df = _n_game_log(5)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        # temporal_cutoff for game 2 should be game 1's date
        cutoff = pd.to_datetime(result.iloc[1]["temporal_cutoff"]).date()
        assert cutoff == date(2026, 4, 1)

    def test_first_game_temporal_cutoff_is_nat(self):
        df = _n_game_log(3)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        assert pd.isna(result.iloc[0]["temporal_cutoff"])

    def test_window_respected_after_many_games(self):
        # 15 games with h=1 except game 1-5 where h=3. Window=10 → after game 15,
        # only games 6-14 (9 prior) are in window (or up to 10). All h=1 after game 5.
        rows = []
        for i in range(15):
            h = 3 if i < 5 else 1
            gd = (date(2026, 4, 1) + timedelta(days=i)).isoformat()
            rows.append(_batter_row(game_id=100+i, game_date=gd, h=h, ab=4))
        df = pd.DataFrame(rows)
        result = _compute_rolling_batter_features(df, window=10, min_periods=3)
        # game 15 (index 14): prior games 5-14 → last 10 are games 5-14
        # games 5,6,...14: h values = 3,1,1,1,1,1,1,1,1,1 (index 4=game5→h=3, then 1)
        # Actually index 5+ have h=1. Window of 10 before row 14: rows 4..13 (0-indexed)
        # row4: h=3, rows5..13: h=1 (9 games of h=1) → sum=3+9=12 for 10 games
        last_ba = result.iloc[14]["ba_l10"]
        # sum(h) = 3 + 9*1 = 12 (games index 4..13), sum(ab) = 10*4 = 40 → BA = 12/40 = 0.300
        assert last_ba == pytest.approx(0.300, rel=1e-3)


# ===========================================================================
# MLBFeatureStore.compute_features_bulk
# ===========================================================================


class TestComputeFeaturesBulk:
    def test_empty_input_returns_empty_df(self):
        store, logger = _make_store()
        empty = pd.DataFrame(columns=list(_batter_row().keys()))
        ok, df = store.compute_features_bulk(
            empty, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore()
        )
        assert ok is True
        assert df.empty
        logger.log.assert_called()

    def test_feature_version_set(self):
        store, _ = _make_store()
        df_in = _n_game_log(5)
        _, df_out = store.compute_features_bulk(
            df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore()
        )
        assert (df_out["feature_version"] == MLB_FEATURE_VERSION).all()

    def test_single_player_rolling_features_present(self):
        store, _ = _make_store()
        df_in = _n_game_log(6, ab_per_game=4, h_per_game=1)
        _, df_out = store.compute_features_bulk(
            df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore()
        )
        assert "ba_l10" in df_out.columns
        assert "slg_l10" in df_out.columns
        assert "obp_l10" in df_out.columns
        assert "ops_l10" in df_out.columns
        assert "h_l10_mean" in df_out.columns
        assert "k_rate_l10" in df_out.columns
        assert "bb_rate_l10" in df_out.columns
        assert "hr_rate_l10" in df_out.columns

    def test_multiple_players_partitioned_correctly(self):
        # Two players with different BA profiles — their rolling stats must not cross-contaminate
        df_p1 = _n_game_log(6, player_id=1, ab_per_game=4, h_per_game=2, game_id_start=100)
        df_p2 = _n_game_log(6, player_id=2, ab_per_game=4, h_per_game=0, game_id_start=200)
        df_in = pd.concat([df_p1, df_p2], ignore_index=True)
        store, _ = _make_store()
        _, df_out = store.compute_features_bulk(
            df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore()
        )
        p1_rows = df_out[df_out["player_id"] == 1].dropna(subset=["ba_l10"])
        p2_rows = df_out[df_out["player_id"] == 2].dropna(subset=["ba_l10"])
        assert (p1_rows["ba_l10"] > 0).all()  # P1 hits
        assert (p2_rows["ba_l10"] == 0.0).all()  # P2 no hits (0 H / 4 AB = exactly 0.0)

    def test_rows_with_no_prior_games_have_nan_rolling(self):
        store, _ = _make_store()
        df_in = _n_game_log(1)
        _, df_out = store.compute_features_bulk(
            df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore()
        )
        assert df_out["ba_l10"].isna().all()

    def test_sp_overlay_known_sp(self):
        store, _ = _make_store()
        game_ids = list(range(100, 106))
        starters = _make_starters(game_ids, home_sp_id=555, away_sp_id=666, venue_name="Yankee Stadium")
        pitcher_store = _make_pitcher_store_with_sp(sp_id=666, n_starts=5, era_per_start=3.0)
        df_in = _n_game_log(6, is_home_game=1, game_id_start=100)  # home batter → opp SP is away (666)
        _, df_out = store.compute_features_bulk(df_in, starters, pitcher_store, MLBTeamStatsStore())
        known_rows = df_out[df_out["opp_sp_is_known"] == 1.0]
        assert len(known_rows) == 6
        # ERA values should not be NaN for rows with sufficient SP history (after game 1)
        # SP data is from 2026-03-01 to 2026-03-21 (5 starts); batter games start 2026-04-01
        # All 6 batter games are after the SP starts → SP ERA should be non-NaN
        era_values = known_rows["opp_sp_era_l5"].dropna()
        assert len(era_values) == 6

    def test_sp_overlay_unknown_sp(self):
        store, _ = _make_store()
        # Starters with None sp_id
        game_ids = list(range(100, 106))
        starters = {gid: {"home_sp_id": None, "away_sp_id": None, "venue_name": "Fenway Park",
                          "home_team_id": 111, "home_team_abbr": "BOS",
                          "away_team_id": 147, "away_team_abbr": "NYY"} for gid in game_ids}
        pitcher_store = MLBPitcherStatsStore()
        df_in = _n_game_log(6, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, starters, pitcher_store, MLBTeamStatsStore())
        assert (df_out["opp_sp_is_known"] == 0.0).all()
        assert df_out["opp_sp_era_l5"].isna().all()
        assert df_out["opp_sp_k9_l5"].isna().all()
        assert df_out["opp_sp_bb9_l5"].isna().all()

    def test_sp_overlay_insufficient_sp_history_returns_nan(self):
        store, _ = _make_store()
        game_ids = list(range(100, 106))
        starters = _make_starters(game_ids, away_sp_id=999)
        # SP 999 has only 1 start — below min_periods=2 → NaN stats
        ps = MLBPitcherStatsStore()
        ps.add_pitcher_log(999, pd.DataFrame([{
            "game_date": "2026-03-28",
            "ip": 5.0, "er": 2, "k": 6, "bb": 2, "is_start": 1,
        }]))
        df_in = _n_game_log(6, is_home_game=1, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, starters, ps, MLBTeamStatsStore())
        # sp_is_known=1 (SP ID is known) but era stats are NaN (insufficient history)
        assert (df_out["opp_sp_is_known"] == 1.0).all()
        assert df_out["opp_sp_era_l5"].isna().all()

    def test_park_factor_known_venue(self):
        store, _ = _make_store()
        game_ids = list(range(100, 106))
        starters = _make_starters(game_ids, venue_name="Coors Field")
        df_in = _n_game_log(6, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, starters, MLBPitcherStatsStore(), MLBTeamStatsStore())
        assert (df_out["park_factor_hits"] > 1.10).all()
        assert np.allclose(df_out["park_factor_hits"].values, 1.120)

    def test_park_factor_unknown_venue_defaults_to_neutral(self):
        store, _ = _make_store()
        game_ids = list(range(100, 106))
        starters = _make_starters(game_ids, venue_name="Mystery Field")
        df_in = _n_game_log(6, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, starters, MLBPitcherStatsStore(), MLBTeamStatsStore())
        assert np.allclose(df_out["park_factor_hits"].values, 1.000)

    def test_park_factor_game_not_in_starters_defaults_to_neutral(self):
        store, _ = _make_store()
        # No starters dict at all
        df_in = _n_game_log(6, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        assert np.allclose(df_out["park_factor_hits"].values, 1.000)

    def test_opp_runs_allowed_populated(self):
        store, _ = _make_store()
        ts = _make_team_store("NYY", n_games=10, runs_allowed=3.5)
        df_in = _n_game_log(6, opponent_team_abbr="NYY", game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), ts)
        non_nan = df_out["opp_runs_allowed_l10"].dropna()
        assert len(non_nan) > 0
        assert np.allclose(non_nan.values, 3.5)

    def test_opp_runs_allowed_unknown_team_is_nan(self):
        store, _ = _make_store()
        ts = MLBTeamStatsStore()  # empty
        df_in = _n_game_log(6, opponent_team_abbr="ZZZ", game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), ts)
        assert df_out["opp_runs_allowed_l10"].isna().all()

    def test_train_test_label_initializes_to_none(self):
        store, _ = _make_store()
        df_in = _n_game_log(5, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        assert df_out["train_test_label"].isna().all()

    def test_audit_log_called_on_start_and_complete(self):
        store, logger = _make_store()
        df_in = _n_game_log(5, game_id_start=100)
        store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        events = [call.args[1] for call in logger.log.call_args_list]
        assert "mlb_feature_derivation_start" in events
        assert "mlb_feature_derivation_complete" in events

    def test_audit_log_on_empty_input(self):
        store, logger = _make_store()
        empty = pd.DataFrame(columns=list(_batter_row().keys()))
        store.compute_features_bulk(empty, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        events = [call.args[1] for call in logger.log.call_args_list]
        assert "mlb_feature_derivation_start" in events
        assert "mlb_feature_derivation_complete" in events

    def test_temporal_integrity_warning_logged_when_no_prior_games(self):
        store, logger = _make_store()
        df_in = _n_game_log(1, game_id_start=100)  # Only 1 game → temporal_cutoff = NaT
        store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        events = [call.args[1] for call in logger.log.call_args_list]
        assert "temporal_integrity_warning" in events

    def test_logger_failure_returns_all_ok_false(self):
        logger = MagicMock()
        logger.log.return_value = False
        store = MLBFeatureStore(logger=logger, snapshot_id="SNAP-X")
        df_in = _n_game_log(5, game_id_start=100)
        ok, _ = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        assert ok is False

    def test_feature_run_id_column_present(self):
        store, _ = _make_store()
        df_in = _n_game_log(5, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        assert "feature_run_id" in df_out.columns
        assert df_out["feature_run_id"].str.startswith("C2MLB-").all()

    def test_sp_k9_and_bb9_populated_for_known_sp(self):
        store, _ = _make_store()
        game_ids = list(range(100, 106))
        starters = _make_starters(game_ids, away_sp_id=777)
        pitcher_store = _make_pitcher_store_with_sp(sp_id=777, n_starts=5, era_per_start=3.0)
        df_in = _n_game_log(6, is_home_game=1, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, starters, pitcher_store, MLBTeamStatsStore())
        # Expect non-NaN K9 and BB9 since SP has 5 starts of history
        k9_non_nan = df_out["opp_sp_k9_l5"].dropna()
        assert len(k9_non_nan) == 6
        # K9 = (7 * 5) / (6.0 * 5) * 9 = 35/30 * 9 = 10.5
        assert k9_non_nan.iloc[0] == pytest.approx(10.5, rel=1e-3)

    def test_away_batter_gets_home_sp_as_opponent(self):
        store, _ = _make_store()
        game_ids = list(range(100, 106))
        # home_sp=555 (for away batter's opponent), away_sp=666
        starters = _make_starters(game_ids, home_sp_id=555, away_sp_id=666, venue_name="Fenway Park")
        ps = _make_pitcher_store_with_sp(sp_id=555, n_starts=5)
        df_in = _n_game_log(6, is_home_game=0, game_id_start=100)  # away batter
        _, df_out = store.compute_features_bulk(df_in, starters, ps, MLBTeamStatsStore())
        # Away batter faces home SP (555), not away SP (666)
        assert (df_out["opp_sp_is_known"] == 1.0).all()
        assert df_out["opp_sp_era_l5"].dropna().shape[0] == 6


# ===========================================================================
# MLBFeatureStore.assign_train_test_labels
# ===========================================================================


class TestAssignTrainTestLabels:
    def _make_feature_df(self, n: int = 15) -> pd.DataFrame:
        store, _ = _make_store()
        df_in = _n_game_log(n, game_id_start=100)
        _, df_out = store.compute_features_bulk(df_in, _empty_starters(), MLBPitcherStatsStore(), MLBTeamStatsStore())
        return df_out

    def test_chronological_labels_assigned(self):
        store, _ = _make_store()
        df = self._make_feature_df(15)
        # Games: 2026-04-01 to 2026-04-15
        ok, labeled = store.assign_train_test_labels(df, "2026-04-08", "2026-04-12")
        assert ok is True
        train_rows = labeled[labeled["train_test_label"] == "TRAIN"]
        val_rows = labeled[labeled["train_test_label"] == "VALIDATION"]
        test_rows = labeled[labeled["train_test_label"] == "TEST"]
        assert len(train_rows) > 0
        assert len(val_rows) > 0
        assert len(test_rows) > 0

    def test_nat_temporal_cutoff_excluded_from_all_splits(self):
        store, _ = _make_store()
        df = self._make_feature_df(15)
        _, labeled = store.assign_train_test_labels(df, "2026-04-08", "2026-04-12")
        nat_rows = labeled[labeled["temporal_cutoff"].isna()]
        assert (nat_rows["train_test_label"].isna()).all()

    def test_train_end_date_inclusive(self):
        store, _ = _make_store()
        df = self._make_feature_df(10)
        _, labeled = store.assign_train_test_labels(df, "2026-04-05", "2026-04-08")
        # 2026-04-05 game should be in TRAIN
        row = labeled[pd.to_datetime(labeled["game_date"]) == pd.Timestamp("2026-04-05")]
        if len(row) > 0 and pd.notna(row.iloc[0]["temporal_cutoff"]):
            assert row.iloc[0]["train_test_label"] == "TRAIN"

    def test_val_end_date_inclusive(self):
        store, _ = _make_store()
        df = self._make_feature_df(10)
        _, labeled = store.assign_train_test_labels(df, "2026-04-05", "2026-04-08")
        row = labeled[pd.to_datetime(labeled["game_date"]) == pd.Timestamp("2026-04-08")]
        if len(row) > 0 and pd.notna(row.iloc[0]["temporal_cutoff"]):
            assert row.iloc[0]["train_test_label"] == "VALIDATION"

    def test_audit_log_called(self):
        store, logger = _make_store()
        df = self._make_feature_df(10)
        store.assign_train_test_labels(df, "2026-04-05", "2026-04-08")
        events = [call.args[1] for call in logger.log.call_args_list]
        assert "mlb_train_test_split_applied" in events

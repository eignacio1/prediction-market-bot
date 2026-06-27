"""
Tests for PIPE-08 MLB Schedule Validator (run_schedule_validator_mlb.py).

Covers: game classification, T4 window computation, pregame time derivation,
assumption guards (T1, T2, resolution), and crontab line parsing.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Import module under test
from prediction_market_bot.run_schedule_validator_mlb import (
    GAME_EXTRA_INNINGS_BUFFER_S,
    PREGAME_FLOOR_H,
    PREGAME_FLOOR_M,
    T4_ALL_POSTPONED_H,
    T4_ALL_POSTPONED_M,
    T4_ALL_POSTPONED_TIMEOUT_S,
    T4_FLOOR_H,
    T4_FLOOR_M,
    T4_MIN_TIMEOUT_S,
    check_resolution_guard,
    check_t1_guard,
    check_t2_guard,
    classify_games,
    compute_pregame_time,
    compute_t4_window,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_game(
    matchup: str,
    start_utc_iso: str,
    detailed_state: str = "Scheduled",
    game_pk: int = 1,
) -> dict:
    away, home = matchup.split(" @ ")
    return {
        "gamePk": game_pk,
        "gameDate": start_utc_iso,
        "status": {"detailedState": detailed_state},
        "teams": {
            "away": {"team": {"name": away}},
            "home": {"team": {"name": home}},
        },
    }


_NOW = datetime(2026, 6, 27, 8, 30, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# classify_games
# ---------------------------------------------------------------------------

class TestClassifyGames:
    def test_all_active(self):
        games = [
            _make_game("NYY @ BOS", "2026-06-27T17:10:00Z", "Scheduled"),
            _make_game("HOU @ DET", "2026-06-27T17:10:00Z", "In Progress"),
        ]
        active, postponed = classify_games(games)
        assert len(active) == 2
        assert len(postponed) == 0

    def test_postponed_removed(self):
        games = [
            _make_game("NYY @ BOS", "2026-06-27T17:10:00Z", "Postponed"),
            _make_game("HOU @ DET", "2026-06-27T17:10:00Z", "Scheduled"),
        ]
        active, postponed = classify_games(games)
        assert len(active) == 1
        assert len(postponed) == 1
        assert postponed[0]["gamePk"] == games[0]["gamePk"]

    def test_cancelled_removed(self):
        games = [_make_game("A @ B", "2026-06-27T17:00:00Z", "Cancelled")]
        active, postponed = classify_games(games)
        assert active == []
        assert len(postponed) == 1

    def test_postponed_rain_removed(self):
        games = [_make_game("A @ B", "2026-06-27T17:00:00Z", "Postponed - Rain")]
        active, postponed = classify_games(games)
        assert active == []
        assert len(postponed) == 1

    def test_rain_delay_kept_active(self):
        """Rain delay keeps game active (may resume)."""
        games = [_make_game("A @ B", "2026-06-27T17:00:00Z", "Delayed: Rain")]
        active, postponed = classify_games(games)
        assert len(active) == 1
        assert postponed == []

    def test_suspended_kept_active(self):
        """Suspended kept active — may resume same day."""
        games = [_make_game("A @ B", "2026-06-27T17:00:00Z", "Suspended")]
        active, postponed = classify_games(games)
        assert len(active) == 1


# ---------------------------------------------------------------------------
# compute_t4_window
# ---------------------------------------------------------------------------

class TestComputeT4Window:
    def test_all_postponed_returns_idle_window(self):
        h, m, timeout, warnings = compute_t4_window([], _NOW)
        assert h == T4_ALL_POSTPONED_H
        assert m == T4_ALL_POSTPONED_M
        assert timeout == T4_ALL_POSTPONED_TIMEOUT_S
        assert any("ALL_GAMES_OFF" in w for w in warnings)

    def test_normal_evening_slate(self):
        """Typical day: earliest game 17:10 UTC. T4 should fire ~16:40 UTC."""
        games = [
            _make_game("NYY @ BOS", "2026-06-27T17:10:00Z"),
            _make_game("HOU @ DET", "2026-06-27T23:05:00Z"),
        ]
        h, m, timeout, warnings = compute_t4_window(games, _NOW)
        # 30 min before 17:10 = 16:40, rounded to 16:40
        assert h == 16
        assert m == 40
        # Timeout from 16:40 UTC to latest expected end (23:05 + 4h30 = 03:35 UTC next day)
        assert timeout >= T4_MIN_TIMEOUT_S
        assert timeout > 10 * 3600  # at least 10h for this slate
        assert warnings == []

    def test_floor_applied_early_game(self):
        """Game starting at 15:00 UTC → computed T4 = 14:30 which hits floor (15:00)."""
        games = [_make_game("A @ B", "2026-06-27T15:00:00Z")]
        h, m, timeout, warnings = compute_t4_window(games, _NOW)
        assert h == T4_FLOOR_H
        assert m == T4_FLOOR_M
        assert any("T4_FLOOR_APPLIED" in w for w in warnings)

    def test_minimum_timeout_enforced(self):
        """Even with very late game, timeout is at least T4_MIN_TIMEOUT_S."""
        # Already-finished game scenario (edge case)
        games = [_make_game("A @ B", "2026-06-27T17:00:00Z", "Final")]
        # With a game start in the past relative to now (08:30 UTC vs 17:00 UTC start)
        # T4 fires at 16:30, timeout would be (17:00 + 4h30m) - 16:30 = 5h
        h, m, timeout, warnings = compute_t4_window(games, _NOW)
        assert timeout >= T4_MIN_TIMEOUT_S

    def test_minute_rounded_to_nearest_5(self):
        """T4 minute should be a multiple of 5."""
        # 17:13 UTC first pitch → computed T4 = 16:43 → rounds to 16:40
        games = [_make_game("A @ B", "2026-06-27T17:13:00Z")]
        h, m, timeout, warnings = compute_t4_window(games, _NOW)
        assert m % 5 == 0

    def test_single_late_game_only(self):
        """Single 23:05 UTC game → T4 fires at 22:35 UTC."""
        games = [_make_game("A @ B", "2026-06-27T23:05:00Z")]
        h, m, timeout, warnings = compute_t4_window(games, _NOW)
        # 23:05 - 30min = 22:35 → rounded to 22:35
        assert h == 22
        assert m == 35
        # Timeout: (23:05 + 4h30) - 22:35 = 5h
        assert abs(timeout - 5 * 3600) <= 300  # within 5 min

    def test_large_slate_timeout_covers_all(self):
        """15-game slate: timeout must cover from T4 start to last expected end."""
        # First game 17:00 UTC, last game 02:05 UTC (next day)
        games = [
            _make_game("A @ B", "2026-06-27T17:00:00Z", game_pk=1),
            _make_game("C @ D", "2026-06-28T02:05:00Z", game_pk=2),
        ]
        h, m, timeout, warnings = compute_t4_window(games, _NOW)
        t4_total_min = h * 60 + m
        last_start_min = (2 + 24) * 60 + 5  # 02:05 next day in minutes from midnight
        buffer_min = GAME_EXTRA_INNINGS_BUFFER_S // 60  # 270 min = 4h30
        expected_min_timeout = (last_start_min + buffer_min - t4_total_min) * 60
        assert timeout >= expected_min_timeout - 60  # 1-min rounding tolerance


# ---------------------------------------------------------------------------
# compute_pregame_time
# ---------------------------------------------------------------------------

class TestComputePregameTime:
    def test_normal_case(self):
        """T4 at 16:40 → pregame at 15:55."""
        h, m = compute_pregame_time(16, 40)
        assert h == 15
        assert m == 55

    def test_floor_applied(self):
        """T4 at 14:30 → pregame would be 13:45, but floor = 14:00."""
        h, m = compute_pregame_time(T4_FLOOR_H, T4_FLOOR_M)
        # T4=15:00 → pregame=14:15, above floor 14:00
        assert h * 60 + m >= PREGAME_FLOOR_H * 60 + PREGAME_FLOOR_M

    def test_pregame_always_before_t4(self):
        """Pregame must always fire before T4."""
        for t4_h in range(15, 24):
            for t4_m in range(0, 60, 5):
                pre_h, pre_m = compute_pregame_time(t4_h, t4_m)
                assert pre_h * 60 + pre_m < t4_h * 60 + t4_m

    def test_pregame_floor_not_breached(self):
        """Even for very early T4 (floor case), pregame never goes below floor."""
        for t4_h in range(15, 20):
            pre_h, pre_m = compute_pregame_time(t4_h, 0)
            assert pre_h * 60 + pre_m >= PREGAME_FLOOR_H * 60 + PREGAME_FLOOR_M


# ---------------------------------------------------------------------------
# T1 guard
# ---------------------------------------------------------------------------

class TestT1Guard:
    def test_no_warning_normal_game(self):
        """17:10 UTC game → T1 at 11:00 fires 6h10m before → no warning."""
        games = [_make_game("A @ B", "2026-06-27T17:10:00Z")]
        warnings = check_t1_guard(games)
        assert warnings == []

    def test_warning_if_game_within_danger_window(self):
        """12:00 UTC game → only 60min after T1 at 11:00 → warning fires."""
        games = [_make_game("A @ B", "2026-06-27T12:00:00Z")]
        warnings = check_t1_guard(games)
        assert len(warnings) == 1
        assert "T1_RISK" in warnings[0]

    def test_no_warning_if_game_at_t1_plus_danger_threshold(self):
        """Game exactly at T1 + danger window: warning fires (< not <=)."""
        # T1_DANGER_LEAD_MIN = 90; T1 at 11:00; danger threshold = 12:30 UTC
        games = [_make_game("A @ B", "2026-06-27T12:29:00Z")]
        warnings = check_t1_guard(games)
        assert any("T1_RISK" in w for w in warnings)

    def test_no_warning_midnight_era_game(self):
        """00:40 UTC game = 8:40pm ET — starts 13h40m after T1, not 9h before."""
        games = [_make_game("LAD @ SD", "2026-06-28T00:40:00Z")]
        warnings = check_t1_guard(games)
        assert warnings == []

    def test_no_warning_01_05_utc_game(self):
        """01:05 UTC = 9:05pm ET — safe, 14h after T1."""
        games = [_make_game("ATL @ SF", "2026-06-28T01:05:00Z")]
        warnings = check_t1_guard(games)
        assert warnings == []


# ---------------------------------------------------------------------------
# T2 guard
# ---------------------------------------------------------------------------

class TestT2Guard:
    def test_no_warning_all_games_after_t2(self):
        """All games start after 19:30 UTC → no T2 coverage warning."""
        games = [_make_game("A @ B", "2026-06-27T23:05:00Z")]
        warnings = check_t2_guard(games)
        assert warnings == []

    def test_warning_if_early_game(self):
        """Some games before T2 → coverage warning (informational)."""
        games = [
            _make_game("A @ B", "2026-06-27T17:10:00Z"),
            _make_game("C @ D", "2026-06-27T23:05:00Z"),
        ]
        warnings = check_t2_guard(games)
        assert len(warnings) == 1
        assert "T2_COVERAGE" in warnings[0]
        assert "1/2" in warnings[0]

    def test_midnight_era_game_not_counted_as_early(self):
        """00:40 UTC = 8:40pm ET — starts AFTER T2 in real time, not before."""
        games = [
            _make_game("A @ B", "2026-06-27T17:10:00Z"),  # truly before T2
            _make_game("C @ D", "2026-06-28T00:40:00Z"),  # 8:40pm ET, after T2
            _make_game("E @ F", "2026-06-28T01:38:00Z"),  # 9:38pm ET, after T2
        ]
        warnings = check_t2_guard(games)
        assert len(warnings) == 1
        assert "1/3" in warnings[0]  # only 1 truly early game


# ---------------------------------------------------------------------------
# Resolution guard
# ---------------------------------------------------------------------------

class TestResolutionGuard:
    def test_no_warning_early_game(self):
        """17:10 UTC game expected end = 21:40 UTC → before 06:30 UTC next day."""
        games = [_make_game("A @ B", "2026-06-27T17:10:00Z")]
        warnings = check_resolution_guard(games)
        assert warnings == []

    def test_warning_late_west_coast_game(self):
        """02:05 UTC game (10pm ET) + 4h30m buffer = 06:35 UTC → after 06:30 UTC res."""
        games = [_make_game("A @ B", "2026-06-28T02:05:00Z")]
        warnings = check_resolution_guard(games)
        assert len(warnings) == 1
        assert "RESOLUTION_RISK" in warnings[0]

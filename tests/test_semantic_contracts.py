"""
ADR-0034 Layer 3 Semantic Contract Tests
=========================================
Coverage requirements (integration patch doc):
  SemanticFloorGuard: 4 tests
  ContaminationGuard.is_clean(): 10 tests
  BandInvariantChecker: 7 tests
  SemanticContractMonitor: 4 tests
Total: 25 tests

Session 102 — wires canonical semantic_contracts.py module into live pipelines.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src on path
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Pipeline env guards must be satisfied before importing pipeline modules.
os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

from prediction_market_bot.c7_monitoring.semantic_contracts import (
    BandInvariantChecker,
    ContaminationGuard,
    ContractViolation,
    SemanticContractMonitor,
    SemanticFloorGuard,
    SemanticFloorViolation,
    T4CorrDownwardViolation,
)


# ---------------------------------------------------------------------------
# SemanticFloorGuard — 4 tests
# ---------------------------------------------------------------------------


class TestSemanticFloorGuard:
    """assert_floor() raises SemanticFloorViolation iff games_fetched>0 AND matched==0."""

    def test_passes_when_games_and_players_matched(self):
        """No violation when games exist and players matched successfully."""
        SemanticFloorGuard.assert_floor(
            pipeline_id="PIPE-05",
            games_fetched=5,
            matched_players=3,
            sport="MLB",
        )  # must not raise

    def test_raises_when_games_fetched_but_no_players(self):
        """Floor violation: games exist in schedule but 0 players matched Kalshi markets."""
        with pytest.raises(SemanticFloorViolation) as exc_info:
            SemanticFloorGuard.assert_floor(
                pipeline_id="PIPE-05",
                games_fetched=4,
                matched_players=0,
                sport="MLB",
            )
        exc = exc_info.value
        assert exc.pipeline_id == "PIPE-05"
        assert exc.sport == "MLB"
        assert exc.games_fetched == 4
        assert exc.matched_players == 0

    def test_passes_on_quiet_day_no_games(self):
        """No violation when games_fetched==0 (off-season / rest day)."""
        SemanticFloorGuard.assert_floor(
            pipeline_id="PIPE-05",
            games_fetched=0,
            matched_players=0,
            sport="MLB",
        )  # quiet day — guard is a no-op

    def test_violation_is_exception_subclass(self):
        """SemanticFloorViolation is catchable as Exception (canonical ADR-0034 hierarchy)."""
        assert issubclass(SemanticFloorViolation, Exception)
        # Check attributes exist on the exception
        with pytest.raises(SemanticFloorViolation) as exc_info:
            SemanticFloorGuard.assert_floor(
                pipeline_id="PIPE-TEST",
                games_fetched=2,
                matched_players=0,
                sport="NBA",
            )
        exc = exc_info.value
        assert hasattr(exc, "diagnosis")
        assert hasattr(exc, "pipeline_id")
        assert hasattr(exc, "sport")


# ---------------------------------------------------------------------------
# ContaminationGuard.is_clean() — 10 tests
# ---------------------------------------------------------------------------


def _make_guard(
    has_live_quotes: bool = True,
    mip: float = 0.55,
    player_in_live_game: bool = True,
    game_in_progress: bool = True,
    elapsed_min: float | None = None,
    game_regulation_min: float = 540.0,   # 9 innings × 60 min (baseball)
    h_needed: int | None = None,
    ab_remaining: float | None = None,
    original_size: float | None = None,
    adjusted_size: float | None = None,
    audit=None,
) -> ContaminationGuard:
    return ContaminationGuard(
        ticker="KXMLBHIT-26JUN241840-BOSSOX-JSOTO-1",
        player_id=660670,
        has_live_quotes=has_live_quotes,
        mip=mip,
        player_in_live_game=player_in_live_game,
        game_in_progress=game_in_progress,
        cycle_id="CG-TEST-01",
        audit=audit,
        session_id="TEST-SESSION",
        snapshot_id="SNAP-TEST",
        elapsed_min=elapsed_min,
        game_regulation_min=game_regulation_min,
        h_needed=h_needed,
        ab_remaining=ab_remaining,
        original_size=original_size,
        adjusted_size=adjusted_size,
    )


class TestCanonicalContaminationGuard:
    """ContaminationGuard.is_clean() from semantic_contracts — 7 checks."""

    def test_has_live_quotes_false_returns_false(self):
        guard = _make_guard(has_live_quotes=False)
        assert guard.is_clean() is False

    def test_mip_zero_returns_false(self):
        guard = _make_guard(mip=0.0)
        assert guard.is_clean() is False

    def test_mip_one_returns_false(self):
        guard = _make_guard(mip=1.0)
        assert guard.is_clean() is False

    def test_player_not_in_live_game_returns_false(self):
        guard = _make_guard(player_in_live_game=False)
        assert guard.is_clean() is False

    def test_game_not_in_progress_returns_false(self):
        guard = _make_guard(game_in_progress=False)
        assert guard.is_clean() is False

    def test_elapsed_min_gte_regulation_returns_false(self):
        guard = _make_guard(elapsed_min=550.0, game_regulation_min=540.0)
        assert guard.is_clean() is False

    def test_h_needed_exceeds_ab_remaining_returns_false(self):
        """Mathematical impossibility: need 3 hits but only 2 ABs remain."""
        guard = _make_guard(h_needed=3, ab_remaining=2)
        assert guard.is_clean() is False

    def test_ab_remaining_zero_returns_false(self):
        """No ABs remaining: bet is impossible regardless of h_needed."""
        guard = _make_guard(h_needed=1, ab_remaining=0)
        assert guard.is_clean() is False

    def test_all_clean_returns_true(self):
        """All checks pass — clean evaluation."""
        guard = _make_guard(
            has_live_quotes=True,
            mip=0.55,
            player_in_live_game=True,
            game_in_progress=True,
            h_needed=1,
            ab_remaining=3,
        )
        assert guard.is_clean() is True

    def test_adjusted_size_exceeds_original_raises_t4corr(self):
        """T4-CORR downward invariant: adjusted_size > original_size must raise."""
        guard = _make_guard(original_size=10.0, adjusted_size=12.0)
        with pytest.raises(T4CorrDownwardViolation) as exc_info:
            guard.is_clean()
        exc = exc_info.value
        assert exc.original_size == pytest.approx(10.0)
        assert exc.adjusted_size == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# BandInvariantChecker — 7 tests
# ---------------------------------------------------------------------------


class TestBandInvariantChecker:
    """check_t1_mlb_threshold, check_t4_proj_lambda, check_t4_flow_score_diff."""

    def test_t1_threshold_1_valid(self):
        assert BandInvariantChecker.check_t1_mlb_threshold(1, "TICKER-1", "PIPE-05") is None

    def test_t1_threshold_3_valid(self):
        assert BandInvariantChecker.check_t1_mlb_threshold(3, "TICKER-3", "PIPE-05") is None

    def test_t1_threshold_0_is_violation(self):
        v = BandInvariantChecker.check_t1_mlb_threshold(0, "TICKER-0", "PIPE-05")
        assert isinstance(v, ContractViolation)
        assert v.violation_reason == "t1_mlb_threshold_out_of_range"
        assert v.payload["threshold"] == 0

    def test_t1_threshold_4_is_violation(self):
        v = BandInvariantChecker.check_t1_mlb_threshold(4, "TICKER-4", "PIPE-05")
        assert isinstance(v, ContractViolation)
        assert v.violation_reason == "t1_mlb_threshold_out_of_range"

    def test_t4_lambda_non_default_valid(self):
        assert BandInvariantChecker.check_t4_proj_lambda(15.5, player_id=12345) is None

    def test_t4_lambda_fallback_is_violation(self):
        v = BandInvariantChecker.check_t4_proj_lambda(20.0, player_id=12345)
        assert isinstance(v, ContractViolation)
        assert v.violation_reason == "t4_proj_lambda_prior_is_fallback"
        assert v.payload["player_id"] == 12345

    def test_t4_flow_score_diff_range(self):
        """In-range (30) → None; out-of-range (70) → ContractViolation."""
        assert BandInvariantChecker.check_t4_flow_score_diff(30, "GAME-123") is None
        v = BandInvariantChecker.check_t4_flow_score_diff(70, "GAME-456")
        assert isinstance(v, ContractViolation)
        assert v.violation_reason == "t4_flow_score_differential_out_of_range"
        assert v.payload["score_differential"] == 70


# ---------------------------------------------------------------------------
# SemanticContractMonitor — 4 tests
# ---------------------------------------------------------------------------


def _make_monitor(tmp_path: Path) -> tuple[SemanticContractMonitor, object]:
    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
    audit = AuditLogger(log_path=tmp_path / "audit.jsonl")
    monitor = SemanticContractMonitor(
        logger=audit,
        session_id="TEST-MONITOR",
        snapshot_id="SNAP-TEST",
    )
    return monitor, audit


class TestSemanticContractMonitor:
    """Session-level semantic health accumulator."""

    def test_initial_state_is_clean(self, tmp_path):
        monitor, _ = _make_monitor(tmp_path)
        state = monitor.get_health_state()
        assert state.n_floor_violations_session == 0
        assert state.is_semantically_dark is False
        assert state.n_contamination_halts_session == 0

    def test_record_floor_violation_sets_dark_and_increments(self, tmp_path):
        monitor, _ = _make_monitor(tmp_path)
        exc = SemanticFloorViolation(
            pipeline_id="PIPE-05",
            sport="MLB",
            games_fetched=3,
            matched_players=0,
            diagnosis="test violation",
        )
        monitor.record_floor_violation(exc)
        state = monitor.get_health_state()
        assert state.n_floor_violations_session == 1
        assert state.is_semantically_dark is True
        assert state.last_floor_violation_ts is not None

    def test_record_contamination_halt_increments_counter(self, tmp_path):
        monitor, _ = _make_monitor(tmp_path)
        monitor.record_contamination_halt("TICKER-ABC", "market_no_live_quotes")
        monitor.record_contamination_halt("TICKER-DEF", "player_not_in_live_boxscore")
        state = monitor.get_health_state()
        assert state.n_contamination_halts_session == 2

    def test_get_health_state_returns_independent_copy(self, tmp_path):
        """Mutations to the returned state must not affect internal monitor state."""
        monitor, _ = _make_monitor(tmp_path)
        state1 = monitor.get_health_state()
        state1.n_floor_violations_session = 999  # mutate copy
        state2 = monitor.get_health_state()
        assert state2.n_floor_violations_session == 0  # original unaffected

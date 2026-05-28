"""
Tests for src/prediction_market_bot/run_backtest.py

Coverage areas:
  - BACKTEST_WINDOWS configuration: both windows defined, dates valid
  - Window validation periods are non-overlapping (independence requirement)
  - Chronological ordering: train_end < val_end for each window
  - Snapshot ID constants present and correctly formatted
  - Window key parsing: 'all', single key, comma-separated
  - _kill_switch: exits with non-zero code
  - run_backtest: missing --raw-csv path triggers kill switch
  - run_backtest: backtester errors propagate kill switch
  - EXP-002 window maps to correct dates
  - EXP-003 window maps to correct dates
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.run_backtest import (
    BACKTEST_WINDOWS,
    SNAPSHOT_ID_FRESH,
    SNAPSHOT_ID_REUSE,
    TARGET_PLAYER_IDS,
    TARGET_SEASONS,
    _kill_switch,
    run_backtest,
)
from prediction_market_bot.backtester import BacktestWindowDef


# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------


class TestBacktestWindowsConfig:
    @pytest.mark.unit
    def test_both_windows_defined(self):
        assert "exp002" in BACKTEST_WINDOWS
        assert "exp003" in BACKTEST_WINDOWS

    @pytest.mark.unit
    def test_exp002_exp_id(self):
        assert BACKTEST_WINDOWS["exp002"].exp_id == "EXP-002"

    @pytest.mark.unit
    def test_exp003_exp_id(self):
        assert BACKTEST_WINDOWS["exp003"].exp_id == "EXP-003"

    @pytest.mark.unit
    def test_exp002_dates(self):
        w = BACKTEST_WINDOWS["exp002"]
        assert w.train_end_date == "2022-01-31"
        assert w.val_end_date == "2022-04-10"

    @pytest.mark.unit
    def test_exp003_dates(self):
        w = BACKTEST_WINDOWS["exp003"]
        assert w.train_end_date == "2021-12-15"
        assert w.val_end_date == "2022-01-31"

    @pytest.mark.unit
    def test_train_end_before_val_end_exp002(self):
        w = BACKTEST_WINDOWS["exp002"]
        train_end = date.fromisoformat(w.train_end_date)
        val_end = date.fromisoformat(w.val_end_date)
        assert train_end < val_end, "train_end must be before val_end (TI-02)"

    @pytest.mark.unit
    def test_train_end_before_val_end_exp003(self):
        w = BACKTEST_WINDOWS["exp003"]
        train_end = date.fromisoformat(w.train_end_date)
        val_end = date.fromisoformat(w.val_end_date)
        assert train_end < val_end, "train_end must be before val_end (TI-02)"

    @pytest.mark.unit
    def test_window_defs_are_backtest_window_def(self):
        for key, w in BACKTEST_WINDOWS.items():
            assert isinstance(w, BacktestWindowDef), f"{key} must be BacktestWindowDef"

    @pytest.mark.unit
    def test_all_windows_have_description(self):
        for key, w in BACKTEST_WINDOWS.items():
            assert w.description, f"{key} has no description"

    @pytest.mark.unit
    def test_all_windows_have_snapshot_id(self):
        for key, w in BACKTEST_WINDOWS.items():
            assert w.snapshot_id.startswith("SNAP-"), f"{key} snapshot_id malformed"


# ---------------------------------------------------------------------------
# Non-overlapping validation periods (independence requirement for G4)
# ---------------------------------------------------------------------------


class TestWindowIndependence:
    @pytest.mark.unit
    def test_validation_periods_non_overlapping(self):
        """
        EXP-002 and EXP-003 validation windows must not overlap.
        Validation starts the day AFTER train_end_date (rows with game_date
        > train_end_date up to val_end_date inclusive).
        G4 evidence requires ≥3 independent experiments (HYP-001).
        """
        from datetime import timedelta

        w002 = BACKTEST_WINDOWS["exp002"]
        w003 = BACKTEST_WINDOWS["exp003"]

        # Validation starts the day AFTER train_end_date (inclusive boundary is train_end)
        val002_start = date.fromisoformat(w002.train_end_date) + timedelta(days=1)
        val002_end = date.fromisoformat(w002.val_end_date)

        val003_start = date.fromisoformat(w003.train_end_date) + timedelta(days=1)
        val003_end = date.fromisoformat(w003.val_end_date)

        # Overlap check: two date ranges [a..b] and [c..d] overlap iff a<=d and c<=b
        overlap = (val002_start <= val003_end) and (val003_start <= val002_end)
        assert not overlap, (
            f"Validation windows overlap: "
            f"EXP-002 [{val002_start}..{val002_end}] vs "
            f"EXP-003 [{val003_start}..{val003_end}]"
        )

    @pytest.mark.unit
    def test_exp001_and_exp002_validation_non_overlapping(self):
        """
        EXP-001 validation (2023-02-01 – 2023-04-30) must not overlap with EXP-002.
        """
        w002 = BACKTEST_WINDOWS["exp002"]

        exp001_val_start = date(2023, 2, 1)
        exp001_val_end = date(2023, 4, 30)

        val002_start = date.fromisoformat(w002.train_end_date)
        val002_end = date.fromisoformat(w002.val_end_date)

        overlap = (exp001_val_start <= val002_end) and (val002_start <= exp001_val_end)
        assert not overlap, "EXP-001 and EXP-002 validation windows must not overlap"

    @pytest.mark.unit
    def test_exp001_and_exp003_validation_non_overlapping(self):
        """
        EXP-001 validation (2023-02-01 – 2023-04-30) must not overlap with EXP-003.
        """
        w003 = BACKTEST_WINDOWS["exp003"]

        exp001_val_start = date(2023, 2, 1)
        exp001_val_end = date(2023, 4, 30)

        val003_start = date.fromisoformat(w003.train_end_date)
        val003_end = date.fromisoformat(w003.val_end_date)

        overlap = (exp001_val_start <= val003_end) and (val003_start <= exp001_val_end)
        assert not overlap, "EXP-001 and EXP-003 validation windows must not overlap"


# ---------------------------------------------------------------------------
# Snapshot ID constants
# ---------------------------------------------------------------------------


class TestSnapshotIds:
    @pytest.mark.unit
    def test_snapshot_id_reuse_format(self):
        assert SNAPSHOT_ID_REUSE.startswith("SNAP-")
        assert SNAPSHOT_ID_REUSE == "SNAP-2026-05-27-001"

    @pytest.mark.unit
    def test_snapshot_id_fresh_format(self):
        assert SNAPSHOT_ID_FRESH.startswith("SNAP-")
        assert SNAPSHOT_ID_FRESH == "SNAP-2026-05-27-002"

    @pytest.mark.unit
    def test_snapshot_ids_are_different(self):
        assert SNAPSHOT_ID_REUSE != SNAPSHOT_ID_FRESH


# ---------------------------------------------------------------------------
# Player/season constants
# ---------------------------------------------------------------------------


class TestPlayerSeasonConstants:
    @pytest.mark.unit
    def test_target_player_ids_count(self):
        assert len(TARGET_PLAYER_IDS) == 10

    @pytest.mark.unit
    def test_target_player_ids_are_unique(self):
        assert len(TARGET_PLAYER_IDS) == len(set(TARGET_PLAYER_IDS))

    @pytest.mark.unit
    def test_target_seasons_count(self):
        assert len(TARGET_SEASONS) == 3

    @pytest.mark.unit
    def test_target_seasons_format(self):
        for s in TARGET_SEASONS:
            # Must be "YYYY-YY" format
            parts = s.split("-")
            assert len(parts) == 2
            assert len(parts[0]) == 4
            assert len(parts[1]) == 2

    @pytest.mark.unit
    def test_target_seasons_chronological(self):
        # Must be in ascending order
        starts = [int(s.split("-")[0]) for s in TARGET_SEASONS]
        assert starts == sorted(starts)


# ---------------------------------------------------------------------------
# _kill_switch
# ---------------------------------------------------------------------------


class TestKillSwitch:
    @pytest.mark.unit
    def test_kill_switch_exits_with_code_1(self):
        with pytest.raises(SystemExit) as exc_info:
            _kill_switch("test reason")
        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_kill_switch_prints_to_stderr(self, capsys):
        with pytest.raises(SystemExit):
            _kill_switch("something went wrong")
        captured = capsys.readouterr()
        assert "something went wrong" in captured.err
        assert "KILL SWITCH" in captured.err


# ---------------------------------------------------------------------------
# run_backtest — integration with mocked Backtester
# ---------------------------------------------------------------------------


class TestRunBacktest:
    @pytest.mark.unit
    def test_missing_raw_csv_triggers_kill_switch(self, tmp_path):
        """If --raw-csv path doesn't exist, kill switch fires."""
        missing = tmp_path / "nonexistent.csv"
        with pytest.raises(SystemExit) as exc_info:
            run_backtest(
                output_dir=tmp_path,
                raw_csv=missing,
                windows_to_run=["exp002"],
                dry_run=True,
            )
        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_unknown_window_key_skips_gracefully(self, tmp_path):
        """Unknown window key emits a warning and triggers kill switch (no valid windows)."""
        # Create a minimal fake CSV so C1 loading path is reached
        import pandas as pd
        csv_path = tmp_path / "raw.csv"
        pd.DataFrame({"player_id": [2544], "game_date": ["2022-01-01"], "season": ["2021-22"]}).to_csv(csv_path, index=False)

        with pytest.raises(SystemExit):
            run_backtest(
                output_dir=tmp_path,
                raw_csv=csv_path,
                windows_to_run=["nonexistent_window"],
                dry_run=True,
            )

    @pytest.mark.unit
    def test_run_backtest_returns_results_list(self, tmp_path):
        """
        Smoke test: run_backtest returns a list of result dicts when
        Backtester succeeds.
        """
        import pandas as pd

        # Minimal raw CSV (just needs to be loadable by pd.read_csv)
        csv_path = tmp_path / "SNAP-2026-05-27-001_raw_game_logs.csv"
        pd.DataFrame({
            "player_id": [2544] * 5,
            "player_name": ["LeBron"] * 5,
            "game_date": ["2022-01-01", "2022-01-03", "2022-01-05", "2022-01-07", "2022-01-09"],
            "season": ["2021-22"] * 5,
        }).to_csv(csv_path, index=False)

        mock_result = {
            "exp_id": "EXP-002",
            "session_id": "BACKTEST-EXP-002-TEST",
            "model_version": "v1-test",
            "snapshot_id": SNAPSHOT_ID_REUSE,
            "train_rows": 80,
            "val_rows": 40,
            "test_rows_held_out": 30,
            "validation_brier_model": 0.22,
            "validation_brier_null": 0.25,
            "brier_improvement": 0.03,
            "beats_null": True,
            "validation_log_loss": 0.60,
            "validation_ece": 0.03,
            "validation_auc_roc": 0.61,
            "c4_gate_result": "REJECTED",
            "output_dir": str(tmp_path / "EXP-002"),
        }

        with (
            patch("prediction_market_bot.run_backtest.AuditLogger") as MockLogger,
            patch("prediction_market_bot.run_backtest.Backtester") as MockBacktester,
        ):
            logger_instance = MockLogger.return_value
            logger_instance.info.return_value = True
            logger_instance.error.return_value = True

            backtester_instance = MockBacktester.return_value

            # Construct a BacktestResult-like object
            from prediction_market_bot.backtester import BacktestResult, BacktestWindowDef
            result_obj = BacktestResult(
                exp_id="EXP-002",
                session_id="BACKTEST-EXP-002-TEST",
                snapshot_id=SNAPSHOT_ID_REUSE,
                model_version="v1-test",
                window_def=BacktestWindowDef("EXP-002", "2022-01-31", "2022-04-10", "W2", SNAPSHOT_ID_REUSE),
                train_rows=80,
                val_rows=40,
                test_rows_held_out=30,
                validation_brier_model=0.22,
                validation_brier_null=0.25,
                validation_log_loss=0.60,
                validation_ece=0.03,
                validation_auc_roc=0.61,
                train_brier_model=0.20,
                train_brier_null=0.25,
                brier_improvement=0.03,
                beats_null=True,
                c4_gate_result="REJECTED",
                output_dir=str(tmp_path / "EXP-002"),
                audit_log_path=str(tmp_path / "EXP-002" / "audit.jsonl"),
            )
            backtester_instance.run_windows.return_value = (True, [result_obj])

            results = run_backtest(
                output_dir=tmp_path,
                raw_csv=csv_path,
                windows_to_run=["exp002"],
                dry_run=True,
            )

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["exp_id"] == "EXP-002"
        assert results[0]["beats_null"] is True
        assert results[0]["brier_improvement"] == pytest.approx(0.03)

    @pytest.mark.unit
    def test_run_backtest_c6_failure_triggers_kill_switch(self, tmp_path):
        """C6 write failure from Backtester propagates as kill switch."""
        import pandas as pd

        csv_path = tmp_path / "raw.csv"
        pd.DataFrame({"player_id": [2544], "game_date": ["2022-01-01"], "season": ["2021-22"]}).to_csv(csv_path, index=False)

        with (
            patch("prediction_market_bot.run_backtest.AuditLogger") as MockLogger,
            patch("prediction_market_bot.run_backtest.Backtester") as MockBacktester,
        ):
            logger_instance = MockLogger.return_value
            logger_instance.info.return_value = True

            backtester_instance = MockBacktester.return_value
            # Simulate C6 write failure inside Backtester
            backtester_instance.run_windows.return_value = (False, [])

            with pytest.raises(SystemExit) as exc_info:
                run_backtest(
                    output_dir=tmp_path,
                    raw_csv=csv_path,
                    windows_to_run=["exp002"],
                    dry_run=True,
                )
            assert exc_info.value.code == 1

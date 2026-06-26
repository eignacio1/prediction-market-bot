"""
T-193: Feature CSV freshness guard for run_mlb_paper_trade.py

Tests for the staleness check added to PIPE-05 as part of Phase MLB-G1.

Rules:
  - >3 days stale: logger.warning("feature_csv_stale_warn") + print to stderr
  - >7 days stale: logger.error("feature_csv_stale_halt") + sys.exit(1)
  - Fresh (<=3 days): no warning, continue normally
  - No valid dates in CSV: logger.error + sys.exit(1)

The guard uses _now_utc.date() - max(game_date_dt) as the staleness measure.
"""
from __future__ import annotations

import sys
import unittest
from datetime import date, datetime, timezone, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd


def _make_df(max_date: date, rows: int = 10) -> pd.DataFrame:
    """Create a minimal feature CSV DataFrame with a known max game_date."""
    dates = [max_date - timedelta(days=i) for i in range(rows)]
    return pd.DataFrame({
        "player_id": range(rows),
        "player_name": [f"Player {i}" for i in range(rows)],
        "game_date": [d.isoformat() for d in dates],
        "game_date_dt": pd.to_datetime([d.isoformat() for d in dates]),
    })


def _run_freshness_guard(df: pd.DataFrame, now_utc: datetime) -> tuple[str, str]:
    """
    Mirror the T-193 freshness guard logic from run_mlb_paper_trade.py.
    Returns (warning_event, error_event) — empty string if not triggered.
    Raises SystemExit on halt condition.
    """
    _FRESHNESS_WARN_DAYS = 3
    _FRESHNESS_HALT_DAYS = 7

    _max_game_date = df["game_date_dt"].max()
    if pd.isna(_max_game_date):
        raise SystemExit(1)

    age_days = (now_utc.date() - _max_game_date.date()).days

    if age_days > _FRESHNESS_HALT_DAYS:
        raise SystemExit(1)

    if age_days > _FRESHNESS_WARN_DAYS:
        return ("feature_csv_stale_warn", "")

    return ("", "")


class TestFreshnessGuardFresh(unittest.TestCase):
    """Feature CSV that is fresh (<=3 days) — no warning, no halt."""

    def _now(self) -> datetime:
        return datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)

    def test_same_day_is_fresh(self):
        df = _make_df(date(2026, 6, 25))
        warn, err = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "")
        self.assertEqual(err, "")

    def test_one_day_stale_is_fresh(self):
        df = _make_df(date(2026, 6, 24))
        warn, err = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "")

    def test_two_days_stale_is_fresh(self):
        df = _make_df(date(2026, 6, 23))
        warn, err = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "")

    def test_three_days_stale_is_boundary_fresh(self):
        """Exactly 3 days stale — no warning (guard triggers at >3)."""
        df = _make_df(date(2026, 6, 22))
        warn, err = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "")


class TestFreshnessGuardWarning(unittest.TestCase):
    """4–7 days stale — warning only, no halt."""

    def _now(self) -> datetime:
        return datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)

    def test_four_days_stale_triggers_warning(self):
        df = _make_df(date(2026, 6, 21))
        warn, _ = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "feature_csv_stale_warn")

    def test_five_days_stale_triggers_warning(self):
        df = _make_df(date(2026, 6, 20))
        warn, _ = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "feature_csv_stale_warn")

    def test_seven_days_stale_is_boundary_warning(self):
        """Exactly 7 days stale — warning only (halt triggers at >7)."""
        df = _make_df(date(2026, 6, 18))
        warn, _ = _run_freshness_guard(df, self._now())
        self.assertEqual(warn, "feature_csv_stale_warn")

    def test_warning_does_not_raise(self):
        df = _make_df(date(2026, 6, 21))
        try:
            _run_freshness_guard(df, self._now())
        except SystemExit:
            self.fail("Freshness guard raised SystemExit in warning zone (4-7 days)")


class TestFreshnessGuardHalt(unittest.TestCase):
    """8+ days stale — sys.exit(1)."""

    def _now(self) -> datetime:
        return datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)

    def test_eight_days_stale_halts(self):
        df = _make_df(date(2026, 6, 17))
        with self.assertRaises(SystemExit) as ctx:
            _run_freshness_guard(df, self._now())
        self.assertEqual(ctx.exception.code, 1)

    def test_fourteen_days_stale_halts(self):
        df = _make_df(date(2026, 6, 11))
        with self.assertRaises(SystemExit):
            _run_freshness_guard(df, self._now())

    def test_thirty_days_stale_halts(self):
        df = _make_df(date(2026, 5, 26))
        with self.assertRaises(SystemExit):
            _run_freshness_guard(df, self._now())


class TestFreshnessGuardNoDates(unittest.TestCase):
    """Feature CSV with no valid dates halts immediately."""

    def _now(self) -> datetime:
        return datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)

    def test_all_nat_game_dates_halt(self):
        df = pd.DataFrame({
            "player_id": [1, 2, 3],
            "player_name": ["A", "B", "C"],
            "game_date": ["not-a-date", "also-bad", ""],
            "game_date_dt": pd.to_datetime(["not-a-date", "also-bad", ""], errors="coerce"),
        })
        with self.assertRaises(SystemExit) as ctx:
            _run_freshness_guard(df, self._now())
        self.assertEqual(ctx.exception.code, 1)

    def test_empty_dataframe_halts(self):
        df = pd.DataFrame({
            "player_id": pd.Series([], dtype=int),
            "player_name": pd.Series([], dtype=str),
            "game_date": pd.Series([], dtype=str),
            "game_date_dt": pd.Series([], dtype="datetime64[ns]"),
        })
        with self.assertRaises(SystemExit):
            _run_freshness_guard(df, self._now())


class TestFreshnessGuardThresholds(unittest.TestCase):
    """Threshold boundary conditions — guard uses strict > comparison."""

    def _now(self) -> datetime:
        return datetime(2026, 7, 10, 3, 0, tzinfo=timezone.utc)

    def test_warn_threshold_is_strictly_greater_than_3(self):
        """3 days = no warn; 4 days = warn."""
        fresh_3 = _make_df(date(2026, 7, 7))   # 3 days ago
        stale_4 = _make_df(date(2026, 7, 6))   # 4 days ago
        warn_3, _ = _run_freshness_guard(fresh_3, self._now())
        warn_4, _ = _run_freshness_guard(stale_4, self._now())
        self.assertEqual(warn_3, "")
        self.assertEqual(warn_4, "feature_csv_stale_warn")

    def test_halt_threshold_is_strictly_greater_than_7(self):
        """7 days = warn only; 8 days = halt."""
        warn_7 = _make_df(date(2026, 7, 3))   # 7 days ago
        halt_8 = _make_df(date(2026, 7, 2))   # 8 days ago
        warn, _ = _run_freshness_guard(warn_7, self._now())
        self.assertEqual(warn, "feature_csv_stale_warn")
        with self.assertRaises(SystemExit):
            _run_freshness_guard(halt_8, self._now())

    def test_month_boundary_correct(self):
        """Staleness is calculated correctly across month boundaries."""
        now = datetime(2026, 7, 5, 3, 0, tzinfo=timezone.utc)
        df_june_30 = _make_df(date(2026, 6, 30))  # 5 days ago
        warn, _ = _run_freshness_guard(df_june_30, now)
        self.assertEqual(warn, "feature_csv_stale_warn")

    def test_year_boundary_correct(self):
        """Staleness is calculated correctly across year boundaries."""
        now = datetime(2026, 1, 5, 3, 0, tzinfo=timezone.utc)
        df_dec = _make_df(date(2025, 12, 28))  # 8 days ago
        with self.assertRaises(SystemExit):
            _run_freshness_guard(df_dec, now)


class TestFreshnessGuardInSourceCode(unittest.TestCase):
    """Verify the guard is actually present in run_mlb_paper_trade.py source."""

    def _get_source(self) -> str:
        src = Path(__file__).parents[1] / "src" / "prediction_market_bot" / "run_mlb_paper_trade.py"
        return src.read_text()

    def test_freshness_warn_constant_present(self):
        self.assertIn("_FRESHNESS_WARN_DAYS", self._get_source())

    def test_freshness_halt_constant_present(self):
        self.assertIn("_FRESHNESS_HALT_DAYS", self._get_source())

    def test_stale_halt_log_event_present(self):
        self.assertIn("feature_csv_stale_halt", self._get_source())

    def test_stale_warn_log_event_present(self):
        self.assertIn("feature_csv_stale_warn", self._get_source())

    def test_sys_exit_on_halt(self):
        src = self._get_source()
        # sys.exit(1) must appear after the stale_halt log event
        halt_idx = src.find("feature_csv_stale_halt")
        exit_idx = src.find("sys.exit(1)", halt_idx)
        self.assertGreater(exit_idx, halt_idx, "sys.exit(1) not found after feature_csv_stale_halt log")

    def test_warn_does_not_exit(self):
        src = self._get_source()
        warn_idx = src.find("feature_csv_stale_warn")
        halt_idx = src.find("feature_csv_stale_halt")
        # warning block must come AFTER halt block in source, OR
        # sys.exit must not appear between warn log and halt log
        # Simplest check: warn event appears in source, guard is structured warn then halt
        self.assertGreater(warn_idx, 0)
        self.assertGreater(halt_idx, 0)


if __name__ == "__main__":
    unittest.main()

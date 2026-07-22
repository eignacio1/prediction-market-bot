"""
Tests for scripts/check_epoch_activation.py — T-388 bump-time behavioral-
activation check for logic-epoch boundaries (GG-124 stacking, GG-105/T-387
field-activation).
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from check_epoch_activation import check_field_activation, check_stacking, main  # noqa: E402
from prediction_market_bot.logic_epoch import LogicEpochBoundary  # noqa: E402


def _boundary(epoch: int, gap: str, ts: str) -> LogicEpochBoundary:
    return LogicEpochBoundary(
        epoch=epoch,
        resolving_gap=gap,
        commit_sha="0" * 40,
        commit_utc=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        description="synthetic fixture boundary",
    )


class TestCheckStacking:
    def test_single_recent_boundary_no_warning(self) -> None:
        boundaries = (
            _boundary(2, "GG-A", "2026-01-01T00:00:00"),
            _boundary(3, "GG-B", "2026-07-15T00:00:00"),
        )
        now = datetime(2026, 7, 21, tzinfo=timezone.utc)
        assert check_stacking(boundaries, now=now) == []

    def test_two_boundaries_within_window_warns(self) -> None:
        boundaries = (
            _boundary(6, "GG-123", "2026-07-16T00:13:46"),
            _boundary(7, "GG-105", "2026-07-18T14:00:00"),
            _boundary(8, "GG-105", "2026-07-18T18:07:19"),
        )
        now = datetime(2026, 7, 21, tzinfo=timezone.utc)
        warnings = check_stacking(boundaries, now=now)
        assert len(warnings) == 1
        assert "3 logic-epoch boundaries" in warnings[0]
        assert "epoch 6" in warnings[0]
        assert "epoch 7" in warnings[0]
        assert "epoch 8" in warnings[0]
        assert "GG-124" in warnings[0]

    def test_boundary_outside_window_excluded(self) -> None:
        boundaries = (
            _boundary(2, "GG-A", "2026-06-01T00:00:00"),
            _boundary(3, "GG-B", "2026-07-19T00:00:00"),
        )
        now = datetime(2026, 7, 21, tzinfo=timezone.utc)
        # only epoch 3 is within the trailing 7 days -> single boundary, no warning
        assert check_stacking(boundaries, now=now) == []

    def test_custom_window_days(self) -> None:
        boundaries = (
            _boundary(2, "GG-A", "2026-07-01T00:00:00"),
            _boundary(3, "GG-B", "2026-07-19T00:00:00"),
        )
        now = datetime(2026, 7, 21, tzinfo=timezone.utc)
        # 30-day window pulls both boundaries in
        warnings = check_stacking(boundaries, now=now, window_days=30)
        assert len(warnings) == 1

    def test_defaults_to_real_boundaries_and_now(self) -> None:
        # Smoke test only: must not raise when called with no args.
        result = check_stacking()
        assert isinstance(result, list)


class TestCheckFieldActivation:
    def test_field_present_passes(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/opt/x/pregame_mlb_20260720.json\t62\t62\n", stderr=""
        )
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            assert check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json") == []

    def test_field_entirely_null_alerts(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/opt/x/pregame_mlb_20260718.json\t62\t0\n", stderr=""
        )
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            alerts = check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json")
        assert len(alerts) == 1
        assert "ALERT" in alerts[0]
        assert "ba_l10_shrunk" in alerts[0]
        assert "GG-105/T-387" in alerts[0]

    def test_field_partially_null_passes(self) -> None:
        # At least one record carries the field -> not the T-387 all-null failure mode.
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/opt/x/pregame_mlb_20260719.json\t62\t40\n", stderr=""
        )
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            assert check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json") == []

    def test_no_files_matched_alerts(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="NO_FILES\n", stderr="")
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            alerts = check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json")
        assert len(alerts) == 1
        assert "no files matched" in alerts[0]

    def test_remote_nonzero_exit_alerts(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Traceback...")
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            alerts = check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json")
        assert len(alerts) == 1
        assert "remote activation check failed" in alerts[0]

    def test_ssh_unreachable_alerts(self) -> None:
        with patch("check_epoch_activation.subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 5)):
            alerts = check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json")
        assert len(alerts) == 1
        assert "could not reach VPS" in alerts[0]

    def test_unexpected_remote_output_alerts(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="garbage\n", stderr="")
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            alerts = check_field_activation("ba_l10_shrunk", "/opt/x/pregame_mlb_*.json")
        assert len(alerts) == 1
        assert "unexpected remote output" in alerts[0]


class TestMain:
    def test_stacking_only_clean_exit_zero(self) -> None:
        # Real boundary history has clustered epoch-7/8 bumps close to "now" in
        # fixture time, but with --skip-vps and no --field, exit code reflects
        # only alerts (never the warn-only stacking check), so it's always 0.
        rc = main(["--skip-vps"])
        assert rc == 0

    def test_field_without_artifact_glob_errors(self) -> None:
        rc = main(["--field", "ba_l10_shrunk"])
        assert rc == 2

    def test_field_alert_sets_exit_code_one(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="NO_FILES\n", stderr="")
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            rc = main(["--field", "ba_l10_shrunk", "--artifact-glob", "/opt/x/*.json"])
        assert rc == 1

    def test_field_clean_sets_exit_code_zero(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/opt/x/f.json\t10\t10\n", stderr=""
        )
        with patch("check_epoch_activation.subprocess.run", return_value=completed):
            rc = main(["--field", "ba_l10_shrunk", "--artifact-glob", "/opt/x/*.json"])
        assert rc == 0

"""
Tests for scripts/assert_service_activation.py (GG-279, T-574, 2026-09-24).

Covers only the comparison primitive -- see the module docstring for why
live service/SSH enumeration is explicitly out of scope for this check.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from assert_service_activation import landed_but_not_activated  # noqa: E402


def test_commit_after_service_start_is_flagged():
    # Mirrors GG-271's own timeline: service last started 00:12:01Z, but a
    # relevant commit landed later at 04:00:00Z -- that commit is not yet
    # active in the running process.
    findings = landed_but_not_activated(
        "2026-09-15T00:12:01Z",
        ["2026-09-15T00:05:00Z", "2026-09-15T04:00:00Z"],
    )
    assert findings == ["2026-09-15T04:00:00Z"]


def test_commit_before_service_start_is_not_flagged():
    findings = landed_but_not_activated(
        "2026-09-15T00:12:01Z",
        ["2026-09-14T23:00:00Z"],
    )
    assert findings == []


def test_commit_exactly_at_service_start_is_not_flagged():
    # Strictly-newer only -- a commit at the same instant as process start
    # is treated as included in that start, not landed-after-the-fact.
    findings = landed_but_not_activated(
        "2026-09-15T00:12:01Z",
        ["2026-09-15T00:12:01Z"],
    )
    assert findings == []


def test_no_commit_timestamps_returns_empty():
    assert landed_but_not_activated("2026-09-15T00:12:01Z", []) == []


def test_naive_and_offset_timestamps_compare_correctly():
    # Naive timestamps (no explicit offset) are treated as UTC, matching
    # systemctl's ActiveEnterTimestamp / git's %cI output conventions.
    findings = landed_but_not_activated(
        "2026-09-15T00:00:00",
        ["2026-09-15T01:00:00+00:00", "2026-09-14T23:00:00+00:00"],
    )
    assert findings == ["2026-09-15T01:00:00+00:00"]

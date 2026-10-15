"""ADR-0074 / Hard Rule 13: handoffs after the cutoff must carry pattern_sweep; older ones still parse."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_session_artifacts as g  # noqa: E402

BASE = "gap_measure: PLUMBING\ngap_delta: none\n"


def _handoff(tmp_path, ts, extra=""):
    p = tmp_path / "h.md"
    p.write_text("<!-- session-meta\ntask_id: T-1\ntier: MICRO\n"
                 f"timestamp: {ts}\ncommit: abc1234\none_line_summary: x\n{BASE}{extra}-->\n")
    return p


def test_before_cutoff_parses_without_pattern_sweep(tmp_path):
    g.parse_session_meta(_handoff(tmp_path, "2026-10-15T11:59:59Z"))


def test_cutoff_instant_is_legacy(tmp_path):
    g.parse_session_meta(_handoff(tmp_path, g.PATTERN_SWEEP_REQUIRED_AFTER))


def test_after_cutoff_without_pattern_sweep_fails(tmp_path):
    with pytest.raises(SystemExit) as e:
        g.parse_session_meta(_handoff(tmp_path, "2026-10-16T00:00:00Z"))
    assert "pattern_sweep" in str(e.value)


def test_after_cutoff_with_na_passes(tmp_path):
    f = g.parse_session_meta(_handoff(tmp_path, "2026-10-16T00:00:00Z", "pattern_sweep: n/a (no defect fixed)\n"))
    assert f["pattern_sweep"].startswith("n/a")


def test_empty_pattern_sweep_counts_as_missing(tmp_path):
    with pytest.raises(SystemExit):
        g.parse_session_meta(_handoff(tmp_path, "2026-10-16T00:00:00Z", "pattern_sweep:\n"))

"""W63.3: gap_measure / gap_delta are required in session-meta for handoffs after Wave 62's close; older ones still parse."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_session_artifacts as g  # noqa: E402


def _handoff(tmp_path, ts, extra=""):
    p = tmp_path / "h.md"
    p.write_text("<!-- session-meta\ntask_id: T-1\ntier: MICRO\n"
                 f"timestamp: {ts}\ncommit: abc1234\none_line_summary: x\n{extra}-->\n")
    return p


def test_old_handoff_without_gap_keys_parses(tmp_path):
    assert g.parse_session_meta(_handoff(tmp_path, "2026-10-09T07:20:00Z"))["task_id"] == "T-1"


def test_cutoff_instant_itself_is_legacy(tmp_path):
    g.parse_session_meta(_handoff(tmp_path, g.GAP_KEYS_REQUIRED_AFTER))


def test_new_handoff_without_gap_keys_fails(tmp_path):
    with pytest.raises(SystemExit) as e:
        g.parse_session_meta(_handoff(tmp_path, "2026-10-09T07:24:14Z"))
    assert "gap_measure" in str(e.value) and "gap_delta" in str(e.value)


def test_new_handoff_missing_only_delta_fails(tmp_path):
    with pytest.raises(SystemExit) as e:
        g.parse_session_meta(_handoff(tmp_path, "2026-10-10T00:00:00Z", "gap_measure: E3\n"))
    assert "gap_delta" in str(e.value)


def test_new_handoff_with_both_keys_passes(tmp_path):
    f = g.parse_session_meta(_handoff(tmp_path, "2026-10-10T00:00:00Z", "gap_measure: PLUMBING\ngap_delta: none\n"))
    assert f["gap_measure"] == "PLUMBING"


def test_empty_value_counts_as_missing(tmp_path):
    with pytest.raises(SystemExit):
        g.parse_session_meta(_handoff(tmp_path, "2026-10-10T00:00:00Z", "gap_measure:\ngap_delta: none\n"))


def test_date_only_legacy_timestamp_parses(tmp_path):
    g.parse_session_meta(_handoff(tmp_path, "2026-06-01"))

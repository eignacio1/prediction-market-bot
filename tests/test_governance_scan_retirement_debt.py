"""
Tests for the "Retirement debt" warn-only block added to
.claude/hooks/governance_scan_full.sh (T-570, Deliverable 2, 2026-09-23).

These tests extract the actual block out of the live hook script (so a future
edit to the block is exercised by these tests, not a hand-copied duplicate of
it) and run it in a bash subshell with `python3` overridden to a function that
echoes canned retire_resolved_gaps.py output -- no real file is read or
written, and the real script is never invoked.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
HOOK = ROOT / ".claude" / "hooks" / "governance_scan_full.sh"  # full scan; governance_scan.sh is the cached wrapper (#235)
WRAPPER = ROOT / ".claude" / "hooks" / "governance_scan.sh"

START_MARKER = 'RETIREMENT_DEBT_OUT=$(python3'
END_MARKER = "\nfi\n"


def _extract_block() -> str:
    text = HOOK.read_text()
    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start) + len(END_MARKER)
    return text[start:end]


def _run_block(fake_python3_stdout: str) -> subprocess.CompletedProcess:
    block = _extract_block()
    script = (
        "set -uo pipefail\n"
        "python3() {\n"
        "  cat <<'FAKE_STDOUT_EOF'\n"
        f"{fake_python3_stdout}\n"
        "FAKE_STDOUT_EOF\n"
        "}\n"
        f"{block}\n"
    )
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True)


def test_block_exists_in_hook():
    # Sanity check the markers still find the real block -- if this fails, the
    # hook was edited in a way that moved/renamed the block and these tests
    # need to be updated, not silently pass on a stale extraction.
    block = _extract_block()
    assert "RETIREMENT_DEBT_N" in block
    assert "retire_resolved_gaps.py" in block


def test_nonzero_debt_prints_loud_warning_and_exits_zero():
    fake = "resolved-class entries that WOULD move: 24\nstay-class entries remaining live: 100\n"
    result = _run_block(fake)
    assert result.returncode == 0
    assert "RETIREMENT DEBT (warn-only): 24 resolved-class gap(s)" in result.stdout
    assert "--apply requires operator sign-off" in result.stdout


def test_zero_debt_prints_clean_line_and_exits_zero():
    fake = "resolved-class entries that WOULD move: 0\nstay-class entries remaining live: 124\n"
    result = _run_block(fake)
    assert result.returncode == 0
    assert "Retirement debt: 0 resolved-class gaps sitting unarchived" in result.stdout
    assert "RETIREMENT DEBT" not in result.stdout


def test_block_never_fails_the_scan_even_with_unparseable_output():
    # If retire_resolved_gaps.py's output format ever drifted (no matching
    # line at all), the grep -oE pipeline yields empty, and the parameter
    # expansion default (`${RETIREMENT_DEBT_N:-0}`) must fall back to 0
    # rather than the block erroring out under `set -u`.
    result = _run_block("some unexpected output with no matching line\n")
    assert result.returncode == 0
    assert "Retirement debt: 0 resolved-class gaps sitting unarchived" in result.stdout


def test_wrapper_returns_fast_and_prints_cached_scan(tmp_path):
    """#235: governance_scan.sh must return in <2s (hook timeout 30s) and print the cached scan, never run the full one inline."""
    import shutil
    import time

    proj = tmp_path / "proj"
    (proj / ".claude" / "hooks").mkdir(parents=True)
    (proj / "03_DECISIONS").mkdir()
    (proj / "03_DECISIONS" / "GOVERNANCE_GAP_LOG.md").write_text("")
    (proj / "logs").mkdir()
    (proj / "logs" / ".governance_scan_last.txt").write_text("CACHED-SCAN-SENTINEL\n")
    shutil.copy(WRAPPER, proj / ".claude" / "hooks" / "governance_scan.sh")
    # a slow stand-in for the full scan: if the wrapper ran it inline, the timing assertion would fail
    (proj / ".claude" / "hooks" / "governance_scan_full.sh").write_text("sleep 5\necho FULL\n")
    t0 = time.monotonic()
    r = subprocess.run(["bash", str(proj / ".claude" / "hooks" / "governance_scan.sh")], capture_output=True, text=True, timeout=30)
    elapsed = time.monotonic() - t0
    assert r.returncode == 0
    assert "[cached governance scan" in r.stdout and "CACHED-SCAN-SENTINEL" in r.stdout
    assert elapsed < 2.0, elapsed

"""scripts/claude_md_now.py - the CLAUDE.md Right-now block (operator 2026-11-10 22:28 PT)."""
import importlib.util
from pathlib import Path
import datetime as dt

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("claude_md_now", ROOT / "scripts" / "claude_md_now.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

TEMPLATE = """# x

## Right now

<!-- NOW:BEGIN test -->
<!-- NOW:END -->

**Window-maintained (as of {hand}, test):**
- line
"""


def _tree(tmp_path, hand="2026-11-11"):
    # The generated lines come from the real repo's code; only the file under test is temporary.
    f = tmp_path / "CLAUDE.md"
    f.write_text(TEMPLATE.format(hand=hand), encoding="utf-8")
    return f


def test_compute_reads_registry():
    lines = m.compute(ROOT)
    assert lines[0].startswith("- Registry: ")
    assert any(l.startswith("- Kelly (execution_bands.py)") for l in lines)
    assert not any("ruled out" in l.lower() for l in lines)  # DOCTRINE 1b wording


def test_write_then_check_is_clean(tmp_path, monkeypatch):
    f = _tree(tmp_path)
    monkeypatch.setattr(m, "compute", lambda root=None: ["- a", "- b"])
    assert m.write(f, dt.date(2026, 11, 11))
    assert m.check(f, dt.date(2026, 11, 12), 7) == []


def test_check_flags_drift_and_age(tmp_path, monkeypatch):
    f = _tree(tmp_path, hand="2026-10-01")
    monkeypatch.setattr(m, "compute", lambda root=None: ["- a"])
    m.write(f, dt.date(2026, 11, 1))
    monkeypatch.setattr(m, "compute", lambda root=None: ["- b"])
    reds = m.check(f, dt.date(2026, 11, 11), 7)
    assert any("code says: - b" in r for r in reds)
    assert any("days old" in r and "generated" in r for r in reds)
    assert any("window-maintained" in r for r in reds)


def test_missing_markers_is_red(tmp_path):
    f = tmp_path / "CLAUDE.md"
    f.write_text("# nothing\n", encoding="utf-8")
    assert m.check(f, dt.date(2026, 11, 11), 7) == ["no NOW markers in CLAUDE.md"]


def test_main_is_alarm_only(tmp_path):
    f = tmp_path / "CLAUDE.md"
    f.write_text("# nothing\n", encoding="utf-8")
    assert m.main(["--file", str(f)]) == 0
    assert m.main(["--file", str(f), "--strict"]) == 1


def test_repo_claude_md_is_current():
    # The live file must carry the markers; staleness is alarm-only (the session scan), not a CI failure.
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert m.BEGIN in text and m.END in text

from pathlib import Path

from scripts import hypothesis_registry_check as h


def _repo(tmp: Path, doctrine: str, files: list[str]) -> Path:
    (tmp / "02_ARCHITECTURE_DESIGN").mkdir()
    (tmp / h.DOCTRINE).write_text(doctrine)
    for f in files:
        p = tmp / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    return tmp


def test_flags_unregistered(tmp_path):
    r = _repo(tmp_path, "| EXP-050 |", ["05_RESEARCH_EXPERIMENTS/EXP051_X_PREREGISTRATION.md"])
    assert h.unregistered(r) == ["05_RESEARCH_EXPERIMENTS/EXP051_X_PREREGISTRATION.md"]


def test_registered_by_id_path_dir_and_lead(tmp_path):
    r = _repo(tmp_path, "EXP-050 and 12_EXPLORATORY/foo and EXP-W9.9 and a/b/PREREG.md",
              ["05_RESEARCH_EXPERIMENTS/EXP050_X_PREREGISTRATION.md",
               "12_EXPLORATORY/foo/PREREG.md",
               "05_RESEARCH_EXPERIMENTS/EXP-W9.9_y_PREREG.md"])
    assert h.unregistered(r) == []


def test_alarm_only_exit_code(tmp_path, monkeypatch):
    assert h.main([]) == 0

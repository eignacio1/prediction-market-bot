"""W80.4: doc_registry.py check — unregistered / missing / stale, alarm-only."""
import datetime as dt
import importlib.util
import pathlib
import subprocess

_spec = importlib.util.spec_from_file_location(
    "doc_registry", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "doc_registry.py")
dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dr)


def _repo(tmp_path, registry_body):
    (tmp_path / "00_ADMIN").mkdir()
    (tmp_path / "10_X").mkdir()
    (tmp_path / "10_X" / "a.md").write_text("a")
    (tmp_path / "10_X" / "b.md").write_text("b")
    (tmp_path / dr.REGISTRY).write_text(registry_body)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], cwd=tmp_path, check=True)
    return tmp_path


BODY = 'covered = ["10_X/"]\n\n[[doc]]\npath = "10_X/a.md"\nclass = "LIVING"\nowner = "IO"\nmax_age_days = 30\nlast_verified = "2026-01-01"\n'


def test_flags_unregistered_and_stale(tmp_path):
    root = _repo(tmp_path, BODY)
    out = dr.check(root, today=dt.date(2026, 10, 1))
    assert "UNREGISTERED 10_X/b.md" in out
    assert any(p.startswith("STALE 10_X/a.md") for p in out)


def test_fresh_and_registered_is_silent(tmp_path):
    body = BODY.replace("2026-01-01", "2026-09-20") + '\n[[doc]]\npath = "10_X/b.md"\nclass = "RECORD"\nowner = "IO"\n'
    root = _repo(tmp_path, body)
    assert dr.check(root, today=dt.date(2026, 10, 1)) == []


def test_missing_registered_path(tmp_path):
    body = BODY + '\n[[doc]]\npath = "10_X/gone.md"\nclass = "RECORD"\nowner = "IO"\n'
    root = _repo(tmp_path, body)
    assert "MISSING 10_X/gone.md" in dr.check(root, today=dt.date(2026, 10, 1))


def test_mini_parser_matches_shape():
    parsed = dr._mini_parse(BODY)
    assert parsed["covered"] == ["10_X/"]
    assert parsed["doc"][0]["max_age_days"] == 30


def test_repo_registry_parses_and_classes_valid():
    # Alarm-only by design: an unregistered new file must not fail CI, so only the registry's shape is asserted.
    docs = dr.load(dr.ROOT)["doc"]
    assert docs and {d["class"] for d in docs} <= {"RECORD", "LIVING", "SUPERSEDED", "DEAD"}

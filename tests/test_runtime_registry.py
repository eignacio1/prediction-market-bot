"""ADR-0074: every running component the repo mirrors (cron fragments, systemd units, workflows) is in the runtime registry.

A new cron line, service or workflow without a registry entry fails CI - that is the point. Add it with
`python3 scripts/runtime_registry.py add`, fill purpose / pillar / writes / alarm, then `... render`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import runtime_registry as rr  # noqa: E402


def test_every_mirrored_component_is_registered():
    assert rr.check(verbose=False) == 0, "run: python3 scripts/runtime_registry.py check"


def test_unregistered_component_fails(monkeypatch):
    real = rr.discover()
    fake = dict(real)
    fake["cron|0 0 * * *|scripts/brand_new_job.py"] = {"kind": "cron", "source": "deploy/cron.x", "mirrors": [], "command": "x"}
    monkeypatch.setattr(rr, "discover", lambda: fake)
    assert rr.check(verbose=False) == 1


def test_live_entry_missing_from_mirrors_fails(monkeypatch):
    real = rr.discover()
    gone = next(k for k in real if k.startswith("cron|"))
    monkeypatch.setattr(rr, "discover", lambda: {k: v for k, v in real.items() if k != gone})
    assert rr.check(verbose=False) == 1


def test_registry_entries_carry_required_fields():
    for c in rr.load():
        missing = [f for f in rr.REQUIRED if f not in c]
        assert not missing, (c.get("key"), missing)
        assert c["status"] in {"live", "paused", "retired"}, c["key"]
        assert c["pillar"] in {"BREADTH", "DEPTH", "EXECUTION", "PROOF", "PLUMBING"}, c["key"]


def test_runtime_map_is_current(tmp_path, monkeypatch):
    committed = rr.MAP.read_text()
    monkeypatch.setattr(rr, "MAP", tmp_path / "map.md")
    rr.render()
    assert (tmp_path / "map.md").read_text() == committed, "run: python3 scripts/runtime_registry.py render"


def test_begin_end_fragments_ignore_install_instructions(tmp_path, monkeypatch):
    d = tmp_path / "deploy"
    d.mkdir()
    (d / "cron.conf").write_text("")
    (d / "cron_x.conf").write_text("# Install: (crontab -l; sed -n '/^# BEGIN X/,/^# END X/p'\n"
                                   "1 1 * * * cd /p && python scripts/a.py >> logs/a.log 2>&1\n"
                                   "# BEGIN X\n2 2 * * * cd /p && python scripts/b.py >> logs/b.log 2>&1\n# END X\n")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    monkeypatch.setattr(rr, "ROOT", tmp_path)
    keys = [k for k in rr.discover() if k.startswith("cron|")]
    assert keys == ["cron|2 2 * * *|scripts/b.py"]

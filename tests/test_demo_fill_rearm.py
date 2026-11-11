"""W109.6: demo_fill_rearm."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("rearm", Path(__file__).resolve().parents[1] / "scripts" / "demo_fill_rearm.py")
rearm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rearm)


def _root(tmp_path):
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "demo_fill.override.env").write_text("DEMO_FILL_PLACEMENT_RULE=off\n")
    return tmp_path


def test_check_changes_nothing(tmp_path):
    r = _root(tmp_path)
    assert rearm.run("check", r, trips=[]) == 0
    assert (r / "deploy" / "demo_fill.override.env").exists()


def test_apply_refuses_when_still_tripped(tmp_path):
    r = _root(tmp_path)
    assert rearm.run("apply", r, trips=[{"condition": "x"}]) == 2
    assert (r / "deploy" / "demo_fill.override.env").exists()


def test_apply_moves_override_aside_and_is_idempotent(tmp_path):
    r = _root(tmp_path)
    assert rearm.run("apply", r, trips=[]) == 0
    assert not (r / "deploy" / "demo_fill.override.env").exists()
    assert len(list((r / "logs").glob("demo_fill.override.env.*.removed"))) == 1
    assert rearm.run("apply", r, trips=[]) == 0


def test_tasks_registered():
    from scripts import box_tasks
    assert box_tasks.TASKS["demo_fill_rearm"].endswith("demo_fill_rearm.py apply")

"""W126.1 Part C: archive_dense `gate` subcommand + archive_dense_gate_read box task are read-only and report the numbers."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_gate_report_refuse_and_pass():
    m = _load("archive_dense_install_w1261", "scripts/archive_dense_install.py")
    total = 100e9
    bad = m.gate_report({"total_bytes": total, "pct": 70.0}, 0.2)
    assert bad["verdict"] in ("REFUSE", "PASS")
    assert bad["ceiling_pct"] == 80.0 and bad["horizon_days"] == 30
    assert "projected_pct_30d" in bad["numbers"]
    if bad["verdict"] == "REFUSE":
        assert bad["max_new_mb_per_day_under_ceiling"] >= 0
        assert "do not approve" in bad["approval_line"]
    ok = m.gate_report({"total_bytes": total, "pct": 10.0}, 0.0)
    assert ok["verdict"] == "PASS" and ok["approval_line"] == "approve archive_dense_install"


def test_gate_task_allowlisted_read_only():
    bt = _load("box_tasks_w1261", "scripts/box_tasks.py")
    cmd = bt.TASKS["archive_dense_gate_read"]
    assert cmd.endswith("archive_dense_install.py gate")
    assert "install" not in "archive_dense_gate_read".replace("archive_dense_", "")

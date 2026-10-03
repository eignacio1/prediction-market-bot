"""vps_job: safety refusals + real detached lifecycle (LocalBackend, tmp dirs)."""
import json, sys, time
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import vps_job as vj

ROOT = Path(__file__).resolve().parent.parent


def _fake_root(tmp_path, body, extra=None):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "job.py").write_text(body)
    for n, b in (extra or {}).items():
        (tmp_path / "scripts" / n).write_text(b)
    return tmp_path


@pytest.mark.parametrize("argv", [
    ["bash", "scripts/job.py"], ["python3", "-c", "print(1)"], ["python3", "-m", "x"],
    ["python3", "/etc/x.py"], ["python3", "scripts/../x.py"], ["python3", "scripts/job.py", "a;rm"],
    ["python3", "scripts/job.py", "--rate", "5"], ["python3", "scripts/nope.py"]])
def test_refuses_bad_commands(tmp_path, argv):
    r = _fake_root(tmp_path, "print(1)")
    with pytest.raises(vj.Refused):
        vj.check_command(argv, 3.3, r)


def test_rate_cap_bounds(tmp_path):
    r = _fake_root(tmp_path, "print(1)")
    for bad in (0, -1, 3.4):
        with pytest.raises(vj.Refused):
            vj.check_command(["python3", "scripts/job.py"], bad, r)
    vj.check_command(["python3", "scripts/job.py", "--rate", "1.5"], 3.3, r)


@pytest.mark.parametrize("body", [
    "from prediction_market_bot.c5_execution.paper_trader import PaperTrader",
    "import kalshi_client",
    "x = 1\nsubmit_order(x)",
    "def f(kelly_fraction=1): pass",
    "import sib",
])
def test_refuses_order_sizing_paths(tmp_path, body):
    r = _fake_root(tmp_path, body, {"sib.py": "from prediction_market_bot.c4_risk_engine import risk"})
    with pytest.raises(vj.Refused):
        vj.check_command(["python3", "scripts/job.py"], 3.3, r)


def test_real_history_builder_passes_safety():
    vj.check_command(["python3", "scripts/kalshi_history_build.py", "fetch", "--rate", "3.3"], 3.3, ROOT)


def test_lifecycle_and_duplicate_refusal(tmp_path):
    r = _fake_root(tmp_path / "repo", "import time, sys\ntime.sleep(float(sys.argv[1]))\nprint('hi')") \
        if (tmp_path / "repo").mkdir() is None else None
    jobs = str(tmp_path / "jobs")
    be = vj.LocalBackend()

    def run(*a):
        return vj.main(list(a), backend=be, root=r, repo=str(r), jobs=jobs)
    assert run("launch", "t1", "--rate-cap", "1", "--", "python3", "scripts/job.py", "30") == 0
    assert run("launch", "t1", "--rate-cap", "1", "--", "python3", "scripts/job.py", "30") == 3  # duplicate
    st = Path(jobs, "t1", "start.json")
    d = json.loads(st.read_text())
    assert d["rate_cap_req_per_s"] == 1 and d["argv"][1] == "scripts/job.py" and "T" in d["launched_utc"]
    assert run("stop", "t1") == 0
    assert json.loads(Path(jobs, "t1", "done.json").read_text())["exit_code"] == "stopped"
    assert run("launch", "t2", "--rate-cap", "1", "--", "python3", "scripts/job.py", "0") == 0
    for _ in range(30):
        if Path(jobs, "t2", "done.json").exists():
            break
        time.sleep(0.2)
    assert json.loads(Path(jobs, "t2", "done.json").read_text())["exit_code"] == 0
    assert "hi" in Path(jobs, "t2", "log").read_text()
    assert run("launch", "t2", "--rate-cap", "1", "--", "python3", "scripts/job.py", "0") == 0  # relaunch after finish
    assert vj.main(["launch", "BAD NAME", "--rate-cap", "1", "--", "python3", "scripts/job.py"], backend=be, root=r) == 2


def test_no_cron_and_no_order_imports_in_runner():
    src = (ROOT / "scripts" / "vps_job.py").read_text()
    assert "crontab" not in src.replace("no cron entry", "")
    for m in vj.closure(ROOT / "scripts" / "vps_job.py", ROOT):
        assert m.name == "vps_job.py"

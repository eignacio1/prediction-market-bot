"""W67.3 / T-813: scripts/ops/vps_deploy.sh behaves like deploy.yml did.

Drives the real script against a throwaway origin + clone, with the gate command and
systemctl stubbed through the script's PMBOT_* test hooks.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "ops" / "vps_deploy.sh"
POLICY = REPO / "scripts" / "deploy_restart_policy.py"
TRUTH = REPO / "scripts" / "ops" / "deploy_truth.py"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}).stdout.strip()


def _commit(work: Path, rel: str, text: str) -> str:
    p = work / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    _git(work, "add", rel)
    _git(work, "commit", "-q", "-m", f"edit {rel}")
    _git(work, "push", "-q", "origin", "HEAD:main")
    return _git(work, "rev-parse", "HEAD")


@pytest.fixture()
def rig(tmp_path):
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    work = tmp_path / "work"
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    (work / "scripts").mkdir()
    shutil.copy(POLICY, work / "scripts" / "deploy_restart_policy.py")
    (work / "scripts" / "ops").mkdir()
    shutil.copy(TRUTH, work / "scripts" / "ops" / "deploy_truth.py")
    (work / "src" / "prediction_market_bot").mkdir(parents=True)
    (work / "src" / "prediction_market_bot" / "run_t4_mlb_live.py").write_text("")
    (work / "04_EXECUTION").mkdir()
    (work / "04_EXECUTION" / "Q.md").write_text("q0")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "init")
    _git(work, "push", "-q", "origin", "HEAD:main")
    proj = tmp_path / "proj"
    _git(tmp_path, "clone", "-q", str(origin), str(proj))
    sysctl = tmp_path / "sysctl.sh"
    sysctl.write_text('#!/usr/bin/env bash\necho "$@" >> "$SYSCTL_LOG"\n'
                      '[ "$1" = show ] && date -u "+%a %Y-%m-%d %H:%M:%S UTC"\nexit 0\n')
    sysctl.chmod(0o755)
    env = {**os.environ, "PMBOT_DIR": str(proj), "PMBOT_PYTHON": sys.executable,
           "PMBOT_SYSTEMCTL": str(sysctl), "PMBOT_STATE_DIR": str(tmp_path / "state"),
           "SYSCTL_LOG": str(tmp_path / "sysctl.log"), "PMBOT_GATE_CMD": "true"}

    def run(**over):
        return subprocess.run(["bash", str(SCRIPT)], env={**env, **over}, capture_output=True, text=True)

    def decisions():
        f = proj / "logs" / "vps_deploy_decisions.jsonl"
        return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []

    return {"work": work, "proj": proj, "run": run, "decisions": decisions,
            "sysctl_log": tmp_path / "sysctl.log", "state": tmp_path / "state"}


def test_nothing_new_is_a_silent_noop(rig):
    assert rig["run"]().returncode == 0
    assert rig["decisions"]() == []
    assert not rig["sysctl_log"].exists()


def test_docs_only_push_is_pulled_without_gate_or_restart(rig):
    sha = _commit(rig["work"], "04_EXECUTION/Q.md", "q1")
    r = rig["run"](PMBOT_GATE_CMD="false")  # a red gate must not matter for docs-only
    assert r.returncode == 0, r.stderr
    assert _git(rig["proj"], "rev-parse", "HEAD") == sha
    assert not rig["sysctl_log"].exists()
    assert [d["outcome"] for d in rig["decisions"]()] == ["docs_only"]


def test_red_gate_pulls_nothing_and_is_not_retried_on_same_sha(rig):
    before = _git(rig["proj"], "rev-parse", "HEAD")
    sha = _commit(rig["work"], "src/prediction_market_bot/other.py", "x = 1\n")
    r = rig["run"](PMBOT_GATE_CMD="false")
    assert r.returncode == 1
    assert _git(rig["proj"], "rev-parse", "HEAD") == before
    assert not rig["sysctl_log"].exists()
    assert (rig["state"] / "rejected_sha").read_text().strip() == sha
    # same SHA again: silent no-op, no second decision row
    assert rig["run"](PMBOT_GATE_CMD="false").returncode == 0
    assert [d["outcome"] for d in rig["decisions"]()] == ["gate_red"]
    # a NEW commit re-arms it
    _commit(rig["work"], "src/prediction_market_bot/other.py", "x = 2\n")
    rig["run"](PMBOT_GATE_CMD="true")  # exit code depends on GNU date (restart verify); the pull is the point
    assert _git(rig["proj"], "rev-parse", "HEAD") != before


@pytest.mark.skipif(sys.platform != "linux", reason="restart verification uses GNU date -d (the VPS)")
def test_code_push_gates_pulls_restarts_dashboard_only_when_t4_unaffected(rig):
    sha = _commit(rig["work"], "src/prediction_market_bot/other.py", "x = 1\n")
    r = rig["run"]()
    assert r.returncode == 0, r.stderr
    assert _git(rig["proj"], "rev-parse", "HEAD") == sha
    calls = rig["sysctl_log"].read_text()
    assert "restart pmbot-web-dashboard" in calls.splitlines()
    assert not any(l.startswith("restart") and "t4-mlb" in l for l in calls.splitlines())
    d = rig["decisions"]()[-1]
    assert d["outcome"] == "deployed" and d["t4_mlb_verdict"] == "not_needed"


def test_dirty_tracked_file_outside_cron_roots_blocks_the_pull(rig):
    (rig["proj"] / "04_EXECUTION" / "Q.md").write_text("hand edit on the box")
    _commit(rig["work"], "04_EXECUTION/Q2.md", "new")
    assert rig["run"]().returncode == 1
    assert [d["outcome"] for d in rig["decisions"]()] == ["dirty_tree_abort"]


# ---- W72.3 (GG-661 / GG-668) -------------------------------------------------------------------
STUB_POLICY = (
    "import os, sys\n"
    "v = os.environ.get('STUB_VERDICT', 'not_needed')\n"
    "open(os.environ['GITHUB_OUTPUT'], 'a').write(f'restart_t4={str(v == \"restart\").lower()}\\nverdict={v}\\n')\n"
)


def _status(rig):
    f = rig["state"] / "deploy_status.json"
    return json.loads(f.read_text()) if f.exists() else {}


def test_quiet_tick_writes_ok_status(rig):
    assert rig["run"]().returncode == 0
    st = _status(rig)
    assert st["outcome"] == "noop" and st["ok"] is True


def test_gate_red_status_is_an_alarm_state_not_just_a_log_line(rig):
    _commit(rig["work"], "src/prediction_market_bot/other.py", "x = 1\n")
    rig["run"](PMBOT_GATE_CMD="false")
    st = _status(rig)
    assert st["outcome"] == "gate_red" and st["ok"] is False and st["fail_since"]
    chk = subprocess.run([sys.executable, str(TRUTH), "--proj", str(rig["proj"]), "--state-dir", str(rig["state"]),
                          "--systemctl", "false", "check"], capture_output=True, text=True)
    assert "ALARM deploy gate_red" in chk.stdout


def test_dirty_tree_abort_status_is_failing(rig):
    (rig["proj"] / "04_EXECUTION" / "Q.md").write_text("hand edit on the box")
    _commit(rig["work"], "04_EXECUTION/Q2.md", "new")
    rig["run"]()
    assert _status(rig)["outcome"] == "dirty_tree_abort" and _status(rig)["ok"] is False


@pytest.mark.parametrize("verdict", ["skip_live_game", "skip_game_state_unknown"])
def test_skipped_t4_restart_writes_pending_marker_and_retry_fires_when_clear(rig, verdict):
    _commit(rig["work"], "scripts/deploy_restart_policy.py", STUB_POLICY)
    rig["run"](STUB_VERDICT=verdict)                       # rc depends on GNU date; the marker is the point
    marker = rig["state"] / "t4_pending_restart.json"
    assert marker.exists() and json.loads(marker.read_text())["verdict"] == verdict
    log = rig["sysctl_log"].read_text().splitlines() if rig["sysctl_log"].exists() else []
    assert not any(l.startswith("restart") and "t4-mlb" in l for l in log)
    # next tick, a game is still live: stays pending, original `since` kept, still no t4 restart
    since = json.loads(marker.read_text())["since"]
    rig["run"](STUB_VERDICT="skip_live_game")
    assert json.loads(marker.read_text())["since"] == since
    # next tick, no live game: t4-mlb restarts, marker cleared, decision recorded
    rig["run"](STUB_VERDICT="restart")
    log = rig["sysctl_log"].read_text().splitlines()
    assert "restart t4-mlb" in log
    assert not marker.exists()
    assert rig["decisions"]()[-1]["outcome"] == "pending_restart_done"


def test_no_marker_means_no_retry(rig):
    rig["run"](STUB_VERDICT="restart")
    assert not rig["sysctl_log"].exists()


def test_policy_pending_flag_ignores_changed_files():
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import deploy_restart_policy as p
    finally:
        sys.path.pop(0)
    v, _ = p.decide(None, set(), {"dates": []})
    assert v == p.RESTART
    v, _ = p.decide(None, set(), {"dates": [{"games": [{"status": {"abstractGameState": "Live"}, "teams": {}}]}]})
    assert v == p.SKIP_LIVE

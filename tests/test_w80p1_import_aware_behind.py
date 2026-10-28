"""W80P.1: "a running service is behind box HEAD" is import-aware and has ONE definition.

W79.1 found the SURFACE BUDGET RED on "t4-mlb running 03ad6df9, 8.33h behind box HEAD" although nothing t4-mlb
imports had changed: runtime_registry.probe_local counted every src/ and scripts/ commit, while the deploy restart
policy (GG-432) restarts t4-mlb only when a file it imports changes. Both now call deploy_truth.unapplied_changes,
which uses the restart policy's import closure.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


dt = _load("deploy_truth", "scripts/ops/deploy_truth.py")
rr = _load("runtime_registry_w80p1", "scripts/runtime_registry.py")

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}
ENTRY = "src/prediction_market_bot/run_t4_mlb_live.py"
IMPORTED = "src/prediction_market_bot/t4_core.py"
UNRELATED = "src/prediction_market_bot/pregame_shadow/silent_arms.py"


def _git(cwd, *a, env=None):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True,
                          env=env or ENV).stdout.strip()


def _commit(proj, rel, text, when: datetime):
    p = proj / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    _git(proj, "add", rel)
    iso = when.strftime("%Y-%m-%dT%H:%M:%S+0000")
    _git(proj, "commit", "-q", "-m", rel, env={**ENV, "GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso})
    return _git(proj, "rev-parse", "HEAD")


@pytest.fixture()
def box(tmp_path):
    """A miniature box checkout: t4-mlb's entry imports t4_core; silent_arms is not imported by it."""
    p = tmp_path / "box"
    p.mkdir()
    _git(p, "init", "-q", "-b", "main")
    for rel in ("scripts/deploy_restart_policy.py", "scripts/ops/deploy_truth.py"):
        (p / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, p / rel)
    now = datetime.now(timezone.utc)
    (p / "src/prediction_market_bot").mkdir(parents=True)
    (p / "src/prediction_market_bot/__init__.py").write_text("")
    (p / ENTRY).write_text("from prediction_market_bot import t4_core\n")
    _commit(p, IMPORTED, "X = 1\n", now - timedelta(hours=30))
    _git(p, "add", "-A")
    iso = (now - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%S+0000")
    _git(p, "commit", "-q", "-m", "base", env={**ENV, "GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso})
    return p, now


def test_unrelated_merge_is_not_behind(box):
    p, now = box
    run_sha = _git(p, "rev-parse", "HEAD")
    head = _commit(p, UNRELATED, "def f():\n    return 1\n", now - timedelta(hours=8))
    hits, first = dt.unapplied_changes(p, "t4-mlb", run_sha, head)
    assert hits == [] and first is None


def test_imported_file_changed_is_behind(box):
    p, now = box
    run_sha = _git(p, "rev-parse", "HEAD")
    _commit(p, UNRELATED, "def f():\n    return 1\n", now - timedelta(hours=9))
    head = _commit(p, IMPORTED, "X = 2\n", now - timedelta(hours=8))
    hits, first = dt.unapplied_changes(p, "t4-mlb", run_sha, head)
    assert hits == [IMPORTED]
    # age is measured from the first commit that touched an imported file, not the first unrelated one
    assert abs((now.timestamp() - first) / 3600 - 8) < 0.01


def test_same_closure_as_the_restart_policy(box):
    """One shared definition: the set unapplied_changes uses for t4-mlb IS the restart policy's import closure."""
    p, _ = box
    policy = _load("drp_w80p1", "scripts/deploy_restart_policy.py")
    assert dt.relevant_files(p, "t4-mlb") == policy.import_closure(p)


def _fake_systemctl_dir(tmp_path, started: datetime) -> str:
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    f = d / "systemctl"
    f.write_text("#!/bin/sh\necho LoadState=loaded\necho ActiveState=active\necho SubState=running\n"
                 f"echo 'ActiveEnterTimestamp={started.strftime('%a %Y-%m-%d %H:%M:%S')} UTC'\necho NRestarts=0\n")
    f.chmod(0o755)
    return str(d)


def _budget(p, tmp_path, monkeypatch, started):
    monkeypatch.setenv("PATH", _fake_systemctl_dir(tmp_path, started) + os.pathsep + os.environ["PATH"])
    probe = rr.probe_local({"root": str(p), "units": ["t4-mlb.service"], "writes": []})
    probe["unit_files"] = ["t4-mlb.service"]  # W92.1: a live unit with no unit file is NOT INSTALLED (RED); this fixture has none on disk
    reg = [{"key": "systemd|t4-mlb.service", "kind": "systemd", "status": "live", "purpose": "t4", "pillar": "PROOF",
            "alarm": "deploy truth", "reviewed": True}]
    return probe["services"]["t4-mlb.service"], rr.evaluate(reg, probe)


def test_probe_unrelated_merge_keeps_budget_green(box, tmp_path, monkeypatch):
    """The W79.1 case end to end: t4-mlb started, then an unrelated src/ merge 8h ago -> GREEN, 0h behind."""
    p, now = box
    _commit(p, UNRELATED, "def f():\n    return 1\n", now - timedelta(hours=8))
    svc, ev = _budget(p, tmp_path, monkeypatch, now - timedelta(hours=20))
    assert svc["behind_h"] == 0.0 and svc["unapplied_files"] == 0
    assert ev["budget"] == "GREEN", ev["reasons"]


def test_probe_imported_change_goes_red(box, tmp_path, monkeypatch):
    p, now = box
    _commit(p, IMPORTED, "X = 3\n", now - timedelta(hours=8))
    svc, ev = _budget(p, tmp_path, monkeypatch, now - timedelta(hours=20))
    assert svc["unapplied_files"] == 1 and svc["behind_h"] > rr.BEHIND_RED_H
    assert ev["budget"] == "RED" and any("BEHIND systemd|t4-mlb.service" in r for r in ev["reasons"])


def test_probe_uses_the_deploy_log_sha_not_commit_dates(box, tmp_path, monkeypatch):
    """GG-920 (W80R.1, 10-16): an imported-file commit dated BEFORE the process start but deployed AFTER it. The old
    `rev-list --before=<start>` called that commit "running" (0.0h behind, false GREEN); the deploy log says otherwise."""
    import json as _json
    p, now = box
    deployed = _git(p, "rev-parse", "HEAD")                        # what the deploy actually put on the box
    _commit(p, IMPORTED, "X = 9\n", now - timedelta(hours=20))      # dated before start, pulled later
    start = now - timedelta(hours=12)
    (p / "logs").mkdir()
    (p / "logs" / "vps_deploy_decisions.jsonl").write_text(_json.dumps(
        {"ts": (start + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), "after": deployed, "outcome": "deployed"}) + "\n")
    svc, ev = _budget(p, tmp_path, monkeypatch, start)
    assert svc["run_sha"] == deployed and svc["unapplied_files"] == 1 and svc["behind_h"] > rr.BEHIND_RED_H
    assert ev["budget"] == "RED"

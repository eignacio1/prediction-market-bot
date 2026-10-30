"""W72.3 (GG-661): scripts/ops/deploy_truth.py -- service-code staleness, pending marker, deploy status."""
from __future__ import annotations

import importlib.util
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("deploy_truth", REPO / "scripts" / "ops" / "deploy_truth.py")
dt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dt)

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}


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


def _fake_systemctl(tmp_path, started: datetime | None) -> str:
    f = tmp_path / "sysctl.sh"
    if started is None:
        f.write_text("#!/bin/sh\necho ActiveState=inactive\n")
    else:
        f.write_text("#!/bin/sh\necho ActiveState=active\n"
                     f"echo 'ActiveEnterTimestamp={started.strftime('%a %Y-%m-%d %H:%M:%S')} UTC'\n")
    f.chmod(0o755)
    return str(f)


@pytest.fixture()
def proj(tmp_path):
    p = tmp_path / "proj"
    p.mkdir()
    _git(p, "init", "-q", "-b", "main")
    return p


def test_current_service_has_no_alarm(proj, tmp_path):
    now = datetime.now(timezone.utc)
    _commit(proj, "src/prediction_market_bot/a.py", "x=1\n", now - timedelta(hours=10))
    rows = dt.staleness(proj, tmp_path / "st", services=("pmbot-web-dashboard",),
                        systemctl=_fake_systemctl(tmp_path, now - timedelta(hours=1)), now=now)
    assert rows[0]["state"] == "CURRENT" and not rows[0]["alarm"]


def test_stale_over_6h_alarms_and_under_6h_does_not(proj, tmp_path):
    now = datetime.now(timezone.utc)
    _commit(proj, "src/prediction_market_bot/a.py", "x=1\n", now - timedelta(hours=20))
    _commit(proj, "src/prediction_market_bot/a.py", "x=2\n", now - timedelta(hours=8))
    sysctl = _fake_systemctl(tmp_path, now - timedelta(hours=12))        # started before the 8h-old change
    r = dt.staleness(proj, tmp_path / "st", services=("pmbot-web-dashboard",), systemctl=sysctl, now=now)[0]
    assert r["state"] == "STALE" and r["alarm"] and r["age_h"] > 6
    sysctl = _fake_systemctl(tmp_path, now - timedelta(hours=12))
    r = dt.staleness(proj, tmp_path / "st", services=("pmbot-web-dashboard",), systemctl=sysctl, now=now,
                     max_age_h=24)[0]
    assert r["state"] == "STALE" and not r["alarm"]


def test_docs_change_after_start_is_not_stale_for_dashboard(proj, tmp_path):
    now = datetime.now(timezone.utc)
    _commit(proj, "src/prediction_market_bot/a.py", "x=1\n", now - timedelta(hours=20))
    _commit(proj, "04_EXECUTION/Q.md", "q\n", now - timedelta(hours=9))
    r = dt.staleness(proj, tmp_path / "st", services=("pmbot-web-dashboard",),
                     systemctl=_fake_systemctl(tmp_path, now - timedelta(hours=12)), now=now)[0]
    assert r["state"] == "CURRENT"


def test_not_running_service_is_not_an_alarm(proj, tmp_path):
    now = datetime.now(timezone.utc)
    _commit(proj, "src/prediction_market_bot/a.py", "x=1\n", now)
    r = dt.staleness(proj, tmp_path / "st", services=("t4-mlb",),
                     systemctl=_fake_systemctl(tmp_path, None), now=now)[0]
    assert r["state"] == "NOT_RUNNING" and not r["alarm"]


def test_exact_sha_from_deploy_log_beats_commit_date(proj, tmp_path):
    now = datetime.now(timezone.utc)
    a = _commit(proj, "src/prediction_market_bot/a.py", "x=1\n", now - timedelta(hours=30))
    _commit(proj, "src/prediction_market_bot/a.py", "x=2\n", now - timedelta(hours=20))
    start = now - timedelta(hours=10)
    # deploy log says the process started on `a` (deploy lagged the commit)
    decisions = [{"ts": (start + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), "after": a,
                  "outcome": "deployed"}]
    sha, how = dt.sha_at(proj, start, decisions)
    assert sha == a and how == "deploy_log"


def test_marker_keeps_original_since_and_alarms_after_6h(tmp_path):
    t0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    dt.marker_set(tmp_path, "skip_live_game", "abc", "live", now=t0)
    rec = dt.marker_set(tmp_path, "skip_live_game", "abc", "live", now=t0 + timedelta(hours=7))
    assert rec["since"] == "2026-10-13T12:00:00Z"
    lines = dt.check(tmp_path, tmp_path, systemctl="false", max_age_h=6, now=t0 + timedelta(hours=7))
    assert any(l.startswith("ALARM t4-mlb restart PENDING") for l in lines)
    assert dt.marker_clear(tmp_path)
    assert not any("PENDING" in l for l in dt.check(tmp_path, tmp_path, "false", 6, now=t0))


def test_status_fail_since_persists_and_ok_resets(tmp_path):
    t0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    dt.status_write(tmp_path, "gate_red", "x", now=t0)
    r = dt.status_write(tmp_path, "gate_red", "x", now=t0 + timedelta(hours=1))
    assert r["fail_since"] == "2026-10-13T12:00:00Z" and r["last_ok_ts"] is None
    r = dt.status_write(tmp_path, "deployed", "", now=t0 + timedelta(hours=2))
    assert r["ok"] and r["fail_since"] is None


def test_short_fetch_failure_is_inside_grace_long_one_alarms(tmp_path):
    t0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    dt.status_write(tmp_path, "fetch_failed", "net", now=t0)
    assert dt.check(tmp_path, tmp_path, "false", 6, now=t0 + timedelta(minutes=10))[0].startswith("OK")
    assert dt.check(tmp_path, tmp_path, "false", 6, now=t0 + timedelta(hours=2))[0].startswith("ALARM")


# ---- W95.3 (GG-1462): box HEAD vs origin/main -------------------------------------------------------------
def _remote_pair(tmp_path, now):
    """A box checkout one commit behind its origin/main; returns (box, push_fn)."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "main")
    _commit(origin, "src/prediction_market_bot/a.py", "x=1\n", now - timedelta(hours=9))
    box = tmp_path / "box"
    _git(tmp_path, "clone", "-q", str(origin), "box")
    return box, origin


def _fetch(box):
    _git(box, "fetch", "-q", "origin")


def test_head_lag_current_when_box_is_at_remote(tmp_path):
    now = datetime.now(timezone.utc)
    box, _ = _remote_pair(tmp_path, now)
    assert dt.head_lag(box, now=now)["state"] == "CURRENT"


def test_head_lag_inside_bound_no_alarm_outside_alarms(tmp_path):
    now = datetime.now(timezone.utc)
    box, origin = _remote_pair(tmp_path, now)
    _commit(origin, "src/prediction_market_bot/a.py", "x=2\n", now - timedelta(minutes=20))
    _fetch(box)
    r = dt.head_lag(box, now=now)
    assert r["state"] == "BEHIND" and not r["alarm"] and 19 < r["lag_min"] < 21
    r = dt.head_lag(box, now=now + timedelta(minutes=40))          # same pending commit, 60 min old
    assert r["alarm"]
    lines = dt.check(box, tmp_path / "st", "false", 6, now=now + timedelta(minutes=40))
    assert any(l.startswith("ALARM box HEAD") for l in lines)


def test_head_lag_ignores_unrelated_merges(tmp_path):
    now = datetime.now(timezone.utc)
    box, origin = _remote_pair(tmp_path, now)
    _commit(origin, "04_EXECUTION/ACTIVE_QUEUE.md", "docs\n", now - timedelta(hours=5))
    _fetch(box)
    r = dt.head_lag(box, now=now)
    assert r["state"] == "BEHIND_UNRELATED" and not r["alarm"]


def test_head_lag_ages_from_first_service_file_commit_not_latest(tmp_path):
    now = datetime.now(timezone.utc)
    box, origin = _remote_pair(tmp_path, now)
    _commit(origin, "src/prediction_market_bot/a.py", "x=2\n", now - timedelta(hours=3))
    _commit(origin, "src/prediction_market_bot/a.py", "x=3\n", now - timedelta(minutes=1))
    _fetch(box)
    assert dt.head_lag(box, now=now)["alarm"]


def test_head_lag_not_a_checkout_is_silent(tmp_path):
    assert dt.head_lag(tmp_path / "nothing", now=datetime.now(timezone.utc)) is None

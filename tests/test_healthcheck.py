"""deploy/healthcheck.sh (W72.3 / GG-669): green when healthy, red only on a real fault."""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "deploy" / "healthcheck.sh"

pytest.importorskip("sklearn")
pytest.importorskip("joblib")

CRON = """\
3-58/5 * * * * bash scripts/ops/vps_deploy.sh
0 14 * * * python scripts/run_mlb_pregame.py
0 9 * * * python scripts/run_resolve_mlb.py
*/10 * * * * python scripts/archive_market_prices.py
0 17 * * * bash deploy/healthcheck.sh
"""


def _git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


@pytest.fixture
def rig(tmp_path):
    proj = tmp_path / "proj"
    for d in ("models", "deploy", "logs", "scripts/ops"):
        (proj / d).mkdir(parents=True)
    (proj / "src").symlink_to(REPO / "src")
    shutil.copy(REPO / "scripts/ops/deploy_truth.py", proj / "scripts/ops/deploy_truth.py")
    (proj / "models/mlb_v1_model.joblib").write_bytes(b"x")
    (proj / "models/mlb_v1_model_meta.json").write_text("{}")
    (proj / ".env").write_text("BOT_ENV=paper\nVENUE_API_KEY=abc123\n")
    os.chmod(proj / ".env", 0o600)
    (proj / "deploy/demo_fill.env").write_text("X=1\n")
    os.chmod(proj / "deploy/demo_fill.env", 0o644)
    for cron in ("cron.conf",):
        (proj / "deploy" / cron).write_text(CRON)
    _git(proj, "init", "-q")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-qm", "init")

    sysctl = tmp_path / "systemctl"
    sysctl.write_text('#!/bin/sh\nif [ "$1" = is-active ]; then echo "${FAKE_ACTIVE:-active}"; '
                      'else echo "${FAKE_NR:-0}"; fi\n')
    sysctl.chmod(sysctl.stat().st_mode | stat.S_IXUSR)
    crontab = tmp_path / "crontab.txt"
    crontab.write_text(CRON)
    return proj, sysctl, crontab


def run(rig, **extra):
    proj, sysctl, crontab = rig
    env = {**os.environ, "PMBOT_DIR": str(proj), "PMBOT_PYTHON": sys.executable,
           "PMBOT_SYSTEMCTL": str(sysctl), "PMBOT_CRONTAB_CMD": f"cat {crontab}",
           "PMBOT_SKIP_NET": "1", "PMBOT_MIN_OPENSSL": "0", **extra}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    return r.returncode, r.stdout


def test_healthy_is_green(rig):
    rc, out = run(rig)
    assert rc == 0, out
    assert "HEALTHY: 0 faults" in out
    assert "[FAIL]" not in out


def test_live_bot_env_is_red(rig):
    proj = rig[0]
    (proj / ".env").write_text("BOT_ENV=live\nVENUE_API_KEY=abc123\n")
    rc, out = run(rig)
    assert rc == 1 and "BOT_ENV=live" in out


def test_env_mode_open_is_red(rig):
    os.chmod(rig[0] / ".env", 0o644)
    rc, out = run(rig)
    assert rc == 1 and ".env mode 644" in out


def test_env_bak_copy_is_red_and_secret_not_echoed(rig):
    (rig[0] / ".env.bak.20260915T055650Z").write_text("BOT_ENV=paper\nVENUE_API_KEY=abc123\n")
    os.chmod(rig[0] / ".env.bak.20260915T055650Z", 0o600)
    rc, out = run(rig)
    assert rc == 1 and ".env.bak.20260915T055650Z" in out
    assert "abc123" not in out


def test_env_secret_not_echoed(rig):
    rc, out = run(rig)
    assert "abc123" not in out


def test_missing_model_is_red(rig):
    (rig[0] / "models/mlb_v1_model.joblib").unlink()
    rc, out = run(rig)
    assert rc == 1 and "model" in out


def test_service_inactive_is_red(rig):
    rc, out = run(rig, FAKE_ACTIVE="failed")
    assert rc == 1 and "t4-mlb is not active" in out


def test_service_restarts_only_warn(rig):
    rc, out = run(rig, FAKE_NR="3")
    assert rc == 0 and "[WARN] t4-mlb active but NRestarts=3" in out


def test_missing_cron_arm_is_red(rig):
    rig[2].write_text(CRON.replace("run_resolve_mlb.py", "other.py"))
    rc, out = run(rig)
    assert rc == 1 and "MISSING from crontab: run_resolve_mlb.py" in out


def test_commented_cron_arm_does_not_count(rig):
    rig[2].write_text(CRON.replace("0 17 * * * bash deploy/healthcheck.sh", "# 0 17 * * * bash deploy/healthcheck.sh"))
    rc, out = run(rig)
    assert rc == 1 and "healthcheck.sh" in out


def test_cron_mirror_drift_warns_not_fails(rig):
    rig[2].write_text(CRON + "5 5 * * * python scripts/new_unmirrored.py\n")
    rc, out = run(rig)
    assert rc == 0 and "new_unmirrored.py" in out and "[WARN] cron-mirror drift" in out


def test_edited_demo_fill_env_is_red(rig):
    (rig[0] / "deploy/demo_fill.env").write_text("X=2\n")
    rc, out = run(rig)
    assert rc == 1 and "differs from git HEAD" in out


def test_world_writable_demo_fill_env_is_red(rig):
    os.chmod(rig[0] / "deploy/demo_fill.env", 0o666)
    rc, out = run(rig)
    assert rc == 1 and "writable" in out


def test_failed_deploy_status_is_red(rig, tmp_path):
    # deploy_truth.py reads STATE_DIR; default is /var/lib/pmbot-deploy, which a test must not touch,
    # so only assert that an ALARM line, when present in the check output, becomes a FAIL.
    proj = rig[0]
    stub = proj / "scripts/ops/deploy_truth.py"
    stub.write_text("print('DEPLOY TRUTH (stub)')\nprint('  ALARM last deploy gate_red')\n")
    rc, out = run(rig)
    assert rc == 1 and "[FAIL] deploy truth: ALARM last deploy gate_red" in out


def test_old_openssl_is_red(rig):
    rc, out = run(rig, PMBOT_MIN_OPENSSL="99")
    assert rc == 1 and "OpenSSL < 3" in out

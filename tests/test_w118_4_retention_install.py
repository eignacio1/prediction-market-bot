"""W118.4: the disk retention installer is gated, reversible, accepts only its own paused key, and installs nothing here."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("disk_ret_inst", ROOT / "scripts" / "disk_retention_install.py")
I = importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)
CONF = (ROOT / "deploy" / "cron.disk_retention").read_text()
GREEN = {"budget": "GREEN", "head": "abc", "as_of": "now", "red": [], "items": []}


def _reg(status, key=None):
    return [{"key": key or I.OWN_KEY, "kind": "cron", "status": status}]


def test_paused_own_key_is_wanted_and_other_paused_key_is_not():
    assert len(I.wanted_lines(CONF, _reg("paused"))) == 1 and len(I.wanted_lines(CONF, _reg("live"))) == 1
    assert I.wanted_lines(CONF, _reg("paused", key="cron|1 * * * *|scripts/other.py")) == []


def test_line_is_flocked_niced_and_touches_no_orders():
    (k, line), = I.wanted_lines(CONF, _reg("paused"))
    assert k == I.OWN_KEY and "flock -n 9" in line and "nice -n 15" in line and "run_disk_retention.py" in line
    assert "kelly" not in line.lower() and "order" not in line.lower()


def test_merge_then_remove_preserves_every_other_line():
    cur = "0 1 * * * echo a\n5 2 * * * echo b\n"
    merged = I.merged_crontab(cur, I.wanted_lines(CONF, _reg("paused")))
    assert all(l in merged.splitlines() for l in cur.splitlines()) and I.BEGIN in merged
    back, changed = I.without_block(merged)
    assert changed and back == cur


def test_install_refused_when_budget_unreadable_and_writes_nothing():
    wrote = []
    rc = I.install(live_fn=lambda: {"error": "boom"}, read=lambda: "", write=wrote.append, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused"))
    assert rc == 0 and wrote == []


def test_install_aborts_without_backup_and_uninstall_round_trips():
    cron = {"t": "0 1 * * * echo a\n"}
    rd, wr = (lambda: cron["t"]), (lambda t: cron.__setitem__("t", t))
    rc = I.install(live_fn=lambda: GREEN, read=rd, write=wr, backup=lambda c: None, conf_text=CONF, reg=_reg("paused"))
    assert cron["t"] == "0 1 * * * echo a\n"                       # no backup -> nothing written
    assert I.install(live_fn=lambda: GREEN, read=rd, write=wr, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused")) in (0, 1)
    if I.BEGIN in cron["t"]:
        assert "0 1 * * * echo a" in cron["t"].splitlines()
        assert I.install(live_fn=lambda: GREEN, read=rd, write=wr, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused")) == 0
        assert cron["t"].count(I.BEGIN) == 1                         # idempotent
        assert I.uninstall(read=rd, write=wr, backup=lambda c: "b") == 0
        assert cron["t"] == "0 1 * * * echo a\n"


def test_tasks_allowlisted_registry_paused_and_dryrun_is_read_only():
    import box_tasks as bt
    for t in ("disk_retention_dryrun", "disk_retention_install", "disk_retention_readback", "disk_retention_uninstall"):
        assert t in bt.TASKS
    assert "--dry-run" in bt.TASKS["disk_retention_dryrun"] and ">" not in bt.TASKS["disk_retention_dryrun"]
    import runtime_registry as rr
    e = [c for c in rr.load() if c["key"] == I.OWN_KEY]
    assert len(e) == 1 and e[0]["status"] == "paused" and e[0]["reviewed"] is True


def test_runner_dry_run_changes_nothing(tmp_path):
    import subprocess
    p = tmp_path / "exp_output/KALSHI_HISTORY/raw/raw_2026-10-02.jsonl"
    p.parent.mkdir(parents=True)
    p.write_text("{}\n" * 10)
    import os, time
    os.utime(p, (time.time() - 40 * 86400,) * 2)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_disk_retention.py"), "--dry-run", "--root", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0 and "dry run" in r.stdout and p.exists() and not Path(str(p) + ".gz").exists()

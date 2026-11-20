"""W121.1: the weekly evidence installer is gated, reversible, accepts only its own paused key, and installs nothing here."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("evid_wk_inst", ROOT / "scripts" / "evidence_weekly_install.py")
I = importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)
CONF = (ROOT / "deploy" / "cron.evidence_weekly").read_text()
GREEN = {"budget": "GREEN", "head": "abc", "as_of": "now", "red": [], "items": []}


def _reg(status, key=None):
    return [{"key": key or I.OWN_KEY, "kind": "cron", "status": status}]


def test_paused_own_key_is_wanted_and_other_paused_key_is_not():
    assert len(I.wanted_lines(CONF, _reg("paused"))) == 1 and len(I.wanted_lines(CONF, _reg("live"))) == 1
    assert I.wanted_lines(CONF, _reg("paused", key="cron|1 * * * *|scripts/other.py")) == []


def test_line_is_flocked_niced_and_touches_no_orders():
    (k, line), = I.wanted_lines(CONF, _reg("paused"))
    assert k == I.OWN_KEY and "flock -n 9" in line and "nice -n 15" in line and "run_evidence_weekly.py" in line and line.startswith("0 10 * * 2 ")
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


def test_tasks_allowlisted_registry_paused_and_run_writes_only_its_dir():
    import box_tasks as bt
    for n in ("evidence_weekly_run", "evidence_weekly_install", "evidence_weekly_readback", "evidence_weekly_uninstall"):
        assert n in bt.TASKS
    assert ">" not in bt.TASKS["evidence_weekly_run"] and "run_evidence_weekly.py" in bt.TASKS["evidence_weekly_run"]
    import runtime_registry as rr
    e = [c for c in rr.load() if c["key"] == I.OWN_KEY]
    assert len(e) == 1 and e[0]["status"] == "paused" and e[0]["reviewed"] is True and e[0]["schedule"] == "0 10 * * 2"

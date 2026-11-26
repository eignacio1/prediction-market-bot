"""W127.3: the NBA combo shadow installer is gated, reversible, accepts only its own paused key, and installs nothing here."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("combo_inst", ROOT / "scripts" / "nba_combo_shadow_install.py")
I = importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)

CONF = (ROOT / "deploy" / "cron.nba_combo_shadow").read_text()


def _reg(status, key=None):
    return [{"key": key or I.OWN_KEY, "kind": "cron", "status": status}]


def test_paused_own_key_is_wanted_and_other_paused_key_is_not():
    both = [{"key": k, "kind": "cron", "status": "paused"} for k in I.OWN_KEYS]
    assert len(I.wanted_lines(CONF, both)) == 2 and len(I.wanted_lines(CONF, _reg("paused"))) == 1
    assert I.wanted_lines(CONF, _reg("paused", key="cron|1 * * * *|scripts/other.py")) == []


def test_line_is_evaluate_only_flocked_and_marked():
    (k, line), = I.wanted_lines(CONF, _reg("paused"))
    assert k == I.OWN_KEY and "flock -n 9" in line and "nba_combo_shadow.py" in line
    assert "ORDERS" not in line.upper() and "kelly" not in line.lower()


def test_merge_then_remove_preserves_every_other_line():
    cur = "0 1 * * * echo a\n5 2 * * * echo b\n"
    add = I.wanted_lines(CONF, _reg("paused"))
    merged = I.merged_crontab(cur, add)
    assert all(l in merged.splitlines() for l in cur.splitlines()) and I.BEGIN in merged
    back, changed = I.without_block(merged)
    assert changed and back == cur


def test_install_refused_when_budget_red_and_writes_nothing():
    wrote = []
    rc = I.install(live_fn=lambda: {"error": "boom"}, read=lambda: "", write=wrote.append, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused"))
    assert rc == 0 and wrote == []


def test_registry_entry_is_paused_or_live_and_task_is_allowlisted():
    import box_tasks as bt
    assert "nba_combo_shadow_install" in bt.TASKS
    import runtime_registry as rr
    e = [c for c in rr.load() if c["key"] == I.OWN_KEY]
    assert len(e) == 1 and e[0]["status"] in ("paused", "live") and e[0]["reviewed"] is True  # live after the operator-approved install


def test_line_is_off_unless_env_on_and_has_no_order_path():
    (k, line), = I.wanted_lines(CONF, _reg("paused"))
    assert "PM_COMBO_SHADOW=on" in line and "BOT_ENV=paper" in line
    assert k == "cron|41 * * * *|scripts/nba_combo_shadow.py"


def test_install_writes_one_block_when_budget_green_and_is_idempotent():
    cur = "0 1 * * * echo a\n"
    state = {"c": cur}
    def w(t): state["c"] = t
    green = lambda: {"budget": "GREEN", "head": "x", "as_of": "t", "red": []}
    rc = I.install(live_fn=green, read=lambda: state["c"], write=w, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused"))
    assert rc == 0 and I.BEGIN in state["c"] and "echo a" in state["c"]
    n = state["c"].count("nba_combo_shadow.py")
    I.install(live_fn=green, read=lambda: state["c"], write=w, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused"))
    assert state["c"].count("nba_combo_shadow.py") == n


def test_rfq_line_is_demo_paper_only_capped_and_registered_paused():
    (k, line), = I.wanted_lines(CONF, _reg("paused", key=I.RFQ_KEY))
    assert k == I.RFQ_KEY and "PM_COMBO_RFQ_DEMO=on" in line and "BOT_ENV=paper" in line and "flock -n 8" in line
    assert "LIVE" not in line.upper() and "kelly" not in line.lower()
    import runtime_registry as rr
    e = [c for c in rr.load() if c["key"] == I.RFQ_KEY]
    assert len(e) == 1 and e[0]["status"] in ("paused", "live") and e[0]["reviewed"] is True
    cur = "0 1 * * * echo a\n"
    added = I.merged_crontab(cur, I.wanted_lines(CONF, [{"key": x, "kind": "cron", "status": "paused"} for x in I.OWN_KEYS]))
    back, changed = I.without_block(added)
    assert changed and back == cur and added.count("combo_rfq_demo.py") == 1


def test_install_refused_when_budget_red_for_the_rfq_line_too():
    wrote = []
    regs = [{"key": k, "kind": "cron", "status": "paused"} for k in I.OWN_KEYS]
    I.install(live_fn=lambda: {"error": "boom"}, read=lambda: "", write=wrote.append, backup=lambda c: "b", conf_text=CONF, reg=regs)
    assert wrote == []

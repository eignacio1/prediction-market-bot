"""W80R.1: scripts/box_tasks.py (allowlist, request parsing, redaction, bounding) and scripts/thin_capture_install.py
(GREEN gate, idempotent append). No network, no ssh."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


bt = _load("box_tasks", "scripts/box_tasks.py")
ci = _load("thin_capture_install", "scripts/thin_capture_install.py")


def _req(tmp_path, text, stem="20261016T1600Z_budget_read"):
    p = tmp_path / f"{stem}.toml"
    p.write_text(text)
    return p


def test_allowlist_v1_names():
    assert set(bt.TASKS) >= {"budget_read", "silent_arms_read", "deploy_truth_read", "capture_install",
                             "capture_readback", "nba_opening_preflight"}
    for name in bt.TASKS:
        assert bt.NAME_RE.match(name)


def test_only_capture_install_can_change_the_box():
    writers = {n for n, c in bt.TASKS.items() if any(w in c for w in ("crontab - ", "crontab -e", " install", " uninstall", "rm ", "systemctl restart",
                                                                     "git pull", "git checkout"))}
    assert writers == {"capture_install", "capture_uninstall", "source_capture_install", "source_capture_uninstall",
                       "archive_cron_install", "archive_cron_uninstall"}
    import re
    for name, c in bt.TASKS.items():      # the only redirections allowed are stderr ones; nothing writes a file
        assert not re.search(r">", re.sub(r"2>&1|2>/dev/null", "", c)), name


def test_valid_request(tmp_path):
    assert bt.parse_request(_req(tmp_path, 'task = "budget_read"\nnote = "after #281"\n')) == ("budget_read", "after #281")


@pytest.mark.parametrize("text,why", [
    ('task = "rm_rf"\n', "allowlist"),
    ('task = "budget_read"\ncmd = "rm -rf /"\n', "extra keys"),
    ('task = "budget_read"\nargs = ["--x"]\n', "extra keys"),
    ('task = "budget_read"\nnote = "' + "x" * 201 + '"\n', "note"),
    ('task = "budget_read"\nnote = "a\\nb"\n', "note"),
    ('task = budget_read\n', "TOML"),
])
def test_bad_requests_are_refused(tmp_path, text, why):
    with pytest.raises(bt.BadRequest, match=why):
        bt.parse_request(_req(tmp_path, text))


def test_bad_file_name_refused(tmp_path):
    with pytest.raises(bt.BadRequest, match="file name"):
        bt.parse_request(_req(tmp_path, 'task = "budget_read"\n', stem="budget_read; rm -rf"))


def test_refused_request_never_runs(tmp_path):
    called = []
    out = tmp_path / "r.md"
    bt.run(_req(tmp_path, 'task = "evil"\n'), out, "k", runner=lambda *a, **k: called.append(a))
    assert not called and "REFUSED" in out.read_text() and "Nothing was run" in out.read_text()


def test_run_uses_exactly_the_allowlisted_command(tmp_path):
    seen = {}

    def runner(cmd, **kw):
        seen["cmd"], seen["stdin"] = cmd, kw.get("stdin")
        return subprocess.CompletedProcess(cmd, 0, "SURFACE BUDGET GREEN\nAPI_KEY=abc123\n", "")
    out = tmp_path / "r.md"
    bt.run(_req(tmp_path, 'task = "budget_read"\n'), out, "/k", runner=runner)
    remote = seen["cmd"][-1]
    assert seen["cmd"][:4] == ["ssh", "-n", "-i", "/k"] and bt.HOST in seen["cmd"]
    assert seen["stdin"] is subprocess.DEVNULL          # run 2 regression: ssh swallowed the request list
    assert remote.startswith(f"cd {bt.BOX} && timeout {bt.TIMEOUT_S} bash -c ")
    assert "runtime_registry.py live" in remote
    txt = out.read_text()
    assert "SURFACE BUDGET GREEN" in txt and "abc123" not in txt and "API_KEY=[REDACTED]" in txt


def test_quoting_keeps_command_one_argument():
    q = bt._sh_quote("echo 'a' && echo b")
    assert subprocess.run(["bash", "-c", f"printf %s {q}"], capture_output=True, text=True).stdout == "echo 'a' && echo b"


def test_redaction():
    raw = ("KALSHI_API_KEY_ID=1234-5678\nexport DB_PASSWORD: hunter2\nAuthorization: Bearer abcdefghijklmnop\n"
           "-----BEGIN OPENSSH PRIVATE KEY-----\nAAAA\n-----END OPENSSH PRIVATE KEY-----\n"
           "token ghp_" + "a" * 30 + "\nbox HEAD 9544c988 ok\n")
    out = bt.redact(raw)
    for secret in ("1234-5678", "hunter2", "abcdefghijklmnop", "AAAA", "ghp_aaaa"):
        assert secret not in out
    assert "box HEAD 9544c988 ok" in out


def test_bound():
    s = "x" * 200_000
    b = bt.bound(s, 1000)
    assert len(b.encode()) < 1200 and "bytes cut" in b
    assert bt.bound("short") == "short"


def test_collect_only_added_request_files(tmp_path):
    g = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, text=True).stdout.strip()
    g("init", "-q", "-b", "main"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    (tmp_path / "a.md").write_text("a"); g("add", "-A"); g("commit", "-qm", "a"); before = g("rev-parse", "HEAD")
    d = tmp_path / bt.REQ_DIR; d.mkdir(parents=True)
    (d / "20261016T1600Z_budget_read.toml").write_text('task = "budget_read"\n')
    (tmp_path / "b.md").write_text("b"); g("add", "-A"); g("commit", "-qm", "b"); after = g("rev-parse", "HEAD")
    assert bt.collect(before, after, cwd=tmp_path) == [f"{bt.REQ_DIR}/20261016T1600Z_budget_read.toml"]


def test_dispatch_writes_a_parseable_request(tmp_path):
    p = bt.dispatch("budget_read", 'why "quoted" \\ back', cwd=tmp_path)
    assert bt.parse_request(p)[0] == "budget_read"
    with pytest.raises(bt.BadRequest):
        bt.dispatch("Bad Name; rm", "", cwd=tmp_path)


# ---- thin_capture_install ----
FRAG = (REPO / "deploy" / "cron.thin_capture").read_text()


def test_install_refuses_when_red():
    writes = []
    rc = ci.install(live_fn=lambda: {"budget": "RED", "reasons": ["BEHIND systemd|t4-mlb.service: x"]},
                    read=lambda: "0 * * * * a\n", write=writes.append)
    assert rc == 0 and writes == []


def test_install_refuses_when_unreadable():
    writes = []
    ci.install(live_fn=lambda: {"error": "ssh"}, read=lambda: "", write=writes.append)
    assert writes == []


def test_install_appends_once_and_keeps_every_line():
    state = {"cron": "5 * * * * cd /x && run a\n# comment\n0 1 * * * b\n"}
    green = lambda: {"budget": "GREEN", "reasons": []}  # noqa: E731
    assert ci.install(live_fn=green, read=lambda: state["cron"], write=lambda t: state.update(cron=t)) == 0
    after = state["cron"]
    assert after.startswith("5 * * * * cd /x && run a\n# comment\n0 1 * * * b\n")
    assert after.count(ci.BEGIN) == 1 and "51 * * * * cd" in after
    ci.install(live_fn=green, read=lambda: state["cron"], write=lambda t: state.update(cron=t))
    assert state["cron"] == after                    # idempotent


def test_fragment_block_is_the_registered_line():
    blk = ci.fragment_block(FRAG)
    assert blk[0] == ci.BEGIN and blk[-1] == ci.END
    assert any("scripts/thin_market_depth_capture.py" in l and l.startswith("51 * * * *") for l in blk)


def test_uninstall_removes_only_the_block_and_is_idempotent():
    base = "5 * * * * a\n# c\n"
    state = {"cron": base}
    ci.install(live_fn=lambda: {"budget": "GREEN"}, read=lambda: state["cron"], write=lambda t: state.update(cron=t))
    assert ci.BEGIN in state["cron"]
    ci.uninstall(read=lambda: state["cron"], write=lambda t: state.update(cron=t))
    assert state["cron"] == base
    writes = []
    ci.uninstall(read=lambda: state["cron"], write=writes.append)
    assert writes == []

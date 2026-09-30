"""
T-589 / Deliverable 1 -- PaperTrader._save() must replace the ledger atomically.

Before: `self._path.write_text(...)` truncated the ledger, then wrote it. A crash,
OOM kill or full disk in between left a truncated/empty ledger.
After: temp file in the same directory -> flush -> fsync -> os.replace, inside the
existing flock critical section.

Interruptions here are injected at the real write boundary (RLIMIT_FSIZE making
the kernel refuse the write mid-file; a hard os._exit between write and rename;
fsync failing) -- _save() itself is never mocked.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution import paper_trader as pt
from prediction_market_bot.c5_execution.paper_trader import PaperTrader


def _logger():
    m = MagicMock()
    for n in ("info", "warning", "error", "log"):
        getattr(m, n).return_value = True
    return m


def _pos(i: int, status: str = "OPEN") -> dict:
    return {
        "position_id": f"POS-{i:06d}", "player_name": "Test Player", "player_id": 1,
        "kalshi_ticker": f"KXMLBHIT-26SEP29TESTTST-P{i}-1", "kalshi_threshold": 1,
        "direction": "YES", "mid_price_at_entry": 0.45, "vig_at_entry": 0.02,
        "size_usd": 1.0, "game_date": "2026-09-29", "status": status,
        "padding": "x" * 200,
    }


def _seeded(path: Path, n: int = 5) -> PaperTrader:
    tr = PaperTrader(path, _logger())
    tr._state["open_positions"] = [_pos(i) for i in range(n)]
    assert tr._save() is True
    return tr


def _leftovers(path: Path) -> list[str]:
    return sorted(p.name for p in path.parent.iterdir()
                  if p.name.startswith(path.name + ".tmp"))


# (a) interrupted save leaves the on-disk file byte-identical and parseable -------

def test_fsync_failure_leaves_ledger_byte_identical(tmp_path, monkeypatch):
    path = tmp_path / "p.json"
    tr = _seeded(path)
    before = path.read_bytes()
    tr._state["open_positions"].append(_pos(999))

    def boom(fd):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(os, "fsync", boom)

    assert tr._save() is False
    assert path.read_bytes() == before
    json.loads(path.read_text())


_CHILD_PREAMBLE = textwrap.dedent("""
    import os, sys, json, signal, resource
    from pathlib import Path
    from unittest.mock import MagicMock
    sys.path.insert(0, {src!r})
    os.environ["BOT_ENV"] = "paper"
    from prediction_market_bot.c5_execution import paper_trader as pt
    lg = MagicMock()
    tr = pt.PaperTrader(Path({path!r}), lg)
    tr._state["open_positions"].extend(
        {{"position_id": "NEW-%d" % i, "status": "OPEN", "size_usd": 1.0, "padding": "y" * 200}}
        for i in range(2000))
""")


def _run_child(body: str, path: Path) -> subprocess.CompletedProcess:
    code = _CHILD_PREAMBLE.format(src=str(_SRC), path=str(path)) + textwrap.dedent(body)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)


def test_kernel_refused_write_midfile_leaves_ledger_intact(tmp_path):
    """RLIMIT_FSIZE: the kernel stops the write partway through the new content."""
    path = tmp_path / "p.json"
    _seeded(path)
    before = path.read_bytes()
    limit = len(before) + 20_000            # old file fits; the new (~600KB) cannot
    r = _run_child(f"""
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, ({limit}, {limit}))
        print("SAVE_RESULT", tr._save())
    """, path)
    assert "SAVE_RESULT False" in r.stdout, (r.stdout, r.stderr)
    assert path.read_bytes() == before
    json.loads(path.read_text())
    assert _leftovers(path) == []           # failure path cleans its temp file


def test_hard_kill_between_write_and_rename_leaves_ledger_intact(tmp_path):
    """os._exit after the temp file is fully written but before os.replace()."""
    path = tmp_path / "p.json"
    _seeded(path)
    before = path.read_bytes()
    r = _run_child("""
        def die(*a, **k):
            os._exit(9)
        os.replace = die
        tr._save()
    """, path)
    assert r.returncode == 9, (r.stdout, r.stderr)
    assert path.read_bytes() == before
    json.loads(path.read_text())
    # A SIGKILL cannot run cleanup, so a stale temp is the accepted residue; the
    # ledger itself must be untouched (asserted above).


# (b) no temp file left on success or failure --------------------------------------

def test_no_temp_file_left_after_successful_save(tmp_path):
    path = tmp_path / "p.json"
    tr = _seeded(path)
    tr._state["open_positions"].append(_pos(77))
    assert tr._save() is True
    assert _leftovers(path) == []
    assert sorted(p.name for p in tmp_path.iterdir() if p.name != "p.json.lock") == ["p.json"]


def test_no_temp_file_left_after_failed_save(tmp_path, monkeypatch):
    path = tmp_path / "p.json"
    tr = _seeded(path)
    monkeypatch.setattr(os, "replace", MagicMock(side_effect=OSError(18, "Invalid cross-device link")))
    assert tr._save() is False
    assert _leftovers(path) == []


def test_temp_file_is_in_target_directory(tmp_path, monkeypatch):
    path = tmp_path / "sub" / "p.json"
    tr = PaperTrader(path, _logger())
    seen = {}
    real_replace = os.replace

    def spy(src, dst):
        seen["src"], seen["dst"] = Path(src), Path(dst)
        return real_replace(src, dst)
    monkeypatch.setattr(os, "replace", spy)
    assert tr._save() is True
    assert seen["src"].parent == seen["dst"].parent == path.parent


# (c) full round trip through the real _reload_locked() ------------------------------

def test_round_trip_through_reload_locked(tmp_path):
    path = tmp_path / "p.json"
    tr = _seeded(path, n=25)
    saved = json.loads(json.dumps(tr._state))
    other = PaperTrader(path, _logger())
    with other._lock, other._file_lock():
        other._state = {}
        other._reload_locked()
    assert other._state == saved


def test_save_still_runs_under_the_flock(tmp_path, monkeypatch):
    """The rename must happen inside the existing critical section (no restructuring)."""
    import fcntl
    path = tmp_path / "p.json"
    tr = _seeded(path)
    held = {}
    real_replace = os.replace

    def probe(src, dst):
        fd = open(path.with_suffix(path.suffix + ".lock"), "w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held["locked_by_us"] = False
            fcntl.flock(fd, fcntl.LOCK_UN)
        except BlockingIOError:
            held["locked_by_us"] = True
        finally:
            fd.close()
        return real_replace(src, dst)
    monkeypatch.setattr(os, "replace", probe)
    with tr._lock, tr._file_lock():
        assert tr._save() is True
    assert held["locked_by_us"] is True


# (d) permissions / ownership survive os.replace() -----------------------------------

@pytest.mark.parametrize("mode", [0o600, 0o640, 0o664, 0o644])
def test_mode_preserved(tmp_path, mode):
    path = tmp_path / "p.json"
    tr = _seeded(path)
    os.chmod(path, mode)
    tr._state["open_positions"].append(_pos(5))
    assert tr._save() is True
    assert stat.S_IMODE(os.stat(path).st_mode) == mode


def test_owner_group_preserved(tmp_path):
    path = tmp_path / "p.json"
    tr = _seeded(path)
    before = os.stat(path)
    tr._state["open_positions"].append(_pos(5))
    assert tr._save() is True
    after = os.stat(path)
    assert (after.st_uid, after.st_gid) == (before.st_uid, before.st_gid)


def test_new_file_gets_same_mode_write_text_would(tmp_path):
    old = os.umask(0o022)
    try:
        path = tmp_path / "fresh.json"
        assert PaperTrader(path, _logger())._save() is True
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o644
    finally:
        os.umask(old)

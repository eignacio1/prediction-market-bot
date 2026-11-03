"""W98.3 / GG-1581: T3 lock+stagger -- round trip, % escaping, registry-key stability, foreign lines untouched, backup abort,
a real flock skip, deploy mirrors + registry in sync, box_memory_read parsing."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import box_memory_read as bmr  # noqa: E402
import runtime_registry as rr  # noqa: E402
import t3_lock_stagger as ts  # noqa: E402

NBA = "9,19,29,39,49,59 16-23,0-4 * * * cd $PROJ && $PYTHON scripts/run_nba_pregame_shadow.py --bands T3 >> logs/nba.log 2>&1"
NHL = "*/10 17-23 * * * cd $PROJ && $PYTHON scripts/run_nhl_shadow_staked.py --band T3 >> logs/nhl.log 2>&1"
OTHER = "0 1 * * * cd $PROJ && $PYTHON scripts/other_job.py --x 1 >> logs/o.log 2>&1"
T2 = "5 * * * * cd $PROJ && $PYTHON scripts/run_pregame_shadow.py --bands T2 >> logs/t2.log 2>&1"
ALL = ["SHELL=/bin/bash", "# a comment", NBA, NHL, OTHER, T2]


class Box:
    def __init__(self, text):
        self.text, self.writes = text, 0

    def read(self):
        return self.text

    def write(self, t):
        self.text, self.writes = t, self.writes + 1


def test_round_trip_and_idempotent():
    for l in (NBA, NHL):
        w = ts.wrap(l)
        assert w and ts.wrap(w) is None and ts.unwrap(w) == l
    assert ts.unwrap(NHL) is None


def test_nba_stagger_only_schedule_change():
    w = ts.wrap(NBA)
    assert w.startswith("0,10,20,30,40,50 16-23,0-4 * * * ( flock -n 9 ||")
    assert w.endswith("9>/tmp/nba_pregame_shadow_t3.lock")
    assert ts.wrap(NHL).startswith("*/10 17-23 * * * ( flock")


def test_percent_escaped_and_original_untouched():
    w = ts.wrap(NHL)
    import re
    assert not re.search(r"(?<!\\)%", w)
    assert NHL.split(None, 5)[5] in w


def test_registry_key_stable():
    assert rr._cron_key(ts.wrap(NHL))[0] == rr._cron_key(NHL)[0]
    assert rr._cron_key(ts.wrap(NBA))[0].split("|")[2:] == rr._cron_key(NBA)[0].split("|")[2:]


def test_foreign_and_non_t3_lines_untouched():
    new, n = ts.rewrite_text("\n".join(ALL) + "\n", ts.wrap)
    assert n == 2
    out = new.splitlines()
    assert [out[i] for i in (0, 1, 4, 5)] == [ALL[i] for i in (0, 1, 4, 5)]


def test_install_uninstall(tmp_path):
    b = Box("\n".join(ALL) + "\n")
    assert ts.install(read=b.read, write=b.write, backup=lambda c: tmp_path / "bak") == 0 and b.writes == 1
    assert ts.install(read=b.read, write=b.write, backup=lambda c: tmp_path / "bak") == 0 and b.writes == 1  # idempotent
    assert ts.uninstall(read=b.read, write=b.write, backup=lambda c: tmp_path / "bak") == 0
    assert b.text == "\n".join(ALL) + "\n"


def test_backup_missing_aborts(capsys):
    b = Box("\n".join(ALL) + "\n")
    ts.install(read=b.read, write=b.write, backup=lambda c: None)
    assert b.writes == 0 and "ABORTED" in capsys.readouterr().out


def test_deploy_mirrors_wrapped_and_registry_clean():
    for f in (ROOT / "deploy").glob("cron*"):
        if f.is_file():
            for l in f.read_text().splitlines():
                if ts.is_cron_line(l) and ts._runner(l)[0]:
                    assert ts.WRAP_RE.search(l), (f.name, l[:90])
    assert subprocess.run([sys.executable, "scripts/runtime_registry.py", "check"], cwd=ROOT).returncode == 0


def test_memory_read_parses_oom():
    t = ("Nov  3 kernel: Out of memory: Killed process 1234 (python) total-vm:900000kB, anon-rss:153600kB, file-rss:0kB\n"
         "Nov  3 kernel: Out of memory: Killed process 55 (python) total-vm:1kB, anon-rss:2048kB, file-rss:0kB\n")
    r = bmr.parse_oom(t)
    assert [x["pid"] for x in r] == [1234, 55] and r[0]["anon_rss_mb"] == 150.0

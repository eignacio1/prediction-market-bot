#!/usr/bin/env python3
"""W98.3 / GG-1581: per-runner non-blocking lock + one staggered start for the T3 pre-game shadow cron lines.

WHY: the T3 runners had no lock. On a 1-core, 961 MB box an uncontended NBA T3 run is ~6.5 s (3 s of it is the venue
adapter's mandatory 1.1 s page pacing), but 2-3 copies stacked until the box swapped; runs then took 13-62 min and
the kernel OOM-killed 20 of them in ~90 min. Cause = no lock, not the runner's I/O or logic.

WHAT: each line is wrapped `( flock -n 9 || {skip row; exit 0}; <ORIGINAL COMMAND UNCHANGED> ) 9>/tmp/<name>.lock`.
A run that finds its predecessor still going exits without running and appends one JSON skip row to
logs/t3_skips.jsonl (ts, runner, reason), so a frozen test can tell a skipped window from a silent one.
It changes WHEN a run happens, never what it computes. The only schedule change is NBA pre-game T3 :09 -> :01 (it ran one
minute after run_pregame_shadow's :08).

The wrapper deliberately contains no `>>` and no `--flag` before the original command, so scripts/runtime_registry.py
derives the same key (script + flags) from a wrapped line as from the original.

  python scripts/t3_lock_stagger.py apply-deploy   rewrite the repo's deploy/ mirrors in place (idempotent)
  python scripts/t3_lock_stagger.py install        box: backup crontab -> wrap every original T3 line -> readback
  python scripts/t3_lock_stagger.py uninstall      box: unwrap every wrapped T3 line (backup first)
  python scripts/t3_lock_stagger.py readback       box: which T3 lines are wrapped, lock files, skip rows so far
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SKIP_LOG = "/opt/prediction-market-bot/logs/t3_skips.jsonl"
# name, substring that identifies the runner's T3 line, schedule change (old minute field -> new) or None
RUNNERS = [
    ("nhl_staked_t3", "scripts/run_nhl_shadow_staked.py --band T3", None),
    ("pregame_shadow_t3", "scripts/run_pregame_shadow.py --bands T3", None),
    ("mlb_pregame_shadow_t3", "scripts/run_mlb_pregame_shadow.py --bands T3", None),
    ("nba_pregame_shadow_t3", "scripts/run_nba_pregame_shadow.py --bands T3",
     ("9,19,29,39,49,59", "1,11,21,31,41,51")),
    ("nba_player_points_t3", "scripts/run_nba_player_points_shadow.py --bands T3", None),
    # W100.3 / B-027: the same lock for the T1/T2 shadow lines (box_memory_read 11-05 showed 4 stacked
    # `run_nba_pregame_shadow --bands T2` copies on a box with 51 MB available; the T3 lock covered only T3).
    # One lock per runner+band, so it never delays a different band; no schedule change.
    ("nba_pregame_shadow_t2", "scripts/run_nba_pregame_shadow.py --bands T2", None),
    ("nba_pregame_shadow_t1", "scripts/run_nba_pregame_shadow.py --bands T1", None),
    ("pregame_shadow_t2", "scripts/run_pregame_shadow.py --bands T2", None),
    ("pregame_shadow_t1", "scripts/run_pregame_shadow.py --refresh --bands T1", None),
    ("mlb_pregame_shadow_t2", "scripts/run_mlb_pregame_shadow.py --bands T2", None),
    ("mlb_pregame_shadow_t1", "scripts/run_mlb_pregame_shadow.py --bands T1", None),
    ("nba_player_points_t2", "scripts/run_nba_player_points_shadow.py --bands T2", None),
    ("nba_player_points_t1", "scripts/run_nba_player_points_shadow.py --bands T1", None),
    ("nhl_staked_t2", "scripts/run_nhl_shadow_staked.py --band T2", None),
    ("nhl_staked_t1", "scripts/run_nhl_shadow_staked.py --band T1", None),
]
WRAP_RE = re.compile(r"\( flock -n 9 \|\| \{ printf '.*?t3_skips\.jsonl > /dev/null; exit 0; \}; (?P<orig>.*) \) 9>/tmp/(?P<name>\w+)\.lock\s*$")


def _runner(line: str):
    for name, marker, sched in RUNNERS:
        if marker in line:
            return name, sched
    return None, None


def is_cron_line(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith("#") and not re.match(r"^[A-Z_]+=", s) and len(s.split()) >= 6


def wrap(line: str) -> str | None:
    """The locked+staggered form of an original T3 line, or None if this is not a T3 line (or already wrapped)."""
    if not is_cron_line(line) or WRAP_RE.search(line):
        return None
    name, sched = _runner(line)
    if not name:
        return None
    parts = line.split(None, 5)
    sched_hours = parts[0]
    if sched and sched_hours == sched[0]:
        sched_hours = sched[1]
    head, orig = " ".join([sched_hours] + parts[1:5]), parts[5]
    # `%` is a newline to cron unless escaped, hence every literal % below is written \%.
    skip = ("printf '{\"ts\":\"\\%%s\",\"runner\":\"" + name + "\",\"event\":\"SKIP_LOCKED\","
            "\"reason\":\"previous run still holding /tmp/" + name + ".lock\"}\\n' \"$(date -u +\\%%FT\\%%TZ)\" "
            "| tee -a " + SKIP_LOG + " > /dev/null").replace("%%", "%")
    return "%s ( flock -n 9 || { %s; exit 0; }; %s ) 9>/tmp/%s.lock" % (head, skip, orig, name)


def unwrap(line: str) -> str | None:
    """Inverse of wrap(): the original line (schedule restored), or None if the line is not wrapped."""
    m = WRAP_RE.search(line)
    if not m:
        return None
    parts = line.split(None, 5)
    sched_hours = parts[0]
    _, sched = _runner(m.group("orig"))
    if sched and sched_hours == sched[1]:
        sched_hours = sched[0]
    return " ".join([sched_hours] + parts[1:5]) + " " + m.group("orig")


def rewrite_text(text: str, fn) -> tuple[str, int]:
    out, n = [], 0
    for raw in text.splitlines():
        new = fn(raw)
        if new is not None:
            out.append(new)
            n += 1
        else:
            out.append(raw)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), n


def apply_deploy(root: Path = ROOT) -> dict:
    changed = {}
    for f in sorted((root / "deploy").glob("cron*")):
        if f.is_dir():
            continue
        text = f.read_text()
        new, n = rewrite_text(text, wrap)
        if n:
            f.write_text(new)
            changed[str(f.relative_to(root))] = n
    return changed


def install(read=None, write=None, backup=None) -> int:
    import archive_cron_install as aci
    read, write, backup = read or aci._crontab_read, write or aci._crontab_write, backup or aci._backup
    cur = read()
    new, n = rewrite_text(cur, wrap)
    if not n:
        print("ALREADY INSTALLED (or no T3 lines present): nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    want = [l for l in new.splitlines()]
    ok = after.splitlines() == want and len(after.splitlines()) == len(cur.splitlines())
    print("%s: %d T3 line(s) wrapped with flock + skip row; every other crontab line preserved (line count %d -> %d)" % (
        "INSTALLED" if ok else "ERROR: crontab write did not verify", n, len(cur.splitlines()), len(after.splitlines())))
    return 0 if ok else 1


def uninstall(read=None, write=None, backup=None) -> int:
    import archive_cron_install as aci
    read, write, backup = read or aci._crontab_read, write or aci._crontab_write, backup or aci._backup
    cur = read()
    new, n = rewrite_text(cur, unwrap)
    if not n:
        print("NOT INSTALLED: no wrapped T3 lines; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    ok = read().splitlines() == new.splitlines()
    print("UNINSTALLED: %d line(s) restored" % n if ok else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def readback() -> int:
    import archive_cron_install as aci
    lines = aci._crontab_read().splitlines()
    wrapped = [l for l in lines if WRAP_RE.search(l)]
    bare = [l for l in lines if is_cron_line(l) and _runner(l)[0] and not WRAP_RE.search(l)]
    print("T3 LINES WRAPPED: %d" % len(wrapped))
    for l in wrapped:
        m = WRAP_RE.search(l)
        print("  %-24s %s" % (m.group("name"), " ".join(l.split()[:5])))
    print("T3 LINES NOT WRAPPED: %d" % len(bare))
    for l in bare:
        print("  ! " + l[:150])
    sk = ROOT / "logs" / "t3_skips.jsonl"
    rows = [json.loads(x) for x in sk.read_text().splitlines() if x.strip()] if sk.exists() else []
    by: dict = {}
    for r in rows:
        by[r.get("runner")] = by.get(r.get("runner"), 0) + 1
    print("SKIP ROWS (logs/t3_skips.jsonl): %d  by runner: %s  last: %s" % (len(rows), json.dumps(by, sort_keys=True), rows[-1]["ts"] if rows else "none"))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "apply-deploy":
        print(json.dumps(apply_deploy(), indent=1))
        sys.exit(0)
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

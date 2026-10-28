#!/usr/bin/env python3
"""W92.1: install the registry-live price-archiver cron lines (NBA / NHL, W91.3) that deploy/cron.conf mirrors but the
box crontab lacks -- ONLY when the SURFACE BUDGET allows (Hard Rule 14) -- and read back what they wrote. Runs ON the
box (via scripts/box_tasks.py). Deploy never touches the crontab (W91.3 left six mirrored-but-not-installed lines).

  install    1. fresh budget probe; blocked -> REFUSED + every blocking reason, nothing changed.
             2. the lines to add = lines in deploy/cron.conf that run scripts/archive_market_prices.py AND whose
                registry entry is status=live AND that are not already in the crontab (EXACT line match -- the
                registry signature drops the schedule, so three NBA lines share one signature).
             3. the crontab is backed up to logs/crontab_backups/ FIRST; a backup that is missing or differs from the
                crontab just read aborts the install before anything is written.
             4. the missing lines are appended inside `# BEGIN/END W92.1 ARCHIVE LINES`. No other line is touched.
  uninstall  removes exactly that BEGIN..END block (backup first); every other line is kept byte-for-byte.
  readback   the installed lines, the log tail, and per-day PRICE_ARCHIVE rows for each archived series. Read-only.

Exit code is 0 in every outcome except a crontab write that did not verify.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CRON_CONF = ROOT / "deploy" / "cron.conf"
BEGIN = "# BEGIN W92.1 ARCHIVE LINES"
END = "# END W92.1 ARCHIVE LINES"
ARCHIVER = "scripts/archive_market_prices.py"
BACKUP_DIR = ROOT / "logs" / "crontab_backups"
ARCHIVE = ROOT / "exp_output" / "PRICE_ARCHIVE"
LOG = ROOT / "logs" / "price_archive_cron.log"
NOT_INSTALLED = "NOT INSTALLED "  # the SURFACE BUDGET reason prefix (runtime_registry, W92.1 part B)


def _rr():
    import runtime_registry as rr
    return rr


def wanted_lines(conf_text: str, reg: list) -> list[tuple[str, str]]:
    """[(registry key, exact cron line)] for every archiver line in cron.conf whose registry entry is live."""
    rr = _rr()
    live = {c["key"] for c in reg if c.get("kind") == "cron" and c.get("status") == "live"}
    out = []
    for raw in conf_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ARCHIVER not in line or len(line.split()) < 6:
            continue
        key, _ = rr._cron_key(line)
        if key in live:
            out.append((key, line))
    return out


def missing_lines(current: str, wanted: list[tuple[str, str]]) -> list[tuple[str, str]]:
    have = {l.strip() for l in current.splitlines()}
    return [(k, l) for k, l in wanted if l not in have]


def gate(ev: dict, own_keys: set[str]) -> tuple[list, list]:
    """(blocking, exempt) red reasons. Only the job's OWN first-run states are exempt, matched exactly: a
    `NOT INSTALLED <key>` for a key about to be installed, or `STALE <key>: no write found`. Any other red blocks, and
    a RED budget with no recorded reasons blocks too (GG-1080)."""
    if ev.get("budget") == "GREEN":
        return [], []
    reasons = list(ev.get("reasons") or [])
    if not reasons:
        return ["budget is %s but no reasons were recorded" % ev.get("budget")], []
    own = set()
    for k in own_keys:
        own.add(NOT_INSTALLED + k)
        own.add("STALE %s: no write found" % k)
    return [r for r in reasons if r not in own], [r for r in reasons if r in own]


def merged_crontab(current: str, add: list[tuple[str, str]]) -> str:
    body = current if current.endswith("\n") or not current else current + "\n"
    return body + "\n".join([BEGIN] + [l for _, l in add] + [END]) + "\n"


def without_block(current: str) -> tuple[str, bool]:
    lines = current.splitlines()
    if BEGIN not in (l.strip() for l in lines):
        return current, False
    i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
    j = next((k for k, l in enumerate(lines) if l.strip() == END and k > i), None)
    if j is None:
        raise SystemExit("crontab has the BEGIN marker without END; refusing to edit")
    kept = lines[:i] + lines[j + 1:]
    return ("\n".join(kept) + "\n") if kept else "", True


def _crontab_read() -> str:
    r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _crontab_write(text: str) -> None:
    subprocess.run(["crontab", "-"], input=text, text=True, check=True)


def _backup(current: str) -> Optional[Path]:
    """Write the crontab as it stands to logs/crontab_backups/; None if it could not be written and re-read equal."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        p = BACKUP_DIR / ("crontab_%s.bak" % dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
        p.write_text(current)
        return p if p.read_text() == current else None
    except OSError:
        return None


def _budget(live_fn: Optional[Callable[[], dict]]) -> dict:
    if live_fn is None:
        rr = _rr()
        live_fn = lambda: rr.live(refresh=True, use_cache=False)  # noqa: E731
    return live_fn()


def install(live_fn=None, read=_crontab_read, write=_crontab_write, backup=_backup,
            conf_text: Optional[str] = None, reg: Optional[list] = None) -> int:
    rr = _rr()
    reg = rr.load() if reg is None else reg
    conf_text = CRON_CONF.read_text() if conf_text is None else conf_text
    ev = _budget(live_fn)
    if ev.get("error"):
        print("REFUSED: SURFACE BUDGET could not be read (%s); nothing installed" % ev["error"])
        return 0
    cur = read()
    add = missing_lines(cur, wanted_lines(conf_text, reg))
    blocking, exempt = gate(ev, {k for k, _ in add})
    print("SURFACE BUDGET: %s (box HEAD %s, as of %s)" % (ev.get("budget"), ev.get("head"), ev.get("as_of")))
    for r in exempt:
        print("  exempt (own first-run state): %s" % r)
    if blocking:
        print("REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:")
        for r in blocking:
            print("  - %s" % r)
        return 0
    if not add:
        print("ALREADY INSTALLED: every registry-live archiver line is in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(merged_crontab(cur, add))
    after = read().splitlines()
    ok = all(l in after for l in cur.splitlines()) and all(l in after for _, l in add)
    for k, l in add:
        print("  + %s" % l[:120])
    print("INSTALLED: %d archiver line(s) appended; every prior crontab line preserved" % len(add) if ok
          else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=_crontab_read, write=_crontab_write, backup=_backup) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W92.1 block in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W92.1 block removed; every other crontab line preserved" if ok else
          "ERROR: crontab write did not verify")
    return 0 if ok else 1


def readback() -> int:
    lines = _crontab_read().splitlines()
    if BEGIN in (l.strip() for l in lines):
        i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
        j = next((k for k, l in enumerate(lines) if l.strip() == END and k > i), len(lines))
        print("CRONTAB BLOCK (%d lines):" % (j - i - 1))
        print("\n".join(l[:150] for l in lines[i:j + 1]))
    else:
        print("CRONTAB BLOCK: not installed")
    print("\nLOG TAIL (logs/price_archive_cron.log), 429s in last 500 lines: %s" % (
        sum(1 for l in LOG.read_text().splitlines()[-500:] if "429" in l) if LOG.exists() else "no log"))
    print("\n".join(LOG.read_text().splitlines()[-6:]) if LOG.exists() else "  (no log yet)")
    print("\nPRICE_ARCHIVE rows by prefix (most recent 2 day files):")
    files = sorted(ARCHIVE.glob("prices_*.jsonl"))[-2:] if ARCHIVE.exists() else []
    pat = re.compile(r'"(?:series|series_ticker)"\s*:\s*"(KX(?:NBA|NHL)[A-Z]*)"')
    for p in files:
        counts: dict = {}
        with p.open() as fh:
            for line in fh:
                m = pat.search(line)
                if m:
                    counts[m.group(1)] = counts.get(m.group(1), 0) + 1
        print("  %s  %d bytes  %s" % (p.name, p.stat().st_size, json.dumps(counts, sort_keys=True)))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

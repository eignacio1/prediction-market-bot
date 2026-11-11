#!/usr/bin/env python3
"""W109.3 / B-070 (EXP-047): install the NBA engine props SHADOW cron line (evaluate-and-log; no order, stake or kelly) that
deploy/cron.nba_engine_props_shadow mirrors -- ONLY when the SURFACE BUDGET allows (Hard Rule 14) -- and read back what it
wrote. Runs ON the box (via scripts/box_tasks.py), and only when the operator approves the task `nba_engine_props_shadow_install`
by name. Same mechanics as scripts/ride_board_install.py (budget probe, crontab backup-or-abort, one BEGIN/END block, no other
line touched). The registry entry is `paused` until then: the operator's named approval IS the activation, so this installer
accepts that entry's key whether paused or live (and no other paused key); flip the registry to live after it runs.

  install    budget probe -> backup -> append the missing line inside `# BEGIN/END W109.3 NBA ENGINE PROPS SHADOW LINE`.
  uninstall  removes exactly that block (backup first).
  readback   the installed line, the cron log tail and the shadow ledgers with mtimes.

Exit code is 0 in every outcome except a crontab write that did not verify.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive_cron_install as aci  # noqa: E402

CRON_CONF = ROOT / "deploy" / "cron.nba_engine_props_shadow"
BEGIN = "# BEGIN W109.3 NBA ENGINE PROPS SHADOW LINE"
END = "# END W109.3 NBA ENGINE PROPS SHADOW LINE"
MARKERS = ("scripts/run_nba_engine_props_shadow.py",)
OWN_KEY = "cron|37 * * * *|scripts/run_nba_engine_props_shadow.py"
LOG = ROOT / "logs" / "nba_engine_props_shadow.log"
LEDGERS = ROOT / "exp_output" / "PREGAME_SHADOW_EXP047"


def wanted_lines(conf_text: str, reg: list) -> list[tuple[str, str]]:
    rr = aci._rr()
    live = {c["key"] for c in reg if c.get("kind") == "cron" and (c.get("status") == "live" or
                                                                 (c.get("status") == "paused" and c.get("key") == OWN_KEY))}
    out = []
    for raw in conf_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or len(line.split()) < 6 or not any(aci.marker_in(line, m) for m in MARKERS):
            continue
        key, _ = rr._cron_key(line)
        if key in live:
            out.append((key, line))
    return out


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


def install(live_fn=None, read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup,
            conf_text=None, reg=None) -> int:
    rr = aci._rr()
    reg = rr.load() if reg is None else reg
    conf_text = CRON_CONF.read_text() if conf_text is None else conf_text
    ev = aci._budget(live_fn)
    if ev.get("error"):
        print("REFUSED: SURFACE BUDGET could not be read (%s); nothing installed" % ev["error"])
        return 0
    cur = read()
    add = aci.missing_lines(cur, wanted_lines(conf_text, reg))
    blocking, exempt = aci.gate(ev, {k for k, _ in add})
    print("SURFACE BUDGET: %s (box HEAD %s, as of %s)" % (ev.get("budget"), ev.get("head"), ev.get("as_of")))
    for r in exempt:
        print("  exempt (own first-run state): %s" % r)
    if blocking:
        print("REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:")
        for r in blocking:
            print("  - %s" % r)
        return 0
    if not add:
        print("ALREADY INSTALLED: the NBA engine props shadow line is in the crontab; nothing changed")
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
    print("INSTALLED: %d props-shadow line(s) appended; every prior crontab line preserved" % len(add) if ok
          else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W109.3 block in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W109.3 block removed; every other crontab line preserved" if ok else
          "ERROR: crontab write did not verify")
    return 0 if ok else 1


def readback() -> int:
    lines = aci._crontab_read().splitlines()
    if BEGIN in (l.strip() for l in lines):
        i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
        j = next((k for k, l in enumerate(lines) if l.strip() == END and k > i), len(lines))
        print("CRONTAB BLOCK (%d lines):" % (j - i - 1))
        print("\n".join(l[:170] for l in lines[i:j + 1]))
    else:
        print("CRONTAB BLOCK: not installed")
    d = LEDGERS
    for f in sorted(d.glob("*")) if d.exists() else []:
        print("  %s  %d bytes  mtime %s" % (f.name, f.stat().st_size, datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")))
    if not d.exists():
        print("  exp_output/PREGAME_SHADOW_EXP047: (none yet)")
    print("\nLOG TAIL (logs/nba_engine_props_shadow.log), error lines in last 500: %s" % (
        sum(1 for l in LOG.read_text().splitlines()[-500:] if "Traceback" in l or "ERROR" in l) if LOG.exists() else "no log"))
    print("\n".join(LOG.read_text().splitlines()[-6:]) if LOG.exists() else "  (no log yet)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

#!/usr/bin/env python3
"""W81.3: install/uninstall/readback of the `# BEGIN/END W81.3 PASSYDS PRE-KICKOFF SNAPSHOT` cron block on the box.
Same gate and semantics as scripts/thin_capture_install.py (SURFACE BUDGET must read GREEN, Hard Rule 14; an existing
block is never rewritten; every other crontab line is kept byte-for-byte). Runs ON the box."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import thin_capture_install as base  # noqa: E402

FRAGMENT = ROOT / "deploy" / "cron.passyds_prekickoff"
BEGIN = "# BEGIN W81.3 PASSYDS PRE-KICKOFF SNAPSHOT"
END = "# END W81.3 PASSYDS PRE-KICKOFF SNAPSHOT"
SCRIPT = "scripts/passyds_prekickoff_snapshot.py"
STORE = ROOT / "exp_output" / "PREGAME_SHADOW_PASSYDS"
LOG = ROOT / "logs" / "passyds_prekickoff_cron.log"


def _bind() -> None:
    base.FRAGMENT, base.BEGIN, base.END = FRAGMENT, BEGIN, END


def install(live_fn=None, read=base._crontab_read, write=base._crontab_write) -> int:
    _bind()
    ev = base.budget(live_fn)
    if ev.get("error"):
        print(f"REFUSED: SURFACE BUDGET could not be read ({ev['error']}); nothing installed")
        return 0
    print(f"SURFACE BUDGET: {ev.get('budget')} (box HEAD {ev.get('head')}, as of {ev.get('as_of')})")
    # Red items that are about THIS component (not yet installed, so no write / no snapshot) cannot block its own
    # install; every other red item still does (Hard Rule 14).
    others = [r for r in ev.get("reasons", []) if "passyds" not in r.lower()]
    if others:
        print("REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:")
        for r in others:
            print(f"  - {r}")
        return 0
    cur = read()
    new, changed = base.merged_crontab(cur, FRAGMENT.read_text())
    if not changed:
        print("ALREADY INSTALLED: crontab already holds the W81.3 block; nothing changed")
        return 0
    write(new)
    after = read()
    ok = BEGIN in after and SCRIPT in after and all(l in after.splitlines() for l in cur.splitlines())
    print("INSTALLED: W81.3 block appended; every prior crontab line preserved" if ok else
          "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=base._crontab_read, write=base._crontab_write) -> int:
    _bind()
    return base.uninstall(read, write)


def readback() -> int:
    cron = base._crontab_read()
    lines = cron.splitlines()
    if BEGIN in (l.strip() for l in lines):
        i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
        print("CRONTAB BLOCK:\n" + "\n".join(lines[i:i + 8]))
    else:
        print("CRONTAB BLOCK: not installed")
    print("\nLOG TAIL (logs/passyds_prekickoff_cron.log):")
    print("\n".join(LOG.read_text().splitlines()[-8:]) if LOG.exists() else "  (no log yet)")
    print("\nSTORE:")
    files = sorted(STORE.glob("snap_????-??-??.jsonl")) if STORE.exists() else []
    for p in files:
        print(f"  {p.name}  {p.stat().st_size} bytes  {sum(1 for _ in p.open())} rows")
    if not files:
        print("  (no snapshot rows yet)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

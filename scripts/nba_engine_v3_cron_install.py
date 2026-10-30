#!/usr/bin/env python3
"""W97.1: install the registry-live NBA engine v3 cron line (EXP-044c runner, own lock) that
deploy/cron.conf mirrors but the box crontab lacks -- ONLY when the SURFACE BUDGET allows (Hard Rule 14) -- and read back
what they wrote. Runs ON the box (via scripts/box_tasks.py). Same mechanics as scripts/nba_engine_cron_install.py (W95.1) (budget
probe, crontab backup-or-abort, one BEGIN/END block, no other line touched); only the markers and the line filter differ.

  install    budget probe -> backup -> append the missing lines inside `# BEGIN/END W97.1 NBA ENGINE V3 LINE`.
  uninstall  removes exactly that block (backup first).
  readback   the installed lines, the cron log tail, the store's last game date, and the v3 arm's status + row counts (rows per game per family, snapshot count).

Exit code is 0 in every outcome except a crontab write that did not verify.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive_cron_install as aci  # noqa: E402

CRON_CONF = ROOT / "deploy" / "cron.conf"
BEGIN = "# BEGIN W97.1 NBA ENGINE V3 LINE"
END = "# END W97.1 NBA ENGINE V3 LINE"
MARKERS = ("prediction_market_bot.nba_engine.live_v3",)
LOG = ROOT / "logs" / "nba_engine_live_cron.log"
ARMS = {"v3 (EXP-044c)": ROOT / "exp_output" / "NBA_ENGINE_LIVE_V3"}
CURRENT_STATUS = ROOT / "exp_output" / "NBA_EVENTS" / "current" / "status.json"


def wanted_lines(conf_text: str, reg: list) -> list[tuple[str, str]]:
    rr = aci._rr()
    live = {c["key"] for c in reg if c.get("kind") == "cron" and c.get("status") == "live"}
    out = []
    for raw in conf_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or len(line.split()) < 6 or not any(m in line for m in MARKERS):
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
        print("ALREADY INSTALLED: the registry-live NBA engine v3 line is in the crontab; nothing changed")
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
    print("INSTALLED: %d NBA engine v3 line(s) appended; every prior crontab line preserved" % len(add) if ok
          else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W97.1 block in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W97.1 block removed; every other crontab line preserved" if ok else
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
    print("\nSTORE (exp_output/NBA_EVENTS/current/status.json):")
    print(CURRENT_STATUS.read_text()[:600] if CURRENT_STATUS.exists() else "  (none yet)")
    for name, d in ARMS.items():
        rows = d / "rows.jsonl"
        n = sum(1 for _ in rows.open()) if rows.exists() else 0
        fams: dict = {}
        if n:
            for ln in rows.open():
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                f = r.get("family") or r.get("market_family") or "?"
                fams[f] = fams.get(f, 0) + 1
        print("\nARM %s: rows=%d families=%s" % (name, n, json.dumps(fams, sort_keys=True)))
        per_game: dict = {}
        if n:
            for ln in rows.open():
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                per_game.setdefault(r.get("event_ticker", "?"), {})[r.get("family", "?")] = per_game.get(r.get("event_ticker", "?"), {}).get(r.get("family", "?"), 0) + 1
        print("  rows per game per family: %s" % json.dumps(per_game, sort_keys=True)[:1500])
        snaps = d / "injury_snapshots.jsonl"
        print("  injury snapshots logged: %d" % (sum(1 for _ in snaps.open()) if snaps.exists() else 0))
        st = d / "status.json"
        print("  status: %s" % (st.read_text()[:400].replace("\n", " ") if st.exists() else "(none)"))
    print("\nLOG TAIL (logs/nba_engine_live_cron.log), error lines in last 500: %s" % (
        sum(1 for l in LOG.read_text().splitlines()[-500:] if "Traceback" in l or "ERROR" in l) if LOG.exists() else "no log"))
    print("\n".join(LOG.read_text().splitlines()[-6:]) if LOG.exists() else "  (no log yet)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

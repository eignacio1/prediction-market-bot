#!/usr/bin/env python3
"""W129.3 Part B: install the MLB daily-board cron line that deploy/cron.mlb_board mirrors, plus the two GG-1957 alarms.

Runs ON the box (via scripts/box_tasks.py) and only when the operator approves the task `mlb_board_install` by name. Same
mechanics as scripts/archive_dense_install.py: SURFACE BUDGET probe (Hard Rule 14), disk budget gate, crontab backup-or-abort,
one `# BEGIN/END W129.3 MLB BOARD` block, no other line touched. The registry entry is `paused` until then.

BUDGET GATE: the job makes no network call (request rate 0) and writes one small board JSON per day plus one run line per run;
the install REFUSES unless projected disk after 30 days < 80% with that growth added to the box's measured growth.

  install      budget probe -> gate -> backup -> append the block.
  uninstall    removes exactly that block (backup first).
  readback     the installed line, gate numbers, log tail, newest board.
  gate         read-only gate verdict as JSON.
  healthcheck  the two GG-1957 alarms, one `PASS|WARN|FAIL <name>: detail` line each (called by deploy/healthcheck.sh):
               ARM-DATE   FAIL if today >= opening day - 7 days (and in season) and the block is not in the crontab.
               SILENT-EXIT FAIL if a run in the last 24 h had games_scheduled > 0 and rows_written == 0.
Exit code is 0 in every outcome except a crontab write that did not verify (healthcheck: 1 on any FAIL).
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import archive_cron_install as aci  # noqa: E402
import mlb_board_daily as bd  # noqa: E402

CRON_CONF = ROOT / "deploy" / "cron.mlb_board"
BEGIN = "# BEGIN W129.3 MLB BOARD"
END = "# END W129.3 MLB BOARD"
MARKERS = ("scripts/mlb_board_daily.py",)
OWN_KEYS = {"cron|10 14,17,20,23 * 3-10 *|scripts/mlb_board_daily.py"}
LOG = ROOT / "logs" / "mlb_board.log"

ASSUMED_OPENING_DAY = date(2027, 3, 25)      # UNVERIFIED expectation (the PREREG says so); the schedule cache overrides it
ARM_LEAD_DAYS = 7
SEASON_END = date(2027, 10, 31)
RUNS_PER_DAY = 4
BYTES_PER_RUN = 400_000                      # board JSON (~15 games x ~30 columns) + run line, rounded far up; no new capture
DISK_CEILING_PCT = 80.0
HORIZON_DAYS = 30


def gate(usage: dict, existing_pct_per_day) -> tuple[bool, list[str], dict]:
    total = float(usage["total_bytes"]) or 1.0
    new_pct_day = 100.0 * BYTES_PER_RUN * RUNS_PER_DAY / total
    base = max(existing_pct_per_day or 0.0, 0.0)
    projected = usage["pct"] + (base + new_pct_day) * HORIZON_DAYS
    nums = {"disk_now_pct": usage["pct"], "existing_pct_per_day": existing_pct_per_day, "new_pct_per_day": round(new_pct_day, 4),
            "new_mb_per_day": round(BYTES_PER_RUN * RUNS_PER_DAY / 1e6, 2), "projected_pct_30d": round(projected, 1),
            "requests_per_min": 0}
    why = []
    if existing_pct_per_day is None:
        why.append("existing disk growth unknown (disk_guard has under its minimum span of samples); cannot project, refusing")
    if projected >= DISK_CEILING_PCT:
        why.append("projected disk after %d days is %.1f%% (limit %.0f%%)" % (HORIZON_DAYS, projected, DISK_CEILING_PCT))
    return not why, why, nums


def _disk_inputs():
    from prediction_market_bot import disk_guard
    a = disk_guard.assess(ROOT)
    return a["usage"], a["pct_per_day"]


def wanted_lines(conf_text: str, reg: list) -> list[tuple[str, str]]:
    rr = aci._rr()
    live = {c["key"] for c in reg if c.get("kind") == "cron" and (c.get("status") == "live" or
                                                                 (c.get("status") == "paused" and c.get("key") in OWN_KEYS))}
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
            conf_text=None, reg=None, disk_fn=None) -> int:
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
        print("ALREADY INSTALLED: the MLB board line is in the crontab; nothing changed")
        return 0
    try:
        usage, pct_day = (disk_fn or _disk_inputs)()
    except Exception as e:  # noqa: BLE001 -- an unreadable disk is a refusal, never a pass
        print("REFUSED: BUDGET GATE could not read the disk (%s: %s); nothing installed" % (type(e).__name__, e))
        return 0
    ok_gate, why, nums = gate(usage, pct_day)
    print("BUDGET GATE numbers: %s" % nums)
    if not ok_gate:
        print("REFUSED: BUDGET GATE (disk after 30 days < %.0f%%):" % DISK_CEILING_PCT)
        for r in why:
            print("  - %s" % r)
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(merged_crontab(cur, add))
    after = read().splitlines()
    ok = all(l in after for l in cur.splitlines()) and all(l in after for _, l in add)
    for _, l in add:
        print("  + %s" % l[:120])
    print("INSTALLED: %d MLB board line(s) appended; every prior crontab line preserved" % len(add) if ok
          else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W129.3 block in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W129.3 block removed; every other crontab line preserved" if ok else "ERROR: crontab write did not verify")
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
    try:
        usage, pct_day = _disk_inputs()
        _, why, nums = gate(usage, pct_day)
        print("GATE (would %s now): %s" % ("PASS" if not why else "REFUSE", nums))
    except Exception as e:  # noqa: BLE001
        print("GATE: unreadable (%s: %s)" % (type(e).__name__, e))
    boards = sorted((ROOT / "exp_output" / "MLB_BOARD").glob("board_*.json")) if (ROOT / "exp_output" / "MLB_BOARD").exists() else []
    print("NEWEST BOARD: %s" % (boards[-1].name if boards else "none yet"))
    if LOG.exists():
        tail = LOG.read_text().splitlines()[-6:]
        print("LOG tail:\n" + "\n".join(l[:200] for l in tail))
    else:
        print("LOG: no log yet")
    return 0


def gate_cmd() -> int:
    try:
        usage, pct_day = _disk_inputs()
        ok, why, nums = gate(usage, pct_day)
        print(json.dumps({"verdict": "PASS" if ok else "REFUSE", "reasons": why, "numbers": nums,
                          "approval_line": "approve mlb_board_install" if ok else "do not approve mlb_board_install yet"},
                         indent=1, sort_keys=True))
        return 0
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "UNREADABLE", "error": "%s: %s" % (type(e).__name__, e)}))
        return 1


def opening_day(root: Path, today: date) -> tuple[date, str]:
    """(first scheduled game on or after Feb 15 of the season year per the schedule cache, source). Fallback: the assumption."""
    try:
        import pandas as pd
        g = pd.read_parquet(root.joinpath(*bd.SCHEDULE))
        d = pd.to_datetime(g["start_utc"], utc=True).dt.tz_convert(bd.ET).dt.date
        nxt = [x for x in d if x >= date(today.year, 2, 15) and x >= today - timedelta(days=200)]
        if nxt:
            return min(nxt), "schedule_cache"
    except Exception:  # noqa: BLE001
        pass
    return ASSUMED_OPENING_DAY, "assumed"


def arm_date_status(today: date, installed: bool, opening: date, source: str = "assumed") -> tuple[str, str]:
    deadline = opening - timedelta(days=ARM_LEAD_DAYS)
    if installed:
        return "PASS", "block installed (opening day %s, %s)" % (opening, source)
    if today > SEASON_END or today < deadline - timedelta(days=60):
        return "PASS", "not due (arm by %s; opening day %s, %s)" % (deadline, opening, source)
    if today >= deadline:
        return "FAIL", "NOT ARMED: opening day %s (%s), arm-by %s, today %s; approve mlb_board_install" % (opening, source, deadline, today)
    return "WARN", "not armed yet; arm-by %s (%d days)" % (deadline, (deadline - today).days)


def healthcheck(now: datetime | None = None, read=aci._crontab_read, root: Path = ROOT) -> int:
    now = now or datetime.now(timezone.utc)
    today = now.date()
    try:
        installed = BEGIN in (l.strip() for l in read().splitlines())
    except Exception as e:  # noqa: BLE001
        print("WARN mlb_board_arm_date: crontab unreadable (%s)" % type(e).__name__)
        installed = None
    rc = 0
    if installed is not None:
        opening, src = opening_day(root, today)
        st, det = arm_date_status(today, installed, opening, src)
        print("%s mlb_board_arm_date: %s" % (st, det))
        rc |= st == "FAIL"
    lines = (root / "logs" / "mlb_board.log").read_text().splitlines() if (root / "logs" / "mlb_board.log").exists() else []
    st, det = bd.silent_exit_status(lines, now)
    if st == "WARN" and not installed:
        st, det = "PASS", "not installed; no run expected"
    print("%s mlb_board_silent_exit: %s" % (st, det))
    rc |= st == "FAIL"
    return int(rc)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fns = {"install": install, "uninstall": uninstall, "readback": readback, "gate": gate_cmd, "healthcheck": healthcheck}
    if cmd not in fns:
        print(__doc__)
        sys.exit(2)
    sys.exit(fns[cmd]())

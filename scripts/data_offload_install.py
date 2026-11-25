#!/usr/bin/env python3
"""W128.5: install the ONE data-offload cron line that deploy/cron.data_offload mirrors (MoneyPuck, NHL API, Baseball Savant
CSVs, MLB boxscores; public endpoints; no order, stake or kelly).

Runs ON the box (via scripts/box_tasks.py), and only when the operator approves the task `data_offload_install` by name.
Same mechanics as scripts/archive_dense_install.py (SURFACE BUDGET probe, crontab backup-or-abort, one BEGIN/END block, no other
line touched). The registry entry is `paused` until then: the operator's named approval IS the activation, so this installer
accepts that entry's key whether paused or live (and no other paused key).

BUDGET GATE -- the install REFUSES unless projected disk after 30 days < 80%: now + (existing growth + new bytes/day) * 30, with
new bytes/day = the scraper's per-night compressed byte cap (data_offload.NIGHT_CAP_BYTES), an upper bound that is only reached
while the multi-night backfill runs. The request rate is capped in the scraper itself (per-host pauses of 0.5-3 s, per-night
request caps). SURFACE BUDGET must be GREEN (Hard Rule 14).

  install    budget probe -> budget gate -> backup -> append the missing line inside `# BEGIN/END W128.5 DATA OFFLOAD`.
  uninstall  removes exactly that block (backup first).
  readback   the installed line, the gate numbers, the log tail and the store sizes.
  gate       READ-ONLY JSON: verdict + MB/day + the approval line.

Exit code is 0 in every outcome except a crontab write that did not verify.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import archive_cron_install as aci  # noqa: E402
import data_offload  # noqa: E402

CRON_CONF = ROOT / "deploy" / "cron.data_offload"
BEGIN = "# BEGIN W128.5 DATA OFFLOAD"
END = "# END W128.5 DATA OFFLOAD"
MARKERS = ("scripts/data_offload.py",)
OWN_KEYS = {"cron|17 9 * * *|scripts/data_offload.py --scope"}
LOG = ROOT / "logs" / "data_offload.log"
DISK_CEILING_PCT = 80.0
HORIZON_DAYS = 30


def capture_budget() -> dict:
    """New bytes/day, upper bound: every night at the per-night compressed cap (the backfill nights)."""
    return {"bytes_per_day": float(data_offload.NIGHT_CAP_BYTES)}


def gate(usage: dict, existing_pct_per_day, cap: dict | None = None) -> tuple[bool, list[str], dict]:
    """(passes, reasons, numbers). usage = disk_guard.current_usage dict; existing_pct_per_day may be None (unknown)."""
    cap = cap or capture_budget()
    total = float(usage["total_bytes"]) or 1.0
    new_pct_day = 100.0 * cap["bytes_per_day"] / total
    base = max(existing_pct_per_day or 0.0, 0.0)
    projected = usage["pct"] + (base + new_pct_day) * HORIZON_DAYS
    nums = {"disk_now_pct": usage["pct"], "existing_pct_per_day": existing_pct_per_day, "new_pct_per_day": round(new_pct_day, 3),
            "new_mb_per_day": round(cap["bytes_per_day"] / 1e6, 1), "projected_pct_30d": round(projected, 1)}
    why = []
    if existing_pct_per_day is None:
        why.append("existing disk growth unknown (disk_guard has under its minimum span of samples); cannot project, refusing")
    if projected >= DISK_CEILING_PCT:
        why.append("projected disk after %d days is %.1f%% (limit %.0f%%): now %.0f%% + (%.2f existing + %.2f new) pct/day"
                   % (HORIZON_DAYS, projected, DISK_CEILING_PCT, usage["pct"], base, new_pct_day))
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
        print("ALREADY INSTALLED: the data offload line is in the crontab; nothing changed")
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
    for k, l in add:
        print("  + %s" % l[:120])
    print("INSTALLED: %d data offload line(s) appended; every prior crontab line preserved" % len(add) if ok
          else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W128.5 block in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W128.5 block removed; every other crontab line preserved" if ok else
          "ERROR: crontab write did not verify")
    return 0 if ok else 1


def _dir_mb(p: Path) -> str:
    if not p.exists():
        return "none yet"
    files = [f for f in p.rglob("*") if f.is_file()]
    return "%d files, %.1f MB" % (len(files), sum(f.stat().st_size for f in files) / 1e6)


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
        for r in why:
            print("  - %s" % r)
    except Exception as e:  # noqa: BLE001
        print("GATE: unreadable (%s: %s)" % (type(e).__name__, e))
    for fam in sorted(data_offload.FAMILIES):
        print("DATA_OFFLOAD/%s: %s" % (fam, _dir_mb(ROOT / "exp_output" / "DATA_OFFLOAD" / fam)))
    if LOG.exists():
        tail = LOG.read_text().splitlines()[-200:]
        print("\nLOG: %d run lines, %d mention REFUSED or an error in the last 200" % (
            len(tail), sum(1 for l in tail if "REFUSED" in l or '"error": "' in l and '"error": ""' not in l)))
        print("\n".join(l[:300] for l in tail[-4:]))
    else:
        print("\nLOG: no log yet")
    return 0


def gate_report(usage: dict, existing_pct_per_day) -> dict:
    """The budget gate as one bounded JSON-able dict, READ-ONLY (no crontab read, no write)."""
    ok, why, nums = gate(usage, existing_pct_per_day)
    total = float(usage["total_bytes"]) or 1.0
    base = max(existing_pct_per_day or 0.0, 0.0)
    room_pct_day = (DISK_CEILING_PCT - usage["pct"]) / HORIZON_DAYS - base
    max_new_mb = max(room_pct_day, 0.0) * total / 100.0 / 1e6
    return {"verdict": "PASS" if ok else "REFUSE", "reasons": why, "numbers": nums, "ceiling_pct": DISK_CEILING_PCT,
            "horizon_days": HORIZON_DAYS, "max_new_mb_per_day_under_ceiling": round(max_new_mb, 1),
            "per_night_caps_mb": {f: round(c[1] / 1e6, 1) for f, c in data_offload.FAMILY_CAPS.items()},
            "approval_line": "approve data_offload_install" if ok else
            "do not approve data_offload_install as built; lower data_offload.FAMILY_CAPS to <= %.0f MB/day total or supersede the %.0f%% ceiling"
            % (max_new_mb, DISK_CEILING_PCT)}


def gate_cmd() -> int:
    import json
    try:
        usage, pct_day = _disk_inputs()
        print(json.dumps(gate_report(usage, pct_day), indent=1, sort_keys=True))
        return 0
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"verdict": "UNREADABLE", "error": "%s: %s" % (type(e).__name__, e)}))
        return 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback", "gate"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback, "gate": gate_cmd}[cmd]())

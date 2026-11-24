#!/usr/bin/env python3
"""W124.4: install the three dense-capture cron lines that deploy/cron.archive_dense mirrors (props from first listing,
5-min game snapshots near start, public trade prints; public read-only endpoints; no order, stake or kelly).

Runs ON the box (via scripts/box_tasks.py), and only when the operator approves the task `archive_dense_install` by name.
Same mechanics as scripts/disk_retention_install.py (SURFACE BUDGET probe, crontab backup-or-abort, one BEGIN/END block, no
other line touched). The registry entries are `paused` until then: the operator's named approval IS the activation, so
this installer accepts those entries' keys whether paused or live (and no other paused key).

BUDGET GATE (Part C) -- the install REFUSES unless BOTH hold:
  1. projected disk after 30 days < 80%: now + (existing growth + new capture bytes/day) * 30.
     Existing growth is the box's own measured growth (disk_guard); new capture is the dry-run size x runs/day, at the
     peak-hour per-run size for every run of the day (an upper bound, not an average).
  2. request rate < half the documented public limit. Kalshi's Basic read tier is 200 tokens/s at 10 tokens a default
     request = 20 req/s (derived from docs.kalshi.com, not a Kalshi-stated req/s; GET /account/limits is the authority).
     Half = 10 req/s = 600 req/min. Checked on the worst case: all three modes bursting at once.

  install    budget probe -> budget gate -> backup -> append the missing lines inside `# BEGIN/END W124.4 DENSE CAPTURE`.
  uninstall  removes exactly that block (backup first).
  readback   the installed lines, the gate numbers, the log tail and the dense store sizes.

Exit code is 0 in every outcome except a crontab write that did not verify.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import archive_cron_install as aci  # noqa: E402
from archive_dense_capture import RUNS_PER_DAY  # noqa: E402

CRON_CONF = ROOT / "deploy" / "cron.archive_dense"
BEGIN = "# BEGIN W124.4 DENSE CAPTURE"
END = "# END W124.4 DENSE CAPTURE"
MARKERS = ("scripts/archive_dense_capture.py",)
OWN_KEYS = {
    "cron|2,22,42 6-16 * * *|scripts/archive_dense_capture.py --mode props",
    "cron|3-58/5 * * * *|scripts/archive_dense_capture.py --mode games",
    "cron|1-56/5 * * * *|scripts/archive_dense_capture.py --mode prints",
}
LOG = ROOT / "logs" / "archive_dense.log"

# Dry-run measurement, 2026-11-24 00:25Z, live public API, written by `archive_dense_capture.py --dry-run` (evening ET,
# NBA + NHL slates on, so a peak-hour run). Re-measure with the dry run when the slate mix changes.
MEASURED = {  # mode: (gz bytes per run, requests per run, seconds per run)
    "props": (118_859, 38, 14.6),
    "games": (34_167, 20, 6.5),
    "prints": (505_150, 104, 42.6),
}
DOC_LIMIT_RPS = 20.0            # derived: 200 tokens/s / 10 tokens per default request (see module docstring)
RATE_FRACTION = 0.5
DISK_CEILING_PCT = 80.0
HORIZON_DAYS = 30


def capture_budget(measured: dict = MEASURED, runs: dict = RUNS_PER_DAY) -> dict:
    """New-capture bytes/day (upper bound: every run at its peak-hour size) and request rates."""
    bytes_day = {m: measured[m][0] * runs[m] for m in measured}
    req_day = {m: measured[m][1] * runs[m] for m in measured}
    burst_rps = sum(measured[m][1] / measured[m][2] for m in measured)       # all three running at once
    return {"bytes_per_day": sum(bytes_day.values()), "bytes_per_day_by_mode": bytes_day,
            "requests_per_min_avg": sum(req_day.values()) / 1440.0, "requests_per_min_burst": burst_rps * 60.0,
            "burst_rps": burst_rps}


def gate(usage: dict, existing_pct_per_day, cap: dict | None = None,
         doc_limit_rps: float = DOC_LIMIT_RPS) -> tuple[bool, list[str], dict]:
    """(passes, reasons, numbers). usage = disk_guard.current_usage dict; existing_pct_per_day may be None (unknown)."""
    cap = cap or capture_budget()
    total = float(usage["total_bytes"]) or 1.0
    new_pct_day = 100.0 * cap["bytes_per_day"] / total
    base = max(existing_pct_per_day or 0.0, 0.0)
    projected = usage["pct"] + (base + new_pct_day) * HORIZON_DAYS
    limit_rps = doc_limit_rps * RATE_FRACTION
    nums = {"disk_now_pct": usage["pct"], "existing_pct_per_day": existing_pct_per_day, "new_pct_per_day": round(new_pct_day, 3),
            "new_mb_per_day": round(cap["bytes_per_day"] / 1e6, 1), "projected_pct_30d": round(projected, 1),
            "burst_rps": round(cap["burst_rps"], 2), "avg_req_per_min": round(cap["requests_per_min_avg"], 1),
            "burst_req_per_min": round(cap["requests_per_min_burst"], 1), "half_limit_req_per_min": limit_rps * 60}
    why = []
    if existing_pct_per_day is None:
        why.append("existing disk growth unknown (disk_guard has under its minimum span of samples); cannot project, refusing")
    if projected >= DISK_CEILING_PCT:
        why.append("projected disk after %d days is %.1f%% (limit %.0f%%): now %.0f%% + (%.2f existing + %.2f new) pct/day"
                   % (HORIZON_DAYS, projected, DISK_CEILING_PCT, usage["pct"], base, new_pct_day))
    if cap["burst_rps"] >= limit_rps:
        why.append("burst request rate %.1f req/s is not under half the documented limit (%.1f req/s)" % (cap["burst_rps"], limit_rps))
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
        print("ALREADY INSTALLED: the dense capture lines are in the crontab; nothing changed")
        return 0
    try:
        usage, pct_day = (disk_fn or _disk_inputs)()
    except Exception as e:  # noqa: BLE001 -- an unreadable disk is a refusal, never a pass
        print("REFUSED: BUDGET GATE could not read the disk (%s: %s); nothing installed" % (type(e).__name__, e))
        return 0
    ok_gate, why, nums = gate(usage, pct_day)
    print("BUDGET GATE numbers: %s" % nums)
    if not ok_gate:
        print("REFUSED: BUDGET GATE (disk after 30 days < %.0f%%, request rate < half the documented limit):" % DISK_CEILING_PCT)
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
    print("INSTALLED: %d dense capture line(s) appended; every prior crontab line preserved" % len(add) if ok
          else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def uninstall(read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W124.4 block in the crontab; nothing changed")
        return 0
    b = backup(cur)
    if not b:
        print("ABORTED: crontab backup missing or unreadable; nothing written")
        return 0
    print("BACKUP: %s" % b)
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W124.4 block removed; every other crontab line preserved" if ok else
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
    print("PRICE_ARCHIVE_DENSE: %s" % _dir_mb(ROOT / "exp_output" / "PRICE_ARCHIVE_DENSE"))
    print("TRADE_PRINTS: %s" % _dir_mb(ROOT / "exp_output" / "TRADE_PRINTS"))
    if LOG.exists():
        tail = LOG.read_text().splitlines()[-500:]
        print("\nLOG: %d run lines, %d with error in last 500" % (len(tail), sum(1 for l in tail if '"error"' in l)))
        print("\n".join(l[:200] for l in tail[-6:]))
    else:
        print("\nLOG: no log yet")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

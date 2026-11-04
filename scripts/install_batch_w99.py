#!/usr/bin/env python3
"""W99.3 / B-036: ONE batch install for the held cron lines, with ONE gate rule (Hard Rule 14 unchanged in meaning).

Why: each held install used to exempt only its OWN first-run reds, so the NBA engine v3 line, the picks builder and the
NBA events refresh each saw the others' `NOT INSTALLED` reds (and v3 saw its own `SILENT ARM`) as blocking -- a deadlock.
The T3 lock/stagger install had no gate at all.

  install    1. T3 lock + stagger runs FIRST and ungated: it wraps existing lines (adds no live component) and is the
                fix for the OOM kills behind the red. Backup + readback verify, as before.
             2. ONE fresh budget probe. The batch gate then runs over steps 2-4 (below).
             3. Steps run in order: t3_lock -> nba_events_refresh -> nba_engine_v3 -> picks_builder. Each has its own
                crontab backup and readback verify (the step modules' own code). The first step that does not verify
                stops the batch and is named; later steps are not attempted.
  readback   every step's readback, read-only.
  uninstall  each step's uninstall in reverse order.

THE RULE (gate_batch). A red is exempt iff it is one of:
  - `NOT INSTALLED <key>` / `STALE <key>: no write found` for a registry key that a step in THIS batch is about to install
    (a step with no missing lines contributes nothing);
  - `SILENT ARM <name>: ...` where <name> is in that step's explicit ARMS map AND that step is about to install a line.
Everything else blocks: any healthcheck fault, any other arm's silence, any other NOT INSTALLED, a RED budget with no
reasons. The arm map is names, not string matching on a keyword.

Exit code is 0 in every outcome except a step whose crontab write did not verify.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive_cron_install as aci  # noqa: E402
import nba_engine_cron_install as nec  # noqa: E402
import nba_engine_v3_cron_install as nv3  # noqa: E402
import picks_sheet_cron_install as psi  # noqa: E402
import t3_lock_stagger as t3  # noqa: E402

# step -> (module, explicit silent-arm display names the step feeds). The names are the ArmSpec.name strings in
# pregame_shadow/silent_arms.py; tests pin them to SPECS so a rename cannot silently break the exemption.
STEPS = [
    ("t3_lock", t3, ()),
    ("nba_events_refresh", nec, ("NBA engine v1 (EXP-044)", "NBA engine v2 (EXP-044b)")),
    ("nba_engine_v3", nv3, ("NBA engine v3 (EXP-044c)",)),
    ("picks_builder", psi, ()),
]
GATED = [s for s in STEPS if s[0] != "t3_lock"]
FAIL_PREFIXES = ("ERROR", "ABORTED", "REFUSED")


def _conf(mod, override):
    """The deploy conf a step reads: its OWN module's CRON_CONF (deploy/cron.conf for the NBA engine lines,
    deploy/cron.picks_sheet for the picks builder), unless a test passes one text for every step. Reading one shared
    conf for all steps made the picks step see no wanted line on the box (11-04 03:16Z: "would add 0 line(s)")."""
    return override if override is not None else mod.CRON_CONF.read_text()


def pending(cur: str, conf_text, reg: list) -> dict:
    """{step: [registry keys it would install]} for the gated steps, from the crontab as it stands."""
    out = {}
    for name, mod, _ in GATED:
        out[name] = [k for k, _l in aci.missing_lines(cur, mod.wanted_lines(_conf(mod, conf_text), reg))]
    return out


def gate_batch(ev: dict, todo: dict) -> tuple[list, list]:
    """(blocking, exempt) over the whole batch. `todo` is pending()'s output."""
    if ev.get("budget") == "GREEN":
        return [], []
    reasons = list(ev.get("reasons") or [])
    if not reasons:
        return ["budget is %s but no reasons were recorded" % ev.get("budget")], []
    own = set()
    for keys in todo.values():
        for k in keys:
            own.add(aci.NOT_INSTALLED + k)
            own.add("STALE %s: no write found" % k)
    arm_prefix = set()
    for name, _mod, arms in GATED:
        if todo.get(name):
            arm_prefix.update("SILENT ARM %s: " % a for a in arms)
    def exempt(r: str) -> bool:
        return r in own or any(r.startswith(p) for p in arm_prefix)
    return [r for r in reasons if not exempt(r)], [r for r in reasons if exempt(r)]


def _run_step(name, mod, fn, **kw) -> tuple[bool, str]:
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = fn(**kw)
    except BaseException as e:  # noqa: BLE001  (SystemExit from a step's own refusal included)
        return False, buf.getvalue() + "EXCEPTION in %s: %r\n" % (name, e)
    out = buf.getvalue()
    bad = rc not in (0, None) or any(l.strip().startswith(FAIL_PREFIXES) for l in out.splitlines())
    return (not bad), out


def install(live_fn=None, read=aci._crontab_read, write=aci._crontab_write, backup=aci._backup,
            conf_text=None, reg=None) -> int:
    rr = aci._rr()
    reg = rr.load() if reg is None else reg
    done = []

    def stop(step, out):
        print(out, end="")
        print("BATCH STOPPED at step '%s'. Completed before it: %s. Not attempted: %s." % (
            step, ", ".join(done) or "none",
            ", ".join(n for n, _, _ in STEPS if n != step and n not in done) or "none"))
        return 1

    # step 1: T3 lock + stagger, ungated (adds no component)
    ok, out = _run_step("t3_lock", t3, t3.install, read=read, write=write, backup=backup)
    print("== step t3_lock ==")
    if not ok:
        return stop("t3_lock", out)
    print(out, end="")
    done.append("t3_lock")

    # step 2: one probe, one gate over the remaining steps
    ev = aci._budget(live_fn)
    if ev.get("error"):
        print("REFUSED: SURFACE BUDGET could not be read (%s); steps after t3_lock not run" % ev["error"])
        return 0
    todo = pending(read(), conf_text, reg)
    blocking, exempt = gate_batch(ev, todo)
    print("SURFACE BUDGET: %s (box HEAD %s, as of %s)" % (ev.get("budget"), ev.get("head"), ev.get("as_of")))
    for name, keys in todo.items():
        print("  batch step %-20s would add %d line(s)" % (name, len(keys)))
    for r in exempt:
        print("  exempt (belongs to this batch): %s" % r)
    if blocking:
        print("REFUSED: Hard Rule 14 -- a red NOT explained by this batch still blocks. Red items:")
        for r in blocking:
            print("  - %s" % r)
        print("t3_lock was applied; nba_events_refresh, nba_engine_v3, picks_builder were NOT attempted.")
        return 0

    green = {"budget": "GREEN", "head": ev.get("head"), "as_of": ev.get("as_of")}  # already gated above, once
    for name, mod, _arms in GATED:
        print("== step %s ==" % name)
        ok, out = _run_step(name, mod, mod.install, live_fn=lambda: green, read=read, write=write, backup=backup,
                            conf_text=_conf(mod, conf_text), reg=reg)
        if not ok:
            return stop(name, out)
        print(out, end="")
        done.append(name)
    print("BATCH COMPLETE: %s" % ", ".join(done))
    return 0


def uninstall() -> int:
    rc = 0
    for name, mod, _ in reversed(STEPS):
        print("== uninstall %s ==" % name)
        rc = max(rc, mod.uninstall() or 0)
    return rc


def readback() -> int:
    for name, mod, _ in STEPS:
        print("== readback %s ==" % name)
        mod.readback()
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

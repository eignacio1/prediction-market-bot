#!/usr/bin/env python3
"""W78.1: read-only summary of the standing gap agent's progress (03_DECISIONS/GG_BURNDOWN.md).

One parser, three consumers: the governance scan, /project (Process integrity panel), the Visual Dashboard builder.
Never writes. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md; this file only reads them.

summary() -> {
  ok, error, ticks, open_first (OPEN at the agent's first tick, before), open_now (after of the latest tick),
  delta, closed {A,B,C}, closed_total, triaged, last_tick (ISO), age_h, queue_status, running, stale, state_line
}
"Stale" = the queue says the agent is running AND the last tick is older than STALE_HOURS. A queue status of
relaunch/stopped/idle is reported as such and is NOT a stale warning (nothing is supposed to be ticking).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BURNDOWN = "03_DECISIONS/GG_BURNDOWN.md"
QUEUE = "04_EXECUTION/ACTIVE_QUEUE.md"
STALE_HOURS = 2.0
NOT_RUNNING = ("relaunch", "stopped", "idle", "paused", "off")


def _cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _parse_ts(s: str):
    m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z?", s or "")
    if not m:
        return None
    t = m.group(0).rstrip("Z")
    fmt = "%Y-%m-%dT%H:%M:%S" if t.count(":") == 2 else "%Y-%m-%dT%H:%M"
    return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc)


def _queue_status(root: Path) -> str:
    """Status cell of the GA row in ACTIVE_QUEUE.md ('' when the row is absent)."""
    try:
        for line in (root / QUEUE).read_text().splitlines():
            if re.match(r"\|\s*GA\s*\|", line):
                cells = _cells(line)
                return cells[3] if len(cells) > 3 else ""
    except OSError:
        pass
    return ""


def summary(root: Path = ROOT, now: datetime | None = None) -> dict:
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    out = {"ok": False, "error": None, "ticks": 0, "open_first": None, "open_now": None, "delta": None,
           "closed": {"A": 0, "B": 0, "C": 0}, "closed_total": 0, "triaged": 0, "last_tick": None, "age_h": None,
           "queue_status": "", "running": False, "stale": False, "state_line": ""}
    try:
        text = (root / BURNDOWN).read_text()
    except OSError as e:
        out["error"] = f"{BURNDOWN} unreadable ({e.__class__.__name__})"
        return out
    ticks = []
    in_totals = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_totals = line.startswith("## Per-tick totals")
            continue
        if not (in_totals and line.startswith("|")):
            continue
        c = _cells(line)
        if len(c) < 5 or not c[0].isdigit():
            continue
        arrow = re.search(r"(\d+)\s*(?:exact-OPEN\s*)?→\s*(\d+)", c[2])
        abc = re.match(r"\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", c[3])
        tri = re.match(r"\s*(\d+)", c[4])
        ticks.append({"n": int(c[0]), "ts": _parse_ts(c[1]),
                      "before": int(arrow.group(1)) if arrow else None,
                      "after": int(arrow.group(2)) if arrow else None,
                      "abc": tuple(int(x) for x in abc.groups()) if abc else (0, 0, 0),
                      "tri": int(tri.group(1)) if tri else 0})
    if not ticks:
        out["error"] = f"no per-tick rows parsed from {BURNDOWN}"
        return out
    ticks.sort(key=lambda t: t["n"])
    first, last = ticks[0], ticks[-1]
    out.update(ok=True, ticks=len(ticks), open_first=first["before"], open_now=last["after"],
               triaged=sum(t["tri"] for t in ticks))
    if first["before"] is not None and last["after"] is not None:
        out["delta"] = last["after"] - first["before"]
    for t in ticks:
        for k, v in zip("ABC", t["abc"]):
            out["closed"][k] += v
    out["closed_total"] = sum(out["closed"].values())
    if last["ts"]:
        out["last_tick"] = last["ts"].strftime("%Y-%m-%dT%H:%MZ")
        out["age_h"] = round((now - last["ts"]).total_seconds() / 3600, 1)
    qs = _queue_status(root)
    out["queue_status"] = qs
    out["running"] = bool(qs) and not any(w in qs.lower() for w in NOT_RUNNING) and "⬜" not in qs
    out["stale"] = bool(out["running"] and out["age_h"] is not None and out["age_h"] > STALE_HOURS)
    if out["stale"]:
        out["state_line"] = f"STALE: queue says running, last tick {out['age_h']}h ago (> {STALE_HOURS:g}h)"
    elif out["running"]:
        out["state_line"] = f"running, last tick {out['age_h']}h ago"
    else:
        age = "" if out["age_h"] is None else f", last tick {out['age_h']}h ago"
        out["state_line"] = f"not ticking (queue: {qs or 'no GA row'}){age}"
    return out


def render_text(s: dict) -> str:
    if not s["ok"]:
        return f"GAP AGENT: no data ({s['error']})"
    d = s["delta"]
    dtxt = "n/a" if d is None else f"{d:+d}"
    return (f"GAP AGENT: OPEN now {s['open_now']} (first tick {s['open_first']}, {dtxt}) · closed A/B/C "
            f"{s['closed']['A']}/{s['closed']['B']}/{s['closed']['C']} · triaged {s['triaged']} · {s['ticks']} ticks · "
            f"last {s['last_tick']} · {s['state_line']}")


if __name__ == "__main__":
    print(render_text(summary(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT)))

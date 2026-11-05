#!/usr/bin/env python3
"""Age of 04_EXECUTION/PROOF_CALENDAR.md for the /visual panel (W102.4 Part C).

Read-only. Parses the generated-at time from the file's header line ("from the box read of <UTC>Z") and reports its
age in days. red is True when the age exceeds one day. Any defect (missing file, no timestamp, unparseable time)
returns ok=False with the reason so the panel shows an error rather than a blank or a green tile.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
RED_AFTER_DAYS = 1.0
_STAMP = re.compile(r"box read of (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")


def load(root: pathlib.Path = ROOT, now: dt.datetime | None = None) -> dict:
    path = root / "04_EXECUTION" / "PROOF_CALENDAR.md"
    try:
        text = path.read_text()
    except OSError as e:
        return {"ok": False, "error": f"PROOF_CALENDAR.md: {type(e).__name__}"}
    m = _STAMP.search("\n".join(text.splitlines()[:8]))
    if not m:
        return {"ok": False, "error": "PROOF_CALENDAR.md: no generated-at time in the header"}
    try:
        gen = dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return {"ok": False, "error": "PROOF_CALENDAR.md: generated-at time unparseable"}
    now = now or dt.datetime.now(dt.timezone.utc)
    age = (now - gen).total_seconds() / 86400.0
    return {"ok": True, "generated_at": m.group(1), "age_days": round(age, 2), "red": age > RED_AFTER_DAYS}

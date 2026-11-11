#!/usr/bin/env python3
"""W109.6: re-arm the ADR-0072 demo-fill forward test after a turn-off (GG-587 override file).

``check``  (default, read-only): print the override file and whether the epoch-gated report still trips.
``apply``: refuse unless the report (run --no-act, so it writes nothing) trips nothing; then move
deploy/demo_fill.override.env to logs/demo_fill.override.env.<UTC>.removed (kept as the record) so the next policy
read sees the tracked demo_fill.env again. Demo orders only; no stake / kelly / cron change. Idempotent.
Allowlisted bridge task ``demo_fill_rearm`` (operator approves by name).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tripped_now(root: Path, python: str = sys.executable) -> list:
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "r.json"
        subprocess.run([python, str(root / "scripts" / "demo_fill_forward_report.py"), "--out", str(out), "--no-act"],
                       cwd=root, check=True, capture_output=True, text=True,
                       env={**__import__("os").environ, "PYTHONPATH": f"{root}/src:{root}"})
        return list(json.loads(out.read_text()).get("tripped") or [])


def run(mode: str, root: Path = ROOT, trips=None) -> int:
    ov = root / "deploy" / "demo_fill.override.env"
    if not ov.exists():
        print("REARM: no override file; nothing to do")
        return 0
    print("override file:\n" + ov.read_text())
    trips = tripped_now(root) if trips is None else trips
    print(f"epoch-gated report trips now: {trips or 'none'}")
    if mode != "apply":
        print("CHECK ONLY: nothing changed")
        return 0
    if trips:
        print("REFUSED: a turn-off still trips on epoch-gated data; not re-arming")
        return 2
    dest = root / "logs" / f"demo_fill.override.env.{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.removed"
    dest.parent.mkdir(exist_ok=True)
    ov.rename(dest)
    print(f"REARMED: override moved to {dest.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "check"))

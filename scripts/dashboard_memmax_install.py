#!/usr/bin/env python3
"""W109.5: raise pmbot-web-dashboard's MemoryMax (128M -> 384M) via a systemd drop-in. Runs ON the box via scripts/box_tasks.py.

Why: box read 2026-11-11T01:15Z -- cgroup memory.max=128M, memory.events max=5082 (limit hit repeatedly), memory.peak=128M, oom_kill 0;
scripts/dashboard_build_peak.py measured the /api/data build at peak_rss 260684 kB (baseline 112192 kB), above the cap. Touches only
the dashboard unit (never t4-mlb). Drop-in, so the repo unit file and rollback stay trivial: `install` writes the drop-in, daemon-reload,
restarts the dashboard, prints MemoryMax; `uninstall` removes the drop-in. Idempotent.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

UNIT = "pmbot-web-dashboard.service"
DROPIN_DIR = Path("/etc/systemd/system") / f"{UNIT}.d"
DROPIN = DROPIN_DIR / "w109-5-memory.conf"
MEMORY_MAX = "384M"
CONTENT = f"# W109.5: /api/data build peaks ~260 MB RSS; 128M cap was hit 5082 times\n[Service]\nMemoryMax={MEMORY_MAX}\n"


def _sh(*a: str) -> str:
    r = subprocess.run(a, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "install"
    if cmd == "install":
        DROPIN_DIR.mkdir(parents=True, exist_ok=True)
        if not DROPIN.exists() or DROPIN.read_text() != CONTENT:
            DROPIN.write_text(CONTENT)
        print(_sh("systemctl", "daemon-reload"))
        print(_sh("systemctl", "restart", UNIT))
    elif cmd == "uninstall":
        DROPIN.unlink(missing_ok=True)
        print(_sh("systemctl", "daemon-reload"))
        print(_sh("systemctl", "restart", UNIT))
    else:
        print(f"unknown command {cmd!r}; use install|uninstall", file=sys.stderr)
        return 2
    print(_sh("systemctl", "show", UNIT, "-p", "ActiveState,MemoryMax,NRestarts"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

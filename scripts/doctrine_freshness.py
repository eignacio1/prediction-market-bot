#!/usr/bin/env python3
"""Doctrine freshness (CLAUDE.md Hard Rule 16; ADR-0077). Alarm-only: always exits 0.

Reads the "Doctrine stack" table in 02_ARCHITECTURE_DESIGN/DOCTRINE.md, finds each file's first "**Last reviewed:** YYYY-MM-DD" line and
prints RED for any file missing, without the line, or older than --max-days (default 14). Operator 2026-11-10 21:45 PT: "This CANNOT keep
fucking happening ... some shit you/another window reads thats 20 waves stale".
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = ROOT / "02_ARCHITECTURE_DESIGN" / "DOCTRINE.md"
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")
REVIEWED = re.compile(r"\*\*Last reviewed:\*\*\s*(\d{4}-\d{2}-\d{2})")


def stack_files(text: str) -> list[str]:
    out, on = [], False
    for line in text.splitlines():
        if line.startswith("## Doctrine stack"):
            on = True
            continue
        if on and line.startswith("## "):
            break
        m = ROW.match(line) if on else None
        if m:
            out.append(m.group(1))
    return out


def check(root: Path, today: date, max_days: int) -> list[tuple[str, str, str]]:
    rows = []
    doctrine = root / "02_ARCHITECTURE_DESIGN" / "DOCTRINE.md"
    if not doctrine.exists():
        return [("RED", "02_ARCHITECTURE_DESIGN/DOCTRINE.md", "missing")]
    for rel in stack_files(doctrine.read_text()):
        f = root / rel
        if not f.exists():
            rows.append(("RED", rel, "missing"))
            continue
        m = REVIEWED.search(f.read_text(errors="replace"))
        if not m:
            rows.append(("RED", rel, "no 'Last reviewed' line"))
            continue
        age = (today - date.fromisoformat(m.group(1))).days
        rows.append(("RED" if age > max_days else "ok", rel, f"last reviewed {m.group(1)} ({age} d)"))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=14)
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    rows = check(Path(a.root), date.today(), a.max_days)
    red = [r for r in rows if r[0] == "RED"]
    print(f"DOCTRINE FRESHNESS: {len(rows) - len(red)} ok, {len(red)} RED (max {a.max_days} d; DOCTRINE.md wins over any stale file)")
    for status, rel, why in rows:
        if status == "RED":
            print(f"  RED  {rel}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

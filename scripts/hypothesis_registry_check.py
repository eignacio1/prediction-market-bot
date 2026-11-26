#!/usr/bin/env python3
"""Alarm-only: flag any PREREG file without a row in HYPOTHESIS_DOCTRINE.md (B-110).

A pre-registration is "registered" when the doctrine text names its file path, its file name,
its experiment directory (12_EXPLORATORY/<dir>), or its EXP / HYP / T id. Exit code is always 0
unless --strict is given. Run in Docs Guard.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOTS = ("05_RESEARCH_EXPERIMENTS", "12_EXPLORATORY")
DOCTRINE = "02_ARCHITECTURE_DESIGN/HYPOTHESIS_DOCTRINE.md"
_ID = re.compile(r"\b(EXP|HYP|T)[-_ ]?0*(\d{1,3}[A-Z]?)(?![0-9])", re.I)


def prereg_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    for root in ROOTS:
        base = repo / root
        if base.is_dir():
            out += [p for p in base.rglob("*") if p.is_file() and p.suffix == ".md" and "PREREG" in p.name.upper()]
    return sorted(out)


def ids_in(text: str) -> set[str]:
    return {f"{m.group(1).upper()}{m.group(2).upper()}" for m in _ID.finditer(text)}


def is_registered(rel: str, doctrine: str, doctrine_ids: set[str]) -> bool:
    p = Path(rel)
    if rel in doctrine or p.name in doctrine:
        return True
    lead = re.split(r"[_ ]", p.stem)[0]
    if len(lead) >= 6 and "-" in lead and lead in doctrine:  # e.g. EXP-W117.1
        return True
    if p.parts[0] == "12_EXPLORATORY" and len(p.parts) > 2 and f"{p.parts[0]}/{p.parts[1]}" in doctrine:
        return True
    return bool(ids_in(p.name) & doctrine_ids) and bool(ids_in(p.name))


def unregistered(repo: Path) -> list[str]:
    doc = (repo / DOCTRINE).read_text()
    dids = ids_in(doc)
    return [str(p.relative_to(repo)) for p in prereg_files(repo)
            if not is_registered(str(p.relative_to(repo)), doc, dids)]


def main(argv: list[str]) -> int:
    repo = Path(__file__).resolve().parent.parent
    miss = unregistered(repo)
    total = len(prereg_files(repo))
    print(f"hypothesis_registry_check: {total} PREREG files, {len(miss)} without a registry row")
    for m in miss:
        print(f"  UNREGISTERED {m}")
    return 1 if (miss and "--strict" in argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Generate 03_DECISIONS/GOVERNANCE_GAP_ARM_INDEX.md -- the "Gaps by Arm" index, from live entries.

W60.3 Part B. The hand-maintained index at the top of GOVERNANCE_GAP_LOG.md (T-374) froze at
126 gaps in 2026-07 while the log grew; this regenerates it from the live log so it cannot rot.

Arm assignment: the T-374 manual classification is kept as the authority for every id it covers
(read from the arm index in git history at ARM_SEED_REF); ids it never covered are assigned by
title keyword and marked "auto" -- an auto arm is a hint, not a review.
Usage: python3 scripts/generate_gap_arm_index.py [--check]   (--check exits 1 if the file is stale)
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "03_DECISIONS/GOVERNANCE_GAP_LOG.md"
ARCHIVE = ROOT / "03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md"
OUT = ROOT / "03_DECISIONS/GOVERNANCE_GAP_ARM_INDEX.md"
SEED_FILE = ROOT / "03_DECISIONS/GOVERNANCE_GAP_ARM_SEED.txt"  # "GG-NNN ARM" lines (T-374 manual pass)
HDR = re.compile(r"^### (GG-\d+)(?: — (.*))?$", re.M)
STAT = re.compile(r"^\*\*Status:\*\* (.+?) · \*\*Severity:\*\* ([A-Za-z]+)", re.M)


def auto_arm(title: str) -> str:
    t = title.lower()
    if re.search(r"\bnhl\b", t) and not re.search(r"\bmlb\b", t):
        return "NHL"
    if re.search(r"\bnba\b", t) and not re.search(r"\bmlb\b", t):
        return "NBA"
    if re.search(r"\bmlb\b|t4m|kxmlb|batter|pitcher|\bt1 mlb", t):
        return "MLB"
    return "Core"


def live_gaps(text: str):
    heads = list(HDR.finditer(text))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        s = STAT.search(text[m.end():end])
        if s:
            yield m.group(1), (m.group(2) or '(untitled)').strip(), s.group(1).split(" — ")[0].split(" (")[0].strip(), s.group(2)


def render() -> str:
    seed = {}
    if SEED_FILE.exists():
        for ln in SEED_FILE.read_text().splitlines():
            p = ln.split()
            if len(p) == 2:
                seed[p[0]] = p[1]
    arms: dict[str, list] = {}
    n_auto = 0
    for gid, title, status, sev in live_gaps(LOG.read_text()):
        arm = seed.get(gid)
        mark = ""
        if arm is None:
            arm, mark, n_auto = auto_arm(title), " _(auto)_", n_auto + 1
        arms.setdefault(arm, []).append((gid, title, status, sev, mark))
    total = sum(len(v) for v in arms.values())
    out = ["# Gaps by Arm — GENERATED (do not hand-edit)", "",
           "Source: `GOVERNANCE_GAP_LOG.md` live entries only (resolved-class gaps live in the archive). "
           "Regenerate: `python3 scripts/generate_gap_arm_index.py`. Arm = T-374 manual classification "
           f"where one exists, else title-keyword **(auto)** — {n_auto} of {total} are auto and unreviewed.", "",
           "**Counts:** " + ", ".join(f"{a}={len(v)} ({sum(1 for x in v if x[2]=='OPEN')} OPEN)"
                                      for a, v in sorted(arms.items())) + f" — {total} live gaps.", ""]
    for a, v in sorted(arms.items()):
        out += [f"## {a} ({len(v)})", ""]
        out += [f"- {g} — {s} · {sv}{m}: {t[:110]}" for g, t, s, sv, m in v]
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    new = render()
    if "--check" in sys.argv:
        sys.exit(0 if OUT.exists() and OUT.read_text() == new else 1)
    OUT.write_text(new)
    print(f"wrote {OUT.relative_to(ROOT)}")

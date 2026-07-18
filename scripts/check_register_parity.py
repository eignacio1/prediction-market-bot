#!/usr/bin/env python3
"""Register-parity check (GG-126) — APR/ADR doc Status vs APPROVALS_REGISTER.md.

Failure class this exists to catch (4 recurrences: GG-108, GG-122, GG-126,
GG-126-recurrence 2026-07-17): a decision document and the approvals register
drifting out of sync — either a sign-off recorded in the doc but never written
back to the register (APR-0025/0026/0028, ADR-0047, APR-0023), or a register
row left PENDING after the doc was accepted (APR-0022, the original GG-126).

Rules:
  1. Every 00_ADMIN/APR-*.md doc must have its own register row (`| APR-NNNN |`),
     unless listed in 00_ADMIN/REGISTER_PARITY_EXEMPTIONS.txt.
  2. Every 03_DECISIONS/ADR-*.md doc with a resolved Status (ACCEPTED/ADOPTED/
     COMPLETE/selected) must be mentioned somewhere in the register (its own row
     or inside an APR row's evidence cell), unless exempt. Legacy ADRs that
     predate the register-row convention are enumerated in the exemptions file —
     new ADRs are NOT grandfathered.
  3. A doc with resolved Status must not have a register row still reading
     PENDING (uppercase — the register's status convention).
  4. A doc whose Status is DRAFT/PROPOSED/PENDING must not have a register row
     recording ACCEPTED.

Exit 0 with "CLEAN" line if parity holds; exit 1 and list findings otherwise.
Output is indented two spaces to slot into governance_scan.sh's format.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "00_ADMIN" / "APPROVALS_REGISTER.md"
EXEMPTIONS = ROOT / "00_ADMIN" / "REGISTER_PARITY_EXEMPTIONS.txt"

RESOLVED_PAT = re.compile(r"ACCEPTED|ADOPTED|COMPLETE|selected")
UNRESOLVED_PAT = re.compile(r"DRAFT|PROPOSED|PENDING|PLACEHOLDER")
# No trailing \b: filenames like APR-0025_gg105-....md put a word char (_)
# right after the digits, which a word boundary would reject.
ID_PAT = re.compile(r"\b((?:APR|ADR)-\d{4})")


def doc_status(path: Path) -> str | None:
    """First Status line in the doc header, or None if unparseable."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[:20]:
            if re.match(r"\s*\*\*Status", line):
                return line
    except OSError:
        pass
    return None


def load_exemptions() -> set[str]:
    if not EXEMPTIONS.exists():
        return set()
    ids: set[str] = set()
    for line in EXEMPTIONS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            ids.add(line)
    return ids


def main() -> int:
    if not REGISTER.exists():
        print("  Could not read APPROVALS_REGISTER.md — parity check skipped")
        return 0

    register_text = REGISTER.read_text(encoding="utf-8")
    register_rows: dict[str, list[str]] = {}
    for line in register_text.splitlines():
        m = re.match(r"\|\s*((?:APR|ADR)-\d{4})\s*\|", line)
        if m:
            register_rows.setdefault(m.group(1), []).append(line)
    mentioned_ids = set(ID_PAT.findall(register_text))
    exempt = load_exemptions()

    docs: list[tuple[str, Path]] = []
    for pattern, folder in (("APR-*.md", "00_ADMIN"), ("ADR-*.md", "03_DECISIONS")):
        for path in sorted((ROOT / folder).glob(pattern)):
            m = ID_PAT.search(path.name)
            if m:
                docs.append((m.group(1), path))

    findings: list[str] = []
    checked = 0
    for doc_id, path in docs:
        status = doc_status(path)
        if status is None:
            continue  # no parseable Status header — nothing to compare
        checked += 1
        resolved = bool(RESOLVED_PAT.search(status))
        rows = register_rows.get(doc_id, [])

        if doc_id.startswith("APR") and not rows and doc_id not in exempt:
            findings.append(
                f"{doc_id}: no APPROVALS_REGISTER.md row at all "
                f"(doc status: {status.strip()[:80]})"
            )
            continue
        if (
            doc_id.startswith("ADR")
            and resolved
            and doc_id not in mentioned_ids
            and doc_id not in exempt
        ):
            findings.append(
                f"{doc_id}: resolved in doc but never mentioned in "
                f"APPROVALS_REGISTER.md (doc status: {status.strip()[:80]})"
            )
            continue
        for row in rows:
            # Date/status is the 4th column. A correction note may legitimately
            # contain the word PENDING (e.g. APR-0022's GG-126 annotation), so a
            # row is stale only if its date cell has no resolved keyword at all.
            cells = [c.strip() for c in row.split("|")]
            date_cell = cells[4] if len(cells) > 4 else row
            if resolved and "PENDING" in date_cell and not RESOLVED_PAT.search(date_cell):
                findings.append(
                    f"{doc_id}: doc says resolved but register row still reads "
                    f"PENDING (the original GG-126 failure)"
                )
            if (
                not resolved
                and UNRESOLVED_PAT.search(status)
                and RESOLVED_PAT.search(date_cell)
            ):
                findings.append(
                    f"{doc_id}: register row records a resolved status but doc "
                    f"status is still {status.strip()[:60]}"
                )

    if findings:
        print(f"  {len(findings)} PARITY MISMATCH(ES) — register write-back missed (GG-126 class):")
        for f in findings:
            print(f"    !! {f}")
        print("    -> Fix the stale side NOW (register row or doc Status) and note it in GG-126.")
        return 1
    print(
        f"  CLEAN — {checked} APR/ADR docs checked against the register "
        f"({len(exempt)} legacy-exempt)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

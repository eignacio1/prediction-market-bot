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
  5. (T-570, 2026-09-23, retirement-mechanism) The reverse of rule 2's floor:
     an ADR with a resolved Status must have its OWN dedicated register row —
     `| ADR-NNNN |` — not merely appear as a mention inside another row's
     evidence cell. Rule 2 already requires *a* mention somewhere; rule 5
     requires that mention to be the ADR's own row. Same exemptions list as
     rule 2 (this is a stricter floor on the same legacy-ADR population, not
     a new one). Run against real data 2026-09-23: 12 ACCEPTED ADRs not on
     the exemptions list currently fail this rule (ADR-0001, 0003, 0010,
     0015, 0018, 0024, 0026, 0027, 0028, 0032, 0045, 0046) — reported as a
     real finding for governance triage, not silently backfilled into the
     exemptions file by this change (adding an exemption is an adjudication
     this script does not make for itself, and requires the stated reason +
     DECISION_LOG.md note the exemptions file itself demands).

  6. (T-584, 2026-09-29, GG-312) Both directions + no silent skips:
     a. Exemptions NO LONGER suppress rules 2/5 for a resolved ADR. The file
        hid 27 of the 36 accepted-without-row ADRs (15 of them post-dating the
        "legacy" convention it claims to grandfather). Exemptions still apply
        to rule 1 (APR rows) and to nothing else; the CLEAN line reports how
        many exemption entries are now redundant.
     b. An ADR counts as having register accountability if ANY of: its own
        `| ADR-NNNN |` row; a row whose SUBJECT cell (2nd column) leads with
        it (`| APR-0020 | ADR-0026: ... |`, `ADR-0003 formal acceptance`) --
        the subject-vs-evidence-mention distinction rule 5 always intended; or
        a dated `RATIFY-*` row that enumerates it inside its "Population"
        list (text before "Not covered" -- IDs a ratification row explicitly
        does NOT cover are never counted).
     c. A doc whose Status header cannot be parsed is now a FINDING, not a
        silent `continue` (that skip is why `## Status`-format ADR-0006/0007
        were invisible). `## Status` + next non-blank line is now parsed.
     d. Reverse direction: every `| APR-/ADR-NNNN |` register row must point
        at a real document -- either a same-id APR-*.md/ADR-*.md, or (older
        gate-passage approvals that never had a standalone doc) an Evidence
        cell that cites at least one file that exists in the repo, or another
        APR/ADR id that has a real doc. Rows still reading PENDING (approval
        not yet granted) are skipped -- a placeholder has nothing to point at.
        Every ID a RATIFY row enumerates must have a same-id doc (no evidence
        fallback).

Exit 0 with "CLEAN" line if parity holds; exit 1 and list findings otherwise.
Output is indented two spaces to slot into governance_scan.sh's format.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "00_ADMIN" / "APPROVALS_REGISTER.md"
EXEMPTIONS = ROOT / "00_ADMIN" / "REGISTER_PARITY_EXEMPTIONS.txt"

RESOLVED_PAT = re.compile(r"\b(?:ACCEPTED|ADOPTED|COMPLETE|selected)\b")
# A resolved keyword preceded by an explicit negation (e.g. "DRAFT -- NOT
# ACCEPTED", "PROPOSED ... Not yet ACCEPTED", "NEVER ACCEPTED") is not a
# resolved status -- it's an author's defensive phrasing to make
# non-acceptance unambiguous (GG-178, GG-222). Case-insensitive since "NOT",
# "Not yet", and "never" all occur in the wild.
NEGATED_PREFIX_PAT = re.compile(r"\b(?:NOT\s+(?:YET\s+)?|NEVER\s+)$", re.IGNORECASE)
UNRESOLVED_PAT = re.compile(r"DRAFT|PROPOSED|PENDING|PLACEHOLDER")
# No trailing \b: filenames like APR-0025_gg105-....md put a word char (_)
# right after the digits, which a word boundary would reject.
ID_PAT = re.compile(r"\b((?:APR|ADR)-\d{4})")


def is_resolved(text: str) -> bool:
    """True if `text` contains a resolved-status keyword not preceded by a
    "NOT "/"NOT YET " negation immediately before it."""
    for m in RESOLVED_PAT.finditer(text):
        if not NEGATED_PREFIX_PAT.search(text[: m.start()]):
            return True
    return False


def doc_status(path: Path) -> str | None:
    """Status line from the doc header, or None if unparseable.

    Two formats exist in the wild: `**Status:** ...` on one line, and a
    `## Status` heading whose value is the next non-blank line (ADR-0004/
    0006/0007), often backtick-wrapped. The latter is normalized to the
    former shape so downstream slicing/printing is uniform."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[:40]
    except OSError:
        return None
    for i, line in enumerate(lines):
        if re.match(r"\s*\*\*Status", line):
            return line
        if re.match(r"\s*#{1,6}\s*Status\s*$", line):
            for nxt in lines[i + 1 :]:
                if nxt.strip():
                    return "**Status:** " + nxt.strip().replace("`", "")
            return None
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


_SUBJECT_LEAD_PAT = re.compile(r"^\W*((?:APR|ADR)-\d{4})")


_FILE_TOKEN_PAT = re.compile(r"[A-Za-z0-9_./\-]+\.(?:md|py|csv|json|jsonl|txt|sh|ya?ml)\b")


def repo_basenames() -> set[str]:
    """Basenames of every tracked file (git ls-files; rglob fallback)."""
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        return {Path(f).name for f in out}
    except (OSError, subprocess.CalledProcessError):
        return {p.name for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}


def evidence_resolves(
    row: str, basenames: set[str], doc_ids: set[str], own_id: str
) -> bool:
    """True if the row's Evidence cell (6th column) cites >=1 existing file,
    or another APR/ADR id that has a real same-id document."""
    cells = [c.strip() for c in row.split("|")]
    if len(cells) <= 5:
        return False
    if any(Path(t).name in basenames for t in _FILE_TOKEN_PAT.findall(cells[5])):
        return True
    return any(i in doc_ids and i != own_id for i in ID_PAT.findall(cells[5]))


def row_is_pending(row: str) -> bool:
    """Date cell (4th column) reads PENDING and records no resolved keyword:
    a placeholder for a not-yet-granted approval has nothing to point at."""
    cells = [c.strip() for c in row.split("|")]
    date_cell = cells[4] if len(cells) > 4 else ""
    return "PENDING" in date_cell and not is_resolved(date_cell)


def ratified_ids(register_text: str) -> set[str]:
    """IDs a dated `RATIFY-*` register row affirms: every ID between its
    "**Population" marker and its "Not covered" marker. Anything after
    "Not covered" (or with no Population marker at all) is never counted."""
    ids: set[str] = set()
    for line in register_text.splitlines():
        if not re.match(r"\|\s*RATIFY-[^|]+\|", line):
            continue
        start = line.find("**Population")
        if start < 0:
            continue
        end = line.find("Not covered", start)
        segment = line[start : end if end > start else None]
        ids.update(ID_PAT.findall(segment))
    return ids


def subject_led_ids(register_rows_all: list[str]) -> set[str]:
    """IDs that lead the SUBJECT cell (2nd column) of some register row."""
    ids: set[str] = set()
    for line in register_rows_all:
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 2:
            m = _SUBJECT_LEAD_PAT.match(cells[2])
            if m:
                ids.add(m.group(1))
    return ids


def collect_findings() -> tuple[list[str], int]:
    """Core parity-check loop, factored out of main() (T-570, 2026-09-23) so
    other tools (generate_operator_console.py's retirement-debt Section 0) can
    reuse the same findings without re-implementing the rules or shelling out
    to this script and re-parsing its printed output. Returns (findings,
    checked_count). Caller is responsible for checking REGISTER.exists()
    first -- this returns ([], 0) if it's missing, matching main()'s prior
    early-return behavior."""
    if not REGISTER.exists():
        return [], 0

    register_text = REGISTER.read_text(encoding="utf-8")
    register_rows: dict[str, list[str]] = {}
    for line in register_text.splitlines():
        m = re.match(r"\|\s*((?:APR|ADR)-\d{4})\s*\|", line)
        if m:
            register_rows.setdefault(m.group(1), []).append(line)
    mentioned_ids = set(ID_PAT.findall(register_text))
    exempt = load_exemptions()
    table_rows = [l for l in register_text.splitlines() if l.startswith("|")]
    ratified = ratified_ids(register_text)
    accountable = set(register_rows) | subject_led_ids(table_rows) | ratified

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
            # T-584: was a silent `continue` -- the blind spot that hid
            # `## Status`-format ADRs. An unreadable header is now loud.
            findings.append(
                f"{doc_id}: no parseable Status header in {path.name} "
                f"(parity cannot be checked)"
            )
            continue
        checked += 1
        resolved = is_resolved(status)
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
        ):
            findings.append(
                f"{doc_id}: resolved in doc but never mentioned in "
                f"APPROVALS_REGISTER.md (doc status: {status.strip()[:80]})"
            )
            continue
        if (
            doc_id.startswith("ADR")
            and resolved
            and doc_id not in accountable
        ):
            findings.append(
                f"{doc_id}: resolved and mentioned in APPROVALS_REGISTER.md, but has "
                f"no OWN dedicated row (only an incidental mention, e.g. inside "
                f"another row's evidence cell) (doc status: {status.strip()[:80]})"
            )
        for row in rows:
            # Date/status is the 4th column. A correction note may legitimately
            # contain the word PENDING (e.g. APR-0022's GG-126 annotation), so a
            # row is stale only if its date cell has no resolved keyword at all.
            cells = [c.strip() for c in row.split("|")]
            date_cell = cells[4] if len(cells) > 4 else row
            if resolved and "PENDING" in date_cell and not is_resolved(date_cell):
                findings.append(
                    f"{doc_id}: doc says resolved but register row still reads "
                    f"PENDING (the original GG-126 failure)"
                )
            if (
                not resolved
                and UNRESOLVED_PAT.search(status)
                and is_resolved(date_cell)
            ):
                findings.append(
                    f"{doc_id}: register row records a resolved status but doc "
                    f"status is still {status.strip()[:60]}"
                )

    # Rule 6d: register rows / ratified IDs must point at a real document.
    doc_ids = {d for d, _ in docs}
    basenames = repo_basenames()
    for rid in sorted(ratified - doc_ids):
        findings.append(
            f"{rid}: enumerated by a RATIFY register row but no same-id "
            f"document exists (APR-*.md in 00_ADMIN/ or ADR-*.md in 03_DECISIONS/)"
        )
    for rid in sorted(set(register_rows) - doc_ids):
        live = [r for r in register_rows[rid] if not row_is_pending(r)]
        if live and not any(
            evidence_resolves(r, basenames, doc_ids, rid) for r in live
        ):
            findings.append(
                f"{rid}: register row points at no real document (no same-id "
                f"doc, and its Evidence cell cites no existing file or documented APR/ADR id)"
            )

    return findings, checked


def main() -> int:
    if not REGISTER.exists():
        print("  Could not read APPROVALS_REGISTER.md — parity check skipped")
        return 0

    findings, checked = collect_findings()
    exempt = load_exemptions()
    redundant = sum(1 for e in exempt if e.startswith("ADR-"))

    if findings:
        print(f"  {len(findings)} PARITY MISMATCH(ES) — register write-back missed (GG-126 class):")
        for f in findings:
            print(f"    !! {f}")
        print("    -> Fix the stale side NOW (register row or doc Status) and note it in GG-126.")
        return 1
    print(
        f"  CLEAN — {checked} APR/ADR docs checked against the register "
        f"({len(exempt)} exemption entries; {redundant} ADR entries no longer "
        f"suppress anything -- rules 2/5 ignore exemptions since T-584)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

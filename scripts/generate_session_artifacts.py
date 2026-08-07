#!/usr/bin/env python3
"""
generate_session_artifacts.py — single source of truth -> generated artifacts
(T-430, session-end cost fix).

WHY: session-end normally re-authors the same session narrative by hand in
six or seven separate places (TODO_NEXT.md/MEMORY_BANK.md/PLAN.md "Last
reviewed" blocks, SESSION_CLAIMS.md closure row, Operator Digest, Next
Session Primer) — each a model-authored write and a tool round-trip, each
re-paying the context tax. On a long session (exactly when context is
scarcest) this compounds instead of staying linear, and was observed to push
a single session-end past 20 minutes into a repeated compaction loop.

THE FIX (already established in this repo — Window F's OPERATOR_CONSOLE.md
is generated from structured entries and never hand-patched): the model
authors the session narrative ONCE, in SESSION_HANDOFF's `<!-- session-meta
-->` block. This script mechanically derives every other artifact from it.

Generated blocks are marked (HTML comments / a fixed pointer sentence) so
nobody hand-edits them back into drift.

USAGE:
    scripts/generate_session_artifacts.py <path-to-SESSION_HANDOFF.md> [--dry-run]

Reads the `<!-- session-meta ... -->` block from the given SESSION_HANDOFF
file and, from it alone, generates/updates:
    1. TODO_NEXT.md, MEMORY_BANK.md, PLAN.md — collapse the "Last reviewed"
       chain to one current-status line (ADR-0044), archiving the rest
       verbatim to the matching *_ARCHIVE.md file.
    2. SESSION_CLAIMS.md — append the closure row (previously 100%
       hand-authored and skipped by at least three prior sessions).
    3. 11_MEMORY_HANDOFF/OPERATOR_DIGEST_<date>.md — append a one-line entry
       (only for MICRO-tier sessions; STANDARD still writes its own prose
       digest by hand, since a real digest needs more than one line).
    4. 04_EXECUTION/.last_session_checkpoint — via the existing
       write_session_checkpoint.sh wrapper (unchanged mechanism).

Does NOT touch: DECISION_LOG.md (Hard Rule 7 — real judgment, stays
model-authored), the substantive content of TODO_NEXT/MEMORY_BANK/PLAN
(task completions, milestone/gate status — still hand-edited when they
actually changed; this script only ever touches the "Last reviewed" chain),
or Step 8's push/merge logic.

Safety (Hard Rule 10): every target file is read fresh immediately before
writing, in this same process invocation — there is no cached/stale view.
This script does not fetch or rebase; run it after `session_end_prep.sh`
(which already fetches origin/main) and before the final commit, same as
any other Step 6 write.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_chain_archive import archive_chain  # noqa: E402

REPO_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
)

META_RE = re.compile(r"<!--\s*session-meta\s*\n(.*?)-->", re.DOTALL)

NAV_TARGETS = [
    dict(
        nav=REPO_ROOT / "11_MEMORY_HANDOFF/MEMORY_BANK.md",
        archive=REPO_ROOT / "11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md",
        heading="Last Reviewed Chain Archive",
    ),
    dict(
        nav=REPO_ROOT / "04_EXECUTION/TODO_NEXT.md",
        archive=REPO_ROOT / "04_EXECUTION/TODO_NEXT_ARCHIVE.md",
        heading="Last Reviewed Chain Archive",
    ),
    dict(
        nav=REPO_ROOT / "04_EXECUTION/PLAN.md",
        archive=REPO_ROOT / "04_EXECUTION/PLAN_ARCHIVE.md",
        heading="Last Reviewed Chain Archive",
    ),
]


def parse_session_meta(handoff_path: Path) -> dict:
    text = handoff_path.read_text()
    m = META_RE.search(text)
    if not m:
        raise SystemExit(
            f"ERROR: no <!-- session-meta --> block found in {handoff_path}.\n"
            "Add one per 00_ADMIN/TEMPLATES/TEMPLATE_SESSION_HANDOFF.md before "
            "running the generator — it is the single source of truth every "
            "other artifact is derived from."
        )
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fields[key.strip()] = val.strip()
    required = {"task_id", "tier", "timestamp", "commit", "one_line_summary"}
    missing = required - fields.keys()
    if missing:
        raise SystemExit(f"ERROR: session-meta block missing required fields: {missing}")
    return fields


def build_current_line(meta: dict, handoff_relpath: str) -> str:
    return (
        f"**Last reviewed:** {meta['timestamp']} "
        f"({meta['task_id']} — {meta['one_line_summary']}) — "
        f"See `{handoff_relpath}` for full session detail."
    )


def build_pointer_line(archive_relpath: str, heading: str) -> str:
    return (
        f"**Earlier history:** entries prior to this review are archived "
        f"verbatim in `{archive_relpath}` § {heading}."
    )


def generate_claims_closure_row(meta: dict, dry_run: bool) -> str:
    claims_path = REPO_ROOT / "04_EXECUTION/SESSION_CLAIMS.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = f"| {ts} | {meta['task_id']} | CLOSED — {meta['one_line_summary']} (commit `{meta['commit']}`) |\n"
    if not dry_run:
        with claims_path.open("a") as fh:
            fh.write(row)
    return row


def generate_operator_digest_line(meta: dict, dry_run: bool) -> str | None:
    if meta.get("tier", "").upper() != "MICRO":
        return None
    date = meta["timestamp"][:10].replace("-", "")
    digest_path = REPO_ROOT / f"11_MEMORY_HANDOFF/OPERATOR_DIGEST_{date}.md"
    line = f"- {meta['task_id']} (auto): {meta['one_line_summary']}\n"
    if dry_run:
        return line
    if digest_path.exists():
        with digest_path.open("a") as fh:
            fh.write(line)
    else:
        template = REPO_ROOT / "00_ADMIN/TEMPLATES/TEMPLATE_OPERATOR_DIGEST.md"
        header = f"# Operator Digest — {meta['timestamp'][:10]}\n\n"
        if template.exists():
            digest_path.write_text(header + line)
        else:
            digest_path.write_text(header + line)
    return line


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("handoff", type=Path, help="Path to this session's SESSION_HANDOFF file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--checkpoint-slug", default=None)
    args = ap.parse_args()

    handoff_path = args.handoff.resolve()
    meta = parse_session_meta(handoff_path)
    handoff_relpath = str(handoff_path.relative_to(REPO_ROOT))

    print(f"session-meta parsed: task_id={meta['task_id']} tier={meta['tier']} "
          f"commit={meta['commit']}")

    results = []
    for target in NAV_TARGETS:
        nav_relpath = str(target["nav"].relative_to(REPO_ROOT))
        archive_relpath = str(target["archive"].relative_to(REPO_ROOT))
        current_line = build_current_line(meta, handoff_relpath)
        pointer_line = build_pointer_line(archive_relpath, target["heading"])
        if args.dry_run:
            print(f"[dry-run] would collapse chain in {nav_relpath} -> {archive_relpath}")
            continue
        outcome = archive_chain(
            target["nav"], target["archive"], target["heading"], current_line, pointer_line
        )
        if outcome:
            print(f"  collapsed {outcome['entries_archived']} entries: "
                  f"{nav_relpath} -> {archive_relpath}")
            results.append(outcome)
        else:
            print(f"  {nav_relpath}: nothing to collapse (0 or 1 chain entries)")

    row = generate_claims_closure_row(meta, args.dry_run)
    print(f"SESSION_CLAIMS.md closure row {'(dry-run) ' if args.dry_run else ''}"
          f"generated: {row.strip()}")

    digest_line = generate_operator_digest_line(meta, args.dry_run)
    if digest_line:
        print(f"Operator Digest one-liner {'(dry-run) ' if args.dry_run else ''}"
              f"generated: {digest_line.strip()}")
    elif meta.get("tier", "").upper() != "MICRO":
        print("Operator Digest: STANDARD tier — write the prose digest by hand (Step 6B).")

    if not args.dry_run:
        slug = args.checkpoint_slug or meta["task_id"].lower()
        subprocess.run(
            [str(REPO_ROOT / "scripts/write_session_checkpoint.sh"), slug],
            check=True,
            cwd=REPO_ROOT,
        )

    print("\nDone. Review the diff (git status / git diff) before committing —"
          " this script writes files but does not commit them.")


if __name__ == "__main__":
    main()

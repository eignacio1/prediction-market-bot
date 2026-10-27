# /session-start — concurrent-safe session bootstrap (GG-082 / GG-101 / Step 0)

Run this at the very start of every session, BEFORE any other work.

## What it does
1. **Guard** — reports whether you are isolated (own worktree/branch) or in the shared `main` tree, HEAD-vs-`origin/main` drift, other sessions' recent claims, and any foreign uncommitted state you could sweep into a commit.
2. **Claim** — atomically appends your row to `04_EXECUTION/SESSION_CLAIMS.md` and pushes it (rebase-retry) so your T-/GG-/ADR- range is reserved through `origin` before you touch anything.

## Steps
```bash
# 0a — if another session may be active, isolate first (recommended):
scripts/new_session_worktree.sh "<short-focus-slug>"
#      then cd into the printed worktree path.

# 0b — guard + atomic claim (run from your session's tree):
bash .claude/hooks/session_guard.sh
scripts/claim_session.sh "<TIER: MICRO|STANDARD> — <the ONE deliverable> — FOR <measure, e.g. D3 or E1, or PLUMBING> — <one-line focus>" "<T-/GG-/ADR- range or TBD>"
```
**Purpose before work (Hard Rule 12, 2026-10-09).** The claim names the distance-to-optimum measure the session is FOR
(CLAUDE.md § "What winning looks like" → "Distance to optimum"; current values in the RUNNING SITREP of `04_EXECUTION/ACTIVE_QUEUE.md`). If you cannot say which
measure your task moves, or that it is PLUMBING, stop and ask before doing anything.
**Declare the tier and the single deliverable in the claim string itself (Hard Rule 11, T-434).**
One session = one deliverable = one merge. If you find a defect outside that deliverable's
scope, register a GG-/T-NNN and STOP — do not fix it in-session. If the task as written reads
as more than one session, say so now and propose the split before doing any work.
Hand off at ~60% context (Hard Rule 8), not 80% — session-end is itself expensive and starting
it late produces a compaction loop.

## Then — Tier 1 state retrieval (ADR-0041)

Before CLAUDE.md Step 1, load current project state via the delta-first path, not a blind full read:

```bash
if [ -s 04_EXECUTION/.last_session_checkpoint ]; then
  # GG-103 (2026-07-15): file is now an append-only log (checkpoint<TAB>timestamp<TAB>slug
  # rows, merge=union in .gitattributes) — read only the LAST row's first field, not the
  # whole-file content, since concurrent sessions may each have appended their own row.
  scripts/session_delta.sh "$(tail -n 1 04_EXECUTION/.last_session_checkpoint | cut -f1)"
else
  echo "No checkpoint on file — falling back to full reads."
fi
```

- **If the checkpoint file exists and `session_delta.sh` runs clean:** read its output (Tier 1 diff since checkpoint + dense state artifact — both ledgers' bankroll, open GGs, last 3 EXP-0xx deltas, GG-004 gate progress). This replaces a full read of `MEMORY_BANK.md` / `TODO_NEXT.md` / `DECISION_LOG.md` for routine session starts.
- **If the checkpoint is missing, stale (script errors), or this is the first session after a long gap:** fall back to full reads of `11_MEMORY_HANDOFF/MEMORY_BANK.md`, `04_EXECUTION/TODO_NEXT.md`, and `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` as before — the delta path is an optimization, not a replacement of ground truth when it can't run.
- **Hard Rule 10 applies unconditionally regardless of which path you took**: before *writing* to any shared nav file, diff it against live `HEAD` or re-read it fresh — a delta computed at session-start is not a substitute for a pre-write re-read later in the session.

Proceed to CLAUDE.md Step 1–4 and the ARE-WE-COMPROMISED checks.

Reminders while working:
- Commit early and often. In the shared `main` tree, commit ONLY your own files, path-scoped (`git commit <file> …`). Never `git add -A` / `git commit -a` / unscoped `git stash` / `reset --hard` / `checkout -- <foreign>` / `clean -fd`.
- Re-read (or `git diff HEAD`) any shared nav file before writing to it (Hard Rule 10).
- macOS has no `timeout` binary (GG-352): a snippet that uses it exits 127, which reads as "check found nothing". Use `gtimeout` (`brew install coreutils`) or `python3 -c` with `subprocess.run(..., timeout=N)`.

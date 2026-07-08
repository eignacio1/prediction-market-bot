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
scripts/claim_session.sh "<one-line focus>" "<T-/GG-/ADR- range or TBD>"
```

## Then
Proceed to CLAUDE.md Step 1–4 and the ARE-WE-COMPROMISED checks.

Reminders while working:
- Commit early and often. In the shared `main` tree, commit ONLY your own files, path-scoped (`git commit <file> …`). Never `git add -A` / `git commit -a` / unscoped `git stash` / `reset --hard` / `checkout -- <foreign>` / `clean -fd`.
- Re-read (or `git diff HEAD`) any shared nav file before writing to it (Hard Rule 10).

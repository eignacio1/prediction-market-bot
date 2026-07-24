# /session-end — End-of-Session Handoff Protocol

## ⚠️ TRIGGER THIS IMMEDIATELY WHEN CONTEXT WINDOW REACHES ~80%

Do not wait until "a good stopping point." At 80% context: stop all implementation work, run this protocol in full, commit, and push. The cost of losing a session's decisions permanently exceeds the cost of any implementation delay. When in doubt, trigger early.

**Signs you are near 80%:** responses are slower, the conversation has been running for many tool calls, or the user references that the window is getting full.

---

## /checkpoint vs /session-end — Know the difference

**`/checkpoint`** — Run between task blocks (every 30 tool calls or at every block boundary). Writes a ~20-line `CHECKPOINT_YYYYMMDD_HHMM.md`. Does NOT update PLAN.md, MEMORY_BANK.md, or produce a commit message. Fast (<2 min). See `.claude/commands/checkpoint.md`.

**`/session-end`** (this file) — Run at true session end OR at 80% context. Full update of all navigation artifacts + commit message + SESSION_HANDOFF file. The heavyweight version.

**If /session-end is being run but /checkpoint was NEVER run this session:** Before running Steps 0–7 below, check whether the session included multiple task blocks. If yes, write a CHECKPOINT for each prior block as part of Step 1B (Tasks Completed). The SESSION_HANDOFF supersedes them but the checkpoints serve as the detailed record.

---

Run this at the end of every Claude Code session before closing. Updates all navigation artifacts so the next session has full context.

**CRITICAL:** Step 1A (Strategic Decisions) is mandatory and must run FIRST. Judgment calls that aren't captured here are permanently lost across context windows.

**Tiering (Fix 5, 2026-07-24):** not every session needs every step at full weight. Steps 0 and 1A below, and every worktree/claim/guard mechanic (GG-101/GG-082), are **mandatory and untiered for every session regardless of tier** — this never shrinks. Only the documentation/handoff weight of Steps 1B, 2, 3, 4, 6, 6B, and 8 varies by tier. See "Tier Routing" after Step 1A for the objective criteria and what changes.

---

## Step 0 — Precompute + Governance Scan (mandatory, untiered — run FIRST)

Run:
```bash
scripts/session_end_prep.sh
```

This single call (Fix 2, symmetric to `session_delta.sh`) gives you, against live git state: commits + diffstat since this branch forked from `origin/main`, whether any `src/` path changed (feeds the Tier Routing call below), the exact CLAUDE.md Step 1 governance grep (`decisions_logged: false` hits), whether a full-suite pytest summary was already logged to `DECISION_LOG.md` this session, and this session's own `SESSION_CLAIMS.md` row. Paste its full output — do not summarize or assert clean without it. It is read-only and does not touch or substitute for Step 0/1A or any worktree/claim/guard mechanic.

For each `decisions_logged: false` doc it returns (section 4 of its output):
- **If you modified it this session:** extract its decisions to `DECISION_LOG.md` now, then set its `**Decisions logged:**` field to `true` before committing
- **If you did not modify it:** add a T-NNN task to `TODO_NEXT.md`: "Extract decisions from [FILENAME] → DECISION_LOG.md, set decisions_logged: true"

**A session that creates or modifies a `decisions_logged: false` document without either resolving it or registering a T-NNN is incomplete and represents a governance gap.**

If section 4 is empty: write "Governance scan: clean — no decisions_logged: false documents found" and proceed.

**If `scripts/session_end_prep.sh` errors or is unavailable** (e.g. no `origin/main` reachable), fall back to running the grep above directly — do not skip the scan.

---

## Step 1A — Capture Strategic Decisions (MANDATORY — do before anything else)

Ask: "Were any judgment calls, threshold changes, sequencing pivots, or holistic review conclusions made this session?"

For each strategic decision:
1. Add a row to `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` → Notable Judgment Calls table
2. If it requires a formal approval (threshold change, governance pivot, gate revision): add to `00_ADMIN/APPROVALS_REGISTER.md`
3. Mark it as an ANTI-CONTEXT-EROSION INVARIANT in MEMORY_BANK.md if it must survive every future context window

If no strategic decisions were made, write: *"None — implementation-only session."* and continue.

**Also scan every artifact modified this session for conditional language** ("may be revised," "could be adjusted," "threshold may change," "possibly," "if needed"). Any conditional language found must be resolved — either converted to a signed decision (APR-XXXX) or explicitly marked "TBD — requires APR-XXXX by [date]." Do not let conditional language survive the session. See CHANGE_CONTROL.md Conditional Language Governance and LL-008.

## Tier Routing (Fix 5 — objective, computed after Steps 0/1A, before 1B)

Route to **STANDARD** if ANY of the following is true — check in this order, using what Step 0/1A already told you (no new commands needed):
1. Step 0's `session_end_prep.sh` output showed any `src/` path changed this session.
2. Step 1A captured one or more real strategic decisions (i.e. you did NOT write "None — implementation-only session").
3. A `GG-NNN` was opened or resolved this session, or an ADR/APR was drafted, signed off, or superseded.

Otherwise route to **MICRO** — the session was pure documentation/navigation/archival housekeeping (e.g. this fix's own worktree: doc/script edits under `scripts/`, `.claude/`, `03_DECISIONS/`, `04_EXECUTION/`, `11_MEMORY_HANDOFF/`, no `src/` change, no new GG/ADR).

**If unsure, default to STANDARD.** This routing only ever cuts documentation weight, never the untiered floor (Steps 0/1A, worktree/claim/guard mechanics) — guessing MICRO wrong costs a few extra lines of doc; guessing STANDARD when MICRO would do just costs a little time, never safety. State which tier you routed to and why (one line) before continuing.

Each step below marks its **[MICRO]** condensed alternative inline. STANDARD sessions run the full (un-bracketed) version of every step.

---

## Step 1B — Summarize What Was Done

List every task completed this session with:
- Task ID (T-NNN or description)
- What was built/changed
- File paths modified
- Test count change (before → after)
- Any new open questions (OQ-NNN)

**[MICRO: 2-4 bullet lines is enough — task/file(s) touched/one-line outcome. Skip the test-count line if no tests changed.]**

## Step 2 — Update TODO_NEXT.md

**Before editing:** use `grep -n` to find the specific section(s) you need to touch, then `Read` with `offset`/`limit` around that line range (Fix 3) — do not `Read` the whole file. It runs ~700-2000+ lines; a full read burns tokens the tiering fixes exist to save.

In `04_EXECUTION/TODO_NEXT.md`:
- Mark all completed tasks ✅ COMPLETE [DATE] — [brief description]
- Mark in-progress tasks 🟡 IN PROGRESS — [current state]
- Add any newly discovered tasks with next T-number
- Update `Last reviewed` date in header

**[MICRO: same actions, but keep each entry to one line — no multi-paragraph rationale. If nothing in this file actually needs to change (no tasks completed/added), say so and skip the edit entirely rather than touching it just to bump a date.]**

**Archival reminder (Fix 4):** if `wc -l 04_EXECUTION/TODO_NEXT.md` is pushing past ~1500 lines, run `scripts/archive_todo_next.sh` (dry-run first) before or after this step — it mechanically moves completed `## ` sections into `MEMORY_BANK_ARCHIVE.md`. Not required every session; check when the file feels heavy.

## Step 3 — Update MEMORY_BANK.md

**Before editing:** `grep -n "^## Current State Snapshot\|^## Compass OS Health\|^\*\*Last reviewed"` first, then `Read` with `offset`/`limit` around the matched lines (Fix 3) — this file has a strict one-authoritative-block-per-chain rule (T-334) enforced by `scripts/check_memory_bank_snapshots.sh`; a full-file read is rarely necessary just to update these fields.

In `11_MEMORY_HANDOFF/MEMORY_BANK.md`:
- Update `Last reviewed` date and description
- Update `Last major milestone` in Project Identity table
- Update Current State Snapshot section:
  - Phase and gate status
  - Component implementation status
  - Test count
  - Experiment progress
  - Snapshots registered count
- Update Compass OS Health table (M1–M8)
- Update "What Must Happen Next" section

**If replacing the Current State Snapshot or Compass OS Health block:** move the prior block verbatim into `MEMORY_BANK_ARCHIVE.md` — never leave it in place marked "(superseded)"/"(prior)" (that pattern is exactly how both chains grew unreconciled twice; see T-334, `check_memory_bank_snapshots.sh`'s own header comment).

**[MICRO: only touch this file if something in the bulleted list above actually changed (test count, gate status, phase, a new milestone). A pure archival/tooling/doc session usually changes none of these — if so, skip Step 3 entirely and say so, rather than bumping `Last reviewed` for its own sake.]**

## Step 4 — Update PLAN.md

**Before editing:** `grep -n` for the relevant milestone/phase heading first, then targeted `Read` (Fix 3) — same rationale as Steps 2/3.

In `04_EXECUTION/PLAN.md`:
- Update `Last reviewed` date
- Update Phase 6 deliverables table with current status
- If any task moved from pending → complete, mark it

**[MICRO: skip entirely unless a deliverable's status actually moved this session.]**

## Step 5 — Commit Message Draft

Provide a concise git commit message in this format:
```
[PHASE6] Brief description of main work done

- T-NNN: specific change
- T-NNN: specific change
- Tests: NNN/NNN passing
- Gate: [unchanged / CLOSED / OPENED]
```

## Step 6 — Create SESSION_HANDOFF File

Create `11_MEMORY_HANDOFF/SESSION_HANDOFF_YYYYMMDD_HHMM.md` from `00_ADMIN/TEMPLATES/TEMPLATE_SESSION_HANDOFF.md`.

This file MUST include:
- **Strategic Decisions This Session** table (from Step 1A) — mandatory even if empty
- Current paper bet count vs G6 gate (**30 bets** — APR-0016; NOT 50)
- One-thing-pending (single most important next action)
- Resume command for next session

**[MICRO: still write the file (a resume pointer is not optional — GG-101/GG-082 need it, and the checkpoint pointer below depends on it existing), but condense it to: the Strategic Decisions table (still mandatory even if "None"), 2-4 lines of what changed (from Step 1B), one-thing-pending, and the resume command. Skip the bet-count line and any section the template has that doesn't apply to a doc-only session.]**

**Also write the checkpoint pointer (ADR-0041, T-300/Window A; wrapper added T-369; format updated GG-103, 2026-07-15):** after the SESSION_HANDOFF commit lands, run `scripts/write_session_checkpoint.sh <short-session-slug>` (wraps the `04_EXECUTION/.last_session_checkpoint` write — do not inline the raw `git rev-parse`/`printf` here again) and commit the result in the same path-scoped commit as the handoff. Per GG-103, the file is now an **append-only log** (`checkpoint<TAB>timestamp<TAB>slug` per row, `merge=union` in `.gitattributes`, mirroring `SESSION_CLAIMS.md`'s pattern) rather than a single overwritten SHA, so two sessions closing concurrently both survive instead of one clobbering the other's pointer — the wrapper appends, it does not overwrite. This is what lets the *next* session's `/session-start` use `scripts/session_delta.sh` instead of a full read (it reads only the last line's checkpoint field) — skipping this step silently degrades the next session back to the full-read fallback. `session_guard.sh` now warns (does not block) if the last-line checkpoint is stale vs. current HEAD, so a skipped write is no longer silent.

## Step 6B — Operator Digest (mandatory, T-372)

Create `11_MEMORY_HANDOFF/OPERATOR_DIGEST_YYYYMMDD.md` from `00_ADMIN/TEMPLATES/TEMPLATE_OPERATOR_DIGEST.md`, filled in for this session, and commit it in the same path-scoped commit as the SESSION_HANDOFF. This is not optional and not conditional on session size — a session with nothing to report still writes the digest and says so plainly (e.g. "No change today — still zero real money at risk"). Use `11_MEMORY_HANDOFF/OPERATOR_DIGEST_20260715.md` as the worked example of tone and length — plain English, no file paths/function names/p-values, 5-10 lines total.

**Why this is its own step, not folded into Step 6:** `SESSION_HANDOFF_*.md` is the technical record for the next session/auditor. The digest is a *different document for a different reader* — Earl, who does not read code and should not have to open a technical log to know what happened. The one digest written so far (`OPERATOR_DIGEST_20260715.md`) was a one-off demonstration with nothing requiring a second one to exist; this step is what makes it a habit instead of a single artifact nobody was asked to repeat.

Keep it to 5-10 lines per the template's own instruction — if it's running longer, the session did too much to summarize well, not a reason to write more.

## Step 7 — Next Session Primer

In 2-3 sentences, what should the next session's opening prompt contain?

Format:
```
NEXT SESSION PRIMER:
[2-3 sentences on exactly where to pick up, what file to read first, what the immediate next action is]
```

## Step 8 — Push + Merge Before Close (GG-107 root-cause fix, T-355; fast-path added Fix 6, 2026-07-24)

**Never leave a branch unmerged overnight.** The GG-107/109/111 duplicate-claim churn (multiple sessions colliding on the same T-/GG-/ADR- ID across 2026-07-08 through 2026-07-13) was caused in part by session branches sitting unpushed or unmerged for hours-to-days, during which their ID reservations were invisible to `SESSION_CLAIMS.md`-based collision checks and to the next session's Step 0c scan. A branch that only exists locally, or that is pushed but not yet merged to `main`, is a live collision risk for as long as it survives. **This requirement — push + merge same session, no unmerged branch left behind — is untiered; only the merge mechanism below differs by tier.**

1. Commit all path-scoped work (Steps 0-7 above).
2. `git push -u origin <session-branch>` — the branch must exist on `origin`, not just locally.
3. Merge into `main` **in this same session** — do not defer the merge to "next session" or leave it for the operator to do later unless the operator explicitly says so. An unmerged branch is unfinished work, not a stopping point. Pick the mechanism:

   **[MICRO fast path — no `src/` files changed this session (per Step 0/Tier Routing):** skip the PR-review dance and merge directly:
   ```bash
   git fetch origin main
   git merge-base --is-ancestor origin/main HEAD && echo "OK — branch is up to date with origin/main, safe to fast-forward-merge"
   ```
   If that prints OK (no divergence — nobody else landed conflicting doc changes since this branch forked), fast-forward `main` and push directly:
   ```bash
   git push origin HEAD:main
   ```
   If it does NOT print OK (origin/main moved), fall back to the STANDARD path below — do not force-push or attempt a manual fast-forward through a divergence.
   A doc/governance/script-only change still gets full review value from the same-session verification already performed in Steps 0-7 (dry-run reviews, diff --stat checks, targeted reads) — a PR round-trip adds latency and token cost without adding safety here, since no `src/` behavior is at stake.]

   **STANDARD path — any `src/` change, or the fast-forward precondition above failed:** open a PR (or merge conventionally) and merge it through the normal review path before ending the session, exactly as before this fix.
4. Retire the isolated worktree (`scripts/end_session_worktree.sh`) only after the merge lands.
5. If a merge genuinely cannot happen this session (e.g. it is gated on DS sign-off or an operator decision), say so explicitly in the SESSION_HANDOFF and register a T-NNN task for the merge itself — do not let it silently sit as an ordinary open branch.

**Exit check:** `git branch -a` should show no session branch that is both unpushed-or-unmerged AND unaccounted-for in the handoff.

---

## Quick Reference — File Paths to Update Every Session

```
11_MEMORY_HANDOFF/MEMORY_BANK.md              ← STANDARD always; MICRO only if snapshot fields changed
04_EXECUTION/TODO_NEXT.md                      ← STANDARD always; MICRO only if tasks completed/added
03_DECISIONS/DECISION_LOG/DECISION_LOG.md      ← if any strategic decision was made (untiered — Step 1A)
00_ADMIN/APPROVALS_REGISTER.md                 ← if any threshold/gate/governance change (untiered)
04_EXECUTION/PLAN.md                           ← STANDARD if milestones changed; MICRO usually skipped
00_ADMIN/CHANGELOG.md                          ← for significant changes
11_MEMORY_HANDOFF/SESSION_HANDOFF_[date].md    ← always, both tiers (condensed for MICRO — Step 6)
11_MEMORY_HANDOFF/OPERATOR_DIGEST_[date].md    ← always, both tiers (from template, Step 6B)
```

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

---

## Step 0 — Governance Scan (Run FIRST, before anything else)

Run this exact command:
```bash
grep -rn "^\*\*Decisions logged:\*\* false" \
  "02_ARCHITECTURE_DESIGN/" \
  "08_MODEL_RISK_GOVERNANCE/" \
  "01_SPEC/" 2>/dev/null
```

For each file returned:
- **If you modified it this session:** extract its decisions to `DECISION_LOG.md` now, then set its `**Decisions logged:**` field to `true` before committing
- **If you did not modify it:** add a T-NNN task to `TODO_NEXT.md`: "Extract decisions from [FILENAME] → DECISION_LOG.md, set decisions_logged: true"

**A session that creates or modifies a `decisions_logged: false` document without either resolving it or registering a T-NNN is incomplete and represents a governance gap.**

If no matches: write "Governance scan: clean — no decisions_logged: false documents found" and proceed.

---

## Step 1A — Capture Strategic Decisions (MANDATORY — do before anything else)

Ask: "Were any judgment calls, threshold changes, sequencing pivots, or holistic review conclusions made this session?"

For each strategic decision:
1. Add a row to `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` → Notable Judgment Calls table
2. If it requires a formal approval (threshold change, governance pivot, gate revision): add to `00_ADMIN/APPROVALS_REGISTER.md`
3. Mark it as an ANTI-CONTEXT-EROSION INVARIANT in MEMORY_BANK.md if it must survive every future context window

If no strategic decisions were made, write: *"None — implementation-only session."* and continue.

**Also scan every artifact modified this session for conditional language** ("may be revised," "could be adjusted," "threshold may change," "possibly," "if needed"). Any conditional language found must be resolved — either converted to a signed decision (APR-XXXX) or explicitly marked "TBD — requires APR-XXXX by [date]." Do not let conditional language survive the session. See CHANGE_CONTROL.md Conditional Language Governance and LL-008.

## Step 1B — Summarize What Was Done

List every task completed this session with:
- Task ID (T-NNN or description)
- What was built/changed
- File paths modified
- Test count change (before → after)
- Any new open questions (OQ-NNN)

## Step 2 — Update TODO_NEXT.md

In `04_EXECUTION/TODO_NEXT.md`:
- Mark all completed tasks ✅ COMPLETE [DATE] — [brief description]
- Mark in-progress tasks 🟡 IN PROGRESS — [current state]
- Add any newly discovered tasks with next T-number
- Update `Last reviewed` date in header

## Step 3 — Update MEMORY_BANK.md

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

## Step 4 — Update PLAN.md

In `04_EXECUTION/PLAN.md`:
- Update `Last reviewed` date
- Update Phase 6 deliverables table with current status
- If any task moved from pending → complete, mark it

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

**Also write the checkpoint pointer (ADR-0041, T-300/Window A; format updated GG-103, 2026-07-15):** after the SESSION_HANDOFF commit lands, APPEND a new row to `04_EXECUTION/.last_session_checkpoint` — do NOT overwrite it (the file is an append-only log, `merge=union` in `.gitattributes`, mirroring `SESSION_CLAIMS.md`'s pattern so two sessions closing concurrently both survive instead of one clobbering the other's pointer):

```bash
printf '%s\t%s\t%s\n' "$(git rev-parse --short HEAD)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "<short-session-slug>" >> 04_EXECUTION/.last_session_checkpoint
```

Commit it in the same path-scoped commit as the handoff. This is what lets the *next* session's `/session-start` use `scripts/session_delta.sh` instead of a full read (it reads only the last line's checkpoint field, per GG-103) — skipping this step silently degrades the next session back to the full-read fallback.

## Step 7 — Next Session Primer

In 2-3 sentences, what should the next session's opening prompt contain?

Format:
```
NEXT SESSION PRIMER:
[2-3 sentences on exactly where to pick up, what file to read first, what the immediate next action is]
```

## Step 8 — Push + Merge Before Close (GG-107 root-cause fix, T-355)

**Never leave a branch unmerged overnight.** The GG-107/109/111 duplicate-claim churn (multiple sessions colliding on the same T-/GG-/ADR- ID across 2026-07-08 through 2026-07-13) was caused in part by session branches sitting unpushed or unmerged for hours-to-days, during which their ID reservations were invisible to `SESSION_CLAIMS.md`-based collision checks and to the next session's Step 0c scan. A branch that only exists locally, or that is pushed but not yet merged to `main`, is a live collision risk for as long as it survives.

Before ending this session:
1. Commit all path-scoped work (Steps 0-7 above).
2. `git push -u origin <session-branch>` — the branch must exist on `origin`, not just locally.
3. Merge (or open and merge a PR) into `main` **in this same session** — do not defer the merge to "next session" or leave it for the operator to do later unless the operator explicitly says so. An unmerged branch is unfinished work, not a stopping point.
4. Retire the isolated worktree (`scripts/end_session_worktree.sh`) only after the merge lands.
5. If a merge genuinely cannot happen this session (e.g. it is gated on DS sign-off or an operator decision), say so explicitly in the SESSION_HANDOFF and register a T-NNN task for the merge itself — do not let it silently sit as an ordinary open branch.

**Exit check:** `git branch -a` should show no session branch that is both unpushed-or-unmerged AND unaccounted-for in the handoff.

---

## Quick Reference — File Paths to Update Every Session

```
11_MEMORY_HANDOFF/MEMORY_BANK.md              ← always
04_EXECUTION/TODO_NEXT.md                      ← always
03_DECISIONS/DECISION_LOG/DECISION_LOG.md      ← if any strategic decision was made
00_ADMIN/APPROVALS_REGISTER.md                 ← if any threshold/gate/governance change
04_EXECUTION/PLAN.md                           ← if milestones changed
00_ADMIN/CHANGELOG.md                          ← for significant changes
11_MEMORY_HANDOFF/SESSION_HANDOFF_[date].md    ← always (from template)
```

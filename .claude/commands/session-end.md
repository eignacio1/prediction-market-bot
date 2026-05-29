# /session-end — End-of-Session Handoff Protocol

Run this at the end of every Claude Code session before closing. Updates all navigation artifacts so the next session has full context.

**CRITICAL:** Step 1A (Strategic Decisions) is mandatory and must run FIRST. Judgment calls that aren't captured here are permanently lost across context windows.

---

## Step 1A — Capture Strategic Decisions (MANDATORY — do before anything else)

Ask: "Were any judgment calls, threshold changes, sequencing pivots, or holistic review conclusions made this session?"

For each strategic decision:
1. Add a row to `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` → Notable Judgment Calls table
2. If it requires a formal approval (threshold change, governance pivot, gate revision): add to `00_ADMIN/APPROVALS_REGISTER.md`
3. Mark it as an ANTI-CONTEXT-EROSION INVARIANT in MEMORY_BANK.md if it must survive every future context window

If no strategic decisions were made, write: *"None — implementation-only session."* and continue.

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

## Step 7 — Next Session Primer

In 2-3 sentences, what should the next session's opening prompt contain?

Format:
```
NEXT SESSION PRIMER:
[2-3 sentences on exactly where to pick up, what file to read first, what the immediate next action is]
```

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

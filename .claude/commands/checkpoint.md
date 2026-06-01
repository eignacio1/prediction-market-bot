# /checkpoint — Mid-Session Save Point

## When to invoke

Invoke **immediately after completing any major task block**, before starting the next one. Do not wait until session end. Do not wait to be asked.

**A major task block is completed when any of these are true:**
1. A PDTP review or holistic analysis session is finished
2. A governance sprint (DECISION_LOG updates, document field changes) is finished
3. An implementation sprint (all planned tasks complete, tests passing) is finished
4. An experiment (EXP-NNN) is run and logged
5. A phase gate (G0–G9) is closed
6. Category switch: moving from governance → implementation, or implementation → research, etc.
7. **30+ tool calls have occurred since the last checkpoint** — use this as a hard failsafe even if no "natural" block boundary has been reached

**The rule is proactive, not reactive.** Do not wait for the context to feel full. Do not wait for the user to ask for a save. Write the checkpoint at the boundary between blocks.

---

## What to produce

Create `11_MEMORY_HANDOFF/CHECKPOINT_YYYYMMDD_HHMM.md` from `00_ADMIN/TEMPLATES/TEMPLATE_CHECKPOINT.md`.

**This is NOT a full /session-end. Skip:** PLAN.md update, MEMORY_BANK.md update, Compass OS health table, git commit message. Only:
1. Write the CHECKPOINT file (Step A)
2. Write any block decisions to DECISION_LOG.md if not already done (Step B)
3. Report to user (Step C)

---

## Step A — Write CHECKPOINT file

Populate template with:
- **Block completed:** 1-2 sentences — specific file names, task IDs, test counts, decision names
- **Decisions made:** every threshold/sequencing/strategy judgment call from this block
- **Governance state:** run the anchored grep scan; record exact output or "clean"
- **Next block:** exactly what the next task is; which file to read first; any operator dependency

---

## Step B — Decisions to DECISION_LOG.md (if not already written)

If this block produced any strategic decisions not yet in DECISION_LOG.md, write them now. The checkpoint references them — they must exist in DECISION_LOG.md first.

Run Step 0 of /session-end (governance scan) to confirm no new `decisions_logged: false` documents were created this block without a corresponding T-NNN.

---

## Step C — Report to user

Tell the user:
- "Checkpoint written: CHECKPOINT_[timestamp].md"
- 1 sentence per section on what was captured
- Exactly what comes next

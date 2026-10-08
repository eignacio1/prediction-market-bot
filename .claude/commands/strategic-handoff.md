# /strategic-handoff — Strategic window handoff (operator protocol, 2026-10-08)

Run this in the **strategic window** (not a terminal) when the operator says the window's last wave is done and to
hand off, or says "handoff" / "wrap it up" / "new chat". The operator should never have to ask for the deliverables
below by name; producing them IS the handoff. (Operator, 2026-10-08: "give me the operational doc + the paste-in
prompt for the new chat - this should be wired into the protocol somehow so I don't need to keep repeating it.")

A window hands off only after its last wave is **verified**, never when the wave is merely issued (operator,
2026-10-07: "AFTER wave 60 is finished then we'll handoff").

## Steps (in order)

1. **Verify the last wave** against GitHub: every block's results doc, PRs merged + CI green, deploy decisions,
   gap-log parity + uniqueness. Close it in `04_EXECUTION/ACTIVE_QUEUE.md` (results table, sequencing track,
   prompts archived verbatim to `ACTIVE_QUEUE_ARCHIVE.md`). Update the **RUNNING SITREP** at the top of the queue.
   Under NOW, state that the next wave is to be written by the incoming window.
2. **Archive** the current `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md` and `04_EXECUTION/NEW_WINDOW_PASTE_IN.md`
   to `11_MEMORY_HANDOFF/<name>_<YYYY-MM-DD of the outgoing version>.md` (skip if that version was never used).
3. **Rewrite the operational doc** — `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md` — sections:
   §1 Role · §2 Protocols (every standing operator rule, with date + his words where short) · §3 Traps ·
   §4 State at handoff (derived by running commands at write time: SHA, max GG/T/ADR/EXP, OPEN count + parity,
   registry counts, capital, books, arms, scheduled jobs) · §5 Arc + what the next wave should be · §6 Open operator
   decisions · §7 What this window got wrong · §8 DO NOT · §9 First actions for the incoming window.
4. **Rewrite the paste-in** — `04_EXECUTION/NEW_WINDOW_PASTE_IN.md` — short, ASCII, self-contained; it must name this
   command so the next window hands off the same way. Template is the current file; update only the window range,
   the handoff time and the FIRST TASK.
5. **DECISION_LOG** entry for the handoff; docs-only commit; push to main.
6. **Deliver, in the chat, without being asked:** `SendUserFile` with the carry-forward, the paste-in and
   `ACTIVE_QUEUE.md` (three file cards), then the paste-in text inside a code fence in the reply so he can copy it
   directly. One-paragraph sitrep. No commands for him to run.

# /strategic-handoff — Strategic window handoff (operator protocol, 2026-10-08)

Run this in the **strategic window** (not a terminal) when the operator says the window's last wave is done and to
hand off, or says "handoff" / "wrap it up" / "new chat". The operator should never have to ask for the deliverables
below by name; producing them IS the handoff. (Operator, 2026-10-08: "give me the operational doc + the paste-in
prompt for the new chat - this should be wired into the protocol somehow so I don't need to keep repeating it.")

A window hands off only after its last wave is **verified**, never when the wave is merely issued (operator,
2026-10-07: "AFTER wave 60 is finished then we'll handoff").

## Steps (in order)

0. **Read `04_EXECUTION/WINDOW_ERROR_LOG.md` first** (ADR-0074, Hard Rule 15) — the incoming window does this before
   writing anything, and names in its first message to the operator the pattern it is most at risk of repeating. The
   outgoing window confirms every mistake it made is a row there (the log, not the carry-forward's §7, is authoritative)
   and updates the pattern tally.


1. **Verify the last wave** against GitHub: every block's results doc, PRs merged + CI green, deploy decisions,
   gap-log parity + uniqueness. Close it in `04_EXECUTION/ACTIVE_QUEUE.md` (results table, sequencing track,
   prompts archived verbatim to `ACTIVE_QUEUE_ARCHIVE.md`). Update the **RUNNING SITREP** at the top of the queue.
   Under NOW, state that the next wave is to be written by the incoming window.
   **Forest check** (same at every wave close, not only at handoff): recompute the DISTANCE TO OPTIMUM table at the top
   of the sitrep (every measure, with source and date, and the "Moved" column), then tally which pillar of CLAUDE.md § "What winning looks like — the operator's north star (four pillars)" each block
   moved (from each handoff's `vision_pillar:` and the results docs), update the sitrep's pillar scoreboard, and tell
   the operator unprompted if two consecutive waves moved no pillar.
   **Surface row:** run `python3 scripts/runtime_registry.py surface` and put live / unreviewed / no-alarm counts in the
   sitrep with the current red signals (healthcheck, silent arms, running-SHA). Hard Rule 14: no wave adds a live component
   while one is red unless its first block fixes it.
   **Wave format (Hard Rule 15):** every wave the window issues carries three lines above the blocks — **Pushback:** the
   strongest reason not to run this wave as planned; **Surface:** components added/retired and the red signals now;
   **Dependencies:** confirmation that no block's merge or input depends on another block of the same wave.
   **Purpose lines:** every block the window writes carries, under its title, `PURPOSE: <measure> — <expected change>`
   (or `PURPOSE: PLUMBING — <why it is needed>`), and its report back states the measured change (Hard Rule 12).
2. **Archive** the current `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md` and `04_EXECUTION/NEW_WINDOW_PASTE_IN.md`
   to `11_MEMORY_HANDOFF/<name>_<YYYY-MM-DD of the outgoing version>.md` (skip if that version was never used).
3. **Rewrite the operational doc** — `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md` — sections:
   §0 North star — a pointer to CLAUDE.md § "What winning looks like — the operator's north star (four pillars)" (never a restatement) plus the distance-to-optimum table at handoff ·
   §1 Role · §2 Protocols (every standing operator rule, with date + his words where short) · §3 Traps ·
   §4 State at handoff (derived by running commands at write time: SHA, max GG/T/ADR/EXP, OPEN count + parity,
   registry counts, capital, books, arms, scheduled jobs) · §5 Arc + what the next wave should be · §6 Open operator
   decisions · §7 What this window got wrong · §8 DO NOT · §9 First actions for the incoming window.
4. **Rewrite the paste-in** — `04_EXECUTION/NEW_WINDOW_PASTE_IN.md` — short, ASCII, self-contained; it must name this
   command so the next window hands off the same way. Template is the current file; update only the window range,
   the handoff time and the FIRST TASK.
5. **Stale-rule sweep:** grep the carry-forward, the paste-in, the queue's standing sections and CLAUDE.md for any rule
   a newer operator directive superseded (2026-10-09 found "calibration mode: not more cells" still in the paste-in
   after the expansion directive). Fix each in place; note it in the DECISION_LOG entry.
5b. **Tension-register review** (ADR-0075): read `02_ARCHITECTURE_DESIGN/TENSIONS/{nfl,nba}.toml` (rules in `TENSIONS/README.md`). Add tensions this wave exposed, mark relieved ones with evidence, flag any relief deferred across two waves. A tension that needs an ADR-0075 definition changed goes to the operator.
6. **DECISION_LOG** entry for the handoff; docs-only commit; push to main.
7. **Deliver, in the chat, without being asked:** `SendUserFile` with the carry-forward, the paste-in and
   `ACTIVE_QUEUE.md` (three file cards), then the paste-in text inside a code fence in the reply so he can copy it
   directly. One-paragraph sitrep. No commands for him to run.

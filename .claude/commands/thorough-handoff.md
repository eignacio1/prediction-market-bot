# /thorough-handoff — Emergency Context Preservation Protocol

**Trigger:** Context window at or above 80%, OR PreCompact hook fired, OR Notification hook detected limit warning.

This is the endpoint for the automated hook in settings.json. Run immediately. Do not defer.

---

## Step 1 — Capture Any Unrecorded Strategic Decisions NOW

Before touching any files, ask: were any strategic decisions made this session that are not yet in `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`?

If yes: write them to DECISION_LOG immediately. One row per decision. Do not skip this.

Scan for conditional language in any artifact modified this session ("may be revised," "could be," "possibly"). If found: resolve or flag as TBD with owner + date. See CHANGE_CONTROL.md Conditional Language Governance.

---

## Step 2 — Write SESSION_HANDOFF File

Create `11_MEMORY_HANDOFF/SESSION_HANDOFF_YYYYMMDD_HHMM.md` from `00_ADMIN/TEMPLATES/TEMPLATE_SESSION_HANDOFF.md`.

The file MUST contain:

**Strategic Decisions This Session** — table of every judgment call, threshold change, or sequencing decision made. Even if none: write "None — implementation-only session."

**Tasks Completed** — every T-NNN finished, with one-line outcome.

**ONE THING PENDING** — the single most critical next action, with exact state:
- If data pull was running: "Pull complete. Cache at [path]. Run with SKIP_PULL=1 — <2 min."
- If operator action needed: "Waiting for [specific action] at [specific location]."
- If implementation in progress: "Stopped at [file]:[line]. Next: [exact next step]."

**Paper portfolio state** — current bankroll, open positions, resolved count vs. G6 gate (30 bets).

**Resume command** — exact prompt for next session.

---

## Step 3 — Update MEMORY_BANK.md

In `11_MEMORY_HANDOFF/MEMORY_BANK.md`:
- Update `Last reviewed` header
- Update Current State Snapshot: tests, experiments, components, gate status
- Update Compass OS Health M1–M8
- Confirm G6 gate shows **30 bets** (not 50 — APR-0016)

---

## Step 4 — Update TODO_NEXT.md

In `04_EXECUTION/TODO_NEXT.md`:
- Mark all completed tasks ✅ COMPLETE [DATE]
- Add any newly discovered tasks with next T-number
- Update `Last reviewed` date

---

## Step 5 — Commit and Push

```bash
git add [all modified files]
git commit -m "[HANDOFF] Session end — [brief description of main work]"
git push origin main
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 "cd /opt/prediction-market-bot && git pull origin main"
```

---

## Step 6 — Confirm Handoff Complete

State: "Handoff complete. Commit [hash] pushed. Resume: [SESSION_HANDOFF filename]."

Next session opens with:
```
Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and 11_MEMORY_HANDOFF/SESSION_HANDOFF_[date].md, confirm [N] tests
```

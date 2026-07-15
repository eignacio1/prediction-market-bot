# Pending Wire-In — 2026-07-15 Efficiency/Fidelity Recommendation Pack

**Why this file exists instead of direct edits:** at session start, `git status` showed `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`, `04_EXECUTION/PLAN.md`, `04_EXECUTION/TODO_NEXT.md`, and `11_MEMORY_HANDOFF/MEMORY_BANK.md` all carrying uncommitted changes — evidence of at least one concurrent session actively mid-edit on the exact shared navigation files this task would otherwise need to touch. This session also had no network route to GitHub (sandboxed environment), so it could not use `claim_session.sh`'s normal atomic-claim-through-origin mechanism to safely serialize against that concurrent work. Rather than risk committing another session's in-flight, not-yet-finalized edits under this session's name/timing (exactly the failure mode Hard Rule 10 / GG-101 exist to prevent), everything below is staged here — in a brand-new file with zero collision surface — for a networked session to fold into the real files once it has confirmed (fresh `git diff`, per Hard Rule 10) that those files are no longer mid-edit.

**Delete this file once its contents have been wired into their real homes** (`TODO_NEXT.md`, `DECISION_LOG.md`) — it is a staging area, not a permanent artifact.

---

## 1. Register: backlog burn-down cadence (proposed T-365)

**Task:** T-365 (proposed, unclaimed — verify T-365 is still the next free ID before registering; SESSION_CLAIMS.md may have advanced past T-364 by the time this is wired in).

**Description:** Establish a recurring cadence — proposed: every 4th session, or once weekly, whichever comes first — dedicated specifically to closing OPEN governance gaps rather than opening new ones. Trigger for this: `GOVERNANCE_GAP_LOG.md` currently shows 17 of 30 logged gaps (57%) still OPEN, and the count has been growing faster than it closes. Most open items are correctly flagged zero-capital-risk today, but an unbounded, growing backlog is exactly the shape of problem that let warning signs go unaddressed before the documented prior crash.

**Proposed mechanics:**
- A dedicated session type ("burn-down session") whose only mandate is: pick the 2-3 oldest or highest-severity OPEN gaps, either resolve them, escalate them to a formal APR/ADR if they need a DS decision, or explicitly re-affirm them as long-term watch items with a stated re-check date — no new feature/experiment work in that session.
- Track burn-down rate alongside open-count in the Step 4 operational health check (CLAUDE.md) or `governance_scan.sh`, so a growing backlog becomes visible the same way a dark pipeline already is.
- Optional: a soft WIP cap (e.g., "if OPEN count exceeds N, the next session must be a burn-down session before new work") — flagged as optional because a hard gate could itself become a source of friction; the operator should decide whether to make this a hard rule or a soft norm.

**Registration action needed:** add this as a new row in `TODO_NEXT.md` with a real T-number (re-verify against live `SESSION_CLAIMS.md`/`TODO_NEXT.md` first), and consider a one-paragraph addition to `CLAUDE.md`'s protocol section if the operator wants it enforced rather than just tracked.

---

## 2. Harden: delta-first checkpoint reliability (proposed T-366)

**Finding (verified by direct read this session, not assumed):** `04_EXECUTION/.last_session_checkpoint` currently holds a valid SHA (`b332186`) — the mechanism is populated right now, so this is not an active outage. The gap is in *how* it gets written: `.claude/commands/session-end.md` Step 6 instructs writing this file via a single manual line buried in a ~150-line protocol document — `git rev-parse --short HEAD > 04_EXECUTION/.last_session_checkpoint`, run by whichever agent happens to be following the protocol correctly that session. The doc itself already admits the risk in its own text: "skipping this step silently degrades the next session back to the full-read fallback." There is no automated check that this step actually ran before a session closes.

**Proposed fix (not yet implemented — registering as a task, not shipping a live hook this session, given the collision risk of modifying shared protocol/hook files while other sessions are actively working):**
- Replace the manual one-liner with a small wrapper script (e.g. `scripts/write_session_checkpoint.sh`) that Step 6 calls instead of the raw command — same effect, but gives future tooling (e.g. `session_guard.sh`) one canonical thing to check for/call.
- Add a passive verification to `session_guard.sh` (already run at every session start): compare `.last_session_checkpoint`'s SHA against `git log` — if the checkpoint is more than N commits or N days behind current HEAD on `main`, print a warning ("checkpoint stale — last session may have skipped Step 6") the same way the guard script already warns about `MEMORY_BANK.md` snapshot hygiene. This makes a missed checkpoint-write visible immediately at the next session's start, instead of silently degrading that session to a full read with no explanation of why.
- Do not change `session_delta.sh` itself — it is correct and already handles a missing/invalid checkpoint by erroring clearly; the gap is entirely upstream, in whether Step 6 reliably produces a fresh one.

**Registration action needed:** add as T-366 in `TODO_NEXT.md`; scope is small (one wrapper script + a few lines added to `session_guard.sh`), suitable for a single focused session once the shared files are free to edit.

---

## 3. Draft DECISION_LOG.md row (for this session, 2026-07-15)

Wire the following into `DECISION_LOG.md`'s Notable Judgment Calls table once it is no longer mid-edit by a concurrent session:

> **2026-07-15** | **[Efficiency/fidelity review + 5-item recommendation pack]** — Operator asked directly whether project scale has outrun the ability to make high-fidelity updates, and whether rigor has insulated against ruin. Answered with measured evidence (47-day repo age, 686 commits, 42 ADRs, 30 GGs/17 OPEN, 6,226 lines across core nav files, GG-105 as a 1,500+-word single-entry example) rather than impression. Verdict: yes, entry-level and file-level bulk has outrun skimmability in places; no, capital-safety rigor has not been compromised (zero live capital, G6 bar made stricter not looser via APR-0024, GG-113 found and fixed this week). Operator approved building all 5 recommendations. Delivered this session: **ADR-0044** (governance-entry current-status + linked-history split, ACCEPTED, operator sign-off in-session — not yet pushed, no network access), a worked, non-live demonstration of the split using GG-105 (`GG105_SPLIT_WORKED_EXAMPLE.md`), an operator-digest template + worked example (`TEMPLATE_OPERATOR_DIGEST.md`, `OPERATOR_DIGEST_20260715.md`), a tested timestamp-integrity checker (`scripts/check_future_timestamps.sh`, verified both clean-path and future-dated-detection-path against a synthetic test repo), and this staging file registering two further proposed tasks (T-365 backlog burn-down cadence, T-366 checkpoint-reliability hardening) that could not be wired directly into `TODO_NEXT.md`/`DECISION_LOG.md` because those files carried concurrent-session uncommitted state at session start and this sandbox had no network route to serialize safely through `origin`. **Correction, same session:** initially suspected a real timestamp-integrity defect in `SESSION_CLAIMS.md` (entries appearing dated a day ahead of the stated "current date"); traced to a timezone-display artifact in the system-provided current-date context (Pacific-time date string vs. the real UTC clock actually used to stamp entries, confirmed via direct `date -u` check against a fresh worktree HEAD) — not a genuine defect. Built the timestamp-integrity checker anyway since the underlying class of problem (a real clock-skew bug) is worth having an automated check for, independent of this particular false alarm.

---

## 4. What was explicitly NOT done this session, and why

- **Did not edit `GOVERNANCE_GAP_LOG.md`'s live GG-105 entry** — demonstrated the split pattern on a copy instead (see `GG105_SPLIT_WORKED_EXAMPLE.md`), because GG-105 had very recent same-day concurrent activity (T-359/T-361) and this session had no way to confirm it was safe to edit live without network access to check `origin` state.
- **Did not apply the `MEMORY_BANK.md` T-334 archival fix** that `session_guard.sh` itself flagged live this session (4 stacked Current State Snapshot headers, 20 stacked Last-reviewed headers) — `MEMORY_BANK.md` was one of the four files carrying concurrent uncommitted state at session start. This is the single most valuable and most ready-made next action once that file is free — the guard script already states the exact fix needed.
- **Did not reach the VPS** — Step 4 of the session-start protocol (operational health check) could not run; this sandbox has no route to `prediction-market-vps` (SSH hostname does not resolve). Disclosed rather than fabricated.
- **Did not push/PR/merge anything to `origin/main`** — no GitHub network access from this sandbox. All new files described above exist locally in the working tree only, ready for a networked session to commit/push.

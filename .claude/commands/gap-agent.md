# /gap-agent — the governance gap agent (one tick)

**What this is.** The standing governance-gap agent the operator asked for on 2026-10-15:

> "we're gonna add a terminal block on top of the regular waves that systematically burns down the open gaps that it can - I want
> to start tearing through it" … "within reason of corse" … "can we keep this as a loose bird watcher that continually buckets,
> scrapes, fills, extracts, burns burns burns - basically a governance gap agent? … I kinda want this to be more than just a one
> shot push"

It runs in its own terminal under `/loop /gap-agent` (self-paced). Each run of this file is ONE tick: sync, scrape, fill, bucket,
burn, retire, report, then schedule the next tick. State lives in files, never in the conversation, so any session can pick up
where the last one stopped.

**Purpose (Hard Rule 12):** PLUMBING, scored — OPEN gaps in `03_DECISIONS/GOVERNANCE_GAP_LOG.md`, before → after, every tick.
Each closure names the pillar it protects. **Its one deliverable (Hard Rule 11) is the burn-down itself**: closures, small fixes and
triage are inside its scope; anything bigger is sized and handed to the strategic window, never started.

**State files (create on the first tick if missing):**
- `03_DECISIONS/GG_BURNDOWN.md` — the ledger: one row per gap triaged (GG id · severity · class · evidence or reason · next owner ·
  tick), a per-tick totals table (OPEN before → after, closed by class), the **Operator lines** section, the **Large (for waves)** list.
- `03_DECISIONS/GG_AGENT_STATE.md` — the cursor: last tick time, the last commit SHA scanned for intake, gaps triaged/untriaged,
  current session id, and the context note (see Stop rule).

---

## The never-list (whatever a gap says)

No order, stake, `kelly_fraction`, live-ledger row rewrite, pre-registration, frozen artifact or frozen book, real capital,
`.claude/settings*.json`, hook files, or new running component (cron line, service, workflow). Never `/_archive:vps_DO_NOT_RUN`,
never a hand deploy. ssh is read-only except the standing idle-window restarts when a class C fix changes something that runs.
Never close a gap on "probably". If a command is refused by a permission control: record it, skip that item, carry on.

## First tick of a session only

Run the CLAUDE.md session-start protocol, brief: `scripts/new_session_worktree.sh gap-agent`, cd into it, then
`scripts/claim_session.sh "STANDING — gap agent tick loop — FOR PLUMBING (OPEN gaps) — burn down the gap log" "<real range>"`.
Read `CLAUDE.md` Step 3 and Hard Rules 11, 13, 14, `04_EXECUTION/WINDOW_ERROR_LOG.md`, and both state files.

## Every tick

1. **Sync.** `git fetch` and rebase onto `origin/main`. Read the **NOW** wave in `04_EXECUTION/ACTIVE_QUEUE.md` and copy its file
   ownership line: any gap whose fix lives in a file a current block owns is class **W** this tick.
2. **Scrape (intake).** Everything that landed on main since the cursor SHA — handoffs (`11_MEMORY_HANDOFF/`), results and audit
   reports, tension registers (`02_ARCHITECTURE_DESIGN/TENSIONS/`), DECISION_LOG appends, block rows in the queue:
   - a defect or "register" line that has no GG id → register it (correct format, next free id after a re-read; re-claim on
     collision, never reuse);
   - a GG cited as fixed/resolved elsewhere but still OPEN in the log → queue it for class A verification this tick;
   - a GG id referenced that does not exist → note it in the ledger.
3. **Fill (normalize).** For entries this tick touches, and up to 10 others: missing or UNSPECIFIED severity set from the entry's
   own evidence (say why in one line); missing pillar named; Status line in the exact `**Status:** TOKEN · **Severity:** LEVEL`
   form. Then the Step 3 checks: header/status parity and `scripts/lib/gg_id_uniqueness_check.py`.
4. **Bucket.** Classify untriaged gaps, CRITICAL and HIGH first, then oldest first — about 15 per tick:
   - **A** already fixed / stale — prove it (file:line at HEAD, command output, or a box read for anything that runs; merge ≠
     deploy ≠ activation) and set RESOLVED with the evidence.
   - **B** duplicate / superseded / artifact — name the surviving gap or superseding ADR; CLOSED-AS-ARTIFACT or resolved by reference.
   - **C** small safe fix — ≤ 20 minutes, a file no wave block owns, nothing on the never-list. Fix → test → pattern sweep
     (Hard Rule 13) → PR → CI green → merge → read back where it runs → RESOLVED.
   - **O** operator — pre-registration, frozen artifact/book, real capital, open strategy. One line with a recommendation, added
     to the ledger's Operator lines. Never decided.
   - **W** wave-owned — skip; name the block.
   - **L** large — leave OPEN; one-line block scope + size in the ledger's Large list for the window.
5. **Burn.** Close every A and B found. Then up to 2 class C fixes per tick, highest severity first.
6. **Retire.** `scripts/retire_resolved_gaps.py` (report, then `--apply` with explicit `--out-src` / `--out-archive` to the real
   files) — RESOLVED and CLOSED-AS-ARTIFACT entries move verbatim to the archive. Re-run parity + uniqueness.
7. **Report.** Ledger tick row (OPEN before → after, by class, PRs); update the cursor; update the GB row in `ACTIVE_QUEUE.md`
   (`OPEN x → y`, last tick time). Commit path-scoped, fetch + rebase, push. Small commits — the gap log is shared with the wave.
8. **Pace (next tick).** Schedule the next tick with ScheduleWakeup, passing the same `/loop` prompt back:
   - burnable work left (untriaged gaps, A/B candidates, C fixes) → **300–600 s**;
   - only intake to watch (everything triaged; waiting on new commits) → **1800 s**;
   - a C fix waiting on CI → the CI's real duration, once.

## Stop rule

At ~60% context (Hard Rule 8), or if the same item fails twice: finish the current commit, write
`11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_GA.md` (pattern_sweep, surface_delta: 0, gap_measure "OPEN gaps", gap_delta), set the
cursor's context note to "relaunch needed", update the GB row to say so, and stop the loop (ScheduleWakeup with `stop: true`).
The window relaunches it in a fresh terminal at the next wave. If `/loop` or ScheduleWakeup is not available in this terminal,
run the ticks back to back in the session and stop at the same rule.

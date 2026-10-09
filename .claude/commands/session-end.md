# /session-end — End-of-Session Handoff Protocol

## HARD BUDGET: ≤10% context, ≤10 minutes wall time — read this before Step 0 (GG-182/T-452)

**Session-end is a checklist, not a composition exercise.** Hard Rule 8's 60% trigger (below) governs WHEN close-out starts; it does not govern what it costs — that is what this section fixes. A 2026-08-14 session-end consumed 53% of context (40%→93%) and ran 52m41s, entirely by hand-rewriting multi-KB `DECISION_LOG.md` blocks with exact-match `Edit` calls (including one failed `Edit` that burned a full round-trip on a multi-KB block) instead of a minimal append. If you cannot fit inside this budget, use the Truncation Path below — do not push through by working faster.

**This budget is now instrumented, not self-assessed (GG-182's assertion, landed T-455).** A model cannot observe its own context/usage capacity in-band — there is no counter to read for the quantity that actually ran out on 2026-08-14. Wall clock and word counts ARE observable, so that is what `scripts/session_end_timer.sh` measures. Run this the moment you start session-end, before Step 0:
```bash
scripts/session_end_timer.sh start
```
Then run `scripts/session_end_timer.sh check` at the two points below where cost actually accumulates — not just at the very end, where the verdict arrives too late to act on. It prints an explicit verdict string (`WITHIN BUDGET` or `BUDGET EXCEEDED, TRUNCATE NOW`) and exits nonzero on breach — read the verdict, don't compute your own.

**Method rules — these are why past close-outs blew the budget, not a style preference:**

- **Never `Edit` a multi-KB block. Never `Edit` `DECISION_LOG.md` at all, regardless of size.** Append only, via heredoc, and check the word count mechanically rather than eyeballing it — `wordcheck` reads the same text on stdin via `tee`:
  ```bash
  scripts/session_end_timer.sh check   # before writing — are you still inside the 10-min budget?
  cat <<'EOF' | tee -a "03_DECISIONS/DECISION_LOG/DECISION_LOG.md" | scripts/session_end_timer.sh wordcheck DECISION_LOG 150

  | YYYY-MM-DD | T-NNN | One-sentence decision, ≤150 words total for the entry. |
  EOF
  ```
- **A failed exact-match `Edit` is a stop, not a retry.** One failed multi-KB `Edit` round-trip is itself a material fraction of the 10-minute budget. The instant an `Edit` fails on a large or verbatim-sensitive block, switch to the heredoc-append form above — do not re-attempt the same `Edit` with adjusted context, and do not try to make the match exact.
- **`scripts/generate_session_artifacts.py` is mandatory, not a suggestion.** It is the write-once mechanism (T-430) for the "Last reviewed" chain collapse, the SESSION_CLAIMS.md closure row, the checkpoint pointer, and the MICRO-tier operator digest one-liner — do not hand-author anything it produces. **It does not cover `DECISION_LOG.md`** — that file is explicitly excluded by design (Hard Rule 7: real judgment stays model-authored) — so `DECISION_LOG.md` entries remain hand-authored, but MUST use the heredoc-append rule above, never `Edit`. This is the one gap in write-once coverage; know it going in.
- **Hard word caps, enforced, not aspirational:** `DECISION_LOG.md` entry ≤150 words · `TODO_NEXT.md` update ≤120 words · `SESSION_HANDOFF` ≤300 words · Operator Digest ≤150 words. Terse-and-complete beats exhaustive — anything longer belongs in the commit range, which is already there and doesn't need to be re-narrated.
- **No re-derivation at close-out.** Every number written into a close-out artifact must already be visible in this session's own scrollback. If writing the close-out requires re-running a command just to get a number, you are over budget — omit the number and say so (e.g. "bet count not re-checked this close-out — see live governance scan") rather than spend budget re-deriving it.

**Truncation path — if you hit the budget mid-close-out:**
1. Commit whatever is already staged/complete, path-scoped.
2. Write a 3-line stub handoff in place of the full SESSION_HANDOFF: task id, one-line summary, "TRUNCATED AT BUDGET — see commit range for detail."
3. Report to the operator: "session-end truncated at budget — [context %]/[minutes] used."
4. Stop. Do not attempt to finish the remaining steps in the same turn.

---

## ⚠️ TRIGGER THIS IMMEDIATELY WHEN CONTEXT WINDOW REACHES ~60%

Do not wait until "a good stopping point." At 60% context: stop all implementation work, run this protocol in full, commit, and push. The cost of losing a session's decisions permanently exceeds the cost of any implementation delay. When in doubt, trigger early. The trigger was 80% until 2026-08-10 (T-434). It was moved to 60% because this protocol is itself context-expensive: starting it at 80% means compacting *during* close-out, which is how a single session-end ran past an hour on T-429.

**Signs you are near 60%:** responses are slower, the conversation has been running for many tool calls, or the user references that the window is getting full.

---

## /checkpoint vs /session-end — Know the difference

**`/checkpoint`** — Run between task blocks (every 30 tool calls or at every block boundary). Writes a ~20-line `CHECKPOINT_YYYYMMDD_HHMM.md`. Does NOT update PLAN.md, MEMORY_BANK.md, or produce a commit message. Fast (<2 min). See `.claude/commands/checkpoint.md`.

**`/session-end`** (this file) — Run at true session end OR at 60% context. Full update of all navigation artifacts + commit message + SESSION_HANDOFF file. The heavyweight version.

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

**Tier is declared at CLAIM time, not computed here (T-434, 2026-08-10).** The routing rules above stay as the check — if what you actually did contradicts the tier you declared at claim time, say so in one line and route on what you did. But declaring up front is what keeps a session sized; re-deriving tier only at close-out is how a MICRO task becomes a STANDARD one without anyone deciding to.

Each step below marks its **[MICRO]** condensed alternative inline. STANDARD sessions run the full (un-bracketed) version of every step.

**T-430 (2026-08-07) — write-once, generate-the-rest:** session-end used to re-author the same session narrative by hand in six or seven places (TODO_NEXT/MEMORY_BANK/PLAN "Last reviewed" chains, SESSION_CLAIMS closure row, checkpoint pointer, Operator Digest), each a separate model-authored write and tool round-trip. That compounds on long sessions — exactly when context is scarcest — and was observed pushing a single close-out past 20 minutes into a repeated compaction loop. The fix, matching this repo's existing `OPERATOR_CONSOLE.md` precedent (generated, never hand-patched): you author the session narrative **once**, in the `<!-- session-meta -->` block at the top of the SESSION_HANDOFF file (Step 6), and `scripts/generate_session_artifacts.py` mechanically derives the "Last reviewed" chain collapse (all three nav files, both tiers), the SESSION_CLAIMS closure row (both tiers — this row previously had no dedicated step at all and was being skipped), and the checkpoint pointer (both tiers) from it. **Target model-authored writes: MICRO ≤3** — the DECISION_LOG row (Step 1A, only if a real decision was made), the SESSION_HANDOFF file itself, and the commit. Everything else on a MICRO session is either generated or explicitly skipped. STANDARD still hand-authors substantive nav-file content (task completions, milestone shifts, prose digest, primer) — only the repetitive narrative-chain/closure-row/checkpoint layer is generated for it too.

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

**Do not hand-edit the `**Last reviewed** chain here (either tier).** That line is now collapsed and regenerated automatically by Step 6's `scripts/generate_session_artifacts.py` call, from the SESSION_HANDOFF's `session-meta` block — it archives the full prior chain verbatim to `TODO_NEXT_ARCHIVE.md` (ADR-0044) and writes one current-status line. This step is only for substantive task-list content.

**[MICRO: same actions, but keep each entry to one line — no multi-paragraph rationale. If nothing in this file actually needs to change (no tasks completed/added), skip this step entirely — the chain bump still happens via Step 6 regardless.]**

**Archival reminder (Fix 4):** if `wc -l 04_EXECUTION/TODO_NEXT.md` is pushing past ~1500 lines, run `scripts/archive_todo_next.sh` (dry-run first) before or after this step — it mechanically moves completed `## ` sections into `MEMORY_BANK_ARCHIVE.md`. Not required every session; check when the file feels heavy.

## Step 3 — Update MEMORY_BANK.md

**Before editing:** `grep -n "^## Current State Snapshot\|^## Compass OS Health\|^\*\*Last reviewed"` first, then `Read` with `offset`/`limit` around the matched lines (Fix 3) — this file has a strict one-authoritative-block-per-chain rule (T-334) enforced by `scripts/check_memory_bank_snapshots.sh`; a full-file read is rarely necessary just to update these fields.

In `11_MEMORY_HANDOFF/MEMORY_BANK.md`:
- Update `Last major milestone` in Project Identity table
- Update Current State Snapshot section:
  - Phase and gate status
  - Component implementation status
  - Test count
  - Experiment progress
  - Snapshots registered count
- Update Compass OS Health table (M1–M8)
- Update "What Must Happen Next" section

**Do not hand-edit the `**Last reviewed** chain here (either tier)** — same generated mechanism as Step 2, archiving to `MEMORY_BANK_ARCHIVE.md`. This is a *different* chain from the Current State Snapshot / Compass OS Health blocks below, which are not touched by the generator and still follow the T-334 rule as-is:

**If replacing the Current State Snapshot or Compass OS Health block:** move the prior block verbatim into `MEMORY_BANK_ARCHIVE.md` — never leave it in place marked "(superseded)"/"(prior)" (that pattern is exactly how both chains grew unreconciled twice; see T-334, `check_memory_bank_snapshots.sh`'s own header comment).

**[MICRO: only touch this file if something in the bulleted list above actually changed (test count, gate status, phase, a new milestone). A pure archival/tooling/doc session usually changes none of these — if so, skip Step 3 entirely and say so; the chain bump still happens via Step 6 regardless.]**

## Step 4 — Update PLAN.md

**Before editing:** `grep -n` for the relevant milestone/phase heading first, then targeted `Read` (Fix 3) — same rationale as Steps 2/3.

In `04_EXECUTION/PLAN.md`:
- Update Phase 6 deliverables table with current status
- If any task moved from pending → complete, mark it

**Do not hand-edit the `**Last reviewed** chain here (either tier)** — same generated mechanism as Steps 2/3, archiving to `PLAN_ARCHIVE.md`.

**[MICRO: skip entirely unless a deliverable's status actually moved this session — set `plan_deliverable_moved: yes` in the SESSION_HANDOFF meta block if so. The chain bump still happens via Step 6 regardless.]**

## Step 5 — Commit Message Draft

Provide a concise git commit message in this format:
```
[PHASE6] Brief description of main work done

- T-NNN: specific change
- T-NNN: specific change
- Tests: NNN/NNN passing
- Gate: [unchanged / CLOSED / OPENED]
```

## Step 6 — Create SESSION_HANDOFF File, Then Generate Everything Else From It

```bash
scripts/session_end_timer.sh check   # before writing SESSION_HANDOFF — the other expensive artifact
```

Create `11_MEMORY_HANDOFF/SESSION_HANDOFF_YYYYMMDD_HHMM.md` from `00_ADMIN/TEMPLATES/TEMPLATE_SESSION_HANDOFF.md`. Word-check it the same way as the DECISION_LOG entry above once written: `scripts/session_end_timer.sh wordcheck SESSION_HANDOFF 300 < <path>`.

**Fill in the `<!-- session-meta -->` block at the top first.** This is the single source of truth the generator (below) reads — get `one_line_summary` right, since it is reused verbatim in every generated artifact. `commit:` is a reference point, not a cryptographic pointer — use the current `git rev-parse --short HEAD` at authoring time (the last real commit already on this branch); it does not need to be the exact final SHA that will include this handoff file itself.

The rest of the file MUST include:
- **Strategic Decisions This Session** table (from Step 1A) — mandatory even if empty
- Current paper bet count vs G6 gate (**30 bets** — APR-0016; NOT 50)
- One-thing-pending (single most important next action)
- Resume command for next session

**[MICRO: still write the file (a resume pointer is not optional — GG-101/GG-082 need it, and the checkpoint pointer depends on it existing), but condense it to: the `session-meta` block, the Strategic Decisions table (still mandatory even if "None"), 2-4 lines of what changed (from Step 1B), one-thing-pending, and the resume command. Skip the bet-count line and any section the template has that doesn't apply to a doc-only session.]**

### Step 6-gen — Run the generator (both tiers, mandatory)

Once every substantive edit from Steps 1A–4 is done and the SESSION_HANDOFF's `session-meta` block is filled in, run:

```bash
python3 scripts/generate_session_artifacts.py 11_MEMORY_HANDOFF/SESSION_HANDOFF_YYYYMMDD_HHMM.md
```

Run this **after** Steps 2–4's substantive content edits (it reads TODO_NEXT/MEMORY_BANK/PLAN fresh — Hard Rule 10) and **before** the commit in Step 8. In one call it:
1. Collapses the `**Last reviewed** chain in all three of TODO_NEXT.md / MEMORY_BANK.md / PLAN.md to one current-status line, archiving the full prior chain verbatim to the matching `*_ARCHIVE.md` (ADR-0044) — both tiers.
2. Appends the SESSION_CLAIMS.md closure row — both tiers (previously had no dedicated step and was routinely skipped).
3. Appends a one-line Operator Digest entry to `11_MEMORY_HANDOFF/OPERATOR_DIGEST_YYYYMMDD.md` — **MICRO only**. STANDARD sessions get nothing here from the generator; write the prose digest by hand in Step 6B as before.
4. Writes the checkpoint pointer via `scripts/write_session_checkpoint.sh` (ADR-0041; format per GG-103, append-only `checkpoint<TAB>timestamp<TAB>slug` row) — both tiers, replacing the old separate manual call. This is what lets the *next* session's `/session-start` use `scripts/session_delta.sh` instead of a full read — skipping this step silently degrades the next session to the full-read fallback.

The script writes files but does not commit — review its diff (`git status` / `git diff`) before Step 8's commit, same as any other generated content. If it errors (e.g. missing `session-meta` block), fix the block and re-run — do not fall back to hand-authoring the collapse/closure/checkpoint just to route around an error.

**GG-186/T-462 — the closure row this writes is truth-checked, not assumed.** Item 2's SESSION_CLAIMS.md row asserts live whether `HEAD` is currently an ancestor of `origin/main` (`git merge-base --is-ancestor`) and writes "CLOSED" only if so — otherwise it writes "MERGED: NO — branch `<name>` awaiting merge". Since Step 6-gen runs *before* Step 8's push+merge, on the STANDARD path this row will correctly read "MERGED: NO" at this point — that is expected, not an error. Step 8 below is what turns it into a true "CLOSED".

## Step 6B — Operator Digest (mandatory, T-372)

**Vision pillar (2026-10-09):** fill `vision_pillar:` in the session-meta block (BREADTH / DEPTH / EXECUTION / PROOF / PLUMBING, per CLAUDE.md § "What winning looks like — the operator's north star (four pillars)"), and say it in the digest in plain words — which part of the operator's north star this session moved, or "plumbing".

**[MICRO: already done — Step 6-gen appended a one-line entry to `11_MEMORY_HANDOFF/OPERATOR_DIGEST_YYYYMMDD.md` from the `session-meta` block's `one_line_summary`. Do not also hand-author a prose digest on top of it; the one-liner is the MICRO-tier digest.]**

STANDARD: Create/append `11_MEMORY_HANDOFF/OPERATOR_DIGEST_YYYYMMDD.md` from `00_ADMIN/TEMPLATES/TEMPLATE_OPERATOR_DIGEST.md`, filled in for this session, and commit it in the same path-scoped commit as the SESSION_HANDOFF. This is not optional and not conditional on session size — a session with nothing to report still writes the digest and says so plainly (e.g. "No change today — still zero real money at risk"). Use `11_MEMORY_HANDOFF/OPERATOR_DIGEST_20260715.md` as the worked example of tone and length — plain English, no file paths/function names/p-values, 5-10 lines total.

**Why this is its own step, not folded into Step 6:** `SESSION_HANDOFF_*.md` is the technical record for the next session/auditor. The digest is a *different document for a different reader* — Earl, who does not read code and should not have to open a technical log to know what happened. A STANDARD session (real `src/` change, a strategic decision, or a GG/ADR event) still earns a hand-authored paragraph explaining it in plain English; a MICRO session's generated one-liner is sufficient because there's nothing behind it that needs explaining to a non-engineer.

Keep it to 5-10 lines per the template's own instruction — if it's running longer, the session did too much to summarize well, not a reason to write more.

## Step 7 — Next Session Primer

**[MICRO: skip — the `session-meta` block's `one_line_summary`, plus the condensed SESSION_HANDOFF's one-thing-pending and resume command (Step 6), already say where to pick up. A separate primer paragraph would just restate them.]**

STANDARD: In 2-3 sentences, what should the next session's opening prompt contain?

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

**Step 8-confirm (mandatory, GG-186/T-462) — after the merge lands, close the gap Step 6-gen's row left open.** Step 6-gen ran *before* this merge, so the closure row it wrote reads "MERGED: NO — branch `<name>` awaiting merge" (see the Step 6-gen note above) — that row is now stale-in-the-good-direction, not wrong, but it is not yet "CLOSED" either. Once the merge above is confirmed landed, run the same assertion again and append the confirming row:

```bash
scripts/session_end_timer.sh merge-check
```

Then write the closure row with the script — **not by hand, and not onto your own branch**:

```bash
scripts/close_session_claim.sh "<TASK_ID>" "<one-line summary>"
```

It re-runs the ancestor assertion itself, writes `CLOSED` only if HEAD is on `origin/main` and an honest `MERGED: NO — branch <name> awaiting merge` otherwise, commits that row **alone**, and pushes it **straight to `origin/main`** with rebase-retry — the same mechanism `scripts/claim_session.sh` has always used at claim time (`SESSION_CLAIMS.md` is `merge=union`, so concurrent rows auto-merge). Never edit an earlier row; the file is append-only.

**Why the row goes to `main` directly instead of riding your branch (2026-09-17).** Step 6-gen appends its row to `SESSION_CLAIMS.md` *on the session branch*. When the branch never merges, that row never reaches `origin/main` — so the row whose entire job is to make an unmerged branch visible is itself trapped on the unmerged branch, and the next session's claims scan sees nothing. That is not hypothetical: **T-545, T-547 and T-551 all finished, pushed, and wrote closure rows, and `origin/main` showed no row for any of them.** Claim rows always reached `main` because `claim_session.sh` pushes them there directly; closure rows never did. This closes that asymmetry.

If the script exits nonzero, the row is committed locally but did **not** reach `origin/main` — say so to the operator explicitly. Do not end the session claiming it landed.

A `MERGED: NO` row is not a failure state to hide from — it is the honest current state, and it is now *visible to everyone* rather than buried on a branch nobody merged. If the merge genuinely cannot happen this session, pair it with Step 8.5's T-NNN.

This is what makes "closed" and "on origin/main" the same fact instead of two facts that can silently drift apart — the failure mode observed four times (T-456 x2, T-458, T-460, see GG-186): a window writes a closure row from local `HEAD` state and ends the session without ever checking that `HEAD` reached `origin/main`. With this step, a window physically cannot produce a "CLOSED" row without the live assertion backing it, and a window that skips this step leaves a "MERGED: NO" row instead — visible to the next session's Step 0c scan and to any audit, rather than a false "CLOSED".

**Exit check:** `git branch -a` should show no session branch that is both unpushed-or-unmerged AND unaccounted-for in the handoff. Additionally: the *last* SESSION_CLAIMS.md row for this session's task ID must read "CLOSED" with a passing `merge-check`, never "MERGED: NO" left as the final word without an accompanying T-NNN follow-up per Step 8.5.

---

## Step 9 — Stray-branch sweep (mandatory, untiered — the last thing you run)

```bash
scripts/sweep_stray_branches.sh 14
```

Fetches, then reports every session branch on `origin` that is not an ancestor of `origin/main`. Two seconds; it fits the budget.

**Read the output against exactly two questions:**

1. **Is one of them mine?** Then Step 8 is not finished. Go back and land it. A branch you pushed but did not merge is the single most common way this project creates work for the next session.
2. **Are any of them somebody else's?** Then name them — branch, commit count, age — in the SESSION_HANDOFF and in one plain line of the operator digest. **Do not merge them.** A stray branch is the operator's routing decision; it becomes a Deliverable 0 in a queue block, sized and claimed like any other work. Landing someone else's branch turns one session into three (Hard Rule 11) and is exactly the cleanup burden this step exists to surface rather than silently absorb.

**Two read-it-right caveats, both real:**
- The script says loudly if it could not fetch. A `NOT LANDED` call against a stale ref can be false; a `LANDED` call cannot. Never write "did not land" off a stale ref — write "not visible at ref `<SHA>`, which may be stale."
- A branch whose content landed under different SHAs (rebase, cherry-pick, squash-merge) still reads `NOT LANDED`. Before flagging one, check whether its GG/T is already resolved on `main` — `origin/session/20260915T003401Z-nfl-capture-gap-0912` is a live example: content merged, GG-276 RESOLVED, branch ref still reads unlanded forever.

This step reports; it never merges, never deletes, and always exits 0. It cannot fail your close-out — it can only tell you the truth about what you are leaving behind.

---

## Quick Reference — File Paths to Update Every Session

```
                                                HAND-AUTHORED (both tiers unless noted)          GENERATED (Step 6-gen, both tiers)
11_MEMORY_HANDOFF/SESSION_HANDOFF_[date].md    always — the single source of truth (session-meta) —
11_MEMORY_HANDOFF/MEMORY_BANK.md               STANDARD: snapshot/health fields, if changed        "Last reviewed" chain -> MEMORY_BANK_ARCHIVE.md
04_EXECUTION/TODO_NEXT.md                      STANDARD: task completions/additions, if any        "Last reviewed" chain -> TODO_NEXT_ARCHIVE.md
04_EXECUTION/PLAN.md                           STANDARD: deliverable status, if moved              "Last reviewed" chain -> PLAN_ARCHIVE.md
03_DECISIONS/DECISION_LOG/DECISION_LOG.md      if any strategic decision was made (Step 1A)         —
00_ADMIN/APPROVALS_REGISTER.md                 if any threshold/gate/governance change              —
00_ADMIN/CHANGELOG.md                          for significant changes                              —
04_EXECUTION/SESSION_CLAIMS.md (closure row)   —                                                     always
04_EXECUTION/.last_session_checkpoint          —                                                     always
11_MEMORY_HANDOFF/OPERATOR_DIGEST_[date].md    STANDARD: prose digest, Step 6B                       MICRO only: one-liner
```

**Closure row and stray sweep (Steps 8-confirm and 9) are untiered and script-driven — `scripts/close_session_claim.sh` and `scripts/sweep_stray_branches.sh`. Neither is hand-authored and neither counts against the write budget.**

MICRO tier's total model-authored write count: DECISION_LOG row (only if Step 1A found a real decision), the SESSION_HANDOFF file, and the commit — **≤3**. Everything in the GENERATED column runs regardless of tier via one Step 6-gen call.

**Project-state snapshot (Wave 47 / 47.1 D6 i) — one script call, generated, not hand-authored, no write budget:** `python3 scripts/generate_project_state.py --html "<shared tree root>/Visual Dashboard.html"` rewrites the static offline "Visual Dashboard.html" stamped with origin/main's sha and generation time. The live `/project` page regenerates from the VPS checkout on request (cached ≤1 min).

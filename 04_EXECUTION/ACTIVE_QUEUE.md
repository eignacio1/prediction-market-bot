# Active queue — the only prompt file to read

**Verified against `origin/main` = `013c8dd`, 2026-09-04.** Cell registry: **78 cells — 1 ACTIVE, 2 BLOCKED, 1 DARK, 74 NOT_IMPLEMENTED**. Gap log: **74 OPEN**, 94 entries, parity **94 = 94**. `logic_epoch.py` carries **12 boundaries, now cell-keyed** (ADR-0054(b) landed).
**Free IDs (a hint, not an assignment):** T-515+ · GG-239+ · ADR-0063+ · APR-0034+ · EXP-026+

> **⚠ THE QUEUE DOES NOT RESERVE IDs.** GG-234 and GG-236: a block was assigned IDs already consumed, and `claim_session.sh`'s collision check **cannot see numbers registered on an unlanded branch** — which is the mechanism behind every GG-162 collision this phase. **Claim your own IDs at run time; re-derive the live max across the gap log, its archive, AND `git log --all`; write your gap-log entry as your first commit and push it immediately.** A number is claimed when it is pushed, not when it is read.

> **⚠ THE STRATEGIC WINDOW CANNOT SEE PAST THE LAST FETCH.** Cowork has no network on the device VM, so `origin/main` above is only as fresh as the last terminal's fetch. **Every gated block below runs `git fetch` first and verifies the record itself.** Do not take this file's header as current — verify it.

---

## Read this first

**Prompt blocks below are the paste-in. Nothing else in this file is a task.**

**DELIVERABLE 0 IN EVERY BLOCK: land any un-landed predecessor before starting your own work.**

**PUSH AFTER EACH DELIVERABLE, NOT AT CLOSE-OUT.** Four waves running, a block has ended at budget with completed work unpushed. A pushed commit survives budget exhaustion.

**Ancestor check direction:** `git merge-base --is-ancestor <your-branch-tip> origin/main`. Paste the exit code.

**When verifying a code fix, import and call the real function.** Never re-implement its logic in a harness.

**Never repair a file a running service owns, or one another process regenerates, without coordinating both** (GG-224, GG-228).

**If a document's own text contradicts what a prompt says it says, STOP and report. Do not reconcile it yourself.**

---

## Sequencing track

| Wave | Closed | Outcome |
|---|---|---|
| 4–9 | 08-26 | Nineteen blocks. GG-203 found; fill haircuts measured; NFR-03 measured failing; ruin geometry; four ADRs signed |
| 10 | 08-29 | NB refit **−0.0048 / n\* 44,220**, INCONCLUSIVE again. 46/46 stuck-open repaired; **GG-224 found** |
| 11 | 09-01 | **532+76 repaired, durability proven**, invariants **630 → 22**, cross-path **52.0%/68.4% → 100%/100%**; **GG-228 found** |
| 12 | 09-02 | Registry **68 → 78**. **n\* 560 → 18,058, P&L/bet +0.2518 → +0.0191** |
| 13 | 09-03 | ADR-0062 drafted; T-506 remainder landed; `NEVER` residual closed |

### ⚠️ WAVE 14 — CLOSED 2026-09-04 · two landed, one blocked at the merge

| # | Block | Status | Outcome |
|---|---|---|---|
| 14.1 | T-512 · record the six sign-offs | ⚠️ **NOT MERGED — PR #126** | Work complete and correct: ADR-0060/0061/0062 flipped PROPOSED→ACCEPTED, APR-0033 PENDING→ACCEPTED, both decision records written, BOUNDARY conflict recorded unresolved as instructed, parity CLEAN both sides of its rebase. **`gh pr merge`, `gh pr merge --admin` and a direct push all refused by the Claude Code auto-mode permission classifier.** Wrote `MERGED: NO`, not a false CLOSED |
| 14.2 | T-514 · landing and hygiene | ✅ **merged** | **Landed T-509** (all three ADR-0054(a) items). Installed the queue. Fixed GG-235's stale VPS filenames; registered **GG-238**. Supplied T-511's missing closure row |
| B.1 | T-513 · ADR-0054 (b) re-key | ✅ **merged** | `LogicEpochBoundary.bands_affected` now cell-keyed, 12 boundaries. Hit the predicted GG collision → renumbered to **GG-237** |

**Nothing regressed:** 78 cells, 12 boundaries, parity 94 = 94, re-derived from the ref 2026-09-04.

### ⬜ WAVE 15 — THE INTEGRATION WAVE · fire 3-wide · **every block self-gates on PR #126**

The strategic window cannot confirm whether PR #126 landed — no network, so its `origin/main` is stale by construction. **Each block therefore fetches and checks the record itself, and stops cheaply if the sign-offs are not there.** That is deliberate: it removes a fact I cannot verify from the critical path.

| # | Task | Gated |
|---|---|---|
| 15.1 | Install this queue (ungated) · **ADR-0062 build** — `T4NFL_*`/`T4NHL_*` members + cells | yes, after install |
| 15.2 | ADR-0061 — the (c) runbook, the (b) lock contract, the (a) diagnostic | yes |
| 15.3 | APR-0033 — re-scope Phase 2 to moneyline-first and **pre-register** the new hypothesis | yes |

### ⬜ BANDWIDTH SLOT — capital-inert, ungated, fires no matter what PR #126 does

| # | Task |
|---|---|
| B.2 | **GG-236 + GG-238** — teach `claim_session.sh` to see unlanded branches; fix `assert_ledger_invariants.py`'s stale default paths |

### 🔒 WAVE 16 — THE HALT ARCHITECTURE · after Wave 15 · prompts written when 15 closes

| # | Task |
|---|---|
| 16.1 | **Halt-hierarchy ADR draft** — align halt granularity to sizing granularity across all five tiers (full book `MAX_PORTFOLIO_DEPLOYMENT_PCT=0.60` → band → 11 T4 segments at 8 distinct Kelly regimes → cell `halt_cell()` built-and-unwired → per-bet `$1.00`/10-contract/`$0.10` bounds). Absorbs GG-038 TASK 2/3. **Must not re-open ADR-0060's accepted (c) or its deferral** |
| 16.2 | **G6 standard amendment ADR draft** — encodes the accepted pre-registration + multiplicity-correction conditions into ADR-0057's closure condition |

### 🔒 WAVE 17 — GATED ON GG-203

| 17.1 | Wire the nine ADR-0058 T1 cells live behind `measurement_stake.py`. **Pre-register the expectation of negative net edge** (T-494) |

---

# 15.1 — INSTALL THE QUEUE, THEN BUILD THE NFL/NHL SUB-BANDS

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "adr0062-nfl-nhl-subband-build"
Claim your own T- and GG- numbers at run time. Re-derive the live max across GOVERNANCE_GAP_LOG.md,
its archive, AND `git log --all` -- claim_session.sh cannot see unlanded branches (GG-236). Write your
gap-log entry as your FIRST commit and push it before deliverable work.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

DELIVERABLE 0 -- INSTALL THE QUEUE. UNCONDITIONAL. Do this before the gate, and push it, so it lands
even if the gate stops you.
  origin/main's ACTIVE_QUEUE.md is stale -- its header still reads `db739af` and it still carries the
  Wave 14 prompt blocks. Copy the current file from the shared main checkout at
  04_EXECUTION/ACTIVE_QUEUE.md into your worktree, commit, push.
  Confirm exactly one: `find . -name "ACTIVE_QUEUE*.md" -not -path "./.git/*"`.

*** GATE -- RUN THIS BEFORE ANY BUILD WORK ***
  git fetch origin && git log --oneline -1 origin/main
  Then read, from origin/main (not from this prompt, not from the working tree):
    03_DECISIONS/ADR-0062*  -- its Status line
    00_ADMIN/APPROVALS_REGISTER.md -- its ADR-0062 row
  **ADR-0062's Status must read ACCEPTED.** T-512 recorded the sign-off on branch
  `session/20260903T002904Z-record-signoffs-20260903` (PR #126); the Claude Code permission classifier
  refused every merge route it tried.
  If ACCEPTED: proceed.
  If still PROPOSED: **STOP. Do not build. Do not attempt the merge yourself -- three routes were
  already tried and refused.** Report that the gate failed, confirm Deliverable 0 landed, and hand back.
  This is not a failure of your block; it is the correct outcome when authority is not in the record.

TIER: STANDARD. ONE deliverable after the gate: registry + band scaffolding. **NO behaviour change.**

READ FIRST, in full: 03_DECISIONS/ADR-0062, especially SS3 (names), SS4 (roster) and SS6 (projection).
Also read how MLB's existing T4M_* members are declared in execution_bands.py -- you are extending an
existing convention, not inventing one.

*** THE BOUNDARY CONFLICT -- RESOLVE IT FIRST AND REPORT YOUR READING ***
ADR-0062 SS4 calls BOUNDARY "propose, scoped only, not authorized to build," mirroring MLB's own
T4M-BOUNDARY posture. **MLB has no T4M_BOUNDARY member -- verify that yourself against
execution_bands.py.** But SS6's 21-cell projection counts BOUNDARY as one of three sub-bands.
Those cannot both be right. T-512 recorded the conflict unresolved at signature and routed it here.
  **DEFAULT TO THE CONSERVATIVE READING unless you find evidence against it: build ARITH and FLOW
  only.** Rationale: SS4 is the roster decision and SS6 is an arithmetic projection; a projection
  cannot authorize what the roster declined, and MLB's precedent has no BOUNDARY member to mirror.
  That yields 2 sub-bands x 4 NFL families + 2 x 3 NHL families = **14 new cells, 78 -> 92**, not 21/99.
  State your reading, your evidence, and the resulting count explicitly. If you conclude otherwise,
  say why -- but do NOT build BOUNDARY members on SS6's arithmetic alone.
  Same test for the `T4NFL-FLOW-BLOWOUT` variant named in SS3: MLB has T4M_FLOW and no separate
  blowout member. Do not create one unless MLB has one.

EXCLUDED BY THE SIGNATURE: **EVENT, both sports.** ADR-0062 SS4 defers it pending verification of each
sport's C1 ingestion mechanism (push vs poll), and the acceptance did not override that. Do not create
T4NFL_EVENT or T4NHL_EVENT. If you want to close that question, the ingestion check is a separate block.

BUILD:
  - Add the ExecutionBand members following MLB's exact declaration pattern. ADR-0056's accepted
    convention is the four-letter sport code (`T4NFL-`/`T4NHL-`, NOT `T4N-` -- that was superseded, see
    GG-233). Derive the Python identifier form from how T4M_* does it; do not guess at hyphens vs
    underscores.
  - Add the cells: NFL_MONEYLINE, NFL_SPREAD, NFL_GAME_TOTAL, NFL_TEAM_TOTAL x each built sub-band;
    NHL_MONEYLINE, NHL_PUCK_LINE, NHL_GAME_TOTAL x each built sub-band.
  - **Every new cell NOT_IMPLEMENTED. Every new member kelly_fraction=0.0. Nothing wired, nothing
    promoted.** T-495's NHL seeding and T-504's MLB extension are the precedents for scope.

**HARD STOP:** if this requires anything beyond registry + band scaffolding -- a ledger schema change,
a kill-switch change, a c4_risk_engine change, a new correlation group, or any ADR-0053 SS6.3 delta item
-- STOP and report. ADR-0062's acceptance does not authorize the delta.

VERIFY: live-import the registry and report before/after cell count and full status breakdown. Do not
restate a number from any document. Full suite green; paste the pass/fail/skip line.

DO NOT: touch any kelly_fraction value other than setting 0.0 on new members. DO NOT: promote any cell.
DO NOT: wire anything live. DO NOT: edit logic_epoch.py -- ADR-0054(b) landed and boundaries are
cell-keyed now; new cells inherit ADR-0062 SS5's fresh epoch-1 per sport, which needs no boundary edit.
DO NOT: build EVENT or BOUNDARY.

SCOPE FENCE: src/prediction_market_bot/execution_bands.py,
src/prediction_market_bot/c5_execution/market_type_registry.py, their tests,
04_EXECUTION/ACTIVE_QUEUE.md (Deliverable 0 only).
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate result (ADR-0062's Status line as read from origin/main, verbatim); the queue
install confirmation; your BOUNDARY reading with evidence and the resulting cell count; the exact
member names created; live-imported before/after counts and status breakdown; the suite line; the
ancestor-check exit code.
```

# 15.2 — ADR-0061 · THE REPAIR-SAFETY RUNBOOK, CONTRACT, AND DIAGNOSTIC

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "adr0061-repair-safety"
Claim your own IDs at run time (GG-236). Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

*** GATE *** `git fetch origin`, then read 03_DECISIONS/ADR-0061*'s Status line FROM origin/main.
  **It must read ACCEPTED.** If still PROPOSED: STOP, report, hand back. Do not attempt the PR #126
  merge -- three routes were already tried and refused by the permission classifier.

TIER: STANDARD. THREE deliverables. READ ADR-0061 IN FULL first -- especially SS2's enumeration and
SS7's recommendation. The accepted combination is: (c) NOW, (b) as complement, (a)'s DIAGNOSTIC half
staffed, (d) NOT adopted.

DELIVERABLE 1 -- OPTION (c): WRITE THE RUNBOOK. A new operational document: the stop-repair-start
procedure for any external repair to a service-owned ledger file. ADR-0061 SS2 enumerated exactly TWO
in-scope processes -- `t4-mlb.service` (run_t4_mlb_live.py, live) and NBA's `run_t4_live.py`
(cron + `timeout 21600`, currently dormant because NBA is dark). Cover both. The procedure is: stop the
owning service, repair the now-static file, verify, restart, then verify durability across at least one
flush interval. **Record that the operator granted a scoped restart pre-authorization on 2026-08-29 and
that it is proof the procedure works when followed, NOT proof it will be followed** (ADR-0061 SS5).

DELIVERABLE 2 -- OPTION (b): STATE THE LOCK CONTRACT. Any external repair script must acquire the same
`fcntl` lock `PaperTrader._file_lock()` already takes before reading, backing up, or writing the target.
The lock file already exists per portfolio path. Write the contract, and add the shared helper in
scripts/lib/ that wraps acquire-read-verify-write-release so repair authors do not hand-roll fcntl.
**A lint-style check that any script writing paper_portfolio*.json calls the helper is in scope and
cheap; a full enforcement mechanism is not.**

DELIVERABLE 3 -- OPTION (a), DIAGNOSTIC HALF ONLY. This is the one that matters most and it is
investigation, not a fix.
  ADR-0061 SS2 found something GG-224's own record does not say: `PaperTrader`'s five mutation methods
  (open_position, exit_position, resolve_pending, settle_position, mark_aged_open) ALREADY wrap every
  mutation in `with self._lock, self._file_lock(): self._reload_locked(); ... ; self._save()` -- an
  exclusive fcntl lock plus a fresh disk re-read immediately before saving, added under GG-034.
  **The T-502 clobber happened anyway, at a flush cadence consistent with open_position() firing.**
  So "no reload exists" is NOT the explanation. Find what is.
  Reproduce it on a NON-PRODUCTION COPY of the portfolio file. **Do not repair, write to, or restart
  anything in production under this block** -- the 2026-08-29 restart pre-authorization was scoped to
  the 11.1 repair and does not extend here.
  Report the mechanism you find, or report plainly that you could not reproduce it and what you ruled
  out. **A negative result stated clearly is a real deliverable here.**
  Why this matters beyond GG-224: the same lock/reload pattern is what GG-034's bankroll-drift fix
  relies on. If it does not hold, that is a second, unregistered exposure.

DO NOT: close GG-224 -- ADR-0061 SS5 is explicit that a runbook is not a structural guarantee.
DO NOT: implement option (a)'s fix half, or option (d), or edit run_t4_mlb_live.py / paper_trader.py.
DO NOT: touch any kelly_fraction, cell status, or production ledger row.

SCOPE FENCE: a new runbook document, scripts/lib/ (helper + optional lint check), a non-production
diagnostic script under scripts/, gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate result verbatim; the runbook's path and the two services it covers; the helper's
path and whether you added the lint check; and for Deliverable 3 -- the mechanism you found, or exactly
what you ruled out and why you could not reproduce it. Say which of the two it is.
```

# 15.3 — APR-0033 · RE-SCOPE PHASE 2 TO MONEYLINE-FIRST

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "apr0033-phase2-moneyline-reroute"
Claim your own IDs at run time (GG-236). Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

*** GATE *** `git fetch origin`, then read APR-0033's row in 00_ADMIN/APPROVALS_REGISTER.md FROM
  origin/main. **It must read ACCEPTED, not PENDING.** If PENDING: STOP, report, hand back.

TIER: STANDARD. TWO deliverables. **You are NOT fitting a model this session.** Read that twice --
LL-009 is a standing rule created by this exact project after ~3-5 hours of stranded build:
"confirm hypothesis with minimal experiment before building supporting component." The pre-registration
comes first and it comes alone.

CONTEXT, verify it yourself rather than trusting this summary: MARKET_EXPANSION_ACTION_PLAN.md's
"Note on model class" states that a falsified 2.3 reroutes to moneyline-first, because moneyline is a
binary target where LR (the production class, ADR-0004) applies directly and needs no distribution fit.
Box 2.3 returned INCONCLUSIVE twice -- Poisson (T-487) and NB (T-500/EXP-025), both with negative point
estimates below HYP-010's pre-registered +0.005 to +0.025 band. The operator accepted firing the reroute.

DELIVERABLE 1 -- RE-SCOPE THE PLAN. Update MARKET_EXPANSION_ACTION_PLAN.md's Phase 2 boxes 2.4 through
2.8 to describe the moneyline-first LR track instead of the team-total distribution-fit track.
  **Box 2.3's INCONCLUSIVE verdict stays EXACTLY as recorded and is NOT relabelled.** Both verdicts
  (Poisson and NB) stay in the record verbatim. What changes is what comes after them.
  **Phase 2 is not terminated.** Record that the reroute is the plan's own defined response, not an
  abandonment, and cite APR-0033's acceptance date.

DELIVERABLE 2 -- PRE-REGISTER THE NEW HYPOTHESIS, AND STOP THERE.
  Register a new HYP-0NN for the moneyline LR track. Take the next free HYP number -- re-derive it.
  The pre-registration must fix, IN ADVANCE and before any modelling code exists:
    (a) the model class -- LR per ADR-0004, and state explicitly that no distribution fit is involved;
    (b) the data source and the archive window it will score against (the price archive is running --
        `deploy/cron.conf:347-348` -- and KXMLBGAME is one of the families it captures; verify);
    (c) the selected-subset rule, stated as a number, not "we will decide later";
    (d) the primary metric -- P&L/bet on the selected subset -- powered via APR-0024's variance-derived
        n* (scripts/run_power_calc.py). Brier is DESCRIPTIVE SECONDARY ONLY, never a gate;
    (e) the three verdict states with the same definitions the project already uses:
        PASS / FALSIFIED / INCONCLUSIVE-EXTEND-ARCHIVE. Do not invent a fourth;
    (f) a pre-registered effect band, and a "results above X are suspect, audit for leakage" line --
        HYP-010 used +0.03 for that;
    (g) **an explicit note that the fill haircut consumed 65% of gross edge on T4M-PROJ (0.0540 ->
        0.0191, T-507), so this gate is scored NET of fill cost or it is not scored at all.** That is
        the single most important lesson available to this hypothesis and it must be in the design,
        not discovered afterwards.
  Commit the pre-registration. **Then stop. Do not fit. Do not score. Do not write backtest code.**

DO NOT: relabel box 2.3's verdict. DO NOT: touch any kelly_fraction or cell status. DO NOT: kill or
modify the price-archive cron -- it feeds T-488 and T-494, not just Phase 2. DO NOT: run the experiment.

SCOPE FENCE: 04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md, 05_RESEARCH_EXPERIMENTS/ (HYPOTHESES.md +
the new pre-registration file), gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate result verbatim; which plan boxes you re-scoped and their new text; the new HYP
number and the pre-registration's path and commit SHA; confirmation that box 2.3's verdict is unchanged;
and explicit confirmation that no model was fit this session.
```

# B.2 — GG-236 + GG-238 · FIX THE TWO INSTRUMENTS  *(ungated — fires regardless of PR #126)*

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "gg236-gg238-instrument-fixes"
Claim your own IDs at run time. Gap-log entry as your FIRST pushed commit -- and note the irony: this
block exists because that step is currently unreliable.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

NO GATE. Both items are capital-inert -- no kelly_fraction, no cell status, no ledger row, no live
pipeline. This block runs whether or not PR #126 has landed.

DELIVERABLE 1 -- GG-236. `claim_session.sh`'s GG-number collision check cannot see numbers registered
on an unlanded branch. **This is the mechanism behind every GG-162 collision this phase.** It predicted
T-513's collision in advance and T-513 hit it anyway (GG-237). The strategic window's workaround is a
process rule ("re-derive across `git log --all`"); the fix is teaching the script to look there.
  Extend the check to scan unlanded branches -- `git log --all` over the gap-log path, or an equivalent
  that catches an entry existing only on a session branch.
  **Add a regression test that FAILS on the old behaviour**: a GG number present only on an unmerged
  branch must be reported as taken. A fix with no test that pins the old failure is how this returns.
  Amend GG-236 with the resolution. Cross-reference GG-162 and GG-237.

DELIVERABLE 2 -- GG-238. `scripts/assert_ledger_invariants.py`'s own default CLI argument paths are
stale, the same way GG-235's documented VPS-fetch commands were (T-514 fixed those).
  Fix the defaults against the real current filenames. **Verify each against the actual repo or the
  actual VPS -- do not infer a rename.** If you cannot verify one, leave it flagged and say so.
  Run the script before and after with no arguments and paste both results.

DO NOT: promote assert_ledger_invariants.py to --strict -- alarm-only is a standing operator decision.
DO NOT: change any assertion's logic or thresholds; this is a path fix, not a semantics fix.
DO NOT: touch any kelly_fraction, cell status, or ledger row.

SCOPE FENCE: scripts/claim_session.sh, scripts/assert_ledger_invariants.py, their tests, gap-log +
DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the claim_session.sh change and the regression test that fails on the old behaviour;
assert_ledger_invariants.py's no-argument output before and after; which GG-238 paths you verified and
which you could not.
```

---

## Needs your decision

| # | Decision | Status |
|---|---|---|
| (0) | **PR #126.** T-512's sign-off recording is complete and correct on its branch. The Claude Code auto-mode permission classifier refused `gh pr merge`, `gh pr merge --admin`, and a direct push. **That is the agent's own permission layer, not a repo check — there is no repo policy being correctly enforced for a terminal to respect.** One merge from you unfreezes 15.1/15.2/15.3. **If you have already merged it, ignore this — the gates will find out and proceed.** | **GATES WAVE 15** |
| (i) | **GG-203 — Kalshi order-write fault.** Nothing accrues until it clears; gates Wave 17. Support ticket or demo-key regeneration. Still the highest-value item on the board and still not code. | **OPEN** |
| (ii) | **GG-038 TASK 2/3 — the kill switch does not halt T4.** `run_t4_mlb_live.py` treats a `KILL_SWITCH` approval identically to an ordinary `REJECTED`; `is_kill_switch_active` is read by zero MLB pipelines. No ADR-0060 remedy option touches either. Recommendation stands: staff it as its own ADR draft, folded into 16.1. Say the word and it becomes a Wave 16 block. | **OPEN** |

## DO NOT — standing

Don't unpark `SCALING_MANDATE_PARKED.md`. Don't promote `assert_ledger_invariants.py` to `--strict`. **Don't touch sizing or any `kelly_fraction` without an ADR.** Don't build ADR-0060's option (c) — accepted as target, deferred to the ADR-0048 reactivation trigger. Don't close GG-224 on ADR-0061's acceptance. Don't relabel box 2.3's INCONCLUSIVE verdict. Don't build EVENT or BOUNDARY members under ADR-0062. Don't adjudicate a decision request. Don't run a clean-vs-corrupted comparison without pre-registering it. Don't re-investigate GG-203 in-repo. Don't kill the price-archive cron. Don't repair a derived file: establish provenance first (GG-228). Don't work from the shared `main` checkout. Don't land red work to clear a backlog. **Don't recommend against a sport or a family on the strength of a finding — operator doctrine 2026-08-21, reaffirmed 2026-08-27.**

**Retired:** "Don't reopen T1." Superseded 2026-08-25.

# Active queue — the only prompt file to read

**Verified against `origin/main` = `db739af`, 2026-09-03.** Cell registry: **78 cells — 1 ACTIVE, 2 BLOCKED, 1 DARK, 74 NOT_IMPLEMENTED**. Gap log: **72 OPEN**, 89 entries, parity **89 = 89**, uniqueness CLEAN. `logic_epoch.py` carries **12 boundaries**. Register parity clean.
**Free IDs (a hint, not an assignment):** T-512+ · GG-236+ · ADR-0063+ · APR-0034+ · EXP-026+

> **⚠ THE QUEUE NO LONGER RESERVES IDs.** GG-234: a block was assigned `T-508 / GG-231` and **both IDs had already been consumed** between the queue being written and the block firing. **Blocks are named by wave coordinate only. Claim your own IDs at run time; write your gap-log entry as your first commit and push it immediately.** A number is claimed when it is pushed, not when it is read.

---

## Read this first

**Prompt blocks below are the paste-in. Nothing else in this file is a task.**

**DELIVERABLE 0 IN EVERY BLOCK: land any un-landed predecessor before starting your own work.** Three consecutive waves ended with a block whose work was complete, correct, and not on `origin/main`.

**PUSH AFTER EACH DELIVERABLE, NOT AT CLOSE-OUT.** T-504, T-506 and T-511 all burned their remaining budget at close-out; T-501 and T-511 wrote truncated stubs. A pushed commit survives budget exhaustion.

**Ancestor check direction:** `git merge-base --is-ancestor <your-branch-tip> origin/main`. Paste the exit code. The reversed form passes for any branch merely ahead of main.

**When verifying a code fix, import and call the real function.** Never re-implement its logic in a harness — the strategic window filed a false finding that way on 2026-09-01 and a deliverable was spent re-closing something already closed.

**Never repair a file a running service owns, or one another process regenerates, without coordinating both** (GG-224, GG-228). Establish provenance before choosing a repair target.

**If an ADR's own text contradicts what a prompt says it says, STOP and report. Do not reconcile it yourself.**

---

## OPERATOR SIGN-OFF — 2026-09-03

**Earl accepted four recommendations in-session on 2026-09-03**, same pre-granted pattern as ADR-0050 and ADR-0059. 14.1 records these formally; **no other block may act on them until 14.1 has landed.** Recorded here verbatim so a block can check its own authority:

- **ADR-0062 — ACCEPTED as written.** D1 naming (`T4NFL-*`/`T4NHL-*`, four-letter convention per ADR-0056 Amendment (iii)), D2 roster, D3 fresh epoch-1 per sport, D4 projection. Authorizes the scaffolding build. **EVENT remains deferred pending ingestion verification. See the BOUNDARY conflict in 15.1 before building anything.**
- **ADR-0060 — option (c) ACCEPTED as the TARGET ARCHITECTURE, implementation DEFERRED.** This is the ADR's own §5 recommendation, not a mandate to build. **Trigger: (c) is scoped and authorized when T4M-PROJ's `kelly_fraction` is next considered for edge-conditional reactivation under ADR-0048.** Current exposure is zero, so there is no operational urgency. **No NFR-03 build is authorized now.** (a) and (b) are not adopted.
- **ADR-0061 — ACCEPTED per its §7:** option **(c)** (stop-repair-start runbook) adopted **now**; option **(b)** (repair scripts must take the existing `fcntl` lock) adopted as a complementary contract; option **(a)**'s **diagnostic half** staffed as a follow-on; option **(d)** **not adopted at this time**. **GG-224 stays OPEN** — a runbook is not a structural guarantee, per §5.
- **APR-0033 — ACCEPTED: fire the moneyline-first reroute.** Both the Poisson fit (T-487) and the NB refit built to correct its misspecification (T-500) returned negative point estimates below HYP-010's pre-registered +0.005…+0.025 band. **Box 2.3's INCONCLUSIVE verdict stays exactly as recorded and is NOT relabelled** — what changes is the routing, per the plan's own "Note on model class".

- **The `n*` standard — ACCEPTED: keep APR-0024 exactly as it is, no revision.** Rationale to record: revising a power standard after it returns an unwelcome number is indistinguishable from weakening a control to make a red measurement green. And it would not help — loosening power .95 → .80 cuts `n*` by ~43% to ≈10,300, still ~18× the 559 held. **The standard is correctly reporting that this band's post-cost edge is too small to validate.** Record the derived finding alongside it: the fill haircut consumed **65% of the gross edge** (0.0540 → 0.0191), so execution cost — not model quality — is what drives `n*` to 18,058.
- **Cells before live capital — ACCEPTED: keep "at least one," add two conditions.** (1) The candidate cell must be **pre-registered as a capital candidate before its cohort completes**, so it cannot be selected after the winner is visible. (2) Its significance threshold must be **corrected for the number of cells in contention** (Bonferroni over the pre-registered candidate set, which is why that set must stay small). Record the acknowledged cost: Bonferroni over five candidates moves α to .01 and **raises `n*` by a further ~46%**. This amends ADR-0057's closure condition and therefore **requires a superseding ADR before it binds** — recording the decision does not itself change the gate. That draft is 16.2.

**None of these six move capital or sizing.** Every `kelly_fraction` stays at 0.0; no cell is promoted; no live pipeline is wired. That is why they were safe to accept as a set.

---

## Where the build actually is

**Nothing has accrued for 19 days.** Last resolved bet remains `game_date` 2026-08-14. **GG-203 is still the only thing standing between this project and any evidence at all**, and it is not code. Compute elapsed days at cite time.

### What ADR-0060 actually recommends — I had been summarizing this wrong

I told you (c) "looks right" while disclaiming that I hadn't read T-498's cost analysis. I have now read ADR-0060 in full. **Its recommendation is (c) as the target architecture and explicitly NOT as the immediate action** — because with `kelly_fraction=0.0` under ADR-0048, every evaluation inside the measured latency gap carries zero live capital. The ADR sequences (c) to the moment sizing is reconsidered. My earlier framing would have staffed a build the ADR itself says not to start. It is recorded above as a deferral with a named trigger, which is what it is.

**ADR-0060 §6 also names three things none of the three options solve.** The sharpest: **`run_t4_mlb_live.py` treats a `KILL_SWITCH` approval status identically to an ordinary `REJECTED`, while T1 branches on it and self-halts** (GG-038 TASK 3). A kill switch that does not actually halt T4 bet submission is a different and arguably worse defect than the latency it was measured for, and no remedy option touches it. Also: `is_kill_switch_active` is read by **zero** MLB pipelines — the fast system-level switch is inert. **Neither is staffed. See decision (iii) below.**

### What ADR-0061 found that changes the shape of the problem

§2 traced the source and found that `PaperTrader`'s five mutation methods **already** wrap every mutation in `fcntl` file lock + fresh disk reload immediately before save — added under GG-034 for a different problem. **The GG-224 clobber happened anyway, on a path that already had the protection.** So GG-224's own conclusion ("no external safeguard can prevent this") is not the whole story: something more specific than "no reload exists" produced the revert, and **until that is diagnosed, the same lock/reload pattern cannot be trusted anywhere else it is used — including for GG-034's original bankroll-drift problem.** That is why the accepted decision staffs (a)'s diagnostic even though (c) is the operational answer.

### Wave 13 outcomes

**T-510** landed ADR-0062 and caught my briefing citing the superseded `T4N-` convention (GG-233) — the second briefing error I have shipped in three waves, both caught by terminals rather than by me. **T-511** landed the T-506 remainder and closed the `NEVER` residual; register parity is clean; then hit budget and wrote a truncated close-out stub (`db739af`). **T-509** completed all three ADR-0054(a) items — 925 insertions across 3 scripts and 4 test files, plus GG-232, GG-184 → PARTIALLY RESOLVED, GG-235 — and was still in session-end at the time of writing. Not failed; unfinished.

### A correction to my own Wave 13 sequencing

I moved ADR-0054 **(b)** out of Wave 13 arguing the cell set was still moving. **Wrong.** (b) re-keys the twelve *historical* boundaries, all of which predate NFL/NHL having any cell — ADR-0062's cells cannot appear in a boundary set from before they existed. It was runnable last wave. It is 14.3 now.

**Distance to live capital:** 1 of 78 cells ACTIVE · every live band at `kelly_fraction=0.0` · zero accrual since 08-15 · epoch-12 repaired and durable · **T4M-PROJ post-haircut clean_n 559 against n\* 18,058** · NFR-03 failing at p50 66.955s, remedy deferred by design · the kill switch not actually wired to halt T4 submission.

---

## Sequencing track

**Legend:** ✅ merged · ⚠️ complete but NOT merged · ⏳ in flight · ⬜ not started

| Wave | Closed | Outcome |
|---|---|---|
| 4–9 | 08-26 | Nineteen blocks, zero cells graduated. GG-203 found; fill haircuts measured; NFR-03 measured failing; ruin geometry; four ADRs signed |
| 10 | 08-29 | NB refit **−0.0048 / n\* 44,220**, INCONCLUSIVE again. GG-186 #6/#7 closed. 46/46 stuck-open repaired; **GG-224 found** |
| 11 | 09-01 | **532+76 repaired, durability proven**, invariants **630 → 22**, cross-path **52.0%/68.4% → 100%/100%**; **GG-228 found**. T-504 blocked at merge |
| 12 | 09-02 | Registry **68 → 78**. **T-507: n\* 560 → 18,058, P&L/bet +0.2518 → +0.0191** |
| 13 | 09-03 | ADR-0062 drafted; T-506 remainder landed; `NEVER` residual closed. **T-509's work complete, merge pending** |

### ⬜ WAVE 14 — RECORD THE SIGN-OFFS, LAND THE BACKLOG, RE-KEY THE BOUNDARIES · fire 3-wide

| # | Task | Surface |
|---|---|---|
| 14.1 | Record the four 2026-09-03 operator sign-offs | `00_ADMIN/`, ADR status lines |
| 14.2 | Land T-509 · install this queue · GG-235 · finish T-511's close-out | `04_EXECUTION/`, the T-509 merge, `11_MEMORY_HANDOFF/` |
| 14.3 | ADR-0054 **(b)** — twelve-boundary re-key | `src/.../logic_epoch.py` |

### 🔒 WAVE 15 — UNBLOCKED BY 14.1 · do not fire until 14.1 has landed · 3-wide

| # | Task |
|---|---|
| 15.1 | ADR-0062 build — `T4NFL-*`/`T4NHL-*` members + cells. **Resolve the §4-vs-§6 BOUNDARY conflict first** |
| 15.2 | ADR-0061 — write the (c) runbook, state the (b) lock contract, run the (a) diagnostic |
| 15.3 | APR-0033 — fire the Phase 2 moneyline-first reroute |

### 🔒 WAVE 16 — THE HALT ARCHITECTURE · fire after Wave 15 · 2-wide · prompts written when 15 closes

| # | Task | Why it is its own wave |
|---|---|---|
| 16.1 | **Draft the halt-hierarchy ADR** — align halt granularity to sizing granularity across all five tiers. Absorbs GG-038 TASK 2/3. Extends ADR-0060 rather than superseding it. Unblocks ADR-0054 **(d)** | The single largest unaddressed architectural gap on the board. Scope below |
| 16.2 | **Draft the G6 standard amendment ADR** — encodes the accepted pre-registration + multiplicity-correction conditions into ADR-0057's closure condition | The decision is accepted; the gate does not change until this ships |

### 🔒 WAVE 17 — GATED ON GG-203

| # | Task | Gate |
|---|---|---|
| 17.1 | Wire the nine ADR-0058 T1 cells live behind `measurement_stake.py`. **Pre-register the expectation of negative net edge** (T-494) | **GG-203 RESOLVED** |
| 17.2 | Build ADR-0060 (c) and ADR-0054 (d) under whatever hierarchy 16.1 establishes | **ADR-0048 kelly reactivation is considered** |

#### 16.1 scope — recorded now so the framing is not lost

**Operator directive, 2026-09-03: a kill switch is meaningless unless it is tied to the Kelly alignment of the thing it halts.** Sizing in this system is decided at five distinct granularities, and every one of them is real and in code — verified against `origin/main` 2026-09-03:

| Tier | Control | Where |
|---|---|---|
| Full book | `MAX_PORTFOLIO_DEPLOYMENT_PCT = 0.60` (`1 − RESERVE_MANDATE_PCT`), two-tier CHECK 8: solvency KILL / policy REJECT | `c4_risk_engine/risk.py:122-130`, ADR-0026 |
| Band (5 buckets) | `kelly_fraction` per band — T1/T2/T3 at 0.0, `T4_IN_PLAY` 0.20, `T5_LATE_GAME` 0.25 | `execution_bands.py` |
| T4 sub-segment (11) | Independent `kelly_fraction` per segment — **eight distinct regimes** across 0.0 / 0.05 / 0.07 / 0.08 / 0.10 / 0.167, each with its own decision tree | `execution_bands.py`, ADR-0029 |
| Cell (78) | `resolve_kill_switch_state()` / `halt_cell()` — **built and not wired.** This is ADR-0054 (d) | `market_type_registry.py:875,885` |
| Individual bet | `T1_MEASUREMENT_STAKE_USD=1.00`, `MAX_CONTRACTS=10`, `MAX_HAIRCUT_PER_CONTRACT_USD=0.10` | `measurement_stake.py:54,55,70`, ADR-0050/0059 |

**ADR-0060 addresses the halt at exactly one of those five tiers** — band-level T4M-PROJ — **against a single 60s bar that GG-038 already records as a batch-era number applied unmodified to a continuous-evaluation architecture.** A halt latency requirement is only meaningful relative to how fast the thing being halted commits capital, and eight different Kelly regimes across the T4 tree commit it at eight different rates. One bar cannot be correct for all of them.

**What 16.1 must therefore do, and must not do.** It must derive a per-tier halt requirement from each tier's own exposure rate — the same discipline APR-0024 demanded for sample adequacy and ADR-0060 §3 demanded for any NFR-03 revision: a number derived from what a kill-trigger event can actually cost at that tier's sizing, never from what the current loop happens to measure. It must absorb GG-038 TASK 2/3 (T4 treats a `KILL_SWITCH` approval identically to an ordinary `REJECTED`; `is_kill_switch_active` is read by zero MLB pipelines) because those are defects in the same subsystem and two ADRs written separately about it will contradict each other. **It must NOT re-open ADR-0060's accepted option (c) or its deferral** — (c) remains the target architecture for the band tier, and this ADR establishes the hierarchy (c) gets built into. **Draft only. No code, no `kelly_fraction`, no ACCEPTED.**

---

# 14.1 — RECORD THE FOUR OPERATOR SIGN-OFFS

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "record-signoffs-20260903"
Claim your own T- and GG- numbers at run time (GG-234). Gap-log entry as your FIRST pushed commit
if you register anything; if you register nothing, say so in your CLOSED row.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: SHORT-STANDARD. ONE deliverable, four rows. Precision matters more than speed here -- these
are formal governance records and three of them are ADR status flips.

Earl signed off in-session 2026-09-03, same pre-granted pattern as ADR-0050 and ADR-0059. Record
each in APPROVALS_REGISTER.md with the date, then flip each document's Status field.
**HARD RULE 3: you may edit a Status field and add a sign-off line. You may NOT edit any ADR's body
or reasoning. If a document's own text contradicts what is written below, STOP and report the
conflict rather than reconciling it.**

ADR-0062 -- ACCEPTED as written. Status PROPOSED -> ACCEPTED.
  D1 naming, D2 roster, D3 fresh epoch-1 per sport, D4 projection all accepted.
  Record two conditions travelling with the signature:
   (i) EVENT stays DEFERRED for both sports pending verification of each sport's C1 ingestion
       mechanism (push vs poll). ADR-0062 section 4 declines to assert live-or-blocked status
       without it; the signature does not override that.
   (ii) ADR-0062 sections 4 and 6 disagree about BOUNDARY -- section 4 calls it "propose, scoped
       only, not authorized to build," section 6's 21-cell projection counts it. **Record the
       conflict in the sign-off line as unresolved-at-signature and route it to 15.1. Do NOT pick a
       reading here.**
  Authorizes the scaffolding build (15.1). Authorizes NO kelly_fraction and NO cell promotion.

ADR-0060 -- option (c) ACCEPTED as TARGET ARCHITECTURE, implementation DEFERRED.
  Status PROPOSED -> ACCEPTED. This is ADR-0060's own section 5 recommendation and the acceptance
  must not read as broader than it.
  Record verbatim in substance: (c) decoupled out-of-band halt is the chosen target architecture.
  **It is NOT authorized to build now.** Trigger: (c) is scoped and authorized when T4M-PROJ's
  kelly_fraction is next considered for edge-conditional reactivation under ADR-0048. Rationale to
  record: current exposure is zero (kelly_fraction=0.0), so there is no operational urgency, and
  reactivating live sizing on a band with a known uninterruptible kill-switch gap is the point at
  which this stops being a research finding and becomes live-capital risk.
  Options (a) and (b) are NOT adopted. ADR-0054 item (d) remains blocked until (c) is built.
  Record as a DECISION OWED, do not solve: ADR-0060 section 6 names two defects no remedy option
  touches -- run_t4_mlb_live.py treats a KILL_SWITCH approval status identically to an ordinary
  REJECTED (T1 branches and self-halts; T4 does not), and `is_kill_switch_active` is read by zero
  MLB pipelines. Both are GG-038 TASK 2/3 and both are unstaffed.

ADR-0061 -- ACCEPTED per its section 7. Status PROPOSED -> ACCEPTED.
  Option (c) stop-repair-start runbook: ADOPTED NOW.
  Option (b) repair scripts must take the existing fcntl lock: ADOPTED as a complementary contract.
  Option (a) diagnostic half (why did the existing reload-before-save not hold?): STAFFED as a
    follow-on. The implementation half of (a) is NOT adopted.
  Option (d) service-owned repair endpoints: NOT ADOPTED at this time.
  **GG-224 stays OPEN.** Per section 5, a runbook is not a structural guarantee and the operator's
  2026-08-29 restart pre-authorization is proof the procedure works when followed, not proof it will
  be followed. Do not close GG-224 on this signature.

APR-0033 -- ACCEPTED: fire the moneyline-first reroute. Register row PENDING -> ACCEPTED 2026-09-03.
  Basis: both the Poisson fit (T-487) and the NB refit built specifically to correct its
  misspecification (T-500/EXP-025) returned negative point estimates below HYP-010's pre-registered
  +0.005 to +0.025 band.
  **Box 2.3's INCONCLUSIVE verdict stays exactly as recorded and is NOT relabelled.** What changes
  is the routing, per MARKET_EXPANSION_ACTION_PLAN.md's own "Note on model class": moneyline-first,
  LR (ADR-0004 production class), binary target, no distribution fit. Phase 2 is not terminated.

TWO OPERATOR DECISIONS -- record as decision records, NOT as gaps, NOT as ADR flips.
  n* STANDARD -- APR-0024 stands unrevised. Record the rationale (post-hoc revision of a power
    standard is indistinguishable from weakening a control; and loosening power .95->.80 leaves
    n*~10,300 against n=559, so it would not help anyway) and the derived finding: the fill haircut
    consumed 65% of gross edge (0.0540 -> 0.0191), making execution cost the binding constraint on
    n*, not model quality. **This closes the open question. It authorizes no code change.**
  CELLS BEFORE LIVE CAPITAL -- "at least one" stands, plus (1) the candidate cell must be
    pre-registered as a capital candidate BEFORE its cohort completes, and (2) its threshold must
    carry a multiplicity correction over the pre-registered candidate set. Record the acknowledged
    cost: Bonferroni over five candidates raises n* a further ~46%.
    **This amends ADR-0057's closure condition, so it does NOT bind until a superseding ADR ships
    (16.2). Record it as an accepted decision awaiting that ADR -- do not treat the gate as changed.**

VERIFY: re-run `python3 scripts/check_register_parity.py` from the merged tree and paste it -- adding
four rows must not introduce a mismatch. Confirm each ADR's Status line reads ACCEPTED with its date.

DO NOT: implement anything any of these authorize -- that is Wave 15, and it does not fire until this
block has landed. DO NOT: touch any kelly_fraction, cell status, ExecutionBand member, or ledger row.
DO NOT: close GG-224. DO NOT: edit any ADR body. DO NOT: resolve the BOUNDARY conflict.

SCOPE FENCE: 00_ADMIN/APPROVALS_REGISTER.md, the Status lines + sign-off lines of ADR-0060/0061/0062,
APR-0033's register row, DECISION_LOG.md.
Self-serialising close-out: rebase onto origin/main immediately before writing GOVERNANCE_GAP_LOG.md
and DECISION_LOG.md.

REPORT BACK: the four register rows as written; each Status line before and after; the parity output;
the DECISION OWED you recorded for GG-038 TASK 2/3; and any place a document's text contradicted this
prompt (there should be none except the BOUNDARY conflict, which is expected and must be recorded).
```

# 14.2 — LANDING AND HYGIENE

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "landing-and-hygiene"
Claim your own T- and GG- numbers at run time (GG-234).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: SHORT-STANDARD. Four deliverables. This block exists because the landing step has failed three
waves running -- treat landing as the product, not as cleanup.

DELIVERABLE 0 -- LAND T-509 IF IT HAS NOT LANDED. Check first:
  git merge-base --is-ancestor session/20260901T052401Z-t509-adr0054a-cell-awareness origin/main
  Exit 0: it landed on its own. Say so, skip to Deliverable 1, do NOT re-land it.
  Exit 1: land it. Complete on branch -- all three ADR-0054(a) items (replay_harness_t427.py no longer
  silently defaults market_type; assert_ledger_invariants.py and run_band_monitor.py cell-aware), 925
  insertions across 3 scripts and 4 test files, plus GG-232, GG-184 -> PARTIALLY RESOLVED, GG-235.
  **Run the full suite on the branch first and paste the pass/fail/skip line. If it is not green, STOP
  and report -- do not land red work to clear a backlog.**
  If a check or classifier blocks the merge (as it did for PR #125), diagnose it, report what it was
  blocking, and say whether it was a true positive. **If it is a real policy violation, STOP.**
  Confirm with the ancestor check in the documented direction; paste the exit code. Amend GG-186.
  NOTE: 14.3 is running concurrently and owns logic_epoch.py. T-509's work reads the epoch boundaries
  but does not write logic_epoch.py -- if you find it does, STOP and coordinate.

DELIVERABLE 1 -- INSTALL THIS QUEUE. origin/main's copy is still the Wave 11 version. Copy the current
file from the shared main checkout at 04_EXECUTION/ACTIVE_QUEUE.md into your worktree, commit, push.
Confirm exactly one queue file: `find . -name "ACTIVE_QUEUE*.md" -not -path "./.git/*"`. Never leave a
second copy anywhere.

DELIVERABLE 2 -- GG-235. LEDGER_INVARIANT_SUITE.md's documented VPS-fetch commands reference filenames
that no longer exist. The entry rides in with Deliverable 0 -- read it from the merged tree, not from
this prompt. Fix the commands against the real current filenames. **Verify each against the actual VPS
or the actual repo. Do not infer a rename.** If you cannot verify one, leave it flagged and say so.

DELIVERABLE 3 -- FINISH T-511's CLOSE-OUT. db739af is a truncated stub written at budget exhaustion.
Confirm T-511's SESSION_CLAIMS row states the true merge status, its DECISION_LOG entry exists, and its
handoff artifacts exist. **Read its commits and report only what they show -- do not invent a
retrospective account.** If something is genuinely absent and cannot be reconstructed, record it absent.

DO NOT: touch any kelly_fraction, cell status, ledger row, or ExecutionBand member.
DO NOT: implement ADR-0054(b) -- 14.3 owns logic_epoch.py. DO NOT: act on any Wave 15 authorization.

SCOPE FENCE: the T-509 merge, 04_EXECUTION/ACTIVE_QUEUE.md, 04_EXECUTION/LEDGER_INVARIANT_SUITE.md,
11_MEMORY_HANDOFF/, gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the Deliverable 0 exit code and whether T-509 had already landed; the suite line if you
landed it; what any blocking check was actually blocking; the find output proving one queue file; which
GG-235 filenames you verified and which you could not; what T-511 left absent.
```

# 14.3 — ADR-0054 (b) · THE TWELVE-BOUNDARY RE-KEY

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "adr0054b-boundary-rekey"
Claim your own T- and GG- numbers at run time (GG-234). Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

DELIVERABLE 0 -- 14.2 owns the T-509 landing. Check whether T-509 is an ancestor of origin/main. If it
is NOT and 14.2 has not landed it yet, you may still proceed: T-509 touches
assert_ledger_invariants.py and run_band_monitor.py, which READ the epoch boundaries but do not write
logic_epoch.py. Rebase onto origin/main before your close-out so the two land cleanly. If you discover
T-509 does modify logic_epoch.py, STOP and coordinate.

TIER: STANDARD, budget generously -- twelve boundaries each need their own judgment call.

READ FIRST, in full: ADR-0054 item (b) and its section 9 sign-off, plus the APPROVALS_REGISTER
ADR-0054 row. Item (b) is SIGNED -- you are implementing an accepted decision, not proposing one.

THE WORK: re-key `LogicEpochBoundary.bands_affected` from band to `(MarketType, band)` cell keys.
logic_epoch.py carries TWELVE boundaries (verified on origin/main 2026-09-03).

*** THE SIGNED CONDITION, AND THE WHOLE POINT OF THE BLOCK: THE FAILURE MODE IS ASYMMETRIC. *** A
boundary scoped too WIDE only costs sample. A boundary scoped too NARROW silently leaves dirty rows
inside a cohort that reports itself clean. **Scope wider when uncertain.** This is not a blanket
re-key: **every one of the twelve carries its own recorded cell scope AND its own written
justification.** Twelve entries, twelve justifications, no "same as above". A boundary you cannot
justify narrowly gets scoped wide and you say so.

Scoping note: all twelve boundaries predate NFL and NHL having any cell, and predate ADR-0062
entirely. A historical boundary cannot be scoped to a cell that did not exist when it was set -- do
not invent forward-looking scope. MLB and NBA are the live question.

VERIFY, both sides: clean_n per band/cell before and after. A re-key that silently changes a cohort
size is either a real finding or a bug -- say which, with evidence. Run assert_ledger_invariants.py
before and after; report the delta with NO_FORMULA (band, assertion) pairs stated SEPARATELY and never
folded into a clean count. Full suite green; paste the pass/fail/skip line.

DO NOT: bump logic_epoch or add a boundary. DO NOT: touch any kelly_fraction or cell status.
DO NOT: implement ADR-0054 (a) -- T-509 built it. DO NOT: implement (d) -- blocked on ADR-0060's
build, which is itself deferred to the ADR-0048 reactivation trigger.
DO NOT: add any ExecutionBand member -- that is 15.1 and it does not fire until 14.1 lands.
DO NOT: promote assert_ledger_invariants.py to --strict.

SCOPE FENCE: src/prediction_market_bot/logic_epoch.py and its tests. Nothing else under src/.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the twelve-row boundary -> cell scope -> justification table; every boundary scoped wider
than strictly necessary and why; clean_n before/after per cell with any change explained as
finding-or-bug; invariant delta with NO_FORMULA pairs separate; the suite line; the ancestor-check code.
```

---

## Needs your decision — three open, and I am giving you a recommendation on each

| # | Decision | Status |
|---|---|---|
| (i) | **GG-203 — the Kalshi order-write fault.** 19 days. Support ticket or demo-key regeneration. Nothing accrues until it clears; gates 16.1. **Still the highest-value item on the board and still not code.** No recommendation to give — it is an action only you can take. | **OPEN** |
| (ii) | **Is the `n*` standard still right?** See the plain-English write-up below. **Recommendation: keep APR-0024 exactly as it is. Do not revise it.** | **OPEN** |
| (iii) | **How many cells before live capital — and the kill-switch wiring defects.** See below. **Recommendation: keep "at least one," add pre-registration + a multiplicity correction. Separately: staff GG-038 TASK 2/3 as its own ADR draft.** | **OPEN** |

## DO NOT — standing

Don't unpark `SCALING_MANDATE_PARKED.md`. Don't promote `assert_ledger_invariants.py` to `--strict`. **Don't touch sizing or any `kelly_fraction` without an ADR** — a nonzero T1 Kelly needs ADR-0048's edge-conditional lookup table and a fresh signature, and T-494 argues against it. Don't build ADR-0060's option (c) — accepted as target, deferred by design. Don't close GG-224 on ADR-0061's acceptance. Don't relabel box 2.3's INCONCLUSIVE verdict. Don't adjudicate a decision request. Don't run a clean-vs-corrupted comparison without pre-registering it. Don't re-investigate GG-203 in-repo. Don't kill the price-archive cron (`deploy/cron.conf:347-348`). Don't repair a derived file: establish provenance first (GG-228). Don't work from the shared `main` checkout. Don't land red work to clear a backlog. **Don't recommend against a sport or a family on the strength of a finding — operator doctrine 2026-08-21, reaffirmed 2026-08-27.**

**Retired:** "Don't reopen T1." Superseded 2026-08-25.

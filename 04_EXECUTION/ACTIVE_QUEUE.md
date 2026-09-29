# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates.

**Verified against:** `origin/main = cdd568e` (2026-09-29). *This window cannot `git fetch`.*
**Live state:** 92 cells - 22 bands - 1 cell ACTIVE - **149 gap entries, 105 OPEN.** Max GG seen:
310 (GG-311 may be claimed -- verify at run time). Shared tree behind origin.

> ### OPERATOR RATIFICATION -- 2026-09-29. BLOCK 37.3 EXECUTES THIS.
>
> A governance audit this session found **36 accepted decisions with no row in
> `APPROVALS_REGISTER.md`**, split two ways:
> - **14** name the operator and a date in their own status line (*"DS sign-off Earl Ignacio
>   2026-06-23"*). Approved; never written back. Record-keeping debt.
> - **22** read bare `ACCEPTED` with **no signer named anywhere** -- ADR-0001 through ADR-0033,
>   the founding period. The record cannot say who approved them. Several are load-bearing:
>   **ADR-0010** (Kelly fraction / reserve mandate), **ADR-0024** (stop-pivot criterion),
>   **ADR-0004** (model class).
>
> **Operator decision, Earl Ignacio, 2026-09-29, in session: "Full approval."** Given in response
> to a choice between (a) ratifying all 22 wholesale in one dated register entry, and (b) triaging
> the load-bearing subset for individual re-reading. **Option (a) selected.**
>
> **Scope, as recorded by the strategic window at the operator's direction:**
> - Covers **ADR-0001 through ADR-0033** inclusive, where the file reads ACCEPTED and no register
>   row exists, PLUS the 14 signer-named-but-unregistered decisions.
> - Affirms them as **operator-approved as of 2026-09-29**. Original sign-off dates are
>   **unrecoverable and must be recorded as such** -- do not invent or infer one.
> - **Does NOT approve anything in "Needs your decision."** The ten pending items stay pending.
>   APR-0035 in particular cannot be "approved" -- it presents options and requires a selection.
> - Ratification is a **recording** action. It changes no code, constant, cell status or sizing.

---

## ⬛ FIRE NOW — Wave 37, three blocks, concurrent

| Paste | Block | Tier | One-line purpose |
|---|---|---|---|
| 1st | **37.1** | STANDARD | **Build a T4-capable A/B harness.** 36.2 proved the ADR-0042 D2 gate cannot run for T4 at all -- every future T4 enhancer is blocked behind this. |
| 2nd | **37.2** | STANDARD | **Enrich EXP-027 with the EPA splits.** NFL is the only live sport; the model sees two aggregate numbers. |
| 3rd | **37.3** | STANDARD | **Burn down the governance tree.** Execute the ratification, archive 24 resolved gaps, delete 39 merged branches. |

**Fire order does not matter.** 37.1 owns the harness stack. 37.2 owns `nfl_exp027_adapter.py` and
the NFL feature accessors. 37.3 owns `APPROVALS_REGISTER.md`, **`GOVERNANCE_GAP_LOG.md` /
`DECISION_LOG.md`**, the retire script and the branch sweep.

**Exactly three fences. A fourth means something is wrong -- stop.**

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **A block in the wave fires immediately, concurrently with every other.** Work that must wait goes in "Queued next." A sequencing note is not a fence.
- **Deliverable 0 in every block: land any un-landed predecessor.**
- **Check your deliverables against real-world sequencing before starting (GG-287).** Do not accept a task that requires an event which has not happened yet.
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no operator approval in a block overrides it — an approval authorizes a CHANGE, never a bypass.
- **Push after each deliverable.** Verify a fix by importing and calling the real function. **Benchmark the real thing.**
- **A merge is not a deployment, and a deployment is not an activation** (GG-279).
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10-34 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **35** | CLOSED | GG-303 mechanism found and fixed (write boundary). **Cohort UNRECOVERABLE.** Feature audit complete; T-569 verdict corrected to its real scope. |
| **36** | **CLOSED -- ALL THREE LANDED** (`cdd568e`) | **`park_factor_hits` was dead and is repaired** (venue-name matching, GG-145); ADR-0064 drafted. **T4 game-state/leverage fields now logged**, `p_t4` unchanged; candidate built offline; ADR-0065 drafted. **GG-303 ACTIVATED with running-process proof** (merge-base ancestry, deployed-file read, MainPID/cwd, no stale bytecode) -- audit-log leg pending a live game window. **Operator Console Section 0 live**: 210 retirement items, 24 unarchived gaps, 39 merged-undeleted branches. |
| **37** | **FIRING** | Make the T4 gate runnable - enrich the only live sport - burn down the governance tree. |

---

## Why this wave is shaped this way

**36.2 found a structural blocker worth more than the candidate it was testing.** The ADR-0042 D2
`DEFENSIBLE_IMPROVEMENT` gate -- the thing standing between any enhancer and the live book --
**cannot be run for T4 at all.** Three converging reasons: the harness's default input file has
never existed in this repo; the harness stack was purpose-built for T1 MLB book-selection filtering
per its own docstring, with no schema concept of T4's fields; and no resolved-bet record anywhere
carries the game-state fields, because they were only logged last block. So ADR-0065's candidate
is not waiting on merit -- it is waiting on a gate that does not exist. 37.1 builds it.

**Neither sport is currently accruing.** MLB's season closed; T4M-PROJ is frozen. And NFL T1 has
**no cron entry at all** -- every NFL run to date was launched by hand, which is how GG-302's
unlogged manual run happened. NFL runs to January and is the only live window the project has.
37.2 makes the NFL model worth running; **scheduling it needs an operator authorization** and is
flagged under "Needs your decision," not assumed here.

**37.3 is the burn-down.** Section 0 now counts the debt; this executes against it.

---

## WAVE 37 BLOCKS

---

# 37.1 -- MAKE THE T4 GATE RUNNABLE - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "t4-ab-harness"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 37.3 owns them. ***

TIER: STANDARD. This unblocks every future T4 enhancer, not just ADR-0065's candidate.

ESTABLISHED -- VERIFY, DO NOT RE-DERIVE (T-580, Wave 36 Block 36.2 Deliverable 4):
the ADR-0042 D2 `DEFENSIBLE_IMPROVEMENT` gate cannot be validly run for T4 today, for three
independent converging reasons: (1) the harness's default input
`logs/.vps_portfolio_cache_mlb.json` has NEVER existed in this repo -- confirmed by a live
FileNotFoundError and `git log --all`; (2) `ab_harness.py` / `run_ab_experiment.py` /
`run_exp017b_decomp_mlb.py` were purpose-built for T1 MLB book-selection filtering per their own
docstrings, with no schema concept of T4's game-state fields; (3) no resolved-bet record anywhere
carries those fields -- they were only logged in 36.2 and the 2026 MLB accrual window has closed.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR. Confirm cdd568e or later is your base.

DELIVERABLE 1 -- DECIDE THE SHAPE BEFORE YOU BUILD, AND WRITE DOWN WHY.
  Does T4 need a parallel harness, a generalization of the existing one, or a shared core with
  per-band adapters? Read the existing stack first and report what is genuinely reusable --
  `compute_clv_row`/`cohort_aggregate` from T-572's CLV work were reported as market-type-agnostic;
  verify that claim rather than trusting it. Push your choice and its reasoning BEFORE building.
  A generalization that breaks T1's existing behaviour is a regression, not a refactor.

DELIVERABLE 2 -- BUILD IT, WITH AN EXPLICIT INPUT CONTRACT.
  The harness must state, in code, what it requires of a cohort: which fields, what resolution
  semantics, what minimum n, and what it refuses. **It must refuse loudly on a cohort that cannot
  support a valid comparison rather than returning a number.** That refusal is the feature -- a
  harness that silently scores an inadequate cohort is how the project got two contradictory
  calibration headlines.
  It must also refuse the T4M-PROJ 765/905-row cohort explicitly by name: T-577 declared it
  UNRECOVERABLE and it must never become a holdout by accident.

DELIVERABLE 3 -- PROVE IT ON A COHORT THAT EXISTS TODAY.
  Demonstrate the harness end-to-end on real data it can legitimately score -- T1 MLB historical,
  or a synthetic cohort with known ground truth where you state plainly that it is synthetic and
  what it does and does not prove. Show it correctly REFUSING at least two inadequate cohorts.
  Do NOT manufacture a cohort to make a test pass.

DELIVERABLE 4 -- SAY WHAT IT STILL CANNOT DO, AND WHEN ADR-0065 BECOMES TESTABLE.
  Name the conditions under which ADR-0065's candidate could actually be gated: which fields,
  how many resolved rows, over how many game-days, from which accrual window. Cost it in calendar
  time given MLB's season is closed. If the honest answer is "not before the 2027 MLB season
  unless T4 runs on another sport," say exactly that.

DO NOT: run the gate on ADR-0065's candidate and report a verdict -- the data does not exist yet.
DO NOT: use the T4M-PROJ cohort as training, holdout or validation, or weaken its exclusion.
DO NOT: change any model, constant, kelly_fraction or cell status.
DO NOT: break or alter T1's existing harness behaviour. Prove that with its existing tests.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 37.3 owns them.
DO NOT: touch `nfl_exp027_adapter.py` -- 37.2 owns it.

SCOPE FENCE: the A/B harness stack, a new T4-capable module, tests, a results summary.

REPORT BACK: the reusability assessment with your architectural choice and reasoning; the input
contract as implemented; the end-to-end demonstration plus two refusals; proof T1's behaviour is
unchanged; and the named conditions and calendar cost for ADR-0065 becoming testable.
```

---

# 37.2 -- GIVE EXP-027 THE SPLITS - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "exp027-epa-splits"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 37.3 owns them. ***

TIER: STANDARD. NFL is the only live sport the project has until March.

T-575's feature audit, item 4: EXP-027 consumes exactly **two inputs** -- `off_epa` and
`def_epa_allowed`, both aggregate sums -- while `passing_epa` / `rushing_epa` splits are **already
fetched and simply never consumed**. It is pointed at NFL spreads, among the sharpest lines in the
world, with two aggregate numbers. T-575 ranked this item 4 only because EXP-027 is already
UNDERPOWERED for small-n reasons a richer feature set does not fix by itself -- that caveat stands
and must appear in your write-up.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR. Confirm cdd568e or later is your base.

DELIVERABLE 1 -- CONFIRM THE DATA IS REALLY RESIDENT. Verify T-575's claim yourself.
  Where do `passing_epa` / `rushing_epa` actually live, at what grain, for how many seasons, and
  with what coverage gaps? Report the real span and any missing weeks. If they are NOT resident as
  claimed, STOP and report -- do not add a data source inside this block.

DELIVERABLE 2 -- BUILD THE ACCESSORS AND THE ENRICHED CANDIDATE. OFFLINE ONLY.
  New accessor methods, then a candidate EXP-027 consuming the splits alongside the existing
  aggregates. Retrain per EXP-027's existing methodology (LogisticRegression +
  CalibratedClassifierCV sigmoid) -- same methodology, more features. Do not redesign the model
  class; that is ADR-0004 territory and a separate decision.
  **The incumbent stays the default. The candidate is wired into no run path.**

DELIVERABLE 3 -- EVALUATE ON HISTORICAL NFL, HONESTLY, WITH A HOLDOUT.
  Out-of-sample by season or by week -- state which and why. Report accuracy, Brier, ECE and
  calibration curve for incumbent vs candidate on the same holdout, with n for each.
  **Report the interval, not just the point estimate.** EXP-027's own prior verdict was
  UNDERPOWERED at n=16 for 2026; if your holdout is also small, say so and do not dress a
  noisy improvement as a result.
  Also report the closing-line comparison if the archive supports it: does either model beat the
  market's own closing price on the same games? That is the harder and more useful question.

DELIVERABLE 4 -- DRAFT THE ADR. DO NOT ACCEPT IT.
  ADR-0004 frozen-model policy applies. Draft with the holdout evidence, the functional change,
  and an explicit statement of what it does NOT fix -- specifically that more features do not
  resolve a small-n power problem. Note that activation also requires clearing ADR-0042 D2, and
  that 37.1 is concurrently establishing whether that gate is runnable here.

DO NOT: wire the candidate into any live run path or change the default model.
DO NOT: add an NFL cron entry. Scheduling NFL T1 requires explicit operator authorization
  (standing DO NOT) and is flagged under "Needs your decision" -- it is not yours to assume.
DO NOT: use the 42 quarantined NFL T1 rows (GG-302) as training, holdout or validation data.
DO NOT: change kelly_fraction, a cell status, or a gating constant.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 37.3 owns them.
DO NOT: touch the A/B harness stack -- 37.1 owns it.

SCOPE FENCE: `nfl_exp027_adapter.py`, the NFL feature accessors and their store, tests, one ADR
draft, a results summary.

REPORT BACK: where the splits live with real coverage span and gaps; the retrained candidate's
holdout results vs incumbent WITH intervals and n; the closing-line comparison if computable; and
the ADR draft path with the small-n caveat stated in it.
```

---

# 37.3 -- BURN DOWN THE GOVERNANCE TREE - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "governance-burndown"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md, DECISION_LOG.md AND APPROVALS_REGISTER.md THIS WAVE. ***

TIER: STANDARD. Filing and recording only. **This block adjudicates nothing.**

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR AND THE QUEUE.
  You own the shared `main` tree. `git fetch origin`; compare `git diff --name-only HEAD
  origin/main` against your dirty set and STOP if any file is in both. `OPERATOR_CONSOLE.md`'s
  diff is hook output -- discard it. `git pull --ff-only`; never force. Then commit and push
  PATH-SCOPED: `04_EXECUTION/ACTIVE_QUEUE.md` and `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` only.
  Verify `grep -c '^```' 04_EXECUTION/ACTIVE_QUEUE.md` returns 6.

DELIVERABLE 1 -- EXECUTE THE OPERATOR RATIFICATION. Record exactly what was authorized.
  Read the "OPERATOR RATIFICATION -- 2026-09-29" block at the top of `ACTIVE_QUEUE.md`. It carries
  the operator's decision verbatim and its scope. **If that block is absent, STOP** -- do not
  ratify on inference.
  Write ONE dated entry in `APPROVALS_REGISTER.md` covering the unregistered accepted decisions.
  It must state, in its own text: the operator's words and the date; that this affirms them as
  operator-approved **as of 2026-09-29**; that **original sign-off dates are unrecoverable and are
  not being invented**; and the two populations separately -- the 14 that name a signer in their
  own status line, and the 22 that name none.
  Enumerate every ID covered. Re-derive that list yourself from the files; do not trust this
  block's counts. If your count differs from 14/22, report the difference rather than reconciling
  silently.
  **Change no ADR's own status line, no code, no constant, no cell status.**

DELIVERABLE 2 -- ARCHIVE THE RESOLVED GAPS. The retire script exists; this is its first real run.
  `scripts/retire_resolved_gaps.py` was built warn-only in 33.3/34.3 and proven on a copy.
  Run it for real against the live log. Section 0 currently counts **24** unarchived resolved-class
  entries -- re-derive that number rather than trusting it.
  Stay-tokens (`PARTIALLY RESOLVED`, `PARTIAL RESOLVE`, `LIKELY RESOLVED`, `IN PROGRESS`,
  `PLAN ACCEPTED`, `ACCEPTED UNCERTAINTY`, `WATCH ITEM`) are **NOT** resolved-class and must not
  move. Verify none moved. Diff before and after and prove only whole entries relocated, verbatim.
  Then re-run the structural parity assertion (headers == status lines) and the id-uniqueness check.

DELIVERABLE 3 -- SWEEP THE BRANCH ESTATE. Merged only.
  `scripts/sweep_stray_branches.sh --execute`. Section 0 counts **39** merged-but-undeleted local
  branches -- re-derive. `git branch -d`, **never `-D`**; if `-d` refuses, that branch is not
  merged -- leave it and report it. Prune worktrees.
  **Do not delete any UNMERGED branch.** 17 remain operator-routed (Hard Rule 11) and nine of those
  need a keep/kill from the operator that has not been given.

DELIVERABLE 4 -- REGISTER WHAT THIS AUDIT EXPOSED, AND RE-RENDER SECTION 0.
  Register a gap for the register-parity failure class itself: 36 accepted decisions accumulated
  with no register row, including load-bearing ones (ADR-0010 Kelly/reserve, ADR-0024 stop-pivot,
  ADR-0004 model class), and the write-back step is still manual. Note that
  `check_register_parity.py` gained the reverse direction in 33.3/34.3 -- state whether it now
  catches this class, and if not, why not.
  Then re-render the Operator Console and report Section 0's counts before and after this block.
  Clear the gap candidates handed over by 37.1 and 37.2.

DO NOT: approve, accept, select an option on, or change the status of ANY item under "Needs your
  decision." Ten items are pending and all ten stay pending. **APR-0035 cannot be "approved" --
  it presents options and requires an operator selection.**
DO NOT: change any ADR's or APR's own status line. The register entry records; it does not amend.
DO NOT: repair, edit or re-stamp any ledger row, including GG-303's 395.
DO NOT: delete an unmerged branch, or move a stay-token gap to the archive.
DO NOT: touch the A/B harness or `nfl_exp027_adapter.py` -- 37.1 and 37.2 own those.
DO NOT: restart a production service.

SCOPE FENCE: `APPROVALS_REGISTER.md`, `GOVERNANCE_GAP_LOG.md`, `GOVERNANCE_GAP_LOG_ARCHIVE.md`,
`DECISION_LOG.md`, the retire and sweep scripts' execution, the operator console re-render, and
the two queue files.
Self-serialising close-out: re-read the logs fresh against HEAD immediately before writing.

REPORT BACK: the ratification entry as written with your own re-derived ID list and any count
difference; the archive diff proving only whole resolved entries moved and no stay-token did; the
branch sweep result with anything `-d` refused; the new gap registered for the parity class; and
Section 0's counts before and after.
```

---

## THE ARC — Waves 34 through 38

Sequenced, not pre-written. Each wave is drafted only once its predecessor reports. Standing
split: **2 calibration, 1 plumbing.**

**The arc's own reorder clause fired.** It said: *"If Wave 35 finds most cells are stub-backed,
then 'calibrate the core four' is still a modeling problem wearing calibration's clothes."* Wave 33
triggered a stronger version of that early — the one cell that *is* implemented has a falsified
thesis. So the arc now front-loads instrument-building and inventory, and defers per-cell
calibration until there is something calibratable and something to score it with.

| Wave | Calibration / grounding | Plumbing | The question it answers |
|---|---|---|---|
| **33** | T4 latency measurement — **NOT SUPPORTED** · cohort integrity — **34 of 765** | Retirement mechanism (warn-only) | *Does the market lag? — No. Is the 765 real? — Mostly unverified.* |
| **34** | CLV harness — the reusable instrument · cohort verification to its retrieval ceiling | The resolved filter + GG-279 check | *Can we score a model without P&L, and do we hold any scorable evidence?* |
| **35** | Model inventory across all 14 market types — **which cells have a real forecaster and which have a stub**, scored on 34.1's harness where possible · **T4's 11 sub-bands re-justified or collapsed** | Branch routing pass (after your keep/kill) + registry-vs-reality sync | *How many of the 92 cells can be calibrated at all, versus needing a model built first?* |
| **36** | Per-cell CLV scoring of whatever real models Wave 35 found · depth distributions against APR-0029 D1/D3 | Cell activation sequencing driven by Wave 32.2's measured gradient | *Which cells show measurable edge on the harness, ranked by evidence rather than convenience?* |
| **37** | **APR-0035 forced to a decision** with Waves 32–36 in hand | G6 / registry reconciliation under ADR-0057 | *What are we accruing toward, and is it the right thing?* |
| **38** | Whatever 36 found worth building or rebuilding | GG-038 kill-switch defects / NFR-03 | *Held open deliberately — 36 decides its content.* |

**The shape of the arc, revised: rebuild the instruments (34) → find out what can be measured at
all (35) → measure it (36) → decide (37).**

Three things that could reorder it again, and should:
- If **34.1's CLV is negative on the model's approvals AND on the random control**, the market, not
  the model, is the finding — and Wave 36 becomes a market-selection wave rather than a
  calibration wave.
- If **34.2's retrieval ceiling is far below 731**, no amount of later work recovers the cohort.
  Wave 35's inventory then becomes the only route to evidence, and it moves ahead of everything.
- If **34.1 finds most of the 92 cells cannot be scored even in principle** (no price history, no
  entry timestamps), then the harness needs a capture layer before it needs models, and that is a
  plumbing wave nobody has scheduled yet.

---

## Queued next — not yet fired

**T4M-PROJ's ACTIVE status — operator decision, not a block.** It is the only ACTIVE cell in the
registry and its founding thesis is now measured and not supported. See "Needs your decision."

**The 0.70–0.90 price stratum — fresh pre-registration on new data, or nothing.** T-569's only
positive segment: forward slope +0.139 (k1) to +0.188 (k4), significant at all four horizons. It is
the smallest cell in the table by roughly 30× and its backward placebo still exceeds forward by
1.1–1.9×, so it did not clear the pre-registered confound bar. **Re-cutting T-569's data until this
survives is prohibited by the standing DO NOT list.** If it is worth pursuing it is worth a new
pre-registration against data T-569 did not see. Wave 35's call, with the inventory in hand.

**APR-0035 — force it to a decision (arc: Wave 37).** The question has changed shape twice now.
31.1 reproduced the model-vs-market result; T-571 then showed that reproduction read a cohort that
is 95.6% unverified and reverses sign on the verified part. It is no longer "how long to reach n*"
and no longer even "is this cohort worth accruing" — it is "does this cohort exist." 34.2 answers
that. Do not pre-write the answer into this queue; it is the operator's.

**GG-295 actor provenance — SHORT block, terminal only.** T-563 established content provenance (42
rows, three fields, diffed against the pre-backfill snapshot). Actor identity is unestablished and
needs VPS shell/SSH history around 2026-09-18T19:04 UTC. **GG-302 has now produced a second
instance of the same class** — 42 NFL T1 rows traced to a single unlogged manual run with no
identifiable actor. Two instances make this a pattern rather than an incident; when it fires, audit
every `repair_ref` stamp in the codebase for the same corroboration gap, per GG-295's own
recommendation (3).

**GG-203 — watch for a real fill.** Shard 3 is funded ($200, 2026-09-22). Closes only when the live
`t4-mlb` service is observed converting an approval into a fill — not a hand-built order
succeeding. No restart is authorized. *Note: T-569's verdict makes it worth asking whether this
service should be sending anything at all — see APR-0034 under "Needs your decision."*

**MLB T1 game markets have never run live.** The path uses `kalshi_client=None` so GG-203 never
blocked it. Blocked instead on the model question: its default is
`StubMLBGameMarketForecastModel`, and stub-sourced positions are worth nothing. Establish whether
EXP-026/HYP-011 produced a real forecaster before scheduling it. **Folded into Wave 35's inventory.**

**The branch routing pass — the one that needs you, briefly (arc: Wave 35's plumbing slot).**
31.3 has run: the estate is 20 remote branches, of which **17 are unmerged**, holding ~54 unique
commits. T-570 has since given `sweep_stray_branches.sh` landed-branch cleanup and worktree prune,
so bucket A and the duplicate pairs can now be handled by tooling rather than by hand. **Bucket B
still needs your call.** Four buckets:

- **A — free delete (1 branch).** `session/20260903T184908Z-apr0033-accept-and-reroute` has 0
  unpatched commits by `git cherry`. Verify post-fetch, then delete. T-570's sweep can do this.
- **B — NEEDS EARL, 9 branches touching `src/`, `scripts/`, `tests/` or `deploy/`.** The question
  is not "can we land it" but "is this still wanted" — several predate ADRs that may have
  superseded them. Keep/kill, named branch by branch:
  `t497-t1-flat-stake-wrapper` (measurement_stake.py + assertions) ·
  `t4-nfl-nhl-scaffolding` (market_type_registry.py, execution_bands.py) ·
  `gg255-mlb-t1-game-market-run-script` (kalshi_client.py, run_t1_mlb_game_market.py) ·
  `gg267-per-row-model-provenance` (paper_trader.py, run_t1_nfl_game_market.py) ·
  `nfl-capture-gap-0912` (cron.conf, nfl_capture_gap_check.py) ·
  `gg291-threshold-backfill` (superseded in substance by T-563 — likely kill) ·
  `install-closeout-fix` + `install-closeout-fix-v2` (duplicate pair; the scripts are already on
  origin/main, so likely both kill) · `gg242-filename-sweep` (assert_ledger_invariants.py).
  *`t4-nfl-nhl-scaffolding` is worth a second look in light of T-569 — scaffolding T4 into two more
  sports is a different proposition now the T4 thesis has failed in the sport it was built for.*
- **C — extract, do not cherry-pick (the remaining ~6).** Their unique commits touch only
  `DECISION_LOG.md`, `GOVERNANCE_GAP_LOG.md` and handoff files. Those two logs have in-place edits
  and no union merge, so cherry-picking through them is a conflict grind with real corruption
  risk. Pull the entries out as text and append them.
- **D — duplicate pairs, pick one each.** `record-signoffs-20260903` vs `rerecord-adr-signoffs`
  (GG-240: the first was stranded by a classifier refusal and superseded by the second, so the
  second is the keeper). `install-closeout-fix` vs `-v2` — see bucket B.

**Standing rule for this pass: cherry-pick or extract. Never merge.** Each branch is weeks behind
main, so `git diff origin/main <branch>` reports up to 25,234 deletions — that is main's later work
the branch never saw, not content the branch removes. A merge would delete a month of work.

---

## Needs your decision

> ### ⬛ GG-303 RESTART AUTHORIZATION -- block 36.3 Deliverable 1 checks for a line here
>
> The write-boundary fix is on `origin/main` and is NOT in the running process. Activating it
> requires restarting `t4-mlb`, which the standing DO NOT forbids without scoped written
> authorization. **36.3 checks this section for an authorization line and SKIPS the deliverable if
> it is absent** -- it will not restart on inference or on a verbal paraphrase.
>
> **[x] AUTHORIZED -- operator Earl Ignacio, 2026-09-28, in session: "Yes - 36.3 has my
> authorization."**
>
> **Scope of this authorization, as recorded by the strategic window at the operator's direction:**
> - Service: **`t4-mlb`** on the paper/demo VPS. No other service.
> - Action: deploy the GG-303 write-boundary fix already on `origin/main`, restart `t4-mlb` to
>   load it, and verify the RUNNING process contains it.
> - **This is a single scoped restart for this activation. It is NOT a standing restart
>   permission** -- any future restart, of this or any service, needs its own authorization line.
> - Demo account only. No real capital. No sizing, cell-status or model change travels with this.
> - The 395 existing fabricated-id rows are **NOT** authorized for repair. Forward fix only.
>
> 36.3 Deliverable 1 is therefore LIVE. Proceed with it.

| Item | Plain English | What happens if it waits |
|---|---|---|
| **GG-303 restart** | **AUTHORIZED 2026-09-28** -- see the block above. 36.3 Deliverable 1 is live. | Resolved. Watch for the proof-from-running-process in 36.3's report-back. |
| **APR-0035** | **It now has its answer.** Cohort UNRECOVERABLE (T-577), thesis NOT SUPPORTED at current feature scope (T-569), gate seasons away. The question is no longer "how long" -- it is what to accrue toward. | Six weeks open. Every wave since has produced evidence it should have consumed. |
| **ADR-0063** | Approved in chat 2026-09-18; still **no signature row** in `APPROVALS_REGISTER.md`. Confirmed absent by grep. | Nothing downstream can cite it. Section 0 will start counting it weekly. |
| **ADR-0053 §2.5 correlation group** | Named, never authorized. **Concurrent bets are currently modelled as independent** -- zero `correlat*` in `risk.py`. | Parlays, clustered pipelines and honest exposure management all stay blocked behind it. |
| **17-branch routing** | Nine need a keep/kill from you; the rest are mechanical. | Each is someone's finished work, ageing. |


---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact refusal and hand back.
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time an existing price-capture window.
- Restart a production service without a scoped, written authorization. None is authorized in Wave 31.
- Add a cron entry for any T1 game-market run script without explicit operator authorization.
- Pre-assign T-/GG- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the running process contains it.
- Manufacture a position, a row, a cohort member, or a final score to have something to measure.
- Submit an order against the production Kalshi account or with real funds. Demo only, always.
- Revive `exchange_index` propagation — T-558 tested and disproved it.

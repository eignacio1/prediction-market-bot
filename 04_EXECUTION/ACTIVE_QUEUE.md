# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed block prompts move
> verbatim to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`. Closed waves stay visible here as
> sequencing-track rows and outcome prose, never as pasteable fences. A fence in this file for a
> wave the track marks CLOSED is a defect — archive it before doing anything else.

**Verified against:** `origin/main = b25fcb6` (2026-09-24, Wave 33 fully landed). *This window
cannot `git fetch`. Every block fetches first. A LANDED call is safe from a stale ref; a "not
landed" call is not — say "not visible at my ref," never "did not land."*

**Live state, derived at `b25fcb6`:** 92 cells (registry-derived) · 22 bands · **1 cell ACTIVE** ·
88 NOT_IMPLEMENTED · 2 BLOCKED · 1 DARK · **141 gap-log entries, 98 OPEN, next free GG-303.**
Max claimed task ID across `git log --all`: **T-571.**

**Two findings from Wave 33 now govern everything downstream.**

1. **T4's founding thesis is measured and NOT SUPPORTED (T-569).** The pooled forward slope of
   `delta_mip` on `gross_edge` is **negative at every horizon k=1..4** (−0.021 → −0.030, CI excludes
   0 throughout) — the market moves *away* from the model, not toward it. The backward placebo
   slope is **5.1–6.4× larger** than the forward slope at every k, so the forward result does not
   clear its own pre-registered confound bar either way. Every T4 band, the 11-sub-band
   decomposition, and T4M-PROJ's ACTIVE status rested on this thesis.
2. **The only scorable cohort is 95.6% unverified, and reverses sign on the verified part
   (T-571).** Of 765 rows, **34 (4.4%) are independently confirmed as real Kalshi fills** (GG-300).
   Restricted to those 34, T4M-PROJ's calibration headline **reverses sign and turns net-negative**
   (GG-301). 42 NFL T1 rows traced to a single unlogged manual run and quarantined (GG-302).

**Read those together: the project's one live cell rests on a falsified thesis, and its one
scorable result does not currently stand on verified trades.** Wave 34 does not repair either
claim. It builds the instrument that can score a model without P&L, and it settles whether a
scorable cohort exists at all.

---

## ⬛ FIRE NOW — Wave 34, three blocks, concurrent

| Paste | Block | Tier | One-line purpose |
|---|---|---|---|
| 1st | **34.1** | STANDARD | **The closing-line-value harness.** Score a model without waiting for settlements or fills — the instrument every future cell inherits. |
| 2nd | **34.2** | STANDARD | **Does a scorable cohort exist at all?** Resolve the 731 unconfirmed rows, and test whether the 34 are a biased sample. |
| 3rd | **34.3** | SHORT | The resolved filter. Finish what 33.3 built warn-only, and correct CLAUDE.md's false structural claim. |

**Fire order does not matter.** 34.1 owns a new `scripts/` module + its own `exp_output/` dir and
touches no ledger. 34.2 owns the ledgers, the VPS reads, **and `GOVERNANCE_GAP_LOG.md` /
`DECISION_LOG.md`.** 34.3 owns `scripts/`-side governance tooling, `.claude/hooks/`, and CLAUDE.md
Step 3, and writes neither log.

**Standing split held: 2 calibration, 1 plumbing.**

**There are exactly three fences in this file. If you see a fourth, stop.**

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
| 10–30 | ✅ CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` and `11_MEMORY_HANDOFF/` |
| **31** | ✅ CLOSED — all three landed | Calibration finding **reproduced in full** (13/13 figures); ADR-0046 found **NOT COMPARABLE**; first real NFL settlement (20/42, +$13.4778); estate 58→20 branches, 61→25 worktrees. |
| **32** | ✅ **CLOSED — all three landed** | **32.1:** only genuine cost-assumption gap is T1 game markets running implicit `vig=0.00`; APR-0036 drafted; **71.5% of the 765 approvals flip to rejected at median measured spread.** **32.2:** `KXMLBHIT` ranks tie-group **3 of 5** — inefficient tail but NOT its end; CLAUDE.md's premise partially falsified. **32.3:** correctly **STOPPED** before funding (true demand 3,221 approvals/$3,095.80, 62% above the ring-buffer figure); **first-ever service-produced fill observed**; **GG-297: 139 of 140 "OPEN" positions are canceled/zero-fill phantoms.** |
| **33** | ✅ **CLOSED — all three landed at `b25fcb6`** | **33.1 / T-569 (PR #147):** T4 latency thesis **NOT SUPPORTED** under pre-registered criteria. 398,865 rows / 8,325 tickers, fresh VPS pull. Pooled forward slope negative at all k (−0.021→−0.030); backward placebo **5.1–6.4×** forward, so confound (b) unmet at every k; D2 signed statistic negative for AB and INNING events at all k. Brief's own premises falsified in passing: cadence p50 is **103.9s, not ~60s**; state-change rate **13.70%, not 9.8%**. Only the 0.70–0.90 price stratum is positive — smallest cell by 30×, still fails the placebo. **33.2 / T-571 (PR #148):** only **34 of 765 (4.4%)** rows Kalshi-confirmed as filled (GG-300); headline **reverses sign, turns net-negative** on those 34 (GG-301); 42 NFL T1 rows traced to one unlogged manual run and quarantined (GG-302); evidence-base table across all cohorts. **33.3 / T-570:** `retire_resolved_gaps.py` archive-mover proven on copies only; warn-only retirement-debt assertion in `governance_scan.sh`; operator-console Section 0 retirement-debt rollup; `sweep_stray_branches.sh` gains landed-branch cleanup + worktree prune; reverse register-parity rule. |
| **34** | ⬜ **FIRING** | CLV harness · cohort verification · the resolved filter. |

---

## Why this wave is shaped this way

Wave 33 was the first wave aimed squarely at the project's own foundations, and **both
foundational claims came back failed rather than merely qualified.** Wave 32's three results were
*partly* wrong. These two are not partial.

That changes what the next wave can usefully do. **It cannot calibrate T4, because T4's edge
mechanism is the thing that just failed measurement.** It cannot score anything on P&L either,
because the only cohort that could be scored is 95.6% unconfirmed and reverses sign on the
confirmed remainder. Both of the project's measurement paths are closed at the same time.

So Wave 34 rebuilds measurement capability rather than chasing a result.

**34.1 is the replacement instrument.** Closing-line value scores a model against the market's own
later price — no settlements, no fills, no accrual, no waiting a season. It is the arc's Wave 34
slot, and T-569/T-571 made it the critical path rather than a convenience. Note the honest prior:
T-569 found our edge signal predicting the market's forward move with the *wrong sign*, so the
expected CLV result is negative. **A negative CLV, cleanly measured, is a finding this project
needs — it is not a failed block.** The harness must therefore be built to the same confound
discipline T-569 used, including the backward placebo, or it will produce numbers nobody can trust.

**34.2 settles whether evidence exists.** T-571 confirmed 34 rows and left 731 unconfirmed —
unconfirmed, not disproven. Two questions decide the project's evidence base: what fraction of the
731 can *ever* be confirmed given Kalshi's actual retention window, and whether the 34 are a biased
sample. If the 34 differ systematically from the 731 on observables, GG-301's sign reversal is not
a correction to the headline — it is a different sample answering a different question, and that
distinction is load-bearing.

**34.3 closes the loop 33.3 opened.** The warn-only mechanism exists; the defect underneath does
not. `classify()` still has no resolved filter, 24 resolved-class entries still bucket as open, and
CLAUDE.md Step 3 still asserts that this is structurally impossible. A false claim in the
session-start protocol is worse than a missing one, because every session reads it as established.

**What this wave deliberately does not do.** It does not re-test the latency thesis under a new
specification, and it does not chase the 0.70–0.90 price stratum. T-569's verdict was
pre-registered; re-cutting the data until a stratum survives is the exact move the standing DO NOT
list prohibits. If that stratum is worth a block, it is worth a *fresh pre-registration on new
data*, and that is Wave 35's call to make with the model inventory in hand — not this wave's.

---

## ⬜ WAVE 34 — REBUILD MEASUREMENT

---

# 34.1 — THE CLOSING-LINE-VALUE HARNESS · SCORE A MODEL WITHOUT P&L · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "clv-harness"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 34.2 owns them. ***
*** Record gap candidates in your own results file for 34.2 to register. ***

TIER: STANDARD. This is the project's replacement measurement path.

ESTABLISHED -- VERIFY, DO NOT RE-DERIVE. Cite these; do not spend deliverables reproducing them.
  - T-569: the T4 latency thesis is NOT SUPPORTED. Pooled forward slope of delta_mip on
    gross_edge is negative at all k=1..4; backward placebo is 5.1-6.4x forward magnitude.
    Pre-registration and results are in 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/.
  - T-571: 34 of 765 rows Kalshi-confirmed (GG-300); headline reverses on those 34 (GG-301).
  - Cycle-log cadence is p50=103.9s, NOT ~60s. State-change rate is 13.70%, NOT 9.8%.

WHY THIS BLOCK EXISTS. Both of the project's measurement paths closed in the same wave. P&L is
unusable because the cohort is 95.6% unverified. The latency thesis is measured and failed. A
closing-line-value instrument depends on neither: it asks whether the price we entered at beats
the market's own later price, and it is computable from the price archive alone. Every future
cell inherits whatever you build here, so build the instrument, not a one-off script.

THE HONEST PRIOR, STATED UP FRONT SO IT CANNOT BE SPUN LATER. T-569 found our edge signal
predicting the market's forward move with the WRONG SIGN. The expected result of this block is
therefore that CLV is NEGATIVE. A cleanly measured negative CLV is a finding this project needs.
It is not a failed block, and it must not be presented as inconclusive to soften it.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR. Confirm b25fcb6 or later is your base.

DELIVERABLE 1 -- PRE-REGISTER, PUSH, THEN COMPUTE. IMMUTABLE ONCE PUSHED.
  Write and push BEFORE any statistic: the CLV definition; which observation you are calling the
  closing price and why (last pre-resolution sample, fixed horizon, or settlement-adjacent -- pick
  one and defend it); the horizon set; the test statistics; the clustering scheme; the backward
  placebo and mean-reversion controls you will run; and the exact thresholds for
  CLV POSITIVE / CLV NEGATIVE / INCONCLUSIVE. Do not relabel any of it afterwards.

DELIVERABLE 2 -- BUILD THE HARNESS AS A REUSABLE MODULE, NOT A SCRIPT.
  Input contract: (ticker, entry_ts, entry_price, side, size_or_none). Output: per-row CLV plus a
  cohort aggregate with cluster-robust SE (block-bootstrap, resampled by game AND by ticker --
  report both; rows within a ticker are not independent). The module must refuse, loudly, to score
  a row whose closing observation is missing rather than silently imputing one. Tests that fail on
  a deliberately malformed cohort are part of this deliverable.

DELIVERABLE 3 -- APPLY IT TO THE T4 MLB ARCHIVE.
  Pull logs/t4_mlb_cycle_log.jsonl FRESH from the VPS. The local mirror
  logs/.vps_t4_mlb_cycle_log_cache.jsonl stops 2026-08-07 and must NOT be the source.
  Report CLV for the model's own approvals, and for a matched RANDOM-ENTRY CONTROL drawn from the
  same tickers and time strata. The control is not optional -- without it a negative CLV cannot be
  separated from a market in which every entry loses to the close.

DELIVERABLE 4 -- THE CONFOUNDS, WITH T-569'S DISCIPLINE.
  (a) BACKWARD PLACEBO. Regress the price move that ALREADY HAPPENED before entry on the same
      signal. T-569's forward result died on exactly this test. If your backward slope is
      comparable to or larger than forward, say so and call the forward result an artifact.
  (b) MEAN REVERSION. Distinguish "price converges toward our model" from "price reverts toward
      its own trailing mean." Run both; report both slopes.
  A CLV number that has not passed (a) is not a result. Do not report one without it.

DELIVERABLE 5 -- STATE WHAT THIS INSTRUMENT CANNOT SCORE, AND WHY.
  Enumerate, against the 92-cell registry, which cells this harness could score today and which it
  cannot -- no price history, no entry timestamps, no model at all. That table is the direct input
  to Wave 35's model inventory, so make it complete rather than illustrative.

SCOPE FENCE. A new module under scripts/ and its own exp_output/ subdirectory. You touch NO
ledger, NO settlements file, NO accrual state, and NEITHER governance log. You do not activate,
deactivate, or re-status any cell. You do not submit an order of any kind.

CLOSE-OUT. Self-serialising: land, then write your session-close artifacts, then report.
REPORT BACK: the pre-registered verdict as it fell out; the approvals CLV and the control CLV with
CIs; the backward-placebo ratio; the can-score / cannot-score cell counts; and one paragraph an
operator can read without the statistics.
```

---

# 34.2 — DOES A SCORABLE COHORT EXIST AT ALL? · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "cohort-verification"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md AND DECISION_LOG.md THIS WAVE. ***
*** 34.1 and 34.3 will leave gap candidates in their results files. Register them. ***

TIER: STANDARD. This block decides whether the project currently holds any scorable evidence.

ESTABLISHED -- VERIFY, DO NOT RE-DERIVE.
  - GG-300: 731 of 765 rows (95.6%) in T4M-PROJ epoch-12's clean cohort have no independent
    Kalshi confirmation of ever being filled. 34 (4.4%) are confirmed real.
  - GG-301: the calibration headline reverses sign and turns net-negative on those 34.
  - GG-302: 42 NFL T1 rows traced to a single unlogged manual run; quarantined.
  - GG-297: 139 of 140 "OPEN" positions are canceled/zero-fill phantoms.
  T-571's results file is the source. Do not re-run its verification of the 34.

THE QUESTION. Unconfirmed is not disproven. Two things decide whether this project has an
evidence base, and neither is yet established.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR. Confirm b25fcb6 or later is your base.

DELIVERABLE 1 -- ESTABLISH THE RETRIEVAL CEILING EMPIRICALLY, NOT FROM DOCUMENTATION.
  What does the Kalshi API actually return for fills and order history at the age of these rows?
  Probe it: retention window, pagination limits, rate limits, whether canceled and zero-fill orders
  are retrievable at all at this age. Report the HARD CEILING -- the maximum number of the 731 that
  can ever be confirmed or refuted, with the measured evidence for that ceiling. If the ceiling is
  well below 731, that is the single most important sentence in your report.

DELIVERABLE 1b -- EXCLUDE THE LOOKUP-KEY EXPLANATION BEFORE YOU TRUST ANY "UNREACHABLE" COUNT.
  T-571 named this and explicitly did NOT exclude it: the ledger's `kalshi_ticker` may not match
  Kalshi's own indexing (normalization, series-prefix, or suffix differences). If the lookup key is
  wrong, a REAL filled trade returns zero orders and lands in "unreachable" -- and the entire
  95.6% figure is an artifact of our query, not a fact about the exchange.
  **This is the cheapest way the whole conclusion reverses, so test it first and report it first.**
  Take rows that ARE confirmed (the 34, plus any post-2026-09-01 row with a known good fill) and
  compare their `kalshi_ticker` string, character by character, against the ticker Kalshi returns
  for the same trade. Then take unreachable rows and probe alternate key forms -- series-level
  queries, event-level queries, date-bounded order listings without a ticker filter at all.
  If ANY unreachable row resolves under an alternate key, STOP the census and report immediately:
  the ceiling in Deliverable 1 is then measuring our own bug, and GG-300's headline number is
  provisional until re-derived with the corrected key.

DELIVERABLE 2 -- CONFIRM OR REFUTE AS MANY OF THE 731 AS THE CEILING ALLOWS.
  FOUR buckets, counted and reconciled to 731: CONFIRMED filled - REFUTED (canceled/zero-fill,
  positively established) - UNREACHABLE-BY-RETENTION (Deliverable 1's measured ceiling explains it)
  - UNREACHABLE-UNEXPLAINED. Every row in the last two carries the specific reason.
  **Do not collapse the two unreachable buckets.** "The record aged out" and "we cannot account for
  why this returns nothing" are different findings with different consequences, and merging them is
  how a lookup bug gets recorded as a retention fact. Write the per-row result to a durable artifact, not only a summary.

DELIVERABLE 3 -- THE SELECTION-BIAS TEST ON THE 34. PRE-REGISTER THE OBSERVABLES FIRST.
  Push the observable list before you test: entry price stratum, game_date, ticker, threshold,
  gross_edge at entry, inning, ab_remaining, and order size. Then test the 34 against the 731 on
  each, with a stated multiple-comparison handling.
  *** THE INTERPRETIVE POINT, AND IT IS LOAD-BEARING: if the 34 differ systematically from the
  731, then GG-301's sign reversal is NOT a correction to the headline. It is a different sample
  answering a different question, and the honest statement is that the headline is UNKNOWN rather
  than reversed. Say whichever your test supports, plainly, and do not blur the two. ***

DELIVERABLE 4 -- THE VERDICT PARAGRAPH, AND THE SHORTEST PATH OUT.
  Does this project hold a scorable cohort today? Yes / No / Only under stated conditions. If no,
  name what would create one and the shortest honest path to it -- and cost it in calendar time,
  not in blocks. Update GG-300, GG-301 and GG-297 with the resolution status each now carries.

DELIVERABLE 5 -- REGISTER THE WAVE'S GAP CANDIDATES.
  34.1 and 34.3 hand you candidates. Register each with its own GG, or record explicitly why not.
  Also register the still-unregistered candidate standing in this queue: generate_operator_console's
  classify() has no resolved filter and CLAUDE.md Step 3's "structurally impossible" claim is
  therefore false. 34.3 is fixing the code; the gap is yours to register.

SCOPE FENCE. Ledgers, VPS reads, the two governance logs. You do NOT build a scoring harness --
34.1 owns that. You do NOT modify generate_operator_console.py or .claude/hooks/ -- 34.3 owns
those. You do NOT re-status any cell.
ABSOLUTE: do not manufacture a position, a row, a cohort member, a fill or a final score to have
something to measure. Do not restart a production service. Demo only, always. If a permission
control refuses you, record the exact command and the exact refusal text and hand back.

CLOSE-OUT. Self-serialising: land, then session-close artifacts, then report.
REPORT BACK: the lookup-key exclusion result FIRST (Deliverable 1b) and whether it changes
anything; the retrieval ceiling and how you measured it; the 731 reconciliation in four buckets; the selection-bias verdict and whether the headline is reversed or unknown; the
scorable-cohort verdict in one paragraph an operator can act on.
```

---

# 34.3 — THE RESOLVED FILTER · FINISH WHAT 33.3 BUILT WARN-ONLY · SHORT

```
Run the CLAUDE.md session-start protocol in full. Paste outputs.
scripts/new_session_worktree.sh "resolved-filter"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU WRITE NEITHER GOVERNANCE_GAP_LOG.md NOR DECISION_LOG.md. 34.2 owns both. ***
*** Record gap candidates in your own results file for 34.2 to register. ***

TIER: SHORT. Four bounded deliverables. Do not expand this into a framework.

ESTABLISHED -- VERIFY, DO NOT RE-DERIVE.
  - T-570 landed the warn-only half: retire_resolved_gaps.py (proven on copies only), a warn-only
    retirement-debt assertion in governance_scan.sh, and an operator-console Section 0 rollup.
  - The live gap log at b25fcb6 holds 141 entries, 98 OPEN, and 24 resolved-class.
  - generate_operator_console.py's classify() has NO resolved filter, so every live entry buckets
    blocked/broken/accruing. It relies on T-420's guarantee that resolved entries were moved to
    GOVERNANCE_GAP_LOG_ARCHIVE.md. That discipline lapsed.
  - CLAUDE.md Step 3 states the archive split made it "structurally impossible" for the live log to
    contain a RESOLVED entry masquerading as open. That claim is FALSE as written.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR, AND LAND THE QUEUE. Confirm b25fcb6 or later.
  *** YOU OWN THE SHARED `main` TREE THIS WAVE. Do this before your worktree, before anything. ***
  The shared tree is ~21 commits behind origin AND holds the only copy of two uncommitted files:
  `04_EXECUTION/ACTIVE_QUEUE.md` (this wave's blocks) and `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`
  (which now contains Wave 33's recovered prompts -- they exist NOWHERE else, having been deleted
  from the queue during the Wave 34 rotation without being archived).
  (a) `git fetch origin`. Compare `git diff --name-only HEAD origin/main` against your dirty set.
      If ANY file is in both, STOP and report. Do not pull, stash, or check out over it.
  (b) `OPERATOR_CONSOLE.md` is generated by the governance hook; its diff is hook output, not work.
      Discard it (T-533 precedent). Leave "Reload Dashboard.command" and any `_w33_recovered.md`
      scratch file alone -- do not commit either.
  (c) `git pull --ff-only`. If it refuses, STOP and report the exact refusal. Never force.
  (d) Commit and push PATH-SCOPED, exactly these two paths: `04_EXECUTION/ACTIVE_QUEUE.md` and
      `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`. Never `git add -A`, `commit -a`, unscoped `stash`,
      `reset --hard`, or `clean -fd` -- 34.1 and 34.2 are live in this tree concurrently.
  (e) Verify: shared tree at origin/main, both files on origin, and `grep -c '^```'` on the queue
      returns 6 (exactly three fenced blocks).
  (f) The queue's archive rule was violated once already this week. Add the shared-tree-behind-
      origin count and "closed-wave fences still in ACTIVE_QUEUE.md" to Deliverable 3's Section 0
      roll-up, so both become visible debt instead of something a person has to notice.

DELIVERABLE 1 -- FIX classify(), TEST-FIRST.
  Enumerate the resolved-class status strings FROM THE LIVE LOG, not from memory -- the variants
  include RESOLVED, PARTIALLY RESOLVED, LIKELY RESOLVED, PARTIAL RESOLVE, ACCEPTED UNCERTAINTY and
  dated "RESOLVED (<date/task>)" forms, and there may be more. Write the failing test first, then
  the filter. A resolved-class entry must bucket as resolved, never as open/blocked/broken. Report
  the console's counts before and after.

DELIVERABLE 2 -- CORRECT CLAUDE.md STEP 3.
  Replace the false "structurally impossible" claim with what is actually true, and cite the
  measured distribution. This is a one-line-scale edit to the session-start protocol. A false
  claim there is worse than a missing one, because every session reads it as established.

DELIVERABLE 3 -- PROMOTE retire_resolved_gaps.py FROM PROVEN-ON-COPY TO GATED EXECUTION.
  Dry-run must remain the DEFAULT. Add an explicit --execute flag, an archive-destination
  assertion, and an idempotency proof (running twice is a no-op). Prove it on copies again under
  the new flag. *** DO NOT RUN IT AGAINST THE LIVE LOG IN THIS BLOCK. *** 34.2 owns that file this
  wave, and a concurrent rewrite of it is exactly the corruption this queue's surface split exists
  to prevent.

DELIVERABLE 4 -- THE GG-279 STRUCTURAL CHECK, MINIMALLY.
  One assertion plus one test: a deploy-vs-activation check that fails when a merged fix is not
  present in the running process. SHORT scope -- an assertion, not a framework. If it cannot be
  done in that scope, register the reason as a gap candidate and stop rather than growing the block.

SCOPE FENCE. scripts/ governance tooling, .claude/hooks/, tests/, and CLAUDE.md Step 3. Nothing
else. You do not touch ledgers, settlements, accrual, the two governance logs, or any cell status.
Never bypass, disable, or work around a permission control -- record the exact refusal and hand back.

CLOSE-OUT. Self-serialising: land, then session-close artifacts, then report.
REPORT BACK: console counts before/after the filter; the resolved-class variants you found; the
CLAUDE.md correction as committed; the idempotency proof; and whether GG-279's check fit in scope.
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

| Item | Plain English | What happens if it waits |
|---|---|---|
| **T4M-PROJ's ACTIVE status** — **NEW, and the biggest one** | T4M-PROJ is the only ACTIVE cell in a 92-cell registry. Its entire rationale is the thesis that the market lags live game state, and T-569 measured that thesis and found the market moving the *other* way. Separately, its calibration headline reverses sign on the 34 trades anyone can verify. The cell is still running and still sending demo orders. | It keeps accruing demo activity against a mechanism we have measured and failed. Nothing is at financial risk, but every day it runs adds rows to a cohort whose value is now in question — and the north star's T4 11-sub-band decomposition inherits the same problem. |
| **APR-0034** | Whether T4 MLB should stop sending demo orders. Was marked "likely moot" once shard 3 was funded. **T-569 makes it live again** — the question is no longer about demo hygiene, it is whether the strategy behind the orders exists. | Directly coupled to the row above. Deciding one effectively decides the other. |
| **APR-0035** | The n\* wall, reshaped twice. It is no longer "how many seasons to the gate," nor even "is this cohort worth accruing" — 34.2 is establishing whether the cohort exists at all. | G6 cannot close on P&L evidence in any practical horizon. Fifth week open. Wait for 34.2 before signing anything. |
| **ADR-0063** | Emergency-stop / bet-sizing hierarchy. Approved in chat 2026-09-18 — **still needs a signature row in `APPROVALS_REGISTER.md`.** | Until the register row exists, nothing downstream can cite it. Unchanged for a week. |
| **GG-292 / branch routing bucket B** | 9 branches, keep/kill, named above. Several predate ADRs that may have superseded them. `t4-nfl-nhl-scaffolding` in particular now reads differently. | Each is someone's finished work. One routing pass turns them into blocks or closes them out. Wave 35's plumbing slot is holding for it. |

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

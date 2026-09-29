# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates. A fence here for a wave the
> track marks CLOSED is a defect -- archive it before anything else.

**Verified against:** `origin/main = c4e555f` (2026-09-28). *This window cannot `git fetch`.*

**Live state at `c4e555f`:** 92 cells - 22 bands - 1 cell ACTIVE - **149 gap-log entries, 105 OPEN,
next free GG-311.** Shared tree ~38 behind origin -- derive from `origin/main` only.

> ### THE OPERATOR SCOPING DIRECTIVE IS STILL BINDING (2026-09-24)
>
> *"Our previous thesis regarding latency capture was proven incorrect -- but that is given our
> current architecture, our current calculations, our current scaffolding... Never think in
> ultimatums. Everything in science was proven impossible until it wasn't."*
>
> T-569's verdict is cited ONLY as **NOT SUPPORTED (current feature set)**. T-575 measured that
> feature set and the numbers are the justification for this entire wave:
>
> | Model | What it actually consumes |
> |---|---|
> | T4 MLB (the model T-569 tested) | 3 scalars + a threshold. Binomial PMF, `p = ba_l10`. **Zero game-state awareness.** |
> | T1 NFL (EXP-027) | **2 inputs** -- `off_epa`, `def_epa_allowed`, both aggregate sums. Pointed at NFL spreads. |
> | T2 MLB | Rule-based. No independent quantitative layer. |
>
> T-575's own words on the highest-value fix: a live score/leverage signal for T4 is *"the single
> highest-leverage addition to the model T-569 actually tested, since a binomial-only model with
> zero game-state awareness is close to the weakest plausible model for the latency thesis."*
>
> **Concurrent bets are modelled as INDEPENDENT.** Zero `correlat*` hits in `risk.py`. The only
> portfolio control is a blunt equity-wide `MAX_PORTFOLIO_DEPLOYMENT_PCT = 0.60`. ADR-0053 §2.5
> names a game-key correlation group and never authorised it. Parlays, clustered pipelines and
> honest exposure management all sit behind that one unwritten ADR.

---

## ⬛ FIRE NOW — Wave 36, three blocks, concurrent

| Paste | Block | Tier | One-line purpose |
|---|---|---|---|
| 1st | **36.1** | STANDARD | **`park_factor_hits` may be a dead feature T1 MLB has been scoring on.** Make it real or retire it. |
| 2nd | **36.2** | STANDARD | **Give T4 eyes.** Score/leverage signal into the exact model T-569 tested -- built, A/B-gated, ADR-drafted. Not activated. |
| 3rd | **36.3** | SHORT | Activate the GG-303 write fix (gated on authorization) and finish the operator console's Section 0. |

**Fire order does not matter.** 36.1 owns `mlb_features.py`'s park-factor path. 36.2 owns
`run_t4_mlb_live.py` and the A/B harness run. 36.3 owns the VPS deploy, governance tooling and
hooks, **and `GOVERNANCE_GAP_LOG.md` / `DECISION_LOG.md`.**

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
| 10-33 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **34** | CLOSED | Lookup-key explanation EXCLUDED. **GG-303: 395/731 rows carry fabricated `kalshi_order_id`s.** Confirmed-34 are a biased sample, so the calibration headline is **UNKNOWN, not reversed.** CLV harness built; INCONCLUSIVE; 1 of 92 cells scorable. |
| **35** | **CLOSED -- ALL THREE LANDED** (`c4e555f`) | **GG-303 mechanism found** -- retry-without-clearing REFUTED, write-boundary defect CONFIRMED and fixed (a write now refuses when Kalshi returns no order id). **Deliverable 4 BLOCKED pending restart authorization -- the fix is in the repo, NOT in the running process.** **T-577: cohort UNRECOVERABLE** (pre-registered, mechanically applied). **T-575 feature audit complete** + T-569 verdict corrected to its real scope. |
| **36** | **FIRING** | Kill a dead feature - give T4 game-state awareness - activate the write fix. |

---

## Why this wave is shaped this way

Wave 35 closed the evidence question with a clean negative: the cohort is **unrecoverable**, and
no amount of re-analysis changes that. So there is nothing further to extract from the past. The
only way forward is to make the next cohort worth having -- which means two things, and this wave
does both.

**Make the models see more.** T-575 produced a ranked, costed list of what is already on the shelf
and never reaches a model. 36.1 and 36.2 take the top two items. 36.1 is a genuine defect, not an
enhancement: `park_factor_hits` may be silently neutral, which would mean T1 MLB has been scoring
on a feature contributing nothing while implying it contributes something. 36.2 is the direct
answer to the operator's scoping directive -- give the model T-569 tested an actual view of the
game before anyone concludes anything about market latency.

**Make the ledger trustworthy going forward.** GG-303's fix exists and is not running. This
project has logged "a merge is not a deployment and a deployment is not an activation" as a named
failure mode (GG-279); a correctness fix sitting unactivated is that failure mode in progress.

**Both model blocks STOP at the ADR.** ADR-0004's frozen-model policy and ADR-0042 D2's
`DEFENSIBLE_IMPROVEMENT` holdout gate both apply: no enhancer reaches the live paper book without
clearing the A/B harness first. These blocks build, test, measure and draft. **They do not
activate.** That is the operator's signature, not a terminal's.

---

## WAVE 36 BLOCKS

---

# 36.1 -- IS `park_factor_hits` A DEAD FEATURE? - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "park-factor-dead-feature"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 36.3 owns them. ***
*** Record gap candidates in your own results file for 36.3 to register. ***

TIER: STANDARD. This is a suspected live defect, not a feature request.

T-575's feature audit, item 2 of its ranked list: `park_factor_hits` may be silently neutral. If
so, **T1 MLB has been scoring on a feature that contributes nothing while the code implies it
contributes something.** T-575's own framing: either make it real (needs a venue-identification
fallback) or remove it -- "the current silent-failure state is the worst of the three options."
Verify that claim yourself. T-575 was an audit, not a test.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR. Confirm c4e555f or later is your base.

DELIVERABLE 1 -- IS IT ACTUALLY DEAD? Measure, do not read.
  Trace `park_factor_hits` from definition to every consumer. Then measure on real historical
  feature rows: what values does it actually take across the dataset? If it is constant, near-
  constant, or defaulting to neutral for some share of rows, report that share exactly and say
  what drives the failure -- missing venue id, a lookup miss, a default that swallows the miss.
  If it is NOT dead, say so plainly and report what it really does. A refuted premise is a
  complete and correct outcome for this deliverable.

DELIVERABLE 2 -- WHAT HAS IT COST? Quantify before you decide the fix.
  Re-score a historical T1 MLB cohort with the feature as-is versus with it removed entirely.
  If the two are identical, that is the proof it contributes nothing and the number to report.
  If they differ, the feature is live and this block's premise is wrong -- report that instead.
  Use existing scoring code unchanged; do not write a parallel scorer.

DELIVERABLE 3 -- FIX OR RETIRE, AND SAY WHICH ON THE EVIDENCE.
  If repairable at reasonable cost (a venue-identification fallback), implement it and show the
  feature taking real, varying values on the same historical rows.
  If not, retire it explicitly: remove it from the feature contract and the model inputs, so no
  future reader believes a neutral column is signal. **Do not leave it in place with a comment.**
  Either path needs tests. Either path is a C2 feature-surface change and therefore needs an ADR
  drafted before it reaches a live model (ADR-0004 frozen-model policy) -- draft it, do not accept
  it. If the fix changes any live scoring behaviour, the ADR-0042 D2 `DEFENSIBLE_IMPROVEMENT`
  holdout gate applies before activation; note that requirement in the ADR.

DELIVERABLE 4 -- WRITE IT UP HONESTLY, INCLUDING THE BLAST RADIUS.
  Which cohorts, experiments or published figures were computed with this feature in the matrix?
  If it is dead, every one of those is unaffected in value but wrong in description -- name them
  so nobody re-derives a conclusion from a feature list that overstates what was used.

DO NOT: activate any model change. Draft the ADR; the signature is the operator's.
DO NOT: touch `run_t4_mlb_live.py` or `MLBLiveBatterState` -- 36.2 owns those.
DO NOT: change kelly_fraction, a cell status, or a gating constant.
DO NOT: repair, edit or re-stamp any ledger row. The cohort is UNRECOVERABLE (T-577); do not
  attempt to rehabilitate it as a side effect of re-scoring.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 36.3 owns them.
DO NOT: restart a production service.

SCOPE FENCE: `mlb_features.py`'s park-factor path and its feature contract, the T1 MLB consumer,
tests, one ADR draft under `03_DECISIONS/`, a results summary under RESULTS_SUMMARIES.

REPORT BACK: the measured value distribution and the exact dead/alive verdict; the with-vs-without
re-scoring delta; which path you took and why on the evidence; the ADR draft path; and the list of
prior figures whose stated feature set is now known to be overstated.
```

---

# 36.2 -- GIVE T4 EYES: SCORE AND LEVERAGE STATE - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "t4-game-state-signal"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 36.3 owns them. ***

TIER: STANDARD. This is the operator's scoping directive made into code.

T-569 found the T4 latency thesis NOT SUPPORTED. The model it tested is
`p_hits_gte_threshold(h_so_far, ab_remaining, ba_l10, threshold)` (`run_t4_mlb_live.py:687`) -- a
binomial PMF with `p = ba_l10`. Three scalars. T-575 ranked a live score/leverage signal as **the
single highest-leverage addition to that exact model**, calling a binomial-only model with zero
game-state awareness "close to the weakest plausible model for the latency thesis." Its note:
the score data is likely already reachable via the same ESPN feed T4 already polls.

**You are not re-testing the thesis. You are building the model that would make a re-test
meaningful.** T-569 stands at its stated scope. Do not re-run it.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR. Confirm c4e555f or later is your base.

DELIVERABLE 1 -- IS THE DATA ALREADY IN HAND? Verify T-575's "likely reachable" claim.
  Inspect the actual ESPN payload T4 already polls. Report exactly which of these are present,
  per poll, with field names: current score both teams, inning and half, outs, base state,
  pitcher identity, pitch count. For each: already parsed / present-but-discarded / absent.
  If score state is NOT in the payload T4 already receives, STOP and report what fetching it
  would require -- do not add a new data source inside this block.

DELIVERABLE 2 -- EXTEND THE STATE OBJECT. NO MODEL CHANGE YET.
  Extend `MLBLiveBatterState` (and the cycle-log row) to carry the game-state fields Deliverable 1
  confirmed are available. Log them. Change NO forecasting behaviour -- `p_t4` must be
  byte-identical to today's value on the same inputs. Prove that with a test.
  **This alone is worth the block**: it starts accruing the state data every future analysis needs,
  immediately, whether or not the model ever consumes it.

DELIVERABLE 3 -- BUILD THE ENRICHED MODEL AS A CANDIDATE, OFFLINE.
  A candidate `p_t4` that consumes score/leverage alongside the existing inputs. Justify the
  functional form in one paragraph -- why this shape, what it assumes. Keep it simple and
  defensible; a leverage-weighted adjustment beats an unexplainable one.
  **The existing model stays the live default. The candidate is not wired into any run path.**

DELIVERABLE 4 -- RUN THE A/B HARNESS. THIS IS THE GOVERNING GATE, NOT AN OPTIONAL STEP.
  ADR-0042 D2: no enhancer activates in the live paper book without clearing
  `DEFENSIBLE_IMPROVEMENT` in `scripts/ab_harness.py` holdout mode. Run candidate vs. incumbent
  there, on historical data -- **NOT on the T4M-PROJ ledger cohort, which is UNRECOVERABLE
  (T-577) and must not be used as a holdout for anything.**
  Report the harness's verdict exactly as it returns it. If it does not clear, say so plainly;
  a candidate that fails its gate is a real result and the block succeeded.

DELIVERABLE 5 -- DRAFT THE ADR. DO NOT ACCEPT IT.
  ADR-0004 frozen-model policy: a live C3 change needs a superseding ADR. Draft it with the
  harness verdict as its evidence, the functional form, what it assumes, and what it does not fix.
  State explicitly that activation requires the operator's signature and a `logic_epoch` bump.

DO NOT: wire the candidate into any live run path, or change the default model.
DO NOT: re-run, re-test or re-litigate T-569. It stands at its stated scope.
DO NOT: use the T4M-PROJ 765/905-row cohort as training, holdout or validation data.
DO NOT: add a new external data source, subscribe to anything, or modify a price-capture window.
DO NOT: change kelly_fraction, a cell status, or a gating constant.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 36.3 owns them.
DO NOT: touch `mlb_features.py`'s park-factor path -- 36.1 owns it.
DO NOT: restart a production service. Deliverable 2's logging change deploys only with the
  operator's scoped written authorization, and that is 36.3's lane this wave, not yours.

SCOPE FENCE: `run_t4_mlb_live.py`, `MLBLiveBatterState`, the cycle-log schema, the A/B harness run
and its output, tests, one ADR draft, a results summary.

REPORT BACK: the ESPN payload field inventory with present/discarded/absent per field; proof that
`p_t4` is unchanged after Deliverable 2; the candidate's functional form and its stated
assumptions; the A/B harness verdict verbatim; and the ADR draft path.
```

---

# 36.3 -- ACTIVATE THE WRITE FIX, FINISH SECTION 0 - SHORT

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg303-activate-section0"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md AND DECISION_LOG.md THIS WAVE. ***

TIER: SHORT. Two bounded deliverables. Do not expand either into a framework.

DELIVERABLE 0 -- LAND ANY UN-LANDED PREDECESSOR, AND LAND THE QUEUE.
  You own the shared `main` tree this wave. It is ~38 commits behind origin and may hold an
  uncommitted queue state. `git fetch origin`; compare `git diff --name-only HEAD origin/main`
  against your dirty set and STOP if any file is in both. `OPERATOR_CONSOLE.md`'s diff is hook
  output -- discard it (T-533 precedent). `git pull --ff-only`; never force. Then commit and push
  PATH-SCOPED: `04_EXECUTION/ACTIVE_QUEUE.md` and `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`, nothing
  else. Verify `grep -c '^```' 04_EXECUTION/ACTIVE_QUEUE.md` returns 6.

DELIVERABLE 1 -- ACTIVATE THE GG-303 WRITE FIX. *** GATED ON WRITTEN AUTHORIZATION. ***
  T-576 fixed the write boundary -- a position write now refuses when Kalshi returns no order id.
  The fix is on origin/main and is NOT in the running process. Deliverable 4 of that session was
  blocked because activation requires restarting `t4-mlb`, and the standing DO NOT forbids
  restarting a production service without scoped written authorization.
  **Check `04_EXECUTION/ACTIVE_QUEUE.md` under "Needs your decision" for an operator
  authorization line naming this restart. If it is absent, SKIP this deliverable entirely, say so
  in your report, and proceed to Deliverable 2. Do not restart on inference, urgency, or a verbal
  paraphrase. An absent authorization is a complete and correct reason to skip.**
  If present: deploy, restart within the authorized scope, and then PROVE the running process
  contains the fix -- not the file on disk (GG-279: a merge is not a deployment and a deployment
  is not an activation). Demonstrate a refused write reaching the audit log from the live service.
  Update GG-303 with what activation actually proved, and state explicitly that the 395 existing
  fabricated-id rows remain unrepaired.

DELIVERABLE 2 -- FINISH THE OPERATOR CONSOLE'S SECTION 0.
  33.3 and 34.3 built toward a retirement-debt roll-up and it is not finished. Complete
  **Section 0 -- "Overdue for retirement"** in `generate_operator_console.py`: one roll-up across
  all twelve departments. Required rows, each with a live count:
    unarchived resolved-class gaps in the live log - merged-but-undeleted branches - prunable
    worktrees - ADRs/APRs whose own file reads ACCEPTED with no `APPROVALS_REGISTER.md` row
    (ADR-0063 and APR-0035 are live examples) - session claims with no closure row -
    shared-tree-behind-origin commit count - closed-wave fences still present in ACTIVE_QUEUE.md
  Render it against the live repo and paste the output. This is the number the operator reads
  weekly instead of reconstructing the board by hand, so it must be correct on first render.

DO NOT: restart any service without the written authorization named in Deliverable 1.
DO NOT: repair, delete or re-stamp any ledger row, including the 395.
DO NOT: change any gap's status beyond GG-303's activation record. Section 0 FILES what is already
  marked done -- retirement is filing, never adjudication.
DO NOT: run the archive move against the live gap log this session; Section 0 only counts it.
DO NOT: delete any UNMERGED branch (17 outstanding, operator-routed, Hard Rule 11).
DO NOT: touch `mlb_features.py`, `run_t4_mlb_live.py` or the A/B harness -- 36.1 and 36.2 own those.

SCOPE FENCE: the VPS deploy for GG-303 if and only if authorized, `generate_operator_console.py`,
`.claude/hooks/`, tests, GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, and the two queue files.
Self-serialising close-out: re-read both logs fresh against HEAD immediately before writing.

REPORT BACK: the queue-landing result and the three-fence verification; whether the authorization
was present and, if so, proof the RUNNING process contains the write fix plus a refused write in
the audit log; Section 0 rendered against the live repo with all seven counts; and an explicit
statement that the 395 rows remain unrepaired.
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

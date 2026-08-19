# Terminal window prompts — 2026-08-03 strategic review

**Source:** `05_RESEARCH_EXPERIMENTS/STRATEGIC_REVIEW_2026-08-03_HANDOFF.md`
**Baseline:** `HEAD=32fb868` on `main`. Last claim closed 2026-08-04T00:50Z (T-412). Task IDs T-413+ are free; gap IDs GG-158+ are free.

## Wave structure

| Wave | Windows | Mode | Gate to next wave |
|---|---|---|---|
| **1** | A, B, C | **Parallel** — disjoint file ownership | All three merged to `main` |
| **2** | D, E | **Sequential** (D then E) — E consumes A's verdict | Both merged |
| **3** | F | **Alone** — restructures the gap log | — |

**Why the waves.** Wave 1's three windows own non-overlapping file sets. Wave 2's E cannot be written until A returns a verdict. Wave 3's F rewrites `GOVERNANCE_GAP_LOG.md` wholesale — anything registering a gap concurrently will conflict or be silently lost, so it runs with nothing else in flight.

## File ownership map — enforce this

| Window | Owns (may write) | Must not touch |
|---|---|---|
| A | `05_RESEARCH_EXPERIMENTS/` (new files), `scripts/` (new analysis script only) | the three Phase-0/1 docs, `src/`, ADR-0050 |
| B | `10_INFRA_OPERATIONS/` (new file), `deploy/` | all `0X_` planning docs except its own new file, `src/` |
| C | `MARKET_EXPANSION_ACTION_PLAN.md`, `MARKET_UNIVERSE_SURVEY_SPEC.md`, `SEGMENTED_POOL_ARCHITECTURE.md` | `src/`, ADR-0050, `05_RESEARCH_EXPERIMENTS/` |
| D | `03_DECISIONS/ADR/` (new ADR draft), `05_RESEARCH_EXPERIMENTS/` (new memo) | `src/`, `execution_bands.py`, anything sizing |
| E | ADR-0050 (amendment), `MARKET_EXPANSION_ACTION_PLAN.md` | `src/` |
| F | `GOVERNANCE_GAP_LOG.md` + generated console + `governance_scan.sh` | everything else |

**All six windows:** `DECISION_LOG.md`, `GOVERNANCE_GAP_LOG.md`, `TODO_NEXT.md`, `MEMORY_BANK.md`, `SESSION_CLAIMS.md` are shared. Write to them **last**, after `git fetch && git rebase origin/main`, re-reading the file fresh (Step 0e / Hard Rule 10), commit path-scoped, push immediately. Never `git add -A`, `git commit -a`, unscoped `stash`, `reset --hard`, `checkout -- <foreign>`, or `clean -fd`.

---

# WAVE 1 — run these three in parallel

---

## WINDOW A — Close Validation Check 6 (highest consequence on the board)

```
Run the CLAUDE.md session-start protocol in full, including Step 0a — launch an isolated
worktree via scripts/new_session_worktree.sh "vc6-vig-cascade". Two other windows are
running in parallel; do not work in the shared main tree. Claim T-413.

TASK: close the last open validation check under the project's only positive result.

PROJECT_ASSESSMENT_2026-07-30.md § 8, Validation Check 6 reads: "Re-run the § 2 robustness
table against paper_trader.py::open_position()'s actual four-branch vig cascade (L462-468)
rather than my reconstruction, to close the last assumption. Not done — needs the live
function, small."

The live function is at paper_trader.py:460-466 (not 462-468 — that citation was corrected
2026-07-31 and the corrected one is exact; verify it yourself before relying on it):

    if direction == "YES":      _directional_gross = gross_edge
    elif band == "T4M-PROJ":    _directional_gross = -gross_edge - 2.0*vig
    elif band == "T1":          _directional_gross = -gross_edge - 1.0*vig
    else:                       _directional_gross = -gross_edge
    fee_net_edge = round(_directional_gross - fee_per_contract, 6)

The -2.0*vig coefficient applies ONLY to the NO branch. YES gets no vig term at all.
PROJECT_ASSESSMENT § 2 describes its reconstruction as "applying the T4M-PROJ -2.0*vig
coefficient" without stating it was applied direction-conditionally.

DO:
1. Determine from the assessment's own text and any surviving script whether the epoch-8
   reconstruction applied the coefficient uniformly or direction-conditionally. If it cannot
   be determined, say so explicitly rather than assuming — that is itself the finding.
2. Rebuild the § 2 five-definition robustness table on the epoch-8 gate-valid cohort using
   the production cascade applied direction-conditionally. Five definitions: raw-2.0*vig,
   raw-1.0*vig, raw, stored gross_edge, stored fee_net_edge. Report n, total P&L, ROI,
   bootstrap P(profit) at 10k resamples, and tercile ROIs, per definition.
3. Report the epoch-8 YES/NO direction mix. (Epoch 12's is 92 YES / 49 NO.)
4. State plainly whether the § 2 headline — "the abs() defect, not the model, is what made
   T4 look negative" — survives, partially survives, or does not.

ALSO reproduce independently (do not take these on faith; I computed them from
logs/.vps_portfolio_cache_mlb_t4.json, last_updated 2026-08-04T03:28:20Z):
  epoch-12 closed n=141, P&L +$48.52 on $122.25 stake, ROI +39.69%, win 42.6%
  top 5 winners = 71% of P&L; excluding top 10 the cohort is -8.84% ROI
  LOW stratum n=30 at +167.78% ROI on 16.7% win rate
  0 of 83 epoch-12 tickers held both directions; 141/141 conform to ADR-0050 sizing
If any of these do not reproduce, that discrepancy outranks the rest of this task.

SCOPE FENCE: no src/ change. No sizing change. No epoch bump. No ADR. Do not touch
MARKET_EXPANSION_ACTION_PLAN.md, MARKET_UNIVERSE_SURVEY_SPEC.md, or
SEGMENTED_POOL_ARCHITECTURE.md — Window C owns those this wave. Analysis script goes in
scripts/ as a new file; results memo goes in 05_RESEARCH_EXPERIMENTS/ as a new file.

DELIVERABLE: 05_RESEARCH_EXPERIMENTS/VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md, plus the
reproducible script. Register a GG (GG-158+) only if the reconstruction proves to have been
wrong in a way that changes a recorded verdict.

REPORT BACK: branch name and commit range. Not a prose summary — I will read the diff.
```

---

## WINDOW B — Step-4 backfill + depth time-series status (the structural blind spot)

```
Run the CLAUDE.md session-start protocol in full, including Step 0a — launch an isolated
worktree via scripts/new_session_worktree.sh "step4-depth-status". Two other windows are
running in parallel; do not work in the shared main tree. Claim T-414.

CONTEXT: you have SSH. The strategic-review window does not — Step 4 (operational health)
has now been silently skipped three consecutive sessions from Cowork-hosted windows. That
is GG-154, registered and unstaffed. You are the only window this wave that can close the
current-state gap.

TASK 1 — run Step 4 for real and record it.
Run the full Step 4 block from CLAUDE.md verbatim (T1 MLB cron, t4-mlb systemd, T1 NBA both
log windows, both semantic-oracle counts, the recency-windowed staleness check, and the
dashboard OOM-restart probe). Paste raw output. Do not summarize.
Specifically confirm or refute: logs/.vps_portfolio_cache_mlb.json (the T1/MAIN book) is
4 days stale in the repo — last_updated 2026-07-31T06:35:06Z — while the T4 cache is current
(2026-08-04T03:28:20Z). Expected explanation is that T1 writes nothing at kelly_fraction=0,
so nothing refreshes it. CONFIRM that explanation against the VPS rather than accepting it.
If the T1 cache is stale for any other reason, that is a live finding and outranks Task 2.

TASK 2 — depth time-series status and an expiry date for the Phase 1 hold.
The price/depth archiver has been running since 2026-08-01 (cron in deploy/cron.conf, both
lines now carrying --depth-sample-per-family 2 as of T-412). Phase 1 is deliberately held
until depth distributions land — target 200+ observations per family. That hold is correct
and currently has NO expiry date, which is how a correct hold becomes drift.
Report, from the live VPS: observations accumulated per family to date, the daily accrual
rate, and the projected calendar date at which each family crosses 200. Then state a single
explicit re-check date.
Note the balanced sampler (_balanced_sample, T-412) only went live 2026-08-04T00:46Z — count
pre- and post-fix observations separately; pre-fix depth samples may be family-misattributed
per GG-155 and should not be pooled with post-fix ones without saying so.

SCOPE FENCE: read-only against the VPS except for confirming crontab state. No src/ change.
No new cron. Do not touch MARKET_EXPANSION_ACTION_PLAN.md (Window C owns it this wave) —
put your findings in a new file and Window E will fold the date in during wave 2.

DELIVERABLE: 10_INFRA_OPERATIONS/OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md — raw Step 4
output, the T1-cache verdict, the per-family observation table, and one stated re-check date.

REPORT BACK: branch name and commit range, plus the raw Step 4 output pasted in your reply.
```

---

## WINDOW C — Citation repair (four verified-wrong claims)

```
Run the CLAUDE.md session-start protocol in full, including Step 0a — launch an isolated
worktree via scripts/new_session_worktree.sh "citation-repair". Two other windows are
running in parallel; do not work in the shared main tree. Claim T-415.

CONTEXT: a verification pass on 2026-08-03 checked ten file:line claims across the Phase 0/1
docs against source. Six were exact. Four were wrong. Fix the four. Verify each against
source yourself before changing it — do not take my line numbers on faith, that is the whole
point of this task.

FIX 1 (highest consequence). MARKET_EXPANSION_ACTION_PLAN.md line 125, Phase 1 box 1.7:
  currently: "Full suite green (baseline 2,757 passed / 17 known-failed / 28 skipped)"
  actual current baseline: 2,792 passed / 8 known-failed / 29 skipped
  corroborated three times: PLAN.md:7, TODO_NEXT.md:11, SESSION_CLAIMS.md:171 (all 2026-08-02)
  The 2,757/17 figure came from PROJECT_ASSESSMENT_2026-07-30.md:120 and predates the GG-146
  partial fix. Re-derive the true current baseline by RUNNING the suite, not by copying my
  number. A gate that compares against a wrong baseline does not gate — a Phase 1 run would
  either flag 35 new passes as suspicious or treat 8 failures as an improvement and miss a
  real regression. Note the GG-146 known-failure count in the box so the next drift is visible.

FIX 2. MARKET_UNIVERSE_SURVEY_SPEC.md line 6 cites `kalshi_client.py:115` for
SERIES_MLB_PLAYER_HITS. The constant is at line 135.

FIX 3. SEGMENTED_POOL_ARCHITECTURE.md line 35: "53 of 83 files" reference player/threshold
shape. Actual: 55 of 89 .py files under tests/ (grep -rlE "player_id|player_name|
kalshi_threshold" --include="*.py" tests/). The doc pins itself to HEAD=00201fe and § 6
already labels this an upper bound — so re-measure at current HEAD and either update the
figure with its HEAD stamp or convert it to a command the reader runs. Prefer the latter;
a pinned count in a doc is a future drift by construction.

FIX 4. SEGMENTED_POOL_ARCHITECTURE.md line 28 says kalshi_client.py has "One series constant
(SERIES_MLB_PLAYER_HITS)". There are two: SERIES_PLAYER_POINTS = "KXNBAPTS" (L133) and
SERIES_MLB_PLAYER_HITS = "KXMLBHIT" (L135). Phase 1.3's registry has to absorb both. Flag in
the Phase 1 blast-radius table that the NBA constant is the dark-band case with no live
test coverage — it is the one most likely to break silently under a registry refactor.

THEN, the meta-task: these four are instances of a class. Every one is a doc citing source
that moved underneath it. Propose (do not build) the cheapest mechanism that would have
caught all four — e.g. a CI check that resolves file:line citations in 0X_ docs against
current source. Write the proposal as a short section in TODO_NEXT.md or as a GG (GG-158+),
your judgment. Do not build it this session.

SCOPE FENCE: no src/ change. Running the test suite is expected; changing tests is not. Do
not touch 05_RESEARCH_EXPERIMENTS/ (Window A) or 10_INFRA_OPERATIONS/ (Window B).

REPORT BACK: branch name and commit range, plus the raw test-suite summary line.
```

---

# WAVE 2 — after all three of Wave 1 are merged. D then E, sequentially.

---

## WINDOW D — T1 adjudication decision memo (unblocks the operator)

```
Run the CLAUDE.md session-start protocol in full, including Step 0a — launch an isolated
worktree via scripts/new_session_worktree.sh "t1-adjudication". Claim T-416.

CONTEXT: GG-153 is the only OPEN gap whose resolution requires an operator decision and has
no technical dependency. It has sat unstaffed since 2026-07-31. It is currently blocking
nothing operationally (T1 is at kelly_fraction=0, no capital at risk) and blocking one thing
permanently (any future T1 reactivation decision).

Read GG-153 in full first. Note that it explicitly retracts the "n=202 / 13-day frozen span"
framing that is still circulating in session briefs — that reading was a transient state
between epoch-9's zeroing and epoch-10's ALL_BANDS reset. Live state is clean_n=0,
structurally unable to increase. Do not restate the retracted framing.

TASK: produce a decision memo that lets Earl pick one of GG-153's three options in under
ten minutes. He is the sole reviewer and sole decision-maker; navigational friction is a
decision-quality risk. The memo must be short.

For each option, answer concretely — not in principle:
  (a) Adjudicate against the last clean cohort read before the epoch-10 reset.
      IS IT RECOVERABLE? Determine from the ledger + logic_epoch.py whether the pre-reset
      cohort can be reconstructed exactly, approximately, or not at all. This is the load-
      bearing unknown in the whole memo — answer it with a computation, not a judgment.
      If recoverable, state n, mean P&L/bet, win rate, cadence span, and what APR-0024's
      variance-derived n* would be against it.
  (b) Extend ADR-0050's fixed_stake_usd bypass to T1, sized depth-and-ruin-safe.
      What stake? Cite GG-135's ruin geometry and the fact that CLAUDE.md now states depth
      must be measured live, not looked up. What ADR would be required. What it costs in
      calendar time to reach n*. Whether it reopens a ruin surface ADR-0048 deliberately
      closed — answer honestly, this is the option's real cost.
  (c) Formally document T1 as permanently unmeasurable under the current regime.
      What exactly gets written where. What it forecloses. Whether it is reversible.

Then give your own recommendation with reasoning, and state what would change it.

SCOPE FENCE: memo only. No ADR accepted, no sizing change, no src/ change, no
execution_bands.py edit. You may DRAFT an ADR for whichever option you recommend, clearly
marked DRAFT / not accepted. Do not reopen T1 modelling — four candidate classes are
exhausted (GG-105 → GG-140 → T9/A1-A3 → G3/opp_sp) and that verdict is not in scope.

DELIVERABLE: 05_RESEARCH_EXPERIMENTS/GG153_T1_ADJUDICATION_MEMO.md, ≤2 pages.

REPORT BACK: branch name and commit range, and the answer to (a)'s recoverability question
in one sentence.
```

---

## WINDOW E — Epoch-12 citation rule + fold in Wave 1's outputs

```
Run the CLAUDE.md session-start protocol in full, including Step 0a — launch an isolated
worktree via scripts/new_session_worktree.sh "epoch12-citation-rule". Claim T-417.

PRECONDITION: Windows A, B, C and D must be merged to main before you start. Read Window A's
VC6 verification memo and Window B's depth status file first — this task consumes both.

CONTEXT: the epoch-12 cohort is the first out-of-sample test of the GG-142 abs()-gate fix.
As of 2026-08-04T03:28Z it reads n=141 closed, +39.69% ROI, bootstrap P(profit) 0.98. That
number is going to get cited. It must never be cited without its concentration profile:

  top 5 winners = 71% of total P&L
  excluding the top 10 winners the cohort is -8.84% ROI
  largest single position +$8.55 on a $1.00 stake = 18% of cohort P&L
  LOW price stratum (<10c, where the 10-contract cap binds): n=30, +167.78% ROI, 16.7% win
  n=141 over 3 game-days, 83 unique markets, against GG-046's bar of >=500 unique markets

The project already made the in-sample version of this mistake once — PROJECT_ASSESSMENT
2026-07-30 § 2 upgraded a claim on a larger sample and had to retract it in the same document.
The out-of-sample version is more dangerous because the number is bigger and sounds validated.

TASK 1: amend ADR-0050 § 8 (the committed analysis rule) so that any citation of the
epoch-12 cohort carries the concentration table and the price-stratum split. Structural, not
advisory — specify where the table is generated from and by what script, so it cannot drift
from the ledger. Recompute all figures yourself from live data before writing them in; the
cohort has grown since 2026-08-04T03:28Z (46 positions were open then).

TASK 2: fold Window B's stated depth re-check date into MARKET_EXPANSION_ACTION_PLAN.md as
an explicit dated item with a stated unpark threshold for Phase 1. The hold is correct; an
undated hold is drift.

TASK 3: if Window A's VC6 verdict changed any recorded conclusion, propagate the correction
to every document carrying the old figure. Enumerate consumers with grep before editing —
GG-072's rule: the incident is not closed until every consumer is enumerated and re-verified,
not just the one that prompted the investigation.

SCOPE FENCE: no src/ change, no sizing change. ADR-0050 amendment only — do not supersede it,
do not alter the $1.00 stake or the 10-contract cap.

REPORT BACK: branch name and commit range, plus the recomputed epoch-12 headline and
excluding-top-10 figures at your run time.
```

---

# WAVE 3 — alone. Nothing else in flight.

---

## WINDOW F — Operator console (GG-132 / GG-133)

```
Run the CLAUDE.md session-start protocol in full, including Step 0a — launch an isolated
worktree via scripts/new_session_worktree.sh "operator-console". Confirm via
04_EXECUTION/SESSION_CLAIMS.md that NO other session is live before you begin — this task
restructures GOVERNANCE_GAP_LOG.md wholesale and a concurrent gap registration will be lost
or conflict. Claim T-418.

CONTEXT: 31 gaps are OPEN. Exactly one of them (GG-153) needs Earl personally. He cannot
currently tell which. GG-132 and GG-133 are registered gaps about the documentation system's
own decay. The agreed fix was recorded 2026-08-02 and in SCALING_MANDATE_PARKED.md § "What
was already agreed" — it has not been built.

Build it, exactly as agreed, no more:
1. Split the gap log by status. OPEN stays in GOVERNANCE_GAP_LOG.md; RESOLVED and
   CLOSED-AS-ARTIFACT move VERBATIM to an archive file. The archive is append-only,
   complete, lineage-preserving — never weaken it. Nothing is summarized on the way across.
2. Structured status headers with narrative below a fold. Severity currently lives in how
   emphatically the prose is written, which is precisely why bolded entries hid from the
   session-start scan (GG-144). Severity must become a field.
3. Generate OPERATOR_CONSOLE.md on every governance scan. Ranked by "blocks operator," not
   by severity. Three sections: decisions blocked on Earl, what is accruing and its clock,
   what is actually broken. Never hand-patch a generated view — put a generated-file banner
   at the top.
4. Wire generation into .claude/hooks/governance_scan.sh.

CRITICAL REGRESSION RISK — read before you start. CLAUDE.md Step 3's anchored-OPEN scan and
governance_scan.sh both match on "^\| Status \| \*{0,2}OPEN". A restructure that changes the
status-row format silently breaks both, and that exact class of defect is GG-144 — an
unanchored pattern that matched 17 of 28 real entries and zero of the bold form, undetected
for weeks. It was also found and fixed in governance_scan.sh (GG-122, 2026-07-16) without
propagating to CLAUDE.md. You are now editing the thing both patterns depend on.
THEREFORE: before merging, run the CLAUDE.md Step 3 command and the governance scan against
the restructured file, and assert the OPEN count matches the pre-restructure count exactly.
Current count for the assertion: 31 real OPEN (21 plain + 11 bold, minus 1 GG-NNN template
row). If it does not match exactly, the restructure is wrong — do not "explain" the delta.

Update CLAUDE.md Step 3 and governance_scan.sh together in the same commit if the format
changes. They have drifted apart before.

SCOPE FENCE: no src/ change. Do not close, reword, re-severity, or re-scope any gap — this
is a structural move, not an editorial pass. Content moves verbatim or not at all.

DELIVERABLE: restructured GOVERNANCE_GAP_LOG.md, the archive file, generated
OPERATOR_CONSOLE.md, hook wiring, and the count assertion output pasted in your reply.

REPORT BACK: branch name and commit range, plus the pre- and post-restructure OPEN counts.
```

---

## Held, deliberately — do not start

| Item | Gate |
|---|---|
| Phase 1 abstraction repair (8 boxes) | Window B's depth re-check date + family verdicts |
| Phase 2 (minimal falsification experiment first, LL-009) | Phase 1 |
| Scaling mandate (`SCALING_MANDATE_PARKED.md`) | Phase 2's gate verdict |
| Measurement/execution decoupling | Not gated — but it is an L and would consume the wave. Schedule it as its own wave once F lands. |
| T1 modelling, any T4 sub-band activation, GG-145 `park_factor`, GG-094 MLB PRF layer | Standing freeze, `PROJECT_ASSESSMENT_2026-07-30.md` § 7.2 |

## What I will ask for on review

Branch name and commit range. Not the prose summary — a summary reproduces the executing
window's framing, which is what a review is supposed to be independent of. If a window
reports a verdict without a diff to read, treat that as the task not being done.

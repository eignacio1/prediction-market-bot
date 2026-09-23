# Active queue — ARCHIVE of closed block prompts

**These blocks are CLOSED. They are kept verbatim for provenance only.**
**Do not paste anything from this file into a terminal.** The live queue is
`04_EXECUTION/ACTIVE_QUEUE.md`, which by rule contains only blocks that are currently firing.

Archived 2026-09-23 from `ACTIVE_QUEUE.md` at `origin/main = 18b0e0d`, after the queue was found
carrying four closed waves' fences (29.1/29.2/29.3/30.1) alongside live ones — an operator caught
it. Rule adopted at the same time: **the live queue holds only active blocks.**

---

## Wave 31 — CLOSED 2026-09-23 (all three landed)

# 31.1 — CALIBRATION BENCHMARK · MODEL vs MARKET · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "calibration-model-vs-market"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md THIS WAVE. 31.2 owns them. ***
*** Record every gap candidate in your own results file for registration next wave. ***

TIER: STANDARD.

A Cowork strategic window computed the figures below on 2026-09-22 from the LOCAL mirror
`logs/.vps_portfolio_cache_mlb_t4.json` (last_updated 2026-09-21T01:57:35Z). They are a CLAIM.
Your job is to reproduce them from the LIVE ledger on the VPS, establish whether they are
comparable to the ADR-0046 baselines, and extend the benchmark. Nothing here is established.

  T4M-PROJ, clean_n=765, logic_epoch 12, games 2026-07-31 to 2026-08-13:
    Brier 0.2191 (ADR-0046 BRIER_BASELINE_MLB = 0.2190)
    ECE   0.0519 (ADR-0046 ECE_BASELINE_MLB   = 0.0680)
    observed base rate 0.4026, mean model_p 0.3976, skill vs climatology +0.089
    market Brier on the same 765 events 0.1890
    paired diff (model - market) +0.0301, se 0.0053, t=5.66
    day-clustered over 11 game-days +0.0593, se 0.0207, t=2.87
    cohort P&L +$39.73 total, +$0.052/bet, win rate 40.5%

  Outcome construction used: y = 1 if actual_hits >= kalshi_threshold else 0; p = model_p;
  market price = mid_price_at_entry (YES-side, verified against entry_price_paid on a NO row).
  Clean filter: prediction_market_bot.logic_epoch.is_clean_for_band(logic_epoch, "T4M-PROJ").
  Brier/ECE via c7_monitoring.monitor._compute_brier / _compute_ece (10 equal-width bins).

DELIVERABLE 1 -- PRE-REGISTER YOUR VERDICT CRITERIA BEFORE YOU COMPUTE ANYTHING.
  Write, commit and push, BEFORE running any analysis: what result would count as REPRODUCED,
  what would count as NOT REPRODUCED, and what magnitude of model-minus-market Brier difference
  you will treat as material. State the test you will use for significance and the clustering
  unit. Once pushed, these are immutable -- a pre-registered criterion may not be relabelled
  after seeing results (standing DO NOT).

DELIVERABLE 2 -- REPRODUCE FROM THE LIVE LEDGER, NOT THE MIRROR.
  Pull the live T4 portfolio from the VPS. Report its last_updated and its closed-position count,
  and say whether it differs from the mirror's 2994 closed / 765 clean. If it differs, the mirror
  was stale and the reproduction supersedes the claim -- say so plainly.
  Recompute every figure in the table above. Report reproduced / not reproduced per figure.
  If any figure does not reproduce, report what you got and STOP before Deliverable 4.

DELIVERABLE 3 -- ESTABLISH COMPARABILITY WITH THE ADR-0046 BASELINE. THIS IS THE WEAK JOINT.
  Read ADR-0046 and its derivation path. Determine whether its n=261 baseline was derived with
  the SAME outcome construction, the same clean filter, and the same ECE binning as Deliverable 2.
  If it was not, the Brier-vs-baseline and ECE-vs-baseline rows are NOT a valid comparison --
  say so explicitly and report both the comparable and non-comparable framings side by side.
  Do not silently reconcile them. The model-vs-market comparison does not depend on this and
  stands either way; say which of your conclusions survive and which do not.

DELIVERABLE 4 -- EXTEND THE MARKET BENCHMARK. THIS IS THE PART NOBODY HAS EVER RUN.
  Run the same model-vs-market paired Brier comparison on every band and every (market_type, band)
  cell with clean_n >= MIN_N, both sports, using each cohort's own clean-epoch floor. Report a
  table: cell, clean_n, model Brier, market Brier, paired diff, se, clustered diff, span in days.
  Then run it on the `rejected_positions` cohort (2000 rows in the mirror) -- the evaluations the
  risk engine refused. Those carry a model_p and a market price and no selection-by-approval,
  so they are the closest thing to a holdout this project has. Report whether the model-vs-market
  sign is the same there. Say clearly what that does and does not establish.

DELIVERABLE 5 -- WRITE IT UP AS EVIDENCE, NOT AS A RECOMMENDATION.
  `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/` -- the pre-registration, every figure with its n,
  se and clustering unit, the comparability verdict from Deliverable 3, and an explicit list of
  what you did NOT check. State the sample's limits in the summary itself: 765 bets but only
  11 game-days across 14 calendar days, one cell, one sport.

DO NOT: recommend against a sport, market family, band or cell on this finding. That is forbidden
  on one result (standing DO NOT) and is not what this block is for.
DO NOT: touch kelly_fraction or any sizing value, promote or demote a cell, or change a model.
DO NOT: change ADR-0046's baseline constants. If you conclude they are wrong or non-comparable,
  record it as a gap candidate for 31.2 to register and stop.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 31.2 owns them this wave.
DO NOT: touch the NFL portfolio, the settlement path or the runbook -- 31.2 owns those.
DO NOT: restart any service, submit any order, or modify a price-capture window.
DO NOT: manufacture a position, row, cohort member or final score to have something to measure.

SCOPE FENCE: a new analysis script under `scripts/`, its output under `exp_output/`, the results
summary under `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`, and read-only pulls from the VPS.
Self-serialising close-out: rebase onto origin/main before your final push.

REPORT BACK: the pre-registration as pushed; live-vs-mirror ledger comparison; reproduced /
not reproduced per figure; the comparability verdict on ADR-0046 and which conclusions survive it;
the full per-cell extension table; the rejected-cohort result and its sign; and your gap
candidates listed for 31.2, unregistered.
```

---

# 31.2 — GG-291 DELIVERABLE 5 · THE LIVE NFL SETTLEMENT · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg291-live-settlement"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md AND DECISION_LOG.md THIS WAVE. 31.1 and 31.3 do not write them. ***

TIER: STANDARD. This is the first end-to-end close of the loop in the project's history.

T-563 fixed the write path (`derive_kalshi_threshold()` / `KalshiThresholdUndefined` in
`kalshi_client.py`, called by both T1 game-market run scripts) and proved the not-yet-final guard
refuses correctly against a copy with real network calls. Deliverable 5, the live settlement,
never executed. Runbook: `04_EXECUTION/NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md`. Read it first.

On GG-295 (HIGH, OPEN): the 42 positions' thresholds were backfilled by an unidentified actor with
no commit anywhere in history and a false attribution to T-562. The operator has reviewed this and
authorized settlement to proceed. The basis is that T-563 established CONTENT provenance -- it
diffed against the pre-backfill snapshot and confirmed exactly 42 rows changed, only the three
fields kalshi_threshold/repaired_at/repair_ref on each, nothing else. What remains unestablished is
ACTOR identity, which needs VPS shell history and is queued separately. **Re-verify that diff
yourself against the snapshot before you settle. Do not take T-563's word or this block's word
for it.** If the diff does not reproduce exactly -- 42 rows, three fields, nothing else -- STOP and
hand back. That is a complete and correct outcome for this block.

DELIVERABLE 1 -- RE-ESTABLISH THE PRE-CONDITION YOURSELF.
  Re-run T-563's diff of the live NFL portfolio against
  `paper_portfolio_t1_nfl_game_market.pre_gg291_backfill_20260918T190405Z.json`.
  Paste the row count, the changed-field set, and an explicit statement that nothing else moved.
  Confirm the running code contains the write-path fix -- prove it from the running process, not
  from the file on disk (standing DO NOT).

DELIVERABLE 2 -- ESTABLISH WHICH GAMES ARE ACTUALLY FINAL. DO NOT ASSUME ~20.
  For each of the 42 positions, report the game and whether it is final per the real data source.
  The "~20 games played" figure in the handoff is unverified. Report the real count.
  A game that is not final must be refused by the not-yet-final guard, not skipped silently.

DELIVERABLE 3 -- BACK UP, THEN SETTLE THE FINAL POSITIONS ONLY.
  Back up first; verify the backup loads and its position set matches exactly before any write.
  Settle only positions whose games are final. Include the tie/ambiguity path --
  `check_settlement_ambiguity()` must REFUSE, not guess (GG-257).
  Stamp provenance on every row you write, per ADR-0055's precedent. This is the ledger whose
  provenance was already violated once; yours must be impeccable.

DELIVERABLE 4 -- PROVE THE WRITE. SIMULATION IS NOT SUCCESS.
  Re-run the five ADR-0055 STEP-2 assertions on the REAL file post-write.
  Run `python3 scripts/assert_ledger_invariants.py` and paste its summary. Do NOT pass --strict.
  Prove idempotency: run settlement a second time and show the file is byte-identical.
  Report the realized P&L per position and in aggregate, and the resulting NFL bankroll.

DELIVERABLE 5 -- CLOSE WHAT THIS ACTUALLY CLOSES, AND ONLY THAT.
  Update GG-291, GG-274 and GG-287 to reflect what the live settlement did and did not prove.
  GG-295 stays OPEN -- actor identity is not established by this block and must not be written
  as resolved. GG-203 stays PARTIALLY RESOLVED -- a settlement is not a fill.
  DECISION_LOG entry per Hard Rule 7, appended via heredoc, never via a multi-KB exact-match Edit.

DO NOT: settle a position whose game is not final, or work around the not-yet-final guard.
DO NOT: change settlement LOGIC (`yes_won`, the tie rule, the guard). Missing data is not a logic
  defect. If you believe the logic is wrong, register and stop.
DO NOT: write GG-295 as RESOLVED. Content provenance is not actor provenance.
DO NOT: open a new position. A fresh open cannot be settled in the same session (GG-287).
DO NOT: touch kelly_fraction, promote a cell, submit an order, or restart a service.
DO NOT: touch `scripts/` analysis code, `exp_output/`, or RESULTS_SUMMARIES -- 31.1 owns those.
DO NOT: touch `11_MEMORY_HANDOFF/` or rewrite git refs -- 31.3 owns those.
DO NOT: manufacture a final score. If a source is unavailable, refuse and report.

SCOPE FENCE: the NFL portfolio and its backup, the settlement path, the runbook, tests,
GOVERNANCE_GAP_LOG.md, DECISION_LOG.md.
Self-serialising close-out: re-read GOVERNANCE_GAP_LOG.md and DECISION_LOG.md fresh against HEAD
immediately before writing them (Hard Rule 10) -- 31.1 and 31.3 are running concurrently.

REPORT BACK: the re-verified backfill diff; the real final-game count per position; the backup
verification; the settlement results with per-position and aggregate P&L; the five assertions and
the invariant-script summary post-write; the byte-identical idempotency proof; and an explicit
statement of what this settlement did NOT prove.
```

---

# 31.3 — RECONCILE LOCAL main + CLEAN THE REF ESTATE · SHORT

```
Run the CLAUDE.md session-start protocol in full. Paste outputs.
*** DO NOT create a worktree for this block -- it operates on the shared repo's refs by design. ***
*** Read Step 0d before you touch anything: path-scoped commits only. Never `git add -A`,
    `git commit -a`, unscoped `git stash`, `git reset --hard`, `git checkout -- <foreign>`,
    or `git clean -fd`. 31.1 and 31.2 are running concurrently and may hold uncommitted work. ***
Claim your own IDs at run time (GG-236).

TIER: SHORT. One deliverable: make `origin/main` the true picture again, and leave the ref
estate honest. Both halves are mechanical -- nothing below requires a judgment call about whether
any work is still wanted. Anything that does require that judgment is explicitly out of scope.

Local `main` = `c8639fe` is not a descendant of `origin/main` = `e9a335d`. Verify both yourself
after fetching -- these SHAs are from a window that could not fetch and may be stale.
Expected shape: 2 commits local-only, 6 commits origin-only, merge-base `91878b3`.
  local-only:  c8639fe (2026-09-22 handoff docs), 8900567 (Wave 30 queue re-issue)
  origin-only: all of T-563, including 603265b which registered GG-295
The consequence being fixed: a session deriving state from the local tree reads 133 gaps / 93 OPEN
/ next free GG-293 and concludes GG-295 does not exist.

DELIVERABLE 1 -- FETCH, CONFIRM THE SHAPE, AND LAND THE STRANDED WORK.
  `git fetch origin`, then report the real divergence counts and merge-base.
  Land the local-only commits onto origin/main -- rebase or cherry-pick, path-scoped, preserving
  authorship. The content to preserve is `11_MEMORY_HANDOFF/NEW_WINDOW_PASTE_IN_2026-09-22.md`,
  `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-09-22.md`, and the current state of
  `04_EXECUTION/ACTIVE_QUEUE.md` (which now carries Wave 31 and is newer than commit 8900567).
  If the queue file conflicts, the WORKING-TREE version wins -- it is the live queue.
  Also land the three untracked 2026-09-15 handoff files in `11_MEMORY_HANDOFF/` if they are
  absent from origin; if they are already there, say so and leave them.
  Verify after: local main and origin/main agree, and GG-295 is present in the working tree's
  gap log with 134 headers / 94 OPEN.

  Housekeeping while you are in the refs: `git worktree list` shows a stale entry
  `ro_e9a335d` (detached, locked, checkout already gone) left by the Cowork strategic window --
  that window could not delete `.git/worktrees/ro_e9a335d` from its mount. Unlock and prune it.
  Two other sessions' stale worktree entries are also undeletable from that mount
  (`20260826T045926Z-t497-t1-flat-stake-wrapper`, `20260910T012346Z-gg267-per-row-model-provenance`)
  -- prune those too if you can, and report if you cannot.

DELIVERABLE 2 -- CLEAN THE ESTATE. MECHANICAL ONLY. NOTHING HERE NEEDS A JUDGMENT CALL.
  Census derived 2026-09-22 at `e9a335d` -- re-derive every count yourself after fetching.
  Expected: 58 remote branches, of which 40 are already fully merged into origin/main; 61
  registered worktrees, of which 59 are prunable (checkout directory already gone).

  (a) Delete every remote branch that `git branch -r --merged origin/main` reports as merged.
      Safety note you can rely on: "merged into an OLDER origin/main" still implies "merged into
      the current one," because the newer ref contains the older. A stale ref cannot make this
      check unsafe in the delete direction. Re-run it post-fetch anyway and use the fresh list.
      Delete the matching local branches too (`git branch -d`, never `-D` -- if `-d` refuses,
      that branch is not actually merged; leave it and report it).
  (b) `git worktree prune`. Several entries are locked or undeletable from some mounts
      (`ro_e9a335d` left by the Cowork window; also
      `20260826T045926Z-t497-t1-flat-stake-wrapper` and
      `20260910T012346Z-gg267-per-row-model-provenance`). Unlock and prune what you can.
      Report anything that still refuses and why -- do not force-remove a worktree whose
      checkout directory still EXISTS and contains uncommitted work.
  (c) Report the post-cleanup counts: remote branches, local branches, registered worktrees.
      Expected landing point: 17 unmerged remote branches and 2 live worktrees.

*** THE 17 UNMERGED BRANCHES ARE OUT OF SCOPE AND PROTECTED. ***
  They hold ~54 unique commits of real work and are queued for a Wave 32 operator routing pass.
  Do not delete, merge, cherry-pick, rebase or rename any of them.
  In particular DO NOT MERGE THEM: each is weeks behind main, so `git diff origin/main <branch>`
  reports up to 25,234 deletions -- that is main's later work the branch never saw, not content
  the branch removes. A merge would delete a month of work. This is why they are a separate,
  operator-authorized pass and not part of a cleanup block.

DO NOT: force-push, or rewrite any commit already on origin/main.
DO NOT: absorb, land, cherry-pick or delete any UNMERGED branch (Hard Rule 11, GG-292). Deleting
  an already-merged branch is not absorption -- its content is in main by definition. The 17
  unmerged branches are a separate operator-routed task and are NOT in scope here.
DO NOT: touch `03_DECISIONS/OPERATOR_CONSOLE.md` -- it has uncommitted local modifications whose
  owner is unknown. Report that it is dirty; leave it alone.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 31.2 owns them this wave.
DO NOT: touch `scripts/`, `exp_output/`, the NFL portfolio, or the settlement path.
DO NOT: resolve a conflict in any file 31.1 or 31.2 owns. Stop and hand back instead.

SCOPE FENCE: git refs and worktree metadata, `11_MEMORY_HANDOFF/`, `04_EXECUTION/ACTIVE_QUEUE.md`.
No file content outside `11_MEMORY_HANDOFF/` and the queue is edited by this block.

REPORT BACK: the real divergence counts and merge-base after fetching; exactly which commits you
landed and by what method; confirmation that no commit already on origin was rewritten; the
post-reconciliation gap-log counts (expect 134 / 94 / next free GG-296); the merged-branch delete
list with its count; the worktree prune result and anything that refused; and the final
branch/worktree counts against the expected 17 and 2.
```




---

## Waves 29-30 — CLOSED (29.1 never executed and was superseded by 30.1; 30.1 superseded by 31.2)

# 29.1 — GG-291 · MAKE THE 42 SETTLEABLE · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg291-threshold-backfill"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD. *** THIS GATES SUNDAY'S SETTLEMENT. It is the wave's priority. ***

All 42 open NFL T1 `nfl_moneyline` positions carry `kalshi_threshold: null`. The real resolver
crashes `TypeError: '>=' not supported between instances of 'float' and 'NoneType'` at
`paper_trader.py::settle_position()` (~line 983, `yes_won = actual_stat >= threshold`) on the first
position it reaches. `run_t1_nfl_game_market.py` and `nfl_exp027_adapter.py` never write the field;
`paper_trader.py:430` defaults it to `None`. The correct value is documented, not open to design:
`game_market_settlement.py`'s docstring states a moneyline is a spread at zero, so `0.0`.
Read `04_EXECUTION/NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md` (T-559) before starting -- it carries the
pre-flight step this block must satisfy.

DELIVERABLE 1 -- ESTABLISH THE FULL BLAST RADIUS BEFORE TOUCHING ANYTHING.
  How many positions, in every portfolio file, carry a null threshold? Check NFL T1 and the MLB T1
  game-market path (`run_t1_mlb_game_market.py`) -- it was built from the same pattern and probably
  has the same hole even though it has never opened a position.
  Which market types legitimately have a null threshold, and which do not? Moneyline is an implicit
  zero; spread and totals read `floor_strike`. Say which types are affected and which are fine.
  **Report before changing code.**

DELIVERABLE 2 -- FIX THE WRITE PATH FIRST, SO THIS STOPS HAPPENING.
  Stamp `kalshi_threshold` at open time for every T1 game-market type, derived per type, not
  hardcoded to zero for everything. Do it in both run scripts if Deliverable 1 shows both affected.
  Then make the silent default impossible: a settleable position must not be writable with a null
  threshold. Refuse, or raise, at write time rather than defaulting -- a silent `None` that only
  surfaces at settlement is exactly this defect.
  Tests: an opened moneyline carries 0.0; an opened spread carries its line; a position that cannot
  determine a threshold refuses rather than writing null.

DELIVERABLE 3 -- BACKFILL THE 42. THIS IS A LIVE LEDGER REPAIR. TREAT IT AS ONE.
  GG-228 applies: establish provenance before repairing a derived file. Back up first, verify the
  backup loads and its position set matches exactly, then write.
  Set `kalshi_threshold = 0.0` on the 42 `nfl_moneyline` positions ONLY. Stamp each repaired row
  with provenance (`repaired_at` / `repair_ref`) per ADR-0055's precedent.
  Nothing else in the file may change -- diff before and after and prove that only this field moved,
  on exactly 42 rows. If the count is not 42, stop and report.

DELIVERABLE 4 -- RE-RUN THE REHEARSAL AGAINST A COPY AND PROVE IT NOW WORKS.
  Repeat T-559's rehearsal on a fresh copy of the repaired file with synthetic finals: hand-verify
  the arithmetic per position, include a deliberate tie (`check_settlement_ambiguity()` must REFUSE,
  GG-257), and prove idempotency by running twice to a byte-identical result.
  **Do not settle the live file.** Sunday's games have not been played.
  Update the runbook with anything that changed, so Sunday's session discovers nothing new.

DO NOT: settle any live position. The games have not happened.
DO NOT: apply the rehearsal's disposable `0.0` data workaround to the live file as a shortcut in
  place of Deliverable 3's backed-up, provenance-stamped repair.
DO NOT: change settlement LOGIC (`yes_won`, the tie rule, the not-yet-final guard) -- this is a
  missing-data defect, not a logic defect. If you believe the logic is also wrong, register and stop.
DO NOT: touch kelly_fraction/sizing, promote a cell, or submit an order.
DO NOT: touch kalshi_client.py or the Kalshi account -- 29.2 owns those.
DO NOT: touch .claude/commands/ or scripts/close_session_claim.sh -- 29.3 owns those.

SCOPE FENCE: both T1 game-market run scripts, paper_trader.py's threshold write path, a backed-up
repair of the NFL portfolio, the runbook, tests, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the null-threshold census across both sports and all market types; the write-path fix
and its three tests; the backup verification and the before/after diff proving exactly 42 rows and
one field changed; the full re-rehearsal table with the tie case and the idempotency proof; and an
explicit go/no-go for Sunday.
```

---

# 29.2 — SHARD 3 · VERIFY FUNDING · RESTART MLB ACCRUAL · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg203-shard3-verify-restart"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

T-558 established GG-203's cause: `GET /portfolio/balance`'s `balance_breakdown` shows shard 0 =
$397.44 and shard 3 (Sports) = $0.00. Every order for 35 days failed because the account has no
collateral on the shard its markets live on. Adding `exchange_index` was tested and made no
difference. The operator has approved allocating demo collateral to shard 3 and may have already
done it. This block verifies and restarts accrual; it does not move funds.

*** GATE *** Read the per-shard breakdown FIRST and paste it.
  If shard 3 is still $0.00, **STOP**. Report the exact figures and hand back -- the allocation has
  not happened yet and nothing below can work. That is a complete and correct outcome for this
  block; do not proceed, and do not move funds yourself.

DELIVERABLE 1 -- PLACE ONE REAL ORDER AND SEE IT SUCCEED.
  Same isolated VPS-side demo-only method T-558 used: one currently-open KXMLBHIT market, the body
  exactly as `submit_order()` builds it, no `exchange_index` (T-558 proved it changes nothing).
  Paste the full request and full response.
  **A 201 here is the end of a 35-day outage.** If it still fails, paste the exact code and body and
  compare against T-558's recorded failures -- a NEW error is a new finding, the same error means
  the allocation did not take.
  Then cancel the order if it rested, so this diagnostic leaves no position behind.

DELIVERABLE 2 -- CONFIRM THE LIVE PIPELINE ACTUALLY RESUMES, NOT JUST A HAND-BUILT ORDER.
  `t4-mlb` has been evaluating and failing all along. Watch it across a real write cycle after the
  allocation: are `risk_eval_approved` events now followed by successful orders rather than
  `kalshi_order_failed`? Use T-547's own detector (`scripts/gg203_order_write_detector.py`).
  Report the approved-vs-failed counts for the current day and compare against the 100% failure
  baseline. **A hand-built order succeeding while the service still fails is a different problem --
  say so rather than declaring victory.**
  Remember GG-279: if the service needs a restart to pick anything up, say so and stop. No restart
  is authorized in this wave.

DELIVERABLE 3 -- MEASURE WHAT THE OUTAGE COST, ONCE, PROPERLY.
  35 days of `risk_eval_approved` with no fill. Report the count of approved-but-discarded
  evaluations across 2026-08-15 to today, and what that means for T4M-PROJ's `clean_n` against
  APR-0024's `n*` (T-554 measured `clean_n=765`, `n*=8,587`, ~198 clean bets/week).
  State plainly how much closer the gate would be had those 35 days accrued. This is the real cost
  of the outage and nobody has quantified it.

DELIVERABLE 4 -- CLOSE OR RE-SCOPE GG-203 HONESTLY.
  RESOLVED only if a real order succeeded AND the live pipeline is filling. If the order succeeded
  but the pipeline is not, split the remainder into a new gap and say exactly what is left.
  Note for the record that `exchange_index` propagation was tested and rejected, so no future
  session re-opens it.

DO NOT: move funds between shards or subaccounts. That is the operator's action on his account.
DO NOT: submit any order against PRODUCTION or with real funds, ever.
DO NOT: implement `exchange_index` propagation -- T-558 disproved it. Do not revive it.
DO NOT: restart any service. DO NOT: rotate the API key.
DO NOT: touch kelly_fraction/sizing or promote a cell.
DO NOT: touch the NFL portfolio, the resolver or the T1 run scripts -- 29.1 owns those.
DO NOT: touch .claude/commands/ or scripts/close_session_claim.sh -- 29.3 owns those.

SCOPE FENCE: an isolated diagnostic script, the order-write detector, kalshi_client.py only if a
proven defect blocks a success, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the per-shard breakdown; the full request/response of the diagnostic order; the live
approved-vs-filled counts against the 100%-failure baseline; the 35-day accrual cost in bets and in
weeks-to-n*; and GG-203's disposition with the exchange_index rejection recorded.
```

---

# 29.3 — INSTALL THE CLOSE-OUT FIX · SHORT

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "install-closeout-fix"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: SHORT.

Two commits have been stranded on the operator's LOCAL main tree for three waves:
  44b7fb5  Wave 27 queue          580e9c9  session-end closure-row fix + stray-branch sweep
They add `scripts/close_session_claim.sh`, `scripts/sweep_stray_branches.sh`, and Step 9 to
`.claude/commands/session-end.md`. None is on `origin/main`. Meanwhile 14 branches are stray
(GG-292) and T-554's closure row never pushed.
GG-289 records that an auto-mode classifier blocks edits to exactly these paths as Self-Modification
-- confirmed twice independently.

*** READ THIS BEFORE YOU START. IT IS NOT NEGOTIABLE. ***
The operator has approved THE CHANGE. He has not, and cannot, approve bypassing a permission
control, and neither can this block. If the classifier refuses you:
  - Record the exact command and the exact refusal text, verbatim, in your report.
  - STOP. Hand back.
  - Do NOT retry with a rephrased command, a different tool, a renamed file, a heredoc, an indirect
    write, or any other route around it. Attempting to defeat a permission control is a worse
    outcome than the fix not landing -- the fix is worth days, the control is worth more.
A clean refusal, recorded precisely, IS a successful outcome for this block.

DELIVERABLE 1 -- TRY IT ONCE, THE SIMPLE WAY.
    git fetch origin && git cherry-pick 44b7fb5 580e9c9 && git push
  If it succeeds, merge and confirm with `git merge-base --is-ancestor` after the merge, then:
    git ls-tree origin/main scripts/ | grep -E "close_session|sweep_stray"
    git show origin/main:.claude/commands/session-end.md | grep -c "Step 9"
  If the classifier refuses at any point, record and stop per the rule above.

DELIVERABLE 2 -- IF IT LANDED, FIX THE KNOWN FAILURE MODE BEFORE ANYONE RELIES ON IT.
  `close_session_claim.sh` has already half-failed once: T-554's run committed the closure row and
  could not push it (`1431cdd`, still local). Local main was ~66 commits behind, so the retry loop
  faced a large divergence. GG-289 suggests the classifier may have been the real blocker.
  Make the script fetch-and-rebase BEFORE its first push attempt rather than only after a rejection,
  and push the row from a purpose-built ref rather than from whatever `HEAD` happens to be.
  Then exercise it at your own close-out and verify your row is visible on `origin/main`.

DELIVERABLE 3 -- REPORT WHAT THE OPERATOR MUST DO BY HAND, IF ANYTHING.
  If the classifier blocked you, write the exact sequence he should run himself -- commands, in
  order, with the verification greps -- so he can land it in one pass without re-deriving anything.
  Keep it to a short fenced list. This is the deliverable when Deliverable 1 is refused.

DO NOT: bypass, disable, rename around, or otherwise defeat a permission control. See above.
DO NOT: merge any of the other 13 stray branches (GG-292) -- they are the operator's routing
  decision, not yours (Hard Rule 11). Report them, do not absorb them.
DO NOT: cd into the shared main tree or run reset/checkout/stash/clean against it (GG-101).
DO NOT: touch the NFL portfolio, the resolver or the run scripts -- 29.1 owns those.
DO NOT: touch kalshi_client.py or the Kalshi account -- 29.2 owns those.
DO NOT: touch kelly_fraction/sizing, promote a cell, submit an order, or settle a position.

SCOPE FENCE: the two cherry-picks, .claude/commands/session-end.md,
scripts/close_session_claim.sh, scripts/sweep_stray_branches.sh, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: whether it landed, with the ls-tree and Step 9 greps if so; the verbatim refusal text
if not; your hardening change and your own closure row verified on origin/main if you got that far;
and the by-hand sequence for the operator if the classifier blocked you.
```

---

# 30.1 — GG-291 · UNBLOCK AND SETTLE · STANDARD · URGENT

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg291-unblock-and-settle"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD. *** URGENT. This was claimed on 2026-09-18 and never executed -- the claim row
exists, no work followed, and the Sunday settlement window was missed as a direct result. ***

42 real NFL T1 positions are open. Their games ran 2026-09-20 through 09-28, so **20 of them are
now final and settleable** (18 on 09-20, 2 on 09-21) -- verify that count yourself, do not take it
from this brief. They cannot be settled because every one stores `kalshi_threshold: null`.

Derived fresh at `origin/main` 91878b3 (verify each before relying on it):
  - Crash: `paper_trader.py:983`  `yes_won = actual_stat >= threshold`, fed by `:977`
    `threshold = pos["kalshi_threshold"]`. `:831` reads the same field.
  - Default: `paper_trader.py:450`  `kalshi_threshold: int | None = None`.
  - `run_t1_nfl_game_market.py:390` and `run_t1_mlb_game_market.py:354` both call
    `open_position()` WITHOUT `kalshi_threshold`. Both sports have the defect; MLB's is latent
    only because it has never opened a position.
  - Correct values are documented, not a design question: moneyline is a spread at zero
    (`strike_type="structured"`, `floor_strike` null) -> `0.0`; spread/total/team-total carry
    `strike_type="greater"` with a real `floor_strike` (e.g. 7.5, 63.5) -> that value.
  - **Type trap:** the parameter is annotated `int | None`, but game-market thresholds are floats
    (7.5, 63.5). Fix the annotation as part of this, or you will ship a half-fix that silently
    truncates every spread and total.

DELIVERABLE 1 -- CENSUS FIRST, BOTH SPORTS, EVERY MARKET TYPE. Change nothing yet.
  How many positions in every portfolio file carry a null threshold, by sport and market type?
  Which types legitimately may be null and which never can? Confirm the 42 and report how many
  have a `game_date` strictly in the past as of now -- that is your settleable set.
  **Report before writing code.**

DELIVERABLE 2 -- FIX THE WRITE PATH IN BOTH SCRIPTS, AND CLOSE THE SILENT DEFAULT.
  Derive `kalshi_threshold` per market type and pass it at open time. Do not hardcode 0.0 for
  everything. Correct the `int | None` annotation to accept floats.
  Then make the failure loud: a settleable position must not be writable with a null threshold --
  refuse or raise at write time. A null that only surfaces at settlement is this whole defect.
  Tests: moneyline carries 0.0; spread carries its floor_strike as a float, unrounded; a position
  with no derivable threshold refuses rather than writing null.

DELIVERABLE 3 -- BACKFILL THE 42. LIVE LEDGER REPAIR -- TREAT IT AS ONE (GG-228).
  Back up first; verify the backup loads and its position set matches exactly.
  Set `kalshi_threshold = 0.0` on the `nfl_moneyline` positions ONLY, stamping each repaired row
  with provenance (`repaired_at` / `repair_ref`) per ADR-0055's precedent.
  Diff before and after and prove ONLY that field moved, on exactly the expected row count. If the
  count is not what Deliverable 1 found, stop and report.

DELIVERABLE 4 -- REHEARSE ON A COPY BEFORE TOUCHING THE REAL LEDGER.
  Follow `04_EXECUTION/NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md` (T-559). Fetch real finals for the
  settleable games on the VPS (GG-266: the Mac cannot TLS-handshake with ESPN) and cross-check
  every score against a second independent source -- paste both.
  Run the resolver against a COPY. Per position: derived actual_stat, threshold, YES/NO, P&L,
  hand-verified against the final score. Moneyline is final margin vs 0. If any game tied,
  `check_settlement_ambiguity()` must REFUSE (GG-257). Run twice, prove byte-identical.
  **Do not proceed to Deliverable 5 until every line of arithmetic is verified by hand.**

DELIVERABLE 5 -- SETTLE FOR REAL. First live settlement in this project's history.
  Only the positions whose games are final. Back up the live file and verify the backup first.
  Run under the existing lock discipline, then run again and prove the ledger is byte-identical.
  Report realized P&L and the resulting ledger state. Closes GG-274 and GG-287.
  **If you reach Hard Rule 8's context trigger before this deliverable, STOP and hand off.**
  Deliverables 1-4 landed cleanly are a complete, valuable session; a settlement rushed at 70%
  context against a live ledger is not. Say plainly which you did.

DELIVERABLE 6 -- ONE HONEST PARAGRAPH. Whatever the P&L, this is ~20 paper positions from a model
  whose own pre-registered gate returned UNDERPOWERED at clean_n=14 against n*=2,610. A win is not
  evidence of edge and a loss is not evidence against it. Write it so it cannot be misread.

DO NOT: settle any position whose game is not final. Verify each, do not infer from the date alone.
DO NOT: apply the rehearsal's disposable 0.0 data workaround to the live file in place of
  Deliverable 3's backed-up, provenance-stamped repair.
DO NOT: change settlement LOGIC (`yes_won`, the tie rule, the not-yet-final guard). This is a
  missing-data defect. If you believe the logic is also wrong, register and stop.
DO NOT: open any new position, or construct PaperTrader with a non-None kalshi_client.
DO NOT: touch kelly_fraction/sizing, MIN_BET_USD, _HARD_LIMITS, or promote a cell.
DO NOT: touch kalshi_client.py's order path or the Kalshi account. DO NOT: restart any service.
DO NOT: merge any of the 17 stray branches (GG-292) -- operator routing, not yours.

SCOPE FENCE: both T1 game-market run scripts, paper_trader.py's threshold write path and
annotation, a backed-up repair + settlement of the NFL portfolio, the runbook, tests,
gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the null-threshold census by sport and market type; your settleable count and how you
verified each game is final; the write-path fix and its three tests; the backup verification and
before/after diff; both independent score sources; the hand-verified rehearsal table; whether you
settled live and the realized P&L with its idempotency proof; and your Deliverable 6 paragraph.
```

---


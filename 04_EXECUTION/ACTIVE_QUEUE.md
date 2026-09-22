# Active queue — the only prompt file to read

**Verified against:** `origin/main = a2d827e` (2026-09-18, Cowork strategic window) — *may be stale; the window cannot `git fetch`. Run `git fetch origin` first. A LANDED call is safe from a stale ref; a "not landed" call is not.*
**Live state, derived by import not grep (2026-09-18):** 92 cells · **22 execution bands** · **1 cell ACTIVE** · 88 NOT_IMPLEMENTED · 2 BLOCKED · 1 DARK · 133 gap-log entries, **93 OPEN**, next free **GG-293**.
**42 NFL T1 paper positions open**, games from 2026-09-20. **Zero MLB positions entered in 35 days** (last: 2026-08-14T03:33:45Z). **14 unlanded remote branches** (GG-292).
**Operator approvals granted 2026-09-18:** shard-3 funding, GG-291 fix, close-out-fix install, ADR-0063 + APR-0035 dispositions.

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **A block in the wave fires immediately, concurrently with every other.** Work that must wait goes in "Queued next."
- **Deliverable 0 in every block: land any un-landed predecessor.**
- **Check your deliverables against real-world sequencing before starting (GG-287).** Do not accept a task that requires an event which has not happened yet.
- **A premise written in a block is a claim to verify, not a fact.**
- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. This is absolute and no operator approval in a block overrides it — an approval authorizes a CHANGE, never a bypass.
- **Push after each deliverable.** Verify a fix by importing and calling the real function. **Benchmark the real thing.**
- **A merge is not a deployment, and a deployment is not an activation** (GG-279).
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10–27 | ✅ CLOSED | see history |
| **28** | ✅ **CLOSED, ALL THREE LANDED** | **GG-203 root cause found** — shard-3 collateral is $0.00 (T-558) · **GG-291 caught before it could hit the live ledger** (T-559) · T-555 stray landed, GG-289 classifier block diagnosed, GG-292 registered (T-557). |
| **29** | ⚠️ **1 OF 3** — 29.2 gated STOP (shard 3 still $0.00); 29.3 landed via T-562; **29.1 claimed and never executed** | Make the 42 positions settleable before Sunday · restart MLB accrual · install the close-out fix |

### ✅ WAVE 28 — what actually happened

**GG-203, 35 days, solved — and not by the hypothesis everyone believed.** T-558 submitted one real KXMLBHIT order to demo twice: once as the bot builds it, once with `exchange_index: 3` added from the market's own record. **Byte-for-byte identical failure.** That killed the `exchange_index`-propagation theory outright, including the outside developer's matching fix, so D3 was correctly never implemented. Then D2 read something nobody had read before — `GET /portfolio/balance` returns a `balance_breakdown` array alongside the headline number: **shard 0 = $397.44, shard 1 = $0.00, shard 2 = $0.00, shard 3 (Sports, where KXMLBHIT lives) = $0.00.** Every prior read, including T-492's and T-556's, took the aggregate and saw a funded account. It was funded on the wrong shard the entire time. `market_not_found` → `user_not_found` → `insufficient_shard_balance` are three renderings of one missing allocation. **No code change can fix it.**

**The rehearsal paid for itself on its first run.** T-559 ran the real resolver against a full copy of the real 42-position portfolio with synthetic finals. It crashed — `TypeError: '>=' not supported between instances of 'float' and 'NoneType'` at `paper_trader.py::settle_position()`, on the first position. **All 42 positions carry `kalshi_threshold: null`.** `run_t1_nfl_game_market.py` never writes the field and `paper_trader.py:430` defaults it to `None`; `game_market_settlement.py`'s own docstring says the value should be `0.0` ("a moneyline is a spread at zero"). Without the rehearsal this would have hit the live ledger Sunday. A crash leaves the file byte-identical (backup runs first), so there was no corruption risk — but zero settlements and a manual rescue mid-run on the first real attempt. **GG-291, HIGH, gating Sunday.**

**We are blocked from fixing our own close-out process.** GG-289: the auto-mode classifier treats edits to `.claude/commands/session-end.md` and the two new scripts as Self-Modification and blocks them — confirmed twice independently, and the likely real reason T-554's closure row never pushed. The scripts are still absent from `origin/main`. 14 branches are now stray (GG-292), correctly registered rather than absorbed.

---

### ⬜ WAVE 30 — one block, fire alone

**29.1 was claimed on 2026-09-18 and no work followed. The Sunday settlement window was missed.** It is re-issued below as 30.1, now including the live settlement, since the games have been played. Fire it alone — it ends in the first live write to a real ledger.

### Wave 29 blocks (29.2/29.3 closed; 29.1 superseded by 30.1)

| # | Block | Tier | Why |
|---|---|---|---|
| 29.1 | **GG-291 — make the 42 settleable** | STANDARD | Games start Sunday. The resolver crashes on position one today. |
| 29.2 | **Shard 3 — verify funding, restart MLB accrual** | STANDARD | 35 days at zero. One allocation should end it; nobody has confirmed it does. |
| 29.3 | **Install the close-out fix** | SHORT | Two waves of strays; sessions are structurally blocked from installing the fix. |

**Surfaces:** 29.1 owns the NFL portfolio, `settle_position()` and the T1 run scripts. 29.2 owns `kalshi_client.py` and the Kalshi account. 29.3 owns `.claude/commands/` and `scripts/`.

---

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

## Queued next — not yet fired

**Wave 30 — settle for real.** Fires after 2026-09-20's games conclude, gated on 29.1 returning a
go. Follows `NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md` against the real ledger: fetch finals on the VPS
(GG-266), cross-check a second source, back up, dry-run against a copy, hand-verify, settle under
the lock, prove idempotency. Closes GG-274 and GG-287. **First end-to-end close in the project's
history** — and a win or loss across 18 games is not evidence of edge either way.

**MLB T1 game markets have never run live.** Same Floor-A fix applies and the path uses
`kalshi_client=None`, so GG-203 never blocked it. Blocked instead on the model question: its default
is `StubMLBGameMarketForecastModel`, and stub-sourced positions are worth nothing. Establish whether
EXP-026/HYP-011 produced a real forecaster before scheduling it.

**GG-292 — 14 stray branches.** Needs one operator routing pass: land, abandon, or archive, named
branch by branch. Not a block until you say which.

**GG-279 — deploy-vs-activation has no structural check.** One SHORT block.

---

## Needs your decision

| Item | Plain English | What happens if it waits |
|---|---|---|
| **ADR-0063** | Emergency-stop / bet-sizing hierarchy. Approved 2026-09-18 — **needs your signature in `APPROVALS_REGISTER.md` to take effect.** | Until the register row exists, nothing downstream can cite it. Thirteen days drafted. |
| **APR-0035** | The n\* wall. P&L gate is ~1.6 MLB seasons / ~11 NFL seasons away at measured effect sizes. Approved in principle 2026-09-18 — **which option?** | G6 cannot close on P&L evidence in any practical horizon until this is settled. |
| **APR-0034** | Whether T4 MLB should stop sending demo orders. | **Likely moot** — if 29.2 confirms shard 3 funded and filling, withdraw it. |
| **GG-292** | 14 stray branches, oldest ~13 days. | Each is someone's finished work. One routing pass from you turns them into blocks or closes them out. |

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
- Restart a production service without a scoped, written authorization. None is authorized in Wave 29.
- Add a cron entry for any T1 game-market run script without explicit operator authorization.
- Pre-assign T-/GG- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the running process contains it.
- Manufacture a position, a row, a cohort member, or a final score to have something to measure.
- Submit an order against the production Kalshi account or with real funds. Demo only, always.
- Revive `exchange_index` propagation — T-558 tested and disproved it.

# Active queue — the only prompt file to read

**Verified against `origin/main` = `16ee0b6`, 2026-08-25.** Note: a local checkout may still be at `8f5801c` — `git pull` before trusting a working tree. Cell registry, imported live: **53 cells — 1 ACTIVE, 2 BLOCKED, 1 DARK, 49 NOT_IMPLEMENTED** across 11 market types and 8 bands. Gap log: **60 OPEN**, of which **2 CRITICAL** (GG-166, GG-170) and 7 HIGH (now including **GG-203**). Re-derive before citing any of it.
**Free IDs:** T-496+ · GG-216+ · ADR-0059+ · APR-0033+ · EXP-025+
**Reserved per block:** T-492/GG-205 · T-486/GG-215 · T-493/GG-213 · T-487/GG-207 · T-495/EXP-024 · T-488/GG-208 · T-490/GG-210 · T-489/GG-209 · T-491/GG-212 · T-494/GG-214.
**Already spent:** GG-203 (T-482) · GG-204 (T-485) · GG-206 (T-484) · GG-211 (T-483).

---

## Read this first

**Prompt blocks below are the paste-in. Nothing else in this file is a task.** Block headings are wave coordinates — `# 5.1` is wave 5, slot 1 — so the sequencing track and the prompts share one numbering. Everything after "Needs your decision" is reference: read it to understand why the order is what it is, not to act on it.

**When a window closes, delete its prompt block and move its row up into the closed-wave table with a status marker and a one-line outcome.** The prompt text goes; the row stays. A closed wave that disappears from the table forces the next reader to comb git to work out what already ran — the exact failure this file exists to prevent. Full detail lives in `SESSION_CLAIMS.md`, `DECISION_LOG.md` and git; the table carries status + outcome only.

**GG numbers are pre-allocated per block, including for blocks not expected to need one.** Take the number your block names and no other. **A reservation is not an entry:** if your block registers nothing, say so in your CLOSED row and return the number.

**Deliverables parallelize; close-outs do not.** Each prompt carries a self-serialising close-out rule — do not remove it. T-482/T-483/T-484 hit two rounds of append-order merge conflicts in `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` on 2026-08-24 running three-wide; the rule works but it is not free.

---

## Where the build actually is

**The bot is alive and has been failing 100% of its order submissions for ten days.** T-482 ran Step 4 for real and found what three sessions of ledger-staring could not: `t4-mlb` is `active`, `NRestarts=0`, the cycle log and audit log are writing in real time — and since **2026-08-15T00:06:20Z** every single `risk_eval_approved` event is followed by a `kalshi_order_failed`, 1:1, daily counts matching exactly (372/372, 692/692, 281/281, 445/444, 1056/1057, 534/534, 180/180, 420/420, 1212/1212). **Roughly 5,200 approved bets, zero submitted.** Two distinct HTTP 404 bodies: `market_not_found` (first, 08-15) and `user_not_found` (most recent, 08-24), both from `component: "C5-PAPER"`. Two different reasons across the window means this is probably not one static misconfiguration — credential or session state, or a market-lookup path that fails differently by ticker. **GG-203, OPEN, HIGH. Registered and stopped. T-492 fixes it and it is the top of the board.**

That is worse than the dark-pipeline hypothesis this queue previously carried, and it kills that hypothesis: it is not GG-143's cold-start blindness. A correctly-evaluating process whose execution layer fails every time is invisible to every health probe except a manual read of the order-outcome audit trail. **Every liveness check the project owns reported healthy for ten days.**

**Operator directive, 2026-08-25 — T1 reopens.** T1 was zeroed by ADR-0048 on GG-135's ruin geometry and then frozen at `clean_n=0` by epoch-10's `ALL_BANDS` reset (GG-153). The directive is that the incoming market arms need it. **That reasoning holds and this queue previously had it wrong.** T1 is the multi-day pregame band, and it has only ever been measured on `KXMLBHIT` — player props, the worst possible market for a multi-day horizon: lineup risk, late scratches, rest days, thin books. The markets now being added — moneyline, spread, run line, totals — are game-level, priced days ahead, with no lineup risk at the game level, materially lower per-bet variance, and vastly greater supply. **GG-135's ~100%/yr kill-switch trip probability was computed on prop variance and does not automatically describe game-market variance.** It has to be re-measured, not assumed in either direction — that is T-494.

**Three facts that make the reopen cheap.** (1) The T1 cells **already exist**: the registry carries `T1` cells for `mlb_moneyline`, `mlb_run_line`, `mlb_game_total`, `mlb_team_total`, `mlb_partial_game`, `nfl_moneyline`, `nfl_spread`, `nfl_game_total`, `nfl_team_total` — all `NOT_IMPLEMENTED`, all scaffolded, none needing construction. (2) **Reopening T1 does not require un-zeroing any Kelly.** ADR-0050's flat measurement stake is exactly how T4M-PROJ accrues evidence at `kelly_fraction=0.0`; T1 can reopen on the same pattern, taking zero ruin exposure while its cells accrue. (3) **GG-153 dissolves under per-cell epoch scoping** — ADR-0054 (b), already sitting in the signature bundle. T1's frozen global cohort stops mattering once each cell carries its own clean floor.

**The convergence nobody has stated: Phase 2's model is a T1 model.** Boxes 2.2/2.3 fit NB/Poisson to team run totals and score against archived `KXMLBTOTAL` — a pregame, multi-day-horizon, game-level forecast. That is not a T4M-PROJ signal; T4M-PROJ is an in-play projection band and you cannot run it on a pregame distribution fit. **If gate 2.3 passes, the cell it activates is `(mlb_game_total, T1)`.** The plan never said so because the plan has no band axis at all — which is GG-172, and which is now T-491's central case rather than a scope footnote.

**Distance to live capital, unchanged by any of the above:** 1 of 53 cells ACTIVE · every live band at `kelly_fraction=0.0` · T4M-PROJ `clean_n=719` against `n*≈5,580` (13%), and it has accrued **nothing since 08-14** because of GG-203 · every paper fill ever recorded assumed at mid, never validated against the book (GG-157, an explicit G6 precondition) · ≤60s kill-switch SLA documented as 12× too slow for continuous evaluation (GG-038) · C7's drift-alarm ladder never invoked from any production path (GG-125) · every `_HARD_LIMITS` value carrying an unmet 2026-05-29 obligation to be revised via ADR at G6.

---

## Sequencing track — every block, run and unrun

**Status legend:** ✅ merged to `origin/main` · ⚠️ complete but NOT merged · ❌ assigned, never ran · ⏳ in flight · ⬜ not started
**Concurrency rule: fire one wave at a time, never mix waves.** Blocks inside a wave have disjoint file surfaces and are safe three-wide at most. **Every block writes `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` at close-out and those are not `merge=union`** — the self-serialising close-out rule in each prompt handles it, but T-482/483/484 still hit two rounds of append-order conflicts running three-wide on 2026-08-24. Three is the ceiling, not the target.

### ✅ WAVE 4 — closed 2026-08-24 (do not re-run; prompt blocks deleted per the rule)

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 4.1 | T-482 | Session-start Step 4 + T4 liveness | ✅ **merged** (#110/#111) | **Found GG-203** — engine alive, 100% order-submission failure since 08-15 |
| 4.2 | T-483 | Install queue + nav housekeeping | ✅ **merged** (#107/#108), **truncated at budget** | Installed an earlier draft; 10 `TERMINAL_PROMPTS_*` files left behind → T-486 |
| 4.3 | T-484 | Commit + extend `KXMLBTOTAL` outcome store | ✅ **merged** (#109/#112/#114/#115) | 239→329 rows, 224→307 resolved; GG-206 OPEN |
| 4.4 | T-485 | ADR-0057 — re-scope G6 off T1 | ⚠️ **NOT MERGED** — branch `ba09980` | ADR-0057 + GG-204 exist only on the branch; CLOSED row written for unlanded work → T-486 |
| 4.5 | T-486 | Install rebuilt queue | ❌ **never ran** — no claim, no branch | Re-issued below as Wave 5 |

### ⬜ WAVE 5 — RUN NOW · 3-wide · disjoint surfaces

| # | ID | Task | Status | Touches | Gate |
|---|---|---|---|---|---|
| **5.1** | **T-492** | **GG-203 — restore order submission** | ⬜ | `src/c5_execution/`, deploy config | none — **outranks everything** |
| 5.2 | T-486 | Install this file · land T-485 · finish cleanup | ⬜ | `04_EXECUTION/`, git branches, ADR-0057 note | none |
| 5.3 | T-493 | ADR-0058 — reopen T1 on the game-market axis | ⬜ | `03_DECISIONS/` (new file) | none |

**T-492 outranks everything, including the signature bundle.** The bot has approved ~5,200 bets it never placed. Until submission works every cell accrues at zero and every `n*` timeline is infinite. If you only run one thing, run 5.1.

### ⬜ WAVE 6 — after Wave 5 · 2-wide

| # | ID | Task | Status | Touches | Gate |
|---|---|---|---|---|---|
| 6.1 | T-487 | Phase 2 boxes 2.2 → 2.3 (EXP-022) | ⬜ | `05_RESEARCH_EXPERIMENTS/`, `scripts/` | T-486 |
| 6.2 | T-495 | NHL skeleton spike (reduced rigor) | ⬜ | `market_type_registry.py`, ticker grammar, `tests/` | T-492 out of `src/` |

*6.2 waits only because T-492 holds `src/c5_execution/`. It has no logical dependency on the sport axis — T-474 built NFL without one.*

### ⬜ WAVE 7 — after Wave 6 · 2-wide · **needs the signature bundle**

| # | ID | Task | Status | Touches | Gate |
|---|---|---|---|---|---|
| 7.1 | T-488 | GG-157 — fills vs the book, props **and game markets** | ⬜ | `scripts/` (new analysis), `exp_output/` | ADR-0055 D1 signed or deferred |
| 7.2 | T-490 | `--sport` axis through the power calc (box 3.4) | ⬜ | `run_power_calc.py`, `run_band_monitor.py`, `tests/` | **ADR-0054 (b) signed** |

### ⬜ WAVE 8 — after Wave 7 · 2-wide

| # | ID | Task | Status | Touches | Gate |
|---|---|---|---|---|---|
| 8.1 | T-489 | GG-038 — kill-switch SLA, T4 tier **and T1 tier** | ⬜ | `tests/` (new), `scripts/` | ADR-0055 D1 signed or deferred |
| 8.2 | T-491 | GG-172 — the band axis, T1 as the live case | ⬜ | `02_ARCHITECTURE_DESIGN/`, `04_EXECUTION/` docs | T-493 |

### ⬜ WAVE 9 — after Wave 8 · single

| # | ID | Task | Status | Touches | Gate |
|---|---|---|---|---|---|
| 9.1 | T-494 | GG-135 re-derivation on game-market variance | ⬜ | `scripts/`, `exp_output/` | T-493 **and** T-488's haircut |

*Single-block wave on purpose: it consumes T-488's output and its answer gates any nonzero T1 Kelly. Nothing should be racing it.*

### Value column — which of these actually shorten the distance to live capital

**Yes:** T-492 (nothing accrues without it) · T-493 (opens the band the new arms need) · T-488 (explicit G6 precondition) · T-489 (NFR-03 hard rule) · T-494 (gates nonzero T1 Kelly).
**No — evidence or scope work:** T-486 · T-487 (generality evidence, and the first T1 cell's case) · T-490 (blocks cell #2, not deployment) · T-491 · T-495 (supply for later).

---

# 5.1 — T-492 · GG-203 · Restore order submission

**Start when:** now. This outranks the signature bundle. Every cell accrues at zero until it lands.

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 — you need SSH for this one and the
whole block is about what Step 4 found. Paste every output.
scripts/new_session_worktree.sh "t492-gg203-order-submission"
scripts/claim_session.sh "T-492: GG-203 -- diagnose and fix 100% Kalshi order-submission failure" "T-492 / GG-205"

TIER: STANDARD. ONE deliverable: a root cause for GG-203, and a fix ONLY if the cause is unambiguous
and the fix does not touch sizing. Hand off at ~60% context.

ESTABLISHED by T-482 — verify, do not re-derive:
  t4-mlb is active, NRestarts=0, cycle log and audit log writing in real time.
  Since 2026-08-15T00:06:20.592Z every risk_eval_approved in audit_mlb_t4.jsonl is followed by a
  kalshi_order_failed, 1:1, ~5,200 events over 10 days. Two distinct HTTP 404 bodies, both from
  component "C5-PAPER":
    {"error":{"code":"market_not_found","message":"market not found"}}
      first occurrence 08-15T00:06:20Z, ticker KXMLBHIT-26AUG141910SDCLE-SDJMERRILL3-1
    {"error":{"code":"user_not_found","message":"user not found"}}
      most recent 08-24T23:28:11Z, ticker KXMLBHIT-26AUG241840TBDET-TBJCAMINERO13-1
  Two different reasons across one window suggests shifting state, not one static misconfiguration.

TASK 1 — classify the two 404s over the whole window before theorising. Count market_not_found vs
user_not_found by day. If the mix shifts on a date, that date is the second event and matters more than
the first. Report the by-day table.

TASK 2 — the cheapest hypothesis first: `user_not_found` is an account/credential-scope 404, not a
market 404. Check what changed around 2026-08-15T00:06Z — a credential rotation, an expired key, a
BOT_ENV/base-URL change, a Kalshi API version or auth change. GG-152 (RESOLVED, archived) is the
_kalshi_base_url() vocabulary-mismatch class: any non-"live" BOT_ENV silently routes to the demo
sandbox, where a live account legitimately does not exist. It is RESOLVED — verify it stayed fixed
rather than assuming, and check the deployed env on the VPS, not the repo default.

TASK 3 — market_not_found on a KXMLBHIT ticker: confirm whether the ticker the bot submits still
resolves against the live venue. Compare a failing ticker string against a currently-open market
fetched directly. T-472 replaced the date-derivation regex with a refusal-only per-series grammar
registry on 08-20 — that is AFTER the 08-15 onset, so it is not the cause, but check it did not
introduce a second, different malformation on top.

TASK 4 — ask the question the audit trail raises: why is a component named C5-PAPER submitting orders
to Kalshi at all? If paper trading is meant to simulate fills, a real order submission is either a
deliberate market-validation step or a live-path leak. Establish which, and say so plainly. If it is a
live-path leak, REGISTER AND STOP — do not fix it in this session; that is a live-capital-path change
and needs an ADR.

HARD STOP: if the cause is not unambiguous, STOP and write up the ruled-out list. Do NOT "fix" an
execution path on a guess — the failure is currently loud, contained, and costing only measurement.
A wrong fix that silences the alarm is worse than the alarm.

SCOPE FENCE: src/prediction_market_bot/c5_execution/ and deploy config. Do NOT touch any
kelly_fraction, risk.py thresholds, the ledger, or paper_trader.py's fill logic.
Amend GG-203 with what you find; GG-205 is reserved for anything genuinely new. Return it if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; the by-day 404 mix; the cause in one sentence with evidence, or the
ruled-out list; whether C5-PAPER submitting live orders is intended; how many days of accrual were lost.
```

---

# 5.2 — T-486 · Install this file, and land T-485

**Start when:** now, first terminal that frees. T-483 landed an earlier draft that had no prompt blocks in it. **T-485 completed its work but never merged** — ADR-0057 exists only on a branch.

```
Run the CLAUDE.md session-start protocol. Steps 0-3 and Q2, paste outputs. SKIP Step 4 — T-482 ran it
in full on 2026-08-24; read GG-203 before doing anything else.
git pull first — a local main may be stale at 8f5801c while origin/main is 16ee0b6.
scripts/new_session_worktree.sh "t486-queue-rebuild"
scripts/claim_session.sh "T-486: install rebuilt ACTIVE_QUEUE + land T-485's ADR-0057 branch" "T-486 / GG-215"

TIER: MICRO. ONE deliverable: the queue file and T-485's branch both on origin/main.

1. T-485 IS UNMERGED. Branch session/20260824T233621Z-t485-adr0057-g6-rescope, tip ba09980, carrying
   03_DECISIONS/ADR-0057_g6-cell-scoped-rescope-decision-request.md and GG-204. Verify with
   `git merge-base --is-ancestor ba09980 origin/main` (expect: not an ancestor), then open and merge
   the PR. This is a GG-186 near-miss: T-485 wrote a CLOSED row for work that never reached main.
   Do NOT re-register it as a new gap — amend GG-186's entry with this instance.
2. Replace 04_EXECUTION/ACTIVE_QUEUE.md wholesale with
   11_MEMORY_HANDOFF/ACTIVE_QUEUE.rebuild_2026-08-25.md, then DELETE the rebuild file.
   Diff against what T-483 landed first and port across anything T-483 wrote that the rebuild does not
   carry. T-483 truncated at budget, so check its handoff stub for unfinished items.
3. T-483's file cleanup did not complete — 10 TERMINAL_PROMPTS files remain in 04_EXECUTION/.
   Delete the untracked TERMINAL_PROMPTS_WAVE{2,4,5,6,7,8,9}.md and TERMINAL_PROMPTS_GG163_HOTFIX.md,
   `git rm` the tracked TERMINAL_PROMPTS_2026-08-03.md and TERMINAL_PROMPTS_T432_HANDOFF.md.
   Verify each is superseded before deleting; do not delete anything with unexecuted content.
4. ADR-0057 PREMISE AMENDMENT, one paragraph, do not rewrite the ADR: it argues G6 should be re-scoped
   off T1 partly because T1 is permanently dead. Operator directive 2026-08-25 reopens T1 on the
   game-market axis (see T-493). The RECOMMENDATION is unaffected — a band-scoped gate still cannot
   express a 53-cell portfolio — but the premise is now false and must not be signed as written.
   Add the amendment note. Leave Status PROPOSED.

SCOPE FENCE: 04_EXECUTION/ nav files and the ADR-0057 amendment note only. Do NOT touch src/,
scripts/, or any other ADR.
GG-215 reserved. Register nothing you did not find; return the number if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if a claim older than
yours has no CLOSED row, wait and re-check. <=10% context, <=10 min, DECISION_LOG append-only via
heredoc. Assert your branch reached origin/main before writing CLOSED (GG-186).

REPORT BACK: branch + commit; T-485 merge confirmation; what you ported from T-483; files deleted.
```

---

# 5.3 — T-493 · ADR-0058 · Reopen T1 on the game-market axis

**Start when:** after T-486. Independent of T-492 — can run alongside it.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
SKIP Step 4 and say so — T-482 ran it; read GG-203 first.
scripts/new_session_worktree.sh "t493-adr0058-t1-reopen"
scripts/claim_session.sh "T-493: ADR-0058 -- reopen T1 on the game-market axis, measurement only" "T-493 / GG-213"

TIER: STANDARD. ONE deliverable: ADR-0058, Status PROPOSED. Do NOT mark it ACCEPTED. Do NOT change any
kelly_fraction, cell status, or band config in this session. This is a decision record, not an
implementation.

OPERATOR DIRECTIVE, 2026-08-25: T1 reopens. The incoming market arms need it. This SUPERSEDES the
standing "do not reopen T1" instruction that appeared in every carry-forward through 2026-08-24 —
that instruction was correct for player props and wrong as a general claim, for the reason below.

THE REASONING TO VERIFY, NOT ASSUME:
  T1_MULTI_DAY is the multi-day pregame band and it has only ever been measured on KXMLBHIT — player
  props, structurally the worst market for a multi-day horizon (lineup risk, late scratches, rest days,
  thin books). ADR-0048 (2026-07-29) zeroed its kelly_fraction on GG-135's finding that MAIN's variance
  alone produces ~100%/yr kill-switch trip probability at any positive Kelly. Then epoch-10's
  ALL_BANDS reset cleared its clean-epoch floor, freezing clean_n at 0 (GG-153, OPEN,
  Blocked-On-Operator). Read GG-135, GG-105, GG-142, ADR-0040, ADR-0048 and GG-153 directly.
  The load-bearing question: GG-135's ruin geometry was computed on PROP variance. Game markets
  (moneyline, spread, run line, totals) have materially different per-bet variance and no lineup risk.
  Whether the ruin conclusion transfers is an EMPIRICAL question and it is T-494's, not yours.
  Do not assert either answer in this ADR. Scope T1's reopening so it does not depend on it.

WHAT THE ADR SHOULD PROPOSE — verify each premise before writing it:
  1. Reopen T1 as CELLS, not as a band-sizing change. Confirm by importing the registry that T1 cells
     already exist at NOT_IMPLEMENTED for mlb_moneyline, mlb_run_line, mlb_game_total, mlb_team_total,
     mlb_partial_game, nfl_moneyline, nfl_spread, nfl_game_total, nfl_team_total. If that holds,
     reopening is an authorization, not a construction job. Say so.
  2. Reopen at kelly_fraction=0.0 on ADR-0050's FLAT MEASUREMENT STAKE pattern — the same mechanism
     by which T4M-PROJ accrues evidence today at zero Kelly. This takes zero ruin exposure while the
     cells accrue, which is what makes the reopen safe without waiting on T-494. Confirm ADR-0050's
     mechanism actually generalises off T4M-PROJ before proposing it; if it is T4-shaped, say so and
     propose what would have to change.
  3. State the dependency on ADR-0054 (b), per-cell epoch scoping, which is in the signature bundle
     and unsigned. Under per-cell floors, GG-153's frozen global T1 cohort stops being load-bearing —
     each cell carries its own clean floor. Propose GG-153 as CLOSABLE-ON-(b), not as closed.
  4. Enumerate what a nonzero T1 Kelly would require, and make it explicit that this ADR authorizes
     none of it: T-494's variance re-derivation, ADR-0048's edge-conditional reactivation lookup
     table, and a fresh operator signature.
  5. Note the sequencing consequence for Phase 2: if gate 2.3 passes, the cell it is evidence for is
     (mlb_game_total, T1). Cross-reference T-487 step 0(e).

Also flag, do not resolve: ADR-0057 (PROPOSED, T-485) argues G6 should be re-scoped off T1 partly
because T1 is dead. T-486 is adding a premise-amendment note. Confirm it landed; if it did not, say so
in your CLOSED row rather than editing ADR-0057 yourself.

SCOPE FENCE: 03_DECISIONS/ only. Do NOT touch src/, execution_bands.py, the cell registry, any
kelly_fraction, or ADR-0048.
GG-213 reserved. Register nothing you did not find; return the number if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit; whether the T1 cells and ADR-0050's flat-stake mechanism verified as
described; anything in the premise you could NOT confirm.
```

---

# 6.1 — T-487 · Phase 2 boxes 2.2 → 2.3 (EXP-022)

**Start when:** after T-486. T-484 already landed the input — the outcome store is now **329 rows / 307 resolved**, up from 239/224.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
SKIP Step 4 and say so — T-482 ran it 2026-08-24; read GG-203 first, it explains why no new T4 evidence
has accrued since 08-14 and why nothing in this block should be read as a live-cohort result.
scripts/new_session_worktree.sh "t487-phase2-team-totals"
scripts/claim_session.sh "T-487: EXP-022 -- Phase 2 boxes 2.2+2.3, team run-total model + gate" "T-487 / GG-207"

TIER: STANDARD. ONE deliverable: a scored gate 2.3 verdict (PASS / FALSIFIED / INCONCLUSIVE-EXTEND).
Register-and-stop on any out-of-scope defect. Hand off at ~60% context.

READ FIRST: 05_RESEARCH_EXPERIMENTS/HYP010_PHASE2_PREREGISTRATION_2026-08-15.md. Box 2.2 is UNSTARTED
and no model artifact exists anywhere in the repo — "run gate 2.3" is not a runnable instruction. This
block is 2.2 and 2.3 together.

STEP 0 — amend the pre-registration BEFORE fitting anything, in its own commit. Each is a forking path
if decided after the result is known.
  (a) BENCHMARK TIMEPOINT. Measured 2026-08-24: median lead time from the last pregame snapshot to
      first pitch is 20 minutes (p10 5 min, p90 13.5h). HYP-010 never says which pregame price the
      model competes against and the archive supports both. Closing is the sharpest price available
      and the hardest benchmark. NAME ONE and justify it in one sentence.
  (b) PREGAME FILTER, ASSERTED IN THE HARNESS. Game start = close_time - 72h (verified exact on
      5,000/5,000 rows against the ticker's own date + hhmm read as ET). 21% of archive rows belonging
      to resolved events (14,815 of 70,762) are timestamped at or after first pitch. Assert the filter
      and report the row count it drops.
  (c) INDEPENDENT UNIT IS THE GAME, not the (game, line) row. Finding 3 says this for Brier; say it
      for the EV gate too or n* is inflated ~12x.
  (d) REVISED PRIOR. Measured pregame market Brier on KXMLBTOTAL decomposes to Reliability 0.0001,
      Resolution 0.0658, Uncertainty 0.2457 — the market is calibrated to measurement precision and
      there is NO recalibration edge. Expect the bottom of the pre-registered +0.005..+0.025 band or
      below. Under Option A that is a FINDING, not a failure — but predict it before the run.
  (e) NEW, AUXILIARY — NAME THE BAND. This model is a pregame, multi-day-horizon, game-level forecast.
      That is a T1 signal, not a T4M-PROJ signal — you cannot run an in-play projection band on a
      pregame distribution fit. State in the prereg that a PASS is evidence for the cell
      (mlb_game_total, T1), which already exists in the registry at NOT_IMPLEMENTED. Do NOT activate
      it — the activation path runs through T-493's ADR. This matters because the plan has no band
      axis at all (GG-172) and has been silently assuming T4.

STEP 1 — box 2.2. Fit NB/Poisson to team runs using MLBTeamStatsStore's EXISTING get_opp_runs_scored /
get_opp_runs_allowed (LL-009: no new C2 matrix, no new ingestion). Verify those two methods actually
return usable series before building on them — the plan asserts it and nobody has run it.

STEP 2 — box 2.3. Score on the subset where |model_p - yes_mid| > 0.010. Compute n* from the
BACKTEST'S OWN mean/sd: n* = ((z_alpha + z_beta) * sigma / mu)**2, one-sided alpha=.05, power .95.
Do NOT route this through run_power_calc.py's ledger path — filter_clean() requires a logic_epoch these
synthetic bets do not have and will silently return zero.
Verdicts: PASS = P&L/bet > 0 at clean_n >= n*. FALSIFIED = P&L/bet <= 0 at clean_n >= n*.
INCONCLUSIVE-EXTEND ARCHIVE = clean_n < n*, explicitly NOT falsified.
Report paired per-game delta-Brier as a DESCRIPTIVE SECONDARY with its CI and measured power. It is not
a gate. Measured critical delta-Brier is ~0.0094 (upper bound) at n=219.

NOTE ON THE INPUT: T-484 reports the 08-18..08-22 gap was closed by an untraced external process before
its session started, and its own run produced 0 new resolutions. Spot-check a sample of the rows added
outside T-484's run against the MLB Stats API before scoring on them.

SCOPE FENCE: 05_RESEARCH_EXPERIMENTS/ and scripts/. Do NOT touch src/, any kelly_fraction, the cell
registry, or the live ledger. Do not activate a cell.
GG-207 reserved. Register nothing you did not find; return the number if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; the amended prereg commit; verdict with clean_n and n*; dropped-row
count from the pregame filter; the spot-check result on externally-added rows.
```

---

# 6.2 — T-495 · NHL skeleton spike (T-474 pattern, reduced rigor)

**Start when:** any time after T-490. Deliberately lower rigor than the NFL spike — the season is far off and this is scaffolding, not evidence.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q2, paste outputs.
scripts/new_session_worktree.sh "t495-nhl-skeleton"
scripts/claim_session.sh "T-495: NHL skeleton spike -- cells + ticker grammar, no sizing, no C3" "T-495 / EXP-024"

TIER: STANDARD. ONE deliverable: NHL registered additively, exactly as T-474 did for NFL.
kelly_fraction=0.0 throughout. ZERO cells above NOT_IMPLEMENTED. No C3. No sizing. No live path.

The registry currently carries 32 MLB cells, 20 NFL, 1 NBA, and ZERO NHL market types. Operator
doctrine 2026-08-21: MLB, NBA, NFL and NHL are all being built; which cells calibrate edge is
discovered per-cell by the engine, never decided in advance. NHL is ~1,312 games/yr — second only to
MLB in supply, and its game markets (moneyline, puck line, totals) are the same shape T1 is reopening
on, so it is worth scaffolding now even though the season is distant.

FOLLOW T-474's PATTERN EXACTLY — read 02_ARCHITECTURE_DESIGN/NFL_SKELETON_SPIKE_BREAKAGE_LIST.md and
the T-474 commits first, then mirror them:
  1. NHL MarketType cells (moneyline, puck line, game total, team total) x the bands, all
     NOT_IMPLEMENTED, honouring ADR-0056's sport attribute and T4NHL- band naming.
  2. NHL ticker grammar registered additively into T-472's per-series refusal-only registry. The NFL
     registration parsed correctly first try because the registry is refusal-only; verify NHL does the
     same and does NOT fall back to a wall-clock date on no-match.
  3. Probe the same shared surfaces T-474 probed and record PASS / STRUCTURAL GAP for each. Do NOT fix
     any gap you find — append it to the existing breakage list. Most NHL gaps will be the same gaps
     NFL found; say which are shared and which are NHL-specific, because the shared ones are already
     scoped as boxes 3.4 and 3.6.

REDUCED RIGOR IS AUTHORIZED AND BOUNDED: no C1 stub required, no cadence analysis (NFL's got GG-202;
NHL's can wait), no efficiency-gradient probe. What is NOT reduced: the refusal-only date binding, the
zero-sizing invariant, and the full test suite green at close-out.

SCOPE FENCE: src/prediction_market_bot/c5_execution/market_type_registry.py, the ticker grammar
registry, and tests/. Do NOT touch any kelly_fraction, run_t4_mlb_live.py, or the ledger.
EXP-024 reserved for the spike record. Register any NHL-specific gap under a fresh GG from the free
pool and name it in your CLOSED row.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; cell count added; shared vs NHL-specific breakage; suite result.
```

---

# 7.1 — T-488 · GG-157 · Do the paper fills survive the book?

**Start when:** ADR-0055 D1 is signed and applied, or explicitly deferred. Reads the epoch-12 cohort; re-run if the repair lands mid-flight.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
scripts/new_session_worktree.sh "t488-gg157-fill-validation"
scripts/claim_session.sh "T-488: GG-157 -- measure realized mid-vs-book fill haircut, props + game markets" "T-488 / GG-208"

TIER: STANDARD. ONE deliverable: a measured fill haircut and its effect on mean P&L/bet.
MEASUREMENT ONLY. Do NOT modify paper_trader.py. A fill-model or sizing change needs an ADR.

WHY THIS IS THE HIGHEST-VALUE MEASUREMENT ON THE BOARD: paper_trader.py has zero orderbook / depth /
available-size / liquidity references anywhere in the file. Every one of ~2,900 paper positions assumed
a fill at mid, never validated against the book. GG-157 is registered as an explicit G6 PRECONDITION:
no live-capital authorization while fill assumptions are unvalidated against production depth. ADR-0028
states the principle directly — a system EV-positive on paper fills and EV-negative after realistic
fill costs is not commercially viable.

Depth series: exp_output/PRICE_ARCHIVE/depth_*.jsonl, accumulating since 2026-08-01 via the archiver's
--depth-sample-per-family 2 flag. Verify non-empty and check coverage before building on it. If coverage
is thin, report what the sample can and cannot support rather than forcing a number.

TASK 1 — for each epoch-12 T4M-PROJ position, join its entry to the nearest depth observation and
compute the realized haircut: what it would have paid crossing the actual book at its intended size
versus the mid it was recorded at. Report the distribution, not a mean.
TASK 2 — recompute mean P&L/bet and n* for the cohort under the haircut. State before/after.
TASK 3 — state plainly whether the cohort's edge survives. If it does not, that is the finding and it
outranks every coverage item in the queue.

TASK 4 — NEW, AUXILIARY, AND IT IS NOT OPTIONAL. Repeat TASK 1's haircut measurement on GAME MARKETS —
KXMLBTOTAL, KXMLBGAME, KXMLBSPREAD — using the same depth series. T1 is reopening on exactly these
markets (T-493) and a haircut measured only on KXMLBHIT props does not transfer: props showed median
half-spread 0.0150 / mean 0.0582 / p90 0.1450, game totals 0.0050 / 0.0094 / 0.0150 — a 3x median and
6x mean difference, so the fill geometry is materially different. There are no T1 game-market positions
to join against yet, so do this SYNTHETICALLY: take the $1.00 ADR-0050 flat stake, price it against the
observed book at each depth observation, and report the implied haircut distribution per family. That
number is the input T-494 needs and the one that tells us whether a 0.0050-half-spread market survives
round-trip costs at all.

CAUTION: do not run any clean-vs-corrupted comparison without pre-registering it first — the last one
had to be withdrawn as temporally confounded and underpowered. If D1 has NOT been applied, scope your
figures to the uncorrected ledger explicitly and do not quote them as authoritative.

SCOPE FENCE: scripts/ and exp_output/. Do NOT touch src/, any kelly_fraction, or the ledger.
GG-208 reserved. Register nothing you did not find; return the number if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; haircut distribution for props AND per game-market family;
before/after mean P&L/bet and n*; whether edge survives; what the depth sample could not cover.
```

---

# 7.2 — T-490 · `--sport` axis through the power calc (breakage item 3 = box 3.4)

**Start when:** ADR-0054 (b) — per-cell epoch scoping — is signed. It is the load-bearing unblock for Phase 3 and this block builds on its shape.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
scripts/new_session_worktree.sh "t490-sport-axis-power-calc"
scripts/claim_session.sh "T-490: box 3.4 -- sport axis through run_power_calc/run_band_monitor" "T-490 / GG-210"

TIER: STANDARD. ONE deliverable: run_power_calc.py computes clean_n / n* for a non-MLB, non-T4M-PROJ
cell. Register-and-stop on out-of-scope defects.

THE BREAKAGE, verified 2026-08-24 — confirm before changing anything:
  scripts/run_power_calc.py hardcodes the literal band string "T4M-PROJ" at lines 306 and 367-372 for
  every T4 ledger record, and has no --sport argument.
  scripts/run_band_monitor.py has DEFAULT_PORTFOLIO = logs/.vps_portfolio_cache_mlb.json,
  DEFAULT_T4_LEDGER = logs/t4_mlb_resolved_ledger.jsonl, and BOOK_BANDS = ("T1","T2","T3").
  analyze_band_power(band, recs, alpha, power) is ALREADY band-agnostic — the hardcoding is in the
  drivers, not the analysis. Do not rewrite the analysis.
  This is GG-004's own sample-adequacy calculator and it cannot compute clean_n/n* for any non-MLB
  cell, which blocks promoting a second cell of any sport.

Build the SPORT axis and the FAMILY axis in one pass — breakage item 3 IS box 3.4 and item 5 IS box
3.6, rediscovered from two directions a month apart. See
02_ARCHITECTURE_DESIGN/NFL_SKELETON_SPIKE_BREAKAGE_LIST.md (T-474). Honour ADR-0056's accepted sport
attribute and band-naming decision (T4MLB-/T4NBA-/T4NFL-/T4NHL- up front, existing names
grandfathered) — ADR-0056 is ACCEPTED and zero of it is implemented.

AUXILIARY, NEW — T1 IS NOW A LIVE CONSUMER OF THIS. BOOK_BANDS already contains "T1", but it reads
from DEFAULT_PORTFOLIO, which is MLB's T1/MAIN cache and is player-prop-shaped. T1 is reopening on
game-market cells (T-493). Prove clean_n/n* computes end-to-end for a T1 GAME-MARKET cell — e.g.
(mlb_game_total, T1) or (nfl_moneyline, T1) — not only for a T4 cell. An empty-cohort
INSUFFICIENT_DATA result from the right code path is the proof; a crash, or a silent T1/MAIN
player-prop answer returned for a game-market cell, is the bug. Add a regression test for exactly that
confusion.

Also add regression tests that fail on the old hardcoded path, and prove the sport axis by computing
clean_n/n* for an NFL cell end-to-end even though the cohort is empty.

SCOPE FENCE: scripts/ and tests/. Do NOT touch the ledger, any kelly_fraction, or cell statuses.
GG-210 reserved. Register nothing you did not find; return the number if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; the NFL-cell and T1-game-market-cell end-to-end results; which
breakage-list items are now closed and which remain.
```

---

# 8.1 — T-489 · GG-038 · Kill-switch SLA against continuous evaluation

**Start when:** ADR-0055 D1 signed or deferred. Independent of T-488 otherwise — can run in parallel.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
scripts/new_session_worktree.sh "t489-gg038-killswitch-sla"
scripts/claim_session.sh "T-489: GG-038 -- measure real halt latency, band and system tier, T4 and T1" "T-489 / GG-209"

TIER: STANDARD. ONE deliverable: measured halt latency for both kill-switch tiers.
MEASUREMENT ONLY. Any SLA change is an ADR. Do not change a threshold.

WHY: NFR-03's "kill switch must halt all components within <=60 seconds" is a CLAUDE.md hard rule, and
GG-038 (OPEN, HIGH) says 60s is 12x too slow for continuous T4 evaluation. CLAUDE.md also requires two
tiers active simultaneously and WITHOUT COUPLING: a band-level switch halts only that band; the
system-level switch halts everything. Neither latency has been measured end-to-end, and this is a
live-capital precondition.

TASK 1 — measure band-level halt latency end-to-end in a test harness: trip condition to
last-evaluation-stopped, for T4M-PROJ. Report the distribution over repeated trials, not one number.
TASK 2 — measure system-level halt latency the same way.
TASK 3 — verify NON-COUPLING by construction, not inspection: trip the band-level switch and assert
another band keeps evaluating; trip the system switch and assert everything stops.
TASK 4 — at T4's ~76 bets/day and 45-90s evaluation cadence, state how many evaluations occur inside
each measured latency window. That number, not the latency, is what GG-038 is about.

TASK 5 — NEW, AUXILIARY. T1 is reopening (T-493) and its SLA question is a different question, not a
smaller one. T1 is multi-day: it evaluates on a nightly cron, holds positions across days, and cannot
exit intraday the way T4 can. A 60s halt latency is irrelevant to a band whose exposure persists for
days — the binding constraint is whether a tripped switch prevents the NEXT cron from placing, and
whether existing multi-day exposure can be closed at all. State the T1 tier's real requirement in those
terms and say whether the current implementation satisfies it. If T1's kill path is untested or absent,
REGISTER AND STOP — do not build it here.

Report each measured figure against the NFR-03 60s bar and say plainly whether it passes. If it does
not, AMEND GG-038 with the measured figures rather than opening a new entry.

SCOPE FENCE: tests/ and scripts/. Do NOT touch risk.py, execution_bands.py, any threshold, or any
kelly_fraction.
GG-209 reserved (use only for something GG-038 does not already cover; otherwise amend and return it).

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; both latency distributions; the non-coupling result;
evaluations-inside-the-window; the T1-tier assessment; pass/fail against NFR-03.
```

---

# 8.2 — T-491 · GG-172 · The band axis, with T1 as the live case

**Start when:** after T-493. ADR-0058 changes what reopening a band means, and this proposal has to match it.

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
scripts/new_session_worktree.sh "t491-gg172-band-axis"
scripts/claim_session.sh "T-491: GG-172 -- band-axis boxes for the expansion plan, T1 as live case" "T-491 / GG-212"

TIER: STANDARD. ONE deliverable: a PROPOSAL for band-axis boxes. Do NOT amend the plan unilaterally —
this changes the shape of the coverage target and is an operator decision.

GG-172 (OPEN, HIGH): MARKET_EXPANSION_ACTION_PLAN.md Phases 1-4 are written entirely in market-type
terms and contain ZERO boxes addressing band activation, though the operator's coverage directive is
"all five bands" and three of five have essentially no trading history — T2 raw_n=2, T3 raw_n=0, T5
never traded, T1 zeroed and frozen (GG-153). COVERAGE_TARGET_MATRIX.md already records the band
dimension as unowned. The plan burns down one axis of a two-axis target.

THIS IS NO LONGER HYPOTHETICAL. The operator reopened T1 on 2026-08-25 (T-493 / ADR-0058) and the plan
has no box anywhere that describes reopening a band. Write the band axis with T1 as the worked example,
not as an abstraction:
  - The missing boxes, per band, each with an explicit entry criterion.
  - What "activate a band" means operationally now that every live band is kelly_fraction=0.0 under
    ADR-0048 — distinguish MEASUREMENT activation (ADR-0050 flat stake, zero ruin exposure, what T1 is
    getting) from SIZING activation (nonzero Kelly, gated on ADR-0048's edge-conditional lookup table
    and on T-494's variance re-derivation). Those are two different gates and the plan conflates them.
  - The band x market-type interaction, which is the actual finding: T1 was measured only on player
    props and killed on prop variance; T4M-PROJ is an in-play band that cannot consume a pregame
    distribution fit. A cell is a (market_type, band) pair for a reason, and the plan's market-type-only
    phases cannot express "this model belongs to that band."

Also surface, do not resolve: COVERAGE_TARGET_MATRIX.md § "The strategic tension nobody has
adjudicated" — the coverage target expands toward moneyline / run line / totals, the most efficiently
priced markets on the board, the opposite end of the efficiency gradient the strategy targets. Measured
2026-08-24: game totals are 3x tighter on median half-spread and 6x on mean than the props the bot
trades, and pregame market reliability on KXMLBTOTAL is 0.0001 — no recalibration edge exists there.
That is an OPEN OPERATOR DECISION. Do not resolve it and do not soften it into a monitoring note.

SCOPE FENCE: 02_ARCHITECTURE_DESIGN/ and 04_EXECUTION/ docs only. Do NOT touch src/, the plan's
existing boxes, or any kelly_fraction.
GG-212 reserved. Register nothing you did not find; return the number if unused.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; the proposed boxes; the measurement-vs-sizing activation split;
what you deliberately left undecided.
```

---

# 9.1 — T-494 · GG-135 re-derivation on game-market variance

**Start when:** after T-493 (ADR-0058 must exist so this has a scope to answer into) and after T-488 (its game-market haircut is an input). **This gates any future nonzero T1 Kelly — nothing else does.**

```
Run the CLAUDE.md session-start protocol in full. Steps 0-3 and Q1/Q2/Q4/Q5/Q7, paste outputs.
scripts/new_session_worktree.sh "t494-gg135-game-market-variance"
scripts/claim_session.sh "T-494: re-derive GG-135 ruin geometry on game-market variance" "T-494 / GG-214"

TIER: STANDARD. ONE deliverable: a ruin-probability estimate for T1 on game markets, with its method
and its uncertainty. MEASUREMENT AND ANALYSIS ONLY. Do NOT change any kelly_fraction — a nonzero T1
Kelly needs ADR-0048's lookup table and a fresh operator signature, neither of which this block touches.

THE QUESTION: GG-135 found that MAIN's real variance alone — independent of edge sign — produces
~100%/yr kill-switch trip probability at any positive Kelly, and ADR-0048 zeroed T1 on that basis.
That computation was done on PLAYER-PROP variance. T1 is reopening on game markets (ADR-0058), which
have materially different per-bet variance, no lineup or scratch risk, and much greater supply.
Whether GG-135's conclusion transfers is the single empirical question standing between T1 and a
nonzero Kelly. Answer it. Do not assume either direction — the prior should be that a lower-variance,
lower-edge market can produce the SAME ruin probability at a proportionally higher Kelly, so a
favourable variance number is not automatically a favourable ruin number.

READ FIRST: GG-135's full record, ADR-0040, ADR-0048, and the Monte Carlo harness GG-135 used
(logs/mc_*.json and whatever script produced them — find it, do not re-implement blind). Reuse that
harness so the two figures are comparable by construction. If it cannot be reused, say why and state
what changed.

TASK 1 — establish game-market per-bet variance empirically, not by assumption. There are no T1
game-market positions, so derive it from the archived price series plus resolved outcomes:
exp_output/PRICE_ARCHIVE/ and logs/t4_mlb_totals_outcome_store.jsonl (329 rows, 307 resolved as of
T-484). Report variance per family — moneyline, spread, run line, totals — separately. They are not
one number.
TASK 2 — feed T-488's measured game-market fill haircut in. A variance estimate that ignores the
round-trip cost on a 0.0050-half-spread market is not a tradeable number.
TASK 3 — re-run the ruin geometry per family across a Kelly grid. Report the Kelly at which annual
kill-switch trip probability crosses the same threshold GG-135 used, per family. If no positive Kelly
clears it, that is the finding and it is as valuable as the opposite.
TASK 4 — state explicitly how much of the answer is driven by the assumed edge. GG-135's result was
notable precisely because it held INDEPENDENT of edge sign. Check whether that independence still holds
on game markets; if it does not, the whole shape of the argument changes and that must be said.

Amend GG-135 with the result rather than opening a new entry, unless you find something genuinely
distinct. GG-214 reserved for that case; return it if unused.

SCOPE FENCE: scripts/ and exp_output/. Do NOT touch execution_bands.py, risk.py, ADR-0048, or any
kelly_fraction.

Before writing any shared nav file at close-out, re-read SESSION_CLAIMS.md fresh; if an older claim has
no CLOSED row, wait. <=10% context, <=10 min, DECISION_LOG append-only. GG-186 before CLOSED.

REPORT BACK: branch + commit range; per-family variance; per-family Kelly-vs-ruin curve; whether
edge-independence holds; what you could not measure and why.
```

---

## Needs your decision, not a window

**ADR-0055 D1 — apply the epoch-12 repair.** Decides whether the reset repairs (n=719) or discards (n=187). Closes GG-166 and GG-170, the only two OPEN CRITICAL gaps. Dry-run simulated, all five pre-registered assertions passed. **Read box S.1 first.**

**ADR-0055 D2 — the 46 stuck-open epoch-12 positions.** Independently safe from D1; can be signed alone.

**ADR-0054 (a)/(b)/(d)** — unsigned since 2026-08-17. **(b), per-cell epoch scoping, is the load-bearing unblock for all of Phase 3**, gates T-490, and is what makes GG-153 closable under the T1 reopen.

**ADR-0057 (PROPOSED, T-485)** — G6 re-scoped off T1 onto the cell registry. Its premise needs T-486's amendment note before it is signed: it argues partly from "T1 is permanently dead," which the 2026-08-25 directive supersedes. The recommendation still stands.

**ADR-0058 (arriving via T-493)** — reopening T1 at measurement stake. The T1 question in previous queues is now answered by directive; this is the record of it.

---

## Standing findings — verify, do not re-derive

- **GG-203 (OPEN, HIGH).** ~5,200 approved bets, zero submitted, 100% order-submission failure since 2026-08-15T00:06:20Z. Engine alive and evaluating throughout. Detail in § "Where the build actually is". **This invalidates the previous queue's hypothesis that GG-143's cold-start blindness was the mechanism** — it is not a silent death, it is an execution-layer failure downstream of a healthy evaluator. Every existing liveness probe reported healthy for ten days.
- **T1's kill was market-specific, not band-specific.** ADR-0048 zeroed T1 on GG-135's prop-variance ruin geometry; T1 has never been measured on game markets. The T1 cells for all nine MLB/NFL game-market types already exist at NOT_IMPLEMENTED. Reopening at ADR-0050 flat stake takes zero ruin exposure. **This supersedes the "do not reopen T1" instruction carried in every handoff through 2026-08-24.**
- **Phase 2's model is a T1 signal, not a T4 signal.** A pregame NB/Poisson distribution fit cannot run in an in-play projection band. A passing gate 2.3 is evidence for `(mlb_game_total, T1)`.
- **Realized pregame market Brier on `KXMLBTOTAL`, measured 2026-08-24** (219 of 224 resolved games with ≥1 pregame quote; 2,408 quotes): `0.1787 = Reliability 0.0001 − Resolution 0.0658 + Uncertainty 0.2457`; skill vs climatology **0.273**; ten calibration bins each within ~2pp of observed. **No recalibration edge exists on this market.** Precision caveat: 12 lines per game share one realized total, so effective independent n is ~219 not 2,408 — the point estimate is unbiased, "0.0001" overstates precision.
- **Half-spreads, re-derived on 40 dates:** `KXMLBTOTAL` n=77,376 median **0.0050** mean 0.0094 p90 0.0150; `KXMLBHIT` n=100,615 median **0.0150** mean 0.0582 p90 0.1450. Previously flagged unverified. **They hold. Citable.**
- **Measured replacement for one column of HYP-010 Finding 3.** Per-game Brier sd 0.0844 at n=219 ⇒ SE 0.0057 ⇒ one-sided α=.05 critical ΔBrier **0.0094**, an upper bound. Finding 3's crit column reads 0.0047 at assumed noise 0.03, 0.0079 at 0.05, 0.0127 at 0.08 — the measured value lands **between the 0.05 and 0.08 rows, not the 0.03 row the prereg anchored to.** A bound, not an identification.
- **Phase 2 input, post-T-484:** `logs/t4_mlb_totals_outcome_store.jsonl` is **329 rows / 307 resolved**, on the VPS and force-added to git (dual path, sha256-identical, reconciled in GG-206). **Caveat T-484 raised: the 08-18..08-22 gap was closed by an untraced external process before its session began, and its own run produced 0 new resolutions.** Spot-check externally-added rows before scoring on them.
- **Archiver sampling bias.** `*/20 22-23,0-5` UTC captures ~12.5 `KXMLBTOTAL` events/day against ~15 MLB games/day; the missing third is systematically the afternoon slate. Not fixable retroactively.
- **GG-185's root cause is still incomplete; T-471 did NOT resolve it.** 0/77 correct under `cbd09ae` vs 0/532 under `687bf9e`, deploy-timestamp-boxed not calendar-boxed, byte-identical write-path code in both. Ruled out: VPS timezone, systemd restart at onset, source diffs. Untested: diff `paper_portfolio_mlb_t4.pre_gg166_correction_20260807T052850Z.json` against live state at that timestamp; live-instrument `game_date` at the `open_position()` call site. GG-190 holds the record.
- **Epoch-12 repair pre-registered and simulated, NOT applied.** Repaired pooled: n=719, mean **+0.0652**/bet (SE 0.0552), `n*` **5,580** — `clean_n` does **not** clear `n*` post-repair. GG-196 (OPEN): the 08-04..08-07 outage-window sub-bucket (n=144) shows mean **+0.3037**, crossing ADR-0055's own suspicion threshold — flagged, not chased.
- **Q7 cross-path disagreement, 2026-08-24:** `T4M-PROJ epoch=12: matched=719/719 hits_agree=49.0% outcome_agree=66.3%` against epoch 8's `99.9%/99.9%`. The `[GG-170 RECURRENCE]` alarm on `UNTAGGED epoch=3` is **1 violation and is the same pre-existing one recorded at T-443** — ruled out, not new.
- **CLAUDE.md's Q1 ruin-risk paragraph ends at ADR-0040's `kelly_fraction=0.061` and never mentions ADR-0048 zeroing it** (T-483 may have fixed this — verify). Consequence: any framing of a data-integrity item as "live capital at risk" is wrong today. The mechanism is **measurement corruption**, which for a calibration engine is the more expensive failure.
- **`GOVERNANCE_GAP_LOG.md` has ~13 RESOLVED entries re-accumulated** since T-420's 2026-08-05 split. Harmless to the anchored OPEN scan. Deliberately unassigned — it edits a non-`merge=union` file that concurrent blocks register into. Pick it up in a quiet window.
- **42% of OPEN gaps carry `Severity: UNSPECIFIED`.** Severity-based triage runs on 58% of the log.

---

## Do not

Don't unpark `SCALING_MANDATE_PARKED.md`. Don't promote `assert_ledger_invariants.py` to `--strict` (alarm-only, operator decision). **Don't touch sizing or any `kelly_fraction` without an ADR — this includes T1: the 2026-08-25 directive reopens T1 at MEASUREMENT stake, `kelly_fraction=0.0`, and authorizes no sizing change.** A nonzero T1 Kelly needs T-494's variance re-derivation, ADR-0048's edge-conditional lookup table, and a fresh signature. Don't mark **ADR-0054**, **ADR-0055**, **ADR-0057** or **ADR-0058** ACCEPTED. Don't apply the epoch-12 repair without D1. Don't quote any epoch-12 P&L or edge figure as production-authoritative until D1 is signed and executed. Don't run any clean-vs-corrupted comparison without pre-registering it first. Don't build the periodic intent-vs-implementation reconciliation unasked. Don't "fix" the GG-203 execution path on a guess — a wrong fix that silences a loud, contained failure is worse than the failure. Don't recommend against a sport on the strength of a finding — **operator doctrine 2026-08-21: MLB, NBA, NFL and NHL are all being built.**

**Retired instruction:** "Don't reopen T1." Superseded by operator directive 2026-08-25. Kept here so a future window does not re-kill it from an old handoff — T1's zeroing was correct for player props and does not generalise to game markets.

---

## Strategic-window log — not blocks, no action

- **2026-08-24/25** (Cowork, PDTP, no git writes): full state re-derivation against `8f5801c`; corrected "zero OPEN CRITICAL gaps" to two (GG-166, GG-170); promoted the half-spread figures from unverified to citable; measured the pregame market Brier decomposition; found the accrual stall — **mechanism subsequently identified correctly by T-482 as GG-203, not the GG-143 cold-start hypothesis this window proposed**; found the ADR-0028 G6/T1 unsatisfiability; rebuilt this file on the T-431-era prompts-in-file structure with a wave-based sequencing track.

*Per-block outcomes live in the closed-wave tables above, not here.*

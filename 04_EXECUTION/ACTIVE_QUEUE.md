# Active queue — the only prompt file to read

**Verified against `origin/main` = `1ecc13a`, 2026-08-11.** Gap log: **52 entries / 42 OPEN** (re-derive before citing — it moved 46→49→51→52 in four days).
**Free IDs: T-436, T-437, … and GG-169+.**
**Taken:** T-431 (B5 disagreement, registered by T-429) · T-434 (**DONE**, merged `40f6385`) · **T-435 (taken — T-434 registered GG-168 against it)**.

> **T-435 collision — sixth of the run.** T-434's close-out registered GG-168 and tracked it as T-435 while this file already assigned T-435 to the depth re-check. **The depth window now claims T-436.** GG-162 (no atomic reservation for mid-session IDs) remains unstaffed and is now demonstrated six times.

> **GG-168, new and relevant while you run:** Step 4's T4 cycle-log write-recency probe — the detector T-429 just shipped — has no exemption for "daily T4 budget exhausted," so a legitimate zero-new-row day will alarm. Same false-positive shape as the two bad assertions I caught in T-432's baseline. If that probe fires mid-run, check it against budget exhaustion before treating it as an outage.

## Read this first — file cleanup

I created ten prompt files across this week and four of them describe the same unexecuted batch. That is sprawl, and it is the pattern GG-132/GG-133 are registered about. **This file replaces all of them.** Every prompt below is complete and inline — no cross-references, nothing to assemble.

**Executed (Waves 1–6, T-413 → T-430) — archive or delete, they are history:**
`TERMINAL_PROMPTS_2026-08-03.md` · `TERMINAL_PROMPTS_WAVE2_REVISED.md` · `TERMINAL_PROMPTS_GG163_HOTFIX.md` · `TERMINAL_PROMPTS_WAVE4.md` · `TERMINAL_PROMPTS_WAVE5.md` · `TERMINAL_PROMPTS_WAVE6.md`

**Never executed — DELETE, their T-numbers collide with live claims:**
`TERMINAL_PROMPTS_WAVE7.md` · `TERMINAL_PROMPTS_WAVE8.md` · `TERMINAL_PROMPTS_WAVE9.md`

**Also delete — superseded now that T-434 has landed:** `PROTOCOL_PATCH_SESSION_SIZING.md`.
**Keep:** `05_RESEARCH_EXPERIMENTS/STRATEGIC_REVIEW_2026-08-03_HANDOFF.md` (reference only).

```bash
mkdir -p 04_EXECUTION/ARCHIVE_PROMPTS && \
mv 04_EXECUTION/TERMINAL_PROMPTS_{2026-08-03,WAVE2_REVISED,GG163_HOTFIX,WAVE4,WAVE5,WAVE6}.md 04_EXECUTION/ARCHIVE_PROMPTS/ && \
rm 04_EXECUTION/TERMINAL_PROMPTS_WAVE{7,8,9}.md 04_EXECUTION/PROTOCOL_PATCH_SESSION_SIZING.md
```

**Rule going forward: when a window closes, delete its prompt block from this file.** A completed prompt sitting in an active queue is the confusion this file exists to prevent. The record lives in `SESSION_CLAIMS.md`, `DECISION_LOG.md` and git — not here. One line in "Done this run" at the bottom is all that stays.

**Housekeeping, first action in the shared `main` tree:** `rm -f .git/index.lock` then `git pull`. I left a stuck zero-byte lock from a failed `merge --ff-only`. HEAD intact at `687bf9e`, no `MERGE_HEAD`, no tracked-file damage — but git writes are blocked until it clears.

---

## Why this week was all fixes, and what ends it

Eleven gaps registered in seven days (GG-158→GG-167), zero forward capability. That is not a work-ethic problem and it is not going to repeat indefinitely — it has a specific cause and a specific terminator.

**Cause:** the measurement layer was never trustworthy, so every analysis built on it was provisional, and each fix exposed the next defect. GG-164 → GG-166 → the B5 residual is one causal chain, not three unrelated bugs. A cascade like that runs until something can tell you the data is right.

**Terminator:** T-432 and T-433. The invariant suite plus cross-path agreement are what convert "we think the ledger is right" into "the ledger asserts itself every run." **Those are not more fixes — they are the exit from the fix loop.** After them, a defect of GG-166's class surfaces in one run instead of four analysis sessions.

**What actually moves the bot forward** is Phase 1 (abstraction repair) → Phase 2 (team model gate) → new market families. Phase 1 has two blockers, both in this queue: **T-431** (~1,220 positions carry stale outcomes, so bit-identical replay would only prove the wrongness reproduces) and **T-436** (the depth verdicts). Nothing else blocks it.

**Shortest path to Phase 1: T-431 → T-436.** T-432/T-433 run in parallel and do not gate it. **T-436's count threshold is already met** (332 obs/family, all six, verified 2026-08-11), so its remaining work is the median-depth verdicts — meaning **Phase 1's real remaining blocker is essentially T-431 alone.**

---

## Run order

| # | ID | Task | Mode | Gates Phase 1? |
|---|---|---|---|---|
| **1** | **T-431** | B5 disagreement root-cause + outcome re-derivation | Critical path | **Yes** |
| 2 | T-432 | Invariant suite, alarm-only | Parallel with T-431 | No |
| 3 | T-433 | ADR-0007 amendment + G6 precondition | ✅ COMPLETE 2026-08-11 (`c64008e`) | No |
| **4** | **T-436** | Depth re-check — count gate already met, verdicts remain | Any time | **Yes** |

T-434's rules are live as of this queue: Hard Rule 8 is 60%, Hard Rule 11 is one-deliverable/register-and-stop, tier is declared in the `claim_session.sh` string. **The size cap is protocol now** — the `TIER:` lines in the prompts below are just the claim-string format, not something to paste.

---


# 1 — T-431 · Root-cause the second disagreement source

```
Run the CLAUDE.md session-start protocol in full. rm -f .git/index.lock if present, then
git pull. Launch an isolated worktree via
scripts/new_session_worktree.sh "t431-b5-disagreement". Claim T-431.

TIER: STANDARD. ONE deliverable: a root cause for the B5 disagreement, or a documented set of
ruled-out hypotheses. Register-and-stop on any out-of-scope defect — write the GG/T-NNN and do
not fix it. Hand off at ~60% context. If this reads as more than one session, say so before
starting and propose the split.

ESTABLISHED by T-429 — verify, do not re-derive:
  GG-166's original mechanism is FIXED and confirmed dead: 0/187 date mismatches, down from
  68.2%. scripts/correct_t4_game_dates.py corrected 1,443 positions in place (backed up first).
  BUT ledger-vs-store still disagrees: hits 36.9%, outcome 25.1% on the current clean cohort.
  ALREADY RULED OUT — do not re-test: single-bad-date concentration; doubleheader / game-number
  ticker collisions.
  UNTESTED LEAD, unconfirmed: source-drift / backfill timing — a multi-day gap between the
  ledger's ORIGINAL resolution timestamp and the outcome store's LATER re-fetch. If the MLB
  Stats API's gameLog changed between those two reads, both sources could be internally
  consistent and still disagree. Hypothesis, not cause.

TASK 1 — root-cause it. Test the timing hypothesis first, it is cheapest: correlate each
disagreeing position's resolved_at against the store's fetch timestamp and check whether the
disagreement rate tracks the gap. If it does not, that hypothesis dies and you report that —
three are already ruled out and a fourth is a real result. State the mechanism in one sentence
with evidence, or state plainly that you could not find one.

TASK 2 — ONLY if Task 1 identifies the cause: re-derive outcome/pnl for the ~1,220 positions
flagged game_date_corrected_but_outcome_stale.
  MANDATORY MECHANISM: GG-084's two-phase off-VPS-fetch / on-VPS-apply pattern. Direct
  sequential VPS fetches trigger a Fastly-CDN block. Read GG-084 before writing any fetch loop.
  Back up the ledger before writing, same as correct_t4_game_dates.py did.

TASK 3 — recompute clean_n / mean / stdev / n* from the re-derived ledger; report before/after.
The current baseline (clean_n=157, mean +$0.3793, stdev $1.8821, n*=267) is the thing under
test. Carry it forward as an assumption and you have learned nothing.

HARD STOP: if Task 1 yields no cause, STOP. Write up what you ruled out and how, and hand off.
Do NOT re-derive 1,220 outcomes on an unexplained mechanism — you would be overwriting a ledger
without knowing which of the two sources is right, which is worse than the current state.

ALSO, cheap and in scope: GG-164's write-site was fixed by T-429. Check whether GG-164 is now
closable, and whether closing it should wait on T-433's assertion requirement.

SCOPE FENCE: scripts/ and the ledger (with backup). Do NOT touch run_t4_mlb_live.py,
run_resolve_mlb.py, execution_bands.py, risk.py, paper_trader.py, or any sizing. Do not build
the invariant suite (T-432).

REPORT BACK: branch + commit range; the mechanism in one sentence with evidence, or the
ruled-out list; before/after clean_n if you re-derived.
```

---

# 2 — T-432 · Invariant suite, alarm-only

**Measured baseline — I ran all nine assertions against the live ledgers before writing this. Two of mine were wrong. Verify every number; if yours differs, mine is wrong and yours is the finding.**

Corrected ticker regex — **100% parse on 2,416 T4 + 485 T1 rows.** My first draft hardcoded `[A-Z]{6}` for the team block and parsed only 65%; two-letter team codes (AZ, SF, SD, TB, KC) and doubleheader `G1`/`G2` suffixes break it:

```
^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})([A-Z]{4,6})(G[12])?-([A-Z]+?)(\d+)-(\d+)$
   groups: YY, MON, DD, HHMM, TEAMS, doubleheader?, PLAYER, jersey, threshold
```

| # | Assertion | T4 (n=2,416) | T1 (n=485) | Read |
|---|---|---|---|---|
| A | ticker date == `game_date` | 1,443 (59.7%) | **0 (0.0%)** | GG-166 confirmed **and scoped — T4 only**. T1 clean, because it is a pregame band on a daily cron before first pitch. |
| B | ticker threshold == `kalshi_threshold` | 0 | 0 | Clean. Good invariant. |
| C | `0 < entry_price_paid <= 1` | 2,229 (92.3%) | 485 (100%) | **MY SPEC ERROR** — needs a presence guard. |
| C2 | `0 <= mid_price_at_entry <= 1` | 0 | 0 | Clean. Good invariant. |
| D | `contracts == size_usd / entry_price` | 0 / 187 | 0 / 0 | Clean where fields exist. |
| E | `pnl` sign matches `outcome` | 0 / 2,193 | 0 / 468 | Clean. Good invariant. |
| F | `resolved_at > entered_at` | 0 | 0 | Clean. Good invariant. |
| G | `gross_edge == (model_p − mid) − vig` | 0 | 483 (99.6%) | **MY SPEC ERROR** — must be band-scoped to T4. |
| H | no both-direction OPEN on same ticker | 17 / 151 | 0 / 17 | Legacy residue, pre-epoch-12. Not a live regression. |

```
Run the CLAUDE.md session-start protocol in full. rm -f .git/index.lock if present, then
git pull. Launch an isolated worktree via scripts/new_session_worktree.sh "invariant-suite".
Claim T-432.

TIER: STANDARD. ONE deliverable: scripts/assert_ledger_invariants.py + tests + wiring.
Register-and-stop on any out-of-scope defect. Hand off at ~60% context.
Window T-431 may run concurrently and touches the ledger. You do not — read-only.

WHY THIS EXISTS. GG-166 corrupted ~44% of the epoch-12 clean cohort's outcomes and P&L, was
computed into four separate analysis sessions' headline figures, and was caught only when an
independent data path (T-421's decoupled store) disagreed with the ledger. Nothing in the
session-start protocol, the gap log, or the 11-step session-end had the shape to catch it:
every one of those verifies PROCESS (was the step run, the decision logged, the gap
registered). None asserts that a VALUE is correct.
Note what actually found things this month — GG-163 (write recency vs wall clock), GG-164
(join-key uniqueness), GG-166 (cross-path agreement), GG-157's zero overlap (row counting).
All four were executable code run against data. Zero came from reading documents.

MODE: ALARM-ONLY, by explicit operator decision. Non-negotiable this wave:
  - MUST exit 0 even when invariants are violated. Violations go to a report and stderr,
    never to an exit code.
  - MUST NOT halt, gate, or block the resolution cron, CI, or any pipeline.
  - MUST NOT modify any ledger, portfolio file, or store. Read-only, full stop.
Build the exit-code path behind an explicit --strict flag, OFF by default and wired to nothing,
so promoting it later is a one-line change rather than a rewrite.

=== TASK 1 — build the suite ===
One script + tests. Every assertion declares:
  id | band scope | fields required | what it asserts | current baseline violation count
Machine-readable report (JSONL) out, human summary to stderr.

THREE DESIGN RULES, each learned from a specific failure — do not relax them:
 1. PRESENCE GUARD. "field absent" is a distinct outcome from "field violates." Never coerce a
    missing field into a value that fails a bound. My assertion C did exactly that and produced
    2,714 false violations across the two ledgers.
 2. BAND SCOPE. Assertions are per-band unless proven global. My assertion G (ADR-0016's
    gross_edge formula) holds 2,416/2,416 on T4 and fails 483/485 on T1 — T1 computes edge
    differently. A band-naive suite emits hundreds of false alarms and gets muted in a week.
 3. VIOLATION PROVENANCE. Every violation reports first-seen epoch and entry timestamp, so
    legacy residue (assertion H's 17 pre-epoch-12 open positions) is distinguishable from a
    live regression. A monitor that cannot tell "old known state" from "new breakage" is noise.

START FROM THE TABLE ABOVE. A, B, C2, D, E, F, H are specified with known baselines. VERIFY
each count yourself before encoding it. Do NOT encode C or G as written — re-derive correct
forms (C with a presence guard, G band-scoped to T4) or drop them.

EXTEND, each measured before inclusion — do not pad the count:
  - size_usd == round(min(1.00, 10 * entry_price_paid), 4) for T4M-PROJ epoch>=12 (ADR-0050);
    contracts <= 10.0 (the cap). VC6 reported 141/141 on the epoch-12 cohort — confirm at
    current n.
  - fee_net_edge == the paper_trader.py:460-466 vig cascade, recomputed direction-conditionally.
    VC6 verified 799/799 exact, max abs diff 0.000000 — strong invariant, proven-clean baseline.
  - actual_hits is a non-negative integer; outcome ∈ {WIN, LOSS}; status ∈ known set.
  - logic_epoch never null on a position written after epoch 1.
  - ticker-derived player token consistent with player_name / player_id mapping.

=== TASK 2 — cross-path agreement as a STANDING check ===
Invariants catch classes someone already thought of. GG-166 was an unknown-unknown, and what
caught it was two independent measurement paths disagreeing. Generalize T-426's one-off check
into a repeatable one: ledger actual_hits/outcome vs T-421's decoupled store's ticker-derived
resolution, reported as an agreement rate per band per epoch.
This is the only mechanism in the project with any chance against a defect nobody anticipated.
Treat it as the most important thing in this task, not an addendum.
Baselines: pre-fix 69/156 (44.2%) hits, 47/156 (30.1%) outcome. Post-T-429 the date mechanism
is dead (0/187) but a second source remains at 36.9%/25.1% — T-431 is root-causing it. Report
what you measure; do not assume it should be zero.

=== TASK 3 — wiring, alarm-only ===
  - .claude/hooks/governance_scan.sh: run the suite, print the summary. NEVER change the
    hook's exit code.
  - CLAUDE.md: add Q7 to the ARE WE COMPROMISED section — "Field integrity: does the data mean
    what the label says?" State the rule: for every field used as a JOIN KEY or a BUCKETING
    DIMENSION in any analysis this session, cross-validate it against an independent encoding
    of the same fact in the same row BEFORE using it. This repo has carried that redundancy on
    every ledger row for months (kalshi_ticker encodes date, teams, player, threshold) and
    nobody used it. Include: reproducing a number from the same source is not verification, it
    is reproducibility; a check that cannot detect a bad input has not verified anything.
  - Update CLAUDE.md and governance_scan.sh in the SAME commit. They have drifted apart before
    (GG-122/GG-144) and that drift is why Step 3 was blind for weeks.

=== TASK 4 — the observation-period exit criterion ===
State in the deliverable what must be true before --strict is turned on: how many consecutive
clean runs, at what cadence, with what false-positive rate. Without a written criterion this
stays alarm-only by default forever, which wastes the build.

SCOPE FENCE: no src/ change. scripts/, tests/, .claude/, one deliverable doc. Do not touch
run_t4_mlb_live.py or run_resolve_mlb.py. Do not fix any data — this suite observes, it does
not repair. Do not add a blocking gate anywhere.

REPORT BACK: branch + commit range; the full assertion table with YOUR measured baselines next
to mine; which of my seven you kept, corrected, or dropped and why; the cross-path agreement
rate; and the written --strict promotion criterion.
```

---

# 3 — T-433 · ADR-0007 amendment, retrofit, G6 precondition — ✅ COMPLETE 2026-08-11 (ADR-0052, commit `c64008e`, merged to `main`)

```
Run the CLAUDE.md session-start protocol in full. rm -f .git/index.lock if present, then
git pull. Launch an isolated worktree via scripts/new_session_worktree.sh "invariant-policy".
Claim T-433.

TIER: STANDARD. ONE deliverable: the superseding ADR + targeted retrofit + the G6 criterion.
Register-and-stop on any out-of-scope defect. Hand off at ~60% context.
T-432 is building scripts/assert_ledger_invariants.py in parallel — reference that path, do
not build the suite yourself.

THE PROBLEM. Re-derive the counts before citing them — they moved 46→49→51 in 48 hours, which
is the same defect ADR-0050 §10 exists to prevent, and GG-165's own text ("38/46 live gap
entries") is already stale for it:
  grep -cE "^### GG-[0-9]" 03_DECISIONS/GOVERNANCE_GAP_LOG.md
  grep -cE "^\*\*Status:\*\* OPEN\b" 03_DECISIONS/GOVERNANCE_GAP_LOG.md
Look at which controls in this project actually held:
  GG-149 (offsetting-position suppression) HELD — it is code, and the epoch-12 cohort shows
    0 of 83 tickers held in both directions.
  GG-164 DID NOT HOLD — it was a paragraph, and its own "Why it survived" field asserted an
    UNVERIFIED NEGATIVE ("game_date isn't used as a resolution join key anywhere in the
    existing pipeline") that a one-file grep would have falsified. It survived 24 hours before
    GG-166 escalated it into a CRITICAL data-integrity defect with direct P&L impact.
The difference is not diligence. One was executable and the other was prose.

=== TASK 1 — amend ADR-0007 ===
State as a SUPERSEDING ADR (ADR-0007 is immutable per Hard Rule 3 — do not edit in place):
  A governance gap may not be marked RESOLVED until an executable assertion exists that would
  have caught it, OR the entry explicitly records why no such assertion is possible.
The escape hatch is deliberate and must be narrow — some gaps are genuinely about process or
judgment and have no data signature. Require the exemption to be stated in a NAMED FIELD, not
implied by absence, so exemptions are countable and reviewable.
Rationale for the ADR: this converts the gap log from an append-only prose archive into a
growing regression suite. Same move Window F (T-420) made for OPERATOR_CONSOLE.md — the signal
that routes attention belongs in a structured field a machine can read, not in how emphatically
a paragraph is written.

=== TASK 2 — retrofit only what matters, and say so ===
Do NOT retrofit all 114 archived RESOLVED entries. That is busywork and this project is already
over-invested in governance relative to engineering. Retrofit exactly the gaps whose recurrence
would corrupt measurement or capital:
  GG-166 (wrong-day resolution) — assertion A
  GG-164 (game_date field) — same assertion
  GG-149 (offsetting positions) — assertion H
  GG-142 (abs() gate) — the fee_net_edge cascade assertion
  GG-141 / GG-145 (dead + hardcoded feature columns) — check_feature_column_health.py already
    exists; wire it in rather than rebuilding it
For each: name the assertion, or state plainly that none is possible and why. If T-432 has not
landed the assertion yet, reference it by ID and mark the gap pending-assertion, not RESOLVED.

=== TASK 3 — G6 gate precondition ===
Add to the G6 criteria, alongside GG-004 (commercial validation) and GG-157 (fill validation):
  G6 does not clear until (a) the invariant suite runs clean at --strict for a stated
  observation period, and (b) cross-path outcome agreement is a standing check, not a one-off.
Justify it concretely IN THE GATE DOC, because the mechanism is the argument: at live capital
GG-166 is not a reporting error. Kelly sizes off the win rate. The permanent drawdown kill
switch computes realized_loss / initial_bankroll FROM THE SAME LEDGER that resolved against the
wrong games. The safety mechanism sits downstream of the corruption — the bot would size up on
a fictional edge while its kill switch measured fiction too. Write that reasoning in, not just
the requirement.

SCOPE FENCE: no src/ change, no code. Governance documents only. Do NOT re-severity or re-scope
gaps beyond adding the assertion field. Do NOT build the suite — that is T-432.

REPORT BACK: branch + commit range; the superseding ADR number; which gaps got an assertion vs
an explicit exemption; and the exact G6 criterion text as landed.
```

---

# 4 — T-436 · Depth re-check · **no longer date-held — run it**

The 2026-08-09 gate date has passed (today is 2026-08-11) and **I measured the archive directly: the observation-count threshold is already satisfied.** This window's job is now the depth *verdicts*, not the wait.

| Family | Total obs | Usable | ≥200? |
|---|---|---|---|
| GAME_TOTAL | 332 | 321 | ✅ |
| GAME_WINNER | 332 | 332 | ✅ |
| PARTIAL_GAME_WINNER | 332 | 330 | ✅ |
| PLAYER_PROP | 332 | 306 | ✅ |
| RUN_LINE | 332 | 320 | ✅ |
| TEAM_TOTAL | 332 | 332 | ✅ |

All six at exactly 332 — the round-robin sampler has **not** regressed. Verify these yourself; if your numbers differ from mine, mine are wrong and yours are the finding.

```
Run the CLAUDE.md session-start protocol in full. git pull. Isolated worktree.
Claim T-436 — NOT T-435, which T-434 took for GG-168.
TIER: MICRO. ONE deliverable: the per-family depth verdict table + a Phase 1 go/no-go.

T-414 set 2026-08-09 as the re-check date for the Phase 1 depth hold, with its own explicit
instruction: THE PROJECTION IS NOT THE CLEARANCE — re-run the table. The date has passed and
the count threshold is met (332/family, all six, verified 2026-08-11). What remains is the
median-depth verdict per family, which no one has computed on the accumulated series.

Threshold: >=200 POST-FIX observations per family — MET. All observations are post-fix by
construction (--depth-sample-per-family and _balanced_sample() shipped in the same commit,
T-412), so there is no pre/post split to reconcile; T-414 already corrected that premise.
Confirm the 332/family balance still holds at your run time — a family drifting off-parity
means the round-robin sampler regressed since 2026-08-11.

Report per family: total observations, usable count, median depth, PASS/FAIL against the $10.00
gate floor (10 × the $1.00 ADR-0050 measurement stake — NOT the live-capital floor; every
verdict recomputes when sizing changes, per 0C.12).

Then state the Phase 1 verdict plainly: does the depth hold clear, and for which families.
GAME_WINNER's pre-slate-PASS / mid-slate-FAIL reversal is a Phase 1 BUILD-ORDER input
(moneyline may be T1-shaped, not T4-shaped, since its liquidity concentrates pregame and thins
in play — the inverse of props). Standing operator instruction: do NOT declare GAME_WINNER or
PARTIAL_GAME_WINNER dead.

SCOPE FENCE: read-only measurement + the action-plan checkbox. No src/, no sizing, no cron
change. [STALE per GG-171 — see below: T-436 delivered and the operator ruled Phase 1 unblocked
same-session; this line's "do NOT start Phase 1" instruction no longer applies. Left in place
verbatim rather than deleted so the T-436 task-template record stays honest about what was
actually instructed at claim time.]

REPORT BACK: branch + commit range; the per-family table; the go/no-go verdict.
```

---

## Phase 1 entry criteria — the forward-motion trigger

**UNBLOCKED as of 2026-08-10 (operator adjudication, "Good to unblock," GG-171 RESOLVED).**

Both conditions below are now met:

1. ~~**T-431 lands**~~ — **does not gate box 1.6.** T-431's remaining scope (re-deriving ~1,220 stale outcome/pnl values) touches resolution fields that T-427's replay-determinism audit (`T427_REPLAY_DETERMINISM_AUDIT.md`) explicitly excludes from box 1.6's gate (Class A exclusion set: entry-time fields only, e.g. the vig-cascade/fee formula — not outcome/pnl). This file previously stated T-431 as a hard co-blocker; that was wrong, per GG-171. T-431 remains open and important in its own right (GG-170, root-caused, VPS-coordinated re-derivation still pending) — it just isn't a Phase 1 precondition.
2. **T-436 cleared** — depth verdict delivered 2026-08-10: 4/6 families PASS the $10.00 gate (GAME_TOTAL $179.55, GAME_WINNER $11.33, RUN_LINE $141.36, TEAM_TOTAL $57.96); PARTIAL_GAME_WINNER ($1.28) and PLAYER_PROP ($8.03) FAIL but are not declared dead per standing operator instruction. Full table in `MARKET_EXPANSION_ACTION_PLAN.md` 0I.1/0C.12.

Phase 1's eight boxes can now run, with the replay harness T-427 already built (`T427_REPLAY_DETERMINISM_AUDIT.md`, incl. its Class D formula-drift finding and the box-1.6 gate correction above) and the corrected suite baseline (2,799 passed / 8 known-failed / 29 skipped — re-run, do not copy).

**Phase 1 is where the bot's capability actually moves.** Everything above it is the cost of being able to trust what it reports.

---

## Needs your decision, not a window

**ADR-0051 (DRAFT) — premise verified, blocker cleared.** It proposes a terminal state for the 17 stuck T1/MAIN positions ($160.24 paper capital in limbo), described as "confirmed permanently unresolvable." My Wave 6 prompt asked Window P to check whether they were GG-166 collateral — a forward-skewed `game_date` returns no gameLog split, **indistinguishable from genuine data absence at the call site**. That check was never run. I ran it: **0 of 17 have a `game_date`/ticker mismatch.** All correctly dated, consistent with T1/MAIN measuring 0/485 on assertion A. The unresolvability is a genuinely separate cause and **the draft's premise stands** — that was the one thing that would have made signing it wrong.

**GG-162 — five ID collisions now** (GG-159 ×2, GG-163 ×2, T-415 ×2, T-427 ×2, T-431 ×2). Still unstaffed. T-432/T-433 running in parallel is the sixth opportunity.

## Queued behind Phase 1's epoch boundary

| Item | Source |
|---|---|
| `mark_aged_open()` terminal state | ADR-0051 — awaiting your sign-off |
| Severity backfill, remaining entries | GG-165 |
| GG-NNN atomic reservation | GG-162 |
| `deploy.yml` dirty-tree guard | GG-167 |

---

## Done this run — context only, no action

| ID | Task | Result |
|---|---|---|
| **T-434** | Protocol session-sizing patch | Merged `40f6385`. Hard Rule 8 → 60% trigger; new Hard Rule 11 (one deliverable, tier at claim, register-and-stop). All 5 verifications passed: no stray `80%`, Rules 10+11 both intact, **T-429's Step-4 write-recency detector survived** the CLAUDE.md edit (the live risk), zero `src/` touched. Registered GG-168 (tracked as T-435). |

Prompt block deleted per the rule above. Full record: `SESSION_CLAIMS.md` 2026-08-10T23:49:32Z · `DECISION_LOG.md` · commits `eb4cabc`, `68bde6c`, `40f6385`, `1ecc13a`.

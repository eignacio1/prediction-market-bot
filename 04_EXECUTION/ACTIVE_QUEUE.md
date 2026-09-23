# Active queue — the only prompt file to read

> **RULE, adopted 2026-09-23 after an operator caught this file carrying four closed waves' fences:
> this file contains ONLY blocks that are currently firing.** Closed block prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`. Closed waves stay visible here as sequencing-track rows
> and outcome prose, never as pasteable fences. If you find a fence in this file for a wave the
> sequencing track marks CLOSED, that is a defect — archive it before doing anything else.

**Verified against:** `origin/main = 18b0e0d` (2026-09-23). *This window cannot `git fetch` (no
credentials on this machine). Every block fetches first. A LANDED call is safe from a stale ref; a
"not landed" call is not — say "not visible at my ref," never "did not land."*

**Live state, derived at `18b0e0d`:** 92 cells · 22 execution bands · **1 cell ACTIVE**
(MLB player-prop hits x T4M-PROJ) · 88 NOT_IMPLEMENTED · 2 BLOCKED · 1 DARK ·
**134 gap-log entries, 91 OPEN, next free GG-296.** Header/status parity 134=134 ✅.

> **⚠️ THE SHARED WORKING TREE IS 7 COMMITS BEHIND `origin/main`** (local `c68a9c8` vs origin
> `18b0e0d`) **and holds the only copy of this rebuilt queue plus its new archive file.**
> All of Wave 31's results are on origin only. Anything deriving state from the shared tree reads
> pre-Wave-31 reality — the same trap that hid GG-295 last wave.
> **Fixed by 32.1's Deliverable 0, which runs before anything else and owns the shared tree this
> wave.** 32.2 and 32.3 are explicitly locked out of it. Until 32.1 reports Deliverable 0 clean,
> derive from `origin/main` directly, never from the shared tree.

**NFL T1:** 20 of 42 positions settled 2026-09-23 (+$13.4778); **22 remain open** pending finality.
**MLB T4M-PROJ:** clean_n 765, frozen since 2026-08-13. **Regular season ends ~2026-09-28.**

---

## ⬛ FIRE NOW — Wave 32, three blocks, concurrent

Paste each fence below into its own terminal. Disjoint by design; all three may start at once.

| Paste | Block | Tier | One-line purpose |
|---|---|---|---|
| 1st | **32.1** | STANDARD | Replace the edge gate's assumed vig with a measurement, per series family. |
| 2nd | **32.2** | STANDARD | Rank all 11 series by measured efficiency; locate the bot on its own gradient. |
| 3rd | **32.3** | STANDARD | Fund the demo shard properly, accrue UNBIASED, confirm a fill. **Expires 2026-09-28.** |

**Fire order does not matter.** 32.1 and 32.2 own separate `scripts/` modules and separate
`exp_output/` directories. 32.3 owns the VPS, the Kalshi demo account and the MLB ledgers, **and is
the only block this wave authorized to write `GOVERNANCE_GAP_LOG.md` or `DECISION_LOG.md`.**

**There are exactly three fences in this file. If you see a fourth, something is wrong — stop.**

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

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10–28 | ✅ CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` and `11_MEMORY_HANDOFF/` |
| **29** | ✅ CLOSED (1 of 3 executed) | 29.2 gated STOP (shard 3 was $0.00); 29.3 landed via T-562; **29.1 claimed and never executed** — superseded by 30.1. Prompts archived. |
| **30** | ✅ CLOSED (superseded) | T-563 fixed the `kalshi_threshold` write path and found the backfill already done by an unidentified actor → **GG-295 registered, HIGH, OPEN.** Deliverable 5 never ran; carried into 31.2. Prompt archived. |
| **31** | ✅ **CLOSED — ALL THREE LANDED** (`18b0e0d`) | Calibration finding **reproduced in full**; first real NFL settlement (20/42, +$13.4778); estate reconciled 58→20 branches, 61→25 worktrees. Prompts archived. |
| **32** | ⬜ **FIRING** | Vig grounding · efficiency-gradient ranking · MLB final-week accrual. |

---

## ✅ WAVE 31 — CLOSED, ALL THREE LANDED (verified at `origin/main = 18b0e0d`, 2026-09-23)

**31.1 (T-565) — the calibration finding REPRODUCED, and corrected one of its own premises.**
All 13 figures reproduced exactly from the live ledger (live file and mirror both 2994 closed /
765 clean — the mirror was not stale). Material by the pre-registered standard.
**But Deliverable 3 found the ADR-0046 comparison is NOT COMPARABLE on four of five dimensions**
(filter, directional convention, band scope, epoch window). The near-equality of Brier 0.2191 vs
baseline 0.2190 is **coincidence with no interpretive weight** — two different measurements sharing
a name. Every "in line with baseline" claim, including the strategic window's own, is withdrawn.
The model-vs-market result does not depend on it and stands.
Also found: **ADR-0046's own ECE drifted 0.0680 -> 0.0832 (+22%)** on identical methodology at
larger n. The baseline constant is not stable. And **T1 clean_n = 0 is structural** — T1's ledger
stopped at epoch 8 while `CURRENT_LOGIC_EPOCH` reached 12, so T1 cannot be calibrated at all from
available data. **The `rejected_positions` holdout idea is dead**: those 2000 rows are not
risk-engine declines, they are exchange-side order failures (see below).

**31.2 (T-564) — first real settlement in project history.** 20 of 42 positions settled (games
final; 22 remain open), **+$13.4778 P&L**, byte-identical idempotency, zero refusals.
GG-291 / GG-274 / GG-287 RESOLVED.

**31.3 — estate reconciled.** 58 remote branches -> 20 (17 unmerged, protected as scoped);
61 worktrees -> 25; stranded handoff commits landed.

---

## ⚠️ PORTED FROM 31.2 — NOT DONE, MUST LAND IN WAVE 32

**The model-provenance check never ran.** It was flagged after the block was already taken; a grep
of every Wave 31 commit message for `stub` / `provenance` / `EXP027` returns **zero matches**.

**20 resolved NFL rows now exist in the live ledger, and nobody has established which model wrote
them.** `run_t1_nfl_game_market.py::main(model=None)` defaults to `StubNFLForecastModel`
(`PROVENANCE = "STUB ... NOT a trained model, GG-255"`). Nothing in `src/`, `scripts/` or
`deploy/` ever passes `EXP027NFLForecastModel` into it; `web_dashboard.py` reads EXP-027's
provenance string as a **display label only** and never instantiates the model. There is no NFL
entry in `deploy/cron.conf`, so every run was launched by hand and the model argument is not
recoverable from the repo.
**GG-274/GG-287's RESOLVED status is defensible** — the settlement *path* was genuinely exercised.
**The 20 rows are not.** Until provenance is established they must not enter G6 evidence, NFL
calibration, or any `clean_n`. **Settle for path validation; quarantine for evidence.**
This is GG-267's subject (per-row model provenance), still on an unmerged branch.

---

## ⚠️ NEW, AND IT CHANGES 32.3 — T4 IS NOT STARVED, IT IS STOPPED

Derived 2026-09-23 from the T4 ledger's `rejected_positions`:

**2,000 C4-approved T4M-PROJ orders were generated in a single 6.8-hour window**
(`2026-09-20T19:07:38Z` -> `2026-09-21T01:57:32Z`), all on one `game_date` (2026-09-20),
**every one failed with `insufficient_shard_balance`.** Intended stake total: **$1,907.85**.

Three consequences, all load-bearing:

1. **"Why only 42 positions" was the wrong frame for T4.** T4M-PROJ approves at ~2,000 orders per
   game-day. It is not opportunity-starved; it is collateral-stopped.
2. **2,000 is the ring-buffer ceiling, not the true count** (GG-271's bounded buffer, ACTIVATED
   2026-09-15). The real volume that day was **at least** 2,000 and is unknown above it.
3. **$200 on shard 3 against $1,907.85/day of intended stakes is ~10x under-funded.** Restarting
   accrual as-is would exhaust collateral inside the first hour of a game night, and every
   subsequent approval would fail exactly as before — meaning the day's accepted positions would
   be **the first ~200 approvals of the night, not a random sample of it.** Those correlate with
   early-inning game state. **That is a selection bias, and it would be injected straight into the
   only clean cohort the project has.**

**Therefore 32.3 is re-scoped.** Naive "restart accrual" is withdrawn. Demo collateral is
plumbing (operator standing directive: sandbox/paper/demo actions are handled, not escalated), so
the block funds shard 3 to cover measured demand with headroom *before* accruing, precisely to
avoid buying 1,200 truncated, early-inning-biased rows into the 765-row cohort.

---

## ⬜ WAVE 32 — THE PENDULUM SWINGS. Ready to fire.

**Operator directive, 2026-09-22:** reformat focus from infrastructure toward edge calibration.
Not 100% — standing split from here is **2 of 3 blocks calibration/grounding, 1 of 3 plumbing.**

**The unlock:** `exp_output/PRICE_ARCHIVE/` holds **913 MB, 1,817,644 rows, 54 days
(2026-08-01 -> 2026-09-23)** across eleven Kalshi series families — each row carrying
`yes_bid/ask`, `no_bid/ask`, `last_price`, `volume`, `open_interest`, `liquidity`, `yes_mid`,
`half_spread` — plus 51 orderbook-depth files. Sampled coverage: `KXMLBHIT` 49,931 ·
`KXMLBTEAMTOTAL` 37,412 · `KXMLBTOTAL` 29,179 · `KXMLBSPREAD` 17,068 · `KXMLBGAME` 15,536 ·
`KXMLBF5/F3/F7` variants ~50,000 · `KXNFLGAME`/`KXNFLTOTAL` 201 each.
**Grounding needs market data, not bets. Neither calibration block requires placing a position.**

| # | Block | Tier | Why now |
|---|---|---|---|
| 32.1 | **Ground the edge gate — real vig per series** | STANDARD | `model_p > mip + vig` is the most load-bearing filter in the system and its cost term is an assumption. Every cell inherits the fix. |
| 32.2 | **Rank the efficiency gradient across 11 series** | STANDARD | Converts CLAUDE.md's explicitly-unadjudicated operator decision from argument into measurement. Feeds APR-0035. |
| 32.3 | **MLB final week — fund, accrue unbiased, confirm a fill** | STANDARD | Expires 2026-09-28. Re-scoped: see the collateral/selection-bias finding above. |

**Surfaces:** 32.1 owns `scripts/` vig code + its `exp_output/` dir. 32.2 owns a separate
`scripts/` efficiency module + its own output dir. 32.3 owns the VPS, the Kalshi demo account and
the MLB ledgers. **32.3 owns `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` this wave.**

---

# 32.1 — GROUND THE EDGE GATE · REAL VIG PER SERIES · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "vig-grounding-from-archive"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md THIS WAVE. 32.3 owns them. ***
*** Record gap candidates in your own results file for 32.3 to register. ***

TIER: STANDARD. *** YOU ALSO OWN THE SHARED `main` TREE THIS WAVE. DELIVERABLE 0 FIRST. ***

DELIVERABLE 0 -- SYNC AND LAND THE SHARED TREE. DO THIS BEFORE YOUR WORKTREE, BEFORE ANALYSIS.
  The shared working tree is 7 commits behind `origin/main` (local `c68a9c8` vs origin `18b0e0d`)
  and carries the strategic window's uncommitted Wave 32 queue rebuild. Both halves matter: a
  session deriving state from the shared tree reads PRE-Wave-31 reality, and the rebuilt queue +
  its new archive file exist nowhere but that tree.
  Derived 2026-09-23 in the shared tree -- re-derive, do not trust these:
    dirty:    03_DECISIONS/OPERATOR_CONSOLE.md (generated), 04_EXECUTION/ACTIVE_QUEUE.md
    untracked: 04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md, "Reload Dashboard.command"
    incoming: 13 files, NONE of which collide with the dirty set -- a ff-only pull is clean
  (a) `git fetch origin`, then re-run the collision check yourself before pulling:
      compare `git diff --name-only HEAD origin/main` against your dirty set. If ANY file appears
      in both, STOP and report -- do not pull, do not stash, do not check out over it.
  (b) `OPERATOR_CONSOLE.md` is a GENERATED file (`scripts/generate_operator_console.py`, run by
      `.claude/hooks/governance_scan.sh` every scan). Its diff is hook output, not work. Discard it
      -- T-533 precedent, DECISION_LOG 2026-09-09. Leave "Reload Dashboard.command" alone.
  (c) `git pull --ff-only`. If it refuses, STOP and report the exact refusal. Never force it.
  (d) Commit and push, PATH-SCOPED, exactly these two paths and nothing else:
      `04_EXECUTION/ACTIVE_QUEUE.md` and `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`.
      Never `git add -A`, `git commit -a`, unscoped `stash`, `reset --hard`, or `clean -fd` --
      32.2 and 32.3 are running concurrently and the shared tree is not yours alone.
  (e) Verify and report: shared tree at `origin/main`, both queue files visible on origin, and the
      queue's own invariant holds -- exactly THREE fenced blocks in `ACTIVE_QUEUE.md`
      (`grep -c '^```' 04_EXECUTION/ACTIVE_QUEUE.md` returns 6).
  (f) Then check whether this is structurally preventable: does
      `.claude/hooks/session_guard.sh` actually surface shared-tree-behind-origin as a visible
      warning? It is documented as checking "HEAD-vs-origin drift," yet the tree reached 7 commits
      behind with nobody noticing. If the check is absent, silent, or only fires on a different
      condition, record it as a gap candidate against **GG-260** (OPEN -- shared-tree drift
      invisible to worktree-isolated sessions) for 32.3 to register. Do not fix it this session.

The C4 edge gate is `model_p > market_implied_prob + vig`. The `vig` term is an assumption. The
price archive carries an observed `half_spread` and full bid/ask on 1.8M rows. This block replaces
the assumption with a measurement, per series family. It does NOT change the gate.

DELIVERABLE 1 -- WHAT IS THE GATE USING TODAY? Read it out of the code, not the docs.
  Enumerate every place a vig / cost / spread term enters an edge or gating decision across
  `risk.py`, `run_t4_mlb_live.py`, both T1 game-market run scripts, `run_t2_mlb_sameday.py` and
  `execution_bands.py`. For each: the literal value or expression, its provenance if traceable,
  and whether it is per-series or global. Report before analyzing anything.

DELIVERABLE 2 -- MEASURE THE REAL DISTRIBUTION, PER SERIES FAMILY.
  Per `series_ticker`: distribution of `half_spread` and of `(yes_ask - yes_bid)` -- median, IQR,
  p90 -- and how each moves with `yes_mid` (spreads widen at the tails) and with time-to-close.
  Report n and date span per series. Handle the `.BROKEN_FIRSTRUN` file explicitly: say whether
  you included it and why.

DELIVERABLE 3 -- QUANTIFY THE GAP. DO NOT CLOSE IT.
  Per family: what the code assumes vs what the market charged. State whether the current constant
  is conservative (over-charges, suppresses bets) or permissive (under-charges, approves bets with
  no real edge), in probability points.
  Then re-run the T4M-PROJ epoch-12 clean cohort's 765 gate decisions under measured vig and report
  how many flip. That number is the finding.

DELIVERABLE 4 -- WRITE IT UP AS AN APR, NOT A CODE CHANGE.
  Changing a live gating constant requires an ADR (Hard Rule 3). Draft the decision request with
  the measured values as evidence. Do not implement. Do not change a constant.

DO NOT: change any vig, cost, spread or gating constant anywhere in src/.
DO NOT: touch kelly_fraction, promote a cell, submit an order, or restart a service.
DO NOT: modify or re-time a price-capture window. Reading the archive is fine.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 32.3 owns them.
DO NOT: touch the efficiency module or its outputs -- 32.2 owns those.
DO NOT: recommend against a series family on this finding alone (standing DO NOT).
DO NOT: cite ADR-0046's BRIER/ECE baselines as a validity reference -- T-565 proved them
  NOT COMPARABLE to band-scoped cohorts, and its ECE baseline drifted +22% at larger n.

SCOPE FENCE: Deliverable 0's shared-tree sync plus the two queue files named there; then one new
analysis script under `scripts/`, its `exp_output/` dir, a results summary under
`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`, one APR draft under `00_ADMIN/`.

REPORT BACK: Deliverable 0 first -- your own collision check, the pull result, the two paths you
committed, the three-fence verification, and your finding on `session_guard.sh`. Then: the
code-derived inventory of every live cost term; measured per-series spread distributions with n and
span; assumed-vs-actual gap per family in probability points; how many of the 765 gate decisions
flip under measured vig; and the APR draft path.
```

---

# 32.2 — RANK THE EFFICIENCY GRADIENT · 11 SERIES · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "efficiency-gradient-ranking"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md THIS WAVE. 32.3 owns them. ***

TIER: STANDARD.

CLAUDE.md states the strategy only works where pricing is inefficient, then states -- in its own
words, as an OPEN OPERATOR DECISION that must not be resolved in-session -- that the coverage
target expands toward moneyline, run line and totals, the opposite end of that gradient. That
tension has never been measured, only argued. The archive can measure it.

DELIVERABLE 1 -- PRE-REGISTER THE RANKING METRIC BEFORE COMPUTING IT.
  Write, commit and push, BEFORE any analysis: which observables define "more efficient" here, how
  they combine, and the ordering you expect. Consider and justify including or excluding: relative
  spread at comparable `yes_mid`, depth from `depth_*.jsonl`, price-discovery speed (variance of
  `yes_mid` changes approaching close), volume and open_interest, and distance from `last_price`
  to closing price. Immutable once pushed -- do not relabel after seeing the ranking.

DELIVERABLE 2 -- RANK THE ELEVEN FAMILIES.
  Per-family n, date span, and a stated uncertainty on each position. A rank with overlapping
  error bars is a TIE and must be reported as one.
  Report MLB and NFL separately: NFL has ~201 rows per family against MLB's tens of thousands.
  If NFL is not yet rankable, say so plainly rather than ranking it.

DELIVERABLE 3 -- LOCATE THE BOT ON ITS OWN GRADIENT.
  Where does `KXMLBHIT` -- the one cell that has ever traded -- sit? CLAUDE.md asserts player props
  in low-attention MLB windows are the inefficient end. Is that true in the data, or a belief the
  project has been operating on?
  Then: where would each of the core four (moneyline, spread, totals, team totals) place the bot?
  Present as evidence for the operator's decision. **Do not make the decision.**

DELIVERABLE 4 -- WRITE IT UP AS THE INPUT TO THAT DECISION.
  A summary an operator can read in five minutes: the ranking, the tie structure, where the bot
  sits, and explicitly what this does NOT establish (efficiency is not edge; a thin market can be
  thin and still unbeatable).

DO NOT: resolve the operator decision, recommend a market family, or soften the tension into a
  monitoring note. CLAUDE.md forbids all three explicitly.
DO NOT: recommend against a sport or market family on one finding (standing DO NOT).
DO NOT: change any constant, cell status, kelly_fraction, or capture window.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 32.3 owns them.
DO NOT: touch the vig module or its outputs -- 32.1 owns those.
DO NOT: pull, commit, push or otherwise touch the shared `main` working tree -- 32.1 owns it this
  wave (its Deliverable 0). Work only in your own worktree.

SCOPE FENCE: one new analysis module under `scripts/`, its own `exp_output/` dir, and a results
summary under `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`.

REPORT BACK: the pre-registration as pushed; the eleven-family ranking with n, span and ties;
where KXMLBHIT actually sits and whether CLAUDE.md's premise survives; where the core four would
place the bot; and an explicit list of what this does not establish.
```

---

# 32.3 — MLB FINAL WEEK · FUND, ACCRUE UNBIASED, CONFIRM A FILL · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "mlb-final-week-accrual"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md AND DECISION_LOG.md THIS WAVE. ***

TIER: STANDARD. *** EXPIRES 2026-09-28 -- MLB regular-season end, derived from archive
close_times (KXMLBGAME 09-28; TOTAL/SPREAD/TEAMTOTAL/F5/F3/F7 09-27; KXMLBHIT 09-26). ***

T4M-PROJ is the only ACTIVE cell and the only cohort with a real clean_n (765, frozen since
2026-08-13, 11 game-days). It is NOT opportunity-starved: on 2026-09-20 it produced >=2,000
C4-approved orders in 6.8 hours totalling $1,907.85 of intended stake, and every one failed
`insufficient_shard_balance`. Shard 3 holds $200 -- roughly 10x under-funded.
The goal is NOT volume. It is (a) ONE fill confirmed from the live service, and (b) any rows
added being UNBIASED -- a collateral-truncated night injects an early-inning selection bias
straight into the project's only clean cohort.

DELIVERABLE 1 -- MEASURE TRUE DEMAND. 2,000 is a ring-buffer ceiling, not a count.
  GG-271's bounded `rejected_positions` buffer (ACTIVATED 2026-09-15) caps at 2,000, so real
  2026-09-20 volume is unknown above that. Recover it from the audit trail / cycle log, not the
  portfolio array. Report approvals per game-day for the last 7 days, intended-stake total per
  day, and the observed per-day maximum. If the true count cannot be recovered, say so and use
  2,000 as an explicit LOWER BOUND -- never present the ceiling as the count.

DELIVERABLE 2 -- FUND SHARD 3 TO COVER MEASURED DEMAND, WITH HEADROOM. Demo collateral only.
  Sandbox/demo action, pre-authorized by standing operator directive. NOT a capital decision and
  must NOT be escalated. Move demo funds so shard 3 covers D1's measured daily intended stake
  plus at least 50% headroom.
  Read `GET /portfolio/balance`'s `balance_breakdown` ARRAY before and after and paste both --
  the aggregate is what fooled every read for 38 days. Pass `authenticated=True` on every
  portfolio read: `_get()` defaults to `authenticated=False`, resolving to PRODUCTION regardless
  of BOT_ENV (T-556, unfixed).
  *** If the demo account cannot reach that level, STOP and report. Do NOT accrue on a
  known-truncating balance -- a biased cohort is worse than no cohort. ***

DELIVERABLE 3 -- OBSERVE A REAL FILL FROM THE LIVE SERVICE.
  GG-203 closes only when the running `t4-mlb` service converts an approval into a fill -- NOT a
  hand-built order succeeding. Report the approval, order id, fill, and resulting ledger row.
  If no approval fires in the window, that is a finding: report evaluation counts and say so.
  NO RESTART IS AUTHORIZED. If you believe one is required, register and stop.

DELIVERABLE 4 -- CHARACTERIZE WHAT THE COHORT GAINED. The calibration track depends on this.
  For every position added: how many, across how many distinct game-days, and the within-day
  distribution by inning / `ab_remaining_at_entry`. Compare that shape to the existing 765.
  State plainly whether collateral ran out on any night and at what clock time -- if it did, rows
  after that point are missing non-randomly and the day is contaminated. FLAG such a day for
  exclusion; do not exclude it yourself.
  Report final T4M-PROJ clean_n, final game date accrued, and the freeze date.

DELIVERABLE 5 -- UPDATE ONLY WHAT IS PROVEN, AND CLEAR T-565'S BACKLOG.
  GG-203 stays PARTIALLY RESOLVED unless a service-produced fill was observed.
  Register the gap candidates in T-565's results file ("Gap candidates for 31.2" -- 31.2 never
  registered them), including the `rejected_positions` naming/framing mismatch and ADR-0046's
  ECE instability (0.0680 -> 0.0832, +22%, identical methodology at larger n).

DO NOT: restart any production service.
DO NOT: touch kelly_fraction or sizing. ADR-0050's flat measurement stake is the authorized
  configuration; funding collateral is not a sizing change and must not become one.
DO NOT: submit an order against the production account or with real funds. Demo only, always.
DO NOT: accrue on a balance you have shown will truncate the night.
DO NOT: manufacture a position, row, cohort member or outcome.
DO NOT: modify or re-time a price-capture window.
DO NOT: touch `scripts/` analysis code or `exp_output/` -- 32.1 and 32.2 own those.
DO NOT: pull, commit, push or otherwise touch the shared `main` working tree -- 32.1 owns it this
  wave (its Deliverable 0). Work only in your own worktree.

SCOPE FENCE: the VPS t4-mlb service (observation only), Kalshi demo account collateral,
kalshi_client.py reads, the MLB ledgers, GOVERNANCE_GAP_LOG.md, DECISION_LOG.md.
Self-serialising close-out: re-read both logs fresh against HEAD immediately before writing.

REPORT BACK: true approval volume per game-day with the ring-buffer caveat stated; per-shard
balance breakdown before and after funding, verbatim; whether a service-produced fill was observed
and its full trail; the added cohort's day/inning shape vs the existing 765; whether any night
truncated and when; final clean_n and freeze date; and what GG-203 still lacks.
```

---

## THE RETIREMENT MECHANISM — specified, ready to fire as Wave 33's plumbing slot

**The diagnosis, in one line: every artifact in this project has an automated, enforced creation
path and a manual, remembered retirement path.**

`claim_session.sh` reserves IDs atomically with rebase-retry so two sessions cannot collide.
`new_session_worktree.sh` creates isolation by default. Gap registration is mandatory and checked.
Creation is a machine step. **Retirement is a person remembering** — and that worked when the
project was small and navigable. It does not survive 12 departments, 134 gaps, 254 sessions and
2,150 commits. The observed debt is not carelessness; it is the predictable output of an asymmetry.

**Measured retirement debt, 2026-09-22 at `e9a335d`:**

| Department | Debt | Should have been retired by |
|---|---|---|
| `03_DECISIONS` | **23 resolved-class entries still in the live gap log** | the T-420 archive-move, per its own contract |
| `00_ADMIN` | **ADR-0063 and APR-0035 signed in chat, no register row** | the signing session (GG-126 class, 6+ recurrences) |
| git estate | **40 merged branches undeleted, 59 prunable worktrees** | `/session-end` Step 9 |
| git estate | **54 commits stranded across 16 unmerged branches** | each session's own close-out |
| `03_DECISIONS` | **operator console reports 133 open against a real 94** | never — it has no retirement awareness at all |

**The design principle: retirement becomes symmetric with creation — a machine step that runs
whether or not anyone remembers.** Five components, in dependency order:

1. **`scripts/retire_resolved_gaps.py`** — moves every live-log entry whose Status token is
   resolved-class, verbatim, into `GOVERNANCE_GAP_LOG_ARCHIVE.md`. Must handle the format drift
   that already exists: bare `RESOLVED`, dated variants (`RESOLVED (2026-09-11)`,
   `RESOLVED 2026-08-28 (T-502)`), `CLOSED-AS-ARTIFACT`, and one entry whose Status value is a
   full paragraph. Idempotent; archive stays append-only and entries never move back.
2. **A parity assertion in `.claude/hooks/governance_scan.sh`** — the live log must contain ZERO
   resolved-class statuses. **This one check would have caught all 23 on day one.** Ship it
   warn-only for one wave, then make it hard-fail.
3. **`generate_operator_console.py` gains a resolved filter and a new Section 0: "Overdue for
   retirement."** Not just gaps — one roll-up across all twelve departments: unarchived resolved
   gaps, merged-but-undeleted branches, prunable worktrees, ADR/APR accepted-without-a-register-row,
   and session claims with no closure row. **This is the CEO dashboard for the company: one number,
   read weekly, that says what should have closed and didn't.**
4. **Extend `sweep_stray_branches.sh`** to also delete merged remote and local branches (`-d`,
   never `-D`) and prune worktrees. It already runs as `/session-end` Step 9, so the cadence exists
   — only the scope is missing.
5. **`check_register_parity.py` gains the reverse direction** — any ADR or APR whose own file
   reads ACCEPTED must have a register row. It currently checks one way only, which is why
   ADR-0063 is invisible to it.

**Deliberately NOT in scope:** changing any gap's status, closing anything, or judging whether work
is finished. This mechanism only moves things that are *already* marked done into where done things
live. Retirement is filing, never adjudication.

---

## THE ARC — Waves 32 through 37

Sequenced, not pre-written. Each wave is drafted only once its predecessor reports, because every
one of these depends on what the last one found. Standing split: **2 calibration, 1 plumbing.**

| Wave | Calibration / grounding | Plumbing | The question it answers |
|---|---|---|---|
| **32** | Vig grounding · Efficiency-gradient ranking | MLB final-week accrual (expires 09-28) | *Are our cost terms and our market choice grounded in anything?* |
| **33** | T4 latency measurement — **the alpha thesis itself**, testable from the intraday archive against ESPN state, with zero bets | The retirement mechanism above | *Does the market actually lag live game state? If not, T4 has no thesis.* |
| **34** | Closing-line-value harness — the reusable scoring instrument every future cell inherits · Depth distributions, which may already clear APR-0029 D1/D3 | Branch routing pass (after your keep/kill) + registry-vs-reality sync | *Can we score a model without waiting a season for P&L?* |
| **35** | Model inventory across all 14 market types — **which cells have a real forecaster and which have a stub** · NFL positions' provenance (GG-267) | GG-038 kill-switch defects / NFR-03 | *How many of the 92 cells can even be calibrated, versus needing a model built first?* |
| **36** | Per-cell calibration of whatever real models Wave 35 found, scored on the Wave 34 harness | Cell activation sequencing driven by Wave 32.2's measured gradient | *Which cells have measurable edge, ranked by evidence rather than convenience?* |
| **37** | **APR-0035 forced to a decision** with Waves 32–36 in hand | G6 / registry reconciliation under ADR-0057 | *What are we accruing toward, and is it the right thing?* |

**The shape of the arc: ground the shared machinery (32–34) → test the theses (35–36) → decide (37).**

Three things that could reorder it, and should:
- If **31.1 fails to reproduce** the model-vs-market result, Wave 33 changes — the latency test
  becomes more urgent, not less, because the thesis would still be open rather than damaged.
- If **32.2's ranking puts `KXMLBHIT` in the efficient half**, the efficiency premise the whole
  strategy rests on is wrong, and that reorders everything after it.
- If **Wave 35 finds most cells are stub-backed**, then "calibrate the core four" is still a
  modeling problem wearing calibration's clothes, and 36 becomes a build wave.

---

## Queued next — not yet fired

**APR-0035 — force it to a decision (arc: Wave 37).** The P&L gate is ~1.6 MLB seasons / ~11 NFL
seasons from clearing at measured effect sizes. **31.1 reproduced the model-vs-market result in
full**, so the question has already changed shape: it is no longer "how long to reach n*" but "is
this cohort worth accruing." Do not pre-write the answer into this queue — it is the operator's.

**GG-295 actor provenance — SHORT block, terminal only.** T-563 established content provenance
(42 rows, three fields, diffed against the pre-backfill snapshot). Actor identity is unestablished
and needs VPS shell/SSH history around 2026-09-18T19:04 UTC. Deliberately did not gate 31.2 — the operator's call,
2026-09-22; 31.2 settled 20/42 without it. Also in scope when it fires: audit every other `repair_ref` stamp in
the codebase for the same corroboration gap, per GG-295's own recommendation (3).

**GG-203 — watch for a real fill.** Shard 3 is funded ($200, 2026-09-22). No order has been
confirmed to fill. Closes only when the live `t4-mlb` service is observed converting an approval
into a fill — not a hand-built order succeeding. No restart is authorized.

**MLB T1 game markets have never run live.** The path uses `kalshi_client=None` so GG-203 never
blocked it. Blocked instead on the model question: its default is
`StubMLBGameMarketForecastModel`, and stub-sourced positions are worth nothing. Establish whether
EXP-026/HYP-011 produced a real forecaster before scheduling it.

**The branch routing pass — the one that needs you, briefly (arc: Wave 34's plumbing slot).**
31.3 has run: the estate is now 20 remote branches, of which **17 are unmerged**, holding ~54
unique commits. 31.3 deliberately did not touch them. They sort into four buckets; only bucket B needs an operator call:

- **A — free delete (1 branch).** `session/20260903T184908Z-apr0033-accept-and-reroute` has 0
  unpatched commits by `git cherry` — its content is already in main by equivalent patch.
  Verify post-fetch, then delete.
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

**`OPERATOR_CONSOLE.md` — the live gap log has 23 resolved entries in it, and the generator counts them as open.**
Derived 2026-09-22. The file is generated by `scripts/generate_operator_console.py` from
`.claude/hooks/governance_scan.sh` on every scan, which is why it shows as uncommitted drift in the
shared `main` tree (GG-260's class). That part is benign. The defect underneath is not:
`classify()` has **no resolved filter** — every entry in the live log is bucketed
blocked/broken/accruing. It relies on T-420's guarantee that resolved entries are moved verbatim to
`GOVERNANCE_GAP_LOG_ARCHIVE.md`, and that discipline has lapsed. Live-log status distribution:
94 `OPEN`, but also **10 `RESOLVED`, 8 `PARTIALLY RESOLVED`, 2 `LIKELY RESOLVED`, 1 `PARTIAL RESOLVE`,
and 9 `RESOLVED (<date/task>)` variants — 23 resolved-class entries total.** The console therefore
reports "133 open/in-progress entries" against a committed baseline of 83.
CLAUDE.md Step 3 states the split made it "structurally impossible" for this file to contain a
RESOLVED entry masquerading as open. That claim is now false. **Gap candidate — unregistered,
for the next wave that owns the gap log.**

**GG-279 — deploy-vs-activation has no structural check.** One SHORT block.

---

## Needs your decision

| Item | Plain English | What happens if it waits |
|---|---|---|
| **APR-0035** | The n\* wall — and it may have just changed shape. If 31.1 reproduces, the model is losing to the market's own price on the exact bets it selected as its best. The question stops being "how many seasons to reach the gate" and becomes "is this the right thing to accrue." | G6 cannot close on P&L evidence in any practical horizon until this is settled. Fourth week open. |
| **ADR-0063** | Emergency-stop / bet-sizing hierarchy. Approved in chat 2026-09-18 — **still needs a signature row in `APPROVALS_REGISTER.md`.** This window confirmed by grep that no row exists. | Until the register row exists, nothing downstream can cite it. |
| **APR-0034** | Whether T4 MLB should stop sending demo orders. | **Likely moot** now shard 3 is funded — withdraw it once a fill is confirmed. |
| **GG-292** | Stray branches, oldest ~2 weeks. Count unverified (see Queued next). | Each is someone's finished work. One routing pass from you turns them into blocks or closes them out. |

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

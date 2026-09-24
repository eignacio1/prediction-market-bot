# Active queue — ARCHIVE of closed block prompts

**These blocks are CLOSED. They are kept verbatim for provenance only.**
**Do not paste anything from this file into a terminal.** The live queue is
`04_EXECUTION/ACTIVE_QUEUE.md`, which by rule contains only blocks that are currently firing.

Archived 2026-09-23 from `ACTIVE_QUEUE.md` at `origin/main = 18b0e0d`, after the queue was found
carrying four closed waves' fences (29.1/29.2/29.3/30.1) alongside live ones — an operator caught
it. Rule adopted at the same time: **the live queue holds only active blocks.**

---

## Wave 33 — CLOSED 2026-09-23 (all three landed)

**Recovered 2026-09-24.** These prompts were deleted from `ACTIVE_QUEUE.md` during the Wave 34
rotation without being archived first, in violation of the queue's own archive rule. Recovered
from the strategic window's delivered copy of the Wave 33 queue and restored here verbatim.

## ⬜ WAVE 33 — TEST THE THESIS, VERIFY THE COHORT

---

# 33.1 — THE T4 LATENCY THESIS · DOES THE MARKET ACTUALLY LAG? · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "t4-latency-thesis"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 33.2 owns them. ***
*** Record gap candidates in your own results file for 33.2 to register. ***

TIER: STANDARD. This is the most load-bearing untested claim in the project.

T4's entire thesis, stated in CLAUDE.md: "prediction markets are slow to incorporate live in-game
state... the market price lags behind the true updated probability... the market hasn't updated
yet, the bot has." Every T4 band, the 11-sub-band decomposition, and T4M-PROJ's ACTIVE status rest
on it. **It has never been measured.** This block measures it, and needs no bets, no fills, no
settlements and no ledger -- so its result survives whatever 33.2 finds about the ledger.

THE INSTRUMENT. `logs/t4_mlb_cycle_log.jsonl` on the VPS. Pull it fresh -- the local mirror
`logs/.vps_t4_mlb_cycle_log_cache.jsonl` stops at 2026-08-07 and must NOT be used as the source.
Every row carries, at a measured ~60s cadence (p10 56s / median 60s / p90 65s):
  ts, ticker, p_t4 (model prob), mip (market implied prob), vig, gross_edge, net_edge,
  h_so_far, ab_so_far, ab_remaining, inning, batting_slot, ba_l10, threshold, game_date
Both the model's probability AND the market's price AND the game state, side by side, per cycle.
In a 400k-row sample of the stale mirror, 9.8% of consecutive same-ticker pairs carried a game-
state change -- thousands of events. Re-derive that rate on the fresh pull; do not reuse it.

DELIVERABLE 1 -- PRE-REGISTER, PUSH, THEN COMPUTE. IMMUTABLE ONCE PUSHED.
  Write and push BEFORE any analysis: the exact event definition, the test statistics, the horizons,
  and what result you will call THESIS SUPPORTED / NOT SUPPORTED / INCONCLUSIVE. Include your
  handling of the two confounds named in D3. Do not relabel any of it afterwards.

DELIVERABLE 2 -- THE DIRECT TEST: does `mip` move AFTER a state change, or was it already there?
  Define a state-change event on a single ticker's time-ordered series (h_so_far increments,
  ab_so_far increments, inning advances -- report these separately, they are not the same event).
  For each event at time T, measure `mip` and `p_t4` at T and at T+1, T+2, T+3, T+4 cycles
  (~60/120/180/240s). Report the mean and distribution of `mip` movement per horizon, split by
  event type and by direction of the model's implied update.
  *** State the resolution limit in the results, prominently: this instrument measures lag at the
  ~60s cadence the bot itself evaluates on. If the market updates in 10 seconds, this test reports
  "already updated by the next sample" -- which is itself decisive, because a lag the bot cannot
  observe at its own cycle rate is a lag the bot cannot trade. Do not present that as a null. ***

DELIVERABLE 3 -- THE SHARP TEST: does our own edge signal predict the market's NEXT MOVE?
  This is the cleanest formulation of the thesis and it requires no outcomes at all.
  If the market lags and the model is ahead of it, then `gross_edge` at time T (= p_t4 - mip)
  should PREDICT the subsequent movement of `mip` from T to T+k. Regress (or bin) forward
  `delta_mip(T to T+k)` on `gross_edge(T)`, for k = 1..4 cycles. Report slope, se, and clustering by game
  and by ticker -- rows within a ticker are not independent and must not be treated as such.
  **Both confounds must be addressed explicitly, not mentioned and dropped:**
   (a) MEAN REVERSION. A large `gross_edge` may be a transient `mip` dislocation that simply
       reverts, which looks like "market moves toward model" with zero model skill. Distinguish
       "mip converges toward p_t4" from "mip reverts toward its own trailing mean" -- run both and
       report both slopes. If reversion explains it, say so plainly.
   (b) SHARED INFORMATION. `p_t4` and `mip` are both functions of overlapping public state, so
       correlation is expected. The thesis needs `gross_edge` to predict mip's FORWARD move, not
       merely to co-move. Say which one your statistic actually measures.

DELIVERABLE 4 -- SEGMENT IT, BECAUSE "T4" IS NOT ONE THING.
  Report the D3 result split by inning bucket, by `ab_remaining`, by price stratum (`mip` band),
  and by threshold. The thesis may hold in some regimes and not others -- that is a more useful
  answer than a single pooled number, and it is directly actionable for band design.

DELIVERABLE 5 -- WRITE IT UP AS EVIDENCE, AND STATE WHAT IT DOES NOT ESTABLISH.
  `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`. Include: the pre-registration, every statistic with
  n / se / clustering unit, the resolution-limit caveat from D2, both confound results from D3, the
  segmentation, and an explicit list of what was NOT checked. A supported thesis here still does
  not establish that the lag is large enough to clear costs -- 32.1 measured that 71.5% of the 765
  approvals flip to rejected at median spread. Name that tension; do not resolve it.

DO NOT: use the stale local cycle-log mirror as the data source. Pull fresh from the VPS.
DO NOT: touch any portfolio/ledger file, or use settled outcomes -- this test needs none, and the
  ledgers are under audit by 33.2 this wave.
DO NOT: change kelly_fraction, a cell status, a band definition, or any constant.
DO NOT: recommend retiring or promoting T4 or any sub-band on this result. Report the measurement.
DO NOT: restart a service, submit an order, or modify a price-capture window.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 33.2 owns them.
DO NOT: touch governance tooling, hooks, or the operator console -- 33.3 owns those.

SCOPE FENCE: one new analysis module under `scripts/`, its own `exp_output/` dir, a results summary
under `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`, and read-only pulls from the VPS.

REPORT BACK: the pre-registration as pushed; fresh-pull row count, date span and re-derived
state-change rate; D2's per-horizon mip movement by event type with the resolution caveat stated;
D3's forward-prediction slopes WITH both confound results; the D4 segmentation; and your verdict
against the pre-registered labels -- plus an explicit list of what this does not establish.
```

---

# 33.2 — IS THE 765 REAL? · LEDGER INTEGRITY · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "ledger-integrity-audit"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md AND DECISION_LOG.md THIS WAVE. ***

TIER: STANDARD.

ONE DELIVERABLE, stated plainly: **establish whether recorded positions represent real trades.**

Two independent HIGH findings now say the ledger misrepresents reality:
  GG-295 -- 42 NFL rows' thresholds were written by an unidentified actor, no commit anywhere in
    repo history, falsely attributed to T-562.
  GG-297 -- 139 of 140 T4M-PROJ positions marked OPEN (all dated 2026-09-22) are `canceled` /
    zero-fill at Kalshi. Only 1 carries a genuine fill.
And T4M-PROJ's 765-row epoch-12 clean cohort is **the only scorable cohort in the project.** Every
calibration figure the project has -- including T-565's reproduced model-vs-market result -- is
computed from it. T-565 reproduced that result by re-reading the same ledger, which cannot detect
this class of problem. **If the 765 contains phantoms, the project's one real finding is unsound.**

DELIVERABLE 1 -- APPLY GG-297'S TEST TO THE COHORT THAT MATTERS.
  GG-297 was found on 2026-09-22 open positions. Run the same check against all 765 epoch-12
  T4M-PROJ closed rows: for each, what does Kalshi's own order/fill record say actually happened?
  Report: confirmed filled, confirmed canceled/zero-fill, and NOT RETRIEVABLE as three separate
  counts -- never collapse "cannot verify" into "verified." If Kalshi's retention window does not
  reach back to 2026-07-31..08-13, say so explicitly and report exactly how far back it does reach;
  that boundary is itself the finding and must be stated, not worked around.
  Pass `authenticated=True` on every portfolio/order read -- `_get()` defaults to
  `authenticated=False`, which resolves to PRODUCTION regardless of BOT_ENV (T-556, unfixed).

DELIVERABLE 2 -- IF PHANTOMS EXIST IN THE 765, SIZE THE DAMAGE. DO NOT REPAIR ANYTHING.
  How many, on which game-dates, and what happens to T-565's headline figures when they are
  excluded -- Brier, ECE, market Brier, the paired diff, and the day-clustered t.
  Recompute using T-565's committed script (`scripts/t565_calibration_model_vs_market.py`) and its
  pre-registered construction, unchanged, so the before/after is comparable.
  **Report the delta. Do not edit the ledger, do not exclude rows from the live cohort, do not
  restate the clean_n.** GG-228 applies: no repair of a derived file before provenance is settled,
  and the repair decision is the operator's.

DELIVERABLE 3 -- NFL: WHICH MODEL WROTE THE 20 SETTLED ROWS? This was ported from 31.2 and dropped.
  `run_t1_nfl_game_market.py::main(model=None)` defaults to `StubNFLForecastModel`
  (`PROVENANCE = "STUB ... NOT a trained model, GG-255"`). Nothing in `src/`, `scripts/` or
  `deploy/` passes `EXP027NFLForecastModel` into it; `web_dashboard.py` reads EXP-027's provenance
  string as a DISPLAY LABEL ONLY and never instantiates the model. There is no NFL cron entry, so
  every run was launched by hand and the model argument is not recoverable from the repo.
  Establish it from the rows themselves, the audit log, or the run history -- or state plainly that
  it is unrecoverable. **If it cannot be established, the 20 settled rows and the 22 still-open
  ones are QUARANTINED from G6 evidence, NFL calibration and any clean_n** -- record that as a
  standing constraint in the gap log, not as a one-session note.

DELIVERABLE 4 -- SAY WHAT THE PROJECT'S EVIDENCE BASE ACTUALLY IS, AS OF NOW.
  One table: every cohort the project might score (T4M-PROJ 765, NFL T1 20 settled / 22 open, T1
  MLB, T2, NBA), its verified/unverified/quarantined status after D1-D3, and one line on why.
  This becomes the reference the calibration track cites instead of re-deriving it each wave.
  Update GG-295, GG-297 and GG-298 with what this session established. Register anything new.
  Clear the gap-candidate backlog handed over by 33.1 and 33.3.

DO NOT: repair, edit, backfill, exclude or re-stamp any ledger row. This block is diagnosis only.
DO NOT: mark GG-295 resolved -- actor provenance is not this block's scope and content provenance
  is not actor provenance.
DO NOT: restate `clean_n` anywhere, or change a cell status, kelly_fraction, or constant.
DO NOT: manufacture a position, row, cohort member or outcome; do not infer a fill from a local
  status field alone -- that is exactly the defect under audit.
DO NOT: restart a service, submit an order, or modify a price-capture window.
DO NOT: touch `scripts/` analysis modules or `exp_output/` belonging to 33.1, or governance tooling
  belonging to 33.3.

SCOPE FENCE: read-only ledger and Kalshi order-record access, T-565's existing script run
unchanged, a results summary, GOVERNANCE_GAP_LOG.md, DECISION_LOG.md.
Self-serialising close-out: re-read both logs fresh against HEAD immediately before writing --
33.1 and 33.3 are running concurrently.

REPORT BACK: the three-way count (filled / canceled / not-retrievable) across the 765 with Kalshi's
actual retention boundary stated; the recomputed T-565 figures with phantoms excluded and the
delta; the NFL provenance verdict or an explicit unrecoverable finding plus the quarantine record;
and the evidence-base table. State plainly whether the project's one real calibration finding
still stands.
```

---

# 33.3 — BUILD THE RETIREMENT MECHANISM · WARN-ONLY · SHORT

```
Run the CLAUDE.md session-start protocol in full. Paste outputs.
scripts/new_session_worktree.sh "retirement-mechanism"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 33.2 owns them. ***

TIER: SHORT. One deliverable: make retirement a machine step instead of a person remembering.

The diagnosis: every artifact in this project has an automated, enforced CREATION path and a
manual, remembered RETIREMENT path. `claim_session.sh` reserves IDs atomically with rebase-retry.
Gap registration is mandatory and checked. Creation is mechanical; retirement is memory. That
worked when the project was navigable and does not survive 12 departments and 138 gaps.

*** SHIP WARN-ONLY. DO NOT EXECUTE THE ARCHIVE MOVE THIS SESSION. *** 33.2 owns the gap log this
wave and is actively writing it. Build the tooling, prove it on a COPY, leave the live log
untouched. The first real run is a later wave's call.

DELIVERABLE 1 -- `scripts/retire_resolved_gaps.py`, and prove it on a copy only.
  Moves every live-log entry whose Status token is resolved-class, VERBATIM, into
  `GOVERNANCE_GAP_LOG_ARCHIVE.md`. Must handle the format drift that already exists: bare
  `RESOLVED`; dated variants (`RESOLVED (2026-09-11)`, `RESOLVED 2026-08-28 (T-502)`,
  `RESOLVED (2026-09-11, code+migration)`); `CLOSED-AS-ARTIFACT`; and at least one entry whose
  Status value runs to a full paragraph. Idempotent. Archive stays append-only; entries never
  return. `PARTIALLY RESOLVED` / `PARTIAL RESOLVE` / `LIKELY RESOLVED` / `IN PROGRESS` /
  `PLAN ACCEPTED` / `ACCEPTED UNCERTAINTY` / `WATCH ITEM` are STAY tokens -- they are NOT
  resolved-class and must not be moved. Get that list right; it is the whole safety margin.
  Run it against a COPY of the live log. Report what it WOULD move, entry by entry, and diff the
  copy to prove nothing but whole entries moved.

DELIVERABLE 2 -- the assertion that would have caught this on day one.
  Add to `.claude/hooks/governance_scan.sh`: the live log must contain ZERO resolved-class
  statuses. **Warn-only this session** -- print loudly, do not fail the scan, do not gate anything.
  Note in the script's own comments the criterion for promoting it to hard-fail later.

DELIVERABLE 3 -- teach the console to see retirement debt.
  `generate_operator_console.py`: add a resolved-class filter (`classify()` currently has NONE, so
  every live-log entry is bucketed blocked/broken/accruing and resolved entries render as
  "accruing" -- this is why it reported 133 open against a real 94 on 2026-09-22).
  Then add **Section 0 -- "Overdue for retirement"**, a roll-up across all twelve departments:
  unarchived resolved gaps; merged-but-undeleted branches; prunable worktrees; ADRs/APRs whose own
  file reads ACCEPTED but which have no `APPROVALS_REGISTER.md` row (ADR-0063 and APR-0035 are
  live examples); and session claims with no closure row. One number the operator reads weekly.

DELIVERABLE 4 -- close the two loops that already exist but only run one way.
  (a) `sweep_stray_branches.sh` already runs as `/session-end` Step 9 -- extend it to also delete
      merged remote AND local branches (`git branch -d`, NEVER `-D`; if `-d` refuses, the branch is
      not merged -- leave it and report) and to `git worktree prune`.
  (b) `check_register_parity.py` checks one direction only. Add the reverse: any ADR/APR file whose
      own status reads ACCEPTED must have a register row. This is why ADR-0063 is invisible to it.

DO NOT: run the archive move against the live `GOVERNANCE_GAP_LOG.md`. Copy only, this session.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md at all -- 33.2 owns them and is writing
  them concurrently. Record your own findings in your results file for 33.2 to register.
DO NOT: change any gap's status, close anything, or judge whether work is finished. This mechanism
  FILES things already marked done. Retirement is filing, never adjudication.
DO NOT: make the new assertion hard-fail, or gate any existing check on it, this session.
DO NOT: delete any UNMERGED branch (17 outstanding, operator-routed, Hard Rule 11).
DO NOT: touch ledgers, `exp_output/`, or 33.1's analysis modules.

SCOPE FENCE: `scripts/retire_resolved_gaps.py` (new), `scripts/generate_operator_console.py`,
`scripts/sweep_stray_branches.sh`, `scripts/check_register_parity.py`,
`.claude/hooks/governance_scan.sh`, their tests, and a short results note.

REPORT BACK: the entry-by-entry list the retire script WOULD move from a copy, with the stay-token
list you implemented; the copy diff proving only whole entries moved; the warn-only assertion's
output against the live log today; the console's new Section 0 rendered, with its twelve-department
roll-up counts; and the two extended loops with evidence each works.
```

---



---

## Wave 32 — CLOSED 2026-09-24 (all three landed; 32.3 correctly STOPPED before funding)

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


## WAVE 33 — CLOSED 2026-09-24 (archived verbatim)

Landed at `origin/main = b25fcb6`. 33.1 = T-569 (PR #147) · 33.2 = T-571 (PR #148) · 33.3 = T-570.
Outcomes are in the sequencing track in `ACTIVE_QUEUE.md`. Prompts below are the text as fired.

## ⬜ WAVE 33 — TEST THE THESIS, VERIFY THE COHORT

---

# 33.1 — THE T4 LATENCY THESIS · DOES THE MARKET ACTUALLY LAG? · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "t4-latency-thesis"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 33.2 owns them. ***
*** Record gap candidates in your own results file for 33.2 to register. ***

TIER: STANDARD. This is the most load-bearing untested claim in the project.

T4's entire thesis, stated in CLAUDE.md: "prediction markets are slow to incorporate live in-game
state... the market price lags behind the true updated probability... the market hasn't updated
yet, the bot has." Every T4 band, the 11-sub-band decomposition, and T4M-PROJ's ACTIVE status rest
on it. **It has never been measured.** This block measures it, and needs no bets, no fills, no
settlements and no ledger -- so its result survives whatever 33.2 finds about the ledger.

THE INSTRUMENT. `logs/t4_mlb_cycle_log.jsonl` on the VPS. Pull it fresh -- the local mirror
`logs/.vps_t4_mlb_cycle_log_cache.jsonl` stops at 2026-08-07 and must NOT be used as the source.
Every row carries, at a measured ~60s cadence (p10 56s / median 60s / p90 65s):
  ts, ticker, p_t4 (model prob), mip (market implied prob), vig, gross_edge, net_edge,
  h_so_far, ab_so_far, ab_remaining, inning, batting_slot, ba_l10, threshold, game_date
Both the model's probability AND the market's price AND the game state, side by side, per cycle.
In a 400k-row sample of the stale mirror, 9.8% of consecutive same-ticker pairs carried a game-
state change -- thousands of events. Re-derive that rate on the fresh pull; do not reuse it.

DELIVERABLE 1 -- PRE-REGISTER, PUSH, THEN COMPUTE. IMMUTABLE ONCE PUSHED.
  Write and push BEFORE any analysis: the exact event definition, the test statistics, the horizons,
  and what result you will call THESIS SUPPORTED / NOT SUPPORTED / INCONCLUSIVE. Include your
  handling of the two confounds named in D3. Do not relabel any of it afterwards.

DELIVERABLE 2 -- THE DIRECT TEST: does `mip` move AFTER a state change, or was it already there?
  Define a state-change event on a single ticker's time-ordered series (h_so_far increments,
  ab_so_far increments, inning advances -- report these separately, they are not the same event).
  For each event at time T, measure `mip` and `p_t4` at T and at T+1, T+2, T+3, T+4 cycles
  (~60/120/180/240s). Report the mean and distribution of `mip` movement per horizon, split by
  event type and by direction of the model's implied update.
  *** State the resolution limit in the results, prominently: this instrument measures lag at the
  ~60s cadence the bot itself evaluates on. If the market updates in 10 seconds, this test reports
  "already updated by the next sample" -- which is itself decisive, because a lag the bot cannot
  observe at its own cycle rate is a lag the bot cannot trade. Do not present that as a null. ***

DELIVERABLE 3 -- THE SHARP TEST: does our own edge signal predict the market's NEXT MOVE?
  This is the cleanest formulation of the thesis and it requires no outcomes at all.
  If the market lags and the model is ahead of it, then `gross_edge` at time T (= p_t4 - mip)
  should PREDICT the subsequent movement of `mip` from T to T+k. Regress (or bin) forward
  `delta_mip(T to T+k)` on `gross_edge(T)`, for k = 1..4 cycles. Report slope, se, and clustering by game
  and by ticker -- rows within a ticker are not independent and must not be treated as such.
  **Both confounds must be addressed explicitly, not mentioned and dropped:**
   (a) MEAN REVERSION. A large `gross_edge` may be a transient `mip` dislocation that simply
       reverts, which looks like "market moves toward model" with zero model skill. Distinguish
       "mip converges toward p_t4" from "mip reverts toward its own trailing mean" -- run both and
       report both slopes. If reversion explains it, say so plainly.
   (b) SHARED INFORMATION. `p_t4` and `mip` are both functions of overlapping public state, so
       correlation is expected. The thesis needs `gross_edge` to predict mip's FORWARD move, not
       merely to co-move. Say which one your statistic actually measures.

DELIVERABLE 4 -- SEGMENT IT, BECAUSE "T4" IS NOT ONE THING.
  Report the D3 result split by inning bucket, by `ab_remaining`, by price stratum (`mip` band),
  and by threshold. The thesis may hold in some regimes and not others -- that is a more useful
  answer than a single pooled number, and it is directly actionable for band design.

DELIVERABLE 5 -- WRITE IT UP AS EVIDENCE, AND STATE WHAT IT DOES NOT ESTABLISH.
  `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`. Include: the pre-registration, every statistic with
  n / se / clustering unit, the resolution-limit caveat from D2, both confound results from D3, the
  segmentation, and an explicit list of what was NOT checked. A supported thesis here still does
  not establish that the lag is large enough to clear costs -- 32.1 measured that 71.5% of the 765
  approvals flip to rejected at median spread. Name that tension; do not resolve it.

DO NOT: use the stale local cycle-log mirror as the data source. Pull fresh from the VPS.
DO NOT: touch any portfolio/ledger file, or use settled outcomes -- this test needs none, and the
  ledgers are under audit by 33.2 this wave.
DO NOT: change kelly_fraction, a cell status, a band definition, or any constant.
DO NOT: recommend retiring or promoting T4 or any sub-band on this result. Report the measurement.
DO NOT: restart a service, submit an order, or modify a price-capture window.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md -- 33.2 owns them.
DO NOT: touch governance tooling, hooks, or the operator console -- 33.3 owns those.

SCOPE FENCE: one new analysis module under `scripts/`, its own `exp_output/` dir, a results summary
under `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`, and read-only pulls from the VPS.

REPORT BACK: the pre-registration as pushed; fresh-pull row count, date span and re-derived
state-change rate; D2's per-horizon mip movement by event type with the resolution caveat stated;
D3's forward-prediction slopes WITH both confound results; the D4 segmentation; and your verdict
against the pre-registered labels -- plus an explicit list of what this does not establish.
```

---

# 33.2 — IS THE 765 REAL? · LEDGER INTEGRITY · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "ledger-integrity-audit"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU OWN GOVERNANCE_GAP_LOG.md AND DECISION_LOG.md THIS WAVE. ***

TIER: STANDARD.

ONE DELIVERABLE, stated plainly: **establish whether recorded positions represent real trades.**

Two independent HIGH findings now say the ledger misrepresents reality:
  GG-295 -- 42 NFL rows' thresholds were written by an unidentified actor, no commit anywhere in
    repo history, falsely attributed to T-562.
  GG-297 -- 139 of 140 T4M-PROJ positions marked OPEN (all dated 2026-09-22) are `canceled` /
    zero-fill at Kalshi. Only 1 carries a genuine fill.
And T4M-PROJ's 765-row epoch-12 clean cohort is **the only scorable cohort in the project.** Every
calibration figure the project has -- including T-565's reproduced model-vs-market result -- is
computed from it. T-565 reproduced that result by re-reading the same ledger, which cannot detect
this class of problem. **If the 765 contains phantoms, the project's one real finding is unsound.**

DELIVERABLE 1 -- APPLY GG-297'S TEST TO THE COHORT THAT MATTERS.
  GG-297 was found on 2026-09-22 open positions. Run the same check against all 765 epoch-12
  T4M-PROJ closed rows: for each, what does Kalshi's own order/fill record say actually happened?
  Report: confirmed filled, confirmed canceled/zero-fill, and NOT RETRIEVABLE as three separate
  counts -- never collapse "cannot verify" into "verified." If Kalshi's retention window does not
  reach back to 2026-07-31..08-13, say so explicitly and report exactly how far back it does reach;
  that boundary is itself the finding and must be stated, not worked around.
  Pass `authenticated=True` on every portfolio/order read -- `_get()` defaults to
  `authenticated=False`, which resolves to PRODUCTION regardless of BOT_ENV (T-556, unfixed).

DELIVERABLE 2 -- IF PHANTOMS EXIST IN THE 765, SIZE THE DAMAGE. DO NOT REPAIR ANYTHING.
  How many, on which game-dates, and what happens to T-565's headline figures when they are
  excluded -- Brier, ECE, market Brier, the paired diff, and the day-clustered t.
  Recompute using T-565's committed script (`scripts/t565_calibration_model_vs_market.py`) and its
  pre-registered construction, unchanged, so the before/after is comparable.
  **Report the delta. Do not edit the ledger, do not exclude rows from the live cohort, do not
  restate the clean_n.** GG-228 applies: no repair of a derived file before provenance is settled,
  and the repair decision is the operator's.

DELIVERABLE 3 -- NFL: WHICH MODEL WROTE THE 20 SETTLED ROWS? This was ported from 31.2 and dropped.
  `run_t1_nfl_game_market.py::main(model=None)` defaults to `StubNFLForecastModel`
  (`PROVENANCE = "STUB ... NOT a trained model, GG-255"`). Nothing in `src/`, `scripts/` or
  `deploy/` passes `EXP027NFLForecastModel` into it; `web_dashboard.py` reads EXP-027's provenance
  string as a DISPLAY LABEL ONLY and never instantiates the model. There is no NFL cron entry, so
  every run was launched by hand and the model argument is not recoverable from the repo.
  Establish it from the rows themselves, the audit log, or the run history -- or state plainly that
  it is unrecoverable. **If it cannot be established, the 20 settled rows and the 22 still-open
  ones are QUARANTINED from G6 evidence, NFL calibration and any clean_n** -- record that as a
  standing constraint in the gap log, not as a one-session note.

DELIVERABLE 4 -- SAY WHAT THE PROJECT'S EVIDENCE BASE ACTUALLY IS, AS OF NOW.
  One table: every cohort the project might score (T4M-PROJ 765, NFL T1 20 settled / 22 open, T1
  MLB, T2, NBA), its verified/unverified/quarantined status after D1-D3, and one line on why.
  This becomes the reference the calibration track cites instead of re-deriving it each wave.
  Update GG-295, GG-297 and GG-298 with what this session established. Register anything new.
  Clear the gap-candidate backlog handed over by 33.1 and 33.3.

DO NOT: repair, edit, backfill, exclude or re-stamp any ledger row. This block is diagnosis only.
DO NOT: mark GG-295 resolved -- actor provenance is not this block's scope and content provenance
  is not actor provenance.
DO NOT: restate `clean_n` anywhere, or change a cell status, kelly_fraction, or constant.
DO NOT: manufacture a position, row, cohort member or outcome; do not infer a fill from a local
  status field alone -- that is exactly the defect under audit.
DO NOT: restart a service, submit an order, or modify a price-capture window.
DO NOT: touch `scripts/` analysis modules or `exp_output/` belonging to 33.1, or governance tooling
  belonging to 33.3.

SCOPE FENCE: read-only ledger and Kalshi order-record access, T-565's existing script run
unchanged, a results summary, GOVERNANCE_GAP_LOG.md, DECISION_LOG.md.
Self-serialising close-out: re-read both logs fresh against HEAD immediately before writing --
33.1 and 33.3 are running concurrently.

REPORT BACK: the three-way count (filled / canceled / not-retrievable) across the 765 with Kalshi's
actual retention boundary stated; the recomputed T-565 figures with phantoms excluded and the
delta; the NFL provenance verdict or an explicit unrecoverable finding plus the quarantine record;
and the evidence-base table. State plainly whether the project's one real calibration finding
still stands.
```

---

# 33.3 — BUILD THE RETIREMENT MECHANISM · WARN-ONLY · SHORT

```
Run the CLAUDE.md session-start protocol in full. Paste outputs.
scripts/new_session_worktree.sh "retirement-mechanism"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***
*** YOU DO NOT OWN GOVERNANCE_GAP_LOG.md OR DECISION_LOG.md. 33.2 owns them. ***

TIER: SHORT. One deliverable: make retirement a machine step instead of a person remembering.

The diagnosis: every artifact in this project has an automated, enforced CREATION path and a
manual, remembered RETIREMENT path. `claim_session.sh` reserves IDs atomically with rebase-retry.
Gap registration is mandatory and checked. Creation is mechanical; retirement is memory. That
worked when the project was navigable and does not survive 12 departments and 138 gaps.

*** SHIP WARN-ONLY. DO NOT EXECUTE THE ARCHIVE MOVE THIS SESSION. *** 33.2 owns the gap log this
wave and is actively writing it. Build the tooling, prove it on a COPY, leave the live log
untouched. The first real run is a later wave's call.

DELIVERABLE 1 -- `scripts/retire_resolved_gaps.py`, and prove it on a copy only.
  Moves every live-log entry whose Status token is resolved-class, VERBATIM, into
  `GOVERNANCE_GAP_LOG_ARCHIVE.md`. Must handle the format drift that already exists: bare
  `RESOLVED`; dated variants (`RESOLVED (2026-09-11)`, `RESOLVED 2026-08-28 (T-502)`,
  `RESOLVED (2026-09-11, code+migration)`); `CLOSED-AS-ARTIFACT`; and at least one entry whose
  Status value runs to a full paragraph. Idempotent. Archive stays append-only; entries never
  return. `PARTIALLY RESOLVED` / `PARTIAL RESOLVE` / `LIKELY RESOLVED` / `IN PROGRESS` /
  `PLAN ACCEPTED` / `ACCEPTED UNCERTAINTY` / `WATCH ITEM` are STAY tokens -- they are NOT
  resolved-class and must not be moved. Get that list right; it is the whole safety margin.
  Run it against a COPY of the live log. Report what it WOULD move, entry by entry, and diff the
  copy to prove nothing but whole entries moved.

DELIVERABLE 2 -- the assertion that would have caught this on day one.
  Add to `.claude/hooks/governance_scan.sh`: the live log must contain ZERO resolved-class
  statuses. **Warn-only this session** -- print loudly, do not fail the scan, do not gate anything.
  Note in the script's own comments the criterion for promoting it to hard-fail later.

DELIVERABLE 3 -- teach the console to see retirement debt.
  `generate_operator_console.py`: add a resolved-class filter (`classify()` currently has NONE, so
  every live-log entry is bucketed blocked/broken/accruing and resolved entries render as
  "accruing" -- this is why it reported 133 open against a real 94 on 2026-09-22).
  Then add **Section 0 -- "Overdue for retirement"**, a roll-up across all twelve departments:
  unarchived resolved gaps; merged-but-undeleted branches; prunable worktrees; ADRs/APRs whose own
  file reads ACCEPTED but which have no `APPROVALS_REGISTER.md` row (ADR-0063 and APR-0035 are
  live examples); and session claims with no closure row. One number the operator reads weekly.

DELIVERABLE 4 -- close the two loops that already exist but only run one way.
  (a) `sweep_stray_branches.sh` already runs as `/session-end` Step 9 -- extend it to also delete
      merged remote AND local branches (`git branch -d`, NEVER `-D`; if `-d` refuses, the branch is
      not merged -- leave it and report) and to `git worktree prune`.
  (b) `check_register_parity.py` checks one direction only. Add the reverse: any ADR/APR file whose
      own status reads ACCEPTED must have a register row. This is why ADR-0063 is invisible to it.

DO NOT: run the archive move against the live `GOVERNANCE_GAP_LOG.md`. Copy only, this session.
DO NOT: write GOVERNANCE_GAP_LOG.md or DECISION_LOG.md at all -- 33.2 owns them and is writing
  them concurrently. Record your own findings in your results file for 33.2 to register.
DO NOT: change any gap's status, close anything, or judge whether work is finished. This mechanism
  FILES things already marked done. Retirement is filing, never adjudication.
DO NOT: make the new assertion hard-fail, or gate any existing check on it, this session.
DO NOT: delete any UNMERGED branch (17 outstanding, operator-routed, Hard Rule 11).
DO NOT: touch ledgers, `exp_output/`, or 33.1's analysis modules.

SCOPE FENCE: `scripts/retire_resolved_gaps.py` (new), `scripts/generate_operator_console.py`,
`scripts/sweep_stray_branches.sh`, `scripts/check_register_parity.py`,
`.claude/hooks/governance_scan.sh`, their tests, and a short results note.

REPORT BACK: the entry-by-entry list the retire script WOULD move from a copy, with the stay-token
list you implemented; the copy diff proving only whole entries moved; the warn-only assertion's
output against the live log today; the console's new Section 0 rendered, with its twelve-department
roll-up counts; and the two extended loops with evidence each works.
```

---

## THE RETIREMENT MECHANISM — spec (now FIRING as block 33.3)

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

---


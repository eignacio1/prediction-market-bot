# Active queue — the only prompt file to read

**Verified against:** `origin/main = e66c5cd` (2026-09-07) — *may be stale; run `git fetch origin` before trusting any "not landed" call in this file.*
**Live state:** 92 cells · 18 execution bands · 5 sizing tiers · GG-252 CLOSED · GG-253 PARTIAL · GG-254/255/256/257 OPEN · GG-203 PARTIALLY RESOLVED
**IDs:** do not pre-assign. Claim at run time (GG-236). Gap-log entry is the first pushed commit.
**Clock:** NFL Week 1 kicks off 2026-09-09.

---

## THE REFRAME THAT SETS THIS WAVE'S PRIORITY

**Capture is already safe. That is the only thing that was ever on a clock.**

Verified this session by direct read: `scripts/archive_market_prices.py` calls `client._get("/markets", ...)` and archives **raw payload dicts**. It never touches `_parse_market()` or `PlayerMarket`. The GG-252 parser bug therefore **never affected price capture** — the archiver has recorded all four NFL series at full fidelity since T-521 (18,194 KXNFL rows). The parser fix mattered for *trading*, not for *capturing*.

Per GG-156 captured price data is un-backfillable and everything else is not. A model built in Week 3 trains fine on Weeks 1–2 data; a Week 1 that was never captured is gone permanently.

So: **21.1 is the only block in this wave with a real deadline.** Everything else is normal-pace build work that loses nothing by landing in Week 2. Do not trade correctness for speed on the firing path to hit a date the firing path cannot hit.

---

## Read this first (standing)

- Fire one wave at a time. Three concurrent maximum, disjoint file surfaces.
- **Deliverable 0 in every block: land any un-landed predecessor.**
- **Push after each deliverable, not at close-out.** Budget the close-out separately.
- Verify a code fix by importing and calling the real function. Never re-implement its logic in a test harness.
- Register-and-stop on any gap outside scope (Hard Rule 11). Do not fix it incidentally.
- If a permission control refuses you, report the exact command and the exact refusal text, then hand back. Do not route around it.

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10–19 | ✅ CLOSED | see history |
| **20** | ✅ **CLOSED** | 20.2 landed; 20.1 + 20.3 built and pushed, **not merged** |
| **21** | ⬜ **21.0–21.3 CLOSED · 21.4 PENDING** | 21.2 built but unlanded; depth capture approved 09-09 |
| 22 | 🔒 | verification sweep + kill switch (needs ADR-0063 signed) |

### ✅ WAVE 20 — CLOSED

| # | Result |
|---|---|
| 20.1 | **BUILT, NOT MERGED** — `session/20260907T234611Z-nfl-game-market-settlement`, 6 commits, 1,265 lines: `c5_execution/game_market_settlement.py`, `c1_signal_ingestion/nfl_espn_results.py`, `scripts/apply_resolved_nfl_game_markets.py`, 606 lines of tests. Confirmed the reframe — no new outcome model was required. Registered **GG-257**: Kalshi settles a tied NFL moneyline as a $0.50/$0.50 split, which `settle_position()`'s boolean `>=` cannot express; the resolver **refuses** the tie via `check_settlement_ambiguity()` rather than guessing. Correct call. |
| 20.2 | ✅ **LANDED** (`5699ae3`) — new `GameMarket` dataclass (a sibling, not a bent `PlayerMarket`); `_parse_market()` split into a dispatcher; threshold read from the payload's `floor_strike`, **not** reconstructed from the ticker suffix (team codes are variable-length: `KC`/`SF`/`NYG`/`LAR`). Live-verified: `KXNFLGAME` 64/64 (was 0), `KXNFLSPREAD` 404/404 (was 0), `KXNFLTEAMTOTAL` 55/55 (was 0), `KXNFLTOTAL` 304/304 unchanged, **`KXMLBHIT` 286/286 before and after — zero prop regression.** 59/59 tests pass. New `fetch_game_markets()`. |
| 20.3 | **BUILT, NOT MERGED** — `session/20260907T234557Z-nfl-c1-ingestion`, 4 commits, 1,229 lines: `c1_signal_ingestion/nfl_ingestion.py`, `nfl_team_stats_store.py`, data contracts, 517 lines of tests. GG-253 → PARTIALLY RESOLVED (C1 built, C2 wiring open). |

### ⬜ WAVE 21 — LAND · PROTECT CAPTURE · WIRE

**Fire 21.0 and 21.1 now, concurrently — disjoint surfaces. 21.2 and 21.3 only after 21.0 lands.**

| # | Block | Tier | Why |
|---|---|---|---|
| 21.0 | Land the two Wave-20 branches | MICRO | 2,494 lines of tested work off main. Everything below depends on it. |
| 21.1 | Pre-kickoff capture fidelity audit | SHORT | **Only time-irreversible item. Must finish before kickoff.** |
| 21.2 | GG-255 — the firing path | STANDARD | Nine T1 game-market cells exist; one importer, an audit tool. |
| 21.3 | EXP-026 — HYP-011 moneyline LR backtest | STANDARD | Never run. Unblocked by 20.3's C1 module. |

---

# 21.0 — LAND WAVE 20 · MICRO · FIRE FIRST, ALONE

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "land-wave20-nfl-settlement-and-c1"
Claim your own IDs at run time (GG-236) -- re-derive the live max across GOVERNANCE_GAP_LOG.md, its
archive, AND `git log --all`; claim_session.sh alone cannot see unlanded branches.
Note GG-256: two sessions claimed T-526 one second apart on 09-07. Verify your T- number is unique
across `git log --all` before you push it.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: MICRO. You are landing already-built, already-tested work. **BUILD NOTHING NEW.**

*** GATE *** `git fetch origin` FIRST. Then confirm both of these branches still exist on origin:
    session/20260907T234611Z-nfl-game-market-settlement   (T-527, 6 commits, ~1265 lines)
    session/20260907T234557Z-nfl-c1-ingestion             (T-526/GG-253, 4 commits, ~1229 lines)
  If either is missing, STOP and report -- do not reconstruct it.
  Print `git log --oneline origin/main..origin/<branch>` for each and paste it.

This is the eleventh-plus recurrence of the GG-186 pattern (complete work that never reached main).
Landing IS the deliverable. Do not treat it as a close-out step.

DELIVERABLE 1 -- LAND THE C1 BRANCH FIRST (smaller surface, no dependency on the other).
  Merge session/20260907T234557Z-nfl-c1-ingestion into main. Push. Then run the FULL test suite --
  not just tests/test_t526_nfl_c1.py. Record the pass/fail/skip line in DECISION_LOG.md.

DELIVERABLE 2 -- LAND THE SETTLEMENT BRANCH.
  Merge session/20260907T234611Z-nfl-game-market-settlement into main. Push. Full suite again.
  Record pass/fail/skip.

DELIVERABLE 3 -- RE-DISPOSE GG-254.
  GG-254's title currently reads "No moneyline/categorical-outcome settlement logic exists anywhere
  in src/, for any sport". **Once Deliverable 2 lands that sentence is factually false** --
  c5_execution/game_market_settlement.py exists. Re-dispose GG-254 accurately against what is now
  actually in the tree.
  **Do NOT close it if the wiring is still missing.** State precisely: what is built, what is wired,
  what is not. If the honest disposition is PARTIALLY RESOLVED, say that. Do not upgrade a build into
  a closure.

IF A MERGE CONFLICTS: resolve it, and say in the commit message exactly what you resolved and why.
IF A PERMISSION CONTROL REFUSES THE MERGE: report the exact command and the exact refusal text
  verbatim, confirm which deliverables did land, and hand back. **Do not attempt an alternate route.**
  Five waves have been lost to this; the diagnostic is worth more than the workaround.

DO NOT: force-push over anything. DO NOT: touch any kelly_fraction or sizing value, including T1.
DO NOT: settle any real position. DO NOT: modify deploy/cron.conf or the archiver.
DO NOT: add a cron entry for anything you land. DO NOT: wire anything live.

SCOPE FENCE: merge commits only, plus GOVERNANCE_GAP_LOG.md and DECISION_LOG.md.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate output verbatim (both branch logs); the resulting origin/main SHA; the two full
suite lines (pass/fail/skip, before and after each merge); your GG-254 re-disposition verbatim; and
whether both merges actually reached origin/main -- confirm with
`git log --oneline -5 origin/main` AFTER a fresh `git fetch`, not from your local view.
```

---

# 21.1 — PRE-KICKOFF CAPTURE FIDELITY AUDIT · SHORT · TIME-CRITICAL

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "nfl-week1-capture-fidelity-audit"
Claim your own IDs at run time (GG-236). Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: SHORT. **THIS BLOCK HAS A REAL DEADLINE: it must complete before 2026-09-09 kickoff.**
Per GG-156 price data is un-backfillable. Every other block in this wave can slip a week without loss.
This one cannot. If you are running short on budget, cut Deliverable 5 first, then 4. Never cut 1-3.

You are answering ONE question: **when Week 1 starts, will we capture everything we would want to
have captured?** You are NOT fixing the trading path. You are NOT wiring anything.

DELIVERABLE 1 -- CONFIRM THE CAPTURE PATH IS PARSER-INDEPENDENT.
  Read scripts/archive_market_prices.py. Establish BY DIRECT READ whether it archives raw payload
  dicts or routes through kalshi_client._parse_market(). Cite file and line.
  A prior read says raw, via `client._get("/markets", ...)` around line 142. **Verify it. Do not
  inherit it.** If it turns out capture DOES depend on the parser, that changes everything about this
  wave's priority -- STOP and report immediately with the line.

DELIVERABLE 2 -- ENUMERATE WHAT IS ACTUALLY BEING CAPTURED.
  Count rows per series in exp_output/PRICE_ARCHIVE for the last 7 days.
  **Report per-series counts, not a total.** A healthy total can hide a dead series.

DELIVERABLE 3 -- CHECK FOR SERIES WE ARE MISSING.
  Query Kalshi LIVE for every open series whose ticker starts KXNFL. Compare against the four in
  deploy/cron.conf (KXNFLGAME KXNFLSPREAD KXNFLTOTAL KXNFLTEAMTOTAL).
  **If a fifth NFL series exists and is not being captured, that is the finding.** Register it and
  report before doing anything else.

DELIVERABLE 4 -- CHECK WINDOW COVERAGE AGAINST THE REAL WEEK 1 SCHEDULE.
  Pull the ACTUAL Week 1 game times (Thu opener, Sun early / late / night, Mon). Do not assume the
  slate; fetch it. For each game confirm a cron window covers 6h before and 4h after kickoff.
  Report any game with a coverage hole, by kickoff time in UTC.
  T-521 added a Sunday window (5,25,45 17-23 * * 0) and a Thursday 0-3Z window. Verify both against
  the real slate rather than trusting the comment in the file.

DELIVERABLE 5 -- ASSESS DEPTH SAMPLING.
  cron.conf passes --depth-sample-per-family 2, sampling orderbook depth for 2 markets per family.
  Say plainly whether that is adequate for the NFL families given their live market counts
  (KXNFLGAME 64, KXNFLSPREAD 404, KXNFLTOTAL 304, KXNFLTEAMTOTAL 55) and state what is permanently
  lost if it is not. Recommend a number; do not silently change it under this deliverable.

DELIVER: a written finding at 04_EXECUTION/NFL_WEEK1_CAPTURE_FIDELITY_<YYYY-MM-DD>.md.
  **Lead with a one-line verdict.** Register a gap for every hole found.

CRON AUTHORIZATION -- NARROW, READ IT EXACTLY:
  You MAY edit deploy/cron.conf ONLY to close a capture hole you have DEMONSTRATED with evidence in
  Deliverable 3 or 4 -- an uncovered real kickoff time, or a live KXNFL series absent from the config.
  ADDITIVE ONLY. **Do not modify, re-time, or reorder any MLB line** -- MLB capture feeds T-488,
  T-494 and Phase 2 and is a standing DO NOT.
  Push any cron change as its OWN commit, separate from the audit document, so it can be reverted
  alone. State in that commit message which deliverable's evidence justifies it.
  A depth-sample change is NOT authorized under this block -- recommend it, do not make it.

DO NOT: touch the parser, the trading path, or any kelly_fraction. DO NOT: wire or schedule anything
new. DO NOT: settle any position. DO NOT: change --depth-sample-per-family.

SCOPE FENCE: the new audit document, deploy/cron.conf (additive NFL lines only, under the
authorization above), gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the one-line verdict; the parser-independence finding with file and line; per-series
7-day row counts; the live KXNFL series list vs the configured four; every Week 1 kickoff with its
window coverage status; your depth-sample recommendation with a number; and whether you changed
cron.conf -- if so, paste the diff.
```

---

# 21.2 — GG-255 · THE FIRING PATH · STANDARD · AFTER 21.0 LANDS

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "gg255-t1-game-market-run-script"
Claim your own IDs at run time (GG-236). Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

*** GATE *** `git fetch origin`, then confirm ON origin/main:
    src/prediction_market_bot/c5_execution/game_market_settlement.py    EXISTS
    src/prediction_market_bot/c1_signal_ingestion/nfl_ingestion.py      EXISTS
  Both land in 21.0. If either is absent: **STOP. Do not rebuild them -- they exist on
  origin/session/20260907T234611Z-nfl-game-market-settlement and
  origin/session/20260907T234557Z-nfl-c1-ingestion.** Report that 21.0 has not landed and hand back.

TIER: STANDARD.

CONTEXT -- GG-255: measurement_stake.py defines all nine ADR-0058 T1 game-market cells, and its only
importer codebase-wide is scripts/assert_ledger_invariants.py, an AUDIT TOOL. No run script and no
cron entry exists for any T1 game-market cell, NFL or MLB. The cells have existed unexercised the
entire time.

DELIVERABLE 1 -- READ BEFORE YOU WRITE.
  Read src/prediction_market_bot/c4_risk_engine/measurement_stake.py IN FULL. Confirm and QUOTE the
  lines for: the nine cells, T1_MEASUREMENT_STAKE_USD (expect 1.00), MAX_CONTRACTS (expect 10),
  MAX_HAIRCUT_PER_CONTRACT_USD (expect 0.10). If any differs from those values, STOP and report --
  do not proceed against an assumption.
  Then read scripts/run_t4_mlb_live.py as the shape precedent.

  *** ITS KNOWN DEFECT -- DO NOT REPRODUCE IT ***
  Per ADR-0060 SS6: run_t4_mlb_live.py treats a KILL_SWITCH approval IDENTICALLY to an ordinary
  REJECTED. T1 branches and self-halts; T4 does not. Verify that yourself in the source and quote the
  branch. **Your script MUST branch on KILL_SWITCH distinctly and self-halt.** State in your report
  which line of yours does it.

DELIVERABLE 2 -- BUILD THE T1 GAME-MARKET RUN SCRIPT. PAPER ONLY.
  Path: fetch game markets (kalshi_client.fetch_game_markets(), new in 20.2)
     -> C1/C2 features (nfl_ingestion.py)
     -> model  -> C4 risk  -> measurement stake  -> PAPER TRADE ONLY.
  If the NFL model layer does not exist yet (it is 21.3's output), build against a clearly-marked
  INJECTABLE model interface and test with a stub. **Say explicitly in your report that it ran against
  a stub and not a model.** Do not invent a model inline to make the path look complete.

DELIVERABLE 3 -- WIRE THE CELL-TIER KILL SWITCH.
  market_type_registry.py's resolve_kill_switch_state() and halt_cell() (~lines 875, 885) are built
  and read by ZERO pipelines. Wire them into this path. This is the cell tier of the five-tier sizing
  hierarchy (full book 0.60 -> band -> 11 T4 segments at 8 Kelly regimes -> cell -> per-bet).
  **This wires the READ side only.** Do not change any halt threshold, and do not halt anything.

DELIVERABLE 4 -- TESTS FOR THE REFUSAL PATHS SPECIFICALLY.
  Kill switch active. No model available. Market unparsed (GG-252's unparsed_count > 0).
  Ambiguous settlement -- an exact-tie moneyline must hit game_market_settlement.py's
  check_settlement_ambiguity() (~lines 206-215) and RAISE, per GG-257. A test that only proves the
  happy path is not a deliverable here.

DO NOT: submit a live order. PAPER ONLY -- and do not rely on GG-203 blocking submission as the
  safety; the fence is the fence.
DO NOT: add a cron entry. Build the script; scheduling is a separately authorized step.
DO NOT: touch any kelly_fraction or sizing value, including T1. ADR-0058 authorizes the measurement
  stake at 0.0 and authorizes NO sizing change.
DO NOT: promote any cell. DO NOT: modify settle_position() -- GG-257 is registered, not assigned here.
DO NOT: promote assert_ledger_invariants.py to --strict; alarm-only is a standing operator decision.
DO NOT: modify deploy/cron.conf or the archiver.

SCOPE FENCE: a new run script under scripts/, its tests, the kill-switch read-side wiring in the
execution path, gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate result (both file existence checks); the four quoted constants from
measurement_stake.py; the run_t4_mlb_live.py KILL_SWITCH branch you are NOT reproducing, quoted, plus
the line of yours that handles it correctly; whether you ran against a model or a stub; the four
refusal tests with their results; and the full suite line.
```

---

# 21.3 — EXP-026 · HYP-011 MONEYLINE LR BACKTEST · STANDARD · AFTER 21.0 LANDS

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "exp026-hyp011-nfl-moneyline-lr"
Claim your own IDs at run time (GG-236). Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

*** GATE *** `git fetch origin`, then confirm
    src/prediction_market_bot/c1_signal_ingestion/nfl_ingestion.py       EXISTS on origin/main
    src/prediction_market_bot/c1_signal_ingestion/nfl_team_stats_store.py EXISTS on origin/main
  Both land in 21.0. If absent: STOP, report that 21.0 has not landed, hand back. Do not rebuild them.

TIER: STANDARD. The HYP-011 moneyline logistic regression has NEVER been run. 20.3's C1 module is
what unblocks it.

DELIVERABLE 1 -- PRE-REGISTER, AND PUSH IT, BEFORE YOU RUN ANYTHING.
  Write into the experiment file, and push that commit BEFORE any model is fit:
    - the hypothesis, stated as a falsifiable claim
    - the exact feature set
    - the train/test split rule
    - the success threshold, chosen NOW
    - the n* calculation per APR-0024: n* = (z_a + z_b)^2 * sigma^2 / delta^2, one-sided alpha=.05,
      power=.95, k = 3.290^2 = 10.824. Show the arithmetic and the resulting n*.
  **The pushed pre-registration commit is Deliverable 1. If you fit a model before pushing it, the
  experiment is void -- say so and start over.**

DELIVERABLE 2 -- BUILD FEATURES from nfl_ingestion.py / nfl_team_stats_store.py: team offensive and
  defensive efficiency (rolling, recency-weighted), rest days, home/away. Strength-of-schedule if
  cheap; do not block on it.

DELIVERABLE 3 -- TRAIN AND TEST.
  Train on completed seasons, test strictly out-of-sample. **Never train on a game in the test set.**
  State your leakage check explicitly -- how you PROVED no test game influenced training, not that
  you intended it.

DELIVERABLE 4 -- REPORT CALIBRATION, NOT JUST ACCURACY.
  A model that is 65% accurate but badly calibrated is worthless for Kelly sizing: the edge estimate
  is the product, the pick is not. Report a calibration curve and Brier score alongside accuracy.
  **Baseline is the market's implied probability, i.e. the closing line. Beating a coin flip is not
  the bar.** Report performance against the closing line explicitly.

DELIVERABLE 5 -- STATE THE VERDICT AGAINST THE PRE-REGISTERED THRESHOLD, VERBATIM AS WRITTEN IN
  DELIVERABLE 1. If n < n*, say so and report the result as UNDERPOWERED. Do not stretch an
  underpowered result into a verdict either direction.

DO NOT: change a pre-registered parameter after seeing results. DO NOT: relabel a pre-registered
  verdict after seeing it. Both are standing rules and both have bitten this project.
DO NOT: recommend against NFL, or against any sport or market family, on the strength of this result.
  Operator doctrine 2026-08-21, reaffirmed 2026-08-27: which cells calibrate edge is discovered
  per-cell, never decided in advance. A negative result here is a result about THIS feature set on
  THIS cell -- nothing more. Say it that way.
DO NOT: wire the model into any live or paper execution path. DO NOT: touch any kelly_fraction.
DO NOT: place or settle any position.

SCOPE FENCE: the experiment file + its output under exp_output/, a feature-build script under
scripts/, tests, gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the pre-registration commit SHA and confirmation it was pushed BEFORE fitting; the n*
arithmetic and the actual n; your leakage check; accuracy, calibration curve, Brier score; performance
vs the closing line; and the verdict quoted against the pre-registered threshold. If underpowered,
lead with that.
```

---

---

# 21.4 — LAND 21.2 + ENABLE NFL DEPTH CAPTURE · SHORT · LAST BLOCK OF WAVE 21

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "land-t530-and-enable-nfl-depth"
Claim your own IDs at run time (GG-236) -- re-derive the live max across GOVERNANCE_GAP_LOG.md, its
archive, AND `git log --all`. Verify your T- number is unique across `git log --all` before pushing
it (GG-256: two sessions collided on T-526 on 09-07).
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: SHORT. TWO deliverables. **OPERATOR-APPROVED 2026-09-09 -- both are authorized.**

*** GATE *** `git fetch origin` FIRST. Print `git log --oneline -3 origin/main` and paste it.

DELIVERABLE 1 -- LAND T-530 (GG-255, the T1 NFL run script).
  Branch: session/20260909T002748Z-gg255-t1-game-market-run-script  (4 commits, ~611 lines:
  scripts/run_t1_nfl_game_market.py 393 lines + tests/test_run_t1_nfl_game_market.py 130 lines).
  Print `git log --oneline origin/main..origin/session/20260909T002748Z-gg255-t1-game-market-run-script`
  and paste it BEFORE merging. If the branch is gone, STOP and report -- do not rebuild it.
  Merge into main. Push. Run the FULL test suite and record pass/fail/skip in DECISION_LOG.md.
  This is the twelfth-plus GG-186 recurrence. Landing IS the deliverable.
  IF A PERMISSION CONTROL REFUSES: paste the exact command and exact refusal text, confirm what did
  land, hand back. **Do not attempt an alternate route.**

DELIVERABLE 2 -- CLOSE GG-259: ENABLE NFL ORDERBOOK-DEPTH CAPTURE.
  *** THE OPERATOR APPROVED THIS ON 2026-09-09. It reverses T-521's deliberate scope decision
  (deploy/cron.conf:405-412, "no depth sampling ... kept out deliberately to minimize added
  volume"). You are not overriding that comment on your own authority -- you are executing an
  operator decision. Update that comment block to say so, and cite this approval date. ***

  Add `--depth-sample-per-family 1` to all FIVE NFL price-archive cron lines
  (deploy/cron.conf, the 5 lines whose --series is `KXNFLGAME KXNFLSPREAD KXNFLTOTAL KXNFLTEAMTOTAL`:
  Sunday `5,25,45 17-23 * * 0`, and `5,25,45 0-3` on days 1, 2, 4, 5).

  **1, not MLB's 2.** Rationale to record: half the added request volume, most of the signal, and
  T4M-PROJ's live MLB reads outrank this archive per the Phase 0-C safety directive inherited in
  cron.conf:405-407. Do not raise it to 2.

  *** DO NOT TOUCH ANY MLB LINE. *** MLB capture feeds T-488, T-494 and Phase 2 and is a standing
  DO NOT. Prove you didn't: paste `git diff deploy/cron.conf` in full and confirm every changed
  line's --series list contains only KXNFL* series.

  VERIFY IT ACTUALLY WORKS -- do not ship the config change on inspection alone:
    a) Confirm the flag's semantics by direct read: archive_market_prices.py:217-220 (defaults to 0)
       and main() at ~:255 (only calls _sample_depth() when > 0). Quote both.
    b) Run the archiver ONCE by hand with the new flag against the four NFL series. Confirm depth
       rows are actually written and non-empty. Paste the row count and one sample row.
    c) Recompute the request-volume estimate against cron.conf:405-412's own arithmetic and state
       the new weekly figure and the new % on top of MLB's baseline.
    d) State the MLB pacing floor is unchanged (DEFAULT_PAUSE_S=0.30s) and that you changed nothing
       about it.
  Push the cron change as its OWN commit, separate from everything else, so it can be reverted alone.

  Then re-dispose GG-259 accurately. Close it only if depth rows are confirmed writing.

TIMING NOTE FOR YOUR REPORT: the Thursday opener is 2026-09-10T03:20:00Z. If you are running after
that, the opener's depth window is already gone and unrecoverable -- say so plainly. The Sunday slate
is the bulk of Week 1 and is what this change actually protects. Do not treat a missed Thursday as a
reason to skip or to rush.

DO NOT: change --depth-sample-per-family on any MLB line, or raise NFL's above 1.
DO NOT: re-time, reorder, or otherwise modify any MLB cron line.
DO NOT: add a cron entry for run_t1_nfl_game_market.py -- scheduling it is NOT authorized.
DO NOT: submit a live order, settle any position, or touch any kelly_fraction including T1.
DO NOT: promote any cell. DO NOT: promote assert_ledger_invariants.py to --strict.
DO NOT: modify settle_position() -- GG-257 is registered, not assigned here.

SCOPE FENCE: the T-530 merge, deploy/cron.conf (NFL lines + its comment block only),
gap-log + DECISION_LOG entries.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate output; the T-530 branch log before merge and the resulting origin/main SHA
after a FRESH fetch; the full suite line; the complete `git diff deploy/cron.conf`; the two quoted
archiver lines proving the flag's semantics; the hand-run depth row count plus one sample row; the
new weekly request estimate and % over MLB baseline; whether the Thursday opener window was missed;
and your GG-259 disposition.
```

## Needs your decision

| Item | What it is | Consequence if it keeps waiting |
|---|---|---|
| **GG-203** | 24+ days. Every Kalshi order submission fails, 1:1 with approvals. Operator-only: support ticket or demo-key regeneration. | Largest item on the board and not a code problem. Everything in Waves 21–22 can complete perfectly and still fire nothing. |
| **ADR-0063** | Five-tier kill-switch / Kelly alignment hierarchy. Drafted PROPOSED 2026-09-05, unsigned. | Gates 21.2's kill-switch write-side and all of Wave 22. |
| **GG-257** | Kalshi splits a tied NFL moneyline $0.50/$0.50; `settle_position()` can't express it. | LOW. Correctly refused today. Needs a decision only before a live NFL portfolio exists (~1 tie/season). |

---

## DO NOT — standing

- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Bypass or disable a permission control — report what refused you and hand back.
- Re-investigate GG-203 in-repo; the ruled-out list is exhaustive.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time the MLB price capture.
- Pre-assign T-/GG- numbers. Claim at run time.

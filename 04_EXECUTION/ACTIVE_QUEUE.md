# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates. Wave 44 is archived there.

**Verified against:** `origin/main = d8d5850` (2026-10-01). *This window cannot `git fetch` or push.*

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-328** · **T-603** · **ADR-0069** · **EXP-033** — ADR-0067 exists only on an unmerged branch |
| Live gap log | 138 entries · **119 OPEN** · header/status parity OK · no duplicate GG ids |
| Cells | 92 · **1 ACTIVE** (MLB hits × T4M-PROJ, MISFILED under C5) |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. |
| Price archive | ~2.125 M rows · 14 MLB/NFL families · 2026-08-01 → 10-01 |
| Queue record | **Waves 37–45 exist only as uncommitted edits in the shared tree.** 45.3 lands them. |
| NBA hold | **Expired.** Tabled until ~1 month before tip-off; 2026-27 opening night is **Oct 20**. |

---

## ⬛ WHAT WAVE 44 FOUND — READ THIS BEFORE THE BLOCKS

**The pre-registered stop condition fired.** EXP-032: no family's E crosses zero under any execution
policy the archive evidences. EXP-033: 0 of 24 multi-leg cells survive. The arc said the next decision
is venue or asset-class selection, not another model, feature or band. **The operator chose: survey the
rest of Kalshi first — the sports board beyond MLB/NFL, and a non-sports control arm.**

**Why the edge and the cost decay together.** H falls an order of magnitude as the start approaches
(KXMLBF7 20c → 1c; TEAMTOTAL 4c → 0.5c) — but B falls with it. At the cheap entry point the mispricing
has already converged. KXMLBHIT's NEAR (+.0042, CI spans zero) was the closest thing to a survivor.

**Three things the strategic window found on handover, all verified against tracked files:**

1. **Every E on record excludes fees.** EXP-031 and EXP-032 pre-registered it (EXP-032 pre-reg, line
   43). Under the in-repo ADR-0016 model, fee ≈ 0.07·p·(1−p) — about 1.6c at p = 0.65, roughly **4×
   KXMLBHIT's NEAR margin**. NEAR is not near. Fees strengthen the stop condition; they cannot weaken it.
2. **Kalshi documents unauthenticated historical endpoints** — historical markets, and candlesticks
   with yes_bid / yes_ask / price OHLC plus volume at 1-min / 1-hour / 1-day. The archive script's
   docstring (2026-08-01) says game-market history "CANNOT BE BACKFILLED." If the endpoint covers past
   seasons, the board survey reaches a verdict **this wave** with no cron line. If it doesn't, the
   survey needs forward capture and your schedule authorization. 45.1 and 45.2 each verify this first.
3. **The record has not landed.** origin/main's queue still shows Wave 37; the archive stops at 36;
   ADR-0067 is on no main; 32 branches read as unmerged (the carry-forward says 9 carry real work).

---

## ⬛ FIRE NOW — Wave 45, three blocks, concurrent

| Paste | Block | Tier | One-line purpose |
|---|---|---|---|
| 1st | **45.1** | LARGE | **Survey the rest of Kalshi's sports board, net of fee.** Prove the historical endpoint against the archive, then run the Wave 43/44 instrument on NHL, NBA, NCAAF, WNBA, soccer — whatever the venue lists. |
| 2nd | **45.2** | LARGE | **Non-sports control arm.** Same instrument on weather and economics series, plus the one test no sports family allows: is the market worse than a free public forecast? |
| 3rd | **45.3** | STANDARD | **Land the record, count the branches, find out what the dashboard is serving.** |

**Fire order does not matter.** Surfaces are disjoint:

- **45.1 owns** new `scripts/board_survey_sports*` + `tests/board_survey_sports*`, one new EXP id and
  its pre-registration / results / exp_output dir, one new raw-history store, **the docstring only** of
  `scripts/archive_market_prices.py`, **and `GOVERNANCE_GAP_LOG.md` / `DECISION_LOG.md`.**
- **45.2 owns** new `scripts/board_survey_nonsports*` + `tests/board_survey_nonsports*`, a different new
  EXP id and its pre-registration / results / exp_output dir, its own raw-history store. **No GGL /
  DECISION_LOG writes.**
- **45.3 owns** the shared main tree's sync, the four `04_EXECUTION/` record files (queue, archive,
  carry-forward, paste-in — landed as written), the named predecessor merges, one results summary, and
  read-only VPS probes. **No GGL / DECISION_LOG writes.**
- **Read-only to all three:** `market_efficiency_survey.py`, `execution_cost_surface.py`,
  `multileg_coherence.py`, `capture_settlements.py`, `exp_output/PRICE_ARCHIVE/`. Import, never edit.

**Exactly three fences. A fourth means something is wrong -- stop.**

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Each block carries its workstream to a measured verdict.** Operator directive 2026-09-30. Terminals are fresh and can take the load; stop only at a governance boundary, and name the boundary when you stop.
- **Deliverable 0 in every block: land any un-landed predecessor, and sync.** *This wave only:* 45.3 alone touches the shared main tree, because the uncommitted queue record lives there; 45.1 and 45.2 work from fresh worktrees off origin/main and do not pull in the shared tree.
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). 45.1 and 45.2 both claim an EXP id concurrently.
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file. *Wave 43 disproved one of its own briefs; that is the system working, not a failure.*
- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no approval in a block overrides it.
- **Pre-register before measuring, pushed as its own commit.** Gates sized before outcomes are seen, never edited after (GG-327).
- **Push after each deliverable.** Verify a fix by importing and calling the real function. **Benchmark the real thing.**
- **A merge is not a deployment, and a deployment is not an activation** (GG-279).
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10-43 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **44** | CLOSED — all three on origin/main `d8d5850` | **EXP-032: no E crosses zero under any evidenced policy** (H and B decay together). **EXP-033: 0/24 survive.** Settlement + depth writers built, proven, idempotent; 1 reconciliation discrepancy (timing). Cron DRAFTED, restart SKIPPED. **Stop condition FIRED.** |
| **45** | **FIRING** | Survey Kalshi beyond MLB/NFL, net of fee — sports and non-sports — and land the record. |

---

## Why this wave is shaped this way

**Every measurement the project has is about one corner of one venue.** Fourteen MLB/NFL families on
Kalshi, sixty late-season days, twenty-minute snapshots. Inside that corner the answer is now firm. Outside
it, nothing has been measured — and the instrument that produced the answer (B, null, the H surface,
B-at-entry, the placebo, the coherence tests) is family-agnostic. Pointing it at the rest of the venue
costs a capture writer, not a new venue adapter.

**45.1 moves down the efficiency gradient without leaving the venue.** Lower-attention sports carry the
same moneyline / spread / total mechanics the coverage target asks for, in markets the strategy's own
thesis says should be priced worse. NBA is back in scope on the operator's own trigger. Its first act is a
correctness gate: rebuild one MLB family from historical candles and reproduce the archive. If candles
cannot reproduce what we captured ourselves, nothing built on them counts.

**45.2 tests the founding claim, not just the venue.** The project calls itself a calibration engine
whose methodology transfers. Weather is where forecast calibration was invented, and it is the only
market class with a free, public, professionally calibrated probabilistic forecast to hold the market
against — with no model of ours involved. It is a deliberate, operator-approved step outside the sports
coverage target.

**45.3 makes the record safe.** Seven waves of prompts exist only as uncommitted edits in a working
tree that is 140 commits behind. One careless git operation erases them. It also settles a contradiction:
the carry-forward says the dashboard serves the old page; T-602 saw the process restart at 02:25Z with no
one recording why.

---

## WAVE 45 BLOCKS

---

# 45.1 -- SURVEY THE REST OF KALSHI'S SPORTS BOARD, NET OF FEE - LARGE

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "kalshi-sports-board-survey"
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).
Highest seen at queue-write time: GG-328, T-603, ADR-0069, EXP-033. Verify; do not assume.
45.2 claims an EXP id concurrently -- re-verify yours after any retry.
Gap-log entry as your FIRST pushed commit. You are the only block this wave that writes to
GOVERNANCE_GAP_LOG.md and DECISION_LOG.md.

YOU OWN, THIS WAVE, EXCLUSIVELY:
  new files under scripts/ and tests/ whose names begin board_survey_sports, one NEW EXP id (its
  pre-registration, exp_output/ directory and results summary), one new raw-history store (location
  stated in your report), GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, and the module DOCSTRING ONLY of
  scripts/archive_market_prices.py (see D7).
READ-ONLY (import, never edit): scripts/market_efficiency_survey.py,
  scripts/execution_cost_surface.py, scripts/multileg_coherence.py, scripts/capture_settlements.py,
  exp_output/PRICE_ARCHIVE/, every EXP-031/032/033 artifact, every pool and model file.
DO NOT pull, sync, stash or commit in the shared main tree. 45.3 owns it this wave.

WHY THIS BLOCK EXISTS -- verify every premise, do not assume it:
  Wave 44's pre-registered stop condition fired: on 14 Kalshi MLB/NFL families, 2026-08-01 to
  10-01, no family's E crosses zero under any evidenced execution policy (EXP-032) and 0 of 24
  multi-leg cells survive (EXP-033). The arc said the next decision is venue or asset-class
  selection. The operator chose to survey the rest of Kalshi first.
  Two facts make that cheap. Both are CLAIMS -- verify them in D1:
    1. Kalshi documents unauthenticated historical endpoints -- GET historical markets, and GET
       historical market candlesticks returning yes_bid / yes_ask / price OHLC plus volume and
       open_interest at period_interval 1, 60 or 1440 minutes, for markets "archived from the live
       data set" (docs.kalshi.com/api-reference/historical/). Lookback depth is NOT documented.
       scripts/archive_market_prices.py's docstring (2026-08-01) says game-market history "CANNOT
       BE BACKFILLED". One of these is wrong, or the endpoint postdates the docstring. Find out which.
    2. EXP-031 and EXP-032 EXCLUDED FEES in every policy (EXP-032 pre-registration, line 43). Every
       E on record is an upper bound. Under the in-repo ADR-0016 model, fee = 0.07*p*(1-p) per
       contract, about 1.6c at p=0.65 -- roughly 4x KXMLBHIT's NEAR margin (+.0042). This block
       scores E NET OF FEE as its primary statistic.
  The operator's NBA hold (04_EXECUTION/TODO_NEXT.md, 2026-07-01: tabled until ~1 month before
  tip-off) has expired: 2026-27 opening night is 2026-10-20. NBA markets are in scope for this
  READ-ONLY survey. Do not touch NBA C1/C2/C3 code, run_t4_live.py, t4_live_runner.py, GG-056 or
  ADR-0035 -- this block measures markets, not our pipeline.

DELIVERABLE 0 -- CONFIRM YOUR BASE. Paste origin/main SHA before and after. Confirm Wave 44's
  artifacts are on origin/main: scripts/execution_cost_surface.py, scripts/multileg_coherence.py,
  scripts/capture_settlements.py, and the EXP032 and EXP033 results summaries. Missing = stop.

DELIVERABLE 1 -- PROVE THE INSTRUMENT BEFORE YOU POINT IT ANYWHERE NEW.
  a) Endpoint reality: call the historical endpoints (and the live candlestick endpoint for settled
     markets not yet past the historical cutoff) for a sample of settled tickers across sports.
     Report: lookback depth actually returned per sport, which fields are populated, null and
     zero-volume candle behaviour, rate-limit headers, the historical cutoff timestamp. Paste raw
     responses for two tickers.
  b) THE CORRECTNESS GATE -- IT DECIDES WHETHER ANY LATER NUMBER COUNTS. Rebuild ONE MLB family
     already in the archive (KXMLBTEAMTOTAL -- densest coverage) from candles alone, over the
     archive's own window. Compare candle-derived bid/ask with archive snapshots matched on ticker
     and time (state the matching rule), and reproduce EXP-031's B and EXP-032's H surface for that
     family. Write the tolerance into your D3 pre-registration's gate section BEFORE running the
     comparison. If candles cannot reproduce the archive within tolerance, every candle-based
     number in this block is VOID: stop after D1, register the discrepancy, hand back.
  c) Fee: confirm ADR-0016's formula, rounding rule and any maker/taker distinction against Kalshi's
     published fee schedule. Cite source and date. If the venue's schedule differs from ADR-0016,
     use the venue's and register the divergence.

DELIVERABLE 2 -- INVENTORY THE BOARD. NO OUTCOME STATISTICS YET.
  Every Kalshi SPORTS series, excluding the 14 already surveyed, with settled markets reachable via
  D1's endpoints. Per series: sport, structure (binary / bracket / ladder / mutually exclusive set),
  settled-market count, date span, distinct events, whether a pre-start clock is recoverable
  (ticker-embedded start, event metadata, or a named external schedule) and the measured
  start-to-close duration distribution. Expect NHL game/spread/total, NBA regular season, NCAA
  football, WNBA, soccer (EPL/MLS/UCL) -- but the list is whatever the venue returns, not this
  sentence. Futures, awards and leaderboard series are inventoried and marked out of scope.
  Freeze the inventory as its own commit. Counts and metadata only, no outcomes.

DELIVERABLE 3 -- PRE-REGISTER. PUSH IT ALONE, BEFORE ANY OUTCOME STATISTIC.
  State in advance:
    - the cohort rule per family: series, settlement window, minimum events and markets to measure;
      below it the family is INSUFFICIENT, not "inconclusive but promising";
    - candle interval(s) and why; the snapshot definition (e.g. candle close bid/ask);
    - B and null exactly as EXP-031 defines them (import, do not re-implement);
    - the cost surface as EXP-032 defines it, plus FEE. Primary: E_net = B - null - H - fee.
      Fee-excluded E reported alongside, for comparability with EXP-031/032;
    - policies: (a) first-seen; (b) cheapest MEASURED cell, with B-AT-ENTRY re-checked at that cell
      (EXP-032's rule); (c) rest at mid, fills evidenced only by a later quote strictly through the
      order. Candles give interval OHLC, not ticks: say exactly what evidences a fill and what not;
    - THE CLOCK GATE PER FAMILY, sized from D2's measured start-to-close durations BEFORE outcomes
      are seen. GG-327 is why: EXP-032 applied one fixed [2.0, 4.5]h range to every family and lost
      four families to it. Do not repeat that, and do not edit a gate after seeing results;
    - multiplicity: Holm across every family tested, m stated;
    - the decision rule: CANDIDATE requires E_net > 0 under policy (b) with B earned at entry, game-
      cluster AND day-cluster CI lower bounds > 0, Holm-adjusted. No depth is captured for these
      series, so the strongest available label is CANDIDATE-PENDING-CAPACITY. Report traded volume
      at the entry cell as context only: volume is not depth and sizes nothing;
    - the drift test with backward placebo (EXP-029 / T-569 / EXP-032 convention), ratio reported.
  Frozen once pushed. Any amendment is a new commit labelled AMENDMENT, with its reason, made before
  the statistic it affects is computed.

DELIVERABLE 4 -- BACK-CAPTURE, READ-ONLY.
  A NEW writer (board_survey_sports*) that pulls historical markets, candles and settlement for the
  pre-registered cohort into a NEW store. Never write into exp_output/PRICE_ARCHIVE/ or any existing
  store. Provenance per row: source URL, retrieval UTC, upstream content hash, runtime commit sha.
  Idempotent and append-only: run it twice, prove the second run writes nothing new (hashes).
  Handle SCALAR settlements (T-602 found 631 in the MLB F-series); a join that treats result as
  yes/no mis-scores them. Pace requests (T-602 used 0.30s); halve the rate on any 429. The
  T4M-PROJ process shares the venue read budget during live MLB postseason games.
  Report total calls, bytes and wall time.

DELIVERABLE 5 -- MEASURE. ONE TABLE, EVERY FAMILY, SAME TREATMENT.
  Ranking table: every family, every policy, E_net and fee-excluded E, CIs, fill rates, day-
  fragility flags, clock-gate outcome, label. KXMLBHIT's EXP-032 row stays in as the reference,
  re-scored net of fee by the same rule. Per sport, the H(tau) shape. Drift with placebo ratio.
  Also run EXP-033's coherence tests (import multileg_coherence.py) on every complementary or
  nested structure these series carry, same toll and Holm rule.
  STATE PLAINLY: does any family reach CANDIDATE-PENDING-CAPACITY, and does any multi-leg cell
  survive? If neither, say so in one sentence. That is the answer, and the stop condition fires.

DELIVERABLE 6 -- RE-SCORE THE OLD FRONTIER NET OF FEE. ARITHMETIC ONLY.
  Subtract the D1(c) fee from EXP-031's and EXP-032's published E columns. This applies a NEW cost
  component to the old tables; it does not re-cut B, H or any pre-registered parameter, and it can
  only lower E. Present it beside the originals. Do not relabel either experiment's verdict.

DELIVERABLE 7 -- REGISTER, LOG, CORRECT.
  Register what this found, including: the backfill premise (if D1(a) shows history IS reachable,
  correct the docstring of scripts/archive_market_prices.py -- docstring only, no code, no capture
  window change); any candle-vs-archive discrepancy; every series excluded and why.
  If 45.2's or 45.3's GAPS FOUND lists are on origin/main before you close, register those too;
  otherwise leave them for Wave 46 and say so. One DECISION_LOG entry for the wave.
  Results summary line by line against the pre-registration, ending with one paragraph: is Kalshi's
  sports board beyond MLB/NFL efficient net of cost and fee -- scoped to exactly the series, seasons
  and cadence tested? Do not generalize past what was measured.

DO NOT:
  - Write into exp_output/PRICE_ARCHIVE/, edit any capture writer's code, or re-time a capture
    window. The archive_market_prices.py docstring is the only exception, and only per D7.
  - Edit market_efficiency_survey.py, execution_cost_surface.py or multileg_coherence.py.
  - Re-cut, re-bucket or re-window B or the null for MLB/NFL families. D6 adds fee; nothing else.
  - Change a pre-registered gate, policy, threshold or decision rule after seeing a result.
  - Promote anything past CANDIDATE-PENDING-CAPACITY. Volume is not depth.
  - Recommend against a sport, band or family on one finding; and do not assume unmeasured series
    behave like measured ones.
  - Build, fit or tune any forecasting model. This block measures the venue, not us.
  - Touch NBA pipeline code, any pool, any position, sizing or kelly_fraction.
  - Install or uncomment any cron entry. This block back-captures by hand and schedules nothing.
  - Pull, stash, reset, checkout or commit in the shared main tree.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

# 45.2 -- NON-SPORTS CONTROL ARM: IS ANY KALSHI BOOK WORSE THAN A FREE FORECAST - LARGE

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "kalshi-nonsports-control"
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).
Highest seen at queue-write time: GG-328, T-603, ADR-0069, EXP-033. Verify; do not assume.
45.1 claims an EXP id concurrently -- re-verify yours after any retry.

YOU OWN, THIS WAVE, EXCLUSIVELY:
  new files under scripts/ and tests/ whose names begin board_survey_nonsports, one NEW EXP id (its
  pre-registration, exp_output/ directory and results summary), one new raw-history store (location
  stated in your report).
READ-ONLY (import, never edit): scripts/market_efficiency_survey.py,
  scripts/execution_cost_surface.py, scripts/multileg_coherence.py, scripts/capture_settlements.py.
YOU DO NOT WRITE: GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 45.1 owns them. List findings under
  GAPS FOUND in your results summary.
DO NOT pull, sync, stash or commit in the shared main tree. 45.3 owns it this wave.

WHY THIS BLOCK EXISTS -- verify every premise, do not assume it:
  Wave 44's stop condition fired on Kalshi's MLB/NFL board (45.1 carries the record). On 2026-09-30
  the operator chose to run a NON-SPORTS CONTROL ARM alongside the sports survey. This is a
  deliberate, operator-approved step outside the sports coverage target
  (02_ARCHITECTURE_DESIGN/COVERAGE_TARGET_MATRIX.md). The reason: the project's founding claim is
  that it is a calibration engine whose methodology transfers. Weather is where forecast
  calibration was invented -- the Brier score was written for it -- and it offers what no sports
  family does: a free, public, professionally calibrated probabilistic forecast to hold the market
  against, with no model of ours involved. A book that settles daily against a public weather
  report is a natural place to look for mispricing. That is a hypothesis, not a finding.
  Premises shared with 45.1 -- verify them yourself: Kalshi's unauthenticated historical
  candlestick endpoints (docs.kalshi.com/api-reference/historical/); fees EXCLUDED from every E on
  record (EXP-032 pre-registration line 43; ADR-0016 model fee = 0.07*p*(1-p)). E_net is primary.

DELIVERABLE 0 -- CONFIRM YOUR BASE. Paste origin/main SHA before and after. Confirm
  scripts/market_efficiency_survey.py, scripts/execution_cost_surface.py and
  scripts/multileg_coherence.py exist on origin/main. Missing = stop and report.

DELIVERABLE 1 -- PROVE THE INSTRUMENT ON THESE SERIES.
  a) Endpoint reality for non-sports series: lookback actually returned, fields populated, null and
     zero-volume candles, rate-limit headers, historical cutoff. Paste raw responses for two tickers.
  b) YOUR OWN CORRECTNESS GATE (45.1 runs a separate one on MLB; you cannot wait for it). During
     your session, read live yes_bid / yes_ask for a sample of currently open non-sports markets at
     least 6 times, spaced >= 20 minutes apart; then pull the 1-minute candles covering those exact
     minutes and compare. Write the tolerance into your pre-registration BEFORE comparing. Fail =
     every candle-based number in this block is VOID: stop, report, hand back.
     If 45.1 reports a candle-vs-archive failure on origin/main before you close, mark every result
     in this block PROVISIONAL pending it.
  c) Fee: the same check as 45.1 D1(c) -- formula, rounding, maker/taker, cited source and date.

DELIVERABLE 2 -- INVENTORY. NO OUTCOME STATISTICS YET.
  Every Kalshi NON-SPORTS series with settled markets reachable via D1: weather (daily highs, lows,
  precipitation by city), economic releases (CPI, payrolls, jobless claims, Fed rate, GDP), and any
  other category the venue returns. Per series: category, structure (binary / bracket / mutually
  exclusive set), settled-market count, events, date span, the settlement source as Kalshi states
  it, typical open-to-close duration. Series with too few events are listed and labelled
  INSUFFICIENT under the D3 cohort rule -- never dropped silently.
  Freeze the inventory as its own commit. Counts and metadata only.

DELIVERABLE 3 -- PRE-REGISTER. PUSH IT ALONE, BEFORE ANY OUTCOME STATISTIC.
  Everything 45.1 D3 requires, adapted: cohort rule per family; candle interval(s); B and null as
  EXP-031 defines them (import); the cost surface as EXP-032 defines it, plus fee; E_net primary and
  fee-excluded E secondary; policies (a)/(b)/(c) with B-at-entry at (b) and an explicit
  fill-evidence rule for (c); Holm across every family tested, m stated;
  CANDIDATE-PENDING-CAPACITY as the strongest label (no depth captured); drift with backward
  placebo, ratio reported.
  THE CLOCK: these markets have no game start. Define the horizon per family as hours-to-close
  (for weather, also hours before the settling observation day), sized from D2's measured
  durations before any outcome is seen.
  THE PUBLIC-FORECAST BENCHMARK (weather only, D5c): name the forecast product and its archive; the
  issue time used relative to each market snapshot -- it must be issued BEFORE the snapshot, no
  look-ahead; the exact mapping from forecast to bracket probability; the scoring rule (Brier and
  log loss against settlement, city-day cluster CIs). The mapping is fixed here. If it needs a free
  parameter, fix it from documentation or from data strictly before the cohort window, and say which.
  Frozen once pushed. Amendments only before the statistic they affect, labelled AMENDMENT.

DELIVERABLE 4 -- BACK-CAPTURE, READ-ONLY.
  A NEW writer (board_survey_nonsports*) into a NEW store. Provenance per row: source URL,
  retrieval UTC, upstream content hash, runtime commit sha. Idempotent and append-only; run twice,
  hashes. Scalar settlements handled. Paced; halve on any 429; T4M-PROJ shares the venue read
  budget during live MLB postseason games. Report calls, bytes and wall time.

DELIVERABLE 5 -- MEASURE.
  a) The same ranking table as 45.1 D5: every family, every policy, E_net and fee-excluded E, CIs,
     fill rates, fragility flags, labels. H(tau) per category. Drift with placebo ratio.
  b) Coherence: weather brackets are mutually exclusive sets. Run EXP-033's tests on them (import
     multileg_coherence.py) under the same toll and Holm rule.
  c) Weather benchmark: market-implied bracket probabilities against the pre-registered public
     forecast, both scored against settlement. Report delta-Brier (market minus forecast) with
     city-day cluster CI. If the forecast archive is unreachable from where you run (network
     allowlist), record the exact refusal, do not route around it, and report D5(c) UNMEASURED.
  STATE PLAINLY: does any family reach CANDIDATE-PENDING-CAPACITY; does any coherence cell survive;
  does the market price worse than the free public forecast, by how much, with what CI?
  A market that loses to a public forecast is NOT an edge until the gap survives cost and fee at
  entry. Say which of those two things you have shown.

DELIVERABLE 6 -- REPORT.
  Results summary line by line against the pre-registration, ending with one paragraph scoped to
  exactly the series, window and cadence tested. Then a section headed
  GAPS FOUND -- FOR REGISTRATION BY 45.1 OR WAVE 46.

DO NOT:
  - Write into exp_output/PRICE_ARCHIVE/ or any existing store; edit any capture writer.
  - Edit market_efficiency_survey.py, execution_cost_surface.py or multileg_coherence.py.
  - Fit, tune or select any forecasting model on outcomes. The public forecast is used as
    published, through a mapping fixed in D3.
  - Use any forecast issued after the market snapshot it is compared against.
  - Change a pre-registered gate, policy, threshold, mapping or rule after seeing a result.
  - Promote anything past CANDIDATE-PENDING-CAPACITY.
  - Generalize past the series, window and cadence measured.
  - Touch any pool, position, schedule, sizing or kelly_fraction. Install no cron entry.
  - Write to GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 45.1 owns them.
  - Pull, stash, reset, checkout or commit in the shared main tree.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

# 45.3 -- LAND THE RECORD, COUNT THE BRANCHES, FIND OUT WHAT THE DASHBOARD SERVES - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
You are the ONE block this wave that works in the shared main tree, for D0 and D1 only.
Everything else from a worktree: scripts/new_session_worktree.sh "land-the-record"
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).

YOU OWN, THIS WAVE, EXCLUSIVELY:
  the shared main tree's sync; 04_EXECUTION/ACTIVE_QUEUE.md, 04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md,
  04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md and 04_EXECUTION/NEW_WINDOW_PASTE_IN.md (land as
  written -- do not edit their content); the predecessor merges named in D2; one results summary;
  read-only probes on the VPS.
YOU DO NOT WRITE: GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 45.1 owns them. List findings under
  GAPS FOUND in your results summary.

THE STATE THIS BLOCK FIXES -- verify each item, do not assume it:
  1. THE QUEUE RECORD FOR WAVES 37-45 IS NOT ON origin/main. At origin/main d8d5850,
     ACTIVE_QUEUE.md still shows Wave 37 and ACTIVE_QUEUE_ARCHIVE.md stops at Wave 36. The real
     record -- this Wave 45 queue, and Waves 37-44 archived verbatim -- exists ONLY as uncommitted
     edits in the shared main tree, which is ~140 commits behind origin/main. One stash, checkout
     or reset there destroys it. STRATEGIC_WINDOW_CARRY_FORWARD.md and NEW_WINDOW_PASTE_IN.md are
     untracked in the same tree.
  2. ADR-0067 (append-only position log, PROPOSED) is on no main. It lives only on
     origin/session/20260930T001343Z-t4-ledger-durability (4b7a2af). One T-600 commit (de94172,
     session-end handoff) is not patch-equivalent to anything on main.
  3. git counts 32 remote branches as not merged into origin/main. The carry-forward says 9 carry
     unlanded work. Most are probably landed under other hashes. Nobody has counted properly.
  4. THE DASHBOARD'S RUNNING STATE IS UNKNOWN. The carry-forward says the VPS serves the old page.
     T-602 (D5) saw pmbot-web-dashboard's process start at 2026-10-01T02:25:20Z, restarted by
     someone other than that session, process.sha f962a57c, never compared to disk. Either an
     unrecorded restart or a crash-restart (GG-118: this service has OOM-looped before while
     is-active reported active).

DELIVERABLE 0 -- SNAPSHOT BEFORE TOUCHING ANYTHING. In the shared tree paste: git status --short,
  HEAD, origin/main, git rev-list --left-right --count HEAD...origin/main (say which side is
  which), and md5sum of the four 04_EXECUTION files above. Copy those four files to a scratch
  directory OUTSIDE the repo and paste the copies' md5sums. That copy is the only undo.

DELIVERABLE 1 -- LAND THE RECORD, THEN FAST-FORWARD THE SHARED TREE.
  a) In a fresh worktree off origin/main, copy the four files in byte-for-byte from the shared
     tree, confirm md5 matches D0, commit them path-scoped, push with rebase-retry. Paste the pushed
     SHA and git hash-object of each landed file against the shared-tree copy.
  b) In the shared tree, if and only if each of the four is byte-identical to the pushed blob:
     restore the two TRACKED paths (ACTIVE_QUEUE.md, ACTIVE_QUEUE_ARCHIVE.md) to HEAD, move the two
     UNTRACKED files into your D0 scratch directory (identical copies arrive with the pull), then
     git pull --ff-only. Re-check md5 of all four against D0 afterwards and paste.
     If the fast-forward is refused for ANY other path, STOP: paste the refusal, list the blocking
     paths, hand back. 04_EXECUTION/SESSION_CLAIMS.md is merge=union and carries other sessions'
     rows -- never discard its local edits; if it blocks the fast-forward, report and stop.
  c) Paste HEAD == origin/main afterwards. 04_EXECUTION/_w33_recovered.md is untracked: report
     whether its content already exists verbatim in the archive. Do not delete it.

DELIVERABLE 2 -- LAND THE NAMED PREDECESSORS, OR SAY EXACTLY WHY NOT.
  For origin/session/20260930T001343Z-t4-ledger-durability and commit de94172: git cherry -v
  against origin/main, list what has not landed, and run the full test suite on a merge candidate.
  A MERGE CAN BE A DEPLOYMENT HERE. First establish, read-only, how /opt/prediction-market-bot on
  the VPS is updated and whether any cron job or service executes from a checkout that tracks
  main. If it does, runtime code (anything under src/, or any script a cron line calls) landing on
  main can reach production on the next pull. In that case land ONLY documents and non-runtime
  files (the ADR-0067 file, results, benches), leave runtime changes on the branch, and say so.
  Never land red work. ADR-0067 lands as PROPOSED; accepting it is the operator's decision.

DELIVERABLE 3 -- COUNT THE BRANCH ESTATE PROPERLY.
  For every remote branch not merged into origin/main: git cherry -v origin/main <branch>.
  One table: branch, last commit date, commits NOT patch-equivalent on main, what they are, tests
  green or red against main, and a disposition -- LANDED-UNDER-ANOTHER-HASH (safe to delete later),
  CARRIES UNLANDED WORK (name it), or SUPERSEDED (cite what superseded it).
  DO NOT DELETE ANY BRANCH. The table is the deliverable; deletion is a later, separate act.

DELIVERABLE 4 -- WHAT IS THE DASHBOARD ACTUALLY SERVING? READ-ONLY.
  On the VPS: systemctl show pmbot-web-dashboard.service -p
  NRestarts,ActiveState,SubState,ExecMainStartTimestamp; journalctl -u pmbot-web-dashboard.service
  --since '-72 hour' | grep -c oom-kill, and the journal lines around 2026-10-01T02:25Z; GET / and
  hash the HTML; hash the _HTML embedded in scripts/web_dashboard.py at origin/main AND in the VPS
  checkout's file on disk; GET /api/data and report whether rejected_counts, t4_cycle_tail and
  process exist, and process.sha.
  One-line verdict: NEW PAGE RUNNING / OLD PAGE RUNNING / NEW FILE ON DISK, OLD PROCESS / UNKNOWN --
  plus whether the 02:25Z start was an OOM crash-restart, a manual restart, or undeterminable.
  RESTART: look under "Needs your decision" in ACTIVE_QUEUE.md for an authorization line naming
  pmbot-web-dashboard. Absent: do not restart, say so. Present: restart within exactly that scope,
  then re-verify from the RUNNING process (GG-279). Never rotate, truncate or clear a journal or log.

DELIVERABLE 5 -- REPORT.
  One results summary: the D0 snapshot, landed SHAs, the predecessor disposition, the branch
  table, the dashboard verdict, and a section headed
  GAPS FOUND -- FOR REGISTRATION BY 45.1 OR WAVE 46.

DO NOT:
  - In the shared tree: stash, reset --hard, clean, or checkout any path other than the two
    tracked files you landed in D1(a). Never use git add -A or git commit -a.
  - Edit the content of the queue, archive, carry-forward or paste-in. Land them as written.
  - Delete any branch, worktree or file.
  - Land red work, or land runtime code onto a main that production pulls from.
  - Accept any ADR. Landing a PROPOSED ADR is not accepting it.
  - Restart any service absent an authorization line naming it.
  - Rotate, truncate or clear a VPS log or journal.
  - Add or install a cron entry.
  - Write to GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 45.1 owns them.
  - Touch sizing, stake, or kelly_fraction.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

## THE ARC — Waves 45 through 48

| Wave | The question it answers |
|---|---|
| **45** | *Is Kalshi's board beyond MLB/NFL efficient net of cost and fee — sports and non-sports? Is any Kalshi book worse than a free public forecast? Is the record safe, and what is the dashboard actually serving?* |
| **46** | If anything reaches CANDIDATE-PENDING-CAPACITY: **capacity first** — depth capture for exactly that family (needs your cron line), then a pre-registered build against it, scored on the T-583 harness. If nothing does: **leave Kalshi** — Polymarket US (T-077 KYC), DFS pick'em (separate ADR), or a sharp-book reference comparison (odds feed) — each gated on you; and/or the information-set question. |
| **47** | Sizing — the first revisit of `kelly_fraction = 0.0` since July — only if something cleared a gate. ADR-0069 governs it if the survivor is multi-leg. |
| **48** | Open the pipes for whatever actually scored. |

What should reorder this, and what should stop it:

- If **45.1's correctness gate fails** (candles cannot reproduce the archive), every candle-based number
  in 45.1 and 45.2 is void, and Wave 46's first job is capture design — forward archives for the new
  series, which needs your schedule authorization — not analysis.
- If **45.1 finds a CANDIDATE-PENDING-CAPACITY in an in-season sport** (NHL, NBA, NCAAF), capacity
  becomes time-sensitive: depth cannot be backfilled, so the depth line for that family is the first
  thing Wave 46 asks you for.
- If **45.2 finds the market worse than the public forecast** with a CI that excludes zero, that is the
  first measured case of a Kalshi book priced below a free benchmark. It is not an edge until it
  survives cost and fee at entry, and Wave 46 pre-registers exactly that test.
- **Stop condition, pre-registered:** if 45.1 finds no CANDIDATE-PENDING-CAPACITY and no surviving
  multi-leg cell across every sports series it can measure, AND 45.2 finds none across every non-sports
  series it can measure, then **Kalshi is efficient net of cost and fee across every series and cadence
  the project can currently measure.** The next decision is then **off-Kalshi** (which venue — each route
  is gated on you) or **the information set** (what does the model know that the market doesn't) — not
  another Kalshi family, and not another model on a Kalshi family. That conclusion is scoped to what was
  measured, and it is a legitimate place to arrive.

---

## Queued next — not yet fired

**T4M-PROJ and T3 disposition.** Both MISFILED under C5; T3 additionally has no order path at all.
Change-control entries drafted by 42.3, awaiting sign-off.

**The NFL pre-kickoff capture.** Runner built, 11/11 tests, hand-run twice, cron DRAFTED. No urgency —
43.3 showed nothing is unrecoverable.

**The settlement back-capture lives in a VPS scratch store** (`/opt/t602_out/SETTLEMENT_ARCHIVE`, 83,309
rows), not the repo archive. Where it permanently lives is decided by the cron line that installs it.

**ADR-0069** (game-key correlation group) — PROPOSED; governs sizing only if a multi-leg survivor appears.

**GG-317's 802 STUB rows · GG-295 actor provenance · GG-203 real fill.** Unchanged.

---

## Needs your decision

**Nothing in Wave 45 is gated on a line here** — all three blocks run to completion without you. One
deliverable *expands* if you write a line (45.3 D4), and two new items set up Wave 46.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **Dashboard service restart** | 45.3 D4 first finds out what is actually running. Write a line naming `pmbot-web-dashboard` and it restarts and verifies from the running process. | Possibly nothing — something restarted it at 02:25Z. D4 will say. |
| **Settlement + depth capture schedules** | Writers built, proven idempotent, cron lines drafted (settlement 09:30Z daily; depth :10 hourly in two windows). | **Depth is the one thing the historical endpoint cannot give.** Any Wave 45 candidate will be blocked on capacity until this runs. |
| **NEW — Polymarket US KYC (T-077)** | Only needed if the stop condition fires. The adapter is a placeholder until a key exists. | Wave 46's off-Kalshi route has nowhere to go. |
| **NEW — odds feed for a sharp-book reference** | A paid data source to test whether Kalshi just mirrors sportsbooks. A spend decision. | Same — one fewer off-Kalshi route. |
| **NFL pre-kickoff capture** | Built and proven; urgency disproved. A normal scheduling decision. | Nothing perishes. |
| **Provenance allowlist — 1,694 rows** | Verifies offline 13/13. Residual risks **L1** (VPS working-tree state at each start) and **L2** (`ba_l10_shrunk` input provenance) are yours. | An MLB season reads as 0 countable rows. |
| **APR-0035** | Both sides of its arithmetic exist. **Eight weeks open.** | The gate question stays open. |
| **ADR-0068** | Band doctrine. Already enforced through C5. **PROPOSED.** | C5 runs on an unaccepted criterion. |
| **ADR-0067** | Append-only position log. 45.3 lands it to main as PROPOSED. | Any pipe-opening wave is blocked behind it. |
| **39.3 triage — 6 NOTED** | One sign-off pass archives six entries. | Cheapest window recovery available. |
| **ADR-0063 · ADR-0064/0065/0066 · APR-0034/0036 · registry corrections** | Unchanged. ADR-0063 lands on one word. | — |

---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no operator approval in a block overrides it — an approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228). Re-capturing a raw source from its own upstream is a different act — say which one you are doing.
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding — and do not assume the rest of the board behaves like the cells that happened to be measurable.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization.
- Add a cron entry without explicit operator authorization, including for read-only capture writers.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`; **re-verify after any release or retry** (GG-322).
- Report a live fix RESOLVED without proving the RUNNING process contains it, not the file on disk.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Assume a fill the data cannot evidence.
- Revive `exchange_index` propagation — T-558 tested and disproved it.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.

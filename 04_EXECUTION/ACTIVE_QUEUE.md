# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates. Wave 45 is archived there.

**Verified against:** `origin/main = 7af1558` (2026-10-02 14:17 PT). *This window cannot `git fetch` or push.*

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-333** · **T-604** · **ADR-0069** · **EXP-035** — ADR-0067 still on no main |
| Live gap log | **124 OPEN** (Wave 45 registered GG-329..333) |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. |
| Wave 45 | **45.1 reached a verdict: its correctness gate FAILED** (GG-333). 45.2 and 45.3 closed PARTIAL. |
| Dashboard | **NEW PAGE RUNNING** (served HTML = origin/main `_HTML`, 59,130 B, process.sha d8d5850). Restarts at 10-01 02:25Z and 02:52Z were manual, not OOM. |
| Shared tree | 156 behind origin/main; **stale `.git/index.lock` since 2026-09-29 17:09 PT** blocks every git write there. |

---

## ⬛ WHAT WAVE 45 FOUND — READ THIS BEFORE THE BLOCKS

**Kalshi's history is reachable, but it has not been shown to equal what we captured.** That is the
one verdict Wave 45 produced, and it was produced correctly: frozen gate, run unrescued, failure
registered, nothing relabelled.

**EXP-035 Part 1 gate (0972862, `gate_result.json`):** candles rebuilt KXMLBTEAMTOTAL against our own
archive.

| Gate | Measured | Threshold | |
|---|---|---|---|
| G1 coverage | 1.000 / 0.998 | ≥ 0.98 | pass |
| G2 quote within 1c of candle close | **0.335** | ≥ 0.80 | FAIL |
| G3 quote inside candle range | **0.472** | ≥ 0.95 | FAIL |
| G4 B | **0.0319** vs 0.0257 | ± 0.003 | FAIL |
| G5 H | **0.090** vs 0.04 | ± 0.005 | FAIL |
| G6 sign of E | negative = negative | match | pass |
| G7 H by time-to-start | **matches in 6 of 7 buckets**; fails only [24,48)h: 0.065 vs 0.03 | ± 0.005 each | FAIL |

**The pattern is diagnostic, and it is a hypothesis — not a finding.** When candles and archive are
compared *by time-to-start* (G7), they agree almost exactly from in-play out to 24h. They disagree where
the comparison depends on *which moment* is matched: individual snapshots (G2, G3) and "first-seen" (G4,
G5, and the earliest bucket). Two design mismatches would produce exactly that:

- **Matching rule vs sparse candles.** Part 1 matched each archive snapshot to the candle with the
  smallest end time *at or after* t. But 1-minute candles have no row when nothing changed (EXP-034 found
  this). Where the quote was stable, that rule finds no candle, or finds the *next change* — a different
  quote by construction. EXP-034 froze the opposite rule (latest close *at or before* t) before seeing data.
- **"First-seen" is two different moments.** Candles see a market from listing, when books are widest;
  the archive first sees it at its first capture run. Wider early books would push H and B up — which is
  what G4/G5 show — and would show up only in the earliest bucket — which is what G7 shows.

Either could also be a code defect in `evaluate`, or the data could genuinely differ. **46.1 tests which.**

**The rest of what Wave 45 established:** `/historical/cutoff` = 2026-08-03 (GG-329); live and
historical candles use different schemas; the fee PDF sits behind a Vercel challenge, correctly not
bypassed (GG-332); EXP-034's own gate is frozen but not yet run; ~7 parallel fetchers broke pacing (4×
429s in shard 0 alone); Step 4 showed three undiagnosed anomalies on the live MLB pipeline.

**Why every block now has a MINIMUM CLOSE.** Wave 45 sessions ended mid-flight with fetches and a
background sampler still running. Each Wave 46 block names the earliest point where stopping still leaves
a verdict on record. Stopping before it is not a close.

---

## ⬛ FIRE NOW — Wave 46, three blocks, concurrent

| Paste | Block | Tier | One-line purpose |
|---|---|---|---|
| 1st | **46.1** | LARGE | **Why did the gate fail?** Diagnose it on data already fetched. Only if the cause is a design mismatch: a clean retest on a family nobody has looked at, same thresholds. Pass → the sports verdict. |
| 2nd | **46.2** | LARGE | **Finish EXP-034.** Run its own frozen gate, then the non-sports verdict and the public-forecast benchmark. |
| 3rd | **46.3** | STANDARD | **Sync the shared tree, land ADR-0067's documents, diagnose the three Step 4 anomalies.** |

**Fire order does not matter.** Surfaces are disjoint:

- **46.1 owns** `scripts/board_survey_sports*`, `tests/board_survey_sports*`, EXP-035's pre-registration /
  results / exp_output, its raw store (`exp_output/BOARD_SURVEY_SPORTS/`), the docstring of
  `scripts/archive_market_prices.py`, **and `GOVERNANCE_GAP_LOG.md` / `DECISION_LOG.md`.**
- **46.2 owns** `scripts/board_survey_nonsports*`, `tests/board_survey_nonsports*`, EXP-034's
  pre-registration / results / `exp_output/EXP-034-NONSPORTS-CONTROL/`, its raw store. **No GGL / DECISION_LOG.**
- **46.3 owns** the shared main tree and its sync, the `04_EXECUTION/` record files (landed as written),
  the ADR-0067 documents-only landing, one SESSION_CLAIMS row, one results summary, read-only VPS probes.
  **No GGL / DECISION_LOG.**
- **Read-only to all:** `market_efficiency_survey.py`, `execution_cost_surface.py`, `multileg_coherence.py`,
  `capture_settlements.py`, `exp_output/PRICE_ARCHIVE/` (shared tree only — GG-331; reference by absolute path).
- **Venue read budget, shared:** 46.1 and 46.2 each stay at or below **3.3 requests/s in aggregate across
  all of their own processes**, and halve on any 429. T4M-PROJ is reading live postseason games.

**Exactly three fences. A fourth means something is wrong -- stop.**

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Each block carries its workstream to a measured verdict.** Operator directive 2026-09-30. Stop only at a governance boundary — **and never before the block's MINIMUM CLOSE.** If a session must end early, end it at a verdict boundary, not mid-fetch, and say which boundary.
- **Deliverable 0 in every block: land any un-landed predecessor, and confirm your base.** This wave only 46.3 touches the shared main tree; 46.1 and 46.2 resume their own Wave 45 worktrees.
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). A claim row reading "TBD" gives no collision protection — claim real numbers.
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no approval in a block overrides it.
- **Frozen gates stay frozen, and failed gates stay failed.** A new test may be designed after a failure, but it is a new, separately pre-registered test, on data it has not seen, with thresholds no looser than the one that failed.
- **No background process outlives its session unrecorded.** If you leave one running, record its PID, command, output path and expected finish in the handoff — and prefer not to.
- **Push after each deliverable.** **A merge is not a deployment, and a deployment is not an activation** (GG-279).
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10-44 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **45** | **CLOSED** | **45.1: candle correctness gate FAILED** (G2–G5, G7; GG-333) — candle numbers VOID, no market verdict. 45.2 PARTIAL (gate frozen, not run). 45.3 PARTIAL: queue record landed (fa99794), dashboard NEW PAGE RUNNING, shared-tree sync blocked by a stale lock. |
| **46** | **FIRING** | Why did the gate fail, and does a clean retest pass? EXP-034's own gate and verdict. The shared tree and the Step 4 anomalies. |

---

## Why this wave is shaped this way

**The board survey stands or falls on whether the history endpoint can stand in for capture we never
did.** If it can, the survey runs on months of history today. If it cannot, every new series needs
forward capture — weeks of waiting and a cron line from you — before anything can be measured. Wave 45's
gate said "not as tested". Wave 46 finds out whether that means "not at all" or "not the way we asked".

**46.1 diagnoses before it retests, and retests only on clean ground.** The diagnosis uses data already
fetched and changes nothing about the failed verdict. A retest happens only if the diagnosis points at a
design mismatch rather than at the data — and then on an archived family nobody has compared, with every
threshold identical to the gate that failed. That is the difference between learning from a failure and
re-cutting until something passes.

**46.2 is independent of 46.1, and that is useful.** EXP-034 checks candles against *live quotes read in
the same session* on non-sports series, with the "latest close at or before t" rule frozen before it saw
data. If it passes while 46.1's original gate failed, that is evidence the original matching rule was the
problem, from a test that was never adjusted.

**46.3 clears the ground the other two stand on.** The shared tree holds the price archive both surveys
read and the queue every terminal reads. A three-day-old lock file is the only thing stopping it syncing.
The three Step 4 anomalies sit on the one pipeline that is actually live.

---

## WAVE 46 BLOCKS

---

# 46.1 -- WHY THE GATE FAILED, AND A CLEAN RETEST ON A FAMILY NOBODY HAS LOOKED AT - LARGE

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
RESUME the Wave 45 worktree (it holds the raw store and the Part 1 sample):
  /Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20261002T192708Z-kalshi-sports-board-survey
If that worktree is gone, stop and report.
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).
Highest seen at queue-write time: GG-333, T-604, ADR-0069, EXP-035. Verify; do not assume.
You are the only block this wave that writes GOVERNANCE_GAP_LOG.md and DECISION_LOG.md.

YOU OWN, THIS WAVE, EXCLUSIVELY:
  scripts/board_survey_sports*, tests/board_survey_sports*, EXP-035's pre-registration, results
  summary and exp_output dirs, exp_output/BOARD_SURVEY_SPORTS/, GOVERNANCE_GAP_LOG.md,
  DECISION_LOG.md, and the module DOCSTRING ONLY of scripts/archive_market_prices.py.
READ-ONLY (import, never edit): market_efficiency_survey.py, execution_cost_surface.py,
  multileg_coherence.py, capture_settlements.py; exp_output/PRICE_ARCHIVE/ in the SHARED tree, by
  absolute path (GG-331). Do not pull, stash or commit in the shared tree; 46.3 owns it.

THE VERDICT THIS BLOCK STARTS FROM -- it stands, and nothing here relabels it:
  EXP-035 Part 1 (frozen e28166a) FAILED at 0972862, unrescued (gate_result.json, GG-333):
    G1 pass (1.000 / 0.998)        G2 0.335 (need >= 0.80)        G3 0.472 (need >= 0.95)
    G4 B 0.0319 vs 0.0257 (+-.003) G5 H 0.090 vs 0.04 (+-.005)    G6 pass (sign)
    G7 candle half-spread equals EXP-032's in 6 of 7 tau buckets (in-play through [12,24)h);
       fails only [24,48)h: 0.065 vs 0.03.
  Candle numbers from Part 1 are VOID and may not be cited as evidence either way.

THE WINDOW'S READING -- FOUR HYPOTHESES, NONE ESTABLISHED. Test them; do not assume any:
  H1 MATCHING RULE vs SPARSE CANDLES. Part 1 matched each archive snapshot at t to the 1-minute
     candle with the smallest end_period_ts >= t inside [t-120s, t+120s]. 1-minute candles have NO
     row when nothing changed (EXP-034 D1(a)). Where the quote was stable, that rule finds no
     candle, or finds the NEXT change -- a different quote by construction. EXP-034 froze the
     opposite rule before seeing data: prevailing quote = close of the latest candle at or before t.
  H2 "FIRST-SEEN" IS TWO DIFFERENT MOMENTS. Part 1's candle first-seen = earliest usable hourly
     candle after window start; the archive's = its first capture run. If candles see markets
     earlier, when books are widest, B and H at "first-seen" differ while the time-bucketed surface
     agrees -- the G4/G5 failures with G7 failing only in [24,48)h fit this.
  H3 A CODE DEFECT in board_survey_sports_gate.py evaluate (no tests exist yet).
  H4 THE DATA GENUINELY DIFFER: candle quotes are not the quotes the archive recorded.

MINIMUM CLOSE: D2 pushed -- the diagnosis verdicts and the fee re-score on record.

DELIVERABLE 0 -- BASE AND STORE STATE. Paste origin/main SHA; worktree HEAD and relation to
  origin/main (fast-forward if behind); pgrep -af board_survey_sports (nothing should be running);
  per-shard file counts, bytes and manifest sha256s. Sum fetch totals across ALL shards (45.1 only
  reported shard 0: 2600 calls, 84MB, 4755s, 4 x 429).

DELIVERABLE 1 -- TESTS FIRST. tests/board_survey_sports_*: both candle schemas (live *_dollars/*_fp,
  historical bare keys) parse to identical values; sparse candles; null price with populated
  previous; scalar settlements; store idempotency; the G7 reader against the real EXP-032
  results.json; and a unit test that pins down what evaluate's matching rule actually does on a
  hand-built sparse candle series. Push green. Never land red.

DELIVERABLE 2 -- DIAGNOSE THE FAILURE, READ-ONLY, ON DATA ALREADY FETCHED.
  a) G2/G3: classify every failing Part 1 snapshot -- (i) no candle within the window; (ii) a candle
     found, but it is a later quote change than t; (iii) empty-book placeholder; (iv) the prevailing
     close at or before t ALSO disagrees by > 0.01. Counts and shares. Only (iv) is evidence for H4.
  b) G4/G5: per ticker, candle first-seen time minus archive first-seen time (distribution). Then
     recompute B and H at the ARCHIVE's own first-seen timestamps from candles, labelled DIAGNOSTIC.
  c) H3: code review of evaluate against the Part 1 text, line by line. Any defect gets a test.
  d) Verdict per hypothesis: SUPPORTED / NOT SUPPORTED / UNDETERMINED, with the numbers.
  e) FEE RE-SCORE OF THE OLD FRONTIER (no candles needed, so always run it): subtract the venue fee
     from EXP-031's and EXP-032's published E columns, beside the originals. Fee source: API series
     fee_type / fee_multiplier plus the docs.kalshi.com fee and rounding pages, cited with URL and
     retrieval date; the PDF is unread (GG-332). If the venue's rule differs from ADR-0016's
     0.07*p*(1-p), use the venue's and register the divergence. Relabel neither verdict.
  Nothing in D2 changes Part 1's verdict. No D2 number is cited as validating candles.
  DECISION: if (iv) carries the failure, or nothing can be attributed: STOP. Candles are not a
  substitute for the archive; the board survey needs forward capture (Wave 47). Register, log,
  report -- a complete, valid close. If H1 and/or H2 (and/or a fixed H3) account for the failure:
  continue to D3.

DELIVERABLE 3 -- GATE 2: PRE-REGISTER ON A FRESH FAMILY. PUSH IT ALONE, BEFORE ANY COMPARISON.
  - A NEW test, titled as designed after Part 1 failed (GG-333). Part 1 stays FAILED.
  - Family: one archived MLB family NOT used in Part 1 and NOT touched in D2. Choose it by a rule
    written before looking at any of its candles (e.g. the archived family with the most settled
    tickers after KXMLBTEAMTOTAL); paste the counts the rule used.
  - Changes from Part 1 are limited to what D2 found mismatched: matching = close of the latest
    candle at or before t (EXP-034's frozen rule); B and H computed at the archive's own first-seen
    timestamps. NOTHING ELSE CHANGES.
  - THRESHOLDS IDENTICAL TO PART 1: G1 >= 0.98; G2 >= 0.80 within 0.01; G3 >= 0.95; G4 |dB| <= 0.003;
    G5 |dH| <= 0.005; G6 sign; G7 every bucket within 0.005. Loosen none.
  - A new fixed seed, stated. KXMLBTEAMTOTAL re-run under Gate 2 is reported as SECONDARY only and
    can never decide the verdict.

DELIVERABLE 4 -- RUN GATE 2. Fetch only what it needs, one process or one shared token bucket at or
  below 3.3 requests/s, halving on any 429. Report every gate against its threshold.
  FAIL: candles are not validated for survey use. Register, log, report, stop -- a complete close.
  PASS: candles are validated for time-matched use on archived MLB books. Continue.

DELIVERABLE 5 -- ONLY IF GATE 2 PASSED: THE SPORTS VERDICT.
  a) Inventory every Kalshi sports series beyond the 14 surveyed (structure, settled count, events,
     span, start-clock source, measured start-to-close durations). Counts only; commit alone.
  b) EXP-035 Part 2, pushed alone before any outcome statistic on a new family: cohort rule and
     INSUFFICIENT floor per family; snapshot definition; B and null imported from EXP-031; cost
     surface from EXP-032 plus fee; E_net = B - null - H - fee primary, fee-excluded E alongside;
     policies (a) first-seen, (b) cheapest MEASURED cell with B-at-entry, (c) rest-at-mid with
     fills evidenced only by a later quote strictly through the order; a clock gate PER FAMILY
     sized from (a)'s durations (GG-327); Holm across all families, m stated;
     CANDIDATE-PENDING-CAPACITY as the strongest label; drift with backward placebo.
  c) Back-capture the cohort (same rate discipline, idempotent, run twice) and measure: one ranking
     table, every family, every policy; KXMLBHIT's EXP-032 row re-scored net of fee as reference;
     H(tau) per sport; drift with placebo; EXP-033 coherence tests (import) on every multi-leg set.
     STATE PLAINLY: any CANDIDATE-PENDING-CAPACITY? any surviving multi-leg cell?

DELIVERABLE 6 -- REGISTER, LOG, REPORT.
  Register, deduplicated against GG-329..333: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/
  WAVE45_land_the_record_results.md GAPS FOUND (11 items); EXP-034's candle schema divergence and
  sparse 1-minute candles; and 46.2's / 46.3's GAPS FOUND if on origin/main before you close.
  Correct the archive_market_prices.py docstring to say exactly what is established -- history is
  reachable (GG-329); equivalence to the archive is Gate 2's verdict, or UNVALIDATED (GG-333) if
  Gate 2 did not run. Docstring only. One DECISION_LOG entry.
  Results summary: the diagnosis, the fee re-score, Gate 2 (pre-registration and result) if run,
  the sports verdict if reached -- each scoped to exactly what was measured.

DO NOT:
  - Relabel Part 1, edit any Part 1 threshold, seed, matching rule or population, or cite a D2 number
    as validating candles.
  - Write Gate 2 after looking at its family's candles, or loosen any threshold in it.
  - Run fetchers above 3.3 requests/s in aggregate. Leave no unrecorded background process.
  - Write into exp_output/PRICE_ARCHIVE/ or edit any capture writer's code.
  - Edit market_efficiency_survey.py, execution_cost_surface.py or multileg_coherence.py.
  - Re-cut B or the null for MLB/NFL families. D2(e) adds fee; nothing else.
  - Promote anything past CANDIDATE-PENDING-CAPACITY. Volume is not depth.
  - Recommend against a sport, band or family on one finding, or assume unmeasured series behave like
    measured ones.
  - Build, fit or tune any forecasting model.
  - Touch NBA pipeline code, any pool, position, schedule, sizing or kelly_fraction. Install no cron.
  - Pull, stash, reset, checkout or commit in the shared main tree.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

# 46.2 -- FINISH EXP-034: ITS OWN GATE, THEN THE NON-SPORTS VERDICT - LARGE

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
RESUME the Wave 45 worktree:
  /Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20261002T192711Z-kalshi-nonsports-control
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).
Highest seen at queue-write time: GG-333, T-604, ADR-0069, EXP-035. EXP-034 is yours.

YOU OWN, THIS WAVE, EXCLUSIVELY:
  scripts/board_survey_nonsports*, tests/board_survey_nonsports*, EXP-034's pre-registration,
  results summary and exp_output/EXP-034-NONSPORTS-CONTROL/, its raw store (location in report).
READ-ONLY (import, never edit): market_efficiency_survey.py, execution_cost_surface.py,
  multileg_coherence.py, capture_settlements.py.
YOU DO NOT WRITE: GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 46.1 owns them. GAPS FOUND goes in your
  results summary. Do not pull, stash or commit in the shared main tree; 46.3 owns it.

WHERE WAVE 45 LEFT THIS -- verify, do not assume (SESSION_HANDOFF_20261002_1945.md, D1_FINDINGS.md):
  - D1(a) done: /historical/cutoff = 2026-08-03; candles reach back to market open; 1-minute candles
    sparse; live vs historical schema divergence; no rate-limit headers.
  - D1(c): API series metadata fee_type=quadratic, fee_multiplier=1. Fee PDF unread: HTTP 429 behind a
    Vercel challenge (GG-332). Correctly not bypassed.
  - D1(b) tolerance FROZEN at 38b8490 (D1B_TOLERANCE_PREREG.md) BEFORE any comparison: 12 tickers
    (first 2 open in KXHIGHNY, KXHIGHCHI, KXHIGHMIA, KXCPI, KXPAYROLLS, KXGDP at round 0), >= 6 rounds
    >= 20 min apart, 1-minute candles pulled after the last round + 10 min; matching = close of the
    latest candle at or before t; pass rule +/-0.01; gate >= 95% pass and no miss > 0.03.
  - Sampler started as background PID 63247 at 19:33Z on 2026-10-02, 7 rounds x 21 min; only round 0
    was recorded at close. Output d1b_live_quotes.jsonl, untracked.
  - Branch commit 0f5de4e (session-end nav) is not on main. D2-D6 not started.

YOUR SIBLING'S GATE FAILED -- READ IT, DO NOT INHERIT IT:
  EXP-035 Part 1 (GG-333) tested candles against the MLB archive and FAILED (G2-G5, G7). Your D1(b)
  gate is independent: different series, live quotes read in-session as the reference, and the
  "latest close at or before t" matching rule frozen before you saw data -- the very rule 46.1 is
  testing as the possible cause. Your gate's verdict stands on its own frozen terms. Do not adjust
  anything because of GG-333. Report your result in full; that comparison is itself evidence.

MINIMUM CLOSE: D2 pushed -- the D1(b) gate verdict on record.

DELIVERABLE 0 -- BASE AND SAMPLER STATE. Paste origin/main SHA, worktree HEAD (fast-forward if
  behind), whether PID 63247 is alive, and d1b_live_quotes.jsonl's line count, rounds present, their
  UTC times and spacing, and its sha256. Land 0f5de4e only if still meaningful; otherwise say it is
  superseded.

DELIVERABLE 1 -- TESTS. Parser handles both candle schemas to identical values; sparse candles
  resolve to the prevailing earlier close per the frozen matching rule; null price with populated
  previous; scalar settlements. Push green.

DELIVERABLE 2 -- THE D1(b) GATE. THE VERDICT.
  a) If the file holds >= 6 rounds spaced >= 20 minutes: pull the 1-minute candles (after last round
     + 10 min), run the frozen comparison, report every pair and the gate result.
  b) If it holds fewer: the sample is incomplete. The frozen rule fixes tickers at round 0, and
     daily weather tickers may have closed since. Write an AMENDMENT commit BEFORE any comparison:
     keep the partial file, labelled and never compared; re-draw 12 tickers by the SAME rule at a new
     round 0; every tolerance unchanged; run >= 6 rounds in-session in the foreground, or with the
     PID recorded.
  FAIL: every candle-based number in EXP-034 is VOID. Write the results summary and stop -- a
  complete, valid close. PASS: continue.

DELIVERABLE 3 -- INVENTORY, THEN PRE-REGISTRATION. EACH PUSHED ALONE.
  a) Every Kalshi NON-SPORTS series with settled markets reachable via the endpoints: category,
     structure, settled count, events, date span, the settlement source as Kalshi states it, open-to-
     close durations. Too few events = listed as INSUFFICIENT, never dropped silently. Counts only.
  b) Pre-registration, pushed alone before any outcome statistic: cohort rule and INSUFFICIENT floor;
     snapshot definition; B and null imported from EXP-031; cost surface from EXP-032 plus fee;
     E_net = B - null - H - fee primary, fee-excluded E alongside; policies (a) first-seen, (b)
     cheapest MEASURED cell with B-at-entry, (c) rest-at-mid with fills evidenced only by a later
     quote strictly through the order; the clock as hours-to-close (for weather, also hours before
     the settling observation day) sized from (a); Holm, m stated; CANDIDATE-PENDING-CAPACITY as the
     strongest label; drift with backward placebo. Fee source as 46.1 D2(e) states it.
     THE PUBLIC-FORECAST BENCHMARK (weather): name the product and archive; the issue time used for
     each snapshot, strictly BEFORE the snapshot; the exact forecast-to-bracket mapping; Brier and log
     loss against settlement with city-day cluster CIs. The mapping is fixed here. Any free parameter
     is fixed from documentation or from data strictly before the cohort window -- say which.

DELIVERABLE 4 -- BACK-CAPTURE AND MEASURE.
  At or below 3.3 requests/s in aggregate across your processes; halve on any 429; idempotent run
  twice with hashes. Then: one ranking table, every family, every policy; H(tau) per category; drift
  with placebo; EXP-033 coherence tests on bracket sets; the weather benchmark as delta-Brier (market
  minus forecast) with CI. If the forecast archive is unreachable from where you run, record the
  exact refusal, do not route around it, and report the benchmark UNMEASURED.
  STATE PLAINLY: any CANDIDATE-PENDING-CAPACITY; any surviving coherence cell; is the market worse
  than the free forecast, by how much, with what CI? Losing to a public forecast is not an edge until
  the gap survives cost and fee at entry -- say which of those you have shown.

DELIVERABLE 5 -- REPORT. Results summary line by line against the pre-registration, scoped to
  exactly the series, window and cadence measured; state GG-333 and, if 46.1's diagnosis is on
  origin/main before you close, whether it bears on your gate. Then:
  GAPS FOUND -- FOR REGISTRATION BY 46.1 OR WAVE 47.

DO NOT:
  - Edit a frozen tolerance or matching rule. An AMENDMENT re-draws an incomplete sample by the same
    rule; it changes no threshold and is pushed before any comparison.
  - Compare a partial sampler file and then decide whether to amend. Decide on round count first.
  - Adjust anything in response to GG-333.
  - Run fetchers above 3.3 requests/s in aggregate. Leave no unrecorded background process.
  - Fit, tune or select any forecasting model on outcomes; use any forecast issued after the snapshot.
  - Change a pre-registered gate, policy, threshold, mapping or rule after seeing a result.
  - Promote anything past CANDIDATE-PENDING-CAPACITY. Generalize past what was measured.
  - Write into exp_output/PRICE_ARCHIVE/ or any existing store; edit any capture writer.
  - Touch any pool, position, schedule, sizing or kelly_fraction. Install no cron entry.
  - Write to GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 46.1 owns them.
  - Pull, stash, reset, checkout or commit in the shared main tree.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

# 46.3 -- SYNC THE SHARED TREE, LAND ADR-0067'S DOCUMENTS, DIAGNOSE STEP 4 - STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
You are the ONE block this wave that works in the shared main tree. Everything that commits goes
through a fresh worktree: scripts/new_session_worktree.sh "sync-and-diagnose"
Claim your own IDs at run time (GG-236); claim a real range, not "TBD" (45.3 GAPS item 9).

YOU OWN, THIS WAVE, EXCLUSIVELY:
  the shared main tree and its sync; 04_EXECUTION/ACTIVE_QUEUE.md and ACTIVE_QUEUE_ARCHIVE.md (land
  as written -- do not edit); one appended row in 04_EXECUTION/SESSION_CLAIMS.md (see D2); the
  ADR-0067 documents-only landing; one results summary; read-only VPS probes.
YOU DO NOT WRITE: GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 46.1 owns them. GAPS FOUND goes in your
  results summary.

WHAT THE WINDOW MEASURED AT 7af1558 -- re-verify every line before acting on it:
  - .git/index.lock: 0 bytes, mtime 2026-09-29 17:09 PT, held open by pid 33525
    (com.apple.Virtualization.VirtualMachine.xpc) per 45.3. Blocks every git write in the shared tree.
  - Shared tree HEAD 9f2b837, 156 behind origin/main, 0 ahead.
  - Dirty tracked files, each compared to its origin/main blob:
      IDENTICAL to origin/main: 02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md,
        03_DECISIONS/ADR-0014_per-band-decision-tree-mechanics.md, CLAUDE.md
      DIFFERS, but every locally added line is already on origin/main:
        02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md
      DIFFERS, generated output: 03_DECISIONS/OPERATOR_CONSOLE.md (a locally regenerated console;
        17 of its 22 added lines are not on origin -- generated text, not authored work)
      DIFFERS, ONE real unlanded line: 04_EXECUTION/SESSION_CLAIMS.md --
        | 2026-10-01T01:42:06Z | T-601 | CLOSED -- merge confirmed ... (cron drafted, not installed) |
      DIFFERS because the window wrote Wave 46 into them: 04_EXECUTION/ACTIVE_QUEUE.md,
        04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md
  - Untracked: "Live Terminal.html" (56,983 B, 2026-09-30 snapshot) collides with a TRACKED
    origin/main path (59,130 B, the landed terminal). NEW_WINDOW_PASTE_IN.md and
    STRATEGIC_WINDOW_CARRY_FORWARD.md are identical to origin/main. _w33_recovered.md, Visual
    Dashboard.html and Reload Dashboard.command are untracked and not on origin.

MINIMUM CLOSE: D3 done -- shared tree HEAD == origin/main, with nothing lost.

DELIVERABLE 0 -- SNAPSHOT. In the shared tree: git status --short, HEAD, origin/main, rev-list
  --left-right --count HEAD...origin/main (say which side is which), md5sum of every dirty and
  untracked file listed above. Copy ALL of them to a scratch directory OUTSIDE the repo; paste the
  copies' md5sums. That copy is the only undo.

DELIVERABLE 1 -- THE STALE LOCK. AUTHORIZED, WITH CONDITIONS.
  The operator's standing framing makes a stale lock in the local working tree plumbing, not a
  decision. Remove .git/index.lock if, and only if, ALL of these hold, each pasted as evidence:
    - ps -axo pid,etime,command | grep -i '[g]it' shows no git process operating on this repo;
    - lsof on the lock shows only the Virtualization XPC host (or nothing);
    - its mtime is more than 24 hours old.
  Any condition fails: do not remove; paste what you saw and hand back.

DELIVERABLE 2 -- LAND WHAT ONLY THE SHARED TREE HOLDS, FROM A WORKTREE.
  In the fresh worktree off origin/main, path-scoped commits, push with rebase-retry:
    a) ACTIVE_QUEUE.md and ACTIVE_QUEUE_ARCHIVE.md, byte-for-byte from the shared tree.
    b) the one SESSION_CLAIMS.md row above, appended (merge=union file; do not rewrite other rows).
  Paste pushed SHAs and git hash-object of each landed file against the shared-tree copy.

DELIVERABLE 3 -- FAST-FORWARD THE SHARED TREE.
  Only after D2 lands, and only file by file as classified above (re-verify each first):
    - files identical to the pushed origin/main blob: restore to HEAD;
    - EXECUTION_BANDS.md: restore only after re-confirming every local-added line is on origin/main;
    - OPERATOR_CONSOLE.md: generated; restore (the D0 copy keeps the local version);
    - "Live Terminal.html": move into the D0 scratch directory (origin's tracked version arrives);
    - NEW_WINDOW_PASTE_IN.md, STRATEGIC_WINDOW_CARRY_FORWARD.md: move into scratch (identical
      copies arrive).
  Then git pull --ff-only. Paste HEAD == origin/main, then md5 of every landed file against D0.
  ANY other path blocks the fast-forward: stop, paste the refusal and the path, hand back.
  Report whether _w33_recovered.md's content already exists verbatim in the archive. Delete nothing.

DELIVERABLE 4 -- LAND ADR-0067'S DOCUMENTS ONLY.
  45.3 established that production updates by manual git pull in /opt/prediction-market-bot, so
  main reaching production is a deployment. From origin/session/20260930T001343Z-t4-ledger-durability
  land ONLY: the ADR-0067 file (stays PROPOSED), the T-589 results, SESSION_HANDOFF_20260930_0045.
  Leave paper_trader.py, its tests and the bench script on the branch. Re-run the documents-only
  candidate's test suite on current main (an older base returned exit 0) and paste the summary line.
  Never land red work.

DELIVERABLE 5 -- DIAGNOSE THE THREE STEP 4 ANOMALIES. READ-ONLY.
  45.3 saw: SemanticFloorViolation = 1; two T1 MLB runs with 0 players matched; T4 cycle-log age 16h.
  MLB is in its postseason, so fewer games and off-days are expected -- but GG-049 (T1 dark for two
  game days) and GG-163 (T4 dark 43.5h while is-active said active) both looked exactly like this.
  For each anomaly: the exact timestamp(s); whether MLB games with Kalshi markets existed in that
  window (name the source); the matching cron log lines; verdict EXPECTED (with the evidence) or
  FAILURE (with what failed). Also report, without acting, what T1 and T4 MLB will do after the
  World Series ends -- does anything stop them, or will they run against an empty slate all winter?
  Do NOT restart, reconfigure or reschedule anything. Do NOT rotate or clear any log.

DELIVERABLE 6 -- REPORT. One results summary: D0 snapshot, lock evidence and action, landed SHAs,
  the fast-forward result, the ADR-0067 landing and test line, the three anomaly verdicts, the
  off-season answer, and GAPS FOUND -- FOR REGISTRATION BY 46.1 OR WAVE 47.

DO NOT:
  - Remove the lock unless every D1 condition holds and is pasted.
  - Stash, reset --hard, clean, or checkout any path not classified in D3. Never git add -A or
    git commit -a in the shared tree.
  - Edit the content of the queue or archive. Land them as written.
  - Delete any branch, worktree or file. Move-to-scratch is the only removal allowed, and only per D3.
  - Land runtime code onto main, or land red work. Accept no ADR.
  - Restart, reconfigure or reschedule any service or cron entry.
  - Rotate, truncate or clear a VPS log or journal.
  - Write to GOVERNANCE_GAP_LOG.md or DECISION_LOG.md. 46.1 owns them.
  - Touch sizing, stake, or kelly_fraction.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

## THE ARC — Waves 46 through 49

| Wave | The question it answers |
|---|---|
| **46** | *Why did the candle gate fail, and does a clean retest pass? Do candles match live quotes on non-sports series? If either holds: is Kalshi's board beyond MLB/NFL efficient net of cost and fee?* Plus: a synced shared tree and a diagnosed live pipeline. |
| **47** | If candles are validated and something reaches CANDIDATE-PENDING-CAPACITY: **capacity first** — depth capture for that family (needs your cron line), then a pre-registered build on the T-583 harness. If candles are validated and nothing does: **leave Kalshi** — Polymarket US (T-077 KYC), DFS pick'em (ADR), or a sharp-book reference (odds feed) — each gated on you; and/or the information-set question. **If candles are not validated: forward capture** for the new series (needs your cron line), and the survey waits for data. Also the MLB off-season disposition of T1/T4. |
| **48** | Sizing — the first revisit of `kelly_fraction = 0.0` since July — only if something cleared a gate. ADR-0069 governs it if the survivor is multi-leg. |
| **49** | Open the pipes for whatever actually scored. |

What should reorder this, and what should stop it:

- If **46.1's diagnosis attributes the failure to genuinely different data (H4)**, candles are out as a
  substitute for capture — for sports and, until shown otherwise, for non-sports too. Wave 47 is forward
  capture design, and nothing gets measured on new series until that data exists.
- If **46.2's gate passes and 46.1's Gate 2 fails** (or the reverse), neither experiment's results are final
  until the disagreement is explained. That reconciliation comes before any further analysis.
- If **a CANDIDATE-PENDING-CAPACITY appears in an in-season sport** (NHL, NBA, NCAAF), capacity is
  time-sensitive: depth cannot be backfilled, so that family's depth line is the first thing Wave 47 asks
  you for.
- If **46.2 finds a market worse than the public forecast** with a CI excluding zero, it is not an edge
  until it survives cost and fee at entry; Wave 47 pre-registers exactly that test.
- If **46.3 finds a Step 4 anomaly is a FAILURE**, it is registered and fixed before anything else touches
  the live pipeline.
- **Stop condition — pre-registered in Wave 45, carried unchanged:** if 46.1 finds no
  CANDIDATE-PENDING-CAPACITY and no surviving multi-leg cell across every sports series it can measure,
  AND 46.2 finds none across every non-sports series it can measure, then **Kalshi is efficient net of
  cost and fee across every series and cadence the project can currently measure.** The next decision is
  then **off-Kalshi** (which venue — each route is gated on you) or **the information set** (what the
  model knows that the market doesn't) — not another Kalshi family, and not another model on a Kalshi
  family. That conclusion is scoped to what was measured, and it is a legitimate place to arrive.
  *(If candles are not validated, the condition cannot fire this wave — the measurement it depends on
  does not exist yet.)*

---

## Queued next — not yet fired

**T4M-PROJ and T3 disposition.** Both MISFILED under C5; T3 has no order path at all. Change-control
entries drafted by 42.3, awaiting sign-off.

**The branch estate.** 45.3's table: 33 unmerged branches, ~8 already landed under other SHAs, several
carrying runtime work (t497 flat-stake wrapper, NFL/NHL T4 scaffolding, gg255, gg267, gg291). No
deletions until each is dispositioned.

**The NFL pre-kickoff capture** — cron drafted; urgency disproved. **The settlement back-capture store**
lives in VPS scratch (`/opt/t602_out/SETTLEMENT_ARCHIVE`); its permanent home is set by its cron line.

**Test suite runtime** (45.3 GAPS item 10): the full suite exceeds 10 minutes; there is no documented
fast subset. **macOS lacks `timeout`** (item 8): protocol snippets using it fail with exit 127, silently.

**GG-317's 802 STUB rows · GG-295 actor provenance · GG-203 real fill.** Unchanged.

---

## Needs your decision

**Nothing in Wave 46 is gated on a line here.** All three blocks run to completion without you.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **Gate 2 (46.1 D3–D4)** — *window's default, veto here* | 45.1 handed back "amend the design or drop candles". The window's default: diagnose first; retest only if the diagnosis points at a design mismatch; fresh family, thresholds unchanged. Write **"NO GATE 2"** here to stop 46.1 after its diagnosis. | — |
| **Settlement + depth capture schedules** | Writers built and proven idempotent; cron lines drafted (settlement 09:30Z daily; depth :10 hourly in two windows). | Depth is the one thing the history endpoint cannot give. If candles fail, forward capture of new series needs a line too. |
| **Polymarket US KYC (T-077)** | Needed only if the stop condition fires. | Wave 47's off-Kalshi route has nowhere to go. |
| **Odds feed for a sharp-book reference** | A paid data source to test whether Kalshi mirrors sportsbooks. A spend decision. | One fewer off-Kalshi route. |
| **MLB off-season** | 46.3 reports what T1/T4 MLB do after the World Series. Whether to stand them down is yours. | Pipelines may run against an empty slate all winter. |
| **NFL pre-kickoff capture** | Built and proven; urgency disproved. | Nothing perishes. |
| **Provenance allowlist — 1,694 rows** | Verifies offline 13/13. Residual risks **L1** and **L2** are yours. | An MLB season reads as 0 countable rows. |
| **APR-0035** | Both sides of its arithmetic exist. **Nine weeks open.** | The gate question stays open. |
| **ADR-0068** | Band doctrine; already enforced through C5. **PROPOSED.** | C5 runs on an unaccepted criterion. |
| **ADR-0067** | Append-only position log. 46.3 lands its documents to main as PROPOSED. | Any pipe-opening wave is blocked behind it. |
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

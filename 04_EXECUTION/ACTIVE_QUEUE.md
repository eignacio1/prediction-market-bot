# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 1d99bee` (2026-10-08 ~17:15 PT, incoming strategic window; no drift from the carry-forward). PRs, CI and results docs read from GitHub; VPS facts are the Wave 60 terminals' reports (this window has no SSH; 61.2 re-checks).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-530** · **T-746** · **ADR-0071** · **EXP-038** · ADR-0070 ACCEPTED · gap log **130 OPEN** (parity 157 = 157, no duplicate ids) |
| Registry (104 cells) | ACTIVE 1 (T4M-PROJ) · SHADOW 24 (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 76 (incl. 12 NBA, flip ~10-21). MLB postseason game cells log + settle but are not registered SHADOW. Counted from `MARKET_TYPE_REGISTRY` at `edb3138`. |
| Capital | **$0 real.** `kelly_fraction = 0.0` on every operating band; **T4M-PROJ places flat paper measurement stakes of min($1, max_contracts x price)** (ADR-0050). Demo venue only. SHADOW = evaluate and log. |
| Shadow arms | **NFL** 12 cells logging, first look projected **2026-11-02**. **MLB postseason** armed and logging (judged n starts 2027). **NHL** 9 cells logging; judged n unreachable this season (GG-514); no NHL T3 score may be read (GG-401). **NBA** preseason rows to a separate labelled ledger; regular season 10-20, cells flip ~10-21. |
| Open PRs | Only stale ones from Waves 30-34 (#133, #144, #146, #149). Nothing from Waves 52-59 is waiting. |
| VPS | Last deploy `056428f` (#188), 2026-10-08 02:43 UTC, success; t4-mlb not restarted by Wave 60 (no T4 import changed). |
| Deploy | **GG-432 resolved (#158, 2026-10-05):** a push restarts `t4-mlb` only if it changes a file t4-mlb imports AND no MLB game is live; otherwise the restart is skipped and logged. Dashboard restarts every deploy. Code can land at any hour. |

---

## 🌲 RUNNING SITREP — the forest (kept by every strategic window; last window: Waves 52–60, 2026-10-03 → 10-08)

*Updated by the strategic window at every wave close and at every handoff. Last update: Wave 61 issued (new window), 2026-10-08 ~17:30 PT.*

**Bottom line.** The plumbing is now sound. Code lands at any hour without killing live services, MLB data no longer
depends on a blocked source, every resolved bet books from Kalshi's own settlement (1,229 of 1,229 match), and four
sports log shadow forecasts. **We still have no verdict that the model beats the market anywhere.** Wave 60 settled
what the only ACTIVE cell's sample is: **94.5% of T4M-PROJ's 1,952 rows were never filled.** The 107 real fills lose
$0.40 a bet. So T4M-PROJ is a calibration record, not trading evidence. **You decided that 2026-10-08 (GG-527 (b)+(c)); Wave 61 builds it.** The first honest
pre-registered edge verdict is **NFL, ~2026-11-02**.

### Scoreboard

| Measure | Start of window (10-03) | Now (10-08) |
|---|---|---|
| Real capital | $0 | $0 — demo only, Kelly 0 everywhere |
| Cells (registry) | 92 · ACTIVE 1 · SHADOW 16 on an unmerged branch | 104 · ACTIVE 1 · SHADOW 24 on main · 12 NBA ready to flip ~10-21 · MLB postseason logging |
| Sports logging forecasts | NFL, NHL (partly) | NFL, NHL, MLB postseason, NBA (preseason labelled + excluded) |
| Cells at a scored look | 0 | 0 — engine sealed below each cell's pre-registered n |
| Books truthful? | 26 MLB positions stuck; NFL book orphaned | All booked from Kalshi (ADR-0071); NFL book archived; **T4M-PROJ fills now known: 107 of 1,952** |
| Open gaps | 176, many stale | **130**, every one re-verified with dated evidence; hook shows the live count |
| VPS stability | Nightly out-of-memory crashes | Staggered crons + swap; clean since 10-05 |

### What this window built, by theme

| Theme | Waves | Outcome |
|---|---|---|
| **Landing + deploy safety** | 52–55 | Four stuck PRs landed (#158–#161). Deploys restart t4-mlb only when its code changed and no game is live. |
| **MLB data off statsapi** | 52–58 | Schedule, cache and features build on GitHub Actions; the degrading 22:30 cron is off; player-hits restored. |
| **Books + settlement** | 53–60 | Kalshi settlement is the paper resolution source; 26 stuck positions booked; settlements cross-checked; T4M-PROJ fill truth established; weekly rebuild can no longer wipe a repair. |
| **Shadow arms** | 53–60 | NFL 12, NHL 9, MLB postseason 12, NBA 12 (EXP-038, frozen model, crons, preseason ledger). |
| **Calibration engine** | 58–60 | One engine, every cell under its own pre-registration, sealed below n, frozen tamper-evident releases, schedule-based projections, NBA included, pre-registration holes closed by dated addenda. |
| **Dashboards** | 52, 56–60 | Live Terminal (`/`) = what the bot places/evaluates now; Visual Dashboard (`/project`) = health, books, evidence clocks, Calibration. Phone-width clean. |
| **Governance** | 58–60 | Gap log 176 → 130, all re-verified; deploy/ mirrors the live crontab; ADR-0070 accepted; window handoff is now a command (`/strategic-handoff`). |

### Against the north star — does the model know something the market doesn't?

| Arm | Status | When a verdict is possible |
|---|---|---|
| **T4M-PROJ** (MLB player hits, ACTIVE) | All rows -0.053/bet (CI spans 0); **real fills -0.40/bet (CI excludes 0), n=107**; latency thesis not supported (T-569) | Execution evidence says no. **Decided (GG-527 b+c):** rows = calibration record only; execution claims count fills; no T4M-PROJ stakes after the World Series (61.1 builds). |
| **NFL** (12 SHADOW) | Logging; 15 settled games per cell at last count | First look **~11-02** (60 games/cell) — may slip; rests on one week of coverage |
| **NHL** (9 SHADOW) | Logging; T3 rows now carry the projected-goalie flag (new rows) | PRELIMINARY all 2026-27 (accepted); base-rate check at 500 games |
| **NBA** (12 cells) | Sealed 0/150; opening night 10-20 | Cells flip ~10-21; first look at 150 games/cell |
| **MLB** game markets | Postseason logging, never scored | 2027 regular season |

### Calendar ahead

| Date | What happens |
|---|---|
| Mon 10-12 14:20 UTC | Weekly T4 resolved-ledger rebuild — first live test of the overwrite guard |
| 10-20 / 10-21 | NBA opening night; NBA cells flip to SHADOW once valid rows exist |
| ~11-02 | NFL first scored look — the project's first pre-registered edge verdict |
| World Series end | T4M-PROJ stakes stop (61.1 gate); registry flip to DARK (later block); T1 MLB winter posture is your call |
| before 2027-01-31 | Define EXP-038's date-triggered second look (GG-529) |

### Your open calls
~~T4M-PROJ cohort (GG-527)~~ decided 10-08 · MLB winter posture (T1 MLB; T4M-PROJ already stands down) · T4M-PROJ band placement (GG-320) · a P&L
gate that can be reached (GG-285) · approval path for self-modifying scripts (GG-289) · kill switch to count
unresolved stake (GG-441) · the unexplained SSH poller (GG-347) · T1 MLB postseason flag · EXP-038 second look
(GG-529, January) · EXP-034 (park recommended).

---

## ⬛ NOW — Wave 61 · issued 2026-10-08 ~17:30 PT · three MEDIUM blocks (60/90-min rule) · paste all three in parallel

Written by the incoming strategic window after verifying `origin/main = 1d99bee` against the carry-forward (no drift).
GG-527 decided by the operator 2026-10-08 (authorization line in "Needs your decision"). The surfaces don't overlap: 61.1 = T4
path + G6 counting + both dashboards' T4M-PROJ panels; 61.2 = VPS health, NHL rows, gap-log retirement, calibration
engine release path; 61.3 = a new exploratory directory + one CI test. Shared docs (gap log, DECISION_LOG, this file):
each block edits only its own entries.

| # | Block | Status | One line |
|---|---|---|---|
| 61.1 | GG-527 built: fills-only execution evidence + T4M-PROJ stand-down gate | ⬜ | — |
| 61.2 | Verdict readiness: VPS health, GG-401 close-out, gap-log retirement, NFL first-look rehearsal | ✅ DONE | VPS healthy; GG-401 RESOLVED; 5 gaps retired; NEW GG-532 (MLB shadow silent, no_kickoff). NFL 12 cells 15/60, first look 2026-11-02 confirmed (~11-09 if a game is missed). Release path fixed (#190): REPORT now written, verdict on dashboard. Runbook: 04_EXECUTION/NFL_FIRST_LOOK_RUNBOOK.md. |
| 61.3 | Exploratory research track: charter, isolation guard, data inventory, first NFL challenger study | 🟨 Parts A-C merged | Fence (#189), recal study (#192), rolling-origin 2019-23 (#194) all merged, CI green, t4-mlb restart not_needed. No challenger beats frozen EXP-037; no pre-reg warranted. Open: candle fetch finishing, GG-533 unregistered. |

### 61.1 — GG-527 built: fills-only execution evidence + T4M-PROJ stand-down gate

```
COMMON RULES - WAVE 61 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-08 (incl. the GG-527 decision), ADR-0070, ADR-0071. Standing
  authorizations: shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy +
  pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in ACTIVE_QUEUE.md "Needs your
  decision". A table row describing a decision is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. Demo only. No live-ledger row rewritten. No edit of an
  existing cron line. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W61_<n>.md (docs-only push).

WAVE 61.1 - GG-527 BUILT: FILLS-ONLY EXECUTION EVIDENCE + T4M-PROJ STAND-DOWN GATE. Repo: eignacio1/prediction-market-bot.

AUTHORITY
This block depends on the blockquote "AUTHORIZATION - GG-527 T4M-PROJ COHORT (operator, 2026-10-08 ...)" in
ACTIVE_QUEUE.md "Needs your decision". Confirm it is there before writing code. If it is missing, stop and report.
Build exactly what it covers, nothing it excludes.

WHY
W60.1 (#185) classified all 1,952 epoch-12 T4M-PROJ rows against the demo venue's own fill history: 107 filled,
1,845 never filled, 0 unverifiable. All rows -0.053/bet (CI spans 0); real fills -0.403/bet (CI -0.650..-0.156).
Per-row output: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W60_1_cohort_fill_truth_rows.json, script
scripts/w60_1_cohort_fill_truth.py. Operator decision: (b) those rows are model-calibration evidence only, any G6 or
execution claim counts real fills only; (c) T4M-PROJ places no paper stake after the 2026 World Series.
Strategic window's code read (verify): neither scripts/run_t4_mlb_live.py nor
src/prediction_market_bot/c5_execution/t4_mlb_execution_engine.py consults MARKET_TYPE_REGISTRY, so a registry status
change alone would NOT stop T4M-PROJ placing stakes when t4-mlb runs again in spring 2027. The gate must be in code.

PART A - Count it the way he decided (no ledger rewrite; ~45 min)
  1. Fill status as a sidecar, not a ledger edit: a reusable classifier (lift the join logic from
     scripts/w60_1_cohort_fill_truth.py into one function + a CLI) that writes logs/t4_mlb_fill_status.jsonl, one row
     per closed T4 position: position_id, kalshi_order_id, fill_class (CONFIRMED_FILLED / CONFIRMED_NOT_FILLED /
     UNVERIFIABLE), matched fill ids, classified_at. Idempotent; append-only for new positions, never rewrites an
     existing row (same rule as the GG-228 guard). Run it once on the VPS over every closed T4 position, including
     postseason rows after the W60.1 cutoff. Report counts.
  2. Keep it current without a cron edit: call the classifier from a code path that already runs on a schedule
     (scripts/run_band_monitor.py or the weekly resolved-ledger build - pick one, say why). No new or edited cron line.
  3. G6 counting: wherever T4M-PROJ's G6 clean_n / n* / P&L-per-bet is computed (start at scripts/run_power_calc.py,
     scripts/run_band_monitor.py, .claude/hooks/governance_scan.sh - grep clean_n; there are others), T4M-PROJ
     execution evidence = CONFIRMED_FILLED rows only. All-rows figures may still print, labelled
     "calibration only - not execution evidence". Tests. No other band's counting changes.
  4. Both dashboards: the T4M-PROJ evidence panel/clock on the Visual Dashboard (/project) and any T4M-PROJ P&L shown on
     the Live Terminal (/) show fills n and fills P&L as the execution figure, all-rows as "calibration record", with
     the label in plain words. Keep the current look. Phone width (390px) still clean.
  PR, CI green, merge; record the deploy decision. Verify on the VPS that the running dashboard shows the new labels.
PART B - The stand-down gate (code only; ~35 min)
  5. In the T4 placement path (wherever the paper stake for T4M-PROJ is placed - find it), add a gate: T4M-PROJ places
     no paper stake for any game whose MLB season is after 2026 (i.e. after the 2026 World Series) unless an explicit
     re-enable setting is on; default off; the setting's docstring names the GG-527 decision and says re-enable needs
     a new operator decision. Evaluations and cycle-log rows keep writing (the calibration record continues). Every
     skipped placement logs one counted line, not one line per cycle.
  6. Confirm the calibration record survives without positions: the cycle log (or whatever T4 writes per evaluation)
     carries model_p, market price, ticker, timestamp and a key that joins to the outcome. Show one real row. If it
     does not, register a gap and stop - do not widen this block.
  7. Tests: 2026 postseason game -> stake placed as today; 2027 game -> no stake, evaluation logged; re-enable on ->
     stake placed. The gate is in t4-mlb's import closure, so the deploy rule decides the restart: record it. If the
     restart was skipped because a game was live, say when the running process will pick it up (next qualifying push or
     restart) - the gate must be live before spring 2027, not tonight.
  8. GG-527: record the decision and what was built; status RESOLVED only once Part A's counting and Part B's gate are
     merged and on the VPS (show git rev-parse there). The registry flip of T4M-PROJ to DARK is NOT this block - it
     happens in a later block after the World Series ends; say so on GG-527.
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W61_1_gg527_fills_only_results.md, updated per part.

END OF BLOCK 61.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 61.2 — Verdict readiness: VPS health, GG-401 close-out, gap-log retirement, NFL first-look rehearsal

```
COMMON RULES - WAVE 61 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-08 (incl. the GG-527 decision), ADR-0070, ADR-0071. Standing
  authorizations: shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy +
  pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in ACTIVE_QUEUE.md "Needs your
  decision". A table row describing a decision is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. Demo only. No live-ledger row rewritten. No edit of an
  existing cron line. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W61_<n>.md (docs-only push).

WAVE 61.2 - VERDICT READINESS: VPS HEALTH, GG-401 CLOSE-OUT, GAP-LOG RETIREMENT, NFL FIRST-LOOK REHEARSAL.
Repo: eignacio1/prediction-market-bot.

WHY
The first pre-registered edge verdict in the project's history is the NFL first look, projected ~2026-11-02 (60
settled games per cell, EXP-037). The calibration engine runs daily at 13:49 UTC and is sealed below each cell's n. On
the day a cell crosses n, the release has to be mechanical and correct the first time - it has never run for real.
Meanwhile: the strategic window cannot SSH, so VPS liveness is unverified since Wave 60; GG-401 (NHL T3 projected-goalie
flag) is closable once NEW rows carry the flag (#188 deployed 2026-10-08 02:43 UTC, new rows only); and the live gap
log still holds 4 RESOLVED entries (GG-228, GG-300, GG-515, GG-525) that belong in the archive.

PART A - Health, GG-401, retirement (~40 min)
  1. Run CLAUDE.md Step 4 in full on the VPS and paste the outputs: T1 MLB last runs, t4-mlb is-active, T4 cycle-log
     age (cross-check against whether postseason games were live), dashboard NRestarts + oom-kills, the semantic oracle
     counts. Also: each shadow arm's newest ledger row timestamp (NFL, NHL, MLB postseason, NBA preseason) against its
     cron schedule. Any arm silent past its schedule = a finding with a GG; do not fix out of scope.
  2. GG-401: read the STORED NHL T3 shadow rows written after 2026-10-08 02:43 UTC. Every one must carry
     confirmed=False and a non-empty starter_source. Report n and pass count. All pass and n >= 1 -> RESOLVED with the
     evidence. n = 0 -> leave OPEN, state when the next T3 rows are due. Any failure -> OPEN with the failing rows.
     Check the rows, not the code path.
  3. Retire every entry in the live gap log whose Status token is RESOLVED or CLOSED-AS-ARTIFACT at run time (expected:
     GG-228, GG-300, GG-515, GG-525 - plus GG-401 if step 2 resolved it) with scripts/retire_resolved_gaps.py
     (verbatim move, never hand-edited). After: parity (headers = status lines), uniqueness check across live +
     archive, and the live OPEN count. Docs-only push.
PART B - NFL first-look rehearsal (no real cell unsealed; ~45 min)
  4. Per NFL cell (12): settled judged-eligible games now, and the engine's projected date to reach judged n from the
     remaining schedule. Confirm or move ~11-02; name any cell that cannot reach n this season. COUNTS ONLY - no score,
     Brier, P&L or calibration statistic for any sealed cell may be computed or printed.
  5. Rehearse the release end to end on a SYNTHETIC fixture cell (a test or temp dir, never real rows): crosses n ->
     daily engine run unseals it -> scores under its pre-registration -> frozen release manifest -> REPORT render ->
     Visual Dashboard Calibration section shows it. Prove which job triggers it, at what UTC time, where the report
     lands and what the operator sees. Fix any break found, with tests; PR, CI green, merge; record the deploy decision.
  6. Write 04_EXECUTION/NFL_FIRST_LOOK_RUNBOOK.md (one page): trigger, outputs and paths, what each verdict line means
     in plain English, what is and is not allowed after a look (no relabel, no parameter change, dated addenda only
     before judged data), and what the strategic window does on release day.
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W61_2_verdict_readiness_results.md, updated per part.

END OF BLOCK 61.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 61.3 — Exploratory research track: charter, isolation guard, data inventory, first NFL challenger study

```
COMMON RULES - WAVE 61 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-08 (incl. the GG-527 decision), ADR-0070, ADR-0071. Standing
  authorizations: shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy +
  pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in ACTIVE_QUEUE.md "Needs your
  decision". A table row describing a decision is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. Demo only. No live-ledger row rewritten. No edit of an
  existing cron line. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W61_<n>.md (docs-only push).

WAVE 61.3 - EXPLORATORY RESEARCH TRACK: CHARTER, ISOLATION GUARD, DATA INVENTORY, FIRST NFL CHALLENGER STUDY.
Repo: eignacio1/prediction-market-bot.

WHY
Operator horizon (2026-10-07): long stretches on edge calibration - research, wiring variants, feature extraction.
The pre-registered cells cannot be touched until their looks, and the first look (NFL, ~11-02) may well say NO -
Waves 38-44 found no edge net of cost across 14 families. When it lands, a challenger should already exist, built on
data the judged cells never see, ready to be pre-registered. That needs a research track that is structurally unable
to contaminate the frozen models, the shadow ledgers, the registry or any pre-registration. This block builds the
fence first, then does the first piece of research inside it.

PART A - The fence (~40 min)
  1. Read the existing efficiency and cost findings (do not redo them): EXP-031, T-567 efficiency gradient, EXP-032
     execution cost surface, EXP-035 + Gate 2, in 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/. Ten lines: what is
     already known about where Kalshi sports markets are and are not beatable net of cost.
  2. Create a top-level exploratory directory (pick a name that fits the repo's numbered layout and is free) with
     CHARTER.md: purpose (build challengers for pre-registered cells); reads only archives, copies and past seasons;
     NEVER reads shadow rows or any result of a sealed cell (that is reading a score below n); never writes to logs/,
     shadow or paper ledgers, the registry, 03_DECISIONS/, any PREREGISTRATION file or a calibration-engine release;
     never imports order, position, promotion or registry-mutation code; every output labelled EXPLORATORY and never
     cited as a verdict; a finding graduates only through a new dated pre-registration the operator accepts, judged on
     data dated after it.
  3. tests/test_exploratory_isolation.py: static scan of that directory's .py files - fails on a forbidden import
     (paper_trader, kalshi order/submit functions, promote_cell_status, registry mutators) or a write to a forbidden
     path. Include one negative fixture proving the test catches a violation. PR, CI green, merge (docs + test only -
     record the deploy decision anyway).
PART B - Inventory + first study (~45 min)
  4. Data inventory table: sport x market family x seasons x rows x location x validated (y/n, by what gate), for
     archived Kalshi prices and past-season outcomes/features (NFL, NHL, NBA, MLB). Copies only; read-only.
  5. NFL challenger slate: three candidate challengers to the frozen EXP-037 model (a feature, a variant, a
     recalibration), each with: data available? pre-2026 seasons only? cost to test? Rank them.
  6. Run the cheapest one as an EXPLORATORY out-of-sample comparison against the frozen EXP-037 model on pre-2026
     seasons only, priced against archived Kalshi prices where they exist (net of the EXP-032 cost model). Report
     honestly, including "no improvement". Draft - do not accept - a challenger pre-registration only if the result
     warrants one; mark it PROPOSED for the operator.
Results doc: inside the new directory, W61_3_exploratory_track_results.md, updated per part.

END OF BLOCK 61.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 61 — ISSUED 2026-10-08 ~17:30 PT · three MEDIUM blocks · first wave of the new window

| # | Block | Status | Outcome |
|---|---|---|---|
| 61.1 | GG-527 built: fills-only evidence + stand-down gate | ⬜ | — |
| 61.2 | Verdict readiness: health, GG-401, retirement, NFL rehearsal | ⬜ | — |
| 61.3 | Exploratory research track | ⬜ | — |

### ✅ WAVE 60 — CLOSED 2026-10-08 · three MEDIUM blocks (60/90-min rule held) · last wave of the Waves 52–60 window

| # | Block | Status | Outcome |
|---|---|---|---|
| 60.1 | Cohort fill truth + Monday guard | ✅ | #185; 107 of 1,952 filled; real fills -0.40/bet; GG-527 to you; GG-228 guarded |
| 60.2 | NBA engine + addenda | ✅ | #186/#188; 12 NBA cells sealed 0/150; addenda applied; GG-529/530 |
| 60.3 | Dashboard truth + gap-log hygiene | ✅ | #184/#187; NBA row, 390px fixed, hook count live; OPEN 130 |

### ✅ WAVE 59 — CLOSED 2026-10-08 ~02:05 UTC · three LARGE blocks (ran long: operator set the 60/90-min rule for Wave 60)

| # | Block | Status | Outcome |
|---|---|---|---|
| 59.1 | The backlog | ✅ | OPEN 176 → 131 re-verified (136 at close); GG-498 resolved (#183) |
| 59.2 | Calibration correctness | ✅ | #178/#181/#182; NFL look 11-02; NHL n unreachable; 1,229/1,229 settlements agree |
| 59.3 | NBA, NHL goalie, ADR-0070 | ✅ | #179/#180; goalie verdict (b); ADR-0070 ACCEPTED; GG-400 resolved |

### ✅ WAVE 58 — CLOSED 2026-10-07 ~02:45 UTC · three LARGE blocks

| # | Block | Status | Outcome |
|---|---|---|---|
| 58.1 | Arms, books, gaps | ⚠️ A–C done, D not run | GG-489, GG-490 resolved; NHL probe job live; NFL book archived; gap triage outstanding |
| 58.2 | NBA arm end to end | ⚠️ built + armed | EXP-038, frozen model, crons; rows from ~10-19 |
| 58.3 | Calibration engine | ✅ | #175; 33 cells, sealed; Calibration section live |

### ✅ WAVE 57 — CLOSED 2026-10-07 ~01:00 UTC · three terminal blocks

| # | Block | Status | Outcome |
|---|---|---|---|
| 57.1 | MLB player-hits dark | ⚠️ partial | #171 features via GH Actions (success); T1 PIPE-05 proof pending; GG-489 unregistered |
| 57.2 | MLB settle + stagger night | ✅ | #170; 128 settled; GG-472, GG-477 resolved |
| 57.3 | Truthful books | ✅ | #172; T4 placements shown; NFL book unmaintained (GG-490) |

### ✅ WAVE 56 — CLOSED 2026-10-06 ~00:30 UTC · three terminal blocks

| # | Block | Status | Outcome |
|---|---|---|---|
| 56.1 | MLB cache via GH Actions + cron stagger | ✅ | #165/#166; GG-482 resolved; stagger applied |
| 56.2 | Live Terminal decision stream + design | ✅ | #167/#169; NOW view live |
| 56.3 | Visual Dashboard ops health + design | ✅ | #168; health strip, ops, books, evidence clocks |

### ✅ WAVE 55 — CLOSED 2026-10-05 ~23:40 UTC · three terminal blocks (+55.3b)

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 55.1 | Land #159 + book 26 positions | ✅ | #159 merged; 26 booked; T1 12.44%, T4 13.45%; GG-440/450 resolved |
| 55.2 | Land #160 + Live Terminal + t4-mlb restart | ✅ | #160 merged; 24 SHADOW live; GG-451 resolved; OOM root cause GG-477 |
| 55.3 | MLB shadow source off statsapi | ⚠️→✅ | ESPN ruled out; 55.3b #164 off-box refresh, 69 MLB T1 rows; GG-482 |

### ✅ WAVE 54 — CLOSED 2026-10-05 ~07:50 UTC · three terminal blocks

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 54.1 | Final landing PR #160 | ✅ | #160 @ `5dbddb2` green + clean; SHADOW 24 on landing |
| 54.2 | Merge #158, VPS proof, arm MLB shadow | ⚠️ partial | #158/#162/#163 merged, t4-mlb never restarted; MLB cells armed, 0 rows (statsapi 406) |
| 54.3 | Kalshi-settlement resolver | ✅ | ADR-0071; #159 @ `2421c0a` green; drawdown after booking T1 12.44%, T4 13.45% |

### ✅ WAVE 53 — CLOSED 2026-10-05 ~04:30 UTC · three terminal blocks · run 10-04 evening PT

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 53.1 | Resolver VPS confirmation (GG-440) | ✅ | 406 on cache-MISS confirmed; 16 cancelled + 10 postponed-game = 0 of 26 settle; #159 @ `c9462a1` CI green |
| 53.2 | Shadow ledger + crontab audit | ✅ | 9 NHL + 12 NFL logging; 12 MLB postseason never armed (GG-453); 8 NFL T2/T3 not SHADOW on landing |
| 53.3 | GG-451 guard into #160 | ⚠️ partial | Guard on `w52/landing` @ `2365cc7`; prompt truncated at D3 — GG-452 + CI check not run; #160 `dirty` on union files |

### ✅ WAVE 52 — CLOSED 2026-10-03 22:00 UTC · one Claude Code session · all 5 done · nothing merged (verified on GitHub)

| # | Block | Status | Outcome |
|---|---|---|---|
| 52.A | Landing prep | ✅ | **PR #160** `w52/landing` @ `6f962400`, CI green, clean: #157 + 51.1 + 51.2 + NHL 9-cell SHADOW flip; suite 3649 passed. Registry on that branch: SHADOW 16. |
| 52.B | GG-432 decision PR | ✅ | **PR #158** (draft): `t4-mlb` restarts only if its import closure changed AND no MLB game live; dashboard always restarts. Yours to decide. |
| 52.C | MLB resolver (GG-440) | ✅ (root cause LIKELY) | **PR #159** (draft): statsapi 406 = Fastly IP block of the VPS (GG-084); ESPN fallback silent. Fix books only Kalshi yes/no, cancelled = skip, `--dry-run`. VPS confirmation = 53.1. |
| 52.D | NHL confirmed goalie (GG-401) | ✅ verdict (c) | Cloud egress refused every NHL source. Probe script on `w52/nhl-goalie-probe`; tonight's measurement = 53.2. |
| 52.E | Live Terminal truth | ✅ | **PR #161** on top of #160: every registry SHADOW cell shown, ledger-only cells labelled "(ledger only)", NHL settled copies no longer double-counted, GG-431 FROZEN label with true age. |
| — | New gaps | — | **GG-451 HIGH** `close_session_claim.sh` pushes HEAD to main (fix = 53.3) · **GG-452 LOW** stale dependency locks. |

### ⚠️ WAVE 51 — all 3 done · folded into 52.A

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 51.1 | Kill-switch truth | ⚠️ done, branch not merged | Verdict (d): realized drawdown **10.60%**, not tripped; dashboard's 26.63% = 10.60% realized + 16.02% stake in 17 positions already settled on Kalshi but never resolved — Kalshi cancelled 16 of them, so realized after booking is ~11–12% (GG-441, GG-450). Dashboard fix on `6cbe62f`. GG-440..442 | Merge in the landing block |
| 51.2 | NHL silent drops | ⚠️ done, branch not merged | SJ/TB/LA/NJ codes were silently dropped; fixed + abstention counters on `f822b6b` | Merge in the landing block |
| 51.3 | PR #157 merge-ready | ✅ done | PR #157 MERGEABLE, CI green (run 37151320465), head `42a0d0d`; 9 NHL cells have rows. **Dirty again by 21:05 UTC** (union-file conflict after main moved) | Re-merge main, then merge in the landing block |
| — | ~~51.3 original: land #157 + NHL SHADOW flip~~ | ❌ withdrawn | — | Needed an idle window; becomes the landing block below |

**Superseded by 52.A:** all three land as one integration PR in an idle window.

### ✅ WAVES 49–50 — CLOSED 2026-10-03 · run inside harness sessions, not from this queue

| # | Block | Status | Outcome |
|---|---|---|---|
| 49.1–49.3 | NFL + MLB shadow code, dashboard fixes, NHL pre-registration | ✅ | On main and auto-deployed by CI (VPS `077558b1`); GG-400..429 registered; crons not armed (cloud can't reach VPS) |
| 50.1 | Process fixes + GG-400..429 triage (T-636) | ⚠️ | PR #157, draft, green but conflicted — 51.3 makes it mergeable |
| 50.2 | Cleanup (T-637) | ✅ | Shadow crons ARMED; tree synced; PR #156 closed; #157 held for live games; GG-430..432 (CI restarts t4-mlb) |

### ✂️ WAVE 48 — CLOSED 2026-10-03

| # | Block | Status | Outcome |
|---|---|---|---|
| 48.1 | Land NFL + MLB shadow (T-631) | ✂️ | Stopped early at operator request; rebased only — landed later by 49.1 |
| 48.2 | Record + VPS jobs (T-632) | ✂️ | Queue + `vps_job.py` landed; detached jobs still unauthorized |
| 48.3 | Dashboards in a real browser (T-621..630) | ⚠️→✅ | Fixes on a branch; landed by 49.2 |

### ✂️ WAVE 47 — CLOSED 2026-10-02 · all three cut at ~2h → the 30-min block rule

| # | Block | Status | Outcome |
|---|---|---|---|
| 47.1 | Candles Gate 2 + Live Terminal v2 (T-615) | ✂️ | **Gate 2 PASSED 7/7** on KXMLBTOTAL; Live Terminal v2 + `/project` deployed; GG-340..356 |
| 47.2 | NFL + MLB postseason shadow (T-608 / EXP-037) | ✂️ | 24 cells built + pre-registered, ADR-0070 PROPOSED; landed later by 49.1 |
| 47.3 | NHL arm (T-607 / EXP-036) | ✅ | **First new arm flying** — model frozen, cron installed, first T3 rows |

### ✅ WAVE 46 — CLOSED 2026-10-02

| # | Block | Status | Outcome |
|---|---|---|---|
| 46.1 | Why candles failed (T-605) | ✅ | Matching rule + sparse candles; Gate 2 pre-registered |
| 46.2 | EXP-034 control arm | ⚠️ | Gate FAIL as run (runner lookback); numbers VOID; branch not merged |
| 46.3 | Shared-tree repair (T-606) | ✅ | Stale lock removed, tree synced, ADR-0067 docs landed |

### ⚠️ WAVE 45 — CLOSED 2026-10-02

| # | Block | Status | Outcome |
|---|---|---|---|
| 45.1 | Candle reconstruction Part 1 (T-604 / EXP-035) | ✅ | Gate FAILED → candle numbers VOID; GG-329..333 |
| 45.2 | EXP-034 setup | ⚠️ | Tolerance frozen; comparison not run |
| 45.3 | Record + dashboard page | ⚠️ | Queue landed; dashboard page running; tree sync blocked |

Waves 10–44: see `ACTIVE_QUEUE_ARCHIVE.md`.

---

## ⬛ OPERATOR DIRECTIVE, 2026-10-07 18:58 PT — MEDIUM BLOCKS (amends the LARGE-block directive below)

"You're making some of these tasks far too long. The terminals are coming back stating ETAs upwards of 3 hours which is
ludicrous from any one terminal to take on." Rule from Wave 60: each block is two parts, ~60-minute target, 90-minute
hard ceiling; a block whose own estimate exceeds 90 minutes does Part A only and hands Part B on. Still three blocks
per wave, still substantive - sized to finish, not to impress.

## ⬛ OPERATOR DIRECTIVE, 2026-10-06 18:10 PT — LARGE BLOCKS (supersedes the 30-minute rule below)

> *"Remember - the terminals can handle plenty of weight. You can expand the workload for each block so that we're not
> spending each wave back and forth making such incremental build progress... give each block enough that they can handle."*

Blocks are multi-part. Each part is pushed and recorded in the queue before the next, so a cut never strands work.
Still: three blocks per wave, disjoint surfaces, never a block that can't run now.

## OPERATOR DIRECTIVE, 2026-10-02 17:03 PT — TIME-BOUNDED BLOCKS (SUPERSEDED 2026-10-06)

> *"We added so many extra tasks to the windows that it was about to take over 2+ hours for each window to
> complete so I cut it short each way. I'm not letting windows run for hours on end — if there's a task that'll
> take that long, don't place it."*

> And minutes later, when a wave was first sized at ~75 minutes a block: *"Even 75 minutes is way too long —
> none of these tasks better take 75 minutes."*

**Every block is sized at about 30 minutes, hard stop at 45** — at the nearest pushed boundary, with a handoff
that names where the next session resumes. Scope is cut to fit the clock, never the reverse: one job per block,
done completely. Budget includes the one full test-suite run (~11 minutes) a block landing `src/` code needs.

**What does not belong in a window:** anything whose wall time is set by waiting rather than working. Those run
unattended on the VPS under their own authorization, and a later block reads what they produced.

---

## ⬛ WHAT 50.2 FOUND (and what this window found checking it)

- **NFL + MLB postseason shadow crons are armed.** The 33 pre-game cells now log unattended. Nothing restarted. **[Corrected 2026-10-05 by 53.2: only the 12 NFL cells were armed; MLB postseason never was — GG-453.]**
- **Who restarted t4-mlb: CI.** `deploy.yml` restarts `t4-mlb` and the dashboard on every code push to main (GG-432).
  That contradicts the standing "never restart t4-mlb" rule; the policy is yours (Needs your decision, first row).
- **The dashboard's stale panel and its 26.63% drawdown are one file** (strategic window, arithmetic):
  `paper_portfolio_mlb.json`, last written 2026-08-06 00:05Z (+58d20h = the panel's "read 58d20h ago", GG-431);
  $733.75 of $1,000 = 26.63%, past the 20% permanent kill switch.
- **The two drawdowns are not the same quantity** (strategic window, code read — 51.1 verifies): the T1 runner feeds
  the kill switch *realized* loss only (`run_mlb_paper_trade.py:670-671`); the dashboard shows
  `(initial − bankroll) / initial` (`web_dashboard.py:761`, `:1498`), which also counts stake locked in ~17 positions
  open since August. So the tile may be alarming on money that is tied up, not lost — or the kill switch may have
  missed a real breach. No capital either way (kelly 0.0).
- **PR #157 is not mergeable as it stands** (GitHub: `mergeable_state = dirty`) — 50.2's report did not say so. 51.3 makes it mergeable; it lands in a later idle window.

---

## Read this first (standing)

- **Protocol (operator, 2026-10-04):** every time this file changes, the strategic window loads it into the chat as a file card. He never has to dig through folders for it.

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Blocks are LARGE and multi-part (operator 2026-10-06)** — each part pushed and recorded before the next. Waiting is still not work.
- **Deliverable 0 in every block: confirm your base** (`git fetch`; work from current `origin/main`).
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). Never "TBD".
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and refusal text, then hand back.
- **Pre-register before scoring.** Frozen pre-registrations stay frozen. No scoring before a cell's judged n.
- **SHADOW means evaluate and log.** No order, position, paper fill, stake or `kelly_fraction` change.
- **A merge is a deployment here, and a code deployment restarts `t4-mlb`** (deploy.yml, GG-432). Until the operator
  decides GG-432: code reaches main only when no MLB game is live (Stats API shows none In Progress, T4 cycle log idle
  > 15 min, no first pitch within 60 min). Docs-only pushes are always fine.
- **Paper and shadow work is plumbing** (operator's standing framing). Real capital is his.
- **The Live Terminal and the project view move with the bot.** A block that adds a cell, ledger, source or verdict makes it visible.
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

## THE ARC — renumbered (49-50 went to landing and cleanup)

| Wave | The question it answers |
|---|---|
| **51** | *Is what the operator sees true, and is everything built actually landed?* Kill switch vs dashboard; NHL silent drops; #157 made mergeable. |
| **52** | **NHL scoring readiness** — confirmed-goalie source at T3 (GG-401), pre-registered spread cutoff (GG-404), clustered scorer (GG-407), matinee coverage (GG-405). **NBA (opens 10-20)** in ~30-minute blocks. Merge whatever 51 left on branches. |
| **53** | First looks as cells reach judged n (NFL first: 60 games ≈ late October). A **flat-stake paper ADR** for SHADOW cells — yours to accept. |
| **later** | In-play arms only where C5 / ADR-0068 shows speed is measured. Sizing only for a cell that cleared its gate and its capacity question. |

What should reorder this, and what should stop it:

- **A shadow path that reaches an order, position or sizing function** stops everything shadow until fixed.
- **A dashboard that shows a number it did not read live, or a number that is not what its label says** is a defect of the same severity.
- **A kill switch that should have fired and did not** (51.1 verdict c) stops everything until understood.
- **Per cell, the pre-registered rules decide.** RULED_OUT at judged n is a completed cell.
- **Board-survey stop condition — pre-registered in Wave 45, carried unchanged.**

---

## Queued next — not yet fired (refreshed 2026-10-08 by the incoming window; dated items wait for their date)

- **On/after 10-21 — NBA flip:** `scripts/w59_3_nba_flip_check.py` prints the `promote_cell_status` lines; flip once valid
  regular-season rows exist. Same block or next: remove the NBA preseason cron line after 10-20 (added under the new-line
  authorization; removal of a line we added).
- **After Mon 10-12 14:20 UTC — first real run of the GG-228 guard:** read `band_monitor_cron.log` for a GG-228 WARNING /
  `rebuild_<UTC>.jsonl`.
- **After the World Series — T4M-PROJ registry flip to DARK** (GG-527 (c), authorized) + **T1 MLB winter posture** (your call).
- **The day an NFL cell crosses n (~11-02):** first scored look, per 61.2's runbook.
- **Before 2027-01-31 — GG-529:** define EXP-038's date-triggered second look (your call; window will propose).
- **Exploratory track, Wave 62+:** next challengers (NHL, NBA) per 61.3's slate.
- Carried, unscheduled: board survey (needs the detached-VPS-jobs line) · Step 4 season-awareness (GG-343..345) · PIPE-08
  406s · T3 disposition (MISFILED) · branch estate · stale PRs #133/#144/#146/#149 · test-suite runtime.

---

## Needs your decision

> **AUTHORIZATION - GG-527 T4M-PROJ COHORT (operator, 2026-10-08 ~17:14 PT, choosing the window's recommendation: "(b)+(c) (Recommended)").**
> Covers: (b) every T4M-PROJ row (epoch-12 and later) counts as model-calibration evidence only; G6 sample adequacy and
> any execution or P&L claim for T4M-PROJ count CONFIRMED_FILLED rows only - computed and labelled that way in the power
> calc, governance scan, band monitor and both dashboards, from a sidecar fill-status file (no live-ledger row
> rewritten). (c) T4M-PROJ places no paper stake for any MLB game after the 2026 World Series: a code gate in the T4
> placement path, default off, re-enabled only by a new operator decision; evaluations keep logging; and, once the
> World Series has ended, T4M-PROJ's registry status goes to DARK with this decision as the reason (a later block).
> Not covered: any kelly_fraction or stake-size change, any other band or cell, T1 MLB winter posture, deleting or
> rewriting any row. Used by 61.1.

> **AUTHORIZATION - PRE-REGISTRATION ADDENDA (operator, 2026-10-07 19:03 PT: "Yes proceed with both recommendations").**
> Covers: appending four dated addenda (original text untouched), before any judged data exists: (1) EXP-037 "earliest
> 60" ordered by (start_time_utc, game_key); (2) EXP-036 bootstrap seed 20261002; (3) EXP-036 goalie: projected starter
> (last start) at every band, T3 included, rows flagged confirmed=False - W59.3 Part B text verbatim; (4) MLB: the
> climatology comparison is unavailable (no p_clim on MLB settled rows), stated with the reason. Not covered: any other
> parameter, judged n, verdict rule or look. Used by 60.2 Part B.

> **DECISION - NHL JUDGED N (operator, 2026-10-07 19:03 PT): keep EXP-036 as written** (judged n 2,473; NHL stays
> PRELIMINARY in 2026-27; the 500-game climatology check still applies). Recorded on GG-514 by 60.2 Part B.

> **AUTHORIZATION - FEATURES CRON REMOVAL (operator, 2026-10-06 18:16 PT: "Yes permission granted").** Covers:
> commenting out the ONE VPS cron line that runs `scripts/generate_mlb_features.py` at 22:30 UTC (it overwrites the
> GitHub-built feature CSV nightly with degraded output), crontab backed up first, mirrored into `deploy/`. Not
> covered: any other line. Used by 58.1 Part A5.

> **AUTHORIZATION - GG-477 CRON STAGGER (operator, 2026-10-05 16:41 PT: "Yes").** Covers: changing ONLY the minute
> field of the existing cron lines listed in `scripts/ops/gg477_cron_stagger.py` RULES, crontab backed up first, and
> mirroring those minutes into `deploy/` cron files. Not covered: any command, hour or other line. Used by 56.2.

> **OPERATOR DIRECTIVE (2026-10-05 16:41 PT):** "MLB can't go dark while games are going on." The MLB postseason
> shadow arms keep logging every game day; nothing in their data path may depend on a manual step.

> **NAMES (operator, 2026-10-05):** **Visual Dashboard** = the operational review of the whole bot (`/project`). "ERP"
> describes its purpose, not a rebuild — he likes its current look; enhance it, keep the style. **Live Terminal** = what
> the bot is actually placing / evaluating, live, full black (`/`).


GG-432, GG-440, GG-450 and postponed games were decided 2026-10-04 (DECISION_LOG 2026-10-05). Arming the MLB postseason shadow cells needs no line — the 2026-10-02 shadow-cron authorization covers new lines.

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").** Unchanged;
> used by 50.2. Not covered: any order, position, fill, stake or `kelly_fraction` change; any EXISTING cron line.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT).** Standing. Covers
> `pmbot-web-dashboard` only. Note: under today's `deploy.yml`, any code merge also restarts `t4-mlb` — see GG-432 below.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **T4M-PROJ cohort (GG-527)** | ✅ **DECIDED 2026-10-08 ~17:14 PT: (b)+(c)** — authorization line above; 61.1 builds it. | — |
| **NEW — EXP-038 second look (GG-529)** | The NBA pre-registration says "n=400 or 2027-01-31, whichever first" but never says what is scored on the date. Needs a definition before 2027-01-31; the engine scores only n=150/400 until then. | Nothing before January. |
| **Pre-registration addenda** | ✅ **DECIDED 2026-10-07 19:03 PT: yes** — authorization line above; 60.2 Part B applies them. | — |
| **NHL judged n (GG-514)** | ✅ **DECIDED 2026-10-07 19:03 PT: keep as written** — NHL PRELIMINARY all 2026-27. | — |
| **GG-432** | ✅ **DECIDED 2026-10-04: option (a), PR #158** — merged in 54.2. | — |
| **GG-450** | ✅ **DECIDED 2026-10-04:** booked at Kalshi settlement value, flagged cancelled, excluded from G6 + calibration — built in 54.3. | — |
| **GG-440** | ✅ **DECIDED 2026-10-04:** Kalshi settlement is the resolution source; statsapi/ESPN cross-check only — ADR + code in 54.3. | — |
| **NHL goalie timing (GG-401)** | Pulled from Wave 53 (timing-bound). The measurement — run `scripts/nhl_goalie_source_probe.py` at ~60/30/15 min before one slate's puck drop — fits a detached read-only VPS job (row below) instead of a terminal. | No NHL T3 score may be read. |
| **Postponed games** | ✅ **DECIDED 2026-10-04:** resolve on Kalshi's result — in 54.3. | — |
| **GG-477 cron stagger** | ✅ **AUTHORIZED 2026-10-05** — line above; 56.2 applies it. | — |
| **VPS 22:30 UTC features cron** | ✅ **AUTHORIZED 2026-10-06** — line above; 58.1 A5 removes it. | — |
| **NEW — NFL game-market paper book (GG-490)** | Old NFL paper book: no writer, no resolver, ~820 open positions on past games. The live NFL work is the EXP-037 shadow arm, which is healthy. **Recommend: retire it** — book its positions once under ADR-0071 (Kalshi settlement, backup + dry-run first), then freeze it and label it archived on both dashboards. | The Visual Dashboard keeps showing a stale book with ~820 open positions. |
| **ADR-0070 scope (GG-400)** | ✅ **DECIDED 2026-10-07:** widen to NHL + NBA, then accept — 59.3. | — |
| **NBA preseason rows** | ✅ **DECIDED 2026-10-07:** default kept — logged, labelled, excluded from judged n. | — |
| **Detached read-only VPS jobs** | Long read-only work runs unattended on the VPS through `scripts/vps_job.py`. A line naming *detached read-only VPS jobs* unlocks it. | The board survey and NFL/NHL market backtests stay blocked. |
| **T1 MLB postseason flag** | Adds `--include-postseason` to the existing T1 MLB cron line. Edits an existing line, so the shadow authorization does not cover it. | T1 player-hits stays blind for the rest of the playoffs. |
| **EXP-034** | Run its ≥2.5-hour sampler as a VPS job, or **park** it (window's recommendation). | Nothing urgent. |
| **GG-347, remaining half** | The SSH poller from 73.231.159.158 — yours? | An unexplained actor on the VPS. |
| **MLB winter** | After the World Series: stand T1/T4 MLB down, or idle all winter? | Daily false alarms in Step 4 until spring. |
| **Settlement + depth capture schedules · Polymarket KYC · odds feed · provenance allowlist · APR-0035 · ADR-0068 · ADR-0067 · 39.3 triage · ADR-0063/0064/0065/0066 · APR-0034/0036** | Unchanged. | — |

---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. An approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Push code to main while an MLB game is live (until GG-432 is decided).
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization. Do not hand-pull on the VPS.
- Add or edit a cron entry without explicit operator authorization.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the RUNNING process contains it.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.

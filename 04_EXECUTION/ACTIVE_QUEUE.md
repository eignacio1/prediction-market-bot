# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 7036e11` (2026-10-08 ~02:00 UTC, strategic window). Results docs and PRs read from GitHub; VPS facts are the Wave 59 terminals' reports.

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-515** (GG-520..524 claimed by 59.3, unused) · **T-737** · **ADR-0071** · **EXP-038** · ADR-0070 **ACCEPTED** · gap log **136 OPEN** (parity 158 = 158) |
| Registry (92 cells) | *(last counted 10-05; not re-counted this wave)* **On main and live: ACTIVE 1 · SHADOW 24** (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 64. MLB postseason game cells log rows but are not yet SHADOW in the registry. |
| Capital | **$0 real.** `kelly_fraction = 0.0` on every operating band; **T4M-PROJ places flat paper measurement stakes of min($1, max_contracts x price)** (ADR-0050). Demo venue only. SHADOW = evaluate and log. |
| Shadow arms | **NFL** 12 cells logging, first look projected **2026-11-02**. **MLB postseason** armed and logging (judged n starts 2027). **NHL** 9 cells logging; judged n unreachable this season (GG-514); no NHL T3 score may be read (GG-401). **NBA** preseason rows to a separate labelled ledger; regular season 10-20, cells flip ~10-21. |
| Open PRs | Only stale ones from Waves 30-34 (#133, #144, #146, #149). Nothing from Waves 52-59 is waiting. |
| VPS | Last deploy `58dc28c` (#183), 2026-10-08 01:47 UTC, success. t4-mlb not restarted by Wave 59 (no T4 file touched). |
| Deploy | **GG-432 resolved (#158, 2026-10-05):** a push restarts `t4-mlb` only if it changes a file t4-mlb imports AND no MLB game is live; otherwise the restart is skipped and logged. Dashboard restarts every deploy. Code can land at any hour. |

---

## ⬛ NOW — Wave 60 · three MEDIUM terminal blocks · run any time, all three in parallel

Operator 2026-10-07 18:58 PT: Wave 59 blocks ran too long (terminals quoted 3h+ ETAs). Wave 60 blocks are MEDIUM:
two parts, ~60 min target, 90 min hard ceiling, stop at a pushed boundary. Wave 60 is the last wave of this strategic
window; handoff follows its verification.

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **60.1** Is the only ACTIVE cohort real? (GG-300) + Monday overwrite guard (GG-228) | ⬜ **READY** | Kalshi demo fills/settlements (read-only GETs); `build_t4_resolved_ledger.py` | — |
| **60.2** NBA into the calibration engine (GG-513) + pre-registration addenda | ⬜ **READY** | `calibration_engine.py`, settled schema, Visual Dashboard Calibration; EXP-036/037 addenda (**authorized 19:03 PT**); GG-514 decision recorded | — |
| **60.3** Dashboard truth gaps + gap-log hygiene | ⬜ **READY** | Live Terminal NBA row, 390px overflow (GG-515); gap-log index, hook count (GG-426), severity tokens | — |

### Wave 59 results (closed 2026-10-08 ~02:05 UTC, verified on GitHub at `7036e11`)

| Block | Status | Result |
|---|---|---|
| **59.1** The backlog | ✅ **DONE** | All OPEN gaps re-verified with live evidence (an early "not re-verified" shortcut was caught and reversed in-session). **OPEN 176 → 131**; 136 at close as other blocks registered new gaps. Parity 158 = 158, no duplicate ids. GG-498 RESOLVED (#183: `deploy/cron.conf` = live crontab). GG-228's body had been overwritten by GG-226's — restored. Surfaced: **4,169 of 4,181 T4 positions never confirmed filled (GG-300)**; epoch-12 T4M-PROJ **-0.0481/bet, n=1,898**; Monday 14:20 UTC rebuild still unguarded (GG-228) → both in 60.1. |
| **59.2** Calibration correctness | ✅ **DONE** | #178/#181/#182. Projection now walks real schedules: **NFL first look 2026-11-02** (rests on one week of coverage); **NHL judged n is unreachable this season** (GG-514); MLB none until 2027. Release mechanics proven on fixtures (59 → nothing, 60 → verdict, 61 → no change; write-once, tamper-evident manifests). NHL bootstrap corrected to EXP-036 (B=10,000, per-game). GG-499 one settled-row schema; Live Terminal count now sees NHL rows. **Kalshi cross-check: 1,229 / 1,229 settlements agree** (NFL 1,100, MLB 129). Registered GG-510..515. |
| **59.3** NBA readiness, NHL goalie, ADR-0070 | ✅ **DONE** | #179/#180. Kalshi lists opening night (moneyline only); VPS dry run logs all bands. Premise "preseason rows banked" was **false** — fixed with a separate labelled ledger + one new cron line (standing authorization). NBA in `_season_state`; 10-21 flip check written. **NHL goalie verdict (b):** the API's starter flag is absent before and during play, present only after the final → no StarterProvider; amendment text written, **not applied** (your call, below). **ADR-0070 ACCEPTED**, GG-400 resolved. Unregistered gap: Feeds & Health shows no NBA row until a ledger exists → 60.3. |


### 60.1 — Is the only ACTIVE cohort real? + Monday overwrite guard

```
COMMON RULES - WAVE 60 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07: 3-hour ETAs are not acceptable). Two parts.
  If your first estimate for the whole block is over 90 minutes, say so in one line, do Part A only, and name Part B
  as the next undone part. Do not re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in ACTIVE_QUEUE.md (Status + one line) with a docs-only push.
  Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-07, ADR-0070 (ACCEPTED 10-08), ADR-0071. Standing authorizations:
  shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live-ledger write. No cron edit beyond the
  standing new-line authorization. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W60_<n>.md (docs-only push).

WAVE 60.1 - IS THE ONLY ACTIVE COHORT REAL? (GG-300) + STOP THE MONDAY OVERWRITE (GG-228). Repo: eignacio1/prediction-market-bot.

WHY
T4M-PROJ is the only ACTIVE cell and its epoch-12 clean cohort is the project's sole G6 calibration cohort. W59.1
confirmed: 4,169 of 4,181 closed T4 positions carry kalshi_order_status="submitted" (12 are "failed: HTTP 410"), nothing
ever re-polls order status, and T-571 found 731 of 765 cohort rows NOT_RETRIEVABLE per-order. So we do not know whether
those paper P&L rows correspond to orders the demo venue ever filled. W59.1 also measured epoch-12 T4M-PROJ P&L at
-0.0481/bet (n=1,898 WIN/LOSS). Separately, deploy/cron.conf:315 rebuilds logs/t4_mlb_resolved_ledger.jsonl wholesale
every Monday 14:20 UTC from closed_positions, with no guard against wiping a repair applied to the derived file (GG-228).

PART A - Fill truth for the cohort (read-only, on the VPS; ~40 min)
  1. Sample 30 of the 731 NOT_RETRIEVABLE rows with scripts/t571_verify_t4mproj_kalshi_fills.py (demo, authenticated=True
     as the script does). Tabulate the failure reasons (404, 410, other). Do not re-run all 731.
  2. Pull the demo account's full GET /portfolio/fills and GET /portfolio/settlements history (paginate to the end;
     record the earliest timestamp each endpoint returns - that is the retention horizon). Join to the cohort on
     kalshi_order_id, falling back to (ticker, side, created-time window) only where the order id is missing, and say
     how many joins used the fallback.
  3. Classify every epoch-12 T4M-PROJ closed row: CONFIRMED_FILLED / CONFIRMED_NOT_FILLED / UNVERIFIABLE (outside the
     retention horizon or no match). Report counts, and P&L per bet with a game-clustered 95% CI for (i) all rows,
     (ii) CONFIRMED_FILLED only. Counts only for any cell that is sealed; T4M-PROJ is ACTIVE, so P&L is allowed.
  4. One plain-English verdict line: what the G6 cohort can and cannot claim. Do not change the cohort definition,
     any status or any ledger - that is the operator's call. GG-300: current state + evidence; RESOLVED only if every
     row is classified CONFIRMED_*.
PART B - GG-228 guard (code only, no cron edit; ~30 min)
  In scripts/build_t4_resolved_ledger.py: before replacing the existing derived file, rebuild to a temp path and diff
  row-by-row against the current file. If any existing row would change or disappear, do NOT overwrite: write the
  rebuild beside it as <name>.rebuild_<UTC>.jsonl, log a WARNING line naming the row count that differs, exit 0. Rows
  that are only added are fine (append-only growth). Tests for: identical, append-only, changed-row, removed-row.
  Confirm whether the builder is in t4-mlb's import closure (it should not be) and record the deploy decision. PR, CI
  green, merge. GG-228 RESOLVED only once the merged code is on the VPS (show git rev-parse there); next Monday run
  is the first real exercise - say so.
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W60_1_cohort_fill_truth_results.md, updated per part.

END OF BLOCK 60.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 60.2 — NBA into the calibration engine + pre-registration addenda

```
COMMON RULES - WAVE 60 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07: 3-hour ETAs are not acceptable). Two parts.
  If your first estimate for the whole block is over 90 minutes, say so in one line, do Part A only, and name Part B
  as the next undone part. Do not re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in ACTIVE_QUEUE.md (Status + one line) with a docs-only push.
  Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-07, ADR-0070 (ACCEPTED 10-08), ADR-0071. Standing authorizations:
  shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live-ledger write. No cron edit beyond the
  standing new-line authorization. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W60_<n>.md (docs-only push).

WAVE 60.2 - NBA INTO THE CALIBRATION ENGINE + PRE-REGISTRATION ADDENDA. Repo: eignacio1/prediction-market-bot.

WHY
NBA regular season opens 2026-10-20 and the first judged NBA rows land ~10-21, but the calibration engine has no NBA
policy (GG-513), so NBA cells would be untracked or tracked under the wrong rules. W59.2 also found three holes in the
pre-registrations the engine follows: EXP-037 never defines the ordering key for "earliest 60" (GG-510; the engine
uses (start_time_utc, game_key)); EXP-036 never specifies the bootstrap seed (GG-511; the engine uses 20261002);
MLB settled rows have no p_clim (GG-512). W59.3 wrote an EXP-036 goalie amendment (projected starter at every band,
T3 included; see W59_3_nba_nhl_readiness_results.md Part B). No cell has judged data, so none of this is
results-driven. NFL's first look is projected for 2026-11-02.

PART A - NBA policy in the engine (~45 min)
  Read EXP-038 in full. Add an NBA per-sport policy to scripts/calibration_engine.py exactly as EXP-038 states it
  (looks, judged n, bootstrap B / seed / clustering, verdict rules, preseason excluded from judged n - rows with
  excluded_from_judged_n=true or from PREGAME_SHADOW_PRESEASON never count). Anything EXP-038 leaves undefined:
  list it, do not invent it; the engine refuses to emit a verdict where the rule is undefined. Wire NBA into
  load_settled via pregame_shadow/settled_schema.py. Fixture tests: preseason rows never counted; sealed below judged
  n (no score, no verdict); release at exactly judged n; one-past does not change the look. The Visual Dashboard
  Calibration section shows the NBA cells with counts and "awaiting first regular-season rows" until 10-21. PR, CI
  green, merge, record the deploy decision. GG-513 RESOLVED once the daily engine run on the VPS lists NBA cells.
PART B - Addenda (~20 min) - AUTHORIZED (operator, 2026-10-07 19:03 PT; the AUTHORIZATION - PRE-REGISTRATION ADDENDA
  blockquote in ACTIVE_QUEUE.md "Needs your decision" is the record - read it and apply exactly what it covers).
  Append as dated addenda at the end of each pre-registration file (never edit the original text): EXP-037 ordering
  key; EXP-036 seed; EXP-036 goalie amendment (W59.3 Part B text, verbatim); for GG-512, state that the MLB
  climatology comparison is unavailable and why. One DECISION_LOG entry citing the line. Close GG-510 / GG-511 /
  GG-512 with the commit. GG-401: RESOLVED only if, under EXP-036 as amended, NHL T3 rows are now judgeable AND the
  running T3 job already writes confirmed=False rows with the projected starter - check the live rows, say which.
  GG-514: record the operator decision (keep EXP-036 as written; NHL PRELIMINARY in 2026-27) in its entry and set its
  status per the log's conventions. Confirm the engine reads the amended values (seed, ordering) - no code change
  should be needed; if one is, tests + PR.
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W60_2_nba_engine_addenda_results.md, updated per part.

END OF BLOCK 60.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 60.3 — Dashboard truth gaps + gap-log hygiene

```
COMMON RULES - WAVE 60 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07: 3-hour ETAs are not acceptable). Two parts.
  If your first estimate for the whole block is over 90 minutes, say so in one line, do Part A only, and name Part B
  as the next undone part. Do not re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in ACTIVE_QUEUE.md (Status + one line) with a docs-only push.
  Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-07, ADR-0070 (ACCEPTED 10-08), ADR-0071. Standing authorizations:
  shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live-ledger write. No cron edit beyond the
  standing new-line authorization. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W60_<n>.md (docs-only push).

WAVE 60.3 - DASHBOARD TRUTH GAPS + GAP-LOG HYGIENE. Repo: eignacio1/prediction-market-bot.

WHY
Two dashboard defects found in Wave 59 and not fixed: (1) the Live Terminal's Feeds & Health tab renders NO NBA row
while no NBA ledger exists, so the "awaiting" state the API returns never reaches the screen (W59.3 Part D; never
registered as a GG); (2) the Visual Dashboard scrolls horizontally at 390px (467px wide) from a long source link in
the Calibration header (GG-515). W59.1 also noted three gap-log defects and left them: the "Gaps by Arm" index at the
top of GOVERNANCE_GAP_LOG.md is stale; the session-start governance hook prints a stale OPEN count (GG-426); two OPEN
entries carry non-severity tokens ("ADR-0052", "ledger") in their Severity field.

PART A - Dashboards (~40 min)
  Register the NBA-row defect as a GG first. Fix it: the Feeds & Health tab always renders the NBA shadow row; with no
  ledger it reads "SHADOW NBA ledgers: no data - awaiting first regular-season rows" (neutral, not red). Keep
  "Live Terminal.html" and the embedded _HTML byte-identical, as before. Fix GG-515: no horizontal scroll at 390px on
  either surface (wrap or truncate the link with the full URL in a title attribute). Tests for both. Real-browser
  before/after with scripts/browser_check_dashboard.py at 1500px and 390px: Live Terminal / and Visual Dashboard
  /project, zero console errors, page width = viewport at 390px. PR, CI green, merge, confirm pmbot-web-dashboard
  restarted on the deploy (NRestarts, ActiveEnterTimestamp) and the fix is served. Both GGs RESOLVED with that proof.
PART B - Gap-log hygiene (~25 min)
  Regenerate the "Gaps by Arm" index from the live entries (or replace it with a pointer to a generated file if a
  generator already exists - check first). Fix GG-426 at its source so the hook prints the live OPEN count computed
  the same way as CLAUDE.md Step 3; show hook output before/after. Give the two odd entries a real severity token,
  citing their own text for the choice. Parity check (headers = status lines) and gg_id_uniqueness_check.py both pass.
  Report OPEN before -> after. Content of other gap entries is not touched.
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W60_3_dashboard_gaplog_results.md, updated per part.

DESIGN BAR (both surfaces)
- Every number states where it came from and how old it is. Stale looks stale. A panel with no data says "no data".
- Colour carries meaning only: green healthy, amber stale/warning, red breach/failure, neutral otherwise.
- Readable at laptop size; usable on a phone - no horizontal scroll.
- Truthful labels: SHADOW is never shown as live trading; $0 stake said plainly.

END OF BLOCK 60.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 60 — issued 2026-10-08 ~02:05 UTC (7:05 PM PT 10-07) · three MEDIUM blocks (60/90-min rule) · last wave of this strategic window

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 60.1 | Cohort fill truth + Monday guard | ⬜ | Kalshi demo GETs; resolved-ledger builder | Every epoch-12 row classified; builder never overwrites a changed row |
| 60.2 | NBA engine + addenda | ⬜ | calibration engine; EXP-036/037 addenda (authorized 10-07 19:03 PT) | NBA cells tracked under EXP-038 before 10-21 |
| 60.3 | Dashboard truth + gap-log hygiene | ⬜ | Live Terminal, Visual Dashboard, gap log | NBA row visible; no 390px scroll; hook count = live |

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

## Queued next — not yet fired

**Landing block** — merge 52.A's PR (then 52.E's) when no MLB game is live; idle probe, Deploy, VPS HEAD, services, Live Terminal checks. **Terminal block for Wave 52's VPS-PENDING items** (NHL rows re-check, resolver VPS repro + ledger dry run, live crontab). **First NFL T1 shadow run** 5:05 PM PT tonight — read its output in that terminal block, not by watching. **NHL scoring readiness** (GG-401, GG-404, GG-405, GG-407) — before any NHL score is read. **NBA game markets.** **The board
survey** (after the history store completes — needs the detached-VPS-jobs line). **MLB winter disposition** after the World
Series. **Step 4 season-awareness** (GG-343..345). **PIPE-08 406s.** **T4M-PROJ and T3 disposition** (both MISFILED). **The
branch estate** (33+ unmerged). **Aged open paper positions** (9 T4, ~17 T1 — 51.1 reports on the T1 set). **Test-suite runtime.**

---

## Needs your decision

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

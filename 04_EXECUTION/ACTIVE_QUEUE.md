# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 1638496` (2026-10-03 22:10 UTC, strategic window). PR state and CI read live from GitHub.
VPS facts are the 50.2 cleanup terminal's report, not re-verified from here (this window has no SSH).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-482** · **ADR-0071** (ACCEPTED) · **EXP-037** · gap log **176 OPEN** |
| Registry (92 cells) | **On main and live: ACTIVE 1 · SHADOW 24** (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 64. MLB postseason game cells log rows but are not yet SHADOW in the registry. |
| Capital | **$0 real.** `kelly_fraction = 0.0` on every operating band; **T4M-PROJ places flat $1.00 paper measurement stakes** (ADR-0050). Demo venue only. SHADOW = evaluate and log. |
| NFL + MLB postseason shadow | **NFL armed and logging** (12 cells, T1/T2/T3; settle job ran, 0 final yet). **MLB postseason NOT armed** — no cron, no ledger (GG-453, found by 53.2). |
| NHL | 9 cells logging valid rows (53.2 audit, to 10-05 00:40Z); registry flip + team-code fix ride in **#160**. Never uses the confirmed goalie (GG-401) - no NHL T3 score may be read. |
| Waiting to land (all CI green, none merged) | **#160** `w52/landing` @ `6f962400` = #157 + 51.1 + 51.2 + NHL 9-cell flip (clean) · **#161** `w52/live-terminal` @ `a1bdfc05`, based on #160 · **#158** GG-432 deploy change (draft, your call) · **#159** resolver (draft; waits on your GG-450 call). #157 stays open, contained in #160. |
| VPS | HEAD `eb2d1434` (50.2). `pmbot-web-dashboard` process still on `077558b`. |
| Deploy | **GG-432 resolved (#158, 2026-10-05):** a push restarts `t4-mlb` only if it changes a file t4-mlb imports AND no MLB game is live; otherwise the restart is skipped and logged. Dashboard restarts every deploy. Code can land at any hour. |
| Live games (10-03 UTC) | MLB: NYY@TB 22:30Z · SD@MIL 00:30Z (5:30 PM PT) - **earliest code-push window ~03:30 UTC = ~8:30 PM PT**, re-checked live then. NHL regular season tonight: 7 games 23:00Z, 1 at 23:30Z, 2 at 00:00Z, 01:00Z, 2 at 02:00Z. First NFL T1 shadow run 00:05Z (5:05 PM PT). |

---

## ⬛ NOW — Wave 59 · three LARGE terminal blocks · run any time · backlog first

Operator 2026-10-07 17:26 PT: "proceed in full" — backlog gets its own block, first; ADR-0070 widened to NHL + NBA and accepted (59.3); NBA preseason default kept. This is the last wave issued by this strategic window; Wave 60 starts in a fresh window.

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **59.1** The backlog: the gap log gets true | 🔄 **IN PROGRESS** — Part A done (19 of 21 leads closed, GG-156/158 kept OPEN: no checkable evidence). OPEN: 176 -> 157. Part B batch 1 (GG-004..GG-160, 25 gaps): 0 closed, all kept OPEN with dated state. OPEN: 157 -> 157. Batch 2 (GG-161..GG-209, 25 gaps): 1 closed (GG-200), 24 kept OPEN. OPEN: 157 -> 156. Batch 3 (GG-216..GG-295, 25 gaps): 0 closed, all kept OPEN. OPEN: 156 -> 156. Batch 4 (GG-296..GG-329, 25 gaps): 3 closed (GG-305 dup of GG-230; GG-318, GG-329 resolved), 22 kept OPEN. OPEN: 156 -> 153. Batch 5 (GG-330..GG-404, 25 gaps): 2 closed (GG-343 dup of GG-309; GG-351 dup of GG-230), 23 kept OPEN. OPEN: 153 -> 151. Batch 6 (GG-405..GG-499): all kept OPEN. Part B complete. OPEN: 151 (176 start). Part C (GG-498) not done at operator direction. Part D + handoff written. | gap log + archive; 21 leads verified; all OPEN gaps classified with evidence; GG-498 deploy/ cron mirror | — |
| **59.2** Calibration correctness before the first look | ⬜ **READY** | projection fix; first-look release mechanics + report template on fixtures; one settled-row schema (GG-499); Live Terminal settled count; Kalshi settlement cross-check (GG-487) | — |
| **59.3** NBA opening-night readiness + NHL goalie verdict + ADR-0070 | ⬜ **READY** | NBA dry-run + season state; NHL probe verdict (StarterProvider if (a)); ADR-0070 widened then accepted; GG-400 | — |

### Wave 58 results (closed, verified on GitHub)

| Block | Status | Result |
|---|---|---|
| **58.1** Arms, books, gaps | ⚠️ **A–C DONE, D not run** | **A:** MLB player-hits back — GG-489 RESOLVED; the 22:30 UTC features cron line commented out (authorized; diff = one line). **B:** NHL goalie probe live as a scheduled GitHub job → branch `data/nhl-goalie-probe`, stops itself 10-14 (#173). **C:** NFL game-market book booked under ADR-0071, frozen, ARCHIVED on both dashboards; GG-490 RESOLVED; 4 positions stay open until their games settle (10-08, 10-11) (#177). **D (gap triage) not done** — unverified leads saved in `RESULTS_SUMMARIES/W58_1_triage_leads/` (20 possibly fixed, 1 possible duplicate). Gap log still **176 OPEN**. |
| **58.2** NBA arm | ⚠️ **PARTIAL — built, armed, waiting for games** | EXP-038 pre-registered **before** any model existed; frozen model `nba_pregame_v1` (hash recorded); ESPN ingest, forecaster, settlement, runner; registry cells (NOT_IMPLEMENTED until they log); cron armed; dashboards wired (#174, #176). Preseason rows banked but **excluded from judged n** (pre-registration default). First real rows ~10-19; then flip cells to SHADOW. |
| **58.3** Calibration engine | ✅ **DONE** | #175: one engine, every cell under its own pre-registration; sealed cells provably cannot emit a score; Calibration section on the Visual Dashboard; daily run 13:49 UTC. **33 cells tracked, 0 at a look.** NFL projected first look shows **10-14 — suspect**: 15 of 60 games per cell after one NFL week implies ~3 more weeks (~10-27). |

### 59.1 — The backlog

```
COMMON RULES - WAVE 59 (read first; they bind this block)
- Size: this is a LARGE block (operator 2026-10-06: "the terminals can handle plenty of weight"). Work the
  deliverables in order. After EACH one: push it, and update this block's row in ACTIVE_QUEUE.md (Status + one line)
  with a docs-only push. If you must stop (context ~60%, or a blocker), stop at a pushed boundary and write the
  handoff naming the next undone deliverable. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY its own PRs. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 (both entries) and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- Crontab: all three Wave 59 blocks may add lines. Re-read the crontab immediately before writing, back it up, add
  ONLY your own lines inside your own marked BEGIN/END block, never reinstall or edit another block, and diff after:
  every pre-existing line must be byte-identical. Mirror your block into deploy/.
- The shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md) are edited by all three blocks: fetch and
  rebase right before each push; edit only your own entries/rows.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
  Note: kelly_fraction is 0 on every operating band, but T4M-PROJ places FLAT $1.00 paper measurement stakes by
  design (ADR-0050). Those are real paper positions, not a defect.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W59_<n>.md
  (docs-only push to main).


WAVE 59.1 - THE BACKLOG, FIRST AND ONLY: THE GAP LOG GETS TRUE. Repo: eignacio1/prediction-market-bot.

WHY
176 gaps are OPEN and the number only grows: triage has been the last part of a block and got cut, wave after wave.
This block does nothing else. It also matters for calibration: the 58.3 engine treats an unreadable or open gap as
open, so a stale log can keep cells sealed that should not be. 58.1 left unverified leads in
05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W58_1_triage_leads/ (about 20 "fixed", 1 duplicate GG-473 -> GG-430) - they
are LEADS, produced without verification.

RULES FOR EVERY GAP
- Classify with evidence you produced in this session (code at origin/main, tests, GitHub, VPS read-only, logs):
  (i) FIXED - verified now; RESOLVED with one evidence line (commit/PR + how you checked it).
  (ii) DUPLICATE - CLOSED-AS-DUPLICATE pointing at the surviving gap; merge any unique detail into it.
  (iii) SUPERSEDED - name the ADR/decision/later gap that made it moot.
  (iv) STILL OPEN - keep it; add a dated one-line "current state" and, where obvious, the smallest next action.
- Never close on a document's say-so. "A handoff says it was fixed" is a lead, not evidence.
- Follow the log's own format and rules: one structured Status line per entry; RESOLVED / CLOSED entries move
  VERBATIM to GOVERNANCE_GAP_LOG_ARCHIVE.md; scripts/lib/gg_id_uniqueness_check.py and the header/status parity check
  must pass after every batch.
- Register GG-495..497 only if the defect is real (58.2 reserved them for: the Live Terminal `_shadow` settled count
  reads `outcome` while settled rows carry `y`); 59.2 fixes it - you only register or release the numbers.

PART A - The 21 leads from W58_1_triage_leads: verify each; classify. Push.
PART B - All remaining OPEN gaps, oldest first, in batches of ~25: classify; one commit per batch; push each batch;
         update this block's queue row with "OPEN: <before> -> <now>" after each batch.
PART C - GG-498 (deploy/cron.conf does not mirror the live crontab): make deploy/ match the live crontab exactly
         (VPS read-only `crontab -l` as the source of truth; no crontab edits), PR, CI green, merge; RESOLVED.
PART D - Report in 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W59_1_backlog_results.md: OPEN before -> after; counts per
         class; the 15 most important still-open gaps, one line each, ranked by what they block (scores, data, ops);
         any gap that needs an operator decision, one line each. Docs-only push.

If you run out of room, stop at a pushed batch boundary: the handoff names the next gap id to start from.

END OF BLOCK 59.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 59.2 — Calibration correctness before the first look

```
COMMON RULES - WAVE 59 (read first; they bind this block)
- Size: this is a LARGE block (operator 2026-10-06: "the terminals can handle plenty of weight"). Work the
  deliverables in order. After EACH one: push it, and update this block's row in ACTIVE_QUEUE.md (Status + one line)
  with a docs-only push. If you must stop (context ~60%, or a blocker), stop at a pushed boundary and write the
  handoff naming the next undone deliverable. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY its own PRs. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 (both entries) and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- Crontab: all three Wave 59 blocks may add lines. Re-read the crontab immediately before writing, back it up, add
  ONLY your own lines inside your own marked BEGIN/END block, never reinstall or edit another block, and diff after:
  every pre-existing line must be byte-identical. Mirror your block into deploy/.
- The shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md) are edited by all three blocks: fetch and
  rebase right before each push; edit only your own entries/rows.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
  Note: kelly_fraction is 0 on every operating band, but T4M-PROJ places FLAT $1.00 paper measurement stakes by
  design (ADR-0050). Those are real paper positions, not a defect.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W59_<n>.md
  (docs-only push to main).


WAVE 59.2 - CALIBRATION CORRECTNESS BEFORE THE FIRST LOOK: PROJECTION, RELEASE MECHANICS, SETTLEMENT TRUTH.
Repo: eignacio1/prediction-market-bot.

WHY
The 58.3 calibration engine is live (33 cells tracked, 0 at a look). Before the first cell crosses its judged n, the
machinery must be right, because a wrong release or a wrong outcome cannot be un-seen. Known problems: (1) the NFL
first-look projection reads 2026-10-14, but NFL cells sit at 15 of 60 settled games after one NFL week - about one
slate per week implies ~3 more weeks; (2) settled-row schemas differ by sport (GG-499: NHL lacks game_key/p_clim, MLB
lacks p_clim, MLB T1 has no settled file); (3) the Live Terminal's shadow panel counts settled rows from `outcome`
while settled rows carry `y` (58.2 note; 59.1 registers it); (4) MLB shadow outcomes come from the games cache's final
scores, not Kalshi's settlement (GG-487 asks for a cross-check). The pre-registration rules are unchanged: NO score is
read for a cell below its judged n, by you or by anything you build.

PART A - Projection: rebuild the first-look projection from each sport's real schedule (games per week remaining for
  the teams/markets in the cell, not a linear rate from the last day). Tests on fixtures. Report each cell's corrected
  date. Visual Dashboard shows the corrected dates.
PART B - Release mechanics: per EXP-037, the first look scores exactly the earliest 60 settled games per cell (check
  the pre-registration's exact wording - first games by date, game-cluster CI, which bootstrap seed). Prove on
  fixtures: at 59 games the cell emits nothing; at 60 it emits exactly the pre-registered verdict fields computed on
  those 60 games; game 61 does not change the first look. Produce a full first-look REPORT on synthetic data in the
  exact format the real one will have (per cell: n, delta-Brier vs market and vs climatology with CI, verdict
  RULED_OUT / SHADOW-continue / pass per the pre-registration). This is the template the real first look will fill.
PART C - Settled-row truth: one schema for settled rows across NFL / NHL / MLB (GG-499) without rewriting any raw
  ledger - normalise at read time or in the settle step for new rows, and back-fill only derived settled/ copies from
  the raw ledgers (GG-228: provenance first). Fix the Live Terminal settled count (`outcome` vs `y`). Tests.
PART D - Settlement cross-check (GG-487): for every settled MLB and NFL shadow row so far, compare the outcome the
  settle step assigned (from final scores) with Kalshi's own settlement for that market. Report agreements,
  disagreements, cancelled/void markets. Any disagreement: register it and stop - do not change outcomes here.
PART E - PRs as you go, CI green, merged (record each deploy's t4-mlb decision). Results doc
  05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W59_2_calibration_correctness_results.md, updated per part.

DESIGN BAR (both surfaces; the operator gave full creative latitude and wants a finished product, not a mockup)
- Every number states where it came from and how old it is. Stale data looks stale (dimmed + age), never live.
  A panel with no data says "no data" - it never shows zeros or placeholders as if real.
- Hierarchy first: the one-glance answer at the top ("is the bot healthy, what is it doing right now"), detail below.
- Colour carries meaning only: green = healthy/positive edge, amber = stale/warning, red = breach/failure, neutral
  otherwise. No decorative colour. Tabular (monospace) numerals so columns line up.
- Dense but calm: consistent spacing, aligned columns, short labels, no walls of text, nothing that moves unless data
  moved. Readable at laptop size; usable on a phone.
- Truthful labels over pretty ones: SHADOW is never shown as live trading; $0 stake is said plainly.
- Verify in a real browser (scripts/browser_check_dashboard.py exists): before/after screenshots in the results doc.

END OF BLOCK 59.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 59.3 — NBA readiness + NHL goalie verdict + ADR-0070

```
COMMON RULES - WAVE 59 (read first; they bind this block)
- Size: this is a LARGE block (operator 2026-10-06: "the terminals can handle plenty of weight"). Work the
  deliverables in order. After EACH one: push it, and update this block's row in ACTIVE_QUEUE.md (Status + one line)
  with a docs-only push. If you must stop (context ~60%, or a blocker), stop at a pushed boundary and write the
  handoff naming the next undone deliverable. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY its own PRs. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 (both entries) and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- Crontab: all three Wave 59 blocks may add lines. Re-read the crontab immediately before writing, back it up, add
  ONLY your own lines inside your own marked BEGIN/END block, never reinstall or edit another block, and diff after:
  every pre-existing line must be byte-identical. Mirror your block into deploy/.
- The shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md) are edited by all three blocks: fetch and
  rebase right before each push; edit only your own entries/rows.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
  Note: kelly_fraction is 0 on every operating band, but T4M-PROJ places FLAT $1.00 paper measurement stakes by
  design (ADR-0050). Those are real paper positions, not a defect.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W59_<n>.md
  (docs-only push to main).


WAVE 59.3 - NBA OPENING-NIGHT READINESS, NHL GOALIE VERDICT, ADR-0070 WIDENED AND ACCEPTED. Repo: eignacio1/prediction-market-bot.

WHY
NBA's regular season opens 2026-10-20; 58.2 built and armed the arm (EXP-038, frozen nba_pregame_v1), but nothing yet
proves it will log on opening night, and the Live Terminal has no NBA season state. NHL: every NHL T3 score is blocked
on GG-401 (confirmed starting goalie); 58.1 started a scheduled probe writing to branch data/nhl-goalie-probe until
2026-10-14. Operator, 2026-10-07 ("proceed in full", DECISION_LOG): widen ADR-0070 to the NHL and NBA shadow models and
accept it; NBA preseason rows stay excluded from judged n.

PART A - NBA readiness (no waiting): Kalshi - are opening-night (10-20) and first-week NBA game markets listed yet?
  Dry-run the NBA runner against them on the VPS (exact cron command, dry-run or a scratch ledger dir - not the live
  ledger) and show what each band would log. Confirm every NBA cron line fires at a time that catches T1/T2/T3 for a
  typical 7-10 PM ET slate. Confirm preseason rows are being banked and labelled "excluded from judged n". Add NBA to
  the Live Terminal's season state (`_season_state` in web_dashboard.py). Write the exact one-line check a later block
  runs on 10-21 to flip the NBA cells to SHADOW (promote_cell_status, superseding_reference="EXP-038") once valid
  rows exist - do not flip them now.
PART B - NHL goalie verdict from whatever the probe has collected (read data/nhl-goalie-probe). If >= 2 slates of
  readings at >= 15 minutes before puck drop: give the verdict (a) API flags the starter in time in k of n games /
  (b) it does not / (c) cannot tell, per the W52_D results doc. If (a): implement the StarterProvider for the T3 run
  exactly as EXP-036 promised (that is compliance with the pre-registration, not a parameter change), tests, PR, merge;
  GG-401 RESOLVED only when the running T3 job uses it. If (b): write the exact pre-registration amendment for the
  operator and stop. If too few slates: interim note and the date the verdict becomes possible. Read no NHL score.
PART C - ADR-0070: widen its scope to the EXP-036 NHL and EXP-038 NBA shadow models (same deviation from ADR-0004;
  shadow only - authorizes no order, position, sizing or CellStatus beyond SHADOW), then mark it ACCEPTED citing the
  operator's 2026-10-07 decision. ADRs are immutable once accepted - widen BEFORE accepting, in one commit sequence.
  GG-400 -> RESOLVED with the commit.
PART D - PRs as you go, CI green, merged (record each deploy's t4-mlb decision). Results doc
  05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W59_3_nba_nhl_readiness_results.md, updated per part.
STATUS (2026-10-08, W59.3): PARTS A, B, C, D DONE and merged (#179, #180; t4-mlb decision not_needed both). Part B verdict (b); amendment awaits operator. Outstanding: before/after browser screenshots of the NBA Live Terminal row (needs post-deploy browser_check_dashboard.py run); 10-21 flip via scripts/w59_3_nba_flip_check.py.

DESIGN BAR (both surfaces; the operator gave full creative latitude and wants a finished product, not a mockup)
- Every number states where it came from and how old it is. Stale data looks stale (dimmed + age), never live.
  A panel with no data says "no data" - it never shows zeros or placeholders as if real.
- Hierarchy first: the one-glance answer at the top ("is the bot healthy, what is it doing right now"), detail below.
- Colour carries meaning only: green = healthy/positive edge, amber = stale/warning, red = breach/failure, neutral
  otherwise. No decorative colour. Tabular (monospace) numerals so columns line up.
- Dense but calm: consistent spacing, aligned columns, short labels, no walls of text, nothing that moves unless data
  moved. Readable at laptop size; usable on a phone.
- Truthful labels over pretty ones: SHADOW is never shown as live trading; $0 stake is said plainly.
- Verify in a real browser (scripts/browser_check_dashboard.py exists): before/after screenshots in the results doc.

END OF BLOCK 59.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 59 — issued 2026-10-08 ~00:35 UTC (5:35 PM PT 10-07) · three LARGE blocks · last wave of this strategic window

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 59.1 | The backlog | ⬜ | gap log | OPEN count down, every change with evidence | [Corrective pass complete: all OPEN re-verified; OPEN 176 -> 131; 0 unverified; Part C pending operator permission]
| 59.2 | Calibration correctness | ⬜ | engine, settle schema, Live Terminal count, cross-check | Release proven on fixtures; projection corrected |
| 59.3 | NBA readiness, NHL verdict, ADR-0070 | ⬜ | NBA runner/dashboards, NHL T3, ADR | NBA proven ready for 10-20; ADR-0070 ACCEPTED |

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
| **ADR-0070** | Model-class deviation for NFL/MLB shadow models. **As written it does not cover NHL** (GG-400): widen it while still PROPOSED, or accept that GG-400 stays open. | Nothing until the flat-stake question. |
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

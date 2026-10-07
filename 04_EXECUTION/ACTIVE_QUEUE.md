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

## ⬛ NOW — Wave 58 · three terminal blocks · run any time · evidence-first

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **58.1** Prove MLB player-hits is back + 57.1 loose ends | ⬜ **READY — first** | VPS reads + one hand run; GG-489; 22:30 cron line ONLY with your authorization line | — |
| **58.2** NBA game markets step 1 (before 10-20) | ⬜ **READY** | Kalshi discovery; registry NBA game cells (NOT_IMPLEMENTED); pre-registration doc | — |
| **58.3** NHL goalie timing via scheduled GitHub job (GG-401) | ⬜ **READY** | probe script + workflow; data branch `data/nhl-goalie-probe` | — |

Disjoint surfaces. 58.2 changes the registry (in t4-mlb's import closure — the deploy decides the restart). **Wave 59 (queued):** NFL first-look scoring code dry-run on fixtures before NFL reaches judged n (~late Oct); NBA step 2 (frozen model); NHL goalie verdict from 58.3's data; NFL game-market book retirement (GG-490, your call).

### Wave 57 results (closed, verified on GitHub)

| Block | Status | Result |
|---|---|---|
| **57.1** MLB player-hits dark | ⚠️ **PARTIAL** | Root cause: statsapi 406s the VPS on every endpoint, AND the 22:30 UTC features cron never fetched postseason games (regular season ended 09-27, so the 7-day halt fired on genuinely stale data). Fix #171 merged: features regenerate on a GitHub runner twice daily (23:17, 10:17 UTC), gated on the unchanged data contract + >= 300 players; first run **success** 00:55 UTC 10-07. **Not yet proven:** the 11:00 UTC T1 run passing PIPE-05. GG-489 claimed but not registered. The VPS's own 22:30 features cron still overwrites the file daily with degraded output (121 of ~575 players) — the 23:17 run re-asserts before T1, but that line should go (your call). |
| **57.2** MLB shadow settle + stagger night | ✅ **DONE** | #170 merged: MLB settle outcome join, **128 settled rows**, daily cron at 11:41 UTC. **GG-472 and GG-477 RESOLVED** (first night after the stagger clean; n=1). T1 cells settle 0 so far — their games aren't final yet. Settle uses the games cache's final scores; GG-487 registers a Kalshi cross-check. |
| **57.3** Truthful books | ✅ **DONE** | #172 merged: Live Terminal shows T4M-PROJ paper placements separate from the $0 shadow stream; blank rows hidden; phone bar fixed; C4 tile reads limits (GG-491 resolved). **NFL game-market paper book: unmaintained** — no writer or resolver cron, ~820 past-date open positions (GG-490). T4 stakes 0.05–1.00 are **intended**: ADR-0050's contract cap (min($1, max contracts × price)). |

### 58.1 — Prove MLB player-hits is back

```
COMMON RULES - WAVE 58 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY the PR(s) named in it. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 (both entries) and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
  Note: kelly_fraction is 0 on every operating band, but T4M-PROJ places FLAT $1.00 paper measurement stakes by
  design (ADR-0050). Those are real paper positions, not a defect.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W58_<n>.md
  (docs-only push to main).

WAVE 58.1 - PROVE MLB PLAYER-HITS IS BACK, AND CLOSE 57.1's LOOSE ENDS. Repo: eignacio1/prediction-market-bot.

WHY
Operator directive: "MLB can't go dark while games are going on." 57.1 found the T1 MLB player-hits arm halting on
a stale feature CSV (statsapi 406s the VPS; the VPS's 22:30 UTC features cron never fetched postseason games). PR #171
moved feature generation to .github/workflows/mlb_features_sync.yml (23:17 + 10:17 UTC, gated on the unchanged
MLB_FEATURE_CSV_CONTRACT + >= 300 players); its first run succeeded 2026-10-07 00:55 UTC. Not yet done: proof that T1
passes PIPE-05, GG-489 registration, the GG-072 consumer check, and the VPS 22:30 cron that still overwrites the good
file nightly with degraded output (121 of ~575 players).

D0 - Worktree w58-mlb-hits-proof; claim "W58.1 STANDARD - MLB player-hits proof + 57.1 loose ends". Register GG-489
     in GOVERNANCE_GAP_LOG.md first (57.1 claimed it but never registered it; check the number is still free).
D1 - VPS read-only: the feature CSV on disk - max game_date, player count, blank-column share, file time - and which
     writer produced it last (GitHub job or the 22:30 cron). Latest mlb_features_sync run result.
D2 - Run the T1 MLB paper cron once by hand with its exact cron command (kelly 0: no T1 bets expected). It must pass
     PIPE-05 and log evaluations. Record players matched and evaluation rows per player-hits cell (T1, T2, T3), and
     when T2/T3 last wrote.
D3 - GG-072 consumer rule: run_mlb_pregame.py (PIPE-06pre) enforces the same contract - check its latest log for the
     same staleness HALT; if it halted, re-run it once by hand if its window is still open. Record each consumer's
     disposition in GG-489.
D4 - The 22:30 UTC features cron line: ONLY if ACTIVE_QUEUE.md shows "AUTHORIZATION - FEATURES CRON REMOVAL", back up
     the crontab, comment out that one line (do not delete; note the GG), diff shows exactly one changed line. Without
     that line, leave it and report.
D5 - GG-489 RESOLVED only with D2's evidence. Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W58_1_mlb_hits_proof_results.md.
     Docs-only push to main.

END OF BLOCK 58.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 58.2 — NBA game markets step 1

```
COMMON RULES - WAVE 58 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY the PR(s) named in it. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 (both entries) and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
  Note: kelly_fraction is 0 on every operating band, but T4M-PROJ places FLAT $1.00 paper measurement stakes by
  design (ADR-0050). Those are real paper positions, not a defect.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W58_<n>.md
  (docs-only push to main).

WAVE 58.2 - NBA GAME MARKETS, STEP 1: KALSHI DISCOVERY + REGISTRY CELLS + PRE-REGISTRATION (before the 10-20 open).
Repo: eignacio1/prediction-market-bot.

WHY
The NBA season opens 2026-10-20. The registry has only NBA_PLAYER_POINTS (DARK). The coverage target covers the
standard mechanisms (moneyline, spread, game total, team total) across bands, pre-game first (operator 2026-09-30).
NFL (EXP-037) and NHL (EXP-036) already went this way: pregame_shadow framework (runner, ledger, settlement, scoring),
a frozen model, a pre-registration written BEFORE any data is scored. This block does step 1 only; the model and the
shadow arm are later blocks. Everything here is shadow-only: no order, no stake, no kelly.

D0 - Worktree w58-nba-step1; claim "W58.2 STANDARD - NBA game markets step 1 (discovery, cells, pre-registration)",
     include one EXP number in the range.
D1 - Kalshi discovery (read-only, demo/public endpoints): which NBA game-market series exist (moneyline, spread,
     total, team total - names, ticker grammar, sample tickers, how team codes are written - remember the NHL
     2-letter-code drop, GG-403), and whether 2026-27 regular-season markets are listed yet. Record exact series ids.
D2 - Registry: add the NBA game MarketTypes and their cells (T1, T2, T3 at least) as NOT_IMPLEMENTED, with series
     tickers and ticker grammar, following how the NFL/NHL types were added (read their commits). Tests, including
     parsing real sample tickers from D1 with every team code.
D3 - Pre-registration doc 05_RESEARCH_EXPERIMENTS/EXP0xx_NBA_PREGAME_SHADOW_PREREGISTRATION_<date>.md, modelled on
     EXP037 NFL: cells, model class and features (and its ADR-0004 / ADR-0070 standing), training data source and
     window, bands and run times, judged n per cell, scoring rule, stop conditions, what counts as a pass. Written now,
     before any NBA data is scored. Flag anything that needs an operator decision instead of deciding it.
D4 - PR (registry + tests), CI green, merge (registry is in t4-mlb's import closure: record the deploy's t4-mlb
     decision). Pre-registration doc docs-only to main. Results doc
     05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W58_2_nba_step1_results.md with the step-2/3 plan sized as ~30-min blocks.

END OF BLOCK 58.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 58.3 — NHL goalie timing via scheduled GitHub job

```
COMMON RULES - WAVE 58 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY the PR(s) named in it. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 (both entries) and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
  Note: kelly_fraction is 0 on every operating band, but T4M-PROJ places FLAT $1.00 paper measurement stakes by
  design (ADR-0050). Those are real paper positions, not a defect.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W58_<n>.md
  (docs-only push to main).

WAVE 58.3 - NHL CONFIRMED GOALIE: MEASURE IT WITH A SCHEDULED GITHUB JOB, NOT A WAITING TERMINAL (GG-401).
Repo: eignacio1/prediction-market-bot.

WHY
EXP-036 promises the NHL T3 run uses the confirmed starting goalie; every NHL band uses a projected one, so no NHL T3
score may be read until this is settled (GG-401). 52.D/53 could not measure when the official NHL API names the
starter: it needs probes at ~60, 30 and 15 minutes before puck drop, and the operator does not run timing blocks.
A scheduled GitHub Actions job can do the waiting: scripts/nhl_goalie_source_probe.py (branch w52/nhl-goalie-probe,
one-shot, read-only, api-web.nhle.com) run on a schedule, results committed to the repo for a later block to read.

D0 - Worktree w58-nhl-goalie-actions; claim "W58.3 STANDARD - NHL goalie timing via scheduled GH Actions (GG-401)".
D1 - Bring the probe script + its test from w52/nhl-goalie-probe onto a fresh branch from main. Read GG-401, the W52_D
     results doc, deploy/cron.nhl_shadow (the real T3 run times) and the probe's output format.
D2 - New .github/workflows/nhl_goalie_probe.yml: schedule every 10 minutes across the NHL evening window (UTC hours
     that cover typical puck drops), plus workflow_dispatch. Each run appends the probe's JSONL to one file on a
     dedicated branch data/nhl-goalie-probe - NEVER main (a commit every 10 minutes on main would collide with every
     session's claim and handoff pushes). It must STOP on its own: an end date 7 days out written into the workflow. Read-only against the
     NHL API; no VPS access; no secrets beyond what it needs.
D3 - PR, CI green, merge (workflow + scripts/: record the t4-mlb decision). Trigger it once by workflow_dispatch and
     confirm one appended record. Do NOT read NHL scores. Do NOT decide the verdict - a later block reads >= 2 slates.
D4 - Note on GG-401 (status unchanged): where the data accrues, when it stops, and the verdict rule from W52_D
     ((a) starter flagged >= 15 min pre-start in k of n games / (b) not / (c) cannot tell). Results doc
     05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W58_3_nhl_goalie_actions_results.md. Docs-only push to main.

END OF BLOCK 58.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 58 — issued 2026-10-07 ~01:15 UTC (6:15 PM PT 10-06) · three terminal blocks

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 58.1 | MLB player-hits proof + loose ends | ⬜ | VPS reads, one hand run, GG-489 | T1 passes PIPE-05 and logs evaluations |
| 58.2 | NBA step 1 | ⬜ | registry, pre-registration | Cells NOT_IMPLEMENTED; pre-reg written before any data |
| 58.3 | NHL goalie timing via GH job | ⬜ | workflow, data branch | Job appends records, stops itself in 7 days |

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

## ⬛ OPERATOR DIRECTIVE, 2026-10-02 17:03 PT — TIME-BOUNDED BLOCKS

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
- **Every block: ~30 minutes, hard stop at 45.** One job per block, done completely. Waiting is not work.
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
| **NEW — VPS 22:30 UTC features cron** | It fetches from statsapi (blocked) and overwrites the feature file daily with degraded output (121 of ~575 players). The GitHub job at 23:17 UTC puts the good file back before the 11:00 T1 run, so nothing breaks today — but it's a nightly fight. **Recommend: remove that one cron line.** Edits an existing line, so it needs your yes. | A bad file sits on the VPS 22:30–23:17 UTC nightly; one missed GitHub run = T1 on bad data. |
| **NEW — NFL game-market paper book (GG-490)** | Old NFL paper book: no writer, no resolver, ~820 open positions on past games. The live NFL work is the EXP-037 shadow arm, which is healthy. **Recommend: retire it** — book its positions once under ADR-0071 (Kalshi settlement, backup + dry-run first), then freeze it and label it archived on both dashboards. | The Visual Dashboard keeps showing a stale book with ~820 open positions. |
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

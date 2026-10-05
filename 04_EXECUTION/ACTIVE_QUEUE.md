# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 1638496` (2026-10-03 22:10 UTC, strategic window). PR state and CI read live from GitHub.
VPS facts are the 50.2 cleanup terminal's report, not re-verified from here (this window has no SSH).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-482** · **ADR-0071** (ACCEPTED) · **EXP-037** · gap log **176 OPEN** |
| Registry (92 cells) | **On main and live: ACTIVE 1 · SHADOW 24** (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 64. MLB postseason game cells log rows but are not yet SHADOW in the registry. |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| NFL + MLB postseason shadow | **NFL armed and logging** (12 cells, T1/T2/T3; settle job ran, 0 final yet). **MLB postseason NOT armed** — no cron, no ledger (GG-453, found by 53.2). |
| NHL | 9 cells logging valid rows (53.2 audit, to 10-05 00:40Z); registry flip + team-code fix ride in **#160**. Never uses the confirmed goalie (GG-401) - no NHL T3 score may be read. |
| Waiting to land (all CI green, none merged) | **#160** `w52/landing` @ `6f962400` = #157 + 51.1 + 51.2 + NHL 9-cell flip (clean) · **#161** `w52/live-terminal` @ `a1bdfc05`, based on #160 · **#158** GG-432 deploy change (draft, your call) · **#159** resolver (draft; waits on your GG-450 call). #157 stays open, contained in #160. |
| VPS | HEAD `eb2d1434` (50.2). `pmbot-web-dashboard` process still on `077558b`. |
| Deploy | **GG-432 resolved (#158, 2026-10-05):** a push restarts `t4-mlb` only if it changes a file t4-mlb imports AND no MLB game is live; otherwise the restart is skipped and logged. Dashboard restarts every deploy. Code can land at any hour. |
| Live games (10-03 UTC) | MLB: NYY@TB 22:30Z · SD@MIL 00:30Z (5:30 PM PT) - **earliest code-push window ~03:30 UTC = ~8:30 PM PT**, re-checked live then. NHL regular season tonight: 7 games 23:00Z, 1 at 23:30Z, 2 at 00:00Z, 01:00Z, 2 at 02:00Z. First NFL T1 shadow run 00:05Z (5:05 PM PT). |

---

## ⬛ NOW — Wave 56 · three terminal blocks · run any time

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **56.1** MLB games cache via GitHub Actions (GG-482) | ⬜ **READY — first** | new workflow `mlb_games_cache_sync.yml` | — |
| **56.2** Apply the cron stagger (GG-477) | ⬜ **READY — needs your authorization line below** | VPS crontab (minute fields only); `deploy/` cron files | — |
| **56.3** MLB shadow settlement (GG-472) + Live Terminal check | ⬜ **READY** | MLB settle path; settled/ copies; dashboard read | — |

**56.1 first:** the MLB games cache was last synced ~2026-10-05 22:57 UTC and the runner refuses it after 26h, so the 12 MLB cells go dark around **6 PM PT Tue 10-06** unless 56.1 lands. 56.2 owns the crontab this wave; 56.3 adds its settle line to the conf only (armed next wave).

### Wave 55 results (closed, verified on GitHub)

| Block | Status | Result |
|---|---|---|
| **55.1** Land #159 + book 26 positions | ✅ DONE | #159 merged. **26 stuck positions booked live per ADR-0071**, backups first. T1 realized drawdown **12.44%**, T4M-PROJ **13.45%** — under 20%. GG-440, GG-450 RESOLVED. |
| **55.2** Land #160 + Live Terminal + t4-mlb restart | ✅ DONE | #160 merged (Waves 51-53 + #157). **24 SHADOW cells live** on the running dashboard. GG-451 RESOLVED. t4-mlb restarted once on this merge — by design (registry is in its import closure, no game live). The 10-05 01:31 UTC self-restart was a **host-wide OOM kill** from ~6 crons starting on the same minute (GG-477): 2 GB swap added; the stagger fix was staged but not applied (needs your line). |
| **55.3** MLB shadow off statsapi | ⚠️ BLOCKED → **55.3b DONE** | ESPN can't supply the starting-pitcher ids the frozen model reads, so no substitution. Instead the cache is refreshed off the VPS and synced up (#164): **69 MLB T1 shadow rows written.** Depends on a daily sync that currently needs the Mac (GG-482) — fixed by 56.1. |

### 56.1 — MLB games cache via GitHub Actions

```
COMMON RULES - WAVE 56 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY the PR(s) named in it. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W56_<n>.md
  (docs-only push to main).

WAVE 56.1 - MLB GAMES CACHE REFRESH WITHOUT THE OPERATOR'S MAC (GG-482). Repo: eignacio1/prediction-market-bot.

WHY
55.3b got the 12 MLB postseason shadow cells writing rows (69 T1 rows) by refreshing the games cache off the VPS
(statsapi 406s the VPS, GG-470) and syncing it up with scripts/sync_mlb_games_cache.sh - which must be run from the
operator's Mac every day. He does not run plumbing. The runner refuses a cache older than 26h, so the cells go dark
about 26h after the last sync (last sync ~2026-10-05 22:57 UTC). Fix: a scheduled GitHub Actions job does the
refresh on a GitHub runner and syncs it to the VPS. .github/workflows/tss_daily_sync.yml already reaches the VPS
with the VPS_SSH_KEY secret - copy its pattern.

D0 - Worktree w56-mlb-cache-actions; claim "W56.1 STANDARD - GH Actions MLB games-cache refresh + VPS sync".
D1 - Read GG-482, GG-470, scripts/sync_mlb_games_cache.sh, scripts/fetch_mlb_game_history.py and tss_daily_sync.yml.
D2 - New workflow .github/workflows/mlb_games_cache_sync.yml: workflow_dispatch + schedule twice daily (pick two
     off-the-hour minutes that miss the :00/:30 VPS cron stampede, GG-477). Steps mirror the sync script exactly:
     seed games.parquet from the VPS, refresh with fetch_mlb_game_history.py, scp to *.tmp, atomic mv, same meta
     stamp. Fail-closed: any failure leaves the VPS cache untouched and fails the job loudly.
D3 - PR, CI green, merge (record the t4-mlb decision from the Deploy summary - a workflow file is not in its closure).
     Then trigger it once by workflow_dispatch. If statsapi also refuses the GitHub runner: record the exact error,
     stop, and report - do not route around it.
D4 - Proof, VPS read-only: games_current.meta.json stamp == the dispatch run's time; then run the MLB T1 shadow job
     once by hand with the cron's exact command and record rows written per cell.
D5 - Keep scripts/sync_mlb_games_cache.sh as a documented manual fallback only. GG-482 -> RESOLVED only after D4.
     GG-470 / GG-453: note the new path. Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W56_1_mlb_cache_actions_results.md.
     Docs-only push to main.

END OF BLOCK 56.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 56.2 — Apply the cron stagger

```
COMMON RULES - WAVE 56 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY the PR(s) named in it. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W56_<n>.md
  (docs-only push to main).

WAVE 56.2 - STOP THE NIGHTLY OOM: APPLY THE CRON STAGGER (GG-477 / T-681). Repo: eignacio1/prediction-market-bot.

WHY
55.2 traced t4-mlb's 2026-10-05 01:30 UTC restart to a host-wide OOM kill: ~6 cron jobs start on the same :00/:30
minute on a 961 MB VPS. 55.2 added 2 GB swap and staged scripts/ops/gg477_cron_stagger.py, which changes ONLY the
minute field of five schedule lines (NHL T2/T3, EXP-037 T3, run_t3_pretip, run_t3_mlb_pretip). It could not apply
it: the terminal's permission layer refused the remote write. Editing existing cron lines needs the operator's
written authorization: it must appear in 04_EXECUTION/ACTIVE_QUEUE.md under "Needs your decision" as
"AUTHORIZATION - GG-477 CRON STAGGER". If that line is not there, do D1 only and stop.
If your terminal shows a permission prompt for the VPS write, it is the operator's to approve there; if it is
refused, record the exact command and refusal and stop - do not work around it.

D0 - Worktree w56-cron-stagger; claim "W56.2 STANDARD - GG-477 cron stagger apply (authorized)".
D1 - VPS read-only: swapon --show (swap active?), free -m, crontab -l. Run the stagger script in dry-run; check it
     matches exactly the expected line counts in RULES and touches nothing else.
D2 - Apply (only with the authorization line present): back up the crontab (timestamped), run with APPLY=1, diff old vs new crontab - only minute fields of the
     five rules may differ.
D3 - Keep it from being reverted: the EXP-037 and NHL cron blocks are reinstalled from deploy/
     (cron_exp037_pregame_shadow.conf, cron.nhl_shadow) by the arm scripts. Update those files to the same staggered
     minutes so a future re-arm keeps them. 56.3 appends a line to cron_exp037_pregame_shadow.conf in its own PR - if
     both touch it, whoever merges second re-merges main first. PR, CI green, merge (record the t4-mlb decision). Do not re-arm now.
D4 - Evidence of the last OOM window, VPS read-only: journalctl -k --since "<today> 01:25" --until "<today> 01:40"
     | grep -ci oom, and t4-mlb NRestarts. Do not wait for the next window - the next block reads it.
D5 - GG-477: note applied (backup path, diff); RESOLVED only after a clean 01:30 UTC window, which a later block
     checks. Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W56_2_cron_stagger_results.md. Docs-only push to main.

END OF BLOCK 56.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 56.3 — MLB shadow settlement + Live Terminal check

```
COMMON RULES - WAVE 56 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the deploy pulls code and skips the restart, logged in the job summary. Each block
  merges ONLY the PR(s) named in it. Always read the Deploy job summary after a merge and record the t4-mlb decision.
- Operator decisions in force: DECISION_LOG 2026-10-05 and ADR-0071. Standing authorizations: shadow-evaluation
  cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy + pmbot-web-dashboard restart (2026-10-02).
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend.
- If a PR shows mergeable_state dirty, it is almost always SESSION_CLAIMS.md / .last_session_checkpoint (union files
  GitHub cannot merge): merge origin/main into the PR branch locally, push, wait for CI green, then merge.
- No order, position, fill, stake or kelly_fraction change. Demo only. No live ledger writes this wave.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W56_<n>.md
  (docs-only push to main).

WAVE 56.3 - MLB SHADOW SETTLEMENT (GG-472) + LIVE TERMINAL CHECK AFTER THE LEDGER BOOKING.
Repo: eignacio1/prediction-market-bot.

WHY
The 12 MLB postseason shadow cells now log rows but nothing ever attaches the outcome, so no MLB cell can ever be
scored (GG-472). scripts/run_pregame_shadow_settle.py does this for NFL only (outcome join, no Brier). The MLB games
cache on the VPS already holds final scores, so the join needs no statsapi call. Separately, 55.1 booked the 26 stuck
MLB positions (T1 realized drawdown 12.44%, T4M-PROJ 13.45%) AFTER 55.2's Live Terminal check, which still showed
T1 FROZEN at 10.60%: confirm the running Live Terminal now shows the booked numbers.

D0 - Worktree w56-mlb-settle; claim "W56.3 STANDARD - MLB shadow settlement join + Live Terminal check".
D1 - Read GG-472, run_pregame_shadow_settle.py, scripts/run_mlb_pregame_shadow.py and the MLB ledgers' row shape
     (exp_output/PREGAME_SHADOW/MLB_*). Outcome join only: no Brier, no score, no read of any result metric
     (pre-registration EXP-037).
D2 - Build the MLB settle path (extend the existing script with an MLB mode, or a sibling - smallest change), reading
     final scores from the games cache. Per market type: moneyline, run line, game total, team total -> y in {0,1};
     a game with no final in the cache stays unsettled (no guess). Tests with recorded fixtures. PR, CI green, merge
     (record the t4-mlb decision).
D3 - VPS: run the MLB settle once by hand on the current ledgers. It writes only the settled/ copies the NFL path
     writes - never the raw ledgers. Record settled rows per cell. Do NOT add a cron line (56.2 owns crontab this
     wave); append the line at the END of deploy/cron_exp037_pregame_shadow.conf in the same PR and say it arms next wave.
D4 - Live Terminal, against the RUNNING dashboard: T1 book no longer FROZEN; realized drawdown tile 12.44% (T1) and
     the T4M-PROJ figure; MLB shadow cells show their rows. Raw API excerpt in the results doc. Anything still stale:
     record exactly what it shows.
D5 - GG-472 -> RESOLVED only after D3 settles rows; GG-431 -> RESOLVED if D4 shows the T1 book live. Results doc
     05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W56_3_mlb_settle_results.md. Docs-only push to main.

END OF BLOCK 56.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 56 — issued 2026-10-05 ~23:50 UTC (4:50 PM PT) · three terminal blocks

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 56.1 | MLB games cache via GH Actions | ⬜ | new workflow | Fresh stamp on VPS + MLB rows, no Mac step |
| 56.2 | Cron stagger (GG-477) | ⬜ | VPS crontab minutes, deploy/ cron files | Your authorization line |
| 56.3 | MLB shadow settlement + Live Terminal | ⬜ | settle path, dashboard read | Settled rows; T1 book live on the terminal |

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
| **NEW — GG-477 cron stagger** | Move the start minute of 5 existing cron lines (NHL T2/T3, EXP-037 T3, two pre-tip jobs) off :00/:30 so they stop starting together and OOM-killing t4-mlb at ~01:30 UTC. Minutes only; commands, hours unchanged; crontab backed up. **Window's recommendation: yes.** Unlocks 56.2. | t4-mlb can be OOM-killed nightly. |
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

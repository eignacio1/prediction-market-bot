# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 1638496` (2026-10-03 22:10 UTC, strategic window). PR state and CI read live from GitHub.
VPS facts are the 50.2 cleanup terminal's report, not re-verified from here (this window has no SSH).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-452** registered (GG-453..460 claimed, unused) · **T-663** claimed (T-660..663 unused) · **ADR-0070** (PROPOSED) · **EXP-037** · gap log **180 OPEN** |
| Registry (92 cells) | On main: ACTIVE 1 · **SHADOW 7** (MLB player-hits T1-T3 + 4 NFL T1) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 81. **After PR #160 lands: SHADOW 16** (+9 NHL), NOT_IMPLEMENTED 72. |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| NFL + MLB postseason shadow | **Armed** (50.2): EXP-037 cron block installed; crontab backup `/root/crontab.bak.20261003T200240Z`; first NFL T1 firing 2026-10-04 00:05 UTC. |
| NHL | Regular season started 10-03. 9 cells log rows (51.3; re-check = 53.2); registry flip + 2-letter team-code fix ride in **#160**. Never uses the confirmed goalie (GG-401) - no NHL T3 score may be read. |
| Waiting to land (all CI green, none merged) | **#160** `w52/landing` @ `6f962400` = #157 + 51.1 + 51.2 + NHL 9-cell flip (clean) · **#161** `w52/live-terminal` @ `a1bdfc05`, based on #160 · **#158** GG-432 deploy change (draft, your call) · **#159** resolver (draft; waits on your GG-450 call). #157 stays open, contained in #160. |
| VPS | HEAD `eb2d1434` (50.2). `pmbot-web-dashboard` process still on `077558b`. |
| Deploy | **Every push to main that touches anything outside the 9 doc folders auto-deploys and restarts `t4-mlb` + `pmbot-web-dashboard`** (`deploy.yml`, GG-432). A push is docs-only only if EVERY file in it is under `00_ADMIN 01_SPEC 02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE 08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF`. |
| Live games (10-03 UTC) | MLB: NYY@TB 22:30Z · SD@MIL 00:30Z (5:30 PM PT) - **earliest code-push window ~03:30 UTC = ~8:30 PM PT**, re-checked live then. NHL regular season tonight: 7 games 23:00Z, 1 at 23:30Z, 2 at 00:00Z, 01:00Z, 2 at 02:00Z. First NFL T1 shadow run 00:05Z (5:05 PM PT). |

---

## ⬛ NOW — Wave 53 · three terminal blocks · run any time (no clock dependence) · nothing merges to main

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **53.1** Resolver VPS confirmation (GG-440) | ⬜ **READY** | VPS read-only; ledger copies on the Mac; `w52/resolver-406` only if the fix is wrong; W52_C results doc | — |
| **53.2** Shadow ledger + crontab audit | ⬜ **READY** | VPS read-only; results doc only | — |
| **53.3** GG-451 guard into the landing PR + GG-452 VPS freeze | ⬜ **READY** | `w52/landing` (PR #160): `scripts/close_session_claim.sh` + one test; VPS read-only | — |

Operator 2026-10-03 15:11 PT: no timing-bound blocks; these run whenever terminals are available. Disjoint: 53.1 resolver branch + W52_C doc; 53.2 results doc only; 53.3 `w52/landing`. Gap-log notes land on different entries (GG-440 / GG-451-452). **GG-451 hazard:** `close_session_claim.sh` pushes HEAD to main — every block is told not to run it.

**Next, not yet issued:** Wave 54 = the **landing block** in the idle window (earliest ~8:30 PM PT): fold #161 into `w52/landing` so it is ONE merge, merge #160, confirm Deploy, VPS HEAD, both services, dashboard `process.sha`, `t4_mlb_cycle_log` resumes, 16 SHADOW cells on the running Live Terminal; plus a read of the first NFL T1 shadow run (00:05Z). Issued when the window opens.

### 53.1 — Resolver VPS confirmation

```
COMMON RULES - WAVE 53 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. One job, done completely. Push at the nearest boundary when you stop.
- Runs at any hour. Any push to main that touches a file outside the 9 doc folders (00_ADMIN 01_SPEC
  02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE
  08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF) deploys and restarts t4-mlb (deploy.yml, GG-432). Landing is a
  separate block. So: NO code to main and NO PR merges in this wave, whatever the time. Docs-only pushes to
  main are fine.
- GG-451 HAZARD: scripts/close_session_claim.sh pushes HEAD to main. Do NOT run it, and do not let
  /session-end run it. Write your handoff file instead.
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own (main's claim script pushes
  HEAD to main - GG-419; the fix sits in unmerged PR #160). Never reuse a number in SESSION_CLAIMS.md.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only doc-folder paths. If your
  branch has code commits, push docs from a second worktree made from origin/main
  (git worktree add ../<slug>-docs origin/main), not from your code branch.
- VPS is read-only: no ledger write, no cron edit, no restart, no hand-pull, no log rotation. Work on copies.
- No order, position, fill, stake or kelly_fraction change. Demo only.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into a SESSION_HANDOFF file (docs-only push to main).

WAVE 53.1 - MLB RESOLVER, VPS CONFIRMATION (GG-440 / PR #159). Repo: eignacio1/prediction-market-bot.

WHY
Wave 52.C (cloud, no VPS) found the LIKELY root cause: statsapi.mlb.com 406s the VPS's IP (Fastly CDN block,
GG-084), and the ESPN fallback then settles nothing through a path that logged nothing. PR #159
(branch w52/resolver-406, fd315549) books only Kalshi yes/no outcomes and skips cancelled markets. 17 T1 + 9 T4
paper positions are stuck. This block turns LIKELY into CONFIRMED or REFUTED, and classifies all 26 positions.
Read first: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W52_C_resolver_406_results.md (its VPS-PENDING list is
this block's checklist), GG-440, GG-450.

D0 - Worktree w53-resolver-vps; claim "W53.1 STANDARD - GG-440 VPS confirmation + 26-position dry run".
D1 - On the VPS, read-only: send the resolver's exact statsapi request (URL, params, headers from
     run_resolve_mlb.py), then vary one thing at a time (Accept: application/json; no custom headers; default
     User-Agent). Record status and the server / via / x-served-by / x-cache headers. Send the identical
     request from this Mac and compare.
D2 - On the VPS: grep -c "ESPN-FALLBACK" logs/resolve_mlb_cron.log, and read the last run's lines for the 26
     positions. Establish why ESPN settled nothing.
D3 - Root cause: CONFIRMED or REFUTED, one sentence, with the evidence lines.
D4 - Copy logs/paper_portfolio_mlb.json and logs/paper_portfolio_mlb_t4.json DOWN to a scratch dir on this
     Mac (never touch the VPS originals). From PR #159's branch:
     LOG_DIR=<copy dir> BOT_ENV=paper python3 src/prediction_market_bot/run_resolve_mlb.py --dry-run
     Table, one row per position (all 26): ticker, band, game_date, Kalshi result, classification
     (settles / skipped-cancelled / skipped-not-final / unresolvable), reason. Confirm ZERO cancelled markets
     get a win or loss. Note: this Mac is not blocked by statsapi, the VPS is - say what that changes.
D5 - If D1-D4 show the fix is wrong or incomplete, correct it on w52/resolver-406 with a test and get CI green.
     Do not merge #159; it waits on the operator's GG-450 call and an idle window.
D6 - Append a "VPS confirmation (W53.1)" section to the W52_C results doc and a note on GG-440 (status
     unchanged). Docs-only push to main.
```

### 53.2 — Shadow ledger + crontab audit

```
COMMON RULES - WAVE 53 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. One job, done completely. Push at the nearest boundary when you stop.
- Runs at any hour. Any push to main that touches a file outside the 9 doc folders (00_ADMIN 01_SPEC
  02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE
  08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF) deploys and restarts t4-mlb (deploy.yml, GG-432). Landing is a
  separate block. So: NO code to main and NO PR merges in this wave, whatever the time. Docs-only pushes to
  main are fine.
- GG-451 HAZARD: scripts/close_session_claim.sh pushes HEAD to main. Do NOT run it, and do not let
  /session-end run it. Write your handoff file instead.
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own (main's claim script pushes
  HEAD to main - GG-419; the fix sits in unmerged PR #160). Never reuse a number in SESSION_CLAIMS.md.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only doc-folder paths. If your
  branch has code commits, push docs from a second worktree made from origin/main
  (git worktree add ../<slug>-docs origin/main), not from your code branch.
- VPS is read-only: no ledger write, no cron edit, no restart, no hand-pull, no log rotation. Work on copies.
- No order, position, fill, stake or kelly_fraction change. Demo only.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into a SESSION_HANDOFF file (docs-only push to main).

WAVE 53.2 - SHADOW LEDGER + CRONTAB AUDIT: is every shadow arm actually logging? Repo: eignacio1/prediction-market-bot.

WHY
The landing PR (#160) flips 9 NHL cells to SHADOW on the strength of a row table taken 2026-10-03
20:34 UTC (11_MEMORY_HANDOFF/SESSION_HANDOFF_20261003_W51_3.md). The EXP-037 NFL + MLB-postseason crons were
armed 2026-10-03 ~20:02 UTC and have not been checked since. PR #161 makes the Live Terminal show every
shadow cell - this block produces the ground-truth table it must match. Read-only. Runs at any hour; it
measures whatever exists when you run it. No NHL or NFL score may be read or computed.

D0 - Worktree w53-shadow-audit; claim "W53.2 STANDARD - shadow ledger + crontab audit (read-only)".
D1 - VPS read-only, NHL: for each file under data/shadow/nhl/ (top level and settled/), count rows, valid rows
     (numeric p_yes in [0,1], mid in (0,1), market_ticker present), settled rows, first and last row time.
     One row per (market type, band). Flag any of the 9 cells #160 flips (NHL_MONEYLINE, NHL_PUCK_LINE,
     NHL_GAME_TOTAL x T1, T2, T3) that has zero rows - #160 must not flip it.
D2 - VPS read-only, EXP-037: find the ledgers the pregame_shadow runner writes
     (src/prediction_market_bot/pregame_shadow/runner.py) for NFL and MLB postseason. Same table: rows, valid,
     settled, first/last row time, per (market type, band). For each cron-scheduled run that should have fired
     by now, say whether it ran and what it wrote (cron log lines). If none has fired yet, say so.
D3 - VPS read-only: crontab -l, shadow lines only (NHL + EXP-037). Diff against deploy/cron.nhl_shadow,
     deploy/cron.nhl_shadow.draft and deploy/cron_exp037_pregame_shadow.conf. Record every difference.
D4 - Cross-check against the registry on PR #160's branch (w52/landing): list cells that log rows but are not
     SHADOW there, and SHADOW cells with no rows. Do not change the registry.
D5 - Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W53_2_shadow_audit_results.md with the tables;
     register a gap only for a real defect (arm not firing, rows invalid, crontab drift). Docs-only push to main.
```

### 53.3 — GG-451 guard into the landing PR + GG-452

```
COMMON RULES - WAVE 53 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. One job, done completely. Push at the nearest boundary when you stop.
- Runs at any hour. Any push to main that touches a file outside the 9 doc folders (00_ADMIN 01_SPEC
  02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE
  08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF) deploys and restarts t4-mlb (deploy.yml, GG-432). Landing is a
  separate block. So: NO code to main and NO PR merges in this wave, whatever the time. Docs-only pushes to
  main are fine.
- GG-451 HAZARD: scripts/close_session_claim.sh pushes HEAD to main. Do NOT run it, and do not let
  /session-end run it. Write your handoff file instead.
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own (main's claim script pushes
  HEAD to main - GG-419; the fix sits in unmerged PR #160). Never reuse a number in SESSION_CLAIMS.md.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only doc-folder paths. If your
  branch has code commits, push docs from a second worktree made from origin/main
  (git worktree add ../<slug>-docs origin/main), not from your code branch.
- VPS is read-only: no ledger write, no cron edit, no restart, no hand-pull, no log rotation. Work on copies.
- No order, position, fill, stake or kelly_fraction change. Demo only.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into a SESSION_HANDOFF file (docs-only push to main).

WAVE 53.3 - CLOSE THE GG-451 HAZARD INSIDE THE LANDING PR, + GG-452 VPS DEPENDENCY CHECK. Repo: eignacio1/prediction-market-bot.

WHY
scripts/close_session_claim.sh pushes HEAD to main (GG-451). Run from a session branch with code on it, it
lands that code on main, and deploy.yml then restarts t4-mlb - the same defect class as GG-419, which PR #157
fixed for claim_session.sh with a guard and tests/test_claim_session_head_guard.py. The next landing (PR #160,
branch w52/landing) is one code merge, so the fix rides in it - no extra restart.

D0 - Worktree w53-gg451; claim "W53.3 STANDARD - GG-451 guard on w52/landing + GG-452 VPS freeze".
D1 - Check out w52/landing (expected head 6f962400; if different, stop and report). Read the GG-419 guard in
     scripts/claim_session.sh and its test on that branch.
D2 - Apply the same guard to scripts/close_session_claim.sh: refuse to push unless HEAD carries nothing beyond
     origin/main except the closure commit itself; print the exact refusal and the safe alternative. Add a test
     mirroring test_claim_session_head_guard.py. Do not change anything else.
D3 - Targeted tests, then the full suite once (PYTHONPATH=src python3 -m pytest tests -q). Must be green.
D4 - Push to w52/landing (this updates PR #160 - do NOT merge it). Wait for CI on #160; record run ID, result,
     and mergeable_state from the GitHub API. PR #161 (w52/live-terminal) is based on w52/landing: confirm it
     is still mergeable after your push. If either goes red or conflicted, revert your commit and report.
D5 - GG-452, VPS read-only: pip freeze from the bot's venv on the VPS; diff against the repo's DEPENDENCY_LOCKS
     files and pyproject.toml bounds. Report mismatches only. Note on GG-452, status unchanged.
D6 - Note on GG-451: "fix on w52/landing @ <sha>, lands with #160" (status unchanged until landed). Docs-only
     push to main.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 53 — issued 2026-10-03 ~3:15 PM PT, 53.2 replaced 3:20 PM PT · three terminal blocks · no clock dependence

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 53.1 | Resolver VPS confirmation (GG-440) | ⬜ | VPS read-only, ledger copies, results doc | #159 still waits on your GG-450 call |
| 53.2 | Shadow ledger + crontab audit | ⬜ | VPS read-only, results doc | Feeds the landing check of #160 / #161 |
| 53.3 | GG-451 guard into #160 + GG-452 freeze | ⬜ | `w52/landing` | #160 green + clean after push |

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

- **NFL + MLB postseason shadow crons are armed.** The 33 pre-game cells now log unattended. Nothing restarted.
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

**Wave 53 runs without a line from you.** Open calls below: **GG-432** (PR #158), **GG-450**, **GG-440** (Kalshi as resolution source), and — depending on 53.2 — an NHL T3 pre-registration amendment.

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").** Unchanged;
> used by 50.2. Not covered: any order, position, fill, stake or `kelly_fraction` change; any EXISTING cron line.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT).** Standing. Covers
> `pmbot-web-dashboard` only. Note: under today's `deploy.yml`, any code merge also restarts `t4-mlb` — see GG-432 below.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **GG-432: CI restarts t4-mlb on every code push** | Today every merge that touches code restarts the live T4 process, including mid-game. Options: (a) **window's recommendation, built as PR #158** — restart `t4-mlb` only when a file it imports changed AND no MLB game is live (otherwise skip, loudly; restart at the next deploy or by hand); (b) never auto-restart `t4-mlb`, restart only by hand; (c) keep as is. | Every code landing waits for an idle window by hand, as Wave 51 does. |
| **GG-450: booking the 16 Kalshi-cancelled T1 positions** | void (stake returned, no P&L) / mark to Kalshi's settlement value / exclude from G6. PR #159 skips them until you choose. | The T1 book stays frozen; realized drawdown stays understated by the open stake (~11-12% after booking, under 20%). |
| **GG-440: Kalshi settlement as a resolution source** | PR #159 books MLB positions from Kalshi's own yes/no result instead of statsapi (blocked from the VPS). ADR-gated. | No MLB paper position settles. |
| **NHL goalie timing (GG-401)** | Pulled from Wave 53 (timing-bound). The measurement — run `scripts/nhl_goalie_source_probe.py` at ~60/30/15 min before one slate's puck drop — fits a detached read-only VPS job (row below) instead of a terminal. | No NHL T3 score may be read. |
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

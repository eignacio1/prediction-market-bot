# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 1638496` (2026-10-03 22:10 UTC, strategic window). PR state and CI read live from GitHub.
VPS facts are the 50.2 cleanup terminal's report, not re-verified from here (this window has no SSH).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-453** registered · **T-663** claimed (T-660..663 unused) · **ADR-0070** (PROPOSED) · **EXP-037** · gap log **180 OPEN** |
| Registry (92 cells) | On main: ACTIVE 1 · **SHADOW 7** (MLB player-hits T1-T3 + 4 NFL T1) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 81. **After PR #160 lands: SHADOW 16** (+9 NHL), NOT_IMPLEMENTED 72. |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| NFL + MLB postseason shadow | **NFL armed and logging** (12 cells, T1/T2/T3; settle job ran, 0 final yet). **MLB postseason NOT armed** — no cron, no ledger (GG-453, found by 53.2). |
| NHL | 9 cells logging valid rows (53.2 audit, to 10-05 00:40Z); registry flip + team-code fix ride in **#160**. Never uses the confirmed goalie (GG-401) - no NHL T3 score may be read. |
| Waiting to land (all CI green, none merged) | **#160** `w52/landing` @ `6f962400` = #157 + 51.1 + 51.2 + NHL 9-cell flip (clean) · **#161** `w52/live-terminal` @ `a1bdfc05`, based on #160 · **#158** GG-432 deploy change (draft, your call) · **#159** resolver (draft; waits on your GG-450 call). #157 stays open, contained in #160. |
| VPS | HEAD `eb2d1434` (50.2). `pmbot-web-dashboard` process still on `077558b`. |
| Deploy | **Every push to main that touches anything outside the 9 doc folders auto-deploys and restarts `t4-mlb` + `pmbot-web-dashboard`** (`deploy.yml`, GG-432). A push is docs-only only if EVERY file in it is under `00_ADMIN 01_SPEC 02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE 08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF`. |
| Live games (10-03 UTC) | MLB: NYY@TB 22:30Z · SD@MIL 00:30Z (5:30 PM PT) - **earliest code-push window ~03:30 UTC = ~8:30 PM PT**, re-checked live then. NHL regular season tonight: 7 games 23:00Z, 1 at 23:30Z, 2 at 00:00Z, 01:00Z, 2 at 02:00Z. First NFL T1 shadow run 00:05Z (5:05 PM PT). |

---

## ⬛ NOW — Wave 54 · three terminal blocks · run any time · only 54.2 merges (PR #158)

Operator 2026-10-04 23:50 PT: *"Proceed with the recommended choice and plot it into the blocks."* Logged in DECISION_LOG 2026-10-05: **GG-432 → (a) PR #158** · **Kalshi settlement = resolution source (GG-440)** · **cancelled → booked at Kalshi settlement value, flagged, excluded from G6 + calibration (GG-450)** · **postponed games → Kalshi result**.

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **54.1** Final landing PR (no merge) | ⬜ **READY** | `w52/landing`: fold #161, 8 NFL T2/T3 SHADOW flips, re-merge main | — |
| **54.2** Merge #158 + VPS proof + arm MLB postseason shadow | ⬜ **READY** | merges #158; `deploy/cron_exp037_pregame_shadow.conf`; VPS crontab (EXP-037 block only) | — |
| **54.3** Kalshi-settlement resolver: ADR + code + dry run | ⬜ **READY** | `w52/resolver-406` (#159); new ADR; W52_C results doc | — |

Disjoint files. 54.1 re-merges main last, because 54.2 and 54.3 push to main during the wave. Every prompt ends with an END-OF-BLOCK line — 53.3 arrived truncated, so a terminal that can't see that line stops.

**Next, not yet issued:** Wave 55 — merge #160 (with #158 in, this is safe at any hour) and check the Live Terminal shows 24 SHADOW cells; live ledger write for the 26 positions under the new ADR (backup + dry-run diff first); MLB shadow settlement.

### 54.1 — Final landing PR

```
COMMON RULES - WAVE 54 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Any push to main touching a file outside the 9 doc folders (00_ADMIN 01_SPEC
  02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE
  08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF) triggers deploy.yml. ONLY block 54.2 merges anything (PR #158, then
  one conf file). 54.1 and 54.3 merge nothing and push no code to main. Docs-only pushes to main are fine.
- Operator decisions in force (DECISION_LOG 2026-10-05): GG-432 option (a) = PR #158; Kalshi's own settlement is the
  resolution source for Kalshi paper positions (GG-440); Kalshi-cancelled markets are booked at Kalshi's settlement
  value, flagged cancelled, and excluded from G6 counts and calibration/Brier (GG-450); postponed games resolve on
  Kalshi's result.
- GG-451 HAZARD (until #160 lands): scripts/close_session_claim.sh pushes HEAD to main. Do NOT run it, and do not
  let /session-end run it. Write your handoff file instead.
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own (main's claim script pushes HEAD to
  main - GG-419). Give a real ID range, never TBD. Never reuse a number in SESSION_CLAIMS.md.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend. If your
  branch has code commits, push docs from a second worktree made from origin/main.
- Ledgers: no write to any live ledger. Work on copies. No order, position, fill, stake or kelly_fraction change.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W54_<n>.md
  (docs-only push to main).

WAVE 54.1 - FINAL LANDING PR: fold #161 in, flip the 8 NFL T2/T3 cells, clear the merge conflict. Do NOT merge.
Repo: eignacio1/prediction-market-bot.

WHY
PR #160 (branch w52/landing) is the one code landing for Waves 51-53. It is "dirty" because main's docs pushes
touched two union-merge files GitHub cannot merge (SESSION_CLAIMS.md, .last_session_checkpoint). PR #161 (Live
Terminal) sits on top of it and should land in the same merge. The W53.2 audit found 8 NFL cells logging valid rows
that are not SHADOW on the branch. After this block, #160 is the single green PR to merge.

D0 - Worktree w54-landing-final; claim "W54.1 STANDARD - final landing PR #160 (no merge)".
D1 - Check out w52/landing; expected head 2365cc7 (the W53.3 GG-451 guard). If different, stop and report.
D2 - Merge w52/live-terminal (PR #161, expected a1bdfc05) into it, --no-ff.
D3 - Own commit: flip NOT_IMPLEMENTED -> SHADOW for NFL_MONEYLINE, NFL_SPREAD, NFL_GAME_TOTAL, NFL_TEAM_TOTAL x
     T2 and T3 in src/prediction_market_bot/c5_execution/market_type_registry.py. Copy the pattern of 0cf11eb (NFL
     T1) and 9f924087 (NHL), tests included. Cite 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W53_2_shadow_audit_results.md
     (row counts per cell). Message: records reality (cron already evaluates them at kelly 0), not a promotion.
     Expected registry after this branch lands: SHADOW 24 (3 MLB player-hits + 12 NFL + 9 NHL). Assert it in a test.
D4 - git fetch; merge origin/main in. The repo's merge=union drivers resolve SESSION_CLAIMS.md and
     .last_session_checkpoint locally; any other conflict: keep both sides, never drop content.
D5 - Full suite once; must be green. Push. Confirm on the GitHub API: #160 CI green on the new head and
     mergeable_state clean. Update #160's body: merged heads with SHAs (#157, 51.1, 51.2, #161, GG-451 guard, NHL +
     NFL flips), test count, expected SHADOW 24. Comment on #161 "folded into #160 @ <sha>" and close it.
     Right before the final push, git fetch again - 54.2 and 54.3 push to main during this wave; re-merge if moved.
D6 - Note on GG-451: "fix on w52/landing @ <sha>, lands with #160" (status unchanged). Docs-only push to main.

END OF BLOCK 54.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 54.2 — Merge #158 + VPS proof + arm MLB postseason shadow

```
COMMON RULES - WAVE 54 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Any push to main touching a file outside the 9 doc folders (00_ADMIN 01_SPEC
  02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE
  08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF) triggers deploy.yml. ONLY block 54.2 merges anything (PR #158, then
  one conf file). 54.1 and 54.3 merge nothing and push no code to main. Docs-only pushes to main are fine.
- Operator decisions in force (DECISION_LOG 2026-10-05): GG-432 option (a) = PR #158; Kalshi's own settlement is the
  resolution source for Kalshi paper positions (GG-440); Kalshi-cancelled markets are booked at Kalshi's settlement
  value, flagged cancelled, and excluded from G6 counts and calibration/Brier (GG-450); postponed games resolve on
  Kalshi's result.
- GG-451 HAZARD (until #160 lands): scripts/close_session_claim.sh pushes HEAD to main. Do NOT run it, and do not
  let /session-end run it. Write your handoff file instead.
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own (main's claim script pushes HEAD to
  main - GG-419). Give a real ID range, never TBD. Never reuse a number in SESSION_CLAIMS.md.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend. If your
  branch has code commits, push docs from a second worktree made from origin/main.
- Ledgers: no write to any live ledger. Work on copies. No order, position, fill, stake or kelly_fraction change.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W54_<n>.md
  (docs-only push to main).

WAVE 54.2 - GG-432: MERGE PR #158, PROVE IT ON THE VPS, THEN ARM THE 12 MLB POSTSEASON SHADOW CELLS (GG-453).
Repo: eignacio1/prediction-market-bot.

WHY
Operator accepted GG-432 option (a): deploy restarts t4-mlb only if a push changes a file the t4-mlb process imports
AND no MLB game is live. That ends "code lands only in idle windows". Merging #158 is safe at any hour because the
merge commit's own deploy runs the new rule and deploy.yml is not in t4-mlb's import closure - prove that before
merging. Second: the W53.2 audit found the 12 MLB postseason shadow cells were never armed (no cron, no ledger) -
rows are lost every game day. The standing shadow-cron authorization (operator 2026-10-02 15:22 PT, new lines only)
covers arming them.

D0 - Worktree w54-gg432-mlb-arm; claim "W54.2 STANDARD - merge #158 + verify on VPS + arm MLB postseason shadow".
D1 - Read PR #158 (branch w52/gg432-deploy, expected 444b54f7) and its decision script + tests. Run the decision
     logic against #158's own diff vs current main: it must say "no t4-mlb restart". If it says restart, stop.
     VPS read-only, BEFORE merging: record t4-mlb and pmbot-web-dashboard ActiveEnterTimestamp and VPS HEAD.
D2 - Mark #158 ready, merge it (merge commit). Watch the Deploy run. Record from the job summary: the t4-mlb
     decision and why; dashboard restarted. VPS read-only: HEAD == merge SHA; t4-mlb ActiveEnterTimestamp UNCHANGED;
     dashboard restarted. If t4-mlb restarted anyway, register a HIGH gap and do NOT continue to D3.
D3 - Arm MLB postseason shadow. Read deploy/cron_exp037_pregame_shadow.conf (NFL block) and
     scripts/run_mlb_pregame_shadow.py (12 cells: MONEYLINE, RUN_LINE, GAME_TOTAL, TEAM_TOTAL x T1, T2, T3). Add MLB
     T1/T2/T3 lines to that conf, same shape and cadence logic as the NFL lines, NFL lines byte-identical. Push the
     conf to main (it deploys; confirm the job summary again says no t4-mlb restart). Then run
     scripts/arm_shadow_crons.sh as designed (dry-run of every line first; crontab backup; EXP-037 block reinstalled
     idempotently; nothing outside the block touched). Run each MLB band once by hand with the cron's exact command and
     record what it wrote (T2/T3 may correctly write nothing outside their windows - say so). MLB settlement: the
     settle script is NFL-only - register a gap for MLB settlement; do not build it here.
D4 - Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W54_2_gg432_mlb_arm_results.md (before/after timestamps,
     deploy summaries, crontab diff, first MLB rows). GG-432: RESOLVED only with the VPS proof from D2. GG-453: note
     armed + first rows (resolve only if rows exist). Docs-only push to main.

END OF BLOCK 54.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 54.3 — Kalshi-settlement resolver: ADR + code + dry run

```
COMMON RULES - WAVE 54 (read first; they bind this block)
- Time: ~30 min, hard stop at 45. Push at the nearest boundary when you stop; say where the next session resumes.
- Runs at any hour. Any push to main touching a file outside the 9 doc folders (00_ADMIN 01_SPEC
  02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE
  08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF) triggers deploy.yml. ONLY block 54.2 merges anything (PR #158, then
  one conf file). 54.1 and 54.3 merge nothing and push no code to main. Docs-only pushes to main are fine.
- Operator decisions in force (DECISION_LOG 2026-10-05): GG-432 option (a) = PR #158; Kalshi's own settlement is the
  resolution source for Kalshi paper positions (GG-440); Kalshi-cancelled markets are booked at Kalshi's settlement
  value, flagged cancelled, and excluded from G6 counts and calibration/Brier (GG-450); postponed games resolve on
  Kalshi's result.
- GG-451 HAZARD (until #160 lands): scripts/close_session_claim.sh pushes HEAD to main. Do NOT run it, and do not
  let /session-end run it. Write your handoff file instead.
- Start: CLAUDE.md session-start protocol, kept brief. Isolated worktree: scripts/new_session_worktree.sh <slug>.
  Claim with scripts/claim_session.sh IMMEDIATELY, before any commit of your own (main's claim script pushes HEAD to
  main - GG-419). Give a real ID range, never TBD. Never reuse a number in SESSION_CLAIMS.md.
- Before ANY push to main: git diff --name-only origin/main..HEAD must list only the paths you intend. If your
  branch has code commits, push docs from a second worktree made from origin/main.
- Ledgers: no write to any live ledger. Work on copies. No order, position, fill, stake or kelly_fraction change.
- Never bypass a permission control: record the exact command and refusal, hand back.
- Every premise below is a claim to verify.
- Report back in this shape: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result |
  anything the operator must decide. Write the same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W54_<n>.md
  (docs-only push to main).

WAVE 54.3 - KALSHI SETTLEMENT AS THE PAPER RESOLUTION SOURCE: ADR + code + 26-position dry run. Do NOT merge,
do NOT write any live ledger. Repo: eignacio1/prediction-market-bot.

WHY
26 MLB paper positions have been stuck since August: 16 T1 on Kalshi-cancelled markets, 10 (1 T1 + 9 T4) on games
postponed and replayed. The operator decided (DECISION_LOG 2026-10-05): Kalshi's own settlement is the resolution
source (GG-440); cancelled markets are booked at Kalshi's settlement value, flagged cancelled, and excluded from G6
counts and calibration/Brier (GG-450); postponed games resolve on Kalshi's result. This block makes that real on PR
#159's branch and proves the numbers on copies. A later landing block does the live ledger write with a backup and a
dry-run diff.

D0 - Worktree w54-kalshi-resolution; claim "W54.3 STANDARD - ADR + Kalshi-settlement resolver + dry run" with an
     ADR number included in your range (next free at run time).
D1 - Read: the DECISION_LOG 2026-10-05 entry; 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W52_C_resolver_406_results.md
     incl. the W53.1 section; GG-440, GG-441, GG-450; run_resolve_mlb.py on w52/resolver-406 (expected head c9462a1).
     Find where the G6 paper-bet count and calibration/Brier read resolved positions.
D2 - ADR in 03_DECISIONS/ (your claimed number): "Kalshi settlement as the resolution source for Kalshi paper
     positions; cancelled and postponed handling". Status ACCEPTED - operator, 2026-10-04 23:50 PT, DECISION_LOG
     2026-10-05. Cover: source of truth, cancelled booking + exclusion flag, postponed games, statsapi/ESPN as
     cross-check only, and that live ledger writes need backup + dry-run diff (GG-228 provenance).
D3 - Code on w52/resolver-406, smallest change, tests: resolve from Kalshi's settled result (yes/no -> win/loss;
     cancelled/scalar -> book at Kalshi's settlement value, cancelled=true); G6 count and calibration/Brier skip
     cancelled=true. If calibration paths are too many for the clock, implement the flag + the G6 exclusion and
     register the rest. No sizing, kelly, limit or order code touched.
D4 - Dry run on COPIES of logs/paper_portfolio_mlb.json and logs/paper_portfolio_mlb_t4.json (scp down; VPS
     read-only). Table, all 26: ticker, band, Kalshi result/settlement value, booked P&L, cancelled flag, counts toward
     G6 (y/n). Then the resulting T1 realized drawdown as the kill switch computes it. If it is >= 20%, STOP and
     report - that is a real event even on paper.
D5 - Push the branch; CI green; update #159's body (decision, ADR, dry-run table). ADR + a results section appended to
     the W52_C results doc go to main (docs-only). Do not merge #159.

END OF BLOCK 54.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 54 — issued 2026-10-05 ~07:05 UTC (12:05 AM PT) · three terminal blocks · no clock dependence

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 54.1 | Final landing PR #160 | ⬜ | `w52/landing` | Green + clean; merged in Wave 55 |
| 54.2 | Merge #158, VPS proof, arm MLB shadow | ⬜ | deploy.yml (via #158), EXP-037 conf, crontab | t4-mlb NOT restarted by either deploy |
| 54.3 | Kalshi-settlement resolver | ⬜ | `w52/resolver-406`, ADR | Realized drawdown after booking < 20% |

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

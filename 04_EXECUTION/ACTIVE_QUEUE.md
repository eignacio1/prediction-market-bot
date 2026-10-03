# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 52e3ea3` (2026-10-03 21:05 UTC, incoming strategic window). GitHub PR/CI state and the MLB Stats API checked live.
VPS facts are the 50.2 cleanup terminal's report, not re-verified from here (this window has no SSH).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-450** registered (GG-443..449 claimed, unused) · **T-653** claimed · **ADR-0070** (PROPOSED) · **EXP-037** · gap log 178 OPEN |
| Registry (92 cells) | ACTIVE 1 · **SHADOW 7** (MLB player-hits T1-T3 + NFL T1 moneyline / spread / total / team total, flipped 2026-10-03 by T-608) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 81 |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| NFL + MLB postseason shadow | **Armed** (50.2): EXP-037 cron block installed; crontab backup `/root/crontab.bak.20261003T200240Z`; first NFL T1 firing 2026-10-04 00:05 UTC. |
| NHL | Flying in shadow: 9 cells have rows (51.3). Registry still says NOT_IMPLEMENTED. Never uses the confirmed goalie (GG-401). Team-code parser unverified (GG-403). |
| PR #157 (50.1 process fixes) | **NOT mergeable again** (GitHub `dirty`, 21:05 UTC): main moved 13 commits after 51.3; the only conflict is `11_MEMORY_HANDOFF/OPERATOR_DIGEST_20261003.md`, a `merge=union` file GitHub can't auto-merge. CI green on head `42a0d0d`. Landing block re-merges main into it first. |
| 51.1 / 51.2 branches | **No CI run on either** (branches only get CI as PRs). 51.2's final full-suite rerun was not confirmed at close-out. 51.2 also conflicts with main on 4 nav files (DECISION_LOG, PLAN, TODO_NEXT, MEMORY_BANK). 51.1 merges clean. |
| VPS | HEAD `eb2d1434` (50.2). `pmbot-web-dashboard` process still on `077558b`. |
| Deploy | **Every push to main that touches anything outside the 9 doc folders auto-deploys and restarts `t4-mlb` + `pmbot-web-dashboard`** (`deploy.yml`, GG-432). A push is docs-only only if EVERY file in it is under `00_ADMIN 01_SPEC 02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE 08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF`. |
| Live games today (Stats API, 21:00 UTC) | CWS@CLE final · **ATL@LAD in progress** · NYY@TB 22:30Z · SD@MIL 00:30Z (5:30 PM PT). **Earliest code-push window: after SD@MIL goes Final, ~03:30 UTC = ~8:30 PM PT.** Tomorrow's first pitch SD@MIL 20:00Z. |

---

## ⬛ NOW — Wave 52 · ONE Claude Code session runs 52.A → 52.E in order, then stops

Operator, 2026-10-03 14:13 PT: near the session limit, so the wave goes to a single Claude Code chat as one prompt, rolling block to block. It executes only; it does not generate waves or take VPS work. It updates only the Status/Result cells below as each block closes. Everything is branch/PR-only — nothing merges to main.

| Block | Status | Touches | Result / next |
|---|---|---|---|
| **52.A** Landing prep | ⬜ not started | branch `w52/landing`: #157 + 51.1 + 51.2 merged, NHL 9-cell SHADOW flip | — |
| **52.B** GG-432 decision PR | ⬜ not started | branch `w52/gg432-deploy`: `deploy.yml` + decision script/tests | — |
| **52.C** MLB resolver (GG-440) | ⬜ not started | branch `w52/resolver-406`: `run_resolve_mlb.py` + tests; results doc | — |
| **52.D** NHL confirmed goalie (GG-401) | ⬜ not started | branch `w52/nhl-goalie-probe` (probe only); results doc | — |
| **52.E** Live Terminal truth | ⬜ not started | branch `w52/live-terminal` stacked on `w52/landing`: `web_dashboard.py`, `Live Terminal.html`, tests | — |

**Cloud limits baked in:** no VPS — every VPS fact is cited from main or marked **VPS-PENDING** for a later terminal block. **Your decisions it prepares, not takes:** GG-432 (52.B PR), GG-450 booking of cancelled T1 positions (52.C skips them), any NHL pre-registration amendment (52.D).

**Next, not yet issued:** the landing block — merge 52.A's PR in an idle window (earliest ~8:30 PM PT, after SD@MIL goes Final; re-checked live then), plus a terminal block for the VPS-PENDING items. Issued when the window opens.

### Wave 52 — the one prompt (paste into Claude Code)

```
WAVE 52 - ONE CLAUDE CODE SESSION, FIVE BLOCKS (52.A-52.E), RUN IN ORDER, THEN STOP.
Repo: eignacio1/prediction-market-bot. Issued by the strategic window 2026-10-03 ~2:20 PM PT.

=== YOUR ROLE - READ THIS FIRST ===
You are an EXECUTOR. You run exactly the five blocks below, in order, and then you stop.
- You do NOT write new waves, new blocks or new prompts. You do NOT pick up work that is not listed here,
  however useful it looks. A gap you find outside scope: register it (GG/T) and move on (Hard Rule 11).
- You do NOT restructure 04_EXECUTION/ACTIVE_QUEUE.md. You only update the Status / Result cells of the
  Wave 52 rows (52.A-52.E) as each block closes. The strategic window owns everything else in that file.
- You do NOT take operator decisions (GG-432, GG-450, any ADR acceptance, any pre-registration amendment).
  You prepare them, state them in one line each, and leave them.
- When all five are done, or when every remaining block is blocked, write the final report (end of this
  prompt) and STOP. Do not look for more work. The strategic window issues the next wave.

=== WHAT THIS SESSION CANNOT DO (cloud, not a terminal) ===
- No SSH to the VPS. No VPS reads or writes, no crontab, no logs, no ledgers. Where a block needs a VPS fact,
  use the tracked record on main and cite it, or mark the item VPS-PENDING (a later terminal block does it).
  Never invent a VPS fact.
- No access to the operator's Mac folder. GitHub is your only shared surface.
- GitHub GraphQL is blocked here: use REST (gh api repos/eignacio1/prediction-market-bot/...) for PRs,
  including creating one (POST .../pulls). gh pr create may fail for that reason.
- Outbound network goes through an allowlist. If a site is refused, record the exact error and go on;
  do not retry through another tool.
- Clone may be shallow: git fetch --depth=1000 origin <branch> before merging or comparing.

=== HARD LIMITS (all five blocks) ===
- NOTHING merges to main. No file outside the 9 doc folders (00_ADMIN 01_SPEC 02_ARCHITECTURE_DESIGN
  03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE 08_MODEL_RISK_GOVERNANCE
  11_MEMORY_HANDOFF) is pushed to main. MLB postseason games are live and deploy.yml restarts t4-mlb on every
  code push (GG-432). Code goes on branches and PRs only. Docs-only pushes to main are fine.
- No order, position, fill, stake or kelly_fraction change. Demo only, always. No cron edits.
- Never bypass a permission control. Record the exact command and refusal, then move on.
- Claim IDs once at the start with scripts/claim_session.sh (derive the next free T- and GG- numbers at run
  time; a range of ~10 each). Never reuse a number already in SESSION_CLAIMS.md or the gap log.
- Every premise in this prompt is a claim to verify against tracked files and GitHub, not a fact.
- Pace: each block ~30 min, hard stop 45. At the stop, push what you have, record where it ends, and move to
  the next block. Run the full test suite (PYTHONPATH=src python3 -m pytest tests -q, ~11 min) at most once
  per code block; targeted tests otherwise.
- Context: you must reach the final report. Keep narration minimal. If context passes ~60%, finish the current
  block's push, skip to the final report, and list the unstarted blocks as NOT RUN.

=== AFTER EACH BLOCK (the rolling step - do this, then continue) ===
1. Push the block's branch / PR (code) and its results doc (docs-only push to main).
2. Update ONLY that block's row in ACTIVE_QUEUE.md (Status + one-line Result), docs-only push to main.
3. Go straight to the next block. Do not wait for the operator.

----------------------------------------------------------------------------------------------------
52.A - LANDING PREP: one pre-tested integration PR for everything Wave 51 left unmerged. Do NOT merge.

Why: PR #157, branch 51.1 (dashboard drawdown fix) and branch 51.2 (NHL team-code fix) are waiting, plus 9
NHL cells that log shadow rows while the registry says NOT_IMPLEMENTED. Tonight's landing must be ONE merge of
ONE green PR, so t4-mlb restarts once, not three times.

D1. From current origin/main, create branch w52/landing. Merge with --no-ff, in order:
   a) PR #157 head - branch claude/peaceful-heisenberg-51g2ee, expected 42a0d0d
   b) session/20261003T201912Z-w51-killswitch-truth, expected 6cbe62f
   c) session/20261003T201919Z-w51-nhl-team-codes, expected f822b6b
   If any head differs from expected, stop this block and report.
   Conflict policy (51.3 precedent): DECISION_LOG and GOVERNANCE_GAP_LOG keep every section from both sides.
   PLAN / TODO_NEXT / MEMORY_BANK carry one "Last reviewed" line: main's newest stays live, the older line
   moves to that file's *_ARCHIVE.md Last Reviewed Chain Archive. OPERATOR_DIGEST_* keep both sides.
   Never drop content from either side. Expected: OPERATOR_DIGEST_20261003.md (from #157) and four nav files
   (from 51.2).
D2. NHL SHADOW flip, own commit. Read commit 0cf11eb (T-608 flipped 4 NFL T1 cells) and copy its pattern,
   tests included. Flip NOT_IMPLEMENTED -> SHADOW in src/prediction_market_bot/c5_execution/market_type_registry.py
   for the cells that have rows per the terminal-verified table in
   11_MEMORY_HANDOFF/SESSION_HANDOFF_20261003_W51_3.md (expected 9: NHL_MONEYLINE, NHL_PUCK_LINE,
   NHL_GAME_TOTAL x T1, T2, T3; NHL_TEAM_TOTAL has none - leave it). You cannot re-check the VPS: cite that
   handoff in the commit and mark "rows re-verified on VPS" as VPS-PENDING for the landing block. Commit
   message: records reality (cron already evaluates these at kelly 0), not a promotion; GG-401 means no NHL T3
   score may be read yet.
D3. Full suite once; must be green. Fix only what your merges broke; anything else, register and continue.
D4. git fetch; if origin/main moved, merge it in. Push. Open ONE PR (REST) titled
   "Wave 52 landing: #157 + 51.1 + 51.2 + NHL SHADOW flip". Body: merged heads with SHAs, each conflict and its
   resolution, test count, and: "Merging this deploys and restarts t4-mlb and pmbot-web-dashboard. Merge only
   when no MLB game is live." Wait for CI on the PR; record run ID, result, and mergeable_state from the
   GitHub API. Leave PR #157 open.

----------------------------------------------------------------------------------------------------
52.B - GG-432 DECISION PR: stop CI restarting t4-mlb mid-game. Prepare only - the operator decides.

Why: .github/workflows/deploy.yml restarts t4-mlb and pmbot-web-dashboard on every push to main that touches
code, including mid-game. That is why code can only land in idle windows.

D1. Read deploy.yml in full and the GG-432 entry. Write down exactly when t4-mlb is restarted today.
D2. On branch w52/gg432-deploy (based on origin/main, NOT on w52/landing), implement the window's recommended
   option as one PR:
   (1) restart t4-mlb only when the push changed a file the t4-mlb process actually imports (derive the set
       from run_t4_mlb_live.py's import graph; a dashboard-only or docs-only push must not restart it), and
   (2) if such a file changed while an MLB game is In Progress (MLB Stats API schedule, checked inside the
       deploy job), pull the code but skip the t4-mlb restart and say so loudly in the job summary.
   State in the PR how the skipped restart gets done later (next deploy, or a by-hand restart) - do NOT add a
   cron or timer; that needs the operator's authorization.
   Keep the T-327 approval-path gate exactly as is. pmbot-web-dashboard keeps restarting (standing
   authorization).
D3. Test the workflow logic you can test locally (factor any decision logic into a small script with unit
   tests). Open the PR (REST) titled "GG-432 (FOR OPERATOR DECISION - do not merge): path-scoped, game-aware
   t4-mlb restart". Body: today vs proposed behavior in a 3-row table, and the 3 options from the queue
   (a: this PR, b: never auto-restart t4-mlb, c: keep as is).

----------------------------------------------------------------------------------------------------
52.C - MLB RESOLVER (GG-440): why no MLB paper position has settled since 2026-08-06.

Why: run_resolve_mlb.py (PIPE-05R, 06:30 UTC daily) logs HTTPError 406 from statsapi.mlb.com on every call
(per GG-440; ~17,000 lines) and settles nothing. 17 T1 + 9 T4 paper positions are stuck. Kalshi CANCELLED 16 of
the 17 T1 markets (GG-450); 1 is a real loss. The operator has NOT decided how cancelled markets get booked.

D1. Read GG-440, GG-441, GG-450, 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W51_1_killswitch_truth_results.md
   and run_resolve_mlb.py in full (note the CDN-block / ESPN comments near lines 105-120). Establish from the
   code which path each stuck position takes and why both paths settle nothing.
D2. Reproduce what you can from here: send the resolver's exact statsapi request (same URL, params, headers)
   and record status + response headers; then vary one thing at a time (Accept: application/json, no custom
   headers, default User-Agent). This is NOT the VPS's network - say so; the VPS reproduction is VPS-PENDING.
D3. Root cause in one sentence, labelled CONFIRMED (the code and your reproduction prove it) or LIKELY (needs
   the VPS reproduction).
D4. Smallest fix, with tests, on branch w52/resolver-406 (based on origin/main). Hard rule: the fix must never
   book a Kalshi-cancelled market as a win or loss - cancelled = skip and report until GG-450 is decided. If
   the root cause is in run_t4_mlb_live.py or anything the running t4-mlb imports, stop at the diagnosis.
   Open a PR (REST), not for merge yet.
D5. Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W52_C_resolver_406_results.md: root cause, evidence,
   the fix, and the VPS-PENDING list for a terminal (VPS reproduction; dry run against a COPY of the ledgers
   listing each of the 26 positions -> settles / skipped-cancelled / unresolvable). Add the root cause to
   GG-440; do NOT mark it resolved.

----------------------------------------------------------------------------------------------------
52.D - NHL CONFIRMED GOALIE (GG-401): can the T3 run know the confirmed starting goalie in time? Research.

Why: every NHL band uses a projected goalie (nhl_pregame.py is never given a starter_provider). The EXP-036
pre-registration promises T3 uses the confirmed starter. Until fixed or amended (operator's call), no NHL T3
score may be read.

Limits: do not edit nhl_pregame.py or nhl_shadow_eval.py (52.A is landing changes to both). Do not change any
pre-registered parameter. Do not read or compute any NHL score. No watchers or samplers - waiting is not work.

D1. Read the T3 promise in 05_RESEARCH_EXPERIMENTS/EXP036_NHL_PREGAME_SHADOW_PREREGISTRATION_2026-10-02.md and
   the StarterProvider interface (nhl_pregame.py ~lines 230-255). NHL run times: deploy/cron.nhl_shadow.draft
   is the tracked record (the live crontab is VPS-PENDING - say which you used). State exactly what T3 needs:
   which field, by what minute relative to puck drop.
D2. Probe sources for the last 2-3 days and today: the official NHL web API (api-web.nhle.com - gamecenter
   landing, boxscore, play-by-play goalie fields) and any public starting-goalie feed. For each: names the
   starter? marks confirmed vs projected? WHEN does it appear (timestamps the source provides)? Terms of use
   for anything unofficial. If the network refuses a source, record it and continue.
D3. Verdict, exactly one: (a) source X gives the confirmed starter before T3 in k of n games -> scope a
   StarterProvider build as one ~30-min block; (b) nothing beats T3 -> operator chooses: move T3 later, or amend
   the pre-registration to "projected goalie" (give exact wording); (c) cannot tell -> name the measurement.
D4. Results doc 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W52_D_nhl_goalie_source_results.md; any probe script
   on branch w52/nhl-goalie-probe. Add the finding to GG-401 without changing its status.

----------------------------------------------------------------------------------------------------
52.E - LIVE TERMINAL MATCHES THE BOT: every shadow cell visible and labelled truthfully.

Why: the Live Terminal is the operator's only visual indicator. After 52.A lands, the registry will hold
SHADOW 16 (3 MLB player-hits, 4 NFL T1, 9 NHL) and EXP-037 runs NFL + MLB-postseason game cells. The operator
must see each one, its row count and last-row time, and nothing labelled as something it is not.

D1. Branch w52/live-terminal from w52/landing (it builds on 51.1's dashboard fix; it lands AFTER 52.A).
   Read scripts/web_dashboard.py's shadow panel (_shadow, SHADOW_GLOBS ~line 422) and the registry.
D2. Audit, with fixture ledgers shaped like the real ones (data/shadow/<sport>/<CELL>.jsonl and the EXP-037
   ledger paths in src/prediction_market_bot/pregame_shadow/): does every registry SHADOW cell appear? Does
   every ledger with rows appear even if the registry says NOT_IMPLEMENTED (shown as such, in a different
   style - not hidden, not upgraded)? Is GG-431's stale panel (T1 book frozen since 2026-08-06) labelled as
   frozen with its true age, not as live?
D3. Fix the gaps, smallest change, tests for each. Keep Live Terminal.html in sync if the byte-fidelity tests
   require it. Targeted dashboard tests, then the full suite once.
D4. Open a PR (REST) based on w52/landing titled "Live Terminal: every shadow cell, truthful labels (lands
   after Wave 52 landing PR)". Body: before/after per gap, and VPS-PENDING: check on the running Live Terminal
   after deploy.

----------------------------------------------------------------------------------------------------
=== FINAL REPORT (write it, push it, then STOP) ===
Write 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC timestamp>_W52_CC.md and give the same text as your last
message. One table, one row per block:
  Block | Status (DONE / PARTIAL / BLOCKED / NOT RUN) | Branch + head SHA | PR # + CI result + mergeable_state |
  One-line result | VPS-PENDING items
Then: IDs claimed and used; every gap registered; every operator decision prepared (one line each); anything
you could not do and the exact error. Confirm: nothing merged to main, no non-docs file pushed to main.
Then stop. Do not start anything else.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 52 — issued 2026-10-03 ~2:20 PM PT · one Claude Code session, five blocks in order · branch/PR-only

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 52.A | Landing prep (integration PR) | ⬜ | `w52/landing` | Merged only in an idle window — the landing block |
| 52.B | GG-432 decision PR | ⬜ | `w52/gg432-deploy` | Your GG-432 call |
| 52.C | MLB resolver 406 (GG-440) | ⬜ | `w52/resolver-406` | VPS repro + ledger dry run (terminal); your GG-450 call |
| 52.D | NHL confirmed goalie (GG-401) | ⬜ | `w52/nhl-goalie-probe` | Verdict a/b/c; (b) needs your amendment call |
| 52.E | Live Terminal truth | ⬜ | `w52/live-terminal` (on `w52/landing`) | Lands after 52.A |

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

**Wave 52 runs without a line from you.** It prepares three of your calls: **GG-432** (52.B PR), **GG-450** booking of the 16 Kalshi-cancelled T1 positions (void / mark to settlement / exclude from G6), and any **NHL T3 pre-registration amendment** (52.D).

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").** Unchanged;
> used by 50.2. Not covered: any order, position, fill, stake or `kelly_fraction` change; any EXISTING cron line.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT).** Standing. Covers
> `pmbot-web-dashboard` only. Note: under today's `deploy.yml`, any code merge also restarts `t4-mlb` — see GG-432 below.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **NEW — GG-432: CI restarts t4-mlb on every code push** | Today every merge that touches code restarts the live T4 process, including mid-game. Options: (a) **window's recommendation** — deploy pulls code on every push but skips the `t4-mlb` restart while an MLB game is live (it restarts at the next idle window); (b) never auto-restart `t4-mlb`, restart only by hand; (c) keep as is. | Every code landing waits for an idle window by hand, as Wave 51 does. |
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
